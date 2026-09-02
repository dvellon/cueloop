# CueLoop App Lab final submission checklist

**Official deadline:** September 13, 2026 at 11:59 PM PDT (**September 14 at 2:59 AM EDT**). Recheck the organizer page immediately before final publication because dates and platform fields can change.

This checklist contains the unavoidable hardware, media, account, and publication actions. Complete it only with direct evidence; “prepared digitally” is not a physical pass.

## 1. Freeze the candidate

- [ ] Choose the release commit after all passing physical-driven code/doc changes are merged.
- [ ] Run `./scripts/test.sh`, Pyright, both canonical Arduino CLI builds, and the isolated App Lab sketch compile at that commit.
- [ ] Run the App synchronizer with model verification and build both release archives.
- [ ] Verify archive SHA-256 values from a second directory; inspect every file list for credentials, audio, databases, caches, local IP/SSID, private media, and build debris.
- [ ] Record tool/core/library/App Lab/runtime versions and final hashes in the build/release record.
- [ ] Tag only the tested commit; do not tag a known-dirty worktree.

## 2. Run unavoidable physical gates

- [ ] Inventory exact hardware, revisions, order accessories, quantities, and markings under W-000 in root `HARDWARE_TESTS.md`.
- [ ] Execute W-100/W-200 in `HARDWARE_TESTS.md`: UNO Q Blink baseline, App Lab CueLoop Run, XIAO USB flash, serial/NVS setup, deterministic `TEST ON` transport.
- [ ] Follow `user_checklists/HARDWARE_BRINGUP.md` before any battery connection: polarity, continuity, inspection, insulation, strain relief, staged USB then battery power.
- [ ] Run H-000 through H-400 in `HARDWARE_TESTS.md` (`user_checklists/PHYSICAL_VALIDATION.md` is the compact matrix) and preserve failures, conditions, units, sample counts, and evidence paths.
- [ ] Disable/drop any class that lacks adequate held-out performance; rebuild/retest if policy or mapping changes.
- [ ] Complete a 30-minute soak and at least one pod/Bridge/app restart-recovery trial.
- [ ] Verify the exact finished build matches the published BOM, wiring, schematic, and safety text.

## 3. Capture original media

- [ ] Capture P01–P15 as applicable from `PHOTO_SHOT_LIST.md`, including real hero, finished system, polarity, App Lab, physical event, schematic, and test setup.
- [ ] Record the primary video storyboard in `VIDEO_PACKAGE.md`, including one successful target event, acknowledgement, and one ambiguous/background outcome.
- [ ] Add physical evidence tier, conditions, and date to result graphics; label any simulator screen unmistakably.
- [ ] Produce accurate captions/transcript, color/brightness-check LED footage, and keep the limitation statement.
- [ ] Complete `LICENSES_AND_ATTRIBUTION.md` media permissions and inspect metadata/reflections/private details before upload.
- [ ] Retain original camera files and edit project outside Git; calculate the final export checksum.

## 4. Populate Hackster fields

- [ ] Select **Best Social Impact** as the primary category if the final platform offers it; do not change claims merely to fit Best in Show.
- [ ] Copy title, subtitle, pitch, and tags from `SUBMISSION_METADATA.md` within live field limits.
- [ ] Use the original physical 16:9 cover—not the Autodesk V2 AI concept—and verify square thumbnail crop.
- [ ] Paste and format `PROJECT_ARTICLE.md`; insert photos where they prove the nearby step, not as an uncaptioned gallery.
- [ ] Replace only explicitly bracketed physical-result/video fields from `HARDWARE_RESULTS.md`; remove unused editorial instructions.
- [ ] Populate Hackster BOM components with exact manufacturer/part/quantity/function/link/price data and match the article.
- [ ] Attach or embed the readable SVG schematic and link the machine-readable netlist/source guide.
- [ ] Attach the App Lab ZIP, clean source ZIP, and relevant safe resource files; include SHA-256 values.
- [ ] Add stable final video URL and verify embedding/playback with sound and captions.
- [ ] Credit model, libraries, sounds, images, fonts, participants, and tools. State project license.
- [ ] State that the entry is original and has not already won another Hackster contest, if truthful at submission time.

## 5. Judge-access and account controls

- [ ] Decide on a stable judge-accessible source location. Because the development repository is private, either publish a sanitized release repository or rely on the attached clean source archive plus an accessible release page; do not paste a private URL as if judges can open it.
- [ ] Test every project, source, model/source, schematic, video, and download link in a logged-out/private browser on desktop and phone.
- [ ] Confirm project visibility is public/submitted, author/profile details are accurate, and collaborators are credited.
- [ ] Confirm every required field and challenge technology/category checkbox is actually saved after page refresh.
- [ ] Save a PDF and full-page screenshots of the final project, rules, timestamp, attachments, and successful submission confirmation.
- [ ] Submit before the deadline buffer; reopen the entry and verify its submitted state rather than trusting a single toast/email.

## 6. Final consistency audit

- [ ] Article, video, dashboard, build manifest, test results, hardware record, BOM, and schematic use the same release/model/protocol versions.
- [ ] No development-host result is described as UNO Q, and no simulated result is described as physical or real-audio accuracy.
- [ ] No “certified alarm,” medical, security, safety replacement, cloud security, encrypted transport, battery-life, or accuracy implication exceeds evidence.
- [ ] V1 is clearly distinct from CueLoop Bridge V2; the V2 concept render and future hardware do not appear as a V1 build.
- [ ] No credentials, raw/private audio, unlicensed media, personal data, database, or debug IP/SSID is in source, archive, screenshots, video, or console excerpts.
- [ ] A fresh reader can find build, wiring, flashing, configuration, operation, troubleshooting, limitations, license, and source without requesting private access.

## Submission record

Fill after completion:

```text
Release version/tag:
Git commit:
App Lab ZIP SHA-256:
Source ZIP SHA-256:
Video SHA-256 and public URL:
Hackster project URL:
Submitted date/time/timezone:
Confirmation evidence path:
Operator:
Known limitations disclosed:
```
