# Bill of materials

**Price check:** September 2, 2026. Manufacturer list prices exclude shipping and may vary by region, tax, promotion, and the actual invoice. EUR and USD are intentionally not combined using a transient exchange rate.

## Minimum working V1

This is the complete electrical BOM for the implemented minimum demo. It uses the UNO Q's onboard MCU RGB LEDs as the physical cue and dashboard controls for acknowledge/mute, so it does not require a Modulino, external buzzer, motor, button, Qwiic cable, or custom PCB.

| Ref | Qty | Item | Manufacturer / part | Purpose | Status | Reference price |
|---|---:|---|---|---|---|---:|
| U1 | 1 | Arduino UNO Q 4 GB RAM / 32 GB eMMC | Arduino ABX00173 | Linux inference/dashboard plus STM32 deterministic visual output | Ordered; markings pending | €82.90 incl. VAT, Arduino EU store |
| U2/MIC1 | 1 | XIAO ESP32S3 Sense, unsoldered | Seeed Studio 113991115 | ESP32-S3, Sense expansion PDM microphone, antenna, USB-C, Wi-Fi, battery management | Ordered; revision pending | US$13.90 |
| B1 | 1 | Protected LiPo, 3.7 V nominal, 500 mAh, JST-PH lead | Adafruit product 1578 | Detachable CuePod power; 29 × 36 × 4.75 mm, 10.5 g | Ordered; inspect before use | US$7.95 |
| J1 | 1 | JST-PH 2-pin female pigtail, 100 mm, 26 AWG | Adafruit product 261 | Replaceable battery interconnect soldered only at the board end, with battery detached | Ordered; mating/polarity pending | US$0.75 |
| PS1 | 1 | USB-C power/data path for UNO Q | Exact Arduino-order cable/supply or PD hub: packing list pending | Development power, App Lab deployment, board connectivity | Ordered infrastructure; exact MPN/price pending invoice | Inventory gate |
| C1 | 1 | USB-C data cable for XIAO | Existing known-good data cable | Initial flash, serial configuration, USB development power | Existing infrastructure | Not costed |
| LAN1 | 1 | Private 2.4 GHz Wi-Fi LAN | Existing router/access point | Local CuePod-to-UNO Q transport; no internet runtime dependency | Existing infrastructure | Not costed |

Core electronics subtotal: **€82.90 plus US$22.60**, before the already ordered/inventory-pending power path, tax differences, and shipping.

The Sense kit normally includes its antenna and microphone expansion board; inventory them as separate line items if the received packaging does. The camera is not used. Do not add headers simply because they are available.

## Mechanical completion items

The preliminary CAD produces a CuePod and receiver enclosure, but exact printable material, fasteners, and quantities cannot truthfully be frozen until the physical boards are measured and the models are sliced. Record the selected spool manufacturer/material/color, sliced grams, support grams, fastener MPN, and actual cost here before the competition's final BOM is published.

| Ref | Planned item | Current specification | Freeze gate |
|---|---|---|---|
| M1 | CuePod base/lid | 2.0 mm nominal wall, protected mic opening, USB access, battery restraint | Caliper validation and fit print |
| M2 | UNO Q receiver base/lid | UNO outline plus measured connector/cable envelope and visible LED path | Accessory inventory and fit print |
| F1 | Service fasteners | M2 strategy, 2.4 mm clearance and 5.5 mm bosses in CAD | Choose thread-forming screw or insert after print-process test |
| I1 | Battery insulation/restraint | Nonconductive, noncompressive, removable; no adhesive on damaged cell | Select after cell/pigtail placement test |

These are not hidden omissions: the electrical bench prototype remains complete without an enclosure, but battery operation is allowed only when the cell and leads are safely restrained away from sharp or conductive parts.

## Optional V1 additions—not required by firmware

| Ref | Item | Connection | Selection rule |
|---|---|---|---|
| S1 | Normally-open momentary acknowledgement button | UNO Q D4 to GND; `INPUT_PULLUP` | Use only after inventory identifies a rated, mountable part; dashboard acknowledgement is the fallback |
| H1 | Haptic motor plus transistor/driver, flyback/suppression as required | Disabled by default in `cue_controller_hardware.local.h` | Never drive a motor from a GPIO; select from measured voltage/current and driver datasheet |
| BZ1 | Active buzzer plus appropriate driver | Disabled by default | Select only if accessible cue testing justifies sound; keep level conservative |
| MOD1 | Arduino Modulino output | Qwiic/I2C only if deliberately supported in a later firmware change | Inventory first; a Qwiic cable is never a battery cable |

## Tools and development infrastructure—not product BOM

| Qty | Item | Identity | Use |
|---:|---|---|---|
| 1 | Temperature-controlled soldering station kit | YIHUA 926 III | Pigtail-to-board work with USB and battery disconnected |
| 1 | Digital multimeter | AstroAI AM33D | Voltage, polarity, continuity/resistance, optional guarded current test |
| 1 | Windows 10/11 64-bit laptop | User equipment | Arduino App Lab, flashing, serial terminal, browser |
| 1 | Ubuntu build machine | User equipment | Reproducible host tests and Arduino CLI builds |

## V2 CueLoop Bridge development BOM

V2 is intentionally not an identical contest resubmission. Its BOM is a gated product-development set, not a claim that unselected parts were built.

| Subsystem | Required V2 selection | Gate/evidence before freezing |
|---|---|---|
| Portable receiver power | USB-PD battery/charge/power-path sized for UNO Q load | Measure UNO Q app idle/peak/current and thermal behavior first |
| Haptic output | Coin/LRA actuator, protected driver, connector | Measure cue detectability, current, mounting noise, and skin-contact comfort |
| Visual output | Diffused high-visibility RGB/light pipe | Test daylight visibility without color-only semantics |
| Tactile controls | Acknowledge, mute, priority controls | Glove/eyes-free usability and debounce testing |
| Dock | Mechanical latch or qualified magnets/keeper | Retention, interference, carry-on and assembly-cycle tests |
| Interconnect | Fusion Electronics carrier PCB if justified | Only after prototype wiring and assembly-time study |
| Enclosure | PCBWay-compatible serviceable process/material | Fit, thermal, drop, clip, dock, draft and fastening validation |
| Fasteners | Production-intent screws/inserts | Torque, boss, repeated-service, and supplier availability tests |

## Source notes

- Arduino lists ABX00173 at €82.90 on the checked regional store page and specifies USB-C 5 V up to 3 A / VIN 7–24 V in current UNO Q documentation.
- Seeed lists 113991115 at US$13.90 and documents the integrated digital microphone, Wi-Fi, battery management, and 21 × 17.8 × 15 mm Sense envelope.
- Adafruit lists product 1578 at US$7.95 and product 261 at US$0.75. Product 1578 is protected but still requires correct CC/CV charging, inspection, and supervision.
- The actual order invoice—not a web price—wins when the final submission cost table is frozen.
