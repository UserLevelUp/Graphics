# Quantitative validation and review resolution

consumer: graph.riemann.switch.verify
consumer: graph.riemann.switch.proof

The review request for explicit numerical thresholds and stopping rules is resolved by `verify_exports.py` and `independent-validation.json`. These are empirical numerical checks, not certified complex-error enclosures or an exhaustive root count.

The independent evaluator is pinned mpmath 1.3.0 at 80 decimal digits. Each export must contain the entire 16-by-9 inclusive rectangle grid, 18 points around the two removable eta-quotient locations at heights `4*pi/log(2)` and `6*pi/log(2)` with sigma/height offsets `-1e-7,0,1e-7`, and three reference-location probes: 165 samples total. Fixed reference probes may lie outside a cropped view; their `insideView` flags are checked. All points remain within the numerical evaluation contract sigma 0.05 through 3, height 10 through 30. Eight additional selector probes test both seam sides, exact ties, exact 0/1, and positive/negative `1e-18` inputs.

| Check | Acceptance threshold |
| --- | --- |
| Zeta and N96 refined value against mpmath | `5e-11 * max(1,abs(reference))` |
| Analytic zeta derivative against mpmath | `5e-10 * max(1,abs(reference derivative))` |
| Shift/product/magnitude identities | `2e-12 * max(1,abs(expected))` |
| Branch-1 value and imaginary-component preservation | Exact equality of exported binary values |
| Reported small residual/refinement magnitudes | Absolute discrepancy at most `1e-20` |
| Independent marker target residual | At most `1e-8` |
| Marker refinement movement | Strictly below `1e-6` |
| Marker derivative magnitude | Greater than `1e-6` |

The computed-value selector is always checked exactly. Independent branch classification is withheld when `abs(Re(reference)-0.5) <= 5e-11`; the deliberately supplied seam reference falls in this category. Exact tie probes still require branch 1. The checker evaluates every required sample and marker, fails on the first mismatch, and exits nonzero. It makes no adaptive or interpolation claim between samples. Pixel-count consistency is checked, but the entire image grid is not independently recomputed at 80 digits.

The native model uses Euler–Maclaurin with N64, ten Bernoulli corrections, and N96 refinement. Its marker search uses sigma seeds `0.35,1,2,2.8` and inclusive height seeds spaced at most 1 apart (`count=max(2,ceil(maxT-minT))`). Each Newton candidate permits at most 30 iterations, requires residual below `2e-12`, rejects derivative magnitude below `1e-10`, caps steps at 1.5, and rejects invalid or out-of-guard iterates. Successful candidates must lie in the actual view. Same-target candidates closer than `1e-7` are deduplicated; N96 Newton refinement is then attempted. The verifier reads and checks these source settings and records the source SHA256 in its report. Refinement agreement is empirical evidence, not a rigorous error bound.

All four final exports pass: overview, rotation 73 with markers hidden, resolution 384, and the cropped height range 23.1–23.6. There are 660 sample evaluations and 558 exactly matching shared-coordinate comparisons across palette, marker visibility, resolution, and domain changes. Maximum observed absolute errors are `6.439e-14` for zeta, `2.298e-13` for its derivative, and `8.496e-14` for N96 values. Maximum independent marker residual is `6.964e-13`. The report binds each input export by SHA256.

Eleven corruptions are rejected: self-consistent wrong zeta, wrong derivative, flipped selector, altered selected value, altered analytic product, hidden refinement discrepancy, wrong tie, seam falsely set to zero, erased tiny branch-1 value, exchanged zero/1-point marker labels, and false analyticity metadata. In particular, direct conditional branch selection preserves tiny values that `(zeta-1)+1` can erase by cancellation. The seam remains nonzero and discontinuous; its rendering is not a new zero. The analytic product and the two marker target levels remain separate. No conclusion about RH follows from this validation.
