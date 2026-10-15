# Validation evidence and remaining checks

Configuration export date: 2026-10-01. Reference hardware: Dell G15 5530,
i5-13450HX, RTX 3050 6 GB, approximately 15.3 GiB RAM; installed kernel
7.2.8 CachyOS and NVIDIA 615.71.09 open modules. These are observed values, not
versions the installer is allowed to install or replace.

## What evidence exists

- User manually entered Hyprland; both session entries and SDDM selection exist.
- Passive sysfs reads observed NVIDIA graphics/audio runtime-suspended while idle.
- Full-history publication scan and isolated pure safety/portability tests pass.
  Run `python -m unittest discover -s tests -v`; these tests never start dictation,
  write live desktop config or perform a privileged package/login change.
- Native Hyprland `--verify-config` and Noctalia `config validate` passed for
  exported/generated configuration in a disposable directory, without a live reload.
- Screenshot coordinate tests cover all corners at four scaling factors.
- Public English speech fixture: approximately 11 seconds of audio recognized in
  1.04 seconds elapsed, 1.94+0.07 seconds CPU time, 130,364 KiB maximum RSS.
- Live **fixture** text-field test peaked around 133.3 MiB cgroup memory, final
  stop around two seconds; runtime directory/unit/cgroup disappeared. This is
  not a real microphone/Tamil recognition test. Some words remained inaccurate.
- Dictation failure fixtures covered a failed recorder, stuck recognizer, main
  process crash and SIGTERM-resistant worker. Cleanup was observed; the hard
  systemd fallback took approximately 15.27 seconds in that failure test.
- NVIDIA remained suspended during CPU-only speech fixture tests. An initial
  GTK test UI probed Vulkan; using Cairo avoided that test-induced GPU wake.

New clone/apply package and greeter operations have not been end-to-end tested in
a disposable CachyOS VM. Pure tests and offline schema validation do not substitute
for that. Do not advertise unattended production readiness on arbitrary hardware.

## Recorded KDE baseline (2026-09-29)

Five-minute settle, ten-minute sample window, 31 samples at 20-second spacing.
Battery power, 50% brightness, 60.01 Hz, power-saver, Wi-Fi on, Bluetooth soft
blocked, keyboard lighting off, foreground apps closed; the agent session stayed
open. This predates the later thermald setup, another comparison confounder.

| Observed metric | Mean | Recorded range |
| --- | --- | --- |
| Used RAM | 3735.11 MiB (3.65 GiB) | 3722.06–3746.24 MiB |
| CPU busy, fraction of total machine capacity | 3.02% | 2.94–3.35% |
| Battery discharge | 18.28 W | 18.00–18.50 W |
| NVIDIA graphics/audio | Suspended in every sample | Suspended |

A comparable controlled Hyprland sample set was not found. Therefore there is
**no verified KDE-versus-Hyprland battery improvement**, no fabricated RAM delta
and no projected battery-hours claim. An idle screenshot or instantaneous reading
is not a matched A/B benchmark.

## Owner-assisted hardware checklist

- [ ] SDDM starts; final greeter authenticates; Plasma still launches.
- [ ] Hyprland (UWSM) starts and reports no configuration errors.
- [ ] Compositor and normal OpenGL/Vulkan apps use Intel, not RTX.
- [ ] `prime-run` uses NVIDIA; both PCI functions re-suspend after exit/settling.
- [ ] Wi-Fi/Bluetooth/audio/microphone and physical brightness/media keys work.
- [ ] Touchpad/tap/scroll/gestures and tiling/focus/fullscreen behave as intended.
- [ ] Lock/lid/suspend/resume work repeatedly without a black screen; Wi-Fi returns.
- [ ] Notifications, clipboard, screenshots, launcher, terminal and Dolphin work.
- [ ] Qt/GTK apps, dark styling, browser file picker and polkit prompts work.
- [ ] Portal screen/window/monitor sharing and browser video playback work.
- [ ] No failed critical services, unexpected polling or abnormal Noctalia idle CPU.
- [ ] If used, external monitor behavior is tested separately with known GPU wiring.
- [ ] Matched KDE/Hyprland power samples exist before any KDE removal recommendation.
- [ ] Real microphone and English-only dictation accuracy are accepted.
- [ ] Super+H off-state has no dictation unit/process/cgroup/runtime recordings.
- [ ] Helium launches with Super+B, is the default URL browser and file picker works.
- [ ] Kamoso previews the camera; closing it releases the camera on this hardware.

`./setup verify` only gathers observable configuration/power state and prints the
remaining manual checks. It does not trigger microphones, suspend, lock or GPU
benchmarks. Retain KDE while any important item is uncertain.

## Browser and camera export (2026-10-15)

The reference machine reports official CachyOS `helium-browser-bin` 0.19.2.1-1
and `kamoso` 26.08.2-1.1 installed. Live Super+B launches `helium-browser`,
while Super+W still launches Brave. The UWSM `BROWSER` and web MIME defaults
point to Helium. The portable package/configuration export now matches those
choices and includes the English OCR packages required by Print Screen's O key.

A prior live Kamoso test opened the webcam and closing the window released it;
PipeWire is retained for normal AV services. This is not a cross-machine
guarantee. Helium launch, browser portals and real camera behavior remain
owner-assisted checks on a fresh target. No camera-only daemon/autostart or
GPU routing change was added. The single-command installer wraps the existing
audited/interactive deployment and has not undergone a fresh-VM package/login
end-to-end test.

## SDDM adaptive palette activation (2026-10-15)

After an owner-approved visual-only change, the reference SDDM Breeze-derived
theme's `Main.qml` contains the same eight Kirigami palette bindings as the
pretested user-owned candidate. Its `theme.conf.user` resolves to the
event-generated, greeter-readable Noctalia wallpaper/color INI. A fresh private
backup of the active theme, SDDM configuration, both session entries, current
wallpaper/palette and relevant Noctalia settings was checked before deployment.
Only those two protected theme files changed; SDDM remained active and enabled,
and both Hyprland (UWSM) and Plasma entries were still present afterward.

The SDDM account could read the palette. The installed theme ran for an
eight-second offscreen `sddm-greeter-qt6 --test-mode` interval with no reported
errors, then exited by the test timeout. This does not verify visual quality,
password authentication, actual boot login or later wallpaper changes. Those
remain owner-assisted; no restart, logout, lock, suspend or reboot was triggered.
The Noctalia lock layout and authentication were not changed. A private
exact-file rollback helper and pre-change checkpoint remain local to
the reference machine, not in the public export.

## Native cursor zoom (2026-10-15)

The existing Super+Plus/Minus Hyprland callbacks now use a bounded 1×–10×
native zoom with crisp pixels. Both the live and exported Lua configurations
passed `Hyprland --verify-config`; a config-only reload reported no errors.
Readback after reload showed `cursor:zoom_factor` at 1.0, with pixel zoom,
rigid cursor-follow and non-detached camera options active. No package, GPU
routing, background service or polling process was added. Physical-key
operation failed owner testing. The old Lua getter used `cursor:zoom_factor`
rather than the documented dotted name, while the old keypad `code:` binds
registered with keycode 0. The follow-up uses the
documented `cursor.zoom_factor` getter, `Super+Shift+=` for the US keyboard's
Plus key, and `KP_Add`/`KP_Subtract`. Physical-key operation still requires an
owner check. Idle battery power was not measured in this configuration-only test.

## English-only dictation update

The owner subsequently chose English-only Tiny.en q5_1 with explicit language
`en`. Three interleaved public-audio trials after warmup observed median elapsed
time 0.59 s versus 1.05 s for the previous multilingual model, and CPU time
1.07 s versus 1.96 s, with zero normalized word error for this sample in both.
Peak RSS remained about 125 MiB; NVIDIA graphics/audio stayed suspended before
and after. One thread offered essentially the same CPU time but slower results,
so the existing two-thread limit was retained. See [DICTATION.md](DICTATION.md)
for conditions, reproduction and limitations. This does not establish battery
energy savings or real microphone accuracy.

An isolated transient-service fixture retested the updated live English helper
with the same production resource/stop limits, separate unit/runtime names,
mocked focus and text injection, and no microphone. Two phrases were recognized;
normal finalization completed in 0.59 s and emergency cancellation in 0.07 s.
In both cases every observed test process, cgroup and runtime directory was
gone, with MainPID 0 and the transient unit unloaded. Those timings are fixture
observations, not guaranteed stop times; the existing 12/15-second finalization
and manager bounds remain. Real focus/text-field/microphone checks remain manual.

## Screenshot text OCR (2026-10-06)

The preview's O key runs installed Tesseract 5.5.3 English OCR
only on demand, with one OpenMP thread, nice 10 and an independent 20-second
timeout. Synthetic light and dark two-line images were recognized as expected
in 0.13/0.15 seconds; a blank image returned no text in 0.10 seconds. Cumulative
child-process peak RSS was about 89 MiB for these fixtures. These tiny fixtures
are not full-screen performance, accuracy or battery-life guarantees.

Actual OCR workers exited and their unnamed temporary output files closed.
Real subprocess fixtures verified scoped cancellation/reaping and the independent
timeout wrapper. Isolated controller tests cover O/o, duplicate-key prevention,
busy Esc, UTF-8 text clipboard routing, empty/error preservation of the preview
and active timer/worker cleanup. They mock clipboard access and never capture
the user's display. End-to-end physical Print/crop/O/paste and visual card checks
remain owner-assisted; tests did not overwrite the user's clipboard.

Follow-up real startup check found the reference machine's `gtk4-layer-shell`
dependency had been removed on October 5 alongside Ghostty leftovers. Python
failed at importing `Gtk4LayerShell`, before either the original or OCR UI could
open. Isolated OCR tests did not detect that missing host dependency. The
preview has been returned to the original three buttons (C copy, Enter save,
Esc cancel); O is keyboard-only after crop/F capture.

After owner approval, the signed official `gtk4-layer-shell` 1.3.0-1.1 package
was restored in a reviewed one-package transaction: no upgrades or removals.
Snapshot hooks were suppressed for that transaction only, and the snapshot
watcher was temporarily stopped with its writer runtime-masked. Initial cleanup
attempted to start the watcher before removing its target's mask and failed;
the corrective cleanup removed the temporary mask first and restored the watcher.
Final checks found the watcher active, its writer inactive, no runtime mask,
45 package files with none missing, and unchanged checksums for the inspected
GRUB configuration files. No boot-generation command was executed.

Real Wayland GTK tests of the live helper then passed full-capture/C image copy,
bottom-right crop/Enter save, full-capture/O English OCR, blank OCR returning to
the preview without changing the clipboard, and actual screen capture/Esc
cancellation. Clipboard writes were intercepted and test saves redirected to a
private temporary directory; no user's clipboard or Pictures files were changed.
Each temporary capture directory disappeared and observed OCR workers were
reaped with their output files closed. The test UI used Cairo; NVIDIA graphics
and audio were runtime-suspended before and after. All 73 isolated tests passed.
Physical Print/crop/O/paste remains owner-assisted; these checks do not establish
full-screen accuracy or zero energy cost while recognition is active.

## Screenshot presentation update (2026-10-07)

The screenshot card now uses plain text labels, flat buttons and a restrained
border instead of emoji decorations, gradients and a large shadow. Capture,
fractional-scale coordinates, keyboard actions, clipboard/save operations and
bounded OCR logic were preserved. AST comparison against each private original
confirmed that only string literals changed in the live and exported helpers;
the installed GTK CSS parser reported no errors. All 77 isolated tests passed.
No new process, service or dependency was added. This presentation-only check
did not capture the screen or modify the clipboard; visual acceptance remains
owner-assisted.

## Native adaptive lock-screen update (2026-10-07)

Noctalia 5.2.1 native clock/date and compact login styling passed staged/live
schema validation and an unlocked visual preview. The original backup stayed
unchanged and its recovery was exercised only in a disposable home. No packages,
daemons, authentication handlers or idle timeouts were changed. Unrelated
preferences and existing helpers stayed unchanged. See [LOCKSCREEN.md](LOCKSCREEN.md)
for the exact role-based profile, short resource observations and manual checks.
The profile is a reviewed reference, not a new automatic installer version gate.

## Dolphin tiling correction (2026-10-12)

Removed the normal Dolphin rule that forced floating, fractional sizing and
cursor-relative placement. Generic transient/modal handling was left unchanged.
Native live/export configuration validation passed. After a config-only reload,
a Dolphin window launched through the Super+E command reported class
org.kde.dolphin and floating=false. No existing windows were closed; monitor,
theme, power and package settings were not changed. A regression test guards
against reintroducing the removed rule; all 81 isolated tests passed. Dialog
interaction remains owner-assisted rather than claimed as an end-to-end pass.

## Optional palette integrations (2026-10-12)

The live Noctalia v5 configuration validated with one-shot Cursor/Firefox
templates and a user-owned SDDM palette preview. Cursor's settings received
73 UI color overrides from the faithful wallpaper palette; its unrelated
auto-detect setting and `kwallet6` argv preference stayed unchanged. The
Firefox colors payload and Noctalia native messaging manifest were created,
but the Pywalfox extension is not installed, so Firefox theming is pending.
No extra system/user service was enabled.

The staged Breeze-derived SDDM QML initially rejected two unsupported theme
properties. Those were removed. A second offscreen `sddm-greeter-qt6 --test-mode`
run loaded the corrected QML and both session desktop entries; the bounded
test ended normally by timeout. It cannot prove appearance, keyboard entry or
authentication. The active protected theme/config checksums still match the
pre-change backup. The owner must visually inspect the preview before any
protected greeter deployment. All 94 isolated tests and the publication scan
passed; the generated shared palette validated.

NVIDIA graphics/audio were both runtime-suspended just after the initial
palette refresh. After the offscreen greeter tests, graphics was repeatedly
`active` while audio was `suspended`; Hyprland held `/dev/nvidia0`,
`/dev/nvidiactl` and the NVIDIA DRM card. The cause was not isolated, so this
turn does **not** establish unchanged idle power or reliable graphics runtime
suspend. No renderer override or GPU service change was made. Re-test on an
otherwise settled desktop before claiming battery optimization.

## On-demand RTX status tile (2026-10-13)

The local Noctalia v5 shortcut and passive sysfs helper passed plugin lint,
native config validation, and synthetic PCI-function tests. Live Noctalia 5.2.1
listed the plugin as enabled and logged the shortcut instantiating when Control
Center opened; Hyprland stayed running with no config errors. Both NVIDIA
functions were observed `suspended` in `D3cold` and video memory `Off` after
deployment. The helper started no persistent process, and no driver, service,
display manager, or boot setting was changed. The owner clicked the tile and
received an "NVIDIA awake" notification. That is a valid instantaneous result.
Two later passive samples found both NVIDIA functions back in `D3cold`; their
active-time counters did not increase between samples while suspended-time
counters did. The cause of the brief wake is unconfirmed. This check is not a
battery-life measurement or evidence that NVIDIA never wakes briefly.

## Matched A/B procedure

Use the same brightness, actual refresh rate, power profile, radios, keyboard
lighting and foreground-app state. NVIDIA must be suspended in **both** sessions.
Keep the same measurement tool/agent overhead, allow at least five minutes to
settle, then take multiple samples over ten minutes. Record used RAM, `/proc/stat`
CPU deltas, battery `power_now` or matched `energy_now` deltas and passive runtime
PM state for every NVIDIA function. Record missing battery telemetry instead of
inventing it. Repeat if temperatures/background jobs differ. Never measure idle
PM with a continually refreshing nvidia-smi. Investigate any worse result before
recommending KDE cleanup.
