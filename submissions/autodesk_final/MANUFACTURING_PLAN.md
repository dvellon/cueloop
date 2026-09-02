# CueLoop Bridge manufacturing and DFM plan

The Autodesk competition describes a concept that could be produced in approximately 750 units. This plan does not claim that quantity has been quoted, manufactured, certified, or economically validated. It identifies the evidence needed to move from a PCBWay prototype to a repeatable product.

## Manufacturing inputs under revision control

- Native Fusion `.f3d` assembly and, if built, Electronics schematic/board linkage.
- Released STEP/3MF or process-specific geometry with units, orientation, material, finish, color, and quantity.
- Dimensioned drawings for critical interfaces, datums, tolerances, fasteners/inserts, diffuser/acoustic features, connector access, and inspection points.
- Versioned BOM with approved manufacturer parts, alternates policy, supply status, price/currency/date, and consumables.
- Assembly work instruction, torque/adhesive/ESD notes, firmware provisioning, serial/label policy, and end-of-line test.
- License/attribution and export/safety/regulatory review appropriate to the final design and markets; no certification is implied by this project.

## Process-selection matrix

| Attribute | SLS/MJF-style nylon candidate | Resin candidate | FDM prototype | Later molded split |
|---|---|---|---|---|
| Early complex geometry | strong candidate | fine detail but material/impact/UV questions | fast local iteration | tooling not justified before geometry freeze |
| Clip fatigue/impact | coupon and cycle test required | likely higher risk; datasheet/test required | anisotropy/orientation critical | material/flow/hinge redesign required |
| Surface/labels | finish/dye and text coupon | strong detail | limited without post-process | texture/marking built into tool |
| Dimensional control | supplier/process tolerance evidence | cure/shrink evidence | printer-specific | tolerance stack/tool qualification |
| Quantity ~750 | quote and nesting required | quote/post-cure labor required | assembly/finish labor likely high | compare tooling plus unit economics only after stable demand |

No process wins from this table alone. Select after coupon, supplier feedback, functional load, acoustic, thermal, finish, lead-time, cost, and repair evidence.

## DFM checklist

- Maintain consistent printable walls and intentional transitions; avoid unexplained thick heat/shrink masses.
- Use radii/fillets at clip, boss, latch, and dock stress concentrations; measure load/fatigue instead of relying on appearance.
- Define mating gaps with a process/material coupon, not a universal printer assumption.
- Keep fastener pilot/clearance/insert geometries process-specific and away from thin edges.
- Use accessible, nonhidden fasteners where possible; minimize unique screw types and assembly direction changes.
- Provide hard stops so screws or closures cannot compress a pouch cell, board, diffuser, or actuator.
- Isolate haptic energy from microphone/board where required and characterize self-noise/coupling.
- Keep microphone openings protected from direct contact while avoiding a water/debris claim without ingress testing.
- Keep antenna volumes free of metal, dense wiring, cells, magnets, and coatings until RF behavior is measured.
- Keep UNO Q connectors, recovery controls, indicators, and ventilation/thermal paths accessible.
- Make battery/power connectors keyed, strain-relieved, inspectable, and serviceable under a documented power-off order.
- Add physical orientation, privacy/local-processing, pod-location, and serial/revision marks that remain readable after finish.
- Check carry-on/product safety with actual cell documentation and destination rules; “portable” is not automatic regulatory approval.

## Prototype inspection plan

1. Quarantine and identify each received part by order/revision/process/material/finish.
2. Photograph all faces before assembly and record warp, cracks, uncured material, sharp edges, occluded holes, weak features, or finish defects.
3. Measure datums, overall envelopes, mating gaps, boss/hole/insert/test-coupon features, acoustic ports, diffuser, dock, and clip geometry using the declared instrument/resolution.
4. Dry-fit inert/uncharged parts first; never force the cell, board, connector, or fastener.
5. Record nonconformances against drawing requirements and disposition them as use-as-is for a named prototype, rework with method, or redesign/reorder. Do not silently sand/drill away traceability.

## Assembly concept

Target one-direction serviceable assembly: install protected/insulated power and any carrier/harness; install UNO Q on verified supports; install light/haptic/control components; route/strain-relieve cables; perform electrical baseline; install diffuser/controls; close lid with controlled fasteners; provision firmware; run end-of-line test; add traceable label. CuePod follows the battery-safe order in `hardware/ASSEMBLY.md` and `HARDWARE_TESTS.md`.

## End-of-line test concept

Each unit/revision record should cover:

1. visual identity/assembly/fastener/label inspection;
2. power-off continuity/short checks at designated test points;
3. current-limited first power and rail/current sanity;
4. board identity, firmware/App/model/protocol version and checksum;
5. self-test of LEDs, haptic, buttons, health/fault patterns, and dock/pod presence if implemented;
6. controlled network/audio signature path with event/acknowledge/mute;
7. privacy audit showing no raw-audio artifact and clearable metadata;
8. short thermal/current observation and charge/power-path function where present;
9. final enclosure, clip/stand/dock, connector, microphone, and antenna access inspection.

Pass limits must be frozen from measured engineering builds before they become production criteria. Store only nonpersonal unit metadata; never provision customer Wi-Fi credentials at manufacturing test.

## Approximately-750-unit review

Before claiming manufacturability at that scale, obtain process-specific quotes and analyze yield/scrap, setup/tooling, inspection labor, assembly time, programming fixture, packaging, logistics, spares/repair, component lifecycle, traceability, warranty, certifications, and regional tax/shipping. The contest prototype can demonstrate a credible path without pretending these commercial gates have passed.
