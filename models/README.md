# Acoustic model workbench

CueLoop uses the official fixed-window YAMNet LiteRT v1 model as a broad, reproducible baseline. The model is optional: the standard-library simulator and receiver tests do not need it, and the service never silently switches from the visibly simulated classifier.

## Reproduce the baseline

```bash
python3 -m venv .venv-model
.venv-model/bin/python -m pip install -r requirements-model.txt
.venv-model/bin/python scripts/fetch_yamnet.py
PYTHONPATH=linux .venv-model/bin/python models/benchmark_yamnet.py --iterations 100
```

The fetcher downloads the pinned official URL into ignored `models/artifacts/`, limits the transfer size, and refuses a size or SHA-256 mismatch. The expected digest and tensor contract are in `model_manifest.json`. Model binaries are intentionally not committed.

Run the service with real inference only when the artifact exists:

```bash
PYTHONPATH=linux .venv-model/bin/python -m cueloop.service \
  --classifier yamnet \
  --model models/artifacts/yamnet-classification-tflite-v1.tflite \
  --mapping models/class_mapping.json
```

This proves the integration path, not real-world event quality. `class_mapping.json` groups specific AudioSet outputs into CueLoop concepts. It deliberately excludes generic `Speech` from `attention_call`; all groups and thresholds remain hypotheses until the real-audio evaluation gate passes.

## Evaluate licensed audio

Keep PCM16 WAV files under ignored `data/private/evaluation/`. Copy `evaluation_manifest.example.json`, replace every template field, and run:

```bash
PYTHONPATH=linux .venv-model/bin/python models/evaluate.py \
  --manifest data/private/evaluation/manifest.json \
  --model models/artifacts/yamnet-classification-tflite-v1.tflite \
  --mapping models/class_mapping.json \
  --split test
```

The evaluator refuses missing provenance, consent, licenses, checksums, malformed event intervals, or unsupported WAV encodings. It reports per-class support and 2×2 confusion matrices, precision/recall/F1, missed-event rate, false triggers per audio hour, Brier/calibration error, inference latency, condition slices, a temporal-policy versus single-window comparison, and annotated WAV-onset-to-decision latency when intervals are supplied. That annotated latency excludes CuePod capture, networking, UNO Q scheduling, Bridge, and physical cue delay; measure full end-to-end latency separately in `HARDWARE_TESTS.md`. Do not tune on the test split; calibrate thresholds on `calibration`, select once on `validation`, and publish only the held-out `test` result.

This V1 deployment uses Google's already-converted, versioned LiteRT artifact. CueLoop therefore does not invent a second conversion pipeline whose output would differ from the pinned official binary. `scripts/fetch_yamnet.py` is the reproducible acquisition/checksum gate; `linux/cueloop/yamnet.py` is the documented preprocessing/tensor adapter. A future task-specific embedding head must add its own conversion/training script, source-model identity, representative data license, quantization method, tensor contract, and output checksum before it can replace this baseline.

Raw audio is read window-by-window and never written by the evaluator. Generated result JSON belongs under ignored `benchmarks/results/`; curated Markdown summaries may be committed only with an explicit evidence tier.
