"""Bounded review turns with clock checks and explicit coordinator handoffs."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

TRACE = "graph.primes.phase"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def response_status(text):
    matches = re.findall(r"^STATUS:\s*(CHECKPOINT|COMPLETE)\s*$", text, re.M)
    if len(matches) != 1:
        raise ValueError("Expected one STATUS: CHECKPOINT or STATUS: COMPLETE line")
    return matches[0]


def validate_reply(text, token):
    status = response_status(text)
    acknowledgments = re.findall(r"^ACK:[ \t]*(\S+)[ \t]*$", text, re.M)
    if acknowledgments != [token]:
        raise ValueError("Worker did not acknowledge this turn's steering token")
    clocks = re.findall(r"^CLOCK:[ \t]*(\S+)[ \t]*$", text, re.M)
    if len(clocks) != 1:
        raise ValueError("Worker did not return its clock observation")
    observed = datetime.fromisoformat(clocks[0])
    if observed.tzinfo is None:
        raise ValueError("Clock observation needs a timezone")
    if status == "CHECKPOINT":
        for heading in ("FINDINGS", "UNCERTAINTY", "NEXT"):
            if heading not in text.upper():
                raise ValueError(f"Missing {heading} in checkpoint")
    if status == "COMPLETE":
        for heading in ("VERDICT", "REASONING", "TESTS"):
            if heading not in text.upper():
                raise ValueError(f"Missing {heading} in completed review")
        if not re.search(r"\b(ACCEPT|REVISE)\b", text):
            raise ValueError("Missing review verdict")
    return status


def command_for(provider, prompt, timeout):
    if provider == "codex":
        return [os.path.join(os.environ["LOCALAPPDATA"], r"Programs\OpenAI\Codex\bin\codex.exe"),
                "exec", "--ignore-user-config", "--approve-for-me",
                "--color", "never", prompt]
    if provider in ("carbon", "hydrogen"):
        return [r"C:\ProgramData\chocolatey\bin\agy.exe", "--model", f"gemini-4-{provider}",
                "--effort", "low", "--sandbox", "--disable-slash-commands",
                "--print-timeout", f"{timeout}s", "--print", prompt]
    return [os.path.join(os.environ["LOCALAPPDATA"],
            r"Microsoft\WinGet\Packages\GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe\copilot.exe"),
            "--trust-folder", "--model", "auto", "--silent", "--no-color", "--no-ask-user",
            "--disable-builtin-mcps", "--allow-tool", "shell(Get-Date -Format o)",
            "--deny-tool", "write", "--prompt", prompt]


def stop_owned_process(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        result = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                capture_output=True, timeout=15)
        if result.returncode and process.poll() is None:
            raise RuntimeError(f"Owned process tree termination failed: {result.stderr!r}")
    else:
        process.kill()
    process.wait(timeout=15)


def monitor(command, workspace, turn_dir, checkpoint_seconds, response_timeout, publish):
    started = time.monotonic()
    checkpoint_sent = False
    with (turn_dir / "stdout.txt").open("w", encoding="utf-8") as stdout, \
            (turn_dir / "stderr.txt").open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(command, cwd=workspace, stdout=stdout, stderr=stderr)
        try:
            publish("running", pid=process.pid, started_at=utc_now())
            while process.poll() is None:
                elapsed = time.monotonic() - started
                if elapsed >= checkpoint_seconds and not checkpoint_sent:
                    publish("checkpoint_overdue", pid=process.pid, elapsed_seconds=round(elapsed, 3),
                            message="Runner status only. Model progress has not returned.",
                            stdout_bytes=(turn_dir / "stdout.txt").stat().st_size)
                    checkpoint_sent = True
                if elapsed >= response_timeout:
                    stop_owned_process(process)
                    publish("response_timeout", elapsed_seconds=round(elapsed, 3),
                            message="Owned worker stopped after checkpoint grace period; partial output retained.")
                    return None
                time.sleep(min(0.25, checkpoint_seconds / 10))
        except BaseException:
            stop_owned_process(process)
            raise
    return process.returncode


def read_decision(path, run_id, turn):
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("run_id") != run_id or value.get("after_turn") != turn:
        raise ValueError("Steering belongs to a different run or turn")
    if value.get("action") not in ("continue", "steer", "stop"):
        raise ValueError("Unknown coordinator action")
    if not isinstance(value.get("token"), str) or not value["token"].strip() or \
            not isinstance(value.get("instruction"), str) or not value["instruction"].strip():
        raise ValueError("Incomplete coordinator decision")
    return value


def drain_notifications(watch, project, provider, turn_dir):
    """Retain diagnostics and retry bounded notification startup failures."""
    for attempt in range(1, 4):
        result = subprocess.run([str(watch), "topic", "drain", TRACE, "--id", provider,
                                 "--confirm", "-d", str(project), "--json"],
                                capture_output=True, encoding="utf-8", timeout=20)
        (turn_dir / f"drain-{attempt}.stderr.txt").write_text(result.stderr, encoding="utf-8")
        (turn_dir / f"drain-{attempt}.stdout.json").write_text(result.stdout, encoding="utf-8")
        if result.returncode == 0:
            (turn_dir / "received-traces.json").write_text(result.stdout, encoding="utf-8")
            return
        if attempt < 3:
            time.sleep(0.5 * attempt)
    raise RuntimeError("Recur topic drain failed after three bounded attempts; diagnostics retained")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=["carbon", "copilot", "codex", "hydrogen"])
    parser.add_argument("prompt_file", type=Path)
    parser.add_argument("--checkpoint-seconds", type=int, default=180)
    parser.add_argument("--response-timeout", type=int, default=240)
    parser.add_argument("--coordinator-wait", type=int, default=300)
    parser.add_argument("--max-turns", type=int, default=3)
    args = parser.parse_args()
    if not 0 < args.checkpoint_seconds < args.response_timeout or args.max_turns < 1:
        parser.error("Need positive checkpoint < response timeout, and at least one turn")
    base = Path(__file__).resolve().parent
    project = base.parent.parent
    workspace = base / args.provider
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = workspace / "runs" / run_id
    run_dir.mkdir(parents=True)
    scope = (base / "graph.primes.phase.contract.current.md").read_text(encoding="utf-8-sig")
    assignment = args.prompt_file.read_text(encoding="utf-8-sig")
    (run_dir / "assignment.txt").write_text(assignment, encoding="utf-8")
    atomic_json(workspace / "latest-run.json", {"run_id": run_id, "provider": args.provider})
    watch = Path(os.environ["USERPROFILE"]) / ".cargo/bin/recur-watch.exe"
    transcript = []
    guidance = "First return a CHECKPOINT with your provisional findings and proposed next step. Wait for coordinator steering before a final verdict."
    token = "initial"
    role = {"carbon": "Review the analytic derivation, domains, and relation to RH.",
            "copilot": "Review numerical tests, error accounting, and rendering failure cases.",
            "codex": "Independently audit which mathematical claims follow from this finite experiment, and identify unjustified inference toward RH.",
            "hydrogen": "Do routine checklist work: turn the supplied scope into a concise numbered implementation test checklist with input, expected outcome, and evidence to retain. Do not claim to validate the mathematics or run tests."}[args.provider]
    for turn in range(1, args.max_turns + 1):
        turn_dir = run_dir / f"turn-{turn:02}"
        turn_dir.mkdir()
        def publish(state, **fields):
            record = dict(trace_id=f"{TRACE}.{args.provider}.progress", run_id=run_id,
                          provider=args.provider, turn=turn, state=state, at=utc_now(), **fields)
            atomic_json(run_dir / "status.json", record)
            with (run_dir / "events.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps(record) + "\n")
            event = base / "events" / f"{TRACE}.{args.provider}.{run_id}.progress.md"
            temporary = event.with_suffix(".tmp")
            temporary.write_text(f"publish: {record['trace_id']}\n"
                                 f'artifact.refs = ["{(run_dir / "status.json").relative_to(project).as_posix()}"]\n\n'
                                 f"State {state}. Turn {turn}. UTC {record['at']}.\n", encoding="utf-8")
            temporary.replace(event)
            print(json.dumps(record), flush=True)
        try:
            drain_notifications(watch, project, args.provider, turn_dir)
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            publish("notification_failed", message=str(error))
            return 2
        deadline = (datetime.now(timezone.utc) + timedelta(seconds=args.checkpoint_seconds)).isoformat()
        prompt = (f"You are {args.provider} in Warp {TRACE}. {role}\n"
                  f"Coordinator turn {turn}, acknowledgement token {token}.\n"
                  f"Absolute UTC progress deadline: {deadline}. Budget {args.checkpoint_seconds} seconds.\n"
                  "Check actual time by executing only Get-Date -Format o in PowerShell at the start, "
                  "after each short reasoning step (no step over 30 seconds), and immediately before returning. "
                  "Do not estimate elapsed time from tokens. Aim to return 30 seconds before the deadline. "
                  "At the deadline return findings so far, uncertainties, blockers, and your proposed next step, "
                  "even if unfinished. No file edits or other commands. If the clock is unavailable, state that explicitly.\n"
                  "Response format: an exact line STATUS: CHECKPOINT or STATUS: COMPLETE, "
                  f"an exact line ACK: {token}, and CLOCK: <last observed ISO timestamp with offset>. "
                  "A checkpoint uses FINDINGS, UNCERTAINTY, NEXT sections. A complete review uses VERDICT "
                  "(ACCEPT or REVISE), REASONING, TESTS. Keep response under 350 words. "
                  "Coordinator acceptance is separate.\n\n"
                  f"CURRENT COORDINATOR INSTRUCTION\n{guidance}\n\n"
                  f"PRIOR TURN RESPONSES (explicit transcript replay, not a native session resume)\n"
                  + "\n\n".join(transcript) + "\n\nREVIEW SCOPE\n" + scope)
        (turn_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        publish("steering_queued", token=token, deadline_utc=deadline)
        def observe(state, **fields):
            publish(state, **fields)
            if state == "running":
                publish("steering_delivered", token=token, pid=fields["pid"], deadline_utc=deadline)
        code = monitor(command_for(args.provider, prompt, args.response_timeout), workspace, turn_dir,
                       args.checkpoint_seconds, args.response_timeout, observe)
        text = (turn_dir / "stdout.txt").read_text(encoding="utf-8", errors="replace")
        if code != 0:
            if code is not None:
                publish("worker_failed", exit_code=code, message="Read retained stdout/stderr for this turn.")
            return 2
        try:
            status = validate_reply(text, token)
        except ValueError as error:
            publish("protocol_failed", message=str(error))
            return 2
        publish("steering_acknowledged", token=token, worker_status=status)
        transcript.append(text)
        if status == "COMPLETE":
            report = f"publish: {TRACE}.{args.provider}.response\n\n" + text
            (run_dir / "review.md").write_text(report, encoding="utf-8")
            (workspace / "review.md").write_text(report, encoding="utf-8")
            publish("complete", report=(run_dir / "review.md").relative_to(project).as_posix())
            print(report, flush=True)
            return 0
        publish("awaiting_coordinator", response=(turn_dir / "stdout.txt").relative_to(project).as_posix())
        decision_path = run_dir / f"steering-after-{turn:02}.json"
        wait_started = time.monotonic()
        while time.monotonic() - wait_started < args.coordinator_wait:
            decision = read_decision(decision_path, run_id, turn)
            if decision:
                break
            time.sleep(1)
        else:
            publish("coordinator_timeout", message="No continuation authorized within wait budget.")
            return 2
        if decision["action"] == "stop":
            publish("stopped_by_coordinator", token=decision["token"])
            return 2
        token, guidance = decision["token"], decision["instruction"]
    publish("turn_limit", message="Bounded turn budget exhausted. Partial reviews retained.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
