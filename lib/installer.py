# SPDX-License-Identifier: MIT
import argparse
import configparser
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess
import tempfile
import tomllib
from toml_state import merge_state
from preferences import apply_preferences, restore_preferences

from detect import audit, packages, run, version

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "packages.json").read_text())
REFERENCE = json.loads((ROOT / "profiles/reference.json").read_text())
MODEL_SHA = "818710568da3ca15689e31a743197b520007872ff9576237bda97bd1b469c3d7"
BREEZE_SHA = "17005cc149ce0f8283e5609df9c5650ecf9e0ffe12ba6aa1e336d96e597c26a0"


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def digest(path):
    path = Path(path)
    if path.is_symlink():
        return "link:" + os.readlink(path)
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def private_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".record-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def checked_target(home, relative):
    home = Path(home).resolve()
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("Unsafe target path rejected.")
    target = home / relative
    for parent in [home, *target.parents]:
        if parent == home.parent:
            break
        if parent.is_symlink():
            raise RuntimeError("Symlinked target parent requires manual review: " + str(relative))
        if parent == home:
            # target.parents starts at the closest parent, checked below.
            continue
        if home not in parent.parents:
            break
    if target.exists() and not target.is_file() and not target.is_symlink():
        raise RuntimeError("Non-file configuration target rejected: " + str(relative))
    return target


def ini_merge(target, additions):
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.optionxform = str
    if target.exists():
        parser.read_string(target.read_text())
    for section, values in additions.items():
        if not parser.has_section(section):
            parser.add_section(section)
        for key, value in values.items():
            parser.set(section, key, value)
    import io
    buffer = io.StringIO()
    parser.write(buffer)
    return buffer.getvalue().encode()


def lua_host(display):
    # JSON strings form valid Lua string literals for these ASCII connector/mode identifiers.
    output, mode = display["output"], display["mode"]
    if not re.fullmatch(r"[A-Za-z0-9_.:-]*", output) or not re.fullmatch(r"[A-Za-z0-9_.@:-]+", mode):
        raise RuntimeError("Invalid display metadata; agent review required.")
    scale = display["scale"]
    if scale != "auto" and not (isinstance(scale, (float, int)) and 0.5 <= scale <= 4):
        raise RuntimeError("Invalid display scale.")
    return ("-- Generated from detected hardware; no GPU override.\nreturn { output = " + json.dumps(output)
            + ", mode = " + json.dumps(mode) + ", scale = " + json.dumps(scale) + " }\n").encode()


def wallpaper_file(args):
    if args.wallpaper:
        path = Path(args.wallpaper).expanduser().resolve()
    else:
        path = Path("/usr/share/wallpapers/cachyos-wallpapers/north.png")
    if not path.is_file() or path.stat().st_size > 128*1024*1024:
        raise RuntimeError("Supply a readable static wallpaper with --wallpaper; packaged fallback missing or invalid.")
    code, mime = run(["file", "--brief", "--mime-type", str(path)])
    if code or mime not in ("image/jpeg", "image/png", "image/webp", "image/bmp", "image/x-ms-bmp", "image/avif"):
        raise RuntimeError("Wallpaper must be a supported static raster image.")
    return path


def render(home, host, wallpaper, sddm=False):
    home, wallpaper = Path(home), Path(wallpaper)
    known = {"config.toml", "sddm-wallpaper-sync.toml"}
    fragments = home / ".config/noctalia"
    if fragments.exists():
        extras = [p.name for p in fragments.glob("*.toml") if p.name not in known]
        if extras:
            raise RuntimeError("Existing Noctalia fragments need manual merge: " + ", ".join(extras))
        if not sddm and (fragments / "sddm-wallpaper-sync.toml").exists():
            raise RuntimeError("Existing SDDM wallpaper hook requires an explicit integration review; not silently replaced.")
    result = {}
    for family in ("hypr", "noctalia", "kitty", "uwsm", "fontconfig"):
        for source in sorted((ROOT / "config" / family).rglob("*")):
            if source.is_file():
                relative = Path(".config") / family / source.relative_to(ROOT / "config" / family)
                result[str(relative)] = source.read_bytes()
    result[".config/hypr/config/host.lua"] = lua_host(host["display"])
    for script in ("hypr-screenshot", "hypr-dictation", "sddm-wallpaper-sync"):
        result[".local/bin/" + script] = (ROOT / "tools" / script).read_bytes()
    result[".config/noctalia/hooks/power-profile.sh"] = (ROOT / "tools/power-profile.sh").read_bytes()
    result[".local/share/color-schemes/noctalia.colors"] = (ROOT / "palettes/noctalia.colors").read_bytes()
    # Alias as an identical file, not a symlink to a private donor path.
    result[".local/share/color-schemes/Noctalia.colors"] = result[".local/share/color-schemes/noctalia.colors"]
    result[".config/qt6ct/colors/noctalia.conf"] = (ROOT / "palettes/qt6ct.conf").read_bytes()
    for generation in ("gtk-3.0", "gtk-4.0"):
        result[f".config/{generation}/noctalia.css"] = (ROOT / f'palettes/{"gtk3" if generation == "gtk-3.0" else "gtk4"}.css').read_bytes()
        result[f".config/{generation}/colors.css"] = (ROOT / "palettes/colors.css").read_bytes()
        result[f".config/{generation}/gtk.css"] = b'@import url("noctalia.css");\n@import url("colors.css");\n'
    appearance = json.loads((ROOT / "config/appearance.json").read_text())
    for generation in ("gtk-3.0", "gtk-4.0"):
        relative = f".config/{generation}/settings.ini"
        result[relative] = ini_merge(checked_target(home, relative), appearance["gtk"])
    qt = appearance["qt6ct"]
    qt["Appearance"]["color_scheme_path"] = str(home / ".config/qt6ct/colors/noctalia.conf")
    for filename, data in (("qt6ct/qt6ct.conf", qt), ("dolphinrc", appearance["dolphin"]),
                           ("kdeglobals", appearance["kdeglobals"]), ("mimeapps.list", appearance["mimeapps"])):
        relative = ".config/" + filename
        result[relative] = ini_merge(checked_target(home, relative), data)
    autostart = ".config/autostart/org.kde.kdeconnect.daemon.desktop"
    if Path("/usr/bin/kdeconnectd").exists():
        target = checked_target(home, autostart)
        defaults = target if target.exists() else Path("/etc/xdg/autostart/org.kde.kdeconnect.daemon.desktop")
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        if defaults.exists():
            parser.read_string(defaults.read_text())
        previous = parser.get("Desktop Entry", "NotShowIn", fallback="")
        additions = {"Desktop Entry": {"NotShowIn": ";".join(dict.fromkeys([p for p in previous.split(";") if p] + ["Hyprland"])) + ";"}}
        if not defaults.exists():
            additions["Desktop Entry"].update({"Type": "Application", "Name": "KDE Connect", "Exec": "/usr/bin/kdeconnectd"})
        result[autostart] = ini_merge(defaults, additions)
    # Do not transplant output-specific lock widget positions or private service settings.
    relative = ".local/state/noctalia/settings.toml"
    additions = tomllib.loads((ROOT / "config/noctalia/config.toml").read_text())
    additions["config_version"] = 14
    additions["wallpaper"]["default"]["path"] = str(wallpaper)
    additions["lockscreen_widgets"] = {"enabled": False}
    result[relative] = merge_state(checked_target(home, relative), additions)
    portal = Path("/usr/share/xdg-desktop-portal/hyprland-portals.conf")
    if portal.is_file():
        result[".config/xdg-desktop-portal/hyprland-portals.conf"] = portal.read_bytes()
    cursor = Path("/etc/skel/.local/share/icons/Bibata-Modern-Ice")
    if cursor.exists():
        for source in cursor.rglob("*"):
            if source.is_file():
                result[str(Path(".local/share/icons/Bibata-Modern-Ice") / source.relative_to(cursor))] = source.read_bytes()
    if sddm:
        output = host["display"]["output"]
        hook = 'bash "$HOME/.local/bin/sddm-wallpaper-sync" "" ' + json.dumps(output)
        result[".config/noctalia/sddm-wallpaper-sync.toml"] = ('[hooks]\nwallpaper_changed = ' + json.dumps(hook) + '\n').encode()
    # Validate generated TOML before any target file changes.
    for name, data in result.items():
        if name.endswith(".toml"):
            tomllib.loads(data.decode())
    return result


def blockers(host, candidates):
    issues = []
    if host["os"] != "cachyos" or host["architecture"] != "x86_64":
        issues.append("Automatic deployment supports x86_64 CachyOS only; other hosts need adaptation.")
    if not host["package_health"]:
        issues.append("Package database health could not be verified.")
    if host["pending_updates"]:
        issues.append("Updates are pending. Have an operator review a normal full update separately; do not partially upgrade.")
    for package, accepted in MANIFEST["tested_versions"].items():
        raw = host["packages"].get(package) or candidates.get(package, "")
        if not raw or version(raw) not in accepted:
            issues.append(f"Unsupported or unknown {package} version. Tested: {', '.join(accepted)}; no downgrade/pinning performed.")
    if any(host["services"].get(unit) == "active" for unit in ("tlp", "auto-cpufreq")):
        issues.append("An alternate power daemon is active; preserve it and resolve compatibility with an agent.")
    if host["services"].get("power-profiles-daemon") != "active":
        issues.append("The existing powerprofilesctl stack must be working before automatic configuration.")
    if any(gpu["vendor"] == "0x10de" and not gpu["driver"] for gpu in host["gpus"]):
        issues.append("NVIDIA has no bound driver; driver installation is deliberately outside this installer.")
    return issues


def package_plan(host):
    installed = packages()
    roots = list(MANIFEST["core"] + MANIFEST["dictation"])
    if any(gpu["vendor"] == "0x10de" for gpu in host["gpus"]):
        roots += MANIFEST["nvidia_existing_driver_only"]
    missing = [name for name in roots if name not in installed]
    candidates = {}
    for name in MANIFEST["tested_versions"]:
        code, output = run(["pacman", "-Si", name])
        match = re.search(r"^Version\s*:\s*(\S+)", output, re.M)
        if not code and match:
            candidates[name] = match[1]
    preview = []
    if missing:
        code, output = run(["pacman", "-Sp", "--needed", "--print-format", "%n %v", *missing])
        if code:
            raise RuntimeError("Official repository dependencies could not be resolved; do not substitute AUR packages.")
        preview = [line.split(" ", 1) for line in output.splitlines() if " " in line]
    return {"roots": missing, "transaction": preview, "candidates": candidates}


def stage_greeter(report_dir, wallpaper):
    source = Path("/usr/share/sddm/themes/breeze")
    if digest(source / "Main.qml") != BREEZE_SHA:
        raise RuntimeError("Installed Breeze differs from the tested source; greeter adaptation/preview required.")
    stage = report_dir / "greeter-preview"
    shutil.copytree(source, stage, symlinks=False)
    shutil.copyfile(ROOT / "greeter/Main.qml", stage / "Main.qml")
    (stage / "theme.conf.user").write_text("[General]\ntype=image\nshowClock=true\nbackground=" + str(wallpaper) + "\n")
    print("Preview manually (close it before applying):\nsddm-greeter-qt6 --test-mode --theme " + __import__("shlex").quote(str(stage)))
    return stage


def prompt(message):
    if not __import__("sys").stdin.isatty():
        raise RuntimeError("Interactive review required. Run apply in a terminal; no unattended confirmation flag exists.")
    if input(message + " [type APPLY]: ") != "APPLY":
        raise RuntimeError("Canceled without further changes.")


def snapshot_and_write(home, payload, backup):
    # Prevalidate every parent and type before making the first change.
    targets = {relative: checked_target(home, relative) for relative in payload}
    records = []
    for relative, target in targets.items():
        old = digest(target)
        record = {"relative": relative, "before": old, "after": hashlib.sha256(payload[relative]).hexdigest(),
                  "mode": target.lstat().st_mode & 0o777 if old is not None else None}
        if old == record["after"]:
            continue
        if old is not None:
            saved = backup / "files" / relative
            saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copy2(target, saved, follow_symlinks=False)
        records.append(record)
    receipt = {"home": str(Path(home).resolve()), "records": records, "complete": False}
    private_json(backup / "receipt.json", receipt)
    # Backups are separate from the writable lifecycle receipt. Never overwrite originals.
    for record in records:
        target = targets[record["relative"]]
        if digest(target) != record["before"]:
            raise RuntimeError("Configuration changed during deployment; receipt retained: " + record["relative"])
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=".hypr-setup-")
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload[record["relative"]])
            executable = record["relative"].startswith(".local/bin/") or record["relative"].endswith(".sh")
            mode = 0o755 if executable else (record["mode"] if record["before"] and not record["before"].startswith("link:") else 0o600)
            Path(temporary).chmod(mode)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    receipt["complete"] = True
    private_json(backup / "receipt.json", receipt)
    return receipt


def rollback(home, backup, check_only=False):
    receipt = json.loads((backup / "receipt.json").read_text())
    if Path(receipt["home"]).resolve() != Path(home).resolve():
        raise RuntimeError("Backup belongs to a different home directory.")
    for record in receipt["records"]:
        target = checked_target(home, record["relative"])
        if digest(target) not in (record["before"], record["after"]):
            raise RuntimeError("Subsequent user edit detected; rollback stopped: " + record["relative"])
        saved = backup / "files" / record["relative"]
        if record["before"] is not None and digest(saved) != record["before"]:
            raise RuntimeError("Backup checksum differs; stopped.")
    if check_only:
        return
    for record in reversed(receipt["records"]):
        target = checked_target(home, record["relative"])
        if digest(target) == record["before"]:
            continue
        if record["before"] is None:
            # Only delete the exact unchanged file created by this receipt.
            target.unlink()
        else:
            saved = backup / "files" / record["relative"]
            temp = target.with_name(".restore-" + stamp())
            shutil.copy2(saved, temp, follow_symlinks=False)
            if not temp.is_symlink():
                temp.chmod(record["mode"])
            os.replace(temp, target)
    print("Recorded user files restored. Packages retained. New unchanged files removed; originals remain in the backup.")


def handoff(report_dir, stage, error, backup=None):
    message = ("This setup was developed on a Dell G15 5530 (Intel i5-13450HX + NVIDIA RTX 3050), "
               "CachyOS, Hyprland 0.56.2 / Noctalia 5.2.0 / UWSM.\n"
               f"Stopped at {stage}: {error}\nNo unsafe fallback was applied.\n"
               "Give a coding agent AGENTS.md, docs/AGENT_HANDOFF.md and this private report AFTER reviewing it for privacy.\n")
    report_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    text = message + ("Recovery backup: " + str(backup) + "\n" if backup else "No configuration backup was needed before this stage.\n")
    (report_dir / "handoff.md").write_text(text)
    (report_dir / "handoff.md").chmod(0o600)
    print(message + "Report: " + str(report_dir))


def verify(host):
    results = {"hyprland_config_errors": run(["hyprctl", "configerrors"]),
               "uwsm_session_available": Path("/usr/share/wayland-sessions/hyprland-uwsm.desktop").exists(),
               "dictation_off": run(["systemctl", "--user", "is-active", "hypr-dictation.service"])[1] in ("inactive", "unknown", ""),
               "nvidia_functions": [f for gpu in host["gpus"] if gpu["vendor"] == "0x10de" for f in gpu["functions"]],
               "power_profile": host["power_profile"],
               "manual_checks_required": ["Intel compositor and normal renderer", "PRIME wake/render/resuspend", "screen sharing", "repeated suspend/resume", "microphone/dictation", "physical keys", "matched A/B power"]}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("audit", "plan", "apply", "verify", "rollback"))
    parser.add_argument("--wallpaper")
    parser.add_argument("--packages", action="store_true", help="explicit reviewed package-install step")
    parser.add_argument("--allow-snapshot-hook-override", action="store_true")
    parser.add_argument("--allow-settings-replacement", action="store_true")
    parser.add_argument("--download-model", action="store_true")
    parser.add_argument("--sddm", action="store_true")
    parser.add_argument("--confirm-greeter-preview", action="store_true")
    parser.add_argument("--select-sddm", action="store_true")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    if os.getuid() == 0:
        print("Run setup as your normal user. Only reviewed privileged steps use sudo.")
        return 2
    home = Path.home().resolve()
    state = Path(os.environ.get("XDG_STATE_HOME", str(home / ".local/state"))) / "cachyos-hyprland-noctalia"
    report_dir = state / "reports" / stamp()
    backup = None
    stage = args.action
    try:
        if args.action == "rollback":
            if not args.backup:
                raise RuntimeError("Specify --backup from the recorded deployment report.")
            user_receipt = (args.backup / "receipt.json").exists()
            if user_receipt:
                rollback(home, args.backup.resolve(), check_only=True)
            elif not (args.backup / "system-receipt.json").exists():
                raise RuntimeError("No deployment receipt found; do not infer rollback targets.")
            restore_preferences(args.backup.resolve(), check_only=True)
            if (args.backup / "system-receipt.json").exists():
                prompt("Also restore recorded system-level settings, without restarting SDDM?")
                subprocess.run(["sudo", "python3", str(ROOT / "lib/privileged.py"), "rollback", "--uid", str(os.getuid()), "--backup", str(args.backup.resolve())], check=True)
            if user_receipt:
                rollback(home, args.backup.resolve())
            restore_preferences(args.backup.resolve())
            return 0
        host = audit()
        private_json(report_dir / "audit.json", host)
        if args.action == "audit":
            print(json.dumps(host, indent=2))
            print("Private report: " + str(report_dir))
            return 0
        if args.action == "verify":
            results = verify(host)
            private_json(report_dir / "verification.json", results)
            print(json.dumps(results, indent=2))
            print("Hardware validation is NOT complete; follow docs/VALIDATION.md.")
            return 0 if results["hyprland_config_errors"] == (0, "") and results["dictation_off"] and results["uwsm_session_available"] else 2
        for variable, expected in (("XDG_CONFIG_HOME", home / ".config"), ("XDG_STATE_HOME", home / ".local/state"),
                                   ("XDG_DATA_HOME", home / ".local/share")):
            if os.environ.get(variable) and Path(os.environ[variable]).resolve() != expected.resolve():
                raise RuntimeError("Custom " + variable + " needs agent path adaptation; no home-default config will be written.")
        plan = package_plan(host)
        problems = blockers(host, plan["candidates"])
        plan["blockers"] = problems
        private_json(report_dir / "plan.json", plan)
        print(json.dumps(plan, indent=2))
        if problems:
            raise RuntimeError("; ".join(problems))
        wallpaper = wallpaper_file(args)
        if args.sddm:
            stage_greeter(report_dir, wallpaper)
        if args.action == "plan":
            payload = render(home, host, wallpaper, args.sddm)
            changes = [key for key, value in payload.items() if digest(checked_target(home, key)) != hashlib.sha256(value).hexdigest()]
            private_json(report_dir / "changes.json", changes)
            print("Files to change:\n" + "\n".join(changes))
            print("Plan only. No target config/services changed. Report: " + str(report_dir))
            return 0
        if run(["systemctl", "--user", "is-active", "hypr-dictation.service"])[1] == "active":
            raise RuntimeError("Stop your dictation session yourself before replacing its helper.")
        if args.select_sddm and not args.sddm:
            raise RuntimeError("--select-sddm requires the reviewed --sddm step.")
        if args.sddm and not args.confirm_greeter_preview:
            raise RuntimeError("Preview the staged greeter, then pass --confirm-greeter-preview; no graphical login change made.")
        prompt("Apply reviewed packages/configuration? Existing configuration will be backed up.")
        backup = state / "backups" / stamp()
        backup.mkdir(parents=True, mode=0o700)
        private_json(backup / "baseline.json", host)
        private_json(backup / "package-plan.json", plan)
        private_json(backup / "packages-installed.json", packages())
        for filename, command in (
            ("packages-explicit.json", ["pacman", "-Qqe"]),
            ("enabled-system-services.json", ["systemctl", "list-unit-files", "--state=enabled", "--no-legend", "--no-pager"]),
            ("enabled-user-services.json", ["systemctl", "--user", "list-unit-files", "--state=enabled", "--no-legend", "--no-pager"])):
            code, output = run(command)
            if code:
                raise RuntimeError("Recovery inventory could not be recorded: " + filename)
            private_json(backup / filename, output.splitlines())
        if plan["roots"]:
            if not args.packages:
                raise RuntimeError("Missing packages. Re-run with --packages only after reviewing the transaction.")
            stage = "package installation"
            command = ["sudo", "python3", str(ROOT / "lib/privileged.py"), "packages", "--uid", str(os.getuid()), "--backup", str(backup)]
            if args.allow_snapshot_hook_override:
                command += ["--allow-snapshot-hook-override"]
            if args.allow_settings_replacement:
                command += ["--allow-settings-replacement"]
            subprocess.run(command, check=True)
            host = audit()
            if blockers(host, {}):
                raise RuntimeError("Post-package compatibility differs; stop before deploying config.")
        stage = "configuration generation"
        payload = render(home, host, wallpaper, args.sddm)
        if args.sddm:
            stage = "SDDM integration"
            cmd = ["sudo", "python3", str(ROOT / "lib/privileged.py"), "sddm", "--uid", str(os.getuid()), "--backup", str(backup), "--wallpaper", str(wallpaper)]
            if args.select_sddm:
                cmd += ["--select-sddm"]
            subprocess.run(cmd, check=True)
        stage = "user configuration deployment"
        receipt = snapshot_and_write(home, payload, backup)
        stage = "GTK dark preferences"
        apply_preferences(backup)
        if args.download_model:
            stage = "verified model download"
            spec = importlib.util.spec_from_file_location("model_download", ROOT / "tools/download_model.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.download(home / ".local/share/hypr-dictation/models/ggml-tiny-q5_1.bin")
        model = home / ".local/share/hypr-dictation/models/ggml-tiny-q5_1.bin"
        ready = digest(model) == MODEL_SHA
        private_json(report_dir / "result.json", {"backup": str(backup), "config_deployed": receipt["complete"], "dictation_model_ready": ready, "hardware_validated": False})
        print("Configuration deployed; no session reload/reboot performed. Backup: " + str(backup))
        print("Choose Hyprland (UWSM) manually; verify the retained desktop fallback first.")
        if not ready:
            handoff(report_dir, "dictation model", "Speech model not installed. Explicitly run python tools/download_model.py; full feature readiness is incomplete.", backup)
            return 2
        print("Run ./setup verify and the manual hardware checklist. No claim of completed migration/battery optimization.")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError, configparser.Error, tomllib.TOMLDecodeError) as error:
        handoff(report_dir, stage, str(error), backup)
        return 2
    except KeyboardInterrupt:
        handoff(report_dir, stage, "Interrupted; review the receipt before rollback or continuing.", backup)
        return 130
