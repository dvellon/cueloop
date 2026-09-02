# CueLoop video production package

The primary cut is designed to finish at **2:55–3:00** and prove the project before explaining it. Every live-device shot must be captured in one continuous take or edited with honest cut labels. Do not imply that a simulator or prerecorded dashboard is a physical run.

## Primary three-minute storyboard

| Time | Picture / action | Narration | On-screen text |
|---:|---|---|---|
| 0:00–0:10 | User at desk wearing headphones; timer or knock occurs beyond doorway; no reaction. | “Important sounds do not always reach the person who needs them. Turning everything up—or putting cloud microphones everywhere—is not a good answer.” | `Important sound. Wrong room.` |
| 0:10–0:22 | CuePod close-up, then wide shot showing separate rooms and UNO Q. | “CueLoop is a private room-to-room sound-awareness system. A detachable microphone pod sends live evidence over a private local network to an Arduino UNO Q.” | `Local network · no cloud · no recordings by default` |
| 0:22–0:36 | Simple animated architecture overlay on the physical wide shot. | “UNO Q’s Linux processor runs the acoustic model and uncertainty policy. Its real-time microcontroller owns the physical cue, so timing stays deterministic.” | `XIAO → Wi-Fi → UNO Q Linux AI → STM32 cue` |
| 0:36–0:50 | App Lab project open; show descriptor, Python app, model identity, and sketch briefly. | “Arduino App Lab deploys the Linux app and the paired sketch together. A compact Bridge message crosses processors; raw audio never crosses that boundary.” | `One App Lab package · pinned model · compact Bridge RPC` |
| 0:50–1:20 | One uninterrupted real-device target-event run. Begin with idle dashboard, trigger controlled knock/timer, show observing then confirming, LED3/dashboard alert, acknowledge using D4 or dashboard. | “One window is not an alert. CueLoop first observes, asks for repeated evidence, then confirms. The cue explains what happened, how confident the system is, and whether the pod and model are healthy.” | Live status labels only; add `Physical run · [date] · [distance]` after capture. |
| 1:20–1:38 | Confusable/background trial in same setup; show no alert or delayed/unknown state. | “Ambiguous sound stays uncertain. Each class has its own threshold, evidence count, confirmation time, cooldown, and enable control.” | `Uncertainty is a product state` |
| 1:38–1:53 | Privacy control: status badge, history metadata, clear action; show no audio files in App data. | “Audio exists only in bounded working memory. CueLoop keeps at most five hundred event and feedback records—not recordings—and the user can clear them.” | `Metadata only · locally clearable` |
| 1:53–2:10 | Fast cuts: packet/ACK diagram, loss injection, Bridge disconnect/red health, recovery. | “The transport validates version, length, flags, and two CRCs. Loss is explicit and bounded. Receiver and Bridge failures are visible, and a restarted microcontroller is resynchronized.” | `CRC · bounded buffers · visible faults · restart recovery` |
| 2:10–2:25 | BOM overhead and safe battery/pigtail close-up; point to separate power domains. | “The minimum build needs only the UNO Q, XIAO Sense pod, protected cell, verified pigtail, and two data-capable USB paths. Polarity is measured before battery connection.” | `Core electronics: €82.90 + US$22.60` / `Never trust wire color` |
| 2:25–2:40 | Results graphic using only final `TEST_RESULTS.md` values. | “The reproducible software and both firmware targets are verified digitally. These physical latency, accuracy, range, and battery values were measured under the conditions shown here.” | Insert final physical values, or show `Physical metrics pending` if still pending. |
| 2:40–2:55 | Finished-system hero; user notices and acknowledges the cue. | “CueLoop is an experimental awareness aid, not a certified alarm. Its goal is simple: help someone know what needs attention without continuously listening, recording, or staying in the same room.” | `CueLoop` / `Know what needs your attention.` |
| 2:55–3:00 | Credits/end card. | None. | `Open source · Arduino UNO Q + App Lab · [stable project URL]` |

If the runtime exceeds three minutes, remove the 1:53–2:10 engineering montage first; do not accelerate speech, trim the physical proof, or remove the limitation statement.

## Primary narration script

Important sounds do not always reach the person who needs them. Turning everything up—or putting cloud microphones everywhere—is not a good answer.

CueLoop is a private room-to-room sound-awareness system. A detachable microphone pod sends live evidence over a private local network to an Arduino UNO Q.

UNO Q’s Linux processor runs the acoustic model and uncertainty policy. Its real-time microcontroller owns the physical cue, so timing stays deterministic. Arduino App Lab deploys the Linux app and the paired sketch together. A compact Bridge message crosses processors; raw audio never crosses that boundary.

One window is not an alert. CueLoop first observes, asks for repeated evidence, then confirms. The cue explains what happened, how confident the system is, and whether the pod and model are healthy. Ambiguous sound stays uncertain. Each class has its own threshold, evidence count, confirmation time, cooldown, and enable control.

Audio exists only in bounded working memory. CueLoop keeps at most five hundred event and feedback records—not recordings—and the user can clear them.

The transport validates version, length, flags, and two CRCs. Loss is explicit and bounded. Receiver and Bridge failures are visible, and a restarted microcontroller is resynchronized.

The minimum build needs only the UNO Q, XIAO Sense pod, protected cell, verified pigtail, and two data-capable USB paths. Polarity is measured before battery connection.

The reproducible software and both firmware targets are verified digitally. [Replace this sentence with concise physical results from the authoritative record, or say: “Accuracy, target latency, range, and battery runtime still require physical measurement.”]

CueLoop is an experimental awareness aid, not a certified alarm. Its goal is simple: help someone know what needs attention without continuously listening, recording, or staying in the same room.

## 60–75 second social cut

| Time | Cut |
|---:|---|
| 0:00–0:07 | Missed sound across doorway: `Important sound. Wrong room.` |
| 0:07–0:16 | CuePod/UNO Q wide: `Local network · no cloud audio` |
| 0:16–0:28 | App Lab + split architecture: `Linux AI + real-time MCU cue` |
| 0:28–0:49 | Real observing → confirming → alerting → acknowledge sequence |
| 0:49–0:59 | Uncertain/background suppression and metadata-only screen |
| 0:59–1:10 | Hero/end card with limitation and project URL |

Narration: “CueLoop helps important sounds cross a doorway without sending audio to the cloud. A XIAO microphone pod streams live evidence over a private LAN. Arduino UNO Q runs the acoustic model locally, waits for repeated evidence, and uses its real-time microcontroller for a clear physical cue. Ambiguous sound stays uncertain. Audio is discarded after inference; only locally clearable event metadata remains. CueLoop is an experimental awareness aid—not a certified alarm. Know what needs your attention without continuously listening or recording.”

## Capture and editing rules

- Record 4K or 1080p landscape at a constant frame rate; lock exposure, white balance, focus, and device-screen brightness.
- Capture room tone and narration separately. Avoid music unless it is original or carries documented, submission-compatible permission.
- Film LED3 so PWM does not band; test shutter settings before the real take. Do not alter cue color in post.
- Use captions for every spoken word and verify technical names manually. Keep text within a 10% safe margin and at least 42 px in a 1080p master.
- Normalize speech for clarity without erasing real device sounds. Avoid loud alarm stimuli and warn before any sharp sound.
- Show physical evidence tier, date, distance, and input source when a result is claimed. Label screen recordings `simulated` if any simulator is involved.
- Retain original camera files, the edit project, consent/releases, asset licenses, final transcript, and export checksum outside Git if they contain private data.
- Export H.264 MP4, 1920×1080, AAC audio, then watch the entire uploaded copy on a logged-out browser and a phone.

## Honest fallback if a physical capture fails

Submit no montage that can be confused with a working prototype. Use a split-screen engineering walkthrough clearly watermarked **SIMULATED PIPELINE — HARDWARE RESULT PENDING**, show both firmware compile records, and say which physical gate failed. This can explain the design but cannot replace the contest’s real-device evidence. If one class fails while others pass, disable and omit the failed class rather than staging its result.
