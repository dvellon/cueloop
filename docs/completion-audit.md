# PROJECT_PROMPT completion audit

**Audit date:** 2026-09-02 EDT

**Method:** each brief requirement is mapped to current repository evidence. “Digitally verified” means an artifact exists and an appropriate test/build/review has run; it never implies physical hardware. “Prepared / physical pending” means the complete procedure/record exists but the required board, measurement, person, interactive desktop, media, or account observation does not.

## Competition, product, and project controls

| Requirement | Evidence | State |
|---|---|---|
| Verify official rules/technical facts and discrepancies from primary sources | `docs/official-requirements.md` with check date/URLs and Autodesk rules-template discrepancy | Digitally verified; recheck before submission |
| Maintain goal, status, plan, decisions, risks, results | active thread goal; `STATUS.md`, `PLAN.md`, `DECISIONS.md`, `RISKS.md`, `HARDWARE_RESULTS.md`, this audit | Digitally verified |
| Safe repository and no secrets/generated/private artifacts | `.gitignore`, package guards/manifests, release tests, Git review | Digitally verified |
| Social-impact but broad user framing; central promise | `docs/product-requirements.md`, V1 article/metadata | Digitally verified |
| Awareness aid, not certified alarm/medical/security/interlock | README, UI, safety/privacy docs, articles, video narration, tests | Digitally verified |
| Distinct V1 and V2 products | `submissions/DIFFERENTIATION.md`, separate application/final workspaces | Digitally verified as scope; final V2 differentiation remains to be physically built |

## V1 uncertainty-aware product

| Required behavior | Evidence | State |
|---|---|---|
| Detached XIAO Sense microphone and room-to-room Wi-Fi | XIAO firmware, Protocol v1, architecture/wiring | Compiles; physical pending |
| UNO Q local edge model and focused vocabulary | pinned YAMNet adapter/manifest/mapping; four retained candidate classes | Digitally verified integration; real-audio/target pending |
| Combine multiple windows and confirm ambiguous events | `engine.py`, evaluator comparison, unit/integration tests, dashboard states | Digitally verified |
| Per-class threshold, importance, priority, cooldown | policies/API/UI/tests | Digitally verified |
| Confirm, dismiss, mute and local feedback | dashboard/API/store/Bridge/tests | Digitally verified; physical control pending |
| Discard raw audio; bounded metadata only | fixed store schema, privacy docs, package/runtime tests | Digitally verified in source/simulation; target filesystem audit pending |
| Meaningful Linux/STM32 split and physical output | Linux receiver/AI/policy/UI plus compact Bridge and deterministic LED3/LED4 sketch | Both paths compile/test digitally; target/LED pending |
| Polished immediately legible local dashboard | accessible responsive HTML/CSS/JS, status/history/config/diagnostics/control UI | Digitally runnable; physical video framing pending |
| One excellent repeatable demo plus confusing background case | `submissions/app_lab/VIDEO_PACKAGE.md`, simulator path, H-100/H-400 | Digital script/fallback complete; physical capture pending |

## CuePod firmware and transport

| Requirement | Evidence | State |
|---|---|---|
| 16 kHz mono PDM microphone capture | `firmware/xiao_cuepod`, official pin/API record | Target compiles; microphone pending |
| Sequence/timestamp packets, packet format, clock | `shared/protocol.md`, Python/C++ encoders/decoders, corruption/round-trip tests | Digitally verified |
| Wi-Fi V1, receiver configuration/pairing | NVS serial commands and explicit receiver IP | Digitally verified in source; physical pending |
| Receiver loss/reconnect | rate-limited CRC ACK, timeout/backoff, restart flags/counters | Digitally tested where simulatable; network pending |
| Battery state when supported | explicit validity flag and fail-safe “unavailable”; manual power mode | Digitally verified; revision/measurement pending |
| Diagnostics and USB/test-tone modes | serial counters, RMS/peak/clipping, `TEST`, `POWER`, `STATUS` | Compiles/tests; physical pending |
| No persistent raw audio/credentials | RAM-only samples, NVS credential path, ignore/package policy | Digitally verified |
| Bandwidth/buffering/loss/reconnect/security/runtime docs | `shared/protocol.md`, `hardware/POWER.md`, architecture/privacy, transport benchmark | Digitally verified calculations/simulation; physical values pending |
| Exact Windows flash/config steps | root `HARDWARE_TESTS.md` W-000 through W-200 | Prepared / physical pending |

## UNO Q Linux, MCU, App Lab, and interface

| Requirement | Evidence | State |
|---|---|---|
| Bounded receive/jitter/ring/window pipeline | `buffering.py`, pipeline and adversarial bounds/restart/loss tests | Digitally verified |
| Normalized real model windows and mapping | YAMNet adapter checksum/tensor/labels/preprocessing tests | Digitally verified on development host |
| Structured events, health/loss/latency/model data | engine/store/pipeline snapshot/API/dashboard | Digitally verified |
| Restart recovery | stream restart, Bridge status/restart resync tests, H-004/H-009 | Digitally verified logic; target pending |
| Supported Bridge/RPC compact MCU commands | `bridge.py`, UNO Q sketch, pinned Router Bridge profile/tests | Compiles/tests; target pending |
| MCU LED patterns, health, acknowledgement, optional safe outputs | cue controller and hardware header; onboard LEDs minimum | Compiles/tests; physical pending |
| Official App Lab folder/descriptor/Python/sketch/profile | `app_lab/CueLoop`, sync/packager/structure tests | Digitally verified; import/Run pending |
| Reproducible dependencies and release | pinned requirements/profile, deterministic App/source ZIPs/manifests/digests | Digitally verified |
| Dashboard required fields | connection, pod/location, event/confidence/time/state/priority, controls/history/loss/latency/privacy/config | Present and integration-tested |

## Simulator, models, experiments, and quantitative evaluation

| Requirement | Evidence | State |
|---|---|---|
| Simulated pod, WAV replay, loss, jitter/latency, reorder/restart | `linux/cueloop/simulator.py`, CLI wrapper/tests | Digitally verified |
| Same simulated/physical processing pipeline | encoded Protocol v1 datagrams into `CueLoopPipeline` | Digitally verified |
| One-command local demo and mock UI data | `scripts/demo.sh` | Digitally verified |
| Model selection/alternatives/benchmark before claim | `models/MODEL_SELECTION.md`, pinned artifact, development-host benchmark | Digitally verified with bounded claim |
| Legally reusable/self-recorded audio policy | provenance schema/gates/docs; audio/datasets ignored | Digitally verified framework; real dataset pending |
| Precision/recall/F1/support/confusion matrices/misses/false alerts | evaluation schema/engine/tests | Digitally verified framework; real data pending |
| Calibration and temporal-versus-single-window benefit | Brier/ECE bins plus confirmation comparison/tests | Digitally verified framework; real data pending |
| Inference and annotated audio-to-decision latency | evaluator and host benchmark | Development-host/synthetic workload only; UNO Q/full physical pending |
| Distance/door/background condition effects | manifest condition slices and H-101–H-108 | Framework prepared; physical/data pending |
| Packet-loss tolerance | deterministic 60-trial benchmark and H-108 | Simulated result complete; target/RF pending |
| Predeclared experiment registry | `experiments/` schema/example/registry | Digitally verified structure |
| Model conversion/preprocessing | official already-converted LiteRT binary is checksum-pinned; adapter implements preprocessing; no unverifiable re-conversion | Digitally verified decision; future custom model requires new pipeline |

## Hardware, safety, BOM, and schematics

| Requirement | Evidence | State |
|---|---|---|
| Exact/minimum/optional/V2 BOMs with MPN/qty/function/source/price | `hardware/BOM.md`, submission BOMs | Digitally complete with received-inventory gates |
| Wiring/pins and deliberate nonconnections | `hardware/WIRING.md`, netlist, schematic/tests | Digitally verified |
| Power/battery/wireless/processor/protocol diagrams | `hardware/DIAGRAMS.md`, `POWER.md`, SVG schematic | Digitally verified |
| Real reproducible schematic plus readable export | JSON netlist + accessible SVG and consistency tests | Digitally verified |
| Assembly, polarity, multimeter, safe first power | `hardware/ASSEMBLY.md`, `docs/safety.md`, `HARDWARE_TESTS.md` | Prepared / physical pending |
| Never solder battery connected/directly; no Qwiic confusion | repeated safety stops and automated doc checks | Digitally verified instruction |
| Windows flashing and all hardware-validation steps/results | root `HARDWARE_TESTS.md`; summary boundary `HARDWARE_RESULTS.md` | Prepared / physical pending |

## Fusion and Autodesk V2

| Requirement | Evidence | State |
|---|---|---|
| Preliminary parametric Fusion Python workflow | `cad/fusion/CueLoopBridgeGenerator.py`, parameter JSON, syntax/envelope tests | Digitally verified; interactive run pending |
| Pod/base/lid/mic path/USB/battery/supports/fasteners | named generated components/bodies and CAD docs | Digitally defined; Fusion/fit pending |
| Receiver/diffuser/buttons/dock/clip/stand/basic assembly | named generated components/bodies | Digitally defined; Fusion/fit pending |
| Realistic preliminary walls/gaps/radii/M2/service | parameter manifest and validation checklist | Digitally defined; measurement/DFM pending |
| Exact `.f3d` save/export and render workflow | `cad/README.md` | Prepared / interactive Fusion pending |
| Application cover | original AI-generated concept with prompt/mode/date/digest disclosure | Digitally complete as concept, not physical evidence |
| September application copy and project opening | complete five responses, biography/URL truth gates, BOM/story/checklist | Digitally complete; identity/account/Fusion export pending |
| December package begun without risking V1 | `submissions/autodesk_final/` plan, manufacturing, evidence, article, checklist | Digitally complete structure; V2 build pending |
| New hardware/interactions/CAD/manufacturing/testing/workflow tracked | Autodesk final artifact map/evidence matrix and differentiation ledger | Digitally prepared; physical execution pending |

## Competition submission materials

| Requirement | Evidence | State |
|---|---|---|
| V1 title/subtitle/cover plan/article/user stories/architecture/AI/App Lab/split | `submissions/app_lab/SUBMISSION_METADATA.md`, `PROJECT_ARTICLE.md` | Digitally complete |
| BOM/schematic/build/setup/use/troubleshooting/privacy/limits/results/source/reuse | article, source guide, troubleshooting, test results, hardware docs | Digitally complete with physical slots only |
| Photo list, three-minute storyboard, short/long narration, on-screen text | photo/video package | Digitally complete; original capture pending |
| Final checklist and judging-rubric optimization | checklist plus 30/20/15/15/20 adversarial review | Digitally complete |
| Deterministic packages/archives and clean extraction | App/source packagers, manifests, release tests and prior clean-extraction run | Digitally verified; regenerate after this audit checkpoint |
| Prioritized remaining user actions | `user_checklists/NEXT_ACTIONS.md`, root hardware test gates | Digitally complete |

## Definition-of-done audit verdict

Every brief item that can be executed without physical boards, interactive Fusion, original photography/video, real licensed/self-recorded evaluation audio, entrant identity, or competition-account access now has an implementation or an explicit evidence-backed nonconversion/optional-hardware decision. At this audit checkpoint, 57 automated tests pass, Pyright reports zero errors/warnings, both canonical firmware targets compile on the pinned cores, the isolated App sketch reproduces the canonical UNO Q binaries, and all recorded binary hashes remain unchanged. Deterministic archives and their clean extraction are regenerated from the exact commit after this audit is committed.

The long-running product goal remains active because hardware/app/media/account claims are explicitly required for the final competitions. Their complete executable steps and record location are in `HARDWARE_TESTS.md`; no pending row is treated as a pass.
