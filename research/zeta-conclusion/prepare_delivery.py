"""Prepare the reviewed closing section and native After Effects launcher."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import imageio_ffmpeg

p=argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
p.add_argument('--work', type=Path, required=True)
args=p.parse_args()
base=Path(__file__).resolve().parent
story=json.loads((base/'formulation/closing-scenes.json').read_text(encoding='utf-8'))
review=json.loads((base/'review/final-content-review.json').read_text(encoding='utf-8'))
assert review['status']=='passed'
for item in review['inputs']:
    reviewed_file=base.parents[1]/item['path']
    assert hashlib.sha256(reviewed_file.read_bytes()).hexdigest()==item['sha256'], item['path']
prime_path=base/'formulation/prime-connection.json'
prime_review=json.loads((base/'review/prime-connection-review.json').read_text(encoding='utf-8'))
assert prime_review['status']=='passed'
assert hashlib.sha256(prime_path.read_bytes()).hexdigest()==prime_review['sha256']
prime=json.loads(prime_path.read_text(encoding='utf-8'))
public_path=base/'formulation/public-language.json'
public_review=json.loads((base/'review/public-language-review.json').read_text(encoding='utf-8'))
assert public_review['status']=='passed'
assert hashlib.sha256(public_path.read_bytes()).hexdigest()==public_review['sha256']
public=json.loads(public_path.read_text(encoding='utf-8'))
target=next(s for s in story['scenes'] if s['id']==public['targetSceneId'])
target['narration']=public['changes']['narration']
for replacement in public['changes']['bulletReplacements']:
    if replacement['index']==len(target['bullets']): target['bullets'].append(replacement['text'])
    else: target['bullets'][replacement['index']]=replacement['text']
story['scenes'].append(prime)
story['append']['repositoryStartSeconds']=102
story['append']['durationSeconds']=114
story['append']['newTotalSeconds']=252
contract=json.loads((base/'graph.riemann.conclusion.contract.current.json').read_text(encoding='utf-8'))
original=Path(contract['originalVideo'])
assert hashlib.sha256(original.read_bytes()).hexdigest()==contract['originalVideoSha256']
args.output.mkdir(exist_ok=True,parents=True)
args.work.mkdir(exist_ok=True,parents=True)
(args.output/'assets').mkdir(exist_ok=True)
copied=args.output/'assets/original-presentation.mp4'
shutil.copy2(original,copied)
prefix_audio=args.output/'assets/public-prefix.wav'
origin_voice=args.output/'assets/voice/origin_public.mp3'
audio_filter='[0:a]asplit=2[oa][ob];[oa]atrim=start=0:end=14,asetpts=PTS-STARTPTS[a0];[1:a]adelay=150:all=1,apad,atrim=duration=14,asetpts=PTS-STARTPTS[a1];[ob]atrim=start=28:end=138,asetpts=PTS-STARTPTS[a2];[a0][a1][a2]concat=n=3:v=0:a=1[a]'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-i',str(copied),'-i',str(origin_voice),'-filter_complex',audio_filter,'-map','[a]','-ar','48000','-ac','2','-c:a','pcm_s16le',str(prefix_audio)],check=True)
assert len(story['scenes'])==5 and story['append']['startSeconds']==138
start=0
for s in story['scenes']:
    assert s['start']==start, (s['id'],s['start'],start)
    start+=s['duration']
    assert (args.output/'assets/voice'/f"{s['id']}.mp3").is_file()
assert start==story['append']['repositoryStartSeconds']==102
assert story['append']['durationSeconds']==114 and story['append']['repositoryCardSeconds']==12
repository=json.loads((base/'evidence/repository-card.json').read_text(encoding='utf-8'))
assert repository['visibility']=='public' and len(repository['sourceCheckpoint'])==40
config=dict(output=args.output.as_posix(), originalVideo=copied.as_posix(),prefixAudio=prefix_audio.as_posix(),story=story,reviewAccepted=True,repository=repository)
(base/'evidence/production-timeline.json').write_text(json.dumps(dict(traceId='graph.riemann.conclusion.timeline',originalSeconds=138,reviewedFormalScenesSeconds=78,reviewedPrimeConnectionSeconds=24,repositorySeconds=12,totalSeconds=252,prefixAudioReplacement=[14,28],explanation='Separately reviewed supplements add the prime bridge and public-audience language. Original source files and prefix visuals remain unchanged; only the authorized14–28second narration is replaced in the derived prefix.'),indent=2)+'\n',encoding='utf-8')
launcher=args.work/'conclusion-launch.jsx'
launcher.write_text('var CONFIG = '+json.dumps(config,ensure_ascii=True)+';\n$.evalFile(new File('+json.dumps((base/'build_ending.jsx').as_posix())+'));\n',encoding='utf-8')
print(launcher)
