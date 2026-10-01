-- Auto-start config
-- if you dont use UWSM add your auto start programs here, otherwise use XDG autostart https://wiki.archlinux.org/title/XDG_Autostart

hl.on("hyprland.start", function ()
    -- UWSM owns the session environment and application lifetime.
    -- The packaged KWallet PAM autostart has X-systemd-skip=true; UWSM skips it.
    -- Complete the existing PAM handshake before starting the shell. No wallet is replaced.
    local wallet = io.open("/usr/lib/pam_kwallet_init", "r")
    if wallet then
        wallet:close()
        hl.exec_cmd("/usr/lib/pam_kwallet_init; uwsm app -- noctalia")
    else
        hl.exec_cmd("uwsm app -- noctalia")
    end
end)
