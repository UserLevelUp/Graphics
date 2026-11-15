# Finite-polynomial interaction bound

defines: graph.riemann.gap.proof
consumer: graph.riemann.collision.proof

This document proves a quantitative interval in which a finite polynomial remains real-rooted with simple roots under the backward heat equation. The proof uses the interaction between all its roots. It makes no claim of novelty and gives no Riemann Hypothesis result or transfer to an infinite entire-function flow.

## Assumptions and main theorem

Let \(P_0\) be a real polynomial of degree \(n\ge3\), with distinct real roots

\[
r_1(0)<\cdots<r_n(0).
\]

A constant nonzero leading coefficient can be divided out, so assume the polynomial is monic. Define its exact finite heat evolution by

\[
P_t(z)=e^{-t\partial_z^2}P_0(z)
=\sum_{j=0}^{\lfloor n/2\rfloor}\frac{(-t)^j}{j!}\partial_z^{2j}P_0(z).
\]

Thus \(\partial_tP_t=-\partial_z^2P_t\), with the leading coefficient and degree fixed for every real \(t\). Write

\[
m=\min_{1\le i<n}\bigl(r_{i+1}(0)-r_i(0)\bigr)>0,
\qquad D_0=r_n(0)-r_1(0)>0,
\qquad \kappa=\frac{n-2}{D_0^2}>0.
\]

Then every root is real and simple throughout \(-T<t\le0\), where

\[
\boxed{T=-\frac{\log(1-\kappa m^2/2)}{4\kappa}.}
\]

At \(t=-T\) all roots are still real, counted with multiplicity; the theorem does not require simplicity at this endpoint. If \(t_c<0\) is the first collision encountered as time decreases from zero, the conclusion is \(t_c\le-T\). Equivalently, the elapsed time to a collision is at least \(T\).

The logarithm is well-defined. Indeed, summing the initial gaps gives \(D_0\ge(n-1)m\), so

\[
0<\frac{\kappa m^2}{2}
\le\frac{n-2}{2(n-1)^2}<1.
\]

Moreover, \(-\log(1-x)>x\) for \(0<x<1\), and consequently

\[
\boxed{T>\frac{m^2}{8}.}
\]

## Root motion and the exact gap identity

On an interval where all roots are real and simple, implicit differentiation of \(P_t(r_i(t))=0\) gives

\[
r_i'(t)=\frac{P_{zz}(t,r_i(t))}{P_z(t,r_i(t))}
=2\sum_{j\ne i}\frac1{r_i(t)-r_j(t)}.
\]

For the second equality, factor \(P_t(z)=(z-r_i)Q_i(z)\). At \(r_i\), \(P_z=Q_i\), \(P_{zz}=2Q_i'\), and \(Q_i'/Q_i=\sum_{j\ne i}(r_i-r_j)^{-1}\).

For an adjacent pair \(a=r_i(t)\), \(b=r_{i+1}(t)\), put \(g=b-a>0\). Every other root lies outside \([a,b]\). Subtracting the two velocity equations yields

\[
\begin{aligned}
g'&=\frac4g+2\sum_{r\ne a,b}\left(\frac1{b-r}-\frac1{a-r}\right)\\
&=\frac4g-2gS,
\qquad
S=\sum_{r\ne a,b}\frac1{(b-r)(a-r)}>0.
\end{aligned}
\]

In particular, for \(y=g^2\),

\[
\boxed{y'=8-4yS.}
\]

The adjacency hypothesis matters: it makes every denominator in \(S\) positive. This formula is not the same inequality for an arbitrary nonadjacent pair.

## A uniform interaction lower bound

Let \(D(t)=r_n(t)-r_1(t)\). The leftmost velocity is negative and the rightmost velocity is positive. Therefore \(D'(t)>0\) while all roots are simple and real. In backward time,

\[
D(t)\le D_0\qquad(t\le0).
\]

For each root \(r\) exterior to an adjacent pair,

\[
0<(b-r)(a-r)=|b-r|\,|a-r|\le D(t)^2\le D_0^2.
\]

There are \(n-2\) such roots, hence

\[
S(t)\ge\frac{n-2}{D_0^2}=\kappa.
\]

The exact gap identity consequently implies

\[
y'+4\kappa y\le8.
\]

Multiply by \(e^{4\kappa t}\) and integrate from a negative time \(t\) to zero. The direction of this integration is essential:

\[
y(0)-e^{4\kappa t}y(t)
\le\frac2\kappa\bigl(1-e^{4\kappa t}\bigr).
\]

Rearrangement gives the lower bound

\[
\boxed{
 g_i(t)^2\ge\frac2\kappa+
 \left(g_i(0)^2-\frac2\kappa\right)e^{-4\kappa t}
 \ge\frac2\kappa+
 \left(m^2-\frac2\kappa\right)e^{-4\kappa t}.
}
\]

The final expression is positive exactly for \(-T<t\le0\), and is zero at \(t=-T\).

## First-collision bootstrap and continuation

The preceding calculations were made only while roots were simple and real. They do not assume that this interval already reaches \(-T\).

At time zero the implicit function theorem supplies such an interval. Continue the ordered real simple roots backward along its maximal connected interval ending at zero. At any finite endpoint the roots cannot escape to infinity: all coefficients of the monic polynomial \(P_t\) are polynomial functions of \(t\), so on a bounded time interval their absolute values are bounded, and a monic-polynomial root bound bounds every root uniformly.

If a finite endpoint had all gaps bounded away from zero, bounded roots would converge to distinct real roots of the endpoint polynomial. The implicit function theorem would continue those roots as distinct real roots past the endpoint, contradicting maximality. Here the limits also follow directly from the velocity formula: with all gaps bounded below and finitely many roots, all velocities are bounded. Thus the only possible finite obstruction is a collision of an adjacent pair, possibly as part of a larger simultaneous collision.

Suppose that obstruction occurred at \(t_c>-T\). The uniform gap lower bound above remains strictly positive as \(t\downarrow t_c\). No gap can then collapse, a contradiction. Hence every root remains simple and real throughout \((-T,0]\). Boundedness and continuity of the polynomial roots give real roots, with multiplicity allowed, at \(-T\) as well. This proves the theorem without presupposing its continuation conclusion.

## Degree two and covariance

For \(n=2\), write the two initial roots as \(c\pm m/2\). The normalized flow is exactly

\[
P_t(z)=(z-c)^2-\frac{m^2}{4}-2t,
\qquad g(t)^2=m^2+8t.
\]

Its first collision occurs exactly at \(t=-m^2/8\). This is also the \(\kappa\to0\) limit of the main bound. Degree one has a constant root and no collision.

Translation of every root leaves gaps, diameter, and the bound unchanged. If every root is changed to \(ar+b\), with real \(a\ne0\), define the corresponding monic flow by

\[
\widetilde P_t(z)=a^nP_{t/a^2}\left(\frac{z-b}{a}\right).
\]

It satisfies the same heat equation. Its initial minimum gap and diameter are \(|a|m\) and \(|a|D_0\), so \(\widetilde\kappa=\kappa/a^2\) and \(\widetilde T=a^2T\). Thus the certified interval has the same translation and scale covariance as the exact flow; a choice of origin or display units cannot improve the mathematical certificate.

## Quartic calibration

For initial roots \(-3,-1,1,3\), one has \(n=4\), \(m=2\), \(D_0=6\), and \(\kappa=1/18\). The interaction bound gives

\[
T=\frac92\log\frac98
=0.5300236604537255\ldots.
\]

The bound obtained by discarding all exterior interactions is \(m^2/8=1/2\). The exact polynomial

\[
P_t(z)=z^4-(10+12t)z^2+9+20t+12t^2
\]

has its first backward collisions at \(t=-2/3\), where \(P_{-2/3}(z)=(z^2-1)^2\). Thus the new bound improves the guaranteed duration from \(0.5\) to approximately \(0.530024\), while the exact duration is \(2/3\). It is a lower bound on the elapsed safe time, not an exact collision predictor. The exact threshold is proved in `research/collision-proof/exact-quartic-proof.md`.

## Appendix: allowing the diameter to contract

A further finite-polynomial bound follows by using a time-dependent diameter estimate. Set

\[
d=D_0^2,\qquad B=16n-24,\qquad A=4(n-2),\qquad q=\frac AB.
\]

Let \(a=r_1\), \(b=r_n\), and \(D=b-a\). The interaction between the two extreme roots contributes \(4/D\) to \(D'\). Each interior root \(r\), with \(x=r-a\in(0,D)\), contributes

\[
2\left(\frac1{b-r}+\frac1{r-a}\right)
=\frac{2D}{x(D-x)}\ge\frac8D.
\]

Consequently,

\[
D'\ge\frac{8n-12}{D},\qquad (D^2)'\ge B,
\qquad \boxed{D(t)^2\le d+Bt}\quad(t\le0)
\]

as long as all roots are simple and real. This yields, wherever \(d+Bt>0\),

\[
S(t)\ge\frac{n-2}{d+Bt},\qquad
 y'+\frac{A}{d+Bt}y\le8.
\]

Writing \(R(t)=1+Bt/d\), the integrating factor is \((d+Bt)^q\). Integration from \(t\) to zero, followed by \(y(0)\ge m^2\), gives

\[
\boxed{
 y(t)\ge R(t)^{-q}
 \left[m^2-\frac{8d}{A+B}\left(1-R(t)^{1+q}\right)\right].
}
\]

Put

\[
\eta=\frac{(A+B)m^2}{8d}
=\frac{(5n-8)m^2}{2d}.
\]

Initial gap packing guarantees

\[
0<\eta\le\frac{5n-8}{2(n-1)^2}<1\quad(n\ge3),
\]

because \(2(n-1)^2-(5n-8)=(2n-5)(n-2)>0\). The right side of the gap bound is positive for \(-T_{\rm dyn}<t\le0\), where

\[
\boxed{
 T_{\rm dyn}=\frac{D_0^2}{B}
 \left[1-\left(1-\frac{(A+B)m^2}{8D_0^2}\right)^{B/(A+B)}\right].
}
\]

In particular \(0<T_{\rm dyn}<d/B\), so the denominator used in the proof stays positive on this entire proposed interval. Apply the same first-collision bootstrap and no-escape argument to conclude that all roots are simple and real on \((-T_{\rm dyn},0]\), and real with multiplicity allowed at its left endpoint.

This bound strictly improves the constant-diameter bound. To see the direction without relying on a series approximation, use elapsed time \(u=-t\). Let \(C(u)\) and \(L(u)\) be the constant and time-dependent gap lower-bound functions with common initial value \(m^2\). They solve

\[
C'=-8+\frac{A}{d}C,
\qquad L'=-8+\frac{A}{d-Bu}L.
\]

If the first zero of \(L\) occurred no later than the first zero of \(C\), then before that time \(C>0\), and their difference \(H=L-C\) would satisfy

\[
H'=\frac{A}{d-Bu}H+
 \left(\frac{A}{d-Bu}-\frac{A}{d}\right)C,
\qquad H(0)=0.
\]

The forcing is strictly positive for \(u>0\). Its integrating-factor formula therefore gives \(H>0\), including at the proposed first zero of \(L\), a contradiction. Hence \(T_{\rm dyn}>T>m^2/8\).

For the quartic, \(d=36\), \(A=8\), \(B=40\), and \(\eta=2/3\), so

\[
T_{\rm dyn}=\frac9{10}\left(1-3^{-5/6}\right)
=0.5397189134471992\ldots<\frac23.
\]

## Scope of the result

Both certificates assume a fixed finite degree, initially distinct real roots, and the specified heat equation. The finite sum for \(S\), finite diameter, coefficient root bound, and continuation argument are essential to this proof. They do not provide a certificate for the Riemann xi function or its heat deformation, whose infinitely many zeros have no finite global diameter. Establishing an appropriate infinite-system estimate would require additional hypotheses and a separate proof. Numerical agreement or a four-color rendering cannot supply that missing argument.
