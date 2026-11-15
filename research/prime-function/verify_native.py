"""Bind native outputs to source/binary hashes and check their exact data and grid."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from PIL import Image
from prime_function import trial,wilson

BASE=Path(__file__).resolve().parent
REPO=BASE.parents[1]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main',type=Path,required=True)
    parser.add_argument('--controls',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    files=[args.main]+[args.controls/f'candidate-{n}.json' for n in (0,4,96,100001,2147483647)]
    checks=[]
    for file in files:
        data=json.loads(file.read_text(encoding='utf-8'))
        assert data['verification']['status']=='passed'
        assert data['verification']['trialRange']==dict(lower=0,upper=100000,integers=100001,primeCount=9592)
        assert data['verification']['wilsonRange']==dict(lower=0,upper=2000,integers=2001)
        assert [r['n'] for r in data['rows']]==list(range(101))
        records=data['rows']+data['examples']+[data['selected']]
        for row in records:
            n=row['n'];reference=trial(n)
            assert row['indicator']==reference['indicator'] and row['classification']==reference['classification'],n
            assert row['trialDivisor']==reference['divisor'],n
            if 2<=n<=100000:
                expected=wilson(n);actual=row['wilson']
                assert actual['available']
                for key in ('indicator','factorialMod','residue','multiplications'):
                    assert actual[key]==expected[key],(n,key)
                assert abs(actual['phaseDegrees']-expected['phaseDegrees'])<1e-10
            else:assert not row['wilson']['available']
        checks.append(dict(path=str(file),sha256=sha(file),selected=data['selected']['n'],recordsChecked=len(records),status='passed'))
    data=json.loads(args.main.read_text(encoding='utf-8'))
    png=args.main.with_suffix('.png')
    palette={'prime':(176,117,228),'composite':(55,69,92),'neither':(82,85,95)}
    with Image.open(png) as image:
        assert image.size==(1920,1080)
        rgb=image.convert('RGB')
        for row in data['rows']:
            n=row['n'];pixel=rgb.getpixel((65+n%11*75+3,666+n//11*29+3))
            assert pixel==palette[row['classification']],(n,pixel)
    inputs=[REPO/'Graphics/Program.cs',REPO/'Graphics/PrimalityFunctionExperiment.cs',
            REPO/'Graphics/bin/Release/net5.0-windows/Graphics.exe',REPO/'Graphics/bin/Release/net5.0-windows/Graphics.dll',
            BASE/'prime_function.py',Path(__file__),BASE/'evidence/build.log']
    report=dict(traceId='graph.primes.function.native.validation',status='passed',createdUtc=datetime.now(timezone.utc).isoformat(),
        sourceAndBinaryInputs=[dict(path=str(p.relative_to(REPO)).replace('\\','/'),sha256=sha(p)) for p in inputs],
        exports=checks,render=dict(path=str(png),sha256=sha(png),size=[1920,1080],exactTileColorsChecked=101),
        runtime=dict(rollForward='Major',reason='Project targets net5.0-windows; installed compatible runtime selected using the existing project convention.'),
        recovery=['Initial Release build was blocked by the old Graphics process14784; its exact repository executable path was verified before termination under prior authorization.',
                  'Initial apphost launch without runtime roll-forward produced no export; task-owned process31328 was stopped. The final export and five controls passed with DOTNET_ROLL_FORWARD=Major.'],
        limits=['Native trial checks every integer divisor; Python skips even divisors after2, so trial operation counts intentionally differ.',
                'Tile fills are checked by indexed pixel samples; glyphs/layout need separate visual inspection.',
                'Exact mathematical claims derive from the theorem, not pixels or finite tests.'])
    (args.output/'native-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',nativeExports=len(checks),tileColorsChecked=101,selectedInputs=[r['selected'] for r in checks]),indent=2))

if __name__=='__main__':main()
