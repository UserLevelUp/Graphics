"""Seal/verify this presentation revision's source and media byte integrity."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EXCLUDE={'delivery-manifest.json','acceptance.json','warp-progress.json','delivery-receipt.json'}
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def collect(root,paths):
    return [dict(path=p.relative_to(root).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(paths)]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--seal',action='store_true');a=p.parse_args();out=a.output.resolve()
    manifest=BASE/'evidence/delivery-manifest.json'
    if a.seal:
        assert not manifest.exists(),'Preserve existing seals; assess changes before resealing.'
        for name in ['media-qa.json','render-review.json']:
            report=json.loads((BASE/'evidence'/name).read_text(encoding='utf-8'));assert report['status']=='passed',(name,report['status'])
        files=[x for x in BASE.rglob('*') if x.is_file() and x.name not in EXCLUDE and not any(v in ('.recur','warps','__pycache__') for v in x.relative_to(BASE).parts)]
        media=[x for x in out.rglob('*') if x.is_file() and x.name not in EXCLUDE]
        value=dict(schema='graph-origin-trail-manifest-v1',traceId='graph.riemann.origin_trail.integrity',createdUtc=datetime.now(timezone.utc).isoformat(),files=collect(ROOT,files),media=collect(out,media),exclusions='Manifest itself, later acceptance/receipt/status records, private configuration and Warp publication layers.',limit='Byte integrity of rendering and media evidence; no new mathematical certificate.')
        manifest.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');(out/'delivery-manifest.json').write_bytes(manifest.read_bytes())
    value=json.loads(manifest.read_text(encoding='utf-8'));failures=[]
    for label,root,rows in [('source',ROOT,value['files']),('media',out,value['media'])]:
        for row in rows:
            f=(root/row['path']).resolve()
            if not f.is_relative_to(root.resolve()) or not f.is_file() or sha(f)!=row['sha256']:failures.append(label+':'+row['path'])
    assert manifest.read_bytes()==(out/'delivery-manifest.json').read_bytes()
    print(json.dumps(dict(status='failed' if failures else 'passed',files=len(value['files']),media=len(value['media']),manifestSha256=sha(manifest),failures=failures),indent=2));return bool(failures)
if __name__=='__main__':raise SystemExit(main())
