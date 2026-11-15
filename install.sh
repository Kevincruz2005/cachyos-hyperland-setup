#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Guided entry point for an existing CachyOS desktop, not an unattended OS installer.
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
cd -- "$repo_dir"

usage() {
    printf '%s\n' 'Usage: ./install.sh [--wallpaper /absolute/path/to/static-image] [--login keep|noctalia] [--gnome-keyring]'
    printf '%s\n' 'Optional reviewed package flags: --allow-snapshot-hook-override --allow-settings-replacement'
    printf '%s\n' 'Default: preserve existing login. In a terminal, the wizard offers the official Noctalia login separately.'
}
config_args=()
review_args=()
login_choice=ask
keyring=0
while (( $# )); do
    case "$1" in
        --wallpaper)
            (( $# >= 2 )) && [[ $2 == /* ]] || { usage >&2; exit 2; }
            config_args+=(--wallpaper "$2"); shift 2 ;;
        --login)
            (( $# >= 2 )) && [[ $2 == keep || $2 == noctalia ]] || { usage >&2; exit 2; }
            login_choice=$2; shift 2 ;;
        --gnome-keyring) keyring=1; shift ;;
        --allow-snapshot-hook-override|--allow-settings-replacement)
            review_args+=("$1"); shift ;;
        --help|-h) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done
if (( EUID == 0 )); then
    printf '%s\n' 'Run as your normal user, not with sudo.' >&2
    exit 2
fi
for required in python pacman sudo file; do
    command -v "$required" >/dev/null || {
        printf '%s\n' "Missing prerequisite: $required. This is an existing CachyOS installer; ask an agent to prepare the prerequisites safely." >&2
        exit 2
    }
done
if [[ $login_choice == ask ]]; then
    login_choice=keep
    if [[ -t 0 ]]; then
        printf '%s\n' 'Keep the working login by default. Noctalia Greeter switches to greetd for NEXT BOOT only; SDDM/KDE stay installed.'
        read -r -p 'Offer the separately approved official Noctalia login stage? [y/N] ' answer
        if [[ $answer == y || $answer == Y ]]; then login_choice=noctalia; fi
    fi
fi
if [[ $login_choice == noctalia ]]; then
    config_args+=(--login noctalia)
    if [[ -t 0 && $keyring == 0 ]]; then
        read -r -p 'Also review optional GNOME Keyring login/password hooks? Existing wallet passwords must match. [y/N] ' answer
        if [[ $answer == y || $answer == Y ]]; then keyring=1; fi
    fi
elif (( keyring )); then
    printf '%s\n' '--gnome-keyring requires --login noctalia. No changes made.' >&2
    exit 2
fi
if (( keyring )); then config_args+=(--gnome-keyring); fi

printf '%s\n' 'Auditing this existing desktop. No packages or settings are changed in this stage.'
if ! ./setup audit; then
    printf '%s\n' 'Audit stopped. This setup was developed for one CachyOS laptop; give AGENTS.md and docs/AGENT_HANDOFF.md to a coding agent for safe adaptation.' >&2
    exit 2
fi

printf '%s\n' 'Preparing the exact package and user-file plan. Review it before confirming apply.'
if ! ./setup plan "${config_args[@]}"; then
    printf '%s\n' 'Plan stopped. Nothing was applied. This setup was developed for one CachyOS laptop; give AGENTS.md, docs/AGENT_HANDOFF.md and the private report to a coding agent after checking it for privacy.' >&2
    exit 2
fi

printf '%s\n' 'The next stage is interactive: type APPLY only after reviewing the plan.'
printf '%s\n' 'It may install reviewed official packages and a verified local speech model; it will not reboot, remove KDE or stop your session.'
printf '%s\n' "Login choice: $login_choice. Any requested login/PAM change has its own APPLY confirmation."
if ! ./setup apply --packages --download-model "${config_args[@]}" "${review_args[@]}"; then
    printf '%s\n' 'Apply stopped. Keep the printed backup/report path; use docs/AGENT_HANDOFF.md for a safe continuation.' >&2
    exit 2
fi

printf '%s\n' 'Configuration staged. Choose Hyprland (UWSM) manually and follow docs/VALIDATION.md; KDE remains the fallback.'
