"""Independent checks and reviewed-scope record for the concluding video script.

defines: graph.riemann.lessons.explanation_review
This reviewer does not import any candidate classifier or renderer.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
RESEARCH = BASE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def prime(n):
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def kind(n):
    return "neither" if n < 2 else "prime" if prime(n) else "composite"


def quadrant(real, imaginary):
    # Reviewed rows for positive integer heights never lie exactly on an axis.
    assert real != 0 and imaginary != 0
    return 1 if real > 0 and imaginary > 0 else 2 if real < 0 < imaginary else 3 if real < 0 and imaginary < 0 else 4


def run(args):
    sys.path.insert(0, str(args.mpmath_dir))
    import mpmath as mp
    mp.mp.dps = 60
    script_path = BASE / "script.json"
    script = read(script_path)
    sources = [
        script_path, Path(__file__), BASE / "math-notes.md",
        RESEARCH / "zeta-zero-index/evidence/zero-index.json",
        RESEARCH / "zeta-zero-index/proof-notes.md",
        RESEARCH / "zeta-prime-check96/evidence/comparison.json",
        RESEARCH / "zeta-prime-check96/README.md",
        RESEARCH / "composite-remainder/evidence/table-0-100.json",
        RESEARCH / "composite-remainder/evidence/independent-review.json",
        RESEARCH / "composite-remainder/proof.md",
        RESEARCH / "prime-divisor-phases/proof-and-findings.md",
        RESEARCH / "prime-function/proof.md",
        RESEARCH / "prime-quadrant-phase/proof.md",
    ]

    zero_rows = read(RESEARCH / "zeta-zero-index/evidence/zero-index.json")["rows"]
    assert [r["zeroIndex"] for r in zero_rows] == list(range(1, 101))
    slope_counts = {k: {"negative": 0, "positive": 0} for k in ("prime", "composite", "neither")}
    max_ratio_error = mp.mpf(0)
    for row in zero_rows:
        j = row["zeroIndex"]
        assert row["classificationPrimeIndex"] == kind(j)
        derivative = row["startDerivative"]
        slope = -mp.mpf(derivative["imag"]) / mp.mpf(derivative["real"])
        assert abs(slope - mp.mpf(row["slope"])) < mp.mpf("1e-40")
        max_ratio_error = max(max_ratio_error, abs(slope - mp.mpf(row["slope"])))
        slope_counts[kind(j)]["negative" if slope < 0 else "positive"] += 1
    assert slope_counts == {"prime": {"negative": 14, "positive": 11}, "composite": {"negative": 35, "positive": 39}, "neither": {"negative": 1, "positive": 0}}

    phase_rows = read(RESEARCH / "zeta-prime-check96/evidence/comparison.json")["rows"]
    assert [r["n"] for r in phase_rows] == list(range(101))
    phases = {}
    for row in phase_rows:
        n = row["n"]
        assert row["classification"] == kind(n)
        if n < 2:
            continue
        quads = tuple(quadrant(mp.mpf(value["real"]), mp.mpf(value["imaginary"])) for value in (row, row["shifted"], row["minus"]))
        assert quads == (row["quadrant"], row["shifted"]["quadrant"], row["minus"]["quadrant"])
        phases[n] = quads
    phase_counts = []
    for indices in ((0,), (0, 1), (0, 2), (0, 1, 2)):
        selected = [n for n, qs in phases.items() if all(qs[i] == phases[97][i] for i in indices)]
        counts = Counter(kind(n) for n in selected)
        phase_counts.append({"channels": list(indices), "primesKept": counts["prime"], "compositesKept": counts["composite"], "primesMissed": 25 - counts["prime"], "selected": selected})
    assert [(r["primesKept"], r["compositesKept"], r["primesMissed"]) for r in phase_counts] == [(10, 33, 15), (7, 28, 18), (7, 22, 18), (6, 18, 19)]

    zhalf = mp.zeta(mp.mpf("0.5"))
    first_zero = mp.zetazero(1)
    third_zero = mp.zetazero(3)
    numeric = {}
    for n in (95, 96, 97, 98, 99):
        outputs = []
        for sigma, channel in ((mp.mpf("0.5"), 0), (mp.mpf("1.5"), 1), (mp.mpf("-0.5"), 2)):
            z = mp.zeta(mp.mpc(sigma, n))
            q = quadrant(z.real, z.imag)
            assert q == phases[n][channel]
            outputs.append({"sigma": str(sigma), "real": str(z.real), "imaginary": str(z.imag), "quadrant": q})
        numeric[str(n)] = outputs
    assert abs(zhalf + mp.mpf("1.460354509")) < mp.mpf("1e-9")
    assert abs(first_zero.imag - mp.mpf("14.134725")) < mp.mpf("1e-6")
    assert abs(third_zero.imag - mp.mpf("25.01085758")) < mp.mpf("1e-8")
    assert abs(mp.zeta(first_zero)) < mp.mpf("1e-50")
    assert phases[97][0] == phases[99][0] == 1
    assert abs(mp.zeta(mp.mpc("0.5", 97))) > 2

    # Direct pair enumeration: independently construct the finite coefficient list.
    pairs = {n: [] for n in range(101)}
    for a in range(3, 101, 2):
        for b in range(a, 101, 2):
            if a * b <= 100:
                pairs[a * b].append([a, b])
    coefficient_rows = read(RESEARCH / "composite-remainder/evidence/table-0-100.json")["rows"]
    for row in coefficient_rows:
        n = row["n"]
        assert row["classification"] == kind(n)
        assert row["factorPairs"] == pairs[n]
        assert row["unorderedCoefficient"] == len(pairs[n])
        if n > 1 and n % 2:
            assert (len(pairs[n]) == 0) == prime(n)
    assert sum(bool(p) for p in pairs.values()) == 25
    assert sum(len(p) for p in pairs.values()) == 30
    assert pairs[97] == [] and pairs[99] == [[3, 33], [9, 11]]
    assert sum(prime(n) for n in range(101)) == 25
    assert sum(kind(n) == "composite" for n in range(101)) == 74

    # Wilson point encoding, checked without importing the project's implementation.
    wilson_examples = {}
    for n in range(2, 101):
        remainder = (math.factorial(n - 1) + 1) % n
        point = ((1, 1), (-1, 1), (-1, -1), (1, -1))[remainder % 4]
        assert (point[0] > 0 and point[1] > 0) == prime(n)
        assert remainder == (0 if prime(n) else 3 if n == 4 else 1)
        if n in (4, 96, 97):
            wilson_examples[str(n)] = {"remainder": remainder, "point": point}

    finite_divisor_pass = lambda n: n >= 2 and (n in (2, 3, 5, 7) or all(n % d for d in (2, 3, 5, 7)))
    assert all(finite_divisor_pass(n) == prime(n) for n in range(101))
    assert finite_divisor_pass(121) and not prime(121)
    for n in range(-100, 101):
        assert 2 * (Fraction(n, 2) - Fraction(1, 2)) + 2 * Fraction(1, 2) == n
    assert Fraction(97, 2) % 1 == Fraction(99, 2) % 1 == Fraction(1, 2)
    # Substituting g(n) in a denominator is literally the same integer base.
    substitutions = []
    for s in (mp.mpf(2), mp.mpc("0.5", "14.134725")):
        ordinary = mp.fsum(mp.power(n, -s) for n in range(1, 101))
        replaced = mp.fsum(mp.power(mp.mpf(2) * (mp.mpf(n) / 2 - mp.mpf("0.5")) + 2 * mp.mpf("0.5"), -s) for n in range(1, 101))
        assert ordinary == replaced
        substitutions.append({"sReal": str(s.real), "sImaginary": str(s.imag), "terms": 100, "absoluteDifference": str(abs(ordinary - replaced)), "finiteSumReal": str(ordinary.real), "finiteSumImaginary": str(ordinary.imag)})
    archived_review = read(RESEARCH / "composite-remainder/evidence/independent-review.json")
    assert archived_review["status"] == "passed"
    assert archived_review["coverage"]["range"] == [0, 100000]
    assert archived_review["coverage"]["scalarClassifications"] == 100001

    prime_coeffs = [int(prime(n)) for n in range(11)]
    reversal_difference = [prime_coeffs[n] - prime_coeffs[10 - n] for n in range(11)]
    assert {n: v for n, v in enumerate(reversal_difference) if v} == {2: 1, 8: -1}
    assert sum(range(1, 11)) - sum(n for n in range(1, 11) if prime(n)) == 38
    assert mp.zeta(-1) == -mp.mpf(1) / 12

    # Direct rational expansion of log(1+B), B=sum odd n>=3 n^-s, to n=100.
    # Dirichlet convolution counts ordered products, not ordinary polynomial powers.
    B = [Fraction(int(n >= 3 and n % 2)) for n in range(101)]
    power = B[:]
    log_coeffs = [Fraction(0) for _ in B]
    for k in range(1, 5):  # 3^5 > 100: no later power contributes at these indices.
        for n in range(101):
            log_coeffs[n] += Fraction((-1) ** (k + 1), k) * power[n]
        product = [Fraction(0) for _ in B]
        for a in range(3, 101, 2):
            for b in range(3, 101 // a + 1, 2):
                product[a * b] += power[a] * B[b]
        power = product
    H = [B[n] - log_coeffs[n] for n in range(101)]
    assert H[9] == Fraction(1, 2) and H[27] == Fraction(2, 3)
    assert H[97] == 0 and H[99] == 1
    assert all((H[n] > 0) == (n % 2 and kind(n) == "composite") for n in range(101))
    with mp.workdps(160):
        A97 = (1 - mp.power(2, -97)) * mp.zeta(97)
        H97 = A97 - 1 - mp.log(A97)
        assert H97 > 0
        H97_text = str(H97)

    # The exact script fingerprint below is reviewed by the independent agent.
    # The expected value is supplied explicitly after editorial mathematical review.
    actual_script_hash = sha(script_path)
    if args.reviewed_script_sha256 != actual_script_hash:
        raise ValueError("Script differs from the independently reviewed revision.")
    scenes = script["scenes"]
    assert len(scenes) >= 10
    assert len({s["id"] for s in scenes}) == len(scenes)
    scene_records = []
    for scene in scenes:
        assert scene["narration"] and scene["title"] and scene["status"]
        assert 2 <= len(scene["screenLines"]) <= 4
        assert scene["durationSeconds"] > 0
        evidence = []
        for path in scene["evidencePaths"]:
            candidate = Path(path)
            if not candidate.is_absolute():
                candidate = RESEARCH.parent / path
            assert candidate.is_file(), candidate
            evidence.append({"path": str(candidate), "sha256": sha(candidate)})
            if candidate not in sources:
                sources.append(candidate)
        scene_records.append({"id": scene["id"], "title": scene["title"], "status": scene["status"], "narrationWords": len(scene["narration"].split()), "durationSeconds": scene["durationSeconds"], "evidence": evidence})
    report = {
        "schema": "graph-riemann-lessons-explanation-review-v1",
        "traceId": "graph.riemann.lessons.explanation_review",
        "status": "passed",
        "reviewedAtUtc": datetime.now(timezone.utc).isoformat(),
        "reviewedScriptSha256": actual_script_hash,
        "reviewer": "Independent Codex subagent /root/lessons_review; no candidate classifier imports",
        "runtime": {"python": sys.version, "executable": sys.executable, "mpmath": mp.__version__, "decimalDigits": mp.mp.dps},
        "scope": "Independent arithmetic checks, saved-row aggregation, high-precision numerical examples, and editorial mathematical review of this exact script revision.",
        "checks": {
            "slopeCountsRecomputedFrom100Rows": slope_counts,
            "largestStoredDerivativeRatioError": str(max_ratio_error),
            "shiftedColorCountsFrom99Rows": phase_counts,
            "zetaHalf": str(zhalf), "firstZero": {"real": str(first_zero.real), "imaginary": str(first_zero.imag)},
            "thirdZero": {"real": str(third_zero.real), "imaginary": str(third_zero.imag)},
            "independentlyReevaluatedZetaExamples": numeric,
            "finite0to100": {"primes": 25, "composites": 74, "neither": [0, 1], "oddCompositeCoefficients": 25, "unorderedPairs": 30},
            "wilsonExamples": wilson_examples,
            "finiteFilterOutsideDomainControl": {"n": 121, "classification": "composite", "fixedFourDivisorFilter": "passes"},
            "halfIdentity": "Exact rational checks on -100..100 supplement the elementary identity n-1+1=n.",
            "denominatorSubstitutionFiniteSums": substitutions,
            "denominatorSubstitutionConclusion": "Termwise equality extends to the ordinary infinite zeta series for Re(s)>1. The critical-line entry above is only a 100-term finite sum; it is not an evaluation of analytically continued zeta.",
            "reversalN10NonzeroCoefficients": {"2": 1, "8": -1},
            "weightedCompositeCoefficients": {"9": "1/2", "27": "2/3", "97": "0", "99": "1"},
            "H97At160Digits": H97_text,
            "archivedLargerImplementationReview": {"range": [0, 100000], "scalarClassifications": 100001, "reevaluatedInThisReview": False},
        },
        "editorialReview": [
            "The claim being rejected is stated with its input mapping and finite scope, not as a universal impossibility theorem.",
            "Prime values, zero indices, noninteger zero heights, coefficients and function arguments are kept distinct.",
            "Exact Wilson/quadrant and divisor constructions are described as established arithmetic, with computational work retained.",
            "The denominator substitution g(n)=n leaves each Dirichlet-series term unchanged; its internal half does not set the exponent s to one half.",
            "The finite reversal obstruction applies to the defined polynomial reversal, not every conceivable reverse recurrence.",
            "Unit-factor inclusion and exclusion is explicit; 1 is not reclassified as prime.",
            "At s=-1 the ordinary integer series diverges; analytic continuation cannot be treated as ordinary subtraction of infinite sums.",
            "At real s>1 H(s) uses an unambiguous real logarithm; coefficient cancellation does not mean H(97)=0.",
            "No mathematical novelty, constant-time classifier, new zero certification or RH progress is claimed.",
        ],
        "scenes": scene_records,
        "limits": [
            "The semantic review is a documented human-readable mathematical assessment by an independent model, not machine-checked theorem proving.",
            "Saved-row count checks recompute the aggregation but do not reevaluate every historical trajectory.",
            "Numerical examples use mpmath at higher precision, not a separate library or interval enclosures.",
            "Finite tests verify the cited examples; all-domain assertions depend on the accompanying elementary arguments and established theorems.",
            "Video, narration pronunciation, captions and layout require separate media review."
        ],
        "inputs": [{"path": str(path.resolve()), "sha256": sha(path)} for path in sources],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "scriptSha256": actual_script_hash, "sceneCount": len(scenes), "report": str(args.output)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mpmath-dir", type=Path, default=Path("C:/Users/marcn/Documents/Codex/2026-11-14/eu/work/zeta-prime-deps"))
    parser.add_argument("--reviewed-script-sha256", required=True)
    parser.add_argument("--output", type=Path, default=BASE / "evidence/explanation-review.json")
    run(parser.parse_args())
