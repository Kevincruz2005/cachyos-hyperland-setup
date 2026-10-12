# Default/no-photo avatar

The desktop profile uses:

```toml
[shell]
avatar_path = ""
```

This removes the shell's custom-photo override. It does not hide the user card,
change the wallpaper, lock screen, typography, theme or authentication.
No custom placeholder image, plugin, service or sampling timer is added.

## Important account fallback

Reviewed against native Noctalia 5.2.1: the shell first uses a nonempty
avatar_path, then the current account's AccountsService IconFile. If both are
empty, the Control Center clears the avatar texture and leaves its native
empty placeholder. A blank shell path alone is not guaranteed to hide an
existing account photo.

Selecting a photo through Noctalia can also save a resized copy through
AccountsService. Clearing the shell setting can therefore reveal that copy
again. The installer only sets the shell preference: it never resets a target
machine's account avatar or copies the author's personal image.

## Reset an existing machine safely

1. Privately back up Noctalia's settings.toml and the currently selected account
   avatar before editing. Keep the original image file; do not delete caches or
   bulk-replace configuration.
2. Set only avatar_path to an empty string in the existing [shell] section of
   `~/.local/state/noctalia/settings.toml`. Do not duplicate the table.
3. If AccountsService still supplies an image, have an agent resolve the current
   user's object with FindUserById, back up its IconFile, then reset only that
   user's image using SetIconFile with an empty string. This can also restore
   the default avatar in other applications/login screens that share account
   data; it must not change any login, password or account-type properties.
   Do not assume a UID/object path or modify another account.
4. Validate the settings with `noctalia config validate`, then issue
   `noctalia msg config-reload`. Reopen the Control Center if necessary.
   No desktop restart, logout or service restart is needed.

To undo, restore only the previous avatar_path property and, if it was reset,
select the backed-up/original account photo again. Preserve later wallpaper,
theme and layout edits rather than restoring the whole state file blindly.

## Evidence and limits

The reference machine reset both the shell override and its account IconFile.
The original image was retained and both prior settings and the account copy
were backed up privately. Native schema validation and isolated export tests
cover the configuration. Both avatar properties were verified empty after
configuration reload; visual acceptance remains owner-assisted.
No measured battery-life improvement is claimed. The reset adds no continuing
worker and avoids loading the selected photo; ordinary panel rendering still
uses resources.

Version-matched primary sources:

- [Shell settings](https://github.com/noctalia-dev/noctalia/blob/v5.2.1/docs/user/configuration/shell.mdx)
- [Avatar resolution](https://github.com/noctalia-dev/noctalia/blob/v5.2.1/src/shell/profile/avatar_path.cpp)
- [Control Center rendering](https://github.com/noctalia-dev/noctalia/blob/v5.2.1/src/shell/control_center/tabs/home_tab.cpp)
