# Contributing

CueLoop welcomes reproducibility fixes, accessible interaction ideas, privacy improvements, event-engine tests, and measured hardware results.

## Ground rules

1. Do not commit credentials, private recordings, downloaded datasets, model binaries, build products, or generated Fusion exports. The repository `.gitignore` is the minimum boundary, not permission to mishandle data.
2. Do not claim a measurement without labeling its evidence tier: `simulated`, `development-computer`, `UNO Q`, `physical CuePod`, or `estimated`.
3. Record third-party source, license, retrieval date, checksum, and intended use before using a dataset, recording, model, image, or design.
4. Preserve the default no-raw-audio-retention policy. Any diagnostic capture must be explicit, time-limited, visibly indicated, and outside version control.
5. Treat CueLoop as an awareness aid, never a certified alarm or medical device.
6. Add or update tests with behavioral changes. Run the repository verification script before opening a change.

## Development flow

- Create a focused branch.
- Keep embedded hardware access behind interfaces so simulator tests still run.
- Format and lint only files in scope.
- Update `CHANGELOG.md`, `DECISIONS.md`, or `RISKS.md` when the change affects users, architecture, or claims.
- Use imperative commit subjects such as `feat: add jitter-buffer loss accounting`.

## Physical results

Record observations in `HARDWARE_RESULTS.md` using the supplied checklist ID, exact firmware commit, test conditions, units, and raw observation. Photos and traces that are safe and licensed may be attached separately; sensitive audio must remain local.
