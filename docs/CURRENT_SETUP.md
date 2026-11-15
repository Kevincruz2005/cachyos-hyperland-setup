# One-script coverage (2026-11-15)

Run `./install.sh` as a normal user on an **existing x86_64 CachyOS desktop**.
This is a guided installer, not an unattended OS installer or universal disk
image. It audits, resolves a plan, requests confirmation, backs up affected
files, applies reviewed modules and prints recovery/validation instructions.

## Current and legacy paths

| Component | Current combination | Legacy combinations |
| --- | --- | --- |
| Hyprland | 0.57.1 | 0.56.2 |
| Noctalia (native v5) | 5.4.1 | 5.2.0 or 5.2.1 |
| UWSM | 0.27.1 | 0.27.0 |
| Alt+Tab | Compact/MRU native held-modifier switcher | Focus-only cycling |
| Super+T | Mousepad, no server | Mousepad, no server |
| Camera | Kamoso plus explicit GStreamer base codecs | Same |
| File/naming dialogs | Scoped centering and monitor-relative size limits | Same rules |

These are combinations, not independently interchangeable version ranges.
Newer repository versions stop for adaptation rather than being downgraded,
ignored or treated as tested. Package/database health and pending updates are
reviewed before installation. A normal full update is separate; the script
does not silently update a kernel, driver, bootloader or EFI.

## Included desktop behavior

The existing export includes the minimal native Noctalia bar/launcher, static
wallpaper palette generation, GTK/Qt/Dolphin/Kitty styling, clipboards, screenshot
crop/copy/save/OCR, bounded English dictation, brightness/media/lock bindings,
power-profile actions, file manager/browser defaults and read-only RTX check on
NVIDIA hosts. No continuously running OCR, speech model, editor or camera worker
is added. Existing PipeWire/WirePlumber/NetworkManager/Bluetooth and power services
remain system responsibilities; the installer never replaces a working stack.

The current path also selects the simple launcher and compact/MRU Alt+Tab.
Known floating save/open/upload/folder dialogs receive a bounded size and
centering; known naming prompts retain their small natural size. Normal tiled
windows, including Dolphin, are not made floating. Unknown/localized dialogs
can require an additional narrow match.

The adaptive lock widgets are generated from the reference only when the target
output, resolution and numeric scale establish logical geometry. Output names
and coordinates are derived, not copied from the original laptop. If scale is
`auto` or geometry is unknown, retain the native lock layout and review it with
the owner. Rotated/multi-monitor lock behavior still needs hardware validation.

## Login and encrypted credentials

The wizard defaults to keeping the current display manager. It can offer
official Noctalia Greeter/greetd for the next boot, with SDDM/KDE retained and
without stopping the current session. This requires extra confirmations,
recognized versions/layouts and an exact protected-change preview. GNOME Keyring
hooks are a further opt-in, never a keyring reset. See [OFFICIAL_LOGIN.md](OFFICIAL_LOGIN.md).

## Deliberate exclusions and remaining review

- No private wallpaper binary, avatar, credentials, editor machine identifiers,
  browser profiles, NetworkManager identities, recordings or private backups.
- No NVIDIA renderer overrides, driver removal, laptop-specific PCI/card names,
  external-port assumptions or claimed battery-life improvement.
- No KDE removal, arbitrary orphan cleanup, BIOS/EFI/bootloader/kernel changes,
  forced logout, reboot, suspend or screen lock.
- No automated Firefox extension installation/account login. Optional application
  palette integrations still need review of the target's installed editor/browser
  and add-on profile; see [THEMING.md](THEMING.md).
- Ollama models, paid apps, account-specific IDE extensions and unrelated user
  packages are not cloned as part of this desktop installer.
- thermald and alternative power-stack decisions remain target-specific review.

If a package hook, active boot-writing snapshot watcher, custom TOML fragment,
custom login/PAM layout or unsupported version prevents safe deployment, the
script stops with a stage-specific private handoff and recovery path. Give a
coding agent `AGENTS.md`, `docs/AGENT_HANDOFF.md` and the privacy-reviewed report.
Do not remove a safety gate simply to make the script continue.

## Verification status

Isolated unit/integration fixtures and native offline config parsing cover
current/legacy generation, dialog/shortcut contracts, target geometry, rollback,
JSONC merges and narrow PAM transforms. They do not authenticate a real login.
A fresh disposable CachyOS VM package-install/login end-to-end test has **not**
been completed. The author laptop's working desktop is not used as an installer
test target. Owner-assisted GPU, camera, suspend/resume, portal and matched power
tests are required on each new machine; see [VALIDATION.md](VALIDATION.md).
