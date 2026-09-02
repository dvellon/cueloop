# CueLoop Bridge native CAD package

The contest-authoritative model is generated inside Autodesk Fusion by `fusion/CueLoopBridgeGenerator.py`. It creates native parametric components from sketches, dimensions, construction planes, extrudes, cuts, joins, fillets, named user parameters, occurrences, and captured timeline history. It does **not** import a completed mesh, STEP, BRep, or base feature.

The independent `reference/freecad_reference.py` implementation uses FreeCAD/OpenCascade on Ubuntu to generate and reopen real STEP solids. Its committed exports provide automated geometric evidence, but they are explicitly non-authoritative and must not be submitted in place of the Fusion `.f3d`.

## Source and evidence map

| Artifact | Purpose | Authority |
|---|---|---|
| `design_parameters.json` | Versioned millimeter dimensions, manufacturing values, placements, and hardware envelopes | Shared design source; measurement gates remain |
| `design_contract.json` | Required components, roles, provenance, minimum native counts, and output structure | Automated acceptance contract |
| `fusion/CueLoopBridgeGenerator.py` | Builds and exports native Fusion design | Authoritative contest generator |
| `reference/freecad_reference.py` | Independent OpenCascade solid implementation | Reference/validation only |
| `reference_exports/` | Editable FCStd reference, reopened STEP evidence, per-part STEP/STL, reports, and hashes | Development-computer CAD evidence only |
| `validate_cad.py` | Dependency-free parameter/output validator | Host acceptance tool |
| `FUSION_WINDOWS_RUNBOOK.md` | Exact Windows run, evidence, visual review, return, and hash workflow | Operator procedure |
| `PROVENANCE.md` | Original-versus-vendor/estimated geometry boundary | Submission claim control |
| `PCBWAY_DFM.md` | Production-process assumptions and outstanding DFM gates | Manufacturing handoff |
| `DIMENSION_VALIDATION.md` | Physical caliper, fit, cable, battery, and coupon checks | Required before manufacture |

## Native component hierarchy

The Fusion Browser should contain:

```text
CueLoop Bridge Native Parametric Assembly
├── CuePod_Microphone_Module
│   ├── CuePod_Bottom
│   ├── CuePod_Top                    (exploded upward)
│   ├── Reference_XIAO_Sense
│   ├── Reference_LiPo_500mAh
│   └── Reference_Microphone_Cartridge
└── Receiver_Assembly
    ├── Receiver_Bottom
    ├── Receiver_Top                  (exploded upward)
    ├── Receiver_Carry_Clip           (exploded behind)
    ├── Alert_Diffuser
    ├── Reference_UNO_Q
    ├── Reference_Support_Electronics
    └── Reference_Haptic_LED_Module
```

The six manufacturing components each finish as one closed solid. Their native feature histories include open-shell cavity cuts, M2 boss/pilot or clearance geometry, lid lips, an elevated battery-clearing XIAO bridge, UNO supports, dock tongue/pocket/rails, microphone ports, USB/power/cable/ventilation/LED/button openings, noncompressive battery restraint rails, and a connected carry clip.

## Automated Ubuntu reference run

The development run uses official FreeCAD 1.1.3 x86_64 AppImage release asset `FreeCAD_1.1.3-Linux-x86_64-py311.AppImage`:

```text
SHA-256: 3a853eb69ee595f779f2255dbf80a765926981d8ff68903cefee4dfb03a8f5ef
Source: https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3
```

The binary and extracted runtime live under ignored `.tools/`; they are not redistributed. A system `FreeCADCmd`, `freecadcmd`, or the extracted verified AppImage can run:

```bash
./scripts/run_cad_reference.sh
python3 cad/validate_cad.py --reference-output cad/reference_exports
```

The current reference run produced an editable `.FCStd`, 12 valid/closed/positive-volume solids, an assembly STEP that reopened as 12 solids, and zero overlap for all 12 forbidden enclosure/envelope and envelope/envelope pairs. The host validator verifies the parameter math, object set, exact bounds, vertical/electronics clearances, per-part STEP/STL structure, report boundary, and SHA-256 manifest. This proves CAD-program continuity and neutral-export integrity, not physical fit or Autodesk-native history.

## Fusion exports

On a successful Windows Fusion run, the script creates `exports/CueLoop_Bridge_Native_v2/` beside the script with:

```text
CueLoop_Bridge_Native.f3d
CueLoop_Bridge_Native.step
CueLoop_Bridge_parameters.json
CueLoop_Bridge_BOM.json
CueLoop_Bridge_BOM.csv
CueLoop_Bridge_validation.json
CueLoop_Bridge_source_manifest.json
README.txt
SHA256SUMS.txt
sources/
  CueLoopBridgeGenerator.py
  design_parameters.json
  design_contract.json
manufacturing/
  Alert_Diffuser.{step,stl,3mf}
  CuePod_Bottom.{step,stl,3mf}
  CuePod_Top.{step,stl,3mf}
  Receiver_Bottom.{step,stl,3mf}
  Receiver_Carry_Clip.{step,stl,3mf}
  Receiver_Top.{step,stl,3mf}
```

The `.f3d` and assembly STEP are self-contained exports through Fusion `ExportManager`. The six per-part STEP/STL/3MF sets are production candidates only after visual, dimensional, fit, material/process, and PCBWay DFM review.

## Official Fusion API basis

The implementation follows Autodesk's current APIs:

- [Fusion `Design.designType`](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Design_designType.htm) for parametric history;
- [`UserParameters.add`](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserParameters_add.htm) and expression-backed `ValueInput` objects;
- [`DistanceExtentDefinition.create`](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/DistanceExtentDefinition_create.htm) with `setOneSideExtent` rather than the retired `setDistanceExtent`;
- [`ExportManager`](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportManager.htm) and `execute` for F3D, STEP, STL, and 3MF;
- [`createFusionArchiveExportOptions`](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportManager_createFusionArchiveExportOptions.htm) for the self-contained archive;
- [`createC3MFExportOptions`](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportManager_createC3MFExportOptions.htm) for 3MF manufacturing output.

Proceed with [the exact Windows procedure](FUSION_WINDOWS_RUNBOOK.md). Do not manufacture from any output until [the dimension checklist](DIMENSION_VALIDATION.md) and [PCBWay DFM gates](PCBWAY_DFM.md) are complete.
