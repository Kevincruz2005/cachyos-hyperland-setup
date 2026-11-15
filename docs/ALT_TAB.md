# Optional native Windows-style Alt+Tab

The reference laptop now uses native Noctalia's compact visual switcher with
recently used windows first. This profile was reviewed with Hyprland 0.57.1,
Noctalia 5.4.1 and UWSM 0.27.1. It adds no package, plugin, daemon or polling
script, and never automatically maximizes or changes window layout.

This started as an **optional reference profile**. Since the November 15 update,
the installer selects it automatically for the exact current desktop combination
above; legacy combinations retain focus-only Alt+Tab. Its fragments are still
available for separately reviewed manual use. Version gates remain in place.
Do not bypass those gates or upgrade/downgrade a working machine merely to apply
this profile. Review current installed APIs before adapting it elsewhere.

## Behavior

- Hold Alt and tap Tab to open the compact switcher; keep tapping to move forward.
- Shift+Tab moves backward while the overlay is open.
- Release Alt to activate the selected window; Enter also accepts.
- Escape cancels without switching. Quick taps use native modifier-release handling.
- Super+Tab remains the existing visual-switcher shortcut.
- On Noctalia 5.4.1, Alt+Shift+Tab from a **closed** overlay retains the original
  native previous-window action. This version's IPC cannot request reverse
  initial selection; do not use a newer `reverse` command without checking support.

The switcher retains the existing output/workspace scope. MRU ordering is based
on window-focus events, not polling. Previews and rendering still use resources
while the overlay is visible; this is not zero resource use or a battery benchmark.

## Apply only after review and backup

1. Save private, timestamped copies of the target's Hyprland and Noctalia
   configuration plus Noctalia's state-dir `settings.toml` and `state.toml`.
   Keep them outside this repository. Do not publish paths, histories or user state.
2. Confirm installed `noctalia msg window-switcher --help` accepts `hold`.
   The reference uses Lua bindings, not older Hyprland text configuration.
3. Replace the existing three Tab bindings with
   [binds.lua.example](../profiles/window-switcher/binds.lua.example), preserving
   the existing `mainMod` and `noctCall` definitions. Do not source or append a
   second set of conflicting bindings.
4. Merge only `style = "compact"` and `mru = true` into the existing
   `[shell.window_switcher]` table, or add that one table if absent. See
   [noctalia.toml.example](../profiles/window-switcher/noctalia.toml.example).
   Inspect effective settings and state overrides first; do not copy a whole
   settings file or overwrite the user's other switcher preferences.
5. Update the target's shortcut descriptions to match the behavior above.
   Validate both configurations before a config-only reload. Do not restart
   the compositor or shell, log out, lock or reboot for this change.
6. Read back `noctalia msg config-get shell.window_switcher` and inspect
   `hyprctl configerrors` and registered bindings. Manually test quick taps,
   hold/cycle/release, Shift+Tab, Escape, tiling and fullscreen applications.

## Recovery

Record hashes of each original and changed file in the private checkpoint.
To undo, close the overlay with `noctalia msg window-switcher close`, restore
only the reviewed bindings, shortcut descriptions and two switcher preferences,
then reload compositor configuration. Compare current hashes first; if there
are later edits, merge selectively instead of replacing the entire file.
No sudo, package removal, theme reset or service restart is required.

The reference's private rollback helper verifies backup/current hashes and
refuses later edits. It is intentionally not exported: its fixed file hashes
and machine paths are not portable. Generic installer rollback still follows
the receipts described in [INSTALL.md](INSTALL.md).

## Evidence and limits (2026-11-14)

The reference configurations validated and a live configuration-only reload
reported no config errors. Effective settings read back compact/MRU enabled.
A bounded open/close test found the native switcher layer, then verified its
removal with the focused window unchanged. A disposable recovery test restored
all three original files, verified idempotence and rejected unexpected later
edits. No failed system or user services were listed.

Physical-key timing, rapid taps, reverse cycling and owner acceptance remain
manual tests; they are not claimed complete. No energy measurements were taken.
Tiling, gestures, theme, wallpaper, power/GPU settings, login, packages and boot
configuration were untouched.

References:

- [Noctalia 5.4.1 shell configuration](https://docs.noctalia.dev/noctalia/v5.4.1/configuration/shell/)
- [Tagged 5.4.1 switcher implementation](https://github.com/noctalia-dev/noctalia/blob/v5.4.1/src/shell/switcher/window_switcher.cpp)
- [Tagged 5.4.1 modifier-release handling](https://github.com/noctalia-dev/noctalia/blob/v5.4.1/src/shell/switcher/window_switcher_shortcut_state.h)
