#!/usr/bin/env bash
set -euo pipefail

CUELOOP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${CUELOOP_ROOT}/linux${PYTHONPATH:+:${PYTHONPATH}}"
export TMPDIR="/home/cd/.tmp-codex"

UDP_PORT="${CUELOOP_UDP_PORT:-57321}"
HTTP_PORT="${CUELOOP_HTTP_PORT:-8080}"
DEMO_SECONDS="${CUELOOP_DEMO_SECONDS:-0}"
DB_PATH="${CUELOOP_ROOT}/data/cueloop_demo.sqlite3"

mkdir -p "${CUELOOP_ROOT}/data" "${TMPDIR}"

python3 -m cueloop.service \
  --udp-host 127.0.0.1 \
  --udp-port "${UDP_PORT}" \
  --http-host 127.0.0.1 \
  --http-port "${HTTP_PORT}" \
  --db "${DB_PATH}" \
  --location "Simulated workshop" &
SERVICE_PID=$!

cleanup() {
  kill "${SERVICE_PID}" 2>/dev/null || true
  wait "${SERVICE_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

python3 - "${HTTP_PORT}" <<'PY'
import sys
import time
import urllib.request

url = f"http://127.0.0.1:{sys.argv[1]}/api/status"
for _ in range(50):
    try:
        with urllib.request.urlopen(url, timeout=0.2) as response:
            if response.status == 200:
                break
    except OSError:
        time.sleep(0.1)
else:
    raise SystemExit("CueLoop service did not become ready")
PY

printf 'Open http://127.0.0.1:%s — input and all results are visibly labeled simulated.\n' "${HTTP_PORT}"
python3 -m cueloop.simulator \
  --host 127.0.0.1 \
  --port "${UDP_PORT}" \
  --run-seconds "${DEMO_SECONDS}" \
  --loss "${CUELOOP_DEMO_LOSS:-0.02}" \
  --jitter-ms "${CUELOOP_DEMO_JITTER_MS:-8}" \
  --reorder-rate "${CUELOOP_DEMO_REORDER_RATE:-0.01}"

