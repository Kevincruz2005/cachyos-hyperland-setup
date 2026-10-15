#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Guided entry point for an existing CachyOS desktop, not an unattended OS installer.
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
cd -- "$repo_dir"

if (( $# != 0 )); then
    if (( $# != 2 )) || [[ $1 != --wallpaper || $2 != /* ]]; then
        printf '%s\n' 'Usage: ./install.sh [--wallpaper /absolute/path/to/static-image]' >&2
        exit 2
    fi
fi
if (( EUID == 0 )); then
    printf '%s\n' 'Run as your normal user, not with sudo.' >&2
    exit 2
fi

printf '%s\n' 'Auditing this existing desktop. No packages or settings are changed in this stage.'
if ! ./setup audit; then
    printf '%s\n' 'Audit stopped. This setup was developed for one CachyOS laptop; give AGENTS.md and docs/AGENT_HANDOFF.md to a coding agent for safe adaptation.' >&2
    exit 2
fi

printf '%s\n' 'Preparing the exact package and user-file plan. Review it before confirming apply.'
if ! ./setup plan "$@"; then
    printf '%s\n' 'Plan stopped. Nothing was applied. This setup was developed for one CachyOS laptop; give AGENTS.md, docs/AGENT_HANDOFF.md and the private report to a coding agent after checking it for privacy.' >&2
    exit 2
fi

printf '%s\n' 'The next stage is interactive: type APPLY only after reviewing the plan.'
printf '%s\n' 'It may install reviewed official packages and a verified local speech model; it will not reboot, remove KDE or select SDDM automatically.'
if ! ./setup apply --packages --download-model "$@"; then
    printf '%s\n' 'Apply stopped. Keep the printed backup/report path; use docs/AGENT_HANDOFF.md for a safe continuation.' >&2
    exit 2
fi

printf '%s\n' 'Configuration staged. Choose Hyprland (UWSM) manually and follow docs/VALIDATION.md; KDE remains the fallback.'
