using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Graphics
{
    // defines: graph.riemann.zero_index.grid
    // consumer: graph.riemann.switch.model
    // consumer: graph.riemann.continuation.animation.model
    internal static class ZetaZeroIndexExperiment
    {
        private const int Terms = 192, RefinedTerms = 256;
        private static readonly Color[] Palette = {
            Color.FromArgb(27, 115, 94), Color.FromArgb(136, 102, 39),
            Color.FromArgb(101, 60, 133), Color.FromArgb(39, 77, 136)
        };

        private sealed class GridSpec
        {
            internal string Name, SourceHeight;
            internal int? ZeroIndex;
            internal double? CenterT;
            internal double MinSigma, MaxSigma, MinT, MaxT;
            internal int Width, Height;
        }

        private static bool Finite(Complex value) => double.IsFinite(value.Real) && double.IsFinite(value.Imaginary);
        private static Complex Invalid => new Complex(double.NaN, double.NaN);
        private static double Sigma(GridSpec spec, int x) => spec.MinSigma + (spec.MaxSigma - spec.MinSigma) * x / (spec.Width - 1);
        private static double Height(GridSpec spec, int y) => spec.MinT + (spec.MaxT - spec.MinT) * y / (spec.Height - 1);
        private static int Quadrant(Complex value)
        {
            if (!Finite(value) || value == Complex.Zero) return -1;
            double angle = value.Phase % (2 * Math.PI);
            if (angle < 0) angle += 2 * Math.PI;
            return Math.Min(3, (int)(angle / (Math.PI / 2)));
        }
        private static string Hash(string path)
        {
            using var stream = File.OpenRead(path);
            using var hash = SHA256.Create();
            return BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
        }

        private static object AuditPoint(string label, double sigma, double t)
        {
            var s = new Complex(sigma, t);
            Complex value = ZetaSwitchExperiment.Evaluate(s, Terms);
            Complex refined = ZetaSwitchExperiment.Evaluate(s, RefinedTerms);
            bool valid = Finite(value), refinedValid = Finite(refined);
            double? difference = valid && refinedValid ? (double?)(value - refined).Magnitude : null;
            int quadrant = Quadrant(value);
            return new {
                label, sigma, t, valid, refinedValid,
                real = valid ? (double?)value.Real : null,
                imaginary = valid ? (double?)value.Imaginary : null,
                refinedReal = refinedValid ? (double?)refined.Real : null,
                refinedImaginary = refinedValid ? (double?)refined.Imaginary : null,
                refinementDifference = difference,
                scaledRefinementDifference = difference.HasValue ? (double?)(difference.Value / Math.Max(1, refined.Magnitude)) : null,
                phaseQuadrantAtTargetZero = quadrant >= 0 ? (int?)(quadrant + 1) : null,
                componentMarginFromAxis = valid ? (double?)Math.Min(Math.Abs(value.Real), Math.Abs(value.Imaginary)) : null
            };
        }

        private static Bitmap Texture(Complex[] values, GridSpec spec)
        {
            var pixels = new byte[checked(spec.Width * spec.Height * 4)];
            Parallel.For(0, spec.Height, y => {
                int pngY = spec.Height - 1 - y;
                for (int x = 0; x < spec.Width; x++)
                {
                    Complex value = values[y * spec.Width + x];
                    int quadrant = Quadrant(value);
                    Color color = !Finite(value) ? Color.Gray
                        : value == Complex.Zero ? Color.White : Palette[quadrant];
                    int offset = (pngY * spec.Width + x) * 4;
                    pixels[offset] = color.B;
                    pixels[offset + 1] = color.G;
                    pixels[offset + 2] = color.R;
                    pixels[offset + 3] = 255;
                }
            });
            var bitmap = new Bitmap(spec.Width, spec.Height, PixelFormat.Format32bppArgb);
            BitmapData data = bitmap.LockBits(new Rectangle(0, 0, spec.Width, spec.Height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try
            {
                for (int row = 0; row < spec.Height; row++)
                    Marshal.Copy(pixels, row * spec.Width * 4, IntPtr.Add(data.Scan0, row * data.Stride), spec.Width * 4);
            }
            finally { bitmap.UnlockBits(data); }
            return bitmap;
        }

        private static object ExportGrid(GridSpec spec, string root)
        {
            string binaryPath = Path.Combine(root, spec.Name + ".f64le");
            string texturePath = Path.Combine(root, spec.Name + "-a0.png");
            string metadataPath = Path.Combine(root, spec.Name + ".grid.json");
            var values = new Complex[checked(spec.Width * spec.Height)];
            int invalidCount = 0;
            var timer = Stopwatch.StartNew();
            Parallel.For(0, spec.Height, y => {
                double t = Height(spec, y);
                int invalidInRow = 0;
                for (int x = 0; x < spec.Width; x++)
                {
                    var s = new Complex(Sigma(spec, x), t);
                    Complex value = s == Complex.One ? Invalid : ZetaSwitchExperiment.Evaluate(s, Terms);
                    if (!Finite(value)) { value = Invalid; invalidInRow++; }
                    values[y * spec.Width + x] = value;
                }
                Interlocked.Add(ref invalidCount, invalidInRow);
            });
            timer.Stop();
            double calculationMilliseconds = timer.Elapsed.TotalMilliseconds;
            timer.Restart();
            using (var writer = new BinaryWriter(File.Create(binaryPath)))
                foreach (Complex value in values) { writer.Write(value.Real); writer.Write(value.Imaginary); }
            using (Bitmap texture = Texture(values, spec)) texture.Save(texturePath, ImageFormat.Png);
            timer.Stop();
            double serializationMilliseconds = timer.Elapsed.TotalMilliseconds;
            timer.Restart();
            object[] samples = {
                AuditPoint("lower-left", spec.MinSigma, spec.MinT),
                AuditPoint("lower-right", spec.MaxSigma, spec.MinT),
                AuditPoint("upper-left", spec.MinSigma, spec.MaxT),
                AuditPoint("upper-right", spec.MaxSigma, spec.MaxT),
                AuditPoint(spec.ZeroIndex.HasValue ? "input-zero-height-on-critical-line" : "critical-line-mid-height", 0.5,
                    spec.CenterT ?? (spec.MinT + spec.MaxT) / 2)
            };
            timer.Stop();
            var payload = new {
                schema = "graph-zeta-zero-index-grid-v1", traceId = "graph.riemann.zero_index.grid",
                id = spec.Name, zeroIndex = spec.ZeroIndex, centerT = spec.CenterT, sourceHeightDecimal = spec.SourceHeight,
                metadataFile = Path.GetFileName(metadataPath),
                width = spec.Width, height = spec.Height, pointCount = values.Length,
                domain = new { minSigma = spec.MinSigma, maxSigma = spec.MaxSigma, minT = spec.MinT, maxT = spec.MaxT,
                    sigmaStep = (spec.MaxSigma - spec.MinSigma) / (spec.Width - 1), tStep = (spec.MaxT - spec.MinT) / (spec.Height - 1) },
                evaluator = new { method = "Existing ZetaSwitchExperiment Euler-Maclaurin continuation",
                    terms = Terms, bernoulliCorrectionCount = 10, refinedAuditTerms = RefinedTerms,
                    arithmetic = "IEEE754 binary64", derivativeComputed = false,
                    accuracy = "Independent audit required;192/256agreement is not a rigorous error enclosure." },
                binary = new { file = Path.GetFileName(binaryPath), bytes = new FileInfo(binaryPath).Length,
                    expectedBytes = 16L * values.Length, sha256 = Hash(binaryPath),
                    scalar = "IEEE754 float64", endianness = "little", components = new[] { "real(zeta)", "imaginary(zeta)" },
                    layout = "row-major [y,x,component]; byteOffset=16*(y*width+x)",
                    xDirection = "sigma increases", yDirection = "t increases",
                    invalidEncoding = "Both components are IEEE754 NaN; invalid JSON values are null." },
                texture = new { file = Path.GetFileName(texturePath), sha256 = Hash(texturePath),
                    target = 0, displayedFunction = "zeta(s)", paletteRotationDegrees = 0,
                    xDirection = "left:minSigma;right:maxSigma", yDirection = "top:maxT;bottom:minT",
                    pixelsAreGridNodes = true, pixelToGrid = "texturePixel(x,pngY) corresponds to binaryGrid(x,height-1-pngY)",
                    palette = Palette.Select((color, index) => new { quadrant = index + 1, rgb = new[] { (int)color.R, color.G, color.B } }).ToArray(),
                    invalidRgb = new[] { 128, 128, 128 }, exactZeroRgb = new[] { 255, 255, 255 } },
                invalidCount, samples,
                timings = new { calculationMilliseconds, serializationMilliseconds, auditMilliseconds = timer.Elapsed.TotalMilliseconds },
                limits = new[] {
                    "Raw zeta values permit downstream recoloring by zeta(s)-a as the target changes.",
                    "No root trajectory is computed by this grid exporter; trajectories are separate evidence.",
                    "Zero ordinal and height select a viewport only; prime labels never enter the zeta evaluator.",
                    "Colors near a zero or axis can be sensitive to finite precision and grid resolution.",
                    "No RH proof, certified zeta enclosure or new prime relation is claimed."
                }
            };
            File.WriteAllText(metadataPath, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
            return payload;
        }

        // publish: graph.riemann.zero_index.grid.export
        internal static void Export(string zeroIndexJson, string outputDirectory)
        {
            string inputPath = Path.GetFullPath(zeroIndexJson);
            string root = Path.GetFullPath(outputDirectory);
            using JsonDocument input = JsonDocument.Parse(File.ReadAllText(inputPath));
            var rows = new Dictionary<int, string>();
            foreach (JsonElement row in input.RootElement.GetProperty("rows").EnumerateArray())
            {
                int index = row.GetProperty("zeroIndex").GetInt32();
                string height = row.GetProperty("height").GetString();
                if (index < 1 || index > 100 || string.IsNullOrWhiteSpace(height)) throw new InvalidDataException("Zero rows need unique indices1..100 and decimal-string heights.");
                rows.Add(index, height);
            }
            int[] selected = input.RootElement.GetProperty("selectedIndices").EnumerateArray().Select(v => v.GetInt32()).ToArray();
            if (selected.Length < 1 || selected.Length > 100 || selected.Distinct().Count() != selected.Length)
                throw new InvalidDataException("selectedIndices must contain1..100 distinct supplied indices.");
            var specs = new List<GridSpec> {
                new GridSpec { Name = "intro", Width = 400, Height = 320, MinSigma = 0.05, MaxSigma = 3, MinT = 10, MaxT = 30 }
            };
            foreach (int index in selected.OrderBy(v => v))
            {
                if (!rows.TryGetValue(index, out string sourceHeight)) throw new InvalidDataException("Selected zero index missing from rows: " + index);
                double center = double.Parse(sourceHeight, NumberStyles.Float, CultureInfo.InvariantCulture);
                if (!double.IsFinite(center) || center <= 0.35 || center > 1000)
                    throw new InvalidDataException("Use a finite zero height in(0.35,1000].");
                specs.Add(new GridSpec { Name = "Z" + index.ToString(CultureInfo.InvariantCulture),
                    ZeroIndex = index, CenterT = center, SourceHeight = sourceHeight,
                    Width = 320, Height = 300, MinSigma = 0.4, MaxSigma = 0.9, MinT = center - 0.35, MaxT = center + 0.35 });
            }
            Directory.CreateDirectory(root);
            string inputHash = Hash(inputPath);
            var grids = new List<object>();
            var timer = Stopwatch.StartNew();
            foreach (GridSpec spec in specs)
            {
                grids.Add(ExportGrid(spec, root));
                File.WriteAllText(Path.Combine(root, "grids.json"), JsonSerializer.Serialize(new {
                    schema = "graph-zeta-zero-index-grids-v1", traceId = "graph.riemann.zero_index.grid.export",
                    status = grids.Count == specs.Count ? "complete" : "running",
                    input = new { file = inputPath, sha256 = inputHash, consumedFields = new[] { "selectedIndices", "rows.zeroIndex", "rows.height" } },
                    selectedIndices = selected.OrderBy(v => v).ToArray(), totalGrids = specs.Count, completedGrids = grids.Count,
                    grids, elapsedMilliseconds = timer.Elapsed.TotalMilliseconds,
                    scope = "Numerical phase grids only. The supplied zero heights and separate continuation paths need their own validation."
                }, new JsonSerializerOptions { WriteIndented = true }));
            }
        }
    }
}
