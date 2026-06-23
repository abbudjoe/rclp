from datetime import datetime, timedelta, timezone

import pytest

from rclp_agents.edge_agent_daemon import EdgeAgentDaemon
from rclp_agents.central_agent_mock import request_remote_assist
from rclp_core.audit import AuditLog
from rclp_core.crypto import DemoKeyPair
from rclp_core.leases import issue_lease
from rclp_core.models import (
    AuditEventType,
    Capability,
    CapabilityConstraintRequirement,
    CapabilityLease,
    CapabilityRequest,
    Decision,
    FallbackAction,
    GeofenceState,
    LeaseConstraints,
    LeaseRevocation,
    NetworkProfile,
    NetworkState,
    RobotStateAssertion,
)
from rclp_core.network import profile
from rclp_core.policy import (
    Policy,
    RequestReplayCache,
    _evaluate_policy_inputs,
    evaluate_policy,
    policy_digest,
)
from rclp_ros2.command_gate import Command, CommandGate, CommandReplayCache


CENTRAL_AGENT_ID = "fleet-agent:v0.1"
EDGE_AGENT_ID = "edge-agent:rover-001"
TRUSTED_ISSUER_ID = "issuer"
CENTRAL_KEY = DemoKeyPair()
EDGE_KEY = DemoKeyPair()
_REPLAY_CACHE_DEFAULT = object()


def remote_assist_constraint_requirements() -> dict[str, CapabilityConstraintRequirement]:
    return {
        Capability.REMOTE_ASSIST.value: CapabilityConstraintRequirement(
            capability=Capability.REMOTE_ASSIST,
            require_geofence_id=True,
            require_network_thresholds=True,
            require_fallback_on_degrade=True,
        )
    }


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
        reason="security negative test",
    )
    if updates:
        request = request.model_copy(update=updates)
    return sign_request(request)


def make_state() -> RobotStateAssertion:
    return sign_state(
        RobotStateAssertion(
            robot_id="rover-001",
            edge_agent_id=EDGE_AGENT_ID,
            mission_id="mission-001",
            network_state=profile("normal"),
            geofence_state=GeofenceState(geofence_id="test-zone-a", inside=True),
        )
    )


def make_command(**updates) -> Command:
    command = Command(
        correlation_id="cmd_security_negative",
        command_id="cmd_security_negative",
        agent_id="fleet-agent:v0.1",
        edge_agent_id=EDGE_AGENT_ID,
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.REMOTE_ASSIST.value,
        payload={},
    )
    if updates:
        command = command.model_copy(update=updates)
    return sign_command(command)


def make_policy() -> Policy:
    return Policy.from_yaml("examples/policies/remote_assist_policy.yaml")


def policy_trust_kwargs(
    policy: Policy,
    accepted_policy: Policy | None = None,
    replay_cache: RequestReplayCache | None | object = _REPLAY_CACHE_DEFAULT,
) -> dict:
    return {
        "agent_public_keys_by_id": {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        "edge_public_keys_by_id": {EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        "accepted_policy_digests": {policy_digest(accepted_policy or policy)},
        "replay_cache": RequestReplayCache.temporary()
        if replay_cache is _REPLAY_CACHE_DEFAULT
        else replay_cache,
    }


def evaluate_inputs(
    request: CapabilityRequest,
    state: RobotStateAssertion,
    policy: Policy,
    *,
    accepted_policy: Policy | None = None,
    **kwargs,
):
    trust_kwargs = policy_trust_kwargs(policy, accepted_policy=accepted_policy)
    trust_kwargs.update(kwargs)
    return _evaluate_policy_inputs(
        request,
        state,
        policy,
        **trust_kwargs,
    )


def make_gate(key: DemoKeyPair, **kwargs) -> CommandGate:
    kwargs.setdefault("accepted_capabilities", {Capability.REMOTE_ASSIST.value})
    kwargs.setdefault(
        "issuer_capability_scopes",
        {TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
    )
    kwargs.setdefault(
        "capability_constraint_requirements",
        remote_assist_constraint_requirements(),
    )
    kwargs.setdefault(
        "agent_public_keys_by_id",
        {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
    )
    kwargs.setdefault(
        "state_public_keys_by_edge_id",
        {EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
    )
    kwargs.setdefault("command_replay_cache", CommandReplayCache.temporary())
    return CommandGate(
        key.public_key_b64,
        trusted_issuer_ids={TRUSTED_ISSUER_ID},
        trusted_revoker_ids={EDGE_AGENT_ID},
        revoker_public_keys_by_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        **kwargs,
    )


def issue_valid_lease(key: DemoKeyPair, issuer_id: str = TRUSTED_ISSUER_ID) -> CapabilityLease:
    request = make_request()
    _, _, _, constraints = evaluate_inputs(request, make_state(), make_policy())
    assert constraints is not None
    return issue_lease(request, constraints, issuer_id, key, ttl_seconds=600)


def issue_speed_limited_lease(key: DemoKeyPair, max_speed_mps: float = 0.5) -> CapabilityLease:
    lease = issue_valid_lease(key)
    constraints = lease.constraints.model_copy(update={"max_speed_mps": max_speed_mps})
    return resign(lease.model_copy(update={"constraints": constraints, "signature": None}), key)


def resign(lease: CapabilityLease, key: DemoKeyPair) -> CapabilityLease:
    lease.signature = key.sign(lease)
    return lease


def test_malformed_request_signature_encoding_is_rejected():
    request = make_request().model_copy(update={"signature": f"{make_request().signature}!"})

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_SIGNATURE_INVALID"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_malformed_lease_signature_encoding_is_rejected():
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(update={"signature": "not-base64!"})

    result = make_gate(key).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "INVALID_SIGNATURE"
    assert result.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY


def test_nonfinite_signed_network_state_is_denied_at_runtime():
    malformed_network = profile("normal").model_copy(update={"uplink_mbps": float("inf")})
    state = sign_state(
        make_state().model_copy(update={"network_state": malformed_network, "signature": None})
    )

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        state,
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "NETWORK_STATE_MALFORMED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_nonfinite_network_and_constraint_models_are_rejected():
    with pytest.raises(ValueError):
        NetworkState(latency_ms_p95=float("inf"), packet_loss_pct=0.0, uplink_mbps=1.0)
    with pytest.raises(ValueError):
        LeaseConstraints(max_speed_mps=float("inf"))


def test_nonfinite_lease_constraint_is_denied_at_runtime():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    constraints = lease.constraints.model_copy(update={"max_speed_mps": float("inf")})
    lease = resign(lease.model_copy(update={"constraints": constraints, "signature": None}), key)

    result = make_gate(key).evaluate(
        make_command(payload={"max_speed_mps": 1_000_000.0}),
        lease,
    )

    assert result.allowed is False
    assert result.reason_code == "LEASE_CONSTRAINT_MALFORMED"
    assert result.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY


def test_unsupported_request_protocol_version_is_denied():
    request = make_request().model_copy(
        update={"protocol_version": "999.0-unsupported", "signature": None}
    )
    sign_request(request)

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "PROTOCOL_VERSION_UNSUPPORTED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_unsupported_request_protocol_version_precedes_semantic_checks():
    request = make_request().model_copy(
        update={
            "protocol_version": "999.0-unsupported",
            "capability": Capability.MISSION_CONTINUE,
            "requesting_agent_id": "fleet-agent:unknown",
            "signature": None,
        }
    )
    sign_request(request)

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "PROTOCOL_VERSION_UNSUPPORTED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_unsupported_state_protocol_version_is_denied():
    state = make_state().model_copy(
        update={"protocol_version": "999.0-unsupported", "signature": None}
    )
    sign_state(state)

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        state,
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "PROTOCOL_VERSION_UNSUPPORTED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_unsupported_state_protocol_version_precedes_semantic_checks():
    state = make_state().model_copy(
        update={
            "protocol_version": "999.0-unsupported",
            "robot_id": "rover-wrong",
            "signature": None,
        }
    )
    sign_state(state)

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        state,
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "PROTOCOL_VERSION_UNSUPPORTED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_naive_lease_timestamps_are_denied_without_crashing():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    lease = resign(
        lease.model_copy(
            update={
                "issued_at": lease.issued_at.replace(tzinfo=None),
                "expires_at": lease.expires_at.replace(tzinfo=None),
                "signature": None,
            }
        ),
        key,
    )

    result = make_gate(key).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "LEASE_TIMESTAMP_INVALID"
    assert result.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY


def test_expired_lease_uses_local_fallback_not_lease_constraint():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    constraints = lease.constraints.model_copy(
        update={"fallback_on_degrade": FallbackAction.ESCALATE_TO_HUMAN}
    )
    lease = resign(
        lease.model_copy(
            update={
                "constraints": constraints,
                "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
                "signature": None,
            }
        ),
        key,
    )

    result = make_gate(key).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "LEASE_EXPIRED"
    assert result.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY


def test_revocation_fallback_action_is_advisory_to_local_policy():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
        )
    )

    revoke_event = gate.revoke(revocation, lease=lease)
    result = gate.evaluate(make_command(), lease)

    assert revoke_event is not None
    assert revoke_event.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY
    assert result.allowed is False
    assert result.reason_code == "LEASE_REVOKED"
    assert result.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.revocation_id == revocation.message_id


def test_unsupported_revocation_protocol_version_is_rejected_without_mutation():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = LeaseRevocation(
        lease_id=lease.lease_id,
        revoked_by=EDGE_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        reason_code="COMPROMISE_SUSPECTED",
        fallback_action=FallbackAction.HOLD_POSITION,
    ).model_copy(update={"protocol_version": "999.0-unsupported", "signature": None})
    sign_revocation(revocation)

    with pytest.raises(ValueError, match="revocation protocol version is unsupported"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.fallback_events == []
    assert gate.audit_log.events[-1].event_type == AuditEventType.REVOCATION_REJECTED
    assert gate.audit_log.events[-1].payload["reason_code"] == "PROTOCOL_VERSION_UNSUPPORTED"


def test_revoker_keys_do_not_default_to_state_assertion_keys():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key, state_public_keys_by_edge_id={})

    result = gate.evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "EDGE_STATE_KEY_NOT_TRUSTED"


def stale_state(now: datetime) -> RobotStateAssertion:
    stale_at = now - timedelta(seconds=120)
    return sign_state(
        make_state().model_copy(
            update={
                "created_at": stale_at,
                "observed_at": stale_at,
                "network_state": profile("normal").model_copy(update={"observed_at": stale_at}),
                "geofence_state": GeofenceState(
                    geofence_id="test-zone-a",
                    inside=True,
                    verified_at=stale_at,
                ),
            }
        )
    )


def test_replayed_request_nonce_is_denied_and_audited(tmp_path):
    replay_cache = RequestReplayCache(tmp_path / "request-replay.sqlite3")
    log = AuditLog()
    request = make_request(request_nonce="nonce_replay")
    policy = make_policy()

    first_decision, first_reason, _, _, _ = evaluate_policy(
        request,
        make_state(),
        policy,
        audit_log=log,
        deciding_actor_id=TRUSTED_ISSUER_ID,
        **policy_trust_kwargs(policy, replay_cache=replay_cache),
    )

    replayed_request = make_request(
        message_id="msg_replayed_request",
        correlation_id="corr_replayed_request",
        request_nonce="nonce_replay",
    )
    second_decision, second_reason, _, second_constraints, second_event = evaluate_policy(
        replayed_request,
        make_state(),
        policy,
        audit_log=log,
        deciding_actor_id=TRUSTED_ISSUER_ID,
        **policy_trust_kwargs(policy, replay_cache=replay_cache),
    )

    assert first_decision == Decision.ALLOW
    assert first_reason == "POLICY_SATISFIED"
    assert second_decision == Decision.DENY
    assert second_reason == "REQUEST_REPLAYED"
    assert second_constraints is None
    assert second_event.payload["reason_code"] == "REQUEST_REPLAYED"


def test_replayed_request_nonce_survives_policy_restart(tmp_path):
    replay_store = tmp_path / "request-replay.sqlite3"
    request = make_request(request_nonce="nonce_restart_replay")
    policy = make_policy()

    first_decision, first_reason, _, _, _ = evaluate_policy(
        request,
        make_state(),
        policy,
        audit_log=AuditLog(),
        deciding_actor_id=TRUSTED_ISSUER_ID,
        **policy_trust_kwargs(policy, replay_cache=RequestReplayCache(replay_store)),
    )
    second_decision, second_reason, _, second_constraints, _ = evaluate_policy(
        request,
        make_state(),
        policy,
        audit_log=AuditLog(),
        deciding_actor_id=TRUSTED_ISSUER_ID,
        **policy_trust_kwargs(policy, replay_cache=RequestReplayCache(replay_store)),
    )

    assert first_decision == Decision.ALLOW
    assert first_reason == "POLICY_SATISFIED"
    assert second_decision == Decision.DENY
    assert second_reason == "REQUEST_REPLAYED"
    assert second_constraints is None


def test_authenticated_denied_request_nonce_cannot_later_allow(tmp_path):
    replay_store = tmp_path / "request-replay.sqlite3"
    request = make_request(request_nonce="nonce_denied_then_replayed")
    policy = make_policy()
    unknown_network_state = sign_state(
        make_state().model_copy(
            update={
                "network_state": NetworkState(
                    profile=NetworkProfile.UNKNOWN,
                    latency_ms_p95=45,
                    packet_loss_pct=0.1,
                    uplink_mbps=8.0,
                ),
                "signature": None,
            }
        )
    )

    first_decision, first_reason, _, first_constraints, _ = evaluate_policy(
        request,
        unknown_network_state,
        policy,
        audit_log=AuditLog(),
        deciding_actor_id=TRUSTED_ISSUER_ID,
        **policy_trust_kwargs(policy, replay_cache=RequestReplayCache(replay_store)),
    )
    second_decision, second_reason, _, second_constraints, _ = evaluate_policy(
        request,
        make_state(),
        policy,
        audit_log=AuditLog(),
        deciding_actor_id=TRUSTED_ISSUER_ID,
        **policy_trust_kwargs(policy, replay_cache=RequestReplayCache(replay_store)),
    )

    assert first_decision == Decision.DENY
    assert first_reason == "NETWORK_STATE_UNKNOWN"
    assert first_constraints is None
    assert second_decision == Decision.DENY
    assert second_reason == "REQUEST_REPLAYED"
    assert second_constraints is None


def test_policy_requires_replay_cache_for_authority_issuance():
    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        make_state(),
        make_policy(),
        replay_cache=None,
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_REPLAY_CACHE_REQUIRED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_policy_requires_durable_replay_store_for_authority_issuance():
    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        make_state(),
        make_policy(),
        replay_cache=RequestReplayCache(),
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_REPLAY_STORE_DURABLE_REQUIRED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_central_agent_mock_emits_signed_request_for_policy_contract():
    signing_key = DemoKeyPair()
    request = request_remote_assist(signing_key)
    policy = make_policy()

    decision, reason, alternatives, constraints = _evaluate_policy_inputs(
        request,
        make_state(),
        policy,
        agent_public_keys_by_id={CENTRAL_AGENT_ID: signing_key.public_key_b64},
        edge_public_keys_by_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        accepted_policy_digests={policy_digest(policy)},
        replay_cache=RequestReplayCache.temporary(),
    )

    assert decision == Decision.ALLOW
    assert reason == "POLICY_SATISFIED"
    assert alternatives == []
    assert constraints is not None


def test_stale_capability_request_is_denied_before_policy_allow():
    stale_request = make_request(created_at=datetime.now(timezone.utc) - timedelta(seconds=301))

    decision, reason, alternatives, constraints = evaluate_inputs(
        stale_request,
        make_state(),
        make_policy(),
        max_request_age_seconds=300,
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_STALE"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_naive_capability_request_timestamp_is_denied_and_audited():
    log = AuditLog()
    naive_request = make_request(created_at=datetime(2026, 6, 22, 12, 0, 0))
    policy = make_policy()

    decision, reason, alternatives, constraints, event = evaluate_policy(
        naive_request,
        make_state(),
        policy,
        audit_log=log,
        deciding_actor_id=TRUSTED_ISSUER_ID,
        **policy_trust_kwargs(policy),
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_TIMESTAMP_INVALID"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None
    assert event == log.events[-1]
    assert event.event_type.value == "capability_denied"
    assert event.payload["reason_code"] == "REQUEST_TIMESTAMP_INVALID"


def test_unsigned_robot_state_assertion_is_denied_before_policy_allow():
    state = make_state().model_copy(update={"signature": None})

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        state,
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "STATE_SIGNATURE_MISSING"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_stale_robot_state_assertion_is_denied_before_policy_allow():
    now = datetime.now(timezone.utc)

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        stale_state(now),
        make_policy(),
        now=now,
        max_state_age_seconds=30,
    )

    assert decision == Decision.DENY
    assert reason == "STATE_STALE"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_invalid_capability_request_signature_is_denied_before_replay_cache_mutation():
    replay_cache = RequestReplayCache()
    request = make_request(request_nonce="nonce_invalid_signature").model_copy(
        update={"reason": "tampered after signing"}
    )
    policy = make_policy()

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        policy,
        replay_cache=replay_cache,
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_SIGNATURE_INVALID"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None
    assert replay_cache.has_seen(request) is False


def test_authenticated_agent_mismatch_is_denied():
    request = make_request()
    request.authenticated_agent_id = "fleet-agent:other"
    request.signature = CENTRAL_KEY.sign(request)

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_AUTHENTICATED_AGENT_MISMATCH"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_stale_lease_is_rejected_even_before_expiry():
    key = DemoKeyPair()
    now = datetime.now(timezone.utc)
    lease = issue_valid_lease(key).model_copy(
        update={
            "issued_at": now - timedelta(seconds=331),
            "expires_at": now + timedelta(seconds=269),
            "signature": None,
        }
    )
    resign(lease, key)

    result = make_gate(
        key,
        max_lease_age_seconds=300,
        max_lease_ttl_seconds=600,
    ).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "LEASE_STALE"


def test_state_scoped_remote_assist_lease_requires_current_state_at_command_gate():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)

    result = make_gate(key).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "CURRENT_STATE_REQUIRED"


def test_stale_current_state_rejects_previously_valid_lease_at_command_gate():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    now = datetime.now(timezone.utc)

    result = make_gate(key).evaluate(make_command(), lease, current_state=stale_state(now), now=now)

    assert result.allowed is False
    assert result.reason_code == "STATE_STALE"


def test_unsigned_current_state_rejects_previously_valid_lease_at_command_gate():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    unsigned_state = make_state().model_copy(
        update={"authenticated_edge_agent_id": None, "signature": None}
    )

    result = make_gate(key).evaluate(make_command(), lease, current_state=unsigned_state)

    assert result.allowed is False
    assert result.reason_code == "STATE_AUTHENTICATED_EDGE_MISSING"


@pytest.mark.parametrize(
    ("payload", "expected_allowed", "expected_reason"),
    [
        ({"max_speed_mps": 0.4}, True, "LEASE_VALID"),
        ({"max_speed_mps": 0.6}, False, "COMMAND_SPEED_TOO_HIGH"),
        ({}, False, "COMMAND_SPEED_MISSING"),
        ({"max_speed_mps": "fast"}, False, "COMMAND_SPEED_MALFORMED"),
        ({"max_speed_mps": float("nan")}, False, "COMMAND_SPEED_MALFORMED"),
        (
            {"max_speed_mps": 0.4, "speed_mps": 99.0},
            False,
            "COMMAND_SPEED_CONFLICT",
        ),
    ],
)
def test_max_speed_constraint_is_enforced_against_command_payload(
    payload,
    expected_allowed,
    expected_reason,
):
    key = DemoKeyPair()
    lease = issue_speed_limited_lease(key, max_speed_mps=0.5)
    command = make_command(payload=payload)

    result = make_gate(key).evaluate(command, lease, current_state=make_state())

    assert result.allowed is expected_allowed
    assert result.reason_code == expected_reason


@pytest.mark.parametrize(
    ("command_update", "expected_reason"),
    [
        ({"agent_id": "fleet-agent:other"}, "LEASE_CONTEXT_MISMATCH"),
        ({"robot_id": "rover-002"}, "LEASE_CONTEXT_MISMATCH"),
        ({"mission_id": "mission-002"}, "LEASE_CONTEXT_MISMATCH"),
        ({"capability": Capability.MISSION_CONTINUE.value}, "LEASE_CONTEXT_MISMATCH"),
    ],
)
def test_lease_context_replay_to_wrong_agent_robot_mission_or_capability_is_rejected(
    command_update,
    expected_reason,
):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command(**command_update)
    gate = make_gate(key)
    if command_update.get("agent_id") == "fleet-agent:other":
        other_key = DemoKeyPair()
        sign_command(command, other_key)
        gate = make_gate(
            key,
            agent_public_keys_by_id={
                CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64,
                "fleet-agent:other": other_key.public_key_b64,
            },
        )

    result = gate.evaluate(command, lease)

    assert result.allowed is False
    assert result.reason_code == expected_reason


def test_command_without_signature_is_rejected_before_lease_validation():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command().model_copy(update={"signature": None})

    result = make_gate(key).evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_SIGNATURE_MISSING"
    assert result.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY


def test_edge_daemon_mismatch_without_command_auth_uses_command_gate_rejection():
    key = DemoKeyPair()
    gate = make_gate(key)
    daemon = EdgeAgentDaemon(EDGE_AGENT_ID, gate)
    command = make_command(edge_agent_id="edge-agent:other").model_copy(
        update={"authenticated_agent_id": None, "signature": None}
    )

    result = daemon.handle_command(command, issue_valid_lease(key), current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_AUTHENTICATED_AGENT_MISSING"
    assert gate.audit_log.events[-2].event_type == AuditEventType.COMMAND_REJECTED
    assert gate.audit_log.events[-2].payload["reason_code"] == "COMMAND_AUTHENTICATED_AGENT_MISSING"


def test_command_without_authenticated_agent_is_rejected_before_lease_validation():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command().model_copy(update={"authenticated_agent_id": None})

    result = make_gate(key).evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_AUTHENTICATED_AGENT_MISSING"


def test_command_authenticated_actor_mismatch_is_rejected_before_lease_validation():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command().model_copy(update={"authenticated_agent_id": "fleet-agent:other"})

    result = make_gate(key).evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_AUTHENTICATED_AGENT_MISMATCH"


def test_command_from_untrusted_agent_key_is_rejected_before_lease_validation():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command(agent_id="fleet-agent:unknown")

    result = make_gate(key).evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_AGENT_KEY_NOT_TRUSTED"


def test_invalid_command_signature_is_rejected_before_lease_validation():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command().model_copy(update={"payload": {"tampered_after_signing": True}})

    result = make_gate(key).evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_SIGNATURE_INVALID"


def test_stale_command_is_rejected_before_lease_validation():
    key = DemoKeyPair()
    now = datetime.now(timezone.utc)
    lease = issue_valid_lease(key)
    command = make_command(created_at=now - timedelta(seconds=120))

    result = make_gate(key, max_command_age_seconds=30).evaluate(
        command,
        lease,
        current_state=make_state(),
        now=now,
    )

    assert result.allowed is False
    assert result.reason_code == "COMMAND_STALE"


def test_future_command_is_rejected_before_lease_validation():
    key = DemoKeyPair()
    now = datetime.now(timezone.utc)
    lease = issue_valid_lease(key)
    command = make_command(created_at=now + timedelta(seconds=120))

    result = make_gate(key).evaluate(
        command,
        lease,
        current_state=make_state(),
        now=now,
    )

    assert result.allowed is False
    assert result.reason_code == "COMMAND_NOT_YET_VALID"


def test_replayed_signed_command_is_rejected_before_second_authorization():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    command = make_command()

    first = gate.evaluate(command, lease, current_state=make_state())
    second = gate.evaluate(command, lease, current_state=make_state())

    assert first.allowed is True
    assert second.allowed is False
    assert second.reason_code == "COMMAND_REPLAYED"


def test_command_gate_requires_durable_command_replay_cache():
    key = DemoKeyPair()

    with pytest.raises(ValueError, match="durable command_replay_cache"):
        CommandGate(
            key.public_key_b64,
            trusted_issuer_ids={TRUSTED_ISSUER_ID},
            trusted_revoker_ids={EDGE_AGENT_ID},
            accepted_capabilities={Capability.REMOTE_ASSIST.value},
            issuer_capability_scopes={TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
            capability_constraint_requirements=remote_assist_constraint_requirements(),
            agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            revoker_public_keys_by_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
            state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
            command_replay_cache=CommandReplayCache(),
        )


def test_replayed_signed_command_is_rejected_after_gate_restart(tmp_path):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    replay_store = tmp_path / "command-replay.sqlite3"
    command = make_command()

    first_gate = make_gate(key, command_replay_cache=CommandReplayCache(replay_store))
    first = first_gate.evaluate(command, lease, current_state=make_state())
    second_gate = make_gate(key, command_replay_cache=CommandReplayCache(replay_store))
    second = second_gate.evaluate(command, lease, current_state=make_state())

    assert first.allowed is True
    assert second.allowed is False
    assert second.reason_code == "COMMAND_REPLAYED"


def test_trusted_issuer_cannot_grant_capability_outside_local_scope():
    key = DemoKeyPair()
    now = datetime.now(timezone.utc)
    lease = CapabilityLease(
        issuer_id=TRUSTED_ISSUER_ID,
        agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.AUTONOMY_ESCALATION,
        constraints=LeaseConstraints(),
        issued_at=now,
        expires_at=now + timedelta(seconds=300),
    )
    resign(lease, key)
    command = make_command(capability=Capability.AUTONOMY_ESCALATION.value)

    result = make_gate(key).evaluate(command, lease)

    assert result.allowed is False
    assert result.reason_code == "CAPABILITY_NOT_GRANTED"


def mission_continue_constraint_requirements() -> dict[str, CapabilityConstraintRequirement]:
    requirements = remote_assist_constraint_requirements()
    requirements[Capability.MISSION_CONTINUE.value] = CapabilityConstraintRequirement(
        capability=Capability.MISSION_CONTINUE,
        require_geofence_id=True,
        require_max_speed_mps=True,
    )
    return requirements


def issue_mission_continue_lease(
    key: DemoKeyPair,
    constraints: LeaseConstraints,
) -> CapabilityLease:
    now = datetime.now(timezone.utc)
    lease = CapabilityLease(
        issuer_id=TRUSTED_ISSUER_ID,
        agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.MISSION_CONTINUE,
        constraints=constraints,
        issued_at=now,
        expires_at=now + timedelta(seconds=300),
    )
    return resign(lease, key)


def test_accepted_non_remote_capability_requires_declared_constraints():
    key = DemoKeyPair()
    gate = make_gate(
        key,
        accepted_capabilities={
            Capability.REMOTE_ASSIST.value,
            Capability.MISSION_CONTINUE.value,
        },
        issuer_capability_scopes={
            TRUSTED_ISSUER_ID: {
                Capability.REMOTE_ASSIST.value,
                Capability.MISSION_CONTINUE.value,
            }
        },
        capability_constraint_requirements=mission_continue_constraint_requirements(),
    )
    lease = issue_mission_continue_lease(key, LeaseConstraints())
    command = make_command(
        capability=Capability.MISSION_CONTINUE.value,
        payload={"max_speed_mps": 0.25},
    )

    result = gate.evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "LEASE_CONSTRAINTS_MISSING"


def test_accepted_non_remote_capability_allows_declared_constraints():
    key = DemoKeyPair()
    gate = make_gate(
        key,
        accepted_capabilities={
            Capability.REMOTE_ASSIST.value,
            Capability.MISSION_CONTINUE.value,
        },
        issuer_capability_scopes={
            TRUSTED_ISSUER_ID: {
                Capability.REMOTE_ASSIST.value,
                Capability.MISSION_CONTINUE.value,
            }
        },
        capability_constraint_requirements=mission_continue_constraint_requirements(),
    )
    lease = issue_mission_continue_lease(
        key,
        LeaseConstraints(geofence_id="test-zone-a", max_speed_mps=0.5),
    )
    command = make_command(
        capability=Capability.MISSION_CONTINUE.value,
        payload={"max_speed_mps": 0.25},
    )

    result = gate.evaluate(command, lease, current_state=make_state())

    assert result.allowed is True
    assert result.reason_code == "LEASE_VALID"


def test_required_fallback_constraint_must_be_explicit():
    key = DemoKeyPair()
    requirements = remote_assist_constraint_requirements()
    requirements[Capability.MISSION_CONTINUE.value] = CapabilityConstraintRequirement(
        capability=Capability.MISSION_CONTINUE,
        require_fallback_on_degrade=True,
    )
    gate = make_gate(
        key,
        accepted_capabilities={
            Capability.REMOTE_ASSIST.value,
            Capability.MISSION_CONTINUE.value,
        },
        issuer_capability_scopes={
            TRUSTED_ISSUER_ID: {
                Capability.REMOTE_ASSIST.value,
                Capability.MISSION_CONTINUE.value,
            }
        },
        capability_constraint_requirements=requirements,
    )
    implicit_default_lease = issue_mission_continue_lease(key, LeaseConstraints())
    explicit_fallback_lease = issue_mission_continue_lease(
        key,
        LeaseConstraints(fallback_on_degrade=FallbackAction.CRAWL_TO_SAFE_ZONE),
    )

    implicit_result = gate.evaluate(
        make_command(
            command_id="cmd_implicit_fallback",
            command_nonce="nonce_implicit_fallback",
            capability=Capability.MISSION_CONTINUE.value,
        ),
        implicit_default_lease,
    )
    explicit_result = gate.evaluate(
        make_command(
            command_id="cmd_explicit_fallback",
            command_nonce="nonce_explicit_fallback",
            capability=Capability.MISSION_CONTINUE.value,
        ),
        explicit_fallback_lease,
    )

    assert implicit_result.allowed is False
    assert implicit_result.reason_code == "LEASE_CONSTRAINTS_MISSING"
    assert explicit_result.allowed is True
    assert explicit_result.reason_code == "LEASE_VALID"


def test_expired_lease_is_rejected():
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(
        update={
            "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
            "signature": None,
        }
    )
    resign(lease, key)

    result = make_gate(key).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "LEASE_EXPIRED"


def test_revoked_lease_is_rejected():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    gate.revoke(
        sign_revocation(
            LeaseRevocation(
                lease_id=lease.lease_id,
                revoked_by="edge-agent:rover-001",
                edge_agent_id=EDGE_AGENT_ID,
                reason_code="COMPROMISE_SUSPECTED",
                fallback_action=FallbackAction.HOLD_POSITION,
            )
        ),
        lease=lease,
    )

    result = gate.evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "LEASE_REVOKED"


def test_forged_revoked_lease_id_cannot_select_revocation_fallback():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
        )
    )
    gate.revoke(revocation, lease=lease)
    fake_lease = lease.model_copy(
        update={
            "robot_id": "robot-victim",
            "mission_id": "mission-victim",
            "signature": None,
        }
    )
    command = make_command(robot_id="robot-victim", mission_id="mission-victim")

    result = gate.evaluate(command, fake_lease)

    assert result.allowed is False
    assert result.reason_code == "INVALID_SIGNATURE"
    assert result.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.revocation_id is None
    assert result.fallback_declaration.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY


def test_unsigned_revocation_cannot_revoke_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)

    with pytest.raises(ValueError, match="revocation signature is missing"):
        gate.revoke(
            LeaseRevocation(
                lease_id=lease.lease_id,
                revoked_by=EDGE_AGENT_ID,
                edge_agent_id=EDGE_AGENT_ID,
                reason_code="COMPROMISE_SUSPECTED",
                fallback_action=FallbackAction.HOLD_POSITION,
            ),
            lease=lease,
        )

    assert gate.revoked_lease_ids == set()
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_SIGNATURE_MISSING"


def test_tampered_revocation_signature_cannot_revoke_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
        )
    ).model_copy(update={"reason_code": "TAMPERED_AFTER_SIGNING"})

    with pytest.raises(ValueError, match="revocation signature is invalid"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_SIGNATURE_INVALID"


def test_stale_revocation_cannot_revoke_lease():
    key = DemoKeyPair()
    now = datetime.now(timezone.utc)
    stale_at = now - timedelta(seconds=400)
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = sign_revocation(
        LeaseRevocation(
            created_at=stale_at,
            revoked_at=stale_at,
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
        )
    )

    with pytest.raises(ValueError, match="revocation is not fresh"):
        gate.revoke(revocation, lease=lease, now=now)

    assert gate.revoked_lease_ids == set()
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_STALE"


def test_revocation_context_mismatch_cannot_revoke_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
            robot_id="rover-002",
            mission_id=lease.mission_id,
            capability=lease.capability,
        )
    )

    with pytest.raises(ValueError, match="revocation context does not match lease"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_CONTEXT_MISMATCH"


def test_revocation_edge_mismatch_cannot_revoke_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id="edge-agent:rover-002",
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            capability=lease.capability,
        )
    )

    with pytest.raises(ValueError, match="revocation context does not match lease"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_CONTEXT_MISMATCH"
    assert gate.audit_log.events[-1].payload["revocation_edge_agent_id"] == "edge-agent:rover-002"


def test_cross_edge_trusted_revoker_cannot_revoke_victim_lease():
    issuer_key = DemoKeyPair()
    revoker_b_key = DemoKeyPair()
    revoker_b_id = "edge-agent:revoker-b"
    lease = issue_valid_lease(issuer_key)
    gate = CommandGate(
        issuer_key.public_key_b64,
        trusted_issuer_ids={TRUSTED_ISSUER_ID},
        trusted_revoker_ids={EDGE_AGENT_ID, revoker_b_id},
        accepted_capabilities={Capability.REMOTE_ASSIST.value},
        issuer_capability_scopes={TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
        capability_constraint_requirements=remote_assist_constraint_requirements(),
        agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        revoker_public_keys_by_id={
            EDGE_AGENT_ID: EDGE_KEY.public_key_b64,
            revoker_b_id: revoker_b_key.public_key_b64,
        },
        state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        command_replay_cache=CommandReplayCache.temporary(),
    )
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=revoker_b_id,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            capability=lease.capability,
        ),
        revoker_b_key,
    )

    with pytest.raises(ValueError, match="revocation actor is not authorized for lease edge"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.fallback_events == []
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_ACTOR_SCOPE_MISMATCH"


def test_explicit_revoker_edge_scope_can_revoke_target_lease():
    issuer_key = DemoKeyPair()
    scoped_revoker_key = DemoKeyPair()
    scoped_revoker_id = "agent:fleet-revoker"
    lease = issue_valid_lease(issuer_key)
    gate = CommandGate(
        issuer_key.public_key_b64,
        trusted_issuer_ids={TRUSTED_ISSUER_ID},
        trusted_revoker_ids={scoped_revoker_id},
        accepted_capabilities={Capability.REMOTE_ASSIST.value},
        issuer_capability_scopes={TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
        capability_constraint_requirements=remote_assist_constraint_requirements(),
        agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        revoker_public_keys_by_id={scoped_revoker_id: scoped_revoker_key.public_key_b64},
        revoker_edge_scopes_by_id={scoped_revoker_id: {EDGE_AGENT_ID}},
        state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        command_replay_cache=CommandReplayCache.temporary(),
    )
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=scoped_revoker_id,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            capability=lease.capability,
        ),
        scoped_revoker_key,
    )

    fallback = gate.revoke(revocation, lease=lease)

    assert fallback is not None
    assert gate.revoked_lease_ids == {lease.lease_id}


def test_unknown_revoker_cannot_revoke_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)

    with pytest.raises(ValueError, match="revocation actor is not trusted"):
        gate.revoke(
            LeaseRevocation(
                lease_id=lease.lease_id,
                revoked_by="agent:unknown",
                edge_agent_id=EDGE_AGENT_ID,
                reason_code="COMPROMISE_SUSPECTED",
                fallback_action=FallbackAction.HOLD_POSITION,
            ),
            lease=lease,
        )

    assert gate.revoked_lease_ids == set()
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_ACTOR_NOT_TRUSTED"


def test_invalid_signature_is_rejected():
    good_key = DemoKeyPair()
    wrong_key = DemoKeyPair()
    lease = issue_valid_lease(good_key)

    result = make_gate(wrong_key).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "INVALID_SIGNATURE"


def test_unknown_requesting_agent_is_denied():
    unknown_agent_request = make_request(requesting_agent_id="fleet-agent:unknown")

    decision, reason, alternatives, constraints = evaluate_inputs(
        unknown_agent_request,
        make_state(),
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "AGENT_KEY_NOT_TRUSTED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_compromised_known_central_agent_escalation_is_denied_and_audited():
    log = AuditLog()
    request = make_request(
        capability=Capability.AUTONOMY_ESCALATION,
        reason="known agent attempting unsupported high-authority escalation",
    )
    policy = make_policy()

    decision, reason, alternatives, constraints, event = evaluate_policy(
        request,
        make_state(),
        policy,
        audit_log=log,
        deciding_actor_id=TRUSTED_ISSUER_ID,
        **policy_trust_kwargs(policy),
    )

    assert decision == Decision.DENY
    assert reason == "CAPABILITY_NOT_COVERED_BY_POLICY"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None
    assert event.payload["request_id"] == request.message_id
    assert event.payload["reason_code"] == "CAPABILITY_NOT_COVERED_BY_POLICY"


def test_unknown_lease_issuer_is_rejected_even_with_a_valid_signature():
    key = DemoKeyPair()
    lease = issue_valid_lease(key, issuer_id="issuer:unknown")

    result = make_gate(key).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "ISSUER_NOT_TRUSTED"
    assert result.fallback_action == FallbackAction.LOCAL_AUTONOMY_ONLY


def test_lease_issuer_identity_must_match_verification_key():
    low_key = DemoKeyPair()
    privileged_key = DemoKeyPair()
    request = make_request()
    _, _, _, constraints = evaluate_inputs(request, make_state(), make_policy())
    assert constraints is not None
    forged_privileged_lease = issue_lease(
        request,
        constraints,
        "issuer:privileged",
        low_key,
        ttl_seconds=600,
    )
    gate = CommandGate(
        low_key.public_key_b64,
        trusted_issuer_ids={"issuer:low", "issuer:privileged"},
        issuer_public_keys_by_id={
            "issuer:low": low_key.public_key_b64,
            "issuer:privileged": privileged_key.public_key_b64,
        },
        trusted_revoker_ids={EDGE_AGENT_ID},
        accepted_capabilities={Capability.REMOTE_ASSIST.value},
        issuer_capability_scopes={
            "issuer:low": {Capability.REMOTE_ASSIST.value},
            "issuer:privileged": {Capability.REMOTE_ASSIST.value},
        },
        capability_constraint_requirements=remote_assist_constraint_requirements(),
        agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        revoker_public_keys_by_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        command_replay_cache=CommandReplayCache.temporary(),
    )

    result = gate.evaluate(make_command(), forged_privileged_lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "INVALID_SIGNATURE"


def test_multiple_trusted_issuers_require_key_registry():
    key = DemoKeyPair()

    with pytest.raises(ValueError, match="issuer_public_keys_by_id is required"):
        CommandGate(
            key.public_key_b64,
            trusted_issuer_ids={"issuer:low", "issuer:privileged"},
            trusted_revoker_ids={EDGE_AGENT_ID},
            accepted_capabilities={Capability.REMOTE_ASSIST.value},
            issuer_capability_scopes={
                "issuer:low": {Capability.REMOTE_ASSIST.value},
                "issuer:privileged": {Capability.REMOTE_ASSIST.value},
            },
            capability_constraint_requirements=remote_assist_constraint_requirements(),
            agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            command_replay_cache=CommandReplayCache.temporary(),
        )


@pytest.mark.parametrize(
    ("scope_field", "expected_reason"),
    [
        ("allowed_agents", "AGENT_NOT_ALLOWED"),
        ("allowed_edge_agents", "EDGE_AGENT_NOT_ALLOWED"),
        ("allowed_robots", "ROBOT_NOT_ALLOWED"),
        ("allowed_missions", "MISSION_NOT_ALLOWED"),
    ],
)
def test_policy_downgrade_empty_authority_scope_fails_closed(scope_field, expected_reason):
    downgraded_policy = make_policy().model_copy(deep=True)
    setattr(downgraded_policy.requirements, scope_field, [])

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        make_state(),
        downgraded_policy,
    )

    assert decision == Decision.DENY
    assert reason == expected_reason
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


@pytest.mark.parametrize(
    "mutate_policy",
    [
        lambda policy: policy.requirements.allowed_robots.append("rover-002"),
        lambda policy: setattr(policy.requirements, "geofence_required", False),
        lambda policy: setattr(policy.requirements.network, "max_latency_ms_p95", 1000),
        lambda policy: setattr(policy, "lease_ttl_seconds", 3600),
    ],
)
def test_permissive_policy_downgrade_requires_accepted_policy_digest(mutate_policy):
    accepted_policy = make_policy()
    downgraded_policy = accepted_policy.model_copy(deep=True)
    mutate_policy(downgraded_policy)

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        make_state(),
        downgraded_policy,
        accepted_policy=accepted_policy,
    )

    assert decision == Decision.DENY
    assert reason == "POLICY_DIGEST_NOT_ACCEPTED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None
