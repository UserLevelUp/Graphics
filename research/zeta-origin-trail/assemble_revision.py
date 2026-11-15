"""Insert the brush demonstration while retaining all existing narration."""
import argparse,json,re,subprocess
from pathlib import Path
import imageio_ffmpeg

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
base=Path(__file__).resolve().parent;out=a.output
c=json.loads((base/'contract.json').read_text(encoding='utf-8'));old=Path(c['originalVideo'])
graph=('[0:v]split=2[old0][old1];[old0]trim=end_frame=336,setpts=PTS-STARTPTS[v0];'
       '[1:v]trim=end_frame=336,setpts=PTS-STARTPTS[v1];'
       '[2:v]trim=end_frame=288,setpts=PTS-STARTPTS[v2];'
       '[old1]trim=start_frame=672:end_frame=5760,setpts=PTS-STARTPTS[v3];'
       '[3:v]trim=end_frame=288,setpts=PTS-STARTPTS[v4];'
       '[v0][v1][v2][v3][v4]concat=n=5:v=1:a=0[v];'
       '[0:a]asplit=2[oa][ob];[oa]atrim=end=28,asetpts=PTS-STARTPTS[a0];'
       '[2:a]apad,atrim=duration=12,asetpts=PTS-STARTPTS[a1];'
       '[ob]atrim=start=28:end=252,asetpts=PTS-STARTPTS[a2];'
       '[a0][a1][a2]concat=n=3:v=0:a=1[a]')
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-y','-i',str(old),'-i',str(out/'origin-trail-scene.mp4'),'-i',str(out/'circle-brush-scene.mp4'),'-i',str(out/'repository-card.mp4'),'-filter_complex',graph,'-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-r','24','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'presentation-with-trail.mp4')]
with (base/'evidence/assembly.log').open('w',encoding='utf-8') as log:subprocess.run(cmd,stdout=log,stderr=log,check=True)
def sec(s):
    h,m,z=s.replace(',',':').split(':')[:3];ms=s[-3:];return int(h)*3600+int(m)*60+int(z)+int(ms)/1000
def stamp(s):
    ms=round(s*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
blocks=[]
for block in (old.parent/'captions.srt').read_text(encoding='utf-8').strip().split('\n\n'):
    lines=block.splitlines();start,end=map(sec,lines[1].split(' --> '));shift=12 if start>=28 else 0
    blocks.append((start+shift,end+shift,'\n'.join(lines[2:])))
voice=json.loads((base/'evidence/circle-voice.json').read_text(encoding='utf-8'))
blocks.append((28.15,28.15+voice['durationSeconds'],c['circleScene']['narration']))
blocks.sort();(out/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(lo)} --> {stamp(hi)}\n{text}' for i,(lo,hi,text) in enumerate(blocks))+'\n',encoding='utf-8')
text=(old.parent/'transcript.txt').read_text(encoding='utf-8')
text=re.sub(r'^\d\d:\d\d:\d\d,\d\d\d',lambda m:stamp(sec(m[0])+(12 if sec(m[0])>=28 else 0)),text,flags=re.M)
needle='00:00:40,000';position=text.index(needle)
text=text[:position]+'00:00:28,000  The same brush draws a circle\n'+c['circleScene']['narration']+'\n\n'+text[position:]
(out/'transcript.txt').write_text(text,encoding='utf-8')
print(json.dumps({'seconds':264,'frames':6336,'origin':[14,28],'circle':[28,40],'finalRepositoryCard':[252,264]}))
