"""Exact finite analysis of divisor phases and half-step pair comparisons.

defines: graph.primes.divisor_phases
consumer: graph.primes.quadrant_phase
Standard library only. Prime labels select comparison cohorts and verify results;
they never enter the phase or quadrant calculation.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIVISORS = (2,3,5,7)


def prime_oracle(n):
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n)+1))


def quadrant(residue, divisor, offset=45):
    """One-based half-open quadrant from exact rational turns."""
    turns = (Fraction(residue % divisor, divisor) + Fraction(offset,360)) % 1
    return int(4*turns) + 1


def color_pass(n, offset=45):
    return all(quadrant(n % d,d,offset) != quadrant(0,d,offset) for d in DIVISORS)


def classify(n, offset=45):
    """Finite experiment only; outside0..100 the fixed divisors do not suffice."""
    if type(n) is not int or not 0 <= n <= 100:
        raise ValueError('This classifier is defined only for integer candidates0..100.')
    if n < 2:
        return 'neither'
    if n in DIVISORS:
        return 'prime'
    return 'prime' if color_pass(n,offset) else 'composite'


def divisor_wave(d,x):
    return (1 + 2*sum(math.cos(2*math.pi*j*x/d) for j in range(1,(d-1)//2+1)))/d


def periodic_product(x):
    result = math.sin(math.pi*x/2)**2
    for d in (3,5,7):
        result *= 1-divisor_wave(d,x)
    return result


def pair_matrix(references,targets):
    raw=[]; half=[]; residues=[]; half_residues=[]; local=[]
    for p in references:
        raw.append([quadrant(q%p,p) for q in targets])
        local.append([quadrant((q-p)%p,p) for q in targets])
        residues.append([q%p for q in targets])
        half.append([quadrant(((q-p)//2)%p,p) if p%2 and q%2 else None for q in targets])
        half_residues.append([((q-p)//2)%p if p%2 and q%2 else None for q in targets])
    assert raw==local
    return dict(references=references,targets=targets,rawQ45=raw,localQ45=local,
                halfQ45=half,rawResidues=residues,halfResidues=half_residues)


def pair_counts(matrix):
    raw_alias=[]; half_alias=[]; joint_alias=[]; true_div=[]; changed=0
    histogram=Counter()
    for i,p in enumerate(matrix['references']):
        for j,q in enumerate(matrix['targets']):
            r=matrix['rawResidues'][i][j]
            a,b=matrix['rawQ45'][i][j],matrix['halfQ45'][i][j]
            histogram[a]+=1
            if r==0:
                true_div.append([p,q])
            elif a==1:
                raw_alias.append([p,q])
            if b is not None:
                h=matrix['halfResidues'][i][j]
                assert (2*h)%p==r
                if r and b==1: half_alias.append([p,q])
                if r and a==b==1: joint_alias.append([p,q])
                changed += a!=b
    return dict(cells=sum(len(row) for row in matrix['rawQ45']),
                exactDivisibilities=len(true_div),rawAliases=len(raw_alias),
                halfAliases=len(half_alias),jointAliases=len(joint_alias),
                changedByHalf=changed,rawHistogram=dict(sorted(histogram.items())),
                examples=dict(rawAliases=raw_alias[:12],halfAliases=half_alias[:12],jointAliases=joint_alias[:12]),
                allAliases=dict(raw=raw_alias,half=half_alias,joint=joint_alias),
                trueDivisibilities=true_div)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    primes=[n for n in range(101) if prime_oracle(n)]
    odd_primes=[n for n in primes if n%2]
    odd_composites=[n for n in range(3,101,2) if not prime_oracle(n)]
    assert len(primes)==25 and len(odd_primes)==24 and len(odd_composites)==25
    rejected=0
    for bad in (-1,101,121,True,3.0):
        try: classify(bad)
        except ValueError: rejected+=1
        else: raise AssertionError(('finite classifier domain',bad))
    rows=[]
    for n in range(101):
        expected='neither' if n<2 else 'prime' if prime_oracle(n) else 'composite'
        assert classify(n)==expected,n
        waves=[dict(divisor=d,value=divisor_wave(d,n),exact=int(n%d==0)) for d in (3,5,7)]
        assert all(abs(w['value']-w['exact'])<1e-12 for w in waves)
        rows.append(dict(n=n,classification=expected,odd=bool(n%2),
            halfIndex=str(Fraction(n-1,2)),halfFraction=str(Fraction(n,2)%1),
            phases=[dict(divisor=d,residue=n%d,q0=quadrant(n%d,d,0),q45=quadrant(n%d,d),
                         exactDivisibility=n%d==0) for d in DIVISORS],
            colorClassification=classify(n),waves=waves,periodicValue=periodic_product(n)))
    max_error=max(abs(rows[n]['periodicValue']-int(prime_oracle(n))) for n in range(8,101))
    assert max_error<1e-12
    rotations=[]
    for offset in (0,15,30,38,Fraction(270,7),39,45,51,Fraction(360,7),52,60,75,90):
        false_neg=[n for n in range(8,101) if prime_oracle(n) and not color_pass(n,offset)]
        false_pos=[n for n in range(8,101) if not prime_oracle(n) and color_pass(n,offset)]
        rotations.append(dict(offsetDegrees=float(offset),exactOffset=str(offset),
            truePositives=21-len(false_neg),falseNegatives=len(false_neg),
            trueNegatives=72-len(false_pos),falsePositives=len(false_pos),
            missedPrimes=false_neg,passedComposites=false_pos))
    assert all(r['falsePositives']==0 for r in rotations)
    assert next(r for r in rotations if r['exactOffset']=='45')['falseNegatives']==0
    all_pairs=pair_matrix(primes,primes)
    odd_pairs=pair_matrix(odd_primes,odd_primes)
    controls=pair_matrix(odd_primes,odd_composites)
    all_counts=pair_counts(all_pairs); odd_counts=pair_counts(odd_pairs); control_counts=pair_counts(controls)
    assert all_counts['rawAliases']==123 and all_counts['exactDivisibilities']==25
    assert (odd_counts['rawAliases'],odd_counts['halfAliases'],odd_counts['jointAliases'])==(104,110,43)
    assert (control_counts['rawAliases'],control_counts['halfAliases'],control_counts['jointAliases'])==(114,156,74)
    assert odd_counts['changedByHalf']==437 and control_counts['exactDivisibilities']==45
    isolation=[]
    for d in range(3,100,2):
        inv2=pow(2,-1,d)
        single=[r for r in range(1,d) if quadrant(r,d)==1]
        joint=[r for r in range(1,d) if quadrant(r,d)==quadrant(r*inv2%d,d)==1]
        assert (len(single)==0)==(d<8)
        assert (len(joint)==0)==(d<16)
        isolation.append(dict(divisor=d,primeReference=prime_oracle(d),
                              rawAliasingResidues=single,jointAliasingResidues=joint))
    data=dict(schema='graph-prime-divisor-phases-v1',traceId='graph.primes.divisor_phases',
        divisors=list(DIVISORS),primes=primes,oddPrimes=odd_primes,oddComposites=odd_composites,
        rows=rows,rotations=rotations,pairMatrix=all_pairs,oddPairMatrix=odd_pairs,controlMatrix=controls,
        summary=dict(primes0to100=25,composites0to100=74,neither=2,
                     ordinaryPairCounts=all_counts,oddPrimePairCounts=odd_counts,
                     oddCompositePairCounts=control_counts,zeroIsolation=isolation,
                     waveMaximumFloatError8to100=max_error,
                     exactCommonOffsetInterval=dict(lower='270/7',lowerInclusive=True,upper='360/7',upperInclusive=False),
                     robustMarginAt45Degrees='45/7',
                     outsideRangeControl=dict(n=121,finiteFilterPasses=color_pass(121),actualPrime=False)),
        formulas=dict(raw='z_d(n)=exp(2*pi*i*n/d)',
                      color='Q=1+floor(4*((n mod d)/d + offset/360 mod1))',
                      local='z_p(q-p)=z_p(q)',
                      half='H_p(q)=exp(2*pi*i*((q-p)/2)/p), odd p,q; H_p(q)^2=z_p(q) BEFORE palette offset'),
        limits=['Colors label phase bins and do not alter arithmetic.',
                'Known primes select comparison cohorts and provide independent verification; they never generate colors.',
                'Half-step identities hold for odd composites too; histogram differences are not a primality claim.',
                'Finite divisibility sieve and phase quantization; no novelty, speedup or RH result established.',
                '0/1 and2/3/5/7 need explicit treatment; the raw periodic product is guaranteed as a prime indicator only on8..100.',
                'A +45-degree palette offset is applied after the raw complex identities. Squaring an already-offset phasor adds a further offset.'])
    result=args.output/'analysis.json'
    result.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    validation=dict(traceId='graph.primes.divisor_phases.validation',status='passed',
        sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        analysisSha256=hashlib.sha256(result.read_bytes()).hexdigest(),
        coverage=dict(integerDomain=[0,100],primePairs=625,oddPrimePairs=576,oddCompositePairs=600,
                      paletteOffsets=len(rotations),oddDivisorResidueEnumerations=49,
                      maxFloatWaveError=max_error,finiteDomainRejections=rejected),
        note='Exact Fraction/integer predicates decide. Floating cosine evaluations are a separately bounded finite numerical check, not a certified global error bound.')
    (args.output/'validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',coverage=validation['coverage'],
                         oddPrimeAliases=[odd_counts[k] for k in ('rawAliases','halfAliases','jointAliases')],
                         controlAliases=[control_counts[k] for k in ('rawAliases','halfAliases','jointAliases')]),indent=2))


if __name__=='__main__': main()
