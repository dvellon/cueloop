#!/usr/bin/env bash
set -euo pipefail

CUELOOP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CUELOOP_ARDUINO_CLI="${CUELOOP_ARDUINO_CLI:-arduino-cli}"
CUELOOP_BUILD_TMPDIR="${CUELOOP_BUILD_TMPDIR:-/home/cd/.tmp-codex}"
CUELOOP_BUILD_CACHE="${CUELOOP_BUILD_CACHE:-${CUELOOP_ROOT}/.cache}"

# A fixed project build timestamp plus checkout-root prefix maps make ESP32's
# __DATE__/__TIME__ strings and embedded ELF digest stable across checkouts.
readonly CUELOOP_SOURCE_DATE_EPOCH=1788307200

if ! command -v "${CUELOOP_ARDUINO_CLI}" >/dev/null 2>&1; then
  echo "arduino-cli is required; no tool or platform is installed by this script" >&2
  exit 2
fi
if [[ ! -d "${CUELOOP_BUILD_TMPDIR}" || ! -w "${CUELOOP_BUILD_TMPDIR}" ]]; then
  echo "Build TMPDIR is missing or not writable: ${CUELOOP_BUILD_TMPDIR}" >&2
  exit 2
fi

cd "${CUELOOP_ROOT}"

command -v "${CUELOOP_ARDUINO_CLI}"
"${CUELOOP_ARDUINO_CLI}" version
"${CUELOOP_ARDUINO_CLI}" core list
"${CUELOOP_ARDUINO_CLI}" board details --fqbn esp32:esp32:XIAO_ESP32S3 >/dev/null
"${CUELOOP_ARDUINO_CLI}" board details --fqbn arduino:zephyr:unoq >/dev/null

CUELOOP_PREFIX_FLAGS="-ffile-prefix-map=${CUELOOP_ROOT}=. -fdebug-prefix-map=${CUELOOP_ROOT}=."

SOURCE_DATE_EPOCH="${CUELOOP_SOURCE_DATE_EPOCH}" \
XDG_CACHE_HOME="${CUELOOP_BUILD_CACHE}" \
TMPDIR="${CUELOOP_BUILD_TMPDIR}" \
"${CUELOOP_ARDUINO_CLI}" compile \
  --clean \
  --fqbn esp32:esp32:XIAO_ESP32S3 \
  --build-property "compiler.c.extra_flags=${CUELOOP_PREFIX_FLAGS}" \
  --build-property "compiler.cpp.extra_flags=${CUELOOP_PREFIX_FLAGS}" \
  --build-property "compiler.S.extra_flags=${CUELOOP_PREFIX_FLAGS}" \
  --build-path firmware/xiao_cuepod/build/work \
  --output-dir firmware/xiao_cuepod/build/artifacts \
  firmware/xiao_cuepod

SOURCE_DATE_EPOCH="${CUELOOP_SOURCE_DATE_EPOCH}" \
XDG_CACHE_HOME="${CUELOOP_BUILD_CACHE}" \
TMPDIR="${CUELOOP_BUILD_TMPDIR}" \
"${CUELOOP_ARDUINO_CLI}" compile \
  --clean \
  --fqbn arduino:zephyr:unoq \
  --build-path firmware/uno_q_cue_controller/build/work \
  --output-dir firmware/uno_q_cue_controller/build/artifacts \
  firmware/uno_q_cue_controller

SOURCE_DATE_EPOCH="${CUELOOP_SOURCE_DATE_EPOCH}" \
XDG_CACHE_HOME="${CUELOOP_BUILD_CACHE}" \
TMPDIR="${CUELOOP_BUILD_TMPDIR}" \
"${CUELOOP_ARDUINO_CLI}" compile \
  --clean \
  --profile uno_q \
  --build-path app_lab/CueLoop/build/sketch-work \
  --output-dir app_lab/CueLoop/build/sketch-artifacts \
  app_lab/CueLoop/sketch

cmp \
  firmware/uno_q_cue_controller/build/artifacts/uno_q_cue_controller.ino.bin \
  app_lab/CueLoop/build/sketch-artifacts/sketch.ino.bin
cmp \
  firmware/uno_q_cue_controller/build/artifacts/uno_q_cue_controller.ino.bin-zsk.bin \
  app_lab/CueLoop/build/sketch-artifacts/sketch.ino.bin-zsk.bin

sha256sum \
  firmware/xiao_cuepod/build/artifacts/xiao_cuepod.ino.bin \
  firmware/xiao_cuepod/build/artifacts/xiao_cuepod.ino.merged.bin \
  firmware/uno_q_cue_controller/build/artifacts/uno_q_cue_controller.ino.bin \
  firmware/uno_q_cue_controller/build/artifacts/uno_q_cue_controller.ino.bin-zsk.bin \
  app_lab/CueLoop/build/sketch-artifacts/sketch.ino.bin \
  app_lab/CueLoop/build/sketch-artifacts/sketch.ino.bin-zsk.bin
