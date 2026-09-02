"""Values shared by the receiver, simulator, model adapter, and API."""

from __future__ import annotations

SAMPLE_RATE_HZ = 16_000
SAMPLE_WIDTH_BYTES = 2
CHANNELS = 1
FRAME_DURATION_MS = 20
SAMPLES_PER_FRAME = SAMPLE_RATE_HZ * FRAME_DURATION_MS // 1000
BYTES_PER_FRAME = SAMPLES_PER_FRAME * SAMPLE_WIDTH_BYTES
WINDOW_SAMPLES = SAMPLE_RATE_HZ
WINDOW_STRIDE_SAMPLES = SAMPLE_RATE_HZ // 2

DEFAULT_UDP_HOST = "0.0.0.0"
DEFAULT_UDP_PORT = 57321
DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_HTTP_PORT = 8080
POD_TIMEOUT_SECONDS = 2.5

EVENT_CLASSES = (
    "door_knock",
    "alarm_beep",
    "dog_bark",
    "attention_call",
)
SUPPRESSION_CLASSES = ("background", "unknown")

EVIDENCE_TIERS = (
    "simulated",
    "development-computer",
    "UNO Q",
    "physical CuePod",
    "estimated",
)

