# CueLoop Bridge preliminary Fusion package

The package creates a parameterized concept assembly rather than pretending to be a production-ready enclosure. Manufacturer outlines are real; connector heights, mounting holes, accessory stack, latch forces, and physical fit remain unverified until hardware measurement.

## Generated concept parts

- CuePod base shell with battery volume, XIAO support points, side USB opening, and M2 boss strategy.
- CuePod lid with a seven-opening microphone labyrinth and screw clearances.
- Receiver base shell sized around the UNO Q with internal support points and a front alert-window opening.
- Separate front diffuser body.
- Receiver lid with shallow pod dock pocket, rails, and three tactile-control locations.
- Clip/stand concept and a simple assembly layout.

All critical millimeter values live in `design_parameters.json`. The script mirrors them into Fusion user parameters where practical, creates named components/bodies, and adds an `ESTIMATED_DIMENSIONS_VALIDATE` document attribute.

## Run inside Autodesk Fusion

1. Install/update Autodesk Fusion and sign in. Open **Utilities → Add-Ins → Scripts and Add-Ins**.
2. On the **Scripts** tab, click **+** to create a Python script named `CueLoopBridgeGenerator`. Use **Open file location** on that new script.
3. Replace the generated Python entry file with `fusion/CueLoopBridgeGenerator.py`. Copy `design_parameters.json` into the same script folder (or its parent; the script checks both).
4. Return to Scripts and Add-Ins, select the script, and click **Run**. It creates a new design named `CueLoop Bridge Preliminary Assembly` in millimeter-derived geometry.
5. Inspect the browser for named components: `CuePod_Base`, `CuePod_Lid`, `Receiver_Base`, `Receiver_Lid`, `Alert_Diffuser`, and `Clip_Stand`.
6. Section the shells and verify that no cavity, boss, port, dock, or light window accidentally intersects a protected hardware envelope. Do not send it to manufacture before completing `DIMENSION_VALIDATION.md`.
7. Save the editable cloud design. Then choose **File → Export**, select **Fusion 360 Archive Files (`*.f3d`)**, and save as `CueLoop_Bridge_Preliminary_YYYY-MM-DD.f3d`.
8. Attach the exported `.f3d` to the Autodesk hardware-application Hackster project. Export neutral STEP/3MF views only after inspection; generated exports belong in ignored `cad/exports/`.

If Fusion reports an API error, copy the full error text into root `HARDWARE_TESTS.md` as a CAD run record, along with Fusion version and operating system. Do not manually patch around the failure without updating the generator.

## Render workflow

1. Apply fine matte navy polymer to structural bodies, translucent warm-coral plastic to `Alert_Diffuser`, and a small teal accent to privacy-status geometry.
2. Close the exploded lid gap for beauty renders or keep a 7 mm gap for an application engineering view.
3. Use the Render workspace with soft daylight, a neutral warm-gray environment, and a three-quarter camera angle.
4. Render one clean 16:9 hero, one exploded assembly, one microphone/USB close-up, and one clip/stand view.
5. Caption every image `Fusion concept render—physical enclosure not yet manufactured` until a physical photograph exists.
