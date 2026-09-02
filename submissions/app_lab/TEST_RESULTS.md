# CueLoop test results for publication

**Snapshot:** 2026-09-02 EDT

**Rule:** this document summarizes reproducible evidence; `HARDWARE_RESULTS.md` remains authoritative for physical observations.

## Publishable digital results

| Area | Evidence tier | Method | Result | Claim boundary |
|---|---|---|---|---|
| Regression suite | Development computer / simulation | `./scripts/test.sh` | 49 tests passed at the last integrated checkpoint | Exercises software/CAD-document contracts; no board or real-audio claim |
| Python static analysis | Development computer | `npx --yes pyright` | 0 errors, 0 warnings | Static analysis, not runtime proof |
| XIAO firmware | Development-computer compile | Arduino CLI 1.5.1, `esp32:esp32` 3.3.11, target `XIAO_ESP32S3` | 888,480 B program (26%); 47,632 B global RAM (14%) | Compiles only; mic, Wi-Fi, NVS, and battery unobserved |
| UNO Q firmware | Development-computer compile | Arduino CLI 1.5.1, `arduino:zephyr` 0.90.0, target `unoq` | 93,304 B program (11%); 34,018 B global RAM (12%) | Compiles only; MCU LEDs, button, and Bridge unobserved |
| App Lab sketch reproducibility | Development-computer compile/hash | canonical versus isolated pinned App sketch profile | deployable binary hashes match | Does not prove App Lab deployment on a board |
| YAMNet adapter | Development computer / synthetic workload | checksum/tensor/label validation plus 100 timed invokes | mean 1.834 ms; p95 1.919 ms; max 1.997 ms; process peak RSS 73,384 KiB | Proves host execution only; input was not an accuracy dataset |
| Protocol resilience | Simulation/unit tests | CRC, unknown flag/version, malformed length, loss, reorder, wrap, restart, huge jump | invalid inputs rejected; bounded cases pass | Controlled software injection, not RF performance |
| Decision policy | Simulation/unit tests | observation, minimum evidence, confirmation interval, cooldown, mute | declared transitions pass | Synthetic scores, not calibrated model performance |
| Storage privacy boundary | Unit/integration tests | fixed event schema, history bound, API clear | metadata-only schema and bounds pass | Does not independently audit OS swap, memory, or hostile hosts |
| Bridge fault handling | Unit tests | failed/late calls, MCU restart/status | failures remain diagnostic and resync paths pass | Mock Bridge, not target Router Bridge timing |

Exact build commands, full artifact hashes, builder/tool versions, and timestamps are in `firmware/BUILD_MANIFEST.md`. The model benchmark includes the host/runtime identity in `models/benchmarks/`.

## Physical and real-audio results still pending

| Required result | Minimum publication evidence | Current status |
|---|---|---|
| Inventory and board revisions | original photos plus markings/quantities | Not observed |
| XIAO USB baseline and serial configuration | upload log, Blink/config/status evidence | Not observed |
| Sense microphone capture | quiet/test-tone RMS, peak, clipping, capture-error record | Not observed |
| CuePod → UNO Q transport | sent/received/ACK/loss counters under stated range/conditions | Not observed |
| App Lab deployment | successful Run screenshot and versioned console log | Not observed |
| UNO Q LiteRT performance | warm/cold inference timing and memory under target runtime | Not observed |
| Bridge and physical cues | LED3/LED4/button timing plus disconnect/restart recovery | Not observed |
| End-to-end alert latency | synchronized stimulus-to-cue method, distribution, and conditions | Not observed |
| Per-class accuracy | provenance-complete calibration/validation/test audio; confusion and confidence records | Not observed |
| False-alert rate | duration and environment-normalized held-out background runs | Not observed |
| Closed-door/range behavior | declared distance/walls/AP/setup and packet statistics | Not observed |
| Battery runtime/charge/thermal | safe staged procedure, time/voltage/temperature observations | Not observed |
| Enclosure fit and usability | measured dimensions, photos, access/strain/heat checks | Not observed |
| Accessibility feedback | consented protocol, participant context, result/limitations | Not observed |

Use `user_checklists/PHYSICAL_VALIDATION.md` for the predeclared methods and write each observation into `HARDWARE_RESULTS.md`. Do not convert “Not observed” to pass based on a compile, simulator, datasheet, visual assumption, or successful test of a different hardware revision.

## Final insertion format

After hardware testing, add a compact publication table without deleting failures:

| Metric | Hardware/revision | Conditions and sample size | Result with unit/distribution | Pass/fail | Evidence link |
|---|---|---|---|---|---|
| [for example: end-to-end latency] | [exact identities] | [source/distance/network/n] | [median/p95/max ms] | [status against predeclared target] | [photo/log/video] |

For classification, report per-class precision, recall, F1, misses, false triggers per audio hour, calibration error, and the number of clips/sources/environments in each split. A qualitative successful demo does not substitute for those metrics.

## Wording that remains prohibited

- “Validated on UNO Q” before an actual target run.
- “Accurate,” “reliable,” “real-time,” or a percentage without a defined dataset, sample count, conditions, and method.
- “Private” without the local-LAN, volatile-audio, unencrypted/unauthenticated V1 boundaries.
- “No false alarms” from a small or curated demonstration.
- “Battery lasts X hours” from capacity arithmetic instead of a physical discharge observation.
- “Detects smoke alarms” in a way that implies certification or replacement of required alarms.
