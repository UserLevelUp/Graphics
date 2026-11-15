"""Independent finite arithmetic and uncertainty checks for the quadrant test.

defines: graph.primes.quadrant_phase.verify
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from phase_test import phase_test, quadrant, observed_quadrant

BASE = Path(__file__).resolve().parent


def sieve(limit):
    flags = bytearray(b'\1') * (limit + 1)
    flags[0:2] = b'\0\0'
    for p in range(2, math.isqrt(limit) + 1):
        if flags[p]:
            flags[p*p:limit+1:p] = b'\0' * ((limit - p*p) // p + 1)
    return flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    flags = sieve(100000)
    counts = {'1': 0, '2': 0, '3': 0, '4': 0, 'undefined': 0}
    factorial = 1
    for n in range(10001):
        row = phase_test(n)
        assert row['indicator'] == flags[n], n
        assert row['defined'] == (n >= 2), n
        if n < 2:
            assert row['quadrant'] is None and row['classification'] == 'neither'
        else:
            q = row['quadrant']
            # Independent direct Cartesian signs, plus independent trig visualization.
            assert q == (1 if row['x'] > 0 and row['y'] > 0 else 2 if row['y'] > 0 else 4), n
            assert row['residue'] == (0 if flags[n] else 3 if n == 4 else 1), n
            assert row['angleDegrees'] in (45, 135, 315)
            a = math.radians(row['angleDegrees'])
            assert (math.cos(a) > 0) == (row['x'] > 0)
            assert (math.sin(a) > 0) == (row['y'] > 0)
            if n <= 2000:
                if n >= 3:
                    factorial *= n - 1
                assert row['factorialMod'] == factorial % n, n
                assert row['residue'] == (factorial + 1) % n, n
        if n <= 100:
            counts[str(row['quadrant']) if row['defined'] else 'undefined'] += 1
    assert counts == {'1':25,'2':73,'3':0,'4':1,'undefined':2}, counts
    controls = [0,1,2,3,4,9,25,49,96,97,121,341,561,1105,1729,2047,6601,9973,99991,100000]
    examples = [phase_test(n) for n in controls]
    assert all(row['indicator'] == flags[row['n']] for row in examples)
    assert phase_test(96)['quadrant'] == 2
    assert phase_test(97)['quadrant'] == 1
    assert phase_test(4)['quadrant'] == 4
    # The generic quadrant routine also handles QIII, although final F(n) never uses it.
    for x, y, q in ((1,1,1),(-1,1,2),(-1,-1,3),(1,-1,4)):
        assert quadrant(x, y) == q
    observations = []
    for angle in (45,135,225,315,-45,405):
        for error in (0,1,44,44.999,45,46,90,360):
            result = observed_quadrant(angle, error)
            assert (result['quadrant'] is not None) == (error < 45)
            if error < 45:
                assert result['quadrant'] == int(angle % 360 // 90) + 1
            observations.append(dict(angle=angle, error=error, **result))
    for angle in (0,90,180,270,360,-90):
        assert observed_quadrant(angle, 0)['status'] == 'uncertain'
    large_angles = [1152921504606847021, 10**400 + 45, -(10**400 + 45)]
    for angle in large_angles:
        result = observed_quadrant(angle, 0)
        exact_mod = angle % 360
        expected = exact_mod // 90 + 1 if exact_mod % 90 else None
        assert result['quadrant'] == expected, (angle, result, expected)
    assert observed_quadrant(-1e-14, 1.2e-14)['quadrant'] is None
    assert observed_quadrant(-1e-14, 0.5e-14)['quadrant'] == 4
    assert observed_quadrant(-5e-324, 0)['quadrant'] == 4
    assert observed_quadrant(45, 10**400)['quadrant'] is None
    invalid = 0
    for bad in (-1,True,3.0,'97',None):
        try:
            phase_test(bad)
        except ValueError:
            invalid += 1
        else:
            raise AssertionError(('domain', bad))
    for angle, error in ((math.nan,0),(math.inf,0),(45,-1),(45,math.inf),('45',0),(True,0),(45,True)):
        try:
            observed_quadrant(angle,error)
        except ValueError:
            invalid += 1
        else:
            raise AssertionError(('observation',angle,error))
    args.output.mkdir(parents=True, exist_ok=True)
    report = dict(traceId='graph.primes.quadrant_phase.validation', status='passed',
        createdUtc=datetime.now(timezone.utc).isoformat(),
        inputs=[dict(path=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in (BASE/'phase_test.py', Path(__file__))],
        coverage=dict(quadrantVsIndependentSieve=[0,10000],
                      remainderVsFullIntegerFactorial=[2,2000], controls=controls,
                      invalidInputsRejected=invalid, angleIntervalChecks=len(observations)+6,
                      largeIntegerAngleRegressions=len(large_angles),
                      nearAxisAndLargeErrorRegressions=4),
        counts0to100=counts, examples=examples, observations=observations,
        limits=['Global theorem and finite implementation tests are separate.',
                'The supplied observation error is assumed, not measured or certified.',
                'No prior-prime list enters the candidate function; the sieve is an oracle only.',
                'Wilson-derived exact quadrant encoding; no new zeta or RH result or speed claim.'])
    (args.output/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','coverage','counts0to100')},indent=2))


if __name__ == '__main__':
    main()
