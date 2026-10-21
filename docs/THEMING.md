# One wallpaper palette for the integrated desktop

The selected Noctalia source is wallpaper with the faithful generator and dark
mode. Unlike Material content schemes, faithful stays close to image colors;
the reference grayscale wallpaper therefore produces near-white accents rather
than the previous blue/pink Material accents. Changing palette source/generator
in Noctalia updates the same pipeline. Saved wallpaper favorites can deliberately
restore their own saved palette choices; they are not silently rewritten.

On the reference laptop, a saved favorite still carried `m3-tonal-spot`. Selecting
it changed the effective generator globally; returning to an unstarred grayscale
wallpaper kept that generator and brought back blue. The owner requested faithful
colors across those wallpapers, so the active scheme and that one favorite's
saved `wallpaper_scheme` were changed to `faithful` while preserving the image
paths, theme mode and other settings. A favorite → grayscale wallpaper round trip
then kept `faithful` and regenerated near-white accents. Other machines should
review their own favorite presets before rewriting them; a config file's
`[theme].wallpaper_scheme` can be overridden by persisted state.

## Native event-driven outputs

The enabled official native templates are GTK3, GTK4, Qt, KColorScheme, Kitty
and Hyprland. No template collection, theme polling service or GPU override is
installed. Native generation and existing apply hooks run on palette changes.

The small user template at
`config/noctalia/templates/desktop-palette.json` emits only validated color-role
values to `~/.config/noctalia/palette.json`. The screenshot helper reads that
file once at invocation, with an 8 KiB cap and neutral fallback for missing or
invalid files. Its CSS, selection border and dimension badge use those roles;
capture geometry, key actions, OCR, clipboard/save and cleanup are unchanged.
There is no screenshot theme watcher or generator subprocess.

GTK imports only the generated noctalia.css, not the old Breeze colors.css.
Existing legacy files are retained unused rather than deleted. The existing
Qt palette selection and Dolphin Noctalia scheme remain in place. Kitty uses
its existing generated include and native reload hook.

Hyprland loads the official generated noctalia.lua after the GUI settings, so
palette-controlled border/group colors win without changing gaps, monitor mode,
geometry, fonts or window rules. A fresh clone can start safely before the first
template exists; once it is generated, a config-only reload establishes the
include and normal config-file watching handles later updates.

The native lock clock uses on_surface (neutral, contrasting text), with the
date using on_surface_variant. Authentication and widget layout are unchanged.
No lock is triggered automatically to test a visual change.

## Optional application and login integrations on the reference laptop

The tested Cursor integration writes `cursor-colors.json` through Noctalia's
native template system and runs `tools/noctalia-cursor-colors.cjs` once on a
palette change. That helper uses Cursor's installed JSONC parser to merge only
`workbench.colorCustomizations`. Existing settings, comments, editor font and
syntax theme are preserved; the theme helper does not change the credential
backend. The original `kwallet6` choice was later changed separately on the
reference host; see [the authorized keyring correction](KEYRING.md). There is
no editor theme daemon or login service. Hosts without
Cursor and its JSONC parser should leave this optional template disabled.

Firefox's optional native template emits a Pywal-compatible `colors.json` with
the `wallpaper` field empty. This avoids disclosing a user's wallpaper path to a
browser add-on. Noctalia's `firefox-theme` post-action installed a user-local
native host manifest pointing to the installed `noctalia` binary. The browser
still needs the official [Pywalfox add-on](https://addons.mozilla.org/en-US/firefox/addon/pywalfox/)
enabled by the owner and Firefox restarted once; without it, the generated
colors cannot affect Firefox. Its host lives only while an enabled browser
profile uses the add-on, but it does consume some memory then. The legacy
Python Pywalfox package and Noctalia's community template are not installed
alongside this local native template, so neither competes for `colors.json`.

`profiles/theme-integrations/noctalia-apps.toml.example` documents the optional
template fragments and `profiles/theme-integrations/` contains their inputs.
They are deliberately not part of the unattended generic installer because
other computers may lack Cursor or use a different Firefox profile layout.
Check that exact host first, preserve its current preferences, then enable the
appropriate fragments and call `noctalia msg templates-apply`.

The reference SDDM theme is a copy of the installed working Breeze-based
theme with only eight Kirigami palette bindings added to `Main.qml`. A Noctalia
template writes a readable color INI into the existing user-owned
`/var/lib/sddm-wallpaper-sync/<user>/` directory on palette changes. The staged
`theme.conf.user` and now the protected reference theme point at that generated
file. The same directory already serves the SDDM wallpaper; no extra daemon is
added. An offscreen
`sddm-greeter-qt6 --test-mode` loaded the installed theme with both session
entry files present, but this cannot establish visual quality or authentication.
The protected reference `Main.qml` and `theme.conf.user` changed only after a
private backup and exact-file preflight; `/etc/sddm.conf.d`, SDDM service,
PAM and session launchers stayed unchanged.
`profiles/theme-integrations/sddm-palette-preview.qml.inc` records
the optional root-item properties for the **exact reviewed** reference
Main.qml; adapt and retest if KDE changes its theme source. Never activate an
uninspected greeter.

On the reference host, manually inspect with:

```sh
sddm-greeter-qt6 --test-mode --theme "$HOME/.local/share/noctalia/sddm-palette-preview"
```

Close the preview without authenticating, then verify the password form,
wallpaper, clock and both session choices. The preview lives under the owner's
nontraversable home directory and must never be selected as the live SDDM path.
On a different host, protected deployment requires its own backup, compatible
theme source, preview, rollback and owner approval; the portable installer does
not activate this optional palette binding. Noctalia's lock layout is separate
from SDDM's Breeze login layout.

Private checkpoint on the reference laptop:
`~/theme-apps-backup-20261012-0IOsNE` (never publish or modify). To recover
Cursor, remove only the managed `workbench.colorCustomizations` entry using
the original `Cursor/settings.json` as a reference. Disable the corresponding
Noctalia user templates, preserving newer wallpaper and editor choices.
For Firefox, deactivate/remove the add-on in Firefox; Noctalia's own manifest
can be removed with `noctalia firefox-theme uninstall` after inspecting it.
The later protected SDDM change has its own separate private checkpoint and
exact-file rollback helper. Do not use the older application-theme backup to
restore SDDM.

## Limits

GTK/Qt integration does not recolor arbitrary web content or application-managed
editor syntax themes. Apps that cache colors may require a manual reopen.

SDDM still uses the working Breeze-derived greeter and last synced static
wallpaper. On the reference laptop its controls now read the persisted Noctalia
palette at greeter startup. This is event-driven: changing a wallpaper in
Noctalia updates the saved image and color file, while boot uses the last saved
values. It does not run Noctalia or a polling service at the login screen.
Other computers retain the portable adapter's default Breeze controls until a
separately reviewed protected deployment.

## Validation and recovery

The reference GTK/Qt/KDE/Kitty colors and live Hyprland border were checked against
the generated shared palette. Installed GTK parsed the screenshot CSS without
errors; isolated tests cover valid, missing, oversized and malformed palette
input. AST comparison verified the screenshot workflow methods stayed unchanged.
Private backup comparisons verified original fonts, GTK settings, wallpaper,
favorites and GUI layout settings were retained. NVIDIA graphics/audio were
observed suspended after the refresh. This is not a matched power benchmark.
Manual visual and real lock/authentication acceptance remain owner-assisted.

Recover selectively from the recorded private checkpoint. Restoring the whole
Noctalia settings file can discard later wallpaper preferences, so preserve
later edits and restore only affected theme fields where possible. Disable the
new template/include only after inspecting current files; do not bulk replace
configuration or remove KDE/Qt libraries.

Primary references:

- [Native theme templates](https://github.com/noctalia-dev/noctalia/blob/v5.2.1/docs/user/theming/templates.mdx)
- [Native app theming](https://github.com/noctalia-dev/noctalia/blob/v5.2.1/docs/user/theming/app-theming.mdx)
- [Installed built-in templates](https://github.com/noctalia-dev/noctalia/tree/v5.2.1/assets/templates)
