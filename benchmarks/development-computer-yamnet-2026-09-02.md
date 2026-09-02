# YAMNet development-computer latency baseline

**Evidence tier:** development computer / synthetic workload  
**Run time:** 2026-09-02 04:05:53 UTC  
**Accuracy evaluated:** no

## Configuration

| Item | Value |
|---|---|
| Host | x86_64, Linux 7.0.0-30-generic, 12 logical CPUs |
| Python | 3.14.4 |
| Runtime | `ai-edge-litert==2.2.0`, `numpy==2.5.2` |
| Threads | 2 |
| Model | Google YAMNet classification LiteRT v1 |
| Model SHA-256 | `10c95ea3eb9a7bb4cb8bddf6feb023250381008177ac162ce169694d05c317de` |
| Artifact size | 4,126,810 bytes |
| Workload | five project-owned deterministic synthetic signatures, 16 kHz, 16,000-sample pipeline windows center-cropped to 15,600 samples |
| Procedure | 10 warm-up inferences, then 100 measured inferences alternating evenly across signals |

## Result

| Metric | Milliseconds |
|---|---:|
| Minimum | 1.789 |
| Mean | 1.834 |
| p50 | 1.820 |
| p95 | 1.919 |
| p99 | 1.956 |
| Maximum | 1.997 |

Linux reported 73,384 KiB process peak RSS, which includes Python, NumPy, LiteRT, the model, and benchmark state; it is not incremental model memory.

## Interpretation boundary

This run establishes that the pinned artifact, embedded labels, class mapping, normalization/cropping, and LiteRT adapter execute reproducibly on the development computer with substantial latency headroom relative to the 500 ms window hop. It does **not** measure UNO Q latency, XIAO capture, network delay, cue delay, or accuracy on knocks, alarms, dogs, or human attention calls.

The mapped output on synthetic tones is intentionally not reported as accuracy. Only the synthetic alarm tone produced a moderate mapped `alarm_beep` score (0.585938); the other event tones were predominantly `unknown`. That is expected because the tones were designed for a deterministic Goertzel test classifier, not to imitate real acoustic events. It is useful negative evidence against reusing simulator results as a model-quality claim.

Reproduce with:

```bash
PYTHONPATH=linux .venv-model/bin/python models/benchmark_yamnet.py \
  --warmup 10 --iterations 100 --threads 2
```

