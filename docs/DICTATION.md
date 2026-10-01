# On-demand voice typing

Click an editable field, then Super+H. Text appears after a ~700 ms pause or
each eight seconds of continuous speech, plus inference time. This is phrase
streaming, not instant word-by-word interim text. Current Tiny.en q5_1 is
English-only with explicit `--language en`, avoiding automatic language detection.
It does not support Tamil or translate other languages.

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

The original multilingual public English sample test peaked ~133 MiB in a live
text field, with ~2-second finalization. Those are historical results, not a new
microphone test or promised measurements on other CPUs. Tiny trades recognition
accuracy for resources; the user's English microphone/accent/noise accuracy
still requires testing. Larger models must be discussed separately.

## English model and measured comparison

Model: `ggml-tiny.en-q5_1.bin`, 32,166,155 bytes, SHA-256:

```text
c77c5766f1cef09b6b7d47f21b546cbddd4157886b3b5d6d4f709e91e66c7c2b
```

The checksum/size come from the [upstream model metadata](https://huggingface.co/ggerganov/whisper.cpp/raw/main/ggml-tiny.en-q5_1.bin).
The [official whisper.cpp model documentation](https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md)
identifies `.en` models as English-only and documents quantization.

On the reference laptop, one warmup per case followed by three interleaved
trials of the same approximately 11-second public English speech fixture gave:

| Model / language / threads | Median elapsed | Median CPU time | Median peak RSS | Sample normalized word error |
| --- | --- | --- | --- | --- |
| Previous Tiny q5_1 / auto / 2 | 1.047 s | 1.958 s | 128,684 KiB | 0% |
| Tiny.en q5_1 / en / 2 | 0.592 s | 1.069 s | 128,052 KiB | 0% |
| Tiny.en q5_1 / en / 1 | 1.068 s | 1.065 s | 129,316 KiB | 0% |

Same CPU-only greedy recognition flags, no GPU. NVIDIA graphics/audio were
suspended before and after. Two threads are retained: one thread used nearly
the same total CPU time but took longer. Both model files are about 32 MB;
English-only does **not** imply a substantially smaller model or lower RAM here.

These direct-process samples were outside the live service's 150% CPU quota,
with the agent/session still open. They are not battery-energy measurements,
microphone accuracy tests or guarantees for other machines/accents.

To reproduce explicitly with both verified models already present:

```bash
python tools/benchmark_dictation.py --audio-fixture /path/to/public-sample.wav --trials 3 --compare-one-thread
```

Optionally add `--reference-file /path/to/public-reference.txt` to compute normalized
word error. The tool never opens the microphone or types into an application;
fixture transcripts/logs stay in a private local report directory, not Git.
The previous model may remain on disk for manual rollback; it is never loaded
by the current helper, and there is no automatic multilingual fallback.
