# System and protocol diagrams

## Wireless system block diagram

```mermaid
flowchart LR
  MIC[Integrated PDM mic] --> XIAO[XIAO ESP32S3 Sense\n16 kHz PCM + framing]
  BAT[Protected 1-cell LiPo] --> XIAO
  XIAO -->|Wi-Fi UDP 57321\ntrusted LAN| RX[UNO Q Linux receiver]
  RX --> MODEL[YAMNet + class map]
  MODEL --> POLICY[temporal confirmation\npriority + cooldown]
  POLICY --> UI[local dashboard :8080]
  POLICY -->|Bridge compact RPC| MCU[UNO Q STM32]
  MCU --> LED3[LED3 event cue]
  MCU --> LED4[LED4 health/mute]
  BTN[optional D4 button] --> MCU
  MCU -->|Bridge acknowledgement| POLICY
```

## Linux/MCU responsibility diagram

```mermaid
flowchart TB
  subgraph Linux[UNO Q Qualcomm / Debian]
    UDP[UDP + jitter/loss]
    AI[inference + temporal policy]
    DB[bounded event/feedback SQLite]
    WEB[REST + dashboard]
  end
  subgraph MCU[UNO Q STM32U585 / Zephyr]
    RPC[RPC validation + heartbeat]
    TIME[nonblocking cue timing]
    IO[LEDs + optional button/driver]
  end
  UDP --> AI
  AI --> DB
  AI --> WEB
  AI -->|cue / clear / mute / heartbeat| RPC
  RPC --> TIME --> IO
  IO -->|ack / status| AI
```

Linux owns uncertain/high-level work; the MCU owns bounded physical timing. If Bridge fails, inference/dashboard remain alive and report degradation. If the MCU restarts, a lower uptime status triggers mute/current-cue resynchronization.

## Power path diagram

```mermaid
flowchart LR
  USBX[XIAO USB-C 5 V\ndevelopment/charge] --> PMIC[XIAO onboard\npower management]
  LIPO[Adafruit 1578\n3.7 V protected LiPo] -->|JST-PH + verified pigtail\nBAT+ / BAT-| PMIC
  PMIC --> POD[XIAO + Sense microphone]

  USBQ[Approved UNO Q USB-C path\n5 V, supply capability up to 3 A] --> UNO[UNO Q MPU + MCU]

  POD -. Wi-Fi only; no shared power .-> UNO
```

## Battery connection diagram

```mermaid
flowchart LR
  B1P[B1 protected LiPo +] --> J1P[J1 measured + lead]
  J1P --> U1P[XIAO BAT+\nfarther from USB-C]
  B1N[B1 protected LiPo -] --> J1N[J1 measured - lead]
  J1N --> U1N[XIAO BAT-\nclosest to USB-C]
```

The battery is detached while J1 is soldered. Connector orientation and voltage—not red/black insulation—determine polarity.

## Network protocol sequence

```mermaid
sequenceDiagram
  participant Pod as XIAO CuePod :57322
  participant Linux as UNO Q Linux :57321
  participant Model as Local model/policy
  participant MCU as UNO Q STM32
  participant UI as Browser :8080
  loop every 20 ms
    Pod->>Linux: 684-byte PCM v1 frame + CRC + sequence
  end
  Linux-->>Pod: 24-byte CRC ACK, at most once/s
  Linux->>Model: normalized bounded window
  Model-->>Linux: class scores + inference time
  Note over Linux: require temporal evidence; apply cooldown/mute
  Linux->>MCU: cueloop/cue(event, class, priority, permille)
  MCU-->>Linux: accepted boolean
  Linux-->>UI: event metadata/status JSON
  UI->>Linux: acknowledge / dismiss / mute
  Linux->>MCU: clear or mute
  MCU-->>Linux: button ack and periodic bounded status
```

CRC detects accidental corruption; it does not authenticate or encrypt. Do not deploy V1 on an untrusted network.
