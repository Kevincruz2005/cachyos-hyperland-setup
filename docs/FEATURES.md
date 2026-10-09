# Features and everyday shortcuts

Super is the Windows/logo key. Super+F1 opens the installed complete cheat sheet.

| Shortcut | Behavior |
| --- | --- |
| Super+Enter / Ctrl+Alt+T | Kitty; Shift+Super+Enter is centered floating Kitty |
| Super+Space / R | Noctalia launcher |
| Super+E | Dolphin |
| Super+B / Super+W | Firefox / Brave |
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

Super+B launches Firefox through UWSM; Super+W keeps the configured browser
(Brave in the reference setup). This does not change MIME/URL defaults or the
session's BROWSER environment. Firefox is included in the reviewed package plan;
the shortcut does not start a browser at login.

Screenshots: drag to crop, F full screen, Esc cancel; then C copies the image,
O recognizes English text and copies it, Enter saves and copies the image,
Esc discards (or cancels active OCR). OCR is local Tesseract, started only on O,
one CPU thread at low priority, with a 20-second hard timeout and no server,
GPU inference or persistent OCR model. If OCR finds nothing or fails, the
preview remains and the clipboard is unchanged; image copy/save still work.
Requires optional official `tesseract` and `tesseract-data-eng` packages. It
recognizes printed text, not reliably handwriting or complex reading order;
use a tight, clear crop. Recognized text is not saved or shown in notifications,
but intentionally enters the clipboard and may be retained by clipboard history.
The normal clipboard owner may remain to serve copied text; it is not an OCR worker.
Fractional scaling preserves original pixels. One-output
capture is tested; mixed-scale multi-output layouts are not claimed supported.

Appearance: dynamic dark m3-tonal-spot colors from a static wallpaper; GTK/Qt/
Kitty templates; Dolphin's explicit noctalia selection with a case-compatible
Noctalia.colors alias. Adwaita Sans shell, JetBrainsMono Nerd Font 12pt Kitty,
opaque background, no blinking cursor/bell, 10,000 scrollback lines.

Power-saver on battery, balanced on mains. Blur/shadows/VRR off; short animations
on. All five Noctalia monitor poll intervals zero; weather/calendar/dock/desktop
widgets/wallpaper automation off. Lock at 10 minutes, screen off at 11; automatic
idle suspend disabled until physical validation.

SDDM login and Noctalia lock are separate. Password entry stays normal. Only
SDDM wallpaper follows later wallpaper changes; greeter colors are a static
snapshot. No Enter-to-reveal password mode or animated greeter background.
