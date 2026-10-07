# SPDX-License-Identifier: MIT
"""Reference profile invariants; no live lock, UI or configuration writes."""
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = tomllib.loads((ROOT / 'profiles/lockscreen-reference.toml').read_text())

class LockscreenProfile(unittest.TestCase):
    def test_visual_scope_preserves_authentication(self):
        self.assertEqual(set(PROFILE), {'lockscreen', 'lockscreen_widgets'})
        self.assertEqual(set(PROFILE['lockscreen']), {'wallpaper', 'tint_intensity'})
        self.assertEqual(PROFILE['lockscreen']['wallpaper'], '')

    def test_static_palette_role_clocks(self):
        clocks = [w for w in PROFILE['lockscreen_widgets']['widget'].values() if w['type'] == 'clock']
        self.assertEqual(len(clocks), 2)
        for clock in clocks:
            settings = clock['settings']
            self.assertEqual(settings['clock_style'], 'digital')
            self.assertFalse(settings['background'])
            self.assertFalse(settings['shadow'])
            self.assertIn(settings['color'], ('primary', 'on_surface_variant'))
            for seconds in ('%S', '%T', '%X'):
                self.assertNotIn(seconds, settings['format'])

    def test_native_login_controls_remain(self):
        widgets = PROFILE['lockscreen_widgets']['widget']
        self.assertEqual(len(widgets), 3)
        login = [w for w in widgets.values() if w['type'] == 'login_box']
        self.assertEqual(len(login), 1)
        self.assertTrue(login[0]['enabled'])
        settings = login[0]['settings']
        for key in ('show_login_button', 'show_unlock_hint', 'show_caps_lock', 'show_keyboard_layout'):
            self.assertTrue(settings[key])
        for key in ('show_media', 'show_weather', 'show_session_buttons'):
            self.assertFalse(settings[key])

if __name__ == '__main__':
    unittest.main()
