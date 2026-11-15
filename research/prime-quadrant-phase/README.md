# Exact primality through a color quadrant

Trace ID: `graph.primes.quadrant_phase`. This experiment adapts the previous exact prime function to a phase/quadrant decision. It preserves the earlier Wilson and zeta-phase experiments as historical comparisons.

For an integer n >= 2, compute

\[
R(n)=((n-1)!+1)\bmod n,\qquad F(n)=(1+i)i^{R(n)}.
\]

The classifier evaluates the exact coordinate signs of F(n). **Quadrant I means prime**; quadrants II and IV mean composite for this construction. No prior-prime list, sieve output, prime indicator or rendered pixel is an input to either candidate function. Both Python and native implementations calculate the modular factorial remainder and then classify the newly constructed point's quadrant.

| Candidates | R | F | Angle | Canonical color/quadrant |
|---|---:|---|---:|---|
| Primes | 0 | 1+i | 45 degrees | Violet / I |
| Composites > 4 | 1 | -1+i | 135 degrees | Amber / II |
| 4 | 3 | 1-i | 315 degrees | Pink / IV |
| 0 and 1 | Undefined | Undefined | Undefined | Neutral / no quadrant |

Quadrant III (cyan) is unused by valid final outputs. It is present because this remains a four-quadrant coordinate system. The [proof](proof.md) establishes why these cases exhaust all integer candidates. Applying the same phase map to an arbitrary remainder does not give a primality test.

## What changed

The earlier phase `exp(2*pi*i*R/n)` put 96 at 3.75 degrees and 97 at 0 degrees, close to the same boundary. The new phase puts them at 135 and 45 degrees. Every valid point is 45 degrees from the nearest canonical axis. Quarter turns are computed with exact integer coordinates (+/-1), so no sine, cosine, factorial-sized float, or angle threshold is needed to make the mathematical decision.

This is an encoding of Wilson's theorem into quadrants. It is a useful exact reference for the graphics experiment; it does not discover primes through the unmodified zeta phase or through brush overwriting. The Wilson modular product still supplies the arithmetic, with O(n) modular multiplications in the worst case. No speed advantage, novel theorem, fast direct nth-prime formula, or RH result is claimed.

## Run the Python test

Python uses only the standard library:

```powershell
python phase_test.py 4 96 97
python phase_test.py 96 97 --angle-error 44
python phase_test.py 96 97 --angle-error 45
python verify_phase.py --output evidence
```

The exact quadrant result remains available in the last two commands. The separate observation field reports whether an interval of the **supplied** angular uncertainty stays inside one quadrant. At 45 degrees of uncertainty around a quadrant center it reports `uncertain`; it does not fabricate a prime decision from a blurred observation. The helper assumes this bound is valid; it does not measure a renderer's actual error.

`phase_test(n)` accepts nonnegative exact Python integers, rejecting booleans, fractional values and negative inputs. Zero and one return `neither` and no phase. The Python implementation has no hard upper limit but becomes expensive for large candidates.

## Run the Graphics mode

From the full repository root, build and export:

```powershell
dotnet build Graphics/Graphics.csproj -c Release
$env:DOTNET_ROLL_FORWARD='Major'
$p = Start-Process -FilePath ./Graphics/bin/Release/net5.0-windows/Graphics.exe -ArgumentList @('--prime-quadrant-phase','prime-quadrant-phase.png','97','0') -WindowStyle Hidden -Wait -PassThru
if ($p.ExitCode -ne 0) { throw 'Export failed' }
```

The CLI accepts `--prime-quadrant-phase <png> [candidate] [displayRotationDegrees]`; it writes the image and a JSON record. The interactive view opens with `--prime-quadrant-lab` and allows candidate and display rotation changes. Native candidates are limited to 0..100000. There is no silent fallback to another primality method when this mode is out of range.

Display rotation moves the points and their reference axes together. The canonical quadrant and its color retain their identities; testing a rotated point against unrelated screen axes would be a different test. Line widths, antialiasing and brush overwriting are visual operations and never replace the exact quadrant record.

The project currently targets .NET 5. On the validation machine, a newer Windows Desktop runtime runs it using the explicit `DOTNET_ROLL_FORWARD=Major` setting shown above. This does not update the project's target framework.

## Verification and prior work

`verify_phase.py` compares the quadrant decision with an independent sieve for every input 0..10000 and compares the remainder with full integer factorials for 2..2000. Additional controls include prime squares, Carmichael numbers, 96, 97, 99991 and 100000. It checks all four generic quadrants, domain rejection and angular uncertainty crossing an axis. Finite implementation checks supplement the all-integer proof; neither establishes an RH claim.

Native exports and display rotation are checked separately, with source hashes recorded in `evidence/`. The Warp at `warps/graph.primes.quadrant_phase.warp-map.json` tracks the equation and native integration gates; a recorded completion follows review, rather than substituting for it.

The mathematical source is [Wilson's theorem and converse in mathlib](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Wilson.html). Its formal development was consulted, not locally replayed. This code and its quadrant adaptation have not been verified in Lean.
