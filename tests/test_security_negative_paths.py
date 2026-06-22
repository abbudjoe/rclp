from datetime import datetime, timedelta, timezone

import pytest

from rclp_agents.central_agent_mock import request_remote_assist
from rclp_core.audit import AuditLog
from rclp_core.crypto import DemoKeyPair
from rclp_core.leases import issue_lease
from rclp_core.models import (
    Capability,
    CapabilityLease,
    CapabilityRequest,
    Decision,
    FallbackAction,
    GeofenceState,
    LeaseRevocation,
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
from rclp_ros2.command_gate import Command, CommandGate


CENTRAL_AGENT_ID = "fleet-agent:v0.1"
TRUSTED_ISSUER_ID = "issuer"
CENTRAL_KEY = DemoKeyPair()


def sign_request(request: CapabilityRequest, key: DemoKeyPair = CENTRAL_KEY) -> CapabilityRequest:
    request.authenticated_agent_id = request.requesting_agent_id
    request.signature = None
    request.signature = key.sign(request)
    return request


def make_request(**updates) -> CapabilityRequest:
    request = CapabilityRequest(
        requesting_agent_id=CENTRAL_AGENT_ID,
        edge_agent_id="edge-agent:rover-001",
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.REMOTE_ASSIST,
        reason="security negative test",
    )
    if updates:
        request = request.model_copy(update=updates)
    return sign_request(request)


def make_state() -> RobotStateAssertion:
    return RobotStateAssertion(
        robot_id="rover-001",
        edge_agent_id="edge-agent:rover-001",
        mission_id="mission-001",
        network_state=profile("normal"),
        geofence_state=GeofenceState(geofence_id="test-zone-a", inside=True),
    )


def make_command(**updates) -> Command:
    command = Command(
        command_id="cmd_security_negative",
        agent_id="fleet-agent:v0.1",
        edge_agent_id="edge-agent:rover-001",
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.REMOTE_ASSIST.value,
        payload={},
    )
    return command.model_copy(update=updates)


def make_policy() -> Policy:
    return Policy.from_yaml("examples/policies/remote_assist_policy.yaml")


def policy_trust_kwargs(policy: Policy, accepted_policy: Policy | None = None) -> dict:
    return {
        "agent_public_keys_by_id": {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        "accepted_policy_digests": {policy_digest(accepted_policy or policy)},
    }


def evaluate_inputs(
    request: CapabilityRequest,
    state: RobotStateAssertion,
    policy: Policy,
    *,
    accepted_policy: Policy | None = None,
    **kwargs,
):
    return _evaluate_policy_inputs(
        request,
        state,
        policy,
        **policy_trust_kwargs(policy, accepted_policy=accepted_policy),
        **kwargs,
    )


def make_gate(key: DemoKeyPair, **kwargs) -> CommandGate:
    return CommandGate(
        key.public_key_b64,
        trusted_issuer_ids={TRUSTED_ISSUER_ID},
        trusted_revoker_ids={"edge-agent:rover-001"},
        **kwargs,
    )


def issue_valid_lease(key: DemoKeyPair, issuer_id: str = TRUSTED_ISSUER_ID) -> CapabilityLease:
    request = make_request()
    _, _, _, constraints = evaluate_inputs(request, make_state(), make_policy())
    assert constraints is not None
    return issue_lease(request, constraints, issuer_id, key, ttl_seconds=600)


def resign(lease: CapabilityLease, key: DemoKeyPair) -> CapabilityLease:
    lease.signature = key.sign(lease)
    return lease


def test_replayed_request_nonce_is_denied_and_audited():
    replay_cache = RequestReplayCache()
    log = AuditLog()
    request = make_request(request_nonce="nonce_replay")
    policy = make_policy()

    first_decision, first_reason, _, _, _ = evaluate_policy(
        request,
        make_state(),
        policy,
        audit_log=log,
        deciding_actor_id=TRUSTED_ISSUER_ID,
        replay_cache=replay_cache,
        **policy_trust_kwargs(policy),
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
        replay_cache=replay_cache,
        **policy_trust_kwargs(policy),
    )

    assert first_decision == Decision.ALLOW
    assert first_reason == "POLICY_SATISFIED"
    assert second_decision == Decision.DENY
    assert second_reason == "REQUEST_REPLAYED"
    assert second_constraints is None
    assert second_event.payload["reason_code"] == "REQUEST_REPLAYED"


def test_central_agent_mock_emits_signed_request_for_policy_contract():
    signing_key = DemoKeyPair()
    request = request_remote_assist(signing_key)
    policy = make_policy()

    decision, reason, alternatives, constraints = _evaluate_policy_inputs(
        request,
        make_state(),
        policy,
        agent_public_keys_by_id={CENTRAL_AGENT_ID: signing_key.public_key_b64},
        accepted_policy_digests={policy_digest(policy)},
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

    result = make_gate(key).evaluate(make_command(**command_update), lease)

    assert result.allowed is False
    assert result.reason_code == expected_reason


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
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by="edge-agent:rover-001",
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
        ),
        lease=lease,
    )

    result = gate.evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "LEASE_REVOKED"


def test_unknown_revoker_cannot_revoke_lease():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)

    with pytest.raises(ValueError, match="revocation actor is not trusted"):
        gate.revoke(
            LeaseRevocation(
                lease_id=lease.lease_id,
                revoked_by="agent:unknown",
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
    assert reason == "AGENT_NOT_ALLOWED"
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
