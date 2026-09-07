# CueLoop licenses and attribution

This is the publication ledger for source, models, libraries, media, and reference facts. Recheck the license shipped with every resolved package/artifact at release time; a name in this file does not override upstream terms.

## Project-authored material

CueLoop source code, written documentation, protocol, schemas, tests, dashboard, schematic source/export, and original design source in the repository are Copyright © 2026 CueLoop contributors and licensed under the repository MIT License unless a file says otherwise.

The final project photographs, narration, diagrams derived solely from repository source, and video should be original project material. Record photographer/narrator/editor and consent in the private media log, then state the chosen publication license on the Hackster project.

## Model and runtime

| Component | Role | Upstream / license record | Distribution treatment |
|---|---|---|---|
| Google YAMNet classification LiteRT v1 | 521-class acoustic baseline | Google/TensorFlow Models; Apache License 2.0; exact upstream/download links and digest in `models/model_manifest.json` | Binary is ignored in source Git; verified copy is included only in the runtime App archive with manifest/attribution |
| AudioSet ontology/class names | upstream label vocabulary | Google AudioSet; referenced through YAMNet artifact/source | small reviewed mapping is project source; retain upstream attribution |
| `ai-edge-litert==2.2.0` | target/host LiteRT Python runtime | Google; PyPI wheel metadata audited as Apache 2.0 and recorded with URL/digest in `models/unoq_runtime_manifest.json`; recheck installed metadata on target | dependency pin only; package itself is installed by the target environment, not vendored |

YAMNet is not presented as a model trained by CueLoop. Its AudioSet/YouTube-derived limitations, target mapping, checksum, tensors, and unmeasured real-audio quality remain explicit in the article and manifest.

## Arduino and board dependencies

| Component | Pinned version/use | Treatment |
|---|---|---|
| Arduino ESP32 platform | `esp32:esp32` 3.3.11 | build dependency; not vendored; retain upstream component notices |
| Arduino Zephyr platform | `arduino:zephyr` 0.90.0 | build dependency; not vendored; retain upstream component notices |
| Arduino Router Bridge | `Arduino_RouterBridge` 0.4.3 in App sketch profile | installed from pinned profile; do not relicense upstream library |
| Arduino App Lab/App CLI | packaging and deployment environment | not distributed in the source archive; refer to Arduino’s official terms/docs |
| Arduino/Seeed core libraries | Wi-Fi/TCP, I2S, NVS, board APIs | provided by pinned cores; not copied as project-authored code |

The compiled firmware and App archive can contain linked or bundled third-party components. Before public binary distribution, retain their generated notices/licenses and verify that the packaging path satisfies each license.

## Technical facts and trademarks

Arduino, Arduino UNO Q, App Lab, Seeed Studio, XIAO, ESP32, Google, YAMNet, TensorFlow, LiteRT, Hackster, Autodesk, Fusion, Adafruit, and other product names are identifiers/trademarks of their respective owners. Their use describes compatibility or sourced components and does not imply endorsement.

Primary URLs for contest, product, App format, Bridge, and microphone facts are recorded with the check date in `docs/official-requirements.md`. BOM source URLs and price-check dates are in `hardware/BOM.md`. Do not copy manufacturer photographs or long passages into the entry merely because the product is purchased; use original photographs and concise attributed facts.

## Audio and evaluation data

No third-party or private audio is committed or included in release archives. Every evaluation clip must have source, owner/license or permission, consent status where voices may be identifiable, checksum, environment, distance, label, and split recorded in the local provenance manifest. Redistribution permission must be evaluated separately from permission to run local evaluation.

For the final demonstration, the safest sound sources are project-created non-identifying room sounds such as a gentle knock or owned timer, recorded with consent. Do not add commercial music, broadcast audio, assistant voices, stock effects, or alarm sounds without a documented compatible license.

## Media release checklist

- [ ] Photographer, videographer, narrator, editor, and on-camera participant permission recorded.
- [ ] Every visible person and private location has consent; sensitive screens, IPs, SSIDs, serials, mail, and reflections inspected.
- [ ] Music is omitted or original/licensed with title, creator, source, license, and proof recorded.
- [ ] Fonts, icons, overlays, stock assets, and sound effects are original, platform-provided under compatible terms, or individually logged.
- [ ] Final cover and real-device photos are not AI-generated or represented as unedited evidence if materially composited.
- [ ] Captions/transcript are project-authored and technical names are corrected.
- [ ] YouTube/Vimeo/Hackster upload settings do not apply an unintended incompatible license.

## AI-generated concept asset outside V1 evidence

`assets/concepts/cueloop-bridge-cover-concept-v1.png` is an AI-generated industrial-design concept for the materially distinct Autodesk V2 application. Its repository README records generation date, tool mode, prompt summary, and digest. It must remain labeled as a concept and must not be used as CueLoop V1 physical, manufacturing, or test evidence.
