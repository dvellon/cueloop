# Official requirements and source check

**Checked:** September 1, 2026 (America/New_York)  
**Policy:** use primary organizer/manufacturer sources; recheck before submission because organizers reserve the right to change dates.

## Competition 1: Invent the Future with Arduino UNO Q and App Lab

Official Hackster contest pages confirm:

- Submission closes **September 13, 2026 at 11:59 PM PDT**.
- The project must use Arduino UNO Q, address a real-world challenge with AI, be in English, and include a name, short description, cover image, BOM, complete instructions, images, and relevant source resources such as code, schematics, and CAD.
- Judging is documentation 30, BOM 20, schematics 15, code/contribution 15, creativity 20.
- Best Social Impact and Best in Show are active prize categories.
- The entry must be original and cannot already have been selected as a winner in another Hackster contest.
- Licensed third-party material must be properly permitted and attributed.

Primary sources:

- [Contest overview](https://www.hackster.io/contests/invent-the-future-with-arduino-uno-q-and-app-lab)
- [Specific rules](https://www.hackster.io/contests/invent-the-future-with-arduino-uno-q-and-app-lab/rules)
- [Official FAQ](https://www.hackster.io/contests/invent-the-future-with-arduino-uno-q-and-app-lab/faq)

## Competition 2: Build the Autodesk University 2027 Product

Official Hackster pages and the organizer-authored guide confirm:

- Hardware applications close **September 7, 2026 at 11:59 PM PDT**.
- Final entries close **December 20, 2026 at 11:59 PM PST**.
- The application must answer all five application prompts and link to a started Hackster project with a name, elevator pitch, cover render/image, beginning BOM, story, UNO Q, Autodesk Fusion, and a preliminary Fusion design/dataset `.f3d` attachment.
- The product must be a compact smart accessory that can be worn, attached, clipped, or carried; it should be handheld, legally carry-on safe, useful beyond the conference, and useful to Autodesk customers.
- The final entry must use UNO Q and Autodesk Fusion, include its `.f3d`, a PCBWay enclosure, video/photos of the prototype in action, BOM, schematics, code, and English documentation.
- Judging is creativity 30, documentation 20, BOM 20, schematics 10, Fusion 10, code/contribution 10.
- The Best AU 2027 Product Concept may be manufactured in approximately 750 units, making manufacturability and serviceability central.

Primary sources:

- [Contest overview](https://www.hackster.io/contests/autodesk-university-2027-product)
- [Specific rules](https://www.hackster.io/contests/autodesk-university-2027-product/rules)
- [Organizer project/application guide](https://www.hackster.io/jessalyn/project-guide-build-the-autodesk-university-2027-product-b9aa9f)

### Official-source discrepancy

The Autodesk specific-rules and FAQ pages contain visible, unfilled boilerplate such as `[sponsor name - platform]`, `[featured technology]`, and example categories unrelated to this contest. The dates, documentation requirements, and rubric are populated. CueLoop follows the more specific contest overview and organizer project guide: Arduino UNO Q, Autodesk Fusion, PCBWay, portable accessory, project link, preliminary `.f3d`, BOM, render, and full application answers. A screenshot/PDF of the live rules should be retained by the entrant near submission time if the placeholders remain.

## UNO Q and App Lab technical facts

Arduino's current product and App Lab documentation confirm:

- UNO Q combines a Qualcomm Dragonwing QRB2210 MPU running Debian Linux with an STM32U585 MCU running Arduino sketches over Zephyr OS.
- The specified 4 GB / 32 GB unit is SKU ABX00173; the brief's configuration is compatible with the 4 GB recommendation for SBC/App Lab workloads.
- App Lab Apps use a mandatory `app.yaml`, mandatory `python/main.py`, optional `python/requirements.txt`, and optional `sketch/sketch.ino` plus `sketch/sketch.yaml`.
- Optional Bricks run on Linux alongside the Python app.
- Linux and MCU communicate through Arduino Bridge RPC. Supported patterns include Python `Bridge.call()`/`Bridge.notify()` and MCU `Bridge.provide()`/`Bridge.provide_safe()` after `Bridge.begin()`.
- Arduino documents the advanced router socket as `/var/run/arduino-router.sock`; CueLoop uses the supported App Lab helper instead of binding directly for V1.

Primary sources:

- [UNO Q product documentation](https://docs.arduino.cc/hardware/uno-q)
- [Arduino App Lab documentation](https://docs.arduino.cc/software/app-lab/)
- [Official App specification](https://github.com/arduino/arduino-app-cli/blob/main/docs/app-specification.md)
- [Official UNO Q user manual source](https://github.com/arduino/docs-content/blob/main/content/hardware/02.uno/boards/uno-q/tutorials/01.user-manual/content.md)
- [Official App Lab examples](https://github.com/arduino/app-bricks-examples)

## XIAO microphone facts

Seeed's official microphone guide documents the Sense expansion board microphone as PDM input at 16 kHz mono/16-bit, with PDM clock on GPIO42 and data on GPIO41. For current Arduino-ESP32 3.x the documented API is `ESP_I2S.h`, `I2S.setPinsPdmRx(42, 41)`, and `I2S.begin(I2S_MODE_PDM_RX, 16000, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO)`. This must still be compiled and verified on the received hardware.

Primary source: [Seeed XIAO ESP32S3 Sense microphone guide](https://wiki.seeedstudio.com/xiao_esp32s3_sense_mic/)
