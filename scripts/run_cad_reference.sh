#!/usr/bin/env bash
set -euo pipefail

CUELOOP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REFERENCE_SCRIPT="${CUELOOP_ROOT}/cad/reference/freecad_reference.py"
LOCAL_APPRUN="${CUELOOP_ROOT}/.tools/squashfs-root/AppRun"
FREECAD_STATE="${CUELOOP_ROOT}/.tools/freecad-home"
FREECAD_CONFIG="${CUELOOP_ROOT}/.tools/freecad-config"
FREECAD_CACHE="${CUELOOP_ROOT}/.tools/freecad-cache"

install -d "${FREECAD_STATE}" "${FREECAD_CONFIG}" "${FREECAD_CACHE}"

if command -v FreeCADCmd >/dev/null 2>&1; then
  FREECAD_USER_HOME="${FREECAD_STATE}" \
    XDG_CONFIG_HOME="${FREECAD_CONFIG}" \
    XDG_CACHE_HOME="${FREECAD_CACHE}" \
    FreeCADCmd "${REFERENCE_SCRIPT}"
elif command -v freecadcmd >/dev/null 2>&1; then
  FREECAD_USER_HOME="${FREECAD_STATE}" \
    XDG_CONFIG_HOME="${FREECAD_CONFIG}" \
    XDG_CACHE_HOME="${FREECAD_CACHE}" \
    freecadcmd "${REFERENCE_SCRIPT}"
elif [[ -x "${LOCAL_APPRUN}" ]]; then
  FREECAD_USER_HOME="${FREECAD_STATE}" \
    XDG_CONFIG_HOME="${FREECAD_CONFIG}" \
    XDG_CACHE_HOME="${FREECAD_CACHE}" \
    "${LOCAL_APPRUN}" freecadcmd "${REFERENCE_SCRIPT}"
else
  printf '%s\n' \
    'FreeCADCmd is unavailable.' \
    'Install the official stable FreeCAD package or place/extract the documented' \
    'checksum-verified AppImage under .tools/ before running this script.' >&2
  exit 2
fi

python3 "${CUELOOP_ROOT}/cad/validate_cad.py" \
  --reference-output "${CUELOOP_ROOT}/cad/reference_exports" \
  --write-report "${CUELOOP_ROOT}/cad/reference_exports/host_validation.json"
