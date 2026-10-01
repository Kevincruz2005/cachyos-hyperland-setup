# Appearance and assets

The reference uses the static pink train/cherry-blossom Wallhaven yqg6r7 image.
It is intentionally not bundled, downloaded automatically, or replaced with
an AI imitation. Visit the source link yourself and, if you may use it, supply
a local file with `./setup apply --wallpaper /absolute/path/image.jpg`.

Reference SHA-256:
`448fca111b8a60f2dc2298dac11b049687283ad11c672e9447f0f876aa0ba928`.

Without that image, the installed CachyOS north.png fallback is used. Palette
snapshots provide readable colors before Noctalia starts; Noctalia regenerates
the palette for your selected image, so an alternative image changes colors.

Font installation uses repository packages, not the author's font binaries.
The required face is **JetBrainsMono Nerd Font**, not its `Mono` icon-width
variant. `fc-match 'JetBrainsMono Nerd Font'` and `fc-match 'Adwaita Sans'`
should resolve correctly. Cursor assets are copied from the official installed
CachyOS skel when available; no font/cursor archive is vendored here.

Only desktop-related INI keys are merged into GTK, qt6ct, KDE, Dolphin and MIME
settings. File-picker history, unrelated associations, wallets and complete
kdeglobals are not exported. Existing target config is backed up before edits.
GTK4 imports the local Noctalia stylesheet, not a light Breeze stylesheet.

Noctalia state files are not copied wholesale: the installer emits only theme/
wallpaper choices and a centered default lock behavior. Disabled, output-specific
lock-widget editor coordinates and unrelated session state are omitted.
