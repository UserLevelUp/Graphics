# Zeta unit-term switch laboratory

defines: graph.riemann.switch.documentation
consumer: graph.riemann.switch.model
consumer: graph.riemann.switch.verify

This native lab compares zeta, zeta minus 1, their nearest-to-zero selector, and the analytic product zeta times (zeta minus 1). It implements an auxiliary switch for the additive n=1 term of the integer Dirichlet series. It does not add 1 to Euler's prime product or change the definition of prime numbers.

Build and open from C:/src/graph:

```powershell
dotnet build Graphics/Graphics.csproj -c Release --no-restore
$env:DOTNET_ROLL_FORWARD = 'Major'
dotnet Graphics/bin/Release/net5.0-windows/Graphics.dll --switch-lab
```

The main graph window also has a **Zeta switch lab** button. Controls change the height window within 10 through 30, resolution, palette rotation, and marker visibility. White circles mark numerical zeta zeros; gold diamonds mark numerical points where zeta equals 1. The dashed white input line sigma=1/2 differs from the cyan output seam Re(zeta)=1/2. Hover to inspect values. Save writes the displayed PNG, its `.values.json` samples and metadata, and a full `.txt` report.

CLI reproduction:

```powershell
dotnet Graphics/bin/Release/net5.0-windows/Graphics.dll --zeta-switch work/overview.png
dotnet Graphics/bin/Release/net5.0-windows/Graphics.dll --zeta-switch work/palette.png 10 30 256 73 False
dotnet Graphics/bin/Release/net5.0-windows/Graphics.dll --zeta-switch work/refinement.png 10 30 384 0 True
dotnet Graphics/bin/Release/net5.0-windows/Graphics.dll --zeta-switch work/one-point.png 23.1 23.6 256 0 True
dotnet Graphics/bin/Release/net5.0-windows/Graphics.dll --verify-switch work/model-checks.txt
```

Use an isolated Python environment with `requirements.txt` (mpmath 1.3.0), then:

```powershell
python -B research/zeta-switch/verify_exports.py work/overview.values.json work/palette.values.json work/refinement.values.json work/one-point.values.json --output work/validation.json
python -B research/zeta-switch/audit_reviews.py
python -B -m unittest discover -s research/zeta-switch -p 'test_review_*.py' -v
```

The shared parallel grid uses Euler–Maclaurin values, cached logarithms, and direct raster writes. This is CPU parallelism; no GPU acceleration is claimed. The selector receives only the complex zeta value. Reference samples and Newton marker searches are separate. Direct branch selection preserves tiny values instead of subtracting and re-adding 1.

The exact result is W(s)=0 if and only if zeta(s) is 0 or 1; G has the same zero union. W jumps at its seam while its magnitude remains continuous and nonzero there. The product supplies an analytic comparison away from the pole. Every hypothetical off-critical-line zeta zero survives both constructions. These are elementary identities, not new prime prediction or an RH proof. Read `math-audit.md` for the derivation and `evidence/review-resolution.md` for numerical limits.

The default plot finds three zeta-zero candidates and one 1-point candidate near 1.40778804065289+23.3279877545591i. The latter is off the critical line because it is a zero of zeta minus 1; it is not a counterexample to RH. Finite sample comparisons, marker searches and plotted seams are empirical, not rigorous enclosures or exhaustive counts.

Recur identity is `graph.riemann.switch`; the parent `graph.riemann` remains open. The fixed contract retains its original filename so Watch input fingerprints remain traceable. Provider records preserve their actual verdicts, including Copilot's request for quantitative thresholds. The coordinator resolves that request through the explicit checker thresholds and recorded tests; helper output alone never accepts a mathematical gate.
