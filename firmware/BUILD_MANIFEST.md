# Firmware build manifest

**Build date:** 2026-09-02 EDT

**Evidence tier:** development-computer compilation only

**Arduino CLI:** 1.5.1 (`01f3d4f2b`)

Compilation validates preprocessing, C++ APIs, linking, board/core compatibility, and resource accounting. It does not validate flashing, microphone data, Wi-Fi, Bridge transport, LEDs, optional actuators, power, timing, or physical behavior.

## XIAO ESP32S3 Sense CuePod

- FQBN: `esp32:esp32:XIAO_ESP32S3`
- Platform: `esp32:esp32` 3.3.11
- Result: 887,568 bytes program reported (26% of 3,342,336); 47,632 bytes global RAM (14% of 327,680), 280,048 bytes remaining
- Flash image: `firmware/xiao_cuepod/build/artifacts/xiao_cuepod.ino.bin`
- Image size: 887,712 bytes
- Image SHA-256: `29bddc5e6fde7cedd1698685e809258c298c93a1c785b636494aa0e3688daea0`
- Merged flash image SHA-256: `ce1766f482becf01248c7ecc4cd977ecc36f100ca0df15b85620d5d87a08d9d7`

## UNO Q STM32U585 cue controller

- FQBN: `arduino:zephyr:unoq`
- Platform: `arduino:zephyr` 0.90.0
- Direct library: `Arduino_RouterBridge` 0.4.3; complete pinned dependency set is in the App Lab `sketch.yaml`
- Result: 93,304 bytes program reported (11% of 786,432); 34,018 bytes global RAM (12% of 262,144), 228,126 bytes remaining
- Binary: `firmware/uno_q_cue_controller/build/artifacts/uno_q_cue_controller.ino.bin`
- Binary size: 32,464 bytes
- Binary SHA-256: `06af97d5714d0fe2caa8ac5c4d37c55a7f5b2fe895c4ba1b18f597e0be30e459`
- Signed-container candidate: `uno_q_cue_controller.ino.bin-zsk.bin`, 32,480 bytes, SHA-256 `657c39742a0a9ebf512a1198bd30282f8501e24b80a17e98817a81d417b214c5`

## Exact App Lab sketch profile

The self-contained `app_lab/CueLoop/sketch` was also compiled using its isolated `uno_q` profile. It reported the same 93,304-byte program and 34,018-byte RAM use. Its `.bin` and `.bin-zsk.bin` hashes exactly match the canonical UNO Q outputs above, demonstrating that the synchronized App Lab MCU source and pinned profile reproduce the canonical binaries on this builder.

Build products remain ignored but are retained in the working copy for later Windows flashing. Rebuild and compare hashes after any firmware, platform, or library change.
