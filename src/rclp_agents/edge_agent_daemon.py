from __future__ import annotations

from rclp_core.models import CapabilityLease
from rclp_core.models import RobotStateAssertion
from rclp_ros2.command_gate import Command, CommandGate, GateResult


class EdgeAgentDaemon:
    def __init__(self, edge_agent_id: str, command_gate: CommandGate) -> None:
        if command_gate.local_edge_agent_id != edge_agent_id:
            raise ValueError("command gate local edge does not match daemon edge")
        self.edge_agent_id = edge_agent_id
        self.command_gate = command_gate

    def handle_command(
        self,
        command: Command,
        lease: CapabilityLease | None,
        current_state: RobotStateAssertion | None = None,
    ) -> GateResult:
        return self.command_gate.evaluate(command, lease, current_state=current_state)
