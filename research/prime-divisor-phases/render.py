"""Render scientific figures from the exact divisor-phase analysis.

Requires matplotlib and numpy; analyze.py remains standard-library only.
defines: graph.primes.divisor_phases.render
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Rectangle, Patch
import numpy as np

COLORS=['#b075e4','#f4c155','#38d1ba','#ee6b92']
BG='#0d121e'; PANEL='#182031'; INK='#eef4fc'; MUTED='#b5c4d8'


def style():
    plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':PANEL,
        'text.color':INK,'axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':MUTED,
        'axes.edgecolor':MUTED,'font.family':'DejaVu Sans','font.size':11,
        'savefig.facecolor':BG})


def overview(data,dest):
    fig=plt.figure(figsize=(16,11))
    fig.text(.045,.956,'0–100: FOUR DIVISOR PHASES PER NUMBER',fontsize=24,weight='bold')
    fig.text(.045,.918,'Color = phase quadrant for a divisor. White outlines identify known primes for comparison only.',color=MUTED)
    ax=fig.add_axes([.045,.22,.67,.66]); ax.set_xlim(0,11);ax.set_ylim(10,0);ax.axis('off')
    for row in data['rows']:
        n=row['n']; x=n%11; y=n//11
        ax.add_patch(Rectangle((x+.04,y+.04),.9,.88,facecolor=PANEL,
                              edgecolor=INK if row['classification']=='prime' else '#39455a',
                              linewidth=2 if row['classification']=='prime' else .7))
        ax.text(x+.49,y+.28,str(n),ha='center',va='center',fontsize=12,weight='bold')
        for j,phase in enumerate(row['phases']):
            ax.add_patch(Rectangle((x+.1+j*.195,y+.52),.18,.26,facecolor=COLORS[phase['q45']-1],edgecolor='none'))
    fig.text(.75,.845,'Each tile, left to right:',fontsize=13,weight='bold')
    fig.text(.75,.812,'divisors 2, 3, 5, 7',fontsize=13)
    fig.text(.75,.744,'At the +45° offset',fontsize=14,weight='bold')
    fig.text(.75,.704,'QI (violet) means a divisor\nalignment in that channel.\nIt does not mean “prime”.',fontsize=12,linespacing=1.5,va='top')
    fig.text(.75,.584,'97: III, II, III, IV\nNo divisor alignment.\n99: III, I, IV, II\nThe divisor 3 aligns.',fontsize=12,linespacing=1.6,va='top')
    fig.text(.75,.405,'25 primes, 74 composites\n0 and 1 are neither.\nSmall primes 2, 3, 5, 7\nneed separate treatment.',fontsize=12,linespacing=1.6,va='top')
    handles=[Patch(color=c,label=f'Q{i+1}') for i,c in enumerate(COLORS)]
    fig.legend(handles=handles,loc='lower left',bbox_to_anchor=(.04,.153),ncol=4,frameon=False,fontsize=12)
    fig.text(.045,.133,r'$z_d(n)=e^{2\pi i n/d}$    Color uses $\arg z_d(n)+45^\circ$.  Exact residues supply the phase.',fontsize=14)
    fig.text(.045,.086,'For 8–100, rejecting a violet match in any channel is exact. At 0° it wrongly rejects seven primes.',color=MUTED,fontsize=11)
    fig.text(.045,.054,'This is divisibility visualized with four quadrants. Changing colors or axes does not change divisibility.',color=MUTED,fontsize=11)
    fig.savefig(dest/'divisor-phases-0-100.png',dpi=160)
    fig.savefig(dest/'divisor-phases-0-100.svg')
    plt.close(fig)


def matrix(ax,values,labels,title):
    cmap=ListedColormap(COLORS); norm=BoundaryNorm([.5,1.5,2.5,3.5,4.5],4)
    ax.imshow(values,cmap=cmap,norm=norm,interpolation='nearest',aspect='equal')
    ax.set_xticks(range(len(labels)),labels,rotation=90,fontsize=8)
    ax.set_yticks(range(len(labels)),labels,fontsize=8)
    ax.set_xlabel('Target q',labelpad=8);ax.set_ylabel('Reference p')
    ax.set_title(title,loc='left',fontsize=13,pad=12)


def pairs(data,dest):
    m=data['oddPairMatrix']; labels=m['references']
    raw=np.array(m['rawQ45']); half=np.array(m['halfQ45']); r=np.array(m['rawResidues'])
    joint=np.where((raw==1)&(half==1),np.where(r==0,2,1),0)
    fig=plt.figure(figsize=(18,10))
    fig.text(.045,.953,'PRIME TO PRIME: WHAT DOES THE HALF-STEP VIEW ADD?',fontsize=24,weight='bold')
    fig.text(.045,.911,'Same 24 odd primes in all three panels. Each row uses that prime as its phase reference.',color=MUTED)
    a=fig.add_axes([.05,.34,.26,.50]);b=fig.add_axes([.375,.34,.26,.50]);c=fig.add_axes([.70,.34,.26,.50])
    matrix(a,raw,labels,'Ordinary phase · 104 false alignments')
    matrix(b,half,labels,'Half-step phase · 110 false alignments')
    c.imshow(joint,cmap=ListedColormap([PANEL,'#f4c155','#eef4fc']),vmin=0,vmax=2,interpolation='nearest')
    c.set_xticks(range(24),labels,rotation=90,fontsize=8); c.set_yticks(range(24),labels,fontsize=8)
    c.set_xlabel('Target q',labelpad=8);c.set_ylabel('Reference p')
    c.set_title('Both views agree · 43 false alignments',loc='left',fontsize=13,pad=12)
    fig.legend(handles=[Patch(color=color,label=f'Q{i+1}') for i,color in enumerate(COLORS)],
               bbox_to_anchor=(.043,.265),loc='lower left',ncol=4,frameon=False)
    fig.legend(handles=[Patch(color='#eef4fc',label='Actual self-divisibility'),Patch(color='#f4c155',label='Color alias')],
               bbox_to_anchor=(.688,.252),loc='lower left',frameon=False,ncol=1,fontsize=10)
    fig.text(.05,.225,r'$z_p(q)=e^{2\pi i q/p}$      $H_p(q)=e^{2\pi i ((q-p)/2)/p}$      $H_p(q)^2=z_p(q)$',fontsize=16)
    fig.text(.05,.185,'The identity is before the palette offset. Both views use +45° when assigning quadrant colors.',color=MUTED,fontsize=11)
    fig.text(.05,.132,'False alignments among nondividing pairs',fontsize=12,weight='bold')
    fig.text(.05,.11,'Odd prime targets (552 pairs):     104 ordinary  →  43 combined\nOdd composite targets (555 pairs): 114 ordinary  →  74 combined',fontsize=11,linespacing=1.6,va='top')
    fig.text(.60,.126,'Combining observations retains more phase information.\nThe same effect occurs for odd composites.\nNo prime-specific half-step law or RH result is established.',fontsize=11,color=MUTED,linespacing=1.7,va='top')
    fig.savefig(dest/'prime-pair-half-step.png',dpi=160)
    fig.savefig(dest/'prime-pair-half-step.svg')
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    data=json.loads(args.data.read_text(encoding='utf-8'))
    style(); overview(data,args.output);pairs(data,args.output)
    print('Rendered two PNG/SVG figures.')


if __name__=='__main__':main()
