# Coding-agent handoff

Suggested request:

> Adapt this repository to my existing system. Read AGENTS.md, INSTALL.md and
> VALIDATION.md first. Run audit and plan; inspect the private handoff and stop
> stage. Preserve my working desktop, current appearance and recovery path.
> Check current official docs and installed versions before changing versioned
> APIs. Ask before any critical removal, boot/kernel/driver change or login risk.
> Explain and test each adaptation. Never claim hardware checks you did not run.

## What to inspect

1. Private report `audit.json`, `plan.json`, `handoff.md` and backup receipts.
   Keep credentials/accounts/home paths out of public issues and commits.
2. Exact installed/candidate Hyprland, Noctalia and UWSM versions. Newer does not
   automatically mean compatible. Do not bypass a version gate or downgrade.
3. Distribution/architecture/package health, update scope and package hooks.
   Snapshots can start independent GRUB writers; pacman HookDir is not enough.
4. GPU PCI functions/driver, DRM ownership, display modes and external outputs.
   First try normal Intel compositing; add no GPU override if it already works.
5. Existing TOML fragments, user preferences, desktop portal selection, idle/power
   stack, session environment and target-user permissions.

## Common adaptations

- Hyprland before/after this Lua API needs a reviewed API/config translation.
- Noctalia v5 native TOML is not v4 Quickshell. Inspect schema and merged state;
  do not append duplicate sections or replace private service state.
- Generic/AMD hosts must not get Dell scaling, thermald or Intel PCI constants.
- NVIDIA-wired external monitors may need a deliberate AC/external profile.
  Do not keep NVIDIA awake in internal battery mode just for an unused port.
- Custom screenshot coordinates currently cover one unrotated output. For
  rotation/multiple outputs, map the selected monitor's logical/physical geometry
  or use Noctalia's native capture UI. Test every edge at fractional scaling.
- New Breeze/KDE source requires greeter preview/adaptation. Never replace PAM,
  SDDM session launchers or an existing custom greeter silently.
- Theme changes can collide with GTK CSS symlinks or existing Noctalia fragment
  overrides; preserve originals and inspect effective state before guessing.
- Current Tiny.en q5_1 speech is English-only, with limited accent/noise accuracy;
  do not advertise automatic language detection or Tamil/code-switching support.
  Bigger models change memory/CPU tradeoffs; ask before installing one. Off-state
  must have no listener/model/unit/cgroup/recordings, not merely a hidden popup.

## Completion evidence

Report changed files/packages/services, private backup location, exact rollback,
manual tests still outstanding, runtime PM for every NVIDIA function and actual
matched A/B samples. Run repository tests and full-history privacy check. A
deployment success is not a hardware-validation success. Keep KDE until the owner
explicitly approves separately reviewed cleanup. If safe adaptation cannot finish,
leave a specific stage/error/next diagnostic, not an optimistic success message.
