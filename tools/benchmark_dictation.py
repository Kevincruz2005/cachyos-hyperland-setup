#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Explicit CPU-only WAV fixture comparison. No microphone, UI or typing."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import statistics
import subprocess
import threading
import time
import wave


def word_error(reference, result):
    normalize = lambda text: re.findall(r"[a-z]+", text.lower())
    expected, actual = normalize(reference), normalize(result)
    previous = list(range(len(actual)+1))
    for i, word in enumerate(expected, 1):
        current = [i]
        for j, other in enumerate(actual, 1):
            current.append(min(current[-1]+1, previous[j]+1, previous[j-1]+(word != other)))
        previous = current
    return previous[-1] / max(len(expected), 1)


def measure(model, language, threads, audio, output):
    args = ["whisper-cli", "--no-gpu", "--threads", str(threads), "--language", language,
            "--model", str(model), "--file", str(audio), "--no-timestamps", "--no-fallback",
            "--beam-size", "1", "--best-of", "1", "--suppress-nst", "--output-txt", "--output-file", str(output)]
    start = time.monotonic()
    with output.with_suffix(".log").open("wb") as log:
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=log, start_new_session=True)
        def timeout():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        timer = threading.Timer(15, timeout)
        timer.daemon = True
        timer.start()
        try:
            _, status, usage = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
        except BaseException:
            timeout()
            _, status, _ = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
            raise
        finally:
            timer.cancel()
            timer.join()
    if process.returncode:
        raise RuntimeError("Fixture recognition failed or exceeded its deadline; inspect the private log.")
    text = output.with_suffix(".txt").read_text().strip()
    return {"elapsed_seconds": time.monotonic()-start, "cpu_seconds": usage.ru_utime+usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss, "output_sha256": hashlib.sha256(text.encode()).hexdigest()}, text


def gpu_states():
    states = {}
    for device in sorted(Path("/sys/bus/pci/devices").glob("*")):
        try:
            if (device / "vendor").read_text().strip() == "0x10de":
                states[device.name] = (device / "power/runtime_status").read_text().strip()
        except OSError:
            pass
    return states


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-fixture", type=Path, required=True)
    parser.add_argument("--reference-file", type=Path)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--compare-one-thread", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.trials <= 5:
        raise RuntimeError("Use 1..5 short fixture trials, not continuous benchmarking.")
    audio = args.audio_fixture.resolve()
    with wave.open(str(audio), "rb") as source:
        duration = source.getnframes()/source.getframerate()
        if (source.getframerate(), source.getnchannels(), source.getsampwidth()) != (16000, 1, 2) or not 0 < duration <= 15:
            raise RuntimeError("Use a <=15-second 16 kHz mono PCM16 public fixture; no microphone is opened.")
    reference = args.reference_file.read_text() if args.reference_file else None
    models = Path.home() / ".local/share/hypr-dictation/models"
    cases = [("multilingual_auto_2t", models / "ggml-tiny-q5_1.bin", "auto", 2),
             ("english_2t", models / "ggml-tiny.en-q5_1.bin", "en", 2)]
    if args.compare_one_thread:
        cases.append(("english_1t", models / "ggml-tiny.en-q5_1.bin", "en", 1))
    if any(not model.is_file() for _, model, _, _ in cases):
        raise RuntimeError("Both verified models must already exist; this tool downloads nothing.")
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    folder = Path.home() / ".local/state/cachyos-hyprland-noctalia/reports" / ("english-fixture-" + name)
    folder.mkdir(parents=True, mode=0o700)
    report = {"audio_seconds": duration, "fixture_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
              "nvidia_before": gpu_states(), "conditions": "Same CPU-only flags; process measurements outside the live service's 150% cgroup quota. Not a battery-energy or microphone benchmark.",
              "cases": {label: [] for label, _, _, _ in cases}}
    # One warmup per case, then interleaved measured trials.
    for label, model, language, threads in cases:
        measure(model, language, threads, audio, folder / (label + "-warmup"))
    for trial in range(args.trials):
        order = cases if trial % 2 == 0 else list(reversed(cases))
        for label, model, language, threads in order:
            sample, text = measure(model, language, threads, audio, folder / (label + f"-{trial}"))
            if reference:
                sample["word_error_rate"] = word_error(reference, text)
            report["cases"][label].append(sample)
    report["nvidia_after"] = gpu_states()
    report["summary"] = {}
    for label, samples in report["cases"].items():
        report["summary"][label] = {key: statistics.median(sample[key] for sample in samples)
                                    for key in ("elapsed_seconds", "cpu_seconds", "peak_rss_kib")}
        if reference:
            report["summary"][label]["word_error_rate"] = statistics.median(s["word_error_rate"] for s in samples)
    path = folder / "results.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    path.chmod(0o600)
    print(json.dumps(report["summary"], indent=2))
    print("NVIDIA before/after:", report["nvidia_before"], report["nvidia_after"])
    print("Private report:", path)


if __name__ == "__main__":
    main()
