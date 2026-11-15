# A Wilson-derived color-quadrant primality test

Trace ID: `graph.primes.quadrant_phase.proof`.

**Claim.** An exact phase can be constructed so that its first quadrant identifies precisely the prime integers. The construction below adapts Wilson's theorem to the four-quadrant display. Its correctness comes from Wilson's arithmetic, not from an independently discovered pattern in zeta phase or overwritten pixels.

## Domain and construction

The input is an integer n >= 2. Inputs 0 and 1 are outside the phase formula and should be displayed as neither prime nor composite. Negative, fractional and complex inputs are not assigned primality by this construction.

Let the remainder always mean the least nonnegative integer remainder, and define

\[
R(n)=\big((n-1)!+1\big)\bmod n,
\qquad
\boxed{F(n)=(1+i)i^{R(n)}.}
\]

This form uses only integer coordinates: F(n)=x+iy with x,y in {-1,1}. An equivalent unit-circle point is Z(n)=F(n)/sqrt(2)=exp(i[pi/4+pi R(n)/2]). Normalization does not change the quadrant.

Number the open quadrants counterclockwise from the positive real axis: I has positive real and imaginary coordinates, II has negative real and positive imaginary coordinates, III has both negative, and IV has positive real and negative imaginary coordinates. None of the constructed points is on an axis. Its exact quadrant is

\[
\boxed{Q(n)=1+\big(R(n)\bmod4\big).}
\]

The phase criterion is therefore **n is prime if and only if Re(F(n))>0 and Im(F(n))>0**, equivalently Q(n)=1. A chosen color, such as violet, may represent quadrant I. Colors assigned to the quadrants are a presentation convention; the exact coordinate signs are the mathematical quantities.

For an exact implementation, let j=R mod4, start at (x,y)=(1,1), and apply the quarter-turn (x,y) <- (-y,x) exactly j times. This produces the following complete map without calling a separate prime indicator or using floating-point trigonometry:

| j | x | y | Quadrant |
|---:|---:|---:|---|
| 0 | 1 | 1 | I |
| 1 | -1 | 1 | II |
| 2 | -1 | -1 | III |
| 3 | 1 | -1 | IV |

## Why the criterion is exact for every input in its domain

Wilson's theorem states that, for n >= 2, n is prime exactly when (n-1)! is congruent to -1 modulo n. A formal statement and proof of both directions are available in [mathlib's Wilson development](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Wilson.html), particularly `Nat.prime_iff_fac_equiv_neg_one`. That Lean development was consulted as prior work; it was not locally replayed and does not formally verify this implementation.

For completeness, the prime direction follows by pairing each nonzero residue modulo a prime with its multiplicative inverse. Each pair contributes 1; the self-inverse residues are 1 and -1, leaving product -1. The case n=2 gives the same result directly. Thus every prime has R(n)=0.

There is a stronger restriction on composite outputs. Write a composite n>4 as n=ab with integers 2 <= a <= b < n. If a<b, the distinct factors a and b occur in (n-1)!, so n divides that factorial. If a=b, then n=a^2 and a>=3; the distinct integers a and 2a are both less than n and occur in the factorial. Their product is 2n, so n again divides the factorial. Consequently **R(n)=1 for every composite n>4**. The remaining composite is 4, where R(4)=(3!+1) mod4=3.

These cases exhaust the integer domain:

| Input class | R(n) | Phase modulo 360 degrees | Exact point F(n) | Quadrant |
|---|---:|---:|---|---|
| Prime n>=2 | 0 | 45 degrees | 1+i | I |
| Composite n>4 | 1 | 135 degrees | -1+i | II |
| n=4 | 3 | 315 degrees | 1-i | IV |

Only the first row occupies quadrant I, proving the criterion. Quadrant III is unused by valid integer candidates; it does not denote a fourth kind of integer. Its appearance would call for inspection of the supplied residue, chosen rotation, renderer or other changed assumptions.

The restriction R(n) in {0,1,3} is essential. Applying Q=1+(R mod4) to an arbitrary integer R is not a primality test: for example, R=4 would also enter quadrant I. The residue must be computed from the specified factorial expression. This proof establishes the whole integer-domain statement; finite software checks are additional implementation evidence.

## Worked candidates and the earlier phase

For 96, the exact modular factorial accumulator is already zero at 8!: 8! mod96=0. Every later multiplication leaves it zero. Hence R(96)=1, F(96)=-1+i, and the phase is 135 degrees in quadrant II.

For 97, exact modular multiplication gives 96! mod97=96. Therefore R(97)=0, F(97)=1+i, and the phase is 45 degrees in quadrant I. The small-divisor check against 2,3,5,7 independently confirms that 97 is prime. No list of earlier prime answers is supplied to the modular-factorial computation.

The earlier encoding used the real angle

\[
\theta_0(n)=\frac{2\pi R(n)}{n},\qquad0\leq\theta_0<2\pi.
\]

It put 96 at 3.75 degrees and 97 on the positive real axis. All composites n>4 approach that axis as n increases. The adapted angle is the candidate-dependent rescaling and rotation

\[
\theta(n)=\frac{\pi}{4}+\frac n4\theta_0(n)
\pmod{2\pi}.
\]

Use the exact real angle specified above, or, preferably, compute the equivalent expression directly from R(n). Do not multiply an arbitrary wrapped principal `Arg` or raise the old complex point to a noninteger power without specifying its branch. Such operations can select a different phase. This rescaling is a deliberate coordinate construction that separates the known arithmetic outcomes; it is not evidence that the unmodified zeta-phase quadrants predict primality.

## Resolution, numerical error and rendering

Each possible exact point is at a quadrant center, with angular distance 45 degrees from the closest axis. A final angular perturbation whose circular distance from the intended angle is strictly less than 45 degrees preserves its quadrant. Equality reaches an axis and provides no such guarantee. This fixed final margin prevents the mathematical separation from shrinking as n grows.

It does not recover information lost in an earlier rounded phase. Before final wrapping, an error epsilon in theta_0 is amplified to n*epsilon/4. The bound |epsilon|<pi/n is sufficient to retain the final quadrant when this is the only error. In particular, an old composite phase rounded to zero becomes indistinguishable from the prime phase before the amplification. Compute the modular remainder exactly rather than using pixels or rounded old angles as input.

The implementation can decide directly from the exact integer coordinate signs of F: x>0 and y>0. The displayed angle is 45+90*j degrees, or exactly (2*j+1)/8 of a turn. Sine and cosine are needed only for optional display rotation. A four-color brush, blending, line width, antialiasing and draw order can alter visible pixels; those overwritten pixels are not substitutes for the exact phase/quadrant record. Any classifier that reads an uncertain image instead should report uncertainty rather than assert exact primality from a color.

A bounded-observation mode may certify that an uncertainty interval around one of the intended center angles lies entirely within its quadrant when its angular half-width is strictly below 45 degrees. At 45 degrees or more it should return unknown. This is a statement about the supplied error bound, not proof that a renderer actually achieved that bound. A user-controlled display rotation must preserve the canonical coordinate reference: rotate the axes with the point or undo the rotation before applying the quadrant decision. Classifying against unrotated screen axes after rotating only the point changes the test.

## What this contributes and what remains open

The adaptation makes the four-quadrant test mathematically exact on its stated integer domain and gives its displayed points a constant angular margin. It provides a reproducible Wilson-derived phase baseline against which genuinely independent proposals can be compared. It does not establish novelty of this encoding.

The computation still requires the Wilson remainder. Direct evaluation uses O(n) modular multiplications in the worst case, with O(log n)-bit residues; the phase transformation adds only a bounded amount of work and does not remove that cost. The test does not supply a fast direct nth-prime formula, an independent zeta-phase predictor, or a proof of any part of the Riemann Hypothesis. Future alternatives would need their own all-input correctness argument and measured computational benefit; matching these colors over a finite sample would not establish either.
