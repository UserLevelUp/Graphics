"""Replay actual zeta phase at integer heights; labels are an independent control.

defines: graph.primes.zeta_check96
Requires mpmath 1.3.0. This is not a primality algorithm or an interval certificate.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from math import isqrt
from pathlib import Path
import time

import mpmath as mp

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]


def prime_indicator(n):
    """Exact trial division with every integer divisor; no prior prime list."""
    return int(n >= 2 and all(n % d for d in range(2, isqrt(n) + 1)))


def classification(n):
    return 'neither' if n < 2 else 'prime' if prime_indicator(n) else 'composite'


def quadrant(value):
    # Current continuation map: half-open sectors of wrapped arg(zeta(s)-a).
    if not value: return None
    angle = mp.arg(value) % (2*mp.pi)
    return min(4, int(angle/(mp.pi/2)) + 1)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(n, dps, method=None, sigma='0.5'):
    with mp.workdps(dps):
        s = mp.mpc(mp.mpf(sigma), n)
        return mp.zeta(s) if method is None else mp.zeta(s, method=method)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    mp.mp.dps = 90
    started = time.perf_counter()
    rows = []
    max_precision_difference = mp.mpf(0)
    max_shifted_difference = mp.mpf(0)
    max_hardy_residual = mp.mpf(0)
    for n in range(101):
        low, value = evaluate(n, 50), evaluate(n, 80)
        difference = abs(value - low)
        assert difference < mp.mpf('1e-45')
        assert quadrant(low) == quadrant(value)
        shifted_low, shifted = evaluate(n,50,sigma='1.5'),evaluate(n,80,sigma='1.5')
        shifted_difference = abs(shifted-shifted_low)
        assert shifted_difference < mp.mpf('1e-45')
        max_shifted_difference = max(max_shifted_difference,shifted_difference)
        assert quadrant(shifted_low) == quadrant(shifted)
        max_precision_difference = max(max_precision_difference, difference)
        theta = mp.siegeltheta(n)
        hardy = mp.exp(1j * theta) * value
        residual = abs(hardy.imag)
        max_hardy_residual = max(max_hardy_residual, residual)
        assert residual < mp.mpf('1e-75')
        rows.append(dict(n=n, classification=classification(n),
            real=mp.nstr(value.real, 35), imaginary=mp.nstr(value.imag, 35),
            magnitude=mp.nstr(abs(value), 35), phaseRadians=mp.nstr(mp.arg(value), 35),
            phaseDegrees=mp.nstr(mp.arg(value)*180/mp.pi, 35), quadrant=quadrant(value),
            hardyZ=mp.nstr(hardy.real, 35),
            shifted=dict(expression='zeta(3/2+i*n)',real=mp.nstr(shifted.real,35),
                imaginary=mp.nstr(shifted.imag,35),phaseRadians=mp.nstr(mp.arg(shifted),35),
                phaseDegrees=mp.nstr(mp.arg(shifted)*180/mp.pi,35),quadrant=quadrant(shifted))))
    numerical_seconds = time.perf_counter() - started
    # A second evaluation method, within the same library, for declared examples.
    method_checks = []
    for n in (49, 91, 95, 96, 97, 98, 99, 100):
        # In mpmath 1.3.0 an explicit 'borwein' argument bypasses the fast path.
        # Default calls use libmp.mpc_zeta (Borwein) at these heights/precisions;
        # an explicit method bypasses that path and reaches _hurwitz here.
        for sigma in ('0.5','1.5'):
            a, b = evaluate(n,80,sigma=sigma), evaluate(n,80,'euler-maclaurin',sigma=sigma)
            delta = abs(a-b)
            assert delta < mp.mpf('1e-70')
            method_checks.append(dict(n=n,sigma=sigma,difference=mp.nstr(delta,15),
                quadrantAgreement=quadrant(a)==quadrant(b)))
    # Compare all labels with the prior exact certificate AND a separate full-divisor check.
    old = REPO / 'research/prime-range-100/certificate.json'
    accepted = json.loads(old.read_text(encoding='utf-8'))
    assert [r['classification'] for r in rows] == [r['classification'] for r in accepted['records']]
    assert all(prime_indicator(n) == int(n >= 2 and all(n % d for d in range(2, n))) for n in range(101))
    by_quadrant = []
    for q in range(1, 5):
        primes = [r['n'] for r in rows if r['quadrant']==q and r['classification']=='prime']
        composites = [r['n'] for r in rows if r['quadrant']==q and r['classification']=='composite']
        by_quadrant.append(dict(quadrant=q, primes=primes, composites=composites,
            primeCount=len(primes), compositeCount=len(composites), mixed=bool(primes and composites)))
    assert all(r['mixed'] for r in by_quadrant)
    # Best possible in-sample binary map of ONE quadrant to a prime/composite label.
    # This is a diagnostic lower bound on unavoidable errors, not a trained predictor.
    forced_errors = sum(min(r['primeCount'], r['compositeCount']) for r in by_quadrant)
    pairs = []
    for first in range(1,5):
        for second in range(1,5):
            members = [r for r in rows if r['n']>=2 and r['quadrant']==first and r['shifted']['quadrant']==second]
            if not members: continue
            primes = [r['n'] for r in members if r['classification']=='prime']
            composites = [r['n'] for r in members if r['classification']=='composite']
            pairs.append(dict(original=first,shifted=second,primes=primes,composites=composites,
                primeCount=len(primes),compositeCount=len(composites)))
    matches97 = next(r for r in pairs if (r['original'],r['shifted'])==(rows[97]['quadrant'],rows[97]['shifted']['quadrant']))
    primary_matches=by_quadrant[rows[97]['quadrant']-1]
    real_values = []
    for n in (96,97):
        value = mp.zeta(n)
        assert value > 1 and mp.arg(value) == 0
        real_values.append(dict(n=n, zetaMinusOne=mp.nstr(value-1,35), phaseRadians='0'))
    count = lambda x: sum(prime_indicator(m) for m in range(2,x+1))
    p25 = next(n for n in range(2,102) if count(n)>=25)
    next97 = next(n for n in range(98,102) if prime_indicator(n))
    assert (count(96),count(97),p25,next97)==(24,25,97,101)
    report = dict(schema='graph-zeta-prime-check-v1',traceId='graph.primes.zeta_check96',
        status='passed',createdUtc=datetime.now(timezone.utc).isoformat(),
        mapping=dict(sigma='0.5',secondarySigma='1.5',secondaryFunction='zeta(s+1)',height='integer n',target='0',basisRadians='0',
            justification='Explicit test interpretation; integer height is not a theorem mapping prime labels to zeros.'),
        method=dict(library='mpmath',version=mp.__version__,precisions=[50,80],
            comparisonMethods=['default libmp.mpc_zeta (Borwein)','explicit Euler-Maclaurin path'],
            methodRouting='Source-inspected mpmath 1.3.0: the explicit borwein setting does not select the fast path; use default versus the explicit Euler-Maclaurin path at these heights.',
            numericalSeconds=numerical_seconds,intervalCertified=False),
        sourceInputs=[dict(path=str(p.relative_to(REPO)).replace('\\','/'),sha256=digest(p)) for p in
            [old,REPO/'Graphics/PrimeUnwrap.cs',REPO/'Graphics/PrimePhaseExperiment.cs',
             REPO/'Graphics/ZetaExperiment.cs',REPO/'Graphics/ZetaContinuationExperiment.cs',
             REPO/'research/zeta-continuation/track_roots.py']],
        libraryImplementationInputs=[dict(path=name,sha256=digest(Path(mp.__file__).parent/name)) for name in
            ('functions/zeta.py','libmp/gammazeta.py','ctx_mp.py')],
        rows=rows,quadrants=by_quadrant,methodChecks=method_checks,quadrantPairs=pairs,
        inputShiftComparison=dict(candidateRule='Same unrotated quadrant pair as n=97',
            pair=[matches97['original'],matches97['shifted']],
            truePositives=len(matches97['primes']),falsePositives=len(matches97['composites']),
            falseNegatives=25-len(matches97['primes']),
            falsePositivesRemoved=len(primary_matches['composites'])-len(matches97['composites']),
            unavoidableErrorsForAnyPairOnlyClassifier=sum(min(r['primeCount'],r['compositeCount']) for r in pairs),
            scope='Finite diagnostic of the requested zeta(s), zeta(s+1) input shift, not an optimized or validated prime predictor.'),
        checks=dict(integerLabels=101,allLabelsMatchAcceptedCertificate=True,
            exhaustiveProperDivisorCrosscheck=True,quadrantsStableAcrossPrecisions=True,
            maximumPrecisionDifference=mp.nstr(max_precision_difference,20),
            maximumSecondaryPrecisionDifference=mp.nstr(max_shifted_difference,20),
            maximumHardyImaginaryResidual=mp.nstr(max_hardy_residual,20)),
        exactExamples=[dict(n=n,remainders=[dict(divisor=d,remainder=n%d) for d in (2,3,5,7)],
            allTrialDivisors=list(range(2,isqrt(n)+1)),indicator=prime_indicator(n)) for n in (96,97)],
        directRealArguments=real_values,
        counting=dict(pi96=count(96),pi97=count(97),p25=p25,nextAfter97=next97),
        finding=dict(allFourQuadrantsContainBothClasses=True,
            unavoidableErrorsForAnyQuadrantOnlyClassifier=forced_errors,classifiedIntegers=99,
            scope='Fixed mapping s=1/2+i*n, n=2..100, target and basis zero. Refutes a quadrant-only perfect test on this finite range.'),
        limits=['No claim that every richer phase-based method is impossible.',
                'Labels come from exact divisibility and are used only as ground truth, not in zeta evaluation.',
                'High-precision agreement is numerical evidence, not an interval-certified zero or RH proof.',
                'No new prime formula, speedup, or zeta-based prime classifier is established.'])
    (args.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',examples=[r for r in rows if r['n'] in (95,96,97,98,99)],
        quadrantCounts=[{k:r[k] for k in ('quadrant','primeCount','compositeCount')} for r in by_quadrant],
        unavoidableErrors=forced_errors,inputShiftComparison=report['inputShiftComparison'],
        maximumPrecisionDifference=report['checks']['maximumPrecisionDifference']),indent=2))


if __name__ == '__main__': main()
