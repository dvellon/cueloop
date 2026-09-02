# CueLoop experiment registry

Use this directory for predeclared methods and curated, nonprivate summaries. Machine output belongs under ignored `experiments/results/`; audio belongs under ignored private data paths. Hardware observations are executed and logged in root `HARDWARE_TESTS.md`, then summarized in `HARDWARE_RESULTS.md`.

## Experiment lifecycle

1. Copy `experiment.example.json`, assign a stable `EXP-###` ID, and state the question before collecting data.
2. Declare independent/dependent variables, controls, sample/repetition plan, acceptance target, evidence tier, safety/privacy constraints, and artifact paths.
3. Freeze calibration/validation/test boundaries before evaluating a model; preserve seed/source groupings.
4. Run without changing the target after seeing results. Record deviations explicitly.
5. Keep raw/private/generated artifacts ignored. Commit only a curated summary with method, counts, units/distribution, commit, limitations, and the manifest/result digest.
6. A failure remains a result. A simulated run never closes a physical experiment.

## Planned registry

| ID | Question | Evidence tier required | Execution record | Status |
|---|---|---|---|---|
| EXP-001 | How does packet loss/jitter/reordering affect the complete software path? | simulated | `benchmarks/simulated-transport-2026-09-02.md` | Complete; software-only |
| EXP-101 | Which V1 classes meet held-out precision/recall/false-trigger targets? | licensed/self-recorded development-host then UNO Q | H-200 in `HARDWARE_TESTS.md` | Pending data/target |
| EXP-102 | What benefit/cost does temporal confirmation have versus one-window decisions? | same held-out records/policies | evaluator comparison + H-200 | Framework complete; data pending |
| EXP-103 | What is physical acoustic-to-cue latency? | physical CuePod + UNO Q | H-302 | Pending hardware |
| EXP-104 | How do distance, door, background, and LAN path change quality? | physical CuePod + UNO Q | H-101–H-108 | Pending hardware |
| EXP-105 | What are CuePod runtime, charge, and thermal behaviors? | physical CuePod | H-307–H-310 | Pending hardware |
| EXP-201 | Does the V2 acoustic labyrinth improve robustness without harmful attenuation? | physical V2 revisions | Autodesk `EVIDENCE_MATRIX.md` | Pending CAD/hardware |
| EXP-202 | Which portable cue/attachment design is understood and comfortable? | consented physical V2 evaluation | Autodesk `EVIDENCE_MATRIX.md` | Pending interaction hardware |

Do not create experiments merely to inflate a test count; every experiment must change a real product decision or substantiate a bounded claim.
