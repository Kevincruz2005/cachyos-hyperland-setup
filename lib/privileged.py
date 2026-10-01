#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Narrow, explicitly requested privileged stages. Never restart a session."""
import argparse
import configparser
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

from detect import packages, run
from installer import ROOT, BREEZE_SHA, digest, private_json, stamp

SNAPSHOT_HOOKS = {"05-snap-pac-pre.hook", "10-snap-pac-removal.hook", "zz-snap-pac-post.hook"}
DM_UNITS = ("sddm.service", "plasmalogin.service", "gdm.service", "lightdm.service", "greetd.service", "lxdm.service")
ALLOWED_REPLACEMENT = "cachyos-kde-settings"
BAD_PACKAGE = re.compile(r"^(?:linux(?:-|$)|nvidia(?:-|$)|lib32-nvidia|systemd(?:-|$)|grub(?:-|$)|limine(?:-|$)|plymouth(?:-|$)|mkinitcpio(?:-|$)|dracut(?:-|$)|sbctl(?:-|$)|efibootmgr(?:-|$))")


def reject_transaction(before, transaction):
    if len({name for name, _ in transaction}) != len(transaction):
        raise RuntimeError("Duplicate package transaction entry.")
    for name, version in transaction:
        if not re.fullmatch(r"[a-zA-Z0-9@+_.-]+", name) or not version or (BAD_PACKAGE.match(name) and name != "nvidia-prime"):
            raise RuntimeError("Kernel/driver/boot/core package change rejected: " + name)
        if name in before:
            raise RuntimeError("Existing package replacement/upgrade rejected: " + name)


def review_hooks(paths, archives, transaction, allow_snapshot=False):
    """Conservative trigger matching; unknown scripts require an agent, not guessing."""
    overrides = []
    names = {name for name, _ in transaction}
    for path in paths:
        text = path.read_text()
        if path.name in SNAPSHOT_HOOKS:
            if not allow_snapshot:
                raise RuntimeError("Snapshot hook present; separately review --allow-snapshot-hook-override: " + path.name)
            overrides.append(path.name)
            continue
        # Repeated [Trigger] sections are legal; a regex conservatively takes their union.
        targets = re.findall(r"^Target\s*=\s*(.+)$", text, re.M)
        if not targets:
            raise RuntimeError("Hook without understood triggers: " + path.name)
        is_file = bool(re.search(r"^Type\s*=\s*(?:Path|File)\s*$", text, re.M))
        haystack = archives if is_file else names
        positive = [target for target in targets if not target.startswith("!")]
        matches = any(fnmatch.fnmatch(item, target) for item in haystack for target in positive)
        if not matches:
            continue
        commands = re.findall(r"^Exec\s*=\s*(.+)$", text, re.M)
        if len(commands) != 1:
            raise RuntimeError("Unrecognized matching package hook: " + path.name)
        command = commands[0]
        if re.search(r"grub|limine|bootctl|efi|mkinitcpio|dracut|update-initramfs|snapper|timeshift|snapshot", command, re.I):
            raise RuntimeError("Matching boot/snapshot-writing hook rejected: " + path.name)
        # Only the distro's ordinary cache-update commands, no shell, custom scripts or daemon restarts.
        executable = shlex.split(command)[0]
        safe = {
            "/usr/bin/update-desktop-database", "/usr/bin/update-mime-database", "/usr/bin/gtk-update-icon-cache",
            "/usr/bin/fc-cache", "/usr/bin/glib-compile-schemas", "/usr/bin/gio-querymodules",
            "/usr/bin/gtk-query-immodules-3.0", "/usr/bin/gdk-pixbuf-query-loaders", "/usr/bin/ldconfig",
            "/usr/share/libalpm/scripts/gtk-update-icon-cache", "/usr/share/libalpm/scripts/update-desktop-database",
            "/usr/share/libalpm/scripts/glib-compile-schemas", "/usr/share/libalpm/scripts/gio-querymodules",
            "/usr/share/libalpm/scripts/update-mime-database", "/usr/share/libalpm/scripts/gtk4-querymodules",
            "/usr/share/libalpm/scripts/texinfo-install", "/usr/share/libalpm/scripts/man-db-install",
        }
        if executable not in safe:
            raise RuntimeError("Matching hook needs manual source review: " + path.name)
    return overrides


def validate_context(uid, backup):
    if os.geteuid() != 0 or uid <= 0 or str(uid) != os.environ.get("SUDO_UID"):
        raise RuntimeError("Run only through the normal user's sudo stage.")
    user = pwd.getpwuid(uid)
    home = Path(user.pw_dir).resolve()
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_-]*", user.pw_name):
        raise RuntimeError("Unsupported username for SDDM image path.")
    backup = Path(backup)
    if backup.is_symlink() or any(parent.is_symlink() for parent in backup.parents):
        raise RuntimeError("Symlinked backup rejected.")
    backup = backup.resolve()
    if home not in backup.parents or backup.stat().st_uid != uid or backup.stat().st_mode & 0o077:
        raise RuntimeError("Backup must be a private caller-owned directory inside their home.")
    return user, home, backup


def owned_json(path, value, uid):
    private_json(path, value)
    os.chown(path, uid, pwd.getpwuid(uid).pw_gid)


def package_stage(args, user, home, backup):
    plan = json.loads((backup / "package-plan.json").read_text())
    before = packages()
    roots = plan["roots"]
    reject_transaction(before, plan["transaction"])
    if not roots:
        return
    for unit in ("grub-btrfs-snapper.path", "grub-btrfs-snapper.service", "grub-btrfsd.service"):
        if run(["systemctl", "is-active", unit])[1] == "active":
            raise RuntimeError("Independent GRUB-writing snapshot watcher active: " + unit + "; resolve it explicitly, outside this installer.")
    configuration = Path("/etc/pacman.conf").read_text()
    if re.search(r"^\s*(?:HookDir|Include)\s*=", configuration, re.M):
        # Includes are normal repository definitions; custom hook dirs hidden in them need inspection.
        code, hookdirs = run(["pacman-conf", "HookDir"])
        if code or any(line not in ("/etc/pacman.d/hooks/", "/etc/pacman.d/hooks") for line in hookdirs.splitlines()):
            raise RuntimeError("Nonstandard pacman hook configuration requires agent review.")
    if run(["pacman", "-Dk"])[0] or run(["pacman", "-Qu"])[1]:
        raise RuntimeError("Package health or full-update requirement changed.")
    code, preview = run(["pacman", "-Sp", "--needed", "--print-format", "%n %v", *roots])
    actual = [line.split(" ", 1) for line in preview.splitlines() if " " in line]
    if code or sorted(actual) != sorted(plan["transaction"]):
        raise RuntimeError("Resolved package transaction differs from preview.")
    replacement = ALLOWED_REPLACEMENT in before
    if replacement:
        if not args.allow_settings_replacement:
            raise RuntimeError("CachyOS KDE settings replacement needs explicit review; Plasma will not be removed.")
        info = run(["pacman", "-Qi", ALLOWED_REPLACEMENT])[1]
        listing = run(["pacman", "-Qlq", ALLOWED_REPLACEMENT])[1].splitlines()
        if "KDE" not in info or not listing or any(path.startswith(("/boot/", "/usr/lib/modules/", "/usr/bin/", "/usr/lib/systemd/")) for path in listing):
            raise RuntimeError("The conflicting settings package differs from reviewed defaults-only scope.")
        print(info)
    print("No sync-database refresh or partial upgrade is performed. Review the interactive download and final transaction.")
    with tempfile.TemporaryDirectory(prefix="hypr-package-review-") as temporary:
        temp = Path(temporary)
        cache, hooks = temp / "cache", temp / "hooks"
        cache.mkdir()
        hooks.mkdir()
        subprocess.run(["pacman", "-Sw", "--needed", "--cachedir", str(cache), *roots], check=True)
        archives, members, found, archive_hooks = [], [], [], []
        for archive in sorted(cache.glob("*.pkg.tar.*")):
            if archive.name.endswith(".sig"):
                continue
            code, info = run(["bsdtar", "-xOf", str(archive), ".PKGINFO"])
            name = re.search(r"^pkgname = (.+)$", info, re.M)
            ver = re.search(r"^pkgver = (.+)$", info, re.M)
            if code or not name or not ver:
                raise RuntimeError("Cannot inspect downloaded package metadata.")
            found.append([name[1], ver[1]])
            code, listing = run(["bsdtar", "-tf", str(archive)])
            files = [line.lstrip("./") for line in listing.splitlines()]
            if code or any(path.startswith(("boot/", "efi/", "usr/lib/modules/", "etc/default/grub", "etc/mkinitcpio", "etc/kernel/")) for path in files):
                raise RuntimeError("Boot/kernel payload or unreadable package rejected: " + name[1])
            if any(line.removeprefix("./") == ".INSTALL" for line in listing.splitlines()):
                raise RuntimeError("Package install script requires manual agent review: " + name[1] + "; no package installed.")
            for member in listing.splitlines():
                relative = member.removeprefix("./")
                if relative.startswith(("usr/share/libalpm/hooks/", "etc/pacman.d/hooks/")) and relative.endswith(".hook"):
                    code, text = run(["bsdtar", "-xOf", str(archive), member])
                    if code:
                        raise RuntimeError("Cannot inspect introduced package hook.")
                    extracted = temp / ("new-" + Path(relative).name)
                    extracted.write_text(text)
                    archive_hooks.append(extracted)
            members.extend(files)
            archives.append(str(archive))
        if sorted(found) != sorted(actual):
            raise RuntimeError("Downloaded packages differ from transaction preview.")
        effective = {}
        for directory in (Path("/usr/share/libalpm/hooks"), Path("/etc/pacman.d/hooks")):
            for hook in directory.glob("*.hook"):
                effective[hook.name] = hook
        if replacement:
            members.extend(line.lstrip("/") for line in run(["pacman", "-Qlq", ALLOWED_REPLACEMENT])[1].splitlines())
        overrides = review_hooks([p for p in effective.values() if p.resolve() != Path("/dev/null")] + archive_hooks,
                                 members, actual + ([[ALLOWED_REPLACEMENT, before[ALLOWED_REPLACEMENT]]] if replacement else []),
                                 args.allow_snapshot_hook_override)
        for name in overrides:
            (hooks / name).symlink_to("/dev/null")
        # --hookdir may replace the default user hook directory. Preserve its other
        # entries in the temporary directory rather than accidentally skipping them.
        for name, source in effective.items():
            if source.parent == Path("/etc/pacman.d/hooks") and name not in overrides:
                if source.resolve() == Path("/dev/null"):
                    (hooks / name).symlink_to("/dev/null")
                else:
                    shutil.copyfile(source, hooks / name)
        # A pre-transaction abort gate also sees removals. Names must exactly match the reviewed set.
        allowed = {name for name, _ in actual} | ({ALLOWED_REPLACEMENT} if replacement else set())
        guard = temp / "guard.py"
        guard.write_text("import sys\nallowed=" + repr(allowed) + "\nitems=set(sys.stdin.read().splitlines())\nsys.exit(0 if items <= allowed else 1)\n")
        guard.chmod(0o600)
        (hooks / "00-guard-desktop-migration.hook").write_text(
            "[Trigger]\nOperation=Install\nOperation=Upgrade\nOperation=Remove\nType=Package\nTarget=*\n"
            "[Action]\nWhen=PreTransaction\nExec=/usr/bin/python3 " + str(guard) + "\nNeedsTargets\nAbortOnFail\n")
        owned_json(backup / "packages-before.json", before, user.pw_uid)
        subprocess.run(["pacman", "-U", "--needed", "--hookdir", str(hooks), *archives], check=True)
        after = packages()
        changed = [name for name, value in before.items() if after.get(name) != value and not (replacement and name == ALLOWED_REPLACEMENT and name not in after)]
        owned_json(backup / "packages-after.json", after, user.pw_uid)
        if changed:
            raise RuntimeError("Unexpected existing package change detected; stop and inspect: " + ", ".join(changed))


def system_receipt(backup):
    path = backup / "system-receipt.json"
    return json.loads(path.read_text()) if path.exists() else {"files": [], "directories": [], "previous_dm": None, "selected_sddm": False}


def save_receipt(backup, receipt, uid):
    owned_json(backup / "system-receipt.json", receipt, uid)


def system_write(path, data, backup, receipt, uid, owner=0):
    path = Path(path)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise RuntimeError("Symlinked system target needs manual review: " + str(path))
    old = digest(path)
    after = hashlib.sha256(data).hexdigest()
    if old == after:
        return
    record = {"path": str(path), "before": old, "after": after, "mode": path.stat().st_mode & 0o777 if old else None,
              "uid": path.stat().st_uid if old else None, "gid": path.stat().st_gid if old else None}
    if old:
        saved = backup / "system-files" / str(path).lstrip("/")
        saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copy2(path, saved)
    receipt["files"].append(record)
    save_receipt(backup, receipt, uid)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".desktop-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, 0o644)
        os.chown(temporary, owner, pwd.getpwuid(owner).pw_gid if owner else 0)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def directory_snapshot(path):
    return {str(item.relative_to(path)): digest(item) for item in path.rglob("*") if item.is_file() or item.is_symlink()}


def sddm_stage(args, user, home, backup):
    if not shutil.which("sddm") or not Path("/usr/share/wayland-sessions/hyprland-uwsm.desktop").is_file():
        raise RuntimeError("SDDM or Hyprland (UWSM) session is missing.")
    if not Path("/usr/share/wayland-sessions/plasma.desktop").is_file():
        raise RuntimeError("KDE Plasma fallback is missing; no display-manager changes allowed.")
    if digest(Path("/usr/share/sddm/themes/breeze/Main.qml")) != BREEZE_SHA:
        raise RuntimeError("Installed Breeze QML differs; preview/adaptation required.")
    wallpaper = Path(args.wallpaper).resolve()
    if not wallpaper.is_file() or wallpaper.stat().st_size > 128*1024*1024 or "\n" in str(wallpaper):
        raise RuntimeError("Invalid wallpaper source.")
    theme = Path("/usr/share/sddm/themes/cachyos-noctalia-static")
    profile = Path("/etc/sddm.conf.d/90-cachyos-noctalia-static.conf")
    image_dir = Path("/var/lib/sddm-wallpaper-sync") / user.pw_name
    for target in (theme, profile, image_dir):
        if target.exists() or target.is_symlink():
            raise RuntimeError("Existing integration needs manual merge, not overwrite: " + str(target))
        if any(parent.is_symlink() for parent in target.parents):
            raise RuntimeError("Symlinked system parent rejected.")
    dm_link = Path("/etc/systemd/system/display-manager.service")
    old_dm = dm_link.resolve().name if dm_link.exists() else None
    if args.select_sddm and old_dm and old_dm not in DM_UNITS:
        raise RuntimeError("Unknown existing display manager; no automatic switch.")
    other = [unit for unit in DM_UNITS if run(["systemctl", "is-enabled", unit])[1] == "enabled" and unit != old_dm]
    if other:
        raise RuntimeError("Additional enabled display manager needs review: " + ", ".join(other))
    receipt = system_receipt(backup)
    if receipt["files"] or receipt["directories"]:
        raise RuntimeError("This backup already contains an integration; do not reuse it.")
    # New directories are explicitly owned by this operation, not replacements.
    image_dir.parent.mkdir(parents=True, exist_ok=True)
    receipt["directories"].append({"path": str(image_dir), "tree": {}})
    save_receipt(backup, receipt, user.pw_uid)
    image_dir.mkdir(mode=0o755)
    os.chown(image_dir, user.pw_uid, user.pw_gid)
    system_write(image_dir / "current", wallpaper.read_bytes(), backup, receipt, user.pw_uid, user.pw_uid)
    receipt["directories"].append({"path": str(theme), "tree": {}})
    save_receipt(backup, receipt, user.pw_uid)
    shutil.copytree("/usr/share/sddm/themes/breeze", theme, symlinks=False)
    shutil.copyfile(ROOT / "greeter/Main.qml", theme / "Main.qml")
    (theme / "theme.conf.user").write_text("[General]\ntype=image\nshowClock=true\nbackground=" + str(image_dir / "current") + "\n")
    for entry in [theme, *theme.rglob("*")]:
        os.chown(entry, 0, 0)
        entry.chmod(0o755 if entry.is_dir() else 0o644)
    receipt["directories"][-1]["tree"] = directory_snapshot(theme)
    save_receipt(backup, receipt, user.pw_uid)
    system_write(profile, b"[Theme]\nCurrent=cachyos-noctalia-static\n", backup, receipt, user.pw_uid)
    if args.select_sddm:
        receipt["previous_dm"] = old_dm
        receipt["selected_sddm"] = True
        save_receipt(backup, receipt, user.pw_uid)
        if old_dm and old_dm != "sddm.service":
            subprocess.run(["systemctl", "disable", old_dm], check=True)
        subprocess.run(["systemctl", "enable", "--force", "sddm.service"], check=True)
        if dm_link.resolve().name != "sddm.service" or any(run(["systemctl", "is-enabled", unit])[1] == "enabled" for unit in DM_UNITS if unit != "sddm.service"):
            raise RuntimeError("Display-manager selection did not verify; use the recorded rollback.")
    print("SDDM staged for next login/boot only. No service stopped or restarted.")
    print("Next-boot rollback: ./setup rollback --backup " + shlex.quote(str(backup)))


def rollback_system(user, home, backup):
    receipt = system_receipt(backup)
    allowed_paths = {"/etc/sddm.conf.d/90-cachyos-noctalia-static.conf", "/root/.local/share/color-schemes/noctalia.colors",
                     "/var/lib/sddm-wallpaper-sync/" + user.pw_name + "/current"}
    allowed_dirs = {"/usr/share/sddm/themes/cachyos-noctalia-static", "/var/lib/sddm-wallpaper-sync/" + user.pw_name}
    # Validate everything before the first mutation; do not trust arbitrary receipt paths.
    for record in receipt["files"]:
        path = Path(record["path"])
        if str(path) not in allowed_paths or path.is_symlink() or digest(path) not in (record["before"], record["after"]):
            raise RuntimeError("System target changed or is unsafe; manual recovery required: " + str(path))
        if record["before"] is not None and digest(backup / "system-files" / str(path).lstrip("/")) != record["before"]:
            raise RuntimeError("Original system backup differs.")
    for directory in receipt["directories"]:
        path = Path(directory["path"])
        if str(path) not in allowed_dirs or path.is_symlink():
            raise RuntimeError("Unsafe integration directory receipt.")
        if directory["tree"] and directory_snapshot(path) != directory["tree"]:
            raise RuntimeError("Greeter files changed; preserve them for manual recovery.")
    if receipt["selected_sddm"]:
        link = Path("/etc/systemd/system/display-manager.service")
        previous = receipt["previous_dm"]
        if link.resolve().name not in ("sddm.service", previous):
            raise RuntimeError("Display manager changed since installation; leave it untouched.")
        if previous is not None and previous not in DM_UNITS:
            raise RuntimeError("Invalid rollback display manager.")
    for record in reversed(receipt["files"]):
        path = Path(record["path"])
        if digest(path) == record["before"]:
            continue
        if record["before"] is None:
            # Recoverable rename of the exact recorded file; no broad delete.
            path.rename(path.with_name(path.name + ".disabled-" + stamp()))
        else:
            saved = backup / "system-files" / str(path).lstrip("/")
            shutil.copy2(saved, path)
            path.chmod(record["mode"])
            os.chown(path, record["uid"], record["gid"])
    for directory in reversed(receipt["directories"]):
        path = Path(directory["path"])
        if path.exists():
            path.rename(path.with_name(path.name + ".disabled-" + stamp()))
    if receipt["selected_sddm"] and receipt["previous_dm"] != "sddm.service":
        subprocess.run(["systemctl", "disable", "sddm.service"], check=True)
        if receipt["previous_dm"]:
            subprocess.run(["systemctl", "enable", "--force", receipt["previous_dm"]], check=True)
    print("Recorded system integration restored for the next boot. Disabled files are recoverable beside their originals; no session restart.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("packages", "sddm", "rollback"))
    parser.add_argument("--uid", type=int, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--wallpaper")
    parser.add_argument("--select-sddm", action="store_true")
    parser.add_argument("--allow-snapshot-hook-override", action="store_true")
    parser.add_argument("--allow-settings-replacement", action="store_true")
    args = parser.parse_args()
    try:
        user, home, backup = validate_context(args.uid, args.backup)
        if args.action == "packages":
            package_stage(args, user, home, backup)
        elif args.action == "sddm":
            sddm_stage(args, user, home, backup)
        else:
            rollback_system(user, home, backup)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("Privileged stage stopped: " + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
