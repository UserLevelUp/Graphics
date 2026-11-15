# Finite prime proof and phase-color zero counting

This example proves the complete classification of the integers 0 through 100: **25 primes, 74 composites, and 0 and 1 neither**. It also explains an exact zero-counting example, `f(z) = z` on the unit circle. Both use established mathematics. Neither is a finite verification or a proof of the Riemann Hypothesis.

Read [proof.md](proof.md) for the complete argument and its limits. The certificate and checker use exact integer arithmetic and Python's standard library. From this directory:

```text
python prime_certificate.py verify certificate.json
python check_certificate.py
```

The second command independently tests every proper divisor, checks adversarial certificate mutations, and writes `evidence/validation.json`. Run in a copy if preserving an archived package byte for byte. These are replayable checks, not a proof-assistant formalization.

A future color rule can supply `candidate.json` with a `predictions` array of 101 ordered records, each containing `n` and boolean `isPrime`. Evaluate it with:

```text
python prime_certificate.py evaluate certificate.json --predictions candidate.json
```

The violet labels in this presentation display the certified answers. No independent brush predictor is implemented. A useful future experiment would freeze the rule before testing, exclude divisor or primality answers from its inputs, and evaluate on a previously unseen range.

## What the color boundaries contribute

For a phase map, assign the four colors to the four sectors of the current complex function value. Boundaries and their junctions can guide refinement around candidate zeros. Keep these colors separate from accumulated brush paint, whose final color depends on draw order.

The diagram demonstrates `f(z) = z`: the function is nonzero everywhere on the unit circle, has no poles, and its continuous phase gains one full turn. The argument principle therefore counts exactly one zero inside. Colors illustrate the analytic argument; a finite set of colored pixels does not establish the winding number.

For zeta, future work must certify nonvanishing on complete contour segments, count poles, and determine a rigorous winding number. Subdividing certified contours could localize zeros. An RH verification also requires complete zero counts and critical-line membership; a global proof must cover all heights. This example performs none of those zeta certifications.

Sources: [DLMF 1.10.9](https://dlmf.nist.gov/1.10.E9) and [Wegert, Phase Plots of Complex Functions](https://arxiv.org/abs/1007.2295).

## Presentation and review

The revised full presentation runs **5:20**, at 1920 × 1080 and 24 fps:

| Interval | Content |
| --- | --- |
| 0:00–4:12 | Previous accepted presentation content |
| 4:12–4:40 | Exact classification of integers 0 through 100 |
| 4:40–5:08 | Phase map and exact model zero count |
| 5:08–5:20 | Public project, branch, source checkpoint and `git remote -v` |

`proof-demonstration.mp4` contains just the two new scenes (56 seconds). The editable project is `presentation-with-finite-proof.aep`; keep its `assets` folder together and relink that folder if After Effects requests it after moving the package. Text uses Segoe UI and Cambria Math. The source project was created in After Effects 2027 (27.0).

The two new narration clips were synthesized from the reviewed script using Runway's Serene voice / Eleven Multilingual v2. Native scene rendering and final assembly preserve the previous presentation's audio, with its last source card shifted to the new end.

Evidence includes an independent certificate review, content review, 150 technical media checks and a separate review of seven decoded stills. Technical checks cover complete video/audio decoding, all 101 tile colors, sampled contour positions, and preservation of prior audio and sampled visuals. The still review covers labels, equations and layout. Neither independent speech transcription nor an every-frame visual review is claimed.

## Reproduction and provenance

The lightweight proof package runs independently with Python. The editable media package includes the native project, assets, captions, transcript, certificate and review records. Its `revision-source/research/prime-range-100` folder preserves the production scripts; the prior verifier helper is included alongside it. Rebuilding from scripts also requires the prior accepted baseline video/project named by `presentation.json`, the project repository, After Effects, NumPy, Pillow and imageio-ffmpeg. Those production dependencies are separate from the standard-library integer certificate.

Public repository: [UserLevelUp/Graphics](https://github.com/UserLevelUp/Graphics). Branch: `graph/riemann-continuation`. The final card displays source checkpoint `a9b86965aef1`; later acceptance and packaging records do not change that rendered checkpoint.

Trace base: `graph.primes.range100`. The Warp has certificate, presentation and acceptance slices. See `trace-map.json` for the evidence route, and `delivery-manifest.json` in the full delivery for byte-integrity hashes. Its later acceptance and delivery-receipt records are explicitly outside the seal.
