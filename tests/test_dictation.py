# SPDX-License-Identifier: MIT
"""Pure CPU/segmentation tests. Never open a microphone or launch a service."""
import array
import hashlib
import io
import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("dictation_export", str(ROOT / "tools/hypr-dictation"))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
sys.path.insert(0, str(ROOT / "lib"))
import installer


def import_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / (name + ".py"))
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    return tool


download = import_tool("download_model")
benchmark = import_tool("benchmark_dictation")


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

    def test_english_cpu_only_arguments(self):
        args = module.recognizer_args(Path("input.wav"), Path("output"))
        self.assertEqual(args[0], "whisper-cli")
        self.assertEqual(args[args.index("--language") + 1], "en")
        self.assertEqual(args[args.index("--threads") + 1], "2")
        self.assertEqual(args[args.index("--model") + 1], str(module.MODEL))
        for flag in ("--no-gpu", "--no-fallback", "--suppress-nst", "--output-txt"):
            self.assertIn(flag, args)
        self.assertNotIn("auto", args)
        self.assertNotIn("--translate", args)

    def test_model_metadata_consistent(self):
        self.assertEqual(module.MODEL.name, download.MODEL_NAME)
        self.assertEqual(installer.MODEL_NAME, download.MODEL_NAME)
        self.assertEqual(installer.MODEL_SHA, download.SHA256)
        self.assertTrue(download.URL.endswith(download.MODEL_NAME))
        self.assertEqual(download.SIZE, 32166155)

    def test_benchmark_normalized_word_error(self):
        self.assertEqual(benchmark.word_error("Hello, WORLD!", "hello world"), 0)
        self.assertEqual(benchmark.word_error("one two", "one three"), 0.5)
        self.assertEqual(benchmark.word_error("one two", "one"), 0.5)
        self.assertEqual(benchmark.word_error("one", "one two"), 1)


class ModelDownloadTests(unittest.TestCase):
    def test_verified_atomic_download_and_reuse(self):
        payload = b"test model bytes"
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(download, "SHA256", hashlib.sha256(payload).hexdigest()), \
                patch.object(download, "SIZE", len(payload)), \
                patch.object(download.urllib.request, "urlopen", return_value=io.BytesIO(payload)) as network:
            target = Path(folder) / "models/model.bin"
            download.download(target)
            self.assertEqual(target.read_bytes(), payload)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            download.download(target)
            self.assertEqual(network.call_count, 1)
            self.assertFalse(list(target.parent.glob(".model-*")))

    def test_bad_response_leaves_no_model_or_temporary(self):
        for payload in (b"short", b"too long" * 20, b"wrong digest"):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as folder, \
                    patch.object(download, "SIZE", 12), \
                    patch.object(download.urllib.request, "urlopen", return_value=io.BytesIO(payload)):
                target = Path(folder) / "model.bin"
                with self.assertRaises(RuntimeError):
                    download.download(target)
                self.assertEqual(list(Path(folder).iterdir()), [])

    def test_existing_bad_model_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(download.urllib.request, "urlopen") as network:
            target = Path(folder) / "model.bin"
            target.write_bytes(b"owner data")
            with self.assertRaises(RuntimeError):
                download.download(target)
            self.assertEqual(target.read_bytes(), b"owner data")
            network.assert_not_called()

    def test_symlink_rejected_without_following(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(download.urllib.request, "urlopen") as network:
            original = Path(folder) / "original"
            original.write_bytes(b"owner data")
            target = Path(folder) / "model.bin"
            target.symlink_to(original)
            with self.assertRaises(RuntimeError):
                download.download(target)
            self.assertEqual(original.read_bytes(), b"owner data")
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
