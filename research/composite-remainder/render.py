"""Render the checked finite odd-factor polynomial through 100.

defines: graph.primes.composite_remainder.visualization
consumer: graph.primes.composite_remainder.table
Colors denote factor contributions, not zeta phase quadrants.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch
import numpy as np

BASE=Path(__file__).resolve().parent
BG='#0c1322'; PANEL='#152034'; TEXT='#eef3fc'; MUTED='#b5c3d8'; GRID='#2b3a51'
COLORS={3:'#52c8b4',5:'#ecc36a',7:'#bd96ec',9:'#73a7f1'}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=BASE/'figures')
    parser.add_argument('--delivery',type=Path)
    args=parser.parse_args()
    data=json.loads((BASE/'evidence/table-0-100.json').read_text(encoding='utf-8'))
    assert data['range']==[0,100]
    rows={r['n']:r for r in data['rows']}
    terms={r['factor']:r['exponents'] for r in data['finiteTerms']}
    assert list(terms)==[3,5,7,9]
    reconstructed=[sum(n in exponents for exponents in terms.values()) for n in range(101)]
    assert reconstructed==[rows[n]['unorderedCoefficient'] for n in range(101)]
    assert reconstructed[97]==0 and reconstructed[99]==2 and reconstructed[81]==2
    assert len(data['oddComposites'])==25 and sum(reconstructed)==30

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.color':TEXT,
        'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,
        'axes.edgecolor':GRID,'svg.fonttype':'none','svg.hashsalt':'composite-remainder-100',
        'savefig.facecolor':BG})
    fig=plt.figure(figsize=(16,9),facecolor=BG)
    fig.text(.045,.95,'A finite formula that marks odd composites',fontsize=26,weight='bold')
    fig.text(.046,.905,'Through 100, four smaller-factor lanes generate all 25 odd composites exactly.',fontsize=14,color=MUTED)
    fig.text(.046,.843,r'$U_{100}(z)=\sum_{d\in\{3,5,7,9\}}\ \sum_{m=0}^{\lfloor(100-d^2)/(2d)\rfloor} z^{d^2+2dm}$',fontsize=20)

    ax=fig.add_axes([.075,.49,.71,.255],facecolor=PANEL)
    ax.set_title('ONE DOT = ONE NONTRIVIAL FACTOR PAIR',loc='left',fontsize=12,pad=15,weight='bold')
    for lane,d in enumerate((9,7,5,3)):
        exponents=terms[d]
        ax.hlines(lane,0,100,color=GRID,linewidth=.7,zorder=0)
        ax.scatter(exponents,[lane]*len(exponents),s=73,color=COLORS[d],zorder=4)
        ax.scatter([d*d],[lane],s=130,facecolors='none',edgecolors=TEXT,marker='s',linewidths=1.25,zorder=5)
    ax.set_yticks(range(4),[r'$d=9$',r'$d=7$',r'$d=5$',r'$d=3$'])
    ax.set_ylim(-.6,3.6);ax.set_xlim(0,102)
    ax.set_xticks(range(0,101,10));ax.tick_params(axis='x',labelbottom=False,length=0)
    ax.tick_params(axis='y',length=0,pad=14,labelsize=13)
    ax.grid(axis='x',color=GRID,linewidth=.7,alpha=.65)
    for side in ('top','right','bottom','left'): ax.spines[side].set_visible(False)
    ax.legend(handles=[Line2D([0],[0],marker='s',linestyle='',markerfacecolor='none',
        markeredgecolor=TEXT,label=r'First term $d^2$: square pair counted once',markersize=8)],
        loc='lower left',bbox_to_anchor=(0,-.22),frameon=False,labelcolor=MUTED,fontsize=10)

    counts=fig.add_axes([.075,.205,.71,.175],facecolor=PANEL,sharex=ax)
    counts.set_title('ADD THE LANES: COEFFICIENT 0 OR A POSITIVE COUNT',loc='left',fontsize=12,pad=14,weight='bold')
    bottom=np.zeros(101,dtype=int)
    positions=np.arange(101)
    for d in (3,5,7,9):
        values=np.array([int(n in terms[d]) for n in range(101)])
        counts.bar(positions,values,bottom=bottom,width=1.12,color=COLORS[d],linewidth=0,zorder=3)
        bottom+=values
    zero_odd=[n for n in range(3,101,2) if reconstructed[n]==0]
    counts.scatter(zero_odd,[0]*len(zero_odd),s=35,facecolors=PANEL,edgecolors=TEXT,linewidths=1,zorder=5)
    counts.set_ylim(-.28,2.45);counts.set_yticks([0,1,2]);counts.set_ylabel(r'$u_n$ = pair count',fontsize=12)
    counts.set_xlabel('Integer n (coefficient index)',labelpad=13,fontsize=12)
    counts.grid(axis='y',color=GRID,linewidth=.7,zorder=0)
    counts.grid(axis='x',color=GRID,linewidth=.7,alpha=.65,zorder=0)
    for side in ('top','right'): counts.spines[side].set_visible(False)
    counts.legend(handles=[Line2D([0],[0],marker='o',linestyle='',markerfacecolor=PANEL,
        markeredgecolor=TEXT,label=r'Zero at odd $n>1$: prime',markersize=6),
        Patch(facecolor=MUTED,label='Positive stack: odd composite')],
        ncol=2,loc='upper left',bbox_to_anchor=(0,-.38),frameon=False,labelcolor=MUTED,fontsize=10,columnspacing=2)

    # Highlight the two nearby candidates without crowded x-axis labels.
    for axis in (ax,counts):
        for n in (97,99): axis.axvline(n,color=TEXT,linewidth=.65,alpha=.22,zorder=1)

    panel=FancyBboxPatch((.817,.205),.158,.54,boxstyle='round,pad=.012,rounding_size=.01',
        transform=fig.transFigure,facecolor=PANEL,edgecolor='none')
    fig.patches.append(panel)
    fig.text(.835,.708,'READ A COEFFICIENT',fontsize=10,color=MUTED,weight='bold')
    examples=[(.65,'97  →  0',TEXT,'No nontrivial odd pair.\n97 is prime.'),
              (.49,'99  →  2',TEXT,'3 × 33  and  9 × 11.\n99 is composite.'),
              (.33,'81  →  2',TEXT,'3 × 27  and  9 × 9.\nThe square pair appears once.')]
    for y,heading,color,body in examples:
        fig.text(.835,y,heading,fontsize=20,color=color,weight='bold')
        fig.text(.835,y-.058,body,fontsize=10.1,color=MUTED,linespacing=1.6,va='top')

    fig.text(.046,.063,'Domain: this zero-count test applies only to odd n > 1.  0 and 1 are neither; 2 is prime; larger evens are composite.',fontsize=10.6,color=MUTED)
    fig.text(.046,.031,'Colors identify factors—not zeta quadrants. Exact divisor enumeration; no new speed advantage or Riemann Hypothesis result is claimed.',fontsize=10.6,color=MUTED)

    args.output.mkdir(parents=True,exist_ok=True)
    png=args.output/'finite-composite-remainder-0-100.png'
    svg=args.output/'finite-composite-remainder-0-100.svg'
    fig.savefig(png,dpi=160,metadata={'Title':'Finite odd-composite factor contributions, 0 to 100'})
    fig.savefig(svg,metadata={'Date':None,'Title':'Finite odd-composite factor contributions, 0 to 100'})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    plt.close(fig)
    report=dict(traceId='graph.primes.composite_remainder.visualization',status='rendered',
        coverage=dict(coefficientIndices=101,factorLanes=4,nontrivialPairDots=30,oddComposites=25,
            zeroOddPrimeMarkers=len(zero_odd),checkedExamples={str(n):reconstructed[n] for n in (81,97,99)}),
        meaning='Factor-lane contributions and exact unordered pair coefficients. Colors are not zeta phase quadrants.',
        inputs=[dict(path=str(p),sha256=sha(p)) for p in (Path(__file__),BASE/'evidence/table-0-100.json')],
        figures=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in (png,svg)])
    (args.output/'render-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if args.delivery:
        args.delivery.mkdir(parents=True,exist_ok=True)
        for file in (png,svg,args.output/'render-report.json'): shutil.copy2(file,args.delivery/file.name)
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
