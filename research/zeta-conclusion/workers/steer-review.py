"""Record one coordinator decision for an exact worker run and checkpoint."""
import argparse
import importlib.util
import os
from pathlib import Path
import uuid

spec = importlib.util.spec_from_file_location("review_runner", Path(__file__).with_name("run-review.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

parser = argparse.ArgumentParser()
parser.add_argument("provider", choices=["codex"])
parser.add_argument("run_id")
parser.add_argument("after_turn", type=int)
parser.add_argument("action", choices=["continue", "steer", "stop"])
parser.add_argument("instruction_file", type=Path)
args = parser.parse_args()
if Path(args.run_id).name != args.run_id or "/" in args.run_id or "\\" in args.run_id or args.run_id in (".", ".."):
    parser.error("Run ID must be a single directory name")
run_dir = Path(__file__).resolve().parent / args.provider / "runs" / args.run_id
import json
status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
if status["state"] != "awaiting_coordinator" or status["turn"] != args.after_turn:
    parser.error("Worker is not awaiting this checkpoint")
path = run_dir / f"steering-after-{args.after_turn:02}.json"
if path.exists():
    parser.error("This checkpoint already has a coordinator decision")
decision = dict(run_id=args.run_id, after_turn=args.after_turn, action=args.action,
                token=uuid.uuid4().hex, instruction=args.instruction_file.read_text(encoding="utf-8-sig"),
                state="queued", queued_at=runner.utc_now())
temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
try:
    temporary.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    os.link(temporary, path)  # Publish complete JSON exactly once, even with competing coordinators.
finally:
    temporary.unlink(missing_ok=True)
print(json.dumps(decision, indent=2))
