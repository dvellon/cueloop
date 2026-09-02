# XIAO ESP32S3 Sense CuePod firmware

This sketch captures the Sense expansion board's PDM microphone as 16 kHz mono PCM16, emits one checksummed 684-byte CueLoop UDP packet every 20 ms, validates receiver heartbeats, reconnects Wi-Fi with bounded backoff, and keeps diagnostic counters. It contains no filesystem or raw-audio recording path.

## Pinned build target

- Arduino CLI 1.5.1
- `esp32:esp32` 3.3.11
- FQBN `esp32:esp32:XIAO_ESP32S3`
- Core libraries only: `ESP_I2S`, `WiFi`, `NetworkUDP`, and `Preferences`
- Default board options shown by Arduino CLI; no PSRAM dependency

Build from the repository root:

```bash
./scripts/build_firmware.sh
```

The builder compiles both project targets and the App Lab profile so their shared release evidence cannot drift. For the ESP32 image it also cleans intermediates, fixes the reproducible build epoch, and normalizes checkout-root paths before hashing. Ad-hoc Arduino CLI builds remain valid compile checks but their embedded compile time/path digest may differ. The `build/` directory and binary products are ignored. No extra Arduino library install is required.

## Configure without source credentials

Flash over USB, open a 115200-baud serial terminal with line ending LF, and send tab-separated commands. Passwords are written directly to ESP32 NVS and never echoed. They do not enter this repository.

```text
SET_WIFI<TAB>your-ssid<TAB>your-password
SET_RECEIVER<TAB>192.168.1.50<TAB>57321
SET_POD_ID<TAB>0xC0E10001
POWER<TAB>USB
TEST<TAB>ON
STATUS
```

`<TAB>` means an actual tab character. `HELP` prints the command list. `STREAM OFF` pauses transmission without recording anything; `ERASE` removes all saved CuePod configuration and restarts. Switch `TEST OFF` before microphone evaluation. Set `POWER BATTERY` after disconnecting USB so packet metadata remains honest; the installed board variant cannot automatically distinguish USB from battery power.

The pod binds local UDP port 57322. The receiver replies from port 57321 once per second. Five seconds without a valid matching CRC heartbeat sets `reachable=no`, increments `receiver_timeouts`, and marks the next packets as a restarted stream. This is reachability diagnostics, not authentication or reliable delivery.

`STATUS` also reports the most recent 20 ms frame's integer RMS and peak plus a cumulative clipped-sample count. In test-tone mode RMS/peak should be approximately 8192 with zero clipping. In microphone mode, nonzero changing values confirm only that samples vary; they do not establish acoustic-model accuracy.

## Battery telemetry boundary

The installed `XIAO_ESP32S3` variant does not expose a verified battery ADC pin/divider for this exact hardware revision, so the default firmware sends battery voltage `0` with `BATTERY_VALID` clear. Do not manufacture a voltage from an unverified pin.

If the physical board schematic and multimeter confirm a battery divider, create ignored `cuepod_hardware.local.h`, override the ADC pin and rational scale, then compare reported millivolts against the meter at multiple voltages before accepting telemetry. Never connect or solder a LiPo while powered; follow the project safety checklist.

## Hardware test still required

Compilation proves APIs and types only. The real board must confirm microphone waveform/non-clipping, pin orientation, Wi-Fi association, UDP heartbeat, receiver timeout/recovery, USB/battery metadata, and safe current/runtime. Append observations under the matching root `HARDWARE_TESTS.md` ID, then copy reviewed summaries to `HARDWARE_RESULTS.md`; do not reinterpret test-tone behavior as acoustic-model accuracy.
