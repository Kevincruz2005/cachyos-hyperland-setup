# SPDX-License-Identifier: MIT
"""Isolated OCR/controller tests: no GUI, real screenshot, clipboard or engine."""
import ast
from math import floor, ceil
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / "tools/hypr-screenshot").read_text())
nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
         and node.name in ("OCRJob", "ScreenshotApp", "logical_to_image_rect")]
scope = {"os": os, "shutil": shutil, "signal": signal, "subprocess": subprocess,
         "tempfile": tempfile, "time": time, "floor": floor, "ceil": ceil,
         "GLib": SimpleNamespace(SOURCE_CONTINUE=True, SOURCE_REMOVE=False,
                                 timeout_add=Mock(return_value=17), source_remove=Mock()),
         "Gdk": SimpleNamespace(**{"KEY_" + key: index for index, key in enumerate(
             ("f", "F", "c", "C", "o", "O", "Return", "KP_Enter", "Escape"))})}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "screenshot-ocr-tests", "exec"), scope)
OCRJob, ScreenshotApp = scope["OCRJob"], scope["ScreenshotApp"]


class OCRTests(unittest.TestCase):
    def job(self, code=None):
        process = Mock(pid=54321)
        process.poll.return_value = code
        with patch.object(shutil, "which", return_value="/usr/bin/tesseract"), \
                patch.object(subprocess, "Popen", return_value=process) as spawn:
            job = OCRJob("fixture.png")
        return job, process, spawn.call_args

    def test_lazy_missing_dependency(self):
        with patch.object(shutil, "which", return_value=None), patch.object(subprocess, "Popen") as spawn:
            with self.assertRaises(RuntimeError):
                OCRJob("fixture.png")
            spawn.assert_not_called()

    def test_local_english_single_thread_bounded_process(self):
        job, process, call = self.job(0)
        try:
            self.assertEqual(call.args[0], ["timeout", "--signal=KILL", "20s", "nice", "-n", "10",
                                           "tesseract", "fixture.png", "stdout", "-l", "eng", "--psm", "11"])
            self.assertEqual(call.kwargs["env"]["OMP_THREAD_LIMIT"], "1")
            self.assertNotIn("LD_PRELOAD", call.kwargs["env"])
            self.assertTrue(call.kwargs["start_new_session"])
        finally:
            job.close()

    def test_output_preserves_newlines_then_closes(self):
        job, process, _ = self.job(0)
        job.output.write(b" Hello world\n\nSecond line\n\x0c")
        self.assertEqual(job.poll(), "Hello world\n\nSecond line")
        self.assertTrue(job.output.closed)
        job.close()  # Cleanup is repeatable.

    def test_empty_output_not_an_error(self):
        job, _, _ = self.job(0)
        self.assertEqual(job.poll(), "")
        self.assertTrue(job.output.closed)

    def test_oversized_output_rejected_and_closed(self):
        job, _, _ = self.job(0)
        job.output.write(b"x" * (1024 * 1024 + 1))
        with self.assertRaises(RuntimeError):
            job.poll()
        self.assertTrue(job.output.closed)

    def test_engine_failure_closes_output(self):
        job, _, _ = self.job(1)
        with self.assertRaises(RuntimeError):
            job.poll()
        self.assertTrue(job.output.closed)

    def test_cancel_kills_only_own_group_and_reaps(self):
        job, process, _ = self.job()
        with patch.object(os, "killpg") as kill:
            job.close()
        kill.assert_called_once_with(process.pid, signal.SIGKILL)
        process.wait.assert_called_once_with(timeout=2)
        self.assertTrue(job.output.closed)

    def test_timeout_kills_and_closes(self):
        job, process, _ = self.job()
        with patch.object(time, "monotonic", return_value=job.started + 21), patch.object(os, "killpg") as kill:
            with self.assertRaises(RuntimeError):
                job.poll()
        kill.assert_called_once_with(process.pid, signal.SIGKILL)
        self.assertTrue(job.output.closed)

    def test_pending_job_does_not_read_output(self):
        job, process, _ = self.job()
        with patch.object(time, "monotonic", return_value=job.started):
            self.assertIsNone(job.poll())
        self.assertFalse(job.output.closed)
        process.poll.return_value = 0
        job.close()

    def test_spawn_failure_closes_temporary_file(self):
        with tempfile.TemporaryFile() as output, patch.object(shutil, "which", return_value="tesseract"), \
                patch.object(tempfile, "TemporaryFile", return_value=output), \
                patch.object(subprocess, "Popen", side_effect=OSError("missing")):
            with self.assertRaises(OSError):
                OCRJob("fixture.png")
            self.assertTrue(output.closed)


class ControllerTests(unittest.TestCase):
    def test_original_three_button_preview_preserved(self):
        app_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ScreenshotApp")
        card = next(n for n in app_class.body if isinstance(n, ast.FunctionDef) and n.name == "show_decision_card")
        labels = [kw.value.value for n in ast.walk(card) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr == "Button"
                  for kw in n.keywords if kw.arg == "label" and isinstance(kw.value, ast.Constant)]
        self.assertEqual(labels, ["Copy [C]", "Save [Enter]", "Cancel [Esc]"])

    def test_plain_labels_and_flat_card_styling(self):
        source = (ROOT / "tools/hypr-screenshot").read_text()
        for decoration in ("📋", "💾", "📸", "✂", "✕"):
            self.assertNotIn(decoration, source)
        self.assertIn('label="Screenshot captured"', source)
        self.assertIn("[F] Full screen", source)
        self.assertNotIn("linear-gradient", source)
        self.assertNotIn("box-shadow", source)

    def app(self):
        app = ScreenshotApp.__new__(ScreenshotApp)
        app.phase = "DECIDE"
        app.ocr_job = None
        app.ocr_timer = None
        app.cropped_png = "fixture.png"
        app.decision_status = Mock()
        app.decision_buttons = (Mock(), Mock(), Mock())
        app.notify = Mock()
        app.cleanup_and_quit = Mock()
        return app

    def test_o_only_starts_in_preview_and_never_twice(self):
        app = self.app()
        with patch.dict(scope, {"OCRJob": Mock()}):
            app.phase = "CROP"
            app.action_ocr()
            scope["OCRJob"].assert_not_called()
            app.phase = "DECIDE"
            app.action_ocr()
            self.assertEqual(app.phase, "OCR")
            app.action_ocr()
            scope["OCRJob"].assert_called_once_with("fixture.png")
        self.assertEqual(app.ocr_timer, 17)

    def test_o_shortcut_routes_to_ocr(self):
        app = self.app()
        app.action_ocr = Mock()
        for key in (scope["Gdk"].KEY_o, scope["Gdk"].KEY_O):
            self.assertTrue(app.on_key_pressed(None, key, 0, 0))
        self.assertEqual(app.action_ocr.call_count, 2)

    def test_success_copies_text_not_image_no_transcript_notification(self):
        app = self.app()
        app.phase = "OCR"
        app.ocr_timer = 17
        app.ocr_job = Mock()
        app.ocr_job.poll.return_value = "Fixture text\nSecond line"
        with patch.object(subprocess, "run") as copy:
            self.assertFalse(app.poll_ocr())
        self.assertEqual(copy.call_args.args[0], ["wl-copy", "--type", "text/plain;charset=utf-8"])
        self.assertEqual(copy.call_args.kwargs["input"], "Fixture text\nSecond line")
        self.assertEqual(copy.call_args.kwargs["timeout"], 3)
        self.assertNotIn("Fixture text", str(app.notify.call_args))
        app.cleanup_and_quit.assert_called_once()
        self.assertIsNone(app.ocr_timer)
        self.assertIsNone(app.ocr_job)

    def test_empty_failure_and_copy_error_keep_preview(self):
        for result in ("", RuntimeError("bad engine"), "recognized"):
            app = self.app()
            app.phase = "OCR"
            app.ocr_job = Mock()
            if isinstance(result, Exception):app.ocr_job.poll.side_effect = result
            else:app.ocr_job.poll.return_value = result
            with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("wl-copy", 3)) as copy:
                self.assertFalse(app.poll_ocr())
            if result != "recognized":copy.assert_not_called()
            self.assertEqual(app.phase, "DECIDE")
            self.assertIsNone(app.ocr_job)
            app.cleanup_and_quit.assert_not_called()
            for button in app.decision_buttons:button.set_sensitive.assert_called_with(True)

    def test_busy_ignores_other_actions_but_escape_cancels(self):
        app = self.app()
        app.phase = "OCR"
        app.action_cancel = Mock()
        with patch.object(subprocess, "run") as run:
            app.action_copy()
            app.action_save()
            self.assertTrue(app.on_key_pressed(None, scope["Gdk"].KEY_o, 0, 0))
            run.assert_not_called()
        app.action_cancel.assert_not_called()
        self.assertTrue(app.on_key_pressed(None, scope["Gdk"].KEY_Escape, 0, 0))
        app.action_cancel.assert_called_once()

    def test_cleanup_removes_active_timer_and_worker(self):
        app = self.app()
        app.ocr_job = job = Mock()
        app.ocr_timer = 17
        with tempfile.TemporaryDirectory() as parent:
            folder = Path(parent) / "private-screenshot"
            folder.mkdir()
            (folder / "fixture.txt").write_text("fixture")
            app.tmp_dir = str(folder)
            app.cleanup()
            self.assertFalse(folder.exists())
        job.close.assert_called_once()
        scope["GLib"].source_remove.assert_called_with(17)
        self.assertIsNone(app.ocr_timer)
        self.assertIsNone(app.ocr_job)


if __name__ == "__main__":
    unittest.main()
