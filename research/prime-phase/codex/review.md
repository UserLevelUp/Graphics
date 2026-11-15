publish: graph.primes.phase.codex.response

STATUS: COMPLETE
ACK: 161a5a9413d041aa9e2c12d0397ddc01
CLOCK: 2026-11-14T20:53:54.1390276-08:00

VERDICT

ACCEPT the corrected mathematical design. This does not certify an implemented renderer or constitute coordinator acceptance. No remaining concrete mathematical defect is apparent in the proposed scope.

REASONING

For \(\sigma>1\), define
\[
L(s)=\sum_p\sum_{m\ge1}\frac{p^{-ms}}m.
\]
Absolute convergence gives \(e^{L(s)}=\zeta(s)\) and
\[
|L-L_N|
\le\sum_{p>N}\frac{p^{-\sigma}}{1-p^{-\sigma}}
\le B_N.
\]
Consequently, \(|\zeta-P_N|\le |P_N|(e^{B_N}-1)\). These are analytic results for exact quantities, not discoveries established by the samples.

Both positive factors defining \(B_N\) decrease with \(N\). Neither actual complex error nor the product-error bound, which also contains \(|P_N|\), is required to decrease monotonically.

The branch correction is sound: the principal logarithm of the final product need not equal \(L_N\). Normalize display angles modulo \(2\pi\); use the stated half-open quadrants for exact nonzero values and neutral output when uncertainty crosses an axis. Phase is undefined at the origin.

All samples lie on \(\Re(s)=2\). Neither shared imaginary coordinates, finite-product nonvanishing, nor converging colors constrains zeros in the critical strip. The derivative-experiment provenance of the third ordinate supplies no zeta-zero assertion. Analytic continuation is established; this finite experiment supplies no proof or disproof of RH.

TESTS

Not executed: this is a textual audit.

- Compare all four computation methods at the 12 specified cases, including complex values and circular phase.
- Check the real reference \(\pi^2/6\), and independently validate complex references.
- Exercise every axis, phase wraparound, origin handling, and uncertainty crossing axes.
- Keep truncation, floating-point, and reference errors separate. The preliminary double-precision Euler–Maclaurin checks are empirical evidence; certified numerical or color claims require justified error enclosures.
