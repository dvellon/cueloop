# Windows Autodesk Fusion native-model runbook

This is the only remaining external Fusion gate. Complete it on Windows with current Autodesk Fusion, inspect the result, make evidence-backed source adjustments if needed, and return the genuine output folder. Do not import `cad/reference_exports/*.step` into the authoritative document.

## 1. Prepare and verify the source

1. Use the exact Git commit recorded for the run. Copy these three files together through a trusted path:
   - `cad\fusion\CueLoopBridgeGenerator.py`
   - `cad\design_parameters.json`
   - `cad\design_contract.json`
2. In PowerShell, preserve source hashes:

   ```powershell
   Get-FileHash .\CueLoopBridgeGenerator.py -Algorithm SHA256
   Get-FileHash .\design_parameters.json -Algorithm SHA256
   Get-FileHash .\design_contract.json -Algorithm SHA256
   ```

3. Record the Windows version, Fusion version/build, Git commit, three hashes, operator, date/time/timezone, and whether the source was modified. Do not continue with an unexplained digest difference.

## 2. Install the Fusion script

1. Install or update Autodesk Fusion from Autodesk, sign in, and start the **Design** workspace.
2. Open **Utilities → Add-Ins → Scripts and Add-Ins**.
3. On **Scripts**, click **+** and create a Python script named `CueLoopBridgeGenerator`.
4. Select it and choose **Open file location**. Close the dialog temporarily.
5. Replace the generated Python entry file with `CueLoopBridgeGenerator.py`. Copy `design_parameters.json` and `design_contract.json` into that same script directory. Do not rename them.
6. Reopen **Scripts and Add-Ins**, select `CueLoopBridgeGenerator`, and click **Run** once. The script always creates a new document; do not run it repeatedly into a manually edited document.

The script must not request an input STEP/mesh. Its source contains no Fusion `ImportManager` call and the authoritative output is created from native API sketches and features.

## 3. Expected messages and files

During a successful run, Fusion creates a new document named `CueLoop Bridge Native Parametric Assembly`, fits the viewport, validates the model, exports, then shows:

```text
CueLoop Bridge native parametric model created and exported.
Validation: PASS
Components including root: <at least 13>
Solid bodies: <at least 11>
Timeline entries: <at least 35>
User parameters: <at least 70>
Files exported: <positive count>
Output directory: ...\exports\CueLoop_Bridge_Native_v2
```

The exact counts may exceed the minima. Confirm the output tree in `cad/README.md`, every file is non-empty, `CueLoop_Bridge_validation.json` says `"status": "pass"`, `CueLoop_Bridge_source_manifest.json` identifies the native generator and exact input hashes, its `sources\` snapshots match the reviewed inputs, and `SHA256SUMS.txt` covers every listed file except itself.

On any error, copy the complete message and traceback. Keep partial output quarantined and mark the run failed. Update the JSON or generator in Git, rerun automated tests, and generate a fresh document; do not manually patch a failed model into apparent success.

## 4. Prove that the model is genuinely native

Capture all of these checks in the run record:

1. The document is a parametric design with a visible, non-empty bottom timeline containing sketch, construction-plane, extrude, cut/join, and fillet feature icons—not a single imported/base/mesh feature.
2. The Browser hierarchy matches `cad/README.md`. Each of the six manufacturing components contains exactly one final solid body; assembly components may contain no body.
3. **Modify → Change Parameters** shows at least 70 named values, including `mfg_wall`, `mfg_fit_clearance`, `mfg_m2_boss_diameter`, `pod_outer_length`, `pod_mic_hole_diameter`, `receiver_outer_length`, and `receiver_dock_pocket_length`.
4. Expand `CuePod_Bottom`, `CuePod_Top`, `Receiver_Bottom`, and `Receiver_Top`: native sketches and features must exist inside the components. Mesh Bodies must be empty.
5. Temporarily change `pod_mic_hole_diameter` from `1.8 mm` to `2.0 mm`. Confirm the seven top acoustic openings update without an error, capture the parameter/geometry evidence, then **Undo** and confirm the value is again `1.8 mm` before export retention.
6. Close Fusion, start a clean session, open `CueLoop_Bridge_Native.f3d`, and repeat Browser/timeline/parameter checks. This rules out evidence from an unsaved source document.
7. Never use the Ubuntu reference STEP as a source feature in this document. It may be opened in a separate document only for visual dimensional comparison.

## 5. Visual and geometric inspection

Use **Inspect → Section Analysis**, **Inspect → Measure**, and **Inspect → Interference** where useful. The script intentionally explodes lids and the clip; examine assembled clearances by moving a copy of an occurrence or by rerunning from a separately preserved parameter file with `layout.exploded_gap` set to a small review value. Do not overwrite the evidence-generating source without committing the change.

Check:

- CuePod wall/floor/top thickness, lid lip, four M2 boss/pilot pairs, four lid clearances, and no zero-thickness or self-intersecting region;
- microphone cartridge alignment with the seven acoustic openings, protected web between holes, and no blocked microphone face;
- XIAO, LiPo, cable-strain, antenna, and USB access envelopes; no cell compression or sharp contact is inferred from CAD alone;
- dock tongue, latch tab, receiver pocket, and rails have visible clearance and are not impossible to assemble;
- receiver wall/floor/top thickness, four bosses/holes, UNO support and placement envelope, support/output envelopes, and service path;
- three button holes, alert LED window/diffuser, power/USB opening, accessory-cable opening, and ventilation openings are present and open to the intended surface;
- carry clip is one connected solid, has a root, flex arm, lead-in foot, declared gap, no knife edge, and a printable orientation;
- every manufacturing body is one closed solid and has no obvious sliver face, inverted cut, floating body, or unsupported accidental island;
- reference envelopes are clearly named `Reference_*`, excluded from manufacturing exports, and never styled or described as original vendor CAD;
- six per-part STEP/STL/3MF exports correspond to the six manufacturing bodies and contain no hardware reference envelope.

Run Fusion's interference analysis twice: once among assembled enclosure/manufacturing parts and once between hardware envelopes and enclosure bodies. Document intentional contacts (boss/floor, lip/panel, diffuser seat) separately from unacceptable overlaps.

## 6. Required screenshots and renders

Retain original full-resolution captures with the Fusion version/build visible where practical:

1. three-quarter exploded assembly with Browser hierarchy and timeline;
2. **Change Parameters** showing named manufacturing and major enclosure values;
3. CuePod section showing shell, cell/XIAO/microphone envelopes, supports, acoustic path, and USB/cable access;
4. receiver section showing UNO/support envelopes, standoffs, openings, bosses, and service clearance;
5. dock close-up showing tongue, latch, pocket, rails, and measured clearances;
6. carry-clip close-up and intended print orientation;
7. top view showing button, LED/diffuser, microphone, and ventilation openings;
8. isolated six manufacturing components with one solid each;
9. reopened `.f3d` with Browser/timeline and the parameter-change proof;
10. export directory plus hash-verification result.

Create at least these Fusion renders:

- 16:9 three-quarter hero with pod detached;
- exploded engineering view;
- CuePod microphone/dock detail;
- receiver clip/control detail.

Use matte navy for structural parts, warm-coral translucent material for `Alert_Diffuser`, and a small teal privacy accent. Caption renders: `Fusion native concept render—physical enclosure and fit validation pending.` Do not composite the AI cover concept as if it were the generated Fusion model.

## 7. Return and hash the genuine outputs

From PowerShell in the generated `CueLoop_Bridge_Native_v2` directory:

```powershell
Get-Content .\SHA256SUMS.txt
Get-FileHash .\CueLoop_Bridge_Native.f3d -Algorithm SHA256
Get-FileHash .\CueLoop_Bridge_Native.step -Algorithm SHA256
Get-ChildItem -File -Recurse |
  Where-Object Name -ne 'WINDOWS_RETURN_HASHES.csv' |
  Get-FileHash -Algorithm SHA256 |
  Select-Object Hash, Path |
  Export-Csv .\WINDOWS_RETURN_HASHES.csv -NoTypeInformation
Compress-Archive -Path .\* -DestinationPath ..\CueLoop_Bridge_Native_v2_Windows_Return.zip -Force
Get-FileHash ..\CueLoop_Bridge_Native_v2_Windows_Return.zip -Algorithm SHA256
```

Return:

- the complete generated directory;
- `WINDOWS_RETURN_HASHES.csv`;
- the ZIP and its SHA-256;
- the screenshots/renders in a separate clearly named evidence folder;
- the run record with exact counts, messages, issues, and adjustments.

On Ubuntu, extract only into ignored `cad/exports/fusion_return/<date-commit>/`, then run:

```bash
python3 cad/validate_cad.py \
  --fusion-output cad/exports/fusion_return/<date-commit>/CueLoop_Bridge_Native_v2 \
  --write-report cad/exports/fusion_return/<date-commit>/fusion_host_validation.json
```

Record the completed C-100 through C-109 entries in root `HARDWARE_TESTS.md`. The Autodesk Fusion gate passes only when the genuine `.f3d` reopens with native history and the review/return checks succeed.
