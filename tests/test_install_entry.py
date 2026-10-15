# SPDX-License-Identifier: MIT
"""Exercise the shell entry point against a fake setup in an isolated directory."""
import os
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
        env = {**os.environ, "TEST_SETUP_LOG": str(self.log)}
        if fail_plan:
            env["TEST_FAIL_PLAN"] = "1"
        return subprocess.run(["bash", str(self.directory / "install.sh"), *args],
                              cwd=self.directory, env=env, capture_output=True, text=True)

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
        self.assertEqual(self.log.read_text().splitlines(), ["audit", "plan"])

    def test_rejects_unreviewed_flags_before_audit(self):
        result = self.run_entry("--select-sddm")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())

    def test_shell_syntax(self):
        result = subprocess.run(["bash", "-n", str(ROOT / "install.sh")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
