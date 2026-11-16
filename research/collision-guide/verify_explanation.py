"""Independent arithmetic and semantic-review receipt for the collision guide.

defines: graph.riemann.collision_guide.explanation_review
The producer is executed as a separate CLI. Polynomial operations below use
descending coefficients; no producer implementation is imported.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import json
from math import factorial
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]
PRODUCER = REPO / 'research/gap-bound/verify_bound.py'
APPLICATION = BASE / 'use_certificate.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strip(a):
    a = list(a)
    while len(a) > 1 and not a[0]:
        a.pop(0)
    return a


def multiply(a, b):
    c = [F(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            c[i+j] += x*y
    return strip(c)


def derivative(a):
    n = len(a)-1
    return strip([v*(n-i) for i,v in enumerate(a[:-1])] or [F(0)])


def division_remainder(a, b):
    a, b = strip(a), strip(b)
    while a != [0] and len(a) >= len(b):
        q = a[0]/b[0]
        for i, v in enumerate(b):
            a[i] -= q*v
        a = strip(a)
    return a


def independent_sturm(a):
    seq = [strip(a), derivative(a)]
    while seq[-1] != [0]:
        nxt = [-x for x in division_remainder(seq[-2],seq[-1])]
        if nxt == [0]:
            break
        seq.append(nxt)
    def variation(at):
        signs = [(1 if q[0] > 0 else -1) * (at ** (len(q)-1)) for q in seq]
        return sum(x != y for x,y in zip(signs,signs[1:]))
    return {'distinctRealRoots':variation(-1)-variation(1),
            'gcdDegreeWithDerivative':len(seq[-1])-1}


def polynomial(roots):
    p = [F(1)]
    for r in roots:
        p = multiply(p,[F(1),-r])
    return p


def heat_at(p, t):
    answer = list(p)
    diff = list(p)
    for order in range(1,(len(p)-1)//2+1):
        diff = derivative(derivative(diff))
        weight = (-t)**order / factorial(order)
        shift = len(answer)-len(diff)
        for j,c in enumerate(diff):
            answer[shift+j] += weight*c
    return strip(answer)


def log_interval(x, terms=80):
    # Independent atanh expansion, distinct from producer's -log(1-x) series.
    w=x/(2-x)
    lo=2*sum((w**(2*j+1)/(2*j+1) for j in range(terms)),F(0))
    tail=2*w**(2*terms+1)/((2*terms+1)*(1-w*w))
    return lo,lo+tail


def power_interval(base, exponent, steps=160):
    lo,hi=F(0),F(1)
    target=base**exponent.numerator
    for _ in range(steps):
        m=(lo+hi)/2
        if m**exponent.denominator < target:
            lo=m
        else:
            hi=m
    assert lo**exponent.denominator <= target <= hi**exponent.denominator
    return lo,hi


def decimals(q):
    with localcontext() as ctx:
        ctx.prec=45
        return str(Decimal(q.numerator)/Decimal(q.denominator))


def bounds(roots):
    n=len(roots);d=(roots[-1]-roots[0])**2
    m=min(b-a for a,b in zip(roots,roots[1:]));k=F(n-2)/d
    loglo,loghi=log_interval(k*m*m/2)
    constant=(loglo/(4*k),loghi/(4*k))
    a,b=F(4*(n-2)),F(16*n-24)
    eta=(a+b)*m*m/(8*d)
    powerlo,powerhi=power_interval(1-eta,b/(a+b))
    dynamic=(d/b*(1-powerhi),d/b*(1-powerlo))
    assert 0<eta<1 and m*m/8 < constant[0] < dynamic[0] < d/b
    return dict(minimumGap=m,diameterSquared=d,kappa=k,baseline=m*m/8,
                constant=constant,dynamic=dynamic,eta=eta)


def interactions(roots):
    velocities=[2*sum((1/(r-s) for j,s in enumerate(roots) if j!=i),F(0)) for i,r in enumerate(roots)]
    d=roots[-1]-roots[0];n=len(roots)
    assert velocities[-1]-velocities[0] >= F(8*n-12)/d
    for i,(a,b) in enumerate(zip(roots,roots[1:])):
        g=b-a
        exterior=sum((1/((b-r)*(a-r)) for j,r in enumerate(roots) if j not in (i,i+1)),F(0))
        assert exterior >= F(n-2)/(d*d)
        assert velocities[i+1]-velocities[i] == 4/g-2*g*exterior
        assert 2*g*(velocities[i+1]-velocities[i]) == 8-4*g*g*exterior
    assert sum(velocities)==0
    return velocities


def application_controls():
    """Exercise the public wrapper, then recompute its point checks separately."""
    def invoke(roots, duration):
        return subprocess.run([sys.executable,'-B',str(APPLICATION),
            '--roots='+roots,'--duration='+duration],capture_output=True,text=True)
    accepted=[]
    specs=[('-3,-1,1,3','0',True,4,0),
           ('-3,-1,1,3','17/32',True,4,0),
           ('-3,-1,1,3','3/5',False,4,0),
           ('-3,-1,1,3','2/3',False,2,2),
           ('-3,-1,1,3','7/10',False,0,0),
           ('3,-1,-3,1','17/32',True,4,0),
           ('0,1/20,1,3,6','1/10000',True,5,0),
           ('0,0.05,1,3,6','1/10000',True,5,0)]
    example=None
    for raw,u,certified,nreal,gcd in specs:
        run=invoke(raw,u);assert run.returncode==0,run.stderr
        result=json.loads(run.stdout)
        roots=sorted(F(x) for x in raw.split(','));duration=F(u)
        own=independent_sturm(heat_at(polynomial(roots),-duration))
        assert own==dict(distinctRealRoots=nreal,gcdDegreeWithDerivative=gcd)
        point=result['exactPointCheck'];interval=result['guaranteedInterval']
        assert result['inputs']['roots']==list(map(str,roots))
        assert F(result['inputs']['flowParameter'])==-duration
        assert point['coefficientsAscending']==list(map(str,reversed(heat_at(polynomial(roots),-duration))))
        assert all(point['counts'][k]==v for k,v in own.items())
        assert point['status']==('all_roots_real_and_simple' if nreal==len(roots) and gcd==0 else 'not_all_roots_real_and_simple')
        assert (interval['status']=='certified')==certified==(duration<F(interval['lowerEnclosure']))
        ownbounds=bounds(roots)
        assert F(interval['lowerEnclosure'])<=ownbounds['dynamic'][0]<=ownbounds['dynamic'][1]<=F(interval['upperEnclosure'])
        accepted.append(dict(roots=raw,elapsedU=u,intervalStatus=interval['status'],independentPointCount=own))
        if raw=='-3,-1,1,3' and u=='17/32':example=result
    recorded=json.loads((BASE/'evidence/use-example.json').read_text(encoding='utf-8-sig'))
    assert recorded==example
    # The implementation deliberately uses a strict comparison even at its lower enclosure.
    boundary=example['guaranteedInterval']['lowerEnclosure']
    equal=invoke('-3,-1,1,3',boundary);assert equal.returncode==0,equal.stderr
    eq=json.loads(equal.stdout)
    assert eq['guaranteedInterval']['status']=='outside_available_guarantee'
    assert eq['exactPointCheck']['status']=='all_roots_real_and_simple'
    assert independent_sturm(heat_at(polynomial(list(map(F,[-3,-1,1,3]))),-F(boundary)))==dict(distinctRealRoots=4,gcdDegreeWithDerivative=0)
    rejected=[]
    for roots,duration,reason in [('0,1','0','degree below three'),('0,1,1','0','duplicate roots'),
        ('0,1,2','-1/10','negative elapsed duration'),('0,1,nan','0','nonfinite root input'),
        ('0,1,2','inf','nonfinite duration'),('0,1/0,2','0','zero denominator')]:
        run=invoke(roots,duration);assert run.returncode!=0
        assert not run.stdout.strip()
        rejected.append(dict(roots=roots,elapsedU=duration,reason=reason,diagnostic=run.stderr.strip()))
    return dict(accepted=accepted,rejected=rejected,strictEnclosureBoundary='Outside available guarantee at equality; independently four simple real roots.',
                recordedExampleMatchesFreshCli=True)


def discovery_controls(scenes):
    path=BASE/'evidence/discovery-provenance.json'
    provenance=json.loads(path.read_text(encoding='utf-8-sig'))
    paths=[path]
    for item in provenance['sources']:
        source=REPO/item['path'];assert sha(source)==item['sha256'],item
        paths.append(source)
    for query in provenance['queries']:
        source=BASE/'evidence'/query['report']
        assert query['returnCode']==0 and sha(source)==query['sha256']
        paths.append(source)
    scene=next(s for s in scenes if s['id']=='discovery_path')
    git_controls=[]
    for stage,milestone in zip(provenance['stages'],scene['diagramData']['milestones']):
        result=subprocess.run(['git','show','-s','--format=%H%n%cI%n%s',stage['commit']],
                              cwd=REPO,capture_output=True,text=True,check=True)
        commit,date,subject=result.stdout.strip().splitlines()
        assert (commit,date,subject)==(stage['git']['hash'],stage['git']['committedAt'],stage['git']['subject'])
        assert commit.startswith(milestone['commit'])
        observed=datetime.fromisoformat(date)
        assert milestone['date']==observed.strftime('%Y-%m-%d')
        assert milestone['time']==observed.strftime('%H:%M:%S %z')[:-2]+':'+observed.strftime('%z')[-2:]
        git_controls.append(dict(commit=commit,committedAt=date,subject=subject))
    assert len(git_controls)==3
    return dict(sourceHashes=len(provenance['sources']),savedTraceQueries=len(provenance['queries']),
        gitMilestones=git_controls,
        manualReview=['The bound-review contract supplies both formulas; reviewer agreement is not an invention record.',
            'The retained coordinator steering identifies the false product inequality, and the final Carbon review explicitly retracts it and derives the reciprocal estimate.',
            'Completed finite-result records and current infinite-system obligations describe different scopes; matching trace IDs are not proof.']),paths


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reviewed-script-sha256',required=True)
    p.add_argument('--output',type=Path,default=BASE/'evidence/explanation-review.json')
    args=p.parse_args()
    script_path=BASE/'script.json';guide=BASE/'guide.md'
    assert sha(script_path)==args.reviewed_script_sha256
    script=json.loads(script_path.read_text(encoding='utf-8-sig'))
    scenes=script['scenes']
    assert 16 <= len(scenes) <= 24
    assert len({s['id'] for s in scenes})==len(scenes)
    references=[]
    for scene in scenes:
        assert scene['narration'] and 1<=len(scene['screenLines'])<=4
        for path in scene.get('evidencePaths',[]):
            q=REPO/path
            assert q.is_file(),q
            references.append(q)
    completed=subprocess.run([sys.executable,'-B',str(PRODUCER)],capture_output=True,text=True,check=True)
    produced=json.loads(completed.stdout)
    assert produced['status']=='passed' and produced['caseCount']==25
    summaries=[];checked_times=0
    for case in produced['cases']:
        roots=list(map(F,case['rootsSorted']))
        assert roots==sorted(roots) and len(roots)==len(set(roots))
        p0=polynomial(roots)
        assert p0==list(reversed(list(map(F,case['initialCoefficientsAscending']))))
        v=interactions(roots);b=bounds(roots);pb={k:F(x) for k,x in case['exactBounds'].items()}
        assert b['minimumGap']==pb['minimum_gap'] and b['diameterSquared']==pb['diameter']**2
        assert pb['lower']<=b['constant'][0]<=b['constant'][1]<=pb['upper']
        assert pb['dynamic_lower']<=b['dynamic'][0]<=b['dynamic'][1]<=pb['dynamic_upper']
        assert b['dynamic'][0]>b['constant'][1]>b['baseline']
        for sample in case['samples']:
            t=F(sample['tau']);assert -b['dynamic'][0]<t<0
            s=independent_sturm(heat_at(p0,t))
            assert s=={k:sample['sturm'][k] for k in s}
            assert s==dict(distinctRealRoots=len(roots),gcdDegreeWithDerivative=0)
            checked_times+=1
        summaries.append(dict(name=case['name'],degree=len(roots),rootList=list(map(str,roots)),
            baseline=str(b['baseline']),constantLower=decimals(b['constant'][0]),dynamicLower=decimals(b['dynamic'][0]),
            sampleCount=len(case['samples'])))
    assert checked_times==100
    application=application_controls()
    discovery,discovery_paths=discovery_controls(scenes)
    quartic=list(map(F,[1,0,-10,0,9]));roots=list(map(F,[-3,-1,1,3]));b=bounds(roots)
    assert heat_at(quartic,F(-2,3))==list(map(F,[1,0,-2,0,1]))
    assert heat_at(quartic,F(-1))==list(map(F,[1,0,2,0,1]))
    assert b['constant'][1] < F(17,32) < b['dynamic'][0] < F(3,5) < F(2,3) < F(7,10)
    quartic_checks=[]
    for u,number,gcd in [(F(0),4,0),(F(17,32),4,0),(F(3,5),4,0),(F(2,3),2,2),(F(7,10),0,0),(F(1),0,2)]:
        q=heat_at(quartic,-u);count=independent_sturm(q)
        assert count==dict(distinctRealRoots=number,gcdDegreeWithDerivative=gcd)
        # Check the explicit quartic formula independently at these exact times.
        assert q==[F(1),F(0),-(10-12*u),F(0),9-20*u+12*u*u]
        quartic_checks.append(dict(elapsedU=str(u),heatParameterT=str(-u),coefficientsDescending=list(map(str,q)),**count))
    # Exact local-predictor counterexamples from the same polynomial.
    def evaluate(p,x):
        value=F(0)
        for a in p:value=value*x+a
        return value
    forecasts=[]
    for center,wanted in [(F(0),F(-9,20)),(F(2),F(-113,196)),(F(4,3),F(-28277,324)),(F(4),F(643,7396))]:
        a=evaluate(quartic,center);v=evaluate(derivative(quartic),center);d=evaluate(derivative(derivative(quartic)),center)
        delta=-(v*v-2*a*d)/(2*d*d)
        assert delta==wanted
        forecasts.append(dict(center=str(center),predictedT=str(delta),predictedLocation=str(center-v/d)))
    # Scaling applies to durations quadratically, including negative scaling.
    for scale,shift in [(F(2),F(7)),(F(-3,2),F(7,3))]:
        transformed=sorted(scale*r+shift for r in roots);tb=bounds(transformed)
        assert tb['baseline']==scale*scale*b['baseline']
        assert all(tb[k][j]==scale*scale*b[k][j] for k in ('constant','dynamic') for j in (0,1))
    sources=sorted(set([Path(__file__),script_path,guide,PRODUCER,APPLICATION,BASE/'evidence/use-example.json',
        REPO/'research/gap-bound/interaction-bound-proof.md',REPO/'research/collision-proof/exact-quartic-proof.md']+references+discovery_paths),key=str)
    report=dict(schema='graph-collision-guide-explanation-review-v1',traceId='graph.riemann.collision_guide.explanation_review',status='passed',
        reviewedAtUtc=datetime.now(timezone.utc).isoformat(),reviewedScriptSha256=sha(script_path),
        reviewer='Independent Codex subagent /root/collision_review; no producer polynomial or bound implementation imported',
        runtime=dict(python=sys.version,executable=sys.executable),
        analyticalReview=[
            'With P_t=-P_zz and t decreasing, u=-t increases and real roots attract. All displayed signs must respect this convention.',
            'The exact root velocity and adjacent squared-gap identity follow by implicit differentiation and finite product differentiation while roots are simple and real.',
            'Each exterior denominator for an adjacent pair is positive and bounded above by the current squared diameter; there are n-2 such roots.',
            'Backward integration converts the upper t-derivative inequality to the stated lower gap bound. Positive lower bounds prevent a first collision inside the certified interval.',
            'Finite degree and fixed nonzero leading coefficient bound roots on compact time intervals. Uniform positive gaps give bounded velocities and implicit-function continuation; no circular assumption of an already-global real-root interval is used.',
            'The dynamic diameter inequality uses reciprocal distances and x(D-x)<=D^2/4. Packing guarantees eta<1 and keeps d-Bu positive until the proposed dynamic threshold.',
            'The comparison ODE has strictly positive forcing before the static threshold, giving a strictly larger dynamic guarantee. Simplicity is claimed only before the threshold, with real roots and possible multiplicity at the endpoint.',
            'The duration bounds concern the exact polynomial flow. They do not bound Euler/Newton time-stepping error, arbitrary polynomial paths, or uncertain input roots.',
            'The known all-real initial state and finite global diameter are essential; the proof does not establish a transfer to the infinite Riemann entire function.',
            'Polynomial heat-flow root dynamics have established prior work. Exact novelty of the project bounds has not been established.'],
        discoveryReview=discovery,
        riemannConnectionReview=dict(primarySource='https://arxiv.org/abs/1801.05914',
            established=['The integral defining H_t has partial_t H=-partial_xx H.',
                'All zeros of H_t are real exactly for t>=Lambda; RH is equivalent to Lambda<=0.',
                'Rodgers and Tao proved Lambda>=0, so RH is equivalent to Lambda=0.'],
            inference='Any all-real regime at a negative parameter would force Lambda<0 and contradict the established lower bound. A route toward RH needs justified infinite-system control down to zero from a known-real regime, without assuming all H_0 zeros real.'),
        numericalAndExactChecks=dict(producerCliCases=25,independentlyRecomputedSturmSamples=checked_times,
            independentLogarithmExpansion='80-term atanh series with exact rational tail bound',independentPowerEnclosure='160 bisection steps checked by exact integer powers',
            rootVelocityAndAdjacentGapIdentities='Exact rational checks on every initial configuration',cases=summaries,
            quarticBounds=dict(baseline=str(b['baseline']),constant=decimals(b['constant'][0]),dynamic=decimals(b['dynamic'][0]),exactCollision='2/3',usefulTest='constantUpper < 17/32 < dynamicLower < 3/5 < 2/3'),
            quarticRootCounts=quartic_checks,localPredictorControls=forecasts,translationAndScalingChecks=2,
            applicationControls=application),
        scenes=[dict(id=s['id'],title=s['title'],narrationWords=len(s['narration'].split())) for s in scenes],
        priorWork=[dict(url='https://terrytao.wordpress.com/2017/10/17/heat-flow-and-zeroes-of-polynomials/',relationship='Established root-motion formulation; its positive heat time corresponds to this guide elapsed u=-t.'),
                   dict(url='https://arxiv.org/abs/1801.05914',relationship='Established infinite-system research; no transfer theorem from these finite bounds is supplied.')],
        limits=['The general proof is a reviewed analytic argument, not a proof-assistant replay.',
                'Exact rational arithmetic validates the listed implementation cases and examples, not every possible input.',
                'The scope and wording of the exact script hash were reviewed manually; numeric tests alone do not evaluate narrative meaning.',
                'Encoded visuals, narration placement and captions require a separate media review.'],
        inputs=[dict(path=str(q.resolve()),sha256=sha(q)) for q in sources])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',scriptSha256=sha(script_path),scenes=len(scenes),exactSturmSamples=checked_times,report=str(args.output)),indent=2))


if __name__=='__main__':main()
