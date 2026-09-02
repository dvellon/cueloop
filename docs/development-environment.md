# Development environment

## Verified Arduino baseline

Verified on the Ubuntu build machine on September 2, 2026:

| Tool/platform | Version | Target |
|---|---:|---|
| Arduino CLI | 1.5.1 (`01f3d4f2b`) | `/home/cd/.local/bin/arduino-cli` |
| Espressif ESP32 platform | 3.3.11 | `esp32:esp32:XIAO_ESP32S3` |
| Arduino UNO Q Zephyr platform | 0.90.0 | `arduino:zephyr:unoq` |
| Pyright | 1.1.413 | Python 3.11 static-analysis contract |

Pinned UNO Q sketch libraries verified on the build machine are `Arduino_RouterBridge` 0.4.3, `Arduino_RPClite` 0.3.0, `ArxContainer` 0.7.0, `ArxTypeTraits` 0.3.2, `DebugLog` 0.8.4, and `MsgPack` 0.4.2. The XIAO sketch uses only libraries supplied by ESP32 core 3.3.11.

The build machine is not assumed to have either board attached. Project build temporaries use `TMPDIR=/home/cd/.tmp-codex`; unrelated `/tmp` data must not be deleted, moved, or repurposed.

Before firmware work or after a toolchain change, run:

```bash
command -v arduino-cli
arduino-cli version
arduino-cli core list
arduino-cli board details --fqbn esp32:esp32:XIAO_ESP32S3
arduino-cli board details --fqbn arduino:zephyr:unoq
```

No extra platform or library may be installed silently. First confirm it is missing, document why it is needed and the intended pinned version, and ask the repository owner for approval.

## Verified reproducible build command

Run all three builds from the repository root:

```bash
./scripts/build_firmware.sh
```

The script executes the required CLI/core/board preflight, cleans all intermediate directories, uses separate work/output paths, and compiles the XIAO, canonical UNO Q, and isolated App Lab profile. It fixes `SOURCE_DATE_EPOCH` at `1788307200` (2026-09-02 00:00:00 UTC) and applies checkout-root `-ffile-prefix-map`/`-fdebug-prefix-map` flags to the ESP32 build. Those controls remove the otherwise varying `__DATE__`/`__TIME__` and embedded ELF-path digest from XIAO images. It then compares both UNO Q containers byte-for-byte and prints all release hashes.

The App Lab profile build resolves its pinned platform and libraries into Arduino CLI's isolated profile cache. The script does not install a missing tool or platform: it fails so the required version can be reviewed and approved. The build manifest records results and reproducible hashes. Arduino App CLI/App Lab itself is not installed on this Ubuntu builder, and no claim is made that the Python app has run on an UNO Q.

For a release-grade check in a separate local clone, with no hard-linked Git objects, run:

```bash
./scripts/verify_clean_checkout.sh
```

If the ignored pinned model exists in `models/artifacts/`, it is checksum-validated and supplied to the clean clone automatically. Otherwise use `--model PATH`, explicitly choose `--fetch-model`, or accept the two clearly reported model/package skips. The verifier preserves its ignored checkout under `tmp/` for inspection, runs the suite and Pyright against Python 3.11 compatibility, invokes the firmware builder, creates both release types when the model is available, and rejects tracked-file mutation.

## Desktop software path

The simulator/service uses Python 3.11 or newer and no third-party runtime dependency:

```bash
./scripts/test.sh
./scripts/demo.sh
```

`CUELOOP_DEMO_SECONDS=5 ./scripts/demo.sh` performs a finite smoke run. Runtime databases use an ignored `.sqlite3` path and contain structured metadata only.

The real-model path additionally uses the checksum-pinned artifact documented under `models/` and `ai-edge-litert==2.2.0`. Run `python3 scripts/sync_app_lab.py --include-model` to create the complete ignored local App Lab working package; `--check --include-model` verifies source and model drift.
