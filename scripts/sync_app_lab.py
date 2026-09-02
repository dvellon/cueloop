#!/usr/bin/env python3
"""Synchronize canonical CueLoop sources into the self-contained App Lab app."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app_lab" / "CueLoop"
CORE_SOURCE = ROOT / "linux" / "cueloop"
CORE_TARGET = APP / "python" / "cueloop"
MODEL_SOURCE = ROOT / "models" / "artifacts" / "yamnet-classification-tflite-v1.tflite"
MODEL_TARGET = APP / "models" / MODEL_SOURCE.name

CORE_FILES = (
    "__init__.py",
    "api.py",
    "bridge.py",
    "buffering.py",
    "constants.py",
    "engine.py",
    "model.py",
    "pipeline.py",
    "protocol.py",
    "service.py",
    "storage.py",
    "yamnet.py",
    "dashboard/app.js",
    "dashboard/index.html",
    "dashboard/styles.css",
)

COPIES = {
    **{CORE_SOURCE / path: CORE_TARGET / path for path in CORE_FILES},
    ROOT / "firmware" / "uno_q_cue_controller" / "uno_q_cue_controller.ino": APP
    / "sketch"
    / "sketch.ino",
    ROOT / "firmware" / "uno_q_cue_controller" / "cue_controller_hardware.h": APP
    / "sketch"
    / "cue_controller_hardware.h",
    ROOT / "models" / "class_mapping.json": APP / "models" / "class_mapping.json",
    ROOT / "models" / "model_manifest.json": APP / "models" / "model_manifest.json",
    ROOT / "models" / "requirements-unoq-cp313.lock": APP
    / "models"
    / "requirements-unoq-cp313.lock",
    ROOT / "models" / "unoq_runtime_manifest.json": APP
    / "models"
    / "unoq_runtime_manifest.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def model_contract() -> tuple[int, str]:
    manifest = json.loads(
        (ROOT / "models" / "model_manifest.json").read_text(encoding="utf-8")
    )
    return int(manifest["expected_bytes"]), str(manifest["sha256"])


def validate_model(path: Path) -> None:
    expected_bytes, expected_sha = model_contract()
    if not path.is_file():
        raise ValueError(f"model artifact not found: {path}")
    if path.stat().st_size != expected_bytes:
        raise ValueError(
            f"model size mismatch: expected {expected_bytes}, got {path.stat().st_size}"
        )
    actual_sha = sha256(path)
    if actual_sha != expected_sha:
        raise ValueError(
            f"model SHA-256 mismatch: expected {expected_sha}, got {actual_sha}"
        )


def synchronize(*, check: bool, include_model: bool) -> list[str]:
    drift: list[str] = []
    for source, target in COPIES.items():
        if not source.is_file():
            raise ValueError(f"canonical source not found: {source}")
        if check:
            if not target.is_file() or source.read_bytes() != target.read_bytes():
                drift.append(str(target.relative_to(ROOT)))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    if include_model:
        validate_model(MODEL_SOURCE)
        if check:
            if not MODEL_TARGET.is_file() or sha256(MODEL_TARGET) != sha256(MODEL_SOURCE):
                drift.append(str(MODEL_TARGET.relative_to(ROOT)))
        else:
            MODEL_TARGET.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(MODEL_SOURCE, MODEL_TARGET)
            validate_model(MODEL_TARGET)
    return drift


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    parser.add_argument(
        "--include-model",
        action="store_true",
        help="require and copy/check the ignored pinned .tflite artifact",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        drift = synchronize(check=args.check, include_model=args.include_model)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"App Lab sync failed: {error}", file=sys.stderr)
        return 1
    if drift:
        print("App Lab package drift detected:", file=sys.stderr)
        for path in drift:
            print(f"  {path}", file=sys.stderr)
        return 1
    action = "verified" if args.check else "synchronized"
    model = " with pinned model" if args.include_model else ""
    print(f"App Lab package {action}{model}: {APP.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
