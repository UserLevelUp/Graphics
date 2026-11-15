"""Render a silent, labeled zero-index continuation tour from checked samples.

defines: graph.riemann.zero_index.animation
Requires NumPy, Pillow and imageio-ffmpeg. Does not evaluate primality or zeta.
"""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
REPO=BASE.parents[1]
FPS=24; SIZE=(1280,720)
PLOT=(80,155,780,465)
BG=(13,18,30); PANEL=(24,32,49); INK=(238,244,252); MUTED=(181,196,216)
PALETTE=np.array([(27,115,94),(136,102,39),(101,60,133),(39,77,136)],dtype=np.uint8)
PINK=(255,151,219); CYAN=(112,240,255); GOLD=(255,225,101)
FONT_DIR=Path('C:/Windows/Fonts')
FONTS={size:ImageFont.truetype(str(FONT_DIR/'segoeui.ttf'),size) for size in (15,17,18,20,22,26,30,34)}
BOLD={size:ImageFont.truetype(str(FONT_DIR/'segoeuib.ttf'),size) for size in (18,20,22,26,30,34)}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(draw,xy,text,size=20,color=INK,bold=False):
    draw.text(xy,text,font=(BOLD if bold else FONTS)[size],fill=color)


def paragraph(draw,x,y,text,size=20,width=310,color=MUTED):
    font=FONTS[size]
    lines=[]
    for segment in text.split('\n'):
        words=segment.split();line=''
        for word in words:
            trial=(line+' '+word).strip()
            if draw.textlength(trial,font=font)>width and line:
                lines.append(line);line=word
            else:line=trial
        lines.append(line)
    for line in lines:
        write_text(draw,(x,y),line,size,color);y+=size+7
    return y


def dashed(draw,a,b,color,width=1,dash=8):
    length=math.hypot(b[0]-a[0],b[1]-a[1])
    if not length:return
    for distance in range(0,int(length),2*dash):
        t0=distance/length;t1=min(1,(distance+dash)/length)
        draw.line((a[0]+t0*(b[0]-a[0]),a[1]+t0*(b[1]-a[1]),
                   a[0]+t1*(b[0]-a[0]),a[1]+t1*(b[1]-a[1])),fill=color,width=width)


def interpolate(points,target):
    times=[p[0] for p in points]
    j=bisect.bisect_right(times,target)
    visible=points[:max(1,j)]
    if j<len(points) and j>0:
        lo,hi=points[j-1],points[j]
        f=(target-lo[0])/(hi[0]-lo[0])
        point=(target,lo[1]+f*(hi[1]-lo[1]),lo[2]+f*(hi[2]-lo[2]))
        visible=visible+[point]
    else:point=visible[-1]
    return visible,point,target>times[-1]+1e-12


class Renderer:
    def __init__(self,grids):
        self.grid_dir=grids
        self.meta=json.loads((grids/'grids.json').read_text(encoding='utf-8-sig'))
        assert self.meta['status']=='complete' and self.meta['completedGrids']==32
        self.zero=json.loads((BASE/'evidence/zero-index.json').read_text())
        self.rows={r['zeroIndex']:r for r in self.zero['rows']}
        self.path_data=json.loads((BASE/'evidence/paths.json').read_text())
        self.paths={p['zeroIndex']:[(float(v['a']),float(v['sigma']),float(v['t'])) for v in p['points']] for p in self.path_data['paths']}
        self.old_path=REPO/'research/zeta-continuation/evidence/native/a1.values.json'
        old=json.loads(self.old_path.read_text(encoding='utf-8-sig'))
        self.original={p['startZeroIndex']:[(v['a'],v['s']['real'],v['s']['imaginary']) for v in p['points']] for p in old['trajectories']}
        self.grids={g['id']:g for g in self.meta['grids']};self.arrays={}
        for g in self.meta['grids']:
            path=grids/g['binary']['file'];assert sha(path)==g['binary']['sha256']
            raw=np.fromfile(path,dtype='<f8').reshape(g['height'],g['width'],2)
            self.arrays[g['id']]=raw[...,0]+1j*raw[...,1]

    def background(self,name,a):
        w=self.arrays[name]-a;finite=np.isfinite(w)
        angle=np.mod(np.angle(np.where(finite,w,1)),2*np.pi)
        q=np.minimum(3,(angle/(np.pi/2)).astype(int))
        rgb=PALETTE[q];rgb[~finite]=(128,128,128)
        rgb[np.abs(w)<1e-10]=(238,244,252)
        return Image.fromarray(rgb[::-1].copy()).resize(PLOT[2:],Image.Resampling.NEAREST)

    def coordinate(self,name,sigma,t):
        d=self.grids[name]['domain'];x,y,w,h=PLOT
        return x+w*(sigma-d['minSigma'])/(d['maxSigma']-d['minSigma']),y+h*(d['maxT']-t)/(d['maxT']-d['minT'])

    def base(self,name,a,title,subtitle,local_index=None):
        image=Image.new('RGB',SIZE,BG);draw=ImageDraw.Draw(image)
        write_text(draw,(34,20),title,30,bold=True)
        write_text(draw,(36,66),subtitle,18,MUTED)
        draw.rounded_rectangle((900,110,1250,645),radius=15,fill=PANEL)
        image.paste(self.background(name,a),(PLOT[0],PLOT[1]))
        draw=ImageDraw.Draw(image)
        x,y,w,h=PLOT;draw.rectangle((x,y,x+w,y+h),outline=MUTED,width=1)
        d=self.grids[name]['domain'];center=float(self.rows[local_index]['height']) if local_index else 0
        xticks=[.4,.5,.6,.7,.8,.9] if local_index else [.05,.5,1,1.5,2,2.5,3]
        yticks=[center+v for v in (-.3,-.15,0,.15,.3)] if local_index else [10,15,20,25,30]
        for sigma in xticks:
            xx,_=self.coordinate(name,sigma,d['minT'])
            draw.line((xx,y+h,xx,y+h+6),fill=MUTED)
            label=f'{sigma:g}';tw=draw.textlength(label,font=FONTS[17]);write_text(draw,(xx-tw/2,y+h+9),label,17,MUTED)
        for t in yticks:
            _,yy=self.coordinate(name,d['minSigma'],t)
            draw.line((x-6,yy,x,yy),fill=MUTED)
            label=f'{t-center:+.2f}' if local_index else f'{t:g}'
            tw=draw.textlength(label,font=FONTS[17]);write_text(draw,(x-11-tw,yy-11),label,17,MUTED)
        xx,_=self.coordinate(name,.5,d['minT']);dashed(draw,(xx,y),(xx,y+h),INK,1)
        write_text(draw,(xx+7,y+7),'σ = ½',17,INK)
        write_text(draw,(x-3,y-32),'t − starting height' if local_index else 'height t',18,MUTED)
        write_text(draw,(x+w-12,y+h+36),'σ',20,MUTED)
        write_text(draw,(570,116),f'Background: phase of ζ(s) − a    a = {a:.3f}',17,MUTED)
        write_text(draw,(35,662),'Near-zero pixels (|ζ(s) − a| < 10⁻¹⁰) are neutral: phase is undefined at a zero.',15,MUTED)
        write_text(draw,(35,689),'Numerical paths; moving dots interpolate checked samples. Colors do not identify individual primes.',15,MUTED)
        return image,draw

    def draw_path(self,draw,name,points,a,color,label=None):
        visible,current,exited=interpolate(points,a)
        coords=[self.coordinate(name,p[1],p[2]) for p in visible]
        if len(coords)>1:
            draw.line(coords,fill=BG,width=6);draw.line(coords,fill=color,width=3)
        sx,sy=self.coordinate(name,points[0][1],points[0][2])
        draw.ellipse((sx-4,sy-4,sx+4,sy+4),fill=INK)
        px,py=self.coordinate(name,current[1],current[2])
        if exited:draw.rectangle((px-5,py-5,px+5,py+5),fill=BG,outline=color,width=2)
        else:draw.ellipse((px-6,py-6,px+6,py+6),fill=color,outline=INK,width=1)
        if label:write_text(draw,(sx+8,sy-24),label,17,color)

    def intro(self,progress):
        a=max(0,min(1,(progress-.12)/.76))
        image,draw=self.base('intro',a,'WHAT THE ORIGINAL LABELS MEAN','Zero #3 means the third zeta zero. It is not the integer 23 or an individual prime.')
        for j,color in ((1,GOLD),(2,CYAN),(3,PINK)):
            self.draw_path(draw,'intro',self.original[j],a,color,f'Zero #{j}')
        write_text(draw,(922,132),'Starts at σ = ½',26,bold=True)
        y=184
        for j,color in ((1,GOLD),(2,CYAN),(3,PINK)):
            row=self.rows[j]
            write_text(draw,(922,y),f'Zero #{j}',22,color,True)
            write_text(draw,(922,y+33),f'height {float(row["height"]):.6f}',18,MUTED)
            write_text(draw,(922,y+61),f'initial slope {float(row["slope"]):+.6f}',20,INK)
            y+=111
        paragraph(draw,922,523,'The starts were chosen on the critical line. Held exit boxes are not current roots after leaving the view.',18)
        return image

    def local(self,index,progress,ordinal,total,control=False):
        a=.1*max(0,min(1,(progress-.18)/.64));row=self.rows[index];name=f'Z{index}'
        kind='NONPRIME INDEX CONTROL' if control else 'PRIME INDEX COMPARISON'
        image,draw=self.base(name,a,f'ZERO #{index}  •  {kind}',
                            f'{ordinal}/{total} in this group. Same local axis scales for every zero; actual starting height is shown at right.',index)
        height=float(row['height']);slope=float(row['slope'])
        dx=min(.07,.15/max(abs(slope),1e-20))
        dashed(draw,self.coordinate(name,.5-dx,height-slope*dx),self.coordinate(name,.5+dx,height+slope*dx),INK,2,7)
        self.draw_path(draw,name,self.paths[index],a,PINK)
        write_text(draw,(922,131),f'Zero #{index}',30,PINK,True)
        write_text(draw,(922,179),'Actual starting height',18,MUTED)
        write_text(draw,(922,208),f'{height:.10f}',22,INK,True)
        write_text(draw,(922,252),'Initial slope at σ = ½',18,MUTED)
        write_text(draw,(922,283),f'{slope:+.6f}',34,CYAN if slope>0 else GOLD,True)
        write_text(draw,(922,331),'UPWARD' if slope>0 else 'DOWNWARD',22,CYAN if slope>0 else GOLD,True)
        paragraph(draw,922,382,f'The index {index} is {row["classificationPrimeIndex"]}. The curve follows ζ(s) = a; it does not represent the integer {index}.',18)
        paragraph(draw,922,499,'Pink identifies the selected path in every scene. Dashed white line: its initial tangent.',18)
        write_text(draw,(922,590),'Short path: a = 0 → 0.10',18,INK)
        return image

    def summary(self):
        image=Image.new('RGB',SIZE,BG);draw=ImageDraw.Draw(image)
        write_text(draw,(55,42),'WHAT THE SLOPE TEST SHOWS',34,bold=True)
        paragraph(draw,57,100,'The sign of the starting slope does not separate prime indices from composite indices.',26,1150,INK)
        draw.rounded_rectangle((55,174,1225,391),radius=18,fill=PANEL)
        for x,label in ((82,'Zero-index group'),(600,'Downward'),(890,'Upward')):
            write_text(draw,(x,193),label,22,MUTED,True)
        for y,label,negative,positive in ((250,'25 prime indices',14,11),(310,'74 composite indices',35,39)):
            write_text(draw,(82,y),label,26,INK,True)
            write_text(draw,(640,y),str(negative),30,GOLD,True);write_text(draw,(930,y),str(positive),30,CYAN,True)
        write_text(draw,(64,411),'Index 1 is neither; its starting slope is negative. There is no zero index 0.',18,MUTED)
        paragraph(draw,64,454,'Zeta connects to the distribution of primes collectively. These continuation curves are paths of ζ(s) = a, not one curve per prime.',22,1140,INK)
        write_text(draw,(64,541),'Slope: dt/dσ = −Im ζ′(s) / Re ζ′(s), where the denominator is nonzero.',22,INK)
        paragraph(draw,64,594,'All starts used known zeros on σ = ½. That choice does not prove RH. The animation compares prime indices 2–97 and six nonprime controls.',18,1140,MUTED)
        write_text(draw,(64,674),'graph.riemann.zero_index  •  Reproducible data, mathematical notes and verification accompany this video.',15,MUTED)
        return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grids',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--previews-only',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    preview=args.output/'preview';preview.mkdir(exist_ok=True)
    r=Renderer(args.grids)
    primes=[j for j,row in r.rows.items() if row['isPrimeIndex']]
    controls=[1,4,6,8,9,10]
    scenes=[dict(kind='intro',seconds=12,index=None)]
    scenes += [dict(kind='prime',seconds=2,index=j) for j in primes]
    scenes += [dict(kind='control',seconds=2,index=j) for j in controls]
    scenes += [dict(kind='summary',seconds=10,index=None)]
    cursor=0
    for scene in scenes:
        scene['startFrame']=cursor;cursor+=scene['seconds']*FPS;scene['endFrameExclusive']=cursor
    assert cursor==2016
    r.intro(0).save(preview/'original-start.png');r.intro(1).save(preview/'original-end.png')
    for j in (2,3,7,8,97):
        control=j in controls;group=controls if control else primes
        r.local(j,1,group.index(j)+1,len(group),control).save(preview/f'Zero-{j}.png')
    r.summary().save(args.output/'slope-summary.png')
    r.local(2,1,1,25).save(args.output/'poster.png')
    manifest=dict(traceId='graph.riemann.zero_index.animation',fps=FPS,width=SIZE[0],height=SIZE[1],
        durationSeconds=cursor/FPS,frames=cursor,primeIndices=primes,controlIndices=controls,scenes=scenes,
        audio='Silent; explanations and labels appear on screen.',
        meaning='Z_j is zero index j. Prime-index selection tests the screenshot interpretation; curves are not individual primes.',
        interpolation='Linear display interpolation between checked solution samples. Background uses the current target a.',
        neutralThreshold=1e-10,
        inputs=[dict(path=str(p),sha256=sha(p)) for p in (Path(__file__),BASE/'evidence/zero-index.json',BASE/'evidence/paths.json',r.old_path,args.grids/'grids.json')])
    if not args.previews_only:
        path=args.output/'zero-index-slope-tour.mp4'
        writer=imageio_ffmpeg.write_frames(str(path),SIZE,fps=FPS,codec='libx264',pix_fmt_in='rgb24',pix_fmt_out='yuv420p',
            quality=None,macro_block_size=1,ffmpeg_log_level='error',output_params=['-crf','18','-preset','fast','-movflags','+faststart'])
        writer.send(None)
        try:
            for scene in scenes:
                count=scene['endFrameExclusive']-scene['startFrame']
                for k in range(count):
                    progress=k/(count-1)
                    if scene['kind']=='intro':image=r.intro(progress)
                    elif scene['kind']=='summary':image=r.summary()
                    else:
                        control=scene['kind']=='control';group=controls if control else primes
                        image=r.local(scene['index'],progress,group.index(scene['index'])+1,len(group),control)
                    writer.send(np.asarray(image))
                print(f"Rendered {scene['kind']} {scene['index']}",flush=True)
        finally:writer.close()
        manifest['video']=dict(path=path.name,sha256=sha(path),bytes=path.stat().st_size)
    (args.output/'animation.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(previewsOnly=args.previews_only,frames=cursor,seconds=cursor/FPS),indent=2))


if __name__=='__main__':main()
