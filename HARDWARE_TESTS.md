# CueLoop Windows flashing and hardware test record

This is the authoritative executable workflow for every board-dependent CueLoop V1 gate. It combines Windows deployment, safe electrical bring-up, model/network testing, and the observation log so hardware unavailability does not stop digital preparation. `HARDWARE_RESULTS.md` is the short publication boundary; measured summaries move there only after the corresponding record in this file is complete.

**Current state:** no physical board, cell, cable, accessory, App Lab run, or Fusion-generated file has been observed. Every hardware row below is pending.

## Evidence and record rules

Use exactly one evidence tier for every number:

- **simulated** — generated packets/audio/faults with no attached board;
- **development-computer** — measured on the Ubuntu or Windows build computer;
- **UNO Q** — measured on the identified physical UNO Q Linux/MCU target;
- **physical CuePod** — measured through the identified XIAO Sense microphone/transport;
- **estimated** — derived from a datasheet or arithmetic, not observed.

For each executed test, copy this block into the execution log at the end of this file:

```text
Test ID:
Date/time/timezone:
Git commit:
Operator:
Hardware identities/revisions/markings:
Windows version:
Arduino App Lab / IDE / CLI / core / library versions:
Firmware/App version and archive SHA-256:
Power source and connection path:
Network/AP/band/client-isolation conditions (no credentials):
Audio source/provenance/consent, distance, door, background, repetitions:
Expected observation or predeclared target:
Observed values with units/distribution:
Evidence tier:
Pass / fail / blocked / not run:
Error text and safe artifact paths:
Notes/limitations:
```

Never record Wi-Fi credentials, private audio, personal data, or an unredacted SSID/IP screenshot in Git. A failed target is evidence and must remain visible.

## Immediate stop conditions

Stop, disconnect external power if safe, and record the condition for heat, odor, swelling, puncture, damaged insulation, reverse/ambiguous polarity, a suspected battery short, smoke, unstable voltage, unexpected reset loops, or a board/cell marking that contradicts the procedure.

- Never solder with USB or the LiPo connected.
- Never solder directly to a LiPo cell.
- Never put an ammeter or resistance/continuity mode directly across a battery.
- Never trust wire color as polarity evidence.
- Never substitute a Qwiic cable for the JST-PH battery pigtail.
- Keep the LiPo detached for every flash and initial USB-only test.
- Do not drive a motor, haptic, buzzer, or other load directly from an MCU GPIO.

Read `docs/safety.md` and `hardware/ASSEMBLY.md` completely before tests H-300 through H-307.

## Release inputs to transfer to Windows

Generate from a clean tested commit on Ubuntu:

```bash
python3 scripts/sync_app_lab.py --include-model
python3 scripts/package_app_lab.py --version 0.1.0
python3 scripts/package_source_release.py --version 0.1.0
```

Transfer through a trusted path:

- `packages/CueLoop-App-Lab-v0.1.0.zip` and its `.sha256` sidecar;
- `packages/CueLoop-Source-v0.1.0.zip` and its `.sha256` sidecar;
- the XIAO sketch under `firmware/xiao_cuepod/`;
- optionally the ignored Ubuntu artifact folders for hash comparison, not guessed-address flashing.

Release ZIP identities are intentionally not hard-coded in this tracked file: the
source ZIP contains this file, so editing its digest here would immediately create
a different source archive. Generate both archives only from the final clean commit,
then retain their adjacent `.sha256` sidecars and verify the embedded commit fields:

| Artifact | SHA-256 / identity |
|---|---|
| App Lab ZIP | Adjacent `.sha256`; `PACKAGE_MANIFEST.json` must say `source_tree_clean: true` and its `source_commit` must equal `git rev-parse HEAD` |
| Source ZIP | Adjacent `.sha256`; `SOURCE_MANIFEST.json` `commit` must equal `git rev-parse HEAD` |
| YAMNet inside App | `10c95ea3eb9a7bb4cb8bddf6feb023250381008177ac162ce169694d05c317de` |
| XIAO platform/FQBN | `esp32:esp32` 3.3.11 / `esp32:esp32:XIAO_ESP32S3` |
| UNO Q platform/FQBN | `arduino:zephyr` 0.90.0 / `arduino:zephyr:unoq` |

In PowerShell, compare the calculated values to the sidecars:

```powershell
Get-FileHash .\CueLoop-App-Lab-v0.1.0.zip -Algorithm SHA256
Get-Content .\CueLoop-App-Lab-v0.1.0.zip.sha256
Get-FileHash .\CueLoop-Source-v0.1.0.zip -Algorithm SHA256
Get-Content .\CueLoop-Source-v0.1.0.zip.sha256
```

Do not proceed if either digest differs.

Also open both embedded manifests and compare their full 40-character commit to
the clean release commit. A matching sidecar alone does not prove that the archive
was generated from the intended source revision.

## Gate W-000 — inventory and Windows preparation

| ID | Action | Expected observation / record |
|---|---|---|
| W-001 | Photograph and record every delivered item/packing-list row. | UNO Q identity/configuration, XIAO/Sense/antenna, protected cell and pigtail, exact USB/power path, tools, accessories, markings, quantities, and visible condition are known. |
| W-002 | Install current official Arduino App Lab for 64-bit Windows 10/11. | App Lab version and installer source recorded; no unofficial package used. |
| W-003 | Install Arduino IDE 2 and Espressif Boards Manager URL `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`. | IDE version recorded; **esp32 by Espressif Systems 3.3.11** installed. |
| W-004 | Verify known USB-C cables/path carry data before connecting the product. | Cable/path identity recorded; Windows Device Manager changes on attach. |
| W-005 | Confirm a trusted 2.4 GHz-capable LAN permits client-to-client UDP/TCP. | No guest/IoT isolation; public/hostile Wi-Fi is not used; VPN/firewall constraints recorded without credentials. |

If Windows prompts for `mdns-discovery.exe`, allow private-network access only as appropriate for this trusted LAN. Network discovery uses mDNS/UDP 5353 and may fail on isolated networks even when internet access works.

## Gate W-100 — UNO Q baseline and App Lab deployment

Keep the CuePod cell detached throughout this gate.

| ID | Procedure | Expected observation / decision |
|---|---|---|
| W-101 | Connect UNO Q with the identified Arduino-order data/power path following the official host/SBC connection mode. | Board identity, 4 GB/32 GB configuration, connection mode, Linux image/update state, LAN address, and App Lab version recorded. |
| W-102 | Run Arduino App Lab’s built-in Blink example. | Documented MCU RGB LED blinks and App Lab reports success. Stop if this board baseline fails. |
| W-103 | Import the verified CueLoop ZIP, or extracted top-level `CueLoop` folder only if this App Lab version requests a directory. | `app.yaml`, `python/main.py`, requirements, sketch/profile, mapping, 4,126,810-byte model, and empty `data/` are present. |
| W-104 | Select UNO Q and press **Run**. | App Lab resolves the complete pinned runtime set, deploys Linux, compiles/flashes STM32, and starts both. Full resolver/monitor output and App Lab/image versions recorded. |
| W-105 | Observe health before and after Linux heartbeats. | LED4 may blink red while unhealthy, then becomes green; LED3 remains off until a confirmed cue. |
| W-106 | Inspect monitor/model startup. | Retain `CueLoop runtime: Python ...; machine=...; libc=...; ai-edge-litert=...`; expected audited family is Python 3.13, ARM64/AArch64, LiteRT 2.2.0. Dashboard and UDP startup appear; no native-import, checksum, tensor, embedded-label, database, socket, or Bridge error. |
| W-107 | Browse to `http://<UNO-Q-IP>:8080/` and `/api/status`. | Dashboard loads; local/no-recordings and model/input/connection states are visible; pod initially disconnected; Bridge status becomes connected. |
| W-108 | Inspect App `data/` before activity. | Empty except App-managed placeholders; no previous database or audio. |
| W-109 | Enable **Run at startup** only after the manual run and restart test pass. | Optional setting and resulting reboot behavior recorded. |

The Ubuntu distribution audit proves a complete exact-hash wheel set headed by `ai-edge-litert==2.2.0` exists for Arduino's documented CPython 3.13/Linux ARM64 runner and verifies 16 LiteRT shared objects as AArch64. It does not prove the received image's loader or model inference. If the set cannot resolve/import on the actual UNO Q image, preserve the complete Python/machine/libc/resolver/traceback output. Do not switch to synthetic inference or an unpinned runtime; that requires an evidence-backed implementation decision. Reflash the UNO Q Linux image only through the official recovery flow after diagnosing a corrupt/unresponsive OS and recording the erase impact.

## Gate W-200 — XIAO source flash and secret-safe configuration

1. Keep the LiPo detached and open `firmware\xiao_cuepod\xiao_cuepod.ino`; confirm both companion headers remain in that folder.
2. Select **XIAO_ESP32S3** and the newly appeared COM port. Keep default options; PSRAM is not required.
3. Click **Verify**, then **Upload**. Record IDE/core versions, COM port, memory report, and upload result.
4. If no port appears, use Seeed’s bootloader sequence: hold BOOT while connecting USB and release after enumeration, or hold BOOT and tap RESET. Do not press tools into nearby parts.
5. Open Serial Monitor at 115200 baud with LF endings. Expected: `CUELOOP_CUEPOD_READY`, a microphone-ready/error line, and a response to `STATUS`.

Optional PowerShell CLI path, after installing the pinned CLI/core on Windows:

```powershell
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 firmware\xiao_cuepod
arduino-cli board list
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 --port COM5 firmware\xiao_cuepod
```

Replace `COM5` with the observed port. Compile/upload source or use a complete tool-generated flash bundle. Never flash a standalone application `.bin` at a guessed ESP32 address.

Send these commands with actual Tab characters where `<TAB>` appears:

```text
SET_WIFI<TAB>private-ssid<TAB>password
SET_RECEIVER<TAB>UNO-Q-IP<TAB>57321
SET_POD_ID<TAB>0xC0E10001
POWER<TAB>USB
TEST<TAB>ON
STATUS
```

Expected: the password is never echoed; Wi-Fi connects; capture/sent counters increase; valid ACKs increase and `reachable=yes` after the receiver responds. Do not capture the credential command in evidence. Begin in `TEST ON`; do not claim acoustic accuracy from the generated tone.

## Gate C-100 — Windows Fusion native-model execution and return

All Ubuntu-executable CAD work is complete before this gate: the native `adsk` generator, shared parameter/contract sources, independent FreeCAD/OpenCascade implementation, committed neutral reference exports, and host validators. Read and execute `cad/FUSION_WINDOWS_RUNBOOK.md` exactly. The OpenCascade STEP is validation/reference geometry only and must never be imported as the authoritative contest model.

| ID | Procedure | Expected observation / required record |
|---|---|---|
| C-101 | Record Git commit, Windows/Fusion versions, operator/date/timezone, and SHA-256 of the Fusion script plus both JSON sources. | Inputs match the reviewed commit; any change is explained before execution. |
| C-102 | Install the three source files as one Fusion Python script and click **Run** once. | A new parametric design is created without requesting/importing STEP, mesh, BRep, or base geometry. |
| C-103 | Preserve the final message and `CueLoop_Bridge_validation.json`. | `Validation: PASS`; component/body/sketch/feature/timeline/parameter counts meet `design_contract.json`. |
| C-104 | Inspect Browser, timeline, Change Parameters, manufacturing bodies, and empty Mesh Bodies. | Hierarchy matches `cad/README.md`; six manufacturing components each finish as one solid; native sketches/features and at least 70 named parameters are visible. |
| C-105 | Change `pod_mic_hole_diameter` from 1.8 to 2.0 mm, observe all seven ports, then Undo to 1.8 mm. | Geometry updates without error, proving the native parameter/feature relationship; final retained output is restored to 1.8 mm. |
| C-106 | Complete section, measure, and interference review for shells, hardware envelopes, dock, clip, fasteners, openings, and service paths. | No unexplained collision, zero-thickness/sliver feature, floating body, blocked required opening, or impossible assembly; limitations/adjustments recorded. |
| C-107 | Close Fusion and reopen exported `CueLoop_Bridge_Native.f3d` in a clean session. | Component hierarchy, non-empty native timeline, parameters, six manufacturing solids, and reference-only names persist. |
| C-108 | Capture the ten screenshots and four native Fusion renders listed in the runbook. | Images prove native history/parameters/geometry and retain the caption `Fusion native concept render—physical enclosure and fit validation pending.` |
| C-109 | Return the complete export directory, CSV/ZIP hashes, screenshots/renders, and run record. | F3D, assembly STEP, six STEP/STL/3MF sets, exact source snapshots/manifest, BOM/parameters/validation, and checksums are non-empty and verify on Ubuntu with `cad/validate_cad.py --fusion-output`. |

If a visual defect requires adjustment, preserve the failure, update `design_parameters.json` or the generator in Git, rerun Ubuntu validation, then execute a fresh Fusion document. Do not repair a generated body manually and present it as script-generated. This gate remains pending until the genuine `.f3d` has been run, visually inspected, reopened, and returned.

## Gate H-000 — deterministic integrated bring-up

| ID | Test | Exact method | Expected observation / target |
|---|---|---|---|
| H-001 | XIAO USB boot | Reconnect on USB, capture serial banner/status. | Ready/mic status, no reset loop, stable/cool board. |
| H-002 | Test-tone framing | `TEST ON`; collect two `STATUS` samples at least 10 s apart. | About 50 captured/s; RMS and peak about 8192; clipped samples 0; counters rise. |
| H-003 | Wi-Fi/receiver ACK | Run CueLoop App and configured private-LAN destination. | Sent and valid ACK counters rise; `reachable=yes`; bad ACK/send-failure counters remain explainable. |
| H-004 | Receiver loss/recovery | Stop App for at least 7 s, observe, restart. | Within about 5 s reachability becomes false/timeout increments; valid ACKs resume; receiver restart visible without CuePod reboot. |
| H-005 | App/Bridge health | Observe LED4 and `/api/status` across startup. | Red unhealthy indication before heartbeat, green healthy after heartbeat; Bridge failures do not terminate Linux service. |
| H-006 | Cue language | Exercise one controlled confirmed path for each enabled class. | LED3 class family/priority cadence matches firmware; event/dashboard agree; clear/mute immediate. Test-tone/simulator paths stay labeled. |
| H-007 | Dashboard controls | Keyboard and pointer acknowledge, dismiss, mute/unmute. | Metadata action changes; MCU clears/mutes; LED4 blue while muted; no raw audio appears. |
| H-008 | Optional D4 button | Only if a normally-open D4-to-GND button is actually installed; press/release 20 times. | Exactly one acknowledgement per press, no idle phantom action. Otherwise mark not installed. |
| H-009 | MCU restart recovery | Restart/redeploy sketch during mute, then with an active pending cue. | Restart count rises; Linux stays alive and restores mute/current cue state. |
| H-010 | Privacy file audit | List App `data/` and inspect SQLite schema before/after a 15 min run. | Only bounded metadata/feedback database; no WAV/audio/blob column or audio file. |

Do not continue to battery testing or publish performance claims until H-001 through H-005 pass.

## Gate H-100 — microphone, network, and controlled loss

Use gentle, consented, provenance-recorded sources. Never strike the MEMS microphone or use a real emergency alarm at unsafe volume. Capture serial/dashboard counters before and after.

| ID | Condition | Repetitions / duration | Required measurements |
|---|---|---:|---|
| H-101 | Quiet room, `TEST OFF` microphone mode | 5 min | RMS/peak range, clipped samples, capture errors, packet loss, jitter, RSSI, disconnects |
| H-102 | Controlled event at 0.5 m line-of-sight | 10 per retained class | triggers, misses, confidence, evidence count, end-to-end latency |
| H-103 | Same source at 1 m and 3 m | 10/class/distance | precision/recall/confidence/latency by distance |
| H-104 | CuePod behind one closed interior door | 10/class | precision/recall/confidence/latency/loss and door description |
| H-105 | Background speech, television, music, fan | 15 min each | false triggers/audio-hour by condition/class; consent/source |
| H-106 | Confusable nontarget knocks, beeps, shouts | at least 10/type | suppression/confirmation behavior and false triggers |
| H-107 | Exact LAN path planned for video | 15 min | packet loss, duplicates/late, jitter, RSSI, disconnects |
| H-108 | Artificial 5% then 20% packet-loss replay | fixed licensed clips and same seed | output comparison and diagnostic accuracy; evidence remains simulated loss unless RF impairment itself is measured |

Nonconstant microphone values prove capture activity, not classifier accuracy.

## Gate H-200 — model evidence and temporal-policy comparison

1. Use self-recorded or legally reusable PCM16 mono 16 kHz WAV files under ignored storage and a complete manifest. Obtain consent for identifiable voices.
2. Keep calibration, validation, and held-out test sources separate. Never tune on the held-out test split.
3. Aim for at least 30 positive held-out examples per retained class across multiple sources/rooms and at least one hour of explicitly defined background. If unavailable, publish the actual smaller count and uncertainty.
4. Run `models/evaluate.py` and retain the generated JSON under an ignored path.
5. Report support, per-class TP/FP/FN/TN and confusion matrices, precision/recall/F1, missed-event rate, false triggers/audio-hour, calibration/Brier error, inference latency, annotated event latency where present, condition slices, and temporal versus single-window differences.
6. Retain a demo class only if held-out precision is at least 0.80 and recall at least 0.75, or disclose the miss and narrow/disable it.
7. Quiet/background goal: fewer than 1 false alert/hour on the specifically documented mixture. Never extrapolate beyond the recorded sources/environments.

## Gate H-300 — latency, resilience, power, fit, and accessibility

| ID | Test | Method | Predeclared goal / required record |
|---|---|---|---|
| H-301 | Warm UNO Q inference | At least 10 warmups then 100 invocations. | mean/median/p95/max, memory, runtime/Python/model identity; no invented pass threshold |
| H-302 | Physical end-to-end alert latency | 20 events; synchronized marker or 60/120 fps video showing source onset and LED3. | median ≤2.5 s, p95 ≤4.0 s; record frame indices/rate and ±1 frame uncertainty |
| H-303 | App restart | 10 restarts. | receiver/dashboard recover without manual DB repair or audio files |
| H-304 | Wi-Fi interruption | 10 AP/client interruptions. | bounded reconnect without board reboot; counters explain gaps |
| H-305 | Bridge interruption/MCU reset | 10 trials. | Linux remains alive, health visibly degrades, state resynchronizes |
| H-306 | 30-minute soak | physical microphone and normal private LAN. | no crash/unbounded growth; temperatures and counters remain plausible |
| H-307 | First battery power | Complete battery procedure below with cell outside enclosure. | five-minute stable stream/ACK run; no heat/odor/swelling/reset/lead movement |
| H-308 | Battery runtime | Full supervised charge, USB detached, normal stream to protected shutdown. | start/end time, usable hours, RSSI, resets, voltage/ambient conditions if safely measured |
| H-309 | Charge behavior | Supervised open-enclosure USB charge. | board revision, indicator sequence, elapsed time, repeatable temperature observation; no rate claim without current evidence |
| H-310 | Thermal soak | 30 min in USB then battery mode. | ambient and repeatable board/enclosure surface method/results |
| H-311 | Enclosure fit/service | Complete `cad/DIMENSION_VALIDATION.md`; insert/remove cables and cell with all power off. | no cell compression/sharp contact, pinched wire, blocked mic/antenna, forced closure, or inaccessible service path |
| H-312 | Cue accessibility | Consented intended user or structured evaluator. | immediate comprehension, non-color cadence distinction, comfort, acknowledge/mute success, limitations |
| H-313 | Video legibility | Record planned 1080p framing and view at normal size. | event, confidence, priority, connection, privacy, and physical cue legible without zoom |

Dashboard `pipeline_latency_ms` measures processing after a complete window, not full acoustic-to-human latency.

### Battery interconnect and first-power procedure for H-307

1. Remove USB and keep the battery disconnected. Inspect received XIAO BAT markings and cell/connector markings.
2. Measure the loose battery connector voltage/polarity without shorting contacts. Record probe orientation and sign.
3. Mate the battery to the loose pigtail away from the board, measure which pigtail conductor is actually positive, label both leads, disconnect the battery, and move it away.
4. Confirm the received XIAO pad mapping: official guidance places `BAT-` closest to USB-C and `BAT+` farther away. Stop if markings/revision contradict this.
5. With all power removed, tin/solder only the verified pigtail to the verified pads. Inspect magnified joints, insulate, and add strain relief.
6. With the cell still detached, continuity-check the intended end-to-end mapping and confirm no persistent low-resistance BAT+↔BAT- short. Never use resistance/continuity on the battery.
7. Repeat a complete USB-only test, then remove USB.
8. Place the cell outside the enclosure on a nonflammable surface, mate the verified connector, set `POWER BATTERY`, and supervise continuously for five minutes.
9. Disconnect and stop on any immediate-stop condition. Do not close the enclosure until fit/thermal checks pass.

## Gate H-400 — final physical evidence and submission

1. Reconcile the received minimum BOM and physical build against `hardware/BOM.md`, wiring, netlist, and SVG schematic.
2. Copy only reviewed quantitative summaries from this execution log to `HARDWARE_RESULTS.md` and `submissions/app_lab/TEST_RESULTS.md`; update the article/video using the same evidence tier and conditions.
3. Capture the required original photos in `submissions/app_lab/PHOTO_SHOT_LIST.md` and the physical sequence in `VIDEO_PACKAGE.md`.
4. Re-run the complete software suite, Pyright, both canonical firmware compiles, isolated App sketch compile, App/source packaging, and archive inspection after any hardware-driven code change.
5. Verify all published links/downloads while logged out and retain the final account confirmation.

## Execution log

No physical test records exist yet. Append completed blocks immediately below this line; do not replace the statement with a generic “passed.”

```text
Test ID: NOT RUN — INITIAL DIGITAL PREPARATION
Date/time/timezone: 2026-09-02 EDT
Git commit: to be replaced by the commit containing this file
Operator: not applicable
Hardware identities/revisions/markings: not observed
Windows version: not observed
Arduino App Lab / IDE / CLI / core / library versions: Ubuntu compile tools only; see firmware/BUILD_MANIFEST.md
Firmware/App version and archive SHA-256: development-computer artifacts only
Power source and connection path: not observed
Network/AP/band/client-isolation conditions: not observed
Audio source/provenance/consent, distance, door, background, repetitions: none
Expected observation or predeclared target: preparation only
Observed values with units/distribution: none
Evidence tier: development-computer documentation
Pass / fail / blocked / not run: not run
Error text and safe artifact paths: none
Notes/limitations: This record does not prove hardware behavior.
```

Official operational references are linked from `docs/official-requirements.md` and `user_checklists/WINDOWS_FLASHING.md`. Recheck them before physical work because App Lab, board images, and platform releases can change.
