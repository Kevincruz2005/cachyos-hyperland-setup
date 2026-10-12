# SPDX-License-Identifier: MIT
"""Regression checks; never open or change a live window."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WindowRules(unittest.TestCase):
    def test_dolphin_not_forced_to_float(self):
        rules = (ROOT / "config/hypr/config/windowrules.lua").read_text()
        self.assertNotIn("org\\\\.kde\\\\.dolphin", rules)
        self.assertNotIn("cursor_x - (window_w*0.50)", rules)
        self.assertIn("-- Float Common Modals", rules)
        self.assertIn('initial_title = "^(Open File)$"', rules)
        self.assertIn('for _, m in ipairs(modalMatches) do hl.window_rule({ match = m, float = true }) end', rules)


if __name__ == "__main__":
    unittest.main()
