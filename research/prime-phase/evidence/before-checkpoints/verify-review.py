import pathlib
import sys

provider = sys.argv[1]
path = pathlib.Path(__file__).resolve().parent / provider / "review.md"
text = path.read_text(encoding="utf-8")
assert len(text) > 300, "Review too short to inspect"
assert f"publish: graph.primes.phase.{provider}.response" in text
for heading in ["VERDICT", "REASONING", "TESTS"]:
    assert heading in text.upper(), f"Missing {heading} section"
assert "ACCEPT" in text.upper() or "REVISE" in text.upper()
print("Review artifact and sections verified. Mathematical acceptance requires coordinator review.")
