# Development environment

## Verified Arduino baseline

Verified on the Ubuntu build machine on September 1, 2026:

| Tool/platform | Version | Target |
|---|---:|---|
| Arduino CLI | 1.5.1 (`01f3d4f2b`) | `/home/cd/.local/bin/arduino-cli` |
| Espressif ESP32 platform | 3.3.11 | `esp32:esp32:XIAO_ESP32S3` |
| Arduino UNO Q Zephyr platform | 0.90.0 | `arduino:zephyr:unoq` |

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

## Desktop software path

The simulator/service uses Python 3.11 or newer and no third-party runtime dependency:

```bash
./scripts/test.sh
./scripts/demo.sh
```

`CUELOOP_DEMO_SECONDS=5 ./scripts/demo.sh` performs a finite smoke run. Runtime databases use an ignored `.sqlite3` path and contain structured metadata only.

