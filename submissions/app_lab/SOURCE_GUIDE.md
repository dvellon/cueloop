# CueLoop source and reproduction guide

This map is written for a reviewer or contributor starting from a clean checkout. The authoritative runtime code lives once under `linux/cueloop`; `scripts/sync_app_lab.py` copies a controlled subset byte-for-byte into the self-contained App Lab folder and tests reject drift.

## Start here by role

| Goal | Entry point | Supporting contract/tests |
|---|---|---|
| See the system locally | `./scripts/demo.sh` | `linux/cueloop/simulator.py`, dashboard under `linux/cueloop/dashboard/` |
| Run all standard-library tests | `./scripts/test.sh` | `tests/` |
| Understand UDP bytes | `shared/protocol.md` | `linux/cueloop/protocol.py`, `shared/cueloop_protocol.h`, `tests/test_protocol.py` |
| Flash the CuePod | `firmware/xiao_cuepod/xiao_cuepod.ino` | local hardware/protocol headers and firmware README |
| Understand inference/policy | `linux/cueloop/yamnet.py`, `engine.py` | class mapping, model/evaluation tests |
| Deploy UNO Q App | `app_lab/CueLoop/python/main.py` | `app.yaml`, pinned `sketch/sketch.yaml`, App README |
| Understand physical cues | `firmware/uno_q_cue_controller/uno_q_cue_controller.ino` | `linux/cueloop/bridge.py`, Bridge tests |
| Reproduce the model | `scripts/fetch_yamnet.py` | `models/model_manifest.json`, `requirements-model.txt` |
| Audit UNO Q Python distributions | `scripts/audit_unoq_runtime.py` | target hash lock, runtime manifest, ELF/metadata tests |
| Evaluate licensed audio | `models/evaluate.py` | manifest/schema, `linux/cueloop/evaluation.py` |
| Build a release ZIP | `scripts/package_app_lab.py` | package tests and generated internal manifest |
| Build a source release | `scripts/package_source_release.py` | committed-tree manifest, privacy guards, deterministic ZIP |
| Verify a fresh checkout | `scripts/verify_clean_checkout.sh` | tests, Pyright, deterministic firmware, model gate, both release types |
| Build safely | `user_checklists/HARDWARE_BRINGUP.md` | `hardware/`, `docs/safety.md`, physical matrix |
| Generate authoritative CAD | `cad/fusion/CueLoopBridgeGenerator.py` | native Fusion contract/runbook; independent OpenCascade reference and host validator |

## Runtime modules

| Module | Responsibility | Boundary |
|---|---|---|
| `constants.py` | sample/frame/window dimensions and vocabulary | no board-specific state |
| `protocol.py` | strict encode/decode, flags, CRC, receiver ACK | rejects unknown flags and malformed lengths |
| `buffering.py` | bounded packet reorder/gap representation and overlapping windows | huge jumps do bounded work |
| `model.py` | classifier protocol and deterministic synthetic signatures | simulated outputs always labeled simulated |
| `yamnet.py` | checksum/tensor/embedded-label validation and LiteRT inference | optional third-party import; no fallback |
| `engine.py` | observe/confirm/alert/cooldown/mute policy | at least two qualifying windows |
| `storage.py` | bounded SQLite event/feedback records | fixed metadata schema; no audio column |
| `pipeline.py` | decode → buffer → model → policy → store/output orchestration | shares one path for simulated/physical packets |
| `bridge.py` | bounded compact Arduino Router Bridge calls and MCU status | exceptions become diagnostics, not receiver crashes |
| `api.py` | local REST/static dashboard server | trusted-LAN/localhost only; no authentication in V1 |
| `service.py` | CLI, UDP receive/ACK, HTTP lifecycle | real YAMNet selected explicitly |
| `simulator.py` | signatures/WAV replay and loss/jitter/reorder/restart injection | WAV provenance remains operator responsibility |
| `evaluation.py` | manifest gate and dataset-scoped metrics | refuses missing license/consent/checksum |

## Exact packet and event boundaries

The 684-byte audio datagram and 24-byte heartbeat are documented byte-for-byte in `shared/protocol.md`. Python is the host reference encoder/decoder; the XIAO manually builds network-order headers and little-endian PCM with the same CRC algorithm. The event database accepts only the fields in `shared/event.schema.json`/`EVENT_COLUMNS`. That explicit schema is the privacy control: an audio blob cannot be accidentally added as an extra dictionary key.

## App Lab synchronization

Run:

```bash
python3 scripts/sync_app_lab.py --include-model
python3 scripts/sync_app_lab.py --check --include-model
```

The first operation copies approved core files, dashboard assets, UNO Q sketch/header, mapping, model/runtime manifests, target dependency lock, and the ignored verified model. The second compares bytes and checksum without writing. Tests run the no-model drift check so clean clones remain testable.

`scripts/package_app_lab.py` repeats the model/source gate, refuses a release archive when any packaging input differs from `HEAD`, excludes build/cache/database/audio/secret-like files, writes an empty `data/` directory, adds a per-file `PACKAGE_MANIFEST.json` with the exact source commit and clean-tree result, fixes ZIP timestamps/permissions for deterministic output, and produces a SHA-256 sidecar. The release archive and model remain ignored. `--allow-dirty` exists only for development tests; never use it for a submission archive.

`scripts/package_source_release.py` packages blobs from exact committed `HEAD`, not arbitrary working-copy bytes. It omits the internal `PROJECT_PROMPT.md`, rejects credential/audio/model/database/build artifact paths, adds the commit plus per-file SHA-256 values to `SOURCE_MANIFEST.json`, and writes an ignored digest sidecar. It refuses a dirty tracked worktree by default; `--allow-dirty` exists for automated testing and still packages committed `HEAD` only.

## Reproducible dependency boundary

- Desktop simulator/service: Python 3.11+ standard library.
- Model path: the complete `ai-edge-litert==2.2.0` dependency set is pinned. `models/requirements-unoq-cp313.lock` and `unoq_runtime_manifest.json` hash-audit the documented CPython 3.13/Linux ARM64 distributions; actual App Lab resolution/import/inference remains a target record.
- XIAO: Arduino CLI 1.5.1, `esp32:esp32` 3.3.11, core libraries only.
- UNO Q: `arduino:zephyr` 0.90.0 plus every library/version in App Lab `sketch.yaml`.
- Downloaded YAMNet: exact URL, byte count, SHA-256, input/output contract, license, and limitations in `models/model_manifest.json`.

## Test organization

- `test_protocol.py`: round trip and corruption rejection for audio/ACK.
- `test_buffering.py`: reorder, loss fill, wraparound, restart, huge jump, bounds.
- `test_model_engine_storage.py`: synthetic mapping, temporal policy, cooldown/mute, storage privacy.
- `test_pipeline_api.py`: end-to-end simulated packets, malformed input, REST controls/dashboard.
- `test_bridge.py`: exact RPC translation, failure containment, status/restart logic.
- `test_yamnet_mapping.py` and `test_evaluation.py`: mapping labels/aggregation and provenance gates/metrics.
- `test_app_lab_package.py`: mandatory structure, pinned dependencies, source/model/archive integrity.
- `test_unoq_runtime_audit.py`: target lock/manifest/App-copy integrity and downloaded wheel metadata/hash/AArch64 ELF audit.
- `test_hardware_docs.py`: safe net connectivity and valid accessible schematic source.
- `test_cad_application.py`: native Fusion API/export/provenance contract, critical clearances, OpenCascade STEP/STL output integrity/interference, and Autodesk answer/evidence gates.
- `test_simulated_transport_benchmark.py`: deterministic clean/moderate/severe fault profiles and software-only claim boundary.
- `test_project_completion_docs.py`: canonical hardware workflow, V2 final structure, and experiment registry contract.
- `test_submission_release.py`: required publication assets, video evidence labels, and deterministic sanitized source release.
- `test_reproducibility.py`: fixed-time/path-normalized firmware builder, minimum-Python static-analysis target, and fresh-checkout release surface.

Compilation results are not tests of attached hardware. Physical observations enter through root `HARDWARE_TESTS.md`; only reviewed summaries enter `HARDWARE_RESULTS.md` and submission copy.

## Safe contribution rules

1. Run `./scripts/test.sh`, Pyright, and `./scripts/build_firmware.sh` in proportion to the changed surface; use `./scripts/verify_clean_checkout.sh` at release checkpoints.
2. Sync the App Lab vendor tree after changing an approved core or UNO Q sketch file.
3. Do not relax the model checksum, evidence-tier labeling, minimum temporal evidence, raw-audio boundary, or safety language merely to make a demo pass.
4. Add/modify packet fields only with a versioned shared protocol change and cross-language tests.
5. Store credentials in XIAO NVS through serial or ignored local configuration—not source.
6. Keep recordings, model weights, build products, databases, caches, and archives ignored.
7. Cite licenses/provenance for any reusable model, audio, code, UI, image, font, or video asset.
8. Report failed physical targets honestly and narrow the supported vocabulary when evidence demands it.
