# Product requirements

## Shared user promise

CueLoop helps a person notice a user-selected acoustic event across an acoustically separated space without cloud microphones, default audio recording, or a continuously listening human. It is useful to people who are deaf or hard of hearing and also to headphone users, workers using hearing protection, caregivers, neurodivergent users, makers, and anyone moving between rooms.

The product is an awareness aid. It does not guarantee detection, is not safety-certified, and cannot replace smoke/CO alarms, machine guarding, supervision, or medical care.

## V1: CueLoop

### Primary demonstration

A detached CuePod sits behind a closed door and hears one controlled target event. The UNO Q in the other room receives live evidence, performs local inference, combines multiple windows, confirms the event, drives a physical cue through the STM32, and shows a large dashboard alert. A confusable/background sound is then suppressed or held for confirmation. The user acknowledges the alert. Diagnostics show loss and latency; the privacy indicator shows that no raw recording is retained.

### Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| V1-F01 | Capture 16 kHz mono audio from the XIAO Sense PDM microphone. | Target compile plus observed mic smoke test. |
| V1-F02 | Send versioned, sequence-numbered audio frames over local Wi-Fi and reconnect after receiver/network interruption. | Protocol tests, simulated recovery, physical recovery test. |
| V1-F03 | Bound all audio buffering and discard consumed audio by default. | Unit test and code review; memory observation on target. |
| V1-F04 | Normalize model windows and classify through a replaceable local model adapter. | Unit/integration tests and target inference benchmark. |
| V1-F05 | Combine temporal evidence with per-class threshold, confirmation, cooldown, priority, and mute policy. | Deterministic state-machine tests. |
| V1-F06 | Represent uncertain outcomes as `observing` or `confirming`, never an immediate definitive alert. | Engine/API tests and dashboard demo. |
| V1-F07 | Let the user acknowledge, dismiss, or mute; persist event metadata/feedback locally without raw audio. | API tests and database inspection. |
| V1-F08 | Show pod health, event, confidence, time, confirmation, priority, privacy, loss, jitter, and latency locally. | Accessible desktop and UNO Q browser review. |
| V1-F09 | Send compact cue commands to the STM32; STM32 owns physical timing and acknowledgement input. | Bridge integration plus physical cue test. |
| V1-F10 | Provide test-tone, synthetic, WAV replay, loss/jitter/latency, and restart paths without hardware. | One-command demo and automated tests. |

### Quality targets

Targets are goals, not results:

- Median end-to-end alert latency: at most 2.5 seconds for confirmed events; p95 at most 4 seconds.
- Packet loss: demonstration remains understandable at 5% random loss; diagnostics remain accurate at 20%.
- False alerts: fewer than 1 per hour in the defined quiet/background test mix.
- Selected-class precision: at least 0.80; selected-class recall: at least 0.75 on the documented evaluation set.
- Dashboard: WCAG-oriented color contrast, keyboard-operable controls, non-color-only cue language, primary alert legible in a 1080p competition video.
- Startup/recovery: services recover without unbounded files or manual database repair.

### Initial vocabulary

`door_knock`, `alarm_beep`, `dog_bark`, and `attention_call`; `background` and `unknown` are suppression outcomes. Safety-alarm sounds may be evaluated as acoustic patterns, but the UI always retains the awareness-aid limitation.

## V2: CueLoop Bridge

CueLoop Bridge is not V1 in a prettier box. It evolves the shared acoustic/uncertainty core into a manufacturable portable system for multi-space creative and technical work.

### V2-specific requirements

- Dockable, separately placeable CuePod with protected microphone labyrinth, USB access, charging/power-state affordance, battery service strategy, and repeatable orientation.
- Portable receiver with a purposeful belt/bag clip, desk stand, lanyard points, tactile controls, haptic motor, high-visibility cue, and dock/transport relationship.
- Compact, carry-on-safe construction with no loose exposed LiPo, sharp tools, high-power laser, prohibited radio, or hazardous material.
- Multi-context modes for printer/CNC/test-rig completion, door/collaborator attention, and travel/conference awareness.
- Multi-pod identity and location cues, while preserving local-only processing and raw-audio deletion.
- Fusion master assembly, named parameters, electronics clearances, acoustic path, fastening/service plan, PCBWay-ready DFM, and potential carrier PCB.
- A credible path to roughly 750 manufactured units: assembly time, fastener count, molded/printed alternatives, test points, labeling, firmware provisioning, and end-of-line test.
- New Autodesk-user testing, interactions, CAD, manufacturing work, and submission story tracked separately from V1.

## Non-goals for the September V1

- Certification, guaranteed emergency detection, speech transcription, speaker identification, cloud accounts, remote internet monitoring, long-term raw audio recording, multi-pod production management, or a custom PCB.
- Audio compression unless benchmarks show raw PCM fails the demonstration requirements.
- More event labels solely to increase a feature count.
