# CueLoop

**Know what needs your attention without continuously listening, recording, or remaining in the same room.**

CueLoop is a private, local-first acoustic event bridge. A detachable Seeed Studio XIAO ESP32S3 Sense pod sends live microphone evidence over the local network to an Arduino UNO Q. The UNO Q performs edge inference, combines confidence across time, asks for more evidence when a result is ambiguous, and emits an accessible cue through its deterministic MCU and a local dashboard. Raw audio is discarded by default after inference.

This repository develops two related, deliberately distinct products:

- **CueLoop V1** — a reproducible social-impact prototype for the 2026 *Invent the Future with Arduino UNO Q and App Lab* competition.
- **CueLoop Bridge V2** — a portable, serviceable multi-space tool for Autodesk users, developed for *Build the Autodesk University 2027 Product*.

CueLoop is an awareness aid. It is not a safety-certified alarm, security system, or medical device, and it must not replace required alarms or supervision.

## Current state

Development began on September 1, 2026. Hardware-dependent results are intentionally separated from simulator and development-computer results. See [STATUS.md](STATUS.md), [PLAN.md](PLAN.md), [HARDWARE_TESTS.md](HARDWARE_TESTS.md), and [HARDWARE_RESULTS.md](HARDWARE_RESULTS.md) for the live record.

Both firmware targets and the exact isolated App Lab sketch profile compile on the documented Ubuntu toolchain. The complete App Lab import archive can be generated locally with `python3 scripts/package_app_lab.py`; no claim is made that it has run on physical boards yet.

## Quick start

The simulator-first path runs without boards or third-party Python packages:

```bash
./scripts/demo.sh
```

The command starts a simulated CuePod, UDP receiver, bounded jitter/window buffer, uncertainty-aware event engine, metadata-only store, API, and accessible local dashboard at `http://127.0.0.1:8080`. Every synthetic result is visibly labeled `simulated`; it is pipeline evidence, not real sound-model evidence. Run `./scripts/test.sh` for the automated suite.

## Repository map

- `app_lab/` — Arduino App Lab package for the UNO Q Linux and MCU sides
- `firmware/` — standalone XIAO CuePod and UNO Q MCU firmware
- `linux/` — receiver, inference, decision engine, API, and dashboard
- `shared/` — protocol, event schema, and constants
- `simulator/` — synthetic sender, WAV replay, loss, jitter, and latency injection
- `models/` — model selection, preprocessing, conversion, provenance, and evaluation
- `experiments/` — predeclared experiment registry, schema, and result boundaries
- `benchmarks/` — evidence-labeled benchmark methods and curated summaries
- `tests/` — unit, protocol, integration, and evaluation tests
- `hardware/` — exact/estimated BOMs, wiring, schematics, power, and assembly
- `cad/` — native Fusion generator, OpenCascade reference exports/validation, parameters, DFM/provenance, and Windows evidence runbook
- `submissions/` — separate competition-ready packages and differentiation record
- `docs/` — product, architecture, privacy, safety, build, test, and demo guidance
- `user_checklists/` — short physical-action checklists and result capture locations

## Safety and privacy

- Never solder while a LiPo battery is connected.
- Never solder directly to a LiPo cell.
- Confirm polarity and continuity before first battery connection.
- Do not substitute a Qwiic cable for the battery pigtail.
- Keep Wi-Fi credentials in ignored local configuration only.
- Do not add private or copyrighted recordings to Git.

Read [docs/safety.md](docs/safety.md) before hardware work and [docs/privacy-model.md](docs/privacy-model.md) before changing audio retention behavior.

For physical work, begin with [the deadline-ordered next actions](user_checklists/NEXT_ACTIONS.md), then execute the authoritative [Windows flashing and hardware test record](HARDWARE_TESTS.md). The [short hardware bring-up checklist](user_checklists/HARDWARE_BRINGUP.md), [Windows quick guide](user_checklists/WINDOWS_FLASHING.md), and [physical validation matrix](user_checklists/PHYSICAL_VALIDATION.md) are compact views. The editable connectivity source and human schematic are under `hardware/schematics/`.

## License

Unless a file says otherwise, code, documentation, and original design source in this repository are licensed under the [MIT License](LICENSE). Third-party models, audio, code, and assets retain their own licenses and must be listed in the relevant provenance manifests.
