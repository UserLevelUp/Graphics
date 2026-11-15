"""Insert the lessons chapter before a refreshed public-repository card.

defines: graph.riemann.lessons.assembly
consumer: graph.riemann.lessons.explanation
The prior presentation is a read-only input. Captions are retimed, not discarded.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
EXPECTED_BASE = '4dbd34ae6816c32301c017fd386202fa5e93c4e65cf5a8a225edceef3402e12e'
INSERT = 308
FPS = 24


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def stamp(t):
    ms = round(t * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def seconds(s):
    h, m, sec = s.replace(',', '.').split(':')
    return 3600 * int(h) + 60 * int(m) + float(sec)


def read_srt(p):
    entries = []
    for block in re.split(r'\n\s*\n', Path(p).read_text(encoding='utf-8-sig').strip()):
        lines = block.splitlines()
        at = next(i for i, line in enumerate(lines) if ' --> ' in line)
        a, b = lines[at].split(' --> ')
        entries.append((seconds(a), seconds(b), '\n'.join(lines[at+1:])))
    return entries


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True, encoding='utf-8').strip()


def repository_card(meta, destination):
    im = Image.new('RGB', (1920, 1080), '#090d17')
    d = ImageDraw.Draw(im)
    font = lambda n, bold=False: ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf', n)
    def text(x, y, value, size=38, color='#eef3fb', bold=False):
        assert d.textlength(value, font=font(size, bold)) <= 1750, value
        d.text((x,y), value, font=font(size,bold), fill=color)
    text(80, 48, 'Explore, reproduce, and challenge the results', 53)
    text(84, 142, 'PUBLIC CODE  •  METHODS  •  COUNTEREXAMPLES  •  REVIEW EVIDENCE', 27, '#71ece9')
    d.rounded_rectangle((80,222,1840,875), radius=30, fill='#111a29', outline='#293e50', width=2)
    text(125,260,'github.com/UserLevelUp/Graphics',49,'#bd96ed',True)
    text(125,350,'Branch: ' + meta['branch'],37)
    text(125,418,'Source checkpoint before export: ' + meta['head'][:12],31,'#b2c1d3')
    text(125,496,'Verified with git remote -v',31,'#71ece9')
    for i, line in enumerate(meta['remoteLines']):
        text(125,550 + i*57,line.replace('\t','    '),27)
    text(125,704,'Research chapter: research/riemann-lessons',32)
    text(125,777,'Exact finite results. No new prime shortcut or RH proof established.',30,'#ffd079')
    text(84,928,'Reproduce the checks, change one hypothesis, and test new inputs.',34)
    text(84,995,'Trace: graph.riemann.lessons',25,'#8fa5bc')
    im.save(destination)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True, type=Path)
    p.add_argument('--chapter', required=True, type=Path)
    p.add_argument('--chapter-captions', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    assert sha(args.base) == EXPECTED_BASE, 'Unexpected historical base export'
    args.output.mkdir(parents=True, exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    reader = imageio_ffmpeg.read_frames(str(args.chapter))
    cm = next(reader)
    reader.close()
    duration = cm['duration']
    chapter_frames = round(duration * FPS)
    assert abs(chapter_frames/FPS-duration) < .011
    duration = chapter_frames/FPS
    repo = BASE.parents[1]
    meta = dict(traceId='graph.riemann.lessons.repository', observedAtUtc=datetime.now(timezone.utc).isoformat(),
                branch=git(repo,'branch','--show-current'), head=git(repo,'rev-parse','HEAD'),
                remoteLines=git(repo,'remote','-v').splitlines(),
                worktreeAtExport=git(repo,'status','--short'), commands=['git branch --show-current','git rev-parse HEAD','git remote -v'])
    assert meta['branch'] == 'graph/riemann-continuation'
    assert len(meta['remoteLines']) == 2 and all('https://github.com/UserLevelUp/Graphics.git' in s for s in meta['remoteLines'])
    (args.output/'repository.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    card = args.output/'repository-card.png'
    repository_card(meta,card)
    captions = []
    for a,b,t in read_srt(args.base.parent/'captions.srt'):
        assert not (a < INSERT < b), 'A historical caption crosses the insertion point'
        captions.append((a+(duration if a>=INSERT else 0),b+(duration if a>=INSERT else 0),t))
    for a,b,t in read_srt(args.chapter_captions):
        assert 0 <= a < b <= duration + .001
        captions.append((a+INSERT,b+INSERT,t))
    captions.sort()
    assert all(captions[i][1] <= captions[i+1][0]+.002 for i in range(len(captions)-1))
    srt = args.output/'presentation-captions.srt'
    srt.write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{t}' for i,(a,b,t) in enumerate(captions))+'\n',encoding='utf-8')
    (args.output/'presentation-transcript.txt').write_text('\n\n'.join(f'[{stamp(a)}]\n{t}' for a,b,t in captions)+'\n',encoding='utf-8')
    total = 320 + duration
    chapters = [(0,INSERT,'The original exploration'),(INSERT,INSERT+duration,'What worked, what did not, and why'),(INSERT+duration,total,'Public project and reproduction')]
    chapter_file = args.output/'chapters.ffmetadata'
    chapter_file.write_text(';FFMETADATA1\ntitle=Four-color exploration: results and limits\n'+''.join(f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(a*1000)}\nEND={round(b*1000)}\ntitle={name}\n' for a,b,name in chapters),encoding='utf-8')
    graph = (f'[0:v]trim=end_frame={INSERT*FPS},setpts=PTS-STARTPTS,setsar=1[v0];'
             f'[0:a]atrim=end={INSERT},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a0];'
             f'[1:v]trim=end_frame={chapter_frames},setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,setsar=1[v1];'
             f'[1:a]apad,atrim=duration={duration},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a1];'
             '[2:v]trim=end_frame=288,setpts=PTS-STARTPTS,setsar=1[v2];'
             '[0:a]atrim=start=308:end=320,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a2];'
             '[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]')
    dest = args.output/'presentation-with-lessons.mp4'
    cmd = [ff,'-hide_banner','-y','-i',str(args.base),'-i',str(args.chapter),'-loop','1','-framerate','24','-i',str(card),'-i',str(srt),'-i',str(chapter_file),
           '-filter_complex',graph,'-map','[v]','-map','[a]','-map','3:0','-map_metadata','4','-map_chapters','4',
           '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-r','24',
           '-c:a','aac','-b:a','192k','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart','-t',str(total),str(dest)]
    with (args.output/'assembly.log').open('w',encoding='utf-8') as log:
        subprocess.run(cmd,stdout=log,stderr=log,check=True)
    assert sha(args.base) == EXPECTED_BASE, 'Base export changed during assembly'
    inputs = [args.base,args.chapter,args.chapter_captions,args.base.parent/'captions.srt',Path(__file__),BASE/'script.json']
    manifest = dict(traceId='graph.riemann.lessons.assembly',createdAtUtc=datetime.now(timezone.utc).isoformat(),
        video=dict(path=str(dest.resolve()),sha256=sha(dest),bytes=dest.stat().st_size,width=1920,height=1080,fps=24,frames=round(total*24),durationSeconds=total),
        chapter=dict(insertAtSeconds=INSERT,durationSeconds=duration,frames=chapter_frames),
        repositoryCard=dict(startSeconds=INSERT+duration,durationSeconds=12,sourceCheckpoint=meta['head'],imageSha256=sha(card)),
        captions=dict(path=str(srt.resolve()),sha256=sha(srt),cues=len(captions),embedded=True),
        preservedSource=dict(path=str(args.base.resolve()),sha256=EXPECTED_BASE),
        inputs=[dict(path=str(q.resolve()),sha256=sha(q)) for q in inputs],
        limits=['The existing 308-second body is re-encoded, not byte-copied, in this separate export.',
                'The old export remains byte-identical. The new repository card replaces its final 12 seconds.',
                'The displayed checkpoint identifies the source state before media export, not a self-referential final media commit.'])
    (args.output/'assembly-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest['video'],indent=2))


if __name__ == '__main__':
    main()
