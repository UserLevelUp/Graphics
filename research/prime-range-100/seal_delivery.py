"""Seal and verify finite-proof source and media byte integrity."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EXCLUDE = {'delivery-manifest.json', 'acceptance.json', 'warp-progress.json', 'delivery-receipt.json'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def collect(root, paths):
    return [dict(path=p.relative_to(root).as_posix(), sha256=sha(p), bytes=p.stat().st_size)
            for p in sorted(paths)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    manifest = BASE / 'evidence/delivery-manifest.json'
    if args.seal:
        assert not manifest.exists(), 'Preserve existing seals; assess changes before resealing.'
        for name in ('validation.json', 'review.json', 'content-review.json', 'media-qa.json', 'render-review.json'):
            report = json.loads((BASE / 'evidence' / name).read_text(encoding='utf-8'))
            assert report['status'] == 'passed', (name, report['status'])
        sources = [p for p in BASE.rglob('*') if p.is_file() and p.name not in EXCLUDE
                   and not any(v in ('.recur', 'warps', '__pycache__') for v in p.relative_to(BASE).parts)]
        media = [p for p in out.rglob('*') if p.is_file() and p.name not in EXCLUDE
                 and '__pycache__' not in p.relative_to(out).parts]
        value = dict(schema='graph-prime-range100-manifest-v1', traceId='graph.primes.range100.integrity',
                     createdUtc=datetime.now(timezone.utc).isoformat(), files=collect(ROOT, sources),
                     media=collect(out, media),
                     exclusions='Manifest itself, later acceptance/receipt/status records, private configuration, Warp publication layers and bytecode caches.',
                     limit='Byte integrity. Mathematical claims are limited to the separately reviewed finite integer proof and model f(z)=z.')
        manifest.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        (out / 'delivery-manifest.json').write_bytes(manifest.read_bytes())
    value = json.loads(manifest.read_text(encoding='utf-8'))
    failures = []
    for label, root, rows in (('source', ROOT, value['files']), ('media', out, value['media'])):
        for row in rows:
            path = (root / row['path']).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file() or sha(path) != row['sha256']:
                failures.append(label + ':' + row['path'])
    assert manifest.read_bytes() == (out / 'delivery-manifest.json').read_bytes()
    print(json.dumps(dict(status='failed' if failures else 'passed', files=len(value['files']),
                         media=len(value['media']), manifestSha256=sha(manifest), failures=failures), indent=2))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
