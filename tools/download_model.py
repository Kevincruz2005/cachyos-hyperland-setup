#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Explicit verified model download; does not load or start the model."""
import hashlib
from pathlib import Path
import tempfile
import urllib.request

MODEL_NAME = "ggml-tiny.en-q5_1.bin"
SHA256 = "c77c5766f1cef09b6b7d47f21b546cbddd4157886b3b5d6d4f709e91e66c7c2b"
URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/" + MODEL_NAME
SIZE = 32166155


def download(destination):
    destination = Path(destination)
    if destination.is_symlink():
        raise RuntimeError("Symlinked speech model destination rejected.")
    if any(parent.is_symlink() for parent in destination.parents):
        raise RuntimeError("Symlinked speech model directory requires manual review.")
    if destination.exists():
        if destination.is_symlink() or hashlib.sha256(destination.read_bytes()).hexdigest() != SHA256:
            raise RuntimeError("Existing speech model differs; refusing to replace it.")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".model-", delete=False) as out:
            temporary = Path(out.name)
            total = 0
            digest = hashlib.sha256()
            with urllib.request.urlopen(URL, timeout=30) as response:
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > SIZE:
                        raise RuntimeError("Model response exceeds the verified size.")
                    digest.update(chunk)
                    out.write(chunk)
            if total != SIZE or digest.hexdigest() != SHA256:
                raise RuntimeError("Model checksum/size mismatch; no model installed.")
        temporary.chmod(0o600)
        # link() is atomic and refuses a destination created during download.
        import os
        os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    download(Path.home() / ".local/share/hypr-dictation/models" / MODEL_NAME)
    print("Verified model present; no microphone or inference process started.")
