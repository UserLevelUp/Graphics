using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Numerics;

namespace Graphics
{
    // defines: graph.primes.phase.unwrap
    internal static class PrimeUnwrap
    {
        private const double Tau = 2 * Math.PI;
        private const double EndTime = 8;

        internal static double[] Angles(int n, double sigma, int steps)
        {
            if (n < 2 || sigma <= 1 || !double.IsFinite(sigma) || steps < 1)
                throw new ArgumentOutOfRangeException();
            var output = new double[steps + 1];
            double previous = 0;
            for (int i = 1; i <= steps; i++)
            {
                double t = EndTime * i / steps;
                double angle = Complex.Exp(-new Complex(sigma, t) * Math.Log(n)).Phase;
                double difference = angle - previous;
                output[i] = output[i - 1] + Math.Atan2(Math.Sin(difference), Math.Cos(difference));
                previous = angle;
            }
            return output;
        }

        internal static object Verify()
        {
            double maximumError = 0;
            double labelError = 0;
            foreach (int n in new[] { 2, 3, 4, 7, 12, 13, 509, 2039 })
            {
                double[] angles = Angles(n, 1.2, 512);
                for (int i = 0; i < angles.Length; i++)
                    maximumError = Math.Max(maximumError, Math.Abs(angles[i] + EndTime * i / 512 * Math.Log(n)));
                double recovered = Math.Exp(-angles.Last() / EndTime);
                labelError = Math.Max(labelError, Math.Abs(recovered - n) / n);
            }
            if (maximumError > 1e-10 || labelError > 1e-12) throw new InvalidOperationException("Unwrapping disagrees with the exact angle.");
            double coarseError = Math.Abs(Angles(13, 1.2, 1).Last() + EndTime * Math.Log(13));
            if (coarseError < Tau) throw new InvalidOperationException("The undersampled control did not miss a turn.");
            return new { status = "passed", traceId = "graph.primes.phase.unwrap", maximumAngleError = maximumError,
                maximumRecoveredLabelRelativeError = labelError, coarseOneStepError = coarseError,
                samples = 513, endTime = EndTime, condition = "Adjacent true phase changes must be below pi for this unwrap algorithm.",
                interpretation = "The straight slope recovers the supplied integer label; composites behave the same way. This does not discover or classify primes." };
        }

        public static Bitmap Render(double sigma, int prime, out string report)
        {
            Verify();
            double[] angles = Angles(prime, sigma, 512);
            double[] control = Angles(12, sigma, 512);
            double maximumError = Enumerable.Range(0, angles.Length)
                .Max(i => Math.Abs(angles[i] + EndTime * i / 512 * Math.Log(prime)));
            var image = new Bitmap(1320, 650);
            using var g = System.Drawing.Graphics.FromImage(image);
            g.Clear(Color.FromArgb(12, 15, 28));
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            using var title = new Font("Segoe UI", 29, FontStyle.Bold, GraphicsUnit.Pixel);
            using var heading = new Font("Segoe UI", 18, FontStyle.Bold, GraphicsUnit.Pixel);
            using var body = new Font("Segoe UI", 15, FontStyle.Regular, GraphicsUnit.Pixel);
            using var small = new Font("Segoe UI", 13, FontStyle.Regular, GraphicsUnit.Pixel);
            using var white = new SolidBrush(Color.FromArgb(236, 240, 251));
            using var muted = new SolidBrush(Color.FromArgb(160, 176, 200));
            using var violet = new SolidBrush(Color.FromArgb(205, 133, 255));
            using var panel = new SolidBrush(Color.FromArgb(22, 27, 45));
            using var purplePen = new Pen(violet, 2.5f);
            using var grayPen = new Pen(Color.FromArgb(165, 176, 195), 1.7f) { DashStyle = DashStyle.Dash };
            using var grid = new Pen(Color.FromArgb(54, 66, 88));
            g.DrawString("UNWRAPPING THE PRIME FACTORS", title, white, 30, 25);
            g.DrawString($"z(t) = {prime}^(-σ-it). Follow the angle through every turn, then lay it on a straight axis.", body, muted, 32, 72);
            g.DrawString($"Selected p = {prime}    •    σ = {sigma:F2}    •    gray control n = 12 (composite)    •    513 samples from t = 0 to 8", small, violet, 32, 107);

            g.FillRectangle(panel, 28, 148, 342, 326);
            g.FillRectangle(panel, 390, 148, 526, 326);
            g.FillRectangle(panel, 936, 148, 356, 326);
            g.DrawString("01   WRAPPED MOTION", heading, white, 46, 164);
            g.DrawString("02   CONTINUOUS ANGLE", heading, white, 408, 164);
            g.DrawString("03   RECOVER THE LABEL", heading, white, 954, 164);
            float cx = 199, cy = 314, radius = 100;
            g.DrawLine(grid, cx - 125, cy, cx + 125, cy);
            g.DrawLine(grid, cx, cy - 118, cx, cy + 118);
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.DrawEllipse(purplePen, cx - radius, cy - radius, 2 * radius, 2 * radius);
            g.DrawEllipse(grayPen, cx - 88, cy - 88, 176, 176);
            for (int i = 0; i <= 5; i++)
            {
                double t = i * 0.3;
                double angle = -t * Math.Log(prime);
                float x = cx + radius * (float)Math.Cos(angle), y = cy - radius * (float)Math.Sin(angle);
                g.FillEllipse(violet, x - 4, y - 4, 8, 8);
                g.DrawString(t.ToString("0.0"), small, white, x + 6, y - 7);
            }
            g.DrawString("Dots show t. Both radii are normalized.", small, muted, 46, 446);
            var plot = new Rectangle(442, 213, 446, 207);
            double lower = -Math.Ceiling(Math.Max(Math.Log(prime), Math.Log(12)) * EndTime / Tau) * Tau;
            for (double theta = 0; theta >= lower; theta -= Tau)
            {
                float y = plot.Top + (float)(theta / lower) * plot.Height;
                g.DrawLine(grid, plot.Left, y, plot.Right, y);
                g.DrawString(theta == 0 ? "0" : $"-{Math.Round(-theta / Math.PI):F0}π", small, muted, plot.Left - 40, y - 8);
            }
            PointF[] Points(double[] values) => Enumerable.Range(0, values.Length)
                .Select(i => new PointF(plot.Left + (float)i / (values.Length - 1) * plot.Width,
                    plot.Top + (float)(values[i] / lower) * plot.Height)).ToArray();
            g.DrawLines(grayPen, Points(control));
            g.DrawLines(purplePen, Points(angles));
            for (int t = 0; t <= 8; t += 2)
                g.DrawString(t.ToString(), small, muted, plot.Left + t * plot.Width / 8 - 4, plot.Bottom + 6);
            g.DrawString($"Exact slope = -log({prime}) = {-Math.Log(prime):F6}", small, violet, 408, 446);
            g.DrawString("n          turn period       recovered n", small, muted, 954, 213);
            int row = 0;
            foreach (int n in new[] { 2, 3, 4, 7, 12, prime }.Distinct())
            {
                double[] sampled = Angles(n, sigma, 512);
                double slope = -sampled.Last() / EndTime;
                double recovered = Math.Exp(slope);
                bool isPrime = PrimePhaseExperiment.Primes(Math.Max(n, 13)).Contains(n);
                g.DrawString($"{n,-7}    {Tau / slope,8:F4}        {recovered:F3}", body, isPrime ? violet : muted, 954, 244 + 31 * row++);
            }
            g.DrawString("Composite labels 4 and 12 work too.", small, muted, 954, 446);

            g.DrawString("The exact formula needs no previous samples:  θ(t) = -t log(n).", heading, white, 32, 504);
            g.DrawString($"The sampled unwrap matches it within {maximumError:E1} radians here. Coarse sampling can miss whole turns.", body, muted, 32, 542);
            g.DrawString("A straight slope reconstructs the supplied n. It does not establish primality or the location of zeta zeros.", body, muted, 32, 575);
            g.DrawString("These are individual factors. The local mesh uses Δlog P = -Log(1-z); the full zeta curve is a different object.", small, muted, 32, 612);
            report = $"Unwrapped {angles.Length} samples. Max angle error {maximumError:E3}. "
                + $"The exact expression is direct. Numerical unwrapping uses previous samples and requires phase steps below π. "
                + "Composite controls unwrap too; this is reconstruction from known inputs, not a primality test.";
            return image;
        }
    }
}
