from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from math import isfinite
from numbers import Real
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

import yaml
from pydantic import BaseModel, Field, model_validator

from rclp_core.audit import AuditLog
from rclp_core.crypto import verify_with_public_key_b64
from rclp_core.models import (
    AuditCommit,
    AuditEventType,
    Capability,
    CapabilityRequest,
    Decision,
    FallbackAction,
    LeaseConstraints,
    NetworkProfile,
    RobotStateAssertion,
    protocol_version_violation,
    stable_json_hash,
)
from rclp_core.state import (
    DEFAULT_STATE_MAX_AGE_SECONDS,
    state_auth_violation,
    state_time_violation,
)


DEFAULT_REQUEST_MAX_AGE_SECONDS = 300
REQUEST_CLOCK_SKEW_SECONDS = 30


class RequestReplayCache:
    """Durable replay window for request nonce checks.

    A cache without a store path remains available for local construction and
    pre-auth negative tests, but policy issuance fails closed unless the cache
    is backed by a durable SQLite store.
    """

    def __init__(self, store_path: str | Path | None = None) -> None:
        self._store_path = Path(store_path) if store_path is not None else None
        self._tempdir: TemporaryDirectory[str] | None = None
        self._seen_request_nonces: set[tuple[str, str]] = set()
        if self._store_path is not None:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS request_replay_nonces (
                        requesting_agent_id TEXT NOT NULL,
                        request_nonce TEXT NOT NULL,
                        request_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        consumed_at TEXT NOT NULL,
                        PRIMARY KEY (requesting_agent_id, request_nonce)
                    )
                    """
                )

    @classmethod
    def temporary(cls) -> "RequestReplayCache":
        tempdir = TemporaryDirectory(prefix="rclp-request-replay-")
        cache = cls(Path(tempdir.name) / "request_replay.sqlite3")
        cache._tempdir = tempdir
        return cache

    @property
    def durable(self) -> bool:
        return self._store_path is not None

    @property
    def store_path(self) -> Path | None:
        return self._store_path

    def _connect(self) -> sqlite3.Connection:
        if self._store_path is None:
            raise ValueError("request replay cache has no durable store")
        return sqlite3.connect(self._store_path, timeout=30, isolation_level="IMMEDIATE")

    def has_seen(self, request: CapabilityRequest) -> bool:
        if self._store_path is not None:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT 1
                    FROM request_replay_nonces
                    WHERE requesting_agent_id = ? AND request_nonce = ?
                    """,
                    (request.requesting_agent_id, request.request_nonce),
                ).fetchone()
            return row is not None
        return (request.requesting_agent_id, request.request_nonce) in self._seen_request_nonces

    def consume(self, request: CapabilityRequest, *, consumed_at: datetime) -> bool:
        if self._store_path is None:
            return False
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO request_replay_nonces (
                        requesting_agent_id,
                        request_nonce,
                        request_id,
                        created_at,
                        consumed_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        request.requesting_agent_id,
                        request.request_nonce,
                        request.message_id,
                        request.created_at.isoformat(),
                        consumed_at.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def remember(self, request: CapabilityRequest) -> None:
        if self._store_path is not None:
            self.consume(request, consumed_at=datetime.now(timezone.utc))
            return
        self._seen_request_nonces.add((request.requesting_agent_id, request.request_nonce))


class NetworkRequirements(BaseModel):
    max_latency_ms_p95: float = Field(default=80.0, ge=0, allow_inf_nan=False)
    max_packet_loss_pct: float = Field(default=1.0, ge=0, le=100, allow_inf_nan=False)
    min_uplink_mbps: float = Field(default=3.0, ge=0, allow_inf_nan=False)
    deny_above_latency_ms_p95: float = Field(default=250.0, ge=0, allow_inf_nan=False)
    deny_above_packet_loss_pct: float = Field(
        default=10.0,
        ge=0,
        le=100,
        allow_inf_nan=False,
    )
    deny_below_uplink_mbps: float = Field(default=0.8, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_degrade_window(self) -> "NetworkRequirements":
        if self.deny_above_latency_ms_p95 < self.max_latency_ms_p95:
            raise ValueError("deny latency threshold must be >= degrade latency threshold")
        if self.deny_above_packet_loss_pct < self.max_packet_loss_pct:
            raise ValueError("deny packet-loss threshold must be >= degrade packet-loss threshold")
        if self.deny_below_uplink_mbps > self.min_uplink_mbps:
            raise ValueError("deny uplink threshold must be <= degrade uplink threshold")
        return self


class PolicyRequirements(BaseModel):
    allowed_agents: list[str] = Field(default_factory=list)
    allowed_edge_agents: list[str] = Field(default_factory=list)
    allowed_robots: list[str] = Field(default_factory=list)
    allowed_missions: list[str] = Field(default_factory=list)
    geofence_required: bool = True
    geofence_allowed: bool = True
    human_operator_available: bool = True
    network: NetworkRequirements = Field(default_factory=NetworkRequirements)


class FallbackPolicy(BaseModel):
    on_deny: FallbackAction = FallbackAction.LOCAL_AUTONOMY_ONLY
    on_network_degrade: FallbackAction = FallbackAction.CRAWL_TO_SAFE_ZONE
    on_disconnect: FallbackAction = FallbackAction.LOCAL_AUTONOMY_ONLY
    on_expiry: FallbackAction = FallbackAction.REVOKE_REMOTE_ASSIST


class Policy(BaseModel):
    policy_id: str
    capability: Capability
    lease_ttl_seconds: int = Field(default=600, gt=0)
    requirements: PolicyRequirements = Field(default_factory=PolicyRequirements)
    fallback: FallbackPolicy = Field(default_factory=FallbackPolicy)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Policy":
        return cls.model_validate(yaml.safe_load(Path(path).read_text()))


def _explicit_member(value: str, allowed: list[str]) -> bool:
    return value in allowed


def _request_time_violation(
    request: CapabilityRequest,
    *,
    now: datetime,
    max_age_seconds: int,
) -> str | None:
    if request.created_at.tzinfo is None or request.created_at.utcoffset() is None:
        return "REQUEST_TIMESTAMP_INVALID"
    if request.created_at > now + timedelta(seconds=REQUEST_CLOCK_SKEW_SECONDS):
        return "REQUEST_NOT_YET_VALID"
    if now - request.created_at > timedelta(seconds=max_age_seconds):
        return "REQUEST_STALE"
    return None


def _finite_nonnegative_number(value: object, *, max_value: float | None = None) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    numeric = float(value)
    if not isfinite(numeric) or numeric < 0:
        return False
    return max_value is None or numeric <= max_value


def _network_state_malformed(net) -> bool:
    return not (
        _finite_nonnegative_number(net.latency_ms_p95)
        and _finite_nonnegative_number(net.packet_loss_pct, max_value=100)
        and _finite_nonnegative_number(net.uplink_mbps)
    )


def _network_requirements_malformed(req: NetworkRequirements) -> bool:
    if not (
        _finite_nonnegative_number(req.max_latency_ms_p95)
        and _finite_nonnegative_number(req.max_packet_loss_pct, max_value=100)
        and _finite_nonnegative_number(req.min_uplink_mbps)
        and _finite_nonnegative_number(req.deny_above_latency_ms_p95)
        and _finite_nonnegative_number(req.deny_above_packet_loss_pct, max_value=100)
        and _finite_nonnegative_number(req.deny_below_uplink_mbps)
    ):
        return True
    return (
        req.deny_above_latency_ms_p95 < req.max_latency_ms_p95
        or req.deny_above_packet_loss_pct < req.max_packet_loss_pct
        or req.deny_below_uplink_mbps > req.min_uplink_mbps
    )


def policy_digest(policy: "Policy") -> str:
    return stable_json_hash(policy.model_dump(mode="json"))


def _policy_digest_violation(policy: "Policy", accepted_policy_digests: set[str]) -> str | None:
    if not accepted_policy_digests:
        return "POLICY_DIGEST_REQUIRED"
    if policy_digest(policy) not in accepted_policy_digests:
        return "POLICY_DIGEST_NOT_ACCEPTED"
    return None


def _request_auth_violation(
    request: CapabilityRequest,
    agent_public_keys_by_id: Mapping[str, str],
) -> str | None:
    if request.authenticated_agent_id is None:
        return "REQUEST_AUTHENTICATED_AGENT_MISSING"
    if request.authenticated_agent_id != request.requesting_agent_id:
        return "REQUEST_AUTHENTICATED_AGENT_MISMATCH"
    if request.signature is None:
        return "REQUEST_SIGNATURE_MISSING"
    public_key = agent_public_keys_by_id.get(request.authenticated_agent_id)
    if public_key is None:
        return "AGENT_KEY_NOT_TRUSTED"
    if not verify_with_public_key_b64(request, request.signature, public_key):
        return "REQUEST_SIGNATURE_INVALID"
    return None


def _evaluate_network_requirements(
    req: NetworkRequirements,
    net,
    fallback: FallbackPolicy,
) -> tuple[Decision, str, list[FallbackAction], LeaseConstraints | None] | None:
    if net.profile == NetworkProfile.UNKNOWN:
        return Decision.DENY, "NETWORK_STATE_UNKNOWN", [fallback.on_disconnect], None
    if not net.attached:
        return Decision.DENY, "NETWORK_DETACHED", [fallback.on_disconnect], None
    if net.latency_ms_p95 > req.deny_above_latency_ms_p95:
        return Decision.DENY, "NETWORK_LATENCY_TOO_HIGH", [fallback.on_network_degrade], None
    if net.packet_loss_pct > req.deny_above_packet_loss_pct:
        return (
            Decision.DENY,
            "NETWORK_PACKET_LOSS_TOO_HIGH",
            [fallback.on_network_degrade],
            None,
        )
    if net.uplink_mbps < req.deny_below_uplink_mbps:
        return Decision.DENY, "NETWORK_UPLINK_TOO_LOW", [fallback.on_network_degrade], None

    if net.latency_ms_p95 > req.max_latency_ms_p95:
        return Decision.DEGRADE, "NETWORK_LATENCY_DEGRADED", [fallback.on_network_degrade], None
    if net.packet_loss_pct > req.max_packet_loss_pct:
        return (
            Decision.DEGRADE,
            "NETWORK_PACKET_LOSS_DEGRADED",
            [fallback.on_network_degrade],
            None,
        )
    if net.uplink_mbps < req.min_uplink_mbps:
        return Decision.DEGRADE, "NETWORK_UPLINK_DEGRADED", [fallback.on_network_degrade], None
    return None


def _evaluate_policy_inputs(
    request: CapabilityRequest,
    state: RobotStateAssertion,
    policy: Policy,
    *,
    agent_public_keys_by_id: Mapping[str, str],
    edge_public_keys_by_id: Mapping[str, str],
    accepted_policy_digests: set[str],
    replay_cache: RequestReplayCache,
    now: datetime | None = None,
    max_request_age_seconds: int = DEFAULT_REQUEST_MAX_AGE_SECONDS,
    max_state_age_seconds: int = DEFAULT_STATE_MAX_AGE_SECONDS,
) -> tuple[Decision, str, list[FallbackAction], LeaseConstraints | None]:
    req = policy.requirements
    net = state.network_state
    now = now or datetime.now(timezone.utc)

    if version_reason := protocol_version_violation(request, state):
        return Decision.DENY, version_reason, [policy.fallback.on_deny], None
    if time_reason := _request_time_violation(
        request,
        now=now,
        max_age_seconds=max_request_age_seconds,
    ):
        return Decision.DENY, time_reason, [policy.fallback.on_deny], None

    if auth_reason := _request_auth_violation(request, agent_public_keys_by_id):
        return Decision.DENY, auth_reason, [policy.fallback.on_deny], None
    if replay_cache is None:
        return Decision.DENY, "REQUEST_REPLAY_CACHE_REQUIRED", [policy.fallback.on_deny], None
    if not replay_cache.durable:
        return (
            Decision.DENY,
            "REQUEST_REPLAY_STORE_DURABLE_REQUIRED",
            [policy.fallback.on_deny],
            None,
        )
    if not replay_cache.consume(request, consumed_at=now):
        return Decision.DENY, "REQUEST_REPLAYED", [policy.fallback.on_deny], None

    if digest_reason := _policy_digest_violation(policy, accepted_policy_digests):
        return Decision.DENY, digest_reason, [policy.fallback.on_deny], None
    if request.capability != policy.capability:
        return Decision.DENY, "CAPABILITY_NOT_COVERED_BY_POLICY", [policy.fallback.on_deny], None
    if request.requested_duration_seconds > policy.lease_ttl_seconds:
        return Decision.DENY, "REQUESTED_DURATION_TOO_LONG", [policy.fallback.on_deny], None
    if not _explicit_member(request.requesting_agent_id, req.allowed_agents):
        return Decision.DENY, "AGENT_NOT_ALLOWED", [policy.fallback.on_deny], None
    if not _explicit_member(request.edge_agent_id, req.allowed_edge_agents):
        return Decision.DENY, "EDGE_AGENT_NOT_ALLOWED", [policy.fallback.on_deny], None
    if not _explicit_member(request.robot_id, req.allowed_robots):
        return Decision.DENY, "ROBOT_NOT_ALLOWED", [policy.fallback.on_deny], None
    if not _explicit_member(request.mission_id, req.allowed_missions):
        return Decision.DENY, "MISSION_NOT_ALLOWED", [policy.fallback.on_deny], None
    if state.robot_id != request.robot_id or state.edge_agent_id != request.edge_agent_id:
        return Decision.DENY, "STATE_ASSERTION_MISMATCH", [policy.fallback.on_deny], None
    if state.mission_id != request.mission_id:
        return Decision.DENY, "MISSION_STATE_MISMATCH", [policy.fallback.on_deny], None
    if state_auth_reason := state_auth_violation(state, edge_public_keys_by_id):
        return Decision.DENY, state_auth_reason, [policy.fallback.on_deny], None
    if state_time_reason := state_time_violation(
        state,
        now=now,
        max_age_seconds=max_state_age_seconds,
    ):
        return Decision.DENY, state_time_reason, [policy.fallback.on_deny], None
    if _network_requirements_malformed(req.network):
        return (
            Decision.DENY,
            "POLICY_NETWORK_REQUIREMENTS_MALFORMED",
            [policy.fallback.on_deny],
            None,
        )
    if _network_state_malformed(net):
        return Decision.DENY, "NETWORK_STATE_MALFORMED", [policy.fallback.on_deny], None
    if req.geofence_required and state.geofence_state.inside != req.geofence_allowed:
        return Decision.DENY, "GEOFENCE_NOT_SATISFIED", [policy.fallback.on_deny], None
    if req.human_operator_available and not state.human_operator_available:
        return Decision.DENY, "HUMAN_OPERATOR_NOT_AVAILABLE", [policy.fallback.on_deny], None

    network_result = _evaluate_network_requirements(req.network, net, policy.fallback)
    if network_result is not None:
        return network_result

    constraints = LeaseConstraints(
        geofence_id=state.geofence_state.geofence_id,
        max_latency_ms_p95=req.network.max_latency_ms_p95,
        max_packet_loss_pct=req.network.max_packet_loss_pct,
        min_uplink_mbps=req.network.min_uplink_mbps,
        fallback_on_degrade=policy.fallback.on_network_degrade,
    )
    return Decision.ALLOW, "POLICY_SATISFIED", [], constraints


def evaluate_policy(
    request: CapabilityRequest,
    state: RobotStateAssertion,
    policy: Policy,
    *,
    audit_log: AuditLog,
    deciding_actor_id: str,
    agent_public_keys_by_id: Mapping[str, str],
    edge_public_keys_by_id: Mapping[str, str],
    accepted_policy_digests: set[str],
    replay_cache: RequestReplayCache,
    now: datetime | None = None,
    max_request_age_seconds: int = DEFAULT_REQUEST_MAX_AGE_SECONDS,
    max_state_age_seconds: int = DEFAULT_STATE_MAX_AGE_SECONDS,
) -> tuple[Decision, str, list[FallbackAction], LeaseConstraints | None, AuditCommit]:
    decision, reason, alternatives, constraints = _evaluate_policy_inputs(
        request,
        state,
        policy,
        agent_public_keys_by_id=agent_public_keys_by_id,
        edge_public_keys_by_id=edge_public_keys_by_id,
        accepted_policy_digests=accepted_policy_digests,
        replay_cache=replay_cache,
        now=now,
        max_request_age_seconds=max_request_age_seconds,
        max_state_age_seconds=max_state_age_seconds,
    )
    event_type = {
        Decision.ALLOW: AuditEventType.CAPABILITY_ALLOWED,
        Decision.DENY: AuditEventType.CAPABILITY_DENIED,
        Decision.DEGRADE: AuditEventType.CAPABILITY_DEGRADED,
    }[decision]
    payload = {
        "request_id": request.message_id,
        "state_assertion_id": state.message_id,
        "decision": decision,
        "reason_code": reason,
        "safe_alternatives": alternatives,
        "policy_id": policy.policy_id,
        "constraints": constraints.model_dump(mode="json") if constraints else None,
        "network_state": state.network_state.model_dump(mode="json"),
        "geofence_state": state.geofence_state.model_dump(mode="json"),
    }
    event = audit_log.record(
        event_type=event_type,
        actor_id=deciding_actor_id,
        robot_id=request.robot_id,
        mission_id=request.mission_id,
        correlation_id=request.correlation_id,
        summary=f"{decision.value} {request.capability.value}: {reason}",
        payload=payload,
        policy_id=policy.policy_id,
        policy_digest=policy_digest(policy),
        state_refs=[state.message_id],
        related_message_ids=[request.message_id, state.message_id],
    )
    return decision, reason, alternatives, constraints, event
