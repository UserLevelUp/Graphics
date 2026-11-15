using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace Graphics
{
    // defines: graph.primes.function
    // consumer: graph.primes.range100.certificate
    internal static class PrimalityFunctionExperiment
    {
        internal const int WilsonLimit = 100000;
        private static readonly Color Background = Color.FromArgb(13, 18, 30);
        private static readonly Color Panel = Color.FromArgb(24, 32, 49);
        private static readonly Color Ink = Color.FromArgb(238, 244, 252);
        private static readonly Color Muted = Color.FromArgb(181, 196, 216);
        private static readonly Color Violet = Color.FromArgb(176, 117, 228);
        private static readonly Color Amber = Color.FromArgb(244, 193, 85);

        internal sealed class WilsonResult
        {
            public bool available { get; set; }
            public string reason { get; set; }
            public int? factorialMod { get; set; }
            public int? residue { get; set; }
            public int? indicator { get; set; }
            public int multiplications { get; set; }
            public bool stoppedAtZero { get; set; }
            public double? phaseDegrees { get; set; }
        }

        internal sealed class Sample
        {
            public int n { get; set; }
            public int indicator { get; set; }
            public string classification { get; set; }
            public int? trialDivisor { get; set; }
            public int trialChecks { get; set; }
            public WilsonResult wilson { get; set; }
        }

        internal static Sample Trial(int n)
        {
            if (n < 0) throw new ArgumentOutOfRangeException(nameof(n), "Use a nonnegative Int32 candidate.");
            var result = new Sample { n = n, indicator = 0, classification = "neither" };
            if (n < 2) return result;
            for (int divisor = 2; divisor <= n / divisor; divisor++)
            {
                result.trialChecks++;
                if (n % divisor == 0)
                {
                    result.classification = "composite";
                    result.trialDivisor = divisor;
                    return result;
                }
            }
            result.indicator = 1;
            result.classification = "prime";
            return result;
        }

        internal static WilsonResult Wilson(int n)
        {
            if (n < 0) throw new ArgumentOutOfRangeException(nameof(n));
            if (n < 2) return new WilsonResult { available = false, reason = "Wilson domain begins at 2; 0 and 1 are neither prime nor composite." };
            if (n > WilsonLimit) return new WilsonResult { available = false, reason = "Wilson display limit is 100000; exact trial classification remains available." };
            int accumulator = 1;
            int multiplications = 0;
            bool stopped = false;
            for (int factor = 2; factor < n; factor++)
            {
                accumulator = (int)((long)accumulator * factor % n);
                multiplications++;
                // Remaining factors cannot change a zero modular product.
                if (accumulator == 0) { stopped = true; break; }
            }
            int residue = (accumulator + 1) % n;
            return new WilsonResult
            {
                available = true,
                factorialMod = accumulator,
                residue = residue,
                indicator = 1 / (1 + residue), // Exact INTEGER division; no floating-point decision.
                multiplications = multiplications,
                stoppedAtZero = stopped,
                phaseDegrees = 360.0 * residue / n
            };
        }

        internal static Sample Evaluate(int n)
        {
            Sample sample = Trial(n);
            sample.wilson = Wilson(n);
            if (sample.wilson.available && sample.wilson.indicator != sample.indicator)
                throw new InvalidOperationException("Wilson and trial classification disagree at " + n);
            return sample;
        }

        private static void Require(bool condition, string message)
        {
            if (!condition) throw new InvalidOperationException("Primality-function verification failed: " + message);
        }

        // defines: graph.primes.function.verify
        internal static object Verify()
        {
            var timer = Stopwatch.StartNew();
            const int upper = 100000;
            // Independent sieve oracle is verification-only; Trial and Wilson never receive it.
            var composite = new bool[upper + 1];
            for (int p = 2; p <= upper / p; p++)
                if (!composite[p])
                    for (int multiple = p * p; multiple <= upper; multiple += p) composite[multiple] = true;
            int primeCount = 0;
            for (int n = 0; n <= upper; n++)
            {
                bool expected = n >= 2 && !composite[n];
                Sample sample = Trial(n);
                Require(sample.indicator == (expected ? 1 : 0), "trial/sieve " + n);
                Require(sample.classification == (n < 2 ? "neither" : expected ? "prime" : "composite"), "class " + n);
                if (expected) primeCount++;
                if (sample.trialDivisor.HasValue)
                    Require(sample.trialDivisor.Value > 1 && sample.trialDivisor.Value < n && n % sample.trialDivisor.Value == 0, "factor witness " + n);
            }
            Require(primeCount == 9592, "prime count through 100000");
            for (int n = 0; n <= 2000; n++)
            {
                WilsonResult result = Wilson(n);
                Require(result.available == (n >= 2), "Wilson domain " + n);
                if (result.available) Require(result.indicator == (!composite[n] ? 1 : 0), "Wilson/sieve " + n);
            }
            int[] controls = { 0, 1, 2, 3, 4, 9, 25, 49, 96, 97, 121, 341, 561, 1105, 1729, 2047 };
            foreach (int n in controls)
            {
                Sample sample = Evaluate(n);
                Require(sample.indicator == (n >= 2 && !composite[n] ? 1 : 0), "control " + n);
            }
            Require(Wilson(4).residue == 3, "n=4 exception");
            Require(Wilson(96).factorialMod == 0 && Wilson(96).residue == 1, "n=96 residue");
            Require(Wilson(97).factorialMod == 96 && Wilson(97).residue == 0, "n=97 residue");
            Require(!Evaluate(WilsonLimit + 1).wilson.available, "Wilson upper limit");
            Sample largest = Evaluate(int.MaxValue);
            Require(largest.indicator == 1 && !largest.wilson.available, "Int32 maximum / overflow-safe divisor loop");
            bool negativeRejected = false;
            try { Evaluate(-1); } catch (ArgumentOutOfRangeException) { negativeRejected = true; }
            Require(negativeRejected, "negative input rejection");
            timer.Stop();
            return new
            {
                status = "passed", traceId = "graph.primes.function.verify",
                trialRange = new { lower = 0, upper, integers = upper + 1, primeCount },
                wilsonRange = new { lower = 0, upper = 2000, integers = 2001 },
                controls, exactResidues = new { n4 = 3, n96 = 1, n97 = 0 },
                integerMaximumControl = int.MaxValue, negativeRejected,
                elapsedMilliseconds = timer.Elapsed.TotalMilliseconds,
                scope = "Exact integer checks against an independent sieve. Timing is one verification run, not a benchmark or asymptotic speed claim."
            };
        }

        private static void Card(System.Drawing.Graphics g, Rectangle rectangle, string title, Sample sample,
            Font heading, Font body, Font math, Brush ink, Brush muted)
        {
            using var panel = new SolidBrush(Panel);
            using var accent = new SolidBrush(sample.indicator == 1 ? Violet : Amber);
            g.FillRectangle(panel, rectangle);
            g.DrawString(title, heading, accent, rectangle.X + 24, rectangle.Y + 15);
            g.DrawString(sample.n == 96 ? "96 = 2 × 48: composite" : "97 mod (2, 3, 5, 7) = (1, 1, 2, 6): prime", body, ink, rectangle.X + 24, rectangle.Y + 63);
            g.DrawString($"({sample.n} − 1)! mod {sample.n} = {sample.wilson.factorialMod}", math, ink, rectangle.X + 24, rectangle.Y + 109);
            g.DrawString($"R({sample.n}) = {sample.wilson.residue}     f({sample.n}) = {sample.wilson.indicator}", math, accent, rectangle.X + 24, rectangle.Y + 157);
        }

        internal static Bitmap Render(Sample selected, Sample[] rows)
        {
            var bitmap = new Bitmap(1920, 1080);
            using var g = System.Drawing.Graphics.FromImage(bitmap);
            g.Clear(Background);
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            using var title = new Font("Segoe UI", 42, FontStyle.Bold, GraphicsUnit.Pixel);
            using var heading = new Font("Segoe UI", 29, FontStyle.Bold, GraphicsUnit.Pixel);
            using var body = new Font("Segoe UI", 24, FontStyle.Regular, GraphicsUnit.Pixel);
            using var small = new Font("Segoe UI", 20, FontStyle.Regular, GraphicsUnit.Pixel);
            using var math = new Font("Cambria Math", 34, FontStyle.Regular, GraphicsUnit.Pixel);
            using var number = new Font("Segoe UI", 20, FontStyle.Bold, GraphicsUnit.Pixel);
            using var ink = new SolidBrush(Ink);
            using var muted = new SolidBrush(Muted);
            using var panel = new SolidBrush(Panel);
            using var violet = new SolidBrush(Violet);
            using var amber = new SolidBrush(Amber);
            g.DrawString("AN EXACT PRIMALITY FUNCTION", title, ink, 40, 23);
            g.DrawString("A candidate goes in. Exact integer arithmetic decides. No previous-prime list is supplied.", body, muted, 43, 87);

            g.FillRectangle(panel, 40, 143, 1840, 180);
            g.DrawString("Wilson's theorem • integer domain n ≥ 2", heading, ink, 64, 158);
            g.DrawString("R(n) = ((n − 1)! + 1) mod n", math, ink, 65, 207);
            g.DrawString("f(n) = 1 / (1 + R(n))   [integer division]", math, violet, 65, 259);
            g.DrawString($"SELECTED: {selected.n}  •  {selected.classification.ToUpperInvariant()}", heading, ink, 1110, 166);
            string trial = selected.n < 2 ? "0 and 1 are neither prime nor composite."
                : selected.trialDivisor.HasValue ? $"Exact factor: {selected.trialDivisor.Value} × {selected.n / selected.trialDivisor.Value}"
                : $"No factor among {selected.trialChecks:N0} tested divisors.";
            g.DrawString(trial, small, muted, 1112, 212);
            string selectedWilson = selected.wilson.available ? $"Wilson R = {selected.wilson.residue}; f = {selected.wilson.indicator}."
                : selected.n < 2 ? "Define f(0) = f(1) = 0 separately." : "Wilson unavailable above 100,000; trial result shown.";
            g.DrawString(selectedWilson, small, muted, 1112, 249);
            g.DrawString("Wilson is exact, but not a fast large-number shortcut.", small, muted, 1112, 284);

            Card(g, new Rectangle(40, 346, 900, 232), "96 • A COMPOSITE EXAMPLE", rows[96], heading, body, math, ink, muted);
            Card(g, new Rectangle(960, 346, 920, 232), "97 • A PRIME EXAMPLE", rows[97], heading, body, math, ink, muted);

            g.FillRectangle(panel, 40, 600, 875, 398);
            g.DrawString("0–100: computed exact labels", heading, ink, 62, 616);
            using var compositeFill = new SolidBrush(Color.FromArgb(55, 69, 92));
            using var neitherFill = new SolidBrush(Color.FromArgb(82, 85, 95));
            for (int n = 0; n <= 100; n++)
            {
                int x = 65 + n % 11 * 75, y = 666 + n / 11 * 29;
                g.FillRectangle(rows[n].indicator == 1 ? violet : n < 2 ? neitherFill : compositeFill, x, y, 68, 25);
                string text = n.ToString(CultureInfo.InvariantCulture);
                float width = g.MeasureString(text, number).Width;
                g.DrawString(text, number, ink, x + (68 - width) / 2, y - 2);
            }
            g.DrawString("25 primes (violet) • 74 composites • 0 and 1 neither", small, muted, 64, 965);

            g.FillRectangle(panel, 935, 600, 945, 398);
            g.DrawString("Phase illustrates the residue", heading, ink, 959, 616);
            const float cx = 1123, cy = 812, radius = 124;
            using var circle = new Pen(Color.FromArgb(115, 137, 164), 2);
            using var axes = new Pen(Color.FromArgb(70, 87, 111), 1);
            using var primePen = new Pen(Violet, 3);
            using var compositePen = new Pen(Amber, 3);
            g.DrawEllipse(circle, cx - radius, cy - radius, radius * 2, radius * 2);
            g.DrawLine(axes, cx - 144, cy, cx + 144, cy);
            g.DrawLine(axes, cx, cy - 144, cx, cy + 144);
            double angle = Math.PI * rows[96].wilson.phaseDegrees.Value / 180;
            var end96 = new PointF(cx + radius * (float)Math.Cos(angle), cy - radius * (float)Math.Sin(angle));
            g.DrawLine(primePen, cx, cy, cx + radius, cy);
            g.DrawLine(compositePen, new PointF(cx, cy), end96);
            g.FillEllipse(violet, cx + radius - 6, cy - 6, 12, 12);
            g.FillEllipse(amber, end96.X - 5, end96.Y - 5, 10, 10);
            g.DrawString("Same unit circle; true angles shown.", small, muted, 960, 960);
            g.DrawString("W(n) = exp(2πi R(n)/n)", math, ink, 1307, 672);
            g.DrawString("96:  R = 1   →   angle 3.75°", body, amber, 1310, 728);
            g.DrawString("97:  R = 0   →   angle 0°", body, violet, 1310, 771);
            g.DrawString("Prime iff the exact residue R is zero.", small, ink, 1311, 821);
            g.DrawString("Rounded angles never decide primality.", small, muted, 1311, 852);
            g.DrawString("n = 4 control: 3! mod 4 = 2", small, muted, 1311, 901);
            g.DrawString("R(4) = 3, so f(4) = 0.", small, muted, 1311, 932);

            g.DrawString("Established mathematics. No fast nth-prime formula or RH result is claimed.  Trace: graph.primes.function", small, muted, 42, 1026);
            return bitmap;
        }

        // produces: graph.primes.function.export
        internal static void Export(string pngPath, int candidate = 97)
        {
            string path = Path.GetFullPath(pngPath);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            Sample selected = Evaluate(candidate);
            Sample[] rows = Enumerable.Range(0, 101).Select(Evaluate).ToArray();
            int[] examples = { 0, 1, 2, 3, 4, 49, 96, 97, 121, 341, 561, 1105, 1729, 2047 };
            object verification = Verify();
            using var image = Render(selected, rows);
            image.Save(path, ImageFormat.Png);
            var payload = new
            {
                schema = "graph-primality-function-v1", traceId = "graph.primes.function",
                definition = new
                {
                    inputDomain = "Nonnegative Int32 integers; 0 and 1 are neither prime nor composite.",
                    wilsonDomain = "Integer n >= 2; native evaluation capped at 100000.", wilsonLimit = WilsonLimit,
                    residue = "R(n) = ((n-1)! + 1) mod n", indicator = "f(n) = 1 / (1 + R(n)), exact integer division",
                    phase = "W(n)=exp(2*pi*i*R(n)/n); floating phase is illustrative only.",
                    exactDecision = "Trial division for every candidate; agreement with exact Wilson remainder wherever available.",
                    priorPrimeListRequired = false
                },
                selected, examples = examples.Select(Evaluate).ToArray(), rows, verification,
                render = new { width = 1920, height = 1080, paletteMeaning = "Violet means exact prime indicator1; color does not supply an independent prediction." },
                limits = new[] { "Wilson is established mathematics, not a new prime formula.", "No claim of a speedup, direct fast nth-prime formula, or RH proof.", "No floating-point threshold is used for primality.", "The sieve is an independent verification oracle only." }
            };
            File.WriteAllText(Path.ChangeExtension(path, ".json"), JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
            File.WriteAllText(Path.ChangeExtension(path, ".txt"),
                $"Exact primality function: selected n={candidate}, indicator={selected.indicator}, classification={selected.classification}." + Environment.NewLine
                + "R(n)=((n-1)!+1) mod n; f(n)=1/(1+R(n)) using integer division, n>=2. f(0)=f(1)=0 separately." + Environment.NewLine
                + "R(96)=1, f(96)=0; R(97)=0, f(97)=1; R(4)=3, f(4)=0." + Environment.NewLine
                + "Exact trial classifications checked against a sieve on0..100000; Wilson checked on0..2000 plus controls. The sieve is never passed to either candidate function." + Environment.NewLine
                + "Phase is illustrative. Wilson is capped at100000 and is not a fast large-number method. No RH or novelty claim.");
        }
    }
}
