"""Read-only host discovery. Do not collect serials, accounts or process argv."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def run(args, timeout=15):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def read(path, default=""):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return default


def packages():
    code, output = run(["pacman", "-Q"])
    return dict(line.split(" ", 1) for line in output.splitlines() if " " in line) if code == 0 else {}


def version(raw):
    return raw.split(":")[-1].rsplit("-", 1)[0]


def edid_modes(blob):
    if len(blob) < 128 or blob[:8] != b"\x00\xff\xff\xff\xff\xff\xff\x00":
        return []
    if any(sum(blob[i:i+128]) % 256 for i in range(0, len(blob), 128)):
        return []
    offsets = [54, 72, 90, 108]
    for block in range(128, len(blob), 128):
        if blob[block] == 2 and 4 <= blob[block+2] < 127:
            offsets.extend(range(block+blob[block+2], block+110, 18))
    modes = []
    for offset in offsets:
        item = blob[offset:offset+18]
        if len(item) < 18 or item[17] & 128:
            continue
        clock = int.from_bytes(item[:2], "little") * 10000
        width, height = item[2] + ((item[4] & 240) << 4), item[5] + ((item[7] & 240) << 4)
        hblank, vblank = item[3] + ((item[4] & 15) << 8), item[6] + ((item[7] & 15) << 8)
        if clock and width and height:
            modes.append({"width": width, "height": height,
                          "hz": clock / ((width+hblank) * (height+vblank))})
    return modes


def choose_display(monitors, dell=False):
    connected = [m for m in monitors if m.get("connected", True)]
    if not connected:
        return {"output": "", "mode": "preferred", "scale": "auto", "verified_60hz": False}
    selected = next((m for m in connected if m["name"].startswith(("eDP-", "LVDS-", "DSI-"))), connected[0])
    modes = selected.get("modes", [])
    if modes:
        native = max(modes, key=lambda m: m["width"] * m["height"])
        battery = [m for m in modes if (m["width"], m["height"]) == (native["width"], native["height"])
                   and 59.5 <= m["hz"] <= 60.5]
        preferred = min(battery, key=lambda m: abs(m["hz"]-60)) if battery else native
        mode = f'{preferred["width"]}x{preferred["height"]}@{preferred["hz"]:.2f}'
    else:
        battery, mode = [], "preferred"
    return {"output": selected["name"], "mode": mode,
            "scale": 1.25 if dell and mode.startswith("1920x1080@60.") else "auto",
            "verified_60hz": bool(battery)}


def audit(sysroot=Path("/sys")):
    sysroot = Path(sysroot)
    installed = packages()
    os_info = dict(re.findall(r'^([A-Z_]+)=(.*)$', read("/etc/os-release"), re.M))
    os_info = {key: value.strip('"') for key, value in os_info.items()}
    vendor = read(sysroot / "class/dmi/id/sys_vendor")
    product = read(sysroot / "class/dmi/id/product_name")
    gpus = []
    pci = sysroot / "bus/pci/devices"
    for device in sorted(pci.iterdir()) if pci.exists() else []:
        cls = read(device / "class", "0")
        if int(cls, 16) >> 16 != 3:
            continue
        functions = []
        for sibling in sorted(pci.glob(device.name.rsplit(".", 1)[0]+".*")):
            functions.append({"pci": sibling.name, "class": read(sibling / "class"),
                              "runtime_status": read(sibling / "power/runtime_status"),
                              "runtime_control": read(sibling / "power/control")})
        gpus.append({"pci": device.name, "vendor": read(device / "vendor"),
                     "device": read(device / "device"),
                     "driver": (device / "driver").resolve().name if (device / "driver").exists() else "",
                     "functions": functions})
    monitors = []
    drm = sysroot / "class/drm"
    for connector in sorted(drm.glob("card*-*")):
        if not (connector / "status").exists():
            continue
        card, name = connector.name.split("-", 1)
        try:
            modes = edid_modes((connector / "edid").read_bytes())
        except OSError:
            modes = []
        monitors.append({"name": name, "connected": read(connector / "status") == "connected",
                         "gpu_pci": (drm / card / "device").resolve().name, "modes": modes})
    code, payload = run(["hyprctl", "-j", "monitors"])
    try:
        if code == 0:
            for monitor in json.loads(payload):
                modes = []
                for text in monitor.get("availableModes", []):
                    match = re.fullmatch(r"(\d+)x(\d+)@([\d.]+)(?:Hz)?", text)
                    if match:
                        modes.append(dict(zip(("width", "height", "hz"),
                                              (int(match[1]), int(match[2]), float(match[3])))))
                existing = next((m for m in monitors if m["name"] == monitor["name"]), None)
                if existing is not None:
                    existing.update(modes=modes or existing["modes"], current_scale=monitor["scale"])
                else:
                    monitors.append({"name": monitor["name"], "connected": True, "modes": modes})
    except (ValueError, KeyError, TypeError):
        pass
    services = {}
    for unit in ("display-manager", "NetworkManager", "bluetooth", "power-profiles-daemon",
                 "thermald", "intel_lpmd", "ollama", "tlp", "auto-cpufreq",
                 "grub-btrfs-snapper.path", "grub-btrfs-snapper.service", "grub-btrfsd.service"):
        services[unit] = run(["systemctl", "is-active", unit])[1] or "unknown"
    protected = {name: value for name, value in installed.items()
                 if name.startswith(("linux-", "nvidia", "lib32-nvidia", "systemd", "grub", "limine"))
                 or name in ("sddm", "plasma-workspace", "plasma-desktop", "networkmanager", "pipewire", "wireplumber")}
    relevant = {name: installed[name] for name in installed if name.startswith(("hypr", "xdg-desktop-portal"))
                or name in ("cachyos-hypr-noctalia", "cachyos-kde-settings", "noctalia", "uwsm", "whisper-cpp", "ggml", "wtype")}
    dm = Path("/etc/systemd/system/display-manager.service")
    return {"os": os_info.get("ID", "unknown"), "architecture": os.uname().machine,
            "kernel": os.uname().release, "machine": {"vendor": vendor, "product": product},
            "cpu_vendor": "Intel" if "GenuineIntel" in read("/proc/cpuinfo") else "other",
            "gpus": gpus, "connectors": monitors,
            "display": choose_display(monitors, "Dell" in vendor and "G15 5530" in product),
            "packages": relevant, "protected_packages": protected, "services": services,
            "display_manager": dm.resolve().name if dm.exists() else "none",
            "power_profile": run(["powerprofilesctl", "get"])[1],
            "package_health": run(["pacman", "-Dk"])[0] == 0,
            "pending_updates": run(["pacman", "-Qu"])[1].splitlines(),
            "commands": {name: bool(shutil.which(name)) for name in ("pacman", "hyprctl", "noctalia", "uwsm", "powerprofilesctl")}}
