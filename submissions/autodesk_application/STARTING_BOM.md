# CueLoop Bridge starting BOM

Prices are manufacturer list prices checked September 1, 2026 and may differ by region, tax, shipping, or the entrant's invoice. “TBD after inventory/test” is deliberate; optional output hardware is not treated as essential until the Arduino packing list and power tests are available.

## Confirmed core and application items

| Qty | Item | Manufacturer / part | Purpose | Status | Reference price |
|---:|---|---|---|---|---:|
| 1 | Arduino UNO Q 4 GB / 32 GB | Arduino ABX00173 | Linux edge AI, local UI, STM32 physical control | Ordered | €82.90, Arduino EU store |
| 1 | XIAO ESP32S3 Sense | Seeed Studio 113991115 | Detachable Wi-Fi PDM microphone pod | Ordered | US$13.99, Seeed list price |
| 1 | Protected 3.7 V 500 mAh LiPo | Adafruit 1578 | CuePod battery; 29 × 36 × 4.75 mm | Ordered | US$7.95 |
| 1 | JST-PH 2-pin female pigtail, 100 mm | Adafruit 261 | Replaceable battery interconnect only after polarity checks | Ordered | US$0.75 |
| 1 | Autodesk Fusion | Autodesk | Mechanical assembly, Electronics, drawings, DFM | Application software | Competition license / trial |
| 1 | PCBWay rapid prototyping allocation | PCBWay | V2 enclosure and possible carrier fabrication | Application resource | Up to US$300 for selected recipients |

## Confirmed development infrastructure

| Qty | Item | Manufacturer / part | Purpose | Product BOM? |
|---:|---|---|---|---|
| 1 | Temperature-controlled soldering station kit | YIHUA 926 III | Assembly; never used with LiPo connected | No; tool |
| 1 | Digital multimeter | AstroAI AM33D | Polarity, continuity, voltage, and current procedures | No; tool |
| 1 | UNO Q USB-C power/connectivity | Exact item from Arduino order pending inventory | Development power, flashing, SBC use | No; infrastructure |
| TBD | Arduino Modulino/Qwiic accessories | Exact packing list pending | Evaluate available human output; none assumed essential | Optional |

## V2 development candidates—not yet purchased or frozen

| Item | Selection gate | Reason |
|---|---|---|
| Low-profile haptic motor plus protected driver | Select after voltage/current and cue testing | Eyes-free portable alerts |
| Diffused RGB light/light-pipe source | Prefer confirmed Arduino accessory if suitable | High-visibility, non-color-only cue language |
| Receiver portable power and charge/power-path subsystem | Select only after UNO Q load and form-factor measurement | Required for fully portable V2; must follow board power rules |
| M2 heat-set inserts/screws or thread-forming alternatives | Decide from PCBWay process and assembly-cycle test | Serviceable enclosure fastening |
| Magnet pair plus steel keeper, or mechanical latch | Confirm carry-on safety, retention, interference, and assembly | Pod dock retention; magnets are not assumed final |
| Custom interconnect/carrier PCB | Build only if wiring/integration test justifies it | Reduce assembly time and improve reliability |
| PCBWay printed enclosure | Material/process selected after fit prototype | Required final contest deliverable |

## Manufacturer geometry used for preliminary CAD

- UNO Q board outline: 68.85 × 53.34 mm; height/connector envelopes require physical confirmation.
- XIAO ESP32S3 Sense with expansion board: 21 × 17.8 × 15 mm; camera is not used and the received stack must be inspected.
- LiPo: 29 × 36 × 4.75 mm, 102 mm lead, 10.5 g; protection/cable placement needs physical confirmation.

Sources: official Arduino store/product documentation, Seeed product sheet 113991115, Adafruit product pages 1578 and 261, and the official Autodesk contest overview.

