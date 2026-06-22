use serde::{Deserialize, Serialize};

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
    pub edge_agent_id: String,
    pub robot_id: String,
    pub mission_id: String,
    pub capability: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LocalContext {
    pub robot_id: String,
    pub edge_agent_id: String,
    pub mission_id: String,
    pub network_state: NetworkState,
    pub geofence_state: GeofenceState,
}

fn default_max_lease_ttl_ms() -> i64 {
    600_000
}

fn default_max_lease_age_ms() -> i64 {
    600_000
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TrustedVerifierContext {
    pub trusted_issuer_ids: Vec<String>,
    pub dev_hmac_secret: String,
    pub revocations: RevocationSet,
    pub now_unix_ms: i64,
    #[serde(default = "default_max_lease_ttl_ms")]
    pub max_lease_ttl_ms: i64,
    #[serde(default = "default_max_lease_age_ms")]
    pub max_lease_age_ms: i64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NetworkState {
    pub profile: NetworkProfile,
    pub attached: bool,
    pub latency_ms_p95: f64,
    pub packet_loss_pct: f64,
    pub uplink_mbps: f64,
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
