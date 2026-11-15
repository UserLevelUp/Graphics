# Oriented zeta contours

defines: graph.zeta.contours

Use the overwrite experiment's phase palette to color the samples of a directed boundary. Sum the signed changes in the phase of zeta around the entire boundary. Compare 16 and 32 samples per edge and mark a count unresolved if they disagree, an increment reaches 90 degrees, or a sample is too close to zero. Reversing a contour should reverse its winding. Compare the three band counts with the count around the outer contour.

Compare the estimated total with a Hardy Z sign bracket on the critical line. Hold the rectangle and critical line fixed and rerun the contour diagnostic on zeta(s - 0.12). This control should detect a zero to the right of the line. Keep the floating-point scope visible in the output.

## Research inputs

- The definition and real-valued sign test for Hardy Z are used in the renderer. [NIST DLMF 25.10](https://dlmf.nist.gov/25.10#ii)
- Platt and Trudgian establish the hypothesis for zeros up to height 3 × 10^12. Their workflow accounts for zeros using sign changes, rigorous ball arithmetic and a variant of Turing's method. Graphics borrows the comparison between an on-line detection and a total count within a window. Its total comes from sampled winding and has no rigorous error bounds. [Platt and Trudgian](https://arxiv.org/abs/2004.09765)
- Anthropic's Claude produced an argument for the asymptotic 67.25% lower bound for simple critical-line zeros. Alpöge and Furman checked it, and Lamzouri gave a separate, simpler proof. An October preprint by Knausgård reports a further bound above 67.35%, with Lean proofs that assume three computed inequalities as axioms. These asymptotic results supply context for future work on spacing and multiplicity. They supply no local pixel classification. [Anthropic](https://www.anthropic.com/research/riemann-zeta) · [Lamzouri](https://arxiv.org/abs/2609.02882) · [Knausgård](https://arxiv.org/abs/2610.08965)
