use std::fmt;

use serde::de;
use serde::{Deserialize, Deserializer, Serialize};

use crate::audit::AuditEvent;

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct VerificationInput {
    pub lease: CapabilityLeaseEnvelope,
    pub command: EdgeCommand,
    pub local_context: LocalContext,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CapabilityLeaseEnvelope {
    pub alg: String,
    pub claims: CapabilityLeaseClaims,
    pub signature: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CapabilityLeaseClaims {
    pub lease_id: String,
    pub issuer_id: String,
    pub agent_id: String,
    pub edge_agent_id: String,
    pub robot_id: String,
    pub mission_id: String,
    pub capability: String,
    pub constraints: LeaseConstraints,
    pub issued_at: i64,
    pub expires_at: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub not_before: Option<i64>,
    pub nonce: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LeaseConstraints {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub geofence_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_latency_ms_p95: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_packet_loss_pct: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub min_uplink_mbps: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub fallback_on_degrade: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_speed_mps: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub network_violation_action: Option<NetworkViolationAction>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NetworkViolationAction {
    Deny,
    Degrade,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EdgeCommand {
    pub command_id: String,
    pub agent_id: String,
    pub authenticated_agent_id: String,
    pub edge_agent_id: String,
    pub robot_id: String,
    pub mission_id: String,
    pub capability: String,
    pub command_nonce: String,
    pub created_at_unix_ms: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_speed_mps: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LocalContext {
    pub robot_id: String,
    pub edge_agent_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub authenticated_edge_agent_id: Option<String>,
    pub mission_id: String,
    pub observed_at_unix_ms: i64,
    pub network_state: NetworkState,
    pub geofence_state: GeofenceState,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<String>,
}

fn default_max_lease_ttl_ms() -> i64 {
    600_000
}

fn default_max_lease_age_ms() -> i64 {
    600_000
}

fn default_max_state_age_ms() -> i64 {
    30_000
}

fn default_max_command_age_ms() -> i64 {
    30_000
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TrustedVerifierContext {
    pub policy_id: String,
    pub policy_digest: String,
    #[serde(deserialize_with = "deserialize_audit_chain_head")]
    pub audit_chain_head: String,
    pub accepted_policies: Vec<PolicyReference>,
    pub trusted_issuer_ids: Vec<String>,
    pub accepted_capabilities: Vec<String>,
    pub issuer_capability_scopes: Vec<IssuerCapabilityScope>,
    pub capability_constraint_requirements: Vec<CapabilityConstraintRequirement>,
    pub trusted_command_agent_ids: Vec<String>,
    #[serde(skip_serializing)]
    pub command_hmac_secret: String,
    #[serde(skip_serializing)]
    pub dev_hmac_secret: String,
    pub trusted_state_edge_ids: Vec<String>,
    #[serde(skip_serializing)]
    pub state_hmac_secret: String,
    pub revocations: RevocationSet,
    pub now_unix_ms: i64,
    #[serde(default = "default_max_lease_ttl_ms")]
    pub max_lease_ttl_ms: i64,
    #[serde(default = "default_max_lease_age_ms")]
    pub max_lease_age_ms: i64,
    #[serde(default = "default_max_state_age_ms")]
    pub max_state_age_ms: i64,
    #[serde(default = "default_max_command_age_ms")]
    pub max_command_age_ms: i64,
}

fn deserialize_audit_chain_head<'de, D>(deserializer: D) -> Result<String, D::Error>
where
    D: Deserializer<'de>,
{
    let value = String::deserialize(deserializer)?;
    if value.trim().starts_with("sha256:") && value.trim().len() > "sha256:".len() {
        Ok(value)
    } else {
        Err(de::Error::custom(
            "audit_chain_head must be a non-empty sha256 hash reference",
        ))
    }
}

impl fmt::Debug for TrustedVerifierContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TrustedVerifierContext")
            .field("policy_id", &self.policy_id)
            .field("policy_digest", &self.policy_digest)
            .field("audit_chain_head", &self.audit_chain_head)
            .field("accepted_policies", &self.accepted_policies)
            .field("trusted_issuer_ids", &self.trusted_issuer_ids)
            .field("accepted_capabilities", &self.accepted_capabilities)
            .field("issuer_capability_scopes", &self.issuer_capability_scopes)
            .field(
                "capability_constraint_requirements",
                &self.capability_constraint_requirements,
            )
            .field("trusted_command_agent_ids", &self.trusted_command_agent_ids)
            .field("command_hmac_secret", &"<redacted>")
            .field("dev_hmac_secret", &"<redacted>")
            .field("trusted_state_edge_ids", &self.trusted_state_edge_ids)
            .field("state_hmac_secret", &"<redacted>")
            .field("revocations", &self.revocations)
            .field("now_unix_ms", &self.now_unix_ms)
            .field("max_lease_ttl_ms", &self.max_lease_ttl_ms)
            .field("max_lease_age_ms", &self.max_lease_age_ms)
            .field("max_state_age_ms", &self.max_state_age_ms)
            .field("max_command_age_ms", &self.max_command_age_ms)
            .finish()
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct IssuerCapabilityScope {
    pub issuer_id: String,
    pub capabilities: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PolicyReference {
    pub policy_id: String,
    pub policy_digest: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CapabilityConstraintRequirement {
    pub capability: String,
    #[serde(default)]
    pub require_geofence_id: bool,
    #[serde(default)]
    pub require_network_thresholds: bool,
    #[serde(default)]
    pub require_fallback_on_degrade: bool,
    #[serde(default)]
    pub require_max_speed_mps: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NetworkState {
    pub profile: NetworkProfile,
    pub attached: bool,
    pub latency_ms_p95: f64,
    pub packet_loss_pct: f64,
    pub uplink_mbps: f64,
    pub observed_at_unix_ms: i64,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NetworkProfile {
    Unknown,
    Normal,
    DegradedTeleop,
    UplinkBad,
    Partition,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GeofenceState {
    pub geofence_id: String,
    pub inside: bool,
    pub verified_at_unix_ms: i64,
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(transparent)]
pub struct RevocationSet {
    pub lease_ids: Vec<String>,
}

impl RevocationSet {
    pub fn contains(&self, lease_id: &str) -> bool {
        self.lease_ids.iter().any(|id| id == lease_id)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub enum Decision {
    Allow,
    Deny,
    Degrade,
}

impl Decision {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Allow => "allow",
            Self::Deny => "deny",
            Self::Degrade => "degrade",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub enum ReasonCode {
    Allow,
    DenyInvalidSignature,
    DenyUnknownAlgorithm,
    DenyExpiredLease,
    DenyNotYetValid,
    DenyRevokedLease,
    DenyReplayedNonce,
    DenyRobotMismatch,
    DenyAgentMismatch,
    DenyMissionMismatch,
    DenyCapabilityNotGranted,
    DenyGeofenceViolation,
    DenyNetworkPolicy,
    DenyMalformedInput,
    DenyUnknownIssuer,
    DenyTtlTooLong,
    DenyStaleLease,
    DenyStaleState,
    DenyStateAuthenticatedEdgeMissing,
    DenyStateAuthenticatedEdgeMismatch,
    DenyStateKeyNotTrusted,
    DenyStateSignatureMissing,
    DenyInvalidStateSignature,
    DenyCommandAuthenticatedAgentMissing,
    DenyCommandAuthenticatedAgentMismatch,
    DenyCommandAgentKeyNotTrusted,
    DenyCommandSignatureMissing,
    DenyInvalidCommandSignature,
    DenyCommandNotYetValid,
    DenyStaleCommand,
    DenyReplayedCommand,
    DenyCommandConstraint,
    DenyPolicyDigestRequired,
    DenyPolicyDigestNotAccepted,
    DegradeNetworkPolicy,
}

impl ReasonCode {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Allow => "ALLOW",
            Self::DenyInvalidSignature => "DENY_INVALID_SIGNATURE",
            Self::DenyUnknownAlgorithm => "DENY_UNKNOWN_ALGORITHM",
            Self::DenyExpiredLease => "DENY_EXPIRED_LEASE",
            Self::DenyNotYetValid => "DENY_NOT_YET_VALID",
            Self::DenyRevokedLease => "DENY_REVOKED_LEASE",
            Self::DenyReplayedNonce => "DENY_REPLAYED_NONCE",
            Self::DenyRobotMismatch => "DENY_ROBOT_MISMATCH",
            Self::DenyAgentMismatch => "DENY_AGENT_MISMATCH",
            Self::DenyMissionMismatch => "DENY_MISSION_MISMATCH",
            Self::DenyCapabilityNotGranted => "DENY_CAPABILITY_NOT_GRANTED",
            Self::DenyGeofenceViolation => "DENY_GEOFENCE_VIOLATION",
            Self::DenyNetworkPolicy => "DENY_NETWORK_POLICY",
            Self::DenyMalformedInput => "DENY_MALFORMED_INPUT",
            Self::DenyUnknownIssuer => "DENY_UNKNOWN_ISSUER",
            Self::DenyTtlTooLong => "DENY_TTL_TOO_LONG",
            Self::DenyStaleLease => "DENY_STALE_LEASE",
            Self::DenyStaleState => "DENY_STALE_STATE",
            Self::DenyStateAuthenticatedEdgeMissing => "DENY_STATE_AUTHENTICATED_EDGE_MISSING",
            Self::DenyStateAuthenticatedEdgeMismatch => "DENY_STATE_AUTHENTICATED_EDGE_MISMATCH",
            Self::DenyStateKeyNotTrusted => "DENY_STATE_KEY_NOT_TRUSTED",
            Self::DenyStateSignatureMissing => "DENY_STATE_SIGNATURE_MISSING",
            Self::DenyInvalidStateSignature => "DENY_INVALID_STATE_SIGNATURE",
            Self::DenyCommandAuthenticatedAgentMissing => {
                "DENY_COMMAND_AUTHENTICATED_AGENT_MISSING"
            }
            Self::DenyCommandAuthenticatedAgentMismatch => {
                "DENY_COMMAND_AUTHENTICATED_AGENT_MISMATCH"
            }
            Self::DenyCommandAgentKeyNotTrusted => "DENY_COMMAND_AGENT_KEY_NOT_TRUSTED",
            Self::DenyCommandSignatureMissing => "DENY_COMMAND_SIGNATURE_MISSING",
            Self::DenyInvalidCommandSignature => "DENY_INVALID_COMMAND_SIGNATURE",
            Self::DenyCommandNotYetValid => "DENY_COMMAND_NOT_YET_VALID",
            Self::DenyStaleCommand => "DENY_STALE_COMMAND",
            Self::DenyReplayedCommand => "DENY_REPLAYED_COMMAND",
            Self::DenyCommandConstraint => "DENY_COMMAND_CONSTRAINT",
            Self::DenyPolicyDigestRequired => "DENY_POLICY_DIGEST_REQUIRED",
            Self::DenyPolicyDigestNotAccepted => "DENY_POLICY_DIGEST_NOT_ACCEPTED",
            Self::DegradeNetworkPolicy => "DEGRADE_NETWORK_POLICY",
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct VerificationDecision {
    pub decision: Decision,
    pub reason_code: ReasonCode,
    pub audit_event: AuditEvent,
}
