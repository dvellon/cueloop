# Model selection record

## Decision

Use Google YAMNet classification LiteRT v1 as the V1 baseline adapter, while keeping Arduino App Lab's `arduino:audio_classification` Brick as a target-hardware comparison path. Do not claim either as production-ready until identical licensed clips are benchmarked on the UNO Q.

## Why YAMNet LiteRT

- It has a stable, versioned official artifact and Apache-2.0 license.
- Its fixed 0.975-second input is a close match for CueLoop's 1-second / 0.5-second-hop window pipeline.
- It exposes 521 interpretable AudioSet scores, including direct labels for knock, alarms/beeps, bark, and shouted attention sounds.
- At 4,126,810 bytes, the downloaded fixed-window artifact is small enough for practical UNO Q deployment.
- LiteRT 2.2.0 publishes CPython 3.13/3.14 aarch64 wheels, making an UNO Q Python adapter plausible. This is a compatibility hypothesis until installed on the board image.

## Alternatives considered

| Candidate | Advantage | Blocking concern / disposition |
|---|---|---|
| Arduino `audio_classification` Brick | Official App Lab lifecycle and very small Python surface | Current official example classifies an audio file; streaming/PCM API and model/version details are not documented publicly enough to make the desktop pipeline depend on it. Retain as hardware comparison. |
| Full TensorFlow YAMNet SavedModel | Reference implementation and embeddings | Much heavier runtime; upstream YAMNet currently relies on Keras 2 and notes Keras 3 incompatibility. Rejected for V1 deployment. |
| CueLoop-specific embedding head | Better task fit with enough labeled data | Needs a provenance-complete, balanced dataset and honest held-out evaluation that is not yet available. Preferred post-baseline improvement, not fabricated now. |
| Synthetic signature classifier | Deterministic and dependency-free | Recognizes owned test tones, not real sounds. Retained only for protocol/UI regression tests. |

## Integration facts and open gates

The downloaded artifact was inspected locally: input `waveform_binary` is float32 `[15600]`; output is float32 `[1, 521]`; 521 labels are embedded as `yamnet_label_list.txt`. The adapter center-crops the pipeline's 16,000-sample window by 200 samples on each side and normalizes signed PCM16 to `[-1, 1]`.

Open gates:

1. Run provenance-complete development-computer evaluation across all four classes and hard negatives.
2. Calibrate mappings and temporal thresholds without touching held-out test clips.
3. Install the exact runtime on UNO Q, measure cold/warm latency and memory, and compare the official App Lab Brick on the same clips.
4. If `attention_call` remains unreliable, drop or rename it rather than broadening to generic speech.

Official sources checked 2026-09-01:

- <https://www.kaggle.com/models/google/yamnet/tfLite/classification-tflite>
- <https://github.com/tensorflow/models/tree/master/research/audioset/yamnet>
- <https://github.com/arduino/app-bricks-examples/tree/main/bricks/arduino/audio_classification/01_glass_breaking_from_file>
- <https://docs.arduino.cc/software/app-lab/tutorials/examples/>

