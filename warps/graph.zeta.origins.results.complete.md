# Local-origin observations

publish: graph.zeta.origins
publish: graph.zeta.origins.samples
consumer: graph.riemann

The original project built successfully after closing its old processes. Local origins opened from its WinForms button and displayed the three plots. The two earlier exports matched their original PNG hashes byte for byte.

The three centers gave winding counts 1/1/1, 2/2/2 and 2/2/1 for radii 0.08, 0.04 and 0.01. All nine loops agreed under 128/256 sampling, 96/128 eta terms and reversed orientation with reversed sign.

The derivative candidate was 2.463161869454 + 23.298320492763i. Its computed |zeta'| was 2.414e-16 while |zeta| was about 0.9296. Changing eta truncation from 96 to 128 terms moved the candidate by 3.553e-15. An independent agent's Euler–Maclaurin calculation with eight Bernoulli corrections and N=32,64,128 gave 2.4631618694543183 + 23.298320492762855i. This is a control to the right of the critical strip.

The affine constant-shift test passed on 16,384 dyadic samples. The reason is the exact algebraic identity documented in graph.riemann.proof.current.md.

These are double-precision numerical observations with convergence checks. Contour enclosures, evaluator error bounds and a proof for all heights remain open. No zero of zeta' in the forbidden left half-strip was established.

Image SHA-256 60595fb4da963e07bbbfb6ef9df009b7430f677f5d95694b68fa3a114359dfe9.

Recur Lang check passed for warps/graph.zeta.origins.recur within WIR1 coverage. The static check excludes numerical accuracy, runtime behavior and mathematical proof.
