# Two-state zeta unit-term switch: mathematical audit

defines: graph.riemann.switch.proof

The model is exactly

\[
Z_b(s)=\zeta(s)-1+b,\qquad b\in\{0,1\},
\]

with the nearest-level selector

\[
b_*(s)=
\begin{cases}
1,&|\zeta(s)|\le|\zeta(s)-1|,\\
0,&|\zeta(s)|>|\zeta(s)-1|,
\end{cases}
\qquad W(s)=Z_{b_*(s)}(s).
\]

Ties select \(b_*=1\). All statements below concern exact function values at finite \(s\ne1\). The definitions and elementary identities hold at every such height; they are not a claim that a numerical rendering certifies the zeros at every height.

## The unit term and the prime product

For \(\operatorname{Re}s>1\), the absolutely convergent defining series gives

\[
Z_b(s)=b+\sum_{n=2}^{\infty}n^{-s}.
\]

Thus \(b\) changes only the coefficient of the integer-series term \(1^{-s}=1\). Elsewhere, \(Z_b\) is defined by the displayed formula using the analytic continuation of \(\zeta\), not by treating a divergent ordinary Dirichlet series as convergent. The zeta function is meromorphic, with a simple pole of residue one at \(s=1\). [NIST DLMF 25.2(i)](https://dlmf.nist.gov/25.2.i)

In the same half-plane,

\[
\zeta(s)=\prod_{p\ \mathrm{prime}}(1-p^{-s})^{-1}.
\]

This product already contains the unit term: choosing the constant term from every geometric-series factor yields the empty-product contribution \(1\). Therefore

\[
Z_1(s)=\prod_p(1-p^{-s})^{-1},\qquad
Z_0(s)=\prod_p(1-p^{-s})^{-1}-1.
\]

Switching the unit term among all integers is not adding 1 to the Euler prime product. Adding 1 to that full product would give \(\zeta(s)+1\), a different function. No prime is added or removed by this two-state operation, and 1 is not made a prime. [NIST DLMF 25.2.11](https://dlmf.nist.gov/25.2.E11)

## What the fixed branches preserve

The two branches differ by a real constant:

\[
Z_1-Z_0=1,\qquad
\operatorname{Im}Z_0=\operatorname{Im}Z_1=\operatorname{Im}\zeta.
\]

At every finite regular point,

\[
Z_0'(s)=Z_1'(s)=\zeta'(s),
\qquad Z_0^{(k)}(s)=Z_1^{(k)}(s)=\zeta^{(k)}(s)\quad(k\ge1).
\]

Both branches have the same pole at \(s=1\), with the same residue. Their critical points are the same. Their zeros and logarithmic derivatives are different:

\[
\frac{Z_1'}{Z_1}=\frac{\zeta'}{\zeta},\qquad
\frac{Z_0'}{Z_0}=\frac{\zeta'}{\zeta-1}
\]

where the respective denominators are nonzero. In particular, equal ordinary derivatives do not imply equal phase velocities or equal zero locations.

For any two finite regular points \(s,c\) and one fixed branch \(b\),

\[
\boxed{Z_b(s)-Z_b(c)=\zeta(s)-\zeta(c).}
\]

A local-origin picture made only from these fixed-branch differences cannot distinguish the two branches. Subtracting the local origin has canceled precisely the constant that distinguishes their zero levels.

For a branch that is allowed to vary between points, the exact formula instead is

\[
\boxed{W(s)-W(c)=\zeta(s)-\zeta(c)+b_*(s)-b_*(c).}
\]

The additional term is \(-1,0,\) or \(1\). It is imposed by the selector; it is not a new term in the analytic derivative of \(\zeta\).

## The selector and its zero set

Write \(\zeta(s)=u+iv\). Then

\[
|\zeta(s)|^2-|\zeta(s)-1|^2
=u^2+v^2-\bigl((u-1)^2+v^2\bigr)=2u-1.
\]

Consequently,

\[
\boxed{b_*(s)=1\ \Longleftrightarrow\ \operatorname{Re}\zeta(s)\le\tfrac12,}
\]

and

\[
W(s)=
\begin{cases}
\zeta(s),&\operatorname{Re}\zeta(s)\le\tfrac12,\\
\zeta(s)-1,&\operatorname{Re}\zeta(s)>\tfrac12.
\end{cases}
\]

The fixed-branch zero sets are

\[
Z_1(s)=0\ \Longleftrightarrow\ \zeta(s)=0,
\qquad
Z_0(s)=0\ \Longleftrightarrow\ \zeta(s)=1.
\]

A point with \(\zeta(s)=1\) is called a 1-point, not a zero of zeta. At a zeta zero the selector chooses \(b_*=1\); at a 1-point it chooses \(b_*=0\). Conversely, either possible way for \(W\) to vanish gives one of those two levels. Therefore

\[
\boxed{\{s:W(s)=0\}=\{s:\zeta(s)=0\}\ \mathbin{\dot\cup}\ \{s:\zeta(s)=1\}.}
\]

The union is disjoint. Near a zeta zero, continuity makes the selector constantly 1. Near a 1-point it is constantly 0. Hence \(W\) is holomorphic in a neighborhood of each of its zeros individually, and their local multiplicities equal the corresponding multiplicities of \(\zeta\) or \(\zeta-1\). This does not make \(W\) holomorphic between those neighborhoods.

The selector also gives useful continuous real-valued data:

\[
\operatorname{Im}W=\operatorname{Im}\zeta,
\qquad
|W|=\min\bigl(|\zeta|,|\zeta-1|\bigr),
\]

and

\[
|W|^2=v^2+\min\bigl(u^2,(u-1)^2\bigr).
\]

Both the imaginary component and magnitude are continuous away from the pole, even where the complex-valued selected map is discontinuous.

## Every finite switching-boundary point is a discontinuity

Define the switching boundary

\[
\mathcal B=\{s\ne1:\operatorname{Re}\zeta(s)=\tfrac12\}.
\]

At a boundary point \(s_0\), write \(\zeta(s_0)=\tfrac12+iv_0\). Approaching through the side \(\operatorname{Re}\zeta<1/2\) gives the limit

\[
\tfrac12+iv_0,
\]

while approaching through \(\operatorname{Re}\zeta>1/2\) gives

\[
-\tfrac12+iv_0.
\]

Both types of approach exist at every \(s_0\in\mathcal B\). Indeed, \(\zeta\) is holomorphic and nonconstant on any sufficiently small disk around \(s_0\). By the open mapping theorem, the image of every such disk contains an open neighborhood of \(\zeta(s_0)\), hence values on both sides of the vertical line \(\operatorname{Re}w=1/2\). Taking shrinking disks produces both approaching sequences.

The two limits differ by exactly \(-1\) when moving from the smaller-real-part side to the larger-real-part side. The tie rule assigns the first limit at the boundary itself. Thus \(W\) is discontinuous at every finite boundary point, and cannot be holomorphic there.

There is no exception merely because \(\zeta'(s_0)=0\). The first nonzero Taylor term then has some higher finite order; the open mapping argument still applies. This statement concerns the two-dimensional function. A particular path can stay on one selector side, or run along the boundary with the tie branch, and have a continuous restriction. A tangential path approaching only from the other branch can instead have a spike at its tie point. Neither behavior repairs the discontinuity in a full neighborhood.

At all boundary points,

\[
|W(s_0)|=\sqrt{\tfrac14+v_0^2}\ge\tfrac12.
\]

So a boundary point is never an actual selected zero. If a renderer draws a straight connecting segment across the unit jump, that segment passes through zero when \(v_0=0\). Such a drawn crossing is an interpolation artifact: neither of the two limiting values, nor the tie value, is zero.

## Which zero-counting arguments are valid

The argument principle applies separately to each fixed meromorphic branch on a domain with a suitable closed contour avoiding its zeros and pole. It does not apply to \(W\) as though \(W\) were one meromorphic function across \(\mathcal B\).

In particular, a contour whose selected image jumps is not a continuous closed curve in \(\mathbb C\setminus\{0\}\). Its usual winding number is not defined without an added rule for connecting the jumps. A program that connects the endpoints or unwraps their phases has introduced extra choices. Different connecting paths can add different windings, and a straight connector can itself hit zero. Integrating the ordinary branch derivatives on the continuous pieces does not account for the jumps and is not an argument-principle certificate for \(W\).

If a closed contour lies in one fixed-selector region, use the corresponding fixed function \(\zeta\) or \(\zeta-1\) and its usual hypotheses. Any resulting count is a count for that fixed function, not automatically for the selected zero union throughout the interior.

There is a simple analytic control for the union:

\[
G(s)=\zeta(s)\bigl(\zeta(s)-1\bigr)=Z_1(s)Z_0(s).
\]

Its zeros are exactly the same disjoint union as the zeros of \(W\), with the same local multiplicities. It is meromorphic and has a double pole at \(s=1\). Where defined,

\[
\frac{G'}G=\frac{\zeta'}\zeta+\frac{\zeta'}{\zeta-1}.
\]

For a positively oriented simple closed contour with neither a zeta zero, a 1-point, nor the pole on it, the argument principle for \(G\) counts

\[
\frac1{2\pi i}\oint\frac{G'}G\,ds
=N_{\zeta=0}+N_{\zeta=1}-2N_{\mathrm{pole}},
\]

with the enclosed zeros counted by multiplicity and \(N_{\mathrm{pole}}=1\) if \(s=1\) is enclosed and 0 otherwise. This analytic product avoids the selector's artificial jumps. It deliberately counts both target levels and does not distinguish one type from the other unless the branch labels are retained.

## What the experiment can establish

The switch is a nearest-of-two-values rule applied to an already defined complex function. Its exact predictions provide useful implementation controls: a real unit translation between the fixed branches, equal imaginary components and ordinary derivatives, the boundary \(\operatorname{Re}\zeta=1/2\), a unit jump there, and a selected zero set consisting of two separately labeled levels. These conclusions follow from elementary algebra and local complex analysis; no mathematical novelty is claimed.

For numerical classification, an approximation \(\widehat\zeta\) with a certified complex error bound \(\varepsilon\) determines the correct branch whenever

\[
\left|\operatorname{Re}\widehat\zeta-\tfrac12\right|>\varepsilon.
\]

Closer to the boundary, the branch cannot in general be certified from that error bound alone. A finite-resolution color change is not itself evidence for a new zero or an analytic singularity.

The Riemann Hypothesis concerns the nontrivial zeros of \(\zeta\), requiring them to have \(\operatorname{Re}s=1/2\). The selector boundary \(\operatorname{Re}\zeta(s)=1/2\) is a condition on the function value, not that critical line in the input plane. The two conditions must not be conflated. [NIST DLMF 25.10(i)](https://dlmf.nist.gov/25.10.i)

Every actual zeta zero is retained by the switch. Thus a hypothetical off-critical-line zero would also remain a selected zero; the selection rule cannot remove it or force it onto the critical line. Additional 1-points are included as well. Proving the displayed identities at all regular inputs supplies no new restriction on where either level is attained, and leaves the Riemann Hypothesis open.
