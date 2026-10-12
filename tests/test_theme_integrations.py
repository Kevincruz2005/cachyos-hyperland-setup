# SPDX-License-Identifier: MIT
"""Isolated editor merges and static optional-profile contracts. No live writes."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tools/noctalia-cursor-colors.cjs"
PROFILES = ROOT / "profiles/theme-integrations"
PARSER = Path('/usr/share/cursor/resources/app/node_modules/jsonc-parser/lib/umd/main.js')
HAS_PARSER = PARSER.exists() or Path('/usr/share/code/resources/app/node_modules/jsonc-parser/lib/umd/main.js').exists()


class IntegrationContracts(unittest.TestCase):
    def test_firefox_native_payload_shape(self):
        data = json.loads((PROFILES / 'firefox-colors.json').read_text())
        self.assertEqual(data['wallpaper'], '')  # Never disclose a private image path.
        self.assertEqual(set(data['colors']), {f'color{i}' for i in range(16)})

    def test_opt_in_profiles_not_enabled_by_default(self):
        import tomllib
        config = tomllib.loads((ROOT / 'config/noctalia/config.toml').read_text())
        self.assertNotIn('cursor_palette', config['theme']['templates']['user'])
        self.assertNotIn('firefox_palette', config['theme']['templates']['user'])
        source = HELPER.read_text()
        for token in ('setInterval(', 'setTimeout(', 'fs.watch(', 'child_process'):
            self.assertNotIn(token, source)

    def test_cursor_template_changes_only_ui_colors(self):
        values = json.loads((PROFILES / 'cursor-colors.json').read_text())
        self.assertGreater(len(values), 30)
        self.assertNotIn('editor.tokenColorCustomizations', values)
        self.assertNotIn('password-store', values)
        self.assertNotIn('editor.fontFamily', values)
        for value in values.values():
            self.assertRegex(value, r'^\{\{ colors\.[a-z_]+\.default\.hex \}\}([0-9A-Fa-f]{2})?$')


@unittest.skipUnless(shutil.which('node') and HAS_PARSER, 'Installed editor JSONC parser required')
class CursorMerges(unittest.TestCase):
    def fixture(self, original, colors=None, symlink=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / 'settings.json'
            settings.write_text(original)
            target = settings
            if symlink:
                target = root / 'link.json'
                target.symlink_to(settings)
            palette = root / 'palette.json'
            palette.write_text(json.dumps(colors if colors is not None else {'editor.background': '#123456'}))
            command = ['node', str(HELPER), str(palette), str(target)]
            result = subprocess.run(command, capture_output=True, timeout=5)
            content = settings.read_text()
            modified = settings.stat().st_mtime_ns
            if result.returncode == 0:
                repeat = subprocess.run(command, capture_output=True, timeout=5)
                self.assertEqual(repeat.returncode, 0)
                self.assertEqual(settings.stat().st_mtime_ns, modified, 'Unchanged colors should not rewrite settings')
            self.assertFalse(list(root.glob('.noctalia-colors-*')))
            return result.returncode, content

    def test_comments_preferences_and_existing_colors_preserved(self):
        original = '// Keep this comment\n{\n "editor.fontSize": 13,\n "window.autoDetectColorScheme": true,\n "workbench.colorCustomizations": {"errorForeground": "#ff1234"},\n}\n'
        code, result = self.fixture(original)
        self.assertEqual(code, 0)
        for value in ('Keep this comment', '"editor.fontSize": 13', '"window.autoDetectColorScheme": true', '"errorForeground": "#ff1234"'):
            self.assertIn(value, result)
        self.assertIn('#123456', result)

    def test_rejected_inputs_leave_settings_unchanged(self):
        for original in ('{', '[]', '{"x":1,"x":2}', '{"workbench.colorCustomizations":null}', '{"workbench.colorCustomizations":{"[Dark]":{}}}', '{"workbench.colorCustomizations":{"x":"#123456","x":"#654321"}}'):
            code, result = self.fixture(original)
            self.assertNotEqual(code, 0)
            self.assertEqual(result, original)

    def test_bad_palette_and_symlink_rejected(self):
        original = '{"editor.fontSize":13}'
        for colors in ([], {}, {'editor.background': '#123456;bad'}, {'password-store': '#123456'}):
            code, result = self.fixture(original, colors)
            self.assertNotEqual(code, 0)
            self.assertEqual(result, original)
        code, result = self.fixture(original, symlink=True)
        self.assertNotEqual(code, 0)
        self.assertEqual(result, original)


if __name__ == '__main__':
    unittest.main()
