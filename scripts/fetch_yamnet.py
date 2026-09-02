#!/usr/bin/env python3
"""Fetch the pinned official YAMNet LiteRT artifact with strict verification."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "models" / "model_manifest.json"
DEFAULT_DESTINATION = ROOT / "models" / "artifacts"
MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def verify(path: Path, manifest: dict[str, object]) -> None:
    expected_size_value = manifest.get("expected_bytes")
    expected_digest = manifest.get("sha256")
    if isinstance(expected_size_value, bool) or not isinstance(expected_size_value, int):
        raise ValueError("manifest expected_bytes must be an integer")
    if not isinstance(expected_digest, str) or len(expected_digest) != 64:
        raise ValueError("manifest sha256 must be a 64-character string")
    expected_size = expected_size_value
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise ValueError(f"size mismatch: expected {expected_size}, got {actual_size}")
    actual_digest = digest(path)
    if actual_digest != expected_digest:
        raise ValueError(
            f"SHA-256 mismatch: expected {expected_digest}, got {actual_digest}"
        )


def download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "CueLoop-model-fetcher/1"})
    with urlopen(request, timeout=60) as response, destination.open("wb") as output:
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > MAX_DOWNLOAD_BYTES:
            raise ValueError("server-declared model size exceeds safety limit")
        total = 0
        while block := response.read(1024 * 1024):
            total += len(block)
            if total > MAX_DOWNLOAD_BYTES:
                raise ValueError("download exceeded safety limit")
            output.write(block)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.destination.mkdir(parents=True, exist_ok=True)
    target = args.destination / str(manifest["artifact_filename"])
    if target.exists():
        verify(target, manifest)
        print(f"Verified existing {target}")
        return 0

    with tempfile.NamedTemporaryFile(
        dir=args.destination, prefix=".yamnet-", suffix=".part", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        download(str(manifest["download_url"]), temporary_path)
        verify(temporary_path, manifest)
        temporary_path.replace(target)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    print(f"Downloaded and verified {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"model fetch failed: {error}", file=sys.stderr)
        raise SystemExit(2) from error
