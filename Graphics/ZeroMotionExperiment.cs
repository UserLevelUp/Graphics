using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Text.Json;

namespace Graphics
{
    // defines: graph.zeros.motion.model
    internal static class ZeroMotionExperiment
    {
        private const double Tau = 2 * Math.PI;
        private const double Extent = 2;
        private static readonly Color Background = Color.FromArgb(12, 15, 28);
        private static readonly Color Panel = Color.FromArgb(21, 27, 44);
        private static readonly Color Ink = Color.FromArgb(238, 242, 251);
        private static readonly Color Muted = Color.FromArgb(162, 177, 200);
        private static readonly Color RootAColor = Color.FromArgb(95, 235, 230);
        private static readonly Color RootBColor = Color.FromArgb(255, 201, 92);
        private static readonly Color[] Palette =
        {
            Color.FromArgb(32, 129, 112), Color.FromArgb(164, 125, 45),
            Color.FromArgb(126, 81, 173), Color.FromArgb(49, 94, 161)
        };
        private static readonly double[] CalibrationParameters = { -1, -0.5, -1e-6, 0, 1e-6, 0.5, 1 };

        internal static (Complex A, Complex B) Roots(double lambda)
        {
            if (!double.IsFinite(lambda) || lambda < -1 || lambda > 1)
                throw new ArgumentOutOfRangeException(nameof(lambda), "Choose a parameter from -1 through 1.");
            Complex first = lambda >= 0 ? new Complex(Math.Sqrt(2 * lambda), 0)
                : new Complex(0, Math.Sqrt(-2 * lambda));
            return (first, -first);
        }

        internal static Complex Value(Complex z, double lambda) => z * z - 2 * lambda;
        internal static Complex ZDerivative(Complex z) => 2 * z;
        internal static Complex SecondZDerivative() => new Complex(2, 0);
        internal static Complex LambdaDerivative() => new Complex(-2, 0);

        private static double Wrap(double angle)
        {
            double wrapped = angle % Tau;
            return wrapped < 0 ? wrapped + Tau : wrapped;
        }

        private static int Quadrant(Complex value, double paletteDegrees)
        {
            if (value == Complex.Zero) return -1;
            return Math.Min(3, (int)(Wrap(value.Phase - paletteDegrees * Math.PI / 180) / (Math.PI / 2)));
        }

        private static object Coordinates(Complex value) => new { real = value.Real, imaginary = value.Imaginary };

        internal static object Snapshot(double lambda)
        {
            var roots = Roots(lambda);
            object[] distinct = lambda == 0
                ? new object[] { new { id = "A+B", real = 0.0, imaginary = 0.0, multiplicity = 2 } }
                : new object[]
                {
                    new { id = "A", real = roots.A.Real, imaginary = roots.A.Imaginary, multiplicity = 1 },
                    new { id = "B", real = roots.B.Real, imaginary = roots.B.Imaginary, multiplicity = 1 }
                };
            var samples = new[] { new Complex(-1.3, 0.7), new Complex(0.23, -0.42), new Complex(2, 1.1) }
                .Select(z => new
                {
                    z = Coordinates(z), value = Coordinates(Value(z, lambda)),
                    factorA = Coordinates(z - roots.A), factorB = Coordinates(z - roots.B),
                    lambdaDerivative = Coordinates(LambdaDerivative()), secondZDerivative = Coordinates(SecondZDerivative())
                }).ToArray();
            return new
            {
                lambda, roots = distinct, branches = new { A = Coordinates(roots.A), B = Coordinates(roots.B) },
                separation = (roots.A - roots.B).Magnitude, discriminant = 8 * lambda,
                freezeDeltaLambda = -lambda, decreasingPredictionApplicable = lambda > 0,
                maximumRootResidual = Math.Max(Value(roots.A, lambda).Magnitude, Value(roots.B, lambda).Magnitude),
                samples
            };
        }

        // defines: graph.zeros.motion.color
        public static Bitmap Render(double lambda, double paletteDegrees, out string report)
        {
            var roots = Roots(lambda);
            if (!double.IsFinite(paletteDegrees)) throw new ArgumentOutOfRangeException(nameof(paletteDegrees));
            var image = new Bitmap(1440, 940);
            using var g = System.Drawing.Graphics.FromImage(image);
            g.Clear(Background);
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            using var title = new Font("Segoe UI", 31, FontStyle.Bold, GraphicsUnit.Pixel);
            using var heading = new Font("Segoe UI", 19, FontStyle.Bold, GraphicsUnit.Pixel);
            using var body = new Font("Segoe UI", 15, FontStyle.Regular, GraphicsUnit.Pixel);
            using var small = new Font("Segoe UI", 13, FontStyle.Regular, GraphicsUnit.Pixel);
            using var ink = new SolidBrush(Ink);
            using var muted = new SolidBrush(Muted);
            using var panel = new SolidBrush(Panel);

            g.DrawString("ZERO MOTION", title, ink, 28, 22);
            g.DrawString("Two local origins follow their roots into a collision, then split along the imaginary axis.", body, muted, 30, 65);
            g.DrawString($"F(z, λ) = z² − 2λ       λ = {lambda:G6}       palette rotation {paletteDegrees:G5}°", heading, ink, 30, 101);
            DrawPlane(g, new Rectangle(28, 146, 448, 466), roots.A, roots, lambda, paletteDegrees, 0,
                "Local origin A", "arg(z − A)   ·   B marks the other root of F", heading, small);
            DrawPlane(g, new Rectangle(496, 146, 448, 466), roots.B, roots, lambda, paletteDegrees, 1,
                "Local origin B", "arg(z − B)   ·   A marks the other root of F", heading, small);
            DrawPlane(g, new Rectangle(964, 146, 448, 466), Complex.Zero, roots, lambda, paletteDegrees, 2,
                "Combined function", "arg(F) = arg(z − A) + arg(z − B)  mod 2π", heading, small);

            g.FillRectangle(panel, 28, 630, 848, 199);
            g.FillRectangle(panel, 896, 630, 516, 199);
            g.DrawString("Paths as λ decreases", heading, ink, 46, 644);
            DrawPaths(g, new Rectangle(54, 684, 788, 103), lambda, small);
            g.DrawString("A follows the positive real branch, then the positive imaginary branch. B follows the opposite branch.",
                small, muted, 46, 803);
            g.DrawString("Measured in this frame", heading, ink, 914, 644);
            g.DrawString($"A  {FormatRoot(roots.A)}       B  {FormatRoot(roots.B)}", body, ink, 914, 678);
            g.DrawString($"Separation  {(roots.A - roots.B).Magnitude:F6}       Δ = 8λ  = {8 * lambda:G6}", body, ink, 914, 708);
            string prediction = lambda > 0 ? $"Predicted Δλ  {(-lambda):G6}  →  collision at λ = 0"
                : lambda == 0 ? "At the double zero. Each local factor remains simple."
                : "Already off the real axis. The decreasing flow separates the roots.";
            g.DrawString(prediction, small, ink, 914, 740);
            g.DrawString("∂F/∂λ = −2 = −∂²F/∂z²", body, muted, 914, 773);

            string[] angles = { "0°–90°", "90°–180°", "180°–270°", "270°–360°" };
            for (int i = 0; i < Palette.Length; i++)
            {
                using var color = new SolidBrush(Palette[i]);
                g.FillRectangle(color, 31 + i * 177, 852, 16, 16);
                g.DrawString(angles[i], small, ink, 55 + i * 177, 851);
            }
            g.FillEllipse(Brushes.White, 750, 852, 16, 16);
            g.DrawString("zero / undefined angle", small, ink, 774, 851);
            g.DrawString("Displayed phase is arg(value) minus the palette angle.", small, muted, 1010, 850,
                new StringFormat { Trimming = StringTrimming.Word });
            g.DrawString("Exact polynomial calibration. The parameter changes the function. The palette changes its colors.",
                body, ink, 30, 891);
            g.DrawString("A model for studying collisions. Applying this method to Riemann's xi flow requires a separate experiment.",
                small, muted, 30, 916);

            report = $"Exact calibration F(z,λ)=z²−2λ at λ={lambda:G8}. A={FormatRoot(roots.A)}, B={FormatRoot(roots.B)}. "
                + $"Separation={(roots.A - roots.B).Magnitude:G8}. Discriminant Δ={8 * lambda:G8}. "
                + $"Frozen quadratic prediction Δλ={-lambda:G8}. "
                + (lambda > 0 ? "Decreasing λ reaches the double zero at zero. "
                    : lambda == 0 ? "The combined zero has multiplicity two. " : "Both roots already lie off the real axis. ")
                + "Phase addition uses the unrotated factor phases modulo 2π. Colors are assigned directly from each value. "
                + "Branch labels are a convention through the collision. This exact polynomial calibration does not establish a result about zeta or RH.";
            return image;
        }

        internal static bool TryMapPixel(float imageX, float imageY, out Complex z)
        {
            const float top = 203;
            const float span = 360;
            for (int panel = 0; panel < 3; panel++)
            {
                float left = 72 + 468 * panel;
                float x = imageX - left;
                float y = imageY - top;
                if (x >= 0 && x <= span && y >= 0 && y <= span)
                {
                    z = new Complex(-Extent + 2 * Extent * x / span, Extent - 2 * Extent * y / span);
                    return true;
                }
            }
            z = Complex.Zero;
            return false;
        }

        internal static string DescribePoint(Complex z, double lambda, double paletteDegrees)
        {
            var roots = Roots(lambda);
            Complex first = z - roots.A;
            Complex second = z - roots.B;
            Complex product = Value(z, lambda);
            string RawAngle(Complex value) => value == Complex.Zero ? "undefined at zero"
                : $"{Wrap(value.Phase):F6} rad";
            string ColorSector(Complex value)
            {
                int quadrant = Quadrant(value, paletteDegrees);
                return quadrant < 0 ? "white / undefined" : $"quadrant {quadrant + 1}";
            }
            string sum = first == Complex.Zero || second == Complex.Zero ? "undefined at zero"
                : $"{Wrap(first.Phase + second.Phase):F6} rad";
            return $"z = {FormatRoot(z)}. Local A = {FormatRoot(first)}. Local B = {FormatRoot(second)}. "
                + $"Raw phase A {RawAngle(first)}. Raw phase B {RawAngle(second)}. Raw sum modulo 2π {sum}. "
                + $"Raw product phase {RawAngle(product)}. Palette rotation {paletteDegrees:G5}°. "
                + $"Displayed A {ColorSector(first)}, B {ColorSector(second)}, product {ColorSector(product)}. "
                + "The raw factor phases add. Each displayed phase subtracts the palette rotation once.";
        }

        private static string FormatRoot(Complex root) => $"{root.Real:0.000000}{(root.Imaginary < 0 ? " − " : " + ")}{Math.Abs(root.Imaginary):0.000000}i";

        private static void DrawPlane(System.Drawing.Graphics g, Rectangle panelBounds, Complex origin,
            (Complex A, Complex B) roots, double lambda, double paletteDegrees, int mode, string title, string caption,
            Font heading, Font small)
        {
            using var background = new SolidBrush(Panel);
            using var ink = new SolidBrush(Ink);
            using var muted = new SolidBrush(Muted);
            g.FillRectangle(background, panelBounds);
            g.DrawString(title, heading, ink, panelBounds.Left + 18, panelBounds.Top + 14);
            var bounds = new Rectangle(panelBounds.Left + 44, panelBounds.Top + 57, 361, 361);
            using var bitmap = PlaneBitmap(bounds.Width, roots, lambda, paletteDegrees, mode);
            g.DrawImageUnscaled(bitmap, bounds.Location);
            PointF Screen(Complex z) => new PointF(bounds.Left + (float)((z.Real + Extent) / (2 * Extent) * (bounds.Width - 1)),
                bounds.Bottom - 1 - (float)((z.Imaginary + Extent) / (2 * Extent) * (bounds.Height - 1)));
            PointF local = Screen(origin);
            using var axis = new Pen(Color.FromArgb(195, 225, 232, 246), 1) { DashStyle = DashStyle.Dash };
            g.DrawLine(axis, bounds.Left, local.Y, bounds.Right - 1, local.Y);
            g.DrawLine(axis, local.X, bounds.Top, local.X, bounds.Bottom - 1);
            using var border = new Pen(Color.FromArgb(87, 100, 124));
            g.DrawRectangle(border, bounds);
            foreach (int tick in new[] { -2, -1, 0, 1, 2 })
            {
                PointF point = Screen(new Complex(tick, tick));
                g.DrawString(tick.ToString(), small, muted, point.X - 6, bounds.Bottom + 4);
                g.DrawString(tick.ToString(), small, muted, bounds.Left - 23, point.Y - 8);
            }
            g.DrawString("Re z", small, muted, bounds.Right - 26, bounds.Bottom + 21);
            g.DrawString("Im z", small, muted, bounds.Left - 27, bounds.Top - 19);
            DrawRoot(g, Screen(roots.A), RootAColor, "A", small, roots.A == roots.B);
            if (roots.A != roots.B) DrawRoot(g, Screen(roots.B), RootBColor, "B", small, false);
            g.DrawString(caption, small, ink, panelBounds.Left + 18, panelBounds.Bottom - 22);
        }

        private static Bitmap PlaneBitmap(int size, (Complex A, Complex B) roots, double lambda, double paletteDegrees, int mode)
        {
            var pixels = new int[size * size];
            for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                var z = new Complex(-Extent + 2 * Extent * x / (size - 1), Extent - 2 * Extent * y / (size - 1));
                Complex value = mode == 0 ? z - roots.A : mode == 1 ? z - roots.B : Value(z, lambda);
                int quadrant = Quadrant(value, paletteDegrees);
                pixels[y * size + x] = quadrant < 0 ? Color.White.ToArgb() : Palette[quadrant].ToArgb();
            }
            var bitmap = new Bitmap(size, size, PixelFormat.Format32bppArgb);
            var data = bitmap.LockBits(new Rectangle(0, 0, size, size), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try
            {
                for (int y = 0; y < size; y++) Marshal.Copy(pixels, y * size, IntPtr.Add(data.Scan0, y * data.Stride), size);
            }
            finally { bitmap.UnlockBits(data); }
            return bitmap;
        }

        private static void DrawRoot(System.Drawing.Graphics g, PointF point, Color color, string label, Font font, bool collision)
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            using var rim = new Pen(Color.FromArgb(12, 15, 28), 4);
            using var marker = new Pen(collision ? Color.White : color, 2);
            using var ink = new SolidBrush(collision ? Color.White : color);
            g.DrawEllipse(rim, point.X - 7, point.Y - 7, 14, 14);
            g.DrawEllipse(marker, point.X - 7, point.Y - 7, 14, 14);
            g.FillEllipse(ink, point.X - 2, point.Y - 2, 4, 4);
            g.DrawString(collision ? "A + B" : label, font, ink, point.X + 11, point.Y - 8);
            g.SmoothingMode = SmoothingMode.None;
        }

        private static void DrawPaths(System.Drawing.Graphics g, Rectangle bounds, double currentLambda, Font small)
        {
            using var axis = new Pen(Color.FromArgb(80, 97, 121));
            using var ink = new SolidBrush(Muted);
            using var first = new Pen(RootAColor, 2);
            using var second = new Pen(RootBColor, 2);
            float centerX = bounds.Left + bounds.Width / 2;
            float centerY = bounds.Top + bounds.Height / 2;
            float horizontalScale = bounds.Width / 4f;
            float verticalScale = bounds.Height / 3.4f;
            PointF Screen(Complex z) => new PointF(centerX + (float)z.Real * horizontalScale,
                centerY - (float)z.Imaginary * verticalScale);
            g.DrawLine(axis, bounds.Left, centerY, bounds.Right, centerY);
            g.DrawLine(axis, centerX, bounds.Top - 2, centerX, bounds.Bottom + 2);
            var pathA = new PointF[81];
            var pathB = new PointF[pathA.Length];
            for (int i = 0; i < pathA.Length; i++)
            {
                var roots = Roots(1 - 2.0 * i / (pathA.Length - 1));
                pathA[i] = Screen(roots.A);
                pathB[i] = Screen(roots.B);
            }
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.DrawLines(first, pathA);
            g.DrawLines(second, pathB);
            DrawArrow(g, Screen(new Complex(0.8, 0)), Screen(new Complex(0.6, 0)), RootAColor);
            DrawArrow(g, Screen(new Complex(-0.8, 0)), Screen(new Complex(-0.6, 0)), RootBColor);
            DrawArrow(g, Screen(new Complex(0, 0.55)), Screen(new Complex(0, 0.8)), RootAColor);
            DrawArrow(g, Screen(new Complex(0, -0.55)), Screen(new Complex(0, -0.8)), RootBColor);
            var current = Roots(currentLambda);
            DrawRoot(g, Screen(current.A), RootAColor, "A", small, currentLambda == 0);
            if (currentLambda != 0) DrawRoot(g, Screen(current.B), RootBColor, "B", small, false);
            g.DrawString("real", small, ink, bounds.Right - 30, centerY + 5);
            g.DrawString("imaginary", small, ink, centerX + 14, bounds.Top - 1);
            g.DrawString("λ = 1", small, ink, bounds.Left + 36, centerY - 23);
            g.DrawString("λ = 0", small, ink, centerX - 50, centerY + 9);
            g.SmoothingMode = SmoothingMode.None;
        }

        private static void DrawArrow(System.Drawing.Graphics g, PointF start, PointF end, Color color)
        {
            using var arrow = new Pen(color, 2) { EndCap = LineCap.ArrowAnchor };
            g.DrawLine(arrow, start, end);
        }

        private static double Winding(double lambda, Complex center, double radius, int samples, bool reverse)
        {
            Complex previous = Value(center + radius, lambda);
            if (previous.Magnitude < 1e-20) throw new InvalidOperationException("Contour touches a zero.");
            double turn = 0;
            for (int i = 1; i <= samples; i++)
            {
                double angle = (reverse ? -1 : 1) * Tau * i / samples;
                Complex next = Value(center + Complex.FromPolarCoordinates(radius, angle), lambda);
                if (next.Magnitude < 1e-20) throw new InvalidOperationException("Contour touches a zero.");
                double phase = (next * Complex.Conjugate(previous)).Phase;
                if (Math.Abs(phase) > Math.PI / 2) throw new InvalidOperationException("Contour sampling is too coarse.");
                turn += phase;
                previous = next;
            }
            return turn / Tau;
        }

        private static void Require(bool condition, string description)
        {
            if (!condition) throw new InvalidOperationException("Zero-motion verification failed. " + description);
        }

        // defines: graph.zeros.motion.verify
        public static object Verify()
        {
            double maximumRootResidual = 0;
            double maximumProductError = 0;
            double maximumPhaseError = 0;
            double maximumDiscriminantError = 0;
            int pointChecks = 0;
            int changedColors = 0;
            var windingCases = new List<object>();
            var random = new Random(17041);
            foreach (double lambda in CalibrationParameters)
            {
                var roots = Roots(lambda);
                maximumRootResidual = Math.Max(maximumRootResidual,
                    Math.Max(Value(roots.A, lambda).Magnitude, Value(roots.B, lambda).Magnitude));
                double separation = (roots.A - roots.B).Magnitude;
                Require(Math.Abs(separation * separation - Math.Abs(8 * lambda)) < 1e-13, "Root separation.");
                Require((LambdaDerivative() + SecondZDerivative()).Magnitude == 0, "Heat equation.");
                for (int i = 0; i < 128; i++)
                {
                    var z = i < 9 ? new Complex(i / 3 - 1, i % 3 - 1)
                        : new Complex(4 * random.NextDouble() - 2, 4 * random.NextDouble() - 2);
                    Complex first = z - roots.A;
                    Complex second = z - roots.B;
                    Complex value = Value(z, lambda);
                    double error = (first * second - value).Magnitude;
                    maximumProductError = Math.Max(maximumProductError, error);
                    Require(error < 1e-13 * Math.Max(1, value.Magnitude), "Product identity.");
                    Complex discriminant = ZDerivative(z) * ZDerivative(z) - 2 * value * SecondZDerivative();
                    maximumDiscriminantError = Math.Max(maximumDiscriminantError, (discriminant - 8 * lambda).Magnitude);
                    Require((discriminant - 8 * lambda).Magnitude < 1e-13, "Discriminant.");
                    Require((-discriminant / 8 + lambda).Magnitude < 1e-13, "Frozen quadratic prediction.");
                    if (first.Magnitude > 1e-12 && second.Magnitude > 1e-12)
                    {
                        foreach (double angle in new[] { 0.0, 22.5, 90.0, 173.0 })
                        {
                            double basis = angle * Math.PI / 180;
                            double errorAngle = Math.Abs(Math.Atan2(Math.Sin(first.Phase + second.Phase - basis - (value.Phase - basis)),
                                Math.Cos(first.Phase + second.Phase - basis - (value.Phase - basis))));
                            maximumPhaseError = Math.Max(maximumPhaseError, errorAngle);
                            Require(errorAngle < 1e-12, "Phase addition in the rotated palette.");
                        }
                    }
                    if (Quadrant(value, 0) != Quadrant(value, 90)) changedColors++;
                    pointChecks++;
                }
                double outer = Winding(lambda, Complex.Zero, 1.8, 512, false);
                double backwards = Winding(lambda, Complex.Zero, 1.8, 512, true);
                double radius = lambda == 0 ? 0.2 : Math.Min(0.2, separation / 4);
                double aroundA = Winding(lambda, roots.A, radius, 256, false);
                double aroundB = Winding(lambda, roots.B, radius, 256, false);
                double multiplicity = lambda == 0 ? 2 : 1;
                Require(Math.Abs(outer - 2) < 1e-12 && Math.Abs(backwards + 2) < 1e-12, "Outer winding and orientation.");
                Require(Math.Abs(aroundA - multiplicity) < 1e-12 && Math.Abs(aroundB - multiplicity) < 1e-12,
                    "Local winding multiplicity.");
                windingCases.Add(new { lambda, outerWindingForward = outer, outerWindingReverse = backwards,
                    rootAWinding = aroundA, rootBWinding = aroundB, localRadius = radius });
            }
            Require(maximumRootResidual < 1e-13, "Root residuals.");
            Require(changedColors > 0 && Quadrant(Complex.Zero, 0) == -1 && Quadrant(Complex.Zero, 90) == -1,
                "Palette rotation and undefined zero angle.");
            return new
            {
                status = "passed", traceId = "graph.zeros.motion.verify", pointChecks,
                maximumRootResidual, maximumProductError, maximumPhaseError, maximumDiscriminantError,
                windingCases, palette = new { testedDegrees = new[] { 0.0, 22.5, 90.0, 173.0 }, changedColors,
                    invariant = "Roots, discriminant, and parameter prediction are computed before color assignment." },
                interpretation = "Exact polynomial identities checked numerically. This calibration makes no assertion about Riemann zeta zeros."
            };
        }

        public static void Export(string path, double lambda = 0.5, double paletteDegrees = 0)
        {
            object verification = Verify();
            using var image = Render(lambda, paletteDegrees, out string report);
            image.Save(path, ImageFormat.Png);
            File.WriteAllText(Path.ChangeExtension(path, ".txt"), report);
            var evidence = new
            {
                schemaVersion = 1, model = "F(z,lambda)=z^2-2*lambda", heatEquation = "dF/dlambda=-d2F/dz2",
                parameters = new { lambda, paletteDegrees }, frame = Snapshot(lambda),
                snapshots = CalibrationParameters.Select(Snapshot).ToArray(), verification
            };
            File.WriteAllText(Path.ChangeExtension(path, ".values.json"),
                JsonSerializer.Serialize(evidence, new JsonSerializerOptions { WriteIndented = true }));
        }
    }
}
