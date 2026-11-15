"""Seal or verify the conclusion delivery; byte integrity is not a proof certificate."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EXCLUDED = {'delivery-manifest.json', 'acceptance.json', 'warp-progress.json',
            'package-receipt.json', 'delivery-receipt.json'}

def digest(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()

def rows(paths, root):
    return [dict(path=p.relative_to(root).as_posix(), sha256=digest(p), bytes=p.stat().st_size)
            for p in sorted(paths)]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    manifest = BASE / 'evidence/delivery-manifest.json'
    if args.seal:
        if manifest.exists():
            parser.error('Preserve the existing seal; assess any change before making a new version.')
        qa = json.loads((BASE / 'evidence/media-qa.json').read_text(encoding='utf-8'))
        review = json.loads((BASE / 'review/render-review.json').read_text(encoding='utf-8'))
        assert qa['status'] == 'passed' and review['status'] == 'passed'
        assert digest(output / 'presentation-with-conclusion.mp4') == qa['videoSha256']
        assert digest(output / 'formal-conclusion.mp4') == review['input']['sha256']
        files = [p for p in BASE.rglob('*') if p.is_file()
                 and not any(part in ('.recur', '__pycache__', 'warps') for part in p.relative_to(BASE).parts)
                 and p.name not in EXCLUDED and p.suffix != '.pyc']
        media = [p for p in output.rglob('*') if p.is_file() and p.name not in EXCLUDED]
        value = dict(schema='graph-conclusion-delivery-manifest-v1',
                     traceId='graph.riemann.conclusion.integrity',
                     createdUtc=datetime.now(timezone.utc).isoformat(),
                     files=rows(files, ROOT), media=rows(media, output),
                     exclusions='Private Recur state, Warp publication layers, manifest itself and subsequent acceptance/packaging receipts.',
                     limit='Integrity of source, reviewed evidence and finite-experiment media; not a mathematical certificate.')
        manifest.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        (output / 'delivery-manifest.json').write_bytes(manifest.read_bytes())
    value = json.loads(manifest.read_text(encoding='utf-8'))
    failures = []
    for label, root, records in [('source', ROOT, value['files']), ('media', output, value['media'])]:
        for row in records:
            path = (root / row['path']).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path) != row['sha256']:
                failures.append(label + ':' + row['path'])
    assert (output / 'delivery-manifest.json').read_bytes() == manifest.read_bytes()
    result = dict(status='failed' if failures else 'passed', files=len(value['files']),
                  media=len(value['media']), manifestSha256=digest(manifest), failures=failures)
    print(json.dumps(result, indent=2))
    return bool(failures)

if __name__ == '__main__':
    raise SystemExit(main())
