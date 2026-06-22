from __future__ import annotations

from rclp_core.models import AuditEventType
from rclp_core.models import CapabilityLease
from rclp_ros2.command_gate import Command, CommandGate, GateResult


class EdgeAgentDaemon:
    def __init__(self, edge_agent_id: str, command_gate: CommandGate) -> None:
        self.edge_agent_id = edge_agent_id
        self.command_gate = command_gate

    def handle_command(self, command: Command, lease: CapabilityLease | None) -> GateResult:
        if command.edge_agent_id != self.edge_agent_id:
            event = self.command_gate.audit_log.record(
                event_type=AuditEventType.COMMAND_REJECTED,
                actor_id=self.edge_agent_id,
                robot_id=command.robot_id,
                mission_id=command.mission_id,
                correlation_id=command.correlation_id or command.command_id,
                summary=f"command {command.command_id} rejected: EDGE_AGENT_MISMATCH",
                payload={
                    "command_id": command.command_id,
                    "expected_edge_agent_id": self.edge_agent_id,
                    "command_edge_agent_id": command.edge_agent_id,
                    "reason_code": "EDGE_AGENT_MISMATCH",
                },
                related_message_ids=[command.command_id],
            )
            return GateResult(
                allowed=False,
                reason_code="EDGE_AGENT_MISMATCH",
                audit_id=event.audit_id,
            )
        return self.command_gate.evaluate(command, lease)
