"""Check actual native exports against the Python quadrant function and pixels.

Requires Pillow for PNG checks; candidate math itself is standard-library only.
defines: graph.primes.quadrant_phase.native_validation
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from PIL import Image
from phase_test import phase_test

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--rotated', type=Path, required=True)
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    paths = [args.main, args.rotated] + sorted(args.controls.glob('candidate-*.json'))
    assert len(paths) == 7
    records, pixels, sectors = 0, 0, 0
    results = []
    for path in paths:
        payload = json.loads(path.read_text(encoding='utf-8-sig'))
        assert payload['schema'] == 'graph-prime-quadrant-phase-v1'
        assert payload['verification']['status'] == 'passed'
        assert (payload['verification']['lower'],payload['verification']['upper']) == (0,2000)
        assert payload['verification']['primeCount'] == 303
        assert [row['n'] for row in payload['rows']] == list(range(101))
        rotation = payload['selected']['displayRotationDegrees']
        for row in [payload['selected']] + payload['rows'] + payload['controls']:
            expected = phase_test(row['n'])
            for field in ('factorialMod','residue','x','y','quadrant','indicator','classification','multiplications'):
                assert row[field] == expected[field], (path.name,row['n'],field)
            assert row['phaseDegrees'] == expected['angleDegrees']
            assert row['displayRotationDegrees'] == rotation
            if expected['defined']:
                assert row['displayPhaseDegrees'] == (expected['angleDegrees']+rotation)%360
                assert row['boundaryMarginDegrees'] == 45
            else:
                assert row['displayPhaseDegrees'] is None
            records += 1
        palette = {p['quadrant']:tuple(p['rgb']) for p in payload['palette']}
        palette[None] = tuple(payload['render']['neutralRgb'])
        image = Image.open(path.with_suffix('.png')).convert('RGB')
        assert image.size == (1920,1080)
        grid = payload['render']['grid']
        for row in payload['rows']:
            n = row['n']
            x = grid['x'] + n % grid['columns'] * grid['stepX'] + 3
            y = grid['y'] + n // grid['columns'] * grid['stepY'] + 3
            assert image.getpixel((x,y)) == palette[row['quadrant']], (path.name,n)
            pixels += 1
        # Interior sector samples avoid text, axes, outlines and candidate rays.
        for q in range(1,5):
            angle = math.radians(rotation + 60 + 90*(q-1))
            xy = round(490+65*math.cos(angle)), round(665-65*math.sin(angle))
            actual = image.getpixel(xy)
            expected = tuple((85*c+170*b)//255 for c,b in zip(palette[q],(24,32,49)))
            assert all(abs(a-b)<=1 for a,b in zip(actual,expected)), (path.name,q,actual,expected)
            sectors += 1
        results.append(dict(path=str(path.resolve()),sha256=sha(path),
                            pngSha256=sha(path.with_suffix('.png')),
                            candidate=payload['selected']['n'],rotation=rotation))
    assert {r['candidate'] for r in results} == {0,4,96,97,99991,100000}
    assert results[1]['rotation'] == 37
    files = [BASE/'phase_test.py', Path(__file__), BASE/'evidence/validation.json',
             BASE/'evidence/build.log', REPO/'Graphics/Program.cs',
             REPO/'Graphics/PrimeQuadrantPhaseExperiment.cs', REPO/'Graphics/PrimeQuadrantPhaseForm.cs',
             REPO/'Graphics/bin/Release/net5.0-windows/Graphics.exe',
             REPO/'Graphics/bin/Release/net5.0-windows/Graphics.dll']
    report = dict(traceId='graph.primes.quadrant_phase.native_validation',status='passed',
        createdUtc=datetime.now(timezone.utc).isoformat(),
        coverage=dict(nativeExports=len(paths),comparedRecords=records,
                      exactTileColors=pixels,rotatedSectorColors=sectors,
                      internalSieveRange=[0,2000]),
        inputs=[dict(path=str(p.resolve()),sha256=sha(p)) for p in files],
        exports=results,
        runtime='Release net5.0-windows build; DOTNET_ROLL_FORWARD=Major on installed newer Windows Desktop runtime.',
        limits=['Finite checks supplement the global theorem.',
                'Pixel checks verify this rendering, not an independent optical primality theorem.',
                'Interactive form controls are checked separately through UI observation.'])
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'native-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],coverage=report['coverage']),indent=2))


if __name__ == '__main__':
    main()
