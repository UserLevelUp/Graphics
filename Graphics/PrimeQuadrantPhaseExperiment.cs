using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace Graphics
{
    // defines: graph.primes.quadrant_phase
    // consumer: graph.primes.function
    internal static class PrimeQuadrantPhaseExperiment
    {
        internal const int MaximumCandidate = 100000;
        internal static readonly Color[] Palette = {
            Color.FromArgb(176, 117, 228), Color.FromArgb(244, 193, 85),
            Color.FromArgb(56, 209, 186), Color.FromArgb(238, 107, 146)
        };
        private static readonly Color Background = Color.FromArgb(13, 18, 30);
        private static readonly Color Panel = Color.FromArgb(24, 32, 49);
        private static readonly Color Ink = Color.FromArgb(238, 244, 252);
        private static readonly Color Muted = Color.FromArgb(181, 196, 216);

        internal sealed class Sample
        {
            public int n { get; set; }
            public int? factorialMod { get; set; }
            public int? residue { get; set; }
            public int multiplications { get; set; }
            public bool stoppedAtZero { get; set; }
            public int? x { get; set; }
            public int? y { get; set; }
            public int? quadrant { get; set; }
            public int indicator { get; set; }
            public string classification { get; set; }
            public double? phaseDegrees { get; set; }
            public double displayRotationDegrees { get; set; }
            public double? displayPhaseDegrees { get; set; }
            public double? oldNormalizedPhaseDegrees { get; set; }
            public int? boundaryMarginDegrees { get; set; }
        }

        private static double Wrap(double degrees)
        {
            double value = degrees % 360;
            if (value < 0) value += 360;
            // Adding a tiny negative remainder to360 can round up to360.
            return value >= 360 ? 0 : value;
        }

        internal static Sample Evaluate(int n, double displayRotationDegrees = 0)
        {
            if (n < 0 || n > MaximumCandidate)
                throw new ArgumentOutOfRangeException(nameof(n), "Use an integer candidate from 0 through 100000 in this Wilson quadrant mode.");
            if (!double.IsFinite(displayRotationDegrees))
                throw new ArgumentOutOfRangeException(nameof(displayRotationDegrees), "Use a finite display rotation.");
            var sample = new Sample {
                n = n, indicator = 0, classification = "neither",
                displayRotationDegrees = Wrap(displayRotationDegrees)
            };
            if (n < 2) return sample;

            // Compute a raw modular product. No prime labels or prior prime list enter this path.
            int accumulator = 1;
            for (int factor = 2; factor < n; factor++)
            {
                accumulator = (int)((long)accumulator * factor % n);
                sample.multiplications++;
                if (accumulator == 0) { sample.stoppedAtZero = true; break; }
            }
            int residue = (accumulator + 1) % n;
            sample.factorialMod = accumulator;
            sample.residue = residue;

            // F(n) = (1+i) i^R. Exact integer coordinates; no trigonometric decision.
            int turn = residue % 4;
            int[] xs = { 1, -1, -1, 1 };
            int[] ys = { 1, 1, -1, -1 };
            sample.x = xs[turn];
            sample.y = ys[turn];
            sample.quadrant = sample.y > 0 ? (sample.x > 0 ? 1 : 2) : (sample.x < 0 ? 3 : 4);
            sample.indicator = sample.quadrant == 1 ? 1 : 0;
            sample.classification = sample.indicator == 1 ? "prime" : "composite";
            sample.phaseDegrees = 45 + 90 * turn;
            sample.displayPhaseDegrees = Wrap(sample.phaseDegrees.Value + sample.displayRotationDegrees);
            sample.oldNormalizedPhaseDegrees = 360.0 * residue / n;
            sample.boundaryMarginDegrees = 45;
            return sample;
        }

        private static void Require(bool ok, string message)
        {
            if (!ok) throw new InvalidOperationException("Quadrant-phase verification failed: " + message);
        }

        // defines: graph.primes.quadrant_phase.verify
        internal static object Verify()
        {
            const int upper = 2000;
            var composite = new bool[upper + 1];
            for (int p = 2; p <= upper / p; p++)
                if (!composite[p])
                    for (int multiple = p * p; multiple <= upper; multiple += p) composite[multiple] = true;
            int primeCount = 0;
            int[] counts = new int[4];
            for (int n = 0; n <= upper; n++)
            {
                Sample s = Evaluate(n);
                bool expected = n >= 2 && !composite[n];
                Require(s.indicator == (expected ? 1 : 0), "sieve agreement " + n);
                Require(s.classification == (n < 2 ? "neither" : expected ? "prime" : "composite"), "class " + n);
                if (expected) primeCount++;
                if (n < 2) Require(s.quadrant == null && s.residue == null && s.x == null && s.y == null, "outside Wilson domain " + n);
                else
                {
                    Require(s.residue == (expected ? 0 : n == 4 ? 3 : 1), "residue theorem " + n);
                    Require(s.quadrant == (expected ? 1 : n == 4 ? 4 : 2), "quadrant theorem " + n);
                    Require(Math.Abs(s.x.Value) == 1 && Math.Abs(s.y.Value) == 1 && s.boundaryMarginDegrees == 45, "exact point " + n);
                    counts[s.quadrant.Value - 1]++;
                }
            }
            double[] rotations = { -720, -360, -91.5, -45, -double.Epsilon, 0, 45, 89.75, 180, 360, 1000000000000 };
            int[] controls = { 0, 1, 2, 4, 49, 96, 97, 121, 341, 561, 1105, 1729, 2047, 9973, 99991, 100000 };
            foreach (int n in controls)
            {
                Sample baseline = Evaluate(n);
                foreach (double rotation in rotations)
                {
                    Sample rotated = Evaluate(n, rotation);
                    Require(rotated.displayRotationDegrees >= 0 && rotated.displayRotationDegrees < 360, "wrapped display rotation");
                    Require(rotated.x == baseline.x && rotated.y == baseline.y && rotated.quadrant == baseline.quadrant
                        && rotated.indicator == baseline.indicator, "canonical rotation invariance " + n);
                    if (rotated.displayPhaseDegrees.HasValue)
                        Require(rotated.displayPhaseDegrees >= 0 && rotated.displayPhaseDegrees < 360, "wrapped display phase");
                }
            }
            Require(Evaluate(96).phaseDegrees == 135 && Evaluate(97).phaseDegrees == 45 && Evaluate(4).phaseDegrees == 315, "worked examples");
            int rejected = 0;
            foreach (int invalid in new[] { -1, MaximumCandidate + 1, int.MaxValue })
                try { Evaluate(invalid); } catch (ArgumentOutOfRangeException) { rejected++; }
            foreach (double invalid in new[] { double.NaN, double.PositiveInfinity, double.NegativeInfinity })
                try { Evaluate(97, invalid); } catch (ArgumentOutOfRangeException) { rejected++; }
            Require(rejected == 6, "invalid input rejection");
            return new {
                traceId = "graph.primes.quadrant_phase.verify", status = "passed",
                independentOracle = "Sieve used only in verification", lower = 0, upper, primeCount,
                canonicalQuadrantCounts = counts, controls, rotations, invalidInputsRejected = rejected,
                exactCoordinates = true, floatingPointClassification = false,
                scope = "Finite checks support the implementation. The global equivalence follows from Wilson and the composite factorial lemma."
            };
        }

        private static PointF Plot(float cx, float cy, float distance, double degrees)
        {
            double radians = degrees * Math.PI / 180;
            return new PointF(cx + distance * (float)Math.Cos(radians), cy - distance * (float)Math.Sin(radians));
        }

        private static void Centered(System.Drawing.Graphics g, string text, Font font, Brush brush, PointF center)
        {
            SizeF size = g.MeasureString(text, font);
            g.DrawString(text, font, brush, center.X - size.Width / 2, center.Y - size.Height / 2);
        }

        internal static Bitmap Render(int candidate = 97, double displayRotationDegrees = 0)
        {
            Sample selected = Evaluate(candidate, displayRotationDegrees);
            Sample[] rows = Enumerable.Range(0, 101).Select(n => Evaluate(n, displayRotationDegrees)).ToArray();
            var bitmap = new Bitmap(1920, 1080);
            using var g = System.Drawing.Graphics.FromImage(bitmap);
            g.Clear(Background);
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            using var title = new Font("Segoe UI", 42, FontStyle.Bold, GraphicsUnit.Pixel);
            using var heading = new Font("Segoe UI", 28, FontStyle.Bold, GraphicsUnit.Pixel);
            using var body = new Font("Segoe UI", 24, FontStyle.Regular, GraphicsUnit.Pixel);
            using var small = new Font("Segoe UI", 20, FontStyle.Regular, GraphicsUnit.Pixel);
            using var number = new Font("Segoe UI", 20, FontStyle.Bold, GraphicsUnit.Pixel);
            using var math = new Font("Cambria Math", 32, FontStyle.Regular, GraphicsUnit.Pixel);
            using var ink = new SolidBrush(Ink);
            using var muted = new SolidBrush(Muted);
            using var panel = new SolidBrush(Panel);
            using var neutral = new SolidBrush(Color.FromArgb(82, 85, 95));
            g.DrawString("AN EXACT COLOR-QUADRANT PRIME TEST", title, ink, 40, 23);
            g.DrawString("A Wilson remainder turns a complex point. Its exact quadrant supplies the decision.", body, muted, 43, 88);
            g.FillRectangle(panel, 40, 142, 1840, 172);
            g.DrawString("R(n) = ((n − 1)! + 1) mod n", math, ink, 64, 159);
            g.DrawString("F(n) = (1 + i) i", math, ink, 64, 207);
            g.DrawString("R(n)", small, ink, 274, 200);
            g.DrawString("Prime ⇔ Re F(n) > 0 and Im F(n) > 0", math, ink, 64, 257);
            g.DrawString("Exact signs → quadrant → color", heading, ink, 1045, 165);
            g.DrawString("Integer n ≥ 2. Define 0 and 1 as neither separately.", small, muted, 1047, 213);
            g.DrawString("No prior-prime list. No rounded-angle decision.", small, muted, 1047, 251);

            g.FillRectangle(panel, 40, 336, 900, 660);
            g.FillRectangle(panel, 960, 336, 920, 660);
            g.DrawString("One fixed mathematical quadrant system", heading, ink, 63, 353);
            g.DrawString($"View rotation {selected.displayRotationDegrees:G6}°; axes and points turn together.", small, muted, 65, 399);
            const float cx = 490, cy = 665, radius = 190;
            double rotation = selected.displayRotationDegrees;
            for (int q = 0; q < 4; q++)
            {
                using var fill = new SolidBrush(Color.FromArgb(85, Palette[q]));
                g.FillPie(fill, cx - radius, cy - radius, radius * 2, radius * 2, (float)(-rotation - 90 * (q + 1)), 90);
                using var color = new SolidBrush(Palette[q]);
                Centered(g, new[] { "QI", "QII", "QIII", "QIV" }[q], heading, color, Plot(cx, cy, 116, rotation + 45 + 90 * q));
            }
            using var axes = new Pen(Color.FromArgb(170, 190, 213), 2);
            using var outline = new Pen(Color.FromArgb(115, 137, 164), 2);
            g.DrawEllipse(outline, cx - radius, cy - radius, radius * 2, radius * 2);
            g.DrawLine(axes, Plot(cx, cy, radius + 10, rotation), Plot(cx, cy, radius + 10, rotation + 180));
            g.DrawLine(axes, Plot(cx, cy, radius + 10, rotation + 90), Plot(cx, cy, radius + 10, rotation + 270));
            Centered(g, "+Re", small, muted, Plot(cx, cy, radius + 30, rotation));
            Centered(g, "+Im", small, muted, Plot(cx, cy, radius + 30, rotation + 90));
            foreach (int n in new[] { 97, 96, 4 })
            {
                Sample s = rows[n];
                PointF point = Plot(cx, cy, 177, s.displayPhaseDegrees.Value);
                using var color = new SolidBrush(Palette[s.quadrant.Value - 1]);
                using var ray = new Pen(Palette[s.quadrant.Value - 1], 3);
                g.DrawLine(ray, new PointF(cx, cy), point);
                g.FillEllipse(color, point.X - 8, point.Y - 8, 16, 16);
                Centered(g, n.ToString(CultureInfo.InvariantCulture), number, ink,
                    Plot(cx, cy, 203, s.displayPhaseDegrees.Value));
            }
            if (selected.quadrant.HasValue)
            {
                PointF point = Plot(cx, cy, 177, selected.displayPhaseDegrees.Value);
                using var ring = new Pen(Ink, 3);
                g.DrawEllipse(ring, point.X - 14, point.Y - 14, 28, 28);
            }
            g.DrawString("QI violet: primes     QII amber: composites > 4", small, ink, 64, 916);
            g.DrawString("QIII cyan: unused    QIV pink: the composite 4", small, ink, 64, 948);

            using var selectedColor = new SolidBrush(selected.quadrant.HasValue ? Palette[selected.quadrant.Value - 1] : Muted);
            g.DrawString($"SELECTED {candidate}  •  {selected.classification.ToUpperInvariant()}", heading, selectedColor, 984, 353);
            if (selected.quadrant.HasValue)
            {
                g.DrawString($"R = {selected.residue};  F = ({selected.x}, {selected.y});  quadrant {selected.quadrant}", math, ink, 985, 402);
                g.DrawString($"Canonical phase {selected.phaseDegrees}° • nearest boundary is 45° away", small, muted, 988, 452);
            }
            else
            {
                g.DrawString("0 and 1: no Wilson phase; neutral color.", body, ink, 986, 405);
                g.DrawString("The formula's primality domain begins at n = 2.", small, muted, 988, 452);
            }
            g.DrawString("0–100: tiles are colored from exact quadrants", heading, ink, 984, 503);
            for (int n = 0; n <= 100; n++)
            {
                int x = 989 + n % 11 * 78, y = 555 + n / 11 * 31;
                using var color = new SolidBrush(rows[n].quadrant.HasValue ? Palette[rows[n].quadrant.Value - 1] : neutral.Color);
                g.FillRectangle(color, x, y, 71, 27);
                // Dark text provides legible contrast on each of the four bright quadrant colors.
                using var dark = new SolidBrush(Background);
                Centered(g, n.ToString(CultureInfo.InvariantCulture), number, n < 2 ? ink : dark,
                    new PointF(x + 35.5f, y + 13.5f));
            }
            g.DrawString("25 QI primes • 73 QII composites • one QIV (4) • two neutral", small, muted, 986, 884);
            g.DrawString("96: R = 1 → 135°       97: R = 0 → 45°", body, ink, 986, 926);
            g.DrawString("Each final phase is safely inside its canonical quadrant.", small, muted, 986, 964);
            g.DrawString("Wilson-derived phase encoding. No speedup, independent zeta prediction, or RH result is claimed.", small, muted, 42, 1023);
            g.DrawString("graph.primes.quadrant_phase", small, muted, 1518, 1023);
            return bitmap;
        }

        // publish: graph.primes.quadrant_phase.export
        internal static void Export(string pngPath, int candidate = 97, double displayRotationDegrees = 0)
        {
            Sample selected = Evaluate(candidate, displayRotationDegrees);
            string path = Path.GetFullPath(pngPath);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            Sample[] rows = Enumerable.Range(0, 101).Select(n => Evaluate(n, displayRotationDegrees)).ToArray();
            object verification = Verify();
            using var image = Render(candidate, displayRotationDegrees);
            image.Save(path, ImageFormat.Png);
            var payload = new {
                schema = "graph-prime-quadrant-phase-v1", traceId = "graph.primes.quadrant_phase",
                definition = new {
                    inputDomain = "Integer 0..100000; 0 and 1 have no phase and are neither prime nor composite.",
                    mathematicalDomain = "All integers n >= 2; native computation is capped at100000.",
                    residue = "R(n)=((n-1)!+1) mod n", complexPoint = "F(n)=(1+i)*i^R(n)",
                    quadrantDecision = "Exact x>0 and y>0 (quadrant I) iff prime on the mathematical domain.",
                    residueRestriction = "R=0 for primes; R=1 for composites>4; R=3 for n=4.",
                    rotation = "Display only: axes and points rotate together. The decision uses canonical exact coordinates.",
                    noPreviousPrimeList = true, noFloatingPointDecision = true
                },
                selected, rows,
                controls = new[] { 0, 1, 2, 4, 49, 96, 97, 121, 341, 561, 9973, 99991, 100000 }.Select(n => Evaluate(n, displayRotationDegrees)).ToArray(),
                palette = Palette.Select((color, index) => new { quadrant = index + 1, rgb = new[] { (int)color.R, color.G, color.B } }).ToArray(),
                render = new { width = 1920, height = 1080, grid = new { x = 989, y = 555, stepX = 78, stepY = 31, width = 71, height = 27, columns = 11 }, neutralRgb = new[] { 82, 85, 95 } },
                verification,
                limits = new[] {
                    "This is a proved Wilson-derived phase encoding, not an independently discovered zeta rule.",
                    "It retains the cost of the modular factorial; no speedup or RH consequence is claimed.",
                    "Pixel colors and rounded angles are visual evidence only; exact coordinate signs decide.",
                    "The45-degree margin is in phase space. A rendered image must still resolve the point and axes."
                }
            };
            File.WriteAllText(Path.ChangeExtension(path, ".json"), JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
            File.WriteAllText(Path.ChangeExtension(path, ".txt"),
                "F(n)=(1+i)*i^R, R=((n-1)!+1) mod n. Prime iff canonical exact quadrant I, n>=2." + Environment.NewLine
                + $"Selected n={candidate}: {selected.classification}; quadrant={selected.quadrant}; exact F=({selected.x},{selected.y})." + Environment.NewLine
                + "96: R1, F(-1,+1), QII135deg.97: R0, F(+1,+1), QI45deg.4: R3, F(+1,-1), QIV315deg." + Environment.NewLine
                + "Wilson-derived encoding; native cap100000. No independent zeta-phase primality rule, speedup, or RH result.");
        }
    }
}
