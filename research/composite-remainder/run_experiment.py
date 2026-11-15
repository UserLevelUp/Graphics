"""Reproducible finite arithmetic experiment and scoped cost comparison.
defines: graph.primes.composite_remainder.experiment
consumer: graph.primes.composite_remainder.model
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from math import isqrt
from pathlib import Path
import platform
import statistics
import sys
import time

from composite_remainder import (batch_classification, classify, factor_pairs,
    finite_ordered, finite_subtraction, finite_unordered, geometric_terms, odd_coefficient)

BASE=Path(__file__).resolve().parent


def oracle_sieve(limit):
    result=bytearray(b'\1')*(limit+1)
    for n in range(min(2,limit+1)): result[n]=0
    for p in range(2,isqrt(limit)+1):
        if result[p]:
            result[p*p:limit+1:p]=b'\0'*(((limit-p*p)//p)+1)
    return result


def odd_trial(n):
    if n<2: return False
    if n==2: return True
    if n%2==0: return False
    return all(n%d for d in range(3,isqrt(n)+1,2))


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def benchmark(function,repeats=7):
    function()  # Warm-up; the medians below exclude it.
    times=[]
    for _ in range(repeats):
        start=time.perf_counter();function();times.append(time.perf_counter()-start)
    return dict(repeats=repeats,seconds=times,medianSeconds=statistics.median(times))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int,default=100000)
    parser.add_argument('--output',type=Path,default=BASE/'evidence')
    args=parser.parse_args()
    if args.limit<100: parser.error('Use a limit of at least 100.')
    start=time.perf_counter()
    oracle=oracle_sieve(args.limit)
    unordered=finite_unordered(args.limit)
    ordered=finite_ordered(args.limit)
    remainder=finite_subtraction(args.limit)
    assert ordered==remainder
    for n in range(args.limit+1):
        assert unordered[n]==odd_coefficient(n)
        expected='neither' if n<2 else 'prime' if oracle[n] else 'composite'
        assert classify(n)==expected
        if n>=3 and n%2:
            assert ordered[n]==2*unordered[n]-int(isqrt(n)**2==n)
            assert (unordered[n]>0)==(not oracle[n])
        else:
            assert unordered[n]==ordered[n]==0
    cutoffs=[b for b in (0,1,2,3,8,9,10,24,25,26,48,49,50,96,97,98,99,100,120,121) if b<=args.limit]
    for bound in cutoffs:
        assert finite_unordered(bound)==unordered[:bound+1]
        assert finite_ordered(bound)==ordered[:bound+1]
        assert finite_subtraction(bound)==remainder[:bound+1]
    for function in (classify,odd_coefficient,factor_pairs,finite_unordered,finite_ordered,finite_subtraction):
        for invalid in (-1,1.5,'97',True,None):
            try: function(invalid)
            except (ValueError,TypeError): pass
            else: raise AssertionError((function.__name__,invalid))
    extra=[]
    for n in (121,169,221,341,561,1105,1729,104729,999983,1000001,1000003,2147483647,3215031751):
        pairs=factor_pairs(n)
        assert len(pairs)==odd_coefficient(n)
        assert (classify(n)=='prime')==odd_trial(n)
        assert all(a*b==n and 3<=a<=b and a%2 and b%2 for a,b in pairs)
        extra.append(dict(n=n,coefficient=len(pairs),classification=classify(n),factorPairs=pairs,
            oddDivisorsExamined=max(0,(isqrt(n)-1)//2)))
    # Directly reverse the finite prime polynomial: this is a separate control.
    reversal=[]
    for bound in (10,100):
        flags=oracle_sieve(bound)
        difference=[int(flags[n])-int(flags[bound-n]) for n in range(bound+1)]
        nonzero=[dict(exponent=n,coefficient=c) for n,c in enumerate(difference) if c]
        composites=[n for n in range(2,bound+1) if not flags[n]]
        assert {v['exponent'] for v in nonzero}!=set(composites)
        assert all(difference[bound-n]==-difference[n] for n in range(bound+1))
        reversal.append(dict(cutoff=bound,nonzeroDifference=nonzero,antisymmetric=True,
            exampleCoefficients={str(n):difference[n] for n in (9,15,97,99) if n<=bound},
            equalsCompositeSupport=False,note='F_N(z)-z^N F_N(1/z); prime oracle used only for this diagnostic control.'))
    assert reversal[0]['nonzeroDifference']==[dict(exponent=2,coefficient=1),dict(exponent=8,coefficient=-1)]
    rows=[dict(n=n,classification=classify(n),orderedCoefficient=ordered[n],
        unorderedCoefficient=unordered[n],factorPairs=factor_pairs(n)) for n in range(101)]
    table=dict(traceId='graph.primes.composite_remainder.table',range=[0,100],rows=rows,
        finiteTerms=geometric_terms(100),oddComposites=[n for n in range(3,101,2) if unordered[n]],
        note='Counts are nontrivial odd factor pairs. Even composites need the separate even-number guard.')
    save(args.output/'table-0-100.json',table)
    validation=dict(traceId='graph.primes.composite_remainder.validation',status='passed',limit=args.limit,
        createdUtc=datetime.now(timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),
        checkedIntegers=args.limit+1,primeCount=sum(oracle),
        oddPrimeCount=sum(oracle[3::2]),oddCompositeCount=sum(1 for n in range(3,args.limit+1,2) if not oracle[n]),
        constructionAgreement='Ordered enumeration equals all-pairs-minus-unit-families; unordered expansion equals exact floor-divisor formula.',
        prefixConsistencyCutoffs=cutoffs,
        extraControls=extra,reversalControls=reversal,
        coefficientSha256=hashlib.sha256(json.dumps(unordered,separators=(',',':')).encode()).hexdigest(),
        sources=[dict(path=p.name,sha256=sha(p)) for p in (BASE/'composite_remainder.py',Path(__file__))],
        elapsedSeconds=time.perf_counter()-start,
        limits=['Finite code checks accompany an elementary all-integer proof, not an RH proof.',
                'No previous-prime list enters the candidate coefficient function.',
                'The direct coefficient is a trial-divisor count, not constant-time primality.'])
    save(args.output/'validation.json',validation)
    timing=dict(traceId='graph.primes.composite_remainder.cost',range=[0,args.limit],
        coefficientBatch=benchmark(lambda:finite_unordered(args.limit)),
        completeClassificationBatch=benchmark(lambda:batch_classification(args.limit)),
        independentSieveBatch=benchmark(lambda:oracle_sieve(args.limit)),
        coefficientUpdates=sum((args.limit-d*d)//(2*d)+1 for d in range(3,isqrt(args.limit)+1,2)),
        perOddCandidateDivisors='max(0,(isqrt(n)-1)//2); exact coefficient needs all these candidates',
        operationsPerDivisor='Two integer floor divisions and subtraction in the equation implementation; the equivalent remainder test uses one modulo.',
        interpretation='One local CPython benchmark, not a universal complexity or speedup claim. Coefficient output contains multiplicities; classifier and sieve outputs both provide primality flags.',
        runtime=dict(python=sys.version,platform=platform.platform()))
    save(args.output/'cost.json',timing)
    print(json.dumps(dict(status='passed',checked=validation['checkedIntegers'],primeCount=validation['primeCount'],
        oddCompositesThrough100=table['oddComposites'],medianSeconds={k:v['medianSeconds'] for k,v in timing.items() if isinstance(v,dict) and 'medianSeconds' in v}),indent=2))


if __name__=='__main__': main()
