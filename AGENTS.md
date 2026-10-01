# Agent operating contract

Read README, docs/INSTALL.md, docs/AGENT_HANDOFF.md and docs/VALIDATION.md
before changing a target machine. Installed versions and detected hardware
outrank old tutorials and assumptions. Check current official CachyOS,
Hyprland, Noctalia and NVIDIA documentation before adapting versioned APIs.

- Audit first; use `./setup plan` and inspect the complete transaction.
- This is not a fresh OS installation. Preserve existing user edits and fallback sessions.
- Never remove KDE/SDDM, kernels, drivers or shared Qt/system components automatically.
- Never touch bootloader settings, EFI, partitions, Windows, Secure Boot or kernel arguments.
- Stop for kernel/NVIDIA changes, important removals or boot-writing package hooks.
- Snapshot watchers can write GRUB independently of pacman hooks. Hook suppression alone is insufficient.
- No partial upgrades, destructive --noconfirm, AUR substitutes for official packages, or orphan sweeps.
- No TLP/optimus-manager/Bumblebee/global NVIDIA renderer forcing or speculative GPU workarounds.
- Derive GPU PCI addresses, DRM nodes, connected outputs and real display modes dynamically.
- Preserve the existing power stack; thermald is Intel-specific and must be justified.
- Keep recovery backups private and unchanged. Never commit reports, recordings, wallet material or account data.
- Do not run apply on the author's working laptop just to test the repository.
- Keep original upstream licenses and source attribution. Do not upload the referenced wallpaper.
- Dictation must have no autostart/idle worker and bounded whole-cgroup termination.
- Do not reset keyrings or change login/PAM handlers to work around authentication issues.
- Never reboot, suspend, lock or log out a user automatically during validation.
- Mark untested hardware behavior honestly; never fabricate A/B power measurements.
- A stopped module is not complete. Produce a stage-specific handoff, backup path and next safe diagnostic.

Use feature-sized Conventional Commits with actual commit dates. Run
`python -m unittest discover -s tests -v` and `python tools/check_publication.py`
before committing or publishing. Do not rewrite someone else's history.
