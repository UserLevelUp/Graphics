# Divisor colors, prime pairs and half-step coordinates

Trace ID: `graph.primes.divisor_phases`.

This experiment evaluates every integer from 0 through 100 and compares every pair of primes in that range. It tests what quadrant colors preserve about periodic divisibility functions, including the coordinate k=(n-1)/2. It uses no Wilson factorial computation. Prime labels independently identify comparison cohorts and verify the outcome; they do not generate phase colors.

## Observed results

1. **Colors do not change divisibility.** The natural phase is z_d(n)=exp(2*pi*i*n/d). Its exact value is 1 iff d divides n. Assigning a quadrant discards part of that phase information.
2. **A suitable alignment preserves enough information for 0–100.** With a +45-degree phase offset, quadrant I contains only the zero remainder for divisors 2,3,5,7. Rejecting that color in any channel exactly classifies 8..100. Handling 0/1 and the small primes 2,3,5,7 separately covers the whole range. At a0-degree offset this coarse filter wrongly rejects seven primes. The common exact offset interval is [270/7,360/7) degrees.
3. **The half-step view helps resolve ambiguous colors when combined with the original view.** For odd reference p and odd target q, set H_p(q)=exp(2*pi*i*((q-p)/2)/p). Before applying palette offsets, H_p(q)^2=z_p(q). On the same24x24odd-prime cohort, ordinary colors produce104false divisor-like matches, half-step colors110, and requiring both matches reduces them to43. There are24actual self-divisibilities, excluded from those false-match counts.
4. **This benefit is not specific to primes.** On600odd-composite target/reference comparisons,45are actual divisibilities. Among the remaining555pairs, false matches fall from114ordinary to74combined. All odd primes and all odd composites have the same fractional half-unit. Differences in color histograms are also confounded by the target value distributions.

Here a false match means a nonzero remainder has the same coarse quadrant as zero. It is not a false prime classification by the exact arithmetic. In each divisor channel, violet QI means a divisor-like alignment under the45-degree convention; it does not mean prime as it did in the older Wilson encoding.

The two-view zero signature halves the ambiguous angular interval in the half-phase coordinate. With the shared45-degree rule, it isolates zero for odd moduli below16; modulus17 already has collisions. This statement is not an optimality claim over all independent choices of axes. It describes retained resolution, not a new arithmetic invariant or computational speedup.

## Reproduce

Core analysis uses only the Python standard library:

```powershell
python analyze.py --output evidence
python build_explorer.py --output explorer.html
```

Open `explorer.html` in a browser. Change the phase offset, candidate, reference prime, and matrix mode. Known prime outlines are an independent comparison layer. The actual colors use exact bounded integer quadrant calculations.

Scientific PNG/SVG figures require matplotlib and NumPy:

```powershell
python render.py --data evidence/analysis.json --output figures
```

`classify` explicitly accepts only integer candidates0..100. The raw four-divisor filter passes121=11^2, which is a recorded outside-range control. The trigonometric product is checked numerically at integer points; exact rational/integer calculations make the decisions. Neither floating cosine agreement nor these finite checks constitute an interval-arithmetic certificate.

See [proof and findings](proof-and-findings.md) for the all-residue derivations, control cohorts and connection to the user's half-step identity. See `evidence/review.json` for independent checks and limits, and `evidence/explorer-validation.json` for browser observations when available. No novelty, fast general primality algorithm, or RH result is claimed.
