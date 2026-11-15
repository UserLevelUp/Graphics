# An exact primality function with no supplied prime history

**Domain:** nonnegative integers n. A prime is an integer greater than 1 with exactly two positive divisors. In particular, 0 and 1 are neither prime nor composite. Primality is not a property being assigned here to arbitrary complex inputs.

For n ≥ 2 define the least nonnegative remainder

\[
R(n)=\big((n-1)!+1\big)\bmod n,
\qquad
f(n)=\left\lfloor\frac{1}{1+R(n)}\right\rfloor.
\]

Set f(0)=f(1)=0 separately; do not evaluate the remainder formula at those inputs. Since R(n) is an integer between 0 and n−1, f(n) is 1 exactly when R(n)=0 and is 0 otherwise. In code, `1 // (1 + R)` evaluates this expression exactly, without floating-point division.

**Theorem:** f(n)=1 if and only if n is prime. This is Wilson's classical theorem expressed as an indicator, not a new prime formula or an RH result. A formal statement and proof of the equivalence already exist in [mathlib's Wilson development](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Wilson.html). That Lean development has not been replayed here, and its existence does not formally verify this project's implementation.

## Proof in both directions

If p=2, then (p−1)!=1≡−1 modulo 2. For an odd prime p, every nonzero residue modulo p has a unique multiplicative inverse. Pair each residue with its inverse: each pair contributes 1 to their product. A residue is its own inverse precisely when a²≡1, or p divides (a−1)(a+1). Since p is prime, these self-inverse residues are exactly 1 and −1. The product of all nonzero residues is therefore −1. Thus (p−1)!+1 is divisible by p, so R(p)=0 and f(p)=1.

Conversely, suppose n≥2 is composite. It has a prime divisor q with 2≤q<n. The factor q occurs in (n−1)!, so that factorial is 0 modulo q. Consequently (n−1)!+1 is 1 modulo q. If it were divisible by n, it would also be divisible by q, a contradiction. Thus R(n)≠0 and f(n)=0. Combined with the boundary definitions, this proves the theorem for every nonnegative integer, not just the tested range.

The proof uses the existence of a prime divisor in the converse. The executable Wilson formula does not need that divisor, a list of earlier primes, or previous primality answers as inputs.

## Most composites have exactly the same remainder

There is a stronger classical consequence: **R(n)=1 for every composite n>4**.

Write n=ab with integers 2≤a≤b<n. If a<b, the two distinct factors a and b occur in (n−1)!, so n divides the factorial. If a=b, then n=a². Because n>4, a≥3; the distinct integers a and 2a both lie between 1 and n−1, and their product is 2n. Again n divides the factorial. In either case, adding 1 leaves remainder 1 modulo n.

The exceptional composite 4 gives R(4)=(3!+1) mod 4=3. Thus the exact output classes are:

| Integer class | R(n) | f(n) |
|---|---:|---:|
| Prime n≥2 | 0 | 1 |
| Composite n>4 | 1 | 0 |
| n=4 | 3 | 0 |
| n=0 or 1 | Formula not evaluated | 0 |

This gives a precise version of the idea that composites can share a common output. It follows from exact arithmetic; it is not a pattern inferred from a rendered color.

## Worked inputs 96 and 97

Compute the factorial modulo n throughout, rather than constructing a huge factorial. Start with a=1 and update a←(a·k) mod n for k=2,...,n−1. Once a is zero, every later update remains zero, so an early exit preserves the exact final remainder.

For n=96:

| Last factor k | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Accumulator k! mod 96 | 1 | 2 | 6 | 24 | 24 | 48 | 48 | 0 |

Therefore 95! mod 96=0, R(96)=1, and f(96)=0. The familiar factorization 96=2×48 independently confirms compositeness.

For n=97, exact modular multiplication through k=96 gives 96! mod 97=96. Hence R(97)=(96+1) mod 97=0 and f(97)=1. This computation needs no earlier prime labels. An independent small-divisor check gives remainders 1,1,2,6 modulo 2,3,5,7; because √97<10, that also proves 97 prime.

Prime squares such as 49 and 121, and composite Fermat-pseudoprime controls such as 341 and the Carmichael numbers 561, 1105 and 1729, have R=1 by the composite theorem. They cannot pass this exact Wilson criterion. Finite implementation tests should check these cases and 0,1,2,3,4, but such tests supplement the all-n proof rather than create it.

## Phase is a visualization of the exact result

An optional unit-circle encoding is

\[
W(n)=\exp\!\left(2\pi i\frac{R(n)}n\right),\qquad n\ge2.
\]

Mathematically W(n)=1 if and only if R(n)=0, since 0≤R(n)<n. Input 96 has angle 2π/96=π/48=3.75°, while 97 has angle 0°. However, with the usual convention assigning the positive real axis to quadrant I, both have the same quadrant color. For composite n>4, the angle 2π/n approaches zero as n grows. A fixed pixel resolution, phase tolerance, or four-color quadrant cannot make the primality decision reliably. Compute the exact remainder first; then display the prime point or zero marker explicitly. That display is not an independent discovery algorithm.

## Optional complex extension, with a restricted meaning

For complex s with Re(s)>0, consider

\[
H(s)=\sin\!\left(\pi\frac{\Gamma(s)+1}{s}\right).
\]

The Gamma function is holomorphic in this half-plane, and Γ(n)=(n−1)! for positive integers; see [DLMF 5.2](https://dlmf.nist.gov/5.2) and [DLMF 5.4.1](https://dlmf.nist.gov/5.4.E1). Therefore H is holomorphic there. At integer n≥2, its real sine argument is an integer multiple of π precisely when n divides (n−1)!+1. Consequently H(n)=0 if and only if n is prime **on that integer domain**.

This is not a function whose only zeros are primes. H(1)=0 although 1 is not prime. There are noninteger zeros as well: the continuous real function g(s)=(Γ(s)+1)/s has g(4)=7/4 and g(5)=5. The intermediate value theorem supplies noninteger points in (4,5) where g equals 2,3 or 4; each is a zero of H. This zero set has no established RH conclusion.

Factorial growth also makes direct numerical Gamma-and-sine evaluation a poor primality test. Large sine arguments require accurate argument reduction, and finite precision can obscure exact integer multiples of π. Floating-point zeros or phase colors must not replace the modular criterion. This extension is a mathematical observation, not the implemented decision rule or a validated new complex-plane renderer.

## Computation, speed and the nth prime

The straightforward Wilson algorithm uses O(n) modular multiplications in the worst case, with O(log n)-bit residues; early zero termination helps many composites but does not change that worst-case bound. Trial division needs O(√n) divisor checks in the worst case and likewise needs no supplied prime list if every integer divisor is considered. These are operation counts, not full bit-complexity bounds. Both iteration counts are exponential in the input length log₂ n, and their arithmetic operations also have a cost. Wilson is an exact reference formula, not a claimed speed improvement.

For integer x≥2, define π(x)=Σ from m=2 to x of f(m). Then the kth prime satisfies

\[
p_k=\min\{m\in\mathbb Z:m\ge2,\ \pi(m)\ge k\},\qquad k\ge1.
\]

The next prime after x is min{m integer : m>x and f(m)=1}. These are exact counting/search formulations without an input list of earlier primes. They still require computation and do not provide a fast direct nth-prime shortcut. Candidate-input primality testing already has unconditional deterministic polynomial-time algorithms, notably [Agrawal, Kayal and Saxena's AKS algorithm](https://annals.math.princeton.edu/2004/160-2/p12). AKS is cited as prior work, not claimed as implemented here.

The resulting contribution is an explicit, proved criterion and a reproducible implementation baseline against which future phase rules can be tested. It establishes neither novelty nor a new prime-prediction speedup, and it does not prove any part of the Riemann Hypothesis.
