# Firmware build manifest

**Build date:** 2026-09-02 EDT

**Evidence tier:** development-computer compilation only

**Arduino CLI:** 1.5.1 (`01f3d4f2b`)

**Reproducible builder:** `scripts/build_firmware.sh`; clean intermediates, fixed `SOURCE_DATE_EPOCH=1788307200`, and checkout-root prefix mapping for ESP32

Compilation validates preprocessing, C++ APIs, linking, board/core compatibility, and resource accounting. It does not validate flashing, microphone data, Wi-Fi, Bridge transport, LEDs, optional actuators, power, timing, or physical behavior.

## XIAO ESP32S3 Sense CuePod

- FQBN: `esp32:esp32:XIAO_ESP32S3`
- Platform: `esp32:esp32` 3.3.11
- Result: 888,480 bytes program reported (26% of 3,342,336); 47,632 bytes global RAM (14% of 327,680), 280,048 bytes remaining
- Flash image: `firmware/xiao_cuepod/build/artifacts/xiao_cuepod.ino.bin`
- Image size: 888,624 bytes
- Image SHA-256: `651efe0835a6a934b4dbe5615920a4094d8ee476581b43468fe5f7dea30fed10`
- Merged flash image SHA-256: `2d80291b2a8e362b93a662d0d24d9f8aff087787fdea9fb97f931bbcd93d68d3`

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

The XIAO application and merged images were independently rebuilt in a second local clone with the same relative work paths and matched byte-for-byte. Without the fixed epoch, ESP32 core compile-time strings change; without prefix mapping, the image's embedded ELF digest changes with the checkout path even when loadable program bytes are otherwise identical. Only artifacts produced by the documented builder should be compared to the hashes above.

Build products remain ignored but are retained in the working copy for later Windows flashing. Run the builder and compare hashes after any firmware, platform, library, or build-policy change.
