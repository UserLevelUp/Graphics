from decimal import Decimal as D, getcontext
import json
from pathlib import Path

getcontext().prec = 70
base = Path(__file__).resolve().parent
actual_path = base / 'prime-color-loom.values.json'
actual = json.loads(actual_path.read_text(encoding='utf-8-sig'))
reference = json.loads((base / 'numeric-references.json').read_text(encoding='utf-8'))
tolerance = D('1e-12')
fields = ('real', 'imaginary', 'logReal', 'logImaginary', 'referenceReal', 'referenceImaginary')
maxima = {field: D(0) for field in fields}
cases = []
used = set()


def atan_small(value):
    term = value
    result = value
    square = value * value
    for n in range(1, 160):
        term *= -square
        change = term / D(2*n+1)
        result += change
        if abs(change) < D('1e-75'):
            return result
    raise AssertionError('atan failed to converge')


for row in actual['cases']:
    matches = [
        (index, item) for index, item in enumerate(reference['records'])
        if item['prime_cutoff'] == row['cutoff']
        and abs(D(item['t']) - D.from_float(float(row['t']))) < tolerance
    ]
    assert len(matches) == 1
    index, expected = matches[0]
    assert index not in used
    used.add(index)
    real = D(expected['partial_product']['real'])
    imaginary = D(expected['partial_product']['imaginary'])
    assert real > 0
    targets = {
        'real': real,
        'imaginary': imaginary,
        'logReal': (real*real + imaginary*imaginary).ln() / 2,
        'logImaginary': atan_small(imaginary/real),
        'referenceReal': D(expected['zeta_reference']['real']),
        'referenceImaginary': D(expected['zeta_reference']['imaginary'])
    }
    # For sigma=2, the accumulated Euler-log phase is in (-pi,pi), so the
    # computed atan is on the same analytic branch as the accumulated log.
    errors = {}
    for field in fields:
        difference = abs(D.from_float(float(row[field])) - targets[field])
        maxima[field] = max(maxima[field], difference)
        errors[field] = format(difference, '.16g')
    cases.append({
        't': expected['t'], 'cutoff': row['cutoff'],
        'input_binary_t_difference': str(D.from_float(float(row['t'])) - D(expected['t'])),
        'absolute_field_errors': errors,
        'passed': all(D(error) < tolerance for error in errors.values())
    })
assert len(cases) == 12 and len(used) == 12
report = {
    'status': 'passed' if all(case['passed'] for case in cases) else 'failed',
    'cases_checked': len(cases),
    'comparison_tolerance': str(tolerance),
    'source': str(actual_path),
    'reference': str(base / 'numeric-references.json'),
    'maximum_absolute_errors': {key: format(value, '.16g') for key, value in maxima.items()},
    'notes': [
        'C# binary t values differ slightly from the exact decimal reference ordinates.',
        'Reference products use 70-digit Decimal arithmetic; zeta references use independent Euler-Maclaurin evaluation.',
        'Log values here are computed on the branch shared by the accumulated Euler log at sigma=2.',
        'These are numerical checks, without interval or directed-rounding certification.'
    ],
    'cases': cases
}
path = base / 'csharp-comparison.json'
path.write_text(json.dumps(report, indent=2)+'\n',encoding='utf-8')
print(path)
print(json.dumps({key: report[key] for key in ('status','cases_checked','maximum_absolute_errors')},indent=2))
