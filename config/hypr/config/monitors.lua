-- SPDX-License-Identifier: GPL-1.0-only
local host = require("config.host")
if host.output ~= "" then
    hl.monitor({ output = host.output, mode = host.mode, position = "auto",
                 scale = host.scale, cm = "srgb" })
end
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })
