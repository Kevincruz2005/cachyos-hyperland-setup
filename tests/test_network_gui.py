# SPDX-License-Identifier: MIT
"""Optional wired-profile editor action is portable and has no idle worker."""
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import installer
from test_safety import host


class NetworkGui(unittest.TestCase):
    def test_action_requires_both_installed_kde_components(self):
        with tempfile.TemporaryDirectory() as path:
            home = Path(path)
            for present in ((), ("plasma-nm",), ("systemsettings",),
                            ("plasma-nm", "systemsettings")):
                target = host()
                target["packages"].update({name: "installed" for name in present})
                payload = installer.render(home, target, home / "wallpaper.png")
                config = tomllib.loads(payload[".config/noctalia/config.toml"].decode())
                actions = config["widget"]["network"].get("actions", {})
                if len(present) == 2:
                    self.assertEqual(actions, {"right": "exec systemsettings kcm_networkmanagement"})
                else:
                    self.assertEqual(actions, {})
                self.assertNotIn("Wired connection 1", str(payload))
                self.assertNotIn("Static Ethernet", str(payload))

    def test_action_is_on_demand_and_leaves_left_click_unset(self):
        target = host()
        target["packages"].update({"systemsettings": "installed", "plasma-nm": "installed"})
        with tempfile.TemporaryDirectory() as path:
            home = Path(path)
            payload = installer.render(home, target, home / "wallpaper.png")
        config = tomllib.loads(payload[".config/noctalia/config.toml"].decode())
        self.assertNotIn("left", config["widget"]["network"]["actions"])
        self.assertNotIn("Home", payload[".config/noctalia/config.toml"].decode())


if __name__ == "__main__":
    unittest.main()
