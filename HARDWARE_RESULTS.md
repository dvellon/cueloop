# Hardware results

No physical results have been recorded. This file is the authoritative publication boundary between digitally verified work and reviewed observations made with real hardware.

Detailed procedures and raw observation blocks are authoritative in `HARDWARE_TESTS.md`. This file contains only reviewed inventory/result summaries suitable for publication.

## Evidence vocabulary

- **Simulated:** generated packet/audio conditions with no hardware in the loop.
- **Development-computer:** measured on the development host; record CPU/OS/version.
- **UNO Q:** measured on the physical UNO Q Linux/MCU system.
- **Physical CuePod:** measured with the XIAO Sense microphone and wireless transport.
- **Estimated:** derived from datasheets, arithmetic, or unverified assumptions.

## Inventory

| Item | Expected identity | Received / markings / quantity | Status |
|---|---|---|---|
| Arduino UNO Q | 4 GB / 32 GB, SKU ABX00173 | Not observed | Pending |
| Arduino order accessories | Exact packing list unknown | Not observed | Pending |
| Seeed XIAO ESP32S3 Sense | MPN 113991115 | Not observed | Pending |
| Protected LiPo | Adafruit 3.7 V 500 mAh, product 1578 | Not observed | Pending |
| JST-PH female pigtail | Adafruit product 261 | Not observed | Pending |
| Soldering station | YIHUA 926 III kit | Not observed | Pending |
| Multimeter | AstroAI AM33D | Not observed | Pending |

## Result records

Use one block per checklist run:

```text
Checklist ID:
Date/time/timezone:
Git commit:
Operator:
Hardware revisions/markings:
Firmware/App Lab versions:
Power source:
Test conditions:
Expected observation:
Observed value and unit:
Evidence tier:
Pass/fail/blocked:
Notes and artifact path:
```

Do not paste Wi-Fi credentials, personal data, or sensitive audio here.

## Prepared digital evidence (not a hardware result)

- Development-computer Arduino CLI compilation is recorded in `firmware/BUILD_MANIFEST.md`.
- Complete Windows flashing, bring-up, validation methods, expected observations, and the execution log are in root `HARDWARE_TESTS.md`.
- Short operator views remain in `user_checklists/WINDOWS_FLASHING.md`, `HARDWARE_BRINGUP.md`, and `PHYSICAL_VALIDATION.md`.
- No row above may change from “Not observed” until a physical operator records the observation using the result block.
