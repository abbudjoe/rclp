use serde::Serialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

use crate::canonical_json::canonical_json;
use crate::types::{Decision, ReasonCode};

#[derive(Clone, Debug)]
pub(crate) struct AuditSubject {
    pub lease_id: Option<String>,
    pub command_id: Option<String>,
    pub robot_id: Option<String>,
    pub edge_agent_id: Option<String>,
    pub mission_id: Option<String>,
    pub actor_id: String,
    pub correlation_id: String,
    pub payload: Value,
    pub policy_id: Option<String>,
    pub policy_digest: Option<String>,
    pub previous_audit_hash: Option<String>,
    pub state_refs: Vec<String>,
    pub related_message_ids: Vec<String>,
    pub observed_at_unix_ms: i64,
}

#[derive(Clone, Debug, Serialize)]
pub struct AuditEvent {
    pub audit_id: String,
    pub message_id: String,
    pub message_type: String,
    pub protocol_version: String,
    pub correlation_id: String,
    pub event_type: String,
    pub actor_id: String,
    pub decision: Decision,
    pub reason_code: ReasonCode,
    pub lease_id: Option<String>,
    pub command_id: Option<String>,
    pub robot_id: Option<String>,
    pub edge_agent_id: Option<String>,
    pub mission_id: Option<String>,
    pub payload: Value,
    pub payload_hash: String,
    pub authority_relevant: bool,
    pub integrity_profile: String,
    pub integrity_proof: String,
    pub policy_id: Option<String>,
    pub policy_digest: Option<String>,
    pub previous_audit_hash: Option<String>,
    pub state_refs: Vec<String>,
    pub related_message_ids: Vec<String>,
    pub created_at: i64,
    pub created_at_unix_ms: i64,
    pub observed_at_unix_ms: i64,
    pub summary: String,
}

impl AuditEvent {
    pub(crate) fn new(decision: Decision, reason_code: ReasonCode, subject: AuditSubject) -> Self {
        let event_type = match decision {
            Decision::Allow => "command_allowed",
            Decision::Deny => "command_rejected",
            Decision::Degrade => "capability_degraded",
        }
        .to_string();
        let summary = format!("{}: {}", decision.as_str(), reason_code.as_str());
        let payload_hash = stable_hash(&subject.payload);
        let integrity_profile = "rclp-dev-sha256-v1".to_string();
        let lease_id = subject.lease_id.clone();
        let command_id = subject.command_id.clone();
        let robot_id = subject.robot_id.clone();
        let edge_agent_id = subject.edge_agent_id.clone();
        let mission_id = subject.mission_id.clone();
        let actor_id = subject.actor_id.clone();
        let correlation_id = subject.correlation_id.clone();
        let policy_id = subject.policy_id.clone();
        let policy_digest = subject.policy_digest.clone();
        let previous_audit_hash = subject.previous_audit_hash.clone();
        let state_refs = subject.state_refs.clone();
        let related_message_ids = subject.related_message_ids.clone();
        let created_at = subject.observed_at_unix_ms;
        let audit_seed = json!({
            "event_type": event_type.clone(),
            "reason_code": reason_code.as_str(),
            "lease_id": lease_id,
            "command_id": command_id,
            "observed_at_unix_ms": subject.observed_at_unix_ms,
        });
        let audit_id = format!("audit_{}", stable_hash_suffix(&audit_seed));
        let message_id = format!(
            "msg_{}",
            stable_hash_suffix(&json!({
                "audit_id": audit_id.clone(),
                "message_type": "audit_commit",
            }))
        );
        let proof_payload = json!({
            "audit_id": audit_id.clone(),
            "message_id": message_id.clone(),
            "message_type": "audit_commit",
            "protocol_version": "0.0.1-draft",
            "correlation_id": correlation_id.clone(),
            "event_type": event_type.clone(),
            "actor_id": actor_id.clone(),
            "decision": decision,
            "reason_code": reason_code,
            "lease_id": lease_id.clone(),
            "command_id": command_id.clone(),
            "robot_id": robot_id.clone(),
            "edge_agent_id": edge_agent_id.clone(),
            "mission_id": mission_id.clone(),
            "summary": summary.clone(),
            "payload_hash": payload_hash.clone(),
            "authority_relevant": true,
            "integrity_profile": integrity_profile.clone(),
            "policy_id": policy_id.clone(),
            "policy_digest": policy_digest.clone(),
            "previous_audit_hash": previous_audit_hash.clone(),
            "state_refs": state_refs.clone(),
            "related_message_ids": related_message_ids.clone(),
            "created_at": created_at,
            "created_at_unix_ms": created_at,
            "observed_at_unix_ms": subject.observed_at_unix_ms,
        });
        let integrity_proof = stable_hash(&proof_payload);
        Self {
            audit_id,
            message_id,
            message_type: "audit_commit".to_string(),
            protocol_version: "0.0.1-draft".to_string(),
            correlation_id,
            event_type,
            actor_id,
            decision,
            reason_code,
            lease_id: subject.lease_id,
            command_id: subject.command_id,
            robot_id: subject.robot_id,
            edge_agent_id,
            mission_id,
            payload: subject.payload,
            payload_hash,
            authority_relevant: true,
            integrity_profile,
            integrity_proof,
            policy_id,
            policy_digest,
            previous_audit_hash,
            state_refs,
            related_message_ids,
            created_at,
            created_at_unix_ms: created_at,
            observed_at_unix_ms: subject.observed_at_unix_ms,
            summary,
        }
    }
}

fn stable_hash(value: &Value) -> String {
    let canonical = canonical_json(value).expect("audit payload canonicalizes");
    let digest = Sha256::digest(canonical.as_bytes());
    format!("sha256:{}", hex::encode(digest))
}

fn stable_hash_suffix(value: &Value) -> String {
    stable_hash(value)
        .strip_prefix("sha256:")
        .expect("stable hash has prefix")
        .chars()
        .take(24)
        .collect()
}
