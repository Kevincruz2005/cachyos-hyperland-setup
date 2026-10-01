-- Hyprland default apps

TERMINAL     = "kitty"
FILE_MANAGER = "dolphin"
BROWSER      = "brave"
EDITOR       = "gnome-text-editor --new-window"
CALCULATOR   = "gnome-calculator"

-- Monitors
MONITOR1 = require("config.host").output -- Generated from this host's connected outputs.
MONITOR2 = ""
MONITOR3 = ""
PRIMARY_MONITOR = MONITOR1

-- Workspaces
NUM_WPM = 9 -- Super+1..9 selects workspaces; only occupied/persistent ones need exist.
