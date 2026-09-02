# CueLoop Arduino App

CueLoop turns selected nearby sounds into private, visible cues. A XIAO ESP32S3 Sense CuePod sends memory-only 16 kHz PCM over a trusted local network; the UNO Q Linux processor runs a checksum-pinned YAMNet baseline and a temporal confirmation engine; the UNO Q STM32 owns deterministic LED, optional haptic/buzzer, health, and acknowledgement timing.

## Before import

From the repository root, run `python3 scripts/sync_app_lab.py --include-model`. This copies the canonical tested Linux modules, dashboard, MCU sketch, class mapping, UNO Q runtime audit records, and the locally downloaded checksum-verified model into this self-contained folder. Model binaries are deliberately excluded from Git. The sync command fails if the source artifact is absent or its SHA-256 differs from the pinned manifest.

Import the `app_lab/CueLoop` folder in Arduino App Lab and deploy it to an UNO Q. App Lab installs the complete pinned Python dependency set and the pinned sketch profile. The Linux log begins with a runtime identity line containing Python, machine, libc, and resolved LiteRT version; retain it with the App Lab version. On the same trusted LAN, configure the CuePod receiver address to the UNO Q and UDP port 57321. Open port 8080 at the UNO Q address for the dashboard.

No Wi-Fi credentials or API keys belong in this App. Raw PCM remains in volatile memory and is discarded after inference; only bounded event/feedback metadata is stored under the visible `data` folder. V1 UDP and the dashboard are unencrypted and unauthenticated, so use an isolated or trusted LAN—not a public or hostile network.

The committed runtime audit proves that the required binary distributions exist for Arduino's documented CPython 3.13/Linux ARM64 runner tuple; it does not prove installation, dynamic loading, or inference on the received board. Compilation and host tests likewise do not prove physical Bridge transport, LED polarity/brightness, CuePod audio quality, model accuracy, Wi-Fi range, battery runtime, or end-to-end latency. Complete the repository hardware checklist before presenting any of those as measured results.
