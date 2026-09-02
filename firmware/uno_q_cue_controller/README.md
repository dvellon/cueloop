# UNO Q STM32 cue-controller firmware

This sketch gives the STM32U585 deterministic ownership of physical cue timing. Linux sends compact Bridge RPC commands; the MCU validates them, generates nonblocking LED/haptic/buzzer patterns, debounces an optional acknowledgement button, reports health, and stops outputs immediately on clear/mute.

## Pinned dependencies and compile

- Arduino CLI 1.5.1
- `arduino:zephyr` 0.90.0
- FQBN `arduino:zephyr:unoq`
- `Arduino_RouterBridge` 0.4.3
- `Arduino_RPClite` 0.3.0 (RouterBridge dependency)

```bash
TMPDIR=/home/cd/.tmp-codex arduino-cli compile \
  --fqbn arduino:zephyr:unoq \
  --build-path firmware/uno_q_cue_controller/build/work \
  --output-dir firmware/uno_q_cue_controller/build/artifacts \
  firmware/uno_q_cue_controller
```

The ignored artifact folder is retained for later Windows flashing. Compilation does not prove LED polarity, brightness, button wiring, optional actuator current, or Bridge operation on a physical UNO Q.

## Bridge interface

| RPC / notification | Direction | Arguments / result |
|---|---|---|
| `cueloop/cue` | Linux → MCU call | `event_id`, class code 1–4, priority 1–3, confidence 0–1000; returns accepted boolean |
| `cueloop/clear` | Linux → MCU call | event ID (or empty for current); returns boolean |
| `cueloop/mute` | Linux → MCU call | boolean; returns actual muted state |
| `cueloop/heartbeat` | Linux → MCU call | Linux uptime milliseconds; returns MCU uptime milliseconds |
| `cueloop/status` | Linux → MCU call | no arguments; returns compact status string |
| `cueloop/ack` | MCU → Linux notification | acknowledged event ID |
| `cueloop/mcu_status` | MCU → Linux notification | uptime, health, active/muted state, counters |

Class codes are 1 door knock, 2 alarm/beep, 3 dog bark, and 4 attention call. LED3 carries event color and priority pulse cadence; LED4 is green for a healthy Linux heartbeat, blue when muted, and blinking red when Bridge/Linux health is unavailable. Both onboard MCU RGB LEDs are active low at the GPIO layer; the sketch follows Arduino's documented digital/PWM APIs.

## Optional hardware

The minimum build needs no external actuator: onboard LEDs provide the physical cue. A normally-open button from D4 to GND enables immediate acknowledgement; without it, the pull-up remains inactive and dashboard acknowledgement still works. Optional active-high haptic/buzzer pins can be set in ignored `cue_controller_hardware.local.h` only after the driver/transistor/current path is documented—do not drive a motor directly from an MCU GPIO.

Record physical Bridge, LED, debounce, cue-timing, and restart observations under H-005 through H-009/H-305 in root `HARDWARE_TESTS.md`, then copy reviewed summaries to `HARDWARE_RESULTS.md`.
