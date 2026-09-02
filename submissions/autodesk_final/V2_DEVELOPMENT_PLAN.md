# CueLoop Bridge V2 development plan

**Final deadline:** December 20, 2026 at 11:59 PM PST (December 21 at 2:59 AM EST), subject to official recheck.

**Product:** a portable, serviceable UNO Q receiver with a dockable CuePod for Autodesk creators moving between acoustically separated work areas.

## V2 definition

CueLoop Bridge is not CueLoop V1 in another shell. It must add:

1. a portable receiver power/thermal architecture compatible with actual UNO Q requirements;
2. a deliberate dock/retention/charging-or-transport relationship for the detached pod;
3. a tactile, non-color-only visual/haptic cue language usable while clipped, carried, or on a stand;
4. measured acoustic, attachment, carry, service, thermal, runtime, and recovery behavior;
5. a native measured Fusion assembly, Fusion Electronics work where justified, and PCBWay-ready manufacturing outputs;
6. a real Autodesk-user workflow, such as monitoring a printer/test rig/process from another work area;
7. new physical media, testing, and story rather than recycling the V1 submission.

## Workstreams and decision gates

### A. Inventory and measured requirements

- Record exact UNO Q/XIAO/accessory revisions, connector envelopes, mount coordinates, antenna/microphone/thermal keepouts, and actual cable bend volumes.
- Measure parts through `cad/DIMENSION_VALIDATION.md`; update `cad/design_parameters.json` with source/evidence for each changed value.
- Interview or run a structured task walkthrough with at least one intended Autodesk/maker user: where receiver is worn/placed, gloves/hearing protection, cue comprehension, acknowledgement, and service needs.
- Freeze no optional module until voltage, peak/current drive, mechanical envelope, library compatibility, and accessibility benefit are known.

**Gate A:** all critical product envelopes and primary workflow needs are observed; unknowns remain explicit.

### B. Portable electrical/product architecture

- Select an approved UNO Q portable power solution only from measured load and official input rules; document protection, charging, power-path, connector, indicator, capacity, transport, and service implications.
- Select a protected haptic driver/motor and visual diffuser/light source; external actuators never connect directly to GPIO.
- Decide whether a carrier PCB materially improves assembly, safety, testability, or size. If not, document why and retain a serviceable harness.
- Create versioned power tree, signal netlist, pin budget, worst-case current, thermal budget, and battery/runtime targets.
- Preserve Linux/STM32 ownership: AI/network/history/UI on Linux; deterministic cues/input/health on MCU.

**Gate B:** schematic/ERC/manual safety review and benchtop subsystem measurements pass before enclosure power integration.

### C. Interaction prototype

- Prototype at least three event-family patterns and three priority levels using rhythm/shape in addition to hue.
- Test acknowledge, mute, class/location selection, health fault, low-power state, pod absent, and uncertain/confirming state without requiring a phone.
- Evaluate clip, lanyard, stand, pocket, and bag contexts; choose only the modes that remain stable and understandable.
- Retain local dashboard for explanation/configuration while making the portable physical interaction complete enough for the primary workflow.

**Gate C:** an intended user/evaluator distinguishes critical patterns and completes acknowledge/mute tasks under recorded conditions.

### D. Fusion mechanical and electronics package

- Replace manufacturer/estimated envelopes with linked measured components and named parameter provenance.
- Model CuePod base/lid, acoustic labyrinth, antenna keepout, battery restraint, USB/service access, dock features, fastening, and strain relief.
- Model receiver base/lid, UNO Q supports/connector/thermal access, light diffuser, haptic mounting/isolation, controls, clip/stand/lanyard, pod dock, portable power, fasteners, and service order.
- Add joints, interference checks, sections, exploded assembly, drawings, critical dimensions/tolerances, material/finish notes, and mass/center-of-gravity estimate.
- Add Fusion Electronics schematic/PCB/carrier and ECAD–MCAD association only if Gate B justifies it.
- Export versioned native `.f3d`, STEP/3MF/manufacturing files, drawings, and renders after inspection; generated exports remain ignored until curated for submission.

**Gate D:** no critical interference, cell compression, blocked acoustic/antenna/thermal path, unsupported actuator, or unserviceable fastener order remains.

### E. PCBWay prototype and DFM

- Use `MANUFACTURING_PLAN.md` to select process/material from load, finish, tolerance, diffuser, acoustic, thermal, and cost evidence.
- Print a tolerance/fastener/text/diffuser/acoustic coupon before freezing mating gaps.
- Submit only reviewed manufacturing files; retain quote, revision, process/material/finish, orientation/support, and feedback.
- Inspect received parts dimensionally and visually before assembly. Feed every deviation back into Fusion parameters and drawings.

**Gate E:** enclosure passes fit/service/carry and no-safety-defect inspection; revisions are traceable.

### F. Integrated validation and final story

- Repeat applicable V1 protocol/model/privacy/recovery tests on V2 hardware.
- Add dock retention/cycles, clip/stand/lanyard load and usability, controlled drop, actuator current/temperature, portable runtime, charging, acoustic-port comparison, carry/pack, and Autodesk-workflow trials.
- Demonstrate uncertainty, a successful creator workflow, a confusable/background case, fault recovery, and local/no-recording behavior.
- Complete `EVIDENCE_MATRIX.md`, publish failures/limits, capture new V2 photos/video, and audit differentiation.

**Gate F:** every final claim maps to an observed record, native design/source, or explicit estimate; no V1 image/result is presented as a V2 physical result.

## Schedule and decision cadence

| Period | Outcome |
|---|---|
| Sep 1–7 | application package, preliminary generator/render, public project start, `.f3d` export |
| Sep 8–13 | protect/finish V1; inventory and measured V2 requirements only |
| Sep 14–30 | portable power/output architecture, interaction breadboard, measured CAD rev A |
| Oct 1–18 | schematic/carrier decision, Fusion assembly rev B, tolerance coupons, design review |
| Oct 19–Nov 8 | PCBWay prototype order/feedback, firmware interaction extensions, test fixtures |
| Nov 9–29 | enclosure rev C, integrated V2 assembly, reliability/usability/workflow testing |
| Nov 30–Dec 10 | final native Fusion/electronics/drawings/BOM/schematics, new article/media capture |
| Dec 11–17 | rubric audit, logged-out reproduction/link/license review, release candidate |
| Dec 18–19 | correction buffer and early submission; do not plan first submission for deadline day |

Physical delivery and organizer feedback may change dates. Preserve a usable serviceable prototype and honest documentation over expanding features late.
