# Completed composite remainder: exact subtraction and coefficient test

defines: graph.primes.composite_remainder
consumer: graph.primes.divisor_phases

The user asked the coordinator to implement and test the mathematics directly using Recur and Eventness. This superseded the planned 30-minute external Carbon consultation. Three actual Carbon checkpoints supplied complement, unordered odd-factor and zeta-series leads; none is accepted as proof on the strength of a model response.

Candidate: start with all ordered pairs of positive odd integers. Remove the pairs with either factor 1, restoring the doubly removed pair (1,1). The remaining generating-series coefficient at odd n>1 is tau(n)-2, positive exactly for composites. Count each unordered nontrivial pair once for a square-root-bounded coefficient calculation.

Completed: exact integer coefficients, an all-integer elementary proof with domain guards, independent comparisons through 100000, 123 prefix checks, 99 domain rejections, 13 larger controls, reversal tests, operation counts, scoped timings and a checked static figure for 0..100. All 100001 classifications and factor-pair lists passed independent factorization-based verification. The finite cutoff produces exact coefficients through its bound.

Bare forward-minus-reversal produces antisymmetric coefficients and does not produce a nonzero nonnegative composite indicator. Removing the unit-factor families does produce the desired remainder. Direct coefficient extraction still checks divisors; the local conventional sieve implementation was faster. The zeta Dirichlet-series forms have reviewed coefficient identities, not a claim that evaluating at s=n tests n or that an RH result follows.

Evidence: `evidence/validation.json`, `evidence/independent-review.json`, `figures/figure-review.json`, `evidence/acceptance.json` and `evidence/warp-progress.json`. Both Warp review gates are accepted. Prior accepted graphics and presentations remain unchanged.
