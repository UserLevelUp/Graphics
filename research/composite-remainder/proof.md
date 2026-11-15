# An exact composite remainder, including finite series

defines: graph.primes.composite_remainder.proof
consumer: graph.primes.composite_remainder.model

## The result

There is a subtraction that leaves exactly the odd composites as its nonzero coefficient positions. It subtracts the two trivial factor families from all odd factor pairs. It does not come from reversing a prime generator, and it is a classical divisor construction rather than a new prime-finding theorem.

For every odd integer n>1, define

\[
D(n)=\sum_{\substack{3\le d\le\lfloor\sqrt n\rfloor\\d\text{ odd}}}
\left(\left\lfloor\frac nd\right\rfloor-
\left\lfloor\frac{n-1}d\right\rfloor\right).
\]

Then D(n) is the number of unordered nontrivial factor pairs of n. In particular,

\[
\boxed{D(n)=0\iff n\text{ is prime},\qquad D(n)>0\iff n\text{ is composite}}
\quad(n>1\text{ odd}).
\]

This is an all-integer elementary proof, not merely an observation from the tested range. The implementation is checked separately on a finite range. No previous-prime list is an input, but the sum performs divisor checks.

## Why the coefficient formula is exact

Write n=qd+r with 0<=r<d. If r=0, subtracting 1 lowers the floor quotient by 1. If r>0, it does not change the quotient. Thus the summand is exactly 1 when d divides n, and 0 otherwise.

An odd composite n has a factorization n=ab with 3<=a<=b, both factors odd, hence a<=sqrt(n). Conversely, any such divisor supplies a nontrivial factorization. Restricting the smaller factor d to d<=sqrt(n) counts each unordered pair once, including a square pair (d,d) once.

With tau(n) the number of positive divisors and the square indicator equal to 1 for a perfect square,

\[
D(n)=\frac{\tau(n)-2+\mathbf1_{\square}(n)}2
=\left\lfloor\frac{\tau(n)-1}{2}\right\rfloor
\quad(n>1\text{ odd}).
\]

At n=1 the coefficient is defined to be zero, but this does not make 1 prime. The complete classifier treats 0 and 1 as neither, 2 as prime, even integers greater than 2 as composite, and applies D only to odd n>1. Negative numbers, noninteger inputs and booleans are rejected by this implementation.

## The subtraction that leaves composites

Let O(z)=z/(1-z^2) generate the positive odd integers. Start with all ordered pairs of positive odd factors:

\[
T(z)=\sum_{d\ge1,\ d\text{ odd}}\frac{z^d}{1-z^{2d}}
=\sum_{a,b\ge1,\ a,b\text{ odd}}z^{ab}.
\]

Remove the pairs (1,b) and (a,1). Each family contributes O(z). Their intersection (1,1) was removed twice, so restore z:

\[
\boxed{Q(z)=T(z)-2O(z)+z
=\sum_{d\ge3,\ d\text{ odd}}\frac{z^{3d}}{1-z^{2d}}.}
\]

Its coefficient at an odd n>1 is tau(n)-2. It is positive exactly at odd composites; coefficients at 0, 1 and even indices are zero. Prime terms disappear because an odd prime has only the two removed factorizations. A composite retains its nontrivial pairs.

To count unordered pairs, use

\[
\boxed{U(z)=\sum_{d\ge3,\ d\text{ odd}}\frac{z^{d^2}}{1-z^{2d}}
=\sum_{d\ge3,\ d\text{ odd}}\sum_{m\ge0}z^{d(d+2m)}.}
\]

The coefficient of z^n is D(n) for odd n>1. These identities hold as formal power series: only finitely many factor pairs contribute to any coefficient. They also converge absolutely for |z|<1. For r=|z|<1,

\[
\sum_{d\ge3,\ d\text{ odd}}\frac{r^{3d}}{1-r^{2d}}
\le \frac{r^9}{(1-r^6)^2}.
\]

The unordered sum is a subseries of the ordered sum. The d=1 component of T is also convergent in this disk.

The underlying established identity is the [Lambert series divisor expansion](https://dlmf.nist.gov/27.7.E2), with the standard divisor-counting specialization in [DLMF 27.7.5](https://dlmf.nist.gov/27.7.E5). The restriction to odd factors and removal of the unit families above are elementary deductions from factor counting.

## Finite series are sufficient and exact

For an integer cutoff N>=0, define the finite polynomial

\[
U_N(z)=\sum_{\substack{3\le d\le\sqrt N\\d\text{ odd}}}
\sum_{m=0}^{\lfloor(N-d^2)/(2d)\rfloor}z^{d^2+2dm}.
\]

Every coefficient through N agrees exactly with U(z). There is no truncation error for those coefficients: d>sqrt(N) contributes nothing below or at N. Since U_N is a polynomial, its finite-sum definition is valid at every complex z, including z=1; evaluating U_N(1) gives a total number of pairs, not the individual coefficient pattern.

At N=100 the four smaller factors are 3,5,7,9:

- d=3 contributes exponents 9,15,21,...,99.
- d=5 contributes 25,35,45,...,95.
- d=7 contributes 49,63,77,91.
- d=9 contributes 81,99.

There are 30 factor-pair contributions at 25 distinct odd-composite exponents. For example D(45)=2 from (3,15) and (5,9); D(81)=2 from (3,27) and (9,9); D(97)=0; D(99)=2 from (3,33) and (9,11). This finite construction needs no infinite endpoint and no list of earlier primes.

## Why bare forward-minus-reverse cannot supply this indicator

For a polynomial F_N(z)=sum_{n=0}^N a_n z^n, define its reversal R_NF_N(z)=z^N F_N(1/z), interpreted polynomially also at z=0. Its nth coefficient is a_{N-n}, and reversing twice restores F_N.

Therefore the difference B=F_N-R_NF_N satisfies R_NB=-B: its coefficients obey b_{N-n}=-b_n. If all b_n are nonnegative, every coefficient must be zero. A nonzero ordinary composite indicator with nonnegative coefficients on the full range 0..N cannot be such a bare reversal difference. For even N, reversal preserves odd positions, so the same obstruction applies to nonnegative coefficients on all the odd positions.

This does not rule out additional operations such as masking, absolute values, or a differently defined backward recurrence. Each would need its own derivation. The statement applies to the explicitly defined polynomial reversal, not every conceivable interpretation of the user's proposal.

For a concrete prime-polynomial control at N=10, F_10=z^2+z^3+z^5+z^7 gives F_10-R_10F_10=z^2-z^8. At N=100 the difference at both 97 (prime) and 99 (composite) is zero. The tested reversal does not isolate composites.

## Zeta representation and its limits

For Re(s)>1, let

\[
A(s)=(1-2^{-s})\zeta(s)=\sum_{n\ge1,\ n\text{ odd}}n^{-s}.
\]

Absolute convergence permits multiplying the series. Ordered and unordered composite pair counts have the Dirichlet generating functions

\[
Q_D(s)=(A(s)-1)^2,\qquad
U_D(s)=\frac{(A(s)-1)^2+A(2s)-1}{2}.
\]

The A(2s)-1 term counts diagonal pairs d*d, d odd and at least 3. These are divisor-series identities, consistent with the established [Dirichlet series for divisor counts](https://dlmf.nist.gov/27.4.E10).

The argument s weights all coefficient indices simultaneously. Evaluating at s=97 does not extract the coefficient at n=97. For every real s>1, both Q_D and U_D are strictly positive, so a value-zero test on that real line cannot separate prime candidates from composite candidates. Evaluation on Re(s)=1/2 requires analytic continuation outside the convergence domain used in this derivation. At any nontrivial zeta zero rho, Q_D(rho)=1; these are not the zeros of Q_D. None of this proves RH or supplies a color-quadrant primality test.

An additional weighted composite series is H(s)=A(s)-1-log A(s), with the analytic logarithm normalized to zero toward Re(s)=+infinity. Expanding the [Euler product](https://dlmf.nist.gov/25.2.E11) over odd primes shows its coefficient is 0 at odd primes, 1-1/k at odd prime powers p^k (k>=2), and 1 at odd numbers with two or more distinct prime factors; all even and unit coefficients are 0. Thus its support is also exactly the odd composites. This is a supplementary analytic identity, not the executed classifier, and no efficiency result follows from its notation. We do not assume that an arbitrary principal-log call reproduces the required branch everywhere.

## What has and has not been accomplished

We have an exact coefficient formula and a finite implementation whose candidate calculation has no prior-prime inputs. The infinite-set subtraction concern is resolved by coefficientwise factor counting. The finite experiment independently compares constructions and classifications, checks squares and domain guards, and tests reversal separately.

Directly evaluating D(n) examines max(0,(isqrt(n)-1)//2) odd divisor candidates. It is the arithmetic of trial division in another form. Computing all coefficients in a range is a divisor sieve; local timings compare it with a separate prime sieve without claiming either an optimality theorem or a universal benchmark. No novel primality algorithm, constant-time decision, direct fast nth-prime formula, or RH advance has been established.
