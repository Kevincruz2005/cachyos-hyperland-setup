shortcut.setLabel("Check RTX")
shortcut.setIcon("device-desktop")
shortcut.setActive(false)

local checking = false

function onClick()
  if checking then
    return
  end
  checking = true
  local helper = noctalia.expandPath("~/.local/bin/gpu-runtime-status")
  local launched = noctalia.runAsync({ helper }, function(result)
    checking = false
    if result.exitCode ~= 0 or result.timedOut or result.stdoutTruncated then
      noctalia.notifyError("NVIDIA status unavailable", "The passive power-state check failed.")
      return
    end
    local state, detail = (result.stdout or ""):match("^(%a+)\n([^\n]+)")
    if state == "asleep" then
      noctalia.notify("NVIDIA asleep (D3cold)", detail)
    elseif state == "awake" then
      noctalia.notify("NVIDIA awake", detail)
    else
      noctalia.notify("NVIDIA state unknown", detail or "Power state could not be confirmed.")
    end
  end)
  if not launched then
    checking = false
    noctalia.notifyError("NVIDIA status unavailable", "Could not start the passive power-state check.")
  end
end
