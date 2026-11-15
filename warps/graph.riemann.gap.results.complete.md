# Interaction-aware finite-polynomial bounds: completed result

defines: graph.riemann.gap.results
consumer: graph.riemann.gap
consumer: graph.riemann.gap.proof
consumer: graph.riemann.gap.verify
consumer: graph.riemann.gap.review.audit

The bounded mathematical result is a pair of stronger collision-free intervals for the exact finite polynomial flow P_t=-P_zz, initially having n>=3 distinct real roots. Let m be the smallest initial adjacent gap, D the initial diameter, and kappa=(n-2)/D^2. The constant-diameter guarantee is T=-log(1-kappa*m^2/2)/(4*kappa), strictly greater than m^2/8. Accounting for backward contraction of the diameter gives the still stronger T_dynamic in interaction-bound-proof.md. Both arguments use a maximal real-simple-root interval and a first-collision contradiction, rather than assuming the desired continuation.

For roots -3,-1,1,3:

| Guarantee or reference | Backward duration |
|---|---:|
| Previous nearest-gap guarantee | 0.5 |
| Constant-diameter interaction guarantee | 0.5300236604537255... |
| Contracting-diameter interaction guarantee | 0.5397189134471992... |
| Actual first collision, independently proved | 2/3 |

The strongest guarantee is about 7.94% longer than the previous guaranteed interval. This percentage describes this control's interval only. The new bound is not an exact collision predictor and is not an RH result or novelty claim.

Implementation: research/gap-bound/verify_bound.py accepts custom comma-separated rational roots, sorts input, rejects duplicates and unsupported degrees below three, and emits exact rational enclosures plus independent Sturm counts. It uses a proved logarithm-series tail bound and integer-power bisection for the dynamic bound. Neither bound_data nor certify_case receives a known collision answer; the quartic threshold is confined to independent controls. Display decimals and the standalone color plot are approximate.

Validation: 25 root configurations spanning degrees 3-8, including uniform, clustered, uneven, translated and scaled cases; 100 exact rational-time Sturm counts, including times beyond the old guarantee and beyond the constant-diameter guarantee; four rejected controls (heat-sign error, inflated safe duration, repeated initial roots, unsupported degree two). Custom rational and unsorted CLI calls succeed; invalid CLI calls return failed JSON and nonzero exit status. An independent reviewer also checked Sturm handling of repeated real and nonreal roots and negative leading coefficients. The general theorem is the separate human analytic proof, not an inference from the finite suite.

Watch coordination: Carbon and Codex reviewed the supplied analytic arguments; Hydrogen mapped the evidence checklist without claiming mathematical validation. Three latest attempts reached produced after their configured protocol checks. Six checkpoint/final responses arrived within their 180-second deadlines; the longest observed response took 131.333 seconds. All continuation tokens and reported-clock ranges were independently checked. Clock execution itself is provider-reported. The records are in evidence/review-audit.json and the provider run histories.

The first Carbon attempt failed on a transient Windows file-replacement lock. The first Codex attempt saved its completed review but failed printing a Unicode comparison symbol to a cp1252 stream. Bounded Watch retries recovered both; the failed attempts and diagnostics are retained. Carbon's first mathematical checkpoint also contained an incorrect product inequality. Coordinator review identified it, and Carbon explicitly retracted it before re-deriving the correct reciprocal-term estimate. Agreement among helpers was not treated as proof.

The exact runner used for those attempts is preserved in evidence/runner-used.py. After all workers terminated, the current runner was hardened for bounded PermissionError retries and ASCII-safe JSON console output; the UTF-8 review files remain unchanged. Separate runtime/protocol tests cover those fixes. Historical attempts remain evidence of the recorded version and were not rewritten.

The parent graph.riemann stays open. The finite global-diameter argument does not transfer to the infinite Riemann deformation. In growing dense root configurations the two guarantees tend to zero along with the minimum gap. The open tail-control obligation and conditional zeta interpretation are recorded in graph.riemann.gap.next.current.md.
