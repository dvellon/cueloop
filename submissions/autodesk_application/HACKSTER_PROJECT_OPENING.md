# CueLoop Bridge: Carry awareness, not recordings

## Elevator pitch

CueLoop Bridge is a private, pocketable acoustic awareness bridge. Leave its detachable CuePod near a door, timer, collaborator, or fabrication process; carry the Arduino UNO Q receiver; and get a calm visual or haptic cue only when local edge AI has enough evidence to interrupt you.

## The moment that inspired it

A fabrication workflow rarely ends where a person is working. A designer starts a print and moves to CAD. A maker wears hearing protection while a test rig runs. Someone joins a focused call while a timer or door is in another room. The important sound still exists, but the person either stays close, checks repeatedly, makes the alert louder, or installs a camera/smart speaker that observes far more than the task requires.

CueLoop Bridge asks a narrower question: **what deserves your attention right now?**

## The product

The system separates sensing from interruption. A tiny battery-powered CuePod can clip near the event source. The portable receiver can clip to a belt or bag, hang from a lanyard, or stand on a desk; the pod docks into it when both are carried. A wide diffused light and distinct haptic patterns let a user understand a cue without reading a screen or increasing the volume of the environment.

The initial event vocabulary is intentionally small: knocks, beeps/alarms, dog barks, and calls for attention, with unknown/background treated as suppression outcomes. Later creator modes can focus on printer or machine completion sounds. Supporting four classes honestly is more valuable than advertising twenty unreliable ones.

## More than a sound classifier

Audio models are uncertain, and rooms make them harder: doors attenuate high frequencies, television creates confusable speech, and a single model window can spike. CueLoop therefore uses two layers. A local model estimates candidate events; then a confidence-aware temporal engine accumulates evidence, applies user priority, and decides whether to keep observing, open a confirmation window, alert, or cool down. A user can acknowledge, dismiss, or mute a cue. That feedback becomes local evaluation metadata for threshold tuning. Raw audio is discarded after inference by default.

This behavior is central to the product. The goal is not to flash every label—it is to earn an interruption.

## Why Arduino UNO Q

The receiver needs Linux-class networking, model inference, structured storage, and a polished local web experience, but its physical cue and acknowledgement control should remain deterministic. Arduino UNO Q puts both roles on one compact board. The Qualcomm Dragonwing MPU runs Debian, receives the pod stream, performs local inference, applies event policy, and serves the interface. Arduino Bridge sends compact event commands to the STM32U585 MCU, which owns LED/haptic timing, button input, and health indication.

That split is visible and testable. If the dashboard is busy, acknowledgement still belongs to the MCU. If the MCU output is unavailable, the inference and diagnostics remain observable. App Lab packages Python, the sketch, and optional services into one reproducible application.

## Why Autodesk Fusion and PCBWay

CueLoop Bridge is a physical relationship between two objects, not a board dropped into a box. Fusion controls the pod's microphone path, battery restraint, USB access, supports, fasteners, and dock orientation; the receiver's UNO Q clearance, light diffuser, tactile controls, clip/stand, and service lid; and the assembly between them. All critical values originate in a named parameter table so measurements from received parts update the design cleanly.

The first generator creates a printable concept with realistic wall thicknesses, M2 fasteners, service gaps, and separate components. Physical fit checks will drive revisions. PCBWay will manufacture the evolved enclosure, and Fusion Electronics will support an optional carrier only if integration testing justifies it. The production path targets repeatable assembly, accessible test points, consistent walls, fewer fasteners, and an end-of-line functional test suitable for hundreds rather than one showcase prototype.

## Privacy and safety limits

CueLoop is local-first: no cloud account, speech transcript, identity inference, or default audio archive. V1 PCM travels only on a trusted private LAN; it is not application-layer encrypted, so the prototype must not be placed on public Wi-Fi or exposed to the internet. Event metadata can be cleared. Diagnostic audio capture, if ever used, is explicit and off by default.

CueLoop is an awareness aid, not a certified alarm, security system, machine interlock, or medical device. It must not replace required smoke/CO alarms, guards, supervision, or emergency procedures.

## What exists at application time

- Product requirements, architecture, privacy model, safety plan, risks, and measurable milestones.
- A genuine native-history preliminary Fusion `.f3d`, generated from the reviewed script and reopened cleanly after inspection.
- Fusion sections, measurements, interference checks, parameter-edit proof, six manufacturing-component proof, and five captioned native renders.
- A native Fusion hero render recommended as the project cover; it is a concept render, not a physical photograph.
- An earlier AI-generated concept image retained separately with its prompt summary, date, digest, and public disclosure.
- Starting V2 BOM and confirmed ordered core hardware.
- A versioned packet design and simulator-first implementation path.
- Separate scope and evidence requirements for the September App Lab prototype and December Autodesk product.

Any result described before physical bring-up is labeled simulated, development-computer, or estimated. Physical performance will be added only after it is observed.

## Development path

1. Freeze the parametric preliminary design and hardware application package (digital Fusion checkpoint completed September 5).
2. Complete the shared protocol, simulator, event engine, API, dashboard, and model evaluation framework (digital baseline complete; target execution remains pending).
3. Bring up the XIAO microphone, wireless stream, UNO Q inference, Bridge cues, and safe power path.
4. Measure accuracy, false alerts, latency, loss, distance, closed-door behavior, background interference, current, and runtime.
5. Build a new V2 carrier/interaction layer, Fusion Electronics design, and portable enclosure.
6. Order PCBWay enclosure iterations; perform fit, carry, dock, acoustic-port, thermal, and assembly tests.
7. Finish new Autodesk-user workflows, manufacturing documentation, final photos/video, and the public build article.

