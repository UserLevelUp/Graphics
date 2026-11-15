"""Protocol checks with temporary files and owned Python test processes only."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("review_runner_under_test", BASE / "run-review.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def checkpoint(token="turn-token"):
    return (
        "STATUS: CHECKPOINT\n"
        f"ACK: {token}\n"
        "CLOCK: 2026-11-15T02:40:00+00:00\n"
        "FINDINGS\nThe model preserves full phase.\n"
        "UNCERTAINTY\nRoundoff remains to be quantified.\n"
        "NEXT\nCheck the reference values.\n"
    )


def complete(token="turn-token"):
    return (
        "STATUS: COMPLETE\n"
        f"ACK: {token}\n"
        "CLOCK: 2026-11-15T02:40:00Z\n"
        "VERDICT\nACCEPT\n"
        "REASONING\nThe domain is explicit.\n"
        "TESTS\nCheck the real-axis control and reversed summation.\n"
    )


class ReplyValidationTests(unittest.TestCase):
    def test_accepts_checkpoint_and_completed_review(self):
        self.assertEqual(runner.validate_reply(checkpoint(), "turn-token"), "CHECKPOINT")
        self.assertEqual(runner.validate_reply(complete(), "turn-token"), "COMPLETE")

    def test_rejects_wrong_acknowledgement(self):
        with self.assertRaises(ValueError):
            runner.validate_reply(checkpoint("prior-turn"), "turn-token")

    def test_rejects_conflicting_statuses(self):
        with self.assertRaises(ValueError):
            runner.validate_reply(checkpoint() + "STATUS: COMPLETE\n", "turn-token")

    def test_rejects_missing_clock(self):
        text = "\n".join(line for line in checkpoint().splitlines() if not line.startswith("CLOCK:"))
        with self.assertRaises(ValueError):
            runner.validate_reply(text, "turn-token")

    def test_rejects_invalid_calendar_timestamp(self):
        text = checkpoint().replace("2026-11-15T02:40:00+00:00", "2026-99-99Tgarbage+00:00")
        with self.assertRaises(ValueError):
            runner.validate_reply(text, "turn-token")

    def test_rejects_checkpoint_without_requested_sections(self):
        text = "STATUS: CHECKPOINT\nACK: turn-token\nCLOCK: 2026-11-15T02:40:00Z\n"
        with self.assertRaises(ValueError):
            runner.validate_reply(text, "turn-token")

    def test_rejects_duplicate_acknowledgements(self):
        with self.assertRaises(ValueError):
            runner.validate_reply(checkpoint() + "ACK: prior-turn\n", "turn-token")

    def test_rejects_complete_without_verdict(self):
        with self.assertRaises(ValueError):
            runner.validate_reply(complete().replace("ACCEPT\n", ""), "turn-token")


class DecisionValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "decision.json"
        self.value = {
            "run_id": "run-1", "after_turn": 2, "action": "steer",
            "token": "new-guidance", "instruction": "Check the truncation bound."
        }

    def write(self):
        self.path.write_text(json.dumps(self.value), encoding="utf-8")

    def test_absent_decision_returns_none(self):
        self.assertIsNone(runner.read_decision(self.path, "run-1", 2))

    def test_exact_run_and_turn_are_accepted(self):
        self.write()
        self.assertEqual(runner.read_decision(self.path, "run-1", 2), self.value)

    def test_stale_run_is_rejected(self):
        self.write()
        with self.assertRaises(ValueError):
            runner.read_decision(self.path, "run-2", 2)

    def test_stale_turn_is_rejected(self):
        self.write()
        with self.assertRaises(ValueError):
            runner.read_decision(self.path, "run-1", 3)

    def test_unknown_action_is_rejected(self):
        self.value["action"] = "silently_restart"
        self.write()
        with self.assertRaises(ValueError):
            runner.read_decision(self.path, "run-1", 2)

    def test_non_string_token_is_rejected(self):
        self.value["token"] = ["ambiguous-token"]
        self.write()
        with self.assertRaises(ValueError):
            runner.read_decision(self.path, "run-1", 2)


class MonitorTests(unittest.TestCase):
    @staticmethod
    def stop_test_process(process):
        # The fake Python children create no descendants. Keep timing tests
        # independent of permissions for Windows taskkill or process-tree APIs.
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)

    def run_command(self, code, checkpoint_seconds, response_timeout):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        events = []

        def publish(state, **fields):
            events.append({"state": state, **fields})

        with mock.patch.object(runner, "stop_owned_process", self.stop_test_process):
            result = runner.monitor(
                [sys.executable, "-u", "-c", code], directory, directory,
                checkpoint_seconds, response_timeout, publish
            )
        return result, events, directory

    def test_normal_exit_retains_both_streams(self):
        result, events, directory = self.run_command(
            "import sys; print('complete stdout'); print('complete stderr', file=sys.stderr)",
            1.0, 3.0
        )
        self.assertEqual(result, 0)
        self.assertEqual([event["state"] for event in events], ["running"])
        self.assertIn("complete stdout", (directory / "stdout.txt").read_text())
        self.assertIn("complete stderr", (directory / "stderr.txt").read_text())

    def test_nonzero_exit_is_returned_with_diagnostics(self):
        result, events, directory = self.run_command(
            "import sys; print('owned test failure', file=sys.stderr); sys.exit(7)", 1.0, 3.0
        )
        self.assertEqual(result, 7)
        self.assertIn("owned test failure", (directory / "stderr.txt").read_text())
        self.assertNotIn("response_timeout", [event["state"] for event in events])

    def test_overdue_checkpoint_then_timeout_retains_partial_output(self):
        result, events, directory = self.run_command(
            "import sys,time; print('partial stdout', flush=True); "
            "print('partial stderr', file=sys.stderr, flush=True); time.sleep(8)",
            0.5, 1.0
        )
        self.assertIsNone(result)
        self.assertEqual(
            [event["state"] for event in events],
            ["running", "checkpoint_overdue", "response_timeout"]
        )
        self.assertIn("Runner status only", events[1]["message"])
        self.assertGreater(events[1]["stdout_bytes"], 0)
        self.assertIn("partial stdout", (directory / "stdout.txt").read_text())
        self.assertIn("partial stderr", (directory / "stderr.txt").read_text())


    def test_publication_error_stops_owned_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            stopped = []

            def publish(state, **fields):
                raise OSError("test publication failed")

            def stop(process):
                stopped.append(process)
                self.stop_test_process(process)

            with mock.patch.object(runner, "stop_owned_process", stop):
                with self.assertRaisesRegex(OSError, "test publication failed"):
                    runner.monitor(
                        [sys.executable, "-u", "-c", "import time; time.sleep(8)"],
                        directory, directory, 0.5, 1.0, publish
                    )
            self.assertEqual(len(stopped), 1)
            self.assertIsNotNone(stopped[0].poll())


class SteeringCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        for name in ("run-review.py", "steer-review.py"):
            shutil.copyfile(BASE / name, self.base / name)
        self.run = self.base / "codex" / "runs" / "run-1"
        self.run.mkdir(parents=True)
        (self.run / "status.json").write_text(json.dumps({
            "state": "awaiting_coordinator", "run_id": "run-1", "turn": 2
        }), encoding="utf-8")
        self.instruction = self.base / "instruction.txt"
        self.instruction.write_text("Check the next numerical case.", encoding="utf-8")

    def invoke(self, turn=2):
        return subprocess.run(
            [sys.executable, str(self.base / "steer-review.py"), "codex", "run-1",
             str(turn), "steer", str(self.instruction)],
            capture_output=True, text=True, timeout=5
        )

    def test_queues_exact_checkpoint_once(self):
        first = self.invoke()
        self.assertEqual(first.returncode, 0, first.stderr)
        path = self.run / "steering-after-02.json"
        original = path.read_bytes()
        decision = json.loads(original)
        self.assertEqual(decision["state"], "queued")
        self.assertEqual(decision["instruction"], "Check the next numerical case.")
        self.assertEqual(decision["after_turn"], 2)
        self.assertTrue(decision["token"])
        second = self.invoke()
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(path.read_bytes(), original)

    def test_refuses_stale_checkpoint(self):
        result = self.invoke(turn=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.run / "steering-after-01.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
