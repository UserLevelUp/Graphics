"""Independent stdlib validation of ZeroMotionExperiment JSON exports.

Usage: python verify_exports.py export.values.json [more.exports.json]
       python verify_exports.py --references
       python verify_exports.py --self-test

Roots use 70-digit Decimal square roots; winding is independently sampled.
These are numerical control checks, not interval certification or RH evidence.
"""
import argparse
import cmath
import copy
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
import sys

TOL = 2e-12
REQUIRED = (-0.5, -1e-6, 0.0, 1e-6, 0.5)
PROBES = (complex(-1.3, 0.7), complex(0.23, -0.42), complex(2, 1.1))
MODEL = 'F(z,lambda)=z^2-2*lambda'
HEAT = 'dF/dlambda=-d2F/dz2'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            label + ' must be a number')
    require(math.isfinite(value), label + ' must be finite')
    return float(value)


def read_complex(value, label):
    require(isinstance(value, dict), label + ' must be a complex coordinate object')
    return complex(number(value.get('real'), label + '.real'),
                   number(value.get('imaginary'), label + '.imaginary'))


def coordinates(z):
    return {'real': z.real, 'imaginary': z.imag}


def close(actual, expected, label):
    error = abs(actual - expected)
    require(error <= TOL * max(1.0, abs(expected)),
            f'{label}: {actual!r} differs from {expected!r}, error={error:.4g}')
    return error


def expected_roots(lam):
    with localcontext() as context:
        context.prec = 70
        magnitude = (Decimal(2) * abs(Decimal(str(lam)))).sqrt()
        a = complex(float(magnitude), 0) if lam >= 0 else complex(0, float(magnitude))
        return (a, -a), str(magnitude)


def polynomial(z, lam):
    return z * z - 2 * lam


def winding(lam, center, radius, samples=1024):
    # Small phase steps are an empirical sampling check, not a general guarantee
    # against unresolved winding for arbitrary analytic functions.
    values = [polynomial(center + radius * cmath.exp(2j * math.pi * k / samples), lam)
              for k in range(samples)]
    require(min(map(abs, values)) > 0, 'contour meets a zero')
    phases = [cmath.phase(values[(k + 1) % samples] / values[k])
              for k in range(samples)]
    turns = math.fsum(phases) / (2 * math.pi)
    require(max(map(abs, phases)) < math.pi / 4, 'contour phase step too large')
    require(abs(turns - round(turns)) < 1e-10, 'nonintegral sampled winding')
    return {'winding': round(turns), 'rawTurns': turns,
            'maximumPhaseStep': max(map(abs, phases)),
            'minimumFunctionMagnitude': min(map(abs, values)), 'samples': samples}


def check_snapshot(snapshot, label):
    lam = number(snapshot.get('lambda'), label + '.lambda')
    expected, decimal_magnitude = expected_roots(lam)
    roots = snapshot.get('roots')
    require(isinstance(roots, list) and len(roots) == (1 if lam == 0 else 2),
            label + ': incorrect number of distinct roots')
    actual_roots = [read_complex(root, label + '.roots') for root in roots]
    if lam != 0:
        # Enumeration and branch naming are conventions, not invariants.
        assignment = min((actual_roots, actual_roots[::-1]),
                         key=lambda order: max(abs(a - e) for a, e in zip(order, expected)))
        root_error = max(close(a, e, label + '.root') for a, e in zip(assignment, expected))
    else:
        root_error = close(actual_roots[0], 0j, label + '.collision root')
    residuals = [abs(polynomial(root, lam)) for root in actual_roots]
    require(max(residuals) <= TOL * max(1, abs(2 * lam)), label + ': root residual')
    contours = []
    for root, exported in zip(actual_roots, roots):
        expected_multiplicity = 2 if lam == 0 else 1
        require(type(exported.get('multiplicity')) is int
                and exported['multiplicity'] == expected_multiplicity,
                label + ': wrong multiplicity')
        radius = 0.25 if lam == 0 else abs(expected[0]) / 3
        contour = winding(lam, root, radius)
        require(contour['winding'] == expected_multiplicity, label + ': contour multiplicity')
        contours.append(contour)
    enclosing = winding(lam, 0j, max(1, 2 * abs(expected[0])))
    require(enclosing['winding'] == 2, label + ': total contour multiplicity')
    branches = snapshot.get('branches')
    require(isinstance(branches, dict), label + ': missing branches')
    a = read_complex(branches.get('A'), label + '.branches.A')
    b = read_complex(branches.get('B'), label + '.branches.B')
    close(a + b, 0j, label + ': branch sum')
    close(a * b, -2 * lam, label + ': branch product')
    for branch in (a, b):
        require(min(abs(branch - root) for root in actual_roots) <= TOL,
                label + ': branch is not an exported root')
    close(number(snapshot.get('separation'), label + '.separation'),
          abs(expected[0] - expected[1]), label + ': separation')
    discriminant = number(snapshot.get('discriminant'), label + '.discriminant')
    close(discriminant, 8 * lam, label + ': signed discriminant')
    close((a - b) ** 2, discriminant, label + ': complex squared separation')
    freeze = number(snapshot.get('freezeDeltaLambda'), label + '.freezeDeltaLambda')
    close(freeze, -lam, label + ': frozen discriminant collision increment')
    close(discriminant + 8 * freeze, 0, label + ': discriminant at predicted collision')
    require(snapshot.get('decreasingPredictionApplicable') is (lam > 0),
            label + ': decreasing-direction applicability')
    reported_residual = number(snapshot.get('maximumRootResidual'), label + '.maximumRootResidual')
    require(reported_residual >= 0, label + ': negative residual report')
    close(reported_residual, max(residuals), label + ': residual report')
    samples = snapshot.get('samples')
    require(isinstance(samples, list) and len(samples) >= len(PROBES),
            label + ': actual function/derivative samples are required')
    sampled_z = []
    max_value_error = max_phase_error = max_heat_error = 0.0
    for index, sample in enumerate(samples):
        tag = f'{label}.samples[{index}]'
        z = read_complex(sample.get('z'), tag + '.z')
        sampled_z.append(z)
        value = read_complex(sample.get('value'), tag + '.value')
        factor_a = read_complex(sample.get('factorA'), tag + '.factorA')
        factor_b = read_complex(sample.get('factorB'), tag + '.factorB')
        dl = read_complex(sample.get('lambdaDerivative'), tag + '.lambdaDerivative')
        dzz = read_complex(sample.get('secondZDerivative'), tag + '.secondZDerivative')
        max_value_error = max(max_value_error, close(value, polynomial(z, lam), tag + ': value'))
        close(factor_a, z - a, tag + ': factor A')
        close(factor_b, z - b, tag + ': factor B')
        close(factor_a * factor_b, value, tag + ': factor product')
        require(min(abs(value), abs(factor_a), abs(factor_b)) > TOL,
                tag + ': phase sample too close to a root')
        phase_error = abs(math.remainder(cmath.phase(value) - cmath.phase(factor_a)
                                       - cmath.phase(factor_b), 2 * math.pi))
        require(phase_error < 1e-11, tag + ': factor phase addition')
        max_phase_error = max(max_phase_error, phase_error)
        close(dl, -2 + 0j, tag + ': lambda derivative')
        close(dzz, 2 + 0j, tag + ': second z derivative')
        max_heat_error = max(max_heat_error, close(dl + dzz, 0j, tag + ': heat identity'))
    for z in PROBES:
        require(any(abs(z - sample) < TOL for sample in sampled_z), label + ': missing fixed probe')
    return {'lambda': lam, 'rootMagnitudeDecimal70': decimal_magnitude,
            'maximumRootError': root_error, 'maximumRootResidual': max(residuals),
            'maximumValueError': max_value_error, 'maximumPhaseAdditionError': max_phase_error,
            'maximumHeatResidual': max_heat_error, 'isolatingContours': contours,
            'enclosingContour': enclosing}


def check_export(document):
    require(document.get('schemaVersion') == 1, 'unsupported schemaVersion')
    require(document.get('model') == MODEL, 'unexpected model label')
    require(document.get('heatEquation') == HEAT, 'unexpected heat-equation label')
    snapshots = document.get('snapshots')
    require(isinstance(snapshots, list), 'missing snapshots')
    for lam in REQUIRED:
        require(any(isinstance(s, dict) and s.get('lambda') == lam for s in snapshots),
                f'missing required snapshot lambda={lam}')
    results = [check_snapshot(s, f'snapshots[{i}]') for i, s in enumerate(snapshots)]
    frame = document.get('frame')
    require(isinstance(frame, dict), 'missing rendered frame')
    parameters = document.get('parameters')
    require(isinstance(parameters, dict), 'missing render parameters')
    close(number(frame.get('lambda'), 'frame.lambda'),
          number(parameters.get('lambda'), 'parameters.lambda'), 'frame/parameter lambda')
    number(parameters.get('paletteDegrees'), 'parameters.paletteDegrees')
    frame_result = check_snapshot(frame, 'frame')
    return {'status': 'passed', 'snapshotsChecked': len(results), 'snapshots': results,
            'frame': frame_result, 'limitations': [
                'Independent numerical control checks; not interval certification.',
                'At collision the root has multiplicity two; branch identities are naming conventions.',
                'The discriminant is signed; separation is its absolute-value square root.',
                'The affine-discriminant prediction is exact for this quadratic only.',
                'No conclusion about primes, zeta zeros, or the Riemann Hypothesis.']}


def fixture_snapshot(lam):
    (a, b), _ = expected_roots(lam)
    root_values = [(a, 2)] if lam == 0 else [(a, 1), (b, 1)]
    return {'lambda': lam,
            'roots': [dict(coordinates(z), multiplicity=m) for z, m in root_values],
            'branches': {'A': coordinates(a), 'B': coordinates(b)},
            'separation': abs(a - b), 'discriminant': 8 * lam,
            'freezeDeltaLambda': -lam, 'decreasingPredictionApplicable': lam > 0,
            'maximumRootResidual': max(abs(polynomial(z, lam)) for z, _ in root_values),
            'samples': [{'z': coordinates(z), 'value': coordinates(polynomial(z, lam)),
                         'factorA': coordinates(z - a), 'factorB': coordinates(z - b),
                         'lambdaDerivative': coordinates(-2 + 0j),
                         'secondZDerivative': coordinates(2 + 0j)} for z in PROBES]}


def references():
    return {'schemaVersion': 1, 'model': MODEL, 'heatEquation': HEAT,
            'parameters': {'lambda': 0.5, 'paletteDegrees': 0},
            'frame': fixture_snapshot(0.5),
            'snapshots': [fixture_snapshot(lam) for lam in REQUIRED]}


def boundary_roots(a, b, c, scale):
    """Independently solve a real boundary polynomial with Decimal arithmetic."""
    tolerance = 1e-12 * scale
    if max(abs(a), abs(b), abs(c)) <= tolerance:
        return True, []
    if abs(a) <= tolerance:
        return False, [] if abs(b) <= tolerance else [-c / b]
    with localcontext() as context:
        context.prec = 70
        da, db, dc = map(lambda x: Decimal.from_float(float(x)), (a, b, c))
        discriminant = db * db - 4 * da * dc
        roundoff_scale = db * db + abs(4 * da * dc)
        if abs(discriminant) <= Decimal('2e-14') * roundoff_scale:
            return False, [float(-db / (2 * da))]
        if discriminant < 0:
            return False, []
        root = discriminant.sqrt()
        return False, sorted([float((-db - root) / (2 * da)),
                              float((-db + root) / (2 * da))])


def sampled_open_phase(start, end, lam):
    # Direct samples of F, not the renderer's analytic sum of factor angles.
    # These fixed control paths stay far enough from zeros for 4096 segments.
    values = [polynomial(start + (end - start) * (i / 4096), lam)
              for i in range(4097)]
    require(min(map(abs, values)) > 0, 'independent phase contour hits zero')
    changes = [cmath.phase(b / a) for a, b in zip(values, values[1:])]
    require(max(map(abs, changes)) < math.pi / 8,
            'independent open-path phase sampling requires refinement')
    return math.fsum(changes)


def check_path(analysis, label):
    start = read_complex(analysis.get('start'), label + '.start')
    end = read_complex(analysis.get('end'), label + '.end')
    lam = number(analysis.get('lambda'), label + '.lambda')
    degrees = number(analysis.get('paletteDegrees'), label + '.paletteDegrees')
    direction = end - start
    roots, _ = expected_roots(lam)
    distinct = roots[:1] if lam == 0 else roots
    scale = max(1, abs(start), abs(end), abs(roots[0]))
    geometric_tolerance = 64 * sys.float_info.epsilon * scale
    near_guard = 1e-7 * scale
    expected_hits = []
    distances = []
    for root in distinct:
        t = ((root - start) / direction).real if direction else 0.0
        clipped = min(1, max(0, t))
        distance = abs(start + clipped * direction - root)
        distances.append(distance)
        if distance <= geometric_tolerance and -1e-10 <= t <= 1 + 1e-10:
            expected_hits.append((clipped, root, 2 if lam == 0 else 1))
    expected_hits.sort()
    hits = analysis.get('zeros')
    require(isinstance(hits, list) and len(hits) == len(expected_hits), label + ': zero count')
    for actual, (t, root, multiplicity) in zip(hits, expected_hits):
        close(number(actual.get('t'), label + '.zero.t'), t, label + ': zero parameter')
        close(read_complex(actual.get('point'), label + '.zero.point'), root, label + ': zero location')
        require(actual.get('multiplicity') == multiplicity, label + ': zero multiplicity')
    close(number(analysis.get('closestRootDistance'), label + '.closestRootDistance'),
          min(distances), label + ': closest distance')
    close(number(analysis.get('nearZeroGuard'), label + '.nearZeroGuard'), near_guard, label + ': guard')
    require(analysis.get('zeroLength') is (direction == 0), label + ': zero-length flag')
    first, last = polynomial(start, lam), polynomial(end, lam)
    close(read_complex(analysis.get('startValue'), label + '.startValue'), first, label + ': start value')
    close(read_complex(analysis.get('endValue'), label + '.endValue'), last, label + ': end value')
    if first:
        close(number(analysis.get('firstOrderPhaseRadians'), label + '.firstOrderPhaseRadians'),
              (2 * start / first * direction).imag, label + ': first-order forecast')
    else:
        require(analysis.get('firstOrderPhaseRadians') is None, label + ': singular first-order forecast')
    principal = None
    if first and last:
        principal = cmath.phase(last / first)
        close(number(analysis.get('principalEndpointChangeRadians'), label + '.principalEndpointChangeRadians'),
              principal, label + ': endpoint principal phase')
        close(number(analysis.get('rawEndpointPhaseDifferenceRadians'), label + '.rawEndpointPhaseDifferenceRadians'),
              cmath.phase(last) - cmath.phase(first), label + ': raw endpoint phase difference')
    else:
        require(analysis.get('principalEndpointChangeRadians') is None,
                label + ': endpoint-zero phase must be undefined')
    integration = analysis.get('integration')
    require(isinstance(integration, dict), label + ': missing integration result')
    safe = not expected_hits and min(distances) > near_guard
    require(integration.get('allowed') is safe, label + ': integration allowance')
    phase = phase_error = numerical_error = None
    if safe:
        phase = sampled_open_phase(start, end, lam)
        phase_error = close(number(analysis.get('continuousPhaseChangeRadians'), label + '.continuousPhaseChangeRadians'),
                            phase, label + ': independently sampled continuous phase')
        turns = round((phase - principal) / (2 * math.pi))
        require(analysis.get('extraFullTurns') == turns, label + ': extra full turns')
        numerical_phase = number(integration.get('phaseRadians'), label + '.integration.phaseRadians')
        numerical_error = abs(numerical_phase - phase)
        close(number(integration.get('referenceDifference'), label + '.integration.referenceDifference'),
              abs(numerical_phase - analysis['continuousPhaseChangeRadians']), label + ': reported integration error')
        require(integration.get('converged') is True, label + ': declared control did not converge')
        require(numerical_error <= 1e-8, label + ': numerical phase integral error')
    else:
        require(analysis.get('continuousPhaseChangeRadians') is None
                and analysis.get('extraFullTurns') is None
                and integration.get('phaseRadians') is None
                and integration.get('converged') is False,
                label + ': guarded/singular path must not claim phase transport')
    rotation = cmath.exp(-1j * math.radians(degrees % 360))
    coefficients = (direction * direction * rotation, 2 * start * direction * rotation,
                    first * rotation)
    coefficient_scale = max(map(abs, coefficients))
    events = analysis.get('boundaryEvents')
    coincidence = analysis.get('boundaryCoincidence')
    require(isinstance(events, list) and isinstance(coincidence, dict), label + ': missing boundaries')
    maximum_boundary_residual = 0.0
    for component in ('real', 'imaginary'):
        a, b, c = [value.real if component == 'real' else value.imag for value in coefficients]
        coincident, parameters = boundary_roots(a, b, c, coefficient_scale)
        require(coincidence.get(component) is coincident, label + ': boundary coincidence')
        expected_t = [min(1, max(0, t)) for t in parameters if -1e-10 <= t <= 1 + 1e-10]
        found = sorted([event for event in events if event.get('boundary') == component], key=lambda event: event['t'])
        require(len(found) == len(expected_t), label + ': ' + component + ' boundary event count')
        for event, t in zip(found, expected_t):
            actual_t = number(event.get('t'), label + '.boundary.t')
            require(abs(actual_t - t) < 1e-9, label + ': boundary location')
            close(read_complex(event.get('point'), label + '.boundary.point'),
                  start + t * direction, label + ': boundary point')
            residual = abs((a * actual_t + b) * actual_t + c)
            maximum_boundary_residual = max(maximum_boundary_residual, residual)
            require(residual <= 1e-10 * max(1, coefficient_scale), label + ': boundary equation residual')
            if t <= 1e-10 or t >= 1 - 1e-10:
                kind = 'endpoint'
            elif any(abs(t - zero_t) <= 1e-10 for zero_t, _, _ in expected_hits):
                kind = 'zero'
            elif abs(2 * a * t + b) <= 1e-10 * max(1, coefficient_scale):
                kind = 'tangency'
            else:
                kind = 'crossing'
            require(event.get('kind') == kind, label + ': boundary event classification')
    require(all(event.get('boundary') in ('real', 'imaginary') for event in events),
            label + ': unknown boundary type')
    return {'name': label, 'zeroCount': len(hits), 'boundaryEventCount': len(events),
            'maximumBoundaryResidual': maximum_boundary_residual,
            'sampledContinuousPhaseRadians': phase, 'continuousPhaseReferenceError': phase_error,
            'numericalIntegrationError': numerical_error}


def check_path_export(document):
    verification = document.get('verification')
    require(isinstance(verification, dict), 'missing path verification')
    cases = verification.get('cases')
    require(isinstance(cases, list), 'missing path control cases')
    expected_names = {'clear_path', 'reversed_clear_path', 'symmetric_one_turn', 'simple_zero_crossing',
                      'double_zero_crossing', 'tangent_boundary', 'coincident_boundary', 'zero_length',
                      'near_zero', 'rotated_clear_path', 'extra_full_turn', 'endpoint_zero'}
    names = [case.get('name') for case in cases]
    require(len(names) == len(set(names)) and expected_names <= set(names), 'missing/duplicate path controls')
    results = [check_path(case['analysis'], case['name']) for case in cases]
    selected = check_path(document['analysis'], 'selected_path')
    by_name = {case['name']: case['analysis'] for case in cases}
    mutations = [
        ('lost full turn', 'symmetric_one_turn', lambda a: a.update(extraFullTurns=0)),
        ('wrapped phase substituted', 'symmetric_one_turn',
         lambda a: a.update(continuousPhaseChangeRadians=a['principalEndpointChangeRadians'])),
        ('wrong numerical integral', 'clear_path', lambda a: a['integration'].update(phaseRadians=42)),
        ('singular integration allowed', 'simple_zero_crossing', lambda a: a['integration'].update(allowed=True)),
        ('tangency called crossing', 'tangent_boundary', lambda a: a['boundaryEvents'][0].update(kind='crossing')),
        ('coincident boundary omitted', 'coincident_boundary', lambda a: a['boundaryCoincidence'].update(imaginary=False)),
        ('missing boundary crossing', 'symmetric_one_turn', lambda a: a['boundaryEvents'].pop()),
        ('endpoint-zero derivative invented', 'endpoint_zero', lambda a: a.update(firstOrderPhaseRadians=0)),
    ]
    for label, name, mutate in mutations:
        corrupted = copy.deepcopy(by_name[name])
        mutate(corrupted)
        try:
            check_path(corrupted, label)
        except (ValueError, KeyError, TypeError):
            continue
        raise AssertionError('path validator accepted negative control: ' + label)
    return {'status': 'passed', 'kind': 'phase-path', 'pathCasesChecked': len(results),
            'selectedPath': selected, 'cases': results,
            'rejectedNegativeControls': [label for label, _, _ in mutations],
            'limitations': ['Numerical phase integration and tolerances are empirical, not certified bounds.',
                           'Boundary names identify the vanishing component, not the geometric axis.',
                           'No claim about primes, Riemann zeta, or the Riemann Hypothesis.']}


def self_test():
    good = references()
    check_export(good)
    mutations = [
        ('incorrect root', lambda d: d['snapshots'][0]['roots'][0].update(real=0.1)),
        ('unsigned discriminant', lambda d: d['snapshots'][0].update(discriminant=4)),
        ('wrong freeze sign', lambda d: d['snapshots'][-1].update(freezeDeltaLambda=0.5)),
        ('collision multiplicity', lambda d: d['snapshots'][2]['roots'][0].update(multiplicity=1)),
        ('wrong heat direction', lambda d: d['snapshots'][0]['samples'][0]['lambdaDerivative'].update(real=2)),
        ('wrong factor phase', lambda d: d['snapshots'][0]['samples'][0]['factorA'].update(real=42)),
        ('near-collision omitted', lambda d: d['snapshots'].pop(1)),
        ('stale frame parameters', lambda d: d['parameters'].update(**{'lambda': -0.5})),
    ]
    for label, mutate in mutations:
        wrong = copy.deepcopy(good)
        mutate(wrong)
        try:
            check_export(wrong)
        except (ValueError, KeyError, TypeError):
            continue
        raise AssertionError('validator accepted negative control: ' + label)
    return {'status': 'passed', 'positiveControl': True,
            'rejectedNegativeControls': [label for label, _ in mutations],
            'note': 'Validator self-test only; no renderer export was checked.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exports', nargs='*', type=Path)
    parser.add_argument('--references', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.references:
        require(not args.exports and not args.self_test, '--references must be used alone')
        print(json.dumps(references(), indent=2, allow_nan=False))
    elif args.self_test:
        require(not args.exports, '--self-test must be used alone')
        print(json.dumps(self_test(), indent=2, allow_nan=False))
    else:
        require(bool(args.exports), 'supply actual JSON export paths, --references, or --self-test')
        results = []
        for path in args.exports:
            document = json.loads(path.read_text(encoding='utf-8-sig'))
            result = check_path_export(document) if 'analysis' in document else check_export(document)
            result['source'] = str(path.resolve())
            results.append(result)
        print(json.dumps({'status': 'passed', 'exports': results}, indent=2, allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        sys.exit(1)
