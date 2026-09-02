# Wiring and pin assignments

## Minimum V1 external wiring

| From | To | Signal/purpose | Required verification |
|---|---|---|---|
| Adafruit 1578 battery JST-PH | Adafruit 261 mating pigtail | Detachable 1-cell LiPo connection | Connector mating and measured polarity; never trust wire color |
| Pigtail verified positive lead | XIAO `BAT+` pad | 3.7 V nominal battery positive | Seeed identifies the positive pad as the side farther from USB-C |
| Pigtail verified negative lead | XIAO `BAT-` pad | Battery return | Seeed identifies the negative pad as the side closest to USB-C |
| XIAO USB-C | Windows laptop USB-C data cable | Flash, serial configuration, USB development power/charge | Battery disconnected during soldering; known-good data cable |
| UNO Q USB-C | Approved Arduino-order supply/data/PD path | UNO Q power and App Lab connection | Exact accessory and mode confirmed from packing list/manual |
| CuePod Wi-Fi | UNO Q Wi-Fi on same trusted LAN | UDP 57321 PCM/ACK transport | 2.4 GHz support, IP address, firewall, no guest isolation |

There is no wired signal or shared ground between CuePod and UNO Q during normal use. There is no Qwiic cable in the minimum build.

## Integrated CuePod signals

These connections are already present on the Seeed Sense expansion board and must not be re-wired externally.

| Function | ESP32-S3 GPIO | Firmware API |
|---|---:|---|
| PDM microphone clock | GPIO42 | `I2S.setPinsPdmRx(42, 41)` clock argument |
| PDM microphone data | GPIO41 | `I2S.setPinsPdmRx(42, 41)` data argument |
| Audio format | — | 16 kHz, mono, signed 16-bit, 320 samples/20 ms |

The XIAO hardware does not expose a verified software battery-voltage divider for this build; battery telemetry remains invalid/zero by default.

## UNO Q minimum and optional connections

| Ref/function | UNO Q pin | Other terminal | Firmware state |
|---|---|---|---|
| Event RGB | MCU LED3 R/G/B (`PH10/PH11/PH12`) | Onboard | Required fallback; class color and priority cadence |
| Health RGB | MCU LED4 R/G/B (`PH13/PH14/PH15`) | Onboard | Green healthy, blue muted, blinking red unhealthy |
| Optional acknowledgement | D4 | Normally-open S1 to GND | `INPUT_PULLUP`; safely inactive when absent |
| Optional haptic | Unassigned | Qualified driver input only | `CUELOOP_HAPTIC_PIN=-1`; disabled |
| Optional buzzer | Unassigned | Qualified driver/input only | `CUELOOP_BUZZER_PIN=-1`; disabled |

All UNO Q MCU GPIO is 3.3 V logic. The current Arduino pinout states MCU GPIO is 5 V tolerant except A0/A1, but CueLoop V1 does not rely on 5 V signaling. Do not connect an actuator until its driver, supply, grounding, and suppression are documented.

## Battery pigtail solder mapping

The authoritative mapping is measured polarity, not insulation color:

```text
Battery positive connector contact ── measured pigtail lead ── XIAO BAT+
Battery negative connector contact ── measured pigtail lead ── XIAO BAT-
                                                             (closest to USB-C)
```

Record connector-face orientation, meter reading, and lead mapping under H-307 in root `HARDWARE_TESTS.md` before tinning. The battery stays physically unplugged for every soldering, inspection, and continuity step.
