#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
    PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
RCLP_REMOTE_ASSIST_REQUEST_TOPIC="${RCLP_REMOTE_ASSIST_REQUEST_TOPIC:-/rclp/remote_assist/request}"
RCLP_REMOTE_ASSIST_ACCEPTED_TOPIC="${RCLP_REMOTE_ASSIST_ACCEPTED_TOPIC:-/sim/remote_assist/accepted}"
RCLP_FALLBACK_TOPIC="${RCLP_FALLBACK_TOPIC:-/rclp/fallback}"

export ROS_DOMAIN_ID

echo "RCLP ROS 2 command-gate placeholder"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
echo "Candidate command topic: ${RCLP_REMOTE_ASSIST_REQUEST_TOPIC}"
echo "Accepted simulator topic: ${RCLP_REMOTE_ASSIST_ACCEPTED_TOPIC}"
echo "Fallback topic: ${RCLP_FALLBACK_TOPIC}"
echo
echo "Future adapter contract:"
echo "  1. subscribe to the candidate command topic"
echo "  2. convert each message into rclp_ros2.command_gate.Command"
echo "  3. call CommandGate.evaluate(command, lease, current_state)"
echo "  4. publish only allowed commands to the accepted simulator topic"
echo "  5. publish fallback/audit output on rejection"
echo

if command -v ros2 >/dev/null 2>&1; then
  echo "ROS 2 is available. Current visible topics:"
  ros2 topic list || true
else
  echo "ros2 is not on PATH. Source the ROS 2 environment before bridge testing."
fi

echo
echo "Running the local RCLP proof next to the ROS 2/Isaac shell context."
"${PYTHON_BIN}" -m rclp_agents.demo_remote_assist \
  --network-profile "${RCLP_NETWORK_PROFILE:-degraded_teleop}"
