# CueLoop: Private Room-to-Room Sound Awareness with UNO Q Edge AI

> A wireless microphone pod turns selected nearby sounds into uncertainty-aware visual cues—locally, without cloud audio or default recordings.

## The moment CueLoop is for

You are wearing headphones at a desk. A timer sounds in the kitchen, someone knocks at the door, or a collaborator calls from the next room. Turning every sound up is not a good answer, and placing cloud microphones throughout a home or workshop creates a different problem.

CueLoop is a private acoustic bridge. A thumb-sized, detachable CuePod listens in the space that matters. It streams short, sequence-numbered audio frames across a private local network to an Arduino UNO Q. The UNO Q runs the acoustic model locally, combines evidence over time, and interrupts only after a user-selected event has enough support. Its real-time STM32 processor turns the result into a physical RGB cue while a high-contrast local dashboard explains the event, confidence, priority, connection health, and privacy state.

The initial social-impact use case is sound awareness for people who are deaf or hard of hearing, but the interaction is intentionally broader. CueLoop can also support people wearing hearing protection, headphone users, caregivers, neurodivergent people who prefer a controlled cue to a startling sound, makers watching a process from another room, and anyone who wants awareness without a cloud microphone or audio archive.

CueLoop is an experimental awareness aid. It is not a certified alarm, security system, machine interlock, or medical device, and it never replaces required alarms, guards, supervision, or emergency procedures.

## More than a label on a screen

A one-window sound classifier can be confidently wrong. CueLoop makes uncertainty part of the interaction rather than hiding it.

The current V1 vocabulary is deliberately small: door knock/doorbell, alarm or appliance beep, dog bark, and a human attention call. The model also produces background and unknown suppression scores. Each monitored class has its own observe threshold, alert threshold, minimum evidence count, confirmation interval, cooldown, priority, and enabled state. One possible sound moves the state to **observing**. Repeated supporting windows move it to **confirming**. Only sufficient evidence creates a confirmed event and an interruption. Ambiguous input stays visible as uncertainty instead of becoming an immediate definitive alert.

A user can acknowledge, dismiss, mute, or disable a class. CueLoop stores that event/feedback metadata locally for evaluation, but it does not store the audio that produced it. The dashboard always distinguishes simulated/test input from physical input so a plumbing demo cannot masquerade as recognition accuracy.

## Why UNO Q is essential

CueLoop uses the dual-brain design as a design constraint, not a logo requirement.

The Qualcomm Dragonwing Linux side receives Wi-Fi audio, repairs small ordering gaps in a bounded jitter buffer, creates overlapping normalized model windows, runs LiteRT inference, maps AudioSet outputs into the small product vocabulary, applies temporal policy, stores metadata, and serves the local dashboard. Those are operating-system and AI-runtime jobs.

The STM32U585 side validates compact Bridge RPC commands and owns physical cue timing. LED3 communicates event family and priority cadence. LED4 communicates health or mute state. An optional normally-open button from D4 to ground can acknowledge the current cue without opening a browser. Because pulse timing and input debounce stay on the MCU, Linux load cannot turn them into a blocking `sleep()` sequence. A Linux heartbeat makes loss of the high-level app visible; a detected MCU restart causes Linux to re-send current mute/cue state.

Arduino App Lab packages `app.yaml`, the Python app, pinned inference requirement, model/mapping, and pinned Zephyr sketch profile into one deployable App. The official Router Bridge carries only compact event IDs, class codes, priorities, confidence permille, health, and acknowledgement—not raw audio.

## Architecture and data flow

The system is intentionally one-way at its privacy-sensitive edge: the CuePod emits volatile PCM; no command enables recording.

1. The integrated Seeed Sense PDM microphone is captured at 16 kHz, mono, signed 16-bit.
2. XIAO emits one 684-byte CueLoop Protocol v1 datagram every 20 ms. Each packet contains version, flags, pod ID, sequence, sample clock, capture uptime, format, optional telemetry, and independent header/payload CRC32 values.
3. UNO Q replies with a 24-byte CRC receiver heartbeat at most once per second. Five seconds without a valid reply makes receiver loss visible at the pod.
4. Linux strictly validates the packet, reorders a small bounded window, represents loss explicitly, and creates one-second overlapping inference windows.
5. The checksum-pinned Google YAMNet LiteRT v1 model returns 521 AudioSet scores. A reviewed mapping aggregates only explicit labels into CueLoop classes; broad generic speech is excluded from “attention call.”
6. The temporal engine combines evidence, applies cooldown/mute/priority, and creates a typed event only after confirmation.
7. Event metadata flows to SQLite, the REST dashboard, and a compact Bridge cue. Audio samples expire from bounded memory and are never passed to the database.
8. Dashboard or button feedback updates event metadata and clears or mutes the MCU cue.

The full block, power, processor, and protocol diagrams are in `hardware/DIAGRAMS.md`. The editable connectivity source is `hardware/schematics/cueloop_v1.netlist.json`; its human-readable export is `cueloop_v1.svg`.

## Bill of materials

The minimum electrical build deliberately uses onboard LEDs so unknown accessory inventory cannot block a reliable demo.

| Qty | Part | Manufacturer identity | Function | Checked list price |
|---:|---|---|---|---:|
| 1 | Arduino UNO Q 4 GB / 32 GB | Arduino ABX00173 | Linux edge AI/dashboard and STM32 physical cues | €82.90 incl. VAT on checked EU page |
| 1 | XIAO ESP32S3 Sense | Seeed Studio 113991115 | Wireless PDM microphone pod | US$13.90 |
| 1 | Protected 3.7 V 500 mAh LiPo | Adafruit 1578 | CuePod battery | US$7.95 |
| 1 | JST-PH female pigtail, 100 mm | Adafruit 261 | Detachable battery interconnect after measured polarity | US$0.75 |
| 1 | UNO Q USB-C power/data path | Exact ordered item recorded at inventory | Power and App Lab connection | Invoice pending |
| 1 | XIAO USB-C data cable | Known-good existing cable | Flash, serial, USB development | existing |
| 1 | Private 2.4 GHz Wi-Fi LAN | existing router/AP | Local transport | existing |

Core electronics subtotal is €82.90 plus US$22.60 before the order-specific power path, regional tax differences, and shipping. A computer running Windows 10/11 64-bit, YIHUA 926 III soldering station, and AstroAI AM33D multimeter are build infrastructure, not product parts.

No Qwiic cable is used in the minimum build. The optional D4 button, haptic driver/motor, buzzer/driver, or Modulino output is added only after exact inventory and electrical limits are known. A motor must never be driven directly from an MCU GPIO. The complete mechanical and V2 development BOM, including honest inventory gates, is in `hardware/BOM.md`.

## Wiring and battery safety

The two devices have separate power domains and communicate only through Wi-Fi. UNO Q uses its approved USB-C path. CuePod uses XIAO USB-C during development or the protected one-cell battery connected to the XIAO battery pads through the removable pigtail.

Seeed identifies XIAO battery negative as the pad closest to USB-C and positive as the pad farther away, but the received board markings and actual connector polarity must still be checked. Wire color is not evidence. The battery is detached while the pigtail is measured, tinned, soldered, inspected, continuity-checked, insulated, or strain-relieved. I never solder directly to the LiPo cell. First battery power happens outside the enclosure on a nonflammable surface after USB-only tests pass.

The exact meter and assembly sequence is in `hardware/ASSEMBLY.md` and the short operator checklist is `user_checklists/HARDWARE_BRINGUP.md`. The schematic also shows deliberate non-connections: no CuePod-to-UNO power/ground cable, no CuePod Qwiic, and no external actuator directly on GPIO.

## Build the software before touching the battery

The repository was developed simulator-first. On any Python 3.11+ computer, this runs the complete protocol, receiver, buffer, synthetic classifier, temporal engine, metadata store, API, and dashboard with visible simulated labeling:

```bash
./scripts/test.sh
./scripts/demo.sh
```

For the real-model workbench, create a dedicated environment, install the pinned runtime, fetch the official artifact through the size/SHA-verifying script, and benchmark it:

```bash
python3 -m venv .venv-model
.venv-model/bin/python -m pip install -r requirements-model.txt
.venv-model/bin/python scripts/fetch_yamnet.py
PYTHONPATH=linux .venv-model/bin/python models/benchmark_yamnet.py --iterations 100
```

Downloaded weights, raw/private audio, local credentials, databases, build trees, and release archives are ignored before they can enter Git.

Both sketches build with Arduino CLI 1.5.1, ESP32 core 3.3.11, and Arduino Zephyr core 0.90.0. Exact commands and output hashes are in `firmware/BUILD_MANIFEST.md`. The UNO Q App Lab sketch also compiles from its isolated pinned profile and produces byte-identical deployable binaries to the canonical UNO Q sketch on the development builder.

Create the complete import package only after the pinned model exists:

```bash
python3 scripts/sync_app_lab.py --include-model
python3 scripts/package_app_lab.py --version 0.1.0
```

The packager refuses source/model drift, rejects secret/runtime file types, leaves App `data/` empty, and writes a SHA-256 sidecar. The complete inference dependency set is also pinned and hash-audited for Arduino's documented CPython 3.13/Linux ARM64 runner: eight wheel archives and 16 LiteRT AArch64 native objects pass offline inspection. This is distribution evidence, not a claim that the received UNO Q has loaded it. On Windows, verify the archive digest, import it in Arduino App Lab, select the UNO Q, and press **Run**. The App prints Python, machine, libc, and LiteRT identity before model construction; retain that line. `user_checklists/WINDOWS_FLASHING.md` gives the full first-connection and recovery procedure.

Flash the XIAO from source with Arduino IDE 2 and `esp32 by Espressif Systems` 3.3.11 while the battery is detached. Select `XIAO_ESP32S3`, its COM port, verify, upload, then open Serial Monitor at 115200 baud with LF line endings.

## Configure and use CueLoop

CuePod configuration goes straight from USB serial into ESP32 NVS; the password is never echoed or present in source. Commands are tab-separated:

```text
SET_WIFI<TAB>private-ssid<TAB>password
SET_RECEIVER<TAB>UNO-Q-IP<TAB>57321
SET_POD_ID<TAB>0xC0E10001
POWER<TAB>USB
TEST<TAB>ON
STATUS
```

Start in `TEST ON`. The deterministic 1 kHz square tone validates frame cadence, CRC, Wi-Fi, heartbeat, buffering, App Lab, Bridge, and dashboard wiring without pretending to be a real event. `STATUS` should show rising capture/sent/ACK counters, `reachable=yes`, RMS/peak near 8192, and no clipped samples. Then switch `TEST OFF` for the physical microphone smoke test. Set `POWER BATTERY` only after USB is disconnected and the battery-safe gate has passed; this is honest metadata because the current board path does not automatically identify the power source.

Open `http://<UNO-Q-IP>:8080/`. The top row must identify input mode, pod connection, and local/no-recording privacy state at a glance. The main card shows current candidate/confirmed event, confidence, priority, and controls. Diagnostics show packet loss, jitter, inference time, RSSI, frame counts, model identity, and Bridge state. Configuration controls enable/disable classes and change policy without editing firmware.

The ideal demo is simple: place CuePod behind a closed door, trigger one controlled target event, show observing → confirming → alerting, show the physical cue and dashboard, acknowledge it, then play a documented confusable/background sound and show suppression or delayed confirmation. Never use a real emergency alarm at unsafe volume.

## AI model and evaluation honesty

V1 begins with Google's Apache-2.0 YAMNet classification LiteRT v1 artifact. The repository pins its 4,126,810-byte file by SHA-256, validates its fixed 15,600-sample float32 input and 521-score output, verifies embedded labels against the class map, and refuses startup if anything differs. The physical App never silently falls back to the synthetic classifier.

YAMNet is a broad AudioSet/YouTube-derived baseline, not a CueLoop-trained or calibrated model. A max aggregation over selected doorbell/knock, alarm/siren/buzzer/beep, dog/bark, and shout/yell labels is a hypothesis until held-out audio testing passes. Scores are not probabilities of safety, and a high smoke-alarm label does not make CueLoop a smoke alarm.

The evaluation tool refuses audio without source, license/ownership, consent, exact checksum, labels, and split metadata; it records environment, distance/door, background, and event intervals where those conditions are measured. Calibration, validation, and held-out test remain separate. It reports per-class support/confusion matrices/precision/recall/F1, false triggers per audio hour, missed-event rate, Brier/calibration error, condition slices, inference and annotated audio-to-decision latency, and the production temporal policy beside a one-window baseline. Raw clips stay ignored and the evaluator never writes derived audio.

## What has actually been measured

| Result | Evidence tier | Outcome |
|---|---|---|
| Automated regression suite | development computer / simulation | 67 tests pass: protocol/CRC/ACK, loss/reorder/restart/bounds, temporal engine, privacy storage, API, Bridge faults/restart, model/evaluation comparison gates, simulated transport benchmark, reproducible builds, commit-bound App/source archives, UNO Q distribution audit, hardware-record safety, and native-CAD/reference-output/submission contracts |
| Static Python analysis | development computer | Pyright: 0 errors, 0 warnings |
| XIAO firmware build | development computer compile | 888,480 bytes program (26%); 47,632 bytes global RAM (14%); fixed-epoch/path-normalized application and merged images match across two local checkouts |
| UNO Q STM32 build | development computer compile | 93,304 bytes program (11%); 34,018 bytes global RAM (12%); canonical and isolated App Lab binary hashes match |
| UNO Q Python distribution set | development computer, cross-platform download/audit | 8/8 exact-version/hash wheels pass; LiteRT metadata/version/license/dependencies match; all 16 native shared objects identify as AArch64. Target installation/loading/inference is not measured. |
| Pinned YAMNet runtime | development computer, deterministic synthetic workload | 100 runs: 1.834 ms mean, 1.919 ms p95, 1.997 ms max; 73,384 KiB whole-process peak RSS |
| Real-audio accuracy | not measured | No precision/recall/false-alert claim yet |
| UNO Q inference and end-to-end latency | not measured | Physical target required |
| Physical CuePod, Wi-Fi range, battery and enclosure | not measured | Hardware bring-up required |

The host benchmark proves that the pinned artifact and adapter execute; its synthetic tones were designed for the simulator, not YAMNet, and are deliberately excluded from accuracy reporting. Physical results will be inserted from reviewed `HARDWARE_RESULTS.md` summaries only after the matching root `HARDWARE_TESTS.md` gates are executed.

## Failure behavior and troubleshooting

Corrupt, wrong-version, wrong-length, wrong-format, or unknown-flag packets are dropped and counted. A small out-of-order window is repaired; missing frames become explicit bounded silence and a loss metric rather than an infinite wait. Huge sequence jumps do constant work. Wi-Fi retry backs off to 30 seconds. Receiver timeout is visible. Bridge calls have a one-second bound and failure counters, so a missing MCU cannot kill inference/dashboard. Model checksum/tensor failures stop real-model startup instead of inventing labels.

Common setup failures are usually simpler: a charge-only USB cable, wrong COM port, XIAO not in bootloader mode, guest Wi-Fi client isolation, wrong UNO Q IP, blocked UDP 57321 or TCP 8080, App Lab/mDNS firewall restrictions, missing model, or dependency resolution on the target image. `submissions/app_lab/TROUBLESHOOTING.md` gives symptom-by-symptom diagnosis without recommending unsafe resets or synthetic fallbacks.

## Privacy and security boundaries

CueLoop is local-first, not magically private. There is no cloud SDK, account, telemetry endpoint, or audio-file writer in the runtime. PCM is held only in bounded working memory, then released; only a maximum of 500 structured event/feedback records is retained. The App Lab `data/` folder is visible and clearable.

V1 UDP and dashboard traffic are unencrypted and unauthenticated. CRC detects accidental corruption, not a malicious sender. Use a private, trusted, client-visible LAN and never expose port 8080 or 57321 to the public internet. A hostile-network product version needs authenticated encryption, provisioning, access control, and a threat-model review.

Always obtain consent before placing any microphone in a shared/private space, even when nothing is recorded. A user can stop streaming, erase CuePod Wi-Fi configuration, clear history, or remove power.

## How to reuse and extend it

CueLoop is organized as an inspectable reference rather than one monolithic demo. The strict Python/C++ packet contract can be reused for other local sensor streams. The classifier protocol allows a different LiteRT model without rewriting buffers, policy, UI, or firmware. The temporal engine can be tested without audio hardware. The Bridge adapter demonstrates compact fault-contained Linux-to-MCU ownership. The App Lab synchronizer keeps desktop-tested code and packaged code byte-aligned, while the deterministic archive makes releases auditable.

Good contributions include a provenance-complete real-audio benchmark, event-level interval evaluator, measured UNO Q runtime/memory profile, authenticated transport profile, accessible cue-language study, or a new model adapter with an equally strict manifest. Do not contribute audio, credentials, downloaded weights, generated databases, or results without evidence labels. `CONTRIBUTING.md` and `submissions/app_lab/SOURCE_GUIDE.md` map the safe paths.

## Limits and next steps

The honest next step is not adding twenty labels. It is running the physical gates, measuring each of four classes, dropping any unreliable class, and polishing one excellent closed-door demo. Battery runtime, charge behavior, microphone clipping, network reach, target inference, full latency, false alerts, accessibility, enclosure fit, and recovery remain open until observed.

The related Autodesk entry is deliberately a different product path, **CueLoop Bridge**: a dockable portable receiver/CuePod system for makers and Autodesk users, with new haptics, tactile interactions, multi-pod workflows, Fusion Electronics, PCBWay DFM, manufacturing and travel testing. It shares the uncertainty core but not an identical name, story, enclosure, interaction, BOM, testing, or submission.

CueLoop's central idea remains small and human: know what needs attention without continuously listening, recording, or staying in the same room.

## Credits and licensing

Project-authored code, documentation, schematic, and design source are MIT licensed unless a file says otherwise. Google YAMNet and TensorFlow model sources retain Apache-2.0 licensing and attribution; `ai-edge-litert` and Arduino/Seeed libraries retain their upstream licenses. No third-party audio or downloaded model binary is committed. Final photos, video, fonts, music, and other submission media must be original or carry documented compatible permission; the safest video soundtrack is original narration and device/room sound only.
