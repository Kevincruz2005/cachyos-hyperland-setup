# SPDX-License-Identifier: MIT
"""Exercise the shell entry point against a fake setup in an isolated directory."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GuidedEntry(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        # The entrypoint checks prerequisites before invoking our fake setup.
        # Make those checks independent of the host (e.g. Ubuntu CI has no pacman).
        # Only the shell/path utility are real; prerequisite stubs fail if called.
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        for name in ("bash", "dirname"):
            executable = shutil.which(name)
            self.assertIsNotNone(executable, "Test harness needs " + name)
            (self.bin / name).symlink_to(executable)
        self.prerequisites = ("python", "pacman", "sudo", "file")
        for name in self.prerequisites:
            executable = self.bin / name
            executable.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' 'Unexpected execution of a prerequisite stub' >&2\n"
                "exit 97\n"
            )
            executable.chmod(0o755)
        shutil.copy2(ROOT / "install.sh", self.directory / "install.sh")
        setup = self.directory / "setup"
        setup.write_text(
            "#!/usr/bin/env bash\n"
            "printf '%s\\n' \"$*\" >> \"$TEST_SETUP_LOG\"\n"
            "if [[ $1 == plan && ${TEST_FAIL_PLAN:-0} == 1 ]]; then exit 3; fi\n"
        )
        setup.chmod(0o755)
        self.log = self.directory / "setup.log"

    def run_entry(self, *args, fail_plan=False):
        # Inherit neither the host PATH nor shell startup/functions/failure flags.
        env = {"PATH": str(self.bin), "TEST_SETUP_LOG": str(self.log), "LC_ALL": "C"}
        if fail_plan:
            env["TEST_FAIL_PLAN"] = "1"
        return subprocess.run(["bash", str(self.directory / "install.sh"), *args],
                              cwd=self.directory, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True)

    def test_guided_audit_plan_apply(self):
        result = self.run_entry("--wallpaper", "/tmp/test-wallpaper.png")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), [
            "audit",
            "plan --wallpaper /tmp/test-wallpaper.png",
            "apply --packages --download-model --wallpaper /tmp/test-wallpaper.png",
        ])

    def test_plan_failure_never_applies(self):
        result = self.run_entry(fail_plan=True)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(self.log.exists(), result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), ["audit", "plan"])

    def test_missing_prerequisites_stop_before_audit(self):
        for name in self.prerequisites:
            with self.subTest(prerequisite=name):
                executable = self.bin / name
                executable.rename(self.bin / (name + ".unavailable"))
                try:
                    result = self.run_entry()
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("Missing prerequisite: " + name + ".", result.stderr)
                    self.assertFalse(self.log.exists())
                finally:
                    (self.bin / (name + ".unavailable")).rename(executable)

    def test_help_works_without_install_prerequisites(self):
        for name in self.prerequisites:
            (self.bin / name).unlink()
        result = self.run_entry('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Usage:', result.stdout)
        self.assertFalse(self.log.exists())

    def test_rejects_unreviewed_flags_before_audit(self):
        result = self.run_entry("--select-sddm")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())

    def test_shell_syntax(self):
        result = subprocess.run(["bash", "-n", str(ROOT / "install.sh")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_explicit_login_and_keyring_remain_in_same_reviewed_flow(self):
        result = self.run_entry('--login', 'noctalia', '--gnome-keyring')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), [
            'audit', 'plan --login noctalia --gnome-keyring',
            'apply --packages --download-model --login noctalia --gnome-keyring'])

    def test_keyring_without_login_is_rejected_before_audit(self):
        result = self.run_entry('--login', 'keep', '--gnome-keyring')
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())

    def test_help_does_not_audit_or_mutate(self):
        result = self.run_entry('--help')
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
