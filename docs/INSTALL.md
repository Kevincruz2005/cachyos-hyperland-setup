# Staged installation on an existing system

Read the safety contract in README and AGENTS.md. Start with an already working
x86_64 CachyOS installation, a normal user, official repository access, working
power-profiles-daemon, installed graphics drivers and a retained desktop fallback.
The automatic adapter currently accepts Hyprland 0.56.2, Noctalia 5.2.0 and UWSM
0.27.0. It does not downgrade, pin packages or force an old version to run.
For other versions/distributions, take the generated handoff to an agent.

## 1. Audit and review

```sh
./setup audit
./setup plan --wallpaper /absolute/path/to/static-wallpaper.png
```

`audit` reads the system and writes a private local report, not desktop settings.
`plan` resolves official repository dependencies against the **existing** package
databases, reports missing packages and proposed file changes, and generates no
live configuration. It does not refresh pacman's databases. Cached `pacman -Qu`
is not proof that remote repositories are current: the operator must review a
normal full update separately before installation. Never run `pacman -Sy` alone.

If a full update changes the kernel/driver or triggers initramfs/bootloader work,
stop and ask the machine owner. This repository cannot safely automate that
machine-specific maintenance. On the original laptop, a Plymouth-triggered
initramfs rebuild was separately authorized, backed up and verified; this is
historical evidence, not blanket permission for another machine.

Private artifacts live under `$XDG_STATE_HOME/cachyos-hyprland-noctalia`, default
`~/.local/state/cachyos-hyprland-noctalia`. Never upload reports or backups: target
configuration may contain service credentials. Review sanitized details only.

## 2. Apply selected modules

If every required package is already installed:

```sh
./setup apply --wallpaper /absolute/path/to/static-wallpaper.png --download-model
```

If missing official packages were reviewed, add `--packages`. Apply requires a
terminal and typing `APPLY`. Privileged stages use sudo separately; pacman remains
interactive. There is no unattended approval switch. The model download is
explicit, checksummed, approximately 32 MB and starts no inference/microphone.
Omitting the download is allowed, but missing model readiness produces a nonzero
handoff rather than claiming every feature works.

Package safeguards deliberately stop for:

- Unexpected resolution, an existing-package upgrade/replacement, critical
  removal, kernel/driver/boot/core payloads or new package install scripts.
- Matching unknown or boot-writing hooks. The hook review is conservative, not
  a generic proof of package safety; inspect refusal messages with an agent.
- Active GRUB snapshot watchers, even if pacman snapshot hooks are suppressed.
- Pending cached updates, unhealthy package database or untested software versions.

`--allow-snapshot-hook-override` explicitly permits temporary **transaction-local**
null overrides of the three known snap-pac snapshot hooks. It does not disable
running snapshot watchers, change installed hooks, GRUB or snapshot policy.
`--allow-settings-replacement` permits only the reviewed defaults-only
`cachyos-kde-settings` conflict. Plasma itself is never an allowed removal.
If a package's `.INSTALL` script requires review, use the agent handoff; do not
edit the guard away or substitute an AUR package blindly.

User files are prevalidated, originals copied to a private timestamped backup,
then replaced atomically. Existing INI and target-local Noctalia state are merged;
comments/formatting may change, but unrelated values remain in the backup and
merge. Unknown existing Noctalia TOML fragments stop for review instead of silently
colliding. Selected GNOME interface dark/font/icon preferences are backed up and
set once through gsettings; no new preference daemon is installed. Symlinked parent
directories require manual review. No `~/.config` tree
replacement, shell rc replacement, wallpaper binary export or KDE removal occurs.
The generated host module uses detected output/modes rather than fixed PCI/card
names. Unknown 60 Hz modes are not invented. Multi-monitor screenshots currently
use Noctalia's native UI instead of this single-output custom tool.

## 3. Optional system integration

See [SDDM](SDDM.md). Greeter deployment requires a source-compatible Breeze
installation, a manual preview and `--confirm-greeter-preview`. `--select-sddm`
additionally selects SDDM for the next boot without stopping the current desktop.
Both Hyprland (UWSM) and KDE Plasma entries must exist. No automatic reboot,
logout, reload, lock, suspend, PAM/keyring modification or service restart occurs.

HyprMod/Ollama are optional, not automatic dependencies; see
[on-demand applications](ON_DEMAND.md). thermald is a separately reviewed
Intel-specific step, not blindly enabled on every target.

## 4. Login and validate

Before leaving the existing session, confirm the fallback remains available.
Manually choose **Hyprland (UWSM)** in SDDM. UWSM manages the session's environment,
systemd user services and application lifetime. The plain Hyprland entry is not
the session this configuration is built around.

```sh
./setup verify
```

This checks only observable configuration/session/power state. It is not a full
hardware pass. Follow [VALIDATION.md](VALIDATION.md), including Intel renderer,
PRIME re-suspend, portals, repeated suspend/resume and matched power measurements.
Never remove KDE merely because `apply` or the automated tests returned zero.

## Recovery

Use the backup path printed by apply:

```sh
./setup rollback --backup /absolute/path/to/recorded-backup
```

Rollback prechecks hashes and refuses later edits or corrupt originals. It
restores recorded user files and removes only unchanged files it created.
Original backups are kept. Packages, the downloaded model and unused parent
directories remain; there is no package removal or orphan cleanup. System
integration rollback requires confirmation, preserves disabled files through
recoverable renames and restores the recorded display-manager choice for the
next boot only. Wallpaper sync after installation can change the recorded image;
if that causes a hash refusal, preserve it and have an agent review recovery.

If login fails, Ctrl+Alt+F3 gets a terminal. If only Hyprland fails, select Plasma.
For a display-manager failure, restore the **recorded** previous unit, not an
assumed unit name. On the reference migration it was `plasmalogin.service`:

```sh
# Reference-machine example only; use your recorded unit.
sudo systemctl disable sddm.service
sudo systemctl enable --force plasmalogin.service
```

Those commands select the next boot without `--now`. Do not run them blindly on
a target with a different previous manager. Do not delete a wallet or alter PAM.
