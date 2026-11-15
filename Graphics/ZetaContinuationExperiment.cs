using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
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
    // defines: graph.riemann.continuation.animation.model
    // consumer: graph.riemann.switch.model
    internal static class ZetaContinuationExperiment
    {
        private const double MinSigma = 0.05, MaxSigma = 3, MinT = 10, MaxT = 30;
        private const double InitialStep = 0.025, MaximumStep = 0.04, MinimumStep = 1e-7;
        private const double DerivativeGuard = 1e-8, ResidualTolerance = 2e-11;
        private const double PredictionMotionLimit = 0.06, AcceptedMotionLimit = 0.09, CorrectionLimit = 0.001;
        private static readonly double[] InitialHeights = { 14.134725141734694, 21.022039638771555, 25.01085758014569 };
        private static readonly Lazy<ContinuationData> CachedPaths = new Lazy<ContinuationData>(CalculatePaths);
        private static readonly ConcurrentDictionary<int, Complex[]> BackgroundGrids = new ConcurrentDictionary<int, Complex[]>();
        private static readonly Rectangle Plot = new Rectangle(92, 192, 920, 650);
        private static readonly Color[] PhaseColors = { Color.FromArgb(27, 115, 94), Color.FromArgb(136, 102, 39), Color.FromArgb(101, 60, 133), Color.FromArgb(39, 77, 136) };
        private static readonly Color[] PathColors = { Color.FromArgb(255, 225, 101), Color.FromArgb(112, 240, 255), Color.FromArgb(255, 151, 219) };

        internal sealed class PathPoint
        {
            internal double A, Residual, Step, PredictionError;
            internal Complex S, Derivative;
            internal int NewtonIterations;
        }
        internal sealed class Trajectory
        {
            internal string Id, Status, StopReason;
            internal int Index;
            internal readonly List<PathPoint> Points = new List<PathPoint>();
            internal readonly List<object> RejectedSteps = new List<object>();
            internal PathPoint Outside;
        }
        internal sealed class ContinuationData
        {
            internal IReadOnlyList<Trajectory> Trajectories { get; }
            internal ContinuationData(IReadOnlyList<Trajectory> trajectories) { Trajectories = trajectories; }
        }
        internal sealed class Frame : IDisposable
        {
            internal Bitmap Image { get; }
            internal string Report { get; }
            internal object Snapshot { get; }
            internal double Target { get; }
            internal Frame(Bitmap image, string report, object snapshot, double target)
            { Image = image; Report = report; Snapshot = snapshot; Target = target; }
            public void Dispose() => Image.Dispose();
        }
        private sealed class DisplayState
        {
            internal Trajectory Trajectory;
            internal PathPoint Point;
            internal string Status;
        }

        private static bool Finite(Complex z) => double.IsFinite(z.Real) && double.IsFinite(z.Imaginary);
        private static bool Inside(Complex s) => s.Real >= MinSigma && s.Real <= MaxSigma && s.Imaginary >= MinT && s.Imaginary <= MaxT;
        private static PathPoint Measure(double a, Complex s, double step = 0, double error = 0, int iterations = 0)
            => new PathPoint { A = a, S = s, Derivative = ZetaSwitchExperiment.Derivative(s),
                Residual = (ZetaSwitchExperiment.Evaluate(s) - a).Magnitude, Step = step,
                PredictionError = error, NewtonIterations = iterations };

        internal static ContinuationData ComputePaths() => CachedPaths.Value;

        private static bool Correct(PathPoint previous, double target, out PathPoint point, out string reason)
        {
            point = null;
            reason = "";
            if (!Finite(previous.Derivative) || previous.Derivative.Magnitude < DerivativeGuard)
            { reason = "low-derivative"; return false; }
            double step = target - previous.A;
            Complex prediction = previous.S + step / previous.Derivative;
            if ((prediction - previous.S).Magnitude > PredictionMotionLimit * (1 + 1e-10))
            { reason = "predicted-motion-limit"; return false; }
            Complex current = prediction;
            int iterations;
            for (iterations = 0; iterations < 16; iterations++)
            {
                Complex value = ZetaSwitchExperiment.Evaluate(current) - target;
                if (!Finite(value)) { reason = "invalid-value"; return false; }
                if (value.Magnitude <= ResidualTolerance) break;
                Complex derivative = ZetaSwitchExperiment.Derivative(current);
                if (!Finite(derivative) || derivative.Magnitude < DerivativeGuard)
                { reason = "low-derivative"; return false; }
                Complex correction = value / derivative;
                if (correction.Magnitude > AcceptedMotionLimit)
                { reason = "newton-motion-limit"; return false; }
                current -= correction;
            }
            if (iterations == 16) { reason = "newton-iteration-limit"; return false; }
            double error = (current - prediction).Magnitude;
            if (error > CorrectionLimit) { reason = "prediction-error-limit"; return false; }
            if ((current - previous.S).Magnitude > AcceptedMotionLimit)
            { reason = "accepted-motion-limit"; return false; }
            point = Measure(target, current, step, error, iterations);
            if (!Finite(point.Derivative) || point.Residual > ResidualTolerance)
            { reason = "residual-or-derivative-invalid"; point = null; return false; }
            return true;
        }

        private static ContinuationData CalculatePaths()
        {
            var paths = new List<Trajectory>();
            for (int index = 0; index < InitialHeights.Length; index++)
            {
                var trajectory = new Trajectory { Id = "Z" + (index + 1), Index = index + 1, Status = "stopped", StopReason = "attempt-limit" };
                PathPoint current = Measure(0, new Complex(0.5, InitialHeights[index]));
                if (current.Residual > ResidualTolerance) throw new InvalidOperationException("Initial zero failed its native residual check.");
                trajectory.Points.Add(current);
                double step = InitialStep;
                for (int attempt = 0; attempt < 10000; attempt++)
                {
                    if (current.A >= 1) { trajectory.Status = "completed"; trajectory.StopReason = "target-one-reached"; break; }
                    if (current.Derivative.Magnitude < DerivativeGuard)
                    { trajectory.StopReason = "low-derivative"; break; }
                    step = Math.Min(step, PredictionMotionLimit * current.Derivative.Magnitude);
                    double next = Math.Min(1, current.A + step);
                    if (next - current.A < MinimumStep && 1 - current.A > MinimumStep)
                    { trajectory.StopReason = "minimum-step"; break; }
                    if (!Correct(current, next, out PathPoint candidate, out string reason))
                    {
                        trajectory.RejectedSteps.Add(new { a = current.A, attemptedA = next, step = next - current.A, reason });
                        step *= 0.5;
                        if (step < MinimumStep) { trajectory.StopReason = reason + "/minimum-step"; break; }
                        continue;
                    }
                    if (!Inside(candidate.S))
                    {
                        RefineExit(trajectory, current, candidate);
                        break;
                    }
                    trajectory.Points.Add(candidate);
                    current = candidate;
                    if (candidate.PredictionError < 0.0002) step = Math.Min(MaximumStep, step * 1.35);
                    else if (candidate.PredictionError > 0.0008) step *= 0.8;
                }
                paths.Add(trajectory);
            }
            return new ContinuationData(paths);
        }

        private static void RefineExit(Trajectory trajectory, PathPoint initialInside, PathPoint initialOutside)
        {
            PathPoint inside = initialInside, outside = initialOutside;
            for (int iteration = 0; iteration < 60 && outside.A - inside.A > 1e-10; iteration++)
            {
                double target = (inside.A + outside.A) / 2;
                if (!Correct(inside, target, out PathPoint middle, out string reason))
                {
                    trajectory.Status = "stopped";
                    trajectory.StopReason = "boundary-refinement-failed/" + reason;
                    trajectory.Outside = outside;
                    return;
                }
                if (Inside(middle.S))
                {
                    inside = middle;
                    // Retain every accepted inside refinement so step and predictor
                    // diagnostics remain relative to the preceding exported point.
                    trajectory.Points.Add(inside);
                }
                else outside = middle;
            }
            trajectory.Outside = outside;
            trajectory.Status = "exited";
            trajectory.StopReason = "viewport-exit";
        }

        private static object C(Complex value) => new { real = value.Real, imaginary = value.Imaginary };
        private static object P(PathPoint point) => new { a = point.A, s = C(point.S), derivative = C(point.Derivative),
            residual = point.Residual, step = point.Step, predictionError = point.PredictionError, newtonIterations = point.NewtonIterations };
        private static string[] ExitBoundaries(Complex s) => new[]
            { s.Real < MinSigma ? "minSigma" : null, s.Real > MaxSigma ? "maxSigma" : null,
              s.Imaginary < MinT ? "minT" : null, s.Imaginary > MaxT ? "maxT" : null }.Where(x => x != null).ToArray();
        private static object TrajectorySnapshot(Trajectory path)
        {
            PathPoint endpoint = path.Points.Last();
            return new { id = path.Id, startZeroIndex = path.Index, status = path.Status, stopReason = path.StopReason,
                points = path.Points.Select(P).ToArray(), rejectedSteps = path.RejectedSteps.ToArray(), endpoint = P(endpoint),
                exit = path.Outside == null ? null : new { inside = P(endpoint), outside = P(path.Outside),
                    widthA = path.Outside.A - endpoint.A, boundaries = ExitBoundaries(path.Outside.S) } };
        }

        private static DisplayState DisplayAt(Trajectory trajectory, double target)
        {
            PathPoint endpoint = trajectory.Points.Last();
            if (target > endpoint.A + 1e-12)
                return new DisplayState { Trajectory = trajectory, Point = endpoint,
                    Status = trajectory.Status == "exited" ? "exited" : "stopped" };
            PathPoint previous = trajectory.Points.Last(p => p.A <= target + 1e-13);
            if (Math.Abs(previous.A - target) < 1e-12)
                return new DisplayState { Trajectory = trajectory, Point = previous,
                    Status = target == 1 ? "completed" : "active" };
            if (Correct(previous, target, out PathPoint point, out string reason))
                return new DisplayState { Trajectory = trajectory, Point = point,
                    Status = target == 1 ? "completed" : "active" };
            return new DisplayState { Trajectory = trajectory, Point = previous, Status = "display-correction-failed/" + reason };
        }

        private static Complex[] Grid(int resolution) => BackgroundGrids.GetOrAdd(resolution, count =>
        {
            var grid = new Complex[count * count];
            Parallel.For(0, count, y =>
            {
                double t = MaxT - (MaxT - MinT) * y / (count - 1);
                for (int x = 0; x < count; x++) grid[y * count + x] = ZetaSwitchExperiment.Evaluate(
                    new Complex(MinSigma + (MaxSigma - MinSigma) * x / (count - 1), t));
            });
            return grid;
        });

        private static Bitmap Background(int resolution, double target, double rotation)
        {
            Complex[] grid = Grid(resolution);
            byte[] pixels = new byte[resolution * resolution * 4];
            Parallel.For(0, resolution, y =>
            {
                for (int x = 0; x < resolution; x++)
                {
                    int index = y * resolution + x;
                    Complex z = grid[index] - target;
                    double angle = (z.Phase - rotation * Math.PI / 180) % (2 * Math.PI);
                    if (angle < 0) angle += 2 * Math.PI;
                    Color color = !Finite(z) ? Color.Gray : z == Complex.Zero ? Color.White
                        : PhaseColors[Math.Min(3, (int)(angle / (Math.PI / 2)))];
                    int offset = index * 4;
                    pixels[offset] = color.B; pixels[offset + 1] = color.G; pixels[offset + 2] = color.R; pixels[offset + 3] = 255;
                }
            });
            var bitmap = new Bitmap(resolution, resolution, PixelFormat.Format32bppArgb);
            BitmapData data = bitmap.LockBits(new Rectangle(0, 0, resolution, resolution), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try
            { for (int y = 0; y < resolution; y++) Marshal.Copy(pixels, y * resolution * 4, IntPtr.Add(data.Scan0, y * data.Stride), resolution * 4); }
            finally { bitmap.UnlockBits(data); }
            return bitmap;
        }

        // consumer: graph.riemann.continuation.animation.render
        internal static Bitmap RenderPhase(double target, int resolution = 256, double rotation = 0)
        {
            if (!double.IsFinite(target) || target < 0 || target > 1) throw new ArgumentOutOfRangeException(nameof(target));
            if (resolution < 64 || resolution > 512) throw new ArgumentOutOfRangeException(nameof(resolution));
            if (!double.IsFinite(rotation)) throw new ArgumentOutOfRangeException(nameof(rotation));
            return Background(resolution, target, rotation);
        }

        private static PointF Screen(Complex s) => new PointF(
            (float)(Plot.Left + (s.Real - MinSigma) / (MaxSigma - MinSigma) * Plot.Width),
            (float)(Plot.Bottom - (s.Imaginary - MinT) / (MaxT - MinT) * Plot.Height));

        // defines: graph.riemann.continuation.animation.render
        internal static Frame Render(ContinuationData paths, double target, int resolution = 256, double rotation = 0)
        {
            if (paths == null) throw new ArgumentNullException(nameof(paths));
            if (!double.IsFinite(target) || target < 0 || target > 1) throw new ArgumentOutOfRangeException(nameof(target));
            if (resolution < 64 || resolution > 512) throw new ArgumentOutOfRangeException(nameof(resolution));
            if (!double.IsFinite(rotation)) throw new ArgumentOutOfRangeException(nameof(rotation));
            DisplayState[] states = paths.Trajectories.Select(p => DisplayAt(p, target)).ToArray();
            var image = new Bitmap(1440, 1040);
            using var g = System.Drawing.Graphics.FromImage(image);
            g.Clear(Color.FromArgb(13, 18, 30));
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            using var title = new Font("Segoe UI", 31, FontStyle.Bold, GraphicsUnit.Pixel);
            using var heading = new Font("Segoe UI", 23, FontStyle.Bold, GraphicsUnit.Pixel);
            using var body = new Font("Segoe UI", 17, FontStyle.Regular, GraphicsUnit.Pixel);
            using var small = new Font("Segoe UI", 14, FontStyle.Regular, GraphicsUnit.Pixel);
            using var ink = new SolidBrush(Color.FromArgb(238, 244, 252));
            using var muted = new SolidBrush(Color.FromArgb(181, 196, 216));
            g.DrawString("FOLLOWING ζ(s) = a", title, ink, 30, 24);
            g.DrawString("Three zeta zeros start moving as the real target a increases from 0 to 1.", body, muted, 32, 72);
            g.DrawString($"a = {target:F4}     local velocity ds/da = 1/ζ′(s)     grid {resolution}²     palette {rotation:G5}°", heading, ink, 32, 112);
            using (Bitmap raster = Background(resolution, target, rotation))
            {
                g.InterpolationMode = InterpolationMode.NearestNeighbor;
                g.PixelOffsetMode = PixelOffsetMode.Half;
                g.DrawImage(raster, Plot);
                g.PixelOffsetMode = PixelOffsetMode.Default;
            }
            using var critical = new Pen(Color.White, 1.3f) { DashStyle = DashStyle.Dash };
            float criticalX = Screen(new Complex(0.5, MinT)).X;
            g.DrawLine(critical, criticalX, Plot.Top, criticalX, Plot.Bottom);
            using var border = new Pen(Color.FromArgb(170, 190, 210));
            g.DrawRectangle(border, Plot);
            foreach (double sigma in new[] { 0.05, 0.5, 1, 1.5, 2, 2.5, 3 })
            {
                PointF point = Screen(new Complex(sigma, MinT));
                string label = sigma.ToString("G3", System.Globalization.CultureInfo.InvariantCulture);
                float width = g.MeasureString(label, small).Width;
                g.DrawString(label, small, muted, point.X - width / 2, Plot.Bottom + 10);
            }
            foreach (double t in new[] { 10.0, 15, 20, 25, 30 })
            {
                float y = Screen(new Complex(MinSigma, t)).Y;
                g.DrawString(t.ToString("G3"), small, muted, Plot.Left - 38, y - 9);
            }
            g.DrawString("height t", small, muted, Plot.Left - 15, Plot.Top - 28);
            g.DrawString("real part σ", body, muted, Plot.Right - 90, Plot.Bottom + 38);
            for (int index = 0; index < states.Length; index++)
            {
                DisplayState state = states[index];
                Trajectory trajectory = state.Trajectory;
                Color color = PathColors[index];
                using var future = new Pen(Color.FromArgb(185, 208, 217, 230), 1.5f) { DashStyle = DashStyle.Dash };
                using var under = new Pen(Color.FromArgb(15, 18, 28), 6);
                using var history = new Pen(color, 3.2f);
                using var colored = new SolidBrush(color);
                using var dark = new SolidBrush(Color.FromArgb(13, 18, 30));
                PointF[] all = trajectory.Points.Select(p => Screen(p.S)).ToArray();
                if (all.Length > 1) g.DrawLines(future, all);
                var past = trajectory.Points.Where(p => p.A <= state.Point.A).Select(p => Screen(p.S)).ToList();
                if (past.Count == 0 || past.Last() != Screen(state.Point.S)) past.Add(Screen(state.Point.S));
                if (past.Count > 1) { g.DrawLines(under, past.ToArray()); g.DrawLines(history, past.ToArray()); }
                PointF origin = Screen(trajectory.Points[0].S);
                g.FillEllipse(dark, origin.X - 6, origin.Y - 6, 12, 12);
                g.DrawEllipse(Pens.White, origin.X - 6, origin.Y - 6, 12, 12);
                g.DrawString(trajectory.Id + " start", small, ink, origin.X + 10, origin.Y + 5);
                PointF current = Screen(state.Point.S);
                if (state.Status == "exited")
                { g.FillRectangle(dark, current.X - 7, current.Y - 7, 14, 14); g.DrawRectangle(history, current.X - 7, current.Y - 7, 14, 14); }
                else
                { g.FillEllipse(dark, current.X - 8, current.Y - 8, 16, 16); g.DrawEllipse(history, current.X - 8, current.Y - 8, 16, 16); }
                float lx = Math.Min(Plot.Right - 29, current.X + 10);
                g.DrawString(trajectory.Id, small, colored, lx, current.Y - 24);
                int cardY = 192 + index * 205;
                using var card = new SolidBrush(Color.FromArgb(24, 32, 49));
                g.FillRectangle(card, 1050, cardY, 360, 190);
                g.DrawString(trajectory.Id + "   " + state.Status.ToUpperInvariant(), heading, colored, 1068, cardY + 14);
                g.DrawString($"σ = {state.Point.S.Real:F9}\nt = {state.Point.S.Imaginary:F9}", body, ink, 1068, cardY + 53);
                string condition = state.Status == "exited" ? $"Left this view at a ≈ {state.Point.A:F9}.\nSquare holds the last inside point."
                    : state.Status == "stopped" ? "Stopped: " + trajectory.StopReason
                    : $"|ζ(s) − {state.Point.A:G6}| = {state.Point.Residual:E2}\n|ζ′(s)| = {state.Point.Derivative.Magnitude:G6}";
                g.DrawString(condition, small, muted, new RectangleF(1068, cardY + 112, 326, 66));
            }
            g.DrawString("SOLID: accepted path so far    DASHED: precomputed future    WHITE CIRCLE: original zero    SQUARE: viewport exit", small, ink, 32, 916);
            g.DrawString("Background: phase quadrant of ζ(s) − a. Dashed vertical line: σ = ½. Palette rotation affects display only.", small, muted, 32, 947);
            g.DrawString("Adaptive predictor + Newton correction; rejected steps shrink. A viewport exit is not a vanished zero. No reseeding is used.", small, muted, 32, 974);
            g.DrawString("Paths, residuals and boundary brackets are empirical floating-point evidence, not certified continuation or an RH proof.", small, muted, 32, 1001);

            var backgroundSamples = new List<object>();
            for (int y = 0; y < 5; y++)
                for (int x = 0; x < 6; x++)
                {
                    Complex s = new Complex(MinSigma + (MaxSigma - MinSigma) * x / 5, MinT + (MaxT - MinT) * y / 4);
                    Complex z = ZetaSwitchExperiment.Evaluate(s);
                    backgroundSamples.Add(new { s = C(s), zeta = C(z), shifted = C(z - target) });
                }
            object snapshot = new
            {
                schema = "graph-zeta-continuation-v1", traceId = "graph.riemann.continuation.animation",
                domain = new { minSigma = MinSigma, maxSigma = MaxSigma, minT = MinT, maxT = MaxT },
                settings = new { initialStep = InitialStep, maxStep = MaximumStep, minStep = MinimumStep,
                    derivativeGuard = DerivativeGuard, residualTolerance = ResidualTolerance,
                    predictionMotionLimit = PredictionMotionLimit, acceptedMotionLimit = AcceptedMotionLimit,
                    predictorCorrectionLimit = CorrectionLimit, boundaryToleranceA = 1e-10, reseeding = false },
                target, resolution, paletteDegrees = rotation,
                trajectories = paths.Trajectories.Select(TrajectorySnapshot).ToArray(),
                displayedStates = states.Select(state => new { id = state.Trajectory.Id, status = state.Status,
                    point = P(state.Point), heldAtEarlierTarget = state.Point.A < target - 1e-12 }).ToArray(),
                backgroundSamples,
                limitations = new[] { "Floating-point Newton continuation and empirical residual checks; no certified interval enclosures.",
                    "First exits are bracketed numerically, and plotted roots are held at the last inside point after exit.",
                    "Three specified starting zeros only; no claim about all zeros or the Riemann Hypothesis." }
            };
            string report = $"Zeta continuation at real target a={target:G8}; fixed view sigma[0.05,3], t[10,30].\n"
                + string.Join("\n", states.Select(s => $"{s.Trajectory.Id}: {s.Status}; point target={s.Point.A:G12}; s={s.Point.S.Real:G13}+{s.Point.S.Imaginary:G13}i; residual={s.Point.Residual:E3}."))
                + "\nSolid path is accepted history; dashed path is the computed future. Exited markers hold a previous target's boundary point."
                + "\nAdaptive predictor/Newton, no reseeding. Empirical floating-point continuation; not certified and not an RH proof.";
            return new Frame(image, report, snapshot, target);
        }

        internal static void Export(string pngPath, Frame frame)
        {
            string path = Path.GetFullPath(pngPath);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            frame.Image.Save(path, ImageFormat.Png);
            File.WriteAllText(Path.ChangeExtension(path, ".values.json"), JsonSerializer.Serialize(frame.Snapshot, new JsonSerializerOptions { WriteIndented = true }));
            File.WriteAllText(Path.ChangeExtension(path, ".txt"), frame.Report);
        }

        internal static bool TryMapPixel(float x, float y, out Complex s)
        {
            if (x < Plot.Left || x > Plot.Right || y < Plot.Top || y > Plot.Bottom) { s = Complex.Zero; return false; }
            s = new Complex(MinSigma + (MaxSigma - MinSigma) * (x - Plot.Left) / Plot.Width,
                MaxT - (MaxT - MinT) * (y - Plot.Top) / Plot.Height);
            return true;
        }
        internal static string DescribePoint(Complex s, double target)
        {
            Complex value = ZetaSwitchExperiment.Evaluate(s);
            return $"s={s.Real:G8}+{s.Imaginary:G8}i; ζ(s)={value.Real:G8}{(value.Imaginary < 0 ? "" : "+")}{value.Imaginary:G8}i; "
                + $"|ζ(s)−a|={(value - target).Magnitude:G8} at a={target:G6}.";
        }

        // defines: graph.riemann.continuation.animation.verify
        internal static string Verify(ContinuationData data)
        {
            int points = 0;
            foreach (Trajectory path in data.Trajectories)
            {
                if (path.Points.Count < 2 || path.Points[0].A != 0) throw new InvalidOperationException("Missing trajectory origin.");
                PathPoint previous = null;
                foreach (PathPoint point in path.Points)
                {
                    if (!Inside(point.S) || point.Residual > ResidualTolerance || !Finite(point.Derivative))
                        throw new InvalidOperationException("Invalid accepted trajectory point.");
                    if (previous != null && (point.A <= previous.A || (point.S - previous.S).Magnitude > AcceptedMotionLimit + 1e-8))
                        throw new InvalidOperationException("Trajectory order or motion bound failed.");
                    previous = point; points++;
                }
                if (path.Status == "exited" && (path.Outside == null || Inside(path.Outside.S)
                    || path.Outside.A - path.Points.Last().A > 1e-10)) throw new InvalidOperationException("Exit bracket failed.");
                if (path.Status == "completed" && path.Points.Last().A != 1) throw new InvalidOperationException("Completed trajectory does not reach one.");
                if (path.Status == "stopped") throw new InvalidOperationException("Unresolved continuation stop: " + path.StopReason);
            }
            return $"{data.Trajectories.Count} trajectories and {points} accepted points pass residual, motion, ordering and explicit endpoint checks. Independent high-precision validation is separate; these are not certified enclosures.";
        }
    }
}
