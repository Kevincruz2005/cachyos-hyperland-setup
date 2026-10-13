# SPDX-License-Identifier: MIT
"""No GPU or desktop is touched: use a synthetic sysfs/procfs tree."""
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import installer
from test_safety import host


class GpuStatus(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.sysroot = self.base / "sys"
        self.procroot = self.base / "proc"
        (self.sysroot / "bus/pci/devices").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def function(self, address, runtime, power_state, vendor="0x10de", cls="0x030000"):
        device = self.sysroot / "bus/pci/devices" / address
        (device / "power").mkdir(parents=True)
        for name, value in (("vendor", vendor), ("class", cls),
                            ("power/runtime_status", runtime), ("power_state", power_state)):
            (device / name).write_text(value + "\n")
        return device

    def status(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools/gpu-runtime-status"),
             "--sysroot", str(self.sysroot), "--procroot", str(self.procroot)],
            capture_output=True, text=True, check=True)
        return completed.stdout.splitlines()

    def test_all_functions_d3cold_and_video_memory_off(self):
        self.function("0000:43:00.0", "suspended", "D3cold")
        self.function("0000:43:00.1", "suspended", "D3cold", cls="0x040300")
        power = self.procroot / "driver/nvidia/gpus/0000:43:00.0/power"
        power.parent.mkdir(parents=True)
        power.write_text("Runtime D3 status: Enabled\nVideo Memory: Off\n")
        state, detail = self.status()
        self.assertEqual(state, "asleep")
        self.assertIn("all PCI functions suspended", detail)
        self.assertIn("video memory off", detail)

    def test_one_function_awake(self):
        self.function("0000:43:00.0", "suspended", "D3cold")
        self.function("0000:43:00.1", "active", "D0", cls="0x040300")
        self.assertEqual(self.status()[0], "awake")

    def test_not_d3cold_is_not_reported_as_asleep(self):
        self.function("0000:43:00.0", "suspended", "D3hot")
        self.assertEqual(self.status()[0], "unknown")

    def test_missing_and_non_nvidia_devices(self):
        self.function("0000:00:02.0", "active", "D0", vendor="0x8086")
        self.assertEqual(self.status()[0], "unknown")
        self.function("0000:43:00.0", "suspended", "D3cold")
        (self.sysroot / "bus/pci/devices/0000:43:00.0/power_state").unlink()
        self.assertEqual(self.status()[0], "unknown")

    def test_export_only_on_nvidia_and_preserves_other_tiles(self):
        home = self.base / "home"
        home.mkdir()
        generic = installer.render(home, host(), self.base / "wallpaper.png")
        self.assertNotIn(".local/bin/gpu-runtime-status", generic)
        hybrid = host()
        hybrid["gpus"] = [{"vendor": "0x10de"}]
        payload = installer.render(home, hybrid, self.base / "wallpaper.png")
        state = tomllib.loads(payload[".local/state/noctalia/settings.toml"].decode())
        tiles = [item["type"] for item in state["control_center"]["shortcuts"]]
        self.assertEqual(tiles, ["wifi", "bluetooth", "kevincruz2005/gpu-status:check",
                                 "nightlight", "notification", "power_profile"])
        self.assertEqual(state["plugins"]["enabled"], ["kevincruz2005/gpu-status"])
        self.assertIn(".local/share/noctalia/plugins/gpu-status/plugin.toml", payload)

    def test_custom_tiles_without_caffeine_stop_for_review(self):
        home = self.base / "home"
        config = home / ".config/noctalia/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text('[[control_center.shortcuts]]\ntype = "wifi"\n')
        hybrid = host()
        hybrid["gpus"] = [{"vendor": "0x10de"}]
        with self.assertRaisesRegex(RuntimeError, "Caffeine shortcut"):
            installer.render(home, hybrid, self.base / "wallpaper.png")

    def test_existing_status_tile_and_other_plugins_are_preserved(self):
        home = self.base / "home"
        settings = home / ".local/state/noctalia/settings.toml"
        settings.parent.mkdir(parents=True)
        settings.write_text('[[control_center.shortcuts]]\ntype = "kevincruz2005/gpu-status:check"\n'
                            '[plugins]\nenabled = ["someone/other"]\n')
        hybrid = host()
        hybrid["gpus"] = [{"vendor": "0x10de"}]
        payload = installer.render(home, hybrid, self.base / "wallpaper.png")
        state = tomllib.loads(payload[".local/state/noctalia/settings.toml"].decode())
        self.assertEqual(state["control_center"]["shortcuts"],
                         [{"type": "kevincruz2005/gpu-status:check"}])
        self.assertEqual(state["plugins"]["enabled"],
                         ["someone/other", "kevincruz2005/gpu-status"])


if __name__ == "__main__":
    unittest.main()
