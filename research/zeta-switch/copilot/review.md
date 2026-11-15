publish: graph.riemann.switch.copilot.response

STATUS: COMPLETE
ACK: 17ebab1e931f490eb033c0de2ce1af25
CLOCK: 2026-11-15T01:10:38.1345511-08:00

VERDICT: REVISE

REASONING
The plan covers the principal mathematical and rendering risks: independent high-precision values and derivatives at fixed samples, eta removable sites and neighborhoods, separate zero/one-point residuals, palette and marker independence, higher-resolution exports, seam metadata, no interpolation-based zero certification, and targeted corrupted-export controls. Its scope also appropriately avoids claiming global RH results or rigorous error bounds.

A material gap remains: no quantitative pass tolerances are specified for values, derivatives, identities, selector decisions, or marker residuals. Nor are refinement stopping criteria and sampling limits defined. Comparing higher-resolution exports is useful, but without thresholds and a clear statement that rendered candidates are exploratory—not exhaustive or certified—it cannot establish reliable refinement behavior. Specify those criteria and keep completeness claims explicitly out of scope.

TESTS
No tests executed; this is a review of the supplied mathematical contract and validation plan, not a code or test certification.

