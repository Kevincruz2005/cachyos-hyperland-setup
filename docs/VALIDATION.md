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
- [ ] Real microphone and English/Tamil/code-switched dictation accuracy are accepted.
- [ ] Super+H off-state has no dictation unit/process/cgroup/runtime recordings.

`./setup verify` only gathers observable configuration/power state and prints the
remaining manual checks. It does not trigger microphones, suspend, lock or GPU
benchmarks. Retain KDE while any important item is uncertain.

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
