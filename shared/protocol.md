# CueLoop Protocol v1

CueLoop V1 uses one length-framed packet per 20 ms of 16 kHz mono signed 16-bit PCM over a persistent TCP connection. At 320 samples/frame the PCM payload is 640 bytes, the CueLoop packet is 684 bytes, and the two-byte stream prefix makes each TCP application frame 686 bytes. The stream consumes approximately 274.4 kbit/s before TCP/IP/link overhead.

V1 is intended only for a trusted private LAN. TCP supplies ordered reliable bytes but no application identity or confidentiality. CRCs detect accidental corruption; they do not provide authentication or integrity against an attacker. Never expose TCP port 57321 to the internet or use the prototype on public Wi-Fi.

## Stream framing

Every CueLoop packet is prefixed by a two-byte unsigned big-endian payload length. The length excludes the prefix and must be from 1 through 1324 bytes. A normal audio frame has prefix value 684; a receiver acknowledgement has prefix value 24. Invalid lengths terminate the connection. The next connection begins at a new frame boundary.

## Header

All multi-byte header integers are unsigned network byte order unless noted. PCM payload samples are signed little-endian int16.

| Offset | Size | Field | Meaning |
|---:|---:|---|---|
| 0 | 4 | magic | ASCII `CLP1` |
| 4 | 1 | version | `1` |
| 5 | 1 | message type | `1` = PCM16 audio |
| 6 | 2 | flags | Bit field below |
| 8 | 4 | pod ID | Locally assigned stable identifier; not a MAC address |
| 12 | 4 | sequence | Increments per frame modulo 2^32 |
| 16 | 8 | sample clock | Count of captured samples since pod stream start |
| 24 | 4 | capture ms | Pod uptime milliseconds, modulo 2^32 |
| 28 | 2 | sample rate | V1 requires 16000 |
| 30 | 2 | sample count | Nominal 320; protocol maximum 640 |
| 32 | 2 | battery mV | Zero when unavailable; valid only with flag |
| 34 | 1 | RSSI dBm | Signed int8; zero when unavailable |
| 35 | 1 | reserved | Must be zero |
| 36 | 4 | payload CRC32 | IEEE/zlib CRC32 over PCM bytes |
| 40 | 4 | header CRC32 | CRC32 over bytes 0–39 |
| 44 | N | PCM payload | `sample_count × 2` bytes |

Flags: bit 0 simulated source, bit 1 test tone, bit 2 USB powered, bit 3 battery value valid, bit 4 stream restart. Unknown bits cause a strict decoder rejection.

## Receiver heartbeat acknowledgement

Once per second, after validating an audio packet, the receiver returns a framed 24-byte acknowledgement on the same TCP connection. This lets the pod distinguish “Wi-Fi associated” from “CueLoop receiver reachable” without cloud state.

| Offset | Size | Field | Meaning |
|---:|---:|---|---|
| 0 | 4 | magic | ASCII `CLP1` |
| 4 | 1 | version | `1` |
| 5 | 1 | message type | `2` = receiver acknowledgement |
| 6 | 2 | flags | Must be zero |
| 8 | 4 | pod ID | Must match the active pod |
| 12 | 4 | last sequence | Most recent audio sequence observed for this reply |
| 16 | 4 | receiver uptime ms | Receiver-process uptime modulo 2^32 |
| 20 | 4 | CRC32 | IEEE/zlib CRC32 over bytes 0–19 |

The pod treats a valid matching acknowledgement as reachability evidence. After five seconds of enabled streaming without one it raises a diagnostic receiver timeout, closes the connection, reconnects with bounded backoff, and marks the next successfully delivered stream as restarted. The acknowledgement does not prove identity and is not a cryptographic authentication tag.

## Ordering, restart, and clock behavior

- TCP preserves byte order within a connection. The receiver still keys state by pod ID and releases frames through a bounded sequence buffer so simulator-injected faults, sender-side drops, and reconnect boundaries remain explicit.
- Duplicates and packets older than the current release point are discarded and counted.
- A sequence gap is held only to the configured bounded depth, then emitted as the expected number of zero samples and counted. TCP retransmission can increase latency, so the pod uses bounded connect/write timeouts instead of waiting indefinitely at the application layer.
- The first packet after a firmware/network stream reset sets `STREAM_RESTART`; the receiver clears pending reorder/audio state and accepts the new sequence/sample clock.
- `capture_ms` is pod uptime, not synchronized wall time. V1 estimates interarrival jitter and decision-pipeline delay; it does not claim one-way network latency without a measured clock-offset exchange.
- A sample-rate or nominal-frame-size change resets the stream and reports a diagnostic mismatch in V1.

## Privacy consequence

The payload exists only in pod/receiver memory and on the trusted LAN. It has no filename, storage command, or replay endpoint in the production receiver. Structured event metadata is a separate schema.
