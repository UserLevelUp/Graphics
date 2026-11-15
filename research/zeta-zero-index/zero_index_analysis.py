"""Starting slopes and short continuation paths for indexed zeta zeros.

defines: graph.riemann.zero_index.analysis
consumer: graph.riemann.continuation

The index j labels a zero. It is not the zero's height and is not an input
integer whose primality is inferred from zeta geometry.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import mpmath as mp

BASE=Path(__file__).resolve().parent
EVIDENCE=BASE/'evidence'
CONTROLS=[1,4,6,8,9,10]


def prime(n):
    return n>=2 and all(n%d for d in range(2,math.isqrt(n)+1))


def num(x): return mp.nstr(x,48)
def cnum(z): return dict(real=num(z.real),imag=num(z.imag))
def sign(x): return 'negative' if x<0 else 'positive' if x>0 else 'zero'
def write(path,data): path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def describe_slope(dz):
    if abs(dz)<mp.mpf('1e-18'):
        raise ArithmeticError('Derivative magnitude is below the continuation guard.')
    velocity=1/dz
    vertical=abs(dz.real)<mp.mpf('1e-25')
    slope=None if vertical else -dz.imag/dz.real
    return velocity,slope,vertical


def base_metadata():
    return dict(createdUtc=datetime.now(timezone.utc).isoformat(),
        source=dict(path=Path(__file__).name,sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
        runtime=dict(python=sys.version,executable=sys.executable,mpmath=mp.__version__,
            recovery='Existing Python3.11 used after Python3.14 access violations in a superseded integer-height mpmath study. No runtime or application installation changed.'))


def starts():
    mp.mp.dps=50
    selected=sorted(set(CONTROLS+[j for j in range(1,101) if prime(j)]))
    records=[];raw={};max_d=mp.mpf(0);max_s=mp.mpf(0);max_rho=mp.mpf(0)
    for j in range(1,101):
        rho=mp.zetazero(j)
        dz=mp.zeta(rho,derivative=1)
        velocity,slope,vertical=describe_slope(dz)
        residual=abs(mp.zeta(rho))
        assert residual<mp.mpf('1e-40')
        with mp.workdps(75):
            rho75=mp.zetazero(j)
            dz75=mp.zeta(rho75,derivative=1)
            independent=mp.diff(mp.zeta,rho75)
            velocity75,slope75,vertical75=describe_slope(dz75)
            assert vertical==vertical75
            derivative_error=abs(dz75-independent)
            precision_error=abs(slope75-slope) if slope is not None else mp.mpf(0)
            max_d=max(max_d,derivative_error)
            max_s=max(max_s,precision_error)
            max_rho=max(max_rho,abs(rho-rho75))
            assert derivative_error<mp.mpf('1e-60')
            assert precision_error<mp.mpf('1e-38')
            if slope is not None: assert sign(slope)==sign(slope75)
        records.append(dict(zeroIndex=j,height=num(rho.imag),sigma=num(rho.real),
            classificationPrimeIndex='neither' if j==1 else 'prime' if prime(j) else 'composite',
            isPrimeIndex=prime(j),selected=j in selected,rho=cnum(rho),zeroResidual=num(residual),
            startDerivative=cnum(dz),dsDa=cnum(velocity),slope=num(slope) if slope is not None else None,
            slopeSign='vertical' if vertical else sign(slope),
            sigmaDirectionForIncreasingA=sign(velocity.real),heightDirectionForIncreasingA=sign(velocity.imag),
            derivativeMagnitude=num(abs(dz)),verticalSlope=vertical,
            precisionCheck=dict(derivativeVsDiffError=num(derivative_error),slope50vs75Error=num(precision_error))))
        raw[j]=(rho,dz)
        if j%10==0: print('Starting slopes checked through index '+str(j),flush=True)
    groups={}
    for group in ('prime','composite','neither'):
        rows=[r for r in records if r['classificationPrimeIndex']==group]
        groups[group]=dict(count=len(rows),negativeIndices=[r['zeroIndex'] for r in rows if r['slopeSign']=='negative'],
                          positiveIndices=[r['zeroIndex'] for r in rows if r['slopeSign']=='positive'],
                          verticalIndices=[r['zeroIndex'] for r in rows if r['slopeSign']=='vertical'])
    report=dict(schema='graph-zeta-zero-index-v1',traceId='graph.riemann.zero_index.analysis',status='passed',
        **base_metadata(),
        definition=dict(trajectory='zeta(s(a))=a, real a; start s(0)=rho_j.',
                        derivative='ds/da=1/zeta_prime(s)',slope='dt/dsigma=-Im(zeta_prime(s))/Re(zeta_prime(s))',
                        slopeConvention='sigma horizontal, t increasing upward; Cartesian slope dt/dsigma.',
                        indexMeaning='j is the ordered positive-height nontrivial zero index, not height t=j.',
                        startTarget=0,indices=[1,100]),
        selectedIndices=selected,controlIndices=CONTROLS,rows=records,summary=groups,
        validation=dict(primaryDps=50,checkDps=75,zeroResidualLimit='1e-40',
                        derivativeComparison='mp.zeta(s,derivative=1) vs mp.diff(mp.zeta,s) at75dps',
                        maxDerivativeDifference=num(max_d),maxSlopePrecisionDifference=num(max_s),
                        maxZeroPrecisionDifference=num(max_rho)),
        guards=dict(lowDerivativeMagnitude='1e-18',verticalIfAbsRealDerivativeBelow='1e-25'),
        limits=['Numerical precision agreement is not an interval certificate.',
                'The prime/composite label describes the zero index only.',
                'Starting slopes do not determine the full path; trajectories can bend.',
                'Phase of zeta(s)-a is undefined on the trajectory itself; the inverse derivative is used there.',
                'No prime predictor or new RH result follows from this comparison.'])
    write(EVIDENCE/'zero-index.json',report)
    print('zero-index.json ready: '+json.dumps(groups),flush=True)
    return raw,selected


def continuation(raw,selected):
    mp.mp.dps=50
    target_step=mp.mpf('.005')
    paths=[]
    for j in selected:
        rho,_=raw[j]
        stats=dict(acceptedSubsteps=0,maxPredictorCorrection=mp.mpf(0),maxStepDistance=mp.mpf(0),
                   maxResidual=mp.mpf(0),minimumDerivative=mp.inf)
        def advance(previous,a0,a1,depth=0):
            derivative=mp.zeta(previous,derivative=1)
            velocity,_,_=describe_slope(derivative)
            guess=previous+(a1-a0)*velocity
            try:
                endpoint=mp.findroot(lambda s:mp.zeta(s)-a1,guess,solver='newton',
                    df=lambda s:mp.zeta(s,derivative=1),maxsteps=30,verify=True)
                residual=abs(mp.zeta(endpoint)-a1)
                correction=abs(endpoint-guess);distance=abs(endpoint-previous)
                accepted=(residual<mp.mpf('1e-38') and correction<mp.mpf('.05') and distance<mp.mpf('.1'))
            except (ValueError,ZeroDivisionError):
                accepted=False
            if not accepted:
                if depth>=12 or a1-a0<mp.mpf('1e-7'):
                    raise ArithmeticError('Continuation correction failed after bounded subdivision.')
                midpoint=(a0+a1)/2
                middle=advance(previous,a0,midpoint,depth+1)
                return advance(middle,midpoint,a1,depth+1)
            if not mp.mpf('.05')<=endpoint.real<=3 or endpoint.imag<=0:
                raise ArithmeticError('Continuation left the computational viewport.')
            endpoint_d=mp.zeta(endpoint,derivative=1)
            describe_slope(endpoint_d)
            stats['acceptedSubsteps']+=1
            stats['maxPredictorCorrection']=max(stats['maxPredictorCorrection'],correction)
            stats['maxStepDistance']=max(stats['maxStepDistance'],distance)
            stats['maxResidual']=max(stats['maxResidual'],residual)
            stats['minimumDerivative']=min(stats['minimumDerivative'],abs(endpoint_d))
            return endpoint
        points=[];s=rho
        for k in range(21):
            a=target_step*k
            if k:s=advance(s,a-target_step,a)
            dz=mp.zeta(s,derivative=1)
            velocity,slope,vertical=describe_slope(dz)
            points.append(dict(a=num(a),s=cnum(s),sigma=num(s.real),t=num(s.imag),
                derivative=cnum(dz),dsDa=cnum(velocity),slope=num(slope) if slope is not None else None,
                slopeSign='vertical' if vertical else sign(slope),residual=num(abs(mp.zeta(s)-a)),
                insideLocalViewport=bool(mp.mpf('.4')<=s.real<=mp.mpf('.9') and abs(s.imag-rho.imag)<=mp.mpf('.35'))))
        # A second, smaller target step tests convergence of the starting secant.
        small=advance(rho,mp.mpf(0),mp.mpf('.0025'))
        true_velocity=1/raw[j][1]
        first=mp.mpc(points[1]['s']['real'],points[1]['s']['imag'])
        full_error=abs((first-rho)/target_step-true_velocity)
        half_error=abs((small-rho)/mp.mpf('.0025')-true_velocity)
        assert half_error<full_error
        paths.append(dict(zeroIndex=j,height=num(rho.imag),isPrimeIndex=prime(j),
            classificationPrimeIndex='neither' if j==1 else 'prime' if prime(j) else 'composite',
            status='complete',points=points,
            checks=dict(startingSecantErrorAt005=num(full_error),startingSecantErrorAt0025=num(half_error),
                        smallerStepImprovesStartingVelocity=True),
            stats={k:num(v) if not isinstance(v,int) else v for k,v in stats.items()}))
        print('Short path complete for zero index '+str(j),flush=True)
    report=dict(schema='graph-zeta-zero-index-paths-v1',traceId='graph.riemann.zero_index.paths',status='passed',
        **base_metadata(),selectedIndices=selected,
        parameters=dict(targetRange=[0,.1],targetSamples=21,nominalStep=.005,precisionDps=50,
                        computationalSigmaViewport=[.05,3],localRenderViewport=dict(sigma=[.4,.9],heightRadius=.35)),
        guards=dict(maxPredictorCorrection='.05',maxAcceptedStepDistance='.1',residualLimit='1e-38',
                    lowDerivativeMagnitude='1e-18',maxSubdivisionDepth=12,minTargetStep='1e-7',
                    verticalIfAbsRealDerivativeBelow='1e-25'),
        paths=paths,summary=dict(paths=len(paths),points=sum(len(p['points']) for p in paths),
            outsideLocalViewport=[dict(zeroIndex=p['zeroIndex'],a=q['a']) for p in paths for q in p['points'] if not q['insideLocalViewport']]),
        limits=['This is numerical predictor/Newton continuation with bounded guards, not a validated interval path certificate.',
                'Prime labels refer to zero indices, never to their noninteger heights.',
                'The short target interval is0..0.10; it does not establish behavior up to target1.',
                'No new RH result, prime predictor or novelty claim is established.'])
    write(EVIDENCE/'paths.json',report)
    print('paths.json ready: '+json.dumps(report['summary']),flush=True)


def main():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    raw,selected=starts()
    continuation(raw,selected)


if __name__=='__main__': main()
