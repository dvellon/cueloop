# CueLoop next physical and account actions

All independent digital development is prepared. Work these gates in deadline order; stop on unsafe or contradictory hardware observations and record them rather than improvising.

## 1. Submit the Autodesk hardware application first

Deadline: **September 7, 2026 at 11:59 PM PDT / September 8 at 2:59 AM EDT**. Target September 6.

1. Create the public CueLoop Bridge Hackster draft using `submissions/autodesk_application/HACKSTER_PROJECT_OPENING.md`, the starting BOM, system diagram, and the clearly labeled V2 concept image.
2. In Autodesk Fusion, run `cad/fusion/CueLoopBridgeGenerator.py`, inspect the named components/cuts, save the cloud design, and export the preliminary `.f3d` exactly as `cad/README.md` describes. This interactive Fusion export cannot be produced on the Ubuntu build host.
3. Write the truthful entrant biography in answer 5 and paste the public draft URL in answer 3. These identity/account fields cannot be inferred safely.
4. Complete `submissions/autodesk_application/APPLICATION_CHECKLIST.md`, preview logged out, save the live rules if template placeholders remain, submit, and retain confirmation evidence.

## 2. Inventory and USB-only baselines

1. Photograph and record exact UNO Q, XIAO Sense, cell, pigtail, cable/power accessory, tool, and optional-part identities under W-000 in root `HARDWARE_TESTS.md`.
2. On Windows, execute W-100/W-200 in `HARDWARE_TESTS.md`; `user_checklists/WINDOWS_FLASHING.md` is the short companion: UNO Q Blink, App Lab import/Run, XIAO flash with the battery detached, tab-separated NVS configuration, and `TEST ON` transport.
3. Record every version, console result, firmware/App identity, commit, and unexpected message. Do not paste Wi-Fi credentials into Git or screenshots.

## 3. Microphone, network, and physical cue

1. Follow `user_checklists/HARDWARE_BRINGUP.md` in order. Confirm deterministic test-tone counters and ACK health before `TEST OFF` microphone mode.
2. Verify RMS/peak variation and clipping/capture counters without claiming class accuracy.
3. Observe App Lab LiteRT startup, dashboard, Bridge LED3/LED4 behavior, acknowledgement, disconnect, and restart resynchronization.
4. Append observations to `HARDWARE_TESTS.md`, then copy only reviewed publishable summaries to `HARDWARE_RESULTS.md`; preserve failures and exact conditions.

## 4. Battery only after the safe gate

Read `docs/safety.md` and `hardware/ASSEMBLY.md` completely. Keep the cell disconnected during measurement, soldering, inspection, insulation, and strain relief. Trust meter readings and board/cell markings—not wire color. First battery power occurs outside the enclosure on a nonflammable surface only after USB operation passes. Stop immediately for heat, odor, swelling, damaged insulation, reverse polarity, unstable voltage, or unexplained resets.

## 5. Measure, narrow, and capture

1. Run H-100 through H-400 in `HARDWARE_TESTS.md` (with `user_checklists/PHYSICAL_VALIDATION.md` as the compact matrix), including provenance-complete audio splits, per-class quality, end-to-end latency, loss/range/door conditions, recovery, 30-minute soak, battery/runtime/thermal, fit, and accessibility checks.
2. Disable or remove any class that fails held-out evidence. Rebuild and repeat affected gates; never tune on the final test split.
3. Capture the real images in `submissions/app_lab/PHOTO_SHOT_LIST.md` and the physical three-minute sequence in `VIDEO_PACKAGE.md`.
4. Copy only measured results into `submissions/app_lab/TEST_RESULTS.md` and the project article. Keep simulation/development-host/UNO-Q/physical evidence labels visible.

## 6. Publish the App Lab entry

Deadline: **September 13, 2026 at 11:59 PM PDT / September 14 at 2:59 AM EDT**.

1. Complete `submissions/app_lab/SUBMISSION_CHECKLIST.md` against the final tested commit.
2. Attach the checksum-verified App Lab and source ZIPs from ignored `packages/`; use a public release location or attachments because the development repository is private.
3. Test the article, video, downloads, schematic, source, and every link while logged out on desktop and phone.
4. Submit early, reopen the entry, and retain the timestamped confirmation.

## Report back for integration

Return the appended `HARDWARE_TESTS.md` blocks, safe photos/logs or their paths, Fusion error text/export confirmation, and any App Lab/flash error exactly as observed. With those records, `HARDWARE_RESULTS.md`, thresholds, supported classes, instructions, BOM, CAD dimensions, and final copy can be revised without guessing.
