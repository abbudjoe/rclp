#!/usr/bin/env bash
set -euo pipefail

section() {
  printf '\n== %s ==\n' "$1"
}

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

section "Python"
"$PYTHON" --version

section "Compile Python sources"
"$PYTHON" -m compileall src tests

section "Pytest"
"$PYTHON" -m pytest

section "Deterministic evals"
"$PYTHON" tests/evals/eval_runner.py

section "Ruff"
if "$PYTHON" -m ruff --version >/dev/null 2>&1; then
  "$PYTHON" -m ruff check .
  "$PYTHON" -m ruff format --check .
else
  printf 'Ruff is declared as a dev dependency but is unavailable for %s.\n' "$PYTHON" >&2
  printf "Install dev dependencies with: %s -m pip install -e '.[dev]'\n" "$PYTHON" >&2
  exit 1
fi

section "Rust"
if [[ -f "Cargo.toml" ]]; then
  if command -v cargo >/dev/null 2>&1; then
    cargo fmt --all -- --check
    cargo clippy --workspace --all-targets -- -D warnings
    cargo test --workspace
  else
    printf 'Cargo unavailable; skipping Rust workspace checks.\n'
  fi
else
  printf 'No Cargo.toml found; skipping Rust checks.\n'
fi

section "Validation complete"
printf 'Local validation checks completed successfully.\n'
