#!/usr/bin/env bash
set -euo pipefail

find_python() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    printf '%s\n' "$PYTHON_BIN"
  elif [[ -x ".venv/bin/python" ]]; then
    printf '%s\n' ".venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    command -v python3
  else
    command -v python
  fi
}

PYTHON="$(find_python)"

cat <<'TEXT'
RCLP validation demo

This demo shows the local remote_assist authority flow:
central agent request -> edge verification -> scoped lease -> command gate ->
network degradation/revocation -> fallback declaration -> audit replay.

Speaker notes: docs/DEMO_WALKTHROUGH.md
Safety note: RCLP is a safety-adjacent authority layer, not a certified safety system.

TEXT

"$PYTHON" -m rclp_agents.demo_remote_assist "$@"
