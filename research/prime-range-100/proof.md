# A finite proof, and what phase colors can contribute

**Proved finite claim.** The primes in the inclusive integer interval 0 through 100 are exactly

2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97.

There are 25 primes, 74 composites, and two integers that are neither: 0 and 1. A prime is an integer greater than 1 with exactly two positive divisors. The integer 1 is a unit; a visualization option that includes it does not change this definition.

## Why the list is complete

If an integer n is composite, write n = ab with integers 2 ≤ a ≤ b. Then a² ≤ n, so a ≤ √n. Some prime q divides a, hence q divides n and q ≤ √n. For n ≤ 100 this gives q ≤ 10, so q is one of 2, 3, 5, 7.

Therefore, for each integer 2 ≤ n ≤ 100, it suffices to test the primes q in {2,3,5,7} satisfying q² ≤ n. A zero remainder gives a nontrivial factorization, proving compositeness. If every required remainder is nonzero, no possible small prime factor exists; the lemma rules out compositeness, proving primality. The comparison q² ≤ n includes equality: 49 = 7² must be tested against 7. The small primes themselves are not crossed out.

[certificate.json](certificate.json) supplies exactly one record for every n from 0 through 100. Each composite record contains a divisor and cofactor with 1 < d,q < n and dq = n. Each prime record contains all required exact nonzero remainders. The verifier checks coverage, types, witnesses and remainders with integer arithmetic. No floating-point approximations occur.

For example, 97 has remainders 1, 1, 2 and 6 modulo 2, 3, 5 and 7. These exclude every possible small prime factor, so 97 is prime. Conversely, 91 = 7·13 is composite. The independent cross-check tests every proper divisor, and adversarial checks reject missing rows, misclassifying 1 or 49, omitted square-boundary tests, false factors and false remainders.

This is an elementary finite proof and reusable reference benchmark. It is established mathematics, not a new prime formula or a proof of RH. The violet prime labels are generated from certified divisibility facts. They are not predictions made by the brush.

## From a phase picture to a zero count

For zero-finding, colors must encode the current function values, for example the four sectors of arg ζ(s) at fixed target a = 0. Accumulated brush paint records drawing history and can depend on stroke direction and overwrite order. Keep that history separate from the instantaneous function-phase map.

Phase patterns can suggest candidate neighborhoods, but a boundary or color junction alone does not prove a zero or distinguish every zero, pole, aliasing artifact or unresolved feature. Phase is undefined at a zero. Four sectors also discard the within-sector angle; sampled colors alone do not certify the continuous winding.

**Exact model example.** Let f(z) = z and C be the positively oriented unit circle z(t) = exp(it), 0 ≤ t ≤ 2π. Then |f(z(t))| = 1 throughout C, so f never vanishes on C. A continuous argument along the contour is θ(t) = t, hence Δ arg f = 2π. Since f is entire and has no poles, the argument principle gives exactly one zero inside C, counted with multiplicity. This is the simple zero z = 0. The phase diagram illustrates this analytic proof; pixels are not its premises.

In general, for a meromorphic function in a neighborhood of a simple, piecewise smooth, positively oriented closed contour and its interior, with no zeros or poles on the contour,

N − P = (1/(2πi)) ∮ f′(z)/f(z) dz = Δ arg f/(2π),

where N and P count interior zeros and poles with multiplicity. See [DLMF 1.10.9](https://dlmf.nist.gov/1.10.E9). Phase visualization and its uses are established work; see [Wegert, Phase Plots of Complex Functions](https://arxiv.org/abs/1007.2295).

For ζ, a rigorous computational implementation would use outward-rounded enclosures, certify nonvanishing over every segment of the contour, account for any pole, and enclose the winding in a single integer. Subdividing certified contours can narrow a zero's location. A finite RH verification additionally needs a complete zero count and proof that all those zeros are on Re(s) = 1/2. A global RH proof needs an argument covering all heights. These ζ obligations are future work here; neither the prime certificate nor the model f(z)=z proves them.

## Reproduce and test a future prediction rule

From this directory, run:

```text
python prime_certificate.py verify certificate.json
python check_certificate.py
```

To evaluate independently supplied labels, supply JSON with `predictions` containing exactly 101 ordered records `{ "n": 0, "isPrime": false }` through n = 100, then run:

```text
python prime_certificate.py evaluate certificate.json --predictions candidate.json
```

The evaluator reports every error and the confusion matrix. It does not derive a prediction from a color. A perfect match on this public interval is a finite test only. Before claiming prediction, specify and freeze the brush rule, exclude primality/divisor answers from its inputs, and evaluate on an unseen range. There is no such validated brush predictor in this deliverable.
