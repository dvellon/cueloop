#!/usr/bin/env python3
"""Build a deterministic, secret-resistant CueLoop App Lab import archive."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app_lab" / "CueLoop"
OUTPUT_ROOT = ROOT / "packages"
FIXED_TIME = (2026, 9, 2, 0, 0, 0)
FORBIDDEN_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".jks",
    ".sqlite",
    ".sqlite3",
    ".wav",
    ".flac",
    ".mp3",
    ".m4a",
    ".local.h",
}
FORBIDDEN_NAMES = {".env", "credentials.json", "secrets.json"}


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def package_files() -> list[Path]:
    files: list[Path] = []
    for path in APP.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(APP)
        if "build" in relative.parts or "__pycache__" in relative.parts:
            continue
        if relative == Path("data/.gitkeep"):
            continue
        if path.name in FORBIDDEN_NAMES or any(
            path.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES
        ):
            raise ValueError(f"forbidden private/runtime file in package: {relative}")
        files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def zip_info(name: str, *, directory: bool = False) -> ZipInfo:
    info = ZipInfo(name, FIXED_TIME)
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o755 if directory else 0o644) << 16
    if directory:
        info.external_attr |= 0x10
    return info


def build(version: str) -> tuple[Path, str]:
    sync = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "sync_app_lab.py"),
            "--check",
            "--include-model",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if sync.returncode:
        raise ValueError(sync.stderr.strip() or sync.stdout.strip())

    files = package_files()
    entries: list[dict[str, object]] = []
    content_by_name: dict[str, bytes] = {}
    for path in files:
        relative = path.relative_to(APP).as_posix()
        content = path.read_bytes()
        content_by_name[relative] = content
        entries.append(
            {
                "path": relative,
                "bytes": len(content),
                "sha256": sha256_bytes(content),
            }
        )

    manifest = json.dumps(
        {
            "schema_version": 1,
            "app": "CueLoop",
            "version": version,
            "raw_audio_included": False,
            "runtime_data_included": False,
            "files": entries,
        },
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    archive = OUTPUT_ROOT / f"CueLoop-App-Lab-v{version}.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr(zip_info("CueLoop/data/", directory=True), b"")
        for relative, content in content_by_name.items():
            bundle.writestr(zip_info(f"CueLoop/{relative}"), content)
        bundle.writestr(zip_info("CueLoop/PACKAGE_MANIFEST.json"), manifest)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="utf-8"
    )
    return archive, digest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.1.0")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.version or any(character.isspace() for character in args.version):
        print("Package version must be nonempty and contain no spaces", file=sys.stderr)
        return 2
    try:
        archive, digest = build(args.version)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"App Lab packaging failed: {error}", file=sys.stderr)
        return 1
    print(f"Created {archive.relative_to(ROOT)}")
    print(f"SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
