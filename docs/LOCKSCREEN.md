# Adaptive native lock screen

The reference laptop now uses Noctalia 5.2.1's native lock-screen widgets:
the current static wallpaper, subtle surface tint, large HH:MM clock in
`primary`, a quiet date in `on_surface_variant`, and a centered compact rounded
password card. Palette roles follow the existing dark wallpaper-derived
`m3-tonal-spot` theme. No wallpaper image, fixed accent palette or account data
is distributed.

The reviewed shape is saved in
[`profiles/lockscreen-reference.toml`](../profiles/lockscreen-reference.toml).
It is outside the automatically deployed configuration on purpose. Its connector
and positions describe the detected Dell panel, not an arbitrary clone's machine.
The main installer's whole-stack 5.2.0 version gate remains unchanged: validating
this 5.2.1 lock-screen profile does not qualify every installer operation on 5.2.1.
Unsupported targets must use the agent handoff, not bypass the gate or downgrade.

## Adapt safely

1. Read AGENTS.md and back up both Noctalia config and private
   `~/.local/state/noctalia/settings.toml` before making any change.
2. Inspect installed versions and `hyprctl monitors -j`. Derive logical width,
   height, output and rotation from the target. Do not assume eDP-1 or 1.25 scale.
3. Translate the reference centers and boxes to that geometry. Retain at least
   one native login box; test additional outputs separately. Do not change PAM,
   passwords, fingerprint settings, lock-before-suspend or SDDM for a visual tweak.
4. Stage an adapted `lockscreen-style.toml` fragment outside the live config.
   Inspect GUI overrides, which load last. Merge/remove only conflicting
   lockscreen_widgets fields; preserve wallpaper, theme and other private state.
5. Validate the complete staged config using the installed binary. Never append
   duplicate TOML sections blindly. No unknown-setting warnings were accepted
   for the reference styling.
6. Apply the minimal changes. Inspect the native unlocked editor with
   `noctalia msg lockscreen-widgets-edit`, on an empty workspace; exit using
   `noctalia msg lockscreen-widgets-exit`. This is a visual preview, not a password
   or real session-lock test. Editor chrome/guides are not part of the locked UI.
7. Have the owner manually test Super+L/unlock and later suspend/resume. Do not
   trigger lock, suspend, logout or reboot automatically.

The editor writes equivalent layout overrides to settings.toml, including
normalizing the reference compact login height from 72 to 70 logical pixels.
Future hand-edited fragment changes may require reconciling those GUI overrides.
Never commit the whole private settings file to make that reconciliation easier.

## Resource behavior

No separate locker, plugin, daemon, cron job or sampler was installed. Blur,
desktop capture, lock transitions and text shadows remain off. Media/weather
decorations and session-action buttons are omitted. Caps Lock, layout indication,
native password submission and auth hint/error messages remain available.

The version-matched host source clears widget instances when unlocked. Digital
formats without seconds use minute-boundary updates; there is no continuously
animated analog second hand or new frame-driven visualizer. This does not mean
zero energy while the screen is on or zero cost to render the UI.

Short unlocked observations on October 7: six 5-second samples per side, same
shell PID, mean CPU 1.866% before / 1.966% after (fraction of one core), mean RSS
198510.0 / 199286.7 KiB, approximately +0.76 MiB. NVIDIA graphics/audio were
suspended in every after sample; graphics was temporarily active in some before
samples. Foreground Firefox/agent activity was not controlled. These observations
are a sanity check, not a matched battery test or proof of a power improvement.

## Recovery and evidence

Private checkpoint directories contain original config/state, manifests and
recovery instructions. Keep them unchanged and off GitHub. Before rollback,
verify originals and preserve later edits. Reverting saved Noctalia state can
also revert later wallpaper preferences. No service/package removal is needed.

The reference pre-style rollback was exercised in a disposable home; corrupt
backup input was rejected before writing. Native config validators and unlocked
visual preview passed; unrelated preferences and existing helpers were unchanged.
Real authentication and suspend/resume checks remain owner-assisted.

Primary references (native v5, not Quickshell/v4):

- [5.2.1 lock-screen widgets](https://github.com/noctalia-dev/noctalia/blob/v5.2.1/docs/user/lockscreen/widgets.mdx)
- [5.2.1 widget host lifecycle/ticks](https://github.com/noctalia-dev/noctalia/blob/v5.2.1/src/shell/lockscreen/lockscreen_widgets_host.cpp)
- [Current configuration layers](https://docs.noctalia.dev/noctalia/configuration/)
- [Wallpaper-derived theme](https://docs.noctalia.dev/noctalia/theming/)
