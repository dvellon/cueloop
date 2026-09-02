# Windows flashing and App Lab deployment

This quick checklist uses source and package artifacts already validated on the Ubuntu builder. It does not assume either board is attached to Ubuntu. Root `HARDWARE_TESTS.md` is authoritative and contains the complete steps, expected observations, and append-only execution record; copy only reviewed summaries to `HARDWARE_RESULTS.md`.

## Prepare transfer artifacts on Ubuntu

From the repository root:

```bash
python3 scripts/sync_app_lab.py --include-model
python3 scripts/package_app_lab.py --version 0.1.0
```

Transfer these to Windows through a trusted method:

- `packages/CueLoop-App-Lab-v0.1.0.zip`
- `packages/CueLoop-App-Lab-v0.1.0.zip.sha256`
- the repository working tree or at least `firmware/xiao_cuepod/`
- optionally `firmware/xiao_cuepod/build/artifacts/` for comparison/recovery

On Windows PowerShell, verify the archive before import:

```powershell
Get-FileHash .\CueLoop-App-Lab-v0.1.0.zip -Algorithm SHA256
Get-Content .\CueLoop-App-Lab-v0.1.0.zip.sha256
```

The two digests must match. Do not put Wi-Fi credentials into the transferred source/archive.

## A. UNO Q first connection and App Lab smoke test

1. Install the current Arduino App Lab for Windows 10/11 64-bit from Arduino's official software page.
2. Keep the CuePod LiPo detached. Connect UNO Q using the known Arduino-order USB-C data/power path. Follow the exact product manual for PC-hosted vs powered-hub/SBC mode; do not assume a charge-only cable is sufficient.
3. Launch App Lab. If Windows Defender asks about `mdns-discovery.exe`, allow private-network access only as appropriate for the trusted LAN. Network mode discovery uses mDNS/UDP 5353; guest, corporate/IoT isolation, VPNs, and firewalls may block it.
4. Record the detected board identity, 4 GB / 32 GB configuration, Linux image/update state, App Lab version, connection mode, and UNO Q LAN address.
5. Run Arduino's built-in Blink example. Expected: the documented MCU-controlled RGB LED blinks and App Lab reports a successful run. Stop here if this baseline fails.

Do not reflash the UNO Q Linux image just because CueLoop fails. Use the official image-recovery flow only for a diagnosed corrupt/unresponsive OS and record whether user data will be erased.

## B. Import and run CueLoop on UNO Q

1. In App Lab, open **My Apps**, choose the Import action, and select the verified CueLoop ZIP (or its extracted `CueLoop` folder if the installed version requests a directory).
2. Inspect before running: `app.yaml`, `python/main.py`, `python/requirements.txt`, `sketch/sketch.ino`, `sketch/sketch.yaml`, `models/class_mapping.json`, `models/requirements-unoq-cp313.lock`, `models/unoq_runtime_manifest.json`, and the 4,126,810-byte `.tflite` model must be present. `data/` must contain no prior event database.
3. Select the connected UNO Q and press **Run**. App Lab should resolve the pinned Python requirement, deploy the Linux app, compile/flash the STM32 sketch, and start them together.
4. Expected MCU indication after heartbeats begin: LED4 green. Before Linux/Bridge health is established, LED4 may blink red. LED3 stays off until a confirmed event.
5. In the App Lab monitor, retain the line beginning `CueLoop runtime:`. Expected values for the audited runner family are Python 3.13, an AArch64/ARM64 machine identity, and `ai-edge-litert=2.2.0`; record the actual libc rather than assuming it. Then look for the dashboard/UDP startup text and no model checksum/tensor error. Record all errors verbatim without credentials.
6. Open `http://<UNO-Q-IP>:8080/` from the Windows browser. Expected: dashboard loads, privacy says local/no recordings, CuePod connection initially shows disconnected, and cue-output diagnostics become connected after Bridge heartbeats.
7. Only after a complete manual run passes, optionally use the arrow beside **Run** to enable **Run at startup**. Do not enable autostart during early debugging.

The Ubuntu audit proves the complete hash-locked wheel set exists for the officially documented Python 3.13/Linux ARM64 tuple; it does not prove the received image can load it. If the pinned set cannot install or import on the actual UNO Q image, record the complete resolver/Python/machine/libc output. Do not switch to synthetic inference or silently change a pin; that is a material model/runtime decision.

## C. Flash XIAO ESP32S3 Sense from source (recommended)

1. Install Arduino IDE 2 on Windows from Arduino's official site.
2. Add Espressif's official Boards Manager URL:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. In Boards Manager install **esp32 by Espressif Systems 3.3.11**. Do not use “latest” without re-running the repository builds.
4. Open `firmware\xiao_cuepod\xiao_cuepod.ino`. Confirm the companion `.h` files are in the same folder.
5. Select **XIAO_ESP32S3** and its newly appeared COM port. Keep default board options; the build does not require PSRAM.
6. Keep the LiPo detached. Click Verify, then Upload. Record the IDE version, core version, COM port, compile memory report, and upload success.
7. If no port appears or upload fails, follow Seeed's official bootloader method: hold BOOT, connect USB, then release BOOT; alternatively hold BOOT and tap RESET. Avoid pressing tools into nearby components.
8. Open Serial Monitor at 115200 baud with LF line ending. Expected first output includes `CUELOOP_CUEPOD_READY` and `STATUS` responds.

Optional Arduino CLI equivalent after installing Arduino CLI/core on Windows:

```powershell
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 firmware\xiao_cuepod
arduino-cli board list
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 --port COM5 firmware\xiao_cuepod
```

Replace `COM5` with the detected port. Recompiling source on Windows is safer than guessing esptool offsets from one `.bin`; the retained Ubuntu artifacts are evidence/recovery inputs, not an instruction to flash `xiao_cuepod.ino.bin` at address zero.

## D. Configure CuePod without committing secrets

In Serial Monitor, send tab-separated commands; each `<TAB>` below means one actual Tab character:

```text
SET_WIFI<TAB>your-private-ssid<TAB>your-password
SET_RECEIVER<TAB>UNO-Q-IP<TAB>57321
SET_POD_ID<TAB>0xC0E10001
POWER<TAB>USB
TEST<TAB>ON
STATUS
```

Expected: password is never echoed; Wi-Fi becomes connected; sent frames increase; after the UNO Q receiver answers, valid ACKs increase and `reachable=yes`. Use a 2.4 GHz-capable private LAN with client-to-client traffic allowed. Switch `TEST OFF` only after deterministic transport and dashboard cue behavior pass.

## E. Expected first integrated observations

1. `TEST ON`: dashboard changes to connected/test-tone or simulated-source labeling as defined, packet counters advance, and a deterministic cue can be exercised without claiming acoustic accuracy.
2. Disconnect/stop UNO Q app: within about five seconds CuePod reports receiver timeout/reachability false.
3. Restart UNO Q app: valid ACKs resume and stream-restart diagnostics increment without rebooting the CuePod.
4. `TEST OFF`: microphone mode streams, but no recognition-quality claim is allowed until the physical audio matrix is completed.
5. Dashboard mute changes LED4 to blue and clears LED3. Acknowledgement clears the current cue; optional D4 button is tested only if actually wired.

Official references: [UNO Q user manual](https://github.com/arduino/docs-content/blob/main/content/hardware/02.uno/boards/uno-q/tutorials/01.user-manual/content.md), [App Lab documentation](https://docs.arduino.cc/software/app-lab/), [Seeed XIAO ESP32S3 guide](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/), and [Arduino CLI upload reference](https://arduino.github.io/arduino-cli/dev/commands/arduino-cli_upload/).
