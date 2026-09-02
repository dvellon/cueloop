# CueLoop photo and screenshot shot list

Capture originals at the highest practical resolution, then export web copies without overwriting them. For every evidence image, record date, setup, hardware revisions, input source, distance, Git commit, and whether the screen shows physical or simulated input.

## Required publication sequence

| ID | Shot | Must prove / show | Acceptance check |
|---|---|---|---|
| P01 | 16:9 hero across doorway | pod and receiver in separate spaces; dashboard/cue legible | real hardware; strong thumbnail crop; no private items/third-party clutter |
| P02 | Finished system overhead | all product parts and their physical relationship | exact submitted BOM parts only; labels readable |
| P03 | CuePod front/back | XIAO Sense identity, microphone opening, safe enclosure/strain relief | no exposed conductor; actual revision visible in a companion close-up |
| P04 | Battery pigtail polarity | measured connector orientation and insulated joints | battery disconnected while probing/soldering; meter reading and probe placement visible |
| P05 | UNO Q receiver | actual board, approved USB-C power/data path, LED3 and LED4 | no unsupported actuator; connection path identifiable |
| P06 | Successful App Lab run | selected UNO Q, CueLoop running, physical mode | no credentials/IP if sensitive; app/model version visible |
| P07 | Idle dashboard | connection/privacy/model status and quiet state | `physical` input; `Local · no recordings` visible |
| P08 | Observing state | first uncertain candidate before an alert | confidence/evidence visible; same trial as P09/P10 where possible |
| P09 | Confirmed event | dashboard event plus physical LED3 cue | event identity and evidence tier visible; not a simulator |
| P10 | Acknowledged event | user action and cleared cue/history feedback | before/after pair or continuous video frame references |
| P11 | Fault state | disconnected pod or Bridge with honest health cue | controlled safe fault; recovery documented |
| P12 | Readable schematic | complete signal and power separation | use repository SVG export; no raster blur |
| P13 | Wiring close-up | optional D4-to-GND button, if installed | exact pins visible; no button photo if feature was not built |
| P14 | Test setup | source, measuring device, distance geometry, room | ruler/tape and device screen readable; no invented calibration |
| P15 | Enclosure/fit | all closures, ports, mic opening, ventilation | no pinched cell/wire; USB accessible; no unsupported fit claim |

## Optional explanatory captures

- App Lab project tree with `app.yaml`, Python app, pinned model, and sketch.
- Protocol/Bridge diagram displayed beside the two physical boards.
- Dashboard diagnostics during a loss/recovery test.
- Serial `STATUS` with rising frames, valid ACKs, RMS/peak, and zero clipping in test-tone mode; redact SSID/IP if needed.
- Side-by-side minimum BOM and optional/future modules, clearly labeled so future hardware is not implied to be present.
- Accessible cue check from the actual intended viewing angle and room lighting.

## Safety and authenticity

- Do not pose a powered or damaged LiPo on conductive tools or flammable material.
- Do not connect or disconnect loose battery wires for a photograph.
- Do not obscure solder joints before inspection evidence is captured.
- Do not use a siren/smoke alarm at unsafe volume; a controlled household timer or gentle knock is enough.
- Do not photograph people, screens, homes, network names, serial numbers, or audio-related context without consent.
- Do not retouch hardware defects, cue colors, measured displays, event labels, or result values. Cropping, exposure, white balance, redaction, and annotation are allowed if logged and non-misleading.
- The Autodesk concept render under `assets/concepts/` is not a CueLoop V1 physical photo and must not be used as one.

## File naming and edit log

Use `YYYYMMDD_P##_short-description_original.ext` for originals and suffix edited exports with `_web_v01`. Keep a small private edit log with source filename, crop/color/redaction changes, photographer, consent status, and license. Add only publication-safe final exports to the project platform after inspecting metadata; do not commit private originals merely for convenience.
