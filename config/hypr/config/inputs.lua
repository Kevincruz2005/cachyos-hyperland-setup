-- Input configuration

hl.config({
    input = {
        -- sensitivity = -0.25,
        accel_profile = "adaptive",
        sensitivity = 0,
        touchpad = {
            tap_to_click = true,
            natural_scroll = false,
        },
    },
    -- Uncomment the section below to enable software cursors; this can help with cursor display or behavior issues
    -- cursor = {
    --     no_hardware_cursors = 1,
    -- },
})

-- Touchpad gestures
hl.gesture({ fingers = 4, direction = "horizontal", action = "workspace" })
-- Explicit states avoid toggle surprises when repeating the same gesture.
hl.gesture({
    fingers = 3,
    direction = "up",
    action = function()
        if hl.get_active_window() then
            hl.dispatch(hl.dsp.window.fullscreen_state({
                action = "set", internal = 1, client = 1,
            }))
        end
    end,
})
hl.gesture({
    fingers = 3,
    direction = "down",
    action = function()
        if hl.get_active_window() then
            hl.dispatch(hl.dsp.window.fullscreen_state({
                action = "set", internal = 0, client = 0,
            }))
        end
    end,
})
-- Floating is keyboard-only (Super+Alt+Space), not an accidental horizontal swipe.
