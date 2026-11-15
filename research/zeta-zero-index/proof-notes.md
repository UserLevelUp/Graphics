# Starting direction of the indexed zeta-zero trajectories

defines: graph.riemann.zero_index.proof
consumer: graph.riemann.continuation

## What the screenshot depicts

The bright pink curve labeled Z3 is the third continuation trajectory, not the purple background quadrant. The old scene assigns distinct stroke colors to Z1, Z2 and Z3. Its background colors show the quadrant of zeta(s)-a. These two uses of color have different meanings.

The trajectory starts at the third positive-height nontrivial zero,

\[
\rho_3=\tfrac12+25.010857580145688763\ldots i,
\]

and follows solutions of zeta(s)=a as the real target a increases from zero. The zero index 3, the noninteger height 25.010857..., and an arbitrary integer input are different quantities. The final comparison therefore uses prime **zero indices** p<=100, rather than setting t=p. The earlier integer-height interpretation was superseded and is not the basis of the animation.

## The relevant derivative

At a simple zero, the local inverse function theorem gives a branch s(a) satisfying

\[
\zeta(s(a))=a,\qquad s(0)=\rho_j.
\]

Differentiating yields

\[
\boxed{\frac{ds}{da}=\frac1{\zeta'(s)}}.
\]

Write s=sigma+it and zeta'(s)=u+iv. Then

\[
\frac{d\sigma}{da}=\frac{u}{u^2+v^2},\qquad
\frac{dt}{da}=\frac{-v}{u^2+v^2},\qquad
\boxed{\frac{dt}{d\sigma}=-\frac vu}
\]

when u is nonzero. If u=0 but zeta'(s) is nonzero, the tangent is vertical in the sigma,t plane. A zero derivative requires a different local analysis and is guarded against in the numerical producer. The sign convention uses sigma increasing to the right and t increasing upward; screenshot pixel y coordinates run the opposite way.

The logarithmic phase derivative zeta'(s)/(zeta(s)-a) is singular **on this path**, because zeta(s)-a=0 there. It must not be used to assign the trajectory's tangent. Likewise, the phase quadrant at the exact shifted zero is undefined. Neighboring background colors can show its local geometry, but the inverse derivative is the appropriate trajectory calculation.

For a>0 the path follows zeros of zeta(s)-a, not zeros of zeta(s). Its departure from Re(s)=1/2 therefore says nothing against the Riemann Hypothesis.

## What the first 100 starting slopes show

The producer evaluates each starting zero and zeta derivative at 50 decimal digits, then repeats the zero and derivative calculation at 75 digits. It also compares the explicit zeta derivative with `mp.diff` at 75 digits. Every reported slope sign agrees across these checks.

| Zero-index class, 1..100 | Number of indices | Negative initial slope | Positive initial slope |
|---|---:|---:|---:|
| Prime indices | 25 | 14 | 11 |
| Composite indices | 74 | 35 | 39 |
| Index 1, neither | 1 | 1 | 0 |
| All indices | 100 | 50 | 50 |

There are no vertical starting tangents in this sample. All 100 measured initial d(sigma)/da values are positive; this is an observation about the sampled zeros, not a theorem about all zeros.

The first three paths reproduce the screenshot's distinction:

| Path | Index classification | Initial dt/dsigma |
|---|---|---:|
| Z1 | Neither | -0.159198755335884 |
| Z2 | Prime index | +0.224223188759618 |
| Z3 | Prime index | -0.347305321686748 |

Thus Z3 really does start with a negative slope at sigma=1/2. However, Z2 and Z7 are prime-index counterexamples to a universally negative prime-index slope. Z8 and Z10 are composite-index counterexamples to using a negative slope as evidence that the index is prime. Index 1 also has a negative slope, but it is neither prime nor composite.

The prime indices with negative starting slope are 3,5,11,17,23,29,37,41,59,67,73,79,83,89. Those with positive starting slope are 2,7,13,19,31,43,47,53,61,71,97. These finite counts are descriptive; the zero indices are not independent random observations, and no statistical predictive claim is made.

## Relation to the established Hardy Z phase

The [DLMF Hardy Z relation](https://dlmf.nist.gov/25.10.E1) writes the critical-line zeta value as zeta(1/2+it)=exp(-i theta(t)) Z(t), where Z(t) is real. The [theta definition](https://dlmf.nist.gov/25.10.E2) comes from the gamma-factor phase. At a simple critical-line zero t_j, differentiation gives

\[
i\zeta'(\rho_j)=e^{-i\theta(t_j)}Z'(t_j),
\qquad
\zeta'(\rho_j)=-i e^{-i\theta(t_j)}Z'(t_j).
\]

The real scalar Z'(t_j) cancels in the slope ratio, so

\[
\boxed{\left.\frac{dt}{d\sigma}\right|_{a=0}=-\cot\theta(t_j)}
\]

whenever the tangent is nonvertical. This derivation explains the direction through the existing critical-line phase relation. It does not make a prime-index criterion. An independent numerical evaluation of `-cot(siegeltheta(height))` from the saved 48-digit heights agrees with all 100 stored slopes to within 1.20e-41; truncation of the saved height limits that comparison. The analytic derivation, rather than that finite agreement, explains the equivalence.

## Short paths used by the animation

`evidence/paths.json` contains 31 paths: all 25 prime indices through 100 and the six controls 1,4,6,8,9,10. Each has 21 target samples from a=0 through a=0.10 at nominal spacing 0.005.

Each advance predicts with ds/da=1/zeta'(s), then corrects with Newton iteration. The producer checks residuals below 1e-38, bounds accepted predictor corrections and step distances, guards against small derivatives, and permits bounded subdivision when a nominal step needs it. It checks the starting secant at a=0.0025 against the a=0.005 secant; the smaller step improves the velocity approximation for every path.

All 651 saved points lie in the local rendering viewport sigma in [0.4,0.9], t within 0.35 of that zero's starting height. Their observed sigma extent is approximately [0.5,0.631520], and their maximum absolute height displacement is approximately 0.075105. The largest saved target residual is below 5.19e-49. No clipping or fabricated extension is needed for those local panels. The short paths do not establish behavior all the way to a=1; the historical three-path scene supplies its separately accepted longer trajectories.

The numerical checks are not interval certificates. They do not certify branch uniqueness through a validated inverse-function or contour bound, nor do they establish a new verification of RH. Their purpose is a reproducible, correctly labeled comparison of the observed trajectories.

## Runtime and reproducibility

The source is `zero_index_analysis.py`, requiring mpmath 1.3.0. Running it writes `evidence/zero-index.json` and `evidence/paths.json`. Each report binds the producer's source hash and records its Python and mpmath versions.

During the superseded integer-height study, the installed Python 3.14 process repeatedly exited with a Windows access violation inside mpmath evaluation; a faulthandler stack identified that failure mode. The final indexed-zero study ran successfully using the already installed Python 3.11 interpreter bundled with KiCad, with the existing pure-Python mpmath dependency path supplied explicitly. No KiCad project, settings, or runtime installation was changed. No cause beyond the observed failing stack is asserted.

This comparison confirms the user's specific Z3 starting-slope observation and supplies counterexamples to its proposed extension to prime indices. It establishes no new primality algorithm, prime-generation formula, speedup, novelty claim, or RH result.
