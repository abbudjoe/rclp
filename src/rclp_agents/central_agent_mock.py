from __future__ import annotations

from rclp_core.crypto import DemoKeyPair
from rclp_core.models import Capability, CapabilityRequest


def request_remote_assist(signing_key: DemoKeyPair) -> CapabilityRequest:
    request = CapabilityRequest(
        requesting_agent_id="fleet-agent:v0.1",
        authenticated_agent_id="fleet-agent:v0.1",
        edge_agent_id="edge-agent:rover-001",
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.REMOTE_ASSIST,
        reason="central mock requests remote assist",
    )
    request.signature = signing_key.sign(request)
    return request
