# CueLoop troubleshooting

Diagnose from the outside inward: power/USB, board baseline, App Lab, model, Bridge, LAN, CuePod transport, microphone, then policy. Preserve error text and counters before erasing or reflashing anything. Never paste passwords into a bug report.

## UNO Q is absent from App Lab

1. Confirm Windows 10/11 64-bit and current official App Lab.
2. Confirm the cable carries data and the board is powered using the mode documented for the actual Arduino-order USB-C path/hub.
3. Run the built-in Blink baseline before CueLoop.
4. For network mode, put Windows and UNO Q on the same client-visible LAN, disable VPN temporarily if policy permits, and allow private-network mDNS/UDP 5353 when Windows prompts for `mdns-discovery.exe`.
5. Guest/corporate/IoT Wi-Fi may isolate clients even when browser/SSH access works. Move to a private test LAN rather than weakening a public firewall.
6. Use official App Lab Settings/connection diagnostics. Reflash the Linux OS only for a diagnosed corrupt/unresponsive image, with a backup/erase decision recorded.

## App Lab import rejects the archive

- Verify ZIP SHA-256 against its `.sha256` sidecar.
- Confirm the archive has one top-level `CueLoop/` folder containing `app.yaml`, `python/main.py`, and `sketch/sketch.ino` plus `sketch/sketch.yaml`.
- If the installed App Lab Import dialog requests a folder rather than ZIP, extract once and select the top-level `CueLoop` folder.
- Rebuild with `python3 scripts/package_app_lab.py --version 0.1.0`; do not hand-edit the vendor copy.
- Record App Lab version and full message. App format changes are a versioned packaging issue, not a reason to remove mandatory files.

## Python requirement or model startup fails

| Message/symptom | Meaning | Correct action |
|---|---|---|
| model not found | `.tflite` absent from App `models/` | rebuild transfer archive with `--include-model` |
| SHA-256 mismatch | model modified, truncated, or wrong release | remove only that known artifact, re-fetch through the verifier, rebuild archive |
| unexpected input/output tensor | incompatible model/runtime | retain error; compare pinned model/runtime; do not bypass validation |
| cannot install `ai-edge-litert==2.2.0` | target Python/aarch64 resolver mismatch or unavailable network | record Python/OS/architecture/resolver output; evaluate a supported pinned runtime as a material decision |
| process exits instead of showing synthetic events | expected fail-closed behavior | fix the physical model path; never enable a synthetic fallback for a physical claim |

## Dashboard does not load

- Confirm App console printed the port 8080 startup line and did not exit on model/database/socket error.
- Use `http://<UNO-Q-IP>:8080/`, not localhost on the Windows laptop.
- Confirm `app.yaml` declares port 8080 and the LAN/firewall permits local TCP 8080.
- Try the status endpoint directly: `http://<UNO-Q-IP>:8080/api/status`.
- Port conflict: stop the other user app or change CueLoop's descriptor and constant together; do not expose the port through a public router.

## LED4 remains blinking red

This means Bridge is unavailable or the Linux heartbeat is stale.

1. Check App Lab monitor for sketch compilation/flash success and Python Bridge registration/call errors.
2. Confirm the imported sketch is the synchronized CueLoop sketch and `Arduino_RouterBridge` versions match `sketch.yaml`.
3. Wait one heartbeat period, then inspect `/api/status` → `cue_output` calls/failures/last error.
4. Restart the CueLoop App once, not unrelated processes. Run official Blink again if the MCU baseline is uncertain.
5. Record MCU/App restarts and status. Do not hide the red fault state in firmware.

## CuePod has no COM port or upload fails

- Use a data-capable USB-C cable and compare Device Manager before/after reconnecting.
- Keep LiPo detached during flashing.
- Select `XIAO_ESP32S3` with Espressif core 3.3.11.
- Enter Seeed's documented bootloader mode: hold BOOT while connecting USB and release after connection; or hold BOOT and tap RESET.
- Try a known Blink example. If Blink fails, CueLoop is not yet the problem.
- Do not flash the application `.bin` at a guessed address. Compile/upload from source or use an exact complete artifact directory/tool invocation.

## CuePod reports `WIFI_NOT_CONFIGURED` or never connects

- `SET_WIFI` arguments require actual Tab characters and LF. SSID is limited to 32 bytes and password to 64.
- XIAO supports 2.4 GHz Wi-Fi; ensure the SSID makes 2.4 GHz available.
- Re-enter the credential through serial; the password is never printed. Do not add it to a header.
- `wifi_attempts` should rise with bounded backoff. If it does, check SSID/security/signal without logging the password.
- `ERASE` deletes all CuePod NVS configuration and reboots. Use it only when intentionally reprovisioning, then enter every setting again.

## Wi-Fi connects, but `reachable=no`

1. Verify UNO Q's current IPv4 address and send `SET_RECEIVER<TAB>address<TAB>57321`.
2. Confirm CueLoop App is running and UDP 57321 is not blocked.
3. Confirm client isolation is off. The internet can work while LAN client-to-client UDP is blocked.
4. Inspect `sent`, `send_failures`, `valid_acks`, `bad_acks`, `receiver_timeouts`, and RSSI.
5. A valid ACK must return from the configured receiver IP/port with matching pod ID and CRC. Do not accept arbitrary sources to make the indicator green.

## Dashboard says disconnected while valid ACKs rise

- The ACK says the receiver socket is alive; dashboard connection requires recently accepted audio frames.
- Confirm `STREAM ON`, sample/frame format, destination port, and increasing frames-received.
- A packet can pass CRC but still be rejected for unsupported sample/frame size; compare Protocol v1 constants.
- Check dashboard diagnostics for bad packets, format mismatches, gaps, and last error.

## Microphone values are zero, constant, or clipped

1. Switch `TEST ON`. Expected RMS/peak ≈8192 and clipping zero. If that fails, diagnose firmware timing/build first.
2. Switch `TEST OFF`. Quiet-room RMS/peak should vary; exact values require the received hardware and room. Rising `capture_errors` suggests I2S/expansion trouble.
3. Confirm Sense expansion seating and exact board revision. Firmware uses Seeed's current `ESP_I2S` PDM RX path with clock GPIO42 and data GPIO41.
4. Do not tap/strike the MEMS microphone or use a loud alarm to force movement. Stop and record persistent near-32768 peaks/clipping.
5. Variable samples prove capture activity, not class accuracy. Use the licensed held-out evaluation path.

## Packets arrive but no event alerts

- Check input-mode labeling. Test tone was designed for transport and the synthetic classifier, not for YAMNet accuracy.
- Confirm class is enabled, scores cross observe/alert thresholds, at least two evidence windows occur inside the confirmation interval, mute is expired, and cooldown has ended.
- Inspect background/unknown and model identity. Do not lower thresholds based on one anecdote or test split.
- Evaluate real licensed/self-recorded clips on calibration/validation splits, then publish held-out results. Drop unreliable classes.

## Too many false alerts

- Record the environment, class, score, temporal evidence, and event action without saving private audio by default.
- Confirm generic speech is not mapped to attention call.
- Reproduce with consented/provenance-complete audio. Tune on calibration only, validate once, keep test held out.
- Increase class threshold/hits, shorten evidence lifetime, lengthen cooldown, disable the class, or narrow mapping. Report the changed policy and comparison.
- Never market a false-alert reduction from simulator signatures as physical performance.

## Battery/charge behavior is unexpected

Disconnect power and stop for heat, odor, swelling, puncture, reverse polarity, damaged insulation, resets, or unstable voltage. Do not troubleshoot a cell with soldering, loose probes, or an ammeter across it. Return to `hardware/ASSEMBLY.md`; record PCB/cell markings and measured connector orientation. The default firmware intentionally reports battery voltage unavailable because no verified divider is assigned.

## Database/history issue

The App stores at most 500 event rows plus linked feedback and no audio. Use the dashboard's confirmed clear action for normal reset. If the database is corrupt, stop the App, preserve a copy only if it contains no sensitive metadata you cannot retain, then remove the specifically identified App `data/cueloop.sqlite3` through App Lab/file management. Do not delete broad directories. Restart and confirm schema recreation.
