# Features and everyday shortcuts

Super is the Windows/logo key. Super+F1 opens the installed complete cheat sheet.

| Shortcut | Behavior |
| --- | --- |
| Super+Enter / Ctrl+Alt+T | Kitty; Shift+Super+Enter is centered floating Kitty |
| Super+Space / R | Noctalia launcher |
| Super+E | Dolphin, following the tiling layout |
| Super+B / Super+W | Helium / Brave |
| Calculator key / Super+C | Calculator |
| Alt+F4 / Super+Q | Close focused app |
| Super+F / Super+Shift+F | Maximize with app tabs / true fullscreen |
| Super+D | Show desktop / return without modifying original layout |
| Alt+Tab / Alt+Shift+Tab | Focus next/previous; no automatic maximize |
| Super+Tab | Visual Noctalia switcher |
| Super+1…9 | Workspaces; Shift sends silently, Alt sends and follows |
| Super+arrows / Super+Alt+arrows | Focus / resize |
| Super+G / Super+[ / Super+] | Group / previous or next group tab |
| Super+Alt+Space | Floating toggle |
| Super+V / Super+L | Clipboard / lock |
| Print / Super+Shift+S | Screenshot selection and preview |
| Super+Shift+W | Wallpaper chooser |
| Super+H / Super+Shift+H | Dictation toggle / immediate cancellation |

Three fingers up maximize; down restore. Three-finger horizontal floating is
disabled. Four-finger horizontal switches workspaces. Tap-to-click on, natural
scroll off, adaptive acceleration. Media/brightness keys use Noctalia actions.

Normal Dolphin windows follow the tiling layout instead of opening as small
cursor-positioned floating windows. Standard transient/dialog handling is
retained; floating can still be toggled manually with Super+Alt+Space.

Super+B launches Helium through UWSM; Super+W launches Brave from the Hyprland
`BROWSER` variable. The UWSM session `BROWSER` and web MIME/URL defaults use
Helium. Firefox remains installed/available, but no browser starts at login.
The installer merges MIME defaults into the user's file with a backup; review
this preference change before applying on another machine.

Kamoso is the on-demand camera app. It adds no camera-only autostart service;
PipeWire/WirePlumber remain for normal desktop audio/video plumbing. Closing
the app should release the camera; check actual hardware behavior on each host.

Screenshots: drag to crop, F full screen, Esc cancel; then C copies the image,
O recognizes English text and copies it, Enter saves and copies the image,
Esc discards (or cancels active OCR). OCR is local Tesseract, started only on O,
one CPU thread at low priority, with a 20-second hard timeout and no server,
GPU inference or persistent OCR model. If OCR finds nothing or fails, the
preview remains and the clipboard is unchanged; image copy/save still work.
The guided package plan includes official `tesseract` and
`tesseract-data-eng` packages. OCR recognizes printed text, not reliably
handwriting or complex reading order;
use a tight, clear crop. Recognized text is not saved or shown in notifications,
but intentionally enters the clipboard and may be retained by clipboard history.
The normal clipboard owner may remain to serve copied text; it is not an OCR worker.
Fractional scaling preserves original pixels. One-output
capture is tested; mixed-scale multi-output layouts are not claimed supported.

Appearance: dynamic dark faithful colors from a static wallpaper; GTK/Qt/
Kitty templates; Dolphin's explicit noctalia selection with a case-compatible
Noctalia.colors alias. Adwaita Sans shell, JetBrainsMono Nerd Font 12pt Kitty,
opaque background, no blinking cursor/bell, 10,000 scrollback lines.

The native template engine also supplies Hyprland border/group colors and a
small shared palette for the screenshot interface. Screenshot CSS and crop
borders read that palette only when invoked; there is no theme watcher or
background helper. The lock-screen clock uses neutral on_surface text instead
of an accent. Switching to another Noctalia palette regenerates the same outputs.
Apps that cache colors may need reopening; websites/editor themes and SDDM's
protected greeter palette are separate from desktop GTK/Qt theming.

Avatar: the profile sets `[shell].avatar_path = ""`, using Noctalia's native
default/account fallback instead of exporting a personal photo. With no account
photo, the Control Center keeps its empty native avatar placeholder. An existing
AccountsService photo can still appear; the installer deliberately does not
modify system account data. See [avatar reset](AVATAR.md) for a separately
reviewed complete no-photo reset. No custom image, plugin or polling is needed.

Power-saver on battery, balanced on mains. Blur/shadows/VRR off; short animations
on. All five Noctalia monitor poll intervals zero; weather/calendar/dock/desktop
widgets/wallpaper automation off. Lock at 10 minutes, screen off at 11; automatic
idle suspend disabled until physical validation.

Super+N cycles the available `powerprofilesctl` modes in this order:
power-saver → balanced → performance → power-saver. The one-shot helper shows a
short notification and exits; it adds no service or polling. Performance can
increase power use, especially on battery. This is a manual selection, and the
existing power-profiles-daemon battery-aware policy and Noctalia AC/battery
hooks can change it again when the power source changes. The shortcut does not
modify that policy, GPU routing or display refresh rate.

SDDM login and Noctalia lock are separate. Password entry stays normal. Only
SDDM wallpaper follows later wallpaper changes; greeter colors are a static
snapshot. No Enter-to-reveal password mode or animated greeter background.
