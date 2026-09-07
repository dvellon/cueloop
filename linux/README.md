# UNO Q Linux application

`cueloop/` is the dependency-light core used by both the development-computer demo and the Arduino App Lab adapter. It contains strict framed-TCP packet decoding, a bounded jitter/window buffer, classifier interface, temporal event engine, metadata-only SQLite store, local API, dashboard, and simulator.

Run from the repository root with `./scripts/demo.sh`. The default classifier recognizes only synthetic test signatures and marks every result `simulated`; it is not evidence of real sound accuracy. A checksum-pinned YAMNet LiteRT adapter is available only through the explicit `--classifier yamnet --model ... --mapping ...` flags and the optional dependencies documented under `models/`.

The service has no cloud runtime dependency and no audio-file writer. V1 binds the dashboard to localhost for desktop development. The completed adapter under `app_lab/CueLoop` publishes declared TCP ports 8080 and 57321, receives length-framed CuePod audio on 57321, sends compact Bridge calls to the STM32, records MCU health notifications, and resynchronizes mute/current-cue state after an observed MCU restart. Its trusted-LAN limitation is explicit.
