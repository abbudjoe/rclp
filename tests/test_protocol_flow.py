from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from rclp_agents.edge_agent_daemon import EdgeAgentDaemon
from rclp_core.audit import AuditLog
from rclp_core.crypto import DemoKeyPair
from rclp_core.leases import issue_lease
from rclp_core.models import (
    AuditEventType,
    Capability,
    CapabilityConstraintRequirement,
    CapabilityLease,
    CapabilityRequest,
    FallbackAction,
    GeofenceState,
    LeaseConstraints,
    LeaseRevocation,
    NetworkProfile,
    NetworkState,
    RobotStateAssertion,
    SafetyState,
)
from rclp_core.network import profile, profile_names
from rclp_core.policy import (
    Policy,
    RequestReplayCache,
    _evaluate_policy_inputs,
    evaluate_policy,
    policy_constraint_bounds,
    policy_digest,
)
from rclp_ros2.command_gate import Command, CommandGate, CommandReplayCache, RevocationStore


CENTRAL_AGENT_ID = "fleet-agent:v0.1"
EDGE_AGENT_ID = "edge-agent:rover-001"
TRUSTED_ISSUER_ID = "issuer"
CENTRAL_KEY = DemoKeyPair()
EDGE_KEY = DemoKeyPair()
_TEST_STORE_DIRS: list[TemporaryDirectory[str]] = []


def sign_request(request: CapabilityRequest, key: DemoKeyPair = CENTRAL_KEY) -> CapabilityRequest:
    request.authenticated_agent_id = request.requesting_agent_id
    request.signature = None
    request.signature = key.sign(request)
    return request


def sign_state(state: RobotStateAssertion, key: DemoKeyPair = EDGE_KEY) -> RobotStateAssertion:
    state.authenticated_edge_agent_id = state.edge_agent_id
    state.signature = None
    state.signature = key.sign(state)
    return state


def sign_revocation(
    revocation: LeaseRevocation,
    key: DemoKeyPair = EDGE_KEY,
) -> LeaseRevocation:
    revocation.signature = None
    revocation.signature = key.sign(revocation)
    return revocation


def sign_command(command: Command, key: DemoKeyPair = CENTRAL_KEY) -> Command:
    command.authenticated_agent_id = command.agent_id
    command.signature = None
    command.signature = key.sign(command)
    return command


def make_request(**updates) -> CapabilityRequest:
    request = CapabilityRequest(
        requesting_agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.REMOTE_ASSIST,
        reason="test",
        requested_duration_seconds=600,
    )
    if updates:
        request = request.model_copy(update=updates)
    return sign_request(request)


def make_state(network_profile: str = "normal") -> RobotStateAssertion:
    return sign_state(
        RobotStateAssertion(
            robot_id="rover-001",
            edge_agent_id=EDGE_AGENT_ID,
            mission_id="mission-001",
            safety_state=SafetyState.NOMINAL,
            network_state=profile(network_profile),
            geofence_state=GeofenceState(geofence_id="test-zone-a", inside=True),
            human_operator_available=True,
        )
    )


def make_command(**updates) -> Command:
    command = Command(
        correlation_id="cmd_test",
        command_id="cmd_test",
        agent_id="fleet-agent:v0.1",
        edge_agent_id="edge-agent:rover-001",
        robot_id="rover-001",
        mission_id="mission-001",
        capability="remote_assist",
        payload={},
    )
    if updates:
        command = command.model_copy(update=updates)
    return sign_command(command)


def make_policy() -> Policy:
    return Policy.from_yaml("examples/policies/remote_assist_policy.yaml")


def _test_store_path(filename: str) -> Path:
    tempdir = TemporaryDirectory(prefix="rclp-test-stores-")
    _TEST_STORE_DIRS.append(tempdir)
    return Path(tempdir.name) / filename


def durable_request_replay_cache() -> RequestReplayCache:
    return RequestReplayCache(_test_store_path("request_replay.sqlite3"))


def durable_command_replay_cache() -> CommandReplayCache:
    return CommandReplayCache(_test_store_path("command_replay.sqlite3"))


def durable_revocation_store() -> RevocationStore:
    return RevocationStore(_test_store_path("revocations.sqlite3"))


def policy_trust_kwargs(policy: Policy) -> dict:
    return {
        "agent_public_keys_by_id": {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        "edge_public_keys_by_id": {EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        "accepted_policy_digests": {policy_digest(policy)},
        "replay_cache": durable_request_replay_cache(),
    }


def evaluate_inputs(
    request: CapabilityRequest,
    state: RobotStateAssertion,
    policy: Policy,
):
    return _evaluate_policy_inputs(request, state, policy, **policy_trust_kwargs(policy))


def make_gate(key: DemoKeyPair, **kwargs) -> CommandGate:
    policy = make_policy()
    kwargs.setdefault("accepted_capabilities", {Capability.REMOTE_ASSIST.value})
    kwargs.setdefault("accepted_policy_id", policy.policy_id)
    kwargs.setdefault("accepted_policy_digests", {policy_digest(policy)})
    kwargs.setdefault(
        "issuer_capability_scopes",
        {TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
    )
    kwargs.setdefault(
        "capability_constraint_requirements",
        {
            Capability.REMOTE_ASSIST.value: CapabilityConstraintRequirement(
                capability=Capability.REMOTE_ASSIST,
                require_geofence_id=True,
                require_network_thresholds=True,
                require_fallback_on_degrade=True,
            )
        },
    )
    kwargs.setdefault("capability_constraint_bounds", policy_constraint_bounds(policy))
    kwargs.setdefault(
        "agent_public_keys_by_id",
        {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
    )
    kwargs.setdefault(
        "state_public_keys_by_edge_id",
        {EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
    )
    kwargs.setdefault("command_replay_cache", durable_command_replay_cache())
    kwargs.setdefault("revocation_store", durable_revocation_store())
    return CommandGate(
        key.public_key_b64,
        local_edge_agent_id=EDGE_AGENT_ID,
        trusted_issuer_ids={TRUSTED_ISSUER_ID},
        trusted_revoker_ids={EDGE_AGENT_ID},
        revoker_public_keys_by_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        **kwargs,
    )


def state_with_network_updates(**updates) -> RobotStateAssertion:
    return sign_state(
        make_state("normal").model_copy(
            update={"network_state": profile("normal").model_copy(update=updates)}
        )
    )


def state_with_unknown_network() -> RobotStateAssertion:
    return sign_state(
        make_state("normal").model_copy(
            update={
                "network_state": NetworkState(
                    profile=NetworkProfile.UNKNOWN,
                    attached=True,
                    latency_ms_p95=45,
                    packet_loss_pct=0.1,
                    uplink_mbps=8.0,
                )
            }
        )
    )


def issue_valid_lease(key: DemoKeyPair) -> CapabilityLease:
    policy = make_policy()
    request = make_request()
    _, _, _, constraints = evaluate_inputs(request, make_state("normal"), policy)
    assert constraints is not None
    return issue_lease(
        request,
        constraints,
        TRUSTED_ISSUER_ID,
        key,
        600,
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )


def test_normal_network_allows_lease_and_command_gate_accepts():
    key = DemoKeyPair()
    gate = make_gate(key)
    policy = make_policy()
    request = make_request()
    decision, reason, _, constraints = evaluate_inputs(request, make_state("normal"), policy)
    assert decision == "allow"
    assert reason == "POLICY_SATISFIED"
    assert constraints is not None
    lease = issue_lease(
        request,
        constraints,
        "issuer",
        key,
        600,
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )
    result = gate.evaluate(make_command(), lease, current_state=make_state("normal"))
    assert result.allowed is True
    assert result.reason_code == "LEASE_VALID"
    assert result.audit_id == gate.audit_log.events[-1].audit_id
    assert gate.audit_log.events[-1].event_type == AuditEventType.COMMAND_ALLOWED
    assert gate.audit_log.events[-1].payload["reason_code"] == "LEASE_VALID"
    assert result.fallback_declaration is None
    assert gate.fallback_events == []


def test_protocol_objects_round_trip_through_json():
    request = make_request()
    restored_request = CapabilityRequest.model_validate_json(request.model_dump_json())
    assert restored_request == request

    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    restored_lease = CapabilityLease.model_validate_json(lease.model_dump_json())
    assert restored_lease == lease


def test_deterministic_network_profiles_are_typed_and_stable():
    assert profile_names() == ["normal", "degraded_teleop", "uplink_bad", "partition"]

    normal = profile("normal")
    same_normal = profile(NetworkProfile.NORMAL)
    assert normal == same_normal
    assert normal.profile == NetworkProfile.NORMAL

    normal.latency_ms_p95 = 999
    assert profile("normal").latency_ms_p95 == 45

    partition = profile("partition")
    assert partition.profile == NetworkProfile.PARTITION
    assert partition.attached is False
    assert partition.packet_loss_pct == 100.0
    assert partition.uplink_mbps == 0.0


def test_degraded_network_degrades_remote_assist_authority():
    policy = make_policy()
    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(), make_state("degraded_teleop"), policy
    )
    assert decision == "degrade"
    assert reason == "NETWORK_LATENCY_DEGRADED"
    assert alternatives == [FallbackAction.CRAWL_TO_SAFE_ZONE]
    assert constraints is None


def test_unknown_network_state_denies_remote_assist_authority():
    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(), state_with_unknown_network(), make_policy()
    )
    assert decision == "deny"
    assert reason == "NETWORK_STATE_UNKNOWN"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


@pytest.mark.parametrize(
    ("state", "expected_reason"),
    [
        (state_with_network_updates(latency_ms_p95=90), "NETWORK_LATENCY_DEGRADED"),
        (state_with_network_updates(packet_loss_pct=2.0), "NETWORK_PACKET_LOSS_DEGRADED"),
        (state_with_network_updates(uplink_mbps=2.0), "NETWORK_UPLINK_DEGRADED"),
    ],
)
def test_policy_degrades_for_each_soft_network_threshold(state, expected_reason):
    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(), state, make_policy()
    )
    assert decision == "degrade"
    assert reason == expected_reason
    assert alternatives == [FallbackAction.CRAWL_TO_SAFE_ZONE]
    assert constraints is None


@pytest.mark.parametrize(
    ("network_profile", "expected_reason", "expected_alternatives"),
    [
        ("uplink_bad", "NETWORK_UPLINK_TOO_LOW", [FallbackAction.CRAWL_TO_SAFE_ZONE]),
        ("partition", "NETWORK_DETACHED", [FallbackAction.LOCAL_AUTONOMY_ONLY]),
    ],
)
def test_policy_denies_for_hard_network_failures(
    network_profile, expected_reason, expected_alternatives
):
    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(), make_state(network_profile), make_policy()
    )
    assert decision == "deny"
    assert reason == expected_reason
    assert alternatives == expected_alternatives
    assert constraints is None


@pytest.mark.parametrize(
    ("request_update", "state_update", "expected_reason"),
    [
        ({"capability": Capability.MISSION_CONTINUE}, {}, "CAPABILITY_NOT_COVERED_BY_POLICY"),
        ({"requested_duration_seconds": 601}, {}, "REQUESTED_DURATION_TOO_LONG"),
        ({"requesting_agent_id": "unknown-agent"}, {}, "AGENT_KEY_NOT_TRUSTED"),
        ({"edge_agent_id": "edge-agent:other"}, {}, "EDGE_AGENT_NOT_ALLOWED"),
        ({"robot_id": "other-robot"}, {}, "ROBOT_NOT_ALLOWED"),
        ({"mission_id": "mission-other"}, {}, "MISSION_NOT_ALLOWED"),
        (
            {},
            {"geofence_state": GeofenceState(geofence_id="test-zone-a", inside=False)},
            "GEOFENCE_NOT_SATISFIED",
        ),
        ({}, {"human_operator_available": False}, "HUMAN_OPERATOR_NOT_AVAILABLE"),
    ],
)
def test_policy_denies_each_allow_requirement(request_update, state_update, expected_reason):
    request = make_request(**request_update)
    state = sign_state(make_state("normal").model_copy(update=state_update))
    decision, reason, alternatives, constraints = evaluate_inputs(request, state, make_policy())
    assert decision == "deny"
    assert reason == expected_reason
    assert alternatives
    assert constraints is None


def test_policy_denies_state_mission_mismatch():
    state = sign_state(make_state("normal").model_copy(update={"mission_id": "mission-other"}))
    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(), state, make_policy()
    )
    assert decision == "deny"
    assert reason == "MISSION_STATE_MISMATCH"
    assert alternatives
    assert constraints is None


def test_public_policy_evaluation_requires_audit_log():
    with pytest.raises(TypeError):
        evaluate_policy(make_request(), make_state("normal"), make_policy())


@pytest.mark.parametrize(
    ("network_profile", "expected_event_type", "expected_decision"),
    [
        ("normal", AuditEventType.CAPABILITY_ALLOWED, "allow"),
        ("degraded_teleop", AuditEventType.CAPABILITY_DEGRADED, "degrade"),
        ("partition", AuditEventType.CAPABILITY_DENIED, "deny"),
    ],
)
def test_audited_policy_decisions_emit_causal_event(
    network_profile, expected_event_type, expected_decision
):
    log = AuditLog()
    request = make_request()
    state = make_state(network_profile)

    decision, reason, _, _, event = evaluate_policy(
        request,
        state,
        make_policy(),
        audit_log=log,
        deciding_actor_id="issuer",
        **policy_trust_kwargs(make_policy()),
    )

    assert decision == expected_decision
    assert event == log.events[-1]
    assert event.event_type == expected_event_type
    assert event.audit_id.startswith("audit_")
    assert event.correlation_id == request.correlation_id
    assert event.robot_id == request.robot_id
    assert event.mission_id == request.mission_id
    assert event.policy_id == "remote-assist-authority-v0"
    assert event.state_refs == [state.message_id]
    assert event.related_message_ids == [request.message_id, state.message_id]
    assert event.payload["reason_code"] == reason
    assert event.payload_hash is not None
    assert event.integrity_proof is not None


def test_no_lease_rejected():
    key = DemoKeyPair()
    gate = make_gate(key)
    result = gate.evaluate(make_command(), None)
    assert result.allowed is False
    assert result.reason_code == "NO_LEASE"
    assert result.audit_id == gate.audit_log.events[-1].audit_id
    assert result.fallback_action is None
    assert result.fallback_declaration is None
    assert gate.fallback_events == []
    assert [event.event_type for event in gate.audit_log.events] == [
        AuditEventType.COMMAND_REJECTED,
    ]
    assert {event.correlation_id for event in gate.audit_log.events} == {"cmd_test"}


def test_fallback_declaration_uses_command_correlation_id():
    key = DemoKeyPair()
    command = make_command(correlation_id="corr_command")
    lease = issue_valid_lease(key)
    result = make_gate(key).evaluate(command, lease, current_state=make_state("uplink_bad"))
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.correlation_id == "corr_command"


def test_edge_agent_mismatch_rejection_is_audited():
    key = DemoKeyPair()
    gate = make_gate(key)
    daemon = EdgeAgentDaemon("edge-agent:rover-001", gate)
    command = make_command(edge_agent_id="edge-agent:other")

    result = daemon.handle_command(command, None)

    assert result.allowed is False
    assert result.reason_code == "EDGE_AGENT_MISMATCH"
    assert result.audit_id == gate.audit_log.events[-1].audit_id
    assert gate.audit_log.events[-1].event_type == AuditEventType.COMMAND_REJECTED
    assert gate.audit_log.events[-1].payload["reason_code"] == "EDGE_AGENT_MISMATCH"


def test_expired_lease_rejected():
    key = DemoKeyPair()
    request = make_request()
    _, _, _, constraints = evaluate_inputs(request, make_state("normal"), make_policy())
    assert constraints is not None
    policy = make_policy()
    lease = issue_lease(
        request,
        constraints,
        "issuer",
        key,
        1,
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )
    lease.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    lease.signature = key.sign(lease)
    result = make_gate(key).evaluate(make_command(), lease)
    assert result.allowed is False
    assert result.reason_code == "LEASE_EXPIRED"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_wrong_robot_rejected():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command(robot_id="other-robot")
    result = make_gate(key).evaluate(command, lease)
    assert result.allowed is False
    assert result.reason_code == "LEASE_CONTEXT_MISMATCH"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_wrong_mission_rejected():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command(mission_id="mission-other")
    result = make_gate(key).evaluate(command, lease)
    assert result.allowed is False
    assert result.reason_code == "LEASE_CONTEXT_MISMATCH"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_wrong_capability_rejected():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command(capability="mission_continue")
    result = make_gate(key).evaluate(command, lease)
    assert result.allowed is False
    assert result.reason_code == "LEASE_CONTEXT_MISMATCH"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_revoked_lease_rejected():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    emitted = []
    gate = make_gate(key, fallback_sink=emitted.append)
    revocation = LeaseRevocation(
        lease_id=lease.lease_id,
        revoked_by="edge-agent:rover-001",
        edge_agent_id=EDGE_AGENT_ID,
        reason_code="NETWORK_DEGRADED_REVOKE",
        fallback_action=FallbackAction.HOLD_POSITION,
    )
    sign_revocation(revocation)
    revoke_event = gate.revoke(revocation, lease=lease)
    assert revoke_event is not None
    assert revoke_event.trigger == "NETWORK_DEGRADED_REVOKE"
    assert revoke_event.fallback_action == FallbackAction.CRAWL_TO_SAFE_ZONE
    assert revoke_event.revocation_id == revocation.message_id
    assert (
        gate.audit_log.events[0].payload["requested_fallback_action"]
        == FallbackAction.HOLD_POSITION
    )
    assert gate.audit_log.events[0].payload["fallback_action"] == FallbackAction.CRAWL_TO_SAFE_ZONE
    result = gate.evaluate(make_command(), lease)
    assert result.allowed is False
    assert result.reason_code == "LEASE_REVOKED"
    assert result.audit_id == gate.audit_log.events[-2].audit_id
    assert result.fallback_action == FallbackAction.CRAWL_TO_SAFE_ZONE
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.revocation_id == revocation.message_id
    assert emitted == gate.fallback_events
    assert [event.event_type for event in gate.audit_log.events] == [
        AuditEventType.LEASE_REVOKED,
        AuditEventType.FALLBACK_DECLARED,
        AuditEventType.COMMAND_REJECTED,
        AuditEventType.FALLBACK_DECLARED,
    ]
    assert {event.correlation_id for event in gate.audit_log.events} == {revocation.correlation_id}


def test_revocation_fallback_uses_revocation_correlation_id():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = LeaseRevocation(
        correlation_id="corr_revocation",
        lease_id=lease.lease_id,
        revoked_by="edge-agent:rover-001",
        edge_agent_id=EDGE_AGENT_ID,
        reason_code="NETWORK_DEGRADED_REVOKE",
        fallback_action=FallbackAction.HOLD_POSITION,
    )
    sign_revocation(revocation)
    fallback = gate.revoke(revocation, lease=lease)
    assert fallback is not None
    assert fallback.correlation_id == "corr_revocation"


def test_raw_lease_id_revocation_is_rejected_without_mutating_authority():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    with pytest.raises(ValueError, match="revocation requires a LeaseRevocation message"):
        gate.revoke(lease.lease_id, lease=lease)
    assert gate.revoked_lease_ids == set()
    assert [event.event_type for event in gate.audit_log.events] == [
        AuditEventType.REVOCATION_REJECTED
    ]
    assert gate.audit_log.events[0].payload["reason_code"] == "REVOCATION_CONTEXT_REQUIRED"


def test_revocation_lease_mismatch_rejected_without_recording():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = LeaseRevocation(
        lease_id="lease_other",
        revoked_by="edge-agent:rover-001",
        edge_agent_id=EDGE_AGENT_ID,
        reason_code="WRONG_REVOCATION_CONTEXT",
        fallback_action=FallbackAction.HOLD_POSITION,
    )
    sign_revocation(revocation)
    with pytest.raises(ValueError, match="revocation lease_id does not match lease"):
        gate.revoke(revocation, lease=lease)
    assert gate.revoked_lease_ids == set()
    assert gate.fallback_events == []
    assert [event.event_type for event in gate.audit_log.events] == [
        AuditEventType.REVOCATION_REJECTED
    ]
    assert gate.audit_log.events[0].payload["reason_code"] == "REVOCATION_LEASE_MISMATCH"


def test_invalid_signature_rejected():
    good_key = DemoKeyPair()
    bad_key = DemoKeyPair()
    lease = issue_valid_lease(good_key)
    result = make_gate(bad_key).evaluate(make_command(), lease)
    assert result.allowed is False
    assert result.reason_code == "INVALID_SIGNATURE"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_tampered_lease_rejected_before_context_use():
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(update={"robot_id": "other-robot"})
    result = make_gate(key).evaluate(make_command(), lease)
    assert result.allowed is False
    assert result.reason_code == "INVALID_SIGNATURE"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_missing_remote_assist_constraints_rejected():
    key = DemoKeyPair()
    policy = make_policy()
    lease = issue_lease(
        make_request(),
        LeaseConstraints(),
        "issuer",
        key,
        600,
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )
    result = make_gate(key).evaluate(make_command(), lease)
    assert result.allowed is False
    assert result.reason_code == "LEASE_CONSTRAINTS_MISSING"


def test_degraded_current_state_rejects_previously_valid_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    state = make_state("degraded_teleop")
    result = make_gate(key).evaluate(make_command(), lease, current_state=state)
    assert result.allowed is False
    assert result.reason_code in {
        "NETWORK_LATENCY_TOO_HIGH",
        "NETWORK_PACKET_LOSS_TOO_HIGH",
        "NETWORK_UPLINK_TOO_LOW",
    }
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.fallback_action == FallbackAction.CRAWL_TO_SAFE_ZONE
    gate = make_gate(key)
    audited_result = gate.evaluate(make_command(), lease, current_state=state)
    command_event = gate.audit_log.events[-2]
    assert audited_result.audit_id == command_event.audit_id
    assert command_event.event_type == AuditEventType.COMMAND_REJECTED
    assert command_event.state_refs == [state.message_id]
    assert state.message_id in command_event.related_message_ids
    assert command_event.payload["current_state"]["message_id"] == state.message_id


@pytest.mark.parametrize(
    ("network_profile", "expected_reason"),
    [
        ("uplink_bad", "NETWORK_UPLINK_TOO_LOW"),
        ("partition", "NETWORK_DETACHED"),
    ],
)
def test_bad_current_network_state_rejects_previously_valid_lease(network_profile, expected_reason):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    result = make_gate(key).evaluate(
        make_command(), lease, current_state=make_state(network_profile)
    )
    assert result.allowed is False
    assert result.reason_code == expected_reason
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.fallback_action == FallbackAction.CRAWL_TO_SAFE_ZONE


def test_unknown_current_network_state_rejects_previously_valid_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    result = make_gate(key).evaluate(
        make_command(), lease, current_state=state_with_unknown_network()
    )
    assert result.allowed is False
    assert result.reason_code == "NETWORK_STATE_UNKNOWN"
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.fallback_action == FallbackAction.CRAWL_TO_SAFE_ZONE


def test_wrong_geofence_current_state_rejects_previously_valid_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    state = sign_state(
        make_state("normal").model_copy(
            update={"geofence_state": GeofenceState(geofence_id="wrong-zone", inside=True)}
        )
    )
    result = make_gate(key).evaluate(make_command(), lease, current_state=state)
    assert result.allowed is False
    assert result.reason_code == "GEOFENCE_CONSTRAINT_VIOLATED"
