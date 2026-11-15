# Exact quartic collision proof

defines: graph.riemann.collision.proof
consumer: graph.zeros.motion.model

For every real parameter \(\tau\), define

\[
P_\tau(z)=z^4-(10+12\tau)z^2+(9+20\tau+12\tau^2).
\]

The exact result is that all four zeros, counted with multiplicity, are real if and only if

\[
\boxed{\tau\ge -\frac23.}
\]

Starting at \(\tau=0\) and decreasing the parameter, the first collisions occur at \(\tau=-2/3\), simultaneously at \(z=-1\) and \(z=1\). Each collision produces a double zero. The proof below uses polynomial algebra throughout.

The sign convention agrees with the backward heat equation \(\partial_\tau P_\tau=-\partial_z^2P_\tau\). The same convention follows by differentiating the defining integral for the de Bruijn–Newman deformation used by Rodgers and Tao. The polynomial considered here is a finite calibration of the flow equation. [Rodgers and Tao, *The De Bruijn–Newman constant is non-negative*](https://arxiv.org/abs/1801.05914)

At parameter zero,

\[
P_0(z)=(z^2-1)(z^2-9)=z^4-10z^2+9.
\]

Writing \(D=\partial_z\), we have

\[
D^2P_0=12z^2-20,\qquad D^4P_0=24,\qquad D^6P_0=0.
\]

The operator exponential therefore terminates exactly,

\[
\begin{aligned}
e^{-\tau D^2}P_0
&=P_0-\tau D^2P_0+\frac{\tau^2}{2}D^4P_0\\
&=z^4-(10+12\tau)z^2+9+20\tau+12\tau^2\\
&=P_\tau.
\end{aligned}
\]

Direct differentiation also checks the sign,

\[
\partial_\tau P_\tau=-12z^2+20+24\tau
=-\partial_z^2P_\tau.
\]

Set \(w=z^2\), \(A=10+12\tau\), and \(B=9+20\tau+12\tau^2\). The equation becomes \(w^2-Aw+B=0\). Its discriminant is

\[
\begin{aligned}
D_w&=A^2-4B\\
&=64+160\tau+96\tau^2\\
&=96(\tau+1)\left(\tau+\frac23\right).
\end{aligned}
\]

The constant term is strictly positive for every real parameter,

\[
B=12\left(\tau+\frac56\right)^2+\frac23>0.
\]

Thus the two \(w\)-roots are nonzero, and when they are real they have the same sign. Their sum is \(A\). Explicitly,

\[
w_\pm=5+6\tau\pm\frac12\sqrt{96(\tau+1)(\tau+2/3)}.
\]

For \(\tau\ge-2/3\), the discriminant is nonnegative and \(A\ge2>0\). Both \(w\)-roots are positive, so their positive and negative square roots give four real zeros of \(P_\tau\), counting multiplicity. For \(\tau>-2/3\), the discriminant is strictly positive and all four zeros are distinct. At the endpoint,

\[
P_{-2/3}(z)=z^4-2z^2+1=(z^2-1)^2.
\]

For \(-1<\tau<-2/3\), the discriminant is negative. The \(w\)-roots are a nonreal conjugate pair. Their square roots form four distinct zeros \(a+ib,a-ib,-a+ib,-a-ib\), with \(a,b\ne0\). There are no real or purely imaginary zeros in this parameter interval.

For \(\tau\le-1\), the discriminant is again nonnegative, but now \(A\le-2<0\). Both \(w\)-roots are negative. All four \(z\)-zeros are consequently purely imaginary and nonzero. At \(\tau=-1\),

\[
P_{-1}(z)=z^4+2z^2+1=(z^2+1)^2,
\]

so the zeros are \(i\) and \(-i\), each of multiplicity two. For \(\tau<-1\), the four purely imaginary zeros are distinct. In particular, the second discriminant zero at \(-1\) does not restore real zeros. These three parameter cases establish the claimed equivalence for every real \(\tau\).

To audit the local predictor, fix a center \(c\) at \(\tau=0\), and write \(u=z-c\). Put

\[
a=P_0(c),\qquad b=P_0'(c),\qquad d=P_0''(c).
\]

When \(d\ne0\), the frozen local quadratic evolved by the same heat equation is

\[
Q(u,\delta)=a+bu+\frac d2u^2-d\delta.
\]

Its spatial discriminant is

\[
\Delta_Q(\delta)=b^2-2d(a-d\delta)
=\Delta_c+2d^2\delta,
\qquad \Delta_c=b^2-2ad.
\]

Its predicted collision decrement and location are therefore

\[
\widehat{\delta}_c=-\frac{\Delta_c}{2d^2},
\qquad \widehat z_c=c-\frac bd.
\]

The following entries are exact rational calculations.

| Center \(c\) | \(P_0(c)\) | \(P_0'(c)\) | \(P_0''(c)\) | \(\Delta_c\) | Predicted \(\widehat\delta_c\) | Predicted \(\widehat z_c\) |
|---|---|---|---|---|---|---|
| \(0\) | \(9\) | \(0\) | \(-20\) | \(360\) | \(-9/20\) | \(0\) |
| \(2\) | \(-15\) | \(-8\) | \(28\) | \(904\) | \(-113/196\) | \(16/7\) |
| \(-2\) | \(-15\) | \(8\) | \(28\) | \(904\) | \(-113/196\) | \(-16/7\) |

All three adjacent gaps in the initial root list \(-3,-1,1,3\) have size \(g=2\). An isolated pair with that spacing has polynomial \(z^2-g^2/4\), whose backward heat evolution is \(z^2-g^2/4-2\tau\). Its collision estimate is consequently

\[
\widehat\delta_{\rm gap}=-\frac{g^2}{8}=-\frac12.
\]

The local estimates and the gap estimate all lie strictly above the actual first collision parameter,

\[
-\frac23<-\frac{113}{196}<-\frac12<-\frac9{20}<0.
\]

The exact classification proves that the quartic still has four distinct real zeros at every predicted parameter in this list. Thus these estimates are not exact collision times for this quartic. They also fail a claim that decreasing the parameter by the predicted amount must already produce a collision. The three centers in this table establish failure of exactness and of the stated collision-by-decrement guarantee.

The center-zero forecast fails even as a prediction of the eventual collision location. The strictly positive formula for \(B\) gives

\[
P_\tau(0)>0\quad\text{for every real }\tau.
\]

The center \(0\) never becomes a zero. At its predicted parameter the exact value is

\[
P_{-9/20}(0)=\frac{243}{100}>0.
\]

The lost terms can be displayed exactly. At any center \(c\),

\[
\begin{aligned}
P_\tau(c+u)-Q(u,\tau)
&=4cu^3+u^4-24c\tau u-12\tau u^2+12\tau^2.
\end{aligned}
\]

The frozen predictor omits these spatial, mixed, and temporal terms. At \(c=u=0\), its entire error is the positive term \(12\tau^2\). This explains the failed center-zero prediction directly.

This proof establishes the exact real-zero threshold and tests the local predictor on the specified quartic. The calculations follow the quadratic formula, Taylor expansion, and the finite heat-operator exponential. They supply a fully solved calibration and an explicit limitation of the frozen approximation. A proof about the Riemann deformation would additionally need control of its full function and all relevant zeros.


## Arbitrary-center counterexamples

Consider the proposed one-sided bounds over every real center \(c\) satisfying \(P_0''(c)\ne0\). The center \(c=0\) already gives

\[
\widehat\delta_0=-\frac9{20}>-\frac23.
\]

A different admissible center gives the opposite ordering. At \(c=4/3\), exact evaluation gives

\[
P_0(c)=-\frac{455}{81},\qquad
P_0'(c)=-\frac{464}{27},\qquad
P_0''(c)=\frac43.
\]

Consequently,

\[
\Delta_{4/3}=\frac{226216}{729},\qquad
\widehat\delta_{4/3}=-\frac{28277}{324}<-\frac23.
\]

Thus neither \(\widehat\delta_c\le-2/3\) nor \(\widehat\delta_c\ge-2/3\) holds for every admissible real center. Both witnesses lie between adjacent initial roots. The center \(4/3\) lies between \(1\) and \(3\), and their midpoint is \(2\). These witnesses leave a midpoint-only claim unassessed.

The predicted increment can also have the wrong direction for a decreasing-parameter experiment. At \(c=4\),

\[
P_0(4)=105,\qquad P_0'(4)=176,\qquad P_0''(4)=172,
\]

and therefore

\[
\Delta_4=-5144,\qquad
\widehat\delta_4=\frac{643}{7396}>0.
\]

This center lies outside the initial root interval \([-3,3]\). It refutes universal negativity when centers are unrestricted. It supplies no counterexample to a rule restricted to adjacent-root midpoints.

## A finite adjacent-gap bound

There is a rigorous bound available from the actual zero dynamics. Let \(P(t,z)\) be a monic polynomial of degree at least two with real coefficients, satisfying

\[
\partial_tP=-\partial_z^2P,
\]

and suppose that at \(t=0\) all its zeros are distinct and real. The terminating heat-operator exponential defines this polynomial flow for every real \(t\); its coefficients are polynomial in \(t\), with a constant leading coefficient. Roots therefore remain bounded on every compact time interval. Follow its ordered real simple roots \(r_1(t)<\cdots<r_n(t)\) on the interval preceding the first backward collision. Every statement below is restricted to that interval.

Differentiating the root equation gives

\[
0=\partial_tP(t,r_i)+\partial_zP(t,r_i)r_i',
\qquad
r_i'=\frac{P_{zz}(t,r_i)}{P_z(t,r_i)}.
\]

Factor \(P(t,z)=(z-r_i)Q_i(t,z)\). At \(z=r_i\), we have \(P_z=Q_i\) and \(P_{zz}=2Q_i'\). Taking the logarithmic derivative of the finite product \(Q_i=\prod_{j\ne i}(z-r_j)\) proves

\[
\boxed{r_i'=2\sum_{j\ne i}\frac1{r_i-r_j}.}
\]

For an adjacent pair \(a=r_i\), \(b=r_{i+1}\), put \(g=b-a>0\). Every other root \(r\) lies outside \([a,b]\), so \((b-r)(a-r)>0\). Subtracting their velocities gives

\[
\begin{aligned}
g'
&=\frac4g+2\sum_{r\ne a,b}\left(\frac1{b-r}-\frac1{a-r}\right)\\
&=\frac4g-2g\sum_{r\ne a,b}\frac1{(b-r)(a-r)}.
\end{aligned}
\]

Writing the nonnegative exterior sum as \(S\), we obtain

\[
\boxed{(g^2)'=8-4g^2S\le8.}
\]

The sum is zero for a degree-two polynomial and strictly positive when other real roots are present. For a negative time \(t\) before the first collision, integration from \(t\) to zero yields

\[
g(0)^2-g(t)^2\le-8t,
\qquad
\boxed{g(t)^2\ge g(0)^2+8t.}
\]

Let \(g_{\min}(0)\) be the smallest initial adjacent gap. If a first backward collision occurred at \(t_c>-g_{\min}(0)^2/8\), at least one adjacent gap would approach zero as \(t\downarrow t_c\). The displayed lower bound would instead approach a strictly positive value. This contradiction proves that any finite first backward collision satisfies

\[
\boxed{t_c\le-\frac{g_{\min}(0)^2}{8}.}
\]

Thus the isolated-pair estimate supplies a guaranteed interval

\[
-\frac{g_{\min}(0)^2}{8}<t\le0
\]

on which the finite polynomial has no root collision. If no finite backward collision occurs, the same interval conclusion holds. Real coefficients and continuity preserve the reality of initially simple real roots until a collision.

For the quartic at parameter zero, direct evaluation gives the exact velocities

\[
\begin{array}{c|rrrr}
r_i&-3&-1&1&3\\ \hline
r_i'&-11/6&-1/2&1/2&11/6.
\end{array}
\]

The three adjacent gaps initially have derivatives \(4/3,1,4/3\). Their exterior sums are respectively \(1/6,1/4,1/6\), agreeing with the velocity identity. Since every initial gap equals two, the bound guarantees the interval \((-1/2,0]\). The exactly computed first collision at \(-2/3\) is consistent with that guarantee.

This argument uses a finite sum of interactions and an interval on which all roots are real and simple. Applying a corresponding argument to an entire function requires appropriate convergence, tail estimates, and justification of the real-root interval. The finite proof alone makes no assertion about the full Riemann deformation.
