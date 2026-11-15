# Prime-phase review and worker checkpoint

defines: graph.primes.phase.reviews
consumer: graph.primes.phase.carbon.response
consumer: graph.primes.phase.copilot.response
consumer: graph.primes.phase.codex.response
consumer: graph.primes.phase.hydrogen.response
consumer: graph.primes.phase.coordination

The coordinator reviewed all four final artifacts and accepts the three textual reviews and Hydrogen's implementation checklist. This acceptance covers the design and checklist. The prime renderer and its acceptance slice remain pending. The parent Riemann proof remains open.

All four workers returned an initial CHECKPOINT, received a specific coordinator instruction, echoed its unique ACK token, and returned a COMPLETE response. The eight observed turns took 14.31 to 62.75 seconds each. The exact run IDs, artifact paths, and durations are in `research/prime-phase/evidence/helper-summary.json`. Recur marked Carbon attempt 4, Copilot attempt 4, Codex attempt 3, and Hydrogen attempt 1 as produced after their configured artifact checks.

The model-written clocks and the supervisor's monotonic deadlines serve different purposes. Every provider family successfully executed a real clock check during setup. Returned timestamps are observations rather than a mathematical guarantee of future timeliness. The supervisor reports an overdue checkpoint at 180 seconds and preserves partial output if it has to stop a worker at 240 seconds.

The coordinator accepted and applied these review corrections to the current contract:

- Define log(zeta) as the analytic Euler-series branch on Re(s)>1. Compare final principal logarithms modulo 2*pi*i.
- Require decreasing B_N without asserting monotonic actual complex error or monotonicity of the bound containing |P_N|.
- Specify half-open angle quadrants for exact values and a neutral phase display at the origin or when uncertainty crosses an axis.
- Clarify that analytic continuation of zeta is established. Extending this renderer requires a justified representation. This finite experiment supplies no proof or disproof of RH.
- Identify the third ordinate as a control drawn from an earlier derivative-critical-point experiment.

The elementary analytic tail derivation was checked directly by the coordinator: expand each logarithm as its absolutely convergent power series, dominate the tail by the sum over all integers greater than N, and apply the integral bound for x^(-sigma). The product bound then follows from |exp(w)-1| <= exp(|w|)-1. These facts concern exact quantities. No certified floating-point enclosure was produced.

Validation consists of 20 passing focused runner tests, a separate actual Windows owned-process-tree timeout check with retained partial stdout, and four live two-turn handoffs. The runner unit tests use short synthetic deadlines; the live handoffs used 180 seconds. The separate numeric baseline contains 12 double-precision spot checks using independent Euler-Maclaurin reference evaluations at two settings. It covers forward, reverse, and log accumulation comparisons. Grouped multiplication, complete display edge cases, and renderer acceptance are still planned. Hydrogen's checklist explicitly marks every implementation test PLANNED.

Historical setup failures remain in the archived dispatch evidence. They include an early wrapper typo, a Carbon response timeout, invalid Copilot tool syntax, an unavailable saved Copilot model, a Recur notification startup failure whose original stderr was not retained by the old wrapper, and an unavailable saved Codex model. The notification-failure cause is unconfirmed. The current wrapper retains each drain diagnostic and retries at most three times. Model selection corrections were confined to these invocations.

Runtime journals and raw stderr remain local. Git preserves the reviewed artifacts, exact steering instructions, progress event histories, scoped source, tests, and dispatch records. No remote push is part of this checkpoint.
