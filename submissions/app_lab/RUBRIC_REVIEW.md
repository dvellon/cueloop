# App Lab competition rubric review

**Contest rubric:** documentation 30, BOM 20, schematics 15, code and contribution 15, creativity 20.

**Review posture:** adversarial preflight. A prepared file is not proof that a judge can see it; every link and attachment must also be checked from a logged-out browser.

## 1. Documentation — 30 points

### Evidence already prepared

- `PROJECT_ARTICLE.md` begins with a human problem, states the social-impact use case, explains the uncertainty interaction, makes UNO Q’s dual processors essential, and supplies end-to-end build/config/use instructions.
- `VIDEO_PACKAGE.md` prioritizes a physical observe → confirm → cue → acknowledge run and includes exact narration, shot timing, captions, safety, privacy, and fallback language.
- `SOURCE_GUIDE.md` maps reviewer roles to implementation and tests; `TROUBLESHOOTING.md` handles likely setup and fault cases.
- Root `HARDWARE_TESTS.md` contains the authoritative Windows/safety/validation workflow and execution record; the three `user_checklists/` views keep operator steps short.
- Limitations are repeated where a reader might otherwise infer a certified alarm, a real-audio result, encrypted transport, or existing hardware validation.

### Remaining score risks

- The article lacks real photos, a working App Lab screenshot, and measured physical results until hardware arrives.
- A long article can bury the actual build. Hackster formatting must retain short paragraphs, headings, tables, code blocks, and inline images at the relevant steps.
- If the video shows only a successful alert, the uncertainty concept is not demonstrated; include one controlled non-alert/ambiguous trial.
- The submitted project must be fully public/accessible to judges; a private repository link alone is insufficient.

### Final acceptance

- Original hero plus at least one image for assembly, App Lab, real event, schematic, and results.
- Video viewed end-to-end with captions and no unsupported narration.
- Fresh reader can reproduce software and wiring without private context.
- All claims agree across article, video, result table, repository, and firmware manifest.

## 2. Bill of materials — 20 points

### Evidence already prepared

- `hardware/BOM.md` separates minimum V1, exact received-item gates, optional outputs, tooling, consumables, and materially different V2 parts.
- Manufacturer, product identity, quantity, function, price, region/date caveats, and unknown order accessories are explicit.
- `PROJECT_ARTICLE.md` gives a concise minimum BOM and honest mixed-currency subtotal.
- The minimum demo deliberately uses onboard UNO Q LEDs, preventing an undocumented actuator from becoming a hidden requirement.

### Remaining score risks

- Exact Arduino-order USB-C power/data accessory and invoice price are unknown until inventory is checked.
- Received part markings/revisions and actual quantities have not been photographed.
- Shipping, regional tax, reused router/computer, soldering tools, and consumables must not be confused with core product subtotal.

### Final acceptance

- Reconcile every published BOM row to a physical item or label it optional/not used.
- Replace only fields supported by receipt/packing-list evidence; preserve price date and currency.
- Show a labeled overhead image matching the minimum BOM.

## 3. Schematics — 15 points

### Evidence already prepared

- `hardware/schematics/cueloop_v1.netlist.json` is editable, machine-readable connectivity source.
- `hardware/schematics/cueloop_v1.svg` is an accessible, human-readable schematic with signal/power boundaries, connector/pad polarity, optional button, and deliberate non-connections.
- `hardware/WIRING.md`, `POWER.md`, `ASSEMBLY.md`, and `DIAGRAMS.md` explain pin ownership, two power domains, battery procedure, protocol, bandwidth, and runtime estimates.
- Automated tests reject unsafe netlist connections, ambiguous battery nets, or a mismatch between the SVG metadata and netlist.

### Remaining score risks

- A conceptual/network diagram alone would not earn schematic credit; attach the actual SVG schematic prominently.
- XIAO battery-pad orientation and received pigtail polarity still require physical verification.
- Optional features must not appear connected if they were not actually built.

### Final acceptance

- Verify SVG readability at Hackster’s displayed size and offer the source file as a resource.
- Add a real wiring photo with pad/pin annotations after assembly inspection.
- Ensure the physical build matches the published schematic; revise both if it does not.

## 4. Code and contribution — 15 points

### Evidence already prepared

- A working simulator-first vertical slice covers packet generation, strict protocol, bounded buffering, classifier interface, uncertainty policy, privacy schema, REST API, dashboard, and fault injection.
- XIAO and UNO Q firmware compile on pinned platforms; the isolated App Lab sketch produces matching deployable binary hashes.
- The App Lab folder is self-contained, dependencies are pinned, real-model startup fails closed, and a deterministic package manifest/digest supports audit.
- The complete Python 3.13/Linux ARM64 inference distribution set is exact-version/hash locked and audited for archive integrity, metadata, and native AArch64 ELF identity; the target log emits its actual runtime identity.
- The model adapter verifies artifact checksum, tensor contract, and embedded labels. Evaluation refuses incomplete provenance.
- Automated tests cover malformed data, loss/reordering/restarts, storage boundaries, Bridge faults, model mapping, packaging, and hardware document consistency.
- MIT licensing, contribution rules, and the source guide make reuse practical.

### Remaining score risks

- Target dependency resolution, dynamic native loading/model inference, and App Lab Router Bridge behavior remain unobserved; the Ubuntu package audit must not be presented as an UNO Q run.
- The private development repository cannot serve as a durable public contribution unless a judge-accessible release/archive is attached.
- The automated fresh local checkout now reproduces tests, static analysis, firmware, model/package gates, and release creation; an independent reader/judge has not yet repeated it on a different machine.

### Final acceptance

- Import/run the packaged App on physical UNO Q and flash/configure XIAO from documented Windows steps.
- Attach the clean source ZIP plus App Lab ZIP; verify SHA-256 and extraction from a second directory.
- Publish a stable judge-accessible source URL or platform attachments and test them logged out.
- Run the final suite/builds at the release commit and record exact outputs.

## 5. Creativity — 20 points

### Evidence already prepared

- CueLoop treats uncertainty as a visible interaction state instead of displaying a one-window label as fact.
- A detachable room pod separates the sound source from the user without depending on a cloud account or permanent installation.
- UNO Q’s Linux/MCU split is meaningful: AI/data/UI on Linux; deterministic physical cue and health state on the MCU.
- The protocol carries CRC-checked volatile evidence and an ACK heartbeat; raw audio is excluded from database and Bridge contracts.
- The architecture generalizes to other local sensing/model adapters while the V1 vocabulary stays intentionally small.
- The accessibility origin is balanced with honest safety, privacy, security, and calibration limits.

### Remaining score risks

- The core concept will feel theoretical until the video shows the physical two-room moment clearly.
- A generic dashboard-only demo would obscure the interaction innovation and dual-processor design.
- Overstating AI accuracy would weaken the responsible-design argument.

### Final acceptance

- Open and close the video on the real human moment: sound in one space, discreet understandable cue in another.
- Visibly show observing/confirming and at least one ambiguous/non-alert outcome.
- Show the onboard physical cue and local dashboard together, with UNO Q identifiable.

## Cross-cutting disqualifier/credibility review

- Entry is in English, original, and not claimed as a previous Hackster winner.
- UNO Q is necessary and visible; real-world AI runs locally on its Linux side in the intended build.
- Title, short description, cover, BOM, full instructions, images, source, schematic, and video are all mapped to a final checklist.
- Every third-party model/library/media asset is permitted and attributed; no copyrighted/private audio is uploaded.
- CueLoop V1 remains distinct from the Autodesk CueLoop Bridge V2 entry in name, product story, interaction, hardware, enclosure, and evidence.
- No physical or accuracy claim is inferred from simulation, compilation, a datasheet, or a development-host benchmark.

## Current readiness verdict

The digital submission package is structurally strong across all five criteria. The largest remaining risks are necessarily physical: no received inventory, App Lab target run, real microphone/network/Bridge behavior, real-audio evaluation, physical photos, or video exists yet. A truthful final entry should prioritize one robust two-room physical workflow, measured evidence for only the classes that pass, and clear failure disclosure over adding features.
