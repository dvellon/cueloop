# UNO Q inference-runtime distribution audit

**Checked:** 2026-09-02 UTC

**Evidence tier:** package-distribution compatibility; not execution on an UNO Q

## Result

The official Arduino App Bricks runtime source currently defines its Python base as `python:3.13-slim` and builds the application images for `linux/arm64`. Arduino App CLI documentation identifies `app-bricks/python-apps-base` as the Python runner image. For that documented tuple, PyPI supplies `ai-edge-litert==2.2.0` as a CPython 3.13 `manylinux_2_27_aarch64` wheel.

CueLoop downloaded the complete eight-wheel dependency set for CPython 3.13/AArch64 without installing it, locked every distribution by version and SHA-256, checked each archive CRC/size/digest, verified the LiteRT distribution/version/license/dependency metadata, and parsed all 16 native shared-object ELF headers. Every native member is 64-bit little-endian AArch64 (`e_machine=183`). The machine-readable evidence is in `unoq_runtime_manifest.json`; hashes used by `pip --require-hashes` are in `requirements-unoq-cp313.lock`.

This closes the Ubuntu-checkable distribution question. It does **not** prove the exact image on the received board, installation into App Lab, dynamic loading against that image's libc/libstdc++, import success, model inference, memory use, or latency. Those remain W-104 through W-106 and H-301 target observations. The App prints Python, machine, libc, and resolved `ai-edge-litert` version before model construction so the operator can retain that evidence.

## Reproduce

Download and audit into the ignored default directory:

```bash
python3 scripts/audit_unoq_runtime.py --download
```

Audit an already downloaded wheel directory without network access:

```bash
python3 scripts/audit_unoq_runtime.py \
  --wheel-dir tmp/unoq-wheel-audit-cp313 \
  --write-report tmp/unoq-runtime-audit.json
```

The download directory must be empty when `--download` is used. Wheels and generated reports remain ignored and are not shipped in source or App archives; App Lab resolves the pinned requirements on the target.

## Primary sources

- Arduino App Bricks Python runtime/source: <https://github.com/arduino/app-bricks-py>
- Arduino App CLI runner-image documentation: <https://github.com/arduino/arduino-app-cli/blob/main/docs/user-documentation.md>
- `ai-edge-litert` 2.2.0 files and metadata: <https://pypi.org/project/ai-edge-litert/2.2.0/>
