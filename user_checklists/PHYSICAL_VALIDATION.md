# CueLoop physical validation matrix

Run only completed rows; leave the rest pending. Root `HARDWARE_TESTS.md` is the authoritative complete method and execution log; this file is the compact matrix. Every result must identify Git commit, firmware/App Lab versions, board revisions, date/timezone, operator, power mode, network conditions, evidence tier, units, and artifact path. Targets are predeclared goals, not results.

## Gate 1 — deterministic bring-up

| ID | Test | Method | Target / expected observation | Current evidence |
|---|---|---|---|---|
| P-001 | XIAO USB flash/boot | Windows source upload, 115200 serial | Ready banner, mic-ready banner, no reset loop | Pending physical |
| P-002 | Test-tone framing | `TEST ON`; record two `STATUS` samples | 50 captured/s nominal; RMS/peak ≈8192; clipped=0 | Pending physical |
| P-003 | Wi-Fi/receiver ACK | Configure private LAN + UNO Q IP | sent and valid ACK counters increase; reachable=yes | Pending physical |
| P-004 | Receiver loss/recovery | Stop App for ≥7 s, then restart | timeout once; reachability false then true; stream restart observed | Pending physical |
| P-005 | App/Bridge health | Deploy exact App Lab package | LED4 red while unhealthy, green after heartbeat; dashboard cue output connected | Pending physical |
| P-006 | Cue language | Trigger one confirmed test path per class through controlled replay/test harness | LED3 class color and priority cadence match firmware; clear/mute immediate | Pending physical |
| P-007 | Dashboard controls | Keyboard and pointer acknowledge/dismiss/mute | metadata changes; MCU clears/mutes; LED4 blue while muted | Pending physical |
| P-008 | Optional D4 button | Only if S1 is actually installed; press/release 20 times | exactly one ack per press, no idle phantom ack | Pending inventory/physical |
| P-009 | MCU restart recovery | Restart/redeploy sketch during mute and active pending cue | restart count rises; Linux restores mute/current pending cue | Pending physical |
| P-010 | Privacy file audit | Before/after 15-min run, list App `data/` and inspect DB schema | only bounded metadata/feedback database; no audio files | Pending physical |

Do not continue to battery or claims testing until P-001 through P-005 pass.

## Gate 2 — microphone and network characterization

For each test capture serial/dashboard counters before and after. Use gentle, consented sources; never strike the board or use a real emergency alarm at unsafe volume.

| ID | Condition | Repetitions/duration | Measurements |
|---|---|---:|---|
| P-101 | Quiet room, microphone mode | 5 min | audio RMS/peak range, clipped samples, capture errors, packet loss, RSSI |
| P-102 | Controlled event at 0.5 m line-of-sight | 10/class | detections, misses, confidence, latency |
| P-103 | Same event at 1 m and 3 m | 10/class/distance | recall/confidence vs distance |
| P-104 | CuePod behind one closed interior door | 10/class | recall/confidence/latency/loss |
| P-105 | Background speech/TV/music/fan | 15 min each | false alerts/hour by condition and class |
| P-106 | Confusable nontarget knocks/beeps/shouts | ≥10/type | suppression/confirmation behavior and false alerts |
| P-107 | LAN distance path used in video | 15 min | packet loss, duplicates/late, jitter, RSSI, disconnects |
| P-108 | 5% and 20% artificial packet loss replay | fixed licensed clips, same seed | understandable demo at 5%; diagnostics accurate at 20% |

P-108 is a target-integrated controlled fault test but remains “simulated loss” unless the loss occurs in a documented physical network impairment. Do not relabel it physical RF performance.

## Gate 3 — model evidence

Use owned or permissively licensed PCM16 mono WAV files and a complete ignored manifest. Obtain consent for any identifiable recording. Keep calibration, validation, and held-out test splits separate.

1. Aim for at least 30 positive test examples per retained class across multiple sources/rooms and at least one hour total defined background audio. If the deadline forces a smaller set, publish the actual count and wide uncertainty—not the target.
2. Tune only on calibration, choose policies on validation once, and publish the held-out test output from `models/evaluate.py`.
3. Report per-class precision, recall, F1, support, confusion matrix, missed-event rate, false alerts/audio-hour, Brier/calibration error, model inference latency, and temporal-confirmation comparison.
4. Retain a class for the polished demo only if held-out precision ≥0.80 and recall ≥0.75 **or** clearly disclose that the target was missed and narrow the claim/demo.
5. The quiet/background target is fewer than 1 false alert/hour on the explicitly defined mix. Never extrapolate beyond it.

The checked-in evaluator accepts one onset/end interval per labeled class and reports onset-to-first-temporally-qualifying-window latency plus explicit temporal-versus-single-window metrics. This remains an audio-file decision metric, not full CuePod-to-physical-cue latency; use synchronized H-302 measurement for the latter.

## Gate 4 — latency and resilience

| ID | Measurement | Method | Goal |
|---|---|---|---|
| P-201 | Warm model inference | ≥100 UNO Q invocations after 10 warmups | report mean/median/p95/max and memory; no fixed pass gate until observed |
| P-202 | End-to-end alert latency | 20 events; 60/120 fps video showing source action and LED3 or synchronized electronic marker | median ≤2.5 s, p95 ≤4.0 s |
| P-203 | App restart | 10 restarts | receiver/dashboard recover without DB repair or audio files |
| P-204 | Wi-Fi interruption | 10 AP/client interruptions | bounded reconnect, no reboot required, counters explain gaps |
| P-205 | Bridge interruption/MCU reset | 10 trials | Linux remains alive; visible degraded health; state resynchronizes |
| P-206 | 30-minute soak | physical microphone + normal LAN | no crash/unbounded growth; capture and packet counters plausible |

Video-frame latency includes uncertainty of ±1 frame plus ambiguity in source onset; record frame rate and exact frame indices. Dashboard `pipeline_latency_ms` is processing delay after a complete window, not full acoustic-to-human latency.

## Gate 5 — power, thermal, mechanical, and accessibility

| ID | Test | Method | Required record |
|---|---|---|---|
| P-301 | First battery run | Follow `HARDWARE_BRINGUP.md`, cell outside enclosure | start/end voltage if safely measured, stability, heat/odor/swelling, counters |
| P-302 | Battery runtime | Full supervised charge, USB detached, normal streaming until protected shutdown | start/end time, usable hours, RSSI, resets, cell/ambient conditions |
| P-303 | Charge behavior | Supervised open-enclosure USB charge | PCB revision, indicator sequence, elapsed time, temperature observation; no rate claim without current evidence |
| P-304 | Thermal soak | 30 min USB and battery modes | ambient plus repeatable board/enclosure surface measurement method |
| P-305 | Enclosure fit | CAD checklist plus cable insertion/service | no battery compression, sharp contact, blocked mic/antenna, or forced closure |
| P-306 | Cue accessibility | at least one intended user or structured evaluator, with consent | immediate comprehension, non-color cue distinction, comfort, acknowledge/mute success |
| P-307 | Video legibility | record planned 1080p framing | event, confidence, priority, connection, privacy, and cue visible without zoom |

## Result publication rule

- Put raw private audio and generated JSON under ignored paths.
- Curated Markdown results may be committed only with dataset size/provenance, method, evidence tier, date, commit, and limitations.
- A failed target is a result, not something to delete.
- Never combine development-computer, UNO Q, physical CuePod, simulated, and estimated numbers in one unlabeled table.
- CueLoop remains an awareness aid regardless of test performance.
