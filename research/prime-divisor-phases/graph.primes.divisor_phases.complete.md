# Accepted finite divisor-phase analysis

defines: graph.primes.divisor_phases
consumer: graph.primes.quadrant_phase

Warp: `warps/graph.primes.divisor_phases.warp-map.json`.

The analysis and visualization slices are accepted within the scope recorded in `evidence/acceptance.json`: exact finite arithmetic, the proof, reviewed scientific figures, and statically checked offline-explorer source. The live Recur projection in `evidence/warp-progress.json` reports 2/2 slices complete with declared review evidence. Completion does not imply that Recur reran the producers or independently proved the mathematical claims.

The analysis uses raw divisor phases and exact rational quadrant bins, with prime labels used only for comparison cohorts and independent checks. It covers integers0..100,625prime pairs,576odd-prime pairs and600odd-composite control pairs. With shared45-degree alignment, combining raw and half-step observations reduces the odd-prime cohort's false divisor-like color matches from104 to43. The same type of improvement occurs for composite controls; it is a resolution result, not a new prime-specific arithmetic invariant.

Independent review passed16checks. Its recorded input hashes and the acceptance receipt's evidence hashes were rechecked before publishing the completion layers. The visualization acceptance covers the static PNG/SVG figures and source review. See `evidence/review.json`, `evidence/validation.json` and `evidence/visualization.json` for coverage and limits.

**Browser interaction and responsive-layout QA remain incomplete.** The user stopped Computer Use with Escape before the explorer page was observed. `evidence/explorer-validation.json` preserves that limitation. The visualization slice must not be presented as a successful browser test. The offline builder and packaged exact analysis replay successfully; this does not substitute for browser interaction evidence.

Deliverables include the offline explorer, PNG/SVG figures, source and proof. The ZIP delivery receipt records archive hashes and replay outcomes. No novelty, general primality shortcut, speedup or RH result is claimed. The later zero-index continuation animation is a separate lane and is not accepted by this capsule.
