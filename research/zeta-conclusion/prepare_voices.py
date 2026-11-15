"""Download authorized narration outputs and fit them without truncating words."""
import argparse
import hashlib
import json
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import imageio_ffmpeg

p=argparse.ArgumentParser()
p.add_argument('--jobs', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--work', type=Path, required=True)
args=p.parse_args()
base=Path(__file__).resolve().parent
jobs=json.loads(args.jobs.read_text(encoding='utf-8'))
story=json.loads((base/'formulation/closing-scenes.json').read_text(encoding='utf-8'))
repo=json.loads((base/'repository-narration.json').read_text(encoding='utf-8'))
extra=base/'formulation/prime-connection.json'
extra_scenes=[json.loads(extra.read_text(encoding='utf-8'))] if extra.exists() else []
expected={s['id']:s['narration'] for s in story['scenes']+extra_scenes+[repo]}
delta=json.loads((base/'formulation/public-language.json').read_text(encoding='utf-8'))['changes']
expected['formal_object']=delta['narration']
expected['origin_public']=delta['originalOriginReplacement']['narration']
ff=imageio_ffmpeg.get_ffmpeg_exe()
destroot=args.output/'assets/voice';destroot.mkdir(exist_ok=True,parents=True)
raw=args.work/'raw-voices';raw.mkdir(exist_ok=True,parents=True)
def one(j):
    assert j['prompt']==expected[j['id']],j['id']
    src=raw/(j['id']+'.mp3');urllib.request.urlretrieve(j['url'],src)
    duration=j['durationSeconds']; rate=max(1,duration/(j['sceneDuration']-.95))
    assert rate<=1.2,(j['id'],rate)
    dst=destroot/(j['id']+'.mp3')
    subprocess.run([ff,'-v','error','-y','-i',str(src),'-af',f'atempo={rate:.9f}','-c:a','libmp3lame','-q:a','2',str(dst)],check=True)
    subprocess.run([ff,'-v','error','-i',str(dst),'-f','null','-'],check=True)
    return dict(id=j['id'],taskId=j['taskId'],voice='Serene',prompt=j['prompt'],sourceDurationSeconds=duration,tempoFactor=rate,expectedOutputDurationSeconds=duration/rate,sceneDurationSeconds=j['sceneDuration'],sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),sourceSha256=hashlib.sha256(src.read_bytes()).hexdigest(),audioDecodePassed=True)
rows=list(ThreadPoolExecutor(max_workers=3).map(one,jobs))
report=dict(traceId='graph.riemann.conclusion.voice',status='passed',allPromptsMatchFinalNarration=True,processing='Pitch-preserving tempo adjustment where needed; no truncated narration.',clips=rows)
(base/'evidence/voice-production.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'passed','clips':[{k:v for k,v in r.items() if k not in ('prompt',)} for r in rows]},indent=2))
