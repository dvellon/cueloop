#!/usr/bin/env bash
set -euo pipefail

CUELOOP_SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CUELOOP_VERIFY_PARENT="${CUELOOP_VERIFY_PARENT:-${CUELOOP_SOURCE_ROOT}/tmp}"
CUELOOP_VERIFY_MODEL=""
CUELOOP_VERIFY_FETCH_MODEL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      if [[ $# -lt 2 ]]; then
        echo "--model requires a path" >&2
        exit 2
      fi
      CUELOOP_VERIFY_MODEL="$2"
      shift 2
      ;;
    --fetch-model)
      CUELOOP_VERIFY_FETCH_MODEL=1
      shift
      ;;
    *)
      echo "Usage: $0 [--model PATH | --fetch-model]" >&2
      exit 2
      ;;
  esac
done

if [[ -n "${CUELOOP_VERIFY_MODEL}" && "${CUELOOP_VERIFY_FETCH_MODEL}" -eq 1 ]]; then
  echo "Choose either --model or --fetch-model, not both" >&2
  exit 2
fi
if [[ -n "${CUELOOP_VERIFY_MODEL}" ]]; then
  if [[ ! -f "${CUELOOP_VERIFY_MODEL}" ]]; then
    echo "Model path is not a file: ${CUELOOP_VERIFY_MODEL}" >&2
    exit 2
  fi
  CUELOOP_VERIFY_MODEL="$(cd "$(dirname "${CUELOOP_VERIFY_MODEL}")" && pwd)/$(basename "${CUELOOP_VERIFY_MODEL}")"
fi
for CUELOOP_REQUIRED_TOOL in git python3 npx arduino-cli sha256sum; do
  if ! command -v "${CUELOOP_REQUIRED_TOOL}" >/dev/null 2>&1; then
    echo "Missing required tool: ${CUELOOP_REQUIRED_TOOL}" >&2
    exit 2
  fi
done

if [[ -n "$(git -C "${CUELOOP_SOURCE_ROOT}" status --porcelain --untracked-files=no)" ]]; then
  echo "Tracked source tree is dirty; commit intended changes before verification" >&2
  exit 2
fi

if [[ -z "${CUELOOP_VERIFY_MODEL}" && "${CUELOOP_VERIFY_FETCH_MODEL}" -eq 0 ]]; then
  CUELOOP_CACHED_MODEL="${CUELOOP_SOURCE_ROOT}/models/artifacts/yamnet-classification-tflite-v1.tflite"
  if [[ -f "${CUELOOP_CACHED_MODEL}" ]]; then
    CUELOOP_VERIFY_MODEL="${CUELOOP_CACHED_MODEL}"
  fi
fi

mkdir -p "${CUELOOP_VERIFY_PARENT}"
CUELOOP_VERIFY_CONTAINER="$(mktemp -d "${CUELOOP_VERIFY_PARENT}/clean-checkout.XXXXXXXX")"
CUELOOP_VERIFY_ROOT="${CUELOOP_VERIFY_CONTAINER}/source"
CUELOOP_VERIFY_COMMIT="$(git -C "${CUELOOP_SOURCE_ROOT}" rev-parse HEAD)"

git clone --quiet --no-hardlinks --local "${CUELOOP_SOURCE_ROOT}" "${CUELOOP_VERIFY_ROOT}"
if [[ "$(git -C "${CUELOOP_VERIFY_ROOT}" rev-parse HEAD)" != "${CUELOOP_VERIFY_COMMIT}" ]]; then
  echo "Clean checkout commit mismatch" >&2
  exit 1
fi

cd "${CUELOOP_VERIFY_ROOT}"

if [[ -n "${CUELOOP_VERIFY_MODEL}" ]]; then
  mkdir -p models/artifacts
  cp "${CUELOOP_VERIFY_MODEL}" models/artifacts/yamnet-classification-tflite-v1.tflite
  python3 scripts/fetch_yamnet.py
  python3 scripts/sync_app_lab.py --include-model
elif [[ "${CUELOOP_VERIFY_FETCH_MODEL}" -eq 1 ]]; then
  python3 scripts/fetch_yamnet.py
  python3 scripts/sync_app_lab.py --include-model
else
  echo "Pinned model not supplied; model/package tests will report two expected skips"
fi

python3 scripts/audit_unoq_runtime.py --download
./scripts/test.sh
npx --yes pyright@1.1.413
./scripts/build_firmware.sh
python3 scripts/package_source_release.py --version clean-checkout

if [[ -f models/artifacts/yamnet-classification-tflite-v1.tflite ]]; then
  python3 scripts/sync_app_lab.py --check --include-model
  python3 scripts/package_app_lab.py --version clean-checkout
fi

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "Verification changed tracked files" >&2
  exit 1
fi

echo "Clean checkout verification passed"
echo "Commit: ${CUELOOP_VERIFY_COMMIT}"
echo "Preserved checkout: ${CUELOOP_VERIFY_ROOT}"
