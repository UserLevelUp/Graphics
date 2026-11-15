"""Verify raw evidence and LF-normalized source hashes (not mathematical truth)."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

# defines: graph.riemann.switch.integrity
ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
MANIFEST = BASE / 'evidence/manifest.json'


def digest(path, mode='raw'):
    data = path.read_bytes()
    if mode == 'text-lf':
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def hash_mode(path):
    relative = path.relative_to(ROOT)
    if relative.parts[0] in ('Graphics', 'warps') or path.parent == ROOT or path.parent == ROOT / '.recur' or path.parent == BASE:
        return 'text-lf'
    return 'raw'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true', help='Explicitly generate a new manifest before acceptance')
    args = parser.parse_args()
    if args.seal:
        files = set(p for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                    and p != MANIFEST and p.suffix != '.pyc')
        files.update(p for p in (ROOT / 'Graphics').rglob('*') if p.is_file()
                     and not {'bin', 'obj'}.intersection(p.parts) and p.suffix in ('.cs', '.csproj', '.resx'))
        files.update(p for p in (ROOT / 'warps').glob('graph.riemann.switch.*')
                     if p.is_file() and not p.name.endswith('.warp-layer.json'))
        files.update(ROOT / p for p in ('.gitattributes', '.gitignore', '.recur/config.toml'))
        rows = [{'path': p.relative_to(ROOT).as_posix(), 'sha256': digest(p, hash_mode(p)),
                 'hashMode': hash_mode(p), 'bytesAtSeal': p.stat().st_size}
                for p in sorted(files)]
        value = {'schema': 'graph-zeta-switch-manifest-v1', 'traceId': 'graph.riemann.switch.integrity',
                 'createdUtc': datetime.now(timezone.utc).isoformat(), 'baseline': 'cf51254',
                 'scope': 'Accepted finite experiment source and evidence at this Git checkpoint; not a proof certificate.',
                 'hashRules': 'text-lf replaces CRLF with LF before hashing source; raw retains exact runtime/evidence bytes.',
                 'files': rows}
        MANIFEST.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    failures = []
    for row in manifest['files']:
        path = (ROOT / row['path']).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or digest(path, row['hashMode']) != row['sha256']:
            failures.append(row['path'])
    for name in ('independent-validation.json', 'native-validation.json'):
        report = json.loads((BASE / 'evidence' / name).read_text())
        if report['status'] != 'passed': failures.append(name + ': status')
        for export in report['exports']:
            path = Path(export['source'])
            # Relocate this repository's exported evidence when restoring on another machine.
            path = BASE / 'evidence' / path.name
            if digest(path) != export['sourceSha256']: failures.append(name + ': ' + path.name)
    result = {'status': 'passed' if not failures else 'failed', 'files': len(manifest['files']),
              'manifestSha256': digest(MANIFEST), 'failures': failures,
              'limit': 'Byte integrity and recorded export bindings only; rerun numerical checks for fresh validation.'}
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
