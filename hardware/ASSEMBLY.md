# Battery-safe assembly order

This procedure stops at every point where a wrong assumption could damage the cell or boards. Keep the CuePod enclosure open and the LiPo outside it during first power and charging checks.

## 1. Inventory and inspect

1. Photograph both sides and record exact markings/revisions for UNO Q, XIAO main board, Sense expansion, battery, pigtail, cables, power supply/hub, and any Modulinos.
2. Reject/stop for a swollen, dented, punctured, hot, odorous, corroded, or abraded cell; damaged connector; loose component; cracked board; or exposed conductor.
3. Confirm the Sense expansion board and antenna are present and properly seated. The camera is unused; do not remove parts until the exact received stack is documented.
4. Confirm the USB cables carry data, not only power.

## 2. Bring up boards on USB before soldering

1. Leave the LiPo and pigtail disconnected.
2. Flash/test the XIAO from USB using the Windows checklist, first in `TEST ON`, then `TEST OFF` microphone mode.
3. Run Arduino's Blink/App Lab smoke test on UNO Q, then deploy CueLoop and verify LED3/LED4 behavior.
4. Stop for resets, unexpected heat, odor, unstable power, or damaged connectors.

## 3. Identify battery and pigtail polarity

1. Prove the multimeter on a known low-voltage source; black lead COM, red lead voltage/ohms jack, DC volts selected.
2. With pigtail **not attached to the board**, carefully measure the protected battery connector contacts without bridging them. A positive display means the red probe is on battery positive. Photograph/record the connector face orientation.
3. Mate battery and pigtail away from metal, measure at the stripped pigtail ends, and label the actual positive/negative leads. Disconnect the battery immediately afterward.
4. Seeed states XIAO BAT- is closest to USB-C and BAT+ is farther away. Verify the received board markings/revision before proceeding.

## 4. Solder only the detached pigtail

1. Confirm both USB and battery are physically disconnected. Move the LiPo away from the soldering area.
2. Trim only as needed, slide on insulation/strain-relief material before soldering, tin quickly, and solder measured pigtail positive to `BAT+` and negative to `BAT-`.
3. Never solder a battery lead while its cell is attached and never solder directly to the cell tabs/pouch.
4. Inspect under good light/magnification. Confirm no splash, whisker, cold joint, exposed conductor, or strain on the pads.

## 5. Unpowered electrical checks

1. With battery and USB still disconnected, continuity-check each connector contact to its intended BAT pad.
2. Check BAT+ to BAT-. A momentary changing resistance from capacitance can be normal; a persistent near-zero/continuity indication is a stop condition.
3. Confirm neither battery lead contacts shields, fasteners, antenna, microphone opening, or conductive enclosure features.

## 6. USB validation of the finished pigtail

1. Keep the LiPo detached; power XIAO by USB on a nonflammable surface.
2. Re-run firmware status/test tone. Inspect temperature and stability for at least five minutes.
3. If safely accessible, measure DC voltage/polarity at the empty battery connector. Stop for reverse polarity or any value inconsistent with a one-cell charging path; do not short the contacts.
4. Disconnect USB and wait before moving the assembly.

## 7. First battery power

1. Place the cell on a nonflammable surface outside the enclosure. Reconfirm there is no USB power.
2. Mate the verified connector while observing the board/cell. Do not force it.
3. Run `POWER BATTERY`, `TEST ON`, and `STATUS`; verify boot, Wi-Fi, packet counters, and no unexpected heat for five minutes.
4. Switch `TEST OFF` only after the deterministic transport test passes.
5. Disconnect the cell before installing/removing any enclosure, fastener, restraint, or wire routing.

## 8. Enclosure and strain relief

1. Complete CAD dimension/fit validation. Remove sharp support scars and debris.
2. Restrain the battery without bending, crushing, puncturing, or placing screw tips/board edges against the pouch. The lead must have strain relief and the connector must remain serviceable.
3. Keep microphone and antenna paths clear. Do not make a sealed heat trap.
4. Close the enclosure only after a powered open-air run passes. Initial charging remains supervised with the enclosure open.

Record every observation against the current Git commit in root `HARDWARE_TESTS.md`; copy only reviewed summaries to `HARDWARE_RESULTS.md`. The short execution order is in `user_checklists/HARDWARE_BRINGUP.md`.
