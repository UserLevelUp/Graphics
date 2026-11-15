# Zeta level continuation: mathematical scope

defines: graph.riemann.continuation.presentation.math
consumer: graph.riemann.continuation
consumer: graph.riemann.continuation.animation

The coordinator owns the overall experiment. The scientific animation belongs to `graph.riemann.continuation.animation`. The explanation and presenter belong to `graph.riemann.continuation.presentation` and are produced only after the animation is accepted. A Warp is an isolated, reversible work scope; it is not a physical effect or a mechanism that changes the mathematics.

## Prior work and precise reuse

The earlier tested two-state laboratory at checkpoint `f24b64c` supplies the two fixed output origins, zeta and zeta minus one. Its discontinuous nearest-level selection is not used to track these branches.

[Wegert's phase plots](https://arxiv.org/abs/1007.2295) provide established phase-coloring context. Four-quadrant quantization is our display choice. [Lester's a-point paper](https://arxiv.org/abs/1402.0169) supplies the established subject, not a distribution theorem implemented here. Derivative prediction and Newton correction are classical. The reference uses documented [mpmath zeta functionality](https://mpmath.org/doc/current/functions/zeta.html), with version 1.3.0 pinned. This specific reproducible combination and finite experiment have no established novelty claim.

The presentation also distinguishes three kinds of prior results about **zeta zeros**. [Platt and Trudgian](https://arxiv.org/abs/2004.09765) rigorously verified RH through height \(3\times10^{12}\) using interval arithmetic; our height-10-to-30 view adds no verified RH height. [Lamzouri's September 2026 preprint](https://arxiv.org/abs/2609.02882v2) presents an asymptotic bound exceeding 67.25% for simple zeros on the line, crediting earlier Claude/Anthropic work. This is not a percentage of RH solved or a claim of journal acceptance. [OpenAI's repository](https://github.com/openai/math/blob/main/lean/docs/003.md) reports a zero-free half-plane \(\operatorname{Re}s>7/8\) and Lean formalization. We have not replayed it or independently verified these recent analytic proofs. None is adopted as an assumption or automatically controls our nonzero moving targets. Sources were checked on 2026-11-15; full links and reuse details are in `sources.txt` and the separate `prior-work-audit.json`.

## The question

Replace the earlier two-state selection between zeta and zeta minus one by the continuous family

\[
F_a(s)=\zeta(s)-a,\qquad 0\le a\le1.
\]

Here the origin moves in the **output plane**. The input coordinate \(s=\sigma+it\) is not being translated. The previous fixed states occur at \(a=0\) and \(a=1\); intermediate targets are now followed continuously rather than chosen by the old nearest-value switch.

Start three branches at the first three positive-height zeta zeros, approximately

\[
\rho_1=\tfrac12+14.13472514173469i,\quad
\rho_2=\tfrac12+21.02203963877155i,\quad
\rho_3=\tfrac12+25.01085758014569i.
\]

These displayed decimals are numerical seed labels. The reference computation must supply its own refined starting values and diagnostics. The viewing rectangle is

\[
R=\{s:0.05\le\operatorname{Re}s\le3,\ 10\le\operatorname{Im}s\le30\}.
\]

The measured objects are labeled solutions \(s_j(a)\) of \(\zeta(s_j(a))=a\). The pole \(s=1\) lies outside this rectangle.

## Elementary statements that can be proved

Suppose \(\zeta(s_0)=a_0\), \(s_0\ne1\), and \(\zeta'(s_0)\ne0\). The analytic inverse function theorem supplies a unique local analytic branch \(s(a)\) through \((a_0,s_0)\). Differentiating its defining identity gives

\[
\zeta'(s(a))s'(a)=1,
\qquad
\boxed{s'(a)=\frac1{\zeta'(s(a))}.}
\]

This is a local theorem under the nonzero-derivative hypothesis. It is not a guarantee that one numerical trajectory will reach \(a=1\) or stay inside the viewing rectangle. Its second derivative, wherever defined, is

\[
s''(a)=-\frac{\zeta''(s(a))}{[\zeta'(s(a))]^3},
\]

which explains why a small derivative or changing curvature can demand smaller numerical steps.

Along an exact branch with real \(a\),

\[
\operatorname{Im}\zeta(s(a))=0,\qquad
\operatorname{Re}\zeta(s(a))=a.
\]

Thus this experiment traces a labeled part of an existing real-value contour. A critical encounter means **both** \(\zeta'(s_c)=0\) and \(\zeta(s_c)=a_c\in[0,1]\) on the tracked branch. A nearby derivative zero, or a small sampled derivative, does not establish such an encounter.

There is also a useful bounded continuation lemma. Suppose an exact branch exists for \(a_0\le a<a_*\), remains in a compact set \(K\subset\mathbb C\setminus\{1\}\), and satisfies \(|\zeta'(s(a))|\ge\delta>0\) throughout. Then \(|s'(a)|\le1/\delta\), so \(s(a)\) is Lipschitz and has a limit \(s_*\in K\) as \(a\uparrow a_*\). Continuity gives \(\zeta(s_*)=a_*\) and \(|\zeta'(s_*)|\ge\delta\). The inverse function theorem extends the branch through \(a_*\). This proves continuation under **uniform, exact** compactness and derivative bounds; checking a finite list of samples does not prove those hypotheses.

At \(a=0\), the solutions are zeta zeros. At \(a=1\), they are zeta 1-points. A 1-point off the critical line is not a counterexample to RH, because zeta equals one there rather than zero. The theory of nonzero a-points is established mathematical territory; see [Lester, *a-Points of the Riemann zeta-function on the critical line*](https://arxiv.org/abs/1402.0169). No novelty is claimed for this family or its inverse-derivative equation.

## A falsifiable finite conjecture

Fix the three seeds and rectangle above before inspecting the outcome. The candidate statement is:

> Each of the three local branches extends through every real target \(0\le a\le1\), remains inside \(R\), has nonzero zeta derivative throughout, and ends at a distinct finite 1-point inside \(R\).

This is deliberately much narrower than RH. A certified boundary crossing on a tracked branch would refute the in-rectangle clause. A certified critical encounter would refute the derivative clause. Distinctness of endpoints follows from uniqueness if the branches remain regular throughout, but retaining their identities is a useful numerical check.

An integration failure is not itself a mathematical counterexample. A numerical exit or low-derivative warning is evidence to investigate, not a formal enclosure. A rigorous version would need, for example, validated continuation tubes and interval bounds excluding \(\zeta'=0\), with certified boundary/endpoint statements.

**Checked finite numerical outcome (2026-11-15):** the independent 80-digit reference suite passed its model controls, coarse/fine comparisons, and reverse tracking. Z1 first exits the right boundary of the original rectangle near \(a=0.85444799296999594658\), at height \(13.83867652419268336\); Z2 exits near \(a=0.91722451938931672698\), at height \(22.20906410469926171\). Z3 reaches target one at approximately

\[
s_3(1)=1.40778804065288669385+23.32798775455910449504i.
\]

These are numerical observations, not interval-certified statements. The largest sampled base residual is below \(9.87\times10^{-61}\); numerical exit brackets have parameter width below \(6.75\times10^{-25}\). The minimum sampled derivative magnitudes are about 0.10806, 0.04593, and 0.10041. Positive sampled minima do not exclude an undetected critical point between samples, and first-detected exits do not certify absence of an earlier unseen excursion.

The observations give numerical counterevidence to the original requirement that all three paths remain inside the rectangle throughout \(0\le a\le1\). A later re-entry, or a finite endpoint inside the window, would not undo an earlier violation of that all-targets confinement condition. Conversely, an exit does not prove disappearance, a critical encounter, or eventual behavior outside the box. Keep the original rectangle visible.

The independent native implementation cross-check also passed. Source artifacts are `evidence/reference-trajectories.json`, `evidence/numerical-report.json`, and `evidence/native-validation.json`. The scientific animation was accepted separately in `evidence/animation-acceptance.json`; this authorizes presentation production, not a claim of certified continuation or an RH proof.

## Numerical and visual meanings

Use derivative prediction followed by Newton correction, shrinking the parameter step when needed and never silently reseeding a failed branch. Preserve separate branch identities from the three starting zeros. Independent high-precision evaluation, smaller-step comparisons, and reverse tracking test consistency; they do not automatically furnish a proof.

The native animation's declared controls are a predicted motion cap of 0.06, accepted motion cap of 0.09, and predictor-correction cap of 0.001 in the input plane, with explicit low-derivative/failure states. These are implementation tolerances, not universal error bounds. The reference audit must check the actual emitted values and limits rather than infer accuracy from these settings.

The phase background is \(\zeta(s)-a\). Original zero circles remain labeled as starting points. Solid paths mean already traversed numerical samples; dashed paths mean precomputed later numerical samples, not analytic predictions or certified future motion. A branch that exits the box is held at its last in-view boundary marker with its exit target shown. For later targets that held marker is **not** a current solution of \(\zeta(s)=a\). Its position must not be used to imply that the mathematical branch ended or encountered a singularity.

## Contribution and the missing global argument

This experiment can test a specific path-connectivity conjecture, reveal when finite framing hides continued motion, and distinguish smooth level continuation from the previous selector's artificial jump. The potential contribution is a reproducible, checked exploratory workflow or a subsequently certified bounded statement. Neither originality nor a new theorem is established merely by making the animation.

RH concerns all nontrivial zeros at \(a=0\), requiring their input real part to be \(1/2\). [NIST DLMF 25.10(i)](https://dlmf.nist.gov/25.10.i) Starting with three known zeros on that line does not examine every other zero. Moving the target away from zero changes the level equation, and imposes no condition excluding a hypothetical off-line zero at target zero. Any such zero would itself supply a local branch whenever it was simple.

Combining phase colors, continuation, high-precision numerics, and analytic estimates is useful only when each contributes a stated check. To turn this experiment into a proof of RH, one would need an additional **global constraint** that excludes all off-critical-line nontrivial zeros, together with a proof of that constraint. This finite animation provides neither that constraint nor a partial RH proof.
