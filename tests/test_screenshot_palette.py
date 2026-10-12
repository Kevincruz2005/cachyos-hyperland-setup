# SPDX-License-Identifier: MIT
"""Pure palette-loading tests: no capture, renderer, clipboard or subprocess."""
import ast
import json
import os
from pathlib import Path
import re
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/hypr-screenshot").read_text()
node = next(n for n in ast.parse(SOURCE).body
            if isinstance(n, ast.FunctionDef) and n.name == "load_screenshot_palette")
scope = {"json": json, "os": os, "re": re}
exec(compile(ast.Module(body=[node], type_ignores=[]), "palette-test", "exec"), scope)
load_palette = scope["load_screenshot_palette"]


class ScreenshotPalette(unittest.TestCase):
    def test_missing_palette_has_neutral_fallback(self):
        with tempfile.TemporaryDirectory() as root:
            palette = load_palette(Path(root) / "absent.json")
        self.assertEqual(palette["primary"], "#dddddd")
        self.assertEqual(palette["on_surface"], "#eeeeee")

    def test_valid_generated_palette_is_used(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "palette.json"
            values = load_palette(Path(root) / "absent")
            values["primary"] = "#abcdef"
            file.write_text(json.dumps(values))
            self.assertEqual(load_palette(file), values)

    def test_invalid_incomplete_and_oversized_palettes_fall_back(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "palette.json"
            neutral = load_palette(Path(root) / "absent")
            payloads = ("{", "[]", "x" * 8193,
                        json.dumps({"primary": "#123456"}),
                        json.dumps({**neutral, "primary": "#ffffff; bad-css"}))
            for payload in payloads:
                file.write_text(payload)
                self.assertEqual(load_palette(file), neutral)

    def test_next_invocation_reads_changed_palette_without_a_watcher(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "palette.json"
            values = load_palette(Path(root) / "absent")
            file.write_text(json.dumps(values))
            self.assertEqual(load_palette(file)["primary"], "#dddddd")
            values["primary"] = "#abcdef"
            file.write_text(json.dumps(values))
            self.assertEqual(load_palette(file)["primary"], "#abcdef")

    def test_xdg_configuration_directory_is_respected(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "noctalia/palette.json"
            file.parent.mkdir()
            values = load_palette(Path(root) / "absent")
            values["primary"] = "#123456"
            file.write_text(json.dumps(values))
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": root}):
                self.assertEqual(load_palette()["primary"], "#123456")

    def test_native_template_matches_palette_roles(self):
        template = json.loads((ROOT / "config/noctalia/templates/desktop-palette.json").read_text())
        neutral = load_palette("/nonexistent-palette-fixture.json")
        self.assertEqual(set(template), set(neutral))
        for role, token in template.items():
            self.assertEqual(token, "{{ colors." + role + ".default.hex }}")
        config = tomllib.loads((ROOT / "config/noctalia/config.toml").read_text())
        self.assertEqual(config["theme"]["wallpaper_scheme"], "faithful")
        self.assertIn("hyprland", config["theme"]["templates"]["builtin_ids"])
        self.assertIn("desktop_palette", config["theme"]["templates"]["user"])

    def test_fixed_blue_overlay_colors_are_removed(self):
        for color in ("#7aa2f7", "#c0caf5", "#3d59a1", "0.48, 0.64, 0.97"):
            self.assertNotIn(color, SOURCE)
        self.assertIn('self.paint_color(cr, "primary")', SOURCE)


if __name__ == "__main__":
    unittest.main()
