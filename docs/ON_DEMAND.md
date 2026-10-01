# Optional applications, not idle services

## Ollama

Ollama is not used by Super+H speech typing. Keep it optional. If using a packaged
system service, inspect its current status and save any running jobs before changing
it. To start only for an intentional session:

```sh
sudo systemctl start ollama.service
ollama list
ollama run YOUR_ALREADY_INSTALLED_MODEL
# After finishing:
sudo systemctl stop ollama.service
systemctl is-active ollama.service
```

`start` does not enable next-boot startup. `stop` ends the service and its managed
workers. Closing `ollama run` alone can leave the server/model resident. If auto-start
is enabled, disabling it is a separately reviewed `systemctl disable ollama.service`
step, not part of the desktop installer. If you manually run `ollama serve`, stop
that specific process too. Models remain on disk; there is no automatic model
download/removal or idle watchdog. Confirm NVIDIA re-suspends after a GPU model exits.

## HyprMod

The reference has HyprMod 0.4.0 as an optional on-demand editor. It is not a required
official repository dependency and this installer does not fetch it from AUR/uv
or start it automatically. Current effective visual overrides are already exported
in `hyprland-gui.lua`. Other releases may write different APIs; inspect them before
letting a settings editor rewrite a working configuration. Close it when finished.

## KDE Connect and retained apps

KDE Connect remains installed but its XDG autostart is excluded from Hyprland,
not KDE. Existing unrelated autostart metadata is merged where present. No private
KDE Connect device identity is copied. Dolphin remains useful; shared Qt/KF/GTK
libraries, PipeWire/WirePlumber, portals, networking, Bluetooth and SDDM are not
"unnecessary" just because Plasma is not the current session.

Reference hyprpaper/Alacritty/Ghostty removals are historical, not an automatic
removal list for another machine. A target may depend on them. No orphan sweep.
