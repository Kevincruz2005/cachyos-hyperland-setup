# Provenance and privacy

The baseline was captured from an existing CachyOS laptop on 2026-10-01.
Live configuration wins over older chat summaries. Recovery reports establish
historical decisions; missing evidence is labeled, not reconstructed as fact.

| Material | Source / license boundary |
| --- | --- |
| Hyprland/Noctalia/Kitty/UWSM configuration | Adapted from [CachyOS official configuration](https://github.com/CachyOS/cachyos-hypr-noctalia), package 1.2.6-1, declared GPL-1.0-only; retain that license on derived configuration |
| Original installer, helpers and documentation | MIT, except explicitly upstream-derived material |
| Static SDDM Main.qml | KDE Breeze; original SPDX LGPL-2.0-or-later header retained; other Breeze assets copied from the installed package on the target |
| Palette snapshots | Generated color values; no wallpaper bitmap included |
| Fonts/cursors/packages | Install official packages or verified upstream assets; never treat their licenses as the repository's MIT license |
| Whisper model | Upstream whisper.cpp model URL and SHA-256; downloaded only on explicit request, not committed |
| Wallpaper | [Wallhaven reference yqg6r7](https://wallhaven.cc/w/yqg6r7); redistribution rights unverified, therefore not bundled |

Package metadata is evidence of CachyOS's declared distribution license; its
upstream repository did not expose a root LICENSE at capture time. This
repository retains the package declaration instead of claiming MIT ownership
of that configuration. Resolve any upstream licensing discrepancy before
relicensing; external applications retain their own licenses.

Allowlist: desktop Lua/TOML, selected appearance settings, palettes, reviewed
helpers and sanitized summaries. Excluded: raw migration archives, KDE Connect
identity keys, wallets, browser history/accounts, SSH/cloud credentials, machine
IDs, recordings, current process command lines, unrelated app associations,
private wallpaper bitmap, package archives and model/font binaries.

The existing dotfiles repository and its uncommitted changes are not imported.
Publication checks cover the full Git history, not only the final working tree.

The publishing helper follows the official [GitHub CLI authentication](https://cli.github.com/manual/gh_auth_login)
and [existing repository inspection](https://cli.github.com/manual/gh_repo_view) workflow.
Browser authorization must finish in the initiating CLI; verify the actual identity
with `gh api user --jq .login` before publishing. Never paste tokens into a chat.
The owner-selected destination is the existing private
`Kevincruz2005/cachyos-hyperland-setup` repository. Publication does not create
another repository or change visibility. Private status does not relax the
allowlist or privacy checks, and collaborators need explicit repository access.
