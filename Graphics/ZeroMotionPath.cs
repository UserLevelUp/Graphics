using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;

namespace Graphics
{
    // defines: graph.zeros.motion.path
    internal static class ZeroMotionPath
    {
        private const double Tau = 2 * Math.PI;
        private const double CoefficientTolerance = 1e-12;
        private const double ParameterTolerance = 1e-10;
        private const double MachineEpsilon = 2.2204460492503131e-16;
        private const double NearRootRelativeDistance = 1e-7;

        private sealed class BoundaryEvent
        {
            public double T;
            public string Boundary;
            public string Kind;
            public Complex Point;
        }

        private sealed class ZeroEvent
        {
            public double T;
            public Complex Point;
            public int Multiplicity;
        }

        private sealed class Integral
        {
            public bool Allowed;
            public bool Converged;
            public double? Phase;
            public int Intervals;
            public double? EmpiricalDifference;
            public double? ReferenceDifference;
            public string Status;
        }

        private sealed class Result
        {
            public Complex Start, End, StartValue, EndValue;
            public double Lambda, PaletteDegrees;
            public double? FirstOrder, ContinuousPhase, PrincipalPhase, RawEndpointDifference;
            public int? ExtraFullTurns;
            public bool ZeroLength, RealCoincidence, ImaginaryCoincidence;
            public double ClosestRootDistance, NearRootGuard, GeometricTolerance;
            public List<ZeroEvent> Zeros = new List<ZeroEvent>();
            public List<BoundaryEvent> Events = new List<BoundaryEvent>();
            public Integral Integration;
        }

        private static bool Finite(Complex value) => double.IsFinite(value.Real) && double.IsFinite(value.Imaginary);
        private static double Principal(double phase) => Math.Atan2(Math.Sin(phase), Math.Cos(phase));
        private static object Coordinates(Complex value) => new { real = value.Real, imaginary = value.Imaginary };

        public static object Analyze(Complex start, Complex end, double lambda, double paletteDegrees)
            => Evidence(Evaluate(start, end, lambda, paletteDegrees));

        private static object Evidence(Result value) => new
        {
            start = Coordinates(value.Start), end = Coordinates(value.End), lambda = value.Lambda,
            paletteDegrees = value.PaletteDegrees, zeroLength = value.ZeroLength,
            startValue = Coordinates(value.StartValue), endValue = Coordinates(value.EndValue),
            firstOrderPhaseRadians = value.FirstOrder, continuousPhaseChangeRadians = value.ContinuousPhase,
            principalEndpointChangeRadians = value.PrincipalPhase,
            rawEndpointPhaseDifferenceRadians = value.RawEndpointDifference, extraFullTurns = value.ExtraFullTurns,
            closestRootDistance = value.ClosestRootDistance, nearZeroGuard = value.NearRootGuard,
            zeros = value.Zeros.Select(zero => new { t = zero.T, point = Coordinates(zero.Point), multiplicity = zero.Multiplicity }).ToArray(),
            boundaryEvents = value.Events.Select(item => new { t = item.T, boundary = item.Boundary,
                kind = item.Kind, point = Coordinates(item.Point) }).ToArray(),
            boundaryCoincidence = new { real = value.RealCoincidence, imaginary = value.ImaginaryCoincidence },
            boundaryMeaning = "real means Re(exp(-i*paletteAngle)*F)=0; imaginary means Im(exp(-i*paletteAngle)*F)=0.",
            integration = new { allowed = value.Integration.Allowed, converged = value.Integration.Converged,
                phaseRadians = value.Integration.Phase, intervals = value.Integration.Intervals,
                empiricalDifference = value.Integration.EmpiricalDifference,
                referenceDifference = value.Integration.ReferenceDifference, status = value.Integration.Status },
            tolerances = new { coefficientRelative = CoefficientTolerance, parameter = ParameterTolerance,
                geometric = value.GeometricTolerance, nearRootRelativeDistance = NearRootRelativeDistance,
                note = "Floating-point tolerances and Simpson refinement provide empirical checks, without certified error bounds." }
        };

        private static Result Evaluate(Complex start, Complex end, double lambda, double paletteDegrees)
        {
            var roots = ZeroMotionExperiment.Roots(lambda);
            if (!Finite(start) || !Finite(end) || !double.IsFinite(paletteDegrees))
                throw new ArgumentOutOfRangeException(nameof(start), "Path coordinates and palette angle must be finite.");
            Complex direction = end - start;
            Complex quadratic = direction * direction;
            Complex linear = 2 * start * direction;
            Complex constant = ZeroMotionExperiment.Value(start, lambda);
            Complex finish = ZeroMotionExperiment.Value(end, lambda);
            if (!Finite(quadratic) || !Finite(linear) || !Finite(constant) || !Finite(finish))
                throw new ArgumentOutOfRangeException(nameof(start), "The path exceeds the polynomial evaluator's finite range.");
            double scale = Math.Max(1, Math.Max(start.Magnitude, Math.Max(end.Magnitude, roots.A.Magnitude)));
            var result = new Result
            {
                Start = start, End = end, Lambda = lambda, PaletteDegrees = paletteDegrees,
                StartValue = constant, EndValue = finish, ZeroLength = direction == Complex.Zero,
                ClosestRootDistance = double.PositiveInfinity,
                NearRootGuard = NearRootRelativeDistance * scale,
                GeometricTolerance = 64 * MachineEpsilon * scale
            };
            InspectRoot(result, roots.A, lambda == 0 ? 2 : 1, direction);
            if (lambda != 0) InspectRoot(result, roots.B, 1, direction);
            result.Zeros.Sort((first, second) => first.T.CompareTo(second.T));

            if (constant != Complex.Zero && finish != Complex.Zero)
            {
                result.RawEndpointDifference = finish.Phase - constant.Phase;
                result.PrincipalPhase = Principal(result.RawEndpointDifference.Value);
            }
            if (constant != Complex.Zero)
                result.FirstOrder = (2 * start / constant * direction).Imaginary;

            bool safe = result.Zeros.Count == 0 && result.ClosestRootDistance > result.NearRootGuard;
            if (safe)
            {
                double firstTurn = FactorTurn(start - roots.A, end - roots.A);
                double secondTurn = FactorTurn(start - roots.B, end - roots.B);
                result.ContinuousPhase = firstTurn + secondTurn;
                result.ExtraFullTurns = (int)Math.Round((result.ContinuousPhase.Value - result.PrincipalPhase.Value) / Tau);
                result.Integration = Integrate(start, direction, lambda, result.ContinuousPhase.Value);
            }
            else
            {
                result.Integration = new Integral { Allowed = false, Status = result.Zeros.Count > 0
                    ? "The segment meets a zero. Continuous phase transport is singular."
                    : "The segment is within the empirical root-distance guard. Integration was skipped." };
            }

            Complex rotation = Complex.FromPolarCoordinates(1, -(paletteDegrees % 360) * Math.PI / 180);
            quadratic *= rotation;
            linear *= rotation;
            constant *= rotation;
            double coefficientScale = Math.Max(quadratic.Magnitude, Math.Max(linear.Magnitude, constant.Magnitude));
            result.RealCoincidence = AddBoundaryEvents(result, direction, "real", quadratic.Real,
                linear.Real, constant.Real, coefficientScale);
            result.ImaginaryCoincidence = AddBoundaryEvents(result, direction, "imaginary", quadratic.Imaginary,
                linear.Imaginary, constant.Imaginary, coefficientScale);
            result.Events.Sort((first, second) => first.T.CompareTo(second.T));
            return result;
        }

        private static void InspectRoot(Result result, Complex root, int multiplicity, Complex direction)
        {
            double length = direction.Magnitude;
            double parameter = length == 0 ? 0 : ((root - result.Start) * Complex.Conjugate(direction / length)).Real / length;
            double clamped = Math.Clamp(parameter, 0, 1);
            Complex nearest = result.Start + clamped * direction;
            double distance = (nearest - root).Magnitude;
            result.ClosestRootDistance = Math.Min(result.ClosestRootDistance, distance);
            if (distance <= result.GeometricTolerance && parameter >= -ParameterTolerance && parameter <= 1 + ParameterTolerance)
                result.Zeros.Add(new ZeroEvent { T = clamped, Point = root, Multiplicity = multiplicity });
        }

        private static double FactorTurn(Complex start, Complex end)
        {
            Complex product = (end / end.Magnitude) * Complex.Conjugate(start / start.Magnitude);
            return Math.Atan2(product.Imaginary, product.Real);
        }

        private static bool AddBoundaryEvents(Result result, Complex direction, string boundary,
            double quadratic, double linear, double constant, double scale)
        {
            double tolerance = CoefficientTolerance * scale;
            if (Math.Abs(quadratic) <= tolerance && Math.Abs(linear) <= tolerance && Math.Abs(constant) <= tolerance)
                return true;
            List<double> roots = SolvePolynomial(quadratic, linear, constant, tolerance);
            var parameters = roots.Where(t => t >= -ParameterTolerance && t <= 1 + ParameterTolerance)
                .Select(t => Math.Clamp(t, 0, 1)).OrderBy(t => t).ToList();
            for (int index = 0; index < parameters.Count; index++)
            {
                double t = parameters[index];
                if (index > 0 && Math.Abs(t - parameters[index - 1]) <= ParameterTolerance) continue;
                string kind;
                if (t <= ParameterTolerance || t >= 1 - ParameterTolerance)
                    kind = "endpoint";
                else if (result.Zeros.Any(zero => Math.Abs(zero.T - t) <= ParameterTolerance))
                    kind = "zero";
                else
                {
                    double previous = index == 0 ? 0 : parameters[index - 1];
                    double next = index == parameters.Count - 1 ? 1 : parameters[index + 1];
                    double left = (previous + t) / 2;
                    double right = (t + next) / 2;
                    double before = (quadratic * left + linear) * left + constant;
                    double after = (quadratic * right + linear) * right + constant;
                    kind = Math.Abs(before) <= tolerance || Math.Abs(after) <= tolerance ? "unresolved"
                        : Math.Sign(before) == Math.Sign(after) ? "tangency" : "crossing";
                }
                result.Events.Add(new BoundaryEvent { T = t, Boundary = boundary, Kind = kind,
                    Point = result.Start + t * direction });
            }
            return false;
        }

        private static List<double> SolvePolynomial(double quadratic, double linear, double constant, double tolerance)
        {
            if (Math.Abs(quadratic) <= tolerance)
                return Math.Abs(linear) <= tolerance ? new List<double>() : new List<double> { -constant / linear };
            double scale = Math.Max(Math.Abs(quadratic), Math.Max(Math.Abs(linear), Math.Abs(constant)));
            double a = quadratic / scale, b = linear / scale, c = constant / scale;
            double discriminant = b * b - 4 * a * c;
            double allowance = 64 * MachineEpsilon * (b * b + Math.Abs(4 * a * c));
            if (discriminant < -allowance) return new List<double>();
            if (Math.Abs(discriminant) <= allowance) return new List<double> { -b / (2 * a) };
            double q = -0.5 * (b + Math.CopySign(Math.Sqrt(discriminant), b));
            return new List<double> { q / a, c / q };
        }

        private static Integral Integrate(Complex start, Complex direction, double lambda, double reference)
        {
            if (direction == Complex.Zero)
                return new Integral { Allowed = true, Converged = true, Phase = 0, Intervals = 0,
                    EmpiricalDifference = 0, ReferenceDifference = 0, Status = "Zero-length path." };
            double Simpson(int intervals)
            {
                double sum = 0;
                for (int i = 0; i <= intervals; i++)
                {
                    Complex z = start + direction * ((double)i / intervals);
                    double value = (2 * z / ZeroMotionExperiment.Value(z, lambda) * direction).Imaginary;
                    int weight = i == 0 || i == intervals ? 1 : i % 2 == 0 ? 2 : 4;
                    sum += weight * value;
                }
                return sum / (3 * intervals);
            }
            int count = 16;
            double previous = Simpson(count);
            double difference = double.PositiveInfinity;
            double current = previous;
            int consecutive = 0;
            while (count < 65536)
            {
                count *= 2;
                current = Simpson(count);
                difference = Math.Abs(current - previous);
                double tolerance = 1e-10 * Math.Max(1, Math.Abs(current));
                consecutive = difference <= tolerance ? consecutive + 1 : 0;
                if (consecutive >= 2 && Math.Abs(current - reference) <= 1e-8) break;
                previous = current;
            }
            bool converged = consecutive >= 2 && Math.Abs(current - reference) <= 1e-8;
            return new Integral { Allowed = true, Converged = converged, Phase = current, Intervals = count,
                EmpiricalDifference = difference, ReferenceDifference = Math.Abs(current - reference),
                Status = converged ? "Successive Simpson refinements agree with the factor-phase reference within empirical tolerances."
                    : "The refinement limit was reached. The numerical integral remains unresolved." };
        }

        public static string Describe(Complex start, Complex end, double lambda, double paletteDegrees)
        {
            Result result = Evaluate(start, end, lambda, paletteDegrees);
            string firstOrder = result.FirstOrder.HasValue ? $"Local derivative predicts {result.FirstOrder.Value:F6} rad. "
                : "The local derivative phase forecast is undefined at the starting zero. ";
            string integration = result.Integration.Allowed
                ? $"Integrated phase {result.Integration.Phase:F6} rad. Factor reference {result.ContinuousPhase:F6} rad. "
                    + $"Endpoint principal change {result.PrincipalPhase:F6} rad. Additional full turns {result.ExtraFullTurns}. "
                    + $"Simpson used {result.Integration.Intervals} intervals with refinement difference {result.Integration.EmpiricalDifference:E2}. "
                    + result.Integration.Status + " "
                : result.Integration.Status + " ";
            int crossings = result.Events.Count(item => item.Kind == "crossing");
            int tangencies = result.Events.Count(item => item.Kind == "tangency");
            int unresolved = result.Events.Count(item => item.Kind == "unresolved");
            string coincidence = result.RealCoincidence || result.ImaginaryCoincidence
                ? $"On a palette boundary within tolerance (Re(F rotated)=0: {result.RealCoincidence}; Im(F rotated)=0: {result.ImaginaryCoincidence}). " : "";
            return $"Path from {start} to {end}; λ={lambda:G6}, palette={paletteDegrees:G5}°.\r\n" + firstOrder + integration + "\r\n"
                + $"Interior boundary crossings {crossings}, tangencies {tangencies}, zero encounters {result.Zeros.Count}, unresolved events {unresolved}. "
                + coincidence + "Phase integration follows F′/F along the segment. Error checks are empirical.";
        }

        private static void Require(bool condition, string description)
        {
            if (!condition) throw new InvalidOperationException("Zero-path verification failed. " + description);
        }

        // defines: graph.zeros.motion.path.verify
        public static object Verify()
        {
            var cases = new List<object>();
            Result Check(string name, Complex start, Complex end, double lambda, double palette)
            {
                Result result = Evaluate(start, end, lambda, palette);
                cases.Add(new { name, analysis = Evidence(result) });
                return result;
            }
            Result clear = Check("clear_path", new Complex(-1.4, 0.7), new Complex(1.1, 0.7), 0.5, 0);
            Result reversed = Check("reversed_clear_path", clear.End, clear.Start, 0.5, 0);
            Result symmetric = Check("symmetric_one_turn", new Complex(-1.6, 0.7), new Complex(1.6, 0.7), 0.5, 0);
            Require(symmetric.ExtraFullTurns == -1 && symmetric.Integration.Converged, "Symmetric path retains its negative full turn.");
            Require(clear.Integration.Allowed && clear.Integration.Converged && reversed.Integration.Converged,
                "Safe paths must converge.");
            Require(Math.Abs(clear.Integration.Phase.Value + reversed.Integration.Phase.Value) < 1e-9,
                "Reversal changes the phase sign.");
            Result simple = Check("simple_zero_crossing", Complex.Zero, new Complex(2, 0), 0.5, 0);
            Require(simple.Zeros.Count == 1 && simple.Zeros[0].Multiplicity == 1 && !simple.Integration.Allowed,
                "Simple zero is singular.");
            Result doubled = Check("double_zero_crossing", new Complex(-1, 0), new Complex(1, 0), 0, 0);
            Require(doubled.Zeros.Count == 1 && doubled.Zeros[0].Multiplicity == 2 && !doubled.Integration.Allowed,
                "Double zero is singular.");
            Result tangent = Check("tangent_boundary", new Complex(-2, 1), new Complex(0, 1), -1, 45);
            Require(tangent.Events.Count(item => item.Kind == "tangency") == 1 && tangent.Zeros.Count == 0,
                "A nonzero boundary tangency is retained.");
            Result boundary = Check("coincident_boundary", new Complex(2, 0), new Complex(3, 0), 0.5, 0);
            Require(boundary.ImaginaryCoincidence && boundary.Integration.Converged
                && Math.Abs(boundary.Integration.Phase.Value) < 1e-12, "An axis path has constant phase.");
            Result stationary = Check("zero_length", new Complex(0.2, 0.4), new Complex(0.2, 0.4), 0.5, 0);
            Require(stationary.ZeroLength && stationary.Integration.Phase == 0 && stationary.Events.Count == 0,
                "A regular zero-length path has zero phase change.");
            Result near = Check("near_zero", new Complex(0, 1e-9), new Complex(2, 1e-9), 0.5, 0);
            Require(near.Zeros.Count == 0 && !near.Integration.Allowed, "Near-zero guard must remain distinct from a root encounter.");
            Result rotated = Check("rotated_clear_path", clear.Start, clear.End, 0.5, 22.5);
            Require(Math.Abs(rotated.Integration.Phase.Value - clear.Integration.Phase.Value) < 1e-12,
                "Palette rotation preserves raw phase transport.");
            Result fullTurn = Check("extra_full_turn", new Complex(-0.1, 1), new Complex(-0.1, -1), 0, 0);
            Require(fullTurn.ExtraFullTurns == 1 && fullTurn.Integration.Converged,
                "The complete phase change preserves its additional turn.");
            Result endpoint = Check("endpoint_zero", Complex.One, new Complex(1, 1), 0.5, 0);
            Require(endpoint.Zeros.Count == 1 && endpoint.Events.All(item => item.Kind != "crossing")
                && !endpoint.Integration.Allowed, "Starting at a zero is explicitly singular.");
            return new { status = "passed", traceId = "graph.zeros.motion.path.verify", cases,
                interpretation = "Polynomial roots, Taylor phase prediction, boundary equations, and logarithmic-derivative integration are established methods." };
        }
    }
}
