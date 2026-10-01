# SPDX-License-Identifier: MIT
"""Small desktop appearance preference merge with hash-like value rollback gates."""
import json
import os
from pathlib import Path
import tempfile
from detect import run

SCHEMA = "org.gnome.desktop.interface"
VALUES = {"color-scheme": "'prefer-dark'", "gtk-theme": "'adw-gtk3-dark'", "icon-theme": "'breeze'", "font-name": "'Noto Sans 10'"}


def save(path, data):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".preferences-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, indent=2)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def apply_preferences(backup):
    record = []
    for key, value in VALUES.items():
        code, current = run(["gsettings", "get", SCHEMA, key])
        if code:
            raise RuntimeError("GTK preference schema/session unavailable; agent adaptation needed.")
        record.append({"key": key, "before": current, "after": value})
    path = backup / "preferences.json"
    if path.exists():
        raise RuntimeError("Preference backup already exists; do not overwrite originals.")
    save(path, record)
    for item in record:
        if item["before"] != item["after"]:
            code, _ = run(["gsettings", "set", SCHEMA, item["key"], item["after"]])
            if code or run(["gsettings", "get", SCHEMA, item["key"]]) != (0, item["after"]):
                raise RuntimeError("Preference change did not verify; receipt retained for rollback.")


def restore_preferences(backup, check_only=False):
    path = backup / "preferences.json"
    if not path.exists():
        return
    record = json.loads(path.read_text())
    for item in record:
        if item["key"] not in VALUES or item["after"] != VALUES[item["key"]]:
            raise RuntimeError("Invalid preference receipt.")
        code, current = run(["gsettings", "get", SCHEMA, item["key"]])
        if code or current not in (item["before"], item["after"]):
            raise RuntimeError("Appearance preference changed after setup; preserve it for manual recovery.")
    if check_only:
        return
    for item in record:
        if run(["gsettings", "set", SCHEMA, item["key"], item["before"]])[0]:
            raise RuntimeError("Preference restore failed; receipt/originals retained.")
