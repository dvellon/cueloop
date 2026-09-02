# Short hardware bring-up checklist

Perform this only when the hardware is present. Expected observations are explicit; stop at the first unsafe or contradictory result and record it in `HARDWARE_RESULTS.md` using the block below.

1. **Inventory:** photograph and record all board/cell/accessory markings and quantities. Expected: UNO Q ABX00173 4 GB/32 GB, XIAO Sense 113991115 with antenna/Sense expansion, undamaged protected Adafruit 1578, product 261 pigtail, and exact power/data accessories.
2. **USB-only baseline:** with LiPo detached and no soldering, run UNO Q App Lab Blink and XIAO USB firmware/`TEST ON`. Expected: both enumerate, flash, remain cool/stable, and match the Windows checklist.
3. **Integrated USB test:** deploy CueLoop, configure private-LAN receiver, and run test tone. Expected: dashboard port 8080 loads; UDP frames/ACKs advance; LED4 becomes green; Bridge cue/mute/ack work; no raw-audio file appears.
4. **Microphone smoke test:** switch `TEST OFF` and inspect counters/response to quiet, close speech, and gentle tapping near—not on—the enclosure. Expected: capture continues and samples are nonconstant/nonclipped; no accuracy claim yet.
5. **Battery polarity:** with all power removed, measure battery contact polarity, mate pigtail away from the board, measure/label lead polarity, then disconnect battery. Expected: mapping agrees with XIAO `BAT+` farther from USB and `BAT-` closest to USB. Do not proceed on any ambiguity.
6. **Solder:** move LiPo away; with USB and battery detached, solder only the pigtail to verified BAT pads, insulate/strain-relieve, inspect, then continuity/resistance-check. Expected: correct end-to-end mapping and no persistent low-resistance BAT+↔BAT- short.
7. **First battery run:** after a final USB-only test, disconnect USB, place cell outside enclosure on a nonflammable surface, mate connector, set `POWER BATTERY`, and run test tone for five minutes. Expected: stable boot/network/ACKs and no heat, odor, swelling, resets, or lead movement.
8. **Mechanical fit:** disconnect battery before assembly. Validate CAD dimensions, mic/antenna/USB openings, cell restraint, screw clearance, and service access. Expected: no cell compression/sharp contact, no pinched wire, no blocked mic/antenna, and enclosure closes without force.
9. **Validation matrix:** run recovery, distance/door/noise, model, latency/loss, current/runtime, and accessibility tests in `PHYSICAL_VALIDATION.md`. Expected: every result has units, conditions, commit, and evidence tier; failures remain visible.

Record each stop/pass as:

```text
Checklist ID:
Date/time/timezone:
Git commit:
Operator:
Hardware revisions/markings:
Firmware/App Lab versions:
Power source:
Test conditions:
Expected observation:
Observed value and unit:
Evidence tier:
Pass/fail/blocked:
Notes and artifact path:
```

Never solder with the battery connected, never solder the LiPo cell, never put the ammeter across the battery, and never substitute a Qwiic cable for the battery pigtail.
