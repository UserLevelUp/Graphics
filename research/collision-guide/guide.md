# A usable guarantee before real polynomial roots collide

defines: graph.riemann.collision_guide.guide
consumer: graph.riemann.gap.proof
consumer: graph.riemann.gap.verify
consumer: graph.riemann.collision.proof

This guide explains a finite-polynomial theorem, its exact-arithmetic implementation, and practical uses. The theorem supplies a lower bound on the time to the first root collision. It does not give the exact collision time in general, certify a numerical integrator, or establish a Riemann Hypothesis result. The novelty of these particular bounds has not been established.

The complete derivations are in [the interaction-bound proof](../gap-bound/interaction-bound-proof.md) and [the exact quartic proof](../collision-proof/exact-quartic-proof.md). This document develops their use rather than replacing their hypotheses with visual intuition.

## How the result developed

The documented sequence can be reconstructed from commits, Eventness records and trace IDs. The [provenance receipt](evidence/discovery-provenance.json) records three Git milestones, source hashes and three trace inventories. These records establish what was saved and reviewed; they do not establish historical priority, private thought processes or mathematical truth.

| Recorded milestone, November 14, 2026 | Trace ID | What the evidence establishes |
|---|---|---|
| 22:31:46 −08:00, commit `170993c` | `graph.zeros.motion` | Four-color phase coordinates, moving origins and point-to-point probes were implemented around an exact quadratic calibration. |
| 23:13:18 −08:00, commit `73518fc` | `graph.riemann.collision` | Exact quartic algebra exposed a failed frozen local forecast. The adjacent-gap argument retained the sufficient baseline \(m^2/8\). |
| 23:37:16 −08:00, commit `cf51254` | `graph.riemann.gap` | Constant and contracting-diameter estimates strengthened the finite-polynomial guarantee and were checked against exact controls. |

The bridge between the second and third milestones is explicit in [the collision next-obligation record](../../warps/graph.riemann.collision.next.current.md): retain the positive exterior-interaction sum \(S\), then find a stronger, non-circular bound on it. This is the precise mathematical change. The four-color display helped make root motion and prediction error visible; its colors were not premises in the proof.

Both proposed duration formulas already appear in [the review contract](../gap-bound/graph.riemann.gap.contract.current.md). Consequently, the later Carbon and Codex reports are reviews of supplied proposals, not evidence that either reviewer invented them. [Carbon's final report](../gap-bound/carbon/review.md) explicitly retracts an erroneous product inequality. Coordinator steering identified the error; the corrected argument uses reciprocal distances. For \(0<x<D\),

\[
x(D-x)\le D^2/4
\quad\Longrightarrow\quad
\frac{2D}{x(D-x)}\ge\frac8D.
\]

In the extreme-root velocity equation, this gives

\[
\frac{dD}{dt}=\frac4D+
\sum_{j=2}^{n-1}\frac{2D}{(r_j-r_1)(r_n-r_j)}
\ge\frac{8n-12}{D},
\]

and hence \((D^2)'\ge16n-24\), with derivatives taken in \(t\). The correction matters: taking reciprocals of positive quantities reverses the inequality direction.

[The completed Eventness record](../../warps/graph.riemann.gap.results.complete.md) records the finite claim and exact checks. [The current next-obligation record](../../warps/graph.riemann.gap.next.current.md) leaves the infinite-system transfer open. A trace occurrence links artifacts for inspection; it does not prove execution. A completion label or agreement among reviewers cannot replace the derivation and independently checked evidence.

In a full repository checkout with the recorded Recur installation, rebuild the discovery receipt with:

```powershell
python -B research/collision-guide/trace_discovery.py
```

That command re-runs the trace inventories and writes the receipt in this chapter's evidence directory. Its `queries` entries preserve the actual Recur arguments and result hashes. The replay script currently uses the recorded Windows Recur executable path; another installation must configure that path before replaying it. Git history supplies the three commit timestamps; the receipt's observation time is the later audit time.

## The problem being solved

Let a real polynomial \(P_0\) of degree \(n\ge3\) have distinct real roots

\[
r_1(0)<r_2(0)<\cdots<r_n(0).
\]

A fixed nonzero leading coefficient can be divided out, so take the polynomial to be monic. Evolve it by

\[
P_t(z)=e^{-t\partial_z^2}P_0(z)
=\sum_{j=0}^{\lfloor n/2\rfloor}\frac{(-t)^j}{j!}P_0^{(2j)}(z),
\qquad \partial_tP_t=-\partial_z^2P_t.
\]

This sum terminates. It defines the exact polynomial at every real parameter \(t\); no Euler discretization is involved in constructing its coefficients.

We start at \(t=0\) and decrease \(t\). To avoid sign ambiguity, use **elapsed duration \(u=-t\ge0\)**. A certificate of duration \(T\) means that the roots are all real and simple for \(0\le u<T\), or equivalently \(-T<t\le0\). At \(u=T\), reality with multiplicity is guaranteed, but simplicity is not asserted by the theorem. A collision could occur later than \(T\).

The result applies to this particular heat evolution. It does not apply unchanged to arbitrary interpolations between polynomials, arbitrary coefficient perturbations, or a collection of observed roots whose defining polynomial is unknown.

## Read the three initial parameters

Set

\[
m=\min_i(r_{i+1}(0)-r_i(0)),\qquad
D_0=r_n(0)-r_1(0),\qquad
\kappa=\frac{n-2}{D_0^2}.
\]

Here \(m>0\) is the smallest adjacent gap and \(D_0>0\) is the full diameter. The number \(n\) counts **all roots of the finite polynomial**, not a selection from a larger function. The packing inequality \(D_0\ge(n-1)m\) ensures that the expressions below have valid logarithm and power arguments.

For the running example

\[
P_0(z)=(z^2-1)(z^2-9),\qquad
(r_1,r_2,r_3,r_4)=(-3,-1,1,3),
\]

the parameters are \(n=4\), \(m=2\), \(D_0=6\), and \(\kappa=1/18\).

## Three levels of guarantee

The elementary two-root baseline is

\[
T_0=\frac{m^2}{8}.
\]

For an isolated pair with spacing \(m\), the squared gap is exactly \(m^2-8u\), so this is its exact collision duration. For a larger admissible finite polynomial, it is a lower bound on the first collision duration.

Retaining exterior-root interactions gives

\[
\boxed{T=-\frac{\log(1-\kappa m^2/2)}{4\kappa}>T_0.}
\]

A stronger estimate uses the contraction of the diameter. Define

\[
d=D_0^2,\qquad A=4(n-2),\qquad B=16n-24,
\qquad \eta=\frac{(A+B)m^2}{8d}.
\]

Then

\[
\boxed{T_{\rm dyn}=\frac dB\left[1-(1-\eta)^{B/(A+B)}\right]>T>T_0.}
\]

The inequalities \(0<\eta<1\) and \(T_{\rm dyn}<d/B\) follow from gap packing. Thus the denominator used in the stronger comparison remains positive over its claimed interval. These are strict improvements over this project's elementary baseline and its constant-diameter bound. They are **not** a demonstrated improvement over the best bound in the research literature.

For the quartic:

| Calculation | Guaranteed duration or exact event |
|---|---:|
| Two-root baseline \(T_0\) | \(1/2=0.5\) |
| Constant-diameter bound \(T\) | \((9/2)\log(9/8)\approx0.53002366045\) |
| Contracting-diameter bound \(T_{\rm dyn}\) | \((9/10)(1-3^{-5/6})\approx0.53971891345\) |
| Actual first collision | \(2/3\approx0.66666666667\) |

Decimals in the table are explanatory. The program makes certification decisions using exact rational enclosures, not these rounded values.

## Why the proof works

As long as the roots are real and simple, differentiating \(P_t(r_i(t))=0\) and factoring the polynomial gives

\[
\frac{dr_i}{dt}=\frac{P_{zz}}{P_z}(t,r_i)
=2\sum_{j\ne i}\frac1{r_i-r_j}.
\]

For adjacent roots \(a<b\), write \(g=b-a\), \(y=g^2\), and

\[
S=\sum_{r\ne a,b}\frac1{(b-r)(a-r)}.
\]

All other roots lie outside the adjacent pair, so every denominator in this sum is positive. Subtracting the root velocities yields the exact identity

\[
\frac{dy}{dt}=8-4yS,\qquad
\frac{dy}{du}=-8+4yS.
\]

The second equation is the same identity after changing to elapsed duration \(u=-t\). Mixing the two time conventions reverses the meaning of the inequalities and is a common source of error.

Before a collision, the full diameter satisfies \(D(-u)\le D_0\). Therefore each positive exterior-root denominator is at most \(D_0^2\), and there are \(n-2\) of them. Hence \(S\ge\kappa\). Compare each actual squared gap to the solution of

\[
C'=-8+4\kappa C,\qquad C(0)=m^2.
\]

Its explicit value is

\[
C(u)=\frac2\kappa+\left(m^2-\frac2\kappa\right)e^{4\kappa u}.
\]

The comparison proves \(y(u)\ge C(u)>0\) for \(0\le u<T\). Solving \(C(T)=0\) gives the displayed constant-diameter certificate.

For the stronger estimate, the equations for the two extreme roots give

\[
D(-u)^2\le d-Bu.
\]

Consequently \(S\ge(n-2)/(d-Bu)\), and the comparison becomes

\[
L'=-8+\frac{A}{d-Bu}L,\qquad L(0)=m^2.
\]

Writing \(R=1-Bu/d\), its explicit value is

\[
L(u)=R^{-A/B}\left[m^2-\frac{8d}{A+B}
\left(1-R^{1+A/B}\right)\right].
\]

It is positive before \(T_{\rm dyn}\). The increasing interaction coefficient produces a strictly stronger certificate than the constant one. The proof compares these two differential equations; it does not infer the improvement merely from a graph or one example.

There is no assumption that the simple-root interval already lasts this long. Start with the local interval guaranteed by distinct initial roots. If its first collision occurred sooner than the certificate, a gap would have to reach zero while the proved lower bound remained positive. Roots also cannot escape to infinity on a bounded parameter interval: the monic polynomial's coefficients are bounded there. Distinct real roots can therefore be continued across any supposed earlier endpoint. This first-collision argument closes the proof.

## Use the practical wrapper

From the repository root, create an output directory and run the supplied exact-rational example:

```powershell
New-Item -ItemType Directory -Force work | Out-Null
python -B research/collision-guide/use_certificate.py --roots=-3,-1,1,3 --duration=17/32 --output work/collision-example.json
```

The wrapper uses `research/gap-bound/verify_bound.py` as its arithmetic backend. It checks the requested **elapsed duration**; it converts that duration to the polynomial parameter \(t=-u\). The output keeps two questions separate:

| Report field | What it means |
|---|---|
| `guaranteedInterval.status` | Whether the analytic theorem and a rigorous rational lower enclosure certify the entire elapsed interval through the requested duration. |
| `guaranteedInterval.lowerEnclosure` | An exact rational value no greater than \(T_{\rm dyn}\). Use this in comparisons. |
| `guaranteedInterval.decimalLowerForDisplay` | A convenient decimal rendering, not the decision input. |
| `exactPointCheck.status` | Whether exact Sturm and polynomial-GCD calculations find all roots real and simple at this one rational time. |
| `exactPointCheck.counts.distinctRealRoots` | The number of distinct real roots of that particular polynomial. |
| `exactPointCheck.counts.gcdDegreeWithDerivative` | Zero means no repeated roots; a positive degree signals multiplicity. |

For \(u=17/32=0.53125\), the wrapper reports both `certified` and `all_roots_real_and_simple`. This time is greater than the upper enclosure of the constant bound and less than the lower enclosure of the dynamic bound. The exact polynomial is

\[
P_{-17/32}(z)=z^4-\frac{29}{8}z^2+\frac{451}{256}.
\]

Its exact Sturm count is four distinct real roots and its GCD with its derivative has degree zero. The analytic theorem covers every intermediate time; the Sturm computation independently checks this particular rational-time polynomial.

Compare two deliberately different situations:

```powershell
python -B research/collision-guide/use_certificate.py --roots=-3,-1,1,3 --duration=3/5
python -B research/collision-guide/use_certificate.py --roots=-3,-1,1,3 --duration=7/10
```

At \(u=3/5\), the conservative interval guarantee is unavailable, but the exact point check still finds four real simple roots. At \(u=7/10\), the bound is again unavailable and the exact point check finds no real roots. **Outside the guaranteed interval is not itself a failure of real-rootedness.** The first status must not be used as a binary collision detector.

At the exact collision \(u=2/3\), all four roots counted with multiplicity remain real, but there are only two distinct roots and they are not simple. Thus `not_all_roots_real_and_simple` need not mean that every root is nonreal. Read the count and GCD fields together.

## Supply another polynomial

The current interface takes a finite list of exact rational roots, with at least three distinct entries. Unsorted input is sorted. Fractions such as `1/20` are exact. A decimal string such as `0.05` is treated as the exact rational \(1/20\); that does not certify a noisy measured value merely because it was entered as a decimal.

For example:

```powershell
python -B research/collision-guide/use_certificate.py --roots=0,1/20,1,3,6 --duration=1/10000 --output work/clustered-example.json
```

Here \(m=1/20\), \(D_0=6\), and the baseline is \(1/3200\). The chosen duration \(1/10000\) lies below even that baseline. This illustrates why a tightly clustered pair can make the guarantee much smaller than the total width of the root configuration might suggest.

To run the original suite or produce full bound-and-sample reports:

```powershell
python -B research/gap-bound/verify_bound.py --roots=-3,-1,1,3 --output work/full-bound-report.json
python -B research/gap-bound/verify_bound.py --output work/bound-suite.json
```

The recorded suite contains 25 root configurations of degrees three through eight, with uniform, clustered, uneven, translated and rescaled examples. It includes 100 exact rational-time root counts, degree/domain rejection controls, a reversed-sign control and a deliberately inflated-duration control. These tests support the implementation on their stated inputs. They do not replace the all-degree analytic argument.

## Practical uses and their limits

**Bound a root-continuation interval.** If a solver is exploring this exact heat flow, choose a rational duration strictly below the certified lower enclosure, optionally leaving an additional margin. The exact roots cannot collide in that interval. The solver still needs its own bounds on discretization error, root-isolation error and Newton convergence. A diverging numerical iteration inside the interval would not refute the theorem; it could indicate a numerical failure.

**Restart from a later polynomial.** The heat evolution has a semigroup property, so the theorem can be applied again after a new starting polynomial has been certified to have distinct real roots. However, its roots will not generally remain rational even when its coefficients do. The current CLI does not accept root intervals or automatically certify approximate root estimates. A production restart scheme would need exact algebraic root information or a separately proved propagation from certified interval bounds. No such interval-root integration is claimed here.

**Benchmark local predictions.** For the quartic, the exact all-real-root threshold is \(t=-2/3\). A frozen quadratic approximation centered at zero instead predicts a collision at \(u=9/20\) and \(z=0\). The exact value is \(P_{-9/20}(0)=243/100>0\). More strongly, \(P_t(0)=12(t+5/6)^2+2/3>0\) for every real \(t\), so zero is never a root. This provides a clear regression example for any predictor that ignores higher spatial or time terms. It refutes this particular prediction, not every possible local approximation method.

**Calibrate a visualization.** Root positions, gap envelopes and certified intervals can be drawn together. Color can identify which guarantee covers a selected time. Use separate marks for the exact collision, the end of a sufficient bound and a failed numerical solver. Do not let a color switch silently equate those three different events.

**Check changes of units and origin.** A translation of all roots leaves the durations unchanged. Scaling all roots by a nonzero real factor \(a\) multiplies all guaranteed durations and the exact evolution time scale by \(a^2\). The code's exact covariance controls help detect unit errors. Rotating a display or recoloring its points does not improve a mathematical certificate.

**Assess edge cases.** Repeated initial roots give \(m=0\) and fall outside the theorem's distinct-root assumptions. Degree two has the exact \(m^2/8\) formula; it is deliberately outside the degree-at-least-three CLI. Degree one has a constant root. If the roots were only approximately supplied, the certificate applies to the exact rational polynomial entered, not automatically to the unknown intended polynomial. The fixed 80-step rational-power enclosure can be too wide to demonstrate a strict dynamic improvement for extreme gap-to-diameter ratios; failure to display that comparison is not a counterexample to the analytic strict inequality.

## Relation to established work and to RH

Polynomial heat flow and the associated root-interaction equations are established mathematics. [Terence Tao's 2017 exposition](https://terrytao.wordpress.com/2017/10/17/heat-flow-and-zeroes-of-polynomials/) derives the root dynamics and discusses earlier work of Csordas, Smith and Varga. Its time convention uses the opposite heat sign; our elapsed variable \(u=-t\) reconciles the conventions. This project supplies explicit finite-diameter estimates and executable examples, but has not established priority or optimality of the resulting formulas.

The relevant entire-function deformation is \(H_t\). It obeys \(\partial_tH_t=-\partial_x^2H_t\), the same heat sign used for our polynomial parameter \(t\). Its zeros are all real exactly when \(t\ge\Lambda\), where \(\Lambda\) is the de Bruijn–Newman constant. RH is equivalent to \(\Lambda\le0\); [Rodgers and Tao proved \(\Lambda\ge0\)](https://arxiv.org/abs/1801.05914). Together these statements make RH equivalent to \(\Lambda=0\).

The shared heat evolution and root-motion method give a meaningful connection, but the hypotheses differ decisively. Our proof uses a finite degree, a finite interaction sum and a finite global diameter. The Riemann flow has infinitely many zeros and no finite global diameter. An actual transfer would need justified infinite sums, bounds on omitted distant zeros and estimates valid at every height. None of these obligations is discharged by recoloring, finite root samples or the polynomial proof.

There is also a starting-assumption trap. Assuming that every zero of \(H_0\) is real would already assume RH. Assuming that they are all simple adds another condition that RH itself does not assert. Moreover, a uniform all-real-root interval extending strictly below \(t=0\) would force \(\Lambda<0\), contradicting the established lower bound. Thus an RH-oriented continuation argument would need to start from an independently known all-real regime and justify control toward \(t=0\), without assuming its desired conclusion. These are logical requirements for future work, not a claim that this certificate supplies that control.

The current formulas themselves exhibit an additional obstruction in growing root systems. As detailed in [the open transfer obligation](../../warps/graph.riemann.gap.next.current.md), put

\[
x=\frac{(n-2)m^2}{2D_0^2},\qquad
\eta=\frac{(5n-8)m^2}{2D_0^2},\qquad
\beta=\frac{16n-24}{20n-32}.
\]

Packing gives \(x,\eta\to0\) as \(n\to\infty\), while \(\beta\to4/5\). Consequently

\[
\frac{T}{m^2/8}=\frac{-\log(1-x)}x\longrightarrow1,
\qquad
\frac{T_{\rm dyn}}{m^2/8}
=\frac{1-(1-\eta)^\beta}{\beta\eta}\longrightarrow1.
\]

If the minimum gaps also tend to zero, both guaranteed durations tend to zero. This conclusion follows from the formulas and packing, rather than extrapolating a plot. It explains why a global diameter estimate cannot simply be copied across increasingly dense finite truncations to obtain a positive uniform interval. A different estimate with justified local interactions and tail control would be needed.

The reusable deliverables are a proved sufficient interval for a defined finite heat flow, an exact-rational checker, a completely solved quartic calibration, and explicit counterexamples to a frozen local predictor. Each can be inspected and reused without treating the animation itself as proof. No RH advance, prime-generation shortcut, or mathematical novelty has been established.
