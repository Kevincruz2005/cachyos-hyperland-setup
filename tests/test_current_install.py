# SPDX-License-Identifier: MIT
"""Current desktop and opt-in login transforms; no real login or package writes."""
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import installer
import login
from test_safety import host


def current_host():
    value = host()
    value['packages'].update(hyprland='0.57.1-1.1', noctalia='5.4.1-1.1', uwsm='0.27.1-1')
    return value


class CurrentInstall(unittest.TestCase):
    def test_current_supported_but_mixed_stack_refused(self):
        value = current_host()
        self.assertEqual(installer.blockers(value, {}), [])
        value['packages']['uwsm'] = '0.27.0-1'
        self.assertTrue(any('combination' in issue for issue in installer.blockers(value, {})))
        value['packages']['noctalia'] = '5.5.0-1'
        self.assertTrue(installer.blockers(value, {}))

    def test_current_render_has_switcher_and_simple_launcher(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rendered = installer.render(home, current_host(), home / 'wallpaper.png')
        state = tomllib.loads(rendered['.local/state/noctalia/settings.toml'].decode())
        self.assertEqual(state['shell']['window_switcher'], {'mru': True, 'style': 'compact'})
        self.assertEqual(state['shell']['launcher']['layout'], 'simple')
        self.assertEqual(state['config_version'], 16)
        binds = rendered['.config/hypr/config/binds.lua'].decode()
        self.assertEqual(binds.count('"window-switcher hold"'), 1)
        self.assertNotIn('hold reverse', binds)
        self.assertIn('next = false', binds)
        self.assertIn(b'mousepad --disable-server', rendered['.config/hypr/config/variables.lua'])
        self.assertFalse(state['shell']['greeter_sync']['auto_sync'])
        self.assertNotIn('pam_gnome_keyring', str(rendered))

    def test_file_dialog_rules_are_scoped(self):
        source = (ROOT / 'config/hypr/config/windowrules.lua').read_text()
        block = source.split('-- Bound file dialogs', 1)[1].split('-- Floating Kitty', 1)[0]
        self.assertIn('Save As', block)
        self.assertIn('float = true', block)
        self.assertIn('center = true', block)
        self.assertIn('persistent_size = false', block)
        self.assertIn('monitor_h*0.80', block)
        self.assertNotIn('org.kde.dolphin', block)

    def test_codec_is_explicit_dependency_and_old_editor_not_required(self):
        core = installer.MANIFEST['core']
        self.assertIn('gst-plugins-base', core)
        self.assertIn('mousepad', core)
        self.assertNotIn('gnome-text-editor', core)
        self.assertNotIn('gnome-keyring', core)
        self.assertNotIn('greetd', core)

    def test_lock_geometry_is_derived_from_target(self):
        value = current_host()
        value['display'] = {'output': 'eDP-7', 'mode': '2560x1600@60.00', 'scale': 2.0}
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rendered = installer.render(home, value, home / 'wallpaper.png')
        state = tomllib.loads(rendered['.local/state/noctalia/settings.toml'].decode())
        widgets = state['lockscreen_widgets']
        self.assertTrue(widgets['enabled'])
        self.assertNotIn('eDP-1', str(widgets))
        for item in widgets['widget'].values():
            self.assertEqual(item['output'], 'eDP-7')
            self.assertEqual(item['placement_width'], 1280)
            self.assertEqual(item['placement_height'], 800)
            self.assertLessEqual(item['cx'], 1280)
            self.assertLessEqual(item['cy'], 800)

    def test_optin_keyring_changes_only_existing_argv_and_is_reversible(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home'; home.mkdir()
            argv = home / '.cursor/argv.json'; argv.parent.mkdir()
            original = '// comment\n{\n "password-store": "kwallet6",\n "other": true,\n}\n'
            argv.write_text(original)
            baseline = installer.render(home, current_host(), home / 'wallpaper.png')
            self.assertNotIn('.cursor/argv.json', baseline)
            rendered = installer.render(home, current_host(), home / 'wallpaper.png', login=True, keyring=True)
            self.assertIn(b'"gnome-libsecret"', rendered['.cursor/argv.json'])
            self.assertIn(b'// comment', rendered['.cursor/argv.json'])
            self.assertNotIn('.vscode/argv.json', rendered)
            self.assertNotIn(b'pam_kwallet_init', rendered['.config/hypr/config/autostart.lua'])
            backup = Path(temp) / 'backup'; backup.mkdir()
            installer.snapshot_and_write(home, {'.cursor/argv.json': rendered['.cursor/argv.json']}, backup)
            installer.rollback(home, backup)
            self.assertEqual(argv.read_text(), original)


class LoginTransforms(unittest.TestCase):
    GREETD_PAM = '#%PAM-1.0\nauth required pam_securetty.so\nauth requisite pam_nologin.so\nauth include system-local-login\naccount include system-local-login\nsession include system-local-login\n'
    PASSWD_PAM = '#%PAM-1.0\nauth include system-auth\naccount include system-auth\npassword include system-auth\n'

    def test_greetd_config_preserves_vt_and_never_adds_autologin(self):
        source = '[terminal]\nvt=2\n[default_session]\ncommand="agreety --cmd /bin/sh"\nuser="greeter"\n'
        result = tomllib.loads(login.greetd_config(source, 'target-user').decode())
        self.assertEqual(result['terminal']['vt'], 2)
        self.assertEqual(set(result), {'terminal', 'default_session'})
        self.assertIn('--session hyprland-uwsm --user target-user', result['default_session']['command'])
        self.assertEqual(result['default_session']['user'], 'greeter')

    def test_custom_login_and_invalid_user_refused(self):
        source = '[terminal]\nvt=1\n[default_session]\ncommand="custom-login"\nuser="greeter"\n'
        with self.assertRaises(RuntimeError): login.greetd_config(source, 'target')
        for extra in ('[initial_session]\ncommand="shell"\nuser="target"\n', '[custom]\nx=1\n'):
            with self.assertRaises(RuntimeError): login.greetd_config(source + extra, 'target')
        with self.assertRaises(RuntimeError): login.greetd_config(source, 'user;bad')

    def test_pam_preserves_all_existing_rules_and_is_idempotent(self):
        for kind, original, number in (('greetd', self.GREETD_PAM, 2), ('passwd', self.PASSWD_PAM, 1)):
            result = login.pam_keyring(original, kind).decode()
            self.assertEqual(result.count('pam_gnome_keyring.so'), number)
            self.assertEqual(''.join(line for line in result.splitlines(keepends=True) if 'pam_gnome_keyring.so' not in line), original)
            self.assertEqual(login.pam_keyring(result, kind).decode(), result)
            for line in result.splitlines():
                if 'pam_gnome_keyring' in line: self.assertIn('optional', line)
        self.assertIn('use_authtok', login.pam_keyring(self.PASSWD_PAM, 'passwd').decode())

    def test_unknown_or_conflicting_pam_refused(self):
        for source in ('auth include other-stack\n', self.GREETD_PAM + 'auth required pam_gnome_keyring.so\n',
                       'auth [success=1 default=ignore] pam_custom.so\n' + self.GREETD_PAM):
            with self.assertRaises(RuntimeError): login.pam_keyring(source, 'greetd')

    def test_editor_jsonc_preserves_comments_nested_values_and_trailing_commas(self):
        for original in ('{}', '{/* note */}', '// header\n{\n "x": "https://example.test/",\n}',
                         '{"nested":{"password-store":"keep"},"password-store":"kwallet6"}'):
            result = login.editor_argv(original).decode()
            self.assertIn('"gnome-libsecret"', result)
            self.assertEqual(login.editor_argv(result).decode(), result)
            if 'nested' in original: self.assertIn('"password-store":"keep"', result)
            if 'header' in original: self.assertTrue(result.startswith('// header'))

    def test_invalid_argv_fails_closed(self):
        for source in ('[]', '{broken', '{/*', '{"password-store":"x","password-store":"y"}', '{"password-store":{}}'):
            with self.assertRaises((RuntimeError, ValueError)):
                login.editor_argv(source)


if __name__ == '__main__':
    unittest.main()
