#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Called only by Noctalia startup/battery events; no timer or monitor process.
set -euo pipefail
profile=power-saver
for supply in /sys/class/power_supply/*; do
    [[ -r "$supply/type" && -r "$supply/online" ]] || continue
    case $(<"$supply/type") in
        Mains|USB|USB_C|USB_PD|USB_PD_DRP)
            if [[ $(<"$supply/online") == 1 ]]; then profile=balanced; break; fi ;;
    esac
done
[[ $(powerprofilesctl get) == "$profile" ]] || powerprofilesctl set "$profile"
