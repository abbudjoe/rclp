use serde_json::Value;

use crate::audit::{AuditEvent, AuditSubject};
use crate::crypto::{verify_dev_hmac_sha256, DEV_HMAC_SHA256_ALG};
use crate::replay::ReplayCache;
use crate::types::{
    CapabilityLeaseClaims, Decision, EdgeCommand, LeaseConstraints, NetworkProfile,
    NetworkViolationAction, ReasonCode, TrustedVerifierContext, VerificationDecision,
    VerificationInput,
};

pub fn verify_json_value(
    input: Value,
    trusted_context: &TrustedVerifierContext,
    replay_cache: &mut dyn ReplayCache,
) -> VerificationDecision {
    match serde_json::from_value::<VerificationInput>(input) {
        Ok(input) => verify(input, trusted_context, replay_cache),
        Err(error) => malformed_decision(
            format!("malformed verification input: {error}"),
            trusted_context.now_unix_ms,
        ),
    }
}

pub fn verify(
    input: VerificationInput,
    trusted_context: &TrustedVerifierContext,
    replay_cache: &mut dyn ReplayCache,
) -> VerificationDecision {
    let claims = &input.lease.claims;

    if required_text_missing(&[
        &input.lease.alg,
        &input.lease.signature,
        &claims.lease_id,
        &claims.issuer_id,
        &claims.agent_id,
        &claims.edge_agent_id,
        &claims.robot_id,
        &claims.mission_id,
        &claims.capability,
        &claims.nonce,
        &input.command.command_id,
        &input.command.agent_id,
        &input.command.edge_agent_id,
        &input.command.robot_id,
        &input.command.mission_id,
        &input.command.capability,
        &input.local_context.robot_id,
        &input.local_context.edge_agent_id,
        &input.local_context.mission_id,
        &trusted_context.dev_hmac_secret,
    ]) || trusted_context.trusted_issuer_ids.is_empty()
    {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    }
    if numeric_fields_malformed(&input, trusted_context) {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    }

    if input.lease.alg != DEV_HMAC_SHA256_ALG {
        return deny(&input, trusted_context, ReasonCode::DenyUnknownAlgorithm);
    }

    if !trusted_context
        .trusted_issuer_ids
        .iter()
        .any(|issuer| issuer == &claims.issuer_id)
    {
        return deny(&input, trusted_context, ReasonCode::DenyUnknownIssuer);
    }

    if verify_dev_hmac_sha256(
        claims,
        &input.lease.signature,
        &trusted_context.dev_hmac_secret,
    )
    .is_err()
    {
        return deny(&input, trusted_context, ReasonCode::DenyInvalidSignature);
    }

    if let Some(not_before) = claims.not_before {
        if trusted_context.now_unix_ms < not_before {
            return deny(&input, trusted_context, ReasonCode::DenyNotYetValid);
        }
    }
    if trusted_context.now_unix_ms < claims.issued_at {
        return deny(&input, trusted_context, ReasonCode::DenyNotYetValid);
    }
    if trusted_context.now_unix_ms >= claims.expires_at {
        return deny(&input, trusted_context, ReasonCode::DenyExpiredLease);
    }
    if claims.expires_at <= claims.issued_at {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    }
    let Some(lease_ttl_ms) = claims.expires_at.checked_sub(claims.issued_at) else {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    };
    let Some(max_ttl_ms) = trusted_context.max_lease_ttl_ms.checked_add(30_000) else {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    };
    if lease_ttl_ms > max_ttl_ms {
        return deny(&input, trusted_context, ReasonCode::DenyTtlTooLong);
    }
    let Some(lease_age_ms) = trusted_context.now_unix_ms.checked_sub(claims.issued_at) else {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    };
    let Some(max_age_ms) = trusted_context.max_lease_age_ms.checked_add(30_000) else {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    };
    if lease_age_ms > max_age_ms {
        return deny(&input, trusted_context, ReasonCode::DenyStaleLease);
    }
    if trusted_context.revocations.contains(&claims.lease_id) {
        return deny(&input, trusted_context, ReasonCode::DenyRevokedLease);
    }
    if replay_cache.seen(&claims.nonce) {
        return deny(&input, trusted_context, ReasonCode::DenyReplayedNonce);
    }
    if !context_robot_matches(&input.command, claims, &input) {
        return deny(&input, trusted_context, ReasonCode::DenyRobotMismatch);
    }
    if !context_agent_matches(&input.command, claims, &input) {
        return deny(&input, trusted_context, ReasonCode::DenyAgentMismatch);
    }
    if input.command.mission_id != claims.mission_id
        || input.local_context.mission_id != claims.mission_id
    {
        return deny(&input, trusted_context, ReasonCode::DenyMissionMismatch);
    }
    if input.command.capability != claims.capability {
        return deny(
            &input,
            trusted_context,
            ReasonCode::DenyCapabilityNotGranted,
        );
    }
    if remote_assist_constraints_missing(claims) {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    }
    if geofence_violated(&input) {
        return deny(&input, trusted_context, ReasonCode::DenyGeofenceViolation);
    }
    if let Some(reason) = network_policy_violation(&input) {
        if reason == ReasonCode::DegradeNetworkPolicy {
            replay_cache.mark_seen(&claims.nonce);
            return decision(&input, trusted_context, Decision::Degrade, reason);
        }
        return deny(&input, trusted_context, reason);
    }

    replay_cache.mark_seen(&claims.nonce);
    decision(&input, trusted_context, Decision::Allow, ReasonCode::Allow)
}

fn required_text_missing(values: &[&String]) -> bool {
    values.iter().any(|value| value.trim().is_empty())
}

fn numeric_fields_malformed(
    input: &VerificationInput,
    trusted_context: &TrustedVerifierContext,
) -> bool {
    let claims = &input.lease.claims;
    if trusted_context.now_unix_ms < 0
        || claims.issued_at < 0
        || claims.expires_at < 0
        || claims.not_before.is_some_and(|value| value < 0)
        || trusted_context.max_lease_ttl_ms <= 0
        || trusted_context.max_lease_age_ms <= 0
    {
        return true;
    }

    let network = &input.local_context.network_state;
    if !finite_nonnegative(network.latency_ms_p95)
        || !finite_nonnegative(network.packet_loss_pct)
        || network.packet_loss_pct > 100.0
        || !finite_nonnegative(network.uplink_mbps)
    {
        return true;
    }

    let constraints = &claims.constraints;
    option_malformed_nonnegative(constraints.max_latency_ms_p95)
        || option_malformed_packet_loss(constraints.max_packet_loss_pct)
        || option_malformed_nonnegative(constraints.min_uplink_mbps)
        || option_malformed_nonnegative(constraints.max_speed_mps)
}

fn finite_nonnegative(value: f64) -> bool {
    value.is_finite() && value >= 0.0
}

fn option_malformed_nonnegative(value: Option<f64>) -> bool {
    value.is_some_and(|value| !finite_nonnegative(value))
}

fn option_malformed_packet_loss(value: Option<f64>) -> bool {
    value.is_some_and(|value| !finite_nonnegative(value) || value > 100.0)
}

fn context_robot_matches(
    command: &EdgeCommand,
    claims: &CapabilityLeaseClaims,
    input: &VerificationInput,
) -> bool {
    command.robot_id == claims.robot_id && input.local_context.robot_id == claims.robot_id
}

fn context_agent_matches(
    command: &EdgeCommand,
    claims: &CapabilityLeaseClaims,
    input: &VerificationInput,
) -> bool {
    command.agent_id == claims.agent_id
        && command.edge_agent_id == claims.edge_agent_id
        && input.local_context.edge_agent_id == claims.edge_agent_id
}

fn remote_assist_constraints_missing(claims: &CapabilityLeaseClaims) -> bool {
    if claims.capability != "remote_assist" {
        return false;
    }
    claims.constraints.geofence_id.is_none()
        || claims.constraints.max_latency_ms_p95.is_none()
        || claims.constraints.max_packet_loss_pct.is_none()
        || claims.constraints.min_uplink_mbps.is_none()
}

fn geofence_violated(input: &VerificationInput) -> bool {
    let Some(geofence_id) = &input.lease.claims.constraints.geofence_id else {
        return false;
    };
    !input.local_context.geofence_state.inside
        || input.local_context.geofence_state.geofence_id != *geofence_id
}

fn network_policy_violation(input: &VerificationInput) -> Option<ReasonCode> {
    let constraints = &input.lease.claims.constraints;
    let network = &input.local_context.network_state;

    let hard_denial = matches!(
        network.profile,
        NetworkProfile::Unknown | NetworkProfile::Partition
    ) || !network.attached;

    let threshold_denial =
        threshold_violated(constraints, network.latency_ms_p95, NetworkMetric::Latency)
            || threshold_violated(
                constraints,
                network.packet_loss_pct,
                NetworkMetric::PacketLoss,
            )
            || threshold_violated(constraints, network.uplink_mbps, NetworkMetric::Uplink);

    if !hard_denial && !threshold_denial {
        return None;
    }
    if constraints
        .fallback_on_degrade
        .as_deref()
        .unwrap_or("")
        .is_empty()
    {
        return Some(ReasonCode::DenyMalformedInput);
    }
    if hard_denial {
        return Some(ReasonCode::DenyNetworkPolicy);
    }
    if constraints.network_violation_action == Some(NetworkViolationAction::Degrade) {
        return Some(ReasonCode::DegradeNetworkPolicy);
    }
    Some(ReasonCode::DenyNetworkPolicy)
}

enum NetworkMetric {
    Latency,
    PacketLoss,
    Uplink,
}

fn threshold_violated(
    constraints: &LeaseConstraints,
    observed: f64,
    metric: NetworkMetric,
) -> bool {
    match metric {
        NetworkMetric::Latency => constraints
            .max_latency_ms_p95
            .is_some_and(|max| observed > max),
        NetworkMetric::PacketLoss => constraints
            .max_packet_loss_pct
            .is_some_and(|max| observed > max),
        NetworkMetric::Uplink => constraints
            .min_uplink_mbps
            .is_some_and(|min| observed < min),
    }
}

fn deny(
    input: &VerificationInput,
    trusted_context: &TrustedVerifierContext,
    reason_code: ReasonCode,
) -> VerificationDecision {
    decision(input, trusted_context, Decision::Deny, reason_code)
}

fn decision(
    input: &VerificationInput,
    trusted_context: &TrustedVerifierContext,
    result: Decision,
    reason_code: ReasonCode,
) -> VerificationDecision {
    VerificationDecision {
        decision: result,
        reason_code,
        audit_event: AuditEvent::new(
            result,
            reason_code,
            AuditSubject {
                lease_id: Some(input.lease.claims.lease_id.clone()),
                command_id: Some(input.command.command_id.clone()),
                robot_id: Some(input.command.robot_id.clone()),
                edge_agent_id: Some(input.command.edge_agent_id.clone()),
                mission_id: Some(input.command.mission_id.clone()),
                observed_at_unix_ms: trusted_context.now_unix_ms,
            },
        ),
    }
}

fn malformed_decision(summary: String, observed_at_unix_ms: i64) -> VerificationDecision {
    let reason_code = ReasonCode::DenyMalformedInput;
    VerificationDecision {
        decision: Decision::Deny,
        reason_code,
        audit_event: AuditEvent {
            event_type: "command_rejected".to_string(),
            decision: Decision::Deny,
            reason_code,
            lease_id: None,
            command_id: None,
            robot_id: None,
            edge_agent_id: None,
            mission_id: None,
            observed_at_unix_ms,
            summary,
        },
    }
}
