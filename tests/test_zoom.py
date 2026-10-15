# SPDX-License-Identifier: MIT
"""Native zoom stays bounded and has no external worker."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ZoomContract(unittest.TestCase):
    def test_native_cursor_zoom_shortcuts_and_bounds(self):
        binds = (ROOT / "config/hypr/config/binds.lua").read_text()
        zoom = binds.split("-- Zoom\n", 1)[1].split("------------------", 1)[0]
        self.assertIn('hl.get_config("cursor:zoom_factor")', zoom)
        self.assertIn("math.max(1.0, math.min(10.0, nextvalue))", zoom)
        self.assertIn('mainMod .. " + Plus"', zoom)
        self.assertIn('mainMod .. " + Minus"', zoom)
        self.assertIn('mainMod .. " + code:82"', zoom)
        self.assertIn('mainMod .. " + code:86"', zoom)
        self.assertNotIn("exec_cmd", zoom)

    def test_pixel_zoom_has_no_background_service(self):
        inputs = (ROOT / "config/hypr/config/inputs.lua").read_text()
        self.assertIn("zoom_disable_aa = true", inputs)
        self.assertIn("zoom_rigid = true", inputs)
        self.assertIn("zoom_detached_camera = false", inputs)
        shortcuts = (ROOT / "config/hypr/SHORTCUTS.txt").read_text()
        self.assertIn("Super + Plus / Minus", shortcuts)


if __name__ == "__main__":
    unittest.main()
