# Simulated transport fault benchmark — 2026-09-02

**Evidence tier:** simulated workload on the development computer

**Purpose:** validate the encoded Protocol v1 → bounded jitter buffer → gap representation → overlapping window → synthetic classifier → temporal-policy path under deterministic packet faults.

## Method

`benchmarks/simulated_transport.py` ran all four project-authored synthetic signatures for four seconds each, using seeds 7, 17, 27, 37, and 47. Each 20 ms frame was encoded as the same datagram consumed by the physical receiver path. Three profiles produced 60 trials total:

| Profile | Requested drop | Uniform arrival jitter | Pair-reorder probability |
|---|---:|---:|---:|
| clean | 0% | 0 ms | 0% |
| moderate | 5% | ±15 ms | 5% |
| severe | 20% | ±40 ms | 15% |

Machine-readable output is ignored at `benchmarks/results/simulated-transport-2026-09-02.json`; the run file SHA-256 was `cbd7ba29d86ca7c6376b17b06345d77e1fb50ae4eb3dbbad7ce7303ef6e2eb25`.

## Results

| Profile | Trials | Mean actual drop | Mean receiver-reported loss | Target signature confirmed |
|---|---:|---:|---:|---:|
| clean | 20 | 0.000% | 0.000% | 20/20 |
| moderate | 20 | 5.200% | 5.200% | 20/20 |
| severe | 20 | 19.100% | 18.441% | 20/20 |

Across all trials, the maximum receiver missing-frame count was 42, maximum late-frame count was 1, and maximum smoothed reported jitter was 23.074 ms. Every trial emitted exactly the intended synthetic class once. The hard buffer limit remained 24,000 samples by construction and test.

The small severe-profile difference between injected drops and receiver-reported loss is expected: a receiver cannot infer unobserved loss after the last delivered sequence, and a dropped first frame precedes its sequence reference. This makes actual injector loss and observable receiver loss deliberately separate metrics.

## Claim boundary

The signatures were designed to be separable by CueLoop's synthetic classifier. A 20/20 result therefore demonstrates software continuity and diagnostics under injected faults; it does **not** demonstrate real-audio accuracy, Wi-Fi/RF performance, UNO Q latency, physical microphone behavior, or a usable 20% loss product threshold. Target-integrated replay and physical-network tests H-108/H-302–H-306 remain pending in `HARDWARE_TESTS.md`.
