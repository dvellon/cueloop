# PCBWay manufacturing and DFM handoff

The six exported manufacturing components are production-intent candidates, not released production files. The current geometry is suitable for quoting and process discussion because it is watertight, one-solid-per-part, dimensioned in millimeters, serviceable by M2 fasteners, and uses nominal 2.4 mm walls/floors with declared gaps and minimum webs. Final process/material/finish/tolerance selection remains evidence-gated.

## Current manufacturing parameters

| Parameter | Value | Purpose |
|---|---:|---|
| nominal wall/floor | 2.4 mm | robust printed enclosure baseline |
| top skin | 2.8 mm | button/LED/acoustic top stiffness allowance |
| mating fit clearance | 0.5 mm per side, 1.0 mm total dock envelope | preliminary printed fit |
| print gap | 0.35 mm | lid-lip preliminary process gap |
| minimum web | 1.2 mm | acoustic/fastener/opening feature guard |
| M2 clearance / pilot / boss OD | 2.4 / 1.65 / 6.4 mm | removable enclosure strategy |
| boss radial web | 2.375 mm | exceeds declared 1.2 mm minimum |
| nominal edge radius | 3.0 mm | handling and stress reduction |
| mesh deviation / max edge | 0.08 / 1.5 mm | high-refinement Fusion STL/3MF export |

These values are named Fusion parameters. The 1° draft value is a planning parameter for a possible molded revision; the current additive geometry does not claim molded-tool release or apply cosmetic draft to every wall.

## Quote/review package

Provide PCBWay with:

- per-part STEP as the dimensional authority for quoting;
- STL or 3MF only as tessellated manufacturing/reference files;
- material/process/color/finish request;
- quantity and intended use;
- the parameter/BOM/validation reports;
- screenshots identifying mating, acoustic, optical, flexing, cosmetic, support-critical, and no-support surfaces;
- explicit note that battery, electronics, clip force, optics, and acoustic behavior remain preproduction tests.

Ask PCBWay to review minimum wall/web, hole/boss process capability, lid/dock/clip gaps, warpage risk, thin acoustic openings, unsupported spans, orientation/support scars, translucent diffuser material, tolerances, and expected post-processing. Record supplier feedback and every geometry revision.

## Required release gates

1. Complete `DIMENSION_VALIDATION.md` from received parts and preserve raw measurements.
2. Print a clearance/hole/web coupon in the exact selected process/material/finish.
3. Rerun both generators, validators, Fusion visual inspection, and export checks after parameter changes.
4. Confirm closed one-solid parts and correct units in an independent slicer/STEP viewer.
5. Perform enclosure fit/service, battery noncompression, cable insertion, mic/antenna clearance, clip force/cycle, dock retention/cycle/drop, thermal, acoustic, and RF tests.
6. Obtain and archive PCBWay DFM feedback/quote with the exact file hashes.
7. Freeze a revisioned manufacturing manifest; never send an unlabeled `latest` file.

No CAD validation replaces electrical safety, battery handling, received-part inspection, human comfort, or production quality control.
