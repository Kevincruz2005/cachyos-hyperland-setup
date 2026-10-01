# On-demand voice typing

Click an editable field, then Super+H. Text appears after a ~700 ms pause or
each eight seconds of continuous speech, plus inference time. This is phrase
streaming, not instant word-by-word interim text. Multilingual Tiny preserves
the detected language instead of translating everything to English.

Second Super+H stops the microphone immediately, processes the final phrase,
and exits. Extra press during finishing or Super+Shift+H kills the dictation
cgroup immediately and discards uncommitted speech. No permanent unit file,
autostart, server, polling listener or model is left running while off.

Two CPU inference threads; nice 10; 150% quota of ONE CPU, not the whole
machine; 384 MiB cgroup cap, no swap. 10-second inference timeout, 12-second
final drain, 15-second manager SIGKILL fallback; automatic stop after 10 minutes.
Private runtime audio/text is deleted per phrase and at unit termination.
No transcript journal/notification/clipboard. Model on disk and reclaimable
file cache are not running workers. Shared PipeWire/Noctalia services remain.

Use `./setup apply --download-model` after reviewing the plan, or explicitly run
`python tools/download_model.py`. Download is checksummed, ~32 MB, and never
starts inference. Ollama/NVIDIA are not used. Run `hypr-dictation status` to
check off-state; `hypr-dictation cancel` is the emergency stop.

Focus change/lock/unknown lock state cancels. Same-app input-field changes cannot
be detected reliably. Do not dictate in passwords or terminal prompts; the
helper does not generate Enter. Noctalia must be running and unlocked.

The reference public English sample test peaked ~133 MiB in a live text field,
with ~2-second finalization. Those are not promised measurements on other CPUs.
Tiny trades recognition accuracy for resources; English/Tamil mixed-language
quality and the user's microphone still require testing. Larger models must
be discussed separately rather than silently installed.
