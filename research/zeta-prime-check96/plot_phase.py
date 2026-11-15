"""Render the recorded zeta comparison. Labels come from the separate integer check."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); data=json.loads(a.data.read_text(encoding='utf-8'))
    palette=['#1b735e','#886627','#653c85','#274d88']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig=plt.figure(figsize=(13.5,10),facecolor='#f6f8fc')
    grid=fig.add_gridspec(2,2,height_ratios=[1.25,1],hspace=.44,wspace=.28)
    fig.suptitle('Does zeta phase distinguish 96 from 97?',x=.06,ha='left',fontsize=23,fontweight='bold',y=.97)
    fig.text(.06,.918,r'Actual $\zeta(\frac{1}{2}+in)$  |  current phase sectors, target 0, no rotation',fontsize=13,color='#42526c')
    ax=fig.add_subplot(grid[0,0]); ax.set_title('Output plane: adjacent integer heights',loc='left',pad=12,fontweight='bold')
    for (x,y,w,h),color in zip([(0,0,2.7,2.6),(-.55,0,.55,2.6),(-.55,-1.3,.55,1.3),(0,-1.3,2.7,1.3)],palette):
        ax.add_patch(Rectangle((x,y),w,h,color=color,alpha=.12))
    ax.axhline(0,color='#9aa6b8',lw=.8); ax.axvline(0,color='#9aa6b8',lw=.8)
    for n,offset in [(95,(10,-18)),(96,(9,9)),(97,(9,9)),(98,(-25,-17)),(99,(9,8))]:
        r=data['rows'][n]; x,y=float(r['real']),float(r['imaginary'])
        ax.plot(x,y,'o',ms=9,color=palette[r['quadrant']-1],markeredgecolor='white')
        ax.annotate(str(n),(x,y),xytext=offset,textcoords='offset points',fontsize=13,fontweight='bold')
    ax.set(xlim=(-.55,2.7),ylim=(-1.3,2.6),xlabel=r'$\operatorname{Re}\zeta$',ylabel=r'$\operatorname{Im}\zeta$')
    ax=fig.add_subplot(grid[0,1]); ax.axis('off')
    ax.set_title('Exact labels compared with numerical phase',loc='left',pad=12,fontweight='bold')
    cols=['n','Integer result','Phase','Sector']
    rows=[]
    for n in (95,96,97,98,99):
        r=data['rows'][n]
        rows.append([n,r['classification'],f"{float(r['phaseDegrees']):.2f}°",['I','II','III','IV'][r['quadrant']-1]])
    table=ax.table(cellText=rows,colLabels=cols,loc='upper left',cellLoc='left',colLoc='left',bbox=[0,.39,1,.61],colWidths=[.12,.38,.27,.23])
    table.auto_set_font_size(False);table.set_fontsize(12)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('#d9e0ec');cell.set_linewidth(.7)
        if r==0:cell.set_facecolor('#e6ebf5');cell.set_text_props(weight='bold')
        else:cell.set_facecolor('white')
    ax.text(0,.27,'97 shares its sector with 95 and 99.\nThose two controls are composite.',fontsize=14,fontweight='bold',va='top')
    ax.text(0,.10,'Color comes only from zeta phase.\nPrimality labels come from exact divisibility.',fontsize=11,color='#42526c',va='top')
    ax=fig.add_subplot(grid[1,0]); qs=data['quadrants']; x=np.arange(4);w=.34
    ax.bar(x-w/2,[r['primeCount'] for r in qs],w,label='Prime heights',color='#9b62c4')
    ax.bar(x+w/2,[r['compositeCount'] for r in qs],w,label='Composite heights',color='#697a93')
    ax.set_title('Every phase sector contains both classes',loc='left',pad=12,fontweight='bold')
    ax.set(xticks=x,xticklabels=['I','II','III','IV'],ylabel='Number of integer heights',xlabel='Phase sector',ylim=(0,45))
    ax.legend(frameon=False,loc='upper right',fontsize=10)
    for i,r in enumerate(qs):
        ax.text(i-w/2,r['primeCount']+.6,str(r['primeCount']),ha='center',fontsize=10)
        ax.text(i+w/2,r['compositeCount']+.6,str(r['compositeCount']),ha='center',fontsize=10)
    ax=fig.add_subplot(grid[1,1]);ax.axis('off')
    ax.set_title('What the comparison establishes',loc='left',pad=12,fontweight='bold')
    ax.text(0,.92,'96 = 2 × 48: composite.\n97 has no divisor from 2 through 9: prime.',fontsize=13,va='top',linespacing=1.6)
    ax.text(0,.62,'Using sector I as “candidate prime” selects\n10 primes and 33 composites, while missing\n15 primes in the integer range 2–100.',fontsize=12,va='top',linespacing=1.55)
    ax.text(0,.26,'This fixed quadrant rule fails.\nRicher zeta-based methods need a separate\nformula, validation and speed comparison.',fontsize=12,va='top',linespacing=1.55)
    fig.text(.06,.045,'Numerical checks: 50 vs 80 digits; second evaluator method on examples. No interval certificate or RH claim.',fontsize=10,color='#42526c')
    fig.text(.06,.023,'Trace: graph.primes.zeta_check96   •   0 and 1 excluded from the prime/composite sector counts.',fontsize=10,color='#42526c')
    fig.subplots_adjust(left=.07,right=.97,top=.86,bottom=.12)
    a.output.mkdir(parents=True,exist_ok=True)
    fig.savefig(a.output/'zeta-phase-96-97.png',dpi=150)
    fig.savefig(a.output/'zeta-phase-96-97.svg')
    plt.close(fig)
    render_shift(data,a.output,palette)


def render_shift(data,out,palette):
    fig=plt.figure(figsize=(14,10),facecolor='#f6f8fc')
    grid=fig.add_gridspec(2,2,height_ratios=[1,1.05],hspace=.43,wspace=.28)
    fig.suptitle('Comparing zeta(s) with zeta(s + 1)',x=.06,ha='left',fontsize=24,fontweight='bold',y=.97)
    fig.text(.06,.918,r'$s=\frac{1}{2}+in$: shift the input from real part 0.5 to 1.5; keep the same integer height.',fontsize=13,color='#42526c')
    examples=[95,96,97,98,99]
    for column,shifted in enumerate((False,True)):
        ax=fig.add_subplot(grid[0,column])
        ax.set_title(r'Secondary: $\zeta(s+1)$' if shifted else r'Original: $\zeta(s)$',loc='left',fontsize=15,fontweight='bold',pad=12)
        ax.axhline(0,color='#9aa6b8',lw=.9);ax.axvline(0,color='#9aa6b8',lw=.9)
        for n in examples:
            row=data['rows'][n];r=row['shifted'] if shifted else row
            x,y=float(r['real']),float(r['imaginary'])
            ax.plot(x,y,'o',ms=10,color=palette[r['quadrant']-1],markeredgecolor='white')
            offset=(9,7)
            if shifted and n==95:offset=(8,-18)
            ax.annotate(str(n),(x,y),xytext=offset,textcoords='offset points',fontsize=12,fontweight='bold')
        if shifted:ax.set(xlim=(.4,1.48),ylim=(-.09,.58))
        else:ax.set(xlim=(-.45,2.7),ylim=(-1.2,2.45))
        ax.set(xlabel='Real part of output',ylabel='Imaginary part of output')
        ax.grid(alpha=.12)
    ax=fig.add_subplot(grid[1,0]);ax.axis('off')
    ax.set_title('Original and secondary phases',loc='left',fontsize=15,fontweight='bold',pad=12)
    rows=[]
    roman=['I','II','III','IV']
    for n in examples:
        r=data['rows'][n];other=r['shifted']
        rows.append([n,r['classification'],f"{float(r['phaseDegrees']):.2f}°",f"{float(other['phaseDegrees']):.2f}°",roman[r['quadrant']-1]+', '+roman[other['quadrant']-1]])
    table=ax.table(cellText=rows,colLabels=['n','Exact class','Original','Secondary','Pair'],cellLoc='left',colLoc='left',bbox=[0,.36,1,.64],colWidths=[.09,.26,.22,.24,.19])
    table.auto_set_font_size(False);table.set_fontsize(11)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('#d9e0ec');cell.set_linewidth(.7)
        cell.set_facecolor('#e6ebf5' if r==0 else 'white')
        if r==0:cell.set_text_props(weight='bold')
    ax.text(0,.23,'The pair rejects composite 95, but retains 99.\nBoth 97 and 99 have the pair (I, I).',fontsize=13,fontweight='bold',va='top',linespacing=1.5)
    ax.text(0,.03,'Exact divisibility labels are comparison data,\nnot inputs to the zeta evaluations.',fontsize=11,color='#42526c',va='top')
    ax=fig.add_subplot(grid[1,1]);x=np.arange(3);w=.34
    ax.bar(x-w/2,[10,33,15],w,label='Original sector I',color='#94a6bc')
    ax.bar(x+w/2,[7,28,18],w,label='Pair (I, I)',color='#1b735e')
    ax.set_title('What the filter does on integers 2–100',loc='left',fontsize=15,fontweight='bold',pad=12)
    ax.set(xticks=x,xticklabels=['Primes kept','Composites kept','Primes missed'],ylim=(0,44),ylabel='Count')
    ax.legend(frameon=False,loc='upper right',fontsize=10)
    for i,(before,after) in enumerate(zip([10,33,15],[7,28,18])):
        ax.text(i-w/2,before+.6,str(before),ha='center',fontsize=11)
        ax.text(i+w/2,after+.6,str(after),ha='center',fontsize=11)
    fig.text(.06,.055,'Result: 5 false positives removed, but 3 additional primes rejected. The paired colors do not establish primality.',fontsize=12,fontweight='bold')
    fig.text(.06,.028,'50/80-digit numerical checks on both lines. No interval or RH certificate. Trace: graph.primes.zeta_check96',fontsize=10,color='#42526c')
    fig.subplots_adjust(left=.075,right=.97,top=.86,bottom=.16)
    fig.savefig(out/'zeta-shift-96-97.png',dpi=150)
    fig.savefig(out/'zeta-shift-96-97.svg')
    plt.close(fig)

if __name__=='__main__':main()
