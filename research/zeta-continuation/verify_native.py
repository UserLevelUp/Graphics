"""Compare native continuation exports with the validated80-digit trajectories.

Usage: python -B verify_native.py evidence/native/*.values.json --output evidence/native-validation.json
Each branch is checked in a fresh subprocess. Reference and native evaluators
are separate implementations of the same Euler-Maclaurin algorithm family.
"""
import argparse
import copy
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import traceback

import mpmath as mp

# defines: graph.riemann.continuation.animation.native_verify
# consumer: graph.riemann.continuation.animation.verify
mp.mp.dps = 80
COORD_TOL = mp.mpf('5e-9')
RESIDUAL_TOL = mp.mpf('1e-9')
DOMAIN = tuple(map(mp.mpf, ['.05', '3', '10', '30']))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def scalar(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), label + ': finite number required')
    return mp.mpf(value)


def complex_value(value, label):
    require(isinstance(value, dict), label + ': coordinate object required')
    return mp.mpc(scalar(value.get('real'), label + '.real'), scalar(value.get('imaginary'), label + '.imaginary'))


def precise_point(point):
    return mp.mpf(point['aDecimal']), mp.mpc(point['sDecimal']['real'], point['sDecimal']['imaginary']), mp.mpc(
        point['derivativeDecimal']['real'], point['derivativeDecimal']['imaginary'])


def inside(s):
    return DOMAIN[0] - mp.mpf('1e-16') <= s.real <= DOMAIN[1] and DOMAIN[2] <= s.imag <= DOMAIN[3]


@lru_cache(maxsize=4096)
def evaluate(real, imaginary):
    s = mp.mpc(mp.mpf(real), mp.mpf(imaginary))
    return mp.zeta(s, method='euler-maclaurin'), mp.zeta(s, derivative=1, method='euler-maclaurin')


def branch_checker(reference):
    seeds = [precise_point(point) for point in reference['points']]
    @lru_cache(maxsize=1024)
    def expected_root(a_float):
        a = mp.mpf(a_float)
        seed_a, seed_s, seed_d = min(seeds, key=lambda row: abs(row[0] - a))
        require(abs(seed_a - a) <= mp.mpf('.05'), 'native target too far from verified reference segment')
        predicted = seed_s + (a - seed_a) / seed_d
        s = predicted
        for _ in range(14):
            value = mp.zeta(s, method='euler-maclaurin') - a
            derivative = mp.zeta(s, derivative=1, method='euler-maclaurin')
            if abs(value) <= mp.mpf('1e-55'):
                require(abs(s - predicted) < mp.mpf('.01'), 'reference comparison left local branch neighborhood')
                return s
            require(abs(derivative) > mp.mpf('1e-8'), 'comparison derivative guard')
            correction = value / derivative
            require(abs(correction) < mp.mpf('.1'), 'comparison Newton motion guard')
            s -= correction
        raise AssertionError('independent comparison correction failed')

    def check_point(point, label):
        a = scalar(point.get('a'), label + '.a')
        require(0 <= a <= 1, label + ': target range')
        s = complex_value(point.get('s'), label + '.s')
        value, derivative = evaluate(float(s.real), float(s.imag))
        residual = abs(value - a)
        require(residual <= RESIDUAL_TOL, label + ': independent residual exceeds1e-9')
        reported = scalar(point.get('residual'), label + '.residual')
        require(0 <= reported <= mp.mpf('2.001e-11'), label + ': native residual stopping threshold')
        require(abs(reported - residual) <= mp.mpf('5e-11'), label + ': inconsistent reported residual')
        actual_derivative = complex_value(point.get('derivative'), label + '.derivative')
        derivative_error = abs(actual_derivative - derivative)
        require(derivative_error <= COORD_TOL, label + ': derivative mismatch')
        require(abs(actual_derivative) >= mp.mpf('1e-8'), label + ': derivative guard')
        expected = expected_root(float(a))
        coordinate_error = abs(s - expected)
        require(coordinate_error <= COORD_TOL, label + ': coordinate mismatch exceeds5e-9')
        require(type(point.get('newtonIterations')) is int and 0 <= point['newtonIterations'] < 16,
                label + ': Newton iteration limit')
        require(0 <= scalar(point.get('predictionError'), label + '.predictionError') <= mp.mpf('.00100000001'),
                label + ': predictor-correction limit')
        scalar(point.get('step'), label + '.step')
        return {'residual': residual, 'coordinateError': coordinate_error, 'derivativeError': derivative_error}
    return check_point


def check_edge(previous, point):
    a0, a1 = mp.mpf(previous['a']), mp.mpf(point['a'])
    require(a1 > a0, 'nonincreasing continuation target')
    step = mp.mpf(point['step'])
    require(abs(step - (a1 - a0)) < mp.mpf('1e-14'), 'step differs from preceding accepted point')
    s0, s1 = complex_value(previous['s'], 'previous.s'), complex_value(point['s'], 'point.s')
    d0 = complex_value(previous['derivative'], 'previous.derivative')
    predicted = s0 + step / d0
    require(abs(predicted - s0) <= mp.mpf('.06000000001'), 'predicted-motion guard exceeded')
    require(abs(s1 - s0) <= mp.mpf('.09000000001'), 'accepted-motion guard exceeded')
    error = abs(s1 - predicted)
    require(abs(error - mp.mpf(point['predictionError'])) <= mp.mpf('5e-12'), 'predictor error metadata mismatch')


def verify_branch(payload):
    native, reference = payload['native'], payload['reference']
    require(native['id'] == reference['id'] and native['startZeroIndex'] == reference['startZeroIndex'], 'branch identity mismatch')
    require(native['status'] == reference['status'], 'branch outcome disagrees with reference')
    points = native['points']
    require(len(points) >= 2 and points[0]['a'] == 0 and native['endpoint'] == points[-1], 'invalid path endpoints')
    check_point = branch_checker(reference)
    results = []
    for index, point in enumerate(points):
        require(inside(complex_value(point['s'], 'path.s')), 'accepted native point outside viewport')
        results.append(check_point(point, f"{native['id']}[{index}]"))
        if index:
            check_edge(points[index - 1], point)
    for row in native.get('rejectedSteps', []):
        require(row['step'] > 0 and row['attemptedA'] > row['a'] and bool(row['reason']), 'invalid rejected-step evidence')
    bracket_report = None
    if native['status'] == 'completed':
        require(native['endpoint']['a'] == 1 and native['exit'] is None, 'completed branch missing target1')
    else:
        bracket = native['exit']
        require(isinstance(bracket, dict) and bracket['inside'] == native['endpoint'], 'missing matching exit bracket')
        inside_a, outside_a = mp.mpf(bracket['inside']['a']), mp.mpf(bracket['outside']['a'])
        width = outside_a - inside_a
        require(0 < width <= mp.mpf('1.00001e-10'), 'native boundary bracket too wide')
        require(abs(width - mp.mpf(bracket['widthA'])) < mp.mpf('1e-15'), 'incorrect bracket width metadata')
        require(not inside(complex_value(bracket['outside']['s'], 'outside.s')), 'outside bracket point is inside')
        require(bracket['boundaries'] == reference['exit']['boundaries'], 'different boundary exit')
        reference_left = mp.mpf(reference['exit']['inside']['aDecimal'])
        reference_right = mp.mpf(reference['exit']['outside']['aDecimal'])
        require(inside_a <= reference_left <= reference_right <= outside_a, 'native bracket does not contain refined reference exit')
        results.append(check_point(bracket['outside'], native['id'] + '-outside'))
        bracket_report = {'nativeWidthA': mp.nstr(width, 20), 'containsReferenceBracket': True}
    for display in payload['displayPoints']:
        results.append(check_point(display, native['id'] + '-display'))
    negative = []
    wrong = copy.deepcopy(points[0]); wrong['s']['real'] += .001
    try:
        check_point(wrong, 'corrupted coordinate')
    except AssertionError:
        negative.append('corrupted coordinate')
    else:
        raise AssertionError('coordinate corruption accepted')
    wrong = copy.deepcopy(points[0]); wrong['a'] = .02
    try:
        check_point(wrong, 'false target')
    except AssertionError:
        negative.append('false target')
    else:
        raise AssertionError('false target accepted')
    wrong = copy.deepcopy(points[1]); wrong['step'] += .01
    try:
        check_edge(points[0], wrong)
    except AssertionError:
        negative.append('false step history')
    else:
        raise AssertionError('false step history accepted')
    return {'id': native['id'], 'status': 'passed', 'acceptedNativePoints': len(points),
            'checkedPointRecordsIncludingDisplaysAndOutside': len(results), 'exit': bracket_report,
            'maximumErrors': {key: mp.nstr(max(row[key] for row in results), 20)
                              for key in ('residual', 'coordinateError', 'derivativeError')},
            'rejectedNegativeControls': negative}


def check_document(document):
    require(document.get('schema') == 'graph-zeta-continuation-v1', 'native schema mismatch')
    require(document.get('domain') == {'minSigma': .05, 'maxSigma': 3, 'minT': 10, 'maxT': 30}, 'native domain mismatch')
    expected = {'initialStep': .025, 'maxStep': .04, 'minStep': 1e-7, 'derivativeGuard': 1e-8,
                'residualTolerance': 2e-11, 'predictionMotionLimit': .06, 'acceptedMotionLimit': .09,
                'predictorCorrectionLimit': .001, 'boundaryToleranceA': 1e-10, 'reseeding': False}
    require(document.get('settings') == expected, 'native numerical settings changed')
    target = scalar(document.get('target'), 'target')
    require(0 <= target <= 1, 'target outside continuation interval')
    require(type(document.get('resolution')) is int and 64 <= document['resolution'] <= 512, 'invalid resolution')
    scalar(document.get('paletteDegrees'), 'paletteDegrees')
    trajectories = {row['id']: row for row in document['trajectories']}
    states = {row['id']: row for row in document['displayedStates']}
    require(set(trajectories) == set(states) == {'Z1', 'Z2', 'Z3'}, 'missing trajectory/display identity')
    for name, state in states.items():
        endpoint = trajectories[name]['endpoint']
        if target > mp.mpf(endpoint['a']) + mp.mpf('1e-12'):
            require(state['status'] == trajectories[name]['status'] == 'exited'
                    and state['heldAtEarlierTarget'] is True and state['point'] == endpoint,
                    name + ': exited root falsely transported to the current target')
        else:
            expected_status = 'completed' if target == 1 else 'active'
            require(state['status'] == expected_status and state['heldAtEarlierTarget'] is False,
                    name + ': active display metadata')
            require(abs(mp.mpf(state['point']['a']) - target) <= mp.mpf('1e-12'), name + ': displayed target mismatch')
    samples = document.get('backgroundSamples')
    require(isinstance(samples, list) and len(samples) >= 30, 'missing background samples')
    maximum = mp.mpf(0)
    for sample in samples:
        s = complex_value(sample['s'], 'background.s')
        value, _ = evaluate(float(s.real), float(s.imag))
        exported = complex_value(sample['zeta'], 'background.zeta')
        error = abs(exported - value)
        require(error <= COORD_TOL, 'background zeta mismatch')
        shifted = complex_value(sample['shifted'], 'background.shifted')
        require(abs(shifted - (exported - target)) <= mp.mpf('1e-12'), 'background shift mismatch')
        maximum = max(maximum, error)
    return {'target': float(target), 'backgroundSamplesChecked': len(samples), 'maximumBackgroundZetaError': mp.nstr(maximum, 20)}


def main():
    require(mp.__version__ == '1.3.0', 'use pinned mpmath1.3.0')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exports', nargs='*', type=Path)
    parser.add_argument('--reference', type=Path, default=Path(__file__).resolve().parent / 'evidence' / 'reference-trajectories.json')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(verify_branch(json.load(sys.stdin))))
        return
    require(bool(args.exports), 'provide actual native export files')
    reference_bytes = args.reference.read_bytes()
    reference = json.loads(reference_bytes.decode('utf-8-sig'))
    require(reference['precisionDigits'] == 80 and reference['reseeding'] is False, 'invalid reference provenance')
    documents, reports = [], []
    for path in args.exports:
        data = path.read_bytes()
        document = json.loads(data.decode('utf-8-sig'))
        reports.append(dict(check_document(document), source=str(path.resolve()), sourceSha256=hashlib.sha256(data).hexdigest()))
        documents.append(document)
    native_paths = documents[0]['trajectories']
    require(all(document['trajectories'] == native_paths for document in documents), 'frame settings changed cached mathematical paths')
    branch_reports = []
    for native in native_paths:
        ref = next(row for row in reference['trajectories'] if row['id'] == native['id'])
        displays = [next(row['point'] for row in document['displayedStates'] if row['id'] == native['id']) for document in documents]
        payload = {'native': native, 'reference': ref, 'displayPoints': displays}
        completed = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--worker'],
                                   input=json.dumps(payload), capture_output=True, text=True)
        require(completed.returncode == 0, 'native validation worker failed (exit ' + str(completed.returncode)
                + '): ' + completed.stderr[-4000:] + completed.stdout[-1000:])
        branch_reports.append(json.loads(completed.stdout))
        print(native['id'] + ' native validation passed.', file=sys.stderr, flush=True)
    terminal = next((document for document in documents if document['target'] == 1), None)
    require(terminal is not None, 'target1 export required for held-exit regression')
    wrong = copy.deepcopy(terminal)
    wrong['displayedStates'][0]['heldAtEarlierTarget'] = False
    try:
        check_document(wrong)
    except AssertionError:
        held_rejected = True
    else:
        held_rejected = False
    require(held_rejected, 'false post-exit transport accepted')
    report = {'status': 'passed', 'traceId': 'graph.riemann.continuation.animation.native_verify',
              'precisionDigits': 80, 'mpmathVersion': mp.__version__,
              'referenceSha256': hashlib.sha256(reference_bytes).hexdigest(),
              'exports': reports, 'branches': branch_reports, 'cachedPathsIdenticalAcrossExports': True,
              'falsePostExitTransportRejected': held_rejected,
              'tolerances': {'nativeCoordinateAndDerivativeAbsolute': '5e-9', 'nativeResidualAbsolute': '1e-9',
                             'referenceCorrectionResidual': '1e-55', 'nativeBoundaryWidthA': '1e-10'},
              'limitations': ['Empirical numerical validation, not interval-certified continuation.',
                              'Reference uses a separate80-digit implementation of the same Euler-Maclaurin algorithm family.',
                              'Accepted native targets are compared by local correction from the validated reference branch, never global endpoint search.',
                              'Native boundary brackets are checked separately against the refined reference brackets.',
                              'Root positions held after exit solve their recorded earlier a, not the later displayed target.',
                              'No exhaustive statement, global noncollision theorem, or RH conclusion.']}
    encoded = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(encoded, encoding='utf-8')
    print(encoded, end='')


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, ArithmeticError, KeyError, TypeError, ValueError, OSError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
