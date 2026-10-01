# SPDX-License-Identifier: MIT
"""Pure CPU/segmentation tests. Never open a microphone or launch a service."""
import array
import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("dictation_export", str(ROOT / "tools/hypr-dictation"))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


class SegmentationTests(unittest.TestCase):
    quiet = bytes(3200)
    voice = array.array("h", [1000]*1600).tobytes()

    def test_silence_never_emits_model_work(self):
        segment = module.Segmenter()
        for _ in range(1000):
            self.assertIsNone(segment.feed(self.quiet))
        self.assertIsNone(segment.flush())
        self.assertLessEqual(len(segment.preroll), 2)

    def test_click_rejected(self):
        segment = module.Segmenter()
        segment.feed(self.voice)
        for _ in range(7):
            self.assertIsNone(segment.feed(self.quiet))

    def test_pause_emits_once(self):
        segment = module.Segmenter()
        for _ in range(5):
            self.assertIsNone(segment.feed(self.voice))
        for _ in range(6):
            self.assertIsNone(segment.feed(self.quiet))
        self.assertEqual(len(segment.feed(self.quiet)), 12*3200)
        self.assertIsNone(segment.flush())

    def test_continuous_speech_bounded(self):
        segment = module.Segmenter()
        output = []
        for _ in range(160):
            result = segment.feed(self.voice)
            if result:
                output.append(result)
        self.assertEqual([len(item) for item in output], [80*3200, 80*3200])

    def test_final_words_flush_once(self):
        segment = module.Segmenter()
        for _ in range(4):
            segment.feed(self.voice)
        self.assertEqual(len(segment.flush()), 4*3200)
        self.assertIsNone(segment.flush())

    def test_lock_unknown_fail_closed(self):
        for value in ('{"locked":true}', '{}', 'not json'):
            with patch.object(module, "command", return_value=subprocess.CompletedProcess([], 0, value, "")):
                self.assertEqual(module.safe_window(), "")

    def test_cancel_scoped_to_whole_own_unit(self):
        with patch.object(module, "command") as run:
            module.cancel_unit()
        self.assertEqual(run.call_count, 2)
        self.assertIn("--kill-whom=all", run.call_args_list[0].args[0])
        self.assertIn("--signal=SIGKILL", run.call_args_list[0].args[0])
        self.assertEqual(run.call_args_list[0].args[0][-1], module.UNIT)

    def test_no_installed_daemon_and_bounded_properties(self):
        source = (ROOT / "tools/hypr-dictation").read_text()
        for expected in ("KillMode=mixed", "SendSIGKILL=yes", "TimeoutStopSec=15s", "RuntimeMaxSec=10min",
                         "MemoryMax=384M", "MemorySwapMax=0", "CPUQuota=150%", "Restart=no", "--collect"):
            self.assertIn(expected, source)
        self.assertFalse(any(ROOT.rglob("hypr-dictation.service")))


if __name__ == "__main__":
    unittest.main()
