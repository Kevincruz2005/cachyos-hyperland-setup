#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Approved owner/repository only. Never overwrite an existing remote/repository.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd -- "$repo_dir"
[[ $(gh api user --jq .login) == Kevincruz2005 ]] || {
    printf '%s\n' 'Publishing stopped: authenticate as Kevincruz2005 and verify gh api user --jq .login.' >&2
    exit 2
}
[[ -z $(git status --porcelain) ]] || {
    printf '%s\n' 'Publishing stopped: review and commit local changes first.' >&2
    exit 2
}
[[ -z $(git remote) ]] || {
    printf '%s\n' 'Publishing stopped: a remote already exists; inspect it before any retry.' >&2
    exit 2
}
python -m unittest discover -s tests -v
python tools/check_publication.py
bash -n tools/power-profile.sh tools/sddm-wallpaper-sync tools/publish.sh
python tools/validate_export.py
printf '%s\n' 'Creating the approved new PUBLIC repository Kevincruz2005/cachyos-hyprland-noctalia.'
# gh refuses an existing repository; no force push, blanket credential setup or deletion.
gh repo create Kevincruz2005/cachyos-hyprland-noctalia \
    --public --source "$repo_dir" --remote origin --push \
    --description 'Battery-first CachyOS Hyprland + Noctalia v5: portable configuration, safe staged migration and on-demand tools'
printf '%s\n' 'Published: https://github.com/Kevincruz2005/cachyos-hyprland-noctalia'
