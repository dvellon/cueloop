# UNO Q Linux application

`cueloop/` is the dependency-light core used by both the development-computer demo and the Arduino App Lab adapter. It contains strict UDP decoding, a bounded jitter/window buffer, classifier interface, temporal event engine, metadata-only SQLite store, local API, dashboard, and simulator.

Run from the repository root with `./scripts/demo.sh`. The default classifier recognizes only synthetic test signatures and marks every result `simulated`; it is not evidence of real sound accuracy. A target model adapter is evaluated separately under `models/`.

The service has no cloud runtime dependency and no audio-file writer. V1 binds the dashboard to localhost for desktop development. App Lab deployment will explicitly bind the declared LAN port and document the trusted-LAN limitation.

