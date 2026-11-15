using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Numerics;

namespace Graphics
{
    // defines: graph.zeta.contours
    // consumer: graph.zeta.overwrite
    internal static class ZetaContours
    {
        private const double Bottom = 13.94;
        private const double Top = 14.33;
        private const double CriticalLine = 0.5;
        private const double ControlShift = 0.12;

        private static readonly double[] Edges = { 0.26, 0.46, 0.54, 0.74 };
        private static readonly string[] Labels = { "Left", "Center", "Right" };

        public static Bitmap Render(out string report)
        {
            Func<Complex, Complex> zeta = ZetaExperiment.Zeta;
            Func<Complex, Complex> control = s => zeta(s - ControlShift);
            double? crossing = FindLineCrossing();
            var bitmap = new Bitmap(856, 448);
            using var drawing = System.Drawing.Graphics.FromImage(bitmap);
            drawing.Clear(Color.White);
            using var heading = new Font("Segoe UI", 18, FontStyle.Bold, GraphicsUnit.Pixel);
            using var label = new Font("Segoe UI", 13, FontStyle.Regular, GraphicsUnit.Pixel);
            using var bold = new Font("Segoe UI", 13, FontStyle.Bold, GraphicsUnit.Pixel);

            drawing.DrawString("Counting turns around zeta zeros", heading, Brushes.Black, 20, 12);
            drawing.DrawString("Follow the colored outlines counterclockwise. Each full turn estimates one enclosed zero.",
                label, Brushes.Black, 20, 40);
            string actual = DrawPlot(drawing, new Rectangle(20, 90, 392, 256), "Riemann zeta",
                zeta, crossing, bold, label);
            string shifted = DrawPlot(drawing, new Rectangle(444, 90, 392, 256),
                "Control: zeta(s - 0.12)", control, null, bold, label);

            string lineCheck = crossing is double height
                ? $"Hardy Z sign change on Re(s) = 1/2 at t ≈ {height:F9} (circled)."
                : "Hardy Z did not give a sign bracket in this window.";
            drawing.DrawString(lineCheck, label, Brushes.Black, 20, 388);
            drawing.DrawString("Dashed line: Re(s) = 1/2. Counts compare 16 and 32 samples per edge and are numerical estimates.",
                label, Brushes.Black, 20, 410);
            report = $"Riemann zeta: {actual}{Environment.NewLine}Shifted control: {shifted}{Environment.NewLine}{lineCheck}";
            return bitmap;
        }

        private static string DrawPlot(System.Drawing.Graphics drawing, Rectangle plot, string title,
            Func<Complex, Complex> evaluate, double? crossing, Font bold, Font label)
        {
            PointF Screen(Complex s) => new PointF(
                plot.Left + (float)((s.Real - Edges[0]) / (Edges[3] - Edges[0]) * plot.Width),
                plot.Bottom - (float)((s.Imaginary - Bottom) / (Top - Bottom) * plot.Height));

            using var phase = new Bitmap(196, 128);
            for (int y = 0; y < phase.Height; y++)
            for (int x = 0; x < phase.Width; x++)
            {
                var input = new Complex(Edges[0] + (x + 0.5) / phase.Width * (Edges[3] - Edges[0]),
                    Top - (y + 0.5) / phase.Height * (Top - Bottom));
                Color color = ZetaExperiment.PhaseColor(evaluate(input));
                phase.SetPixel(x, y, Color.FromArgb((color.R + 510) / 3,
                    (color.G + 510) / 3, (color.B + 510) / 3));
            }

            drawing.DrawString(title, bold, Brushes.Black, plot.Left, plot.Top - 24);
            drawing.InterpolationMode = InterpolationMode.NearestNeighbor;
            drawing.DrawImage(phase, plot);
            float lineX = Screen(new Complex(CriticalLine, Bottom)).X;
            using var dashed = new Pen(Color.FromArgb(80, 80, 80)) { DashStyle = DashStyle.Dash };
            drawing.DrawLine(dashed, lineX, plot.Top, lineX, plot.Bottom);

            using var underlay = new Pen(Color.FromArgb(38, 38, 38), 5);
            using var segment = new Pen(Color.White, 3);
            var counts = new int?[Labels.Length];
            var reverse = new int?[Labels.Length];
            for (int i = 0; i < Labels.Length; i++)
            {
                Complex[] points = Boundary(Edges[i], Edges[i + 1], 32);
                var values = points.Select(evaluate).ToArray();
                counts[i] = Estimate(Winding(values.Where((_, sample) => sample % 2 == 0)), Winding(values));
                reverse[i] = Estimate(Winding(values.Reverse().Where((_, sample) => sample % 2 == 0)),
                    Winding(values.Reverse()));

                for (int j = 0; j < points.Length; j++)
                    drawing.DrawLine(underlay, Screen(points[j]), Screen(points[(j + 1) % points.Length]));
                for (int j = 0; j < points.Length; j++)
                {
                    segment.Color = ZetaExperiment.PhaseColor(values[j]);
                    drawing.DrawLine(segment, Screen(points[j]), Screen(points[(j + 1) % points.Length]));
                }

                var topCenter = Screen(new Complex((Edges[i] + Edges[i + 1]) / 2, Top));
                var arrow = new[]
                {
                    new PointF(topCenter.X - 6, topCenter.Y),
                    new PointF(topCenter.X + 5, topCenter.Y - 5),
                    new PointF(topCenter.X + 5, topCenter.Y + 5)
                };
                drawing.FillPolygon(Brushes.Black, arrow);
                string countLabel = $"{Labels[i]} {FormatCount(counts[i])}";
                var width = drawing.MeasureString(countLabel, label).Width;
                drawing.DrawString(countLabel, label, Brushes.Black, topCenter.X - width / 2, plot.Bottom + 8);
            }

            if (crossing is double height)
            {
                PointF zero = Screen(new Complex(CriticalLine, height));
                using var ring = new Pen(Color.Black, 2);
                drawing.DrawEllipse(ring, zero.X - 7, zero.Y - 7, 14, 14);
            }

            var whole = Boundary(Edges[0], Edges[3], 32).Select(evaluate).ToArray();
            int? total = Estimate(Winding(whole.Where((_, sample) => sample % 2 == 0)), Winding(whole));
            return $"left/center/right {FormatCounts(counts)}; clockwise {FormatCounts(reverse)}; outer contour {FormatCount(total)}.";
        }

        private static string FormatCount(int? count) => count?.ToString() ?? "?";

        private static string FormatCounts(int?[] counts) => string.Join("/", counts.Select(FormatCount));

        private static Complex[] Boundary(double left, double right, int samplesPerEdge)
        {
            var corners = new[]
            {
                new Complex(left, Bottom), new Complex(right, Bottom),
                new Complex(right, Top), new Complex(left, Top)
            };
            var points = new Complex[4 * samplesPerEdge];
            for (int side = 0; side < corners.Length; side++)
            {
                Complex start = corners[side];
                Complex edge = corners[(side + 1) % corners.Length] - start;
                for (int sample = 0; sample < samplesPerEdge; sample++)
                    points[side * samplesPerEdge + sample] = start + edge * ((double)sample / samplesPerEdge);
            }
            return points;
        }

        private static int? Winding(System.Collections.Generic.IEnumerable<Complex> samples)
        {
            Complex[] values = samples.ToArray();
            double turn = 0;
            for (int i = 0; i < values.Length; i++)
            {
                Complex current = values[i];
                Complex next = values[(i + 1) % values.Length];
                double phase = (next * Complex.Conjugate(current)).Phase;
                if (current.Magnitude < 1e-8 || !double.IsFinite(phase) || Math.Abs(phase) >= Math.PI / 2)
                    return null;
                turn += phase;
            }

            double turns = turn / (2 * Math.PI);
            double rounded = Math.Round(turns);
            return Math.Abs(turns - rounded) < 1e-8 ? (int)rounded : (int?)null;
        }

        private static int? Estimate(int? coarse, int? fine) => coarse == fine ? fine : null;

        private static double? FindLineCrossing()
        {
            double low = Bottom;
            double high = Top;
            int lowSign = Math.Sign(HardyZ(low));
            if (lowSign == Math.Sign(HardyZ(high)))
                return null;

            for (int i = 0; i < 32; i++)
            {
                double mid = (low + high) / 2;
                if (Math.Sign(HardyZ(mid)) == lowSign)
                    low = mid;
                else
                    high = mid;
            }
            return (low + high) / 2;
        }

        private static double HardyZ(double t)
        {
            // DLMF 25.10.1-2. Shift the log-gamma argument by recurrence,
            // then use the first three Stirling corrections (DLMF 5.11.1).
            var input = new Complex(0.25, t / 2);
            var shifted = input + 8;
            Complex inverse = 1 / shifted;
            Complex squared = inverse * inverse;
            Complex logGamma = (shifted - 0.5) * Complex.Log(shifted) - shifted
                + inverse * (1.0 / 12 + squared * (-1.0 / 360 + squared / 1260));
            for (int i = 0; i < 8; i++)
                logGamma -= Complex.Log(input + i);
            double theta = logGamma.Imaginary - t * Math.Log(Math.PI) / 2;
            return (Complex.FromPolarCoordinates(1, theta) *
                ZetaExperiment.Zeta(new Complex(CriticalLine, t))).Real;
        }
    }
}
