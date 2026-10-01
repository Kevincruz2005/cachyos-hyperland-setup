# Optional static SDDM integration

This is a visual fork of the installed official Breeze theme, not a PAM/session
replacement. The bundled LGPL Main.qml removes wallpaper fading/blur and clock/
logo shadows, and leaves the normal password form visible. Existing Breeze,
Login.qml, session launchers and authentication handlers remain untouched.

The adapter requires a compatible installed Breeze source. If unavailable or
changed, stop for an agent instead of installing all of Plasma just for a theme.
Do not activate an untested greeter. Stage and manually preview it:

```sh
./setup plan --sddm
# The command prints the private staged theme path and preview command.
# Run that command, inspect password form and both session entries, close preview.
./setup apply --sddm --confirm-greeter-preview
```

`--select-sddm` additionally changes the NEXT-BOOT display-manager selection;
it never starts/stops a running manager. Both Hyprland UWSM and an existing
fallback session must be available. Original selection/configuration is recorded
for rollback. Reboot/login tests are always manual.

User wallpaper sync writes only a per-user raster image, not privileged config.
Noctalia's wallpaper_changed hook runs it once for the generated primary output.
Atomic copy, size/MIME checks, lock and unchanged-image skip preserve the last
valid image. Login colors are a static palette snapshot, not continuously synced.
Animated formats are excluded in the portable adapter to preserve static behavior.

If SDDM fails, use Ctrl+Alt+F3 and the recorded rollback commands. If only Hyprland
fails, choose the retained desktop session. Never delete/reset a wallet or change
PAM. Major KDE/Qt updates require another preview; source-hash mismatch stops.
