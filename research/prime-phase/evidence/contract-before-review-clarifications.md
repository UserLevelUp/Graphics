# Prime-factor phase experiment

defines: graph.primes.phase
consumer: graph.riemann
consumer: graph.zeta.origins

The user proposes compounding color from prime contributions. For s=sigma+it with sigma>1, form
L_N(s) = -sum over primes p<=N of Log(1-p^(-s)), and P_N(s)=exp(L_N(s)).
Keep the full complex value until display. Angle controls the quadrant color, while log magnitude records accumulated scale. State explicitly how points on the axes are colored.

The convergent Euler product supplies the analytic logarithm in this domain. A principal logarithm of the final product can differ from L_N by a multiple of 2*pi*i. Compare circular phase and complex products accordingly.

For integer N>=2 an elementary truncation bound is
B_N = N^(1-sigma) / ((sigma-1)*(1-(N+1)^(-sigma))).
The proposed bounds are |log(zeta)-L_N| <= B_N and
|zeta-P_N| <= |P_N|*(exp(B_N)-1).
Floating-point error and reference-evaluator error require their own accounting.

Use N=32,128,512,2048 and s=2, 2+14.134725141734694i, 2+23.298320492762855i.
The real reference is pi^2/6. The complex reference must be independently checked.
Compare direct multiplication, log accumulation, reversed prime order, and grouped multiplication.
The bound should decrease with N. Actual complex error can fluctuate through cancellation.
Color changes near axes can be valid while numerical values converge.

The finite-prime product experiment uses sigma>1. Analytic continuation into the critical strip and the global RH proof remain open research.

Slices:
carbon reviews the derivation and mathematical limitations.
copilot reviews acceptance cases and numerical failure modes.
codex independently audits the mathematical inference and finite-experiment limitations.
render implements the visual experiment after all three reviews are accepted.
acceptance verifies rendering and numerical comparisons and records a snapshot.

Reviewers return a concise report with VERDICT, REASONING and TESTS sections. Use ACCEPT or REVISE as the verdict. Identify concrete corrections. This assignment is a textual review. All needed mathematical scope is included here. Return the review as the final response.

Source https://dlmf.nist.gov/25.2.E11
