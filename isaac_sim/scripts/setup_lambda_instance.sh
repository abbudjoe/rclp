#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

echo "RCLP Lambda/Isaac local prerequisite check"
echo "This script is credential-free. Do not add Lambda API keys or account-specific values."

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
    PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

"${PYTHON_BIN}" --version

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "nvidia-smi not found; run this on the Lambda GPU instance after launch."
fi

if command -v ros2 >/dev/null 2>&1; then
  ros2 --version || true
else
  echo "ros2 not found on PATH; source /opt/ros/<distro>/setup.bash before ROS 2 bridge tests."
fi

if [[ -n "${ISAAC_SIM_ROOT:-}" ]]; then
  echo "ISAAC_SIM_ROOT=${ISAAC_SIM_ROOT}"
else
  echo "ISAAC_SIM_ROOT is unset; set it after Isaac Sim is installed or mounted."
fi

echo "Repository root: ${REPO_ROOT}"
