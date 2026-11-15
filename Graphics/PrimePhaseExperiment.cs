using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading.Tasks;

namespace Graphics
{
    // defines: graph.primes.phase.render
    // consumer: graph.primes.phase
    internal static class PrimePhaseExperiment
    {
        private const int Rows = 481;
        private const double HeightMax = 40;
        private const double Tau = 2 * Math.PI;
        private static readonly Color Background = Color.FromArgb(12, 15, 28);
        private static readonly Color Panel = Color.FromArgb(22, 27, 45);
        private static readonly Color Ink = Color.FromArgb(236, 240, 251);
        private static readonly Color Muted = Color.FromArgb(159, 174, 199);
        private static readonly Color Violet = Color.FromArgb(205, 133, 255);
        private static readonly Color[] Palette = {
            Color.FromArgb(56, 209, 186), Color.FromArgb(245, 191, 86),
            Color.FromArgb(238, 107, 146), Color.FromArgb(80, 145, 231)
        };

        public static int[] Primes(int cutoff)
        {
            if (cutoff < 2 || cutoff > 100000) throw new ArgumentOutOfRangeException(nameof(cutoff));
            var composite = new bool[cutoff + 1];
            for (int p = 2; p * p <= cutoff; p++)
                if (!composite[p])
                    for (int n = p * p; n <= cutoff; n += p) composite[n] = true;
            return Enumerable.Range(2, cutoff - 1).Where(p => !composite[p]).ToArray();
        }

        private static void Domain(Complex s)
        {
            if (!double.IsFinite(s.Real) || !double.IsFinite(s.Imaginary) || s.Real <= 1)
                throw new ArgumentOutOfRangeException(nameof(s), "This finite Euler-product experiment requires real part greater than 1.");
        }

        internal static Complex Contribution(Complex s, int p)
        {
            Domain(s);
            if (p < 2) throw new ArgumentOutOfRangeException(nameof(p));
            return -Complex.Log(Complex.One - Complex.Exp(-s * Math.Log(p)));
        }

        private static Complex Step(double amplitude, double angle) =>
            -Complex.Log(new Complex(1 - amplitude * Math.Cos(angle), amplitude * Math.Sin(angle)));

        internal static double Wrap(double phase)
        {
            double value = phase % Tau;
            if (value < 0) value += Tau;
            return value >= Tau ? 0 : value;
        }

        internal static int Quadrant(Complex value, double basis = 0, double uncertainty = 0)
        {
            if (!double.IsFinite(value.Real) || !double.IsFinite(value.Imaginary)
                || !double.IsFinite(uncertainty) || uncertainty < 0 || value.Magnitude <= uncertainty) return -1;
            var rotated = value * Complex.FromPolarCoordinates(1, -basis);
            if (uncertainty > 0 && (Math.Abs(rotated.Real) <= uncertainty || Math.Abs(rotated.Imaginary) <= uncertainty)) return -1;
            return Math.Min(3, (int)(Wrap(value.Phase - basis) / (Math.PI / 2)));
        }

        internal static double TailBound(double sigma, int cutoff)
        {
            Domain(new Complex(sigma, 0));
            if (cutoff < 2) throw new ArgumentOutOfRangeException(nameof(cutoff));
            return Math.Pow(cutoff, 1 - sigma) / ((sigma - 1) * (1 - Math.Pow(cutoff + 1, -sigma)));
        }

        private sealed class Mesh
        {
            public int[] Primes;
            public Complex[] Steps, Logs;
            public bool[] Flips, Comparable;
            public int[] ContributionPixels, ProductPixels;
            public int FlipCount, RotatedDifferences;
            public double ReverseError;
        }

        private static Mesh Calculate(double sigma, int cutoff, double basisDegrees, bool reverse, int rows)
        {
            Domain(new Complex(sigma, 0));
            if (!double.IsFinite(basisDegrees)) throw new ArgumentOutOfRangeException(nameof(basisDegrees));
            int[] primes = Primes(cutoff);
            if (reverse) Array.Reverse(primes);
            int count = primes.Length;
            var mesh = new Mesh { Primes = primes, Steps = new Complex[count * rows], Logs = new Complex[count * rows],
                Flips = new bool[count * rows], Comparable = new bool[count * rows], ContributionPixels = new int[count * rows], ProductPixels = new int[count * rows] };
            var logs = primes.Select(p => Math.Log(p)).ToArray();
            var amplitudes = primes.Select(p => Math.Pow(p, -sigma)).ToArray();
            var flipCounts = new int[rows];
            var rotationCounts = new int[rows];
            var reverseErrors = new double[rows];
            double basis = basisDegrees * Math.PI / 180;
            Parallel.For(0, rows, y =>
            {
                double t = HeightMax * (rows - 1 - y) / (rows - 1);
                Complex sum = Complex.Zero;
                for (int x = 0; x < count; x++)
                {
                    int i = y * count + x;
                    Complex step = Step(amplitudes[x], t * logs[x]);
                    Complex before = Complex.Exp(sum);
                    sum += step;
                    Complex after = Complex.Exp(sum);
                    // t=0 is exactly real by construction. Else use an explicitly empirical display tolerance.
                    double epsilon = t == 0 ? 0 : 1e-12 * Math.Max(1, after.Magnitude);
                    int oldQuadrant = Quadrant(before, basis, t == 0 || x == 0 ? 0 : epsilon);
                    int newQuadrant = Quadrant(after, basis, epsilon);
                    // Compare consecutive nonempty partial products, excluding the initial unit on an axis.
                    bool comparable = x > 0 && oldQuadrant >= 0 && newQuadrant >= 0;
                    bool flip = comparable && oldQuadrant != newQuadrant;
                    int alternateBefore = Quadrant(before, basis + Math.PI / 8, epsilon);
                    int alternateAfter = Quadrant(after, basis + Math.PI / 8, epsilon);
                    bool rotatedFlip = x > 0 && alternateBefore >= 0 && alternateAfter >= 0 && alternateBefore != alternateAfter;
                    mesh.Steps[i] = step;
                    mesh.Logs[i] = sum;
                    mesh.Flips[i] = flip;
                    mesh.Comparable[i] = comparable;
                    flipCounts[y] += flip ? 1 : 0;
                    rotationCounts[y] += flip != rotatedFlip ? 1 : 0;
                    double localEpsilon = t == 0 ? 0 : 1e-12 * Math.Max(1, step.Magnitude);
                    int localQuadrant = Quadrant(step, basis, localEpsilon);
                    double strength = Math.Clamp(step.Magnitude / -Math.Log(1 - amplitudes[x]), 0, 1);
                    mesh.ContributionPixels[i] = flip ? Violet.ToArgb() : Shade(localQuadrant, 0.48 + 0.52 * strength).ToArgb();
                    mesh.ProductPixels[i] = flip ? Violet.ToArgb() : Shade(newQuadrant, 0.55 + 0.35 * Math.Tanh(after.Magnitude / 2)).ToArgb();
                }
                Complex backwards = Complex.Zero;
                for (int x = count - 1; x >= 0; x--) backwards += mesh.Steps[y * count + x];
                reverseErrors[y] = (Complex.Exp(sum) - Complex.Exp(backwards)).Magnitude;
            });
            mesh.FlipCount = flipCounts.Sum();
            mesh.RotatedDifferences = rotationCounts.Sum();
            mesh.ReverseError = reverseErrors.Max();
            return mesh;
        }

        private static Color Shade(int quadrant, double strength)
        {
            if (quadrant < 0) return Color.FromArgb(105, 110, 128);
            Color color = Palette[quadrant];
            return Color.FromArgb((int)(color.R * strength), (int)(color.G * strength), (int)(color.B * strength));
        }

        private static Bitmap Pixels(int width, int height, int[] pixels)
        {
            var bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
            var data = bitmap.LockBits(new Rectangle(0, 0, width, height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try
            {
                for (int row = 0; row < height; row++)
                    Marshal.Copy(pixels, row * width, IntPtr.Add(data.Scan0, row * data.Stride), width);
            }
            finally { bitmap.UnlockBits(data); }
            return bitmap;
        }

        public static Bitmap Render(double sigma, int cutoff, double basisDegrees, int selectedPrime, bool reverse, out string report, bool overlay = false)
        {
            var timer = Stopwatch.StartNew();
            Mesh mesh = Calculate(sigma, cutoff, basisDegrees, reverse, Rows);
            int count = mesh.Primes.Length;
            if (!mesh.Primes.Contains(selectedPrime)) throw new ArgumentOutOfRangeException(nameof(selectedPrime));
            double flipRate = (double)mesh.FlipCount / (Rows * count);
            double rotationRate = (double)mesh.RotatedDifferences / (Rows * count);
            double spacing = Math.PI / Math.Log(selectedPrime);
            double bound = TailBound(sigma, cutoff);
            var result = new Bitmap(1500, 1060);
            using var g = System.Drawing.Graphics.FromImage(result);
            g.Clear(Background);
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            using var title = new Font("Segoe UI", 32, FontStyle.Bold, GraphicsUnit.Pixel);
            using var heading = new Font("Segoe UI", 20, FontStyle.Bold, GraphicsUnit.Pixel);
            using var body = new Font("Segoe UI", 15, FontStyle.Regular, GraphicsUnit.Pixel);
            using var small = new Font("Segoe UI", 13, FontStyle.Regular, GraphicsUnit.Pixel);
            using var white = new SolidBrush(Ink);
            using var muted = new SolidBrush(Muted);
            using var violet = new SolidBrush(Violet);
            using var panel = new SolidBrush(Panel);
            g.DrawString("THE PRIME COLOR LOOM", title, white, 36, 24);
            g.DrawString("Each prime is a local step: a change in scale and a turn in angle. Violet marks an accumulated quadrant change.", body, muted, 38, 71);
            g.DrawString($"REAL PART  {sigma:F2}     PRIMES THROUGH  {cutoff}     {count} PRIME FACTORS     AXES  {basisDegrees:F0}°     {(reverse ? "DESCENDING" : "ASCENDING")} ORDER", body, violet, 38, 106);

            var left = new Rectangle(68, 204, 654, 480);
            var right = new Rectangle(808, 204, 654, 480);
            g.FillRectangle(panel, 28, 148, 708, 600);
            g.FillRectangle(panel, 768, 148, 708, 600);
            g.DrawString("01   WHAT EACH PRIME ADDS", heading, white, 48, 161);
            g.DrawString("02   THE ACCUMULATING PRODUCT", heading, white, 788, 161);
            DrawMesh(g, mesh, mesh.ContributionPixels, left, selectedPrime, small, muted);
            DrawMesh(g, mesh, mesh.ProductPixels, right, selectedPrime, small, muted);
            if (overlay) DrawLandmarks(g, right, small);
            g.DrawString("x = prime index. Quadrant of Δlog P; column-scaled brightness.", small, muted, 48, 719);
            g.DrawString("x = prime index. Quadrant of finite P; gray = uncertain quadrant.", small, muted, 788, 719);

            g.FillRectangle(panel, 28, 764, 708, 234);
            g.FillRectangle(panel, 768, 764, 708, 234);
            g.DrawString($"03   THE RHYTHM OF p = {selectedPrime}", heading, white, 48, 777);
            DrawWave(g, sigma, selectedPrime, new Rectangle(68, 832, 640, 102), small, muted);
            g.DrawString($"Zero-crossing spacing = π / log({selectedPrime}) = {spacing:F4}. Dashed gray: composite n = 12.", small, muted, 48, 965);
            RowOverlap overlap = CountRowOverlaps(mesh);
            if (overlay)
            {
                g.DrawString("04   VIOLET AT INTEGER HEIGHTS", heading, white, 788, 777);
                g.DrawString($"Prime rows  {overlap.PrimeFlips:N0} / {overlap.PrimeComparisons:N0}  ({overlap.PrimeDensity:P2})",
                    body, violet, 788, 821);
                g.DrawString($"Composite rows  {overlap.CompositeFlips:N0} / {overlap.CompositeComparisons:N0}  ({overlap.CompositeDensity:P2})",
                    body, white, 788, 851);
                g.DrawString("Counts use valid consecutive quadrant comparisons at integer t.", small, muted, 788, 890);
                g.DrawString("Lime marks prime t. White marks zeta zeros. Amber marks ζ′.", small, muted, 788, 919);
                g.DrawString("Shared height references. The horizontal axis still indexes primes.", small, muted, 788, 949);
            }
            else
            {
                g.DrawString("04   WHAT SURVIVES A CONTROL?", heading, white, 788, 777);
                g.DrawString($"Violet cells: {mesh.FlipCount:N0} / {Rows * count:N0}   ({flipRate:P2})", body, violet, 788, 821);
                g.DrawString($"Rotate axes 22.5°: {rotationRate:P2} of all marker cells change.", body, white, 788, 851);
                g.DrawString($"Reverse order: final product differs by at most {mesh.ReverseError:E1}.", body, white, 788, 881);
                g.DrawString($"Zeta log-tail bound: {bound:F4} rad. Colors above describe finite P.", small, muted, 788, 919);
                g.DrawString("Violet depends on the axes; the endpoint survives reordering.", small, muted, 788, 949);
            }

            for (int q = 0; q < 4; q++)
            {
                using var color = new SolidBrush(Palette[q]);
                g.FillRectangle(color, 38 + q * 161, 1021, 13, 13);
                g.DrawString(new[] { "+real, +imag", "-real, +imag", "-real, -imag", "+real, -imag" }[q], small, muted, 58 + q * 161, 1018);
            }
            g.FillRectangle(violet, 707, 1021, 13, 13);
            g.DrawString("quadrant change", small, muted, 727, 1018);
            g.DrawString("Re(s) > 1  •  sampled finite products  •  no RH conclusion", small, muted, 938, 1018);
            report = $"{count} primes; {Rows} height samples; {timer.ElapsedMilliseconds} ms including drawing. "
                + $"Violet crossings {flipRate:P3}. Axis-rotation marker difference {rotationRate:P3}. "
                + $"Reverse endpoint difference {mesh.ReverseError:E3}. "
                + $"Each prime is a step in log(product): real part changes magnitude; imaginary part changes phase. "
                + $"Wave spacing π/log(p) also occurs for composites. Prime membership comes from the sieve. "
                + $"Gray uses empirical tolerance 1e-12 * max(1, |value|); it is not a certified arithmetic bound. "
                + $"Infinite-product log-tail bound B_N={bound:G6}, excluding roundoff. These are finite-product colors.";
            if (overlay)
                report += $" Prime-height violet density {overlap.PrimeFlips}/{overlap.PrimeComparisons} ({overlap.PrimeDensity:P3}). "
                    + $"Composite-height violet density {overlap.CompositeFlips}/{overlap.CompositeComparisons} ({overlap.CompositeDensity:P3}). "
                    + "The prime, zeta-zero and derivative-zero lines share the height coordinate only.";
            return result;
        }

        private sealed class RowOverlap
        {
            public int PrimeFlips { get; set; }
            public int PrimeComparisons { get; set; }
            public int CompositeFlips { get; set; }
            public int CompositeComparisons { get; set; }
            public double PrimeDensity => PrimeComparisons == 0 ? 0 : (double)PrimeFlips / PrimeComparisons;
            public double CompositeDensity => CompositeComparisons == 0 ? 0 : (double)CompositeFlips / CompositeComparisons;
        }

        private static RowOverlap CountRowOverlaps(Mesh mesh)
        {
            var primeHeights = new HashSet<int>(Primes(40));
            var result = new RowOverlap();
            for (int t = 2; t <= 40; t++)
            {
                int y = 480 - 12 * t;
                bool primeRow = primeHeights.Contains(t);
                for (int x = 1; x < mesh.Primes.Length; x++)
                {
                    int index = y * mesh.Primes.Length + x;
                    if (!mesh.Comparable[index]) continue;
                    if (primeRow)
                    {
                        result.PrimeComparisons++;
                        if (mesh.Flips[index]) result.PrimeFlips++;
                    }
                    else
                    {
                        result.CompositeComparisons++;
                        if (mesh.Flips[index]) result.CompositeFlips++;
                    }
                }
            }
            return result;
        }

        private static void DrawLandmarks(System.Drawing.Graphics g, Rectangle bounds, Font font)
        {
            using var lime = new Pen(Color.FromArgb(165, 190, 255, 102), 1);
            using var limeInk = new SolidBrush(Color.FromArgb(190, 255, 102));
            using var white = new Pen(Color.FromArgb(215, 245, 248, 255), 1) { DashStyle = DashStyle.Dash };
            using var whiteInk = new SolidBrush(Color.FromArgb(245, 248, 255));
            using var amber = new Pen(Color.FromArgb(255, 194, 82), 1) { DashStyle = DashStyle.DashDot };
            using var amberInk = new SolidBrush(Color.FromArgb(255, 194, 82));
            foreach (int prime in Primes(40))
            {
                float y = bounds.Bottom - (float)(prime / HeightMax * bounds.Height);
                g.DrawLine(lime, bounds.Left, y, bounds.Right, y);
                g.DrawString($"p{prime}", font, limeInk, bounds.Right + 3, y - 8);
            }
            foreach (double height in new[] { 14.134725, 21.022040, 25.010858, 30.424876, 32.935062, 37.586178 })
            {
                float y = bounds.Bottom - (float)(height / HeightMax * bounds.Height);
                g.DrawLine(white, bounds.Left, y, bounds.Right, y);
                g.DrawString($"ζ  {height:F3}", font, whiteInk, bounds.Left + 8, y - 17);
            }
            float derivativeY = bounds.Bottom - (float)(23.298320 / HeightMax * bounds.Height);
            g.DrawLine(amber, bounds.Left, derivativeY, bounds.Right, derivativeY);
            g.DrawString("ζ′  23.298", font, amberInk, bounds.Left + 8, derivativeY - 17);
        }

        private static void DrawMesh(System.Drawing.Graphics g, Mesh mesh, int[] pixels, Rectangle bounds, int selectedPrime, Font font, Brush ink)
        {
            using var bitmap = Pixels(mesh.Primes.Length, Rows, pixels);
            g.InterpolationMode = InterpolationMode.NearestNeighbor;
            g.PixelOffsetMode = PixelOffsetMode.Half;
            g.DrawImage(bitmap, bounds, new Rectangle(0, 0, bitmap.Width, bitmap.Height), GraphicsUnit.Pixel);
            g.PixelOffsetMode = PixelOffsetMode.Default;
            using var grid = new Pen(Color.FromArgb(90, 220, 228, 250));
            using var selected = new Pen(Color.FromArgb(180, 255, 255, 255));
            for (int t = 0; t <= 40; t += 10)
            {
                float y = bounds.Bottom - (float)t / 40 * bounds.Height;
                g.DrawString(t.ToString(), font, ink, bounds.Left - 28, y - 9);
                g.DrawLine(grid, bounds.Left - 5, y, bounds.Left, y);
            }
            g.DrawString("t", font, ink, bounds.Left - 27, bounds.Top - 22);
            for (int j = 0; j <= 5; j++)
            {
                int index = (int)Math.Round((mesh.Primes.Length - 1) * j / 5.0);
                float x = bounds.Left + (index + 0.5f) / mesh.Primes.Length * bounds.Width;
                g.DrawString(mesh.Primes[index].ToString(), font, ink, x - 10, bounds.Bottom + 7);
            }
            int selectedIndex = Array.IndexOf(mesh.Primes, selectedPrime);
            float selectedX = bounds.Left + (selectedIndex + 0.5f) / mesh.Primes.Length * bounds.Width;
            g.DrawLine(selected, selectedX, bounds.Top, selectedX, bounds.Bottom);
        }

        private static void DrawWave(System.Drawing.Graphics g, double sigma, int prime, Rectangle bounds, Font font, Brush ink)
        {
            double amplitude = Math.Asin(Math.Pow(prime, -sigma));
            double controlAmplitude = Math.Asin(Math.Pow(12, -sigma));
            using var wave = new Pen(Violet, 2);
            using var control = new Pen(Color.FromArgb(150, 160, 177), 1) { DashStyle = DashStyle.Dash };
            using var zero = new Pen(Color.FromArgb(70, 85, 110));
            g.DrawLine(zero, bounds.Left, bounds.Top + bounds.Height / 2, bounds.Right, bounds.Top + bounds.Height / 2);
            var points = new PointF[bounds.Width + 1];
            var comparison = new PointF[points.Length];
            for (int i = 0; i < points.Length; i++)
            {
                double t = 8.0 * i / bounds.Width;
                double value = Contribution(new Complex(sigma, t), prime).Imaginary / amplitude;
                double other = Contribution(new Complex(sigma, t), 12).Imaginary / controlAmplitude;
                points[i] = new PointF(bounds.Left + i, (float)(bounds.Top + bounds.Height * (0.5 - 0.44 * value)));
                comparison[i] = new PointF(bounds.Left + i, (float)(bounds.Top + bounds.Height * (0.5 - 0.44 * other)));
            }
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.DrawLines(control, comparison);
            g.DrawLines(wave, points);
            g.SmoothingMode = SmoothingMode.None;
            for (int t = 0; t <= 8; t += 2) g.DrawString(t.ToString(), font, ink, bounds.Left + t * bounds.Width / 8 - 4, bounds.Bottom + 2);
            g.DrawString("phase turn vs t, scaled per curve", font, ink, bounds.Left, bounds.Top - 23);
        }

        private static Complex Product(Complex s, int[] primes) => primes.Aggregate(Complex.One,
            (value, p) => value / (1 - Complex.Exp(-s * Math.Log(p))));

        private static Complex Grouped(Complex[] factors, int start, int count)
        {
            if (count == 1) return factors[start];
            if (count == 0) return Complex.One;
            int half = count / 2;
            return Grouped(factors, start, half) * Grouped(factors, start + half, count - half);
        }

        private static Complex ZetaReference(Complex s, int n)
        {
            Complex sum = Complex.Zero;
            for (int k = 1; k < n; k++) sum += Complex.Pow(k, -s);
            sum += Complex.Pow(n, 1 - s) / (s - 1) + 0.5 * Complex.Pow(n, -s);
            double[] b = { 1.0 / 6, -1.0 / 30, 1.0 / 42, -1.0 / 30, 5.0 / 66, -691.0 / 2730, 7.0 / 6, -3617.0 / 510 };
            for (int k = 1; k <= b.Length; k++)
            {
                Complex rising = Complex.One;
                for (int j = 0; j < 2 * k - 1; j++) rising *= s + j;
                double factorial = 1;
                for (int j = 2; j <= 2 * k; j++) factorial *= j;
                sum += b[k - 1] / factorial * rising * Complex.Pow(n, -s - 2 * k + 1);
            }
            return sum;
        }

        private static void Require(bool condition, string name)
        {
            if (!condition) throw new InvalidOperationException("Prime-phase check failed: " + name);
        }

        // defines: graph.primes.phase.acceptance
        public static object Verify()
        {
            var values = new List<object>();
            foreach (double t in new[] { 0.0, 14.134725141734694, 23.298320492762855 })
            {
                Complex s = new Complex(2, t);
                Complex reference = ZetaReference(s, 64);
                Require((reference - ZetaReference(s, 32)).Magnitude < 1e-12, "reference cross-check");
                if (t == 0) Require((reference - Math.PI * Math.PI / 6).Magnitude < 1e-12, "real reference");
                double priorBound = double.PositiveInfinity;
                foreach (int cutoff in new[] { 32, 128, 512, 2048 })
                {
                    int[] primes = Primes(cutoff);
                    Complex direct = Product(s, primes);
                    Complex reverse = Product(s, primes.Reverse().ToArray());
                    Complex log = primes.Aggregate(Complex.Zero, (sum, p) => sum + Contribution(s, p));
                    Complex exponentiated = Complex.Exp(log);
                    Complex grouped = Grouped(primes.Select(p => 1 / (1 - Complex.Exp(-s * Math.Log(p)))).ToArray(), 0, primes.Length);
                    double methodError = Math.Max((direct - reverse).Magnitude, Math.Max((direct - grouped).Magnitude, (direct - exponentiated).Magnitude));
                    Require(methodError < 1e-12, "four computation methods");
                    double bound = TailBound(s.Real, cutoff);
                    Require(bound < priorBound, "decreasing log-tail bound");
                    priorBound = bound;
                    double productBound = direct.Magnitude * (Math.Exp(bound) - 1);
                    Require((direct - reference).Magnitude <= productBound + 1e-12, "observed product error");
                    Require((log - Complex.Log(reference)).Magnitude <= bound + 1e-12, "analytic-log reference at sigma=2");
                    values.Add(new { sigma = 2, t, cutoff, real = direct.Real, imaginary = direct.Imaginary,
                        logReal = log.Real, logImaginary = log.Imaginary, referenceReal = reference.Real,
                        referenceImaginary = reference.Imaginary, observedError = (direct - reference).Magnitude,
                        logTailBound = bound, productBound, methodError });
                }
            }
            Require(Primes(512).Length == 97 && Primes(2048).Length == 309, "sieve counts");
            Require(Quadrant(Complex.One) == 0 && Quadrant(Complex.ImaginaryOne) == 1
                && Quadrant(-Complex.One) == 2 && Quadrant(-Complex.ImaginaryOne) == 3, "half-open exact axes");
            Require(Quadrant(Complex.Zero) == -1 && Quadrant(new Complex(1, 1e-14), 0, 1e-12) == -1, "uncertain quadrant");
            Require(Quadrant(new Complex(1, 1e-6)) == 0 && Quadrant(new Complex(1, -1e-6)) == 3, "both sides of axis");
            foreach (double angle in new[] { -8.1, -Math.PI - 1e-7, Math.PI + 1e-7, 8.1 })
            {
                Complex log = new Complex(0.4, angle);
                Complex wrapped = Complex.Log(Complex.Exp(log));
                double turns = (log.Imaginary - wrapped.Imaginary) / Tau;
                Require(Math.Abs(turns - Math.Round(turns)) < 1e-12 && Math.Abs(log.Real - wrapped.Real) < 1e-12, "phase wrap");
            }
            foreach (double sigma in new[] { 1.0, 0.5, double.NaN })
            {
                bool rejected = false;
                try { Contribution(new Complex(sigma, 10), 2); } catch (ArgumentOutOfRangeException) { rejected = true; }
                Require(rejected, "domain rejection");
            }
            int latticeChecks = 0;
            foreach (int p in Primes(512))
                for (int k = 1; k <= 10; k++)
                {
                    double t = k * Math.PI / Math.Log(p);
                    Require(Math.Abs(Contribution(new Complex(1.2, t), p).Imaginary) < 1e-13, "predicted phase crossings");
                    latticeChecks++;
                }
            Mesh coarse = Calculate(1.2, 512, 0, false, 241);
            Mesh fine = Calculate(1.2, 512, 0, false, 481);
            Mesh finer = Calculate(1.2, 512, 0, false, 961);
            double coarseRate = (double)coarse.FlipCount / coarse.Flips.Length;
            double fineRate = (double)fine.FlipCount / fine.Flips.Length;
            double finerRate = (double)finer.FlipCount / finer.Flips.Length;
            Require(Math.Abs(fineRate - finerRate) < 0.002, "refined marker rate");
            int newMidpointFeatures = 0;
            for (int y = 1; y < 481; y += 2)
                for (int x = 0; x < fine.Primes.Length; x++)
                    if (fine.Flips[y * fine.Primes.Length + x] != coarse.Flips[(y / 2) * fine.Primes.Length + x]) newMidpointFeatures++;
            Mesh backwards = Calculate(1.2, 512, 0, true, 481);
            Require(fine.ReverseError < 1e-12 && backwards.ReverseError < 1e-12, "permutation endpoint");
            Require(fine.RotatedDifferences > 0, "palette rotation control");
            RowOverlap baselineRows = CountRowOverlaps(fine);
            RowOverlap rotatedRows = CountRowOverlaps(Calculate(1.2, 512, 22.5, false, 481));
            RowOverlap reversedRows = CountRowOverlaps(backwards);
            Require(baselineRows.PrimeFlips == 0 && baselineRows.PrimeComparisons == 1152
                && baselineRows.CompositeFlips == 15 && baselineRows.CompositeComparisons == 2592,
                "default integer-height overlays");
            Require(rotatedRows.PrimeFlips == 2 && rotatedRows.CompositeFlips == 9,
                "rotated integer-height overlays");
            Require(reversedRows.PrimeFlips == 152 && reversedRows.CompositeFlips == 368,
                "reversed integer-height overlays");
            return new { status = "passed", traceId = "graph.primes.phase.acceptance", cases = values,
                overlays = new { baseline = baselineRows, rotated22_5Degrees = rotatedRows, reverseOrder = reversedRows,
                    heights = "Integer t from 2 through 40, x >= 1, valid consecutive quadrant comparisons only." },
                latticeChecks, refinement = new { coarseRate, fineRate, finerRate, newMidpointFeatures,
                    rows = new[] { 241, 481, 961 }, note = "Midpoint markers compared with the preceding coarse row; this is not a count of hidden crossings. Finite sampling does not certify every crossing." },
                controls = new { rotatedMarkerDifferenceFraction = (double)fine.RotatedDifferences / fine.Flips.Length,
                    reverseEndpointError = fine.ReverseError, reverseOrderFlipRate = (double)backwards.FlipCount / backwards.Flips.Length },
                limitation = "Numerical spot checks, empirical 1e-12 allowance; no directed-rounding certification or RH conclusion." };
        }

        public static void Export(string pngPath, double sigma = 1.2, int cutoff = 512, double basisDegrees = 0,
            int selectedPrime = 13, bool reverse = false, bool overlay = false)
        {
            using var image = Render(sigma, cutoff, basisDegrees, selectedPrime, reverse, out string report, overlay);
            image.Save(pngPath, ImageFormat.Png);
            File.WriteAllText(Path.ChangeExtension(pngPath, ".txt"), report);
            var evidence = JsonSerializer.Deserialize<Dictionary<string, object>>(JsonSerializer.Serialize(Verify()));
            evidence["renderParameters"] = new { sigma, cutoff, basisDegrees, selectedPrime, reverse, overlay, rows = Rows, heightMax = HeightMax };
            evidence["verificationParameters"] = new
            {
                mesh = new { sigma = 1.2, cutoff = 512, basisDegrees = 0, reverse = false, rows = Rows },
                referenceCases = new { sigma = 2.0, cutoffs = new[] { 32, 128, 512, 2048 },
                    heights = new[] { 0.0, 14.134725141734694, 23.298320492762855 } }
            };
            File.WriteAllText(Path.ChangeExtension(pngPath, ".values.json"), JsonSerializer.Serialize(evidence, new JsonSerializerOptions { WriteIndented = true }));
        }
    }
}
