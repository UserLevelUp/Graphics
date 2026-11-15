"""Regression checks for observed Windows publication and console failures."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gap_runtime_runner", BASE / "run-review.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ReplaceRetryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.target = self.base / "event.md"
        self.target.write_text("old event", encoding="utf-8")
        self.temporary = self.base / "event.tmp"
        self.temporary.write_text("new event: τ", encoding="utf-8")

    def test_transient_permission_errors_then_real_atomic_replace(self):
        original_replace = Path.replace
        calls = []

        def briefly_locked(source, target):
            calls.append((source, target))
            if len(calls) <= 2:
                raise PermissionError(5, "reader holds destination")
            return original_replace(source, target)

        with mock.patch.object(Path, "replace", autospec=True,
                               side_effect=briefly_locked), \
                mock.patch.object(runner.time, "sleep") as sleep:
            runner.replace_with_retry(self.temporary, self.target)
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleep.call_args_list, [mock.call(0.05), mock.call(0.1)])
        self.assertEqual(self.target.read_text(encoding="utf-8"), "new event: τ")
        self.assertFalse(self.temporary.exists())

    def test_persistent_permission_error_exhausts_five_attempts_and_preserves_files(self):
        error = PermissionError(5, "persistent destination lock")
        with mock.patch.object(Path, "replace", side_effect=error) as replace, \
                mock.patch.object(runner.time, "sleep") as sleep:
            with self.assertRaises(PermissionError) as caught:
                runner.replace_with_retry(self.temporary, self.target)
        self.assertIs(caught.exception, error)
        self.assertEqual(replace.call_count, 5)
        self.assertEqual(sleep.call_args_list, [mock.call(x) for x in (0.05, 0.1, 0.2, 0.4)])
        self.assertEqual(self.target.read_text(encoding="utf-8"), "old event")
        self.assertEqual(self.temporary.read_text(encoding="utf-8"), "new event: τ")

    def test_other_oserror_is_not_retried(self):
        error = OSError(28, "disk failure")
        with mock.patch.object(Path, "replace", side_effect=error) as replace, \
                mock.patch.object(runner.time, "sleep") as sleep:
            with self.assertRaises(OSError) as caught:
                runner.replace_with_retry(self.temporary, self.target)
        self.assertIs(caught.exception, error)
        replace.assert_called_once_with(self.target)
        sleep.assert_not_called()

    def test_atomic_json_recovers_from_reader_lock(self):
        target = self.base / "status.json"
        original_replace = Path.replace
        calls = []

        def once_locked(source, destination):
            calls.append((source, destination))
            if len(calls) == 1:
                raise PermissionError(5, "reader lock")
            return original_replace(source, destination)

        with mock.patch.object(Path, "replace", autospec=True, side_effect=once_locked), \
                mock.patch.object(runner.time, "sleep"):
            runner.atomic_json(target, {"state": "complete", "math": "Λ ≥ 0"})
        self.assertEqual(len(calls), 2)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")),
                         {"state": "complete", "math": "Λ ≥ 0"})


class ConsoleTransportTests(unittest.TestCase):
    def test_math_report_round_trips_through_strict_cp1252_console(self):
        report = "publish: graph.riemann.gap.codex.response\n∂tP = −∂z²P; Λ ≥ 0; τ ≤ −2/3\n"
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
        with contextlib.redirect_stdout(stream):
            runner.print_review(report)
        payload = raw.getvalue().decode("ascii")
        self.assertEqual(json.loads(payload), {"review": report})
        self.assertTrue(payload.endswith("\n"))
        stream.detach()


if __name__ == "__main__":
    unittest.main(verbosity=2)
