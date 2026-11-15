# A correct candidate-input primality function

The function is now implemented in Python and the native Graphics application. For a nonnegative integer n, it returns **1 exactly for primes and 0 otherwise**, with 0 and 1 explicitly classified as neither prime nor composite. Its input is the candidate integer; no list of earlier primes or earlier primality answers is supplied.

The equation is established mathematics, based on Wilson's theorem:

R(n) = ((n−1)! + 1) mod n,

f(n) = floor(1 / (1 + R(n))), for n ≥ 2; define f(0)=f(1)=0.

Read [proof.md](proof.md) for the complete two-direction proof, the optional complex extension and the distinction between an exact criterion and a fast algorithm. [Mathlib's Wilson development](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Wilson.html) already contains a formal theorem and converse; we did not replay Lean or formally verify this code with it.

## The requested examples

| Input | (n−1)! mod n | R(n) | f(n) | Result |
|---|---:|---:|---:|---|
| 96 | 0 | 1 | 0 | Composite |
| 97 | 96 | 0 | 1 | Prime |
| 4 | 2 | 3 | 0 | Composite exception for R |

Every composite greater than 4 has R(n)=1. All prime inputs have R(n)=0. Thus the common composite output exists exactly for this arithmetic construction; it is not a resemblance inferred from a picture.

The program multiplies modulo n throughout and can stop when the accumulator reaches zero. For 96 it reaches zero at 8!, after seven nontrivial multiplications. For 97 it performs 95 modular multiplications and obtains 96 modulo 97. Neither result uses previous prime answers.

## Run the function

The Python implementation and its arithmetic validation use only the standard library. From this directory:

```text
python prime_function.py 96 97 --method both
python verify_function.py --output evidence
```

In Python, `f(n, method='wilson')` evaluates the exact Wilson equation; `f(n)` defaults to an equivalent trial-division implementation. Python integers have arbitrary precision, but computation time still grows with the input. The code never decides primality from a floating-point factorial, phase, or tolerance.

The native application accepts a nonnegative Int32 candidate. From the repository root in PowerShell:

```powershell
dotnet build Graphics/Graphics.csproj -c Release
$env:DOTNET_ROLL_FORWARD='Major'
$p = Start-Process -FilePath ./Graphics/bin/Release/net5.0-windows/Graphics.exe -ArgumentList @('--primality-function','primality-function.png','97') -WindowStyle Hidden -Wait -PassThru
if ($p.ExitCode -ne 0) { throw 'Export failed' }
```

The candidate argument is optional and defaults to 97. The command writes a 1920×1080 PNG plus JSON and TXT reports. The project currently targets .NET 5 Windows; the local run used its existing major-version roll-forward convention with an installed Windows Desktop runtime. The native Wilson demonstration is capped at 100,000 to bound its work. Larger Int32 candidates still receive an exact trial-division answer and an explicit unavailable Wilson field.

The exported diagram always includes 96 and 97, the 0–100 classification grid, the selected candidate and a phase illustration. A candidate's exact value is computed before choosing a display color. The existing prime dropdown, which is prefiltered with a sieve, is not used as the input to this function.

## What the phase now means

The optional phasor W(n)=exp(2πiR(n)/n) displays the remainder. Its angles are 3.75° for 96 and 0° for 97. The exact condition is R(n)=0; both points can occupy the same phase quadrant. For large composites the angle approaches zero, so a rounded angle or colored pixel cannot replace the exact integer test. The violet prime marker explicitly displays the proved arithmetic answer.

An analytic expression H(s)=sin(π(Γ(s)+1)/s) has zeros at exactly the prime **integer inputs n≥2**. However it also vanishes at 1 and at some nonintegers. Its factorial-sized arguments make floating-point evaluation unsuitable as the primality decision. The proof note explains these limitations; H is not a new RH function or the native renderer's decision rule.

## Validation and cost

The Python trial implementation was checked against an independent sieve for every integer from 0 through 100,000: 9,592 primes. Wilson was checked against both that sieve and independent full big-integer factorials through 2,000. Additional controls include prime squares, 341, 561, 1105, 1729, 2047 and larger candidates, plus invalid input types.

The native executable runs its own sieve comparisons on the same stated ranges. Separate exports cover 0, 4, 96, 97, 100,001 and Int32 maximum. The independent native cross-check compares their JSON with Python exact arithmetic and samples all 101 grid colors. Native trial division checks every divisor; Python skips even divisors after 2, so their operation counts differ even though their answers agree. Visual inspection checks the rendered equations and labels separately.

Wilson's worst case requires O(n) modular multiplications; the simple trial baseline requires O(√n) divisor checks. These operation counts are exponential in the number of input bits. A bounded five-run Python timing comparison is recorded in `evidence/validation.json`; it favors trial division on those inputs and is not a general performance guarantee. More sophisticated candidate-input primality algorithms already exist, including [AKS](https://annals.math.princeton.edu/2004/160-2/p12); none is claimed as implemented here.

The all-n correctness statement comes from the theorem and the exact algorithms. Finite tests verify implementation behavior on their declared ranges. This work establishes a correct, inspectable baseline; it does not establish a new theorem, a fast direct nth-prime formula or a result about RH.

Trace/Warp: `graph.primes.function`. Public repository: [UserLevelUp/Graphics](https://github.com/UserLevelUp/Graphics), branch `graph/riemann-continuation`. Previous accepted research media and certificates are preserved.
