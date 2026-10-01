# SPDX-License-Identifier: MIT
import ast
import configparser
import datetime
import hashlib
import json
from math import ceil, floor
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import detect
import installer
import privileged
import toml_state


def host():
    return {"os": "cachyos", "architecture": "x86_64", "package_health": True, "pending_updates": [],
            "packages": {"hyprland": "0.56.2-1", "noctalia": "5.2.0-1", "uwsm": "0.27.0-1"},
            "services": {"power-profiles-daemon": "active"}, "gpus": [],
            "display": {"output": "eDP-7", "mode": "2560x1600@60.00", "scale": "auto"}}


class Deployment(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / "other-user"
        self.home.mkdir()
        self.backup = self.base / "private-backup"
        self.backup.mkdir(mode=0o700)

    def tearDown(self):
        self.temp.cleanup()

    def test_idempotent_and_rollback(self):
        target = self.home / ".config/sample"
        target.parent.mkdir()
        target.write_text("original")
        target.chmod(0o600)
        data = {".config/sample": b"new", ".config/created": b"only here"}
        receipt = installer.snapshot_and_write(self.home, data, self.backup)
        self.assertTrue(receipt["complete"])
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        second = self.base / "second"
        second.mkdir()
        self.assertEqual(installer.snapshot_and_write(self.home, data, second)["records"], [])
        installer.rollback(self.home, self.backup)
        self.assertEqual(target.read_text(), "original")
        self.assertFalse((self.home / ".config/created").exists())
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.backup / "files/.config/sample").read_text(), "original")

    def test_rollback_rejects_later_edit_before_any_changes(self):
        data = {"a": b"first", "b": b"second"}
        installer.snapshot_and_write(self.home, data, self.backup)
        (self.home / "b").write_text("later edit")
        with self.assertRaises(RuntimeError):
            installer.rollback(self.home, self.backup)
        self.assertTrue((self.home / "a").exists())

    def test_rollback_detects_corrupt_original(self):
        (self.home / "a").write_text("original")
        installer.snapshot_and_write(self.home, {"a": b"new"}, self.backup)
        (self.backup / "files/a").write_text("corrupted")
        with self.assertRaises(RuntimeError):
            installer.rollback(self.home, self.backup)
        self.assertEqual((self.home / "a").read_text(), "new")

    def test_symlink_leaf_restored_without_following(self):
        outside = self.base / "outside"
        outside.write_text("not overwritten")
        (self.home / "a").symlink_to(outside)
        installer.snapshot_and_write(self.home, {"a": b"new"}, self.backup)
        self.assertEqual(outside.read_text(), "not overwritten")
        installer.rollback(self.home, self.backup)
        self.assertTrue((self.home / "a").is_symlink())

    def test_symlink_parent_blocks_all_changes(self):
        (self.home / "link").symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            installer.snapshot_and_write(self.home, {"good": b"no", "link/bad": b"no"}, self.backup)
        self.assertFalse((self.home / "good").exists())

    def test_path_traversal_rejected(self):
        for name in ("../escape", "/tmp/escape", "a/../../escape"):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                installer.checked_target(self.home, name)

    def test_partial_apply_has_usable_receipt(self):
        original = installer.os.replace
        def failing(source, destination):
            if Path(destination).name == "b":
                raise OSError("simulated interruption")
            return original(source, destination)
        with patch.object(installer.os, "replace", side_effect=failing), self.assertRaises(OSError):
            installer.snapshot_and_write(self.home, {"a": b"one", "b": b"two"}, self.backup)
        self.assertFalse(json.loads((self.backup / "receipt.json").read_text())["complete"])
        installer.rollback(self.home, self.backup)
        self.assertFalse((self.home / "a").exists())

    def test_ini_preserves_unrelated_preferences(self):
        target = self.home / "preferences"
        target.write_text("[Identity]\nAccount=target-only\n[UiSettings]\nColorScheme=Old\n")
        result = installer.ini_merge(target, {"UiSettings": {"ColorScheme": "noctalia"}})
        parser = configparser.ConfigParser()
        parser.read_string(result.decode())
        self.assertEqual(parser["Identity"]["Account"], "target-only")

    def test_render_is_portable_and_preserves_state(self):
        state = self.home / ".local/state/noctalia/settings.toml"
        state.parent.mkdir(parents=True)
        state.write_text('[target_private]\npreference="keep-local"\n[theme]\nmode="light"\n')
        result = installer.render(self.home, host(), self.home / "wallpaper.png")
        rendered = tomllib.loads(result[".local/state/noctalia/settings.toml"].decode())
        self.assertEqual(rendered["target_private"]["preference"], "keep-local")
        self.assertEqual(rendered["theme"]["mode"], "dark")
        self.assertIn(b"eDP-7", result[".config/hypr/config/host.lua"])
        self.assertNotIn(b"0000:00:02.0", b"\n".join(result.values()))
        self.assertFalse((self.home / ".config").exists())


class Detection(unittest.TestCase):
    def test_non_dell_output_and_60hz(self):
        panel = {"name": "eDP-8", "modes": [{"width": 2560, "height": 1600, "hz": 165}, {"width": 2560, "height": 1600, "hz": 60.01}]}
        result = detect.choose_display([panel])
        self.assertEqual(result["output"], "eDP-8")
        self.assertEqual(result["mode"], "2560x1600@60.01")
        self.assertEqual(result["scale"], "auto")

    def test_no_invented_60hz(self):
        result = detect.choose_display([{"name": "DSI-3", "modes": [{"width": 1920, "height": 1200, "hz": 90}]}])
        self.assertFalse(result["verified_60hz"])
        self.assertIn("@90", result["mode"])

    def test_no_display_uses_preferred(self):
        self.assertEqual(detect.choose_display([])["mode"], "preferred")

    def test_disconnected_panel_not_chosen(self):
        result = detect.choose_display([{"name": "eDP-1", "connected": False}, {"name": "DP-9", "modes": []}])
        self.assertEqual(result["output"], "DP-9")

    def test_malformed_edid(self):
        for data in (b"", bytes(128), b"\0\xff\xff\xff\xff\xff\xff\0" + bytes(122)):
            self.assertEqual(detect.edid_modes(data), [])

    def test_epoch_version(self):
        self.assertEqual(detect.version("2:0.56.2-3"), "0.56.2")

    def test_host_gates(self):
        self.assertEqual(installer.blockers(host(), {}), [])
        for field, value in (("os", "ubuntu"), ("architecture", "aarch64"), ("package_health", False), ("pending_updates", ["one"])):
            changed = host()
            changed[field] = value
            self.assertTrue(installer.blockers(changed, {}))

    def test_version_gate_no_downgrade(self):
        value = host()
        value["packages"]["hyprland"] = "0.57.0-1"
        self.assertTrue(installer.blockers(value, {}))

    def test_conflicting_power_stack(self):
        value = host()
        value["services"]["tlp"] = "active"
        self.assertTrue(installer.blockers(value, {}))

    def test_missing_nvidia_driver(self):
        value = host()
        value["gpus"] = [{"vendor": "0x10de", "driver": ""}]
        self.assertTrue(installer.blockers(value, {}))

    def test_lua_injection_rejected(self):
        value = host()["display"]
        value["output"] = 'eDP-1";exec()'
        with self.assertRaises(RuntimeError):
            installer.lua_host(value)


class PackageGuards(unittest.TestCase):
    def test_protected_packages_rejected(self):
        for name in ("linux-cachyos", "nvidia-open", "grub", "plymouth", "systemd", "efibootmgr", "mkinitcpio"):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                privileged.reject_transaction({}, [[name, "1-1"]])

    def test_prime_helper_allowed(self):
        privileged.reject_transaction({}, [["nvidia-prime", "1.0-1"]])

    def test_existing_package_changes_rejected(self):
        with self.assertRaises(RuntimeError):
            privileged.reject_transaction({"dolphin": "1-1"}, [["dolphin", "2-1"]])

    def test_duplicate_transaction_rejected(self):
        with self.assertRaises(RuntimeError):
            privileged.reject_transaction({}, [["dolphin", "1-1"], ["dolphin", "1-1"]])

    def test_hook_review(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "grub.hook"
            path.write_text("[Trigger]\nType=File\nTarget=usr/lib/modules/*/vmlinuz\n[Action]\nExec=/usr/bin/grub-mkconfig -o /boot/grub/grub.cfg\n")
            self.assertEqual(privileged.review_hooks([path], ["usr/share/font.ttf"], [["font", "1"]]), [])
            with self.assertRaises(RuntimeError):
                privileged.review_hooks([path], ["usr/lib/modules/test/vmlinuz"], [["font", "1"]])

    def test_unknown_matching_hook_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "custom.hook"
            path.write_text("[Trigger]\nType=Package\nTarget=*\n[Action]\nExec=/usr/bin/sh -c something\n")
            with self.assertRaises(RuntimeError):
                privileged.review_hooks([path], [], [["app", "1"]])

    def test_snapshot_opt_in(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "05-snap-pac-pre.hook"
            path.write_text("anything")
            with self.assertRaises(RuntimeError):
                privileged.review_hooks([path], [], [])
            self.assertEqual(privileged.review_hooks([path], [], [], True), [path.name])

    def test_benign_cache_hook_allowed(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "font.hook"
            path.write_text("[Trigger]\nType=File\nTarget=usr/share/fonts/*\n[Action]\nExec=/usr/bin/fc-cache -s\n")
            self.assertEqual(privileged.review_hooks([path], ["usr/share/fonts/a.ttf"], [["font", "1"]]), [])


class DataFormats(unittest.TestCase):
    def test_toml_roundtrip(self):
        value = {"a": "Tamil தமிழ்\nquoted \"", "date": datetime.date(2026, 10, 1), "flag": False,
                 "nested": {"items": [{"type": "a", "n": 3}, {"type": "b", "n": 4}], "list": [1, 2.5, True]}}
        self.assertEqual(tomllib.loads(toml_state.dump(value).decode()), value)

    def test_all_toml_parses(self):
        for path in (ROOT / "config").rglob("*.toml"):
            with self.subTest(path=path):
                tomllib.loads(path.read_text())

    def test_no_gpu_force_in_environment(self):
        data = (ROOT / "config/uwsm/env-hyprland").read_text()
        for key in ("GBM_BACKEND", "__GLX_VENDOR_LIBRARY_NAME", "AQ_DRM_DEVICES", "WLR_DRM_DEVICES"):
            self.assertNotIn(key, data)

    def test_efficiency_schema(self):
        data = tomllib.loads((ROOT / "config/noctalia/config.toml").read_text())
        self.assertFalse(data["system"]["monitor"]["enabled"])
        self.assertTrue(all(value == 0 for key, value in data["system"]["monitor"].items() if "poll" in key))
        for key in ("dock", "weather", "calendar", "desktop_widgets"):
            self.assertFalse(data[key]["enabled"])


class ScreenshotCoordinates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse((ROOT / "tools/hypr-screenshot").read_text())
        node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "logical_to_image_rect")
        scope = {"floor": floor, "ceil": ceil}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "coordinates", "exec"), scope)
        cls.convert = staticmethod(scope[node.name])

    def test_all_scales_all_corners(self):
        for scale in (1, 1.25, 1.5, 2):
            w, h = 1920 / scale, 1080 / scale
            self.assertEqual(self.convert(0, 0, w, h, 1920, 1080, w, h), (0, 0, 1920, 1080))
            self.assertEqual(self.convert(w-100, h-80, 100, 80, 1920, 1080, w, h),
                             (int(1920-100*scale), int(1080-80*scale), int(100*scale), int(80*scale)))

    def test_bounds_clamped(self):
        self.assertEqual(self.convert(-20, -10, 1000, 1000, 100, 100, 100, 100), (0, 0, 100, 100))

    def test_zero_view_safe(self):
        self.assertEqual(self.convert(0, 0, 0, 0, 100, 100, 0, 0), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
