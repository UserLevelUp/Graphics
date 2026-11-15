"""Bounds and permissions specific to the conclusion review adapter."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys
import hashlib

spec = importlib.util.spec_from_file_location("bounded_conclusion_runner", Path(__file__).with_name("run-review.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ReviewBoundsTests(unittest.TestCase):
    def test_requested_limits_are_accepted(self):
        runner.validate_limits(180, 240, 2, 300)

    def test_larger_budgets_or_invalid_order_are_rejected(self):
        for values in ((181, 240, 2, 300), (180, 241, 2, 300), (180, 240, 3, 300),
                       (180, 240, 2, 301), (180, 180, 2, 300), (0, 240, 2, 300)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                runner.validate_limits(*values)

    def test_codex_uses_read_only_without_permission_bypass(self):
        argv = runner.command_for("codex", "review this text", 240)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "read-only")
        self.assertIn('approval_policy="never"', argv)
        self.assertNotIn("--approve-for-me", argv)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", argv)
        self.assertEqual(argv[-1], "-")
        self.assertNotIn("review this text", argv)

    def test_large_utf8_prompt_is_passed_by_stdin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt = root / "prompt.txt"
            prompt.write_text("zeta \u03b6\n" * 10000, encoding="utf-8")
            code = runner.monitor([sys.executable, "-c", "import sys; print(len(sys.stdin.buffer.read()))"],
                                  root, root, 1, 3, lambda *args, **kwargs: None, prompt)
            self.assertEqual(code, 0)
            self.assertEqual(int((root / "stdout.txt").read_text()), len(prompt.read_bytes()))

    def test_unconfigured_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            runner.command_for("carbon", "review", 240)

    def test_reference_projection_labels_omitted_interior_points(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "workers"
            base.mkdir()
            (root / "formulation").mkdir()
            (root / "inputs").mkdir()
            (base / "review-scope.md").write_text("Scope", encoding="utf-8")
            for name in ("conclusion.json", "closing-scenes.json"):
                (root / "formulation" / name).write_text("{}", encoding="utf-8")
            data = {"schema": "reference", "trajectories": [{"id": "Z1", "status": "exited",
                    "points": [{"largeInterior": "omitted_marker"}], "rejectedSteps": [],
                    "endpoint": {"a": 0.85}, "exit": {"widthA": 1e-24}}]}
            (root / "inputs/reference-trajectories.json").write_text(json.dumps(data), encoding="utf-8")
            scope = runner.load_scope(root, base)
            self.assertIn("Endpoint/status projection only", scope)
            self.assertIn('"pointCount": 1', scope)
            self.assertIn('"widthA": 1e-24', scope)
            self.assertNotIn("omitted_marker", scope)

    def test_recovery_preserves_checkpoint_and_requires_its_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "checkpoint.txt"
            checkpoint.write_text("STATUS: CHECKPOINT\nACK: initial\nCLOCK: unavailable - blocked\n", encoding="utf-8")
            recovery = {"priorTurn": 1, "token": "exact-token", "instruction": "Final review",
                        "checkpointPath": "checkpoint.txt", "checkpointSha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest()}
            path = root / "recovery.json"
            path.write_text(json.dumps(recovery), encoding="utf-8")
            loaded, text = runner.load_recovery(path, root)
            self.assertEqual(loaded["token"], "exact-token")
            self.assertIn("CLOCK: unavailable", text)
            checkpoint.write_text(checkpoint.read_text() + "modified", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "fingerprint changed"):
                runner.load_recovery(path, root)

    def test_recovery_refuses_additional_prior_turns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "recovery.json"
            path.write_text(json.dumps({"priorTurn": 2, "token": "token", "instruction": "Review"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "one prior turn"):
                runner.load_recovery(path, root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
