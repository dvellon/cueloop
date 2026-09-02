# Power and bandwidth analysis

Every value below is labeled. Manufacturer figures are not measurements of CueLoop firmware.

## Power domains

CueLoop V1 has two independent power domains:

1. The UNO Q uses its documented USB-C power path. Arduino specifies a 5 V supply with up to 3 A capability; the exact ordered supply/hub must be inventoried before use. CueLoop does not power the CuePod or any actuator from the UNO Q.
2. The CuePod uses XIAO USB-C during development or one protected 3.7 V nominal LiPo on the XIAO battery pads. The XIAO's onboard management circuit owns power selection/charging. Never apply a battery to the 5 V pin.

The domains communicate only by Wi-Fi. There is no ground loop or cross-power cable.

## CuePod estimate

Known manufacturer data:

- Battery: 500 mAh at 3.7 V nominal, approximately 1.9 Wh; protected; 4.2 V full; Adafruit says CC/CV charge at 500 mA or less.
- Seeed's current XIAO ESP32S3 Series table reports representative Sense workloads around 64.5 mA average for microphone recording plus SD and 110 mA with Wi-Fi active on the expansion-board configuration. Those are separate manufacturer workloads, not additive CueLoop measurements.
- The implemented workload continuously captures PDM and transmits Wi-Fi; camera and SD are unused.

Planning range (**estimated**): 110–170 mA average. With an 80% usable-capacity planning factor:

| Assumed average current | Ideal `500 mAh / I` | 80%-capacity planning runtime |
|---:|---:|---:|
| 110 mA | 4.55 h | 3.64 h |
| 140 mA | 3.57 h | 2.86 h |
| 170 mA | 2.94 h | 2.35 h |

Use **about 2.4–3.6 hours estimated**, never “measured battery life,” until the physical CuePod runs a timed discharge test. Wi-Fi retries, cell age, protection cutoff, temperature, regulator efficiency, and signal strength can materially change it.

The current Seeed page clearly documents battery power management and pad polarity but its charge-current table formatting is ambiguous across the base, Sense, and Plus variants. Do not publish a CuePod charge-time claim until the received PCB revision is identified and charge current is measured or unambiguously traced from its matching schematic.

## Network bandwidth

Protocol v1 sends 50 audio datagrams per second:

| Layer | Arithmetic | Rate |
|---|---:|---:|
| PCM payload only | 640 B × 50 | 32,000 B/s = 256.0 kbit/s |
| CueLoop UDP payload | 684 B × 50 | 34,200 B/s = 273.6 kbit/s |
| IPv4 + UDP | (684 + 20 + 8) B × 50 | 35,600 B/s = 284.8 kbit/s |
| Receiver ACK | 24 B once/s, plus headers | negligible |

802.11 framing, acknowledgements, contention, retries, and link-layer security add overhead, so measured airtime and interface throughput will be higher. The application stays well below the nominal capacity of a healthy private 2.4 GHz Wi-Fi link, but physical loss/jitter testing remains required.

## Measurement plan

### Safe first-pass power evidence

1. Run the XIAO from USB with the battery detached. Confirm test tone, microphone mode, Wi-Fi, and temperature before battery use.
2. For battery runtime, fully charge under supervision, disconnect USB, record start/end time and firmware counters, and stop at normal protected shutdown. This avoids opening the battery path with a meter.
3. If current is required, prefer a suitable inline USB power meter for USB mode. It is not in the confirmed inventory.

### Optional series-current test with the AstroAI meter

Only attempt this if the meter manual, fuse rating, and lead jacks are understood and a protected break-out/test harness exists. Do not improvise by holding loose probes against LiPo connector contacts.

1. Disconnect USB and battery first.
2. Put the black lead in COM and red lead in the meter's documented high-current jack; select DC current at the highest safe range.
3. Insert the meter **in series** in a protected positive-lead test harness: battery positive → meter → CuePod positive. Keep battery negative directly connected.
4. Check polarity and insulated connections before mating the battery, then power briefly and step down range only if the reading and fuse limit make that safe.
5. Disconnect battery before moving a lead or changing the circuit. Return the red lead to the voltage/ohms jack immediately afterward.

Never place an ammeter directly across battery positive and negative; that is a short circuit.

## Required result fields

Record average/peak method, meter/tool identity, cell voltage, firmware mode, Wi-Fi RSSI, duration, temperature observation, shutdown behavior, and evidence tier under H-307 through H-310 in root `HARDWARE_TESTS.md`; copy reviewed summaries to `HARDWARE_RESULTS.md`.
