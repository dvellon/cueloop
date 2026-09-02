# CAD design provenance

## Original CueLoop geometry

The enclosure shells, lid lips, M2 boss/clearance strategy, XIAO/UNO support strategy, battery restraint rails, microphone opening array, USB/power/cable/ventilation/button/LED openings, detachable-pod tongue/latch, receiver pocket/rails, diffuser envelope, clip geometry, exploded assembly layout, parameter system, Fusion generator, and FreeCAD reference generator are original CueLoop work in this repository.

The AI-generated raster under `assets/concepts/` is visual concept art with its own prompt/mode/digest record. It is not CAD, physical evidence, or a source body for either generator.

## Vendor-derived and estimated references

The following `Reference_*` bodies are deliberately simplified rectangular placement envelopes:

| Reference body | Dimension source | Claim boundary |
|---|---|---|
| `Reference_UNO_Q` | Arduino official product/form-factor material plus an explicitly conservative height envelope | Not Arduino board CAD, connector geometry, mounting-hole evidence, or an original board model |
| `Reference_XIAO_Sense` | Seeed official outline plus conservative stacked-height allowance | Not a reproduction of the PCB, antenna, camera, microphone package, or connector |
| `Reference_LiPo_500mAh` | Adafruit product 1578 published dimensions | Not pouch-tolerance, cable-bend, swelling, compression, charge, or safety evidence |
| `Reference_Microphone_Cartridge` | Conservative CueLoop keepout pending received-part measurement | Not vendor package geometry or proof of an acoustic seal/path |
| `Reference_Support_Electronics` | CueLoop reserved volume | No vendor selected; not a purchased BOM part |
| `Reference_Haptic_LED_Module` | CueLoop reserved volume | No vendor selected; not a purchased BOM part |

Source URLs and geometry policies are stored next to the dimensions in `design_parameters.json` and copied into `CueLoop_Reference_provenance.json` and the Fusion BOM export. Reference bodies are excluded from per-part manufacturing exports.

No third-party STEP, mesh, BRep, or board model is imported by either generator. If a future vendor model is used, retain its original filename, URL, license/terms, retrieval date, digest, transformations, and visible `VENDOR_REFERENCE_*` naming; never merge it silently into original geometry.

## Evidence hierarchy

1. `design_parameters.json` and the generators prove authored source and intent.
2. Committed OpenCascade exports/reports prove that the independent reference implementation forms valid neutral solids on the recorded development tool.
3. The returned Fusion `.f3d`, validation report, screenshots, and parameter-edit/reopen test prove that Autodesk-native geometry and history were created.
4. Caliper, fit, cable, battery, acoustic, thermal, RF, load, and DFM records prove physical/manufacturing claims.

No lower tier may be promoted into a higher-tier claim.
