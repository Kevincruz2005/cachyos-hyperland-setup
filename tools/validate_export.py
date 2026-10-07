#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline config parsing in a disposable directory; never launch a desktop."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from installer import render, snapshot_and_write


def main():
    if not all(shutil.which(name) for name in ("Hyprland", "noctalia")):
        print("SKIP: installed Hyprland/Noctalia binaries are needed for native schema validation.")
        return 0
    with tempfile.TemporaryDirectory(prefix="desktop-export-validation-") as name:
        base = Path(name)
        home, backup = base / "isolated-home", base / "backup"
        home.mkdir()
        backup.mkdir()
        host = {"display": {"output": "eDP-7", "mode": "2560x1600@60.00", "scale": "auto"}}
        snapshot_and_write(home, render(home, host, base / "wallpaper.png", sddm=True), backup)
        env = {**os.environ, "HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
               "XDG_STATE_HOME": str(home / ".local/state"), "XDG_DATA_HOME": str(home / ".local/share"),
               "XDG_CACHE_HOME": str(base / "cache")}
        commands = [
            ["Hyprland", "--verify-config", "--config", str(home / ".config/hypr/hyprland.lua")],
            ["noctalia", "config", "validate", str(home / ".config/noctalia")],
            ["noctalia", "config", "validate", str(home / ".local/state/noctalia/settings.toml")],
            ["noctalia", "config", "validate", str(ROOT / "profiles/lockscreen-reference.toml")],
        ]
        for command in commands:
            result = subprocess.run(command, cwd=home / ".config/hypr", env=env, capture_output=True, text=True, timeout=30)
            print("$ " + " ".join(command[:3]))
            print((result.stdout + result.stderr).strip())
            if result.returncode:
                return result.returncode
    print("Native offline config validation passed. No live reload, UI, microphone or compositor started.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
