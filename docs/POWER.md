# Power and hybrid graphics

Intel drives the reference desktop; RTX 3050 is used on demand through PRIME.
No global GBM/GLX/WLR/AQ GPU override is exported. Do not turn a reference PCI
address or card number into a portable setting.

`./setup audit` discovers GPU addresses, drivers, associated PCI functions,
DRM connector ownership and real modes. Runtime PM reads are passive sysfs
reads; never continuously refresh nvidia-smi while testing idle suspend.

After manual login, verify normal renderer and Hyprland use Intel; run a short
PRIME renderer test, close it, allow settling and verify **all** relevant NVIDIA
functions return to suspended. Investigate device holders if they do not.
HDMI is NVIDIA-wired on the reference laptop; external output use can legitimately
keep it awake. USB-C wiring is not established. Do not force Intel-only DRM
selection until external-output requirements and compositor behavior are known.

The event helper selects power-saver on battery, balanced when a reported mains/
USB power supply is online. Unsupported power stacks stop for adaptation rather
than being replaced. thermald/intel_lpmd are retained on the reference; enabling
thermald on another Intel machine is a reviewed manual step, not a blind default.
Do not introduce TLP or multiple competing power managers.

Internal-panel 60 Hz is selected only when actually advertised at native
resolution. Otherwise preferred mode is retained and reported. Generic scale
is auto; the verified Dell 1080p/60 profile uses the current 1.25 scale. No AC
high-refresh automation or kernel-parameter tuning is introduced.

Noctalia is intentionally trimmed. Short animations are retained; permanent
graphs, visualizers, weather/calendar services and wallpaper animation are not.
See validation for matched A/B procedure and measurement limitations.
