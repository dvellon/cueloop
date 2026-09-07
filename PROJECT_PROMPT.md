You are the lead engineer, AI developer, embedded developer, product designer, test engineer, and competition-submission writer for CueLoop. Treat this as a long-running goal, not a one-turn consultation.

Create an active goal whose objective is:

“Design, implement, test, document, and package CueLoop as a highly competitive Arduino UNO Q project for the 2026 Invent the Future with Arduino UNO Q and App Lab competition, while creating a materially differentiated Autodesk University 2027 product application and development path based on the same technical foundation.”

Continue working until every task that can be completed digitally is complete. Do not stop after producing a plan or skeleton repository. Write the code, tests, documentation, diagrams, CAD automation, submission drafts, scripts, and user instructions. Make reasonable engineering decisions independently. Ask me questions only when a missing choice would materially change the product or when a physical action or observation is genuinely required.

## Dates and competitions

Current starting date is approximately September 1, 2026. Check the actual date when beginning.

Competition 1:

- Invent the Future with Arduino UNO Q and App Lab
- Final deadline: September 13, 2026 at 11:59 PM Pacific
- Target category: Best Social Impact, with Best in Show as secondary upside
- Judging emphasis:
  - Project documentation: 30
  - BOM: 20
  - Schematics: 15
  - Code and contribution: 15
  - Creativity: 20

Competition 2:

- Build the Autodesk University 2027 Product
- Hardware application deadline: September 7, 2026 at 11:59 PM Pacific
- Final project deadline: December 20, 2026 at 11:59 PM Pacific
- The September application requires a credible product concept, Hackster project beginning, preliminary Fusion design, starting BOM, cover image/render, and project story.
- The December product must be portable, wearable, attachable, clipped, or carried; useful beyond Autodesk University; and suitable for Autodesk customers.
- Judging emphasis:
  - Creativity: 30
  - Documentation: 20
  - BOM: 20
  - Schematics: 10
  - Fusion: 10
  - Code: 10

Before relying on these details, verify the latest official competition rules and official Arduino UNO Q/App Lab documentation. Use official primary sources. If current official information conflicts with this prompt, follow the official information and document the discrepancy.

## Confirmed hardware

The following hardware has been ordered:

- Arduino UNO Q 4 GB / 32 GB, SKU ABX00173
- The accompanying Arduino order and its Modulino/Qwiic accessories; inventory the exact modules when the packing list or hardware is available
- Seeed Studio XIAO ESP32S3 Sense, manufacturer part 113991115
- Adafruit protected 3.7 V 500 mAh LiPo battery, product 1578
- Adafruit JST-PH female pigtail, product 261
- YIHUA 926 III temperature-controlled soldering-station kit
- AstroAI AM33D multimeter
- Appropriate UNO Q power, USB-C connectivity, and Qwiic infrastructure from the Arduino order

Do not assume optional modules are essential. Build the minimum reliable product around the UNO Q, XIAO Sense, and available human-output hardware. Provide graceful software fallbacks when hardware is still in transit.

Never instruct me to solder with the battery connected. Require polarity and continuity checks before first battery connection. Never solder directly to a LiPo cell.

## Product thesis

CueLoop is a private, local-first acoustic event bridge.

A detachable, battery-powered wireless microphone pod can be placed in another room, workspace, doorway, machine area, studio, or other acoustically separated location. The pod streams or transmits acoustic evidence to the UNO Q. Edge AI recognizes important environmental events and converts them into discreet, understandable visual, audible, and/or haptic cues.

Examples include:

- Door knocks
- Timers and appliance beeps
- Smoke or safety alarms
- Running water
- Glass breaking
- A crying baby
- A dog barking
- Someone calling for attention
- A machine completing a cycle
- Workshop or fabrication alerts

The initial social-impact use case includes people who are deaf or hard of hearing, but the product must not be framed as exclusively for that population. Additional users include:

- People wearing headphones
- Workers wearing hearing protection
- Caregivers
- Neurodivergent users who want controlled rather than startling alerts
- People moving between rooms
- Makers monitoring a machine or process from another space
- People who want awareness without cloud microphones or constant audio recording

The central promise is:

“Know what needs your attention without continuously listening, recording, or remaining in the same room.”

Avoid claiming CueLoop is a safety-certified alarm or medical device.

## What makes this more than a sound classifier

A winning project cannot merely run an audio model and display a label.

Develop a confidence-aware event pipeline:

1. The remote pod observes audio.
2. The UNO Q estimates the likely event and confidence.
3. Temporal evidence is combined across multiple windows.
4. Ambiguous events trigger a deliberate confirmation window or adjusted measurement instead of an immediate false alert.
5. The system reports the event only when the evidence and user-configured importance justify it.
6. The user can confirm, dismiss, or mute the cue.
7. Feedback is stored locally as evaluation data and, if feasible, used for lightweight personalization.
8. Raw audio is discarded by default after inference.

This “uncertainty-aware acoustic bridge” is the technical and creative core.

## Two related but distinct products

Do not submit one identical project twice.

### App Lab V1: CueLoop

CueLoop V1 is a working, highly reproducible social-impact prototype completed by September 13.

It should demonstrate:

- A detachable XIAO Sense microphone
- Wireless room-to-room audio or acoustic-feature transmission
- UNO Q edge-AI event recognition
- Confidence and temporal confirmation
- Local-first privacy
- A clear App Lab workflow
- Meaningful use of both the UNO Q Linux/Qualcomm side and STM32 MCU side
- At least one physical output such as LEDs, haptics, buzzer, or another available Modulino
- A polished local dashboard
- Complete BOM, schematics, code, build instructions, and quantitative testing

Target one excellent, repeatable demonstration rather than many unreliable features.

### Autodesk V2: CueLoop Studio / CueLoop Bridge

Develop a materially evolved portable product for Autodesk users and multi-space work.

Possible use cases include:

- A designer wearing hearing protection while a printer, CNC machine, laser cutter, test rig, or curing process runs elsewhere
- A creator working in a studio while monitoring a door, timer, machine, or collaborator
- A portable conference or hotel-room awareness accessory
- A clip-on receiver paired with detachable acoustic pods
- A privacy-preserving alternative to placing smart speakers throughout a space

V2 must add product depth, not merely a prettier enclosure:

- A detachable or dockable CuePod
- A portable receiver or main unit
- Purposeful clip, stand, lanyard, magnetic dock, or attachment system
- Designed microphone port and acoustic path
- Haptic and visual cue language
- Serviceable enclosure
- Battery and charging strategy
- Improved controls and ergonomics
- Manufacturable Fusion design
- PCBWay-appropriate enclosure
- Potential custom PCB or carrier
- Clear Autodesk-workflow relevance
- Materially expanded reliability, portability, and interaction design

Maintain separate Hackster submission content and a clear shared-work/differentiation record.

## Required repository

Create and maintain a clean repository resembling:

- `README.md`
- `LICENSE`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `docs/`
  - product requirements
  - architecture
  - privacy model
  - safety
  - build instructions
  - testing
  - troubleshooting
  - photo shot list
  - demo instructions
- `firmware/`
  - `xiao_cuepod/`
  - `uno_q_mcu/`
- `linux/`
  - audio receiver
  - inference service
  - event engine
  - API
  - local dashboard
- `app_lab/`
- `models/`
  - model-selection notes
  - class mappings
  - preprocessing
  - conversion scripts
  - evaluation tools
- `shared/`
  - protocol definitions
  - schemas
  - constants
- `simulator/`
  - simulated wireless microphone
  - prerecorded-event replay
  - packet-loss and latency injection
- `tests/`
  - unit
  - integration
  - protocol
  - recorded-audio evaluation
- `hardware/`
  - BOM
  - wiring tables
  - pin assignments
  - schematics
  - power calculations
- `cad/`
  - Fusion scripts
  - dimension parameters
  - generated reference exports
  - assembly instructions
- `submissions/`
  - `app_lab/`
  - `autodesk_application/`
  - `autodesk_final/`
- `experiments/`
- `benchmarks/`
- `scripts/`
- `assets/`
- `user_checklists/`

Use a structure appropriate to the actual tools and languages after examining the official UNO Q development workflow.

## Technical architecture to validate and implement

Treat this as a starting architecture, not unquestionable truth. Validate each assumption against official documentation and actual benchmarks.

### CuePod: XIAO ESP32S3 Sense

Implement firmware that:

- Captures the onboard digital microphone
- Begins with 16 kHz mono audio suitable for event classification
- Uses Wi-Fi for V1 unless testing proves another transport superior
- Sends sequence-numbered, timestamped packets
- Reports battery state when supported
- Supports a simple pairing/configuration mechanism
- Detects receiver loss and reconnects cleanly
- Exposes diagnostic counters
- Avoids persistent raw-audio storage
- Includes a USB-powered development mode
- Includes a simulated or test-tone mode
- Keeps credentials out of source control
- Documents exactly how to flash and configure the board

Use persistent length-framed TCP for raw PCM and ACK traffic because Arduino App Lab publishes declared ports as TCP. Add compression only if measurements justify the complexity.

Design and document:

- Packet format
- Discovery or receiver configuration
- Buffering
- Lost-packet behavior
- Clock/timestamp handling
- Reconnection
- Security and privacy limitations
- Expected bandwidth
- Expected battery runtime

### UNO Q Linux side

Implement services that:

- Receive the CuePod stream
- Maintain a bounded jitter/ring buffer
- Produce correctly normalized model windows
- Run a lightweight audio-event model locally
- Map broad model outputs into a small, understandable CueLoop vocabulary
- Combine evidence temporally
- Apply per-class thresholds, cooldowns, and user priorities
- Perform confirmation passes for uncertain events
- Generate structured event records
- Avoid saving raw audio by default
- Expose health, latency, packet-loss, and model-performance information
- Serve a polished local web interface
- Run through the official App Lab workflow where practical
- Include reproducible environment and dependency setup
- Recover after component restart

Investigate suitable pretrained models, beginning with lightweight TFLite audio-event models such as YAMNet or a better supported equivalent. Benchmark before committing. Do not claim the model works well merely because inference runs.

### UNO Q STM32 side

Use the MCU for responsibilities that genuinely benefit from deterministic hardware behavior, such as:

- Button/knob input
- Haptic patterns
- LED patterns
- Buzzer timing
- Watchdog/health indication
- Fast acknowledgement input
- Sensor sampling if an available Modulino adds meaningful value

Use the supported UNO Q Bridge/RPC mechanism. The Linux side should send compact event commands; the MCU should own reliable physical cue timing.

If the actual UNO Q/App Lab architecture differs, adapt cleanly and explain why.

### Local interface

Create a visually polished, accessible dashboard that shows:

- Connection state
- Current monitored location/pod
- Recognized event
- Confidence
- Time detected
- Confirmation state
- User priority
- Mute/acknowledge controls
- Recent event history without raw audio
- Packet loss and latency in a diagnostics view
- Privacy state
- Simple event-class configuration

Design for a competition video: important information must be legible immediately.

## Simulator-first requirement

Do not wait idly for hardware.

Before hardware arrives, implement:

- A simulated CuePod sender
- WAV-file replay
- Artificial packet loss
- Artificial jitter and latency
- Receiver reconnection tests
- Event-engine unit tests
- Dashboard mock data
- Model evaluation scripts
- A one-command local demonstration

Keep hardware-specific code behind clear interfaces so simulated and physical sources use the same processing pipeline.

Never present simulated results as physical validation.

## Model and data evaluation

Create an honest evaluation framework.

Use legally reusable or self-recorded test audio. Record provenance and licensing. Avoid committing copyrighted or sensitive recordings.

Measure:

- Per-class precision and recall
- Confusion matrix
- False alerts per hour
- Missed-event rate
- End-to-end latency
- Inference latency
- Packet-loss tolerance
- Effect of distance and closed doors
- Effect of background speech, television, music, and fans
- Confidence calibration
- Benefit of temporal confirmation versus a single-window classifier

Select a limited set of classes that can be demonstrated reliably. It is better to support four classes convincingly than twenty poorly.

Mark every number as one of:

- Simulated
- Benchmarked on development computer
- Measured on UNO Q
- Measured with physical CuePod
- Estimated

Never fabricate test results.

## Schematics and BOM

Create:

- Exact BOM with manufacturer numbers, quantities, purpose, source, and price
- Minimum V1 BOM
- Optional V1 parts
- V2 development BOM
- Wiring tables
- Power-path diagram
- Battery connection diagram
- Wireless/system block diagram
- MCU/Linux responsibility diagram
- Network protocol diagram
- A real schematic using an appropriate reproducible format where possible
- Human-readable SVG/PNG exports
- Pin assignments
- Assembly order
- Polarity checks
- Multimeter procedures
- Safe first-power checklist

Do not confuse Qwiic cables with the battery pigtail. The CuePod does not need a Qwiic cable unless a later sensor is deliberately added.

## Fusion and Autodesk work

Create a preliminary but credible Fusion 360 design workflow before the September 7 application deadline.

Because direct Fusion manipulation may require user interaction, do as much as possible through generated files and automation:

- Write a Fusion 360 Python script or add-in that generates the preliminary parametric parts
- Clearly document how I run the script inside Fusion
- Define all critical dimensions in one parameter section
- Create at least:
  - CuePod enclosure
  - Microphone acoustic opening
  - USB access
  - Battery cavity
  - Internal board supports
  - Lid/fastening strategy
  - Clip/dock/stand concept
  - Main receiver enclosure concept
  - Basic assembly
- Use realistic wall thicknesses, clearances, fillets, draft/printing constraints, fastener sizes, and service access
- Generate any reference renders or diagrams possible outside Fusion
- Give me exact instructions for saving the resulting design as `.f3d`
- Produce an application-ready cover render or a detailed render-generation workflow
- Maintain a dimensional validation checklist against the physical parts when they arrive

For December, evolve the CAD toward a manufacturable PCBWay enclosure and document DFM decisions.

## Competition deliverables

### Autodesk application package — first priority

Complete as early as possible:

- Final product name recommendation
- One-sentence pitch
- Short elevator pitch
- Long project story
- Problem and user definition
- Product differentiation
- Why UNO Q is necessary
- Why Fusion is necessary
- Why Autodesk users would carry it
- Starting BOM
- System architecture
- Preliminary CAD
- Cover image/render
- Hackster project opening
- Application responses
- Credible execution timeline
- Risk management
- Explicit explanation of how V2 differs from the App Lab prototype

Write polished, submission-ready copy—not bullet fragments.

### App Lab package

Create:

- Competition-ready title and subtitle
- Cover-image plan
- Complete Hackster project article
- Problem statement
- User stories
- Architecture explanation
- AI explanation
- App Lab explanation
- Linux/MCU split explanation
- Full BOM
- Complete schematics
- Reproducible build instructions
- Setup instructions
- Usage instructions
- Troubleshooting
- Privacy explanation
- Limitations
- Test results
- Source-code guide
- Contribution/reuse value
- Photo shot list
- Three-minute demo storyboard
- Short and long narration scripts
- On-screen text plan
- Final submission checklist

Optimize explicitly for the published judging rubric.

### Autodesk final package

Begin the structure now but do not let December work endanger the September deadlines. Track:

- V1 shared work
- V2-specific work
- New hardware
- New interactions
- New CAD
- New manufacturing work
- New testing
- New Autodesk-user workflow
- Eligibility differentiation

## Demo design

Design a demonstration that is understandable without explanation:

1. Place the CuePod in another room or behind a closed door.
2. Show the UNO Q receiver and dashboard in the primary room.
3. Trigger a selected sound event.
4. Show wireless reception, edge inference, confirmation, and a physical cue.
5. Show the event label and confidence.
6. Demonstrate acknowledgement or mute.
7. Trigger a confusing/background sound and show that the system avoids or delays a false alert.
8. Show that processing remains local and no raw recording is retained.
9. Show diagnostic latency and packet-loss measurements.

Create a fallback demo using recorded WAV files, but the final competition video should prioritize a real detached microphone.

## Milestones and ordering

Work in this order unless official requirements force a change:

1. Verify official rules and technical documentation.
2. Create the repository, goal, decision log, risk register, and master plan.
3. Draft the Autodesk application and product requirements.
4. Generate preliminary Fusion automation and cover-render assets.
5. Build the simulator and common protocol.
6. Implement the UNO Q receiver, event engine, API, and dashboard.
7. Implement model evaluation and select reliable event classes.
8. Implement XIAO firmware.
9. Implement UNO Q MCU physical cues and Bridge/RPC integration.
10. Integrate through App Lab.
11. Execute hardware bring-up using exact user checklists.
12. Measure performance and replace simulated results with physical results.
13. Finish App Lab documentation, schematics, BOM, and video package.
14. Perform a rubric-based adversarial review.
15. Package and archive the submission.
16. Continue the Autodesk V2 development plan without conflating the two entries.

## Working behavior

- Begin immediately; do not ask me to approve the plan.
- Maintain `STATUS.md`, `PLAN.md`, `DECISIONS.md`, `RISKS.md`, and `HARDWARE_RESULTS.md`.
- Provide concise progress updates during long work.
- Use version control carefully and make logical commits when appropriate.
- Preserve user changes.
- Run tests after meaningful changes.
- Prefer primary documentation and reproducible dependencies.
- Do not leave large placeholder sections when implementation is possible.
- Do not claim hardware behavior that has not been observed.
- Do not silently abandon a difficult component; investigate alternatives and document the decision.
- When blocked on hardware, continue all unrelated work.
- When my physical input is required, give me one short numbered checklist with expected observations and a precise place to record the results.
- Keep secrets and Wi-Fi credentials out of the repository.
- Avoid unnecessary cloud dependencies.
- Avoid adding hardware simply because it is available.
- Keep V1 small enough to finish reliably.
- Treat documentation, schematics, BOM, and the demo as first-class engineering outputs.

## Definition of done

Do not mark the long-running goal complete merely because a prototype skeleton exists.

The digitally complete project should contain:

- Buildable XIAO firmware
- Buildable UNO Q MCU code
- Runnable UNO Q Linux services
- App Lab integration
- Functional simulator
- Automated tests
- Model-selection and evaluation tools
- Local dashboard
- Protocol documentation
- Complete BOM
- Wiring and schematics
- Safe hardware bring-up instructions
- Fusion automation and preliminary product design
- Autodesk application copy
- App Lab Hackster submission copy
- Video scripts and shot lists
- Quantitative test framework
- Clear placeholders only for measurements or photos that require physical hardware
- A prioritized list of remaining user actions
- A rubric-by-rubric final review

At the start, report the verified deadlines, the first concrete files you will create, and any official-rule discrepancy. Then begin creating the project immediately.
