# Development environment

## Verified Arduino baseline

Verified on the Ubuntu build machine on September 1, 2026:

| Tool/platform | Version | Target |
|---|---:|---|
| Arduino CLI | 1.5.1 (`01f3d4f2b`) | `/home/cd/.local/bin/arduino-cli` |
| Espressif ESP32 platform | 3.3.11 | `esp32:esp32:XIAO_ESP32S3` |
| Arduino UNO Q Zephyr platform | 0.90.0 | `arduino:zephyr:unoq` |

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

## Verified build commands

Use distinct work and output paths; using the same directory can produce invalid copied outputs with this toolchain.

```bash
XDG_CACHE_HOME="$PWD/.cache" TMPDIR=/home/cd/.tmp-codex arduino-cli compile \
  --fqbn esp32:esp32:XIAO_ESP32S3 \
  --build-path firmware/xiao_cuepod/build/work \
  --output-dir firmware/xiao_cuepod/build/artifacts \
  firmware/xiao_cuepod

XDG_CACHE_HOME="$PWD/.cache" TMPDIR=/home/cd/.tmp-codex arduino-cli compile \
  --fqbn arduino:zephyr:unoq \
  --build-path firmware/uno_q_cue_controller/build/work \
  --output-dir firmware/uno_q_cue_controller/build/artifacts \
  firmware/uno_q_cue_controller

XDG_CACHE_HOME="$PWD/.cache" TMPDIR=/home/cd/.tmp-codex arduino-cli compile \
  --profile uno_q \
  --build-path app_lab/CueLoop/build/sketch-work \
  --output-dir app_lab/CueLoop/build/sketch-artifacts \
  app_lab/CueLoop/sketch
```

The App Lab profile build resolves its pinned platform and libraries into Arduino CLI's isolated profile cache. The build manifest records results and hashes. Arduino App CLI/App Lab itself is not installed on this Ubuntu builder, and no claim is made that the Python app has run on an UNO Q.

## Desktop software path

The simulator/service uses Python 3.11 or newer and no third-party runtime dependency:

```bash
./scripts/test.sh
./scripts/demo.sh
```

`CUELOOP_DEMO_SECONDS=5 ./scripts/demo.sh` performs a finite smoke run. Runtime databases use an ignored `.sqlite3` path and contain structured metadata only.

The real-model path additionally uses the checksum-pinned artifact documented under `models/` and `ai-edge-litert==2.2.0`. Run `python3 scripts/sync_app_lab.py --include-model` to create the complete ignored local App Lab working package; `--check --include-model` verifies source and model drift.
