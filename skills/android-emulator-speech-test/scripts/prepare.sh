#!/usr/bin/env bash
# Explicit local setup only: no SDK downloads, emulator boot, app or device operation.
set -euo pipefail
umask 077
[[ $# -eq 2 ]] || { echo 'Usage: prepare.sh ABSOLUTE_SDK_DIR ABSOLUTE_CACHE_DIR' >&2; exit 2; }
sdk="$1"
cache="$2"
[[ "$sdk" = /* && "$cache" = /* && -f "$sdk/emulator/lib/emulator_controller.proto" ]] || { echo 'Select an installed SDK and an absolute private cache directory.' >&2; exit 2; }
root=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$cache"
[[ ! -L "$cache" && -O "$cache" ]] || { echo 'Cache must be an owned directory, not a symlink.' >&2; exit 2; }
python3 - "$cache" <<'PY_CHECK'
from pathlib import Path
import os, stat, sys
cache = Path(sys.argv[1])
info = os.lstat(cache)
if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
    raise SystemExit("Cache must already be private (0700); choose a fresh cache directory.")
# Validate both destinations before venv/pip or protoc can follow a preexisting redirect.
for name in ("python", "stubs"):
    path = cache / name
    if os.path.lexists(path):
        child = os.lstat(path)
        if not stat.S_ISDIR(child.st_mode) or child.st_uid != os.getuid() or child.st_mode & 0o077:
            raise SystemExit("Cache child must be a private owned directory, never a symlink.")
PY_CHECK
python3 -m venv "$cache/python"
"$cache/python/bin/python" -m pip install --only-binary=:all: -r "$root/requirements.txt"
include=$("$cache/python/bin/python" -c 'import grpc_tools,pathlib; print(pathlib.Path(grpc_tools.__file__).parent / "_proto")')
mkdir -p "$cache/stubs"
"$cache/python/bin/python" -m grpc_tools.protoc -I"$sdk/emulator/lib" -I"$include" \
  --python_out="$cache/stubs" --grpc_python_out="$cache/stubs" "$sdk/emulator/lib/emulator_controller.proto"
echo 'Prepared local Python environment and SDK-derived clients. No emulator or ASR test ran.'
