# Prime-factor phase experiment

defines: graph.primes.phase
consumer: graph.riemann
consumer: graph.zeta.origins

The user proposes compounding color from prime contributions. For s=sigma+it with sigma>1, form
L_N(s) = -sum over primes p<=N of Log(1-p^(-s)), and P_N(s)=exp(L_N(s)).
Keep the full complex value until display. Angle controls the quadrant color, while log magnitude records accumulated scale. Normalize angle to [0,2*pi) and assign exact nonzero values to half-open quadrants [k*pi/2,(k+1)*pi/2). Use a neutral/undefined phase marker at the origin and when the stated uncertainty crosses an axis. These are implementation requirements, not completed rendering behavior.

Define log(zeta(s)) here as L(s)=sum_p sum_{m>=1} p^(-m*s)/m, the analytic Euler-series branch in sigma>1. The convergent Euler product supplies this analytic logarithm. A principal logarithm of the final product can differ from L_N by a multiple of 2*pi*i. Compare circular phase and complex products accordingly.

For integer N>=2 an elementary truncation bound is
B_N = N^(1-sigma) / ((sigma-1)*(1-(N+1)^(-sigma))).
The proposed bounds are |log(zeta)-L_N| <= B_N and
|zeta-P_N| <= |P_N|*(exp(B_N)-1).
Floating-point error and reference-evaluator error require their own accounting.

Use N=32,128,512,2048 and s=2, 2+14.134725141734694i, 2+23.298320492762855i.
The real reference is pi^2/6. The complex reference must be independently checked.
Compare direct multiplication, log accumulation, reversed prime order, and grouped multiplication.
B_N must decrease with N. No monotonicity claim is made for the product-error bound containing |P_N|. Actual complex error can fluctuate through cancellation.
Color changes near axes can be valid while numerical values converge.

The finite-prime product experiment uses sigma>1. Analytic continuation of zeta into the critical strip is established mathematics. Extending this particular renderer into that strip requires an appropriate representation and separate verification. This finite sigma>1 experiment provides no proof or disproof of RH. The third test ordinate is a control taken from an earlier zeta-derivative critical-point experiment, not a zeta-zero assertion.

Slices:
carbon reviews the derivation and mathematical limitations.
copilot reviews acceptance cases and numerical failure modes.
codex independently audits the mathematical inference and finite-experiment limitations.
hydrogen prepares the routine implementation test checklist.
render implements the visual experiment after the three reviews and the checklist are accepted.
acceptance verifies rendering and numerical comparisons and records a snapshot.

Reviewers return a concise report with VERDICT, REASONING and TESTS sections. Use ACCEPT or REVISE as the verdict. Identify concrete corrections. This assignment is a textual review. All needed mathematical scope is included here. Return the review as the final response.

Source https://dlmf.nist.gov/25.2.E11
