"""Independent factorization-based review of the composite remainder experiment.

defines: graph.primes.composite_remainder.independent_review
consumer: graph.primes.composite_remainder.model
Uses a least-prime-factor factorization oracle, not the producer's prime sieve.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import isqrt
from pathlib import Path
import subprocess
import statistics
import sys
import time

import composite_remainder as model

BASE = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def least_prime_factors(limit):
    values = list(range(limit + 1))
    for candidate in range(2, isqrt(limit) + 1):
        if values[candidate] == candidate:
            for multiple in range(candidate*candidate, limit + 1, candidate):
                if values[multiple] == multiple:
                    values[multiple] = candidate
    return values


def factor_small(n, least):
    answer = []
    while n > 1:
        prime = least[n]
        exponent = 0
        while n % prime == 0:
            n //= prime
            exponent += 1
        answer.append((prime, exponent))
    return answer


def factor_large(n, primes):
    answer = []
    for prime in primes:
        if prime*prime > n:
            break
        exponent = 0
        while n % prime == 0:
            n //= prime
            exponent += 1
        if exponent:
            answer.append((prime, exponent))
    if n > 1:
        answer.append((n, 1))
    return answer


def tau_from_factors(factors):
    count = 1
    for _, exponent in factors:
        count *= exponent + 1
    return count


def pairs_from_factors(n, factors):
    if n < 3 or n % 2 == 0:
        return []
    divisors = [1]
    for prime, exponent in factors:
        divisors = [d * prime**power for d in divisors for power in range(exponent+1)]
    return sorted((d, n//d) for d in divisors if 3 <= d <= n//d)


def oracle_row(n, factors):
    prime = n >= 2 and len(factors) == 1 and factors[0][1] == 1
    classification = 'neither' if n < 2 else 'prime' if prime else 'composite'
    tau = tau_from_factors(factors) if n else 0
    ordered = tau-2 if n >= 3 and n % 2 else 0
    unordered = (tau-1)//2 if n >= 3 and n % 2 else 0
    return dict(n=n,classification=classification,orderedCoefficient=ordered,
                unorderedCoefficient=unordered,factorPairs=[list(p) for p in pairs_from_factors(n,factors)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=BASE/'evidence/independent-review.json')
    parser.add_argument('--small-run-output',type=Path,required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    producer_files = [BASE/'composite_remainder.py',BASE/'run_experiment.py',BASE/'proof.md',
                      BASE/'evidence/validation.json',BASE/'evidence/table-0-100.json',BASE/'evidence/cost.json']
    before = {str(path):sha(path) for path in producer_files}
    validation = load(BASE/'evidence/validation.json')
    table = load(BASE/'evidence/table-0-100.json')
    costs = load(BASE/'evidence/cost.json')
    require(validation['status']=='passed','Producer reported failure')
    limit = validation['limit']
    require(limit>=100,'Accepted range must include the complete 0..100 table')
    for source in validation['sources']:
        require(sha(BASE/source['path'])==source['sha256'],'Producer source fingerprint: '+source['path'])
    extra_values = [row['n'] for row in validation['extraControls']]
    factor_limit = max(limit,isqrt(max(extra_values)))
    least = least_prime_factors(factor_limit)
    primes = [n for n in range(2,factor_limit+1) if least[n]==n]
    oracle = [oracle_row(n,factor_small(n,least)) for n in range(limit+1)]
    expected_u = [row['unorderedCoefficient'] for row in oracle]
    expected_q = [row['orderedCoefficient'] for row in oracle]
    expected_flags = [row['classification']=='prime' for row in oracle]
    require(model.finite_unordered(limit)==expected_u,'Unordered coefficients versus multiplicative tau')
    require(model.finite_ordered(limit)==expected_q,'Ordered coefficients versus multiplicative tau')
    require(model.finite_subtraction(limit)==expected_q,'Subtraction versus multiplicative tau')
    require(model.batch_classification(limit)==expected_flags,'Batch classifications versus factorizations')
    for row in oracle:
        n=row['n']
        require(model.odd_coefficient(n)==row['unorderedCoefficient'],'Scalar coefficient '+str(n))
        require(model.classify(n)==row['classification'],'Scalar classification '+str(n))
        require([list(p) for p in model.factor_pairs(n)]==row['factorPairs'],'Factor pairs '+str(n))
    require(validation['checkedIntegers']==limit+1,'Saved checked count')
    require(validation['primeCount']==sum(expected_flags),'Saved prime count')
    require(validation['oddPrimeCount']==sum(expected_flags[3::2]),'Saved odd prime count')
    require(validation['oddCompositeCount']==sum(v>0 for v in expected_u),'Saved odd composite count')
    require(validation['coefficientSha256']==hashlib.sha256(json.dumps(expected_u,separators=(',',':')).encode()).hexdigest(),
            'Full saved coefficient fingerprint')
    require(table['rows']==oracle[:101],'All 101 saved table rows')
    require(table['oddComposites']==[n for n in range(3,101,2) if expected_u[n]>0],'Saved odd composite support')
    expected_terms = [dict(factor=d,exponents=[n for n in range(101) if n%2 and n%d==0 and n//d>=d])
                      for d in (3,5,7,9)]
    require(table['finiteTerms']==expected_terms==model.geometric_terms(100),'Finite terms through 100')
    prefix_cutoffs = sorted(set(range(min(122,limit+1)))|set(validation['prefixConsistencyCutoffs'])|{limit})
    for cutoff in prefix_cutoffs:
        require(model.finite_unordered(cutoff)==expected_u[:cutoff+1],'Unordered prefix '+str(cutoff))
        require(model.finite_ordered(cutoff)==expected_q[:cutoff+1],'Ordered prefix '+str(cutoff))
        require(model.finite_subtraction(cutoff)==expected_q[:cutoff+1],'Subtraction prefix '+str(cutoff))
        require(model.batch_classification(cutoff)==expected_flags[:cutoff+1],'Classifier prefix '+str(cutoff))
    class IntSubclass(int):
        pass
    invalids = [-1,1.5,97.0,'97',True,False,None,complex(97,0),[],{},IntSubclass(97)]
    public = [model.natural,model.odd_coefficient,model.factor_pairs,model.classify,model.finite_unordered,
              model.finite_ordered,model.finite_subtraction,model.batch_classification,model.geometric_terms]
    rejected = 0
    for function in public:
        for value in invalids:
            try:
                function(value)
            except (ValueError,TypeError):
                rejected += 1
            else:
                raise AssertionError('Domain guard '+function.__name__+' '+repr(value))
    extra_results=[]
    for saved in validation['extraControls']:
        n=saved['n']; factors=factor_large(n,primes); row=oracle_row(n,factors)
        require(model.classify(n)==row['classification'],'Large classification '+str(n))
        require(model.odd_coefficient(n)==row['unorderedCoefficient'],'Large coefficient '+str(n))
        require([list(p) for p in model.factor_pairs(n)]==row['factorPairs'],'Large pairs '+str(n))
        require(saved['coefficient']==row['unorderedCoefficient'] and saved['classification']==row['classification']
                and saved['factorPairs']==row['factorPairs'],'Saved large control '+str(n))
        extra_results.append(dict(n=n,factorization=factors,coefficient=row['unorderedCoefficient'],classification=row['classification']))
    reversal_results=[]
    for saved in validation['reversalControls']:
        cutoff=saved['cutoff']
        difference=[int(expected_flags[n])-int(expected_flags[cutoff-n]) for n in range(cutoff+1)]
        require(saved['nonzeroDifference']==[dict(exponent=n,coefficient=v) for n,v in enumerate(difference) if v],
                'Saved reversal coefficient list')
        require(all(difference[cutoff-n]==-difference[n] for n in range(cutoff+1)),'Reversal antisymmetry')
        require(saved['exampleCoefficients']=={str(n):difference[n] for n in (9,15,97,99) if n<=cutoff},'Reversal examples')
        require(set(n for n,v in enumerate(difference) if v)!=set(n for n in range(2,cutoff+1) if not expected_flags[n]),
                'Reversal must not equal composite support')
        if cutoff==100:
            require(difference[97]==difference[99]==0,'97 and 99 reversal collision')
        reversal_results.append(dict(cutoff=cutoff,antisymmetric=True,examples=saved['exampleCoefficients']))
    # Supplementary H coefficients: exact Euler-log prime-power coefficients,
    # independently compared with the multiplicative factorization description.
    # This audits the stated identity; H is not the producer's classifier.
    log_coefficients = [Fraction(0) for _ in range(limit+1)]
    for prime in primes:
        if prime==2 or prime>limit:
            continue
        power=prime; exponent=1
        while power<=limit:
            log_coefficients[power]=Fraction(1,exponent)
            power*=prime; exponent+=1
    h_examples=[]
    for n in range(limit+1):
        factors=factor_small(n,least)
        observed=(Fraction(1) if n>=3 and n%2 else Fraction(0))-log_coefficients[n]
        expected=(Fraction(1)-Fraction(1,factors[0][1]) if len(factors)==1 else Fraction(1)) if n>=3 and n%2 else Fraction(0)
        require(observed==expected,'Supplementary H coefficient '+str(n))
        require((observed>0)==(expected_u[n]>0),'Supplementary H support '+str(n))
        if n in (1,9,15,25,27,45,81,97,99):
            h_examples.append(dict(n=n,coefficient=str(observed)))
    require(costs['range']==[0,limit],'Timing range')
    require(costs['coefficientUpdates']==sum(expected_u),'Coefficient update count')
    for name in ('coefficientBatch','completeClassificationBatch','independentSieveBatch'):
        row=costs[name]
        require(row['repeats']==len(row['seconds'])==7 and all(t>=0 for t in row['seconds']),'Timing sample metadata')
        require(row['medianSeconds']==statistics.median(row['seconds']),'Recorded timing median')
    small_output = args.small_run_output.resolve()
    require(small_output!=BASE and BASE not in small_output.parents,
            'Keep the independent small-run output outside the accepted research lane')
    args.small_run_output.mkdir(parents=True,exist_ok=True)
    small = subprocess.run([sys.executable,str(BASE/'run_experiment.py'),'--limit','100','--output',str(args.small_run_output)],
                           cwd=BASE,capture_output=True,text=True,encoding='utf-8',timeout=90)
    require(small.returncode==0,'--limit 100 subprocess failed: '+small.stderr)
    small_validation=load(args.small_run_output/'validation.json')
    small_table=load(args.small_run_output/'table-0-100.json')
    require(small_validation['limit']==100 and small_validation['checkedIntegers']==101,'Small CLI range')
    require(small_validation['prefixConsistencyCutoffs']==[n for n in validation['prefixConsistencyCutoffs'] if n<=100],
            'Small CLI prefix filtering')
    require(small_table['rows']==oracle[:101],'Small CLI table')
    for path in producer_files:
        require(sha(path)==before[str(path)],'Input changed during independent review: '+str(path))
    inputs=producer_files+[Path(__file__)]
    report=dict(schema='graph-composite-remainder-independent-review-v1',traceId='graph.primes.composite_remainder.independent_review',
        status='passed',reviewedAtUtc=datetime.now(timezone.utc).isoformat(),
        runtime=dict(python=sys.version,executable=sys.executable),
        oracle='Least-prime-factor factorization; tau(n) is the product of exponent+1, with factor-pair reconstruction from generated divisors.',
        coverage=dict(range=[0,limit],coefficients=limit+1,scalarClassifications=limit+1,factorPairLists=limit+1,
                      prefixCutoffs=prefix_cutoffs,domainRejections=rejected,extraControls=len(extra_results),
                      supplementaryHCoefficients=limit+1,savedTableRows=101),
        counts=dict(primes=sum(expected_flags),oddPrimes=sum(expected_flags[3::2]),oddComposites=sum(v>0 for v in expected_u)),
        extraControls=extra_results,reversal=reversal_results,
        cliLimit100=dict(exitCode=small.returncode,checkedIntegers=small_validation['checkedIntegers'],
                         outputDirectory=str(args.small_run_output.resolve()),stdout=small.stdout.strip(),
                         files=[dict(path=str(p.resolve()),sha256=sha(p)) for p in sorted(args.small_run_output.glob('*.json'))]),
        mathematicalReview=dict(status='passed',
            statements=['The floor difference equals the exact divisibility indicator.',
                        'Restricting the smaller odd divisor to sqrt(n) counts unordered pairs, including square pairs once.',
                        'Subtracting the two unit-factor families and restoring (1,1) yields ordered odd composite multiplicities.',
                        'U_N has exact coefficients through N; omitted d>sqrt(N) cannot contribute there.',
                        'The Lambert series converge absolutely for |z|<1, with the stated r^9/(1-r^6)^2 bound.',
                        'A(s)=(1-2^(-s))*zeta(s), Q_D=(A-1)^2 and U_D=((A-1)^2+A(2s)-1)/2 have the claimed coefficients for Re(s)>1.',
                        'H=A-1-log(A) uses the analytic Euler-product logarithm on Re(s)>1; its stated prime-power and composite weights are correct.',
                        'For real s>1, Q_D and U_D are positive; analytic values at s=n are not coefficient extraction.',
                        'At a nontrivial zeta zero rho, Q_D(rho)=1; continuation to Re(s)=1/2 does not prove RH.',
                        'A bare polynomial reversal difference is antisymmetric, preventing a nonzero nonnegative full-range composite indicator.'],
            supplementaryHExamples=h_examples,
            supplementaryScope='Q_D/U_D/H are reviewed mathematical identities. Only U coefficients and separate domain guards supply the executed candidate classifier.'),
        benchmarkReview=dict(status='scope-checked-only',coefficientUpdates=costs['coefficientUpdates'],
            statement='Local CPython timings compare Python coefficient loops with an optimized bytearray sieve using C-level slice assignment. They do not isolate algorithmic efficiency. Multiplicity counts and prime flags also differ in output content.',
            scalarCost='The scalar equation uses two floor divisions per odd candidate divisor and counts all candidates through sqrt(n); the equivalent modulo test can use one remainder and stop after finding a factor.',
            acceptedTimingRerun=False,smallCliBenchmarkExecuted=True,
            timingNote='The --limit 100 smoke run also executes the producer timing section; those new timings are not used to claim performance.'),
        blockers=[],
        limitations=['Finite implementation verification supplements the elementary all-integer argument; it is not a formal proof-assistant replay.',
                     'No performance advantage, novel prime algorithm, instant coefficient extraction, or RH progress is established.',
                     'No graphics or presentation rendering is included in this review.',
                     'H coefficient checks validate the stated supplementary expansion, not a numerical complex-log evaluator.'],
        inputs=[dict(path=str(p.resolve()),sha256=sha(p)) for p in inputs],
        elapsedSeconds=time.perf_counter()-started)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',range=[0,limit],coefficients=limit+1,
                         prefixCutoffs=len(prefix_cutoffs),domainRejections=rejected,counts=report['counts'],
                         report=str(args.output),sha256=sha(args.output)),indent=2),flush=True)


if __name__=='__main__':
    main()
