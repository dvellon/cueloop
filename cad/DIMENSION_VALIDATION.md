# Physical dimension validation

Record caliper measurements in millimeters. Update `design_parameters.json`, rerun the generator, and preserve the original measurement record.

## CuePod

- [ ] XIAO main board length, width, and PCB thickness.
- [ ] Sense expansion board length, width, assembled height, microphone center, and any removable camera interference.
- [ ] USB-C plug shell and common cable overmold insertion envelope.
- [ ] Battery pouch length, width, thickness at center and protection end, taped cable exit, bend radius, and connector orientation.
- [ ] Clearance between microphone face and inner acoustic wall.
- [ ] Pigtail/connector strain-relief route with no pressure on cell pouch.
- [ ] Standoff positions do not contact components or antenna keepout.
- [ ] Elevated XIAO bridge clears the cell, supports the board without component contact, and leaves the declared 0.35 mm XIAO-to-microphone keepout in the measured stack.
- [ ] Lid closes without compressing the battery.

## Receiver

- [ ] UNO Q PCB length/width and maximum component/header/connector height.
- [ ] Mount-hole center coordinates and usable screw diameter.
- [ ] USB-C insertion/removal envelope and hub/power-cable overmolds.
- [ ] Wi-Fi antenna, LED matrix, status LED, user-button, Qwiic, and ventilation keepouts.
- [ ] Any selected haptic, diffuser/LED, buzzer, and accessory dimensions.
- [ ] Stand angle remains stable under cable load and button force.
- [ ] Clip gap/force works on the intended belt, pocket, and bag strap without sharp stress risers.
- [ ] Dock retains the pod under a carry/drop test without damaging connectors.

## Print/DFM coupon

- [ ] Measure 0.25/0.35/0.45/0.55 mm mating gaps in the chosen PCBWay process.
- [ ] Measure M2 clearance holes, boss pilot holes, and insert pockets.
- [ ] Check minimum readable embossed/debossed privacy and orientation marks.
- [ ] Inspect wall warp, diffuser fit, microphone openings, unsupported spans, and surface finish.
