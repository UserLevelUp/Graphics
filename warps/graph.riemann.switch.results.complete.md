# Two-state zeta lab: bounded implementation and validation

defines: graph.riemann.switch.results
consumer: graph.riemann.switch.proof
consumer: graph.riemann.switch.verify
consumer: graph.riemann.switch.ui
consumer: graph.riemann.switch.review.audit

The child implements the agreed auxiliary unit-term switch with four aligned native views, independent marker overlays, hover inspection and exports. Its namespace remains under the existing graph base: graph.riemann.switch. Baseline: cf51254, on graph/riemann-local-origins.

For exact regular inputs, Z1=zeta, Z0=zeta-1 and b=1 when Re(zeta)<=1/2, otherwise 0. W selects Zb, while G=zeta(zeta-1) provides an analytic comparison away from the pole. Both have precisely the union of the zeta-zero and zeta-one level sets. W is discontinuous on the switching seam; its continuous magnitude is at least 1/2 there. The input critical line and output seam are different conditions. The derivation in research/zeta-switch/math-audit.md supplies no exclusion of hypothetical off-line zeta zeros, all of which would survive these maps. No novelty or RH proof is claimed.

Implementation uses one parallel Euler–Maclaurin grid, cached logarithms, and direct bitmap writes for all four panels. It avoids eta-quotient removable singularities. Direct conditional branch selection fixes cancellation of tiny real values; finite rotations are reduced modulo 360 before radians; UI bounds match the validated height interval. Export reuses the displayed frame. Source review and native UI exercise are recorded separately from numerical checks.

Validation comprises 94 native model controls; independent 80-digit mpmath checks of four exports (660 samples), 558 exact cross-export comparisons, eleven rejected corruptions, and a separate native-export comparison. Across the four exports, maximum observed absolute zeta error is 6.44e-14 and derivative error is 2.30e-13. The independent comparison covers explicit samples and markers, not every pixel or all complex inputs. Thresholds, marker-search stopping rules, input hashes and limitations are in evidence/independent-validation.json, native-validation.json and review-resolution.md under research/zeta-switch.

The default view has three numerical zeta-zero markers and one numerical 1-point marker near 1.40778804065289+23.3279877545591i. Marker labels and targets remain separate. The 1-point is a useful control against misreading all selected zeros as RH zeros. Sampled or interpolated color boundaries are never used as certified zero locations.

Carbon and Codex accepted the scoped contract and plan. Copilot returned REVISE because its supplied review text lacked quantitative tolerances and stopping criteria. That actual verdict is retained. The coordinator resolves the request using the explicit thresholds in the checker and review-resolution.md, with observed passing results. Each provider completed a checkpoint and a final turn with explicit coordinator steering. Watch produced status confirms configured protocol checks only. The timing/token audit is in evidence/review-audit.json.

Native UI checks cover the overview, a cropped 1-point view, palette changes, marker visibility, hover values, invalid-bound feedback, and PNG/JSON/text export. Build has zero errors and seven existing warnings. Legacy-route and runner protocol results, including any retained transient observations, are in evidence/regression.json and protocol-tests.txt. A SHA256 manifest binds accepted source and evidence. Historical accepted layers remain unchanged; prior restore points preserve their historical source versions.

The final legacy comparison matches eleven PNGs byte for byte and nineteen data/report sidecars. An earlier run of the same final DLL differed at four pixels in the unchanged zeta-contours renderer; five targeted repeats and the full rerun matched. Its cause remains unresolved. The initial failed record is retained, and passing repeats are not a claim that the legacy renderer is deterministic. All twenty-five scoped Watch protocol/runtime tests pass.

This child completes a finite diagnostic tool. The parent graph.riemann remains open, with no all-heights zero exclusion or prime-generation formula established. The next mathematically meaningful step would require an independent global constraint on zeta or its derivative, or a clearly bounded certified count using analytic maps and validated error bounds. Switching color origins alone supplies no such constraint.
