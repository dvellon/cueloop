# Privacy model

## Promise

CueLoop turns transient acoustic evidence into local event metadata. It does not need a cloud account, speech transcript, speaker identity, or default recording archive.

## Data inventory

| Data | Location | Retention | User control |
|---|---|---|---|
| PCM audio frames | Pod RAM, LAN packets, UNO Q bounded RAM | Milliseconds to active model-window duration; released after inference | Monitoring on/off; no default replay |
| Model scores | UNO Q RAM | Only while temporal decision is active | Threshold/class configuration |
| Event record | UNO Q local store | Configurable; default rolling metadata history | Acknowledge/dismiss; clear history |
| Feedback | UNO Q local store | Until cleared | Confirm/dismiss and delete |
| Diagnostics | UNO Q memory/local metadata | Bounded counters/history | Diagnostics view/reset |
| Wi-Fi secret | Ignored local pod configuration | Until changed by owner | Reflash/reprovision; never Git |

Event records contain event ID, pod ID/location label, class, confidence, timestamps, decision state, priority, latency/loss snapshot, and user action. They do not contain raw audio, transcript, or speaker identity.

## Threats and controls

- **LAN eavesdropping:** V1 raw UDP can be observed by a device already on the same network. Use a trusted isolated LAN, avoid guest/public networks, never port-forward. V2 must evaluate authenticated encryption.
- **Accidental retention:** audio buffers are bounded memory objects without a file-writing interface; diagnostic capture is a separate explicit tool, ignored by Git, visibly indicated, and off by default.
- **Sensitive metadata:** location labels should be generic (“workshop”), the dashboard should remain LAN-only, and history can be cleared.
- **Unauthorized control:** bind to the intended interface, use local-network firewall rules, and treat V1 API controls as trusted-LAN only until authentication is implemented.
- **Model overreach:** no speech-to-text, emotion inference, identity inference, or conversational analytics.
- **Submission leakage:** use owned/licensed demonstration sounds and imagery; remove IP addresses, SSIDs, faces, private locations, and serial numbers from public assets.

## Verifiable invariants

- No production path calls an audio-file writer.
- No cloud SDK or telemetry endpoint is a runtime dependency.
- Ring/jitter buffers enforce maximum sizes.
- API event schemas contain no audio field.
- Tests search persisted records for audio payloads and validate buffer eviction.

## Honest limitation

“Local-first” does not mean “cryptographically private” on V1: PCM travels over a trusted local Wi-Fi network without application-layer encryption. That is acceptable for the controlled prototype only when disclosed and demonstrated on a private network.
