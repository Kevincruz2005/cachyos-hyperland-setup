-- Show wallpaper on the current monitor without moving/minimizing app windows.
-- A second press restores the previous workspace, including its tiling/fullscreen.
-- No processes, timers or polling. Workspace history survives config reloads.
-- Pinned (all-workspace) windows intentionally retain their pinned behavior.
return function()
    local current = hl.get_active_workspace()
    if not current then return end
    local prefix = "__show_desktop_"
    if current.name:sub(1, #prefix) == prefix then
        local previous = hl.get_last_workspace()
        if previous and previous.name:sub(1, #prefix) ~= prefix then
            hl.dispatch(hl.dsp.focus({ workspace = previous.config_name }))
        end
        return
    end

    -- Do not hide newly opened apps in a previously used desktop workspace.
    local index = 1
    while true do
        local target = "name:" .. prefix .. index
        local workspace = hl.get_workspace(target)
        if not workspace or (workspace.is_empty and not workspace.visible) then
            hl.dispatch(hl.dsp.focus({ workspace = target }))
            return
        end
        index = index + 1
    end
end
