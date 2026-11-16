"""Package the reviewed explanation, reusable certificate and media receipts.

defines: graph.riemann.collision_guide.delivery
consumer: graph.riemann.collision_guide.explanation_review
consumer: graph.riemann.collision_guide.media_review
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

BASE=Path(__file__).resolve().parent
REPO=BASE.parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args();out=args.output
    kit=args.work/'toolkit'
    kit.mkdir(parents=True,exist_ok=True)
    required=[BASE/'script.json',BASE/'guide.md',BASE/'use_certificate.py',
              REPO/'research/gap-bound/verify_bound.py',
              REPO/'research/gap-bound/interaction-bound-proof.md',
              REPO/'research/collision-proof/exact-quartic-proof.md',
              BASE/'evidence/use-example.json',BASE/'evidence/discovery-provenance.json',
              BASE/'evidence/explanation-review.json',BASE/'evidence/media-review.json']
    historical=['warps/graph.riemann.collision.next.current.md',
                'research/gap-bound/graph.riemann.gap.contract.current.md',
                'research/gap-bound/carbon/review.md',
                'warps/graph.riemann.gap.results.complete.md',
                'warps/graph.riemann.gap.next.current.md']
    required.extend(REPO/p for p in historical)
    for source in required:
        destination=kit/source.relative_to(REPO)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
    for source in (BASE/'script.json',BASE/'evidence/explanation-review.json',
                   BASE/'evidence/media-review.json',BASE/'evidence/discovery-provenance.json',
                   REPO/'research/gap-bound/interaction-bound-proof.md',
                   REPO/'research/collision-proof/exact-quartic-proof.md'):
        shutil.copyfile(source,out/source.name)
    guide=(BASE/'guide.md').read_text(encoding='utf-8')
    guide=guide.replace('../gap-bound/interaction-bound-proof.md','interaction-bound-proof.md').replace('../collision-proof/exact-quartic-proof.md','exact-quartic-proof.md')
    guide=guide.replace('](evidence/discovery-provenance.json)','](discovery-provenance.json)')
    checkpoint=json.loads((out/'repository.json').read_text())['head']
    for relative in historical:
        original=('../'+relative.removeprefix('research/')) if relative.startswith('research/') else '../../'+relative
        guide=guide.replace(']('+original+')','](https://github.com/UserLevelUp/Graphics/blob/'+checkpoint+'/'+relative+')')
    (out/'guide.md').write_text(guide,encoding='utf-8')
    for path in (out/'guide.md',kit/'research/collision-guide/guide.md'):
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if not link.startswith(('https://','http://','#')):
                assert (path.parent/link).exists(),(path,link)
    quickstart='''# Reproduce the finite-polynomial certificate

Requires Python 3.11 or later, using only the standard library. Run from this extracted folder:

```powershell
python -B research/collision-guide/use_certificate.py --roots=-3,-1,1,3 --duration=17/32 --output example.json
```

The interval status should be `certified`; the exact point check should report four distinct real roots and gcd degree zero. Use duration `3/5` to see an uncertified interval endpoint that nevertheless still has four simple real roots. `2/3` is an exact double-root collision in this example, and `7/10` has no real roots.

Read research/collision-guide/guide.md for the assumptions, derivation, discovery history, applications and RH connection. The finite-degree theorem does not establish an infinite-system theorem or a new prime algorithm; novelty has not been established. JSON evidence records the specific cases and source hashes reviewed, rather than certifying every possible input.

The full public project and historical trace sources are at https://github.com/UserLevelUp/Graphics on branch graph/riemann-continuation. Historical source paths in receipts refer to that repository. This compact kit includes the checker and proofs needed for the example, not every historical record or media file.
'''
    (kit/'START_HERE.md').write_text(quickstart,encoding='utf-8')
    result=subprocess.run([sys.executable,'-B','research/collision-guide/use_certificate.py','--roots=-3,-1,1,3','--duration=17/32'],cwd=kit,capture_output=True,text=True,check=True)
    example=json.loads(result.stdout)
    assert example['guaranteedInterval']['status']=='certified'
    counts=example['exactPointCheck']['counts']
    assert counts['distinctRealRoots']==4 and counts['gcdDegreeWithDerivative']==0
    (out/'portable-example.json').write_text(json.dumps(example,indent=2)+'\n',encoding='utf-8')
    archive=out/'collision-certificate-toolkit.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(kit.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(kit).as_posix())
    cm=json.loads((out/'chapter-manifest.json').read_text())
    fm=json.loads((out/'focused-manifest.json').read_text())
    def timestamp(seconds):
        whole=int(seconds);return f'{whole//60:02}:{whole%60:02}'
    readme='''# A guarantee before real polynomial roots collide

Watch [the focused explanation](finite-root-collision-guide.mp4), or [the full presentation with the new chapter](presentation-with-collision-guide.mp4). Both include narration, selectable English captions and a final repository card. The earlier exports remain unchanged.

The new chapter explains the proved finite-polynomial bound, its documented development, a worked exact-arithmetic example, practical uses and its connection to the heat-flow formulation of the Riemann Hypothesis. No RH advance, new prime-identification method or mathematical novelty is claimed.

Read [the detailed guide](guide.md), [the full proof](interaction-bound-proof.md) and [the exact quartic calibration](exact-quartic-proof.md). Download [the runnable toolkit](collision-certificate-toolkit.zip) to reproduce the example with Python's standard library.

## Focused-video chapters

'''
    for scene in cm['scenes']:
        readme+=f'- {timestamp(scene["startFrame"]/24)} — {scene["title"]}\n'
    readme+=f'- {timestamp(cm["durationSeconds"])} — Public code and reproduction\n'
    readme+='''
## Evidence and scope

[Explanation review](explanation-review.json) records independent exact arithmetic checks at 100 times across 25 initial configurations, the worked example and narrative review. [Media review](media-review.json) records full decoding, frame, audio and caption checks. [Discovery provenance](discovery-provenance.json) ties the history to commits, trace inventories and hashed sources. Trace IDs and Eventness organize those records; they do not substitute for proof.

The chapter is rendered at 1280×720 and upscaled in the 1920×1080 exports. Captions follow complete narration clips; sentence timing is estimated by word count rather than forced alignment. Animation is illustrative. The all-interval result comes from the proof, while exact root counts test selected times.

Public source: https://github.com/UserLevelUp/Graphics, branch `graph/riemann-continuation`. The closing card displays the source checkpoint used before export; later delivery commits add the completed evidence. Prior work is cited in the guide and narration script.
'''
    (out/'START_HERE.md').write_text(readme,encoding='utf-8')
    targets=['finite-root-collision-guide.mp4','presentation-with-collision-guide.mp4','guide.md',
             'collision-certificate-toolkit.zip','START_HERE.md','explanation-review.json','media-review.json',
             'discovery-provenance.json','focused-captions.srt','presentation-captions.srt']
    manifest=dict(traceId='graph.riemann.collision_guide.delivery',createdAtUtc=datetime.now(timezone.utc).isoformat(),
        portableExample=dict(status='passed',python=sys.version,workingDirectory=str(kit),report='portable-example.json'),
        focusedDurationSeconds=fm['video']['durationSeconds'],
        files=[dict(path=name,sha256=sha(out/name),bytes=(out/name).stat().st_size) for name in targets])
    (out/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='packaged',files=len(targets),archive=str(archive)),indent=2))


if __name__=='__main__':main()
