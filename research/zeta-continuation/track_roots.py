"""Independent adaptive continuation of zeta(s)=a from three seeded zeros.

Requires mpmath==1.3.0. Run with --output-dir evidence. No global root search or
endpoint reseeding is used during continuation. All accuracy/guard claims are
numerical; finite samples do not certify the entire curves or RH.
"""
import argparse
from dataclasses import dataclass, replace
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

import mpmath as mp

# defines: graph.riemann.continuation.animation.verify
# consumer: graph.riemann.continuation.animation
mp.mp.dps = 80
DOMAIN = tuple(map(mp.mpf, ['.05', '3', '10', '30']))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


@dataclass(frozen=True)
class Settings:
    initial_step: object = mp.mpf('.025')
    max_step: object = mp.mpf('.04')
    min_step: object = mp.mpf('1e-10')
    derivative_guard: object = mp.mpf('1e-8')
    residual_goal: object = mp.mpf('1e-60')
    prediction_motion: object = mp.mpf('.08')
    accepted_motion: object = mp.mpf('.12')
    correction_limit: object = mp.mpf('.001')
    boundary_tolerance: object = mp.mpf('1e-24')
    max_newton: int = 14
    max_attempts: int = 20000


class Rejected(Exception):
    pass


def inside(s, domain):
    return domain[0] <= s.real <= domain[1] and domain[2] <= s.imag <= domain[3]


def boundaries(s, domain):
    return [name for name, condition in zip(('minSigma', 'maxSigma', 'minT', 'maxT'),
            (s.real < domain[0], s.real > domain[1], s.imag < domain[2], s.imag > domain[3])) if condition]


def record(a, s, derivative, residual, step=0, error=0, iterations=0, event='continuation'):
    return {'a': mp.mpf(a), 's': mp.mpc(s), 'derivative': mp.mpc(derivative),
            'residual': mp.mpf(residual), 'step': mp.mpf(step), 'predictionError': mp.mpf(error),
            'newtonIterations': iterations, 'event': event}


def corrected(value, derivative, target, predictor, settings):
    s = predictor
    for iteration in range(settings.max_newton):
        f = value(s) - target
        d = derivative(s)
        if not (mp.isfinite(f) and mp.isfinite(d)):
            raise Rejected('nonfinite_evaluation')
        if abs(f) <= settings.residual_goal:
            return s, d, abs(f), iteration
        if abs(d) <= settings.derivative_guard:
            raise Rejected('derivative_guard_during_correction')
        change = f / d
        if abs(change) > settings.accepted_motion:
            raise Rejected('newton_motion_guard')
        s -= change
        if abs(s - predictor) > 4 * settings.correction_limit:
            raise Rejected('newton_departed_predictor_neighborhood')
    raise Rejected('newton_iteration_limit')


def check_motion(previous, candidate, predictor, settings):
    error = abs(candidate - predictor)
    if error > settings.correction_limit:
        raise Rejected('predictor_correction_guard')
    if abs(candidate - previous['s']) > settings.accepted_motion:
        raise Rejected('accepted_motion_guard')
    return error


def advance(value, derivative, previous, target, settings, event='continuation'):
    if abs(previous['derivative']) <= settings.derivative_guard:
        raise Rejected('derivative_guard')
    step = target - previous['a']
    predictor = previous['s'] + step / previous['derivative']
    if abs(predictor - previous['s']) > settings.prediction_motion * (1 + mp.mpf('1e-50')):
        raise Rejected('prediction_motion_guard')
    s, d, residual, iterations = corrected(value, derivative, target, predictor, settings)
    error = check_motion(previous, s, predictor, settings)
    return record(target, s, d, residual, step, error, iterations, event)


def refine_exit(value, derivative, left, right, domain, settings, points):
    require(inside(left['s'], domain) and not inside(right['s'], domain), 'invalid exit bracket')
    iterations = 0
    while abs(right['a'] - left['a']) > settings.boundary_tolerance:
        iterations += 1
        require(iterations <= 120, 'boundary bisection iteration limit')
        target = (left['a'] + right['a']) / 2
        middle = advance(value, derivative, left, target, settings, 'boundary-refinement')
        if inside(middle['s'], domain):
            points.append(middle)
            left = middle
        else:
            right = middle
    return {'inside': left, 'outside': right, 'widthA': abs(right['a'] - left['a']),
            'boundaries': boundaries(right['s'], domain), 'iterations': iterations}


def track(value, derivative, start_s, start_a, end_a, domain=DOMAIN, settings=Settings(), name='path'):
    start_a, end_a = mp.mpf(start_a), mp.mpf(end_a)
    direction = 1 if end_a >= start_a else -1
    first = record(start_a, start_s, derivative(start_s), abs(value(start_s) - start_a), event='start')
    require(first['residual'] <= settings.residual_goal, name + ': start does not solve its target')
    require(inside(first['s'], domain), name + ': start outside domain')
    points, rejected = [first], []
    step_size = settings.initial_step
    checkpoints = [mp.mpf(k) / 10 for k in range(11)]
    result = {'id': name, 'points': points, 'rejectedSteps': rejected, 'exit': None}
    for attempt in range(settings.max_attempts):
        current = points[-1]
        if current['a'] == end_a:
            result.update(status='completed', stopReason='target_reached', endpoint=current)
            return result
        if abs(current['derivative']) <= settings.derivative_guard:
            result.update(status='stopped', stopReason='derivative_guard', endpoint=current)
            return result
        ahead = [a for a in checkpoints if direction * (a - current['a']) > 0
                 and direction * (end_a - a) >= 0]
        next_target = min(ahead) if direction > 0 and ahead else max(ahead) if ahead else end_a
        distance = min(abs(end_a - current['a']), abs(next_target - current['a']))
        step = min(step_size, settings.max_step, distance,
                   settings.prediction_motion * abs(current['derivative']))
        if step < settings.min_step and distance > settings.min_step:
            result.update(status='stopped', stopReason='minimum_step', endpoint=current)
            return result
        target = current['a'] + direction * step
        if step == distance:
            target = next_target
        try:
            candidate = advance(value, derivative, current, target, settings)
        except Rejected as error:
            rejected.append({'a': current['a'], 'attemptedA': target, 'step': direction * step, 'reason': str(error)})
            step_size = step / 2
            continue
        # Near a boundary, inspect the half-step too. This is a numerical check,
        # not interval certification that an undetected exit/reentry is absent.
        margin = min(current['s'].real - domain[0], domain[1] - current['s'].real,
                     current['s'].imag - domain[2], domain[3] - current['s'].imag)
        if inside(candidate['s'], domain) and margin < 2 * settings.prediction_motion and step > settings.min_step:
            middle = advance(value, derivative, current, (current['a'] + target) / 2, settings, 'boundary-midpoint-check')
            if not inside(middle['s'], domain):
                candidate = middle
        if not inside(candidate['s'], domain):
            bracket = refine_exit(value, derivative, current, candidate, domain, settings, points)
            result.update(status='exited', stopReason='first_detected_boundary_exit',
                          endpoint=bracket['inside'], exit=bracket)
            return result
        points.append(candidate)
        # Landing on a fixed target can leave an arbitrarily tiny rounding
        # remainder. Do not use that truncated landing distance as the next
        # adaptive step size; it is not evidence of high curve curvature.
        adaptation_step = step_size if step == distance else step
        if candidate['predictionError'] < settings.correction_limit / 8 and candidate['newtonIterations'] <= 4:
            step_size = min(settings.max_step, adaptation_step * mp.mpf('1.5'))
        elif candidate['predictionError'] > settings.correction_limit * mp.mpf('.75'):
            step_size = adaptation_step * mp.mpf('.8')
        else:
            step_size = adaptation_step
    result.update(status='stopped', stopReason='maximum_attempts', endpoint=points[-1])
    return result


def decimal(value):
    return mp.nstr(value, 72)


def coordinates(value, strings=False):
    convert = decimal if strings else float
    return {'real': convert(value.real), 'imaginary': convert(value.imag)}


def serialize_point(point):
    return {'a': float(point['a']), 'aDecimal': decimal(point['a']),
            's': coordinates(point['s']), 'sDecimal': coordinates(point['s'], True),
            'derivative': coordinates(point['derivative']), 'derivativeDecimal': coordinates(point['derivative'], True),
            'residual': float(point['residual']), 'residualDecimal': decimal(point['residual']),
            'step': float(point['step']), 'stepDecimal': decimal(point['step']),
            'predictionError': float(point['predictionError']), 'newtonIterations': point['newtonIterations'],
            'event': point['event']}


def serialize_track(trajectory):
    result = {'id': trajectory['id'], 'startZeroIndex': trajectory.get('startZeroIndex'),
              'status': trajectory['status'], 'stopReason': trajectory['stopReason'],
              'points': [serialize_point(point) for point in trajectory['points']],
              'rejectedSteps': [{key: decimal(value) if key != 'reason' else value for key, value in row.items()}
                                for row in trajectory['rejectedSteps']],
              'endpoint': serialize_point(trajectory['endpoint']), 'exit': None}
    if trajectory['exit'] is not None:
        bracket = trajectory['exit']
        result['exit'] = {'inside': serialize_point(bracket['inside']), 'outside': serialize_point(bracket['outside']),
                          'widthA': decimal(bracket['widthA']), 'boundaries': bracket['boundaries'],
                          'iterations': bracket['iterations']}
    return result


def checkpoint_points(trajectory):
    return {k: next((point for point in trajectory['points'] if abs(point['a'] - mp.mpf(k) / 10) < mp.mpf('1e-70')), None)
            for k in range(11)}


def compare_tracks(first, second):
    require(first['status'] == second['status'], 'coarse/fine status disagreement')
    a_points, b_points = checkpoint_points(first), checkpoint_points(second)
    errors = [abs(a_points[k]['s'] - b_points[k]['s']) for k in range(11)
              if a_points[k] is not None and b_points[k] is not None]
    maximum = max(errors, default=mp.mpf(0))
    require(maximum < mp.mpf('1e-45'), 'common-target root disagreement')
    endpoint_a = abs(first['endpoint']['a'] - second['endpoint']['a'])
    endpoint_s = abs(first['endpoint']['s'] - second['endpoint']['s'])
    require(endpoint_a < mp.mpf('1e-20') and endpoint_s < mp.mpf('1e-18'), 'endpoint/refined-exit disagreement')
    if first['exit'] is not None:
        require(first['exit']['boundaries'] == second['exit']['boundaries'], 'different exit boundaries')
    return {'commonCheckpoints': len(errors), 'maximumRootDifference': decimal(maximum),
            'endpointADifference': decimal(endpoint_a), 'endpointSDifference': decimal(endpoint_s)}


def model_controls(settings):
    square_domain = tuple(map(mp.mpf, ['-3', '3', '-2', '2']))
    linear = track(lambda z: z, lambda z: mp.mpc(1), mp.mpc(0), 0, 1, square_domain, settings, 'linear')
    require(linear['status'] == 'completed' and all(point['s'] == point['a'] for point in linear['points']), 'linear exact model')
    quadratic = []
    for sign in (1, -1):
        path = track(lambda z: z*z, lambda z: 2*z, mp.mpc(sign), 1, mp.mpf('.25'), square_domain, settings, 'quadratic')
        require(path['status'] == 'completed' and abs(path['endpoint']['s'] - sign * mp.mpf('.5')) < mp.mpf('1e-55'),
                'quadratic branch was lost')
        require(all(sign * point['s'].real > 0 for point in path['points']), 'quadratic branch switched')
        quadratic.append({'sign': sign, 'points': len(path['points']), 'endpointError': decimal(abs(path['endpoint']['s'] - sign * mp.mpf('.5')))})
    boundary_domain = tuple(map(mp.mpf, ['-.5', '.6', '-1', '1']))
    boundary = track(lambda z: z, lambda z: mp.mpc(1), mp.mpc(0), 0, 1, boundary_domain, settings, 'linear_boundary')
    require(boundary['status'] == 'exited' and abs(boundary['endpoint']['a'] - mp.mpf('.6')) < mp.mpf('1e-22'),
            'linear boundary refinement')
    critical = track(lambda z: z*z, lambda z: 2*z, mp.mpc(0), 0, 1, square_domain, settings, 'critical_start')
    require(critical['status'] == 'stopped' and critical['stopReason'] == 'derivative_guard', 'derivative guard failed')
    prior = record(1, mp.mpc(1), mp.mpc(2), 0)
    target = mp.mpf('.99')
    predictor = prior['s'] + (target - prior['a']) / prior['derivative']
    try:
        check_motion(prior, -mp.sqrt(target), predictor, settings)
    except Rejected:
        jump_rejected = True
    else:
        jump_rejected = False
    require(jump_rejected, 'zero-residual jump to other quadratic root was accepted')
    return {'linearExact': True, 'quadraticBranches': quadratic, 'linearBoundaryWidthA': decimal(boundary['exit']['widthA']),
            'criticalStartStopped': True, 'zeroResidualWrongBranchRejected': True}


def summary(trajectory):
    points = trajectory['points']
    return {'id': trajectory['id'], 'status': trajectory['status'], 'stopReason': trajectory['stopReason'],
            'acceptedPoints': len(points), 'rejectedSteps': len(trajectory['rejectedSteps']),
            'maximumResidual': decimal(max(point['residual'] for point in points)),
            'minimumSampledDerivativeMagnitude': decimal(min(abs(point['derivative']) for point in points)),
            'maximumPredictionError': decimal(max(point['predictionError'] for point in points)),
            'endpoint': serialize_point(trajectory['endpoint']),
            'exitWidthA': decimal(trajectory['exit']['widthA']) if trajectory['exit'] else None,
            'exitBoundaries': trajectory['exit']['boundaries'] if trajectory['exit'] else []}


def variants():
    settings = Settings()
    return {'base': settings,
            'coarse': replace(settings, initial_step=mp.mpf('.05'), max_step=mp.mpf('.08'),
                              prediction_motion=mp.mpf('.16'), accepted_motion=mp.mpf('.24'), correction_limit=mp.mpf('.004')),
            'fine': replace(settings, initial_step=mp.mpf('.0125'), max_step=mp.mpf('.02'),
                            prediction_motion=mp.mpf('.04'), accepted_motion=mp.mpf('.06'), correction_limit=mp.mpf('.00025'))}


def restore_point(point):
    def complex_decimal(value):
        return mp.mpc(value['real'], value['imaginary'])
    return record(mp.mpf(point['aDecimal']), complex_decimal(point['sDecimal']),
                  complex_decimal(point['derivativeDecimal']), mp.mpf(point['residualDecimal']),
                  mp.mpf(point['stepDecimal']), mp.mpf(point['predictionError']),
                  point['newtonIterations'], point['event'])


def restore_track(data):
    result = {key: data[key] for key in ('id', 'startZeroIndex', 'status', 'stopReason')}
    result['points'] = [restore_point(point) for point in data['points']]
    result['endpoint'] = restore_point(data['endpoint'])
    result['rejectedSteps'] = [{key: value if key == 'reason' else mp.mpf(value) for key, value in row.items()}
                               for row in data['rejectedSteps']]
    result['exit'] = None
    if data['exit']:
        result['exit'] = dict(data['exit'], inside=restore_point(data['exit']['inside']),
                              outside=restore_point(data['exit']['outside']), widthA=mp.mpf(data['exit']['widthA']))
    return result


def worker_run(variant, index, start=None):
    command = [sys.executable, '-B', str(Path(__file__).resolve()), '--worker', variant, '--index', str(index)]
    payload = json.dumps(serialize_point(start)) if start is not None else None
    completed = subprocess.run(command, input=payload, capture_output=True, text=True)
    require(completed.returncode == 0,
            f'isolated {variant} Z{index} failed without publishing evidence: ' + completed.stderr[-4000:])
    return restore_track(json.loads(completed.stdout))


def main():
    require(mp.__version__ == '1.3.0', 'use pinned mpmath1.3.0')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent / 'evidence')
    parser.add_argument('--worker', choices=('base', 'coarse', 'fine', 'reverse'), help=argparse.SUPPRESS)
    parser.add_argument('--index', type=int, choices=(1, 2, 3), help=argparse.SUPPRESS)
    args = parser.parse_args()
    value = lambda s: mp.zeta(s, method='euler-maclaurin')
    derivative = lambda s: mp.zeta(s, derivative=1, method='euler-maclaurin')
    if args.worker:
        require(args.index is not None, 'worker needs a zero index')
        if args.worker == 'reverse':
            start = restore_point(json.load(sys.stdin))
            path = track(value, derivative, start['s'], start['a'], 0, DOMAIN, Settings(), f'Z{args.index}-reverse')
        else:
            path = track(value, derivative, mp.zetazero(args.index), 0, 1, DOMAIN, variants()[args.worker], f'Z{args.index}')
        path['startZeroIndex'] = args.index
        print(json.dumps(serialize_track(path)))
        return
    started = time.monotonic()
    settings = Settings()
    controls = model_controls(settings)
    print('Model controls passed.', file=sys.stderr, flush=True)
    # Select mpmath's general Euler-Maclaurin route explicitly. The default
    # fast kernel raised intermittent internal TypeErrors on this Python3.14
    # host during long runs; no failed run is used as accepted evidence.
    runs = {}
    for variant in variants():
        runs[variant] = []
        for index in (1, 2, 3):
            path = worker_run(variant, index)
            require(path['status'] in ('completed', 'exited'), 'unresolved zeta path: ' + path['stopReason'])
            runs[variant].append(path)
            print(f"{variant} Z{index}: {path['status']}, a={mp.nstr(path['endpoint']['a'],18)}, points={len(path['points'])}", file=sys.stderr, flush=True)
    comparisons = []
    reverse_reports = []
    for index, base in enumerate(runs['base']):
        comparisons.append({'id': base['id'], 'coarse': compare_tracks(base, runs['coarse'][index]),
                            'fine': compare_tracks(base, runs['fine'][index])})
        reverse = worker_run('reverse', index + 1, base['endpoint'])
        require(reverse['status'] == 'completed', 'reverse continuation did not finish')
        error = abs(reverse['endpoint']['s'] - base['points'][0]['s'])
        require(error < mp.mpf('1e-45'), 'reverse endpoint mismatch')
        forward_checks, reverse_checks = checkpoint_points(base), checkpoint_points(reverse)
        shared = [abs(forward_checks[k]['s'] - reverse_checks[k]['s']) for k in range(11)
                  if forward_checks[k] is not None and reverse_checks[k] is not None]
        require(max(shared) < mp.mpf('1e-45'), 'reverse common-target mismatch')
        reverse_reports.append({'id': base['id'], 'acceptedPoints': len(reverse['points']),
                                'endpointError': decimal(error), 'commonCheckpoints': len(shared),
                                'maximumCommonTargetError': decimal(max(shared))})
        print(base['id'] + ' reverse check passed.', file=sys.stderr, flush=True)
    config = {key: decimal(value) if not isinstance(value, int) else value for key, value in vars(settings).items()}
    trajectories = {'schema': 'graph-zeta-continuation-reference-v1', 'traceId': 'graph.riemann.continuation.animation.verify',
                    'precisionDigits': 80, 'mpmathVersion': mp.__version__,
                    'referenceMethod': 'mpmath Euler-Maclaurin at80digits',
                    'domain': dict(zip(('minSigma', 'maxSigma', 'minT', 'maxT'), map(float, DOMAIN))),
                    'settings': config, 'reseeding': False,
                    'trajectories': [serialize_track(path) for path in runs['base']]}
    report = {'status': 'passed', 'traceId': 'graph.riemann.continuation.animation.verify',
              'precisionDigits': 80, 'mpmathVersion': mp.__version__, 'settings': config,
              'referenceMethod': 'mpmath Euler-Maclaurin at80digits',
              'executionModel': 'Fresh Python subprocess per branch and forward/reverse variant; no failed run is accepted.',
              'modelControls': controls, 'variants': {name: [summary(path) for path in paths] for name, paths in runs.items()},
              'coarseFineComparisons': comparisons, 'reverseComparisons': reverse_reports,
              'elapsedSeconds': time.monotonic() - started,
              'observedOutcome': {'completed': [path['id'] for path in runs['base'] if path['status'] == 'completed'],
                                  'exited': [path['id'] for path in runs['base'] if path['status'] == 'exited'],
                                  'allThreeReachDistinctInViewOnePoints': all(path['status'] == 'completed' for path in runs['base'])},
              'limitations': ['Empirical high-precision continuation, not interval-certified branch isolation.',
                              'Reference and native evaluators are separate implementations of the same Euler-Maclaurin algorithm family.',
                              'First detected exits are bracketed; an unseen excursion between samples is not rigorously excluded.',
                              'A positive sampled derivative minimum does not certify nonvanishing between samples.',
                              'A viewport exit is not disappearance or proof that a branch never returns.',
                              'Display interpolation is not a solved root. No global reseeding or endpoint replacement is used.',
                              'Off-line zeta=1 points are not counterexamples to RH. No exhaustive or RH claim is made.']}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'reference-trajectories.json').write_text(json.dumps(trajectories, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'numerical-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'elapsedSeconds': report['elapsedSeconds'], 'observedOutcome': report['observedOutcome'],
                      'trajectories': str(args.output_dir / 'reference-trajectories.json'),
                      'report': str(args.output_dir / 'numerical-report.json')}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, ArithmeticError, Rejected, TypeError, ValueError, OSError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
