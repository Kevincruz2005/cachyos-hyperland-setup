# SPDX-License-Identifier: MIT
"""Simulate next-boot login staging in a disposable filesystem, never real systemctl."""
import copy
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import privileged
import test_current_install


class LoginStage(unittest.TestCase):
    def exercise(self, *, consent=True, keyring=False, fail_enable=False, custom=False):
        with tempfile.TemporaryDirectory(prefix='login-stage-test-') as temp:
            base = Path(temp)
            tree, backup = base / 'system', base / 'backup'
            backup.mkdir()
            def system_path(*parts):
                p = Path(*parts)
                if str(p).startswith(('/etc/', '/usr/', '/var/lib/')):
                    return tree / p.relative_to('/')
                return p
            fixtures = {
                '/usr/share/wayland-sessions/hyprland-uwsm.desktop': 'session',
                '/usr/share/wayland-sessions/plasma.desktop': 'fallback',
                '/usr/bin/noctalia-greeter-session': 'official-wrapper',
                '/usr/lib/security/pam_gnome_keyring.so': 'module',
                '/etc/greetd/config.toml': '[terminal]\nvt=1\n[default_session]\ncommand="' + ('custom' if custom else 'agreety --cmd /bin/sh') + '"\nuser="greeter"\n',
                '/etc/pam.d/greetd': test_current_install.LoginTransforms.GREETD_PAM,
                '/etc/pam.d/passwd': test_current_install.LoginTransforms.PASSWD_PAM,
                '/etc/pam.d/system-auth': 'auth required pam_unix.so\n',
                '/etc/pam.d/system-login': 'session include system-auth\n',
                '/etc/pam.d/system-local-login': 'auth include system-login\n',
                '/usr/lib/systemd/system/sddm.service': 'fallback',
                '/usr/lib/systemd/system/greetd.service': 'greeter',
            }
            for name, text in fixtures.items():
                path = system_path(name); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
            state = system_path('/var/lib/noctalia-greeter'); state.mkdir(parents=True)
            link = system_path('/etc/systemd/system/display-manager.service'); link.parent.mkdir(parents=True)
            link.symlink_to(system_path('/usr/lib/systemd/system/sddm.service'))
            enabled, commands, written, receipts = {'sddm.service'}, [], [], []
            def command(args, **kwargs):
                commands.append(args)
                self.assertEqual(args[0], 'systemctl')
                self.assertNotIn('--now', args)
                self.assertNotIn(args[1], ('stop', 'restart', 'start'))
                if args[1] == 'disable':
                    enabled.discard(args[-1])
                    if link.exists() and link.resolve().name == args[-1]: link.unlink()
                elif args[1] == 'enable':
                    if fail_enable and args[-1] == 'greetd.service':
                        raise privileged.subprocess.CalledProcessError(1, args)
                    enabled.add(args[-1]); link.unlink(missing_ok=True)
                    link.symlink_to(system_path('/usr/lib/systemd/system/' + args[-1]))
                else:
                    raise AssertionError('Unexpected system operation')
                return SimpleNamespace(returncode=0)
            user = SimpleNamespace(pw_name='target-user', pw_uid=os.getuid(), pw_gid=os.getgid())
            args = SimpleNamespace(confirm_login_change=True, gnome_keyring=keyring)
            with patch.object(privileged, 'Path', side_effect=system_path), \
                 patch.object(privileged, 'packages', return_value={'noctalia':'5.4.1-1', 'noctalia-greeter':'1.7.0-1', 'greetd':'0.10.3-2', 'gnome-keyring':'51.1-1'}), \
                 patch.object(privileged, 'trusted_session_wrapper', return_value=True), \
                 patch.object(privileged.shutil, 'which', return_value='/usr/bin/sddm'), \
                 patch.object(privileged.pwd, 'getpwnam', return_value=user), \
                 patch.object(privileged, 'run', side_effect=lambda args: (0, 'enabled' if args[-1] in enabled else 'disabled')), \
                 patch.object(privileged.subprocess, 'run', side_effect=command), \
                 patch.object(privileged, 'system_receipt', return_value={'files':[], 'directories':[], 'previous_dm':None, 'selected_sddm':False}), \
                 patch.object(privileged, 'save_receipt', side_effect=lambda b,r,u: receipts.append(copy.deepcopy(r))), \
                 patch.object(privileged, 'system_write', side_effect=lambda p,d,*a: written.append((str(p),d))), \
                 patch.object(privileged.sys.stdin, 'isatty', return_value=True), \
                 patch('builtins.input', return_value='ENABLE NOCTALIA LOGIN' if consent else 'no'):
                if not consent or custom or fail_enable:
                    with self.assertRaises((RuntimeError, privileged.subprocess.CalledProcessError)):
                        privileged.login_stage(args, user, base/'home', backup)
                else:
                    privileged.login_stage(args, user, base/'home', backup)
            if not consent or custom:
                self.assertEqual(written, [])
                self.assertEqual(commands, [])
                self.assertEqual(receipts, [])
            elif fail_enable:
                self.assertEqual(enabled, {'sddm.service'})
                self.assertEqual(link.resolve().name, 'sddm.service')
            else:
                self.assertEqual(enabled, {'greetd.service'})
                self.assertEqual(len(written), 3 if keyring else 1)
                self.assertEqual(receipts[-1]['previous_dm'], 'sddm.service')
                self.assertEqual(receipts[-1]['selected_dm'], 'greetd.service')

    def test_default_login_selection_keeps_pam_untouched(self): self.exercise()
    def test_optin_keyring_stages_only_three_known_files(self): self.exercise(keyring=True)
    def test_declined_final_plan_has_no_login_writes(self): self.exercise(consent=False)
    def test_custom_launcher_refused_without_writes(self): self.exercise(custom=True)
    def test_failed_switch_restores_previous_manager(self): self.exercise(fail_enable=True)


if __name__ == '__main__': unittest.main()
