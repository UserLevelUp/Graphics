using System;
using System.Drawing;
using System.Linq;
using System.Numerics;
using System.Threading.Tasks;

namespace Graphics
{
    // defines: graph.zeta.origins
    // consumer: graph.zeta.overwrite
    internal static class ZetaOrigins
    {
        private const double Radius = 0.08;
        private const int PanelSize = 256;
        private static readonly double[] Radii = { Radius, 0.04, 0.01 };

        private sealed class Evaluator
        {
            private readonly double[] weights;
            private readonly double[] logs;

            public Evaluator(int terms)
            {
                weights = ZetaExperiment.BuildEtaWeights(terms);
                logs = Enumerable.Range(1, terms).Select(n => Math.Log(n)).ToArray();
            }

            public (Complex Value, Complex First, Complex Second) At(Complex s)
            {
                Complex eta = Complex.Zero;
                Complex first = Complex.Zero;
                Complex second = Complex.Zero;
                for (int n = 0; n < weights.Length; n++)
                {
                    Complex term = weights[n] * Complex.Exp(-s * logs[n]);
                    eta += term;
                    first -= logs[n] * term;
                    second += logs[n] * logs[n] * term;
                }

                double logTwo = Math.Log(2);
                Complex q = Complex.Exp((1 - s) * logTwo);
                Complex denominator = 1 - q;
                Complex value = eta / denominator;
                Complex derivative = (first - value * logTwo * q) / denominator;
                Complex curvature = (second + value * logTwo * logTwo * q
                    - 2 * derivative * logTwo * q) / denominator;
                return (value, derivative, curvature);
            }

            public Complex CriticalPoint()
            {
                var point = new Complex(2.4, 23.3);
                for (int i = 0; i < 12; i++)
                {
                    var sample = At(point);
                    if (sample.First.Magnitude < 1e-14)
                        return point;
                    if (sample.Second.Magnitude < 1e-12)
                        throw new InvalidOperationException("Critical-point search lost its derivative.");
                    point -= sample.First / sample.Second;
                }
                throw new InvalidOperationException("Critical-point search did not converge.");
            }
        }

        public static Bitmap Render(out string report)
        {
            var evaluator = new Evaluator(96);
            var comparison = new Evaluator(128);
            Complex critical = evaluator.CriticalPoint();
            Complex check = comparison.CriticalPoint();
            if ((critical - check).Magnitude > 1e-9)
                throw new InvalidOperationException("Changing the evaluator length moved the candidate.");

            var centers = new[]
            {
                new Complex(0.5, 14.134725141734694),
                critical,
                critical + 0.01
            };
            string[] titles = { "Simple zeta zero", "Zeta derivative zero", "Center moved right by 0.01" };
            string[] turns = new string[centers.Length];
            for (int c = 0; c < centers.Length; c++)
            {
                Complex center = centers[c];
                Complex anchor = evaluator.At(center).Value;
                turns[c] = string.Join(" / ", Radii.Select(radius => {
                    Func<Complex, Complex> local = s => evaluator.At(s).Value - anchor;
                    int coarse = Winding(local, center, radius, 128);
                    int fine = Winding(local, center, radius, 256);
                    int backward = Winding(local, center, radius, -256);
                    Complex otherAnchor = comparison.At(center).Value;
                    int other = Winding(s => comparison.At(s).Value - otherAnchor, center, radius, 256);
                    if (coarse != fine || backward != -fine || fine != other)
                        throw new InvalidOperationException("A local loop failed its refinement check.");
                    return fine.ToString();
                }));
            }
            if (turns[0] != "1 / 1 / 1" || turns[1] != "2 / 2 / 2" || turns[2] != "2 / 2 / 1")
                throw new InvalidOperationException("The local winding controls gave unexpected results.");

            CheckTranslationInvariance();
            var candidate = evaluator.At(critical);
            report = $"Local winding at radii 0.08 / 0.04 / 0.01{Environment.NewLine}"
                + string.Join(Environment.NewLine, titles.Select((title, i) => $"{title}: {turns[i]}"))
                + $"{Environment.NewLine}Derivative candidate: {critical.Real:F12} + {critical.Imaginary:F12}i."
                + $"{Environment.NewLine}|zeta'| = {candidate.First.Magnitude:E3}; |zeta| = {candidate.Value.Magnitude:E3}."
                + $"{Environment.NewLine}96/128-term candidate difference = {(critical - check).Magnitude:E3}."
                + $"{Environment.NewLine}128/256 samples, reverse direction, and 96/128 terms agree for all nine loops."
                + $"{Environment.NewLine}Affine constant-shift invariance passed at 16,384 dyadic samples.";

            var image = new Bitmap(888, 448);
            using var drawing = System.Drawing.Graphics.FromImage(image);
            drawing.Clear(Color.White);
            using var heading = new Font("Segoe UI", 18, FontStyle.Bold, GraphicsUnit.Pixel);
            using var label = new Font("Segoe UI", 13, FontStyle.Regular, GraphicsUnit.Pixel);
            using var bold = new Font("Segoe UI", 13, FontStyle.Bold, GraphicsUnit.Pixel);
            drawing.DrawString("Every point as its own origin", heading, Brushes.Black, 20, 12);
            drawing.DrawString("Color = quadrant of zeta(s) - zeta(center). Three circles test what survives as the radius shrinks.",
                label, Brushes.Black, 20, 41);

            for (int c = 0; c < centers.Length; c++)
            {
                int left = 20 + 288 * c;
                drawing.DrawString(titles[c], bold, Brushes.Black, left, 72);
                DrawLocal(drawing, evaluator, centers[c], left, 96);
                drawing.DrawString("Turns   " + turns[c], bold, Brushes.Black, left, 362);
            }
            drawing.DrawString("Circle radii   0.08 / 0.04 / 0.01       The derivative zero is at Re(s) = 2.463161869, to the right of the strip.",
                label, Brushes.Black, 20, 393);
            drawing.DrawString("Sampled winding estimates. A nearby center can show an extra turn on a large circle.",
                label, Brushes.Black, 20, 416);
            return image;
        }

        private static void DrawLocal(System.Drawing.Graphics drawing, Evaluator evaluator,
            Complex center, int left, int top)
        {
            var colors = new Color[PanelSize * PanelSize];
            Complex anchor = evaluator.At(center).Value;
            Parallel.For(0, PanelSize, y =>
            {
                for (int x = 0; x < PanelSize; x++)
                {
                    var offset = new Complex((x + 0.5 - PanelSize / 2.0) * 2 * Radius / PanelSize,
                        (PanelSize / 2.0 - y - 0.5) * 2 * Radius / PanelSize);
                    colors[y * PanelSize + x] = ZetaExperiment.PhaseColor(evaluator.At(center + offset).Value - anchor);
                }
            });
            using var bitmap = new Bitmap(PanelSize, PanelSize);
            for (int y = 0; y < PanelSize; y++)
                for (int x = 0; x < PanelSize; x++)
                    bitmap.SetPixel(x, y, colors[y * PanelSize + x]);
            drawing.DrawImageUnscaled(bitmap, left, top);
            using var pen = new Pen(Color.Black, 1.5f);
            float cx = left + PanelSize / 2f;
            float cy = top + PanelSize / 2f;
            foreach (double radius in Radii)
            {
                float r = (float)(radius / Radius * (PanelSize / 2 - 1));
                drawing.DrawEllipse(pen, cx - r, cy - r, r * 2, r * 2);
            }
            drawing.DrawLine(Pens.White, cx - 4, cy, cx + 4, cy);
            drawing.DrawLine(Pens.White, cx, cy - 4, cx, cy + 4);
        }

        private static int Winding(Func<Complex, Complex> function, Complex center, double radius, int samples)
        {
            int count = Math.Abs(samples);
            Complex first = function(center + radius);
            Complex previous = first;
            double turn = 0;
            for (int i = 1; i <= count; i++)
            {
                Complex next = i == count ? first : function(center
                    + Complex.FromPolarCoordinates(radius, 2 * Math.PI * i / samples));
                double increment = (next * Complex.Conjugate(previous)).Phase;
                if (!double.IsFinite(increment) || previous.Magnitude < 1e-10 ||
                    Math.Abs(increment) >= Math.PI / 2)
                    throw new InvalidOperationException("A contour needs finer sampling or more precision.");
                turn += increment;
                previous = next;
            }
            double winding = turn / (2 * Math.PI);
            if (Math.Abs(winding - Math.Round(winding)) > 1e-8)
                throw new InvalidOperationException("The contour failed to close.");
            return (int)Math.Round(winding);
        }

        private static void CheckTranslationInvariance()
        {
            var a = new Complex(0.5, 14.125);
            var b = new Complex(0.625, 14.125);
            var center = new Complex(0.4375, 14.1875);
            for (int y = 0; y < 128; y++)
                for (int x = 0; x < 128; x++)
                {
                    var point = new Complex(x / 128.0, 14 + y / 128.0);
                    if ((point - a) - (center - a) != (point - b) - (center - b))
                        throw new InvalidOperationException("The affine local differences changed.");
                }
        }
    }
}
