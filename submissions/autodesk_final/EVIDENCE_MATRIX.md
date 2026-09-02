# CueLoop Bridge V2 evidence matrix

This matrix prevents preliminary V1/shared work from silently becoming a V2 product claim. Add result IDs/links only after the named setup is observed.

| Claim / final story element | Minimum evidence | Current status |
|---|---|---|
| Product is portable/carryable | complete powered assembly mass/dimensions, runtime, connector/cable behavior, carry/pack trial | Pending V2 hardware |
| Clip/stand/lanyard is purposeful | measured load/stability, repeated use, intended material/process, user task result | Pending design/physical |
| CuePod docks securely | retention geometry, cycle/load/drop test, removal ergonomics, no connector/cell damage | Pending design/physical |
| Dock charges CuePod | verified power-path schematic, protected hardware, current/thermal/charge measurements | Not selected or implemented |
| Visual/haptic language is understandable | exact patterns and at least one consented intended-user/structured evaluation | Pending interaction hardware |
| Non-color-only accessibility | cadence/shape/haptic distinctions demonstrated under realistic viewing/carry modes | Pending physical |
| Local AI works on UNO Q | pinned runtime/model on identified target, licensed clips, target latency/memory | Pending UNO Q |
| Event recognition is useful | provenance-complete held-out per-class metrics and defined hard negatives | Pending audio dataset/target |
| Uncertainty reduces false interruption | identical held-out inputs compared single-window vs temporal policy | Framework complete; real data pending |
| No raw audio retained by default | source/schema review plus before/after target App filesystem/database audit | Digital tests pass; target audit pending |
| Private/local-first | no cloud endpoint, trusted-LAN limitation, observed offline/local run, consent/control story | Digital boundary documented; physical run pending |
| Battery/runtime is adequate | exact power architecture, safe charge/discharge observation and runtime distribution | Pending V2 selection/physical |
| Thermal behavior is acceptable | repeatable ambient/surface/component method across workload/power/enclosure | Pending physical |
| Acoustic path helps/protects | A/B measurement of open board versus enclosure revisions across relevant sounds | Pending CAD/physical |
| RF path remains usable | packet loss/RSSI/recovery across carry/dock/enclosure orientations and workflow | Pending physical |
| Enclosure is serviceable | timed assembly/disassembly, tool/fastener count, cable/cell/board access and damage check | Pending manufactured part |
| Fusion is source of truth | native parameterized `.f3d`, measured parameters, timeline/components, interference/drawings/revisions, source hashes | Native generator and independent reference validation complete; Windows Fusion C-100 execution/review pending |
| Fusion Electronics adds value | linked carrier schematic/PCB/MCAD and physical carrier, or documented no-carrier decision | Pending Gate B |
| PCBWay process is appropriate | coupon, supplier feedback, released files/quote, received-part inspection and revisions | Pending selection/order |
| Approximately-750-unit path is credible | assembly/EOL process, quote/economics/yield/component lifecycle review | Planning only |
| Autodesk creator workflow matters | observed printer/CNC/test/process workflow, baseline pain, task outcome/user feedback | Pending user/workflow test |
| V2 is materially different from V1 | new hardware, interaction, CAD, manufacturing, tests, workflow, photos/video, final audit | Planned; not yet proven |

## Required evidence metadata

Every quantitative record includes date/timezone, commit/design revision, operator, exact hardware/process/software identities, power/network/environment, source/provenance/consent, sample count/duration, method/instrument/resolution, units/distribution, evidence tier, pass/fail against a predeclared target, artifact path, and limitations.

## Publication rules

- Simulation validates software behavior only; it is never physical product or model-quality evidence.
- A Fusion render proves design intent, not fit, manufacture, portability, thermal behavior, or safety.
- A datasheet value remains estimated until the actual integrated configuration is measured.
- One successful demo is not a rate, accuracy, reliability, or accessibility study.
- Negative results remain in the development story and drive scope reduction or revision.
- V1 measurements can be cited as shared baseline only with their exact configuration; they cannot prove V2 enclosure/output/power behavior.
