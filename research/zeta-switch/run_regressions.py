"""Re-export scoped legacy CLI routes and compare accepted pixels/stable data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

from PIL import Image, ImageChops


BASE = Path(__file__).resolve().parent
PROJECT = BASE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-root', type=Path, required=True)
    parser.add_argument('--legacy-output-root', type=Path, required=True)
    args = parser.parse_args()
    work = args.work_root.resolve() / ('switch-regression-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6])
    work.mkdir(parents=True)
    dll = PROJECT / 'Graphics/bin/Release/net5.0-windows/Graphics.dll'
    baseline = PROJECT / 'research/zero-motion/evidence'
    prime = PROJECT / 'research/prime-phase/evidence/render'
    cases = [
        ('zero-before', '--zero-motion', baseline / 'zero-before.png', ['0.5', '0'], ['.values.json', '.txt']),
        ('zero-collision', '--zero-motion', baseline / 'zero-collision.png', ['0', '0'], ['.values.json', '.txt']),
        ('zero-after', '--zero-motion', baseline / 'zero-after.png', ['-0.5', '0'], ['.values.json', '.txt']),
        ('zero-rotated', '--zero-motion', baseline / 'zero-rotated.png', ['0.5', '22.5'], ['.values.json', '.txt']),
        ('zero-path', '--zero-path', baseline / 'zero-path.png', ['0.5', '-1.6', '0.7', '1.6', '0.7', '0'], ['.json', '.path.json', '.values.json', '.path.txt', '.txt']),
        ('prime-color-loom', '--prime-phase', prime / 'prime-color-loom.png', [], ['.values.json', '.txt']),
        ('prime-color-overlay', '--prime-phase', prime / 'prime-color-overlay.png', ['1.2', '512', '0', '13', 'false', 'true'], ['.values.json', '.txt']),
        ('prime-unwrapped', '--prime-unwrap', prime / 'prime-unwrapped.png', [], ['.json', '.txt']),
        ('zeta-overwrite', '--zeta-preview', args.legacy_output_root / 'zeta-overwrite.png', [], []),
        ('zeta-contours', '--zeta-contours', args.legacy_output_root / 'zeta-contours.png', [], []),
        ('zeta-origins', '--zeta-origins', args.legacy_output_root / 'zeta-origins.png', [], []),
    ]
    env = dict(os.environ, DOTNET_ROLL_FORWARD='Major')
    results = []
    for name, flag, accepted, arguments, sidecars in cases:
        output = work / (name + '.png')
        target = output.with_suffix('.json') if flag == '--zero-path' else output
        command = ['dotnet', str(dll), flag, str(target), *arguments]
        run = subprocess.run(command, cwd=PROJECT, env=env, capture_output=True, timeout=120)
        record = {'name': name, 'command': command, 'returnCode': run.returncode,
                  'acceptedImage': str(accepted), 'outputImage': str(output), 'dataComparisons': []}
        (work / (name + '.stdout.txt')).write_bytes(run.stdout)
        (work / (name + '.stderr.txt')).write_bytes(run.stderr)
        try:
            if run.returncode:
                raise RuntimeError(f'CLI exit {run.returncode}: ' + run.stderr.decode('utf-8', errors='replace')[:500])
            with Image.open(accepted) as a, Image.open(output) as b:
                a = a.convert('RGB')
                b = b.convert('RGB')
                same = a.size == b.size and a.tobytes() == b.tobytes()
                record['dimensions'] = list(a.size)
                record['pixelsIdentical'] = same
                record['pixelDifferenceBounds'] = None if same or a.size != b.size else ImageChops.difference(a, b).getbbox()
            record['acceptedSha256'] = sha(accepted)
            record['outputSha256'] = sha(output)
            record['bytesIdentical'] = record['acceptedSha256'] == record['outputSha256']
            for suffix in sidecars:
                expected = accepted.with_suffix(suffix)
                actual = output.with_suffix(suffix)
                old, new = expected.read_text(encoding='utf-8-sig'), actual.read_text(encoding='utf-8-sig')
                if suffix.endswith('.json'):
                    matched = json.loads(old) == json.loads(new)
                    comparison = 'parsed JSON; no fields removed'
                else:
                    # Prime reports contain a run-duration sentence; other report text is stable.
                    normalize = lambda text: re.sub(r'\b\d+ ms including drawing\b', '<elapsed> ms including drawing', text)
                    matched = normalize(old) == normalize(new)
                    comparison = 'text; only drawing elapsed milliseconds normalized'
                record['dataComparisons'].append({'suffix': suffix, 'identical': matched,
                    'comparison': comparison, 'acceptedSha256': sha(expected), 'outputSha256': sha(actual)})
            record['passed'] = same and all(item['identical'] for item in record['dataComparisons'])
        except Exception as error:
            record['passed'] = False
            record['error'] = str(error)
        results.append(record)
        print(json.dumps({'case': name, 'passed': record['passed'], 'pixelsIdentical': record.get('pixelsIdentical')}), flush=True)
    evidence = {'traceId': 'graph.riemann.switch.regression',
                'status': 'passed' if all(r['passed'] for r in results) else 'failed',
                'createdUtc': datetime.now(timezone.utc).isoformat(), 'workDirectory': str(work),
                'executable': str(dll), 'executableSha256': sha(dll), 'cases': results,
                'scope': 'Legacy CLI route compatibility; these comparisons do not validate the new zeta mathematics.'}
    destination = BASE / 'evidence/regression.json'
    destination.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'status': evidence['status'], 'cases': len(results), 'evidence': str(destination)}))
    return 0 if evidence['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
