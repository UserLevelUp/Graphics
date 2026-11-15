using System;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Numerics;
using System.Threading.Tasks;

namespace Graphics
{
    // defines: graph.zeta.overwrite
    internal static class ZetaExperiment
    {
        private const int Size = 224;
        private const int CoarseStep = 32;
        private const int FineStep = CoarseStep / 2;
        private const double ZeroHeight = 14.134725141734694;
        private const double UnitsPerPixel = 0.5 / Size;
        private static readonly Color[] Palette =
            { Color.DeepSkyBlue, Color.DeepPink, Color.Gold, Color.Green };

        private static readonly double[] EtaWeights = BuildEtaWeights();
        private static readonly double[] TermLogs =
            Enumerable.Range(1, EtaWeights.Length).Select(i => Math.Log(i)).ToArray();

        public static Bitmap Render(out string report)
        {
            var timer = Stopwatch.StartNew();
            var values = new Complex[Size * Size];
            Parallel.For(0, Size, y =>
            {
                for (int x = 0; x < Size; x++)
                    values[y * Size + x] = Zeta(Input(x, y));
            });
            long mathMs = timer.ElapsedMilliseconds;
            timer.Restart();
            var coarse = Stamp(values, CoarseStep, CoarseStep / 2, false);
            var fine = Stamp(values, FineStep, CoarseStep / 2, false);
            var shifted = Stamp(values, FineStep, CoarseStep / 2 + FineStep / 2, false);
            var reversed = Stamp(values, FineStep, CoarseStep / 2, true);
            if (!fine.SequenceEqual(reversed))
                throw new InvalidOperationException("Reversing the centers changed the image.");
            long stampMs = timer.ElapsedMilliseconds;

            var zero = new Complex(0.5, ZeroHeight);
            var ordinary = new Complex(0.67, ZeroHeight);
            double zeroMagnitude = Zeta(zero).Magnitude;
            string loops = $"Winding at 32 / 64 samples: known zero {Winding(zero, 32)} / {Winding(zero, 64)}, off-line control {Winding(ordinary, 32)} / {Winding(ordinary, 64)}.";
            string changes = $"Winning colors changed on {Changed(coarse, fine):P1} of pixels when halving h and {Changed(fine, shifted):P1} when shifting the fine grid.";
            report = $"{loops}{Environment.NewLine}{changes}{Environment.NewLine}Reverse draw order: identical. |zeta(known zero)| = {zeroMagnitude:E2}.{Environment.NewLine}Zeta grid: {mathMs} ms. Four stamp passes, including reverse check: {stampMs} ms.";

            var result = new Bitmap(996, 370);
            using var drawing = System.Drawing.Graphics.FromImage(result);
            drawing.Clear(Color.White);
            using var heading = new Font("Segoe UI", 12, FontStyle.Bold, GraphicsUnit.Pixel);
            using var label = new Font("Segoe UI", 12, FontStyle.Regular, GraphicsUnit.Pixel);
            drawing.DrawString("Four-color zeta experiment", heading, Brushes.Black, 16, 10);
            drawing.DrawString("Same region in all panels. Dashed line: Re(s) = 1/2. Circle: known zero. Square: off-line control.", label, Brushes.Black, 16, 30);
            DrawPanel(drawing, coarse, null, 16, "Local origins, coarse grid", heading);
            DrawPanel(drawing, fine, null, 260, "Local origins, half the spacing", heading);
            DrawPanel(drawing, shifted, null, 504, "Local origins, shifted half a step", heading);
            DrawPanel(drawing, null, values, 748, "Fixed output origin at zero", heading);
            drawing.DrawString("Signs (real, imaginary): blue ++   pink -+   gold --   green +-    Darker local pixels received conflicting colors.", label, Brushes.Black, 16, 305);
            drawing.DrawString(loops, label, Brushes.Black, 16, 324);
            drawing.DrawString(changes, label, Brushes.Black, 16, 343);
            return result;
        }

        private static Complex Input(int x, int y) =>
            new Complex(0.5 + (x - Size / 2) * UnitsPerPixel,
                        ZeroHeight + (Size / 2 - y) * UnitsPerPixel);

        internal static double[] BuildEtaWeights(int terms = 52)
        {
            // Collect the signed binomial coefficients of the Euler-transformed eta series.
            var weights = new double[terms];
            double rowWeight = 0.5;
            for (int row = 0; row < weights.Length; row++)
            {
                double coefficient = rowWeight;
                for (int term = 0; term <= row; term++)
                {
                    weights[term] += coefficient;
                    coefficient *= -(double)(row - term) / (term + 1);
                }
                rowWeight *= 0.5;
            }
            return weights;
        }

        internal static Complex Zeta(Complex s)
        {
            Complex eta = Complex.Zero;
            for (int i = 0; i < EtaWeights.Length; i++)
                eta += EtaWeights[i] * Complex.Exp(-s * TermLogs[i]);
            return eta / (1 - Complex.Exp((1 - s) * TermLogs[1]));
        }

        internal static Color PhaseColor(Complex z) => Palette[Quadrant(z)];

        private static int Quadrant(Complex z)
        {
            if (z.Imaginary >= 0)
                return z.Real >= 0 ? 0 : 1;
            return z.Real < 0 ? 2 : 3;
        }

        private struct Pixel
        {
            public int Owner;
            public int DistanceSquared;
            public int Color;
            public int Votes;
        }

        private static Pixel[] Stamp(Complex[] values, int step, int offset, bool reverse)
        {
            int first = offset % step;
            int radius = step;
            var centers = Enumerable.Range(0, values.Length)
                .Where(i => i % Size % step == first && i / Size % step == first);
            var pixels = new Pixel[values.Length];

            foreach (int center in reverse ? centers.Reverse() : centers)
            {
                int cx = center % Size;
                int cy = center / Size;
                for (int y = Math.Max(0, cy - radius); y <= Math.Min(Size - 1, cy + radius); y++)
                for (int x = Math.Max(0, cx - radius); x <= Math.Min(Size - 1, cx + radius); x++)
                {
                    int dx = x - cx;
                    int dy = y - cy;
                    int distance = dx * dx + dy * dy;
                    if (distance == 0 || distance > radius * radius)
                        continue;

                    int index = y * Size + x;
                    int color = Quadrant(values[index] - values[center]);
                    ref Pixel pixel = ref pixels[index];
                    if (pixel.Votes == 0 || distance < pixel.DistanceSquared ||
                        (distance == pixel.DistanceSquared && center < pixel.Owner))
                    {
                        pixel.Owner = center;
                        pixel.DistanceSquared = distance;
                        pixel.Color = color;
                    }
                    pixel.Votes |= 1 << color;
                }
            }
            return pixels;
        }

        private static double Changed(Pixel[] first, Pixel[] second)
        {
            int changes = 0;
            for (int i = 0; i < first.Length; i++)
                if (first[i].Color != second[i].Color)
                    changes++;
            return (double)changes / first.Length;
        }

        private static int Winding(Complex center, int samples)
        {
            const double radius = 0.06;
            Complex first = Zeta(center + radius);
            Complex previous = first;
            double turn = 0;
            for (int i = 1; i <= samples; i++)
            {
                Complex next = i == samples ? first :
                    Zeta(center + Complex.FromPolarCoordinates(radius, 2 * Math.PI * i / samples));
                turn += (next / previous).Phase;
                previous = next;
            }
            return (int)Math.Round(turn / (2 * Math.PI));
        }

        private static void DrawPanel(System.Drawing.Graphics drawing, Pixel[] local, Complex[] values,
            int left, string title, Font heading)
        {
            const int top = 70;
            using var bitmap = new Bitmap(Size, Size);
            for (int y = 0; y < Size; y++)
            for (int x = 0; x < Size; x++)
            {
                int index = y * Size + x;
                Color color;
                if (local == null)
                    color = Palette[Quadrant(values[index])];
                else
                {
                    Pixel pixel = local[index];
                    color = pixel.Votes == 0 ? Color.White : Palette[pixel.Color];
                    if ((pixel.Votes & (pixel.Votes - 1)) != 0)
                        color = Color.FromArgb(color.R * 3 / 5, color.G * 3 / 5, color.B * 3 / 5);
                }
                bitmap.SetPixel(x, y, color);
            }

            drawing.DrawString(title, heading, Brushes.Black, left, 51);
            drawing.DrawImageUnscaled(bitmap, left, top);
            int critical = left + Size / 2;
            using var line = new Pen(Color.White) { DashStyle = System.Drawing.Drawing2D.DashStyle.Dash };
            drawing.DrawLine(line, critical, top, critical, top + Size - 1);
            int mid = top + Size / 2;
            int control = critical + (int)Math.Round(0.17 / UnitsPerPixel);
            drawing.DrawEllipse(Pens.Black, critical - 5, mid - 5, 10, 10);
            drawing.DrawRectangle(Pens.Black, control - 4, mid - 4, 8, 8);
            drawing.DrawRectangle(Pens.Black, left, top, Size, Size);
        }
    }
}
