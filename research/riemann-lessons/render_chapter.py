"""Render the narrated evidence/limitations chapter from its reviewed script.

defines: graph.riemann.lessons.media
Deterministic vector-like Pillow frames; illustrations are explicitly schematic.
No zeta or primality conclusions are inferred from rendered colors.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import wave

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
FPS = 24
SIZE = (1280, 720)
BG = (9, 14, 24)
PANEL = (16, 25, 40)
INNER = (21, 34, 51)
EDGE = (57, 88, 106)
INK = (239, 245, 252)
MUTED = (163, 184, 205)
CYAN = (93, 230, 236)
GOLD = (255, 207, 97)
VIOLET = (186, 137, 230)
GREEN = (58, 164, 135)
BLUE = (56, 102, 166)
PINK = (255, 153, 218)
PALETTE = [GREEN, GOLD, VIOLET, BLUE]
FONTROOT = Path('C:/Windows/Fonts')
FONT = {(size, bold): ImageFont.truetype(str(FONTROOT / ('segoeuib.ttf' if bold else 'segoeui.ttf')), size)
        for size in (14, 16, 17, 18, 20, 22, 24, 26, 28, 30, 32, 34, 38, 42, 48, 54) for bold in (False, True)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def wrap(draw, text, size, width, bold=False):
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split():
            new = (line + ' ' + word).strip()
            if draw.textlength(new, font=FONT[size, bold]) > width and line:
                lines.append(line)
                line = word
            else:
                line = new
        lines.append(line)
    return lines


def label(draw, xy, text, size=24, color=INK, bold=False, width=None):
    assert size in (14, 16, 17, 18, 20, 22, 24, 26, 28, 30, 32, 34, 38, 42, 48, 54)
    if width is not None:
        assert draw.textlength(text, font=FONT[size, bold]) <= width, (text, width)
    draw.text(xy, text, font=FONT[size, bold], fill=color)


def paragraph(draw, xy, text, width, size=24, color=INK, bold=False, max_height=200):
    lines = wrap(draw, text, size, width, bold)
    line_height = size + 8
    assert len(lines) * line_height <= max_height, (text, len(lines), max_height)
    for i, line in enumerate(lines):
        label(draw, (xy[0], xy[1] + i * line_height), line, size, color, bold, width)
    return len(lines) * line_height


def ease(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def arrow(draw, a, b, color=CYAN, width=4, head=12):
    draw.line((a, b), fill=color, width=width)
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    draw.polygon([b, (b[0]-head*math.cos(angle-.45), b[1]-head*math.sin(angle-.45)),
                  (b[0]-head*math.cos(angle+.45), b[1]-head*math.sin(angle+.45))], fill=color)


def pill(draw, xy, text, color=CYAN, width=220, size=20):
    x, y = xy
    draw.rounded_rectangle((x, y, x+width, y+40), radius=12, fill=INNER, outline=color, width=1)
    tw = draw.textlength(text, font=FONT[size, True])
    assert tw <= width-18, text
    label(draw, (x+(width-tw)/2, y+5), text, size, color, True)


class Renderer:
    def __init__(self, script=BASE/'script.json'):
        self.script_path = Path(script)
        self.script = json.loads(self.script_path.read_text(encoding='utf-8-sig'))
        self.scenes = self.script['scenes'] if isinstance(self.script, dict) else self.script

    def presenter(self, draw, time):
        bob = 2*math.sin(time*1.1)
        cx, cy = 140, 525+bob
        draw.rounded_rectangle((55, 421+bob, 225, 647+bob), radius=60, fill=(12, 23, 33))
        draw.ellipse((101, 432+bob, 179, 510+bob), fill=(251, 247, 222), outline=EDGE, width=2)
        for x in (128, 151):
            draw.ellipse((x, 464+bob, x+5, 471+bob), fill=BG)
        draw.arc((126, 478+bob, 155, 492+bob), 15, 165, fill=EDGE, width=2)
        draw.rounded_rectangle((94, 525+bob, 182, 626+bob), radius=24, fill=(18, 55, 72), outline=EDGE, width=2)
        draw.rounded_rectangle((99, 630+bob, 128, 638+bob), radius=5, fill=CYAN)
        draw.rounded_rectangle((148, 630+bob, 177, 638+bob), radius=5, fill=CYAN)
        py = 517+bob+5*math.sin(time*.6)
        draw.line(((179, 548+bob), (220, 534+bob), (246, py)), fill=CYAN, width=8)
        draw.ellipse((241, py-5, 251, py+5), fill=GOLD)
        draw.polygon(((249, py-6), (270, py-12), (255, py+4)), fill=CYAN)
        label(draw, (101, 647), 'COMPASS', 14, MUTED)

    def bubble(self, draw, scene, progress):
        draw.rounded_rectangle((35, 161, 245, 367), radius=18, fill=(24, 43, 58), outline=EDGE, width=2)
        draw.polygon(((116, 366), (145, 366), (132, 405)), fill=(24, 43, 58), outline=EDGE)
        short = {
            'brush_order': 'A visual effect needs an arithmetic test.',
            'slope_rule': 'A counterexample breaks the rule.',
            'half_identity': 'The same half-step also fits composites.',
            'critical_line': 'One point is different from a whole line.',
            'shifted_zeta': 'A new input still needs a decision rule.',
            'unit_switch': 'A useful bookkeeping term is not a prime.',
            'finite_reversal': 'Keep the cutoff finite. Then compare.',
            'infinite_subtraction': 'Continuation is not ordinary summation.',
            'coefficient_cancellation': 'A coefficient is different from a value.',
            'exact_color': 'Arithmetic decides. Color shows the result.',
            'finite_result': 'A finite proof has a precise boundary.',
            'next_steps': 'Make every next claim independently checkable.'
        }.get(scene['id'], 'What did the evidence establish?')
        paragraph(draw, (53, 184), short, 174, 22, max_height=160)

    def frame(self, scene_index, seconds, duration=None):
        scene = self.scenes[scene_index]
        duration = duration or scene['durationSeconds']
        p = max(0, min(1, seconds/duration))
        image = Image.new('RGB', SIZE, BG)
        draw = ImageDraw.Draw(image)
        label(draw, (36, 23), 'WHAT WORKS • WHAT THE TESTS RULE OUT', 16, CYAN, True)
        paragraph(draw, (36, 58), scene['title'], 1190, 34, max_height=76)
        label(draw, (1140, 120), f'{scene_index+1:02d} / {len(self.scenes):02d}', 16, CYAN)
        draw.rounded_rectangle((279, 154, 1245, 634), radius=22, fill=PANEL, outline=(25, 39, 56), width=1)
        self.presenter(draw, seconds)
        self.bubble(draw, scene, p)
        self.diagram(draw, scene['id'], seconds, p)
        lines = scene.get('screenLines', [])
        assert len(lines) <= 4
        for i, text in enumerate(lines):
            # All statements are readable by the first third of each scene.
            visible = seconds >= .45+i*1.0
            if visible:
                color = INK if i == 0 else MUTED
                size = 26 if i == 0 else 22
                paragraph(draw, (310, 432+i*46), text, 902, size, color, i==0, max_height=40)
        status = scene.get('status', 'EVIDENCE REVIEW')
        # Status remains fully readable; long editorial descriptions wrap.
        paragraph(draw, (295, 650), status, 935, 17, CYAN, True, max_height=52)
        draw.rectangle((0, 713, int(SIZE[0]*p), 719), fill=CYAN)
        return image

    def diagram(self, d, sid, time, p):
        q = ease(min(1, p/.65))
        if sid == 'brush_order':
            label(d, (315, 174), 'SCHEMATIC BRUSH TRAILS', 16, MUTED)
            for row, direction in enumerate((1, -1)):
                yy=245+row*112
                label(d, (319, yy-16), 'left → right' if direction==1 else 'right → left', 20, INK)
                n=int(44*q)+1
                for j in range(n):
                    x=534+j*13 if direction==1 else 1093-j*13
                    for dx,dy,c in ((0,-35,GREEN),(-35,-35,GOLD),(-35,0,VIOLET),(0,0,BLUE)):
                        d.rectangle((x+dx, yy+dy, x+dx+35, yy+dy+35), fill=c)
                d.line((x-43,yy,x+43,yy),fill=INK,width=1)
                d.line((x,yy-43,x,yy+43),fill=INK,width=1)
            label(d, (738, 398), 'Same brush. Different last writer.', 17, MUTED)
        elif sid == 'slope_rule':
            label(d, (315, 174), 'FIRST 100 ZERO INDICES • OBSERVED INITIAL SLOPES', 16, MUTED)
            for y, title, neg, pos, total in ((227,'Prime indices',14,11,25),(320,'Composite indices',35,39,74)):
                label(d, (315,y), title,22,INK,True)
                x=552;w=600
                nwidth=w*neg/total*q;pwidth=w*pos/total*q
                d.rounded_rectangle((x,y,x+nwidth,y+45),radius=7,fill=VIOLET)
                if pwidth>0:d.rounded_rectangle((x+nwidth,y,x+nwidth+pwidth,y+45),radius=7,fill=GREEN)
                label(d,(x+8,y+6),f'{neg} negative',20,BG,True)
                label(d,(x+w*neg/total+8,y+6),f'{pos} positive',20,BG,True)
            label(d,(552,385),'Index 1: neither prime nor composite; negative slope.',17,MUTED)
        elif sid == 'half_identity':
            for x, n, color, kind in ((335,97,CYAN,'PRIME'),(790,99,GOLD,'COMPOSITE')):
                d.rounded_rectangle((x,181,x+393,387),radius=18,fill=INNER,outline=EDGE)
                label(d,(x+22,194),f'{n}',48,color,True)
                label(d,(x+123,214),kind,18,color,True)
                label(d,(x+25,276),f'{n} / 2 = {n//2} + ½',30,INK)
                if q>.35:label(d,(x+25,333),f'{n} = 2 × {n//2} + 1',26,MUTED)
        elif sid == 'critical_line':
            x0,y0=425,373; xline=665
            arrow(d,(x0,y0),(1120,y0),MUTED,2)
            arrow(d,(x0,y0),(x0,182),MUTED,2)
            label(d,(1127,361),'σ',22,MUTED);label(d,(406,164),'t',22,MUTED)
            d.line((xline,187,xline,373),fill=CYAN,width=3)
            label(d,(xline-20,380),'½',22,CYAN,True)
            label(d,(940,183),'s = ½ + it',26,CYAN,True)
            for t in (14.134725,21.022040,25.010858):
                yy=y0-t*6
                radius=5+2*math.sin(time*1.5+t)
                d.ellipse((xline-radius,yy-radius,xline+radius,yy+radius),fill=GOLD)
                label(d,(xline+17,yy-13),f't ≈ {t:.6f}',18,MUTED)
            d.ellipse((xline-6,y0-6,xline+6,y0+6),fill=PINK)
            label(d,(765,337),'ζ(½) ≈ −1.46035 ≠ 0',22,PINK)
        elif sid == 'shifted_zeta':
            for i, text in enumerate(('ζ(s − 1)','ζ(s)','ζ(s + 1)')):
                x=325+i*295
                d.rounded_rectangle((x,214,x+265,341),radius=18,fill=INNER,outline=EDGE,width=2)
                label(d,(x+42,239),text,38,CYAN if i==1 else INK,True)
                label(d,(x+35,298),'Evaluate a function',17,MUTED)
            for i in range(2):arrow(d,(600+i*295,276),(614+i*295,276),GOLD,3,8)
            label(d,(468,376),'The tested three-color match fails.',24,GOLD)
        elif sid == 'unit_switch':
            label(d,(337,194),'Multiplication',22,MUTED)
            label(d,(337,241),'1 × n = n',42,CYAN,True)
            label(d,(337,312),'1 contributes no new factor.',22,MUTED)
            d.line((770,193,770,379),fill=EDGE,width=2)
            label(d,(813,194),'Series bookkeeping',22,MUTED)
            label(d,(813,245),'ζ(s) − 1',38,GOLD,True)
            label(d,(813,315),'Remove the unit term.',22,MUTED)
        elif sid == 'finite_reversal':
            if p<.43:
                nums=[2,3,5,7];offset=min(1,p/.3)
                label(d,(320,183),'REORDER THE SAME FINITE SUM',16,MUTED)
                for row in range(2):
                    for j,n in enumerate(nums):
                        x=490+140*(j if row==0 else (j*(1-offset)+(3-j)*offset));y=230+row*90
                        d.rounded_rectangle((x,y,x+90,y+56),radius=12,fill=INNER,outline=CYAN if row==0 else VIOLET,width=2)
                        label(d,(x+32,y+7),str(n),30,INK,True)
                label(d,(323,242),'forward',22,CYAN);label(d,(323,332),'reversed',22,VIOLET)
                label(d,(1067,278),'17 − 17',22,INK,True)
                label(d,(1100,319),'= 0',30,GOLD,True)
            else:
                label(d,(320,183),'REVERSE COEFFICIENT POSITIONS • CUTOFF N = 10',16,MUTED)
                d.line((390,290,1140,290),fill=MUTED,width=2)
                for n in range(11):
                    x=400+n*70
                    d.line((x,286,x,294),fill=MUTED,width=1)
                    label(d,(x-6,381),str(n),18,MUTED)
                height=70*ease((p-.43)/.2)
                d.rectangle((520,290-height,560,290),fill=CYAN)
                d.rectangle((940,290,980,290+height),fill=VIOLET)
                label(d,(514,222),' +1',22,CYAN,True)
                label(d,(934,342),' −1',22,VIOLET,True)
                label(d,(677,230),'z² − z⁸',38,INK,True)
        elif sid == 'infinite_subtraction':
            label(d,(328,185),'FINITE CUTOFF: 1 THROUGH 10',16,MUTED)
            nums=[1,4,6,8,9,10]
            for j,n in enumerate(nums):
                x=334+j*140
                d.rounded_rectangle((x,226,x+116,291),radius=10,fill=INNER,outline=VIOLET if n>1 else GOLD,width=2)
                label(d,(x+33,235),str(n),34,INK,True)
            label(d,(331,320),'55 − 17 = 38',38,CYAN,True)
            label(d,(735,333),'The leftovers include the unit 1.',22,MUTED)
            label(d,(332,380),'At s = −1: 1 + 2 + 3 + … diverges.',22,GOLD)
        elif sid == 'coefficient_cancellation':
            label(d,(330,180),'COEFFICIENTS OF n⁻ˢ IN H(s)',16,MUTED)
            for i,(n,v) in enumerate(((9,.5),(15,1),(25,.5),(27,2/3),(97,0),(99,1))):
                x=355+i*140;h=140*v*q
                d.line((x-25,359,x+70,359),fill=EDGE,width=2)
                if h:d.rounded_rectangle((x,359-h,x+45,359),radius=5,fill=VIOLET if n!=97 else CYAN)
                else:d.ellipse((x+17,352,x+29,364),fill=CYAN)
                label(d,(x-2,369),str(n),22,INK,True)
                label(d,(x-5,204),('0' if v==0 else '½' if v==.5 else '⅔' if v<1 else '1'),24,CYAN if n==97 else GOLD,True)
        elif sid == 'exact_color':
            cx,cy=520,287;r=103
            for start,c in ((270,GREEN),(180,GOLD),(90,VIOLET),(0,BLUE)):
                d.pieslice((cx-r,cy-r,cx+r,cy+r),start,start+90,fill=c)
            label(d,(555,233),'QI',20,INK,True)
            d.line((cx-r-15,cy,cx+r+15,cy),fill=INK,width=1);d.line((cx,cy-r-15,cx,cy+r+15),fill=INK,width=1)
            n=(96,97,99)[min(2,int(p*3))]
            remainder=(math.factorial(n-1)+1)%n
            angle=math.pi/4+remainder*math.pi/2
            xx=cx+85*math.cos(angle);yy=cy-85*math.sin(angle)
            d.line((cx,cy,xx,yy),fill=INK,width=3);d.ellipse((xx-6,yy-6,xx+6,yy+6),fill=INK)
            arrow(d,(680,284),(780,284),CYAN,4)
            label(d,(813,219),'exact remainder',26,INK,True)
            label(d,(813,270),'→ phase',30,CYAN,True)
            label(d,(813,320),'→ display color',30,VIOLET,True)
            label(d,(337,402),f'Schematic palette • n = {n}; R(n) = {remainder}',16,MUTED)
        elif sid == 'finite_result':
            label(d,(316,176),'EXACT CLASSIFICATION • 0 THROUGH 100',16,MUTED)
            for n in range(101):
                x=324+(n%17)*52;y=214+(n//17)*31
                prime=n>=2 and all(n%v for v in range(2,math.isqrt(n)+1))
                reveal=n<=max(5,math.ceil(101*q))
                col=VIOLET if prime and reveal else INNER
                d.rounded_rectangle((x,y,x+43,y+26),radius=5,fill=col)
                label(d,(x+(9 if n<10 else 4),y+1),str(n),16,INK if reveal else EDGE,prime and reveal)
            label(d,(881,402),'25 primes • 0 and 1 neither',17,MUTED)
        elif sid == 'next_steps':
            cx,cy,r=497,290,96
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=EDGE,width=3)
            angle=-2*math.pi*min(1,p/.82)
            end=(cx+r*math.cos(angle),cy+r*math.sin(angle))
            pts=[(cx+r*math.cos(-2*math.pi*k/180),cy+r*math.sin(-2*math.pi*k/180)) for k in range(max(2,int(180*min(1,p/.82))))]
            d.line(pts,fill=CYAN,width=4)
            d.ellipse((end[0]-6,end[1]-6,end[0]+6,end[1]+6),fill=GOLD)
            label(d,(cx-37,cy-20),'f(z)=z',22,INK,True)
            label(d,(349,395),'EXACT MODEL • ONE ENCLOSED ZERO',14,MUTED)
            for y,t,c in ((199,'Visual candidate',VIOLET),(272,'Certified contour bounds',CYAN),(345,'Complete zero count',GOLD)):
                pill(d,(748,y),t,c,425,22)
            arrow(d,(960,243),(960,266),MUTED,2);arrow(d,(960,316),(960,339),MUTED,2)
        else:
            label(d,(335,250),'Evidence → interpretation → next test',32,CYAN,True)


def clock(t):
    millis=round(t*1000);h,millis=divmod(millis,3600000);m,millis=divmod(millis,60000);s,ms=divmod(millis,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script',type=Path,default=BASE/'script.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--voices',type=Path,help='JSON clips: id, narration, localPath, taskId, voice.')
    parser.add_argument('--preview-only',action='store_true')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True);args.work.mkdir(parents=True,exist_ok=True)
    preview=args.output/'preview';preview.mkdir(exist_ok=True)
    renderer=Renderer(args.script)
    for i,scene in enumerate(renderer.scenes):
        renderer.frame(i,scene['durationSeconds']*.65).save(preview/f'{i+1:02d}-{scene["id"]}.png')
    if args.preview_only:
        print(json.dumps({'status':'previews_rendered','count':len(renderer.scenes)}));return
    assert args.voices and args.voices.exists(),'A matched voice manifest is required.'
    voices=json.loads(args.voices.read_text(encoding='utf-8-sig'))
    voices=voices['clips'] if isinstance(voices,dict) else voices
    voice_by_id={r['id']:r for r in voices}
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    assets=args.output/'assets'/'voice';assets.mkdir(parents=True,exist_ok=True)
    pcm=[];scenes=[];cursor=0;captions=[];transcript=[];clip_evidence=[]
    for i,scene in enumerate(renderer.scenes):
        v=voice_by_id[scene['id']];assert v.get('narration',v.get('prompt'))==scene['narration'],scene['id']
        src=Path(v['localPath'])
        if not src.is_absolute():
            src=args.voices.parent/src
        wav=assets/f'{scene["id"]}.wav'
        subprocess.run([ff,'-v','error','-y','-i',str(src),'-ar','48000','-ac','1','-c:a','pcm_s16le',str(wav)],check=True)
        with wave.open(str(wav),'rb') as w:
            assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==48000
            data=w.readframes(w.getnframes());voice_duration=w.getnframes()/48000
        duration=max(float(scene['durationSeconds']),math.ceil((voice_duration+2.0)*FPS)/FPS)
        frames=round(duration*FPS);duration=frames/FPS
        lead=round(.65*48000);tail=round(duration*48000)-lead-len(data)//2
        assert tail>=round(.5*48000),'Narration must not be truncated.'
        pcm.append(b'\0\0'*lead+data+b'\0\0'*tail)
        scenes.append(dict(id=scene['id'],title=scene['title'],startFrame=cursor,endFrameExclusive=cursor+frames,
                           durationSeconds=duration,voiceSeconds=voice_duration,voiceStartSeconds=cursor/FPS+.65))
        chunks=re.split(r'(?<=[.!?])\s+',scene['narration']);weight=sum(len(c.split()) for c in chunks)
        at=cursor/FPS+.65
        for c in chunks:
            dt=voice_duration*len(c.split())/weight
            captions.append((at,at+dt,c));at+=dt
        transcript.append(f'{clock(cursor/FPS)}  {scene["title"]}\n{scene["narration"]}\n')
        clip_evidence.append(dict(id=scene['id'],voice=v.get('voice'),taskId=v.get('taskId'),narration=scene['narration'],
            source=dict(path=str(src.resolve()),sha256=sha(src)),wav=dict(path=str(wav.resolve()),sha256=sha(wav)),
            durationSeconds=voice_duration,sceneSeconds=duration,leadSeconds=.65,truncated=False))
        cursor+=frames
    combined=args.output/'narration.wav'
    with wave.open(str(combined),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
        for data in pcm:w.writeframes(data)
    (args.output/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{clock(a)} --> {clock(b)}\n{t}' for i,(a,b,t) in enumerate(captions))+'\n',encoding='utf-8')
    (args.output/'transcript.txt').write_text('\n'.join(transcript),encoding='utf-8')
    video=args.output/'chapter.mp4'
    log=args.work/'render.log'
    command=[ff,'-v','warning','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-',
        '-i',str(combined),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',str(video)]
    with log.open('wb') as out:
        proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=out)
        try:
            for i,scene in enumerate(scenes):
                count=scene['endFrameExclusive']-scene['startFrame']
                for f in range(count):
                    proc.stdin.write(renderer.frame(i,f/FPS,scene['durationSeconds']).tobytes())
                print(f'Rendered scene {i+1}/{len(scenes)}: {scene["id"]}',flush=True)
            proc.stdin.close()
            assert proc.wait()==0,log.read_text(errors='replace')
        except BaseException:
            proc.kill();proc.wait();raise
    inputs=[args.script,Path(__file__),args.voices]
    manifest=dict(traceId='graph.riemann.lessons.media',createdUtc=datetime.now(timezone.utc).isoformat(),status='rendered',
        width=1280,height=720,fps=FPS,frames=cursor,durationSeconds=cursor/FPS,
        resolutionNote='Chapter is rendered natively at1280x720; the combined1080p export upscales this chapter only and preserves the existing1920x1080 presentation size.',
        video=dict(path=str(video.resolve()),sha256=sha(video),bytes=video.stat().st_size),
        scenes=scenes,voiceClips=clip_evidence,
        captions=dict(path='captions.srt',sha256=sha(args.output/'captions.srt'),timing='Sentence boundaries apportioned by word count within each complete narration clip; not forced-aligned.'),
        illustrations='Schematic explanatory animations; slope counts and finite classification labels are exact declared inputs.',
        inputs=[dict(path=str(p.resolve()),sha256=sha(p)) for p in inputs])
    write_json(args.output/'chapter-manifest.json',manifest)
    write_json(args.output/'voice-production.json',dict(status='produced',clips=clip_evidence))
    print(json.dumps({k:manifest[k] for k in ('status','frames','durationSeconds','video')},indent=2))


if __name__=='__main__':
    main()
