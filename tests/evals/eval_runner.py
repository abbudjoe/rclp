#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from rclp_core.audit import AuditLog
from rclp_core.crypto import DemoKeyPair
from rclp_core.models import (
    AuditCommit,
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
    NetworkState,
    RobotStateAssertion,
    SafetyState,
    SUPPORTED_PROTOCOL_VERSION,
)
from rclp_core.network import profile
from rclp_core.policy import (
    Policy,
    RequestReplayCache,
    evaluate_policy,
    policy_constraint_bounds,
    policy_digest,
)
from rclp_ros2.command_gate import Command, CommandGate, CommandReplayCache, RevocationStore


DEFAULT_NOW_UNIX_MS = 1_760_000_000_000
CENTRAL_AGENT_ID = "fleet-agent:v0.1"
EDGE_AGENT_ID = "edge-agent:rover-001"
ROBOT_ID = "rover-001"
MISSION_ID = "mission-001"
CAPABILITY = Capability.REMOTE_ASSIST
GEOFENCE_ID = "test-zone-a"
ISSUER_ID = "rclp-demo-issuer"
POLICY_PATH = REPO_ROOT / "examples/policies/remote_assist_policy.yaml"
EXPECTED_DECISIONS = {"allow", "deny", "degrade"}
_EVAL_STORE_DIRS: list[TemporaryDirectory[str]] = []
REQUIRED_SCENARIO_NAMES = {
    "valid_remote_assist",
    "no_lease_denied",
    "expired_lease_denied",
    "not_yet_valid_denied",
    "revoked_lease_denied",
    "replay_nonce_denied",
    "wrong_central_agent_denied",
    "wrong_edge_agent_denied",
    "wrong_robot_denied",
    "wrong_mission_denied",
    "capability_not_granted_denied",
    "unknown_alg_denied",
    "malformed_signature_denied",
    "malformed_input_denied",
    "geofence_violation_denied",
    "high_latency_degraded_or_denied",
    "high_packet_loss_degraded_or_denied",
    "cloud_partition_no_new_authority",
    "stale_command_after_expiry_denied",
    "conflicting_state_denied",
    "audit_allow_complete",
    "audit_deny_complete",
    "scenario_network_degrade_revokes",
    "scenario_cloud_partition_expiry",
    "missing_current_state_denied",
    "stale_current_state_denied",
    "unsigned_state_policy_denied",
    "stale_state_policy_denied",
    "max_speed_too_high_denied",
    "unsigned_revocation_denied",
    "unsigned_current_state_denied",
    "conflicting_speed_alias_denied",
    "nonfinite_speed_denied",
}


def eval_store_path(filename: str) -> Path:
    tempdir = TemporaryDirectory(prefix="rclp-eval-stores-")
    _EVAL_STORE_DIRS.append(tempdir)
    return Path(tempdir.name) / filename


@dataclass
class EvalOutcome:
    decision: str
    reason_code: str
    audit_events: list[AuditCommit] = field(default_factory=list)
    audit_view: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class EvalCaseResult:
    name: str
    kind: str
    passed: bool
    expected_decision: str | None
    actual_decision: str | None
    expected_reason_code: str | None
    actual_reason_code: str | None
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    audit_event_types: list[str] = field(default_factory=list)
    missing_audit_fields: list[str] = field(default_factory=list)

    def to_report(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "status": "passed" if self.passed else "failed",
            "expected_decision": self.expected_decision,
            "actual_decision": self.actual_decision,
            "expected_reason_code": self.expected_reason_code,
            "actual_reason_code": self.actual_reason_code,
            "audit_event_types": self.audit_event_types,
            "missing_audit_fields": self.missing_audit_fields,
            "errors": self.errors,
            "notes": self.notes,
        }


def scenario_dir() -> Path:
    return Path(__file__).resolve().parent / "scenarios"


def default_report_path() -> Path:
    return Path(__file__).resolve().parent / "reports" / "latest.json"


def datetime_from_unix_ms(value: int | float | None) -> datetime:
    unix_ms = DEFAULT_NOW_UNIX_MS if value is None else value
    return datetime.fromtimestamp(unix_ms / 1000, tz=timezone.utc)


def unix_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    return [
        yaml.safe_load(scenario_path.read_text()) for scenario_path in sorted(path.glob("*.yaml"))
    ]


def validate_scenario_registry(scenarios: list[dict[str, Any]]) -> list[EvalCaseResult]:
    failures: list[EvalCaseResult] = []
    names: list[str] = []
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            failures.append(registry_failure(f"scenario at index {index} is not a YAML mapping"))
            continue
        name = scenario.get("name")
        if isinstance(name, str):
            names.append(name)
        else:
            failures.append(registry_failure(f"scenario at index {index} is missing name"))

    if not scenarios:
        failures.append(registry_failure("no eval scenarios discovered"))

    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    for name in duplicate_names:
        failures.append(registry_failure(f"duplicate eval scenario name: {name}"))

    present_names = set(names)
    for name in sorted(REQUIRED_SCENARIO_NAMES - present_names):
        failures.append(registry_failure(f"missing required eval scenario: {name}"))
    return failures


def registry_failure(message: str) -> EvalCaseResult:
    return EvalCaseResult(
        name="scenario_registry",
        kind="registry",
        passed=False,
        expected_decision=None,
        actual_decision=None,
        expected_reason_code=None,
        actual_reason_code=None,
        errors=[message],
    )


def sign_request(request: CapabilityRequest, key: DemoKeyPair) -> CapabilityRequest:
    request.authenticated_agent_id = request.requesting_agent_id
    request.signature = None
    request.signature = key.sign(request)
    return request


def sign_state(state: RobotStateAssertion, key: DemoKeyPair) -> RobotStateAssertion:
    state.authenticated_edge_agent_id = state.edge_agent_id
    state.signature = None
    state.signature = key.sign(state)
    return state


def sign_revocation(revocation: LeaseRevocation, key: DemoKeyPair) -> LeaseRevocation:
    revocation.signature = None
    revocation.signature = key.sign(revocation)
    return revocation


def make_policy(scenario_input: dict[str, Any] | None = None) -> Policy:
    policy = Policy.from_yaml(POLICY_PATH)
    policy_spec = (scenario_input or {}).get("policy", {})
    requirements_spec = policy_spec.get("requirements", {})
    if "max_speed_mps" in requirements_spec:
        policy = policy.model_copy(deep=True)
        policy.requirements.max_speed_mps = requirements_spec["max_speed_mps"]
    return policy


def make_request(
    scenario_input: dict[str, Any],
    *,
    now: datetime,
    central_key: DemoKeyPair,
) -> CapabilityRequest:
    request_spec = scenario_input.get("request", {})
    capability = Capability(request_spec.get("capability", CAPABILITY.value))
    request = CapabilityRequest(
        message_id=request_spec.get("message_id", "msg_eval_request"),
        correlation_id=request_spec.get("correlation_id", "corr_eval"),
        created_at=now + timedelta(milliseconds=request_spec.get("created_at_offset_ms", -1000)),
        requesting_agent_id=request_spec.get("central_agent_id", CENTRAL_AGENT_ID),
        authenticated_agent_id=request_spec.get("authenticated_agent_id"),
        edge_agent_id=request_spec.get("edge_agent_id", EDGE_AGENT_ID),
        robot_id=request_spec.get("robot_id", ROBOT_ID),
        mission_id=request_spec.get("mission_id", MISSION_ID),
        capability=capability,
        reason=request_spec.get("reason", "protocol eval"),
        requested_duration_seconds=request_spec.get("requested_duration_seconds", 600),
        request_nonce=request_spec.get("request_nonce", "nonce_eval"),
    )
    signature_mode = request_spec.get("signature", "valid")
    if signature_mode == "valid":
        return sign_request(request, central_key)
    if signature_mode == "missing":
        request.authenticated_agent_id = request.requesting_agent_id
        request.signature = None
        return request
    if signature_mode == "malformed":
        request.authenticated_agent_id = request.requesting_agent_id
        request.signature = "not-a-valid-signature"
        return request
    raise ValueError(f"unknown request signature mode: {signature_mode}")


def make_state(
    scenario_input: dict[str, Any],
    *,
    now: datetime,
    edge_key: DemoKeyPair,
    default_network_profile: str = "normal",
) -> RobotStateAssertion:
    context = scenario_input.get("local_context", {})
    state_observed_at = now + timedelta(milliseconds=context.get("observed_at_offset_ms", 0))
    state_created_at = now + timedelta(milliseconds=context.get("created_at_offset_ms", 0))
    network_spec = context.get("network", {})
    network_profile = network_spec.get("profile", default_network_profile)
    network = profile(network_profile)
    network_updates = {
        key: value
        for key, value in network_spec.items()
        if key in {"attached", "latency_ms_p95", "packet_loss_pct", "uplink_mbps"}
    }
    if network_updates:
        network = network.model_copy(update=network_updates)
    network_observed_at = now + timedelta(
        milliseconds=network_spec.get(
            "observed_at_offset_ms", context.get("observed_at_offset_ms", 0)
        )
    )
    network = network.model_copy(update={"observed_at": network_observed_at})

    geofence_spec = context.get("geofence", {})
    geofence_verified_at = now + timedelta(
        milliseconds=geofence_spec.get(
            "verified_at_offset_ms",
            context.get("observed_at_offset_ms", 0),
        )
    )
    geofence = GeofenceState(
        geofence_id=geofence_spec.get("geofence_id", GEOFENCE_ID),
        inside=geofence_spec.get("inside", True),
        verified_at=geofence_verified_at,
    )
    state = RobotStateAssertion(
        message_id=context.get("state_message_id", "msg_eval_state"),
        correlation_id=context.get("correlation_id", "corr_eval"),
        created_at=state_created_at,
        robot_id=context.get("robot_id", ROBOT_ID),
        edge_agent_id=context.get("edge_agent_id", EDGE_AGENT_ID),
        authenticated_edge_agent_id=context.get(
            "authenticated_edge_agent_id",
            context.get("edge_agent_id", EDGE_AGENT_ID),
        ),
        mission_id=context.get("mission_id", MISSION_ID),
        safety_state=SafetyState(context.get("safety_state", SafetyState.NOMINAL.value)),
        network_state=NetworkState.model_validate(network.model_dump(mode="python")),
        geofence_state=geofence,
        observed_at=state_observed_at,
        human_operator_available=context.get("human_operator_available", True),
    )
    signature_mode = context.get("signature", "valid")
    if signature_mode == "valid":
        return sign_state(state, edge_key)
    if signature_mode == "missing":
        state.signature = None
        return state
    if signature_mode == "malformed":
        state.signature = "not-a-valid-signature"
        return state
    raise ValueError(f"unknown state signature mode: {signature_mode}")


def make_constraints(
    policy: Policy, constraints_spec: dict[str, Any] | str | None
) -> LeaseConstraints:
    if constraints_spec == "missing":
        return LeaseConstraints()
    constraints_data = constraints_spec if isinstance(constraints_spec, dict) else {}
    return LeaseConstraints(
        geofence_id=constraints_data.get("geofence_id", GEOFENCE_ID),
        max_latency_ms_p95=constraints_data.get(
            "max_latency_ms_p95",
            policy.requirements.network.max_latency_ms_p95,
        ),
        max_packet_loss_pct=constraints_data.get(
            "max_packet_loss_pct",
            policy.requirements.network.max_packet_loss_pct,
        ),
        min_uplink_mbps=constraints_data.get(
            "min_uplink_mbps",
            policy.requirements.network.min_uplink_mbps,
        ),
        fallback_on_degrade=FallbackAction(
            constraints_data.get("fallback_on_degrade", policy.fallback.on_network_degrade.value)
        ),
        max_speed_mps=constraints_data.get("max_speed_mps"),
    )


def make_lease(
    scenario_input: dict[str, Any],
    *,
    now: datetime,
    request: CapabilityRequest,
    issuer_key: DemoKeyPair,
    policy: Policy,
) -> CapabilityLease | None:
    lease_spec = scenario_input.get("lease", {})
    if lease_spec.get("present", True) is False:
        return None

    validity = lease_spec.get("validity", "valid")
    if validity == "valid":
        issued_at = now - timedelta(seconds=60)
        expires_at = now + timedelta(seconds=540)
    elif validity == "expired":
        issued_at = now - timedelta(seconds=120)
        expires_at = now - timedelta(seconds=1)
    elif validity == "not_yet_valid":
        issued_at = now + timedelta(seconds=60)
        expires_at = now + timedelta(seconds=660)
    elif validity == "short_valid":
        issued_at = now - timedelta(seconds=1)
        expires_at = now + timedelta(seconds=60)
    else:
        raise ValueError(f"unknown lease validity: {validity}")

    lease = CapabilityLease(
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        message_id=f"msg_{lease_spec.get('lease_id', 'lease_eval')}",
        correlation_id=request.correlation_id,
        created_at=now,
        message_type="capability_lease",
        lease_id=lease_spec.get("lease_id", "lease_eval"),
        issuer_id=lease_spec.get("issuer_id", ISSUER_ID),
        agent_id=lease_spec.get("central_agent_id", request.requesting_agent_id),
        edge_agent_id=lease_spec.get("edge_agent_id", request.edge_agent_id),
        robot_id=lease_spec.get("robot_id", request.robot_id),
        mission_id=lease_spec.get("mission_id", request.mission_id),
        capability=Capability(lease_spec.get("capability", request.capability.value)),
        constraints=make_constraints(policy, lease_spec.get("constraints")),
        issued_at=issued_at,
        expires_at=expires_at,
        nonce=lease_spec.get("nonce", "lease_nonce_eval"),
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )
    signature_mode = lease_spec.get("signature", "valid")
    if signature_mode == "valid":
        lease.signature = issuer_key.sign(lease)
    elif signature_mode == "malformed":
        lease.signature = "not-a-valid-signature"
    elif signature_mode == "unknown_algorithm":
        lease.signature = "RCLP-UNKNOWN:not-a-valid-signature"
    elif signature_mode == "missing":
        lease.signature = None
    else:
        raise ValueError(f"unknown lease signature mode: {signature_mode}")
    return lease


def sign_command(command: Command, key: DemoKeyPair) -> Command:
    command.authenticated_agent_id = command.agent_id
    command.signature = None
    command.signature = key.sign(command)
    return command


def make_command(
    scenario_input: dict[str, Any],
    *,
    now: datetime,
    central_key: DemoKeyPair,
) -> Command:
    command_spec = scenario_input.get("command", {})
    command = Command(
        correlation_id=command_spec.get("correlation_id", "corr_eval"),
        command_id=command_spec.get("command_id", "cmd_eval"),
        created_at=command_spec.get("created_at", now),
        agent_id=command_spec.get("central_agent_id", CENTRAL_AGENT_ID),
        edge_agent_id=command_spec.get("edge_agent_id", EDGE_AGENT_ID),
        robot_id=command_spec.get("robot_id", ROBOT_ID),
        mission_id=command_spec.get("mission_id", MISSION_ID),
        capability=command_spec.get("capability", CAPABILITY.value),
        payload=command_spec.get("payload", {}),
    )
    return sign_command(command, central_key)


def make_gate(
    issuer_key: DemoKeyPair,
    edge_key: DemoKeyPair,
    audit_log: AuditLog,
    central_key: DemoKeyPair,
    policy: Policy | None = None,
) -> CommandGate:
    policy = policy or make_policy()
    return CommandGate(
        issuer_key.public_key_b64,
        local_edge_agent_id=EDGE_AGENT_ID,
        trusted_issuer_ids={ISSUER_ID},
        trusted_revoker_ids={EDGE_AGENT_ID},
        accepted_capabilities={CAPABILITY.value},
        accepted_policy_id=policy.policy_id,
        accepted_policy_digests={policy_digest(policy)},
        issuer_capability_scopes={ISSUER_ID: {CAPABILITY.value}},
        capability_constraint_requirements={
            CAPABILITY.value: CapabilityConstraintRequirement(
                capability=CAPABILITY,
                require_geofence_id=True,
                require_network_thresholds=True,
                require_fallback_on_degrade=True,
            )
        },
        capability_constraint_bounds=policy_constraint_bounds(policy),
        agent_public_keys_by_id={CENTRAL_AGENT_ID: central_key.public_key_b64},
        revoker_public_keys_by_id={EDGE_AGENT_ID: edge_key.public_key_b64},
        state_public_keys_by_edge_id={EDGE_AGENT_ID: edge_key.public_key_b64},
        command_replay_cache=CommandReplayCache(eval_store_path("command_replay.sqlite3")),
        revocation_store=RevocationStore(eval_store_path("revocations.sqlite3")),
        audit_log=audit_log,
    )


def trusted_policy_kwargs(
    policy: Policy,
    central_key: DemoKeyPair,
    edge_key: DemoKeyPair,
    replay_cache: RequestReplayCache,
) -> dict[str, Any]:
    return {
        "agent_public_keys_by_id": {CENTRAL_AGENT_ID: central_key.public_key_b64},
        "edge_public_keys_by_id": {EDGE_AGENT_ID: edge_key.public_key_b64},
        "accepted_policy_digests": {policy_digest(policy)},
        "replay_cache": replay_cache,
    }


def run_policy_decision(scenario: dict[str, Any]) -> EvalOutcome:
    now = datetime_from_unix_ms(scenario.get("now_unix_ms"))
    scenario_input = scenario.get("input", {})
    central_key = DemoKeyPair()
    edge_key = DemoKeyPair()
    policy = make_policy(scenario_input)
    log = AuditLog()
    request = make_request(scenario_input, now=now, central_key=central_key)
    state = make_state(scenario_input, now=now, edge_key=edge_key)
    replay_cache = RequestReplayCache(eval_store_path("request_replay.sqlite3"))
    for nonce in scenario_input.get("seen_request_nonces", []):
        replay_cache.remember(
            make_request(
                {"request": {"request_nonce": nonce}},
                now=now,
                central_key=central_key,
            )
        )

    decision, reason, _, _, event = evaluate_policy(
        request,
        state,
        policy,
        audit_log=log,
        deciding_actor_id=ISSUER_ID,
        now=now,
        **trusted_policy_kwargs(policy, central_key, edge_key, replay_cache),
    )
    return EvalOutcome(
        decision=decision.value,
        reason_code=reason,
        audit_events=log.events,
        audit_view=audit_view(event, log.events),
    )


def run_command_gate(scenario: dict[str, Any]) -> EvalOutcome:
    now = datetime_from_unix_ms(scenario.get("now_unix_ms"))
    scenario_input = scenario.get("input", {})
    central_key = DemoKeyPair()
    edge_key = DemoKeyPair()
    issuer_key = DemoKeyPair()
    policy = make_policy(scenario_input)
    log = AuditLog()
    request = make_request(scenario_input, now=now, central_key=central_key)
    lease = make_lease(
        scenario_input,
        now=now,
        request=request,
        issuer_key=issuer_key,
        policy=policy,
    )
    command = make_command(scenario_input, now=now, central_key=central_key)
    gate = make_gate(issuer_key, edge_key, log, central_key, policy=policy)

    if lease is not None and scenario_input.get("revocation", {}).get("present", False):
        revocation_spec = scenario_input.get("revocation", {})
        revocation = LeaseRevocation(
            message_id=revocation_spec.get("message_id", "msg_eval_revocation"),
            correlation_id=revocation_spec.get("correlation_id", "corr_eval"),
            created_at=now,
            lease_id=lease.lease_id,
            revoked_by=revocation_spec.get("revoked_by", EDGE_AGENT_ID),
            edge_agent_id=revocation_spec.get("edge_agent_id", lease.edge_agent_id),
            reason_code=revocation_spec.get("reason_code", "NETWORK_PROFILE_REVOKE"),
            revoked_at=now,
            fallback_action=FallbackAction(
                revocation_spec.get("fallback_action", FallbackAction.HOLD_POSITION.value)
            ),
            robot_id=revocation_spec.get("robot_id", lease.robot_id),
            mission_id=revocation_spec.get("mission_id", lease.mission_id),
            capability=Capability(revocation_spec.get("capability", lease.capability.value)),
        )
        signature_mode = revocation_spec.get("signature", "valid")
        if signature_mode == "valid":
            sign_revocation(revocation, edge_key)
        elif signature_mode == "malformed":
            sign_revocation(revocation, edge_key)
            revocation.reason_code = "TAMPERED_AFTER_SIGNING"
        elif signature_mode == "missing":
            revocation.signature = None
        else:
            raise ValueError(f"unknown revocation signature mode: {signature_mode}")
        try:
            gate.revoke(revocation, lease=lease, now=now)
        except ValueError:
            rejected_event = log.events[-1] if log.events else None
            return EvalOutcome(
                decision="deny",
                reason_code=(
                    rejected_event.payload.get("reason_code")
                    if rejected_event is not None
                    else "REVOCATION_REJECTED"
                ),
                audit_events=log.events,
                audit_view=audit_view(rejected_event, log.events),
            )

    state = None
    if scenario_input.get("include_current_state", False):
        state = make_state(scenario_input, now=now, edge_key=edge_key)
    result = gate.evaluate(command, lease, current_state=state, now=now)
    primary_event = find_event(log.events, result.audit_id)
    return EvalOutcome(
        decision="allow" if result.allowed else "deny",
        reason_code=result.reason_code,
        audit_events=log.events,
        audit_view=audit_view(primary_event, log.events),
    )


def run_malformed_input(scenario: dict[str, Any]) -> EvalOutcome:
    raw_request = scenario.get("input", {}).get("raw_request", {})
    try:
        CapabilityRequest.model_validate(raw_request)
    except ValidationError:
        return EvalOutcome(
            decision="deny",
            reason_code="MALFORMED_INPUT",
            notes=["Malformed input was rejected during schema validation."],
        )
    return EvalOutcome(
        decision="allow",
        reason_code="MALFORMED_INPUT_NOT_DETECTED",
        notes=["Malformed-input scenario unexpectedly validated."],
    )


def run_network_degrade_revokes(scenario: dict[str, Any]) -> EvalOutcome:
    now = datetime_from_unix_ms(scenario.get("now_unix_ms"))
    central_key = DemoKeyPair()
    edge_key = DemoKeyPair()
    issuer_key = DemoKeyPair()
    policy = make_policy()
    log = AuditLog()
    replay_cache = RequestReplayCache(eval_store_path("request_replay.sqlite3"))
    request = make_request(scenario.get("input", {}), now=now, central_key=central_key)
    gate = make_gate(issuer_key, edge_key, log, central_key)

    log.record(
        event_type=AuditEventType.CAPABILITY_REQUESTED,
        actor_id=request.requesting_agent_id,
        robot_id=request.robot_id,
        mission_id=request.mission_id,
        correlation_id=request.correlation_id,
        summary="eval central agent requested remote_assist",
        payload=request.model_dump(mode="json"),
        related_message_ids=[request.message_id],
    )
    normal_state = make_state(
        {"local_context": {"network": {"profile": "normal"}}},
        now=now,
        edge_key=edge_key,
    )
    log.record(
        event_type=AuditEventType.NETWORK_STATE_ASSERTED,
        actor_id=EDGE_AGENT_ID,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        correlation_id=request.correlation_id,
        summary="eval normal network state observed",
        payload=normal_state.model_dump(mode="json"),
        related_message_ids=[normal_state.message_id],
    )
    decision, _, _, constraints, _ = evaluate_policy(
        request,
        normal_state,
        policy,
        audit_log=log,
        deciding_actor_id=ISSUER_ID,
        now=now,
        **trusted_policy_kwargs(policy, central_key, edge_key, replay_cache),
    )
    if decision != Decision.ALLOW or constraints is None:
        raise ValueError("network degradation scenario could not establish initial lease")
    lease = CapabilityLease(
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        message_id="msg_lease_eval_network_degrade",
        correlation_id=request.correlation_id,
        created_at=now,
        message_type="capability_lease",
        lease_id="lease_eval_network_degrade",
        issuer_id=ISSUER_ID,
        agent_id=request.requesting_agent_id,
        edge_agent_id=request.edge_agent_id,
        robot_id=request.robot_id,
        mission_id=request.mission_id,
        capability=request.capability,
        constraints=constraints,
        issued_at=now - timedelta(seconds=60),
        expires_at=now + timedelta(seconds=540),
        nonce="lease_nonce_eval_network_degrade",
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )
    lease.signature = issuer_key.sign(lease)
    gate.evaluate(
        make_command(
            {"command": {"command_id": "cmd_eval_initial"}},
            now=now,
            central_key=central_key,
        ),
        lease,
        current_state=normal_state,
        now=now,
    )

    degraded_state = make_state(
        {"local_context": {"network": {"profile": "degraded_teleop"}}},
        now=now + timedelta(seconds=5),
        edge_key=edge_key,
    )
    log.record(
        event_type=AuditEventType.NETWORK_STATE_ASSERTED,
        actor_id=EDGE_AGENT_ID,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        correlation_id=request.correlation_id,
        summary="eval degraded network state observed",
        payload=degraded_state.model_dump(mode="json"),
        related_message_ids=[degraded_state.message_id],
    )
    degraded_request = make_request(
        {
            "request": {
                "message_id": "msg_eval_degraded_request",
                "correlation_id": request.correlation_id,
                "request_nonce": "nonce_eval_degraded_request",
            }
        },
        now=now + timedelta(seconds=5),
        central_key=central_key,
    )
    log.record(
        event_type=AuditEventType.CAPABILITY_REQUESTED,
        actor_id=degraded_request.requesting_agent_id,
        robot_id=degraded_request.robot_id,
        mission_id=degraded_request.mission_id,
        correlation_id=degraded_request.correlation_id,
        summary="eval central agent requested remote_assist after degradation",
        payload=degraded_request.model_dump(mode="json"),
        related_message_ids=[degraded_request.message_id],
    )
    degrade_decision, _, degrade_alternatives, _, _ = evaluate_policy(
        degraded_request,
        degraded_state,
        policy,
        audit_log=log,
        deciding_actor_id=ISSUER_ID,
        now=now + timedelta(seconds=5),
        **trusted_policy_kwargs(policy, central_key, edge_key, replay_cache),
    )
    if degrade_decision not in {Decision.DEGRADE, Decision.DENY}:
        raise ValueError("network degradation scenario did not degrade or deny")
    fallback = (
        degrade_alternatives[0] if degrade_alternatives else FallbackAction.CRAWL_TO_SAFE_ZONE
    )
    revocation = LeaseRevocation(
        message_id="msg_eval_network_revocation",
        correlation_id=request.correlation_id,
        created_at=now + timedelta(seconds=6),
        lease_id=lease.lease_id,
        revoked_by=EDGE_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        reason_code="NETWORK_PROFILE_REVOKE",
        revoked_at=now + timedelta(seconds=6),
        fallback_action=fallback,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        capability=Capability.REMOTE_ASSIST,
    )
    sign_revocation(revocation, edge_key)
    gate.revoke(revocation, lease=lease, now=now + timedelta(seconds=6))
    final_command = make_command(
        {"command": {"command_id": "cmd_eval_after_degrade"}},
        now=now + timedelta(seconds=7),
        central_key=central_key,
    )
    final_result = gate.evaluate(
        final_command,
        lease,
        current_state=degraded_state,
        now=now + timedelta(seconds=7),
    )
    primary_event = find_event(log.events, final_result.audit_id)
    return EvalOutcome(
        decision="allow" if final_result.allowed else "deny",
        reason_code=final_result.reason_code,
        audit_events=log.events,
        audit_view=audit_view(primary_event, log.events),
    )


def run_cloud_partition_expiry(scenario: dict[str, Any]) -> EvalOutcome:
    now = datetime_from_unix_ms(scenario.get("now_unix_ms"))
    central_key = DemoKeyPair()
    edge_key = DemoKeyPair()
    issuer_key = DemoKeyPair()
    policy = make_policy()
    log = AuditLog()
    replay_cache = RequestReplayCache(eval_store_path("request_replay.sqlite3"))
    request = make_request(scenario.get("input", {}), now=now, central_key=central_key)
    gate = make_gate(issuer_key, edge_key, log, central_key)
    log.record(
        event_type=AuditEventType.CAPABILITY_REQUESTED,
        actor_id=request.requesting_agent_id,
        robot_id=request.robot_id,
        mission_id=request.mission_id,
        correlation_id=request.correlation_id,
        summary="eval central agent requested remote_assist before partition",
        payload=request.model_dump(mode="json"),
        related_message_ids=[request.message_id],
    )
    normal_state = make_state(
        {"local_context": {"network": {"profile": "normal"}}},
        now=now,
        edge_key=edge_key,
    )
    log.record(
        event_type=AuditEventType.NETWORK_STATE_ASSERTED,
        actor_id=EDGE_AGENT_ID,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        correlation_id=request.correlation_id,
        summary="eval normal network state observed before partition",
        payload=normal_state.model_dump(mode="json"),
        related_message_ids=[normal_state.message_id],
    )
    decision, _, _, constraints, _ = evaluate_policy(
        request,
        normal_state,
        policy,
        audit_log=log,
        deciding_actor_id=ISSUER_ID,
        now=now,
        **trusted_policy_kwargs(policy, central_key, edge_key, replay_cache),
    )
    if decision != Decision.ALLOW or constraints is None:
        raise ValueError("cloud partition scenario could not establish initial lease")

    lease = CapabilityLease(
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        message_id="msg_lease_eval_cloud_partition",
        correlation_id=request.correlation_id,
        created_at=now,
        message_type="capability_lease",
        lease_id="lease_eval_cloud_partition",
        issuer_id=ISSUER_ID,
        agent_id=request.requesting_agent_id,
        edge_agent_id=request.edge_agent_id,
        robot_id=request.robot_id,
        mission_id=request.mission_id,
        capability=request.capability,
        constraints=constraints,
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(seconds=60),
        nonce="lease_nonce_eval_cloud_partition",
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
    )
    lease.signature = issuer_key.sign(lease)
    gate.evaluate(
        make_command(
            {"command": {"command_id": "cmd_eval_before_partition"}},
            now=now + timedelta(seconds=30),
            central_key=central_key,
        ),
        lease,
        current_state=normal_state,
        now=now + timedelta(seconds=30),
    )

    partition_state = make_state(
        {"local_context": {"network": {"profile": "partition"}}},
        now=now + timedelta(seconds=31),
        edge_key=edge_key,
    )
    log.record(
        event_type=AuditEventType.NETWORK_STATE_ASSERTED,
        actor_id=EDGE_AGENT_ID,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        correlation_id=request.correlation_id,
        summary="eval cloud/control-plane partition observed",
        payload=partition_state.model_dump(mode="json"),
        related_message_ids=[partition_state.message_id],
    )
    partition_request = make_request(
        {
            "request": {
                "message_id": "msg_eval_partition_request",
                "correlation_id": request.correlation_id,
                "request_nonce": "nonce_eval_partition_request",
            }
        },
        now=now + timedelta(seconds=31),
        central_key=central_key,
    )
    log.record(
        event_type=AuditEventType.CAPABILITY_REQUESTED,
        actor_id=partition_request.requesting_agent_id,
        robot_id=partition_request.robot_id,
        mission_id=partition_request.mission_id,
        correlation_id=partition_request.correlation_id,
        summary="eval central agent requested remote_assist during partition",
        payload=partition_request.model_dump(mode="json"),
        related_message_ids=[partition_request.message_id],
    )
    new_authority_decision, _, _, _, _ = evaluate_policy(
        partition_request,
        partition_state,
        policy,
        audit_log=log,
        deciding_actor_id=ISSUER_ID,
        now=now + timedelta(seconds=31),
        **trusted_policy_kwargs(policy, central_key, edge_key, replay_cache),
    )
    if new_authority_decision != Decision.DENY:
        raise ValueError("partition did not deny new high-risk authority")

    partition_command = make_command(
        {"command": {"command_id": "cmd_eval_partition_before_expiry"}},
        now=now + timedelta(seconds=32),
        central_key=central_key,
    )
    partition_result = gate.evaluate(
        partition_command,
        lease,
        current_state=partition_state,
        now=now + timedelta(seconds=32),
    )
    if partition_result.allowed or partition_result.reason_code != "NETWORK_DETACHED":
        raise ValueError("partitioned pre-expiry command did not fail closed")

    final_command = make_command(
        {"command": {"command_id": "cmd_eval_partition_after_expiry"}},
        now=now + timedelta(seconds=61),
        central_key=central_key,
    )
    final_result = gate.evaluate(
        final_command,
        lease,
        current_state=partition_state,
        now=now + timedelta(seconds=61),
    )
    primary_event = find_event(log.events, final_result.audit_id)
    return EvalOutcome(
        decision="allow" if final_result.allowed else "deny",
        reason_code=final_result.reason_code,
        audit_events=log.events,
        audit_view=audit_view(primary_event, log.events),
        notes=[
            "Cloud connectivity is represented by deterministic partition state; "
            "the MVP has no separate cloud_connected protocol field.",
            "The MVP command gate denies partitioned remote_assist commands before expiry "
            "because the current local network state violates lease constraints.",
        ],
    )


RUNNERS = {
    "policy_decision": run_policy_decision,
    "command_gate": run_command_gate,
    "malformed_input": run_malformed_input,
    "network_degrade_revokes": run_network_degrade_revokes,
    "cloud_partition_expiry": run_cloud_partition_expiry,
}


def find_event(events: list[AuditCommit], audit_id: str | None) -> AuditCommit | None:
    for event in events:
        if event.audit_id == audit_id:
            return event
    return None


def audit_view(event: AuditCommit | None, events: list[AuditCommit]) -> dict[str, Any]:
    if event is None:
        return {}

    payloads = audited_payloads(event, events)
    return {
        "event_id": event.audit_id,
        "audit_id": event.audit_id,
        "timestamp": event.created_at.isoformat(),
        "timestamp_unix_ms": unix_ms(event.created_at),
        "decision": first_nonempty(payloads, "decision")
        or decision_from_event_type(event.event_type),
        "reason_code": first_nonempty(payloads, "reason_code", "trigger"),
        "central_agent_id": first_nonempty(
            payloads,
            "central_agent_id",
            "requesting_agent_id",
            "agent_id",
        ),
        "edge_agent_id": first_nonempty(payloads, "edge_agent_id") or event.actor_id,
        "robot_id": first_nonempty(payloads, "robot_id") or event.robot_id,
        "mission_id": first_nonempty(payloads, "mission_id") or event.mission_id,
        "requested_capability": first_nonempty(
            payloads,
            "requested_capability",
            "capability",
        ),
        "lease_id": first_nonempty(payloads, "lease_id"),
        "network_state": first_nonempty(payloads, "network_state"),
        "geofence_state": first_nonempty(payloads, "geofence_state"),
        "fallback_action": first_nonempty(payloads, "fallback_action"),
    }


def audited_payloads(primary_event: AuditCommit, events: list[AuditCommit]) -> list[dict[str, Any]]:
    ordered_events = [primary_event] + [
        event for event in events if event.audit_id != primary_event.audit_id
    ]
    payloads: list[dict[str, Any]] = []
    for audit_event in ordered_events:
        payloads.append(audit_event.payload)
        current_state = audit_event.payload.get("current_state")
        if isinstance(current_state, dict):
            payloads.append(current_state)
    return payloads


def first_nonempty(payloads: list[dict[str, Any]], *keys: str) -> Any:
    for payload in payloads:
        for key in keys:
            value = payload.get(key)
            if value not in (None, "", []):
                return value
    return None


def decision_from_event_type(event_type: AuditEventType) -> str | None:
    if event_type in {AuditEventType.CAPABILITY_ALLOWED, AuditEventType.COMMAND_ALLOWED}:
        return "allow"
    if event_type in {AuditEventType.CAPABILITY_DEGRADED}:
        return "degrade"
    if event_type in {
        AuditEventType.CAPABILITY_DENIED,
        AuditEventType.COMMAND_REJECTED,
        AuditEventType.REVOCATION_REJECTED,
    }:
        return "deny"
    return None


def evaluate_scenario(scenario: dict[str, Any]) -> EvalCaseResult:
    name = scenario.get("name", "<unnamed>")
    kind = scenario.get("kind", "<missing>")
    expected = scenario.get("expected", {})
    expected_decision = expected.get("decision")
    expected_reason = expected.get("reason_code")
    errors: list[str] = []
    missing_audit_fields: list[str] = []
    outcome: EvalOutcome | None = None

    if expected_decision not in EXPECTED_DECISIONS:
        errors.append(
            "expected.decision must be one of "
            f"{', '.join(sorted(EXPECTED_DECISIONS))}; got {expected_decision!r}"
        )
    if not isinstance(expected_reason, str) or not expected_reason:
        errors.append("expected.reason_code is required")

    try:
        runner = RUNNERS[kind]
        outcome = runner(scenario)
    except KeyError:
        errors.append(f"unknown scenario kind: {kind}")
    except Exception as exc:  # noqa: BLE001 - eval reports should capture all scenario failures.
        errors.append(f"runner exception: {type(exc).__name__}: {exc}")

    if outcome is not None:
        if expected_decision is not None and outcome.decision != expected_decision:
            errors.append(f"expected decision {expected_decision}, got {outcome.decision}")
        if expected_reason is not None and outcome.reason_code != expected_reason:
            errors.append(f"expected reason {expected_reason}, got {outcome.reason_code}")
        for field_name in expected.get("audit_required_fields", []):
            if not outcome.audit_view.get(field_name):
                missing_audit_fields.append(field_name)
        if missing_audit_fields:
            errors.append(f"missing audit fields: {', '.join(missing_audit_fields)}")
        event_types = [str(event.event_type.value) for event in outcome.audit_events]
        for event_type in expected.get("audit_event_types", []):
            if event_type not in event_types:
                errors.append(f"missing audit event type: {event_type}")
    else:
        event_types = []

    return EvalCaseResult(
        name=name,
        kind=kind,
        passed=not errors,
        expected_decision=expected_decision,
        actual_decision=outcome.decision if outcome is not None else None,
        expected_reason_code=expected_reason,
        actual_reason_code=outcome.reason_code if outcome is not None else None,
        errors=errors,
        notes=outcome.notes if outcome is not None else [],
        audit_event_types=event_types,
        missing_audit_fields=missing_audit_fields,
    )


def run_all(scenarios_path: Path, report_path: Path) -> dict[str, Any]:
    scenarios = load_scenarios(scenarios_path)
    case_results = validate_scenario_registry(scenarios)
    case_results.extend(
        evaluate_scenario(scenario) for scenario in scenarios if isinstance(scenario, dict)
    )
    passed = sum(1 for result in case_results if result.passed)
    failed = len(case_results) - passed
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(case_results),
            "passed": passed,
            "failed": failed,
        },
        "results": [result.to_report() for result in case_results],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def print_summary(report: dict[str, Any], report_path: Path) -> None:
    summary = report["summary"]
    print(
        f"RCLP evals: {summary['passed']} passed, "
        f"{summary['failed']} failed, {summary['total']} total"
    )
    for result in report["results"]:
        status = "PASS" if result["status"] == "passed" else "FAIL"
        print(
            f"{status} {result['name']}: {result['actual_decision']} {result['actual_reason_code']}"
        )
        for error in result["errors"]:
            print(f"  - {error}")
        for note in result["notes"]:
            print(f"  note: {note}")
    print(f"Wrote JSON report: {report_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic RCLP adversarial evals.")
    parser.add_argument("--scenarios", type=Path, default=scenario_dir())
    parser.add_argument("--report", type=Path, default=default_report_path())
    args = parser.parse_args(argv)

    report = run_all(args.scenarios, args.report)
    print_summary(report, args.report)
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
