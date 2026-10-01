-- Look and feel configuration

hl.config({
    general = {
        gaps_in = 3,
        gaps_out = 8,
        border_size = 2,
        extend_border_grab_area = 10,
        resize_on_border = true,
        col = {
            active_border = {
                colors = { "rgba(7aa2f7ff)", "rgba(bb9af7ff)" },
                angle = 45,
            },
            inactive_border = "rgba(414868ff)",
        },
    },
    group = {
        col = {
            border_active = CACHYLBLUE,
            border_inactive = CACHYGRAY,
            border_locked_active = CACHYDBLUE,
            border_locked_inactive = CACHYGRAY,
        },
        groupbar = {
            col = {
                active = CACHYLGREEN,
                inactive = CACHYGRAY,
                locked_active = CACHYDBLUE,
                locked_inactive = CACHYGRAY,
            },
        },
    },
    decoration = {
        dim_special = 0.3,
        rounding = 10,
        active_opacity = 1,
        inactive_opacity = 1,
        fullscreen_opacity = 1,
        blur = {
            enabled = false,
            size = 5,
            passes = 4,
            special = true,
        },
        shadow = { enabled = false },
    },
})
