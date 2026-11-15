"""Independent numerical review of zero-index paths and native grid samples.

defines: graph.riemann.zero_index.independent_math_grid_review
Requires mpmath only, plus the Python standard library. No NumPy or UI access.
This is finite numerical evidence, not an interval certificate or RH proof.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time

import mpmath as mp

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def C(value, imaginary='imag'):
    return mp.mpc(value['real'], value[imaginary])


def dec(value):
    return mp.nstr(value, 35)


def sgn(value):
    return 'negative' if value < 0 else 'positive' if value > 0 else 'zero'


def require(condition, description):
    if not condition:
        raise AssertionError(description)


def sieve(limit):
    flags = [True] * (limit + 1)
    flags[0] = flags[1] = False
    for p in range(2, limit + 1):
        if flags[p]:
            for n in range(2*p, limit + 1, p):
                flags[n] = False
    return flags


def coordinate(grid, x, y):
    d = grid['domain']
    return (d['minSigma'] + (d['maxSigma']-d['minSigma'])*x/(grid['width']-1),
            d['minT'] + (d['maxT']-d['minT'])*y/(grid['height']-1))


def quadrant(z):
    if z == 0:
        return None
    # Half-open counterclockwise quadrants; tested audit points need no tolerance.
    return int((mp.arg(z) % (2*mp.pi))/(mp.pi/2)) + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grids', type=Path, required=True)
    parser.add_argument('--native-bin', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=BASE/'evidence/independent-math-grid-review.json')
    args = parser.parse_args()
    started = time.perf_counter()
    starts_path = BASE/'evidence/zero-index.json'
    paths_path = BASE/'evidence/paths.json'
    starts, paths, grids = load(starts_path), load(paths_path), load(args.grids)
    require(grids['status'] == 'complete' and grids['completedGrids'] == grids['totalGrids'] == 32,
            'All 32 native grids must have completed before validation.')
    require(starts['status'] == paths['status'] == 'passed', 'Producer reports must pass.')
    require(starts['source']['sha256'] == paths['source']['sha256'] == sha(BASE/'zero_index_analysis.py'),
            'Producer source hashes do not match.')
    require(grids['input']['sha256'] == sha(starts_path), 'Native grid input hash does not match.')
    require([r['zeroIndex'] for r in starts['rows']] == list(range(1,101)), 'Starting indices must be 1..100.')
    flags = sieve(100)
    expected_selected = sorted(set([1,4,6,8,9,10] + [j for j in range(1,101) if flags[j]]))
    require(starts['selectedIndices'] == paths['selectedIndices'] == grids['selectedIndices'] == expected_selected,
            'Selected prime indices and controls differ.')
    mp.mp.dps = 75
    zero_error = mp.mpf(0); derivative_error = mp.mpf(0); velocity_error = mp.mpf(0)
    slope_error = mp.mpf(0); hardy_error = mp.mpf(0); initial_residual = mp.mpf(0)
    initial = {}; summary = {}
    for row in starts['rows']:
        j = row['zeroIndex']
        kind = 'neither' if j == 1 else 'prime' if flags[j] else 'composite'
        require(row['classificationPrimeIndex'] == kind and row['isPrimeIndex'] == flags[j], f'Index class{j}')
        require(row['selected'] == (j in expected_selected), f'Selection{j}')
        saved = C(row['rho'])
        fresh = mp.zetazero(j)
        dz = mp.diff(lambda s: mp.zeta(s), fresh)
        require(abs(dz) > mp.mpf('1e-18'), f'Nonzero derivative guard{j}')
        slope = -dz.imag/dz.real
        velocity = 1/dz
        zero_error = max(zero_error, abs(saved-fresh))
        derivative_error = max(derivative_error, abs(C(row['startDerivative'])-dz))
        velocity_error = max(velocity_error, abs(C(row['dsDa'])-velocity))
        slope_error = max(slope_error, abs(mp.mpf(row['slope'])-slope))
        hardy_error = max(hardy_error, abs(-mp.cot(mp.siegeltheta(mp.mpf(row['height'])))-mp.mpf(row['slope'])))
        initial_residual = max(initial_residual, abs(mp.zeta(saved)))
        require(row['sigma'] == '0.5' and saved.real == mp.mpf('.5'), f'Critical-line seed{j}')
        require(row['height'] == row['rho']['imag'], f'Height duplicate{j}')
        require(not row['verticalSlope'] and abs(dz.real) > mp.mpf('1e-25'), f'Nonvertical classification{j}')
        require(row['slopeSign'] == sgn(slope), f'Slope sign{j}')
        require(row['sigmaDirectionForIncreasingA'] == sgn(velocity.real), f'Sigma direction{j}')
        require(row['heightDirectionForIncreasingA'] == sgn(velocity.imag), f'Height direction{j}')
        require(abs(mp.mpf(row['derivativeMagnitude'])-abs(dz)) < mp.mpf('1e-40'), f'Derivative magnitude{j}')
        summary.setdefault(kind, {'count':0,'negativeIndices':[],'positiveIndices':[],'verticalIndices':[]})
        summary[kind]['count'] += 1
        summary[kind][sgn(slope)+'Indices'].append(j)
        initial[j] = (fresh,dz,velocity,slope)
        if j % 10 == 0:
            print('Independently checked starting zero index '+str(j), flush=True)
    for value, label in ((zero_error,'zeros'),(derivative_error,'derivatives'),(velocity_error,'velocities'),
                         (slope_error,'slopes'),(hardy_error,'Hardy slope identity'),(initial_residual,'seed residuals')):
        require(value < mp.mpf('1e-38'), 'High-precision agreement: '+label)
    require(summary == starts['summary'], 'Slope summary differs.')
    require(starts['rows'][1]['slopeSign'] == starts['rows'][6]['slopeSign'] == 'positive', 'Prime counterexamples 2 and 7')
    require(starts['rows'][7]['slopeSign'] == starts['rows'][9]['slopeSign'] == 'negative', 'Composite counterexamples 8 and 10')
    old_path = REPO/'research/zeta-continuation/evidence/reference-trajectories.json'
    old = load(old_path)
    old_comparison = []
    for branch in old['trajectories']:
        j = branch['startZeroIndex']
        if j not in (1,2,3):
            continue
        point = branch['points'][0]
        dz = C(point['derivativeDecimal'], 'imaginary')
        old_slope = -dz.imag/dz.real
        err = abs(old_slope - initial[j][3])
        require(err < mp.mpf('1e-40'), f'Historical slope Z{j}')
        old_comparison.append(dict(zeroIndex=j,slope=dec(old_slope),difference=dec(err)))
    require(len(old_comparison) == 3, 'Three historical starting slopes required.')

    path_residual = mp.mpf(0); path_d_error = mp.mpf(0); path_v_error = mp.mpf(0)
    path_slope_error = mp.mpf(0); max_step = mp.mpf(0); max_correction = mp.mpf(0)
    max_full_secant_error = mp.mpf(0); max_half_secant_error = mp.mpf(0)
    outside = []; points_checked = 0; path_details = []
    require([p['zeroIndex'] for p in paths['paths']] == expected_selected, 'Path order differs.')
    for path in paths['paths']:
        j = path['zeroIndex']; rho,dz0,v0,_ = initial[j]
        require(path['status'] == 'complete' and len(path['points']) == 21, f'Complete 21-point path Z{j}')
        require(path['isPrimeIndex'] == flags[j], f'Path class Z{j}')
        require(path['stats']['acceptedSubsteps'] == 21, f'This audit expects 20 nominal steps plus 1 half-step Z{j}')
        previous = None; local_max_step = mp.mpf(0); local_max_correction = mp.mpf(0)
        derivative_min = mp.inf
        for k, point in enumerate(path['points']):
            a = mp.mpf(point['a']); s = C(point['s'])
            require(abs(a-mp.mpf(k)/200) < mp.mpf('1e-45'), f'Target spacing Z{j}:{k}')
            require(point['sigma'] == point['s']['real'] and point['t'] == point['s']['imag'], f'Coordinate duplicates Z{j}:{k}')
            residual = abs(mp.zeta(s)-a)
            dz = mp.zeta(s, derivative=1); v = 1/dz; slope = -dz.imag/dz.real
            path_residual = max(path_residual, residual)
            path_d_error = max(path_d_error, abs(C(point['derivative'])-dz))
            path_v_error = max(path_v_error, abs(C(point['dsDa'])-v))
            path_slope_error = max(path_slope_error, abs(mp.mpf(point['slope'])-slope))
            require(residual < mp.mpf('1e-38') and abs(dz) > mp.mpf('1e-18'), f'Residual/derivative guard Z{j}:{k}')
            require(point['slopeSign'] == sgn(slope), f'Path slope sign Z{j}:{k}')
            inside = mp.mpf('.4') <= s.real <= mp.mpf('.9') and abs(s.imag-rho.imag) <= mp.mpf('.35')
            require(point['insideLocalViewport'] == inside, f'Viewport flag Z{j}:{k}')
            if not inside: outside.append(dict(zeroIndex=j,a=point['a']))
            if previous is not None:
                prev_s,prev_dz = previous
                distance = abs(s-prev_s); correction = abs(s-(prev_s+mp.mpf('.005')/prev_dz))
                require(distance < mp.mpf('.1') and correction < mp.mpf('.05'), f'Step guards Z{j}:{k}')
                local_max_step=max(local_max_step,distance);local_max_correction=max(local_max_correction,correction)
                derivative_min=min(derivative_min,abs(dz))
            previous=(s,dz);points_checked+=1
        # Independent secant solver for the additional target half-step.
        half_target=mp.mpf('.0025')
        half=mp.findroot(lambda s:mp.zeta(s)-half_target,(rho,rho+half_target*v0),solver='secant',verify=True)
        half_d=mp.zeta(half,derivative=1)
        half_residual=abs(mp.zeta(half)-half_target)
        require(half_residual < mp.mpf('1e-60'), f'Independent half-step residual Z{j}')
        local_max_step=max(local_max_step,abs(half-rho))
        local_max_correction=max(local_max_correction,abs(half-(rho+half_target*v0)))
        derivative_min=min(derivative_min,abs(half_d))
        full=C(path['points'][1]['s'])
        full_error=abs((full-rho)/mp.mpf('.005')-v0)
        half_error=abs((half-rho)/half_target-v0)
        require(half_error < full_error, f'Half-step convergence Z{j}')
        require(abs(full_error-mp.mpf(path['checks']['startingSecantErrorAt005']))<mp.mpf('1e-38'), f'Reported full secant Z{j}')
        require(abs(half_error-mp.mpf(path['checks']['startingSecantErrorAt0025']))<mp.mpf('1e-38'), f'Reported half secant Z{j}')
        for value,key in ((local_max_step,'maxStepDistance'),(local_max_correction,'maxPredictorCorrection'),(derivative_min,'minimumDerivative')):
            require(abs(value-mp.mpf(path['stats'][key]))<mp.mpf('1e-38'), f'Substep stat Z{j}:{key}')
        require(mp.mpf(path['stats']['maxResidual'])<mp.mpf('1e-38'), f'Producer residual bound Z{j}')
        max_step=max(max_step,local_max_step);max_correction=max(max_correction,local_max_correction)
        max_full_secant_error=max(max_full_secant_error,full_error);max_half_secant_error=max(max_half_secant_error,half_error)
        path_details.append(dict(zeroIndex=j,fullSecantError=dec(full_error),halfSecantError=dec(half_error)))
        print('Reviewed short path Z'+str(j),flush=True)
    require(points_checked==651 and not outside and paths['summary']['outsideLocalViewport']==outside, 'All 651 points inside local viewports.')
    for value in (path_d_error,path_v_error,path_slope_error):
        require(value < mp.mpf('1e-38'), 'Path derivative/velocity/slope agreement.')

    mp.mp.dps=50
    audit_results=[]; node_results=[]; binary_bindings=[]
    max_native=mp.mpf(0);max_native_scaled=mp.mpf(0);max_refined=mp.mpf(0)
    max_refinement=mp.mpf(0);max_refinement_scaled=mp.mpf(0);max_node=mp.mpf(0)
    unsafe_quadrants=[];phase_mismatches=[];total_nodes=0
    require(len(grids['grids'])==32, 'Grid count')
    for grid in grids['grids']:
        w,h=grid['width'],grid['height'];root=args.grids.parent
        require(grid['pointCount']==w*h and grid['binary']['bytes']==grid['binary']['expectedBytes']==16*w*h, 'Binary length metadata')
        binary=root/grid['binary']['file']; texture=root/grid['texture']['file']; metadata=root/grid['metadataFile']
        require(sha(binary)==grid['binary']['sha256'] and binary.stat().st_size==16*w*h, 'Binary hash/length '+grid['id'])
        require(sha(texture)==grid['texture']['sha256'], 'Texture hash '+grid['id'])
        require(load(metadata)==grid, 'Per-grid metadata differs '+grid['id'])
        png=texture.read_bytes()
        require(png[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',png[16:24])==(w,h), 'Texture dimensions '+grid['id'])
        require(grid['binary']['endianness']=='little' and grid['binary']['layout']=='row-major [y,x,component]; byteOffset=16*(y*width+x)', 'Binary layout '+grid['id'])
        require(grid['evaluator']['terms']==192 and grid['evaluator']['refinedAuditTerms']==256, 'Term counts '+grid['id'])
        require(grid['domain']['minT']>0 and grid['texture']['pixelToGrid']=='texturePixel(x,pngY) corresponds to binaryGrid(x,height-1-pngY)', 'Grid domain/orientation')
        raw=binary.read_bytes()
        invalid=sum(not(math.isfinite(re) and math.isfinite(im)) for re,im in struct.iter_unpack('<dd',raw))
        require(invalid==grid['invalidCount']==0, 'All native values finite '+grid['id'])
        total_nodes+=w*h
        if grid['zeroIndex'] is not None:
            j=grid['zeroIndex'];height=starts['rows'][j-1]['height']
            require(grid['sourceHeightDecimal']==height and grid['centerT']==float(height), 'Zero height consumed correctly '+grid['id'])
        for point in grid['samples']:
            require(point['valid'] and point['refinedValid'], 'Audit values valid')
            s=mp.mpc(point['sigma'],point['t']); ref=mp.zeta(s)
            native=mp.mpc(point['real'],point['imaginary']);refined=mp.mpc(point['refinedReal'],point['refinedImaginary'])
            err=abs(native-ref);err_scaled=err/max(1,abs(ref));refined_error=abs(refined-ref)
            refinement=abs(native-refined);scaled_refinement=refinement/max(1,abs(refined))
            max_native=max(max_native,err);max_native_scaled=max(max_native_scaled,err_scaled)
            max_refined=max(max_refined,refined_error);max_refinement=max(max_refinement,refinement)
            max_refinement_scaled=max(max_refinement_scaled,scaled_refinement)
            require(err<mp.mpf('1e-10') and refined_error<mp.mpf('1e-10') and err_scaled<mp.mpf('1e-10'), 'Native high-precision agreement '+grid['id']+':'+point['label'])
            require(abs(refinement-mp.mpf(point['refinementDifference']))<mp.mpf('1e-24'), 'Recorded refinement difference')
            if min(abs(ref.real),abs(ref.imag))<=mp.mpf('1e-10'):
                unsafe_quadrants.append(dict(grid=grid['id'],label=point['label']))
            if quadrant(native)!=quadrant(ref):
                phase_mismatches.append(dict(grid=grid['id'],label=point['label'],nativeQuadrant=quadrant(native),referenceQuadrant=quadrant(ref)))
            audit_results.append(dict(grid=grid['id'],label=point['label'],sigma=point['sigma'],t=point['t'],
                nativeAbsoluteError=dec(err),nativeScaledError=dec(err_scaled),refinedAbsoluteError=dec(refined_error)))
        for x,y in ((w//3,h//4),(2*w//3,3*h//4)):
            re,im=struct.unpack_from('<dd',raw,16*(y*w+x))
            sigma,t=coordinate(grid,x,y)
            ref=mp.zeta(mp.mpc(sigma,t));value=mp.mpc(re,im);err=abs(value-ref)
            require(err<mp.mpf('1e-10'), 'Interior binary node '+grid['id'])
            max_node=max(max_node,err)
            node_results.append(dict(grid=grid['id'],x=x,y=y,byteOffset=16*(y*w+x),sigma=sigma,t=t,
                                     absoluteError=dec(err),scaledError=dec(err/max(1,abs(ref)))))
        binary_bindings.append(dict(grid=grid['id'],binary=str(binary),binarySha256=sha(binary),
                                    texture=str(texture),textureSha256=sha(texture),metadata=str(metadata),metadataSha256=sha(metadata)))
        print('Audited native grid '+grid['id'],flush=True)
    require(len(audit_results)==160 and len(node_results)==64, 'Native audit counts')
    unsafe_locations = {(p['grid'], p['label']) for p in unsafe_quadrants}
    require(all((p['grid'], p['label']) in unsafe_locations for p in phase_mismatches),
            'Every observed quadrant disagreement must be near an axis or zero.')
    inputs=[BASE/'zero_index_analysis.py',BASE/'proof-notes.md',Path(__file__),starts_path,paths_path,old_path,
            REPO/'Graphics/ZetaZeroIndexExperiment.cs',REPO/'Graphics/ZetaSwitchExperiment.cs',REPO/'Graphics/Program.cs',
            args.grids,args.native_bin/'Graphics.exe',args.native_bin/'Graphics.dll',args.native_bin/'Graphics.runtimeconfig.json']
    report=dict(schema='graph-zeta-zero-index-independent-review-v1',traceId='graph.riemann.zero_index.independent_math_grid_review',
        status='passed',reviewedAtUtc=datetime.now(timezone.utc).isoformat(),
        runtime=dict(python=sys.version,executable=sys.executable,mpmath=mp.__version__,mathDigits=75,nativeReferenceDigits=50),
        coverage=dict(initialZeroIndices=100,independentDerivativeChecks=100,hardyPhaseChecks=100,
                      paths=31,pathPoints=points_checked,independentHalfStepSolves=31,
                      nativeGrids=32,finiteBinaryNodes=total_nodes,highPrecisionAuditPoints=160,highPrecisionInteriorBinaryNodes=64),
        startingSlopes=dict(summary=summary,historicalFirstThree=old_comparison,
            maxZeroCoordinateDifference=dec(zero_error),maxDerivativeDifference=dec(derivative_error),
            maxVelocityDifference=dec(velocity_error),maxSlopeDifference=dec(slope_error),
            maxHardyPhaseSlopeDifference=dec(hardy_error),maxReevaluatedSavedSeedResidual=dec(initial_residual)),
        continuation=dict(maxReevaluatedSavedPointResidual=dec(path_residual),maxDerivativeDifference=dec(path_d_error),
            maxVelocityDifference=dec(path_v_error),maxSlopeDifference=dec(path_slope_error),maxStepDistance=dec(max_step),
            maxPredictorCorrection=dec(max_correction),maxFullStartingSecantError=dec(max_full_secant_error),
            maxHalfStartingSecantError=dec(max_half_secant_error),outsideLocalViewport=outside,stepComparisons=path_details),
        native=dict(absoluteErrorLimit='1e-10',scaledErrorLimit='1e-10',
            max192TermAbsoluteError=dec(max_native),max192TermScaledError=dec(max_native_scaled),
            max256TermAbsoluteError=dec(max_refined),max192vs256Difference=dec(max_refinement),
            max192vs256ScaledDifference=dec(max_refinement_scaled),maxBinaryInteriorAbsoluteError=dec(max_node),
            phaseSensitivityThreshold='1e-10',auditPointsNearAnAxis=unsafe_quadrants,
            observedQuadrantDisagreements=phase_mismatches,
            auditSamples=audit_results,binaryNodeSamples=node_results),
        inputs=[dict(path=str(p.resolve()),sha256=sha(p)) for p in inputs],grids=binary_bindings,
        elapsedSeconds=time.perf_counter()-started,
        limitations=['Finite numerical comparisons, not interval bounds, a certified branch tube, or an RH proof.',
                    'The label prime describes the zero ordinal j; it does not classify the noninteger zero height.',
                    'The a=0 seeds lie at sigma=0.5; paths at positive a are zeros of zeta(s)-a, not counterexamples to RH.',
                    'Saved coordinates have 48 significant digits; their recomputed residuals need not equal the producer residuals at 50 digits.',
                    'Every binary node is scanned for finiteness. Layout metadata, lengths, and selected coordinates are checked; high-precision accuracy is checked at 224 points, not every grid node.',
                    '192/256agreement does not constitute an error enclosure. Colors near zeros or axes remain sensitive.',
                    'PNG dimensions/hashes and declared orientation are checked; this review does not verify every rendered pixel or movie frame.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',coverage=report['coverage'],nativeMaximumError=dec(max_native),
                         pathMaximumResidual=dec(path_residual),report=str(args.output)),indent=2),flush=True)


if __name__ == '__main__':
    main()
