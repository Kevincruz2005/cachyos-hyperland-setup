# SPDX-License-Identifier: MIT
"""Version-specific switcher export stays opt-in and does not change window size."""
from pathlib import Path
import json
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AltTabProfile(unittest.TestCase):
    def test_native_bindings_only_without_fullscreen_or_workers(self):
        source = (ROOT / 'profiles/window-switcher/binds.lua.example').read_text()
        bindings = [line for line in source.splitlines() if line.startswith('hl.bind(')]
        self.assertEqual(len(bindings), 3)
        self.assertIn('hl.bind("ALT + Tab",         hl.dsp.exec_cmd(noctCall .. "window-switcher hold"))', bindings)
        self.assertIn('hl.bind("ALT + SHIFT + Tab", hl.dsp.window.cycle_next({ next = false }))', bindings)
        self.assertIn('hl.bind(mainMod .. " + Tab",   hl.dsp.exec_cmd(noctCall .. "window-switcher"))', bindings)
        for unsupported in ('fullscreen', 'systemd-run', 'sleep ', 'while ', 'hold reverse'):
            self.assertFalse(any(unsupported in line for line in bindings))

    def test_only_two_switcher_preferences(self):
        source = (ROOT / 'profiles/window-switcher/noctalia.toml.example').read_text()
        self.assertEqual(tomllib.loads(source), {'shell': {'window_switcher': {'style': 'compact', 'mru': True}}})

    def test_generic_installer_baseline_unchanged(self):
        source = (ROOT / 'config/hypr/config/binds.lua').read_text()
        self.assertIn('hl.bind("ALT + Tab",         hl.dsp.window.cycle_next({ next = true }))', source)
        self.assertNotIn('window-switcher hold', source)
        config = tomllib.loads((ROOT / 'config/noctalia/config.toml').read_text())
        self.assertNotIn('window_switcher', config['shell'])
        versions = json.loads((ROOT / 'packages.json').read_text())['tested_versions']
        self.assertNotIn('5.4.1', versions['noctalia'])
        self.assertNotIn('0.57.1', versions['hyprland'])

    def test_documents_limitations_and_private_recovery(self):
        source = (ROOT / 'docs/ALT_TAB.md').read_text()
        for phrase in ('optional reference profile', 'closed', 'later edits',
                       'manual tests', 'not exported', 'No energy measurements'):
            self.assertIn(phrase, source)


if __name__ == '__main__':
    unittest.main()
