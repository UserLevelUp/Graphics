# What worked, what failed, and what remains open

defines: graph.riemann.lessons.documentation
consumer: graph.riemann.lessons

This narrated, animated chapter explains the tested prime and zeta ideas for a public audience. It is inserted at **5:08** in a separately named revision of the full presentation, before the final public-project card. The historical 5:20 export remains unchanged.

The chapter separates counterexamples to a specific rule, correct classical mathematics, finite implementation checks, and work that remains open. Neither a new efficient primality algorithm nor progress toward proving RH is established.

## Findings explained in the chapter

| Proposal | What the calculation establishes |
|---|---|
| Overwriting four-color brush trails | A useful display of geometry and draw order; a surviving color alone is not an arithmetic certificate. |
| Negative slope at the critical line | Among the first 100 zero indices, both signs occur in both prime and composite cohorts. These are zero indices, not individual prime values. |
| Half-unit denominator substitution | `g(n) = 2(n/2 - 1/2) + 2(1/2) = n`. Replacing `n` with `g(n)` in the zeta series leaves every term unchanged. |
| Put `1/2` into zeta | Zeta has a nonzero value at this real point. The critical line is the family `1/2 + it`; particular heights, not every point or every prime height, give zeros. |
| Compare zeta at `s`, `s+1`, `s-1` | The tested rule matching 97's three quadrants retains six primes and eighteen composites, missing nineteen primes in 2–100. |
| Switch the unit term | Removing 1 changes the target to zeta equal to 1. Multiplying the original and shifted functions retains any original zeros, including hypothetical off-line zeros. |
| Subtract a reversed prime expression | Reordering a finite sum does not change its sum. The explicitly tested polynomial reversal difference is antisymmetric, not a nonnegative composite indicator. Other backward recurrences require their own definition and analysis. |
| Subtract infinite prime and integer sums at `s=-1` | Finite term removal is valid but uses known prime information. The ordinary infinite sums diverge; analytic continuation is not ordinary summation. |
| Cancel prime terms in a zeta-based series | The reviewed `H(s)=A(s)-1-log A(s)` identity does remove odd-prime coefficients for real `s>1`, leaving weighted odd composites. Evaluating `H(97)` does not extract its coefficient at index 97. |
| Exact phase/quadrant classifier | Wilson arithmetic supplies an exact candidate-input test; the quadrant encodes its result. It requires no list of previous primes, but still performs computation. |
| Count nontrivial factor pairs | The classical coefficient criterion is proved for odd integers greater than 1. The implementation was independently checked on 0–100000. |
| Use colors for future zero searches | Phase plots can guide a search. Rigorous contour bounds and a complete zero count remain necessary for certification; finite checks do not prove global RH. |

## The latest series-substitution question

For positive integer `n`, the half-unit expression `g(n)` equals `n` exactly. Therefore

```
sum(n>=1) 1/g(n)^s = sum(n>=1) 1/n^s = zeta(s),  Re(s)>1.
```

Every finite partial sum also agrees at other complex arguments. At `Re(s)=1/2`, this finite equality does **not** assert that the ordinary infinite series converges to the continued zeta function. The half inside `g` is not a choice of exponent `s`.

Changing coefficients is a different operation. For example, a factor-pair count multiplying `n^(-s)` can make prime-indexed terms disappear. Putting that count in the **denominator** instead would divide by zero at primes; that would not define a valid prime test. A new series must specify its summation index, coefficient, exponent, domain, and proposed decision rule separately.

## Files and reproduction

- `script.json`: twelve scenes, visible statements, complete narration, source references and evidence pointers.
- `math-notes.md`: domain restrictions, derivations and primary sources.
- `verify_explanation.py`: independent exact arithmetic, saved-row aggregation and high-precision numerical checks.
- `render_chapter.py`: deterministic 1280×720, 24 fps Compass animation, audio placement and sidecar captions.
- `assemble.py`: preserves the previous export, inserts the chapter after 308 seconds, refreshes the final 12-second repository card and retimes/embeds captions.
- `verify_media.py`: encoded-media and integration checks.
- `evidence/`: review receipts, source fingerprints and acceptance.

Rendering uses Python with Pillow and imageio-ffmpeg and the Windows Segoe UI fonts. Mathematical verification uses mpmath. The successful math runtime is recorded separately in the evidence. Narration uses the same Serene voice preset as the earlier presentation; the voice files and task receipts permit review without treating a provider response as mathematical evidence.

The chapter's native resolution is 1280×720. The full presentation retains 1920×1080, with only the new chapter upscaled. It is a separately encoded export, not a byte-level concatenation of the original. Captions inside each new narration clip use estimated sentence timing, not word-level forced alignment. Schematics illustrate the reviewed results; they are not new zeta measurements.

To replay the chapter from delivered voice files, use the packaged voice manifest and a new output directory, preserving the accepted evidence:

```powershell
python research/riemann-lessons/render_chapter.py --voices PATH/voice-manifest.json --output work/lessons-replay --work work/lessons-replay-work
python research/riemann-lessons/assemble.py --base PATH/presentation-with-finite-proof.mp4 --chapter work/lessons-replay/chapter.mp4 --chapter-captions work/lessons-replay/captions.srt --output work/lessons-full-replay
```

The base directory must also contain its historical `captions.srt`. Assembly verifies the base SHA256 and reads the current branch and remote with Git. The closing checkpoint is the source state observed before export; the final media commit necessarily comes afterward.

Trace/Warp: `graph.riemann.lessons`. Public repository: [UserLevelUp/Graphics](https://github.com/UserLevelUp/Graphics), branch `graph/riemann-continuation`.
