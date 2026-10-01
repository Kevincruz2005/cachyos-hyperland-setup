# Reconstructed migration history

This is a sanitized reconstruction from current files and available migration
reports, not an assertion that every chat survived. Missing tests are explicitly
unknown. Git commits document the export implementation with real commit dates;
they are not backdated to impersonate the original conversations.

## 2026-09-29: preserve KDE and establish recovery

Audited an existing Dell G15 5530 with Intel i5-13450HX, Intel i915 graphics and
RTX 3050 6 GB with NVIDIA open kernel modules. Original GPU addresses are reference
facts only: Intel `0000:00:02.0`; NVIDIA graphics/audio `0000:01:00.0/.1`.
The internal LG panel advertised 1920×1080 at approximately 60.012 and 120 Hz.
60.01 Hz was selected for the battery baseline; Intel owns the internal panel.
HDMI ownership was identified as NVIDIA; USB-C wiring was not established.

Private package/service/configuration recovery data was captured before changes.
A normal full update included nine packages. A Plymouth-triggered initramfs
rebuild was authorized separately, the existing image backed up, free space
checked and mkinitcpio completion/image existence verified. The current kernel,
NVIDIA driver, bootloader configuration and Windows/EFI were not replaced.

The controlled KDE measurement used a five-minute settle and 31 samples at
20-second intervals over ten minutes. See VALIDATION for actual values and
limits. It is not a promised battery-life estimate.

Official `cachyos-hypr-noctalia` 1.2.6-1 brought the CachyOS Hyprland stack and
dependencies (51 official packages in that installation transaction). Only the
conflicting `cachyos-kde-settings` 4.9-8 defaults/settings package was removed;
Plasma itself remained. Current Hyprland 0.56.2, native Noctalia 5.2.0 and UWSM
0.27.0 are the exported tested tuple. No Caelestia or Quickshell/v4 rice was used.

## 2026-09-30: controlled graphical fallback and workflow

SDDM was selected with `systemctl enable --force`, without `--now`, while the
existing KDE session continued. Plasma Login Manager package/configuration were
retained. Both Plasma and Hyprland (UWSM) entries were verified, and the owner
later logged into Hyprland manually. No automatic reboot/session termination.

The preferred workflow distinguishes maximize from F11-style client fullscreen:
Super+F maximizes; Super+Shift+F requests true fullscreen. Alt+F4 closes; Super+D
hides/restores the desktop. Calculator and Print keys have dedicated actions.
Alt+Tab's automatic maximize/fullscreen behavior was removed after reported
tiling/gesture collisions. Three-finger up maximizes, down restores; four-finger
horizontal switches workspaces. Accidental horizontal floating gestures were
disabled. Current shortcut truth is `config/hypr/SHORTCUTS.txt`, not an old summary.

JetBrainsMono Nerd Font/Kitty and dark GTK/Qt styling were integrated. Dolphin's
Noctalia scheme was manually selected; generated lowercase/uppercase scheme
aliases avoid a case mismatch. Noctalia derives accent colors from a static
wallpaper. The later interruption check did not find an unfinished unsafe system
change. Current HyprMod effective overrides are deliberately exported: zero gaps,
black active border and 125% reference-panel scaling, not an earlier look.

KDE Connect was stopped for Hyprland, but retained for KDE through a session-scoped
autostart exclusion. Exactly hyprpaper, Alacritty and Ghostty were removed after
approval without recursive dependency/orphan removal. GTK4 Layer Shell remained
because the screenshot utility needs it. Ollama became manual start/stop, retaining
installed models/packages. Closing an Ollama client does not stop its server.

The blue login appearance was changed by a static Breeze greeter fork, leaving the
normal password field/authentication intact. Wallpaper synchronization uses one
event hook and atomic file copy, no polling daemon. The requested hidden-password
Enter-to-reveal design was not forced into an unsupported/brittle auth workflow.
Next-boot authentication with the final theme still requires an owner-confirmed test.

An old GRUB snapshot watcher had an existing permission-related failure in local
records. It was not "fixed" by loosening permissions or rewriting GRUB. The
export guard blocks such independent watchers rather than treating hook suppression
as sufficient. Do not reproduce an unrelated machine failure as a desktop feature.

## 2026-10-01: screenshots and bounded offline dictation

The custom crop overlay originally confused logical GTK dimensions with original
pixels at 125% scale, showing a zoomed top-left region. Pixel-edge conversion now
uses floor/ceil and actual viewport/image dimensions; the overlay covers the bar
without reserving space. Corner/edge tests cover 100%, 125%, 150% and 200% scaling.
The portable version rejects untested multi-output capture rather than cropping
the wrong screen. Interactive physical crop/save checks remain manual.

Super+H toggles offline multilingual voice typing through whisper.cpp Tiny q5_1,
two CPU threads, bounded transient systemd service/cgroup and wtype. Silence does
not load a model. Second press stops recording immediately, drains a final phrase
for a bounded period and stops the entire cgroup. Emergency cancel discards it.
No permanent service, microphone listener, transcript archive or idle model remains.
Public English audio and failure/cleanup fixtures were tested; real microphone and
English/Tamil mixed-language quality were not established. See DICTATION/VALIDATION.

## Repository export

The export is allowlisted, not a copy of the home directory or raw recovery archives.
It excludes identity keys, wallets, models, recordings, accounts and wallpaper
bitmap. The wallpaper is referenced rather than redistributed. Source licenses
are retained separately from original MIT helper/installer code.

The staged adapter generates host-specific paths/modes, performs narrow reviewed
package/system stages, saves receipts and stops with an agent handoff when it
cannot safely complete. Automated tests never apply it to the working laptop.
Successful installation in a disposable CachyOS VM has **not** yet been established;
version-gated deployment must remain conservative until that end-to-end test exists.
