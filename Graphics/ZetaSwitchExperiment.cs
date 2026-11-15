using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading.Tasks;

namespace Graphics
{
    // defines: graph.riemann.switch.model
    internal static class ZetaSwitchExperiment
    {
        internal const double MinSigma = 0.05;
        internal const double MaxSigma = 3;
        private const int Terms = 64;
        private const int RefinedTerms = 96;
        private static readonly double[] Bernoulli =
        {
            1.0 / 12, -1.0 / 720, 1.0 / 30240, -1.0 / 1209600,
            1.0 / 47900160, -691.0 / 1307674368000.0,
            7.0 / 523069747200.0, -3617.0 / 10670622842880000.0,
            43867.0 / 5109094217170944000.0,
            -174611.0 / 802857662698291200000.0
        };
        private static readonly ConcurrentDictionary<int, double[]> LogCache = new ConcurrentDictionary<int, double[]>();
        private static readonly Color Background = Color.FromArgb(13, 18, 30);
        private static readonly Color Card = Color.FromArgb(23, 30, 46);
        private static readonly Color Ink = Color.FromArgb(237, 242, 251);
        private static readonly Color Muted = Color.FromArgb(174, 188, 208);
        private static readonly Color[] Palette =
        {
            Color.FromArgb(27, 132, 110), Color.FromArgb(180, 135, 45),
            Color.FromArgb(133, 76, 172), Color.FromArgb(48, 99, 178)
        };

        internal sealed class Frame : IDisposable
        {
            internal Bitmap Image { get; }
            internal string Report { get; }
            internal object Snapshot { get; }
            internal double MinT { get; }
            internal double MaxT { get; }
            internal Frame(Bitmap image, string report, object snapshot, double minT, double maxT)
            { Image = image; Report = report; Snapshot = snapshot; MinT = minT; MaxT = maxT; }
            public void Dispose() => Image.Dispose();
        }

        private sealed class Marker
        {
            internal string Label;
            internal int Target;
            internal Complex S;
            internal Complex Value;
            internal double Residual;
            internal double RefinedResidual;
            internal double Movement;
            internal int Iterations;
        }

        private static bool Finite(Complex z) => double.IsFinite(z.Real) && double.IsFinite(z.Imaginary);
        private static Complex Invalid => new Complex(double.NaN, double.NaN);

        // This selector has no access to s, marker lists, root coordinates, or palette settings.
        // Z_1=zeta, Z_0=zeta-1; W=Z_b. A tie belongs to b=1.
        internal static int Select(Complex value) => !Finite(value) ? -1 : value.Real <= 0.5 ? 1 : 0;
        // Preserve small values exactly on branch 1; (z-1)+1 loses tiny real parts.
        private static Complex Selected(Complex value) => Select(value) switch
        { 1 => value, 0 => value - 1, _ => Invalid };

        internal static Complex Evaluate(Complex s, int n = Terms) => EvaluatePair(s, n, false).Value;
        internal static Complex Derivative(Complex s, int n = Terms) => EvaluatePair(s, n, true).Derivative;

        private static (Complex Value, Complex Derivative) EvaluatePair(Complex s, int n, bool derivative)
        {
            if (n < 16 || n > 1024) throw new ArgumentOutOfRangeException(nameof(n));
            if (!Finite(s) || s == Complex.One) return (Invalid, Invalid);
            double[] logs = LogCache.GetOrAdd(n, count => Enumerable.Range(1, count).Select(k => Math.Log(k)).ToArray());
            double re = 0, im = 0, reError = 0, imError = 0, dr = 0, di = 0;
            for (int k = 0; k < n - 1; k++)
            {
                double magnitude = Math.Exp(-s.Real * logs[k]);
                double angle = -s.Imaginary * logs[k];
                double tr = magnitude * Math.Cos(angle), ti = magnitude * Math.Sin(angle);
                // Compensated summation controls cancellation near both kinds of marker.
                double yr = tr - reError, nextRe = re + yr;
                reError = (nextRe - re) - yr; re = nextRe;
                double yi = ti - imError, nextIm = im + yi;
                imError = (nextIm - im) - yi; im = nextIm;
                if (derivative) { dr -= logs[k] * tr; di -= logs[k] * ti; }
            }
            double logN = logs[n - 1];
            Complex power = Complex.Exp(-s * logN);
            Complex denominator = s - 1;
            Complex value = new Complex(re, im) + n * power / denominator + 0.5 * power;
            Complex first = derivative ? new Complex(dr, di)
                + n * power * (-logN / denominator - 1 / (denominator * denominator))
                - 0.5 * logN * power : Complex.Zero;
            Complex rising = Complex.One, risingPrime = Complex.Zero;
            int degree = 0;
            for (int k = 0; k < Bernoulli.Length; k++)
            {
                int wanted = 2 * k + 1;
                while (degree < wanted)
                {
                    if (derivative) risingPrime = risingPrime * (s + degree) + rising;
                    rising *= s + degree;
                    degree++;
                }
                Complex factor = Bernoulli[k] * power * Math.Pow(n, -wanted);
                value += factor * rising;
                if (derivative) first += factor * (risingPrime - logN * rising);
            }
            return (value, first);
        }

        private static object Coordinates(Complex z) => new
        {
            real = double.IsFinite(z.Real) ? (double?)z.Real : null,
            imaginary = double.IsFinite(z.Imaginary) ? (double?)z.Imaginary : null
        };

        private static int Quadrant(Complex value, double rotation)
        {
            if (!Finite(value)) return -2;
            if (value == Complex.Zero) return -1;
            double angle = (value.Phase - (rotation % 360) * Math.PI / 180) % (2 * Math.PI);
            if (angle < 0) angle += 2 * Math.PI;
            return Math.Min(3, (int)(angle / (Math.PI / 2)));
        }

        private static Bitmap Raster(Complex[] grid, int resolution, int panel, double rotation)
        {
            var bytes = new byte[resolution * resolution * 4];
            Parallel.For(0, resolution, y =>
            {
                for (int x = 0; x < resolution; x++)
                {
                    int index = y * resolution + x;
                    Complex z = grid[index];
                    Complex displayed = panel == 0 ? z : panel == 1 ? z - 1
                        : panel == 2 ? Selected(z) : z * (z - 1);
                    int q = Quadrant(displayed, rotation);
                    Color color = q == -2 ? Color.FromArgb(90, 94, 105)
                        : q == -1 ? Color.White : Palette[q];
                    int offset = index * 4;
                    bytes[offset] = color.B; bytes[offset + 1] = color.G;
                    bytes[offset + 2] = color.R; bytes[offset + 3] = 255;
                }
            });
            var bitmap = new Bitmap(resolution, resolution, PixelFormat.Format32bppArgb);
            BitmapData data = bitmap.LockBits(new Rectangle(0, 0, resolution, resolution), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try
            {
                for (int y = 0; y < resolution; y++)
                    Marshal.Copy(bytes, y * resolution * 4, IntPtr.Add(data.Scan0, y * data.Stride), resolution * 4);
            }
            finally { bitmap.UnlockBits(data); }
            return bitmap;
        }

        private static bool Newton(Complex seed, int target, double minT, double maxT, int n,
            out Complex root, out int iterations)
        {
            root = seed;
            for (iterations = 0; iterations < 30; iterations++)
            {
                var point = EvaluatePair(root, n, true);
                if (!Finite(point.Value) || !Finite(point.Derivative)) return false;
                Complex residual = point.Value - target;
                if (residual.Magnitude < 2e-12)
                    return root.Real >= MinSigma && root.Real <= MaxSigma
                        && root.Imaginary >= minT && root.Imaginary <= maxT;
                if (point.Derivative.Magnitude < 1e-10) return false;
                Complex step = residual / point.Derivative;
                if (step.Magnitude > 1.5) step *= 1.5 / step.Magnitude;
                root -= step;
                if (root.Real < MinSigma - 1 || root.Real > MaxSigma + 1
                    || root.Imaginary < minT - 2 || root.Imaginary > maxT + 2) return false;
            }
            return false;
        }

        private static List<Marker> FindMarkers(double minT, double maxT)
        {
            var result = new List<Marker>();
            foreach (int target in new[] { 0, 1 })
            {
                foreach (double sigma in new[] { 0.35, 1.0, 2.0, 2.8 })
                {
                    int count = Math.Max(2, (int)Math.Ceiling(maxT - minT));
                    for (int i = 0; i <= count; i++)
                    {
                        var seed = new Complex(sigma, minT + (maxT - minT) * i / count);
                        if (!Newton(seed, target, minT, maxT, Terms, out Complex root, out int iterations)) continue;
                        if (result.Any(m => m.Target == target && (m.S - root).Magnitude < 1e-7)) continue;
                        if (!Newton(root, target, minT, maxT, RefinedTerms, out Complex refined, out _)) continue;
                        Complex value = Evaluate(root);
                        result.Add(new Marker { S = root, Target = target, Value = value,
                            Residual = (value - target).Magnitude,
                            RefinedResidual = (Evaluate(root, RefinedTerms) - target).Magnitude,
                            Movement = (refined - root).Magnitude, Iterations = iterations });
                    }
                }
            }
            result = result.OrderBy(m => m.Target).ThenBy(m => m.S.Imaginary).ToList();
            int zeros = 0, ones = 0;
            foreach (Marker marker in result) marker.Label = marker.Target == 0 ? "Z" + (++zeros) : "O" + (++ones);
            return result;
        }

        private static IEnumerable<(string Id, Complex S)> SamplePoints(double minT, double maxT)
        {
            for (int y = 0; y < 9; y++)
                for (int x = 0; x < 16; x++)
                    yield return ($"grid-{y}-{x}", new Complex(MinSigma + (MaxSigma - MinSigma) * x / 15, minT + (maxT - minT) * y / 8));
            foreach (int k in new[] { 2, 3 })
                foreach (double dx in new[] { -1e-7, 0.0, 1e-7 })
                    foreach (double dy in new[] { -1e-7, 0.0, 1e-7 })
                        yield return ($"eta-removable-{k}-{dx:R}-{dy:R}", new Complex(1 + dx, 2 * k * Math.PI / Math.Log(2) + dy));
            yield return ("reference-zero", new Complex(0.5, 14.134725141734694));
            yield return ("reference-one", new Complex(1.4077880406528867, 23.327987754559104));
            yield return ("reference-seam", new Complex(1.3869097447840162, 14.134725141734694));
        }

        // defines: graph.riemann.switch.render
        internal static Frame Compute(double minT, double maxT, int resolution, double rotation, bool showMarkers = true)
        {
            if (!double.IsFinite(minT) || !double.IsFinite(maxT) || minT < 10 || maxT > 30 || maxT <= minT)
                throw new ArgumentOutOfRangeException(nameof(minT), "Choose 10 <= minimum height < maximum height <= 30.");
            if (resolution < 64 || resolution > 512) throw new ArgumentOutOfRangeException(nameof(resolution));
            if (!double.IsFinite(rotation)) throw new ArgumentOutOfRangeException(nameof(rotation));
            var timer = Stopwatch.StartNew();
            var grid = new Complex[resolution * resolution];
            Parallel.For(0, resolution, y =>
            {
                double height = maxT - (maxT - minT) * y / (resolution - 1);
                for (int x = 0; x < resolution; x++)
                    grid[y * resolution + x] = Evaluate(new Complex(MinSigma + (MaxSigma - MinSigma) * x / (resolution - 1), height));
            });
            var markers = FindMarkers(minT, maxT);
            double maxRefinement = 0, maxDerivativeRefinement = 0;
            var samples = new List<object>();
            foreach (var point in SamplePoints(minT, maxT))
            {
                var evaluated = EvaluatePair(point.S, Terms, true);
                var refined = EvaluatePair(point.S, RefinedTerms, true);
                Complex value = evaluated.Value;
                int b = Select(value);
                double difference = (value - refined.Value).Magnitude;
                maxRefinement = Math.Max(maxRefinement, difference);
                maxDerivativeRefinement = Math.Max(maxDerivativeRefinement, (evaluated.Derivative - refined.Derivative).Magnitude);
                samples.Add(new { id = point.Id, s = Coordinates(point.S), zeta = Coordinates(value),
                    zetaMinusOne = Coordinates(value - 1), b, selected = Coordinates(Selected(value)),
                    product = Coordinates(value * (value - 1)), derivative = Coordinates(evaluated.Derivative),
                    refinedZeta = Coordinates(refined.Value), refinementDelta = difference,
                    insideView = point.S.Imaginary >= minT && point.S.Imaginary <= maxT });
            }
            int invalid = grid.Count(z => !Finite(z));
            int branchOne = grid.Count(z => Select(z) == 1);
            int seamCells = 0;
            for (int y = 0; y < resolution - 1; y++)
                for (int x = 0; x < resolution - 1; x++)
                {
                    int index = y * resolution + x;
                    double[] signs = { grid[index].Real - 0.5, grid[index + 1].Real - 0.5,
                        grid[index + resolution].Real - 0.5, grid[index + resolution + 1].Real - 0.5 };
                    if (signs.All(double.IsFinite) && signs.Min() <= 0 && signs.Max() >= 0) seamCells++;
                }
            Bitmap image = Render(grid, resolution, minT, maxT, rotation, showMarkers, markers, maxRefinement);
            timer.Stop();
            var controls = new[] { Complex.Zero, Complex.One, new Complex(0.5, 2), new Complex(0.5 - 1e-7, 0.7),
                new Complex(0.5 + 1e-7, 0.7), new Complex(-2, 4), new Complex(3, -5) }
                .Select(z => new { input = Coordinates(z), b = Select(z), selected = Coordinates(Selected(z)),
                    product = Coordinates(z * (z - 1)) }).ToArray();
            var selectorProbes = new[]
            {
                (Id: "seam-left", Z: new Complex(0.5 - 1e-8, 0.3)),
                (Id: "seam-right", Z: new Complex(0.5 + 1e-8, 0.3)),
                (Id: "seam-tie-complex", Z: new Complex(0.5, 0.3)),
                (Id: "seam-tie-real", Z: new Complex(0.5, 0)),
                (Id: "exact-zero", Z: Complex.Zero), (Id: "exact-one", Z: Complex.One),
                (Id: "tiny-positive", Z: new Complex(1e-18, 0)), (Id: "tiny-negative", Z: new Complex(-1e-18, 0))
            }.Select(p => new { id = p.Id, zeta = Coordinates(p.Z), b = Select(p.Z),
                selected = Coordinates(Selected(p.Z)), product = Coordinates(p.Z * (p.Z - 1)) }).ToArray();
            object snapshot = new
            {
                schema = "graph-zeta-switch-v1", traceId = "graph.riemann.switch",
                domain = new { minSigma = MinSigma, maxSigma = MaxSigma, minT, maxT },
                settings = new { resolution, paletteDegrees = rotation, showMarkers,
                    evaluator = new { method = "Euler-Maclaurin", n = Terms, corrections = Bernoulli.Length, refinementN = RefinedTerms } },
                selector = new { definition = "b=1 if Re(zeta)<=0.5, otherwise b=0; W=zeta-1+b", tie = 1,
                    inputs = "complex zeta value only", seam = "Re(zeta)=0.5", selectedMapHolomorphic = false,
                    product = "G=zeta*(zeta-1); holomorphic on this viewing rectangle" },
                metrics = new { validPixels = grid.Length - invalid, invalidPixels = invalid, branchOnePixels = branchOne,
                    branchZeroPixels = grid.Length - invalid - branchOne, seamCells, maxRefinementDelta = maxRefinement,
                    maxDerivativeRefinementDelta = maxDerivativeRefinement, elapsedMilliseconds = timer.ElapsedMilliseconds },
                interpretation = new { selectorUsesMarkers = false, selectedAnalytic = false, productAnalyticOnDomain = true },
                samples, controls, selectorProbes,
                markers = markers.Select(m => new { label = m.Label, kind = m.Target == 0 ? "zeta-zero" : "zeta-one",
                    s = Coordinates(m.S), zeta = Coordinates(m.Value), target = m.Target, residual = m.Residual,
                    refinedResidual = m.RefinedResidual, refinementMovement = m.Movement, iterations = m.Iterations }).ToArray(),
                limitations = new[] { "Floating-point Euler-Maclaurin values; refinement agreement is not a certified error bound.",
                    "Newton markers are empirical candidates, not exhaustive root counts or rigorous enclosures.",
                    "Sampled seam interpolation is display geometry, not a certified contour.",
                    "Colors and the selector do not prove RH or distinguish prime numbers." }
            };
            string report = $"Zeta switching laboratory: sigma [{MinSigma}, {MaxSigma}], t [{minT}, {maxT}].\n"
                + $"One shared {resolution}x{resolution} Euler-Maclaurin grid; N={Terms}, {Bernoulli.Length} corrections.\n"
                + "Z1=zeta; Z0=zeta-1; b=1 when Re(zeta)<=1/2 (tie1), else0; W=Zb. G=zeta(zeta-1).\n"
                + "W has a jump at the output seam Re(zeta)=1/2. G is holomorphic in this view.\n"
                + "Dashed white input line sigma=1/2 differs from the cyan output seam. Palette rotation affects colors only.\n"
                + $"Pixels: b1={branchOne}; b0={grid.Length - invalid - branchOne}; invalid={invalid}; seam cells={seamCells}.\n"
                + $"{samples.Count} numeric samples; N64/96 max value difference={maxRefinement:E3}; derivative difference={maxDerivativeRefinement:E3}.\n"
                + string.Join("\n", markers.Select(m => $"{m.Label}: zeta={m.Target}, s={m.S.Real:G16}+{m.S.Imaginary:G16}i, residual={m.Residual:E3}, refinement movement={m.Movement:E3}"))
                + $"\nElapsed {timer.ElapsedMilliseconds} ms. Marker search is empirical and not exhaustive. Refinement is not a rigorous enclosure. No RH result is claimed.";
            return new Frame(image, report, snapshot, minT, maxT);
        }

        internal static bool TryMapPixel(Frame frame, float imageX, float imageY, out Complex s)
        {
            for (int panel = 0; panel < 4; panel++)
            {
                int left = panel % 2 == 0 ? 24 : 732;
                int top = panel < 2 ? 145 : 620;
                var plot = new Rectangle(left + 65, top + 80, 590, 316);
                if (imageX >= plot.Left && imageX <= plot.Right && imageY >= plot.Top && imageY <= plot.Bottom)
                {
                    s = new Complex(MinSigma + (MaxSigma - MinSigma) * (imageX - plot.Left) / plot.Width,
                        frame.MaxT - (frame.MaxT - frame.MinT) * (imageY - plot.Top) / plot.Height);
                    return true;
                }
            }
            s = Complex.Zero;
            return false;
        }

        internal static string DescribePoint(Complex s, double rotation)
        {
            Complex value = Evaluate(s);
            if (!Finite(value)) return "Invalid evaluator value; this pixel has no selected branch.";
            int b = Select(value);
            Complex shifted = value - 1, selected = Selected(value), product = value * shifted;
            string C(Complex z) => $"{z.Real:G7}{(z.Imaginary < 0 ? "" : "+")}{z.Imaginary:G7}i";
            string Q(Complex z) => z == Complex.Zero ? "undefined at zero" : (Quadrant(z, rotation) + 1).ToString();
            return $"s={C(s)}; ζ={C(value)}; ζ−1={C(shifted)}; b={b}; W={C(selected)}; G={C(product)}. "
                + $"Display quadrants ζ/ζ−1/W/G: {Q(value)}/{Q(shifted)}/{Q(selected)}/{Q(product)}. "
                + $"Output seam residual Re ζ−½={value.Real - 0.5:G6}; input σ−½={s.Real - 0.5:G6}.";
        }

        private static Bitmap Render(Complex[] grid, int resolution, double minT, double maxT, double rotation,
            bool showMarkers, List<Marker> markers, double refinement)
        {
            var image = new Bitmap(1440, 1200);
            using var g = System.Drawing.Graphics.FromImage(image);
            g.Clear(Background);
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            using var title = new Font("Segoe UI", 30, FontStyle.Bold, GraphicsUnit.Pixel);
            using var heading = new Font("Segoe UI", 21, FontStyle.Bold, GraphicsUnit.Pixel);
            using var body = new Font("Segoe UI", 16, FontStyle.Regular, GraphicsUnit.Pixel);
            using var small = new Font("Segoe UI", 13, FontStyle.Regular, GraphicsUnit.Pixel);
            using var ink = new SolidBrush(Ink);
            using var muted = new SolidBrush(Muted);
            g.DrawString("ZETA: TWO OUTPUT ORIGINS AND THEIR SWITCH", title, ink, 25, 20);
            g.DrawString("The selector sees only ζ(s). It chooses the output nearest zero; colors show phase quadrants.", body, muted, 28, 63);
            g.DrawString($"σ = {MinSigma} … {MaxSigma}    t = {minT:G5} … {maxT:G5}    grid {resolution}²    palette {rotation:G5}°    N64/96 sample Δ ≤ {refinement:E1}", body, ink, 28, 96);
            string[] names = { "Z₁ = ζ(s)", "Z₀ = ζ(s) − 1", "W = Zb   ·   discontinuous selector", "G = ζ(s)[ζ(s) − 1]   ·   analytic product" };
            string[] subtitles = { "Original output origin: circle Z markers have ζ = 0.",
                "Shifted output origin: diamond O markers have ζ = 1.",
                "b = 1 if Re ζ ≤ ½; b = 0 otherwise. Ties choose 1.",
                "Both kinds of zero remain distinct; no switching is used." };
            for (int panel = 0; panel < 4; panel++)
            {
                int left = panel % 2 == 0 ? 24 : 732;
                int top = panel < 2 ? 145 : 620;
                var bounds = new Rectangle(left, top, 684, 455);
                var plot = new Rectangle(left + 65, top + 80, 590, 316);
                using var card = new SolidBrush(Card);
                g.FillRectangle(card, bounds);
                g.DrawString(names[panel], heading, ink, left + 17, top + 12);
                g.DrawString(subtitles[panel], small, muted, left + 17, top + 44);
                using (Bitmap raster = Raster(grid, resolution, panel, rotation))
                {
                    g.InterpolationMode = InterpolationMode.NearestNeighbor;
                    g.PixelOffsetMode = PixelOffsetMode.Half;
                    g.DrawImage(raster, plot);
                    g.PixelOffsetMode = PixelOffsetMode.Default;
                }
                DrawSeam(g, grid, resolution, plot);
                float criticalX = (float)(plot.Left + (0.5 - MinSigma) / (MaxSigma - MinSigma) * plot.Width);
                using var critical = new Pen(Color.White, 1.3f) { DashStyle = DashStyle.Dash };
                g.DrawLine(critical, criticalX, plot.Top, criticalX, plot.Bottom);
                using var border = new Pen(Color.FromArgb(155, 176, 202));
                g.DrawRectangle(border, plot);
                foreach (double sigma in new[] { MinSigma, 0.5, 1, 2, 3 })
                {
                    float x = (float)(plot.Left + (sigma - MinSigma) / (MaxSigma - MinSigma) * plot.Width);
                    string label = sigma.ToString("G3", CultureInfo.InvariantCulture);
                    SizeF size = g.MeasureString(label, small);
                    g.DrawString(label, small, muted, x - size.Width / 2, plot.Bottom + 7);
                }
                for (int k = 0; k <= 4; k++)
                {
                    double height = maxT - (maxT - minT) * k / 4;
                    float y = plot.Top + plot.Height * k / 4f;
                    string label = height.ToString("G4", CultureInfo.InvariantCulture);
                    SizeF size = g.MeasureString(label, small);
                    g.DrawString(label, small, muted, plot.Left - 10 - size.Width, y - 8);
                }
                g.DrawString("t", body, muted, left + 20, plot.Top - 22);
                g.DrawString("real part σ", small, muted, plot.Right - 65, plot.Bottom + 29);
                if (showMarkers) DrawMarkers(g, markers, plot, minT, maxT, small);
            }
            g.DrawString("WHITE DASH: input σ = ½     CYAN CURVE: output Re ζ = ½     CIRCLE Z: ζ = 0     DIAMOND O: ζ = 1", body, ink, 28, 1092);
            g.DrawString("Phase minus rotation:", small, muted, 28, 1126);
            for (int q = 0; q < 4; q++)
            {
                int x = 180 + q * 155;
                using var swatch = new SolidBrush(Palette[q]);
                g.FillRectangle(swatch, x, 1128, 18, 13);
                g.DrawString($"Q{q + 1}: {q * 90}–{(q + 1) * 90}°", small, muted, x + 24, 1126);
            }
            g.DrawString("White: exact zero. Gray: invalid.", small, muted, 820, 1126);
            g.DrawString("One ζ grid is reused; markers never affect selection. Newton candidates and sampled seams are empirical, not certified enclosures.", small, muted, 28, 1150);
            g.DrawString("This finite numerical experiment does not establish the Riemann Hypothesis. Zero and one-point data remain separate in the export.", small, muted, 28, 1174);
            return image;
        }

        private static void DrawSeam(System.Drawing.Graphics g, Complex[] grid, int resolution, Rectangle plot)
        {
            using var outline = new Pen(Color.FromArgb(15, 24, 36), 3.5f);
            using var seam = new Pen(Color.FromArgb(60, 251, 244), 1.5f);
            float dx = (float)plot.Width / (resolution - 1), dy = (float)plot.Height / (resolution - 1);
            for (int y = 0; y < resolution - 1; y++)
                for (int x = 0; x < resolution - 1; x++)
                {
                    int index = y * resolution + x;
                    double[] v = { grid[index].Real - 0.5, grid[index + 1].Real - 0.5,
                        grid[index + resolution + 1].Real - 0.5, grid[index + resolution].Real - 0.5 };
                    if (v.Any(z => !double.IsFinite(z)) || v.Min() > 0 || v.Max() < 0) continue;
                    PointF[] corners = { new PointF(plot.Left + x * dx, plot.Top + y * dy),
                        new PointF(plot.Left + (x + 1) * dx, plot.Top + y * dy),
                        new PointF(plot.Left + (x + 1) * dx, plot.Top + (y + 1) * dy),
                        new PointF(plot.Left + x * dx, plot.Top + (y + 1) * dy) };
                    var crossings = new List<PointF>(4);
                    for (int edge = 0; edge < 4; edge++)
                    {
                        int next = (edge + 1) % 4;
                        if ((v[edge] <= 0) == (v[next] <= 0)) continue;
                        float fraction = (float)(v[edge] / (v[edge] - v[next]));
                        crossings.Add(new PointF(corners[edge].X + fraction * (corners[next].X - corners[edge].X),
                            corners[edge].Y + fraction * (corners[next].Y - corners[edge].Y)));
                    }
                    // Ambiguous four-crossing cells are display interpolation, never proof data.
                    for (int k = 0; k + 1 < crossings.Count; k += 2)
                    { g.DrawLine(outline, crossings[k], crossings[k + 1]); g.DrawLine(seam, crossings[k], crossings[k + 1]); }
                }
        }

        private static void DrawMarkers(System.Drawing.Graphics g, List<Marker> markers, Rectangle plot,
            double minT, double maxT, Font font)
        {
            foreach (Marker marker in markers)
            {
                float x = (float)(plot.Left + (marker.S.Real - MinSigma) / (MaxSigma - MinSigma) * plot.Width);
                float y = (float)(plot.Bottom - (marker.S.Imaginary - minT) / (maxT - minT) * plot.Height);
                Color color = marker.Target == 0 ? Color.White : Color.FromArgb(255, 204, 83);
                using var pen = new Pen(color, 2.5f);
                using var dark = new SolidBrush(Color.FromArgb(16, 20, 31));
                using var brush = new SolidBrush(color);
                if (marker.Target == 0)
                { g.FillEllipse(dark, x - 6, y - 6, 12, 12); g.DrawEllipse(pen, x - 6, y - 6, 12, 12); }
                else
                {
                    PointF[] diamond = { new PointF(x, y - 7), new PointF(x + 7, y), new PointF(x, y + 7), new PointF(x - 7, y) };
                    g.FillPolygon(dark, diamond); g.DrawPolygon(pen, diamond);
                }
                SizeF label = g.MeasureString(marker.Label, font);
                float lx = Math.Min(plot.Right - label.Width - 3, Math.Max(plot.Left + 2, x + 9));
                float ly = Math.Min(plot.Bottom - label.Height - 2, Math.Max(plot.Top + 2, y - label.Height - 2));
                g.FillRectangle(dark, lx - 1, ly, label.Width + 2, label.Height);
                g.DrawString(marker.Label, font, brush, lx, ly);
            }
        }

        internal static void Export(string pngPath, Frame frame)
        {
            string path = Path.GetFullPath(pngPath);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            frame.Image.Save(path, ImageFormat.Png);
            File.WriteAllText(Path.ChangeExtension(path, ".values.json"),
                JsonSerializer.Serialize(frame.Snapshot, new JsonSerializerOptions { WriteIndented = true }));
            File.WriteAllText(Path.ChangeExtension(path, ".txt"), frame.Report);
        }

        // defines: graph.riemann.switch.verify
        internal static string Verify()
        {
            int checks = 0;
            void Check(bool pass, string description)
            { checks++; if (!pass) throw new InvalidOperationException("Switch verification failed: " + description); }
            foreach (double real in new[] { -2, 0, 0.4999999, 0.5, 0.5000001, 1, 3 })
                foreach (double imaginary in new[] { -4.0, 0, 5.0 })
                {
                    Complex value = new Complex(real, imaginary);
                    int b = Select(value);
                    Complex chosen = Selected(value), alternate = b == 1 ? value - 1 : value;
                    Check(b == (real <= 0.5 ? 1 : 0), "pure real-part selector including exact tie");
                    Check(chosen.Magnitude <= alternate.Magnitude + 1e-14, "selector chooses nearest output");
                    if (real != 0.5) Check(Select(1 - value) == 1 - b, "opposite real branch reflection");
                }
            Check(Select(Invalid) == -1, "invalid values have no selected branch");
            Check(Select(Complex.Zero) == 1 && Select(Complex.One) == 0, "zero and one-point select different branches");
            Check(Selected(new Complex(1e-18, 0)) == new Complex(1e-18, 0), "positive tiny input is not erased into a false zero");
            Check(Selected(new Complex(-1e-18, 0)) == new Complex(-1e-18, 0), "negative tiny input is not erased into a false zero");
            Check(Quadrant(Complex.One, double.MaxValue) == Quadrant(Complex.One, double.MaxValue % 360), "finite large palette rotation does not overflow");
            Complex left = new Complex(0.5 - 1e-7, 0.7), right = new Complex(0.5 + 1e-7, 0.7);
            Complex jump = Selected(right) - Selected(left);
            Check(Math.Abs(jump.Real + 1 - 2e-7) < 1e-14 && jump.Imaginary == 0, "nonzero selector jump at seam");
            Complex[] inputs = { new Complex(0.5, 14.134725141734694), new Complex(2, 20), new Complex(1, 4 * Math.PI / Math.Log(2)),
                new Complex(1, 6 * Math.PI / Math.Log(2)), new Complex(1.4077880406528867, 23.327987754559104) };
            foreach (Complex s in inputs)
            {
                Complex value = Evaluate(s), refined = Evaluate(s, RefinedTerms);
                Check(Finite(value) && (value - refined).Magnitude < 1e-10, "N64/96 value refinement including eta removable points");
                const double h = 1e-5;
                Complex a = Evaluate(s + h), b = Evaluate(s - h);
                Complex numeric = (a - b) / (2 * h), shiftedNumeric = ((a - 1) - (b - 1)) / (2 * h);
                Check((numeric - Derivative(s)).Magnitude < 2e-8, "analytic Euler-Maclaurin derivative");
                Check((numeric - shiftedNumeric).Magnitude < 2e-10, "constant shift preserves derivative");
                Check((Evaluate(Complex.Conjugate(s)) - Complex.Conjugate(value)).Magnitude < 1e-12, "conjugation symmetry");
                Complex offset = new Complex(0.017, 0.023);
                Complex other = Evaluate(s + offset);
                Check(((other - value) - ((other - 1) - (value - 1))).Magnitude < 1e-12, "constant shift preserves point differences");
            }
            Check((Evaluate(new Complex(2, 0)) - Math.PI * Math.PI / 6).Magnitude < 1e-12, "zeta(2) reference");
            Check(Evaluate(inputs[0]).Magnitude < 1e-11, "reference zeta zero residual");
            Check((Evaluate(inputs[4]) - 1).Magnitude < 1e-11, "reference zeta one-point residual");
            return $"{checks} switch/model checks passed: pure selector/ties, nearest output, seam jump, opposite branches, invalid state, N64/96 refinement, analytic derivative, shift invariance, conjugation, and reference residuals. Numerical checks are not an RH proof.";
        }
    }
}
