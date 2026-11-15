# Optional official Noctalia login

The single entry script can offer the official Noctalia Greeter, not a custom
SDDM imitation. It runs under greetd and is separate from the in-session lock
screen. SDDM and Plasma remain installed as recovery options.

```sh
./install.sh --login noctalia
# Add only when the target owner also approves GNOME Keyring integration:
./install.sh --login noctalia --gnome-keyring
```

Without these options, the terminal wizard asks; the default answer is **keep
existing login**. Noninteractive input defaults to keeping login, but the actual
apply stage still refuses unattended confirmation. No bypass flag exists.

## Review gates

The login adapter requires the current 0.57.1/5.4.1/0.27.1 desktop combination,
Noctalia Greeter 1.6.0 or 1.7.0, and greetd 0.10.3. Version revisions from the
distribution are allowed; unreviewed upstream versions stop. Existing official
packages are used; absent ones require the reviewed repository-only package
stage. Neither AUR substitutes nor archived reference packages are fetched.

The apply stage asks separately about next-boot login and optional PAM changes.
After package installation, the protected stage inspects and previews the exact
configuration changes and asks for **ENABLE NOCTALIA LOGIN**. Until then, that
stage changes no login files or service selection. If the owner declines after
desktop deployment, installed packages/user configuration may remain staged;
the report identifies the completed stages and backup for recovery.

Preflight requires both Hyprland (UWSM) and Plasma desktop entries, retained
SDDM, an existing known display manager, no second enabled manager, a trusted
packaged session wrapper and a recognized greetd configuration. Custom launchers,
autologin sections, session users, terminal layouts and symlinked protected
files stop for manual review. The existing terminal VT number is retained.

The adapter points greetd at the official session wrapper, preferring the
`hyprland-uwsm` session and target username. This is a normal password login,
not autologin. It selects only greetd for the **next boot**, using service
enable/disable without `--now`, stop, restart or reboot. Failure during selection
attempts to restore the previous next-boot manager immediately; the receipt
also retains the recovery choice.

## Keyring option

`--gnome-keyring` adds three optional GNOME Keyring hooks after known PAM
include anchors: greetd auth, greetd session `auto_start`, and passwd
`use_authtok`. All existing authentication rules remain; unknown/conflicting
hooks or an included stack already handling GNOME Keyring stop for review.
No password, encrypted keyring, wallet contents or PAM authentication requirement
is weakened/reset. Existing login/keyring passwords must match; if they differ,
the owner must align them manually. Admin password resets without the old
password may still need a separate keyring update.

Only already-existing standard VS Code/Cursor argv files are merged to use
`gnome-libsecret`; comments, other settings and nested objects are retained.
Unsupported/symlinked/invalid runtime files stop. Other editor editions/profile
paths are not guessed. The Hyprland autostart then avoids initializing KWallet
as well. Existing KDE sessions/wallets are retained; old app credentials are not
migrated or deleted. Save work and reopen editors manually to test them.

See [KEYRING.md](KEYRING.md) for the original diagnosis, caveats and references.

## Appearance and first login

The greeter uses its official defaults until native sync is approved. After
manually entering Hyprland, use Noctalia's Greeter settings or:

```sh
noctalia msg greeter-sync
```

The opted-in desktop config enables native auto-sync for subsequent wallpaper,
palette and font changes. Administrator authorization may be requested. No
passwordless Polkit rule is installed and no arbitrary privileged setup helper
is executed. Existing greeter state is retained; a missing state directory is
created for the packaged greeter user. It is not removed on rollback because
later sync may put valuable appearance state there.

## Recovery

The printed private backup records affected system files, hashes, original
metadata and previous manager. From the retained session or a TTY:

```sh
./setup rollback --backup /absolute/path/to/the/printed/backup
```

It prechecks recorded originals and later edits, requests confirmation for
system changes, restores files and the previous manager for the next boot,
and leaves the running graphical session alone. New protected files are
renamed recoverably rather than broadly deleted. Installed packages and greeter
state remain; no recursive removal or keyring restoration occurs.

Real boot authentication, automatic keyring unlock, first appearance sync and
fallback-session login remain owner-assisted tests. No fresh-VM end-to-end
login validation is claimed for this adapter.

Primary references:

- [Official Greeter installation](https://github.com/noctalia-dev/noctalia-greeter/blob/v1.7.0/docs/user/installation.md)
- [Greeter configuration and built-in defaults](https://github.com/noctalia-dev/noctalia-greeter/blob/v1.7.0/docs/user/configuration.md)
- [Native Greeter sync](https://docs.noctalia.dev/noctalia/configuration/shell/#greeter-sync)
