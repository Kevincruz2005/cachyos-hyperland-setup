#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Approved existing repository only. Respect owner-selected visibility; never change it.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd -- "$repo_dir"
repo_name=Kevincruz2005/cachyos-hyperland-setup
repo_url=https://github.com/Kevincruz2005/cachyos-hyperland-setup.git
[[ $(gh api user --jq .login) == Kevincruz2005 ]] || {
    printf '%s\n' 'Publishing stopped: authenticate as Kevincruz2005 and verify gh api user --jq .login.' >&2
    exit 2
}
[[ -z $(git status --porcelain) ]] || {
    printf '%s\n' 'Publishing stopped: review and commit local changes first.' >&2
    exit 2
}
[[ $(git branch --show-current) == main ]] || {
    printf '%s\n' 'Publishing stopped: the reviewed branch must be main.' >&2
    exit 2
}
[[ $(git remote get-url origin) == "$repo_url" && $(git remote get-url --push origin) == "$repo_url" ]] || {
    printf '%s\n' 'Publishing stopped: origin must point to the approved repository for both fetch and push.' >&2
    exit 2
}
repo_metadata=$(gh repo view "$repo_name" --json nameWithOwner,isPrivate --jq '.nameWithOwner + " " + (.isPrivate|tostring)')
case "$repo_metadata" in
    "$repo_name true") visibility=private ;;
    "$repo_name false") visibility=public ;;
    *) printf '%s\n' 'Publishing stopped: the approved repository could not be verified.' >&2; exit 2 ;;
esac
python -m unittest discover -s tests -v
python tools/check_publication.py
bash -n tools/power-profile.sh tools/sddm-wallpaper-sync tools/publish.sh
python tools/validate_export.py
printf '%s\n' "Pushing reviewed main history to existing $visibility repository $repo_name."
# Credential setup is command-local, not a global Git/account configuration change.
# A non-fast-forward is rejected normally: no overwrite, deletion or automatic merge.
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push -u origin main
printf '%s\n' "Published: https://github.com/$repo_name ($visibility)"
