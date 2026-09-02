#!/usr/bin/env bash
set -euo pipefail

CUELOOP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${CUELOOP_ROOT}/linux${PYTHONPATH:+:${PYTHONPATH}}"
export TMPDIR="/home/cd/.tmp-codex"

cd "${CUELOOP_ROOT}"
python3 -m unittest discover -s tests -p 'test_*.py' -v

