"""Append the native ending to the accepted presentation, retaining exact segment durations."""
import argparse
import json
import subprocess
from pathlib import Path
import imageio_ffmpeg

p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
args=p.parse_args()
base=Path(__file__).resolve().parent
story=json.loads((base/'formulation/closing-scenes.json').read_text(encoding='utf-8'))
duration=story['append']['durationSeconds']+24
ff=imageio_ffmpeg.get_ffmpeg_exe()
original=args.output/'assets/original-presentation.mp4'
ending=args.output/'formal-conclusion.mp4'
dest=args.output/'presentation-with-conclusion.mp4'
graph=(f'[0:v]trim=end_frame=3312,setpts=PTS-STARTPTS[v0];'
       f'[2:a]atrim=duration=138,asetpts=PTS-STARTPTS[a0];'
       f'[1:v]trim=end_frame={int(duration*24)},setpts=PTS-STARTPTS[v1];'
       f'[1:a]apad,atrim=duration={duration},asetpts=PTS-STARTPTS[a1];'
       '[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]')
cmd=[ff,'-hide_banner','-y','-i',str(original),'-i',str(ending),'-i',str(args.output/'assets/public-prefix.wav'),'-filter_complex',graph,
     '-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
     '-r','24','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
with (base/'evidence/assembly.log').open('w',encoding='utf-8') as log:
    subprocess.run(cmd,stdout=log,stderr=log,check=True)
print(json.dumps({'video':str(dest),'expectedDuration':138+duration,'expectedFrames':int((138+duration)*24),'prefix':'Accepted source copied unchanged; the combined export is re-encoded.'}))
