import importlib.util
import json
from pathlib import Path
import sys

base = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("review_runner", base / "run-review.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
provider = sys.argv[1]
latest = json.loads((base / provider / "latest-run.json").read_text(encoding="utf-8"))
run = base / provider / "runs" / latest["run_id"]
status = json.loads((run / "status.json").read_text(encoding="utf-8"))
assert status["state"] == "complete", "Latest run is not complete"
events = [json.loads(line) for line in (run / "events.jsonl").read_text(encoding="utf-8").splitlines()]
ack = next(e for e in reversed(events) if e["state"] == "steering_acknowledged")
text = (run / "review.md").read_text(encoding="utf-8")
assert len(text) > 300, "Review too short to inspect"
assert (base / provider / "review.md").read_text(encoding="utf-8") == text
assert f"publish: graph.riemann.conclusion.review.{provider}.response" in text
assert runner.validate_reply(text, ack["token"]) == "COMPLETE"
if (run / "recovery.json").exists():
    recovery, checkpoint = runner.load_recovery(run / "recovery.json", base.parent)
    assert any(e["state"] == "checkpoint_recovered" for e in events), "No recovery event observed"
    assert ack["token"] == recovery["token"], "Recovery steering was not acknowledged"
    assert status["turn"] == 2, "Recovery exceeds the two-turn review budget"
    assert "CLOCK_SOURCE: coordinator" in text
else:
    assert any(e["state"] == "awaiting_coordinator" for e in events), "No coordinator handoff observed"
assert ack["token"] != "initial", "Continuation was not acknowledged"
print("Clock-formatted response, checkpoint, coordinator handoff, acknowledgment and final artifact verified.")
print("Recovery clocks are coordinator-supplied, not successful model clock observations. Mathematical acceptance requires coordinator review.")
