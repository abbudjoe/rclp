from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pydantic import ValidationError

from rclp_agents.edge_agent_daemon import EdgeAgentDaemon
from rclp_agents.central_agent_mock import request_remote_assist
import rclp_core.attestation as attestation_module
from rclp_core.attestation import attestation_auth_violation, attestation_trust_violation
import rclp_core.crypto as crypto
import rclp_core.leases as leases_module
import rclp_core.policy as policy_module
import rclp_core.state as state_module
from rclp_core.audit import AuditLog
from rclp_core.crypto import DemoKeyPair
from rclp_core.leases import issue_lease
from rclp_core.models import (
    AgentAttestation,
    AuditCommit,
    AuditEventType,
    Capability,
    CapabilityConstraintBounds,
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
    NetworkStateAssertion,
    RobotStateAssertion,
    SafetyState,
    SUPPORTED_PROTOCOL_VERSION,
)
from rclp_core.network import profile
from rclp_core.policy import (
    Policy,
    RequestReplayCache,
    _evaluate_policy_inputs,
    evaluate_policy,
    policy_constraint_bounds,
    policy_digest,
)
import rclp_ros2.command_gate as command_gate_module
from rclp_ros2.command_gate import Command, CommandGate, CommandReplayCache, RevocationStore


CENTRAL_AGENT_ID = "fleet-agent:v0.1"
EDGE_AGENT_ID = "edge-agent:rover-001"
TRUSTED_ISSUER_ID = "issuer"
CENTRAL_KEY = DemoKeyPair()
EDGE_KEY = DemoKeyPair()
_REPLAY_CACHE_DEFAULT = object()
_TEST_STORE_DIRS: list[TemporaryDirectory[str]] = []


def remote_assist_constraint_requirements() -> dict[str, CapabilityConstraintRequirement]:
    return {
        Capability.REMOTE_ASSIST.value: CapabilityConstraintRequirement(
            capability=Capability.REMOTE_ASSIST,
            require_geofence_id=True,
            require_network_thresholds=True,
            require_fallback_on_degrade=True,
        )
    }


def remote_assist_constraint_bounds(
    policy: Policy | None = None,
) -> dict[str, CapabilityConstraintBounds]:
    return policy_constraint_bounds(policy or make_policy())


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


def sign_attestation(
    attestation: AgentAttestation,
    key: DemoKeyPair = CENTRAL_KEY,
) -> AgentAttestation:
    attestation.authenticated_agent_id = attestation.agent_id
    attestation.signature = None
    attestation.signature = key.sign(attestation)
    return attestation


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
        requested_duration_seconds=600,
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
            safety_state=SafetyState.NOMINAL,
            network_state=profile("normal"),
            geofence_state=GeofenceState(geofence_id="test-zone-a", inside=True),
            human_operator_available=True,
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


def policy_trust_kwargs(
    policy: Policy,
    accepted_policy: Policy | None = None,
    replay_cache: RequestReplayCache | None | object = _REPLAY_CACHE_DEFAULT,
) -> dict:
    return {
        "agent_public_keys_by_id": {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        "edge_public_keys_by_id": {EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        "accepted_policy_digests": {policy_digest(accepted_policy or policy)},
        "replay_cache": durable_request_replay_cache()
        if replay_cache is _REPLAY_CACHE_DEFAULT
        else replay_cache,
    }


def gate_policy_kwargs(policy: Policy | None = None) -> dict:
    policy = policy or make_policy()
    return {
        "accepted_policy_id": policy.policy_id,
        "accepted_policy_digests": {policy_digest(policy)},
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
    for key_name, value in gate_policy_kwargs().items():
        kwargs.setdefault(key_name, value)
    kwargs.setdefault(
        "issuer_capability_scopes",
        {TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
    )
    kwargs.setdefault(
        "capability_constraint_requirements",
        remote_assist_constraint_requirements(),
    )
    kwargs.setdefault(
        "capability_constraint_bounds",
        remote_assist_constraint_bounds(),
    )
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


def issue_valid_lease(key: DemoKeyPair, issuer_id: str = TRUSTED_ISSUER_ID) -> CapabilityLease:
    policy = make_policy()
    request = make_request()
    _, _, _, constraints = evaluate_inputs(request, make_state(), policy)
    assert constraints is not None
    return issue_lease(
        request,
        constraints,
        issuer_id,
        key,
        ttl_seconds=600,
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )


def issue_speed_limited_lease(
    key: DemoKeyPair,
    max_speed_mps: float = 0.5,
    *,
    policy: Policy | None = None,
) -> CapabilityLease:
    policy = policy or make_policy().model_copy(deep=True)
    policy.requirements.max_speed_mps = max_speed_mps
    request = make_request()
    _, _, _, constraints = evaluate_inputs(request, make_state(), policy)
    assert constraints is not None
    assert constraints.max_speed_mps == max_speed_mps
    return issue_lease(
        request,
        constraints,
        TRUSTED_ISSUER_ID,
        key,
        ttl_seconds=600,
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )


def resign(lease: CapabilityLease, key: DemoKeyPair) -> CapabilityLease:
    lease.signature = key.sign(lease)
    return lease


def make_attestation(**updates) -> AgentAttestation:
    attestation = AgentAttestation(
        agent_id=CENTRAL_AGENT_ID,
        kind="central_agent",
        manifest_digest="sha256:test-central-agent",
        public_key_id="test-central-ed25519",
        trust_tier="development",
    )
    if updates:
        attestation = attestation.model_copy(update=updates)
    return sign_attestation(attestation)


def test_signed_agent_attestation_authenticates_claimed_identity():
    attestation = make_attestation()

    assert (
        attestation_auth_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        )
        is None
    )


def test_signed_agent_attestation_satisfies_trust_boundary():
    attestation = make_attestation()

    assert (
        attestation_trust_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            public_key_ids_by_agent_id={
                CENTRAL_AGENT_ID: "test-central-ed25519",
            },
            accepted_trust_tiers={"development"},
            manifest_digests_by_agent_id={
                CENTRAL_AGENT_ID: "sha256:test-central-agent",
            },
        )
        is None
    )


def test_agent_attestation_missing_trust_tier_is_rejected_at_boundary():
    raw_attestation = make_attestation().model_dump(mode="json")
    raw_attestation.pop("trust_tier")

    with pytest.raises(ValidationError, match="trust_tier"):
        AgentAttestation.model_validate(raw_attestation)


def test_agent_attestation_requires_explicit_trust_tier_policy():
    attestation = make_attestation()

    assert (
        attestation_trust_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            public_key_ids_by_agent_id={
                CENTRAL_AGENT_ID: "test-central-ed25519",
            },
            manifest_digests_by_agent_id={
                CENTRAL_AGENT_ID: "sha256:test-central-agent",
            },
        )
        == "ATTESTATION_TRUST_TIER_POLICY_REQUIRED"
    )


def test_agent_attestation_requires_explicit_manifest_policy():
    attestation = make_attestation()

    assert (
        attestation_trust_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            public_key_ids_by_agent_id={
                CENTRAL_AGENT_ID: "test-central-ed25519",
            },
            accepted_trust_tiers={"development"},
        )
        == "ATTESTATION_MANIFEST_DIGEST_POLICY_REQUIRED"
    )


def test_oversized_attestation_material_rejects_before_signature_verification(monkeypatch):
    attestation = make_attestation(manifest_digest=f"sha256:{'x' * 2_000}")

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("attestation signature verification should not run")

    monkeypatch.setattr(attestation_module, "verify_with_public_key_b64", fail_verify)

    assert (
        attestation_auth_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        )
        == "ATTESTATION_SIGNED_MATERIAL_TOO_LARGE"
    )


def test_oversized_invalid_attestation_material_rejects_before_signature_verification(
    monkeypatch,
):
    attestation = make_attestation(manifest_digest=f"sha256:{'x' * 2_000}").model_copy(
        update={"signature": "not-a-valid-signature"}
    )

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("invalid oversized attestation should not reach verification")

    monkeypatch.setattr(attestation_module, "verify_with_public_key_b64", fail_verify)

    assert (
        attestation_auth_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        )
        == "ATTESTATION_SIGNED_MATERIAL_TOO_LARGE"
    )


@pytest.mark.parametrize(
    ("update", "trusted_keys", "expected_reason"),
    [
        (
            {"authenticated_agent_id": None, "signature": None},
            {},
            "ATTESTATION_AUTHENTICATED_AGENT_MISSING",
        ),
        (
            {"signature": None},
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            "ATTESTATION_SIGNATURE_MISSING",
        ),
        (
            {"authenticated_agent_id": "fleet-agent:other"},
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            "ATTESTATION_AUTHENTICATED_AGENT_MISMATCH",
        ),
        ({}, {}, "ATTESTATION_AGENT_KEY_NOT_TRUSTED"),
        (
            {"manifest_digest": "sha256:tampered-after-signing"},
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            "ATTESTATION_SIGNATURE_INVALID",
        ),
    ],
)
def test_agent_attestation_auth_failures(update, trusted_keys, expected_reason):
    attestation = make_attestation()
    attestation = attestation.model_copy(update=update)

    assert attestation_auth_violation(attestation, trusted_keys) == expected_reason


@pytest.mark.parametrize(
    ("update", "accepted_tiers", "manifest_digests", "expected_reason"),
    [
        (
            {"manifest_digest": ""},
            {"development"},
            {CENTRAL_AGENT_ID: ""},
            "ATTESTATION_MANIFEST_DIGEST_MISSING",
        ),
        (
            {"public_key_id": ""},
            {"development"},
            {CENTRAL_AGENT_ID: "sha256:test-central-agent"},
            "ATTESTATION_PUBLIC_KEY_ID_MISSING",
        ),
        (
            {"revoked": True},
            {"development"},
            {CENTRAL_AGENT_ID: "sha256:test-central-agent"},
            "ATTESTATION_AGENT_REVOKED",
        ),
        (
            {},
            {"production"},
            {CENTRAL_AGENT_ID: "sha256:test-central-agent"},
            "ATTESTATION_TRUST_TIER_NOT_ACCEPTED",
        ),
        (
            {},
            {"development"},
            {},
            "ATTESTATION_MANIFEST_DIGEST_NOT_TRUSTED",
        ),
        (
            {},
            {"development"},
            {CENTRAL_AGENT_ID: "sha256:other-manifest"},
            "ATTESTATION_MANIFEST_DIGEST_MISMATCH",
        ),
    ],
)
def test_agent_attestation_trust_boundary_failures(
    update,
    accepted_tiers,
    manifest_digests,
    expected_reason,
):
    attestation = make_attestation(**update)

    assert (
        attestation_trust_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            public_key_ids_by_agent_id={
                CENTRAL_AGENT_ID: "test-central-ed25519",
            },
            accepted_trust_tiers=accepted_tiers,
            manifest_digests_by_agent_id=manifest_digests,
        )
        == expected_reason
    )


def test_agent_attestation_rejects_stale_trust_material():
    now = datetime.now(timezone.utc)
    attestation = make_attestation(created_at=now - timedelta(seconds=400))

    assert (
        attestation_trust_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            public_key_ids_by_agent_id={
                CENTRAL_AGENT_ID: "test-central-ed25519",
            },
            accepted_trust_tiers={"development"},
            manifest_digests_by_agent_id={
                CENTRAL_AGENT_ID: "sha256:test-central-agent",
            },
            now=now,
        )
        == "ATTESTATION_STALE"
    )


def test_agent_attestation_rejects_unbound_public_key_id():
    attestation = make_attestation(public_key_id="attacker-selected-key-id")

    assert (
        attestation_trust_violation(
            attestation,
            {CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            public_key_ids_by_agent_id={
                CENTRAL_AGENT_ID: "test-central-ed25519",
            },
            accepted_trust_tiers={"development"},
            manifest_digests_by_agent_id={
                CENTRAL_AGENT_ID: "sha256:test-central-agent",
            },
        )
        == "ATTESTATION_PUBLIC_KEY_ID_MISMATCH"
    )


def test_malformed_request_signature_encoding_is_rejected():
    signature = make_request().signature
    assert signature is not None
    request = make_request().model_copy(update={"signature": f"!{signature[1:]}"})

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_SIGNATURE_INVALID"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_capability_request_missing_explicit_duration_is_denied_before_policy_allow():
    raw_request = make_request().model_dump(mode="json")
    raw_request.pop("requested_duration_seconds")
    request = CapabilityRequest.model_validate(raw_request)
    request.signature = None
    sign_request(request)

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        make_policy(),
    )

    assert "requested_duration_seconds" not in request.model_fields_set
    assert decision == Decision.DENY
    assert reason == "REQUEST_REQUIRED_FIELD_MISSING"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_robot_state_missing_explicit_safety_state_is_denied_before_policy_allow():
    raw_state = make_state().model_dump(mode="json")
    raw_state.pop("safety_state")
    state = RobotStateAssertion.model_validate(raw_state)
    state.signature = None
    sign_state(state)

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        state,
        make_policy(),
    )

    assert "safety_state" not in state.model_fields_set
    assert decision == Decision.DENY
    assert reason == "STATE_REQUIRED_FIELD_MISSING"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_policy_required_human_operator_state_must_be_explicit_before_policy_allow():
    raw_state = make_state().model_dump(mode="json")
    raw_state.pop("human_operator_available")
    state = RobotStateAssertion.model_validate(raw_state)
    state.signature = None
    sign_state(state)

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        state,
        make_policy(),
    )

    assert "human_operator_available" not in state.model_fields_set
    assert decision == Decision.DENY
    assert reason == "STATE_REQUIRED_FIELD_MISSING"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_robot_state_missing_network_attached_is_rejected_before_policy_allow():
    raw_state = make_state().model_dump(mode="json")
    raw_state["network_state"].pop("attached")

    with pytest.raises(ValidationError, match="attached"):
        RobotStateAssertion.model_validate(raw_state)


def test_explicit_human_operator_available_state_still_allows_policy():
    state = make_state()

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        state,
        make_policy(),
    )

    assert "human_operator_available" in state.model_fields_set
    assert state.human_operator_available is True
    assert decision == Decision.ALLOW
    assert reason == "POLICY_SATISFIED"
    assert alternatives == []
    assert constraints is not None


def test_oversized_robot_state_material_rejects_before_signature_verification(monkeypatch):
    state = make_state().model_copy(update={"mission_id": "x" * 2_000})

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("state signature verification should not run for oversized state")

    monkeypatch.setattr(state_module, "verify_with_public_key_b64", fail_verify)

    assert (
        state_module.state_auth_violation(
            state,
            {EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        )
        == "STATE_SIGNED_MATERIAL_TOO_LARGE"
    )


def test_oversized_request_signature_rejects_before_decode_or_verify(monkeypatch):
    request = make_request().model_copy(update={"signature": "A" * 2_000})

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("verify should not run for over-budget request signature")

    monkeypatch.setattr(policy_module, "verify_with_public_key_b64", fail_verify)

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_SIGNED_MATERIAL_TOO_LARGE"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_oversized_request_signed_field_rejects_before_canonical_json(monkeypatch):
    request = make_request().model_copy(update={"reason": "X" * 2_000})
    state = make_state()

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("verify should not run for over-budget request material")

    def fail_canonical_json(payload):
        raise AssertionError("canonical_json should not run for over-budget request material")

    monkeypatch.setattr(policy_module, "verify_with_public_key_b64", fail_verify)
    monkeypatch.setattr(crypto, "canonical_json", fail_canonical_json)

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        state,
        make_policy(),
    )

    assert decision == Decision.DENY
    assert reason == "REQUEST_SIGNED_MATERIAL_TOO_LARGE"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_malformed_lease_signature_encoding_is_rejected():
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(update={"signature": "not-base64!"})

    result = make_gate(key).evaluate(make_command(), lease)

    assert result.allowed is False
    assert result.reason_code == "INVALID_SIGNATURE"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_oversized_lease_signature_rejects_before_decode_or_verify(monkeypatch):
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(update={"signature": "A" * 2_000})
    gate = make_gate(key)

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("verify should not run for over-budget lease signature")

    monkeypatch.setattr(leases_module, "verify_with_public_key_b64", fail_verify)

    result = gate.evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "LEASE_SIGNED_MATERIAL_TOO_LARGE"
    assert result.fallback_action is None
    assert result.fallback_declaration is None
    rejected = next(
        event
        for event in gate.audit_log.events
        if event.event_type == AuditEventType.COMMAND_REJECTED
    )
    assert rejected.payload["reason_code"] == "LEASE_SIGNED_MATERIAL_TOO_LARGE"


def test_oversized_lease_signed_field_rejects_before_canonical_json_or_verify(
    monkeypatch,
):
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(update={"message_id": "m" * 2_000})
    gate = make_gate(key)

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("verify should not run for over-budget lease fields")

    monkeypatch.setattr(leases_module, "verify_with_public_key_b64", fail_verify)

    result = gate.evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "LEASE_SIGNED_MATERIAL_TOO_LARGE"
    assert result.fallback_action is None
    assert result.fallback_declaration is None
    rejected = next(
        event
        for event in gate.audit_log.events
        if event.event_type == AuditEventType.COMMAND_REJECTED
    )
    assert rejected.payload["reason_code"] == "LEASE_SIGNED_MATERIAL_TOO_LARGE"


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
        NetworkState(
            attached=True,
            latency_ms_p95=float("inf"),
            packet_loss_pct=0.0,
            uplink_mbps=1.0,
        )
    with pytest.raises(ValueError):
        LeaseConstraints(max_speed_mps=float("inf"))
    with pytest.raises(ValueError):
        CapabilityConstraintBounds(
            capability=Capability.REMOTE_ASSIST,
            max_speed_mps=float("inf"),
        )


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
    assert result.fallback_action is None
    assert result.fallback_declaration is None


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


def test_capability_request_future_authority_fields_are_rejected_at_boundary():
    raw_request = make_request().model_dump(mode="json")
    raw_request["future_authority_override"] = "allow"

    with pytest.raises(ValidationError, match="future_authority_override"):
        CapabilityRequest.model_validate(raw_request)


def test_robot_state_future_authority_fields_are_rejected_at_boundary():
    raw_state = make_state().model_dump(mode="json")
    raw_state["future_authority_override"] = "allow"

    with pytest.raises(ValidationError, match="future_authority_override"):
        RobotStateAssertion.model_validate(raw_state)


def test_raw_unsupported_lease_protocol_version_is_rejected_at_boundary():
    key = DemoKeyPair()
    raw_lease = issue_valid_lease(key).model_dump(mode="json")
    raw_lease["protocol_version"] = "999.0-unsupported"

    with pytest.raises(ValueError, match="unsupported protocol_version"):
        CapabilityLease.model_validate(raw_lease)


def test_raw_lease_future_fields_are_rejected_at_boundary():
    key = DemoKeyPair()
    raw_lease = issue_valid_lease(key).model_dump(mode="json")
    raw_lease["future_authority_override"] = "allow"

    with pytest.raises(ValueError, match="future_authority_override"):
        CapabilityLease.model_validate(raw_lease)


def test_raw_lease_nested_future_fields_are_rejected_at_boundary():
    key = DemoKeyPair()
    raw_lease = issue_valid_lease(key).model_dump(mode="json")
    raw_lease["constraints"]["future_authority_override"] = "allow"

    with pytest.raises(ValueError, match="future_authority_override"):
        CapabilityLease.model_validate(raw_lease)


def test_authority_models_reject_string_numeric_and_boolean_scalars_at_boundary():
    raw_request = make_request().model_dump(mode="json")
    raw_request["requested_duration_seconds"] = "600"
    with pytest.raises(ValidationError, match="JSON integers"):
        CapabilityRequest.model_validate(raw_request)

    raw_request = make_request(
        requested_constraints=LeaseConstraints(max_speed_mps=0.5)
    ).model_dump(mode="json")
    raw_request["requested_constraints"]["max_speed_mps"] = "0.5"
    with pytest.raises(ValidationError, match="JSON numbers"):
        CapabilityRequest.model_validate(raw_request)

    raw_state = make_state().model_dump(mode="json")
    raw_state["network_state"]["attached"] = "false"
    with pytest.raises(ValidationError, match="JSON booleans"):
        RobotStateAssertion.model_validate(raw_state)

    raw_state = make_state().model_dump(mode="json")
    raw_state["network_state"]["latency_ms_p95"] = "45"
    with pytest.raises(ValidationError, match="JSON numbers"):
        RobotStateAssertion.model_validate(raw_state)

    raw_network_assertion = {
        "protocol_version": SUPPORTED_PROTOCOL_VERSION,
        "message_type": "network_state_assertion",
        "edge_agent_id": EDGE_AGENT_ID,
        "robot_id": "rover-001",
        "mission_id": "mission-001",
        "profile": NetworkProfile.NORMAL.value,
        "attached": True,
        "latency_ms_p95": 45.0,
        "packet_loss_pct": 0.1,
        "uplink_mbps": 8.0,
        "measurement_window_seconds": "10",
        "source": "test",
    }
    with pytest.raises(ValidationError, match="JSON integers"):
        NetworkStateAssertion.model_validate(raw_network_assertion)

    raw_requirement = {
        "capability": Capability.REMOTE_ASSIST.value,
        "require_geofence_id": "true",
    }
    with pytest.raises(ValidationError, match="JSON booleans"):
        CapabilityConstraintRequirement.model_validate(raw_requirement)

    raw_bounds = {
        "capability": Capability.REMOTE_ASSIST.value,
        "max_speed_mps": "0.5",
    }
    with pytest.raises(ValidationError, match="JSON numbers"):
        CapabilityConstraintBounds.model_validate(raw_bounds)

    raw_audit = AuditCommit(
        correlation_id="corr_scalar",
        event_type=AuditEventType.DIAGNOSTIC,
        actor_id="test",
        summary="scalar boundary",
    ).model_dump(mode="json")
    raw_audit["authority_relevant"] = "false"
    with pytest.raises(ValidationError, match="JSON booleans"):
        AuditCommit.model_validate(raw_audit)


def test_json_integer_network_metrics_remain_valid_numbers():
    network = NetworkState(
        attached=True,
        latency_ms_p95=45,
        packet_loss_pct=0,
        uplink_mbps=8,
    )

    assert network.latency_ms_p95 == 45
    assert network.packet_loss_pct == 0
    assert network.uplink_mbps == 8


def test_partition_profile_with_attached_state_denies_policy_and_command_gate():
    key = DemoKeyPair()
    contradictory_network = profile("normal").model_copy(
        update={
            "profile": NetworkProfile.PARTITION,
            "attached": True,
        }
    )
    state = sign_state(
        make_state().model_copy(
            update={
                "network_state": contradictory_network,
                "signature": None,
            }
        )
    )

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        state,
        make_policy(),
    )
    assert decision == Decision.DENY
    assert reason == "NETWORK_DETACHED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None

    result = make_gate(key).evaluate(make_command(), issue_valid_lease(key), current_state=state)
    assert result.allowed is False
    assert result.reason_code == "NETWORK_DETACHED"
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.fallback_action == FallbackAction.CRAWL_TO_SAFE_ZONE


@pytest.mark.parametrize(
    "missing_field",
    ["protocol_version", "message_id", "correlation_id", "created_at", "message_type"],
)
def test_raw_lease_missing_common_envelope_field_is_rejected_at_boundary(missing_field):
    key = DemoKeyPair()
    raw_lease = issue_valid_lease(key).model_dump(mode="json")
    raw_lease.pop(missing_field)

    with pytest.raises(ValueError, match=missing_field):
        CapabilityLease.model_validate(raw_lease)


def test_unsupported_lease_protocol_version_is_denied_before_authorization():
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(
        update={"protocol_version": "999.0-unsupported", "signature": None}
    )
    resign(lease, key)

    result = make_gate(key).evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "PROTOCOL_VERSION_UNSUPPORTED"


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
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_expired_lease_does_not_emit_fallback_from_lease_constraint():
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
    assert result.fallback_action is None
    assert result.fallback_declaration is None


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
                    attached=True,
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


def test_policy_rejects_ephemeral_temporary_replay_store_for_authority_issuance():
    replay_cache = RequestReplayCache.temporary()

    decision, reason, alternatives, constraints = evaluate_inputs(
        make_request(),
        make_state(),
        make_policy(),
        replay_cache=replay_cache,
    )

    assert replay_cache.store_path is not None
    assert replay_cache.durable is False
    assert decision == Decision.DENY
    assert reason == "REQUEST_REPLAY_STORE_DURABLE_REQUIRED"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_policy_rejects_unknown_top_level_field_before_digest_pin():
    raw_policy = make_policy().model_dump(mode="json")
    raw_policy["future_authority_override"] = "allow"

    with pytest.raises(ValidationError, match="future_authority_override"):
        Policy.model_validate(raw_policy)


@pytest.mark.parametrize(
    "path",
    [
        ("requirements", "network", "future_threshold"),
        ("requirements", "future_scope"),
        ("fallback", "future_fallback"),
    ],
)
def test_policy_rejects_unknown_nested_field_before_digest_pin(path):
    raw_policy = make_policy().model_dump(mode="json")
    target = raw_policy
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = "allow"

    with pytest.raises(ValidationError, match=path[-1]):
        Policy.model_validate(raw_policy)


def test_policy_rejects_string_numeric_and_boolean_scalars_before_digest_pin():
    raw_policy = make_policy().model_dump(mode="json")
    raw_policy["lease_ttl_seconds"] = "600"
    with pytest.raises(ValidationError, match="JSON integers"):
        Policy.model_validate(raw_policy)

    raw_policy = make_policy().model_dump(mode="json")
    raw_policy["requirements"]["geofence_required"] = "false"
    with pytest.raises(ValidationError, match="JSON booleans"):
        Policy.model_validate(raw_policy)

    raw_policy = make_policy().model_dump(mode="json")
    raw_policy["requirements"]["max_speed_mps"] = "0.5"
    with pytest.raises(ValidationError, match="JSON numbers"):
        Policy.model_validate(raw_policy)

    raw_policy = make_policy().model_dump(mode="json")
    raw_policy["requirements"]["network"]["max_latency_ms_p95"] = "80"
    with pytest.raises(ValidationError, match="JSON numbers"):
        Policy.model_validate(raw_policy)


def test_requested_speed_constraint_cannot_create_policy_authority():
    policy = make_policy()
    request = make_request(
        requested_constraints=LeaseConstraints(max_speed_mps=0.5),
    )

    decision, reason, alternatives, constraints = evaluate_inputs(request, make_state(), policy)

    assert decision == Decision.DENY
    assert reason == "REQUESTED_CONSTRAINTS_TOO_BROAD"
    assert alternatives == [FallbackAction.LOCAL_AUTONOMY_ONLY]
    assert constraints is None


def test_requested_speed_constraint_can_narrow_policy_owned_ceiling():
    policy = make_policy().model_copy(deep=True)
    policy.requirements.max_speed_mps = 0.75
    request = make_request(
        requested_constraints=LeaseConstraints(max_speed_mps=0.5),
    )

    decision, reason, alternatives, constraints = evaluate_inputs(request, make_state(), policy)

    assert decision == Decision.ALLOW
    assert reason == "POLICY_SATISFIED"
    assert alternatives == []
    assert constraints is not None
    assert constraints.max_speed_mps == 0.5


def test_requested_constraints_cannot_expand_policy_network_thresholds():
    policy = make_policy()
    request = make_request(
        requested_constraints=LeaseConstraints(
            max_latency_ms_p95=policy.requirements.network.max_latency_ms_p95 + 1
        ),
    )

    decision, reason, alternatives, constraints = evaluate_inputs(
        request,
        make_state(),
        policy,
    )

    assert decision == Decision.DENY
    assert reason == "REQUESTED_CONSTRAINTS_TOO_BROAD"
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
        replay_cache=durable_request_replay_cache(),
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


def test_lease_ttl_exact_max_passes_but_max_plus_one_rejects_within_skew():
    key = DemoKeyPair()
    now = datetime.now(timezone.utc)
    exact_max_lease = issue_valid_lease(key).model_copy(
        update={
            "issued_at": now,
            "expires_at": now + timedelta(seconds=600),
            "signature": None,
        }
    )
    overlong_lease = issue_valid_lease(key).model_copy(
        update={
            "issued_at": now,
            "expires_at": now + timedelta(seconds=601),
            "signature": None,
        }
    )
    resign(exact_max_lease, key)
    resign(overlong_lease, key)

    assert (
        leases_module.lease_time_violation(
            exact_max_lease,
            at=now,
            max_lease_age_seconds=600,
            max_lease_ttl_seconds=600,
            clock_skew_seconds=30,
        )
        is None
    )
    assert (
        leases_module.lease_time_violation(
            overlong_lease,
            at=now,
            max_lease_age_seconds=600,
            max_lease_ttl_seconds=600,
            clock_skew_seconds=30,
        )
        == "LEASE_TTL_TOO_LONG"
    )


def test_command_gate_rejects_lease_ttl_max_plus_one_even_within_skew():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    overlong_lease = lease.model_copy(
        update={
            "expires_at": lease.issued_at + timedelta(seconds=601),
            "signature": None,
        }
    )
    resign(overlong_lease, key)

    result = make_gate(key, max_lease_ttl_seconds=600).evaluate(
        make_command(),
        overlong_lease,
        current_state=make_state(),
    )

    assert result.allowed is False
    assert result.reason_code == "LEASE_TTL_TOO_LONG"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


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


def test_no_speed_lease_allows_empty_command_payload():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)

    result = make_gate(key).evaluate(
        make_command(payload={}),
        lease,
        current_state=make_state(),
    )

    assert result.allowed is True
    assert result.reason_code == "LEASE_VALID"


@pytest.mark.parametrize(
    "payload",
    [
        {"intent": "start_remote_assist"},
        {"max_speed_mps": 0.25},
        {"speed_mps": 0.25},
    ],
)
def test_no_speed_lease_rejects_nonempty_command_payload_schema(payload):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)

    result = make_gate(key).evaluate(
        make_command(payload=payload),
        lease,
        current_state=make_state(),
    )

    assert result.allowed is False
    assert result.reason_code == "COMMAND_PAYLOAD_SCHEMA_VIOLATION"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_signed_lease_cannot_expand_policy_absent_speed_ceiling():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    constraints = lease.constraints.model_copy(update={"max_speed_mps": 100.0})
    lease = resign(lease.model_copy(update={"constraints": constraints, "signature": None}), key)

    result = make_gate(key).evaluate(
        make_command(payload={"max_speed_mps": 99.0}),
        lease,
        current_state=make_state(),
    )

    assert result.allowed is False
    assert result.reason_code == "LEASE_CONSTRAINTS_EXCEED_POLICY"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_signed_lease_cannot_relax_policy_network_thresholds():
    key = DemoKeyPair()
    policy = make_policy()
    lease = issue_valid_lease(key)
    constraints = lease.constraints.model_copy(
        update={"max_latency_ms_p95": policy.requirements.network.max_latency_ms_p95 + 1}
    )
    lease = resign(lease.model_copy(update={"constraints": constraints, "signature": None}), key)

    result = make_gate(key).evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "LEASE_CONSTRAINTS_EXCEED_POLICY"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_policy_derived_bounds_include_required_geofence_identity():
    bounds = remote_assist_constraint_bounds()

    assert bounds[Capability.REMOTE_ASSIST.value].geofence_id == "test-zone-a"


def test_policy_required_geofence_identity_must_be_explicit():
    raw_policy = make_policy().model_dump(mode="json")
    raw_policy["requirements"].pop("geofence_id")

    with pytest.raises(ValidationError, match="geofence_id is required"):
        Policy.model_validate(raw_policy)


def test_signed_lease_cannot_expand_policy_geofence_identity():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    constraints = lease.constraints.model_copy(update={"geofence_id": "wrong-zone"})
    lease = resign(lease.model_copy(update={"constraints": constraints, "signature": None}), key)

    result = make_gate(key).evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "LEASE_CONSTRAINTS_EXCEED_POLICY"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


@pytest.mark.parametrize(
    ("payload", "expected_allowed", "expected_reason"),
    [
        ({"max_speed_mps": 0.4}, True, "LEASE_VALID"),
        ({"speed_mps": 0.4}, True, "LEASE_VALID"),
        ({"max_speed_mps": 0.4, "speed_mps": 0.4}, True, "LEASE_VALID"),
        ({"max_speed_mps": 0.6}, False, "COMMAND_SPEED_TOO_HIGH"),
        ({}, False, "COMMAND_SPEED_MISSING"),
        ({"max_speed_mps": "fast"}, False, "COMMAND_SPEED_MALFORMED"),
        ({"max_speed_mps": float("nan")}, False, "COMMAND_SPEED_MALFORMED"),
        (
            {"max_speed_mps": 0.4, "motion": {"max_speed_mps": 99.0}},
            False,
            "COMMAND_PAYLOAD_SCHEMA_VIOLATION",
        ),
        (
            {"max_speed_mps": 0.4, "trajectory": [{"speed_mps": 99.0}]},
            False,
            "COMMAND_PAYLOAD_SCHEMA_VIOLATION",
        ),
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
    policy = make_policy().model_copy(deep=True)
    lease = issue_speed_limited_lease(key, max_speed_mps=0.5, policy=policy)
    command = make_command(payload=payload)

    result = make_gate(
        key,
        **gate_policy_kwargs(policy),
        capability_constraint_bounds=remote_assist_constraint_bounds(policy),
    ).evaluate(command, lease, current_state=make_state())

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
    assert result.fallback_action is None
    assert result.fallback_declaration is None


@pytest.mark.parametrize(
    ("command_edge_agent_id", "lease_edge_agent_id"),
    [
        ("edge-agent:rover-002", "edge-agent:rover-002"),
        (EDGE_AGENT_ID, "edge-agent:rover-002"),
    ],
)
def test_direct_command_gate_rejects_nonlocal_edge_context_before_lease_validation(
    command_edge_agent_id,
    lease_edge_agent_id,
):
    key = DemoKeyPair()
    other_edge_key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(
        update={"edge_agent_id": lease_edge_agent_id, "signature": None}
    )
    lease = resign(lease, key)
    command = make_command(edge_agent_id=command_edge_agent_id)
    state_edge_agent_id = command_edge_agent_id
    current_state = sign_state(
        RobotStateAssertion(
            robot_id="rover-001",
            edge_agent_id=state_edge_agent_id,
            mission_id="mission-001",
            safety_state=SafetyState.NOMINAL,
            network_state=profile("normal"),
            geofence_state=GeofenceState(geofence_id="test-zone-a", inside=True),
            human_operator_available=True,
        ),
        other_edge_key if state_edge_agent_id != EDGE_AGENT_ID else EDGE_KEY,
    )
    gate = make_gate(
        key,
        state_public_keys_by_edge_id={
            EDGE_AGENT_ID: EDGE_KEY.public_key_b64,
            "edge-agent:rover-002": other_edge_key.public_key_b64,
        },
    )

    result = gate.evaluate(command, lease, current_state=current_state)

    assert result.allowed is False
    assert result.reason_code == "EDGE_AGENT_MISMATCH"
    assert result.fallback_action is None
    assert result.fallback_declaration is None
    assert gate.audit_log.events[-1].event_type == AuditEventType.COMMAND_REJECTED
    assert gate.audit_log.events[-1].actor_id == EDGE_AGENT_ID
    assert gate.audit_log.events[-1].payload["expected_edge_agent_id"] == EDGE_AGENT_ID
    assert gate.audit_log.events[-1].payload["command_edge_agent_id"] == command_edge_agent_id
    assert gate.audit_log.events[-1].payload["lease_edge_agent_id"] == lease_edge_agent_id


def test_nonlocal_edge_rejection_does_not_consume_command_replay_nonce():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    nonlocal_command = make_command(edge_agent_id="edge-agent:rover-002")

    mismatch = gate.evaluate(nonlocal_command, lease, current_state=make_state())
    corrected_command = make_command(
        command_id=nonlocal_command.command_id,
        command_nonce=nonlocal_command.command_nonce,
        edge_agent_id=EDGE_AGENT_ID,
    )
    corrected = gate.evaluate(corrected_command, lease, current_state=make_state())

    assert mismatch.allowed is False
    assert mismatch.reason_code == "EDGE_AGENT_MISMATCH"
    assert corrected.allowed is True
    assert corrected.reason_code == "LEASE_VALID"


def test_command_without_signature_is_rejected_before_lease_validation():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command().model_copy(update={"signature": None})

    result = make_gate(key).evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_SIGNATURE_MISSING"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


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
    assert gate.audit_log.events[-1].event_type == AuditEventType.DIAGNOSTIC
    assert gate.audit_log.events[-1].authority_relevant is False
    assert gate.audit_log.events[-1].actor_id == "local_command_gate"
    assert gate.audit_log.events[-1].payload["reason_code"] == "COMMAND_AUTHENTICATED_AGENT_MISSING"
    assert gate.fallback_events == []


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


@pytest.mark.parametrize(
    "command_update",
    [
        {"command_id": "x" * 2_000},
        {"payload": {"blob": "x" * 70_000}},
        {"payload": {"nested": {"child": {"leaf": "ok"}}}},
    ],
)
def test_oversized_signed_command_material_rejects_before_canonical_json(
    monkeypatch,
    command_update,
):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command()
    if "payload" in command_update and "nested" in command_update["payload"]:
        payload = command_update["payload"]
        for _ in range(40):
            payload = {"child": payload}
        command_update = {"payload": payload}
    command = command.model_copy(update=command_update)
    state = make_state()
    gate = make_gate(key)
    canonical_json_calls = 0
    original_canonical_json = crypto.canonical_json

    def counting_canonical_json(payload):
        nonlocal canonical_json_calls
        canonical_json_calls += 1
        return original_canonical_json(payload)

    monkeypatch.setattr(crypto, "canonical_json", counting_canonical_json)

    result = gate.evaluate(command, lease, current_state=state)

    assert result.allowed is False
    assert result.reason_code == "COMMAND_SIGNED_MATERIAL_TOO_LARGE"
    assert result.fallback_action is None
    assert result.fallback_declaration is None
    assert canonical_json_calls == 0
    assert gate.fallback_events == []
    assert [event.event_type for event in gate.audit_log.events] == [AuditEventType.DIAGNOSTIC]
    assert gate.audit_log.events[0].authority_relevant is False
    assert gate.audit_log.events[0].actor_id == "local_command_gate"


def test_oversized_command_signature_rejects_before_decode_or_verify(monkeypatch):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command().model_copy(update={"signature": "A" * 2_000})
    gate = make_gate(key)

    def fail_unb64(value):
        raise AssertionError(f"unb64 should not decode over-budget signature {len(value)}")

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("verify should not run for over-budget command signature")

    monkeypatch.setattr(command_gate_module, "unb64", fail_unb64)
    monkeypatch.setattr(command_gate_module, "verify_with_public_key_b64", fail_verify)

    result = gate.evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_SIGNED_MATERIAL_TOO_LARGE"
    assert result.fallback_action is None
    assert result.fallback_declaration is None
    assert gate.audit_log.events[-1].event_type == AuditEventType.DIAGNOSTIC
    assert gate.audit_log.events[-1].payload["reason_code"] == "COMMAND_SIGNED_MATERIAL_TOO_LARGE"


def test_malformed_command_signature_rejects_before_canonical_json(monkeypatch):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    command = make_command().model_copy(update={"signature": "not-base64!"})
    state = make_state()
    gate = make_gate(key)
    canonical_json_calls = 0
    original_canonical_json = crypto.canonical_json

    def counting_canonical_json(payload):
        nonlocal canonical_json_calls
        canonical_json_calls += 1
        return original_canonical_json(payload)

    monkeypatch.setattr(crypto, "canonical_json", counting_canonical_json)

    result = gate.evaluate(command, lease, current_state=state)

    assert result.allowed is False
    assert result.reason_code == "COMMAND_SIGNATURE_INVALID"
    assert result.fallback_action is None
    assert result.fallback_declaration is None
    assert canonical_json_calls == 0


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


@pytest.mark.parametrize(
    ("case_name", "expected_reason"),
    [
        ("missing_authenticated_agent", "COMMAND_AUTHENTICATED_AGENT_MISSING"),
        ("missing_signature", "COMMAND_SIGNATURE_MISSING"),
        ("invalid_signature", "COMMAND_SIGNATURE_INVALID"),
        ("untrusted_agent_key", "COMMAND_AGENT_KEY_NOT_TRUSTED"),
    ],
)
def test_command_auth_denials_do_not_emit_fallback_side_effects(case_name, expected_reason):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    emitted = []
    gate = make_gate(key, fallback_sink=emitted.append)
    command = make_command()
    if case_name == "missing_authenticated_agent":
        command = command.model_copy(update={"authenticated_agent_id": None, "signature": None})
    elif case_name == "missing_signature":
        command = command.model_copy(update={"signature": None})
    elif case_name == "invalid_signature":
        command = command.model_copy(update={"payload": {"tampered_after_signing": True}})
    elif case_name == "untrusted_agent_key":
        command = make_command(agent_id="fleet-agent:unknown")

    result = gate.evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == expected_reason
    assert result.fallback_action is None
    assert result.fallback_declaration is None
    assert emitted == []
    assert gate.fallback_events == []
    assert [event.event_type for event in gate.audit_log.events] == [AuditEventType.DIAGNOSTIC]
    assert gate.audit_log.events[0].authority_relevant is False
    assert gate.audit_log.events[0].actor_id == "local_command_gate"
    payload = gate.audit_log.events[0].payload
    assert payload["fallback_action"] is None
    for trusted_key in [
        "command_id",
        "command_message_id",
        "agent_id",
        "authenticated_agent_id",
        "edge_agent_id",
        "robot_id",
        "mission_id",
        "capability",
        "command_nonce",
        "lease_id",
    ]:
        assert trusted_key not in payload
    assert payload["claimed_command_id"] == command.command_id
    assert payload["claimed_agent_id"] == command.agent_id
    assert payload["claimed_edge_agent_id"] == command.edge_agent_id
    assert payload["claimed_robot_id"] == command.robot_id
    assert payload["claimed_mission_id"] == command.mission_id
    assert payload["claimed_capability"] == command.capability
    assert payload["claimed_lease_id"] == lease.lease_id


def test_command_auth_diagnostic_bounds_oversized_claimed_fields():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    huge_command_id = "cmd-" + ("x" * 20_000)
    command = make_command(command_id=huge_command_id).model_copy(
        update={"authenticated_agent_id": None, "signature": None}
    )
    gate = make_gate(key)

    result = gate.evaluate(command, lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "COMMAND_AUTHENTICATED_AGENT_MISSING"
    event = gate.audit_log.events[-1]
    assert event.event_type == AuditEventType.DIAGNOSTIC
    assert huge_command_id not in event.summary
    claimed_command_id = event.payload["claimed_command_id"]
    assert claimed_command_id["byte_length"] == len(huge_command_id)
    assert claimed_command_id["truncated"] is True
    assert claimed_command_id["sha256"].startswith("sha256:")
    assert "value" not in claimed_command_id


def test_revocation_diagnostic_bounds_oversized_claimed_revoker():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    huge_revoker = "revoker-" + ("x" * 20_000)
    revocation = LeaseRevocation(
        lease_id=lease.lease_id,
        revoked_by=huge_revoker,
        edge_agent_id=EDGE_AGENT_ID,
        reason_code="NETWORK_PROFILE_REVOKE",
        fallback_action=FallbackAction.HOLD_POSITION,
    )
    gate = make_gate(key)

    with pytest.raises(ValueError, match="revocation actor is not trusted"):
        gate.revoke(revocation, lease=lease)

    event = gate.audit_log.events[-1]
    assert event.event_type == AuditEventType.REVOCATION_REJECTED
    assert huge_revoker not in event.summary
    assert event.related_message_ids == []
    claimed_revoked_by = event.payload["claimed_revoked_by"]
    assert claimed_revoked_by["byte_length"] == len(huge_revoker)
    assert claimed_revoked_by["truncated"] is True
    assert claimed_revoked_by["sha256"].startswith("sha256:")
    assert "value" not in claimed_revoked_by


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
    assert second.fallback_action is None
    assert second.fallback_declaration is None
    assert gate.fallback_events == []
    assert gate.audit_log.events[-1].event_type == AuditEventType.COMMAND_REJECTED
    assert gate.audit_log.events[-1].authority_relevant is True
    assert gate.audit_log.events[-1].actor_id == EDGE_AGENT_ID
    assert gate.audit_log.events[-1].payload["reason_code"] == "COMMAND_REPLAYED"
    assert gate.audit_log.events[-1].payload["fallback_action"] is None


def test_missing_lease_denial_does_not_consume_command_replay_or_emit_fallback():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    emitted = []
    gate = make_gate(key, fallback_sink=emitted.append)
    command = make_command()

    missing_lease = gate.evaluate(command, None, current_state=make_state())
    with_valid_lease = gate.evaluate(command, lease, current_state=make_state())

    assert missing_lease.allowed is False
    assert missing_lease.reason_code == "NO_LEASE"
    assert missing_lease.fallback_action is None
    assert missing_lease.fallback_declaration is None
    assert with_valid_lease.allowed is True
    assert with_valid_lease.reason_code == "LEASE_VALID"
    assert with_valid_lease.fallback_declaration is None
    assert emitted == []
    assert gate.fallback_events == []


def test_replayed_post_auth_denial_does_not_reemit_fallback():
    key = DemoKeyPair()
    emitted = []
    gate = make_gate(key, fallback_sink=emitted.append)
    lease = issue_valid_lease(key)
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            capability=lease.capability,
        )
    )
    gate.revoke(revocation, lease=lease)
    baseline_fallback_count = len(gate.fallback_events)
    emitted.clear()
    command = make_command()

    first = gate.evaluate(command, lease, current_state=make_state())
    second = gate.evaluate(command, lease, current_state=make_state())

    assert first.allowed is False
    assert first.reason_code == "LEASE_REVOKED"
    assert first.fallback_declaration is not None
    assert second.allowed is False
    assert second.reason_code == "COMMAND_REPLAYED"
    assert second.fallback_declaration is None
    assert len(emitted) == 1
    assert len(gate.fallback_events) == baseline_fallback_count + 1


def test_command_gate_accepts_signed_lease_with_matching_policy_provenance():
    key = DemoKeyPair()
    lease = issue_valid_lease(key)

    result = make_gate(key).evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is True
    assert result.reason_code == "LEASE_VALID"


def test_command_gate_rejects_signed_lease_missing_policy_provenance():
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(
        update={"policy_id": None, "policy_digest": None, "signature": None}
    )
    lease.signature = key.sign(lease)

    result = make_gate(key).evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "LEASE_POLICY_PROVENANCE_REQUIRED"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_command_gate_rejects_signed_lease_policy_digest_mismatch():
    key = DemoKeyPair()
    lease = issue_valid_lease(key).model_copy(
        update={"policy_digest": "sha256:stale-policy-digest", "signature": None}
    )
    lease.signature = key.sign(lease)

    result = make_gate(key).evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "LEASE_POLICY_NOT_ACCEPTED"
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_command_gate_requires_durable_command_replay_cache():
    key = DemoKeyPair()

    with pytest.raises(ValueError, match="durable command_replay_cache"):
        CommandGate(
            key.public_key_b64,
            local_edge_agent_id=EDGE_AGENT_ID,
            trusted_issuer_ids={TRUSTED_ISSUER_ID},
            trusted_revoker_ids={EDGE_AGENT_ID},
            accepted_capabilities={Capability.REMOTE_ASSIST.value},
            **gate_policy_kwargs(),
            issuer_capability_scopes={TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
            capability_constraint_requirements=remote_assist_constraint_requirements(),
            capability_constraint_bounds=remote_assist_constraint_bounds(),
            agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            revoker_public_keys_by_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
            state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
            command_replay_cache=CommandReplayCache(),
            revocation_store=durable_revocation_store(),
        )


def test_command_gate_requires_durable_revocation_store():
    key = DemoKeyPair()

    with pytest.raises(ValueError, match="durable revocation_store"):
        CommandGate(
            key.public_key_b64,
            local_edge_agent_id=EDGE_AGENT_ID,
            trusted_issuer_ids={TRUSTED_ISSUER_ID},
            trusted_revoker_ids={EDGE_AGENT_ID},
            accepted_capabilities={Capability.REMOTE_ASSIST.value},
            **gate_policy_kwargs(),
            issuer_capability_scopes={TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
            capability_constraint_requirements=remote_assist_constraint_requirements(),
            capability_constraint_bounds=remote_assist_constraint_bounds(),
            agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            revoker_public_keys_by_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
            state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
            command_replay_cache=durable_command_replay_cache(),
            revocation_store=RevocationStore(),
        )


def test_command_gate_rejects_ephemeral_temporary_stores():
    key = DemoKeyPair()
    command_cache = CommandReplayCache.temporary()
    revocation_store = RevocationStore.temporary()

    assert command_cache.store_path is not None
    assert command_cache.durable is False
    assert revocation_store.store_path is not None
    assert revocation_store.durable is False

    with pytest.raises(ValueError, match="durable command_replay_cache"):
        make_gate(
            key,
            command_replay_cache=command_cache,
            revocation_store=durable_revocation_store(),
        )
    with pytest.raises(ValueError, match="durable revocation_store"):
        make_gate(
            key,
            command_replay_cache=durable_command_replay_cache(),
            revocation_store=revocation_store,
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


def test_revoked_lease_is_rejected_after_gate_restart(tmp_path):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    revocation_store = tmp_path / "revocations.sqlite3"
    first_gate = make_gate(key, revocation_store=RevocationStore(revocation_store))
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            capability=lease.capability,
        )
    )

    first_gate.revoke(revocation, lease=lease)
    second_gate = make_gate(key, revocation_store=RevocationStore(revocation_store))
    result = second_gate.evaluate(make_command(), lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "LEASE_REVOKED"
    assert result.fallback_declaration is not None
    assert result.fallback_declaration.revocation_id == revocation.message_id
    assert second_gate.revoked_lease_ids == {lease.lease_id}


def test_replayed_signed_revocation_after_restart_does_not_reemit_fallback(tmp_path):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    emitted = []
    revocation_store = tmp_path / "revocations.sqlite3"
    first_gate = make_gate(
        key,
        revocation_store=RevocationStore(revocation_store),
        fallback_sink=emitted.append,
    )
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=EDGE_AGENT_ID,
            edge_agent_id=EDGE_AGENT_ID,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            capability=lease.capability,
        )
    )

    first_fallback = first_gate.revoke(revocation, lease=lease)
    second_gate = make_gate(
        key,
        revocation_store=RevocationStore(revocation_store),
        fallback_sink=emitted.append,
    )
    replay_result = second_gate.revoke(revocation, lease=lease)

    assert first_fallback is not None
    assert replay_result is None
    assert len(emitted) == 1
    assert len(first_gate.fallback_events) == 1
    assert second_gate.fallback_events == []
    assert second_gate.audit_log.events[-1].event_type == AuditEventType.REVOCATION_REJECTED
    assert second_gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_REPLAYED"


def test_trusted_issuer_cannot_grant_capability_outside_local_scope():
    key = DemoKeyPair()
    policy = make_policy()
    now = datetime.now(timezone.utc)
    lease = CapabilityLease(
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        message_id="msg_unsupported_capability_lease",
        correlation_id="corr_unsupported_capability_lease",
        created_at=now,
        message_type="capability_lease",
        issuer_id=TRUSTED_ISSUER_ID,
        agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.AUTONOMY_ESCALATION,
        constraints=LeaseConstraints(),
        issued_at=now,
        expires_at=now + timedelta(seconds=300),
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
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


def mission_continue_constraint_bounds() -> dict[str, CapabilityConstraintBounds]:
    bounds = remote_assist_constraint_bounds()
    bounds[Capability.MISSION_CONTINUE.value] = CapabilityConstraintBounds(
        capability=Capability.MISSION_CONTINUE,
        geofence_id="test-zone-a",
        max_speed_mps=0.5,
    )
    return bounds


def issue_mission_continue_lease(
    key: DemoKeyPair,
    constraints: LeaseConstraints,
) -> CapabilityLease:
    policy = make_policy()
    now = datetime.now(timezone.utc)
    lease = CapabilityLease(
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        message_id=f"msg_mission_continue_{now.timestamp()}",
        correlation_id="corr_mission_continue",
        created_at=now,
        message_type="capability_lease",
        issuer_id=TRUSTED_ISSUER_ID,
        agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id="rover-001",
        mission_id="mission-001",
        capability=Capability.MISSION_CONTINUE,
        constraints=constraints,
        issued_at=now,
        expires_at=now + timedelta(seconds=300),
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
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
        capability_constraint_bounds=mission_continue_constraint_bounds(),
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
        capability_constraint_bounds=mission_continue_constraint_bounds(),
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
        capability_constraint_bounds={
            **remote_assist_constraint_bounds(),
            Capability.MISSION_CONTINUE.value: CapabilityConstraintBounds(
                capability=Capability.MISSION_CONTINUE,
                fallback_on_degrade=FallbackAction.CRAWL_TO_SAFE_ZONE,
            ),
        },
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


def test_implicit_fallback_default_cannot_bypass_policy_bounds():
    constraints = LeaseConstraints()
    bounds = CapabilityConstraintBounds(
        capability=Capability.MISSION_CONTINUE,
        fallback_on_degrade=FallbackAction.CRAWL_TO_SAFE_ZONE,
    )

    assert "fallback_on_degrade" not in constraints.model_fields_set
    assert leases_module.capability_constraints_exceed_bounds(constraints, bounds) is True


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
    assert result.fallback_action is None
    assert result.fallback_declaration is None


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
    assert result.fallback_action is None
    assert result.fallback_declaration is None


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
    assert gate.audit_log.events[-1].actor_id == "local_command_gate"
    assert gate.audit_log.events[-1].payload["claimed_revoked_by"] == EDGE_AGENT_ID
    assert "revoked_by" not in gate.audit_log.events[-1].payload


def test_oversized_revocation_signature_rejects_before_decode_or_verify(monkeypatch):
    key = DemoKeyPair()
    lease = issue_valid_lease(key)
    gate = make_gate(key)
    revocation = LeaseRevocation(
        lease_id=lease.lease_id,
        revoked_by=EDGE_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        reason_code="COMPROMISE_SUSPECTED",
        fallback_action=FallbackAction.HOLD_POSITION,
        signature="A" * 2_000,
    )

    def fail_unb64(value):
        raise AssertionError(f"unb64 should not decode over-budget signature {len(value)}")

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("verify should not run for over-budget revocation signature")

    monkeypatch.setattr(command_gate_module, "unb64", fail_unb64)
    monkeypatch.setattr(command_gate_module, "verify_with_public_key_b64", fail_verify)

    with pytest.raises(ValueError, match="revocation signed material is too large"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.fallback_events == []
    assert gate.audit_log.events[-1].payload["reason_code"] == (
        "REVOCATION_SIGNED_MATERIAL_TOO_LARGE"
    )


def test_oversized_revocation_signed_field_rejects_before_canonical_json(monkeypatch):
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
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            capability=lease.capability,
        )
    ).model_copy(update={"reason_code": "X" * 2_000})

    def fail_verify(payload, signature, public_key_b64):
        raise AssertionError("verify should not run for over-budget revocation material")

    def fail_canonical_json(payload):
        raise AssertionError("canonical_json should not run for over-budget revocation material")

    monkeypatch.setattr(command_gate_module, "verify_with_public_key_b64", fail_verify)
    monkeypatch.setattr(crypto, "canonical_json", fail_canonical_json)

    with pytest.raises(ValueError, match="revocation signed material is too large"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.fallback_events == []
    assert gate.audit_log.events[-1].payload["reason_code"] == (
        "REVOCATION_SIGNED_MATERIAL_TOO_LARGE"
    )


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
    assert gate.audit_log.events[-1].actor_id == "local_command_gate"
    assert gate.audit_log.events[-1].payload["claimed_revoked_by"] == EDGE_AGENT_ID
    assert "revoked_by" not in gate.audit_log.events[-1].payload


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

    with pytest.raises(ValueError, match="revocation edge_agent_id does not match local edge"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_EDGE_AGENT_MISMATCH"
    assert gate.audit_log.events[-1].payload["revocation_edge_agent_id"] == "edge-agent:rover-002"
    assert gate.audit_log.events[-1].payload["expected_edge_agent_id"] == EDGE_AGENT_ID


def test_nonlocal_lease_edge_revocation_rejects_before_side_effects():
    issuer_key = DemoKeyPair()
    scoped_revoker_key = DemoKeyPair()
    scoped_revoker_id = "agent:fleet-revoker"
    nonlocal_edge_id = "edge-agent:rover-002"
    emitted: list = []
    lease = issue_valid_lease(issuer_key).model_copy(
        update={"edge_agent_id": nonlocal_edge_id, "signature": None}
    )
    lease = resign(lease, issuer_key)
    gate = CommandGate(
        issuer_key.public_key_b64,
        local_edge_agent_id=EDGE_AGENT_ID,
        trusted_issuer_ids={TRUSTED_ISSUER_ID},
        trusted_revoker_ids={scoped_revoker_id},
        accepted_capabilities={Capability.REMOTE_ASSIST.value},
        **gate_policy_kwargs(),
        issuer_capability_scopes={TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
        capability_constraint_requirements=remote_assist_constraint_requirements(),
        capability_constraint_bounds=remote_assist_constraint_bounds(),
        agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        revoker_public_keys_by_id={scoped_revoker_id: scoped_revoker_key.public_key_b64},
        revoker_edge_scopes_by_id={scoped_revoker_id: {nonlocal_edge_id}},
        state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        command_replay_cache=durable_command_replay_cache(),
        revocation_store=durable_revocation_store(),
        fallback_sink=emitted.append,
    )
    revocation = sign_revocation(
        LeaseRevocation(
            lease_id=lease.lease_id,
            revoked_by=scoped_revoker_id,
            edge_agent_id=nonlocal_edge_id,
            reason_code="COMPROMISE_SUSPECTED",
            fallback_action=FallbackAction.HOLD_POSITION,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            capability=lease.capability,
        ),
        scoped_revoker_key,
    )

    with pytest.raises(ValueError, match="revocation edge_agent_id does not match local edge"):
        gate.revoke(revocation, lease=lease)

    assert gate.revoked_lease_ids == set()
    assert gate.fallback_events == []
    assert emitted == []
    assert gate.audit_log.events[-1].payload["reason_code"] == "REVOCATION_EDGE_AGENT_MISMATCH"
    assert gate.audit_log.events[-1].payload["lease_edge_agent_id"] == nonlocal_edge_id


def test_cross_edge_trusted_revoker_cannot_revoke_victim_lease():
    issuer_key = DemoKeyPair()
    revoker_b_key = DemoKeyPair()
    revoker_b_id = "edge-agent:revoker-b"
    lease = issue_valid_lease(issuer_key)
    gate = CommandGate(
        issuer_key.public_key_b64,
        local_edge_agent_id=EDGE_AGENT_ID,
        trusted_issuer_ids={TRUSTED_ISSUER_ID},
        trusted_revoker_ids={EDGE_AGENT_ID, revoker_b_id},
        accepted_capabilities={Capability.REMOTE_ASSIST.value},
        **gate_policy_kwargs(),
        issuer_capability_scopes={TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
        capability_constraint_requirements=remote_assist_constraint_requirements(),
        capability_constraint_bounds=remote_assist_constraint_bounds(),
        agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        revoker_public_keys_by_id={
            EDGE_AGENT_ID: EDGE_KEY.public_key_b64,
            revoker_b_id: revoker_b_key.public_key_b64,
        },
        state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        command_replay_cache=durable_command_replay_cache(),
        revocation_store=durable_revocation_store(),
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
        local_edge_agent_id=EDGE_AGENT_ID,
        trusted_issuer_ids={TRUSTED_ISSUER_ID},
        trusted_revoker_ids={scoped_revoker_id},
        accepted_capabilities={Capability.REMOTE_ASSIST.value},
        **gate_policy_kwargs(),
        issuer_capability_scopes={TRUSTED_ISSUER_ID: {Capability.REMOTE_ASSIST.value}},
        capability_constraint_requirements=remote_assist_constraint_requirements(),
        capability_constraint_bounds=remote_assist_constraint_bounds(),
        agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        revoker_public_keys_by_id={scoped_revoker_id: scoped_revoker_key.public_key_b64},
        revoker_edge_scopes_by_id={scoped_revoker_id: {EDGE_AGENT_ID}},
        state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        command_replay_cache=durable_command_replay_cache(),
        revocation_store=durable_revocation_store(),
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
    assert result.fallback_action is None
    assert result.fallback_declaration is None


def test_lease_issuer_identity_must_match_verification_key():
    low_key = DemoKeyPair()
    privileged_key = DemoKeyPair()
    policy = make_policy()
    request = make_request()
    _, _, _, constraints = evaluate_inputs(request, make_state(), policy)
    assert constraints is not None
    forged_privileged_lease = issue_lease(
        request,
        constraints,
        "issuer:privileged",
        low_key,
        ttl_seconds=600,
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )
    gate = CommandGate(
        low_key.public_key_b64,
        local_edge_agent_id=EDGE_AGENT_ID,
        trusted_issuer_ids={"issuer:low", "issuer:privileged"},
        issuer_public_keys_by_id={
            "issuer:low": low_key.public_key_b64,
            "issuer:privileged": privileged_key.public_key_b64,
        },
        trusted_revoker_ids={EDGE_AGENT_ID},
        accepted_capabilities={Capability.REMOTE_ASSIST.value},
        **gate_policy_kwargs(),
        issuer_capability_scopes={
            "issuer:low": {Capability.REMOTE_ASSIST.value},
            "issuer:privileged": {Capability.REMOTE_ASSIST.value},
        },
        capability_constraint_requirements=remote_assist_constraint_requirements(),
        capability_constraint_bounds=remote_assist_constraint_bounds(),
        agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
        revoker_public_keys_by_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        state_public_keys_by_edge_id={EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        command_replay_cache=durable_command_replay_cache(),
        revocation_store=durable_revocation_store(),
    )

    result = gate.evaluate(make_command(), forged_privileged_lease, current_state=make_state())

    assert result.allowed is False
    assert result.reason_code == "INVALID_SIGNATURE"


def test_multiple_trusted_issuers_require_key_registry():
    key = DemoKeyPair()

    with pytest.raises(ValueError, match="issuer_public_keys_by_id is required"):
        CommandGate(
            key.public_key_b64,
            local_edge_agent_id=EDGE_AGENT_ID,
            trusted_issuer_ids={"issuer:low", "issuer:privileged"},
            trusted_revoker_ids={EDGE_AGENT_ID},
            accepted_capabilities={Capability.REMOTE_ASSIST.value},
            **gate_policy_kwargs(),
            issuer_capability_scopes={
                "issuer:low": {Capability.REMOTE_ASSIST.value},
                "issuer:privileged": {Capability.REMOTE_ASSIST.value},
            },
            capability_constraint_requirements=remote_assist_constraint_requirements(),
            capability_constraint_bounds=remote_assist_constraint_bounds(),
            agent_public_keys_by_id={CENTRAL_AGENT_ID: CENTRAL_KEY.public_key_b64},
            command_replay_cache=durable_command_replay_cache(),
            revocation_store=durable_revocation_store(),
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
