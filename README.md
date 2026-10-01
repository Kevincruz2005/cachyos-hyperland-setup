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
./setup audit
./setup plan
```

Read [installation](docs/INSTALL.md) before applying anything. CachyOS-first;
other distributions and untested versions stop with an agent handoff instead
of executing guessed package commands. Never pipe downloaded scripts into sudo.
This repository is private: cloning requires access granted by its owner.

## What this reproduces

- Dark wallpaper-derived GTK/Qt/Kitty colors and Dolphin integration.
- Adwaita Sans, JetBrainsMono Nerd Font, Bibata cursor and minimal Noctalia bar.
- Current window/gesture shortcuts, Windows-style show desktop, maximize separate from true fullscreen.
- Interactive Print Screen crop/preview/copy/save with fractional-scale fixes.
- Offline English/Tamil phrase dictation, with no idle model/listener and whole-cgroup cleanup.
- Event-driven power profiles and SDDM wallpaper synchronization; no new polling daemons.
- KDE fallback, portals, networking/audio/Bluetooth and optional on-demand local AI.

Current Dell tuning includes 125% display scaling, zero gaps and black active
borders. A generic host receives detected display settings rather than eDP-1
or a copied PCI address. Exact appearance requires supplying the referenced
wallpaper; the image itself is not redistributed.

## Safety contract

No automatic KDE removal, kernel/driver replacement, bootloader/EFI/partition
changes, Windows changes, TLP, global NVIDIA forcing, orphan cleanup, reboot
or session termination. Package and system-level steps require review.

| Guide | Purpose |
| --- | --- |
| [Features and shortcuts](docs/FEATURES.md) | Everyday behavior |
| [Installation](docs/INSTALL.md) | Staged migration and recovery |
| [Migration history](docs/HISTORY.md) | Decisions and evidence, not fabricated chat history |
| [Validation](docs/VALIDATION.md) | Verified results and outstanding hardware checks |
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
It checks the approved owner, private repository, remote, clean history/export and
tests, then pushes `main` to the existing `Kevincruz2005/cachyos-hyperland-setup`
repository. It never creates a repository, changes visibility or force-pushes.
Review the allowlist as well; automated secret scans are not a guarantee.
