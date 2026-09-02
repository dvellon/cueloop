# Audio data provenance policy

CueLoop does not commit recordings, downloaded datasets, private captures, or derived audio. A filename is not provenance: every evaluated clip must have a manifest record containing a stable ID, cryptographic checksum, labels, split, source/acquisition method, exact license or ownership statement, and confirmed recording consent.

## Acceptable sources

- Self-recorded non-speech household sounds where the recorder owns the recording and records that fact.
- Deliberately recorded attention calls only with informed participant consent; do not store names in filenames or metadata.
- Public clips with an exact license that allows the intended evaluation and submission use, accompanied by source URL and attribution requirements.
- Synthetic audio for software tests, always labeled `simulated` and never included in real-accuracy totals.

## Excluded by default

- Scraped social media or video audio.
- AudioSet/YouTube training clips copied from source videos. The pretrained model can be used under its model license; that does not grant redistribution rights for training videos.
- Smart-speaker, security-camera, workplace, classroom, or home recordings containing incidental private speech.
- Files whose license, consent, source, or checksum is missing.
- Repeated augmentations of one source presented as independent test evidence.

## Split discipline

Group variations from the same recording session/source into one split. Use `calibration` for thresholds, `validation` for mapping/model choices, and a locked `test` split exactly once for the reported result. Report counts by class and hard-negative environment, not only a pooled accuracy.

The evaluator validates the manifest and file checksums before inference. Audio remains memory-only during processing, and only aggregate metrics may be committed. Physical-distance, closed-door, background-noise, and device-microphone results belong in `HARDWARE_RESULTS.md` after the corresponding real setup is observed.

