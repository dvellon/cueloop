"""Local model interfaces and a simulation-only acoustic signature classifier."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol

from .constants import EVENT_CLASSES, SAMPLE_RATE_HZ


@dataclass(frozen=True, slots=True)
class Classification:
    scores: dict[str, float]
    inference_ms: float
    model_name: str
    evidence_tier: str


class AudioClassifier(Protocol):
    def classify(self, samples: tuple[int, ...], sample_rate: int) -> Classification:
        ...


def goertzel_amplitude(
    normalized: list[float], sample_rate: int, frequency: float
) -> float:
    length = len(normalized)
    if length == 0:
        return 0.0
    target_bin = int(0.5 + length * frequency / sample_rate)
    omega = 2.0 * math.pi * target_bin / length
    coefficient = 2.0 * math.cos(omega)
    previous = 0.0
    previous_two = 0.0
    for sample in normalized:
        current = sample + coefficient * previous - previous_two
        previous_two = previous
        previous = current
    power = max(
        0.0,
        previous_two * previous_two
        + previous * previous
        - coefficient * previous * previous_two,
    )
    return 2.0 * math.sqrt(power) / length


class SignatureClassifier:
    """Deterministic test classifier for synthetic signals only.

    It makes the end-to-end pipeline runnable before a model is downloaded, but
    it is never evidence of real acoustic-event accuracy.
    """

    TARGET_FREQUENCIES = {
        "door_knock": 280.0,
        "dog_bark": 650.0,
        "attention_call": 900.0,
        "alarm_beep": 1400.0,
    }

    def classify(self, samples: tuple[int, ...], sample_rate: int) -> Classification:
        import time

        started = time.perf_counter()
        if sample_rate != SAMPLE_RATE_HZ:
            raise ValueError(f"SignatureClassifier requires {SAMPLE_RATE_HZ} Hz")
        normalized = [sample / 32768.0 for sample in samples]
        rms = math.sqrt(
            sum(sample * sample for sample in normalized) / max(1, len(normalized))
        )
        amplitudes = {
            label: goertzel_amplitude(normalized, sample_rate, frequency)
            for label, frequency in self.TARGET_FREQUENCIES.items()
        }
        total = sum(amplitudes.values()) + 1e-9
        dominant = max(amplitudes, key=lambda label: amplitudes[label])
        dominant_amplitude = amplitudes[dominant]
        dominance = dominant_amplitude / total

        scores = {label: 0.01 for label in EVENT_CLASSES}
        if rms < 0.008 or dominant_amplitude < 0.015:
            scores.update({"background": 0.97, "unknown": 0.02})
        else:
            confidence = max(0.35, min(0.99, 0.42 + 0.62 * dominance))
            scores[dominant] = confidence
            scores.update(
                {
                    "background": max(0.0, 0.20 - rms),
                    "unknown": max(0.01, 1.0 - confidence - 0.08),
                }
            )
        elapsed = (time.perf_counter() - started) * 1000.0
        return Classification(
            scores=scores,
            inference_ms=elapsed,
            model_name="synthetic-signature-v1",
            evidence_tier="simulated",
        )
