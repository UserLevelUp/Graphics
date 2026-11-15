"""Independent finite checks of the exact candidate-input primality functions."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from statistics import median
import time

from prime_function import f, trial, wilson

BASE = Path(__file__).resolve().parent


def sieve(limit):
    flags=bytearray(b'\1')*(limit+1)
    flags[0:2]=b'\0\0'
    for p in range(2, math.isqrt(limit)+1):
        if flags[p]:
            flags[p*p:limit+1:p]=b'\0'*(((limit-p*p)//p)+1)
    return flags


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    flags=sieve(100000)
    assert sum(flags)==9592
    for n in range(100001):
        result=trial(n)
        assert result['indicator']==flags[n],n
        if result['divisor'] is not None:
            assert 1<result['divisor']<n and n%result['divisor']==0
    # Incremental factorial is an independent full-big-integer calculation.
    factorial=1
    for n in range(2001):
        if n>=3:factorial*=n-1
        result=wilson(n)
        assert result['indicator']==flags[n],n
        if n>=2:
            assert result['factorialMod']==factorial%n,n
            assert result['residue']==(factorial+1)%n,n
            if not flags[n] and n>4:assert result['residue']==1,n
    cases=[0,1,2,3,4,9,25,49,96,97,121,341,561,1105,1729,2047,2465,2821,6601,9973,99991,100000]
    examples=[]
    for n in cases:
        a,b=trial(n),wilson(n)
        assert a['indicator']==b['indicator']==flags[n],n
        examples.append(dict(n=n,trial=a,wilson=b))
    assert wilson(96)['residue']==1 and wilson(96)['factorialMod']==0
    assert wilson(97)['residue']==0 and wilson(97)['factorialMod']==96
    assert wilson(4)['residue']==3
    rejected=[]
    for bad in (-1,True,3.0,'97',None):
        for name,method in (('trial',trial),('wilson',wilson)):
            try:method(bad)
            except ValueError:rejected.append(dict(method=name,value=repr(bad)))
            else:raise AssertionError((name,bad))
    # Explicitly bounded illustrative timing, on the same inputs, five repetitions.
    timing_inputs=[96,97,9973,10000,99991,100000]
    timings={}
    for name,method in (('trial',trial),('wilson',wilson)):
        samples=[]
        for _ in range(5):
            started=time.perf_counter_ns()
            outputs=[method(n)['indicator'] for n in timing_inputs]
            elapsed=time.perf_counter_ns()-started
            assert outputs==[flags[n] for n in timing_inputs]
            samples.append(elapsed/1e6)
        timings[name]=dict(medianMilliseconds=median(samples),runsMilliseconds=samples)
    report=dict(traceId='graph.primes.function.validation',status='passed',
        createdUtc=datetime.now(timezone.utc).isoformat(),
        inputs=[dict(path=p.name,sha256=sha(p)) for p in (BASE/'prime_function.py',Path(__file__))],
        coverage=dict(trialVsIndependentSieve=[0,100000],primesThrough100000=sum(flags),
            wilsonVsSieveAndBigIntegerFactorial=[0,2000],specialControls=cases,invalidInputsRejected=len(rejected)),
        examples=examples,invalidInputs=rejected,
        timing=dict(inputs=timing_inputs,repetitions=5,methods=timings,
            scope='Single-host illustrative measurements of these Python implementations. Not a complexity proof or an optimized-algorithm benchmark.'),
        limits=['The all-integer correctness theorem is stated separately; finite tests check these implementations.',
                'No input list of primes enters either candidate function. The sieve is only the independent validation oracle.',
                'Floating phase is an illustration; exact residue determines Wilson classification.',
                'Known theorem, no new formula or speedup claimed; no RH verification.'])
    dest=args.output/'validation.json';dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',coverage=report['coverage'],timing=report['timing']),indent=2))


if __name__=='__main__':main()
