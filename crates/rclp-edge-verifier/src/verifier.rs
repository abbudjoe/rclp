use serde_json::Value;

use crate::audit::{AuditEvent, AuditSubject};
use crate::crypto::{
    verify_dev_hmac_sha256, verify_dev_hmac_sha256_command, verify_dev_hmac_sha256_local_context,
    DEV_HMAC_SHA256_ALG,
};
use crate::replay::ReplayCache;
use crate::types::{
    CapabilityConstraintRequirement, CapabilityLeaseClaims, Decision, EdgeCommand,
    LeaseConstraints, NetworkProfile, NetworkViolationAction, ReasonCode, TrustedVerifierContext,
    VerificationDecision, VerificationInput,
};

const CLOCK_SKEW_MS: i64 = 30_000;

pub fn verify_json_value(
    input: Value,
    trusted_context: &TrustedVerifierContext,
    replay_cache: &mut dyn ReplayCache,
) -> VerificationDecision {
    if !audit_chain_head_well_formed(trusted_context) {
        return malformed_decision(
            "trusted audit_chain_head is missing or malformed".to_string(),
            trusted_context,
        );
    }
    match serde_json::from_value::<VerificationInput>(input) {
        Ok(input) => verify(input, trusted_context, replay_cache),
        Err(error) => malformed_decision(
            format!("malformed verification input: {error}"),
            trusted_context,
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
        &input.command.command_nonce,
        &input.local_context.robot_id,
        &input.local_context.edge_agent_id,
        &input.local_context.mission_id,
        &trusted_context.policy_id,
        &trusted_context.policy_digest,
        &trusted_context.audit_chain_head,
        &trusted_context.command_hmac_secret,
        &trusted_context.dev_hmac_secret,
        &trusted_context.state_hmac_secret,
    ]) || trusted_context.trusted_issuer_ids.is_empty()
        || trusted_scope_malformed(trusted_context)
        || trusted_context.trusted_state_edge_ids.is_empty()
        || trusted_context.trusted_command_agent_ids.is_empty()
    {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    }
    if numeric_fields_malformed(&input, trusted_context) {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    }
    if let Some(reason) = policy_digest_violation(trusted_context) {
        return deny(&input, trusted_context, reason);
    }

    if input.lease.alg != DEV_HMAC_SHA256_ALG {
        return deny(&input, trusted_context, ReasonCode::DenyUnknownAlgorithm);
    }
    if trusted_context.trusted_issuer_ids.len() != 1
        || trusted_context.trusted_command_agent_ids.len() != 1
        || trusted_context.trusted_state_edge_ids.len() != 1
    {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    }

    if let Some(reason) = command_auth_violation(&input, trusted_context, replay_cache) {
        return deny(&input, trusted_context, reason);
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
    if !capability_allowed_for_issuer(claims, trusted_context) {
        return deny(
            &input,
            trusted_context,
            ReasonCode::DenyCapabilityNotGranted,
        );
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
    if required_constraints_missing(claims, trusted_context) {
        return deny(&input, trusted_context, ReasonCode::DenyMalformedInput);
    }
    if let Some(reason) = local_state_auth_violation(&input, trusted_context) {
        return deny(&input, trusted_context, reason);
    }
    if let Some(reason) = local_state_time_violation(&input, trusted_context) {
        return deny(&input, trusted_context, reason);
    }
    if geofence_violated(&input) {
        return deny(&input, trusted_context, ReasonCode::DenyGeofenceViolation);
    }
    if let Some(reason) = network_policy_violation(&input) {
        if reason == ReasonCode::DegradeNetworkPolicy {
            if !replay_cache.consume_nonce(&claims.nonce) {
                return deny(&input, trusted_context, ReasonCode::DenyReplayedNonce);
            }
            return decision(&input, trusted_context, Decision::Degrade, reason);
        }
        return deny(&input, trusted_context, reason);
    }
    if let Some(reason) = command_constraint_violation(&input) {
        return deny(&input, trusted_context, reason);
    }

    if !replay_cache.consume_nonce(&claims.nonce) {
        return deny(&input, trusted_context, ReasonCode::DenyReplayedNonce);
    }
    decision(&input, trusted_context, Decision::Allow, ReasonCode::Allow)
}

fn required_text_missing(values: &[&String]) -> bool {
    values.iter().any(|value| value.trim().is_empty())
}

fn trusted_scope_malformed(trusted_context: &TrustedVerifierContext) -> bool {
    trusted_context.accepted_capabilities.is_empty()
        || !audit_chain_head_well_formed(trusted_context)
        || string_list_missing(&trusted_context.accepted_capabilities)
        || trusted_context.accepted_policies.is_empty()
        || trusted_context.accepted_policies.iter().any(|policy| {
            policy.policy_id.trim().is_empty() || policy.policy_digest.trim().is_empty()
        })
        || trusted_context.issuer_capability_scopes.is_empty()
        || trusted_context
            .capability_constraint_requirements
            .is_empty()
        || string_list_missing(&trusted_context.trusted_command_agent_ids)
        || trusted_context
            .issuer_capability_scopes
            .iter()
            .any(|scope| {
                scope.issuer_id.trim().is_empty()
                    || scope.capabilities.is_empty()
                    || string_list_missing(&scope.capabilities)
            })
        || trusted_context
            .accepted_capabilities
            .iter()
            .any(|capability| {
                trusted_context
                    .capability_constraint_requirements
                    .iter()
                    .filter(|requirement| requirement.capability == *capability)
                    .count()
                    != 1
            })
        || trusted_context
            .capability_constraint_requirements
            .iter()
            .any(|requirement| requirement.capability.trim().is_empty())
}

fn string_list_missing(values: &[String]) -> bool {
    values.iter().any(|value| value.trim().is_empty())
}

fn capability_allowed_for_issuer(
    claims: &CapabilityLeaseClaims,
    trusted_context: &TrustedVerifierContext,
) -> bool {
    trusted_context
        .accepted_capabilities
        .iter()
        .any(|capability| capability == &claims.capability)
        && trusted_context
            .issuer_capability_scopes
            .iter()
            .any(|scope| {
                scope.issuer_id == claims.issuer_id
                    && scope
                        .capabilities
                        .iter()
                        .any(|capability| capability == &claims.capability)
            })
}

fn policy_digest_violation(trusted_context: &TrustedVerifierContext) -> Option<ReasonCode> {
    if trusted_context.policy_id.trim().is_empty()
        || trusted_context.policy_digest.trim().is_empty()
    {
        return Some(ReasonCode::DenyPolicyDigestRequired);
    }
    if !trusted_context.accepted_policies.iter().any(|policy| {
        policy.policy_id == trusted_context.policy_id
            && policy.policy_digest == trusted_context.policy_digest
    }) {
        return Some(ReasonCode::DenyPolicyDigestNotAccepted);
    }
    None
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
        || trusted_context.max_state_age_ms <= 0
        || trusted_context.max_command_age_ms <= 0
        || input.command.created_at_unix_ms < 0
        || input.local_context.observed_at_unix_ms < 0
        || input.local_context.network_state.observed_at_unix_ms < 0
        || input.local_context.geofence_state.verified_at_unix_ms < 0
    {
        return true;
    }

    if input
        .command
        .max_speed_mps
        .is_some_and(|value| !finite_nonnegative(value))
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

fn command_auth_violation(
    input: &VerificationInput,
    trusted_context: &TrustedVerifierContext,
    replay_cache: &mut dyn ReplayCache,
) -> Option<ReasonCode> {
    let command = &input.command;
    if command.authenticated_agent_id.trim().is_empty() {
        return Some(ReasonCode::DenyCommandAuthenticatedAgentMissing);
    }
    if command.authenticated_agent_id != command.agent_id {
        return Some(ReasonCode::DenyCommandAuthenticatedAgentMismatch);
    }
    if !trusted_context
        .trusted_command_agent_ids
        .iter()
        .any(|agent_id| agent_id == &command.authenticated_agent_id)
    {
        return Some(ReasonCode::DenyCommandAgentKeyNotTrusted);
    }
    let Some(signature) = command.signature.as_ref() else {
        return Some(ReasonCode::DenyCommandSignatureMissing);
    };
    if signature.trim().is_empty() {
        return Some(ReasonCode::DenyCommandSignatureMissing);
    }
    if verify_dev_hmac_sha256_command(command, signature, &trusted_context.command_hmac_secret)
        .is_err()
    {
        return Some(ReasonCode::DenyInvalidCommandSignature);
    }
    if let Some(reason) = command_time_violation(input, trusted_context) {
        return Some(reason);
    }
    let command_id_key = format!(
        "command-id:{}:{}",
        command.authenticated_agent_id, command.command_id
    );
    let command_nonce_key = format!(
        "command-nonce:{}:{}",
        command.authenticated_agent_id, command.command_nonce
    );
    if !replay_cache.consume_nonce(&command_id_key)
        || !replay_cache.consume_nonce(&command_nonce_key)
    {
        return Some(ReasonCode::DenyReplayedCommand);
    }
    None
}

fn command_time_violation(
    input: &VerificationInput,
    trusted_context: &TrustedVerifierContext,
) -> Option<ReasonCode> {
    let Some(max_age) = trusted_context
        .max_command_age_ms
        .checked_add(CLOCK_SKEW_MS)
    else {
        return Some(ReasonCode::DenyMalformedInput);
    };
    let Some(max_future_timestamp) = trusted_context.now_unix_ms.checked_add(CLOCK_SKEW_MS) else {
        return Some(ReasonCode::DenyMalformedInput);
    };
    let timestamp = input.command.created_at_unix_ms;
    if timestamp > max_future_timestamp {
        return Some(ReasonCode::DenyCommandNotYetValid);
    }
    let Some(age) = trusted_context.now_unix_ms.checked_sub(timestamp) else {
        return Some(ReasonCode::DenyCommandNotYetValid);
    };
    if age > max_age {
        return Some(ReasonCode::DenyStaleCommand);
    }
    None
}

fn local_state_time_violation(
    input: &VerificationInput,
    trusted_context: &TrustedVerifierContext,
) -> Option<ReasonCode> {
    let Some(max_age) = trusted_context.max_state_age_ms.checked_add(CLOCK_SKEW_MS) else {
        return Some(ReasonCode::DenyMalformedInput);
    };
    let Some(max_future_timestamp) = trusted_context.now_unix_ms.checked_add(CLOCK_SKEW_MS) else {
        return Some(ReasonCode::DenyMalformedInput);
    };
    for timestamp in [
        input.local_context.observed_at_unix_ms,
        input.local_context.network_state.observed_at_unix_ms,
        input.local_context.geofence_state.verified_at_unix_ms,
    ] {
        if timestamp > max_future_timestamp {
            return Some(ReasonCode::DenyStaleState);
        }
        if let Some(age) = trusted_context.now_unix_ms.checked_sub(timestamp) {
            if age > max_age {
                return Some(ReasonCode::DenyStaleState);
            }
        }
    }
    None
}

fn local_state_auth_violation(
    input: &VerificationInput,
    trusted_context: &TrustedVerifierContext,
) -> Option<ReasonCode> {
    let Some(authenticated_edge_agent_id) =
        input.local_context.authenticated_edge_agent_id.as_ref()
    else {
        return Some(ReasonCode::DenyStateAuthenticatedEdgeMissing);
    };
    if authenticated_edge_agent_id.trim().is_empty() {
        return Some(ReasonCode::DenyStateAuthenticatedEdgeMissing);
    }
    if authenticated_edge_agent_id != &input.local_context.edge_agent_id {
        return Some(ReasonCode::DenyStateAuthenticatedEdgeMismatch);
    }
    if !trusted_context
        .trusted_state_edge_ids
        .iter()
        .any(|edge_id| edge_id == authenticated_edge_agent_id)
    {
        return Some(ReasonCode::DenyStateKeyNotTrusted);
    }
    let Some(signature) = input.local_context.signature.as_ref() else {
        return Some(ReasonCode::DenyStateSignatureMissing);
    };
    if signature.trim().is_empty() {
        return Some(ReasonCode::DenyStateSignatureMissing);
    }
    if verify_dev_hmac_sha256_local_context(
        &input.local_context,
        signature,
        &trusted_context.state_hmac_secret,
    )
    .is_err()
    {
        return Some(ReasonCode::DenyInvalidStateSignature);
    }
    None
}

fn command_constraint_violation(input: &VerificationInput) -> Option<ReasonCode> {
    let max_speed = input.lease.claims.constraints.max_speed_mps?;
    let Some(command_speed) = input.command.max_speed_mps else {
        return Some(ReasonCode::DenyCommandConstraint);
    };
    if command_speed > max_speed {
        return Some(ReasonCode::DenyCommandConstraint);
    }
    None
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

fn required_constraints_missing(
    claims: &CapabilityLeaseClaims,
    trusted_context: &TrustedVerifierContext,
) -> bool {
    let Some(requirement) = trusted_context
        .capability_constraint_requirements
        .iter()
        .find(|requirement| requirement.capability == claims.capability)
    else {
        return true;
    };
    capability_constraints_missing(&claims.constraints, requirement)
}

fn capability_constraints_missing(
    constraints: &LeaseConstraints,
    requirement: &CapabilityConstraintRequirement,
) -> bool {
    (requirement.require_geofence_id && constraints.geofence_id.is_none())
        || (requirement.require_network_thresholds
            && (constraints.max_latency_ms_p95.is_none()
                || constraints.max_packet_loss_pct.is_none()
                || constraints.min_uplink_mbps.is_none()))
        || (requirement.require_fallback_on_degrade
            && constraints
                .fallback_on_degrade
                .as_deref()
                .unwrap_or("")
                .trim()
                .is_empty())
        || (requirement.require_max_speed_mps && constraints.max_speed_mps.is_none())
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
    let payload = serde_json::json!({
        "decision": result.as_str(),
        "reason_code": reason_code.as_str(),
        "lease_id": &input.lease.claims.lease_id,
        "lease_issuer_id": &input.lease.claims.issuer_id,
        "command_id": &input.command.command_id,
        "command_agent_id": &input.command.agent_id,
        "authenticated_command_agent_id": &input.command.authenticated_agent_id,
        "edge_agent_id": &input.command.edge_agent_id,
        "robot_id": &input.command.robot_id,
        "mission_id": &input.command.mission_id,
        "capability": &input.command.capability,
        "local_context_observed_at_unix_ms": input.local_context.observed_at_unix_ms,
    });
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
                actor_id: input.command.edge_agent_id.clone(),
                correlation_id: input.command.command_id.clone(),
                payload,
                policy_id: Some(trusted_context.policy_id.clone()),
                policy_digest: Some(trusted_context.policy_digest.clone()),
                previous_audit_hash: audit_chain_head(trusted_context),
                state_refs: vec![format!(
                    "local_context:{}:{}",
                    input.local_context.edge_agent_id, input.local_context.observed_at_unix_ms
                )],
                related_message_ids: vec![
                    input.command.command_id.clone(),
                    input.lease.claims.lease_id.clone(),
                ],
                observed_at_unix_ms: trusted_context.now_unix_ms,
            },
        ),
    }
}

fn malformed_decision(
    summary: String,
    trusted_context: &TrustedVerifierContext,
) -> VerificationDecision {
    let reason_code = ReasonCode::DenyMalformedInput;
    let payload = serde_json::json!({
        "decision": Decision::Deny.as_str(),
        "reason_code": reason_code.as_str(),
        "summary": summary,
    });
    VerificationDecision {
        decision: Decision::Deny,
        reason_code,
        audit_event: AuditEvent::new(
            Decision::Deny,
            reason_code,
            AuditSubject {
                lease_id: None,
                command_id: None,
                robot_id: None,
                edge_agent_id: None,
                mission_id: None,
                actor_id: "local_edge_verifier".to_string(),
                correlation_id: "malformed_verification_input".to_string(),
                payload,
                policy_id: Some(trusted_context.policy_id.clone())
                    .filter(|value| !value.is_empty()),
                policy_digest: Some(trusted_context.policy_digest.clone())
                    .filter(|value| !value.is_empty()),
                previous_audit_hash: audit_chain_head(trusted_context),
                state_refs: Vec::new(),
                related_message_ids: Vec::new(),
                observed_at_unix_ms: trusted_context.now_unix_ms,
            },
        ),
    }
}

fn audit_chain_head(trusted_context: &TrustedVerifierContext) -> Option<String> {
    Some(trusted_context.audit_chain_head.clone())
}

fn audit_chain_head_well_formed(trusted_context: &TrustedVerifierContext) -> bool {
    let value = trusted_context.audit_chain_head.trim();
    value.starts_with("sha256:") && value.len() > "sha256:".len()
}
