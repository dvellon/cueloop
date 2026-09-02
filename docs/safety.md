# Safety

CueLoop is an experimental awareness aid, not a certified alarm, security system, machine-safety device, or medical device. Continue using required smoke/CO alarms, guards, interlocks, supervision, and established emergency procedures.

## LiPo non-negotiables

1. **Never solder with the battery connected.** Disconnect USB and the LiPo before soldering or continuity work.
2. **Never solder directly to a LiPo cell.** Only work on the replaceable pigtail/connector away from the cell.
3. Do not trust wire color alone. Compare connector orientation and measure polarity before the first connection.
4. With all power removed, use continuity/resistance mode to rule out a short between power and ground.
5. Measure pigtail/cell polarity in DC-voltage mode before mating. Record the actual connector face orientation and readings.
6. Stop for swelling, puncture, heat, odor, corrosion, damaged insulation, or unexpected voltage. Move away from flammables and follow the battery supplier's disposal guidance.
7. Do not charge unattended or inside a closed printed enclosure during bring-up.
8. Protect the cell from screws, sharp board edges, crushing, strain, and soldering heat.

The Adafruit product 261 is a JST-PH battery pigtail. A Qwiic cable is for I2C accessories and is not a battery substitute.

## Electrical bring-up order

1. Inventory markings and inspect for shipping damage.
2. Test the multimeter on a known source and confirm lead/jack selection.
3. Keep the LiPo physically disconnected.
4. Inspect/measure pigtail polarity and board connector polarity.
5. Inspect solder joints under good light; verify no bridge between power and ground.
6. Power logic by the documented USB source first and run smoke/temperature checks.
7. Disconnect USB where the board documentation requires it; only then connect the verified battery path.
8. Measure idle/current behavior without exceeding meter/fuse ratings. Never place an ammeter directly across a battery.

## Mechanical and acoustic safety

- Provide strain relief and prevent conductive parts from contacting the LiPo pouch.
- Do not block board cooling or make the enclosure airtight around heat-generating electronics.
- Use rounded, carry-safe edges and captive/serviceable fasteners.
- Keep buzzer levels conservative; haptic/visual output is preferred for discreet alerts.
- Use test sounds at the lowest useful volume. Do not repeatedly sound real emergency alarms or expose people/animals to startling levels.
- Obtain consent before placing a microphone in a shared or private space, even though audio is not retained.

## Soldering safety

Work on a stable, ventilated, nonflammable surface with eye protection. Treat the iron as live whenever plugged in, return it to its stand, keep the cable clear, wash hands after handling solder, and allow joints to cool before inspection. Battery and USB remain disconnected throughout soldering.
