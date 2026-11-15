"""Independent 80-digit numerical checks for the two-state zeta laboratory.

Install requirements.txt in an isolated environment. Then:
  python -B verify_exports.py --references --output reference.json
  python -B verify_exports.py export.values.json [other.controls.values.json]

These are empirical high-precision cross-checks, not interval certificates or
a proof of the Riemann Hypothesis. Reference markers never select a branch.
"""
import argparse
import copy
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import mpmath as mp

# defines: graph.riemann.switch.verify
# consumer: graph.riemann.switch.proof
mp.mp.dps = 80
VALUE_TOL = mp.mpf('5e-11')
DERIVATIVE_TOL = mp.mpf('5e-10')
ALGEBRA_TOL = mp.mpf('2e-12')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def scalar(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), label + ': finite JSON number required')
    return mp.mpf(value)


def complex_value(value, label):
    require(isinstance(value, dict), label + ': complex coordinate object required')
    return mp.mpc(scalar(value.get('real'), label + '.real'),
                  scalar(value.get('imaginary'), label + '.imaginary'))


def text_number(value):
    return mp.nstr(value, 78)


def text_complex(value):
    return {'real': text_number(value.real), 'imaginary': text_number(value.imag)}


def check_close(actual, expected, label, tolerance=ALGEBRA_TOL):
    error = abs(actual - expected)
    require(error <= tolerance * max(1, abs(expected)),
            label + ': error ' + mp.nstr(error, 12) + ' exceeds tolerance')
    return error


@lru_cache(maxsize=8192)
def independent_value(real, imaginary):
    s = mp.mpc(mp.mpf(real), mp.mpf(imaginary))
    return mp.zeta(s), mp.zeta(s, derivative=1)


def at_exported_point(point):
    # mp.mpf(float) preserves the exported binary input at the working precision.
    return independent_value(float(point.real), float(point.imag))


@lru_cache(maxsize=1)
def reference_markers():
    zeros = [('zeta-zero', 'zeta zero ' + str(index), mp.zetazero(index), 0)
             for index in range(1, 4)]
    one = mp.findroot(lambda s: mp.zeta(s) - 1, mp.mpc('1.4', '23.33'), tol=mp.mpf('1e-72'))
    require(mp.mpf('.05') < one.real < 3 and 10 < one.imag < 30
            and abs(mp.zeta(one) - 1) < mp.mpf('1e-65'), 'independent 1-point refinement')
    return zeros + [('zeta-one', 'zeta 1-point 1', one, 1)]


def references():
    markers = []
    points = [(f'corner_{sigma}_{height}', mp.mpc(sigma, height))
              for sigma in ('0.05', '3') for height in ('10', '30')]
    for kind, label, s, target in reference_markers():
        zeta = mp.zeta(s)
        markers.append({'kind': kind, 'label': label, 's': text_complex(s), 'target': target,
                        'zeta': text_complex(zeta), 'derivative': text_complex(mp.zeta(s, derivative=1)),
                        'residual': text_number(abs(zeta - target))})
        points.append((label, s))
    for k in (2, 3):
        height = 2 * mp.pi * k / mp.log(2)
        for offset in ('-0.0000001', '0', '0.0000001'):
            points.append((f'eta_removable_{k}_sigma_offset_{offset}', mp.mpc(1 + mp.mpf(offset), height)))
    seam_height = mp.im(mp.zetazero(1))
    seam_sigma = mp.findroot(lambda sigma: mp.re(mp.zeta(mp.mpc(sigma, seam_height))) - mp.mpf('.5'),
                            (mp.mpf('1.3'), mp.mpf('1.5')))
    seam_s = mp.mpc(seam_sigma, seam_height)
    seam_zeta = mp.zeta(seam_s)
    records = []
    for label, s in points:
        value = mp.zeta(s)
        records.append({'id': label, 's': text_complex(s), 'zeta': text_complex(value),
                        'derivative': text_complex(mp.zeta(s, derivative=1)),
                        'b': 1 if value.real <= mp.mpf('.5') else 0,
                        'product': text_complex(value * (value - 1))})
    return {'schema': 'graph-zeta-switch-independent-reference-v1', 'precisionDigits': 80,
            'mpmathVersion': mp.__version__, 'recommendedDomain': {'minSigma': '.05', 'maxSigma': '3', 'minT': '10', 'maxT': '30'},
            'markers': markers, 'samples': records,
            'seamReference': {'s': text_complex(seam_s), 'zeta': text_complex(seam_zeta),
                              'selectedMagnitude': text_number(abs(seam_zeta)),
                              'note': 'Re zeta=.5; tie chooses1. Selected magnitude is at least .5, not zero.'},
            'limitations': ['High-precision numerical references, not interval certification.',
                           'Marker searches are not exhaustive and are never selector inputs.']}


def check_selection(record, label):
    value = complex_value(record.get('zeta'), label + '.zeta')
    expected_b = 1 if value.real <= mp.mpf('.5') else 0
    require(type(record.get('b')) is int and record['b'] == expected_b, label + ': wrong selector or tie')
    selected = complex_value(record.get('selected'), label + '.selected')
    product = complex_value(record.get('product'), label + '.product')
    if expected_b == 1:
        require(selected == value, label + ': branch1 must preserve the input value exactly')
    require(selected.imag == value.imag, label + ': selector must preserve imaginary component exactly')
    check_close(selected, value - 1 + expected_b, label + ': selected value')
    check_close(product, value * (value - 1), label + ': analytic product')
    check_close(selected.imag, value.imag, label + ': imaginary component')
    check_close(abs(selected), min(abs(value), abs(value - 1)), label + ': nearest magnitude')
    return value, selected, product


def check_sample(record, label):
    s = complex_value(record.get('s'), label + '.s')
    require(mp.mpf('.05') - mp.mpf('1e-15') <= s.real <= 3 + mp.mpf('1e-15')
            and 10 <= s.imag <= 30, label + ': sample outside evaluator contract domain')
    zeta, selected, product = check_selection(record, label)
    reference, derivative = at_exported_point(s)
    zeta_error = check_close(zeta, reference, label + ': independent zeta', VALUE_TOL)
    derivative_error = check_close(complex_value(record.get('derivative'), label + '.derivative'),
                                   derivative, label + ': independent derivative', DERIVATIVE_TOL)
    check_close(complex_value(record.get('zetaMinusOne'), label + '.zetaMinusOne'), zeta - 1,
                label + ': constant shift')
    refined = complex_value(record.get('refinedZeta'), label + '.refinedZeta')
    refined_error = check_close(refined, reference, label + ': refined independent zeta', VALUE_TOL)
    check_close(scalar(record.get('refinementDelta'), label + '.refinementDelta'), abs(zeta - refined),
                label + ': refinement discrepancy', mp.mpf('1e-20'))
    margin = abs(reference.real - mp.mpf('.5'))
    if margin > VALUE_TOL:
        require(record['b'] == (1 if reference.real <= mp.mpf('.5') else 0),
                label + ': branch disagrees with independent value away from seam')
    return {'zetaError': zeta_error, 'derivativeError': derivative_error,
            'refinedZetaError': refined_error, 'nearSeam': margin <= VALUE_TOL}


def check_probe_set(probes):
    require(isinstance(probes, list) and len(probes) >= 8, 'missing explicit selector probes')
    values = []
    for index, probe in enumerate(probes):
        values.append(check_selection(probe, 'selectorProbes[' + str(index) + ']'))
    def locate(real, imaginary):
        target = mp.mpc(real, imaginary)
        matches = [row for row in values if abs(row[0] - target) < mp.mpf('2e-16')]
        require(bool(matches), 'missing selector probe ' + str(target))
        return matches[0]
    left = locate('0.49999999', '0.3')
    tie = locate('0.5', '0.3')
    right = locate('0.50000001', '0.3')
    real_tie = locate('0.5', '0')
    locate('0', '0')
    locate('1', '0')
    check_close(right[1] - left[1], mp.mpc('-0.99999998', 0), 'seam jump control')
    require(abs(tie[1]) >= mp.mpf('.5') and abs(real_tie[1]) == mp.mpf('.5'),
            'switch seam was mistaken for a selected zero')
    for probe_id, sign in [('tiny-positive', 1), ('tiny-negative', -1)]:
        matching = [probe for probe in probes if probe.get('id') == probe_id]
        require(len(matching) == 1, 'missing tiny preservation probe ' + probe_id)
        value, selected, _ = check_selection(matching[0], probe_id)
        require(0 < sign * value.real < mp.mpf('1e-16') and selected == value,
                probe_id + ': cancellation erased a tiny branch1 value')
    return {'count': len(probes), 'tieSelectsOne': True, 'unitJumpControl': True,
            'seamIsNonzero': True, 'tinyBranchOneValuesPreservedExactly': True}


def check_marker(record, domain, label):
    kind = record.get('kind')
    require(kind in ('zeta-zero', 'zeta-one'), label + ': unknown marker kind')
    target = 0 if kind == 'zeta-zero' else 1
    require(type(record.get('target')) is int and record['target'] == target,
            label + ': marker kind/target mismatch')
    require(isinstance(record.get('label'), str) and bool(record['label'].strip()), label + ': missing label')
    s = complex_value(record.get('s'), label + '.s')
    require(domain['minSigma'] <= s.real <= domain['maxSigma']
            and domain['minT'] <= s.imag <= domain['maxT'], label + ': marker outside plot domain')
    value = complex_value(record.get('zeta'), label + '.zeta')
    reference, derivative = at_exported_point(s)
    check_close(value, reference, label + ': independent marker zeta', VALUE_TOL)
    actual_residual = abs(reference - target)
    require(actual_residual <= mp.mpf('1e-8'), label + ': marker is not at its labeled target')
    require(abs(derivative) > mp.mpf('1e-6'), label + ': finite-precision false/degenerate marker')
    check_close(scalar(record.get('residual'), label + '.residual'), abs(value - target),
                label + ': marker residual', mp.mpf('1e-20'))
    check_close(scalar(record.get('refinedResidual'), label + '.refinedResidual'), actual_residual,
                label + ': refined marker residual', VALUE_TOL)
    movement = scalar(record.get('refinementMovement'), label + '.refinementMovement')
    require(0 <= movement < mp.mpf('1e-6'), label + ': marker refinement instability')
    require(type(record.get('iterations')) is int and 0 <= record['iterations'] < 30,
            label + ': invalid iteration count')
    return {'kind': kind, 's': s, 'independentResidual': actual_residual}


def validate_document(document):
    require(document.get('schema') == 'graph-zeta-switch-v1', 'wrong export schema')
    raw_domain = document.get('domain')
    require(isinstance(raw_domain, dict), 'missing actual domain')
    domain = {name: scalar(raw_domain.get(name), 'domain.' + name)
              for name in ('minSigma', 'maxSigma', 'minT', 'maxT')}
    check_close(domain['minSigma'], mp.mpf('.05'), 'minimum sigma')
    check_close(domain['maxSigma'], 3, 'maximum sigma')
    require(10 <= domain['minT'] < domain['maxT'] <= 30, 'invalid height range')
    settings = document.get('settings')
    require(isinstance(settings, dict), 'missing actual settings')
    require(type(settings.get('resolution')) is int and settings['resolution'] in (128, 256, 384), 'invalid resolution')
    require(0 <= scalar(settings.get('paletteDegrees'), 'settings.paletteDegrees') <= 360, 'invalid palette')
    require(type(settings.get('showMarkers')) is bool, 'invalid marker visibility')
    evaluator = settings.get('evaluator')
    require(isinstance(evaluator, dict) and evaluator.get('method') == 'Euler-Maclaurin'
            and evaluator.get('n') == 64 and evaluator.get('corrections') == 10
            and evaluator.get('refinementN') == 96, 'unexpected evaluator parameters')
    interpretation = document.get('interpretation')
    require(isinstance(interpretation, dict) and interpretation.get('selectorUsesMarkers') is False
            and interpretation.get('selectedAnalytic') is False
            and interpretation.get('productAnalyticOnDomain') is True,
            'missing/incorrect selector and analyticity metadata')
    samples = document.get('samples')
    require(isinstance(samples, list) and len(samples) >= 165, 'insufficient actual samples')
    ids = [sample.get('id') for sample in samples]
    require(all(isinstance(item, str) and item for item in ids) and len(set(ids)) == len(ids), 'sample IDs missing or duplicated')
    indexed = {sample['id']: sample for sample in samples}
    for y in range(9):
        for x in range(16):
            sample_id = f'grid-{y}-{x}'
            require(sample_id in indexed, 'missing fixed-grid sample ' + sample_id)
            expected = mp.mpc(domain['minSigma'] + (domain['maxSigma'] - domain['minSigma']) * x / 15,
                              domain['minT'] + (domain['maxT'] - domain['minT']) * y / 8)
            check_close(complex_value(indexed[sample_id]['s'], sample_id + '.s'), expected,
                        sample_id + ': grid coordinates')
    for sample in samples:
        point = complex_value(sample['s'], sample['id'] + '.s')
        inside = domain['minT'] <= point.imag <= domain['maxT']
        require(sample.get('insideView') is inside, sample['id'] + ': insideView metadata')
    require({'reference-zero', 'reference-one', 'reference-seam'} <= set(ids), 'missing independent-location probes')
    results = [check_sample(sample, 'samples[' + str(index) + ']') for index, sample in enumerate(samples)]
    # Require the eta-quotient cancellation sites to be tested independently.
    for k in (2, 3):
        for dx in ('-1e-7', '0', '1e-7'):
            for dy in ('-1e-7', '0', '1e-7'):
                point = mp.mpc(1 + mp.mpf(dx), 2 * mp.pi * k / mp.log(2) + mp.mpf(dy))
                require(any(abs(complex_value(sample['s'], 'sample.s') - point) < mp.mpf('1e-12') for sample in samples),
                        'missing eta removable-site neighborhood control')
    metrics = document.get('metrics')
    require(isinstance(metrics, dict), 'missing grid metrics')
    for key in ('validPixels', 'invalidPixels', 'branchOnePixels', 'branchZeroPixels', 'seamCells'):
        require(type(metrics.get(key)) is int and metrics[key] >= 0, 'invalid pixel metric ' + key)
    require(metrics['invalidPixels'] == 0 and metrics['validPixels'] == settings['resolution'] ** 2
            and metrics['branchOnePixels'] + metrics['branchZeroPixels'] == metrics['validPixels']
            and metrics['seamCells'] <= (settings['resolution'] - 1) ** 2, 'inconsistent grid metrics')
    check_close(scalar(metrics.get('maxRefinementDelta'), 'metrics.maxRefinementDelta'),
                max(scalar(sample['refinementDelta'], 'sample.refinementDelta') for sample in samples),
                'maximum reported refinement discrepancy', mp.mpf('1e-20'))
    probe_result = check_probe_set(document.get('selectorProbes'))
    markers = document.get('markers')
    require(isinstance(markers, list), 'missing marker list')
    checked_markers = [check_marker(marker, domain, 'markers[' + str(i) + ']') for i, marker in enumerate(markers)]
    for index, marker in enumerate(checked_markers):
        require(all(marker['kind'] != other['kind'] or abs(marker['s'] - other['s']) > mp.mpf('1e-6')
                    for other in checked_markers[:index]), 'duplicate numerical marker')
    if settings['showMarkers']:
        for kind, label, s, _ in reference_markers():
            if domain['minSigma'] <= s.real <= domain['maxSigma'] and domain['minT'] <= s.imag <= domain['maxT']:
                require(any(marker['kind'] == kind and abs(marker['s'] - s) < mp.mpf('1e-6') for marker in checked_markers),
                        'missing independently known marker: ' + label)
    return {'status': 'passed', 'sampleCount': len(samples), 'markerCount': len(markers),
            'maximumAbsoluteErrors': {key: mp.nstr(max(result[key] for result in results), 15)
                                      for key in ('zetaError', 'derivativeError', 'refinedZetaError')},
            'nearSeamSamplesNotIndependentlyClassified': sum(result['nearSeam'] for result in results),
            'maximumIndependentMarkerResidual': mp.nstr(max([marker['independentResidual'] for marker in checked_markers] + [mp.mpf(0)]), 15),
            'selectorControls': probe_result, 'settings': settings, 'domain': raw_domain}


def negative_controls(document):
    sample = document['samples'][0]
    def consistent_wrong_zeta(record):
        value = complex(record['zeta']['real'], record['zeta']['imaginary']) + complex(.1, .02)
        def coords(z):
            return {'real': z.real, 'imaginary': z.imag}
        record.update(zeta=coords(value), zetaMinusOne=coords(value - 1),
                      refinedZeta=coords(value), refinementDelta=0,
                      b=1 if value.real <= .5 else 0)
        record['selected'] = coords(value if record['b'] == 1 else value - 1)
        record['product'] = coords(value * (value - 1))
    mutations = [
        ('self-consistent incorrect zeta', consistent_wrong_zeta),
        ('incorrect derivative', lambda r: r['derivative'].update(real=r['derivative']['real'] + .1)),
        ('selector flipped', lambda r: r.update(b=1 - r['b'])),
        ('selected value corrupted', lambda r: r['selected'].update(real=r['selected']['real'] + .1)),
        ('analytic product corrupted', lambda r: r['product'].update(real=r['product']['real'] + .1)),
        ('refinement discrepancy hidden', lambda r: r.update(refinementDelta=1)),
    ]
    rejected = []
    for name, mutate in mutations:
        wrong = copy.deepcopy(sample)
        mutate(wrong)
        try:
            check_sample(wrong, name)
        except (AssertionError, ValueError, KeyError, TypeError):
            rejected.append(name)
            continue
        raise AssertionError('corrupted sample was accepted: ' + name)
    tie = next(probe for probe in document['selectorProbes'] if probe['zeta']['real'] == .5)
    for name, mutate in [
        ('tie incorrectly chooses zero', lambda p: p.update(b=0)),
        ('seam drawn as a zero', lambda p: p.update(selected={'real': 0, 'imaginary': 0})),
    ]:
        wrong = copy.deepcopy(tie)
        mutate(wrong)
        try:
            check_selection(wrong, name)
        except AssertionError:
            rejected.append(name)
            continue
        raise AssertionError('corrupted seam control was accepted: ' + name)
    tiny = copy.deepcopy(next(probe for probe in document['selectorProbes'] if probe.get('id') == 'tiny-positive'))
    tiny['selected'] = {'real': 0, 'imaginary': 0}
    try:
        check_selection(tiny, 'tiny branch1 value erased')
    except AssertionError:
        rejected.append('tiny branch1 value erased')
    else:
        raise AssertionError('zeroed tiny branch1 value was accepted')
    if document['markers']:
        wrong = copy.deepcopy(document['markers'][0])
        wrong['kind'] = 'zeta-one' if wrong['kind'] == 'zeta-zero' else 'zeta-zero'
        domain = {name: mp.mpf(value) for name, value in document['domain'].items()}
        try:
            check_marker(wrong, domain, 'marker relabeled')
        except AssertionError:
            rejected.append('zeta zero and one-point labels exchanged')
        else:
            raise AssertionError('mislabeled marker was accepted')
    wrong = copy.deepcopy(document)
    wrong['interpretation']['selectedAnalytic'] = True
    try:
        validate_document(wrong)
    except AssertionError:
        rejected.append('selected map falsely declared analytic')
    else:
        raise AssertionError('false analyticity declaration was accepted')
    return rejected


def compare_exports(documents):
    shared_comparisons = 0
    pairs = []
    math_fields = ('zeta', 'zetaMinusOne', 'b', 'selected', 'product', 'derivative', 'refinedZeta', 'refinementDelta')
    for first_index, first in enumerate(documents):
        indexed = {(record['s']['real'], record['s']['imaginary']): record for record in first['samples']}
        for second_index in range(first_index + 1, len(documents)):
            second = documents[second_index]
            matches = 0
            for record in second['samples']:
                prior = indexed.get((record['s']['real'], record['s']['imaginary']))
                if prior is None:
                    continue
                for key in math_fields:
                    require(prior[key] == record[key], 'palette/resolution/marker settings changed mathematical sample ' + key)
                matches += 1
            shared_comparisons += matches
            pairs.append({'firstExport': first_index, 'secondExport': second_index, 'identicalSharedSamples': matches,
                          'paletteChanged': first['settings']['paletteDegrees'] != second['settings']['paletteDegrees'],
                          'resolutionChanged': first['settings']['resolution'] != second['settings']['resolution'],
                          'markerVisibilityChanged': first['settings']['showMarkers'] != second['settings']['showMarkers'],
                          'domainChanged': first['domain'] != second['domain']})
    return {'sharedSampleComparisons': shared_comparisons, 'pairs': pairs,
            'paletteControlPresent': any(pair['paletteChanged'] and pair['identicalSharedSamples'] for pair in pairs),
            'resolutionControlPresent': any(pair['resolutionChanged'] and pair['identicalSharedSamples'] for pair in pairs),
            'markerVisibilityControlPresent': any(pair['markerVisibilityChanged'] and pair['identicalSharedSamples'] for pair in pairs),
            'domainControlPresent': any(pair['domainChanged'] and pair['identicalSharedSamples'] for pair in pairs)}


def audited_native_search():
    path = Path(__file__).resolve().parents[2] / 'Graphics' / 'ZetaSwitchExperiment.cs'
    data = path.read_bytes()
    source = data.decode('utf-8-sig')
    def matched(pattern, label):
        match = re.search(pattern, source)
        require(match is not None, 'cannot audit native search setting: ' + label)
        return match.group(1)
    iterations = int(matched(r'iterations\s*<\s*(\d+)', 'iterations'))
    residual = matched(r'residual\.Magnitude\s*<\s*([0-9.eE+-]+)', 'residual')
    derivative_floor = matched(r'point\.Derivative\.Magnitude\s*<\s*([0-9.eE+-]+)', 'derivative floor')
    step_cap = matched(r'if\s*\(step\.Magnitude\s*>\s*([0-9.]+)\)', 'step cap')
    deduplication = matched(r'\(m\.S\s*-\s*root\)\.Magnitude\s*<\s*([0-9.eE+-]+)', 'deduplication')
    seed_text = matched(r'foreach\s*\(double sigma in new\[\]\s*\{([^}]*)\}', 'seed sigmas')
    seeds = [float(value.strip()) for value in seed_text.split(',')]
    require(iterations == 30 and mp.mpf(residual) == mp.mpf('2e-12')
            and mp.mpf(derivative_floor) == mp.mpf('1e-10')
            and mp.mpf(step_cap) == mp.mpf('1.5')
            and mp.mpf(deduplication) == mp.mpf('1e-7')
            and seeds == [.35, 1, 2, 2.8], 'native search settings changed; update the audited contract')
    require(re.search(r'Math\.Max\(2,\s*\(int\)Math\.Ceiling\(maxT\s*-\s*minT\)\)', source) is not None,
            'native height seed rule changed')
    return {'source': str(path), 'sourceSha256': hashlib.sha256(data).hexdigest(),
            'maximumNewtonIterations': iterations, 'successResidualStrictlyBelow': residual,
            'minimumDerivativeMagnitude': derivative_floor, 'maximumStepMagnitude': step_cap,
            'sameTargetDeduplicationDistanceStrictlyBelow': deduplication,
            'seedSigmas': seeds, 'heightSeedRule': 'inclusive endpoints with count=max(2,ceil(maxT-minT)); spacing<=1',
            'refinement': 'Repeat Newton at N96; export value residual at original coordinate and movement.',
            'stoppingScope': 'Invalid values, small derivative, outside expanded guard, or30iterations terminate the candidate search; candidates must finish inside the plot rectangle.',
            'interpretation': 'Empirical search and stopping criteria, not exhaustive or certified root isolation.'}


def main():
    require(mp.__version__ == '1.3.0', 'use pinned mpmath==1.3.0 for reproducibility')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exports', nargs='*', type=Path)
    parser.add_argument('--references', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.references:
        require(not args.exports, '--references is separate from export verification')
        result = references()
    else:
        require(bool(args.exports), 'supply at least one actual export JSON file')
        source_bytes = [path.read_bytes() for path in args.exports]
        documents = [json.loads(data.decode('utf-8-sig')) for data in source_bytes]
        reports = []
        for path, document, data in zip(args.exports, documents, source_bytes):
            report = validate_document(document)
            report['source'] = str(path.resolve())
            report['sourceSha256'] = hashlib.sha256(data).hexdigest()
            reports.append(report)
        result = {'status': 'passed', 'traceId': 'graph.riemann.switch.verify', 'mpmathVersion': mp.__version__,
                  'precisionDigits': mp.mp.dps, 'exports': reports,
                  'auditedNativeSearch': audited_native_search(),
                  'controls': compare_exports(documents),
                  'rejectedNegativeControls': negative_controls(documents[0]),
                  'tolerances': {'zetaScaled': str(VALUE_TOL), 'derivativeScaled': str(DERIVATIVE_TOL),
                                 'algebraScaled': str(ALGEBRA_TOL), 'markerResidualAbsolute': '1e-8',
                                 'markerMovementAbsolute': '1e-6', 'markerDerivativeMagnitudeMinimum': '1e-6',
                                 'reportedSmallMagnitudeAbsolute': '1e-20',
                                 'branchOneAndImaginaryPreservation': 'exact equality of exported binary values'},
                  'samplingAndStopping': {
                      'independentPrecisionDigits': 80,
                      'referenceEvaluation': 'Pinned mpmath1.3.0 zeta and analytic derivative at every exported sample.',
                      'perExportMandatorySamples': '144 rectangle points (16x9 inclusive), 18 eta-removable-neighborhood points, 3 reference-location probes.',
                      'etaNeighborhood': 'sigma=1+dx, t=2*k*pi/log(2)+dy; k=2,3; dx,dy in {-1e-7,0,1e-7}.',
                      'selectorProbes': '8 required, including exact ties, both seam sides, exact0/1, and positive/negative1e-18 preservation.',
                      'classificationNearSeam': 'Independent selector comparison withheld when |Re(reference)-.5|<=5e-11; computed-value selector still checked exactly.',
                      'stopping': 'Evaluate all listed samples/markers and cross-export matches; fail immediately on any mismatch. No adaptive claim between sampled points.',
                      'gridMetrics': 'Structural consistency checked; full pixel grids are not independently recomputed at80digits.'},
                  'limitations': ['High-precision numerical comparisons, not certified interval bounds.',
                                 'Numerical marker searches are not exhaustive.',
                                 'Cross-export controls apply only to supplied files and common input coordinates.',
                                 'Palette images and UI behavior require separate visual verification.',
                                 'The selected map is discontinuous at its seam and is not globally analytic.',
                                 'No result about the Riemann Hypothesis is established.']}
    encoded = json.dumps(result, indent=2) + '\n'
    if args.output is not None:
        args.output.write_text(encoded, encoding='utf-8')
    print(encoded, end='')


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, ArithmeticError, KeyError, TypeError, ValueError, OSError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        sys.exit(1)
