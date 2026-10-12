-- CachyOS Hyprland Configuration

require("config.animations")
require("config.autostart")
require("config.colors")
require("config.decorations")
require("config.variables")
require("config.environment")
require("config.inputs")
require("config.binds")
require("config.misc")
require("config.monitors")
require("config.windowrules")
require("config.workspaces")

-- HyprMod managed settings
require("hyprland-gui")

-- Palette colors override only color fields; layout/fonts/monitor settings stay local.
-- A fresh clone may not have generated this native template yet.
local palette_ok, palette = pcall(function() return require("noctalia") end)
if palette_ok and type(palette) == "table" and type(palette.apply_theme) == "function" then
    palette.apply_theme()
end
