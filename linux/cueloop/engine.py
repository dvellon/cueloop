"""Confidence-aware temporal decision engine."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock
import time
import uuid

from .constants import EVENT_CLASSES


@dataclass(slots=True)
class ClassPolicy:
    enabled: bool = True
    observe_threshold: float = 0.50
    alert_threshold: float = 0.74
    minimum_hits: int = 2
    confirmation_seconds: float = 3.0
    cooldown_seconds: float = 8.0
    priority: int = 2

    def validate(self) -> None:
        if not 0 <= self.observe_threshold <= self.alert_threshold <= 1:
            raise ValueError("require 0 <= observe <= alert <= 1")
        if self.minimum_hits < 2:
            raise ValueError("minimum_hits must be at least 2")
        if self.confirmation_seconds <= 0 or self.cooldown_seconds < 0:
            raise ValueError("invalid timing policy")
        if self.priority not in (1, 2, 3):
            raise ValueError("priority must be 1, 2, or 3")


DEFAULT_POLICIES = {
    "door_knock": ClassPolicy(priority=2),
    "alarm_beep": ClassPolicy(alert_threshold=0.78, priority=3),
    "dog_bark": ClassPolicy(alert_threshold=0.76, priority=1),
    "attention_call": ClassPolicy(alert_threshold=0.78, priority=2),
}


@dataclass(slots=True)
class EventRecord:
    id: str
    class_name: str
    confidence: float
    detected_at: str
    pod_id: int
    location: str
    priority: int
    decision_state: str
    evidence_windows: int
    evidence_tier: str
    packet_loss_rate: float
    pipeline_latency_ms: float | None
    user_action: str = "pending"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class DecisionSnapshot:
    state: str = "idle"
    candidate: str | None = None
    confidence: float = 0.0
    evidence_windows: int = 0
    muted_until_monotonic: float = 0.0

    def as_dict(self, *, now: float | None = None) -> dict[str, object]:
        current = time.monotonic() if now is None else now
        return {
            "state": self.state,
            "candidate": self.candidate,
            "confidence": round(self.confidence, 4),
            "evidence_windows": self.evidence_windows,
            "muted_seconds_remaining": round(
                max(0.0, self.muted_until_monotonic - current), 1
            ),
        }


class EventEngine:
    def __init__(self, policies: dict[str, ClassPolicy] | None = None) -> None:
        source = DEFAULT_POLICIES if policies is None else policies
        self.policies = {
            label: ClassPolicy(**asdict(policy)) for label, policy in source.items()
        }
        for label in EVENT_CLASSES:
            if label not in self.policies:
                raise ValueError(f"missing policy for {label}")
            self.policies[label].validate()
        self.snapshot = DecisionSnapshot()
        self._evidence: dict[str, deque[tuple[float, float]]] = {
            label: deque() for label in EVENT_CLASSES
        }
        self._cooldown_until = {label: 0.0 for label in EVENT_CLASSES}
        self._lock = RLock()

    def process(
        self,
        scores: dict[str, float],
        *,
        pod_id: int,
        location: str,
        evidence_tier: str,
        packet_loss_rate: float,
        pipeline_latency_ms: float | None,
        now: float | None = None,
        wall_time: datetime | None = None,
    ) -> EventRecord | None:
        current = time.monotonic() if now is None else now
        timestamp = datetime.now(timezone.utc) if wall_time is None else wall_time
        with self._lock:
            self._expire(current)
            if current < self.snapshot.muted_until_monotonic:
                self.snapshot.state = "muted"
                self.snapshot.candidate = None
                self.snapshot.confidence = 0.0
                self.snapshot.evidence_windows = 0
                return None

            for label in EVENT_CLASSES:
                score = max(0.0, min(1.0, float(scores.get(label, 0.0))))
                policy = self.policies[label]
                if policy.enabled and score >= policy.observe_threshold:
                    self._evidence[label].append((current, score))

            candidates: list[tuple[float, str, float, int]] = []
            for label in EVENT_CLASSES:
                policy = self.policies[label]
                evidence = self._evidence[label]
                if not policy.enabled or not evidence:
                    continue
                confidence = sum(score for _, score in evidence) / len(evidence)
                candidates.append((confidence, label, confidence, len(evidence)))

            if not candidates:
                self.snapshot.state = "idle"
                self.snapshot.candidate = None
                self.snapshot.confidence = 0.0
                self.snapshot.evidence_windows = 0
                return None

            _, label, confidence, hits = max(candidates)
            policy = self.policies[label]
            self.snapshot.candidate = label
            self.snapshot.confidence = confidence
            self.snapshot.evidence_windows = hits
            self.snapshot.state = "observing" if hits == 1 else "confirming"

            if current < self._cooldown_until[label]:
                self.snapshot.state = "cooldown"
                return None
            if hits < policy.minimum_hits or confidence < policy.alert_threshold:
                return None

            event = EventRecord(
                id=str(uuid.uuid4()),
                class_name=label,
                confidence=round(confidence, 4),
                detected_at=timestamp.astimezone(timezone.utc).isoformat(),
                pod_id=pod_id,
                location=location[:48],
                priority=policy.priority,
                decision_state="confirmed",
                evidence_windows=hits,
                evidence_tier=evidence_tier,
                packet_loss_rate=round(max(0.0, min(1.0, packet_loss_rate)), 6),
                pipeline_latency_ms=(
                    None
                    if pipeline_latency_ms is None
                    else round(max(0.0, pipeline_latency_ms), 3)
                ),
            )
            self._cooldown_until[label] = current + policy.cooldown_seconds
            for evidence in self._evidence.values():
                evidence.clear()
            self.snapshot.state = "alerting"
            self.snapshot.candidate = label
            self.snapshot.confidence = confidence
            self.snapshot.evidence_windows = hits
            return event

    def _expire(self, now: float) -> None:
        for label, evidence in self._evidence.items():
            cutoff = now - self.policies[label].confirmation_seconds
            while evidence and evidence[0][0] < cutoff:
                evidence.popleft()

    def mute(self, seconds: float, *, now: float | None = None) -> None:
        if not 0 <= seconds <= 86_400:
            raise ValueError("mute seconds must be between 0 and 86400")
        current = time.monotonic() if now is None else now
        with self._lock:
            self.snapshot.muted_until_monotonic = current + seconds
            self.snapshot.state = "muted" if seconds else "idle"
            for evidence in self._evidence.values():
                evidence.clear()

    def update_policy(self, label: str, changes: dict[str, object]) -> ClassPolicy:
        allowed = {
            "enabled",
            "observe_threshold",
            "alert_threshold",
            "minimum_hits",
            "confirmation_seconds",
            "cooldown_seconds",
            "priority",
        }
        if label not in self.policies:
            raise KeyError(label)
        if set(changes) - allowed:
            raise ValueError("unsupported policy field")
        with self._lock:
            candidate = ClassPolicy(**{**asdict(self.policies[label]), **changes})
            candidate.validate()
            self.policies[label] = candidate
            self._evidence[label].clear()
            return ClassPolicy(**asdict(candidate))

    def policies_snapshot(self) -> dict[str, dict[str, object]]:
        with self._lock:
            return {label: asdict(policy) for label, policy in self.policies.items()}

    def state_snapshot(self) -> dict[str, object]:
        with self._lock:
            return self.snapshot.as_dict()

