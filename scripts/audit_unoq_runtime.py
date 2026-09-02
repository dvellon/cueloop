#!/usr/bin/env python3
"""Verify the hash-locked LiteRT wheel set for App Lab's Linux ARM64 runner."""

from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "models" / "unoq_runtime_manifest.json"
DEFAULT_LOCK = ROOT / "models" / "requirements-unoq-cp313.lock"
DEFAULT_WHEEL_DIR = ROOT / "tmp" / "unoq-wheel-audit-cp313"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_distribution(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def download_wheels(wheel_dir: Path, lock_path: Path, target: dict[str, Any]) -> None:
    wheel_dir.mkdir(parents=True, exist_ok=True)
    if any(wheel_dir.iterdir()):
        raise ValueError(f"download directory must be empty: {wheel_dir}")
    command = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--dest",
        str(wheel_dir),
        "--require-hashes",
        "--only-binary=:all:",
        "--platform",
        str(target["pip_platform"]),
        "--python-version",
        str(target["python_version"]),
        "--implementation",
        str(target["implementation"]),
        "--abi",
        str(target["abi"]),
        "-r",
        str(lock_path),
    ]
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode:
        raise ValueError(f"target wheel download failed with exit {result.returncode}")


def verify_lock(lock_path: Path, records: list[dict[str, Any]]) -> None:
    lock = lock_path.read_text(encoding="utf-8")
    for record in records:
        requirement = f'{record["distribution"]}=={record["version"]}'
        digest = f'sha256:{record["sha256"]}'
        if requirement not in lock or digest not in lock:
            raise ValueError(f"lock is missing {requirement} with its target hash")


def verify_litert_wheel(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    top_level = manifest["top_level"]
    native = manifest["native_validation"]
    with ZipFile(path) as wheel:
        corrupt = wheel.testzip()
        if corrupt is not None:
            raise ValueError(f"wheel CRC failure: {path.name}:{corrupt}")
        metadata = BytesParser().parsebytes(
            wheel.read(str(top_level["metadata_path"]))
        )
        wheel_metadata = wheel.read(str(top_level["wheel_metadata_path"])).decode(
            "utf-8"
        )
        if normalize_distribution(str(metadata["Name"])) != normalize_distribution(
            str(top_level["distribution"])
        ):
            raise ValueError("LiteRT wheel distribution metadata mismatch")
        if metadata["Version"] != top_level["version"]:
            raise ValueError("LiteRT wheel version metadata mismatch")
        if metadata["License"] != top_level["license"]:
            raise ValueError("LiteRT wheel license metadata mismatch")
        expected_tag = f'Tag: {top_level["wheel_tag"]}'
        if expected_tag not in wheel_metadata:
            raise ValueError(f"LiteRT wheel is missing {expected_tag}")

        unconditional: set[str] = set()
        for requirement in metadata.get_all("Requires-Dist", []):
            if ";" in requirement:
                continue
            match = re.match(r"[A-Za-z0-9_.-]+", requirement)
            if match is None:
                raise ValueError(f"cannot parse requirement metadata: {requirement}")
            unconditional.add(normalize_distribution(match.group(0)))
        expected_requirements = set(top_level["required_distributions"])
        if unconditional != expected_requirements:
            raise ValueError(
                "LiteRT dependency metadata mismatch: "
                f"expected {sorted(expected_requirements)}, got {sorted(unconditional)}"
            )

        shared_objects = sorted(name for name in wheel.namelist() if name.endswith(".so"))
        if len(shared_objects) != native["expected_shared_object_count"]:
            raise ValueError(
                f"expected {native['expected_shared_object_count']} shared objects, "
                f"got {len(shared_objects)}"
            )
        for name in shared_objects:
            header = wheel.read(name)[:20]
            if len(header) != 20 or header[:4] != b"\x7fELF":
                raise ValueError(f"native member is not ELF: {name}")
            if header[4] != native["elf_class"] or header[5] != native["elf_data"]:
                raise ValueError(f"ELF class/data mismatch: {name}")
            machine = int.from_bytes(header[18:20], "little")
            if machine != native["elf_machine_id"]:
                raise ValueError(f"ELF machine mismatch in {name}: {machine}")
    return {
        "distribution": metadata["Name"],
        "version": metadata["Version"],
        "license": metadata["License"],
        "wheel_tag": top_level["wheel_tag"],
        "shared_object_count": len(shared_objects),
        "shared_object_machine": manifest["target"]["elf_machine"],
    }


def audit(
    manifest_path: Path,
    lock_path: Path,
    wheel_dir: Path,
    *,
    download: bool,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported UNO Q runtime manifest schema")
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise ValueError("UNO Q runtime manifest has no wheel files")
    verify_lock(lock_path, records)
    if download:
        download_wheels(wheel_dir, lock_path, manifest["target"])

    expected_names = {str(record["filename"]) for record in records}
    actual_paths = sorted(wheel_dir.glob("*.whl"))
    actual_names = {path.name for path in actual_paths}
    if actual_names != expected_names:
        raise ValueError(
            f"wheel set mismatch: missing={sorted(expected_names - actual_names)}, "
            f"unexpected={sorted(actual_names - expected_names)}"
        )

    verified_files: list[dict[str, Any]] = []
    top_wheel: Path | None = None
    for record in records:
        path = wheel_dir / str(record["filename"])
        if path.stat().st_size != record["bytes"]:
            raise ValueError(f"wheel size mismatch: {path.name}")
        actual_digest = sha256(path)
        if actual_digest != record["sha256"]:
            raise ValueError(f"wheel SHA-256 mismatch: {path.name}")
        with ZipFile(path) as wheel:
            corrupt = wheel.testzip()
            if corrupt is not None:
                raise ValueError(f"wheel CRC failure: {path.name}:{corrupt}")
        verified_files.append(
            {
                "filename": path.name,
                "bytes": path.stat().st_size,
                "sha256": actual_digest,
            }
        )
        if normalize_distribution(str(record["distribution"])) == normalize_distribution(
            str(manifest["top_level"]["distribution"])
        ):
            top_wheel = path
    if top_wheel is None:
        raise ValueError("top-level LiteRT wheel is absent from manifest")

    return {
        "schema_version": 1,
        "status": "pass",
        "evidence_tier": manifest["evidence_tier"],
        "target": manifest["target"],
        "litert": verify_litert_wheel(top_wheel, manifest),
        "verified_files": verified_files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--wheel-dir", type=Path, default=DEFAULT_WHEEL_DIR)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit(
            args.manifest,
            args.lock,
            args.wheel_dir,
            download=args.download,
        )
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.write_report is not None:
            args.write_report.parent.mkdir(parents=True, exist_ok=True)
            args.write_report.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BadZipFile) as error:
        print(f"UNO Q runtime audit failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
