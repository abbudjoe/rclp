from __future__ import annotations

import json
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from rclp_core.audit import AuditLog
from rclp_core.crypto import DemoKeyPair
from rclp_core.leases import issue_lease
from rclp_core.models import (
    AgentAttestation,
    AuditEventType,
    Capability,
    CapabilityConstraintRequirement,
    CapabilityDecision,
    CapabilityRequest,
    Decision,
    FallbackAction,
    GeofenceState,
    LeaseRevocation,
    MissionContext,
    RobotIdentity,
    RobotStateAssertion,
)
from rclp_core.network import profile, profile_names
from rclp_core.policy import Policy, RequestReplayCache, evaluate_policy, policy_digest
from rclp_ros2.command_gate import (
    Command,
    CommandGate,
    CommandReplayCache,
    GateResult,
    RevocationStore,
)

CORRELATION_ID = "corr_demo_remote_assist"
CENTRAL_AGENT_ID = "fleet-agent:v0.1"
EDGE_AGENT_ID = "edge-agent:rover-001"
ROBOT_ID = "rover-001"
MISSION_ID = "mission-001"
GEOFENCE_ID = "test-zone-a"
POLICY_PATH = "examples/policies/remote_assist_policy.yaml"
ISSUER_ID = "rclp-demo-issuer"


def make_state(network_profile: str, key: DemoKeyPair) -> RobotStateAssertion:
    state = RobotStateAssertion(
        correlation_id=CORRELATION_ID,
        robot_id=ROBOT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        authenticated_edge_agent_id=EDGE_AGENT_ID,
        mission_id=MISSION_ID,
        network_state=profile(network_profile),
        geofence_state=GeofenceState(geofence_id=GEOFENCE_ID, inside=True),
    )
    state.signature = key.sign(state)
    return state


def audit(
    log: AuditLog,
    event_type: AuditEventType,
    actor_id: str,
    summary: str,
    payload: dict | None = None,
    *,
    authority_relevant: bool = True,
) -> str:
    event = log.record(
        correlation_id=CORRELATION_ID,
        event_type=event_type,
        actor_id=actor_id,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        summary=summary,
        payload=payload or {},
        authority_relevant=authority_relevant,
    )
    return event.audit_id


def print_json(title: str, payload: object) -> None:
    print(f"\n### {title}")
    if hasattr(payload, "model_dump_json"):
        print(payload.model_dump_json(indent=2))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


def command_denial_payload(
    *,
    summary: str,
    audit_id: str,
    gate_result: GateResult,
    safe_alternatives: list[FallbackAction],
    retry_after_seconds: int | None,
) -> dict:
    return {
        "decision": "deny",
        "reason_code": gate_result.reason_code,
        "summary": summary,
        "safe_alternatives": safe_alternatives,
        "retry_after_seconds": retry_after_seconds,
        "audit_id": audit_id,
        "gate_result": gate_result.model_dump(mode="json"),
    }


def sign_command(command: Command, key: DemoKeyPair) -> Command:
    command.authenticated_agent_id = command.agent_id
    command.signature = None
    command.signature = key.sign(command)
    return command


def make_command(command_id_prefix: str, key: DemoKeyPair) -> Command:
    command = Command(
        correlation_id=CORRELATION_ID,
        command_id=f"{command_id_prefix}_{uuid4().hex}",
        agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        capability=Capability.REMOTE_ASSIST.value,
        payload={"intent": "start_remote_assist", "max_speed_mps": 0.6},
    )
    return sign_command(command, key)


def sign_request(request: CapabilityRequest, key: DemoKeyPair) -> CapabilityRequest:
    request.authenticated_agent_id = request.requesting_agent_id
    request.signature = None
    request.signature = key.sign(request)
    return request


def sign_revocation(revocation: LeaseRevocation, key: DemoKeyPair) -> LeaseRevocation:
    revocation.signature = None
    revocation.signature = key.sign(revocation)
    return revocation


def main(impaired_network_profile: str = "degraded_teleop") -> None:
    log = AuditLog()
    central_key = DemoKeyPair()
    edge_key = DemoKeyPair()
    issuer_key = DemoKeyPair()
    policy = Policy.from_yaml(POLICY_PATH)
    agent_public_keys_by_id = {CENTRAL_AGENT_ID: central_key.public_key_b64}
    edge_public_keys_by_id = {EDGE_AGENT_ID: edge_key.public_key_b64}
    runtime_store_dir = TemporaryDirectory(prefix="rclp-demo-stores-")
    runtime_store_path = Path(runtime_store_dir.name)
    replay_cache = RequestReplayCache(runtime_store_path / "request_replay.sqlite3")
    active_policy_digest = policy_digest(policy)
    accepted_policy_digests = {active_policy_digest}
    gate = CommandGate(
        issuer_public_key_b64=issuer_key.public_key_b64,
        local_edge_agent_id=EDGE_AGENT_ID,
        trusted_issuer_ids={ISSUER_ID},
        trusted_revoker_ids={EDGE_AGENT_ID},
        accepted_capabilities={Capability.REMOTE_ASSIST.value},
        accepted_policy_id=policy.policy_id,
        accepted_policy_digests=accepted_policy_digests,
        issuer_capability_scopes={ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
        capability_constraint_requirements={
            Capability.REMOTE_ASSIST.value: CapabilityConstraintRequirement(
                capability=Capability.REMOTE_ASSIST,
                require_geofence_id=True,
                require_network_thresholds=True,
                require_fallback_on_degrade=True,
            )
        },
        agent_public_keys_by_id=agent_public_keys_by_id,
        revoker_public_keys_by_id=edge_public_keys_by_id,
        state_public_keys_by_edge_id=edge_public_keys_by_id,
        command_replay_cache=CommandReplayCache(runtime_store_path / "command_replay.sqlite3"),
        revocation_store=RevocationStore(runtime_store_path / "revocations.sqlite3"),
        audit_log=log,
    )
    impaired_profile_state = profile(impaired_network_profile)

    central_identity = AgentAttestation(
        agent_id=CENTRAL_AGENT_ID,
        kind="central_agent",
        manifest_digest="sha256:demo-central-agent-v0.1",
        public_key_id="demo-central-ed25519-non-production",
    )
    edge_identity = AgentAttestation(
        agent_id=EDGE_AGENT_ID,
        kind="edge_agent",
        manifest_digest="sha256:demo-edge-agent-v0.1",
        public_key_id="demo-edge-ed25519-non-production",
    )
    robot = RobotIdentity(
        robot_id=ROBOT_ID,
        hardware_id="demo-hardware-rover-001",
        edge_agent_id=EDGE_AGENT_ID,
    )
    mission = MissionContext(
        mission_id=MISSION_ID,
        mission_type="warehouse_remote_assist_demo",
        human_operator_available=True,
    )
    geofence = GeofenceState(geofence_id=GEOFENCE_ID, inside=True)

    print("RCLP remote_assist local protocol demonstration")
    print("Safety note: RCLP is a safety-adjacent authority layer, not a certified safety system.")
    print("All keys, agents, robot state, network state, and audit events are local demo fixtures.")
    print_json(
        "setup",
        {
            "central_agent": central_identity.model_dump(mode="json"),
            "edge_agent": edge_identity.model_dump(mode="json"),
            "robot": robot.model_dump(mode="json"),
            "mission": mission.model_dump(mode="json"),
            "geofence": geofence.model_dump(mode="json"),
            "policy_id": policy.policy_id,
            "policy_path": POLICY_PATH,
            "remote_assist_network_thresholds": policy.requirements.network.model_dump(),
            "deterministic_network_profiles": profile_names(),
            "impaired_demo_profile": impaired_profile_state.profile,
        },
    )
    audit(
        log,
        AuditEventType.DEMO_SETUP,
        EDGE_AGENT_ID,
        "created local central agent, edge agent, robot, mission, geofence, and policy",
        {
            "central_agent_id": CENTRAL_AGENT_ID,
            "edge_agent_id": EDGE_AGENT_ID,
            "robot_id": ROBOT_ID,
            "mission_id": MISSION_ID,
            "geofence_id": GEOFENCE_ID,
            "policy_id": policy.policy_id,
        },
        authority_relevant=False,
    )

    request = CapabilityRequest(
        correlation_id=CORRELATION_ID,
        requesting_agent_id=CENTRAL_AGENT_ID,
        authenticated_agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        capability=Capability.REMOTE_ASSIST,
        reason="low-confidence obstacle negotiation",
        requested_duration_seconds=600,
    )
    sign_request(request, central_key)
    audit(
        log,
        AuditEventType.CAPABILITY_REQUESTED,
        request.requesting_agent_id,
        "central agent requested remote_assist",
        request.model_dump(mode="json"),
    )
    print_json("capability_request", request)

    normal_state = make_state("normal", edge_key)
    audit(
        log,
        AuditEventType.NETWORK_STATE_ASSERTED,
        EDGE_AGENT_ID,
        "normal network state observed for remote_assist request",
        normal_state.model_dump(mode="json"),
    )
    decision, reason, alternatives, constraints, decision_audit = evaluate_policy(
        request,
        normal_state,
        policy,
        audit_log=log,
        deciding_actor_id=ISSUER_ID,
        agent_public_keys_by_id=agent_public_keys_by_id,
        edge_public_keys_by_id=edge_public_keys_by_id,
        accepted_policy_digests=accepted_policy_digests,
        replay_cache=replay_cache,
    )
    if decision == Decision.ALLOW and constraints:
        lease = issue_lease(
            request,
            constraints,
            ISSUER_ID,
            issuer_key,
            policy.lease_ttl_seconds,
            policy_id=policy.policy_id,
            policy_digest=active_policy_digest,
        )
    else:
        lease = None

    cap_decision = CapabilityDecision(
        correlation_id=request.correlation_id,
        request_id=request.message_id,
        decision=decision,
        reason_code=reason,
        deciding_actor_id=ISSUER_ID,
        policy_id=policy.policy_id,
        policy_digest=active_policy_digest,
        lease=lease,
        safe_alternatives=alternatives,
        audit_id=decision_audit.audit_id,
    )
    print_json("normal_network_decision", cap_decision)

    command = make_command("cmd_valid_lease", central_key)
    gate_result = gate.evaluate(command, lease, current_state=normal_state)
    print_json("command_gate_with_valid_lease", gate_result)

    no_lease_command = make_command("cmd_no_lease", central_key)
    no_lease_result = gate.evaluate(no_lease_command, None, current_state=normal_state)
    no_lease_summary = "command without a valid lease was rejected"
    print_json(
        "command_without_valid_lease",
        command_denial_payload(
            summary=no_lease_summary,
            audit_id=no_lease_result.audit_id or "",
            gate_result=no_lease_result,
            safe_alternatives=[FallbackAction.LOCAL_AUTONOMY_ONLY],
            retry_after_seconds=None,
        ),
    )

    degraded_state = make_state(impaired_network_profile, edge_key)
    audit(
        log,
        AuditEventType.NETWORK_STATE_ASSERTED,
        EDGE_AGENT_ID,
        f"network profile changed to {impaired_network_profile}",
        degraded_state.model_dump(mode="json"),
    )
    degraded_request = CapabilityRequest(
        correlation_id=CORRELATION_ID,
        requesting_agent_id=CENTRAL_AGENT_ID,
        authenticated_agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        capability=Capability.REMOTE_ASSIST,
        reason="network impairment authority reevaluation",
        requested_duration_seconds=600,
    )
    sign_request(degraded_request, central_key)
    audit(
        log,
        AuditEventType.CAPABILITY_REQUESTED,
        degraded_request.requesting_agent_id,
        "central agent requested remote_assist after network impairment",
        degraded_request.model_dump(mode="json"),
    )
    degraded_decision, degraded_reason, degraded_alts, _, degraded_audit = evaluate_policy(
        degraded_request,
        degraded_state,
        policy,
        audit_log=log,
        deciding_actor_id=ISSUER_ID,
        agent_public_keys_by_id=agent_public_keys_by_id,
        edge_public_keys_by_id=edge_public_keys_by_id,
        accepted_policy_digests=accepted_policy_digests,
        replay_cache=replay_cache,
    )
    degraded_cap_decision = CapabilityDecision(
        correlation_id=degraded_request.correlation_id,
        request_id=degraded_request.message_id,
        decision=degraded_decision,
        reason_code=degraded_reason,
        deciding_actor_id=ISSUER_ID,
        policy_id=policy.policy_id,
        policy_digest=active_policy_digest,
        lease=None,
        safe_alternatives=degraded_alts,
        audit_id=degraded_audit.audit_id,
    )
    print_json("impaired_network_decision", degraded_cap_decision)

    impaired_fallback = degraded_alts[0] if degraded_alts else FallbackAction.CRAWL_TO_SAFE_ZONE
    if lease:
        revocation = LeaseRevocation(
            correlation_id=CORRELATION_ID,
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="NETWORK_PROFILE_REVOKE",
            fallback_action=impaired_fallback,
            robot_id=ROBOT_ID,
            mission_id=MISSION_ID,
            capability=Capability.REMOTE_ASSIST,
        )
        sign_revocation(revocation, edge_key)
        revocation_fallback = gate.revoke(revocation, lease=lease)
        assert revocation_fallback is not None
        print_json("lease_revocation", revocation)

    revoked_command = make_command("cmd_after_revocation", central_key)
    revoked_result = gate.evaluate(revoked_command, lease, current_state=degraded_state)
    revoked_summary = (
        f"command after network-profile revocation rejected: {revoked_result.reason_code}"
    )
    print_json(
        "command_gate_after_network_revocation",
        command_denial_payload(
            summary=revoked_summary,
            audit_id=revoked_result.audit_id or "",
            gate_result=revoked_result,
            safe_alternatives=[impaired_fallback],
            retry_after_seconds=30,
        ),
    )

    print("\n### audit_jsonl")
    print(log.to_jsonl())

    print("\n### incident_replay_summary")
    print(log.replay_summary())


def cli() -> None:
    parser = ArgumentParser(description="Run the local RCLP remote_assist authority demo.")
    parser.add_argument(
        "--network-profile",
        choices=[name for name in profile_names() if name != "normal"],
        default="degraded_teleop",
        help="deterministic impaired profile to apply after the initial normal-network lease",
    )
    args = parser.parse_args()
    main(impaired_network_profile=args.network_profile)


if __name__ == "__main__":
    cli()
