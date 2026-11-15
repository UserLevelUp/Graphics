"""Check the appended export, source integrity, scene audio and review frames."""
import argparse,hashlib,json,re,subprocess,textwrap
from pathlib import Path
import imageio_ffmpeg
import numpy as np
from PIL import Image

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
base=Path(__file__).resolve().parent;out=args.output;ff=imageio_ffmpeg.get_ffmpeg_exe()
story=json.loads((base/'formulation/closing-scenes.json').read_text(encoding='utf-8'))
prime=json.loads((base/'formulation/prime-connection.json').read_text(encoding='utf-8'))
public=json.loads((base/'formulation/public-language.json').read_text(encoding='utf-8'))['changes']
next(s for s in story['scenes'] if s['id']=='formal_object')['narration']=public['narration']
repo=json.loads((base/'repository-narration.json').read_text(encoding='utf-8'))
contract=json.loads((base/'graph.riemann.conclusion.contract.current.json').read_text(encoding='utf-8'))
voice=json.loads((base/'evidence/voice-production.json').read_text(encoding='utf-8'))
video=out/'presentation-with-conclusion.mp4';original=out/'assets/original-presentation.mp4'
assert hashlib.sha256(original.read_bytes()).hexdigest()==contract['originalVideoSha256']
assert hashlib.sha256(Path(contract['originalVideo']).read_bytes()).hexdigest()==contract['originalVideoSha256']
decoded=subprocess.run([ff,'-v','error','-nostats','-progress','pipe:1','-i',str(video),'-f','null','-'],capture_output=True,text=True,encoding='utf-8')
assert decoded.returncode==0 and not decoded.stderr.strip(),decoded.stderr
frames=int(re.findall(r'^frame=(\d+)$',decoded.stdout,re.M)[-1]);assert frames==6048,frames
(base/'evidence/full-decode.log').write_text(decoded.stdout+decoded.stderr,encoding='utf-8')
probe=subprocess.run([ff,'-hide_banner','-i',str(video),'-t','0','-f','null','-'],capture_output=True,text=True,encoding='utf-8')
assert '1920x1080' in probe.stderr and '24 fps' in probe.stderr
(base/'evidence/media-probe.log').write_text(probe.stderr,encoding='utf-8')
preview=out/'preview';preview.mkdir(exist_ok=True)
scenes=story['scenes']+[prime,dict(repo,start=102,title='Public project and branch')]
shots=[]
for s in scenes:
    t=138+s['start']+s['duration']/2;dest=preview/(s['id']+'.png')
    subprocess.run([ff,'-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-y',str(dest)],check=True)
    shots.append(dict(id=s['id'],time=t,path=str(dest)))
last=preview/'last-frame.png'
subprocess.run([ff,'-v','error','-ss',str(251.958333),'-i',str(video),'-frames:v','1','-y',str(last)],check=True)
sheet=Image.new('RGB',(1920,1080))
for i,path in enumerate([Path(s['path']) for s in shots]+[last]):
    im=Image.open(path).convert('RGB').resize((640,360));sheet.paste(im,((i%3)*640,(i//3)*360))
sheet.save(preview/'contact-sheet.png')
def frame_bytes(file,t):
    return subprocess.check_output([ff,'-v','error','-ss',str(t),'-i',str(file),'-frames:v','1','-vf','scale=480:270','-pix_fmt','rgb24','-f','rawvideo','-'])
prefix=[]
for t in [7,35.5,84,115.5,130.5]:
    a=np.frombuffer(frame_bytes(original,t),dtype=np.uint8).astype(float)
    b=np.frombuffer(frame_bytes(video,t),dtype=np.uint8).astype(float)
    rmse=float(np.sqrt(np.mean((a-b)**2)));assert rmse<3,(t,rmse)
    prefix.append(dict(time=t,rgbRmse=rmse,tolerance=3))
pcm=subprocess.check_output([ff,'-v','error','-i',str(video),'-vn','-ac','1','-ar','16000','-f','f32le','-'])
a=np.frombuffer(pcm,dtype='<f4');assert abs(len(a)/16000-252)<.05
audio=[]
for s in scenes:
    lo=138+s['start'];hi=lo+s['duration'];seg=a[int(lo*16000):int(hi*16000)]
    rms=float(np.sqrt(np.mean(seg.astype(float)**2)));peak=float(np.max(np.abs(seg)))
    assert rms>.001 and peak<1.05,(s['id'],rms,peak)
    audio.append(dict(id=s['id'],rms=rms,peak=peak))
def read_audio(path):
    return np.frombuffer(subprocess.check_output([ff,'-v','error','-i',str(path),'-vn','-ac','1','-ar','16000','-f','f32le','-']),dtype='<f4')
source_audio=read_audio(original);public_audio=read_audio(out/'assets/public-prefix.wav')
outside=[]
for lo,hi in [(0.1,13.9),(28.1,137.9)]:
    a0=source_audio[int(lo*16000):int(hi*16000)];a1=public_audio[int(lo*16000):int(hi*16000)]
    err=float(np.max(np.abs(a0-a1)));assert err<.001,(lo,hi,err)
    outside.append(dict(start=lo,end=hi,maxAbsoluteSampleDifference=err))
changed=float(np.sqrt(np.mean((source_audio[14*16000:28*16000]-public_audio[14*16000:28*16000])**2)))
assert changed>.005,changed
def stamp(sec):
    ms=round(sec*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'
old=Path(contract['originalVideo']).parent
old_story=json.loads((base.parent/'zeta-continuation/storyboard.json').read_text(encoding='utf-8'))
old_voice=json.loads((base.parent/'zeta-continuation/evidence/voice-production.json').read_text(encoding='utf-8'))
old_dur={c['id']:c['expectedOutputDurationSeconds'] for c in old_voice['clips']}
transcript='';captions=''
dur={r['id']:r['expectedOutputDurationSeconds'] for r in voice['clips']}
for i,s in enumerate(old_story['scenes']):
    narration=public['originalOriginReplacement']['narration'] if s['id']=='origin' else s['narration']
    length=dur['origin_public'] if s['id']=='origin' else old_dur[s['id']]
    t=s['startSeconds']
    transcript+=f"{stamp(t)}  {s['title']}\n{narration}\n\n"
    captions+=f"{i+1}\n{stamp(t+.15)} --> {stamp(t+.15+length)}\n"+textwrap.fill(narration,64)+'\n\n'
for i,s in enumerate(scenes):
    t=138+s['start']
    transcript+=f"{stamp(t)}  {s['title']}\n{s['narration']}\n\n"
    captions+=f"{10+i}\n{stamp(t+.15)} --> {stamp(t+.15+dur[s['id']])}\n"+textwrap.fill(s['narration'],64)+'\n\n'
assert 'your idea' not in transcript.lower()
(out/'transcript.txt').write_text(transcript,encoding='utf-8');(out/'captions.srt').write_text(captions,encoding='utf-8')
sources=(old/'sources.txt').read_text(encoding='utf-8')+'\n\nFORMAL CONCLUSION SOURCES\n'
sources+='\n\n'.join(s['title']+'\n'+s['url']+'\n'+s['use'] for s in story['sources'])
sources+='\n\nPRIME-DISTRIBUTION BRIDGE\n'+json.dumps(prime.get('sources',[]),ensure_ascii=False,indent=2)
(out/'sources.txt').write_text(sources+'\n',encoding='utf-8')
report=dict(traceId='graph.riemann.conclusion.media.verify',status='technical_pass_visual_review_pending',videoSeconds=252,frames=frames,frameSize=[1920,1080],framesPerSecond=24,fullDecodePassed=True,originalFileUnchanged=True,originalCopiedExactly=True,authorizedPrefixAudioReplacement=[14,28],publicAudienceTranscriptChecked=True,prefixReencodingComparisons=prefix,endingAudio=audio,previewFrames=shots,lastFrame=str(last),videoSha256=hashlib.sha256(video.read_bytes()).hexdigest(),aepSha256=hashlib.sha256((out/'presentation-with-conclusion.aep').read_bytes()).hexdigest(),limitations=['Combined video is re-encoded; original source file is unchanged. Derived prefix replaces narration only at14–28seconds. Visual prefix comparisons sample five timestamps, not every frame.','Narration source prompts, duration, decoding and signal presence are checked; no independent speech transcription.'])
report['prefixAudioEditCheck']=dict(outsideReplacementComparisons=outside,replacementRmsDifference=changed,edgeGuardSeconds=.1)
(base/'evidence/media-qa.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('previewFrames','endingAudio')},indent=2))
