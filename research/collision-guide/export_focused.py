"""Export the complete collision chapter plus its public repository ending.

defines: graph.riemann.collision_guide.focused
"""
import argparse
import json
from pathlib import Path
import subprocess
import imageio_ffmpeg
from assemble import sha, read_srt, stamp, INSERT_FRAME, FPS

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); out=args.output
    m=json.loads((out/'assembly-manifest.json').read_text())
    source=Path(m['video']['path'])
    assert sha(source)==m['video']['sha256']
    frames=m['video']['frames']-INSERT_FRAME
    duration=frames/FPS
    entries=[(a-INSERT_FRAME/FPS,b-INSERT_FRAME/FPS,t) for a,b,t in read_srt(out/'presentation-captions.srt') if a>=INSERT_FRAME/FPS]
    srt=out/'focused-captions.srt'
    srt.write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{t}' for i,(a,b,t) in enumerate(entries))+'\n',encoding='utf-8')
    chapters=json.loads((out/'chapter-manifest.json').read_text())['scenes']
    ffmeta=out/'focused-chapters.ffmetadata'
    ffmeta.write_text(';FFMETADATA1\ntitle=How long before polynomial roots can collide?\n'+''.join(f'[CHAPTER]\nTIMEBASE=1/24000\nSTART={s["startFrame"]*1000}\nEND={s["endFrameExclusive"]*1000}\ntitle={s["title"]}\n' for s in chapters)+f'[CHAPTER]\nTIMEBASE=1/24000\nSTART={(frames-288)*1000}\nEND={frames*1000}\ntitle=Public code and reproducible evidence\n',encoding='utf-8')
    dest=out/'finite-root-collision-guide.mp4'
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-y','-i',str(source),'-i',str(srt),'-i',str(ffmeta),
         '-filter_complex',f'[0:v]trim=start_frame={INSERT_FRAME},setpts=PTS-STARTPTS[v];[0:a]atrim=start={INSERT_FRAME/FPS},asetpts=PTS-STARTPTS[a]',
         '-map','[v]','-map','[a]','-map','1:0','-map_metadata','2','-map_chapters','2',
         '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-r','24',
         '-c:a','aac','-b:a','192k','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart','-t',str(duration),str(dest)]
    with (out/'focused-export.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=log,check=True)
    result=dict(traceId='graph.riemann.collision_guide.focused',video=dict(path=str(dest.resolve()),sha256=sha(dest),bytes=dest.stat().st_size,frames=frames,fps=24,width=1920,height=1080,durationSeconds=duration),
                captions=dict(path=str(srt.resolve()),cues=len(entries),sha256=sha(srt)),
                source=dict(path=str(source),sha256=sha(source),startFrame=INSERT_FRAME),
                inputs=[dict(path=str(q.resolve()),sha256=sha(q)) for q in [Path(__file__),out/'assembly-manifest.json',out/'chapter-manifest.json']])
    (out/'focused-manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['video'],indent=2))

if __name__=='__main__':main()
