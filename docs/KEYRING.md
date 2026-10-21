# Encrypted application credentials with greetd

## Reference-machine correction (2026-10-21)

After a separately approved move to the official Noctalia Greeter and greetd,
the reference laptop requested a second password to unlock its login keyring.
Some Electron editors also reported that no OS keyring could be identified.
The installed greetd PAM configuration lacked GNOME Keyring integration; the
existing keyring already accepted the user's current login password. No keyring
reset, password change or weaker encryption was needed.

This is a record of an explicitly authorized, host-reviewed fix, **not** an
automatic installer module or permission to change another machine's login.
The portable installer still has its existing version gates and SDDM path;
it does not install/select greetd or apply the PAM changes below.

## Review before adapting

Determine the active display manager, PAM includes, Secret Service provider,
installed module dependencies and existing editor runtime arguments first.
Do not stack another keyring provider onto a working KWallet setup. Preserve
all authentication rules and existing user settings, and keep a private backup
and recovery terminal available. Obtain explicit owner approval for PAM edits.

On the reference host, the only additions to `/etc/pam.d/greetd` were:

```text
# Immediately after auth include system-local-login:
-auth      optional     pam_gnome_keyring.so
# Immediately after session include system-local-login:
-session   optional     pam_gnome_keyring.so auto_start
```

The only addition to `/etc/pam.d/passwd`, after its existing
`password include system-auth` rule, was:

```text
-password   optional    pam_gnome_keyring.so use_authtok
```

These are insertion examples, not complete replacement PAM files. Existing
secure-terminal, nologin, account and session checks remained unchanged.
Do not duplicate hooks already provided by an included stack. The optional
module uses the login password collected by the existing authentication stack.
The password hook can synchronize ordinary password changes when both old and
new passwords are available; an administrator reset without the old password
may still need a separate keyring password update.

## VS Code and Cursor

The reference host's installed product metadata identified these runtime files:

- VS Code: `~/.vscode/argv.json`
- Cursor: `~/.cursor/argv.json`

The following property was merged into each existing JSONC object, retaining
comments and all unrelated settings:

```json
"password-store": "gnome-libsecret"
```

This is a property fragment, not a replacement file. VS Code also exposes its
runtime file through **Preferences: Configure Runtime Arguments**. Inspect
other editions' product metadata, launcher flags and packaging before assuming
the same paths. A legacy `~/.config/Cursor/argv.json` on this host also selected
`kwallet6`; that stale selection was aligned with the verified GNOME provider.
Do not copy the author's full argv files: they can contain machine identifiers.

Save work, fully quit the editor's processes normally and reopen it to test the
new selection. Do not select weaker/basic encryption or delete existing tokens
to hide a credential-store error. Changing backends may require signing into
an application again; retain the previous store until recovery is verified.

## Resource impact and validation

The change added no polling, monitoring service, package or new enabled daemon.
It integrates the already installed GNOME Keyring with login/password events
and selects that existing encrypted provider in editors. Keyring services still
use some memory and event-driven CPU; this is not a zero-resource claim or a
measured battery-life improvement. Power, GPU, theme and boot settings were
untouched.

Checks completed on the reference host:

- Installed PAM matched reviewed files; original checks were preserved.
- The keyring PAM module had no missing shared-library dependencies.
- Editor runtime objects differed only in `password-store`.
- The login collection was unlocked; the user confirmed their current password
  worked. No stored password or credential was changed.
- Private editor database backups passed SQLite integrity checks.
- greetd stayed active, no failed system/user units were reported, and no extra
  keyring daemon process was spawned by applying the change.
- Both NVIDIA PCI functions were runtime-suspended during verification.

Automatic unlock at the next manual password login and editor restart behavior
still need owner confirmation. No logout, restart or password change was forced.

## Recovery

Keep original PAM files, editor argv files, encrypted keyrings and consistent
editor database backups **private**, outside this repository. Restore only the
reviewed PAM/argv files if needed, preserving later edits. Do not automatically
restore old keyrings or editor databases over newer credentials/state. Record
exact host-specific rollback commands in the private checkpoint; never publish
its contents. A display-manager restart is not necessary to save these changes
and can terminate the user's graphical session.

Primary references:

- [GNOME Keyring PAM integration](https://wiki.gnome.org/Projects/GnomeKeyring/Pam/Manual)
- [VS Code credential-store troubleshooting](https://code.visualstudio.com/docs/configure/settings-sync#_troubleshoot-credentialstore-issues)
