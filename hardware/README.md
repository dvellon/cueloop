# CueLoop V1 hardware package

This folder is the source of truth for the physical V1 build. It deliberately separates confirmed manufacturer facts, development-computer build evidence, estimates, and observations that still require the received hardware.

- `BOM.md` defines the minimum working product, optional inventory-gated additions, tools, and the distinct V2 development BOM.
- `WIRING.md` defines every external V1 connection and pin assignment.
- `POWER.md` contains power paths, bandwidth arithmetic, runtime estimates, and the measurement plan.
- `ASSEMBLY.md` gives the battery-safe assembly sequence.
- `DIAGRAMS.md` contains the wireless/system, processor-responsibility, power, and protocol views.
- `schematics/cueloop_v1.netlist.json` is the machine-readable connectivity source.
- `schematics/cueloop_v1.svg` is the human-readable schematic export.

No Qwiic cable is used by the minimum CuePod. No wire connects the CuePod to the UNO Q during use. The only inter-device path is trusted-LAN Wi-Fi.

Official source facts checked September 2, 2026:

- [Arduino UNO Q 4 GB product page](https://store.arduino.cc/products/uno-q-4gb)
- [Arduino UNO Q datasheet](https://docs.arduino.cc/resources/datasheets/ABX00162-ABX00173-datasheet.pdf)
- [Seeed XIAO ESP32S3 Sense product page](https://www.seeedstudio.com/XIAO-ESP32S3-Sense-p-5639.html)
- [Seeed XIAO ESP32S3 getting-started and battery guide](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)
- [Adafruit protected 500 mAh LiPo](https://www.adafruit.com/product/1578)
- [Adafruit JST-PH female pigtail](https://www.adafruit.com/product/261)
