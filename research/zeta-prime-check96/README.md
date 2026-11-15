# 96, 97, and an actual zeta-phase test

**Finding:** comparing the current four-sector phase of ζ(s) with ζ(s+1) removes five composite matches to 97, but also removes three prime matches on integers 2–100. The surviving color pair still contains seven primes and 28 composites. This paired rule is not a reliable prime test. This is useful counterevidence to a specific proposed shortcut, not evidence against every conceivable use of zeta.

## Exact calculation first

For 96, the remainders modulo 2, 3, 5 and 7 are **0, 0, 1, 5**. In particular 96 = 2 × 48, so it is composite.

For 97, the remainders are **1, 1, 2, 6**. Every composite at most 100 has a prime divisor at most 10, so these checks prove 97 prime. This proof does not depend on a phase picture.

96 is one composite control. It does not represent a universal phase appearance for all composites. Also, 0 and 1 are nonprime but are not composite.

## Evaluate the actual zeta function

We explicitly use integer n as the height in s = 1/2 + in, hold the output target at zero, and use the current unrotated four-sector phase map. This choice is a test mapping, not an asserted theorem identifying integer prime labels with zeta zeros. Values are evaluated with mpmath, not by selecting prime factors before drawing an Euler product.

| n | Exact class | ζ(1/2 + in), rounded | Phase | Sector |
|---|---|---|---|---|
| 95 | composite | 0.343530 + 0.217245i | 32.31° | I |
| 96 | composite | −0.166198 + 0.170006i | 134.35° | II |
| 97 | prime | 1.375850 + 2.047089i | 56.09° | I |
| 98 | composite | 2.277755 − 0.941458i | −22.46° | IV |
| 99 | composite | 0.115074 + 0.575861i | 78.70° | I |

The 96/97 contrast alone looks promising, but 95 and 99 immediately show why sector I is not a prime signal. On all integers 2–100:

| Sector | Prime heights | Composite heights |
|---|---:|---:|
| I | 10 | 33 |
| II | 3 | 3 |
| III | 1 | 6 |
| IV | 11 | 32 |

Calling sector I a candidate-prime color selects 43 numbers, including 33 composites, and misses 15 of the 25 primes. Every sector is mixed, so no rule using **only this quadrant** can perfectly classify even this finite interval. Any binary assignment of these four sectors incurs at least 25 errors among the 99 integers, the same minimum error count as simply calling every integer composite. That is an in-sample diagnostic, not a trained predictor or a statement about richer features.

If n is instead substituted directly as a real argument, ζ(96) and ζ(97) are both positive real numbers greater than 1, so both have phase zero. This follows from the positive [Dirichlet series](https://dlmf.nist.gov/25.2.E1).

On the critical line, the [Hardy Z relation](https://dlmf.nist.gov/25.10.E1) says Z(t) = exp(iθ(t))ζ(1/2+it) is real. Away from zeros, arg ζ is therefore −θ(t) modulo π; the sign of Z selects the ray. The phase follows this analytic geometry. A prime-specific criterion on integer t has not been established here.

## The requested secondary function: ζ(s+1)

The final requested comparison shifts the **input** from s_n = 1/2 + in to s_n + 1 = 3/2 + in. It does not add one to the output ζ(s). The earlier output-translation calculation is retained separately as superseded evidence and is not the result reported here.

For the requested examples:

- ζ(3/2 + 96i) ≈ 0.6465700007 + 0.2978214012i, with phase 24.73162046°.
- ζ(3/2 + 97i) ≈ 1.0704471233 + 0.4836653181i, with phase 24.31511088°.

| n | Exact class | Phase ζ(s_n) | Phase ζ(s_n+1) | Sector pair |
|---|---|---:|---:|---|
| 95 | composite | 32.31° | −0.61° | I, IV |
| 96 | composite | 134.35° | 24.73° | II, I |
| 97 | prime | 56.09° | 24.32° | I, I |
| 98 | composite | −22.46° | 4.73° | IV, I |
| 99 | composite | 78.70° | 3.84° | I, I |

Requiring the same pair as 97, **(I,I)**, now rejects composite 95, but still admits composite 99. In the full finite check it retains seven primes and 28 composites. Relative to the original quadrant-I rule, it removes five false positives while losing three true positives. It misses 18 of the 25 primes. These counts compare an explicitly stated rule; they do not result from tuning a predictor.

Every observed pair still contains both classes:

| Original / secondary sector | Primes | Composites |
|---|---:|---:|
| I / I | 7 | 28 |
| I / IV | 3 | 5 |
| II / I | 3 | 3 |
| III / IV | 1 | 6 |
| IV / I | 2 | 8 |
| IV / IV | 9 | 24 |

Thus even an arbitrary binary assignment of these observed pairs cannot classify all 99 integers correctly: its minimum is still 25 errors. This does not rule out a future rule using finer phase, magnitude, derivatives, more locations, or another justified transformation. Such a rule needs a mathematical basis, testing on unseen inputs, and a speed comparison; fitting the known labels on 0–100 would not establish a new prime algorithm.

## Equations that do not need a list of preceding primes

A classical exact indicator for an integer m ≥ 2 is

P(m) = product over d = 2,...,floor(sqrt(m)) of ceil((m mod d)/d).

Each factor is zero when d divides m and one otherwise. The empty product is one for 2 and 3; define P(0) = P(1) = 0 separately. Thus P(m) is one exactly for a prime. The implementation uses exact integer remainder comparisons, not floating-point ceiling operations. It needs no supplied list of previous primes, but it performs trial division.

Then π(x) = sum from m=2 to floor(x) of P(m), and the kth prime is p_k = min{m ≥ 2 : π(m) ≥ k}. The next prime after x is min{m integer : m > x and P(m) = 1}. Here π(96)=24, π(97)=25, p_25=97, and the next prime after 97 is 101. These exact search/count identities do not supply an efficient direct shortcut. Candidate-input primality algorithms without a list of all earlier primes are already known; [AKS](https://annals.math.princeton.edu/2004/160-2/p12) is an unconditional deterministic polynomial-time example.

For a zeta-specific direction, the established identity

−ζ′(s)/ζ(s) = sum from m=1 to infinity of Λ(m)/m^s,  Re(s) > 1,

encodes the von Mangoldt coefficients; see [DLMF 27.4.12](https://dlmf.nist.gov/27.4.E12). Λ(m)=log p for m=p^k and is zero otherwise. In particular, Λ(96)=0, Λ(97)=log 97, and Λ(49)=log 7. These coefficient values are consequences of known factorizations here, **not results of a new zeta coefficient-extraction computation**. Prime powers must be distinguished from primes: for m≥2, Λ(m)=log m exactly when m is prime.

A future computational experiment could investigate extracting these coefficients with rigorous error bounds without an input list of primes, then compare its cost with ordinary primality tests. This uses more information than phase at one point, and no speed advantage follows from writing the identity. Such work would build on established analytic number theory; a new fast nth-prime algorithm or an RH result has not been obtained.

## Reproduce and review

```text
python -m pip install -r requirements.txt
python check_phase.py --output evidence
python plot_phase.py --data evidence/comparison.json --output figures
```

The exact label checks cover 101 integers and agree with the previously accepted certificate and an exhaustive proper-divisor cross-check. Zeta values on both vertical lines are compared at 50 and 80 digits; the examples also compare the default Borwein fast path with the explicit Euler–Maclaurin path in the same library. Source inspection found that mpmath 1.3.0 does not route the explicit `method='borwein'` setting through its fast path, so the comparison uses the default call instead. The superseded requested-method report is retained as historical evidence, not the accepted method comparison. This is numerical validation, not interval certification or independent-library validation. Neither zeta zeros nor RH are proved by this experiment. Use a working copy when rerunning to preserve archived evidence.

The figure uses the current continuation palette: I green, II yellow, III purple, IV blue. The phase is current function phase, with no accumulated brush overwrite. Previous accepted media and certificates remain unchanged.

Trace and Warp: `graph.primes.zeta_check96`. Public repository: [UserLevelUp/Graphics](https://github.com/UserLevelUp/Graphics), branch `graph/riemann-continuation`.
