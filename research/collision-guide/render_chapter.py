"""Render the narrated finite-collision guide from its reviewed script.

defines: graph.riemann.collision_guide.media
Deterministic mathematical diagrams. Quartic root positions and displayed gap curves
come from the specified exact polynomial formulas; screen coordinates are floating point.
The all-interval certificate comes from the separate proof, not sampled images.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import cmath
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
        for size in range(14,55) for bold in (False, True)}


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
    assert 14 <= size <= 54
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
        short = scene.get('bubble', {
            'promised_result': 'A guarantee before the first collision.',
            'discovery_path': 'Counterexamples shaped the next question.',
            'discovery_audit': 'Trace the history. Check the derivation.',
            'exact_flow': 'Keep the direction of time explicit.',
            'read_inputs': 'Start with exact, distinct real roots.',
            'quartic_orbit': 'This calibration has an exact answer.',
            'isolated_baseline': 'A useful baseline, not the exact answer.',
            'coupled_motion': 'Every root influences every other root.',
            'adjacent_gap': 'An adjacent pair makes the signs work.',
            'diameter_lowerbound': 'The outer span bounds each interaction.',
            'static_certificate': 'A positive lower bound prevents a collision.',
            'why_proof_closes': 'The first collision would contradict the bound.',
            'contracting_diameter': 'A shrinking span strengthens the estimate.',
            'dynamic_certificate': 'A longer certified interval follows.',
            'bound_vs_collision': 'A guaranteed duration is a lower bound.',
            'run_checker': 'Use your own finite rational root list.',
            'certified_rational_step': 'Exact root counts check selected times.',
            'use_and_rebase': 'Root separation is not a numerical error bound.',
            'predictor_benchmark': 'Compare forecasts with an exact control.',
            'assumptions_scaling': 'A certificate needs the stated assumptions.',
            'rh_connection': 'Shared dynamics connect two different settings.',
            'rh_open_obligation': 'The infinite system needs more than a finite bound.',
            'reproducible_scope': 'Reuse the proof and checker within their scope.'
        }.get(scene['id'], 'Read the assumptions before using the bound.'))
        paragraph(draw, (53, 184), short, 174, 22, max_height=160)

    def frame(self, scene_index, seconds, duration=None):
        scene = self.scenes[scene_index]
        duration = duration or scene['durationSeconds']
        p = max(0, min(1, seconds/duration))
        image = Image.new('RGB', SIZE, BG)
        draw = ImageDraw.Draw(image)
        label(draw, (36, 23), 'A GUARANTEE BEFORE ROOTS COLLIDE', 16, CYAN, True)
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
                while size > 18 and draw.textlength(text, font=FONT[size, i==0]) > 902:
                    size -= 2
                paragraph(draw, (310, 432+i*46), text, 902, size, color, i==0, max_height=40)
        status = scene.get('status', 'EVIDENCE REVIEW')
        # Status remains fully readable; long editorial descriptions wrap.
        paragraph(draw, (295, 650), status, 935, 17, CYAN, True, max_height=52)
        draw.rectangle((0, 713, int(SIZE[0]*p), 719), fill=CYAN)
        return image


    def root_axis(self, d, roots, xleft=365, xright=1160, y=290, span=3.5, labels=True):
        d.line((xleft,y,xright,y),fill=EDGE,width=2)
        pos=lambda r: (xleft+xright)/2 + float(r)*((xright-xleft)/(2*span))
        for k in range(-3,4):
            xx=pos(k);d.line((xx,y-4,xx,y+4),fill=EDGE,width=1)
            if labels:label(d,(xx-6,y+18),str(k),16,MUTED)
        for j,r in enumerate(roots):
            xx=pos(r)
            d.ellipse((xx-8,y-8,xx+8,y+8),fill=(CYAN,VIOLET,GOLD,PINK)[j%4])
        return pos

    @staticmethod
    def quartic(u):
        # P_{-u}(z)=z^4-(10-12u)z^2+9-20u+12u^2.
        disc=cmath.sqrt(96*(1-u)*(2/3-u))
        w1=(10-12*u-disc)/2;w2=(10-12*u+disc)/2
        a,b=cmath.sqrt(w1),cmath.sqrt(w2)
        return [-b,-a,a,b]

    def root_motion(self, d, u, y=292):
        x0,x1=370,1160;cx=(x0+x1)/2;scale=112
        d.line((x0,y,x1,y),fill=EDGE,width=2)
        d.line((cx,y-95,cx,y+95),fill=EDGE,width=1)
        label(d,(1159,y+8),'Re z',14,MUTED)
        label(d,(cx+8,y-100),'Im z',14,MUTED)
        for k in range(-3,4):
            xx=cx+k*scale;d.line((xx,y-4,xx,y+4),fill=EDGE,width=1)
            label(d,(xx-6,y+13),str(k),16,MUTED)
        for j,z in enumerate(self.quartic(u)):
            xx=cx+z.real*scale;yy=y-z.imag*scale
            d.ellipse((xx-8,yy-8,xx+8,yy+8),fill=(CYAN,VIOLET,GOLD,PINK)[j])
        label(d,(346,180),f'EXACT QUARTIC FORMULA • u = {u:.4f}; t = −u',16,MUTED)

    def duration_chart(self, d, p, all_bounds=True, marker=None):
        values=[('Pair baseline',.5,MUTED),('Fixed diameter',.5300236604537255,CYAN),
                ('Shrinking diameter',.5397189134471992,VIOLET),('Exact quartic collision',2/3,GOLD)]
        for i,(name,value,col) in enumerate(values):
            y=197+i*48
            label(d,(319,y),name,18,col)
            x=600;w=505*value/.7*ease(min(1,p/.6))
            d.rounded_rectangle((x,y,x+w,y+24),radius=5,fill=col)
            label(d,(1120,y-1),f'{value:.6f}',16,col)
        if marker is not None:
            xx=600+505*marker/.7
            d.line((xx,190,xx,386),fill=PINK,width=2)
            label(d,(780,391),f'Chosen step u = {marker:.5f}',18,PINK)

    @staticmethod
    def gap_lower(u,dynamic=False):
        if dynamic:
            R=1-40*u/36
            return R**(-.2)*(4-6*(1-R**1.2)) if R>0 else float('nan')
        k=1/18
        return 2/k+(4-2/k)*math.exp(4*k*u)

    def gap_plot(self,d,p,dynamic=False):
        xl,xr,yt,yb=395,1165,206,371
        d.line((xl,yt-8,xl,yb,xr,yb),fill=EDGE,width=2)
        label(d,(320,178),'SQUARED GAP LOWER BOUND • QUARTIC CALIBRATION',16,MUTED)
        for u in (0,.25,.5,.54):
            xx=xl+(xr-xl)*u/.56
            d.line((xx,yb-4,xx,yb+4),fill=MUTED,width=1)
            label(d,(xx-12,yb+11),str(u),16,MUTED)
        label(d,(1170,yb+4),'u',18,MUTED)
        for v in (0,2,4):
            yy=yb-(yb-yt)*v/4
            label(d,(366,yy-9),str(v),16,MUTED)
        end=.56*ease(min(1,p/.7))
        for fun,col in ((lambda u:4-8*u,MUTED),(lambda u:self.gap_lower(u),CYAN)):
            pts=[]
            for j in range(201):
                u=end*j/200;val=fun(u)
                if val>=0:pts.append((xl+(xr-xl)*u/.56,yb-(yb-yt)*val/4))
            if len(pts)>1:d.line(pts,fill=col,width=3)
        if dynamic:
            pts=[]
            for j in range(201):
                u=end*j/200;val=self.gap_lower(u,True)
                if val>=0:pts.append((xl+(xr-xl)*u/.56,yb-(yb-yt)*val/4))
            if len(pts)>1:d.line(pts,fill=VIOLET,width=4)
        text='gray: pair • cyan: fixed diameter' + (' • violet: shrinking diameter' if dynamic else '')
        label(d,(430,398),text,16,MUTED)

    def diagram(self,d,sid,time,p):
        q=ease(min(1,p/.7))
        if sid=='promised_result':
            label(d,(326,181),'A CERTIFIED INTERVAL, NOT AN EXACT COLLISION FORECAST',16,MUTED)
            xl,xr=380,1155;y=285
            d.line((xl,y,xr,y),fill=EDGE,width=3)
            boundary=xl+(xr-xl)*.539718913/.75
            d.rounded_rectangle((xl,y-29,xl+(boundary-xl)*q,y+29),radius=7,fill=(34,95,94))
            label(d,(425,269),'guaranteed real + simple',25,CYAN,True)
            d.line((boundary,y-48,boundary,y+48),fill=VIOLET,width=3)
            d.ellipse((boundary-6,y-6,boundary+6,y+6),fill=PANEL,outline=VIOLET,width=2)
            label(d,(xl,342),'u = 0',22,MUTED)
            label(d,(boundary-66,342),'T ≈ 0.539719',22,VIOLET)
            label(d,(945,239),'beyond T:',18,MUTED)
            label(d,(945,270),'not decided',22,GOLD,True)
            label(d,(945,302),'by this bound',18,MUTED)
            label(d,(360,395),'Illustration: roots initially at −3, −1, 1, 3',17,MUTED)
        elif sid=='discovery_path':
            label(d,(329,179),'RECORDED MILESTONES • NOVEMBER 14, 2026',16,MUTED)
            milestones=(('170993c','Phase coordinates','Exact quadratic',CYAN),
                        ('73518fc','Quartic counterexample','Pair baseline',VIOLET),
                        ('cf51254','Exterior interactions','Two certificates',GOLD))
            for i,(commit,head,body,col) in enumerate(milestones):
                x=321+i*300
                d.rounded_rectangle((x,221,x+278,363),radius=15,fill=INNER,outline=col)
                label(d,(x+20,237),commit,26,col,True)
                label(d,(x+18,285),head,20,INK,True)
                label(d,(x+18,322),body,20,MUTED)
                if i<2:arrow(d,(x+280,290),(x+297,290),GOLD,2,7)
            label(d,(366,393),'A visual question became an algebraic, testable obligation.',20,MUTED)
        elif sid=='discovery_audit':
            label(d,(330,179),'PROVENANCE AND MATHEMATICAL EVIDENCE HAVE DIFFERENT ROLES',16,MUTED)
            for x,head,lines,col in ((326,'History',('Contract supplied formulas','Review correction retained'),VIOLET),
                                     (779,'Proof',('Reciprocal-term inequality','First-collision argument'),CYAN)):
                d.rounded_rectangle((x,217,x+416,348),radius=15,fill=INNER,outline=col)
                label(d,(x+20,230),head,26,col,True)
                for j,line in enumerate(lines):label(d,(x+20,276+j*31),line,21,INK)
            pill(d,(361,372),'Finite result: complete',CYAN,350,19)
            pill(d,(815,372),'Infinite transfer: open',GOLD,350,19)
        elif sid=='exact_flow':
            for x,t,col in ((338,'Initial polynomial',CYAN),(822,'Evolved polynomial',VIOLET)):
                d.rounded_rectangle((x,208,x+370,296),radius=15,fill=INNER,outline=col)
                label(d,(x+24,230),t,26,col,True)
            arrow(d,(722,250),(808,250),GOLD,4)
            label(d,(411,323),'t = 0',28,CYAN,True)
            label(d,(915,323),'t = −u',28,VIOLET,True)
            label(d,(420,383),'u increases → we follow the heat parameter backward',22,MUTED)
        elif sid=='read_inputs':
            pos=self.root_axis(d,[-3,-1,1,3],y=272)
            for a,b in ((-3,-1),(-1,1),(1,3)):
                d.line((pos(a),319,pos(b),319),fill=CYAN,width=3)
                label(d,((pos(a)+pos(b))/2-18,329),'2',22,CYAN,True)
            d.line((pos(-3),215,pos(3),215),fill=GOLD,width=3)
            label(d,(681,176),'D = 6',26,GOLD,True)
            label(d,(366,381),'Four distinct real roots: n = 4; minimum gap m = 2',22,MUTED)
        elif sid=='quartic_orbit':
            if p < .70:
                u=(2/3)*ease(p/.70)
            elif p < .85:
                u=2/3
            else:
                u=2/3+(.70-2/3)*ease((p-.85)/.15)
            self.root_motion(d,u)
            status=('distinct real roots' if u<2/3-1e-8 else
                    'double roots at ±1' if abs(u-2/3)<1e-8 else 'nonreal after collision')
            label(d,(422,393),f'u = 2/3 is the exact first collision • {status}',20,GOLD)
        elif sid=='isolated_baseline':
            u=.5*q;gap=math.sqrt(max(0,4-8*u));cx=765;y=277;scale=150
            d.line((420,y,1110,y),fill=EDGE,width=2)
            for x in (cx-scale*gap/2,cx+scale*gap/2):d.ellipse((x-10,y-10,x+10,y+10),fill=CYAN)
            label(d,(339,181),'ISOLATED PAIR • EXACT DEGREE-TWO EVOLUTION',16,MUTED)
            label(d,(550,338),f'g² = 4 − 8u = {4-8*u:.3f}',30,CYAN,True)
            label(d,(493,389),'The pair collides exactly at u = 1/2.',22,MUTED)
        elif sid=='coupled_motion':
            u=.4*q;roots=[z.real for z in self.quartic(u)]
            pos=self.root_axis(d,roots,y=290)
            for j,r in enumerate(roots):
                for k,other in enumerate(roots):
                    if j<k:
                        mid=(pos(r)+pos(other))/2
                        d.arc((pos(r),200+(k-j)*12,pos(other),360-(k-j)*12),180,360,fill=EDGE,width=1)
                vel=-2*sum(1/(r-other) for k,other in enumerate(roots) if k!=j)
                arrow(d,(pos(r),337),(pos(r)+vel*29,337),CYAN,3)
            label(d,(330,179),'ALL-PAIR INTERACTIONS • ARROWS FOLLOW INCREASING u',16,MUTED)
            label(d,(447,390),'The other roots alter each pair’s isolated motion.',22,MUTED)
        elif sid=='adjacent_gap':
            pos=self.root_axis(d,[-3,-1,1,3],y=278)
            d.rounded_rectangle((pos(-3)-20,234,pos(-1)+20,322),radius=15,outline=CYAN,width=2)
            for r in (1,3):
                d.line((pos(-3),260,pos(r),209),fill=EDGE,width=2)
                d.line((pos(-1),260,pos(r),209),fill=VIOLET,width=2)
            label(d,(419,329),'a',22,CYAN,True);label(d,(647,329),'b',22,CYAN,True)
            label(d,(337,177),'ADJACENCY PUTS EVERY OTHER ROOT OUTSIDE [a,b]',16,MUTED)
            label(d,(443,383),'Exterior products (b−r)(a−r) are positive.',22,GOLD)
        elif sid=='diameter_lowerbound':
            pos=self.root_axis(d,[-3,-1,1,3],y=282)
            d.line((pos(-3),217,pos(3),217),fill=GOLD,width=4)
            label(d,(688,179),'D(−u) ≤ D₀',26,GOLD,True)
            for a,b,y,col in ((-3,1,343,CYAN),(-1,1,376,VIOLET)):
                d.line((pos(a),y,pos(b),y),fill=col,width=3)
            label(d,(913,344),'each distance ≤ D₀',18,MUTED)
            label(d,(913,378),'n−2 exterior roots',18,MUTED)
        elif sid=='static_certificate':
            self.gap_plot(d,p,False)
        elif sid=='why_proof_closes':
            for i,(txt,col) in enumerate((('Before first collision',MUTED),('Every gap stays positive',CYAN),('No collision for u < T',GOLD))):
                x=321+i*300
                d.rounded_rectangle((x,222,x+278,332),radius=15,fill=INNER,outline=col)
                paragraph(d,(x+17,242),txt,244,22,col,True,max_height=75)
                if i<2:arrow(d,(x+280,277),(x+296,277),GOLD,2,7)
            label(d,(424,383),'Bounded coefficients prevent roots escaping to infinity.',20,MUTED)
        elif sid=='contracting_diameter':
            u=.54*q;actual=[z.real for z in self.quartic(u)]
            pos=self.root_axis(d,actual,y=292)
            half=math.sqrt(max(0,36-40*u))/2
            x1,x2=pos(-half),pos(half)
            d.rounded_rectangle((x1,242,x2,343),radius=8,outline=VIOLET,width=3)
            label(d,(338,180),f'QUARTIC: D(−u)² ≤ 36 − 40u; u = {u:.3f}',22,VIOLET,True)
            label(d,(469,385),'The enclosure contracts as elapsed u increases.',22,MUTED)
        elif sid=='dynamic_certificate':
            self.gap_plot(d,p,True)
        elif sid=='bound_vs_collision':
            self.duration_chart(d,p)
        elif sid=='run_checker':
            d.rounded_rectangle((318,180,1205,409),radius=15,fill=(6,13,22),outline=EDGE)
            label(d,(340,194),'POWERSHELL • FROM THE GRAPHICS REPOSITORY',16,CYAN)
            for i,line in enumerate(('python -B research/collision-guide/use_certificate.py',
                                     '  --roots=-3,-1,1,3',
                                     '  --duration=17/32')):
                label(d,(342,247+i*39),line,22,INK,True)
            label(d,(342,375),'Enter as one command; interval and point checks are separate.',18,MUTED)
        elif sid=='certified_rational_step':
            self.duration_chart(d,p,marker=17/32)
        elif sid=='use_and_rebase':
            for i,(title,sub,col) in enumerate((('Geometry','No collision before T',CYAN),('Numerics','Control step + rounding',GOLD),('New certificate','Prove the next start data',VIOLET))):
                x=318+i*300
                d.rounded_rectangle((x,210,x+280,365),radius=16,fill=INNER,outline=col)
                label(d,(x+17,229),title,24,col,True)
                paragraph(d,(x+18,280),sub,244,22,MUTED,max_height=80)
            label(d,(384,392),'A floating-point approximation is not a new exact input.',20,MUTED)
        elif sid=='predictor_benchmark':
            label(d,(335,180),'FROZEN LOCAL QUADRATIC • CENTER c = 0',16,MUTED)
            for x,head,value,col in ((337,'Local forecast','u = 0.45',VIOLET),(815,'Exact answer','u = 2/3',GOLD)):
                d.rounded_rectangle((x,219,x+363,343),radius=16,fill=INNER,outline=col)
                label(d,(x+23,236),head,22,col,True)
                label(d,(x+23,282),value,34,INK,True)
            label(d,(394,383),'At the forecast: P(−9/20, 0) = 243/100 > 0.',24,CYAN)
        elif sid=='assumptions_scaling':
            for i,(txt,col) in enumerate((('Finite degree',CYAN),('Distinct real roots',CYAN),('Exact rational inputs',CYAN))):
                pill(d,(331,193+i*67),txt,col,365,24)
            label(d,(793,204),'r → ar + b',34,VIOLET,True)
            label(d,(793,267),'m, D → |a|m, |a|D',24,INK)
            label(d,(793,326),'T → a²T',34,GOLD,True)
        elif sid=='rh_connection':
            label(d,(329,180),'ESTABLISHED LOGIC • NO NUMERICAL VALUE OF Λ IS ASSUMED',16,MUTED)
            for x,head,body,col in ((329,'RH','Λ ≤ 0',CYAN),(786,'Rodgers–Tao','Λ ≥ 0',VIOLET)):
                d.rounded_rectangle((x,216,x+409,309),radius=15,fill=INNER,outline=col)
                label(d,(x+20,231),head,23,col,True)
                label(d,(x+237,232),body,32,INK,True)
            arrow(d,(535,319),(693,367),GOLD,3)
            arrow(d,(990,319),(835,367),GOLD,3)
            pill(d,(667,354),'RH exactly when Λ = 0',GOLD,378,24)
        elif sid=='rh_open_obligation':
            label(d,(329,177),'SCHEMATIC ROOT SYSTEMS • POSITIONS ARE NOT ZETA DATA',16,MUTED)
            for x,head,col in ((329,'Finite certificate',CYAN),(786,'Infinite obligation',VIOLET)):
                d.rounded_rectangle((x,213,x+410,363),radius=15,fill=INNER,outline=col)
                label(d,(x+19,224),head,25,col,True)
            d.line((370,296,696,296),fill=EDGE,width=2)
            for xx in (388,462,550,679):d.ellipse((xx-6,290,xx+6,302),fill=CYAN)
            d.line((388,326,679,326),fill=CYAN,width=2)
            label(d,(458,332),'finite diameter',17,MUTED)
            d.line((815,296,1166,296),fill=EDGE,width=2)
            for xx in (821,846,883,935,1005,1097,1151):d.ellipse((xx-5,291,xx+5,301),fill=VIOLET)
            arrow(d,(850,329),(812,329),GOLD,2,8)
            arrow(d,(1135,329),(1174,329),GOLD,2,8)
            label(d,(884,322),'tails need control',17,MUTED)
            label(d,(432,385),'Known-real regime',22,MUTED)
            arrow(d,(678,399),(837,399),GOLD,3)
            label(d,(851,385),'toward t = 0',22,GOLD,True)
        elif sid=='reproducible_scope':
            for i,(head,body,col) in enumerate((('Proof','All finite inputs\nunder the assumptions',CYAN),('Checker','Exact arithmetic\nat selected times',VIOLET),('Open boundary','Novelty unestablished\nNo RH transfer',GOLD))):
                x=319+i*301
                d.rounded_rectangle((x,212,x+280,376),radius=17,fill=INNER,outline=col)
                label(d,(x+19,232),head,26,col,True)
                paragraph(d,(x+18,289),body,245,21 if False else 20,MUTED,max_height=80)
            label(d,(422,395),'Reuse the finite theorem; do not infer an infinite result.',20,MUTED)
        else:
            label(d,(333,255),'Exact inputs → theorem → certified interval',30,CYAN,True)


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
    expected_previews={f'{i+1:02d}-{s["id"]}.png' for i,s in enumerate(renderer.scenes)}
    for old in preview.glob('*.png'):
        if re.fullmatch(r'\d{2}-[a-z_]+\.png',old.name) and old.name not in expected_previews:
            old.unlink()  # Only this renderer's stale numbered scene previews.
    for i,scene in enumerate(renderer.scenes):
        renderer.frame(i,scene['durationSeconds']*.65).save(preview/f'{i+1:02d}-{scene["id"]}.png')
    contact=Image.new('RGB',(1920,380*math.ceil(len(renderer.scenes)/3)),BG)
    contact_draw=ImageDraw.Draw(contact)
    for i,scene in enumerate(renderer.scenes):
        x=(i%3)*640;y=(i//3)*380
        im=Image.open(preview/f'{i+1:02d}-{scene["id"]}.png')
        contact.paste(im.resize((640,360),Image.Resampling.LANCZOS),(x,y+20))
        label(contact_draw,(x+5,y),f'{i+1:02d} {scene["id"]}',16,INK)
    contact.save(preview/'contact-sheet.png')
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
    manifest=dict(traceId='graph.riemann.collision_guide.media',createdUtc=datetime.now(timezone.utc).isoformat(),status='rendered',
        width=1280,height=720,fps=FPS,frames=cursor,durationSeconds=cursor/FPS,
        resolutionNote='Chapter is rendered natively at 1280x720; the combined 1080p export upscales this chapter only and preserves the existing 1920x1080 presentation size.',
        video=dict(path=str(video.resolve()),sha256=sha(video),bytes=video.stat().st_size),
        scenes=scenes,voiceClips=clip_evidence,
        captions=dict(path='captions.srt',sha256=sha(args.output/'captions.srt'),timing='Sentence boundaries apportioned by word count within each complete narration clip; not forced-aligned.'),
        illustrations='Quartic root positions and gap curves use explicit formulas. Interaction diagrams are schematic; the all-interval claim comes from the separate analytic proof.',
        inputs=[dict(path=str(p.resolve()),sha256=sha(p)) for p in inputs])
    write_json(args.output/'chapter-manifest.json',manifest)
    write_json(args.output/'voice-production.json',dict(status='produced',clips=clip_evidence))
    print(json.dumps({k:manifest[k] for k in ('status','frames','durationSeconds','video')},indent=2))


if __name__=='__main__':
    main()
