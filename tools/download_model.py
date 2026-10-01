#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Explicit verified model download; does not load or start the model."""
import hashlib
from pathlib import Path
import tempfile
import urllib.request

SHA256 = "818710568da3ca15689e31a743197b520007872ff9576237bda97bd1b469c3d7"
URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny-q5_1.bin"
SIZE = 32152673


def download(destination):
    destination = Path(destination)
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
        temporary.hardlink_to if False else None  # no following destination symlinks
        import os
        os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    download(Path.home() / ".local/share/hypr-dictation/models/ggml-tiny-q5_1.bin")
    print("Verified model present; no microphone or inference process started.")
