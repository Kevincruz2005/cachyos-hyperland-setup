# CachyOS · Hyprland · Noctalia

A battery-first desktop developed on a Dell G15 5530: official CachyOS
Hyprland + Noctalia v5, UWSM, Intel desktop rendering and NVIDIA on demand.

**An existing-system migration, not a fresh OS installer.** KDE remains a
recovery option. This is a reproducible desktop configuration, not an image
of someone's home directory. No credentials or private backups are included.

The configuration and isolated recovery tests are validated; the privileged
installer has **not** yet completed a disposable-CachyOS-VM end-to-end test.
This is a conservative version-gated adapter, not an unattended universal installer.

## Start here

```sh
git clone https://github.com/Kevincruz2005/cachyos-hyperland-setup.git
cd cachyos-hyperland-setup
./install.sh
```

The script offers a login choice, runs audit, shows a plan, then asks you to type `APPLY` before any
package/configuration changes. Optionally pass `--wallpaper
/absolute/path/to/your/static-wallpaper.png` to use your own image; the author's
personal wallpaper is not included. Existing login is preserved by default;
official Noctalia Greeter/greetd is a separately approved **next-boot** option.
Reboot is always manual. Read [installation](docs/INSTALL.md) before applying anything.
CachyOS-first;
other distributions and untested versions stop with an agent handoff instead
of executing guessed package commands. Never pipe downloaded scripts into sudo.
This project is intended for public reuse. The owner controls repository visibility;
if it is private, cloning requires granted access. Private backups, account state
and photos are never part of the export. No setup/publishing command changes
repository visibility.

## What this reproduces

- Dark wallpaper-derived GTK/Qt/Kitty colors and Dolphin integration.
- Adwaita Sans, JetBrainsMono Nerd Font, Bibata cursor and minimal Noctalia bar.
- Current window/gesture shortcuts, Windows-style show desktop, maximize separate from true fullscreen.
- Mousepad on Super+T and bounded, centered floating file/naming dialogs.
- On the reviewed current stack, compact/MRU Alt+Tab with release-Alt selection.
- Native cursor-following screen zoom up to 10×, with no idle magnifier process.
- Interactive Print Screen crop/preview/copy/save and on-demand English text OCR, with fractional-scale fixes.
- Offline English-only phrase dictation, with no idle model/listener and whole-cgroup cleanup.
- Event-driven power profiles and SDDM wallpaper synchronization; no new polling daemons.
- On NVIDIA hosts, a one-click, read-only Noctalia Control Center RTX power-state check; no live GPU-off switch or monitoring loop.
- Native adaptive lock-screen reference profile, with separately reviewed host-specific layout.
- Native default/no-photo avatar preference; no personal avatar is redistributed.
- Helium as the default browser and Super+B target, with Brave on Super+W; Firefox remains available.
- Kamoso plus its GStreamer base codecs, on demand without a camera-only service.
- Optional right-click network icon shortcut to the installed KDE profile editor; no bundled network identities.
- KDE fallback, portals, networking/audio/Bluetooth and optional on-demand local AI.

The current desktop adapter covers **Hyprland 0.57.1 + Noctalia 5.4.1 + UWSM
0.27.1** as a combination, alongside the older legacy combinations. Unknown or
mixed versions stop; no pinning/downgrades or unattended OS update is performed.
See [current coverage and limits](docs/CURRENT_SETUP.md). Account data, private
backups, wallpaper images and hardware validation are not cloned.

For an explicit full-desktop plus official-login review in the same script:

```sh
./install.sh --login noctalia --gnome-keyring --wallpaper /absolute/path/to/your-wallpaper.png
```

These options do not skip approvals. Login/PAM has additional confirmations and
an exact protected-change preview; the final phrase is `ENABLE NOCTALIA LOGIN`.
Keeping the existing login is also supported with `./install.sh --login keep`.

Current Dell tuning includes 125% display scaling, zero gaps and black active
borders. A generic host receives detected display settings rather than eDP-1
or a copied PCI address. Exact appearance requires supplying the referenced
wallpaper; the image itself is not redistributed.

## Safety contract

No automatic KDE removal, kernel/driver replacement, bootloader/EFI/partition
changes, Windows changes, TLP, global NVIDIA forcing, orphan cleanup, reboot
or session termination. Package and system-level steps require review. Unsupported
versions or hardware stop for adaptation; cloning alone cannot reproduce a
validated hardware setup on every computer.

| Guide | Purpose |
| --- | --- |
| [Features and shortcuts](docs/FEATURES.md) | Everyday behavior |
| [Windows-style Alt+Tab](docs/ALT_TAB.md) | Version-aware native compact/MRU profile and safe rollback |
| [Current setup coverage](docs/CURRENT_SETUP.md) | What the one-script installer includes and what still needs review |
| [Official Noctalia login](docs/OFFICIAL_LOGIN.md) | Explicit next-boot greeter/keyring choices and recovery |
| [Installation](docs/INSTALL.md) | Staged migration and recovery |
| [Migration history](docs/HISTORY.md) | Decisions and evidence, not fabricated chat history |
| [Validation](docs/VALIDATION.md) | Verified results and outstanding hardware checks |
| [Adaptive lock screen](docs/LOCKSCREEN.md) | Reference styling, efficient rendering and safe adaptation |
| [Wallpaper color synchronization](docs/THEMING.md) | Native desktop templates and application/greeter limits |
| [Encrypted application credentials](docs/KEYRING.md) | Reviewed greetd/keyring fix and editor backend selection; not automatic |
| [Coding-agent handoff](docs/AGENT_HANDOFF.md) | Adapt unsupported hardware safely |
| [Provenance](docs/PROVENANCE.md) | Sources, licenses and publication boundaries |

Do not interpret reference measurements as promised battery life on another
machine. A successful configuration deployment is not a completed hardware
validation. Start with `audit`, retain a working fallback, and test deliberately.

## Development and publication

```sh
python -m unittest discover -s tests -v
python tools/check_publication.py
python tools/validate_export.py  # Native offline checks when binaries are installed.
```

The author can run `bash tools/publish.sh` after a successful GitHub CLI login.
It checks the approved owner, repository identity/visibility, remote, clean history/export and
tests, then pushes `main` to the existing `Kevincruz2005/cachyos-hyperland-setup`
repository. It never creates a repository, changes visibility or force-pushes.
Review the allowlist as well; automated secret scans are not a guarantee.
