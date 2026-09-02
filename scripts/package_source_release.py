#!/usr/bin/env python3
"""Build a deterministic source archive from an exact committed CueLoop tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "packages"
FIXED_TIME = (2026, 9, 2, 0, 0, 0)
EXCLUDED_PATHS = {"PROJECT_PROMPT.md"}
EXCLUDED_PARTS = {".git", ".agents", ".codex", "__pycache__"}
FORBIDDEN_NAMES = {
    ".env",
    "credentials.json",
    "secrets.json",
    "wifi_secrets.h",
}
FORBIDDEN_SUFFIXES = {
    ".aac",
    ".bin",
    ".elf",
    ".flac",
    ".hex",
    ".jks",
    ".key",
    ".m4a",
    ".mp3",
    ".onnx",
    ".p12",
    ".pb",
    ".pem",
    ".pfx",
    ".pt",
    ".pth",
    ".sqlite",
    ".sqlite3",
    ".tflite",
    ".uf2",
    ".wav",
}


def run_git_bytes(*arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        error = (result.stderr.strip() or result.stdout.strip()).decode(
            "utf-8", errors="replace"
        )
        raise ValueError(f"git {' '.join(arguments)} failed: {error}")
    return result.stdout


def run_git_text(*arguments: str) -> str:
    return run_git_bytes(*arguments).decode("utf-8")


def commit_identity() -> str:
    return run_git_text("rev-parse", "HEAD").strip()


def tracked_tree(commit: str) -> list[tuple[str, str, str]]:
    raw = run_git_bytes("ls-tree", "-r", "-z", commit)
    entries: list[tuple[str, str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", maxsplit=1)
        mode, object_type, object_id = metadata.decode("ascii").split(" ")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(
                f"unsupported tracked entry {path_bytes.decode('utf-8')}: "
                f"{mode} {object_type}"
            )
        path = path_bytes.decode("utf-8")
        relative = PurePosixPath(path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe tracked path: {path}")
        if path in EXCLUDED_PATHS:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            raise ValueError(f"forbidden internal path is tracked: {path}")
        if relative.name in FORBIDDEN_NAMES or relative.name.startswith(".env."):
            raise ValueError(f"forbidden credential path is tracked: {path}")
        if relative.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"forbidden generated/private artifact is tracked: {path}")
        entries.append((path, mode, object_id))
    return sorted(entries)


def zip_info(name: str, *, executable: bool = False) -> ZipInfo:
    info = ZipInfo(name, FIXED_TIME)
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o755 if executable else 0o644) << 16
    return info


def build(version: str, *, allow_dirty: bool = False) -> tuple[Path, str]:
    status = run_git_text("status", "--porcelain", "--untracked-files=no")
    if status.strip() and not allow_dirty:
        raise ValueError(
            "tracked worktree is dirty; commit or restore intended release changes first"
        )

    commit = commit_identity()
    root_name = f"CueLoop-Source-v{version}"
    records: list[dict[str, object]] = []
    content_by_path: dict[str, tuple[bytes, bool]] = {}
    for path, mode, object_id in tracked_tree(commit):
        content = run_git_bytes("cat-file", "blob", object_id)
        content_by_path[path] = (content, mode == "100755")
        records.append(
            {
                "bytes": len(content),
                "path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )

    manifest = json.dumps(
        {
            "archive_contains_ignored_files": False,
            "commit": commit,
            "excluded_tracked_paths": sorted(EXCLUDED_PATHS),
            "files": records,
            "raw_audio_included": False,
            "runtime_model_included": False,
            "schema_version": 1,
            "version": version,
        },
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    archive = OUTPUT_ROOT / f"{root_name}.zip"
    with ZipFile(archive, "w") as bundle:
        for path, (content, executable) in content_by_path.items():
            bundle.writestr(
                zip_info(f"{root_name}/{path}", executable=executable), content
            )
        bundle.writestr(
            zip_info(f"{root_name}/SOURCE_MANIFEST.json"), manifest
        )

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="utf-8"
    )
    return archive, digest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="package committed HEAD even if tracked working files differ",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.version or any(character.isspace() for character in args.version):
        print("Package version must be nonempty and contain no spaces", file=sys.stderr)
        return 2
    try:
        archive, digest = build(args.version, allow_dirty=args.allow_dirty)
    except (OSError, ValueError) as error:
        print(f"Source packaging failed: {error}", file=sys.stderr)
        return 1
    print(f"Created {archive.relative_to(ROOT)}")
    print(f"SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
