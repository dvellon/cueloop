# Ubuntu OpenCascade reference pipeline

`freecad_reference.py` builds a second implementation of the CueLoop geometry from `cad/design_parameters.json` using FreeCAD's OpenCascade kernel. It saves and reopens an editable FCStd, exports and reopens the assembly STEP, exports per-part STEP/STL files, evaluates forbidden intersections, and records validity, closedness, solid count, volume, area, bounding boxes, provenance, and hashes.

This model is deliberately **not authoritative** for the Autodesk submission. It exists to detect parameter, boolean, solid, and export defects on Ubuntu before the native `adsk` script is run. The contest archive must be the `.f3d` created directly by `cad/fusion/CueLoopBridgeGenerator.py`, with a visible Fusion timeline, native sketches/features, named parameters, and component hierarchy.

The generator labels every vendor-derived or estimated hardware shape as a simple placement envelope. It neither contains nor claims original vendor board, connector, microphone-package, or battery geometry.

Run the pinned local tool path with:

```bash
./scripts/run_cad_reference.sh
python3 cad/validate_cad.py --reference-output cad/reference_exports
```

The runner expects the checksum-verified FreeCAD 1.1.3 AppImage in ignored `.tools/`, or a `FreeCADCmd`/`freecadcmd` command already installed. See `cad/README.md` for acquisition and checksum details.
