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
assert f"publish: graph.riemann.switch.{provider}.response" in text
assert runner.validate_reply(text, ack["token"]) == "COMPLETE"
assert any(e["state"] == "awaiting_coordinator" for e in events), "No coordinator handoff observed"
assert ack["token"] != "initial", "Continuation was not acknowledged"
print("Clock-formatted response, checkpoint, coordinator handoff, acknowledgment and final artifact verified.")
print("Clock values are worker observations; mathematical acceptance requires coordinator review.")
