#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Scan every historical Git blob and unignored working file; never print secrets."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private key": rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "GitHub credential": rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})",
    "AWS credential": rb"(?:AKIA|ASIA)[A-Z0-9]{16}",
    "donor home path": rb"/home/" + rb"kevin-cruz(?:/|\b)",
    "private identity": rb"BEGIN " + rb"CERTIFICATE|kdeconnect/" + rb"privateKey|oauth_" + rb"token:\s*\S+",
}
FORBIDDEN = {".pem", ".key", ".bin", ".gguf", ".wav", ".pcm", ".ogg", ".mp3", ".ttf", ".otf", ".png", ".jpg", ".jpeg", ".webp", ".avif", ".zip", ".gz", ".zst", ".7z"}


def inspect(data, label):
    issues = []
    if len(data) > 1024*1024 or b"\0" in data:
        issues.append("binary/oversized content: " + label)
    for name, pattern in PATTERNS.items():
        if re.search(pattern, data):
            issues.append(name + ": " + label)
    return issues


def check():
    problems = []
    objects = subprocess.check_output(["git", "rev-list", "--objects", "--all"], cwd=ROOT).decode().splitlines()
    count = 0
    for line in objects:
        sha, _, name = line.partition(" ")
        kind = subprocess.check_output(["git", "cat-file", "-t", sha], cwd=ROOT).strip()
        if kind == b"blob":
            problems += inspect(subprocess.check_output(["git", "cat-file", "blob", sha], cwd=ROOT), "history:" + (name or sha))
            count += 1
    files = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode().split("\0")
    for name in filter(None, files):
        path = ROOT / name
        if path.is_symlink():
            problems.append("symlink in export: " + name)
        elif path.is_file():
            if path.suffix in FORBIDDEN or any(part in ("backups", "reports", ".aws", ".ssh") for part in path.parts):
                problems.append("excluded file type/path: " + name)
            problems += inspect(path.read_bytes(), "working:" + name)
    if problems:
        print("Publication blocked:\n" + "\n".join(sorted(set(problems))))
        return 2
    print(f"Publication scan passed: {count} historical blobs and {len([f for f in files if f])} working files. Automated screening is not a guarantee; review the allowlist too.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
