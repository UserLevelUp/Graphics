# Divisor phases, quadrant colors, and half-step comparisons

defines: graph.primes.divisor_phases.proof
consumer: graph.primes.quadrant_phase

This note independently analyzes all integers from 0 through 100, the 25 primes in that interval, and their pairwise phase relationships. Its purpose is to distinguish arithmetic facts from information introduced or discarded by a coloring convention. No Wilson remainder or input primality label is used to define a divisor phase.

## 1. The phase and the periodic divisibility expression

For an integer divisor d >= 2 and integer candidate n, let

\[
z_d(n)=\exp(2\pi i n/d).
\]

Then z_d(n)=1 exactly when d divides n. Equivalently, with r=n mod d,

\[
\frac1d\sum_{j=0}^{d-1}z_d(n)^j
=\begin{cases}1&d\mid n,\\0&d\nmid n.\end{cases}
\]

If z=1, every summand is 1. Otherwise, multiply the finite geometric sum by 1-z: the result is 1-z^d=0, and division by the nonzero factor 1-z gives a zero sum. This proves the exact integer-input claim. The familiar vanishing sum for nontrivial primitive roots is also documented in [mathlib's roots-of-unity development](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RingTheory/RootsOfUnity/PrimitiveRoots.html), theorem `IsPrimitiveRoot.geom_sum_eq_zero`. That source was consulted as prior work; no Lean replay or formal verification of this experiment is claimed.

For odd d, the balanced real expression used in the conversation,

\[
D_d(x)=\frac{1+2\sum_{j=1}^{(d-1)/2}\cos(2\pi jx/d)}d,
\]

has these same divisibility values at integer inputs. It is a smooth real function between integers. Its values and derivatives at noninteger inputs are not primality labels.

For n=8,...,100, the exact finite test

\[
P(n)=\sin^2(\pi n/2)\prod_{d\in\{3,5,7\}}[1-D_d(n)]
\]

is 1 exactly for primes. Every composite n in this range has a prime divisor at most sqrt(n)<=10, hence one of 2,3,5,7. The cases 0 and 1 are neither prime nor composite; 2,3,5,7 are prime and must be handled separately if this particular fixed product is used on the whole 0..100 range. This is the standard finite divisibility test expressed through periodic functions. For example, 121 passes the four-factor product, so it is not an all-integer prime function.

## 2. An exact definition of the four colors

Choose a phase offset alpha in degrees and use half-open quadrants:

\[
Q_\alpha(n;d)=1+\left\lfloor4\left(\frac{n\bmod d}{d}+\frac\alpha{360}\pmod1\right)\right\rfloor.
\]

The fractional turn and its quadrant can be evaluated with exact rational arithmetic. Axes are assigned consistently to the quadrant beginning at that axis. No floating trigonometric threshold is needed for the finite classification checks.

The offset changes where the color boundaries cut the same phase data. It does not change divisibility. A whole-scene rotation of both points and their axes likewise changes no canonical quadrant. These are different operations: changing the phase offset relative to fixed quadrant axes changes the bin assignment; rotating a diagram and its coordinate system together does not.

In this experiment the color of Q_alpha(0;d) marks a **divisor-like phase**, not primality by itself. In the older Wilson-derived rendering, quadrant I was chosen to mean prime. Colors have no intrinsic prime meaning across different functions.

## 3. Why a 45-degree offset works for 2, 3, 5 and 7

At alpha=45 degrees, the zero residue lies at the center of quadrant I. A residue enters that quadrant precisely when

\[
\frac rd\in[0,1/8)\ \cup\ [7/8,1).
\]

For d=2,3,5,7, every nonzero residue has 1/d <= r/d <= 1-1/d. Those bounds exclude the displayed intervals. Therefore

\[
\boxed{Q_{45}(n;d)=1\iff d\mid n\quad(d\in\{2,3,5,7\}).}
\]

The complete residue-to-quadrant maps are:

| d | Quadrants for residues 0,1,...,d-1 |
|---:|---|
| 2 | 1, 3 |
| 3 | 1, 2, 4 |
| 5 | 1, 2, 3, 3, 4 |
| 7 | 1, 2, 2, 3, 3, 4, 4 |

Thus, for n=8,...,100, rejecting a candidate whenever any of these four phases is in quadrant I gives the exact same result as the ordinary divisibility test. With the small-case rules above, all 101 integers are classified correctly: 25 primes, 74 composites, and 0/1 neither.

The common admissible offset interval for all four divisors, within the first 90-degree sector, is

\[
\alpha\in[90-360/7,\,360/7)=[270/7,\,360/7)\text{ degrees}.
\]

The lower endpoint is included because its nearest positive nonzero residue reaches the next quadrant's starting axis. The upper endpoint is excluded because the nearest negative nonzero residue reaches the first quadrant's starting axis. At 45 degrees, a strictly smaller than 45/7 degree offset error preserves all four divisibility decisions. This is a mathematical margin on the phase partition, not certification of a pixel measurement's error.

## 4. Rotation sensitivity measured over 8..100

For each offset, compare a candidate's quadrant to the quadrant of the zero residue at that same offset. Reject a candidate if any divisor's colors match. Comparing blindly to a fixed color after the zero residue moves would be a different, inconsistent rule.

| Phase offset | Correctly retained primes, out of 21 | Rejected primes | Accepted composites |
|---:|---:|---:|---:|
| 0 degrees | 14 | 7 | 0 |
| 15 degrees | 14 | 7 | 0 |
| 30 degrees | 18 | 3 | 0 |
| 45 degrees | 21 | 0 | 0 |
| 60 degrees | 17 | 4 | 0 |
| 75 degrees | 12 | 9 | 0 |
| 90 degrees | 14 | 7 | 0 |

The missing primes at zero offset are 11,29,31,41,43,61,71. At 30 degrees they are 29,43,71; at 60 degrees they are 13,41,83,97. These are false indications of divisibility caused by color compression, not changes in arithmetic. No composite survives because a true divisor always has the zero-residue color in this rule. The four small primes are separate cases and are not included in these 21-prime counts.

## 5. A limitation of a single quadrant observation

At divisor 11 and offset 45 degrees, residues 1 and 10 share quadrant I with residue 0. For example, 23 has remainder 1 modulo 11 and receives the divisor-like color even though 11 does not divide 23.

This limitation cannot be removed for divisor 11 merely by choosing a better rotation. The nearest nonzero roots are at angles +/-360/11 degrees from zero. A single 90-degree half-open sector containing zero cannot exclude both neighbors: the entire gap between them is only 720/11 degrees, less than 90 degrees. More generally a single standard quadrant can isolate the zero root among all d equally spaced roots only when d<=7; the d=8 endpoint case still includes one neighbor under the half-open convention. More colors, an explicit extra boundary/axis state, or additional phase observations are needed beyond that limit.

## 6. Each prime as a reference point

For prime references p and prime candidates q from 2 through 100, compare

\[
z_p(q)=\exp(2\pi i q/p).
\]

Translating the input origin to p does not change this periodic phase:

\[
z_p(q-p)=z_p(q).
\]

In the 25-by-25 matrix, all 25 diagonal entries have exact phase zero. No off-diagonal entry does, because distinct primes do not divide each other. Nevertheless, at the 45-degree offset the quadrant counts are 148,179,165,133. Of the 148 quadrant-I cells, **123 are off-diagonal color aliases**, with no actual divisibility.

Examples include reference 11 with candidate 23, and reference 97 with candidate 89. Broad same-color bands near the diagonal are expected: q near p has q/p near 1, hence a phase near zero. The allowed closeness grows with p because this is a ratio. Such bands occur with nearby composite candidates too; they are not by themselves a prime-specific relationship.

## 7. What the half-step coordinates do

For odd p and q, write k_p=(p-1)/2 and k_q=(q-1)/2. Then

\[
q-p=2(k_q-k_p),\qquad
H_p(q)=\exp\left(2\pi i\frac{k_q-k_p}{p}\right).
\]

Consequently

\[
\boxed{H_p(q)^2=z_p(q).}
\]

Since p is odd, multiplication by 2 is invertible modulo p. The residue h=(q-p)/2 mod p is therefore the unique modular half of r=q mod p. The transformation permutes the residue classes; it introduces no new exact arithmetic information. It also preserves exact divisibility: h=0 iff r=0.

There are 24 odd primes and thus 576 ordered odd-prime pairs. At the same 45-degree color offset, the original and half-step matrices differ in **437 of 576 colors**. Their quadrant counts are respectively (128,176,140,132) and (134,100,145,197). A substantial color change is expected from a permutation followed by coarse binning; it does not alone show a new prime invariant.

As a control, the half-step square identity also holds for every one of the 600 pairs formed by the 24 odd-prime references and the 25 odd composite candidates from 3 through 99. All 49 odd candidates in that interval have fractional part 1/2 when divided by 2. The half-unit fact alone cannot distinguish the 24 primes from those 25 composites.

## 8. Combining the original and half-step colors retains more information

Although the exact half-step phase has no new arithmetic information, two coarse quadrant observations can retain more information than either one separately.

Let t=h/p in [0,1), so that the original phase has fractional turn 2t mod1. Quadrant I at offset 45 degrees corresponds to A=[0,1/8) union [7/8,1). Requiring both observations to be in that quadrant means

\[
t\in A\quad\hbox{and}\quad2t\bmod1\in A.
\]

Splitting A into its two intervals gives exactly

\[
\boxed{t\in[0,1/16)\ \cup\ [15/16,1).}
\]

Hence the joint divisor-like signature isolates h=0, equivalently r=0, for every odd modulus p<16. This includes 9 and 15 as well as the primes 3,5,7,11,13; it is not a theorem specific to prime moduli. The first prime modulus where it fails is 17: h=1 or16, corresponding to r=2 or15, also has the joint signature.

Measured alias counts at the 45-degree offset are:

| Pair set | Actual zero residues | Raw-color aliases | Half-color aliases | Joint-color aliases |
|---|---:|---:|---:|---:|
| 576 odd-prime pairs | 24 diagonal | 104 | 110 | 43 |
| 600 odd-composite control pairs | 45 | 114 | 156 | 74 |

An alias here is a nonzero residue whose observed color(s) match the zero residue. Joint observations reduce aliases, but do not eliminate them across all prime references through 97. For example, reference 17 and candidate 19 still collide with the zero signature. The modulus-17 failure applies to this shared 45-degree rule; it is not a proof of optimality over independently chosen axes for the two observations.

This is a useful and proved finite-resolution observation: combining related phase channels refines a color bin. Repeatedly doubling an underlying phase and observing each result with the same 45-degree offset refines the zero-compatible interval further. The offset must be applied after each power; squaring an already offset complex point also squares its offset and changes the rule. The underlying remainder or phase computation remains necessary. No faster arithmetic algorithm or new invariant is established by this refinement alone.

## 9. Evidence scope and conclusion

The independent finite checks for this note used exact Python `Fraction` phases and trial division as the separate primality oracle. They enumerated the classifier range 8..100, every prime pair, the 600 odd-composite control pairs, every residue of odd moduli 3..99 for the joint-signature threshold, and the listed phase offsets. Inputs 0..7 are covered by the explicit small-case rules. These observations do not establish statistical significance beyond the enumerated sets.

The colors do not alter mathematical relationships. They can preserve enough information for the bounded divisor test, or discard it and create collisions. Half-step coordinates provide a valid second representation, and combining both coarse representations provably reduces some collisions. These are finite arithmetic and representation results grounded in known divisibility and roots-of-unity identities. No novelty claim, independent prediction of primes from zeta, speed advantage, or Riemann Hypothesis result follows from this experiment.
