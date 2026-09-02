# CueLoop

**Know what needs your attention without continuously listening, recording, or remaining in the same room.**

CueLoop is a private, local-first acoustic event bridge. A detachable Seeed Studio XIAO ESP32S3 Sense pod sends live microphone evidence over the local network to an Arduino UNO Q. The UNO Q performs edge inference, combines confidence across time, asks for more evidence when a result is ambiguous, and emits an accessible cue through its deterministic MCU and a local dashboard. Raw audio is discarded by default after inference.

This repository develops two related, deliberately distinct products:

- **CueLoop V1** — a reproducible social-impact prototype for the 2026 *Invent the Future with Arduino UNO Q and App Lab* competition.
- **CueLoop Bridge V2** — a portable, serviceable multi-space tool for Autodesk users, developed for *Build the Autodesk University 2027 Product*.

CueLoop is an awareness aid. It is not a safety-certified alarm, security system, or medical device, and it must not replace required alarms or supervision.

## Current state

Development began on September 1, 2026. Hardware-dependent results are intentionally separated from simulator and development-computer results. See [STATUS.md](STATUS.md), [PLAN.md](PLAN.md), and [HARDWARE_RESULTS.md](HARDWARE_RESULTS.md) for the live record.

## Intended quick start

The simulator-first path will remain usable without boards:

```bash
./scripts/demo.sh
```

The command will start a simulated CuePod, the UDP receiver, uncertainty-aware event engine, API, and local dashboard. Until that checkpoint lands, `STATUS.md` is authoritative about what is runnable.

## Repository map

- `app_lab/` — Arduino App Lab package for the UNO Q Linux and MCU sides
- `firmware/` — standalone XIAO CuePod and UNO Q MCU firmware
- `linux/` — receiver, inference, decision engine, API, and dashboard
- `shared/` — protocol, event schema, and constants
- `simulator/` — synthetic sender, WAV replay, loss, jitter, and latency injection
- `models/` — model selection, preprocessing, conversion, provenance, and evaluation
- `tests/` — unit, protocol, integration, and evaluation tests
- `hardware/` — exact/estimated BOMs, wiring, schematics, power, and assembly
- `cad/` — parametric Fusion automation, dimensions, exports, and assembly notes
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

## License

Unless a file says otherwise, code, documentation, and original design source in this repository are licensed under the [MIT License](LICENSE). Third-party models, audio, code, and assets retain their own licenses and must be listed in the relevant provenance manifests.
