use serde::Serialize;

use crate::types::{Decision, ReasonCode};

#[derive(Clone, Debug)]
pub(crate) struct AuditSubject {
    pub lease_id: Option<String>,
    pub command_id: Option<String>,
    pub robot_id: Option<String>,
    pub edge_agent_id: Option<String>,
    pub mission_id: Option<String>,
    pub observed_at_unix_ms: i64,
}

#[derive(Clone, Debug, Serialize)]
pub struct AuditEvent {
    pub event_type: String,
    pub decision: Decision,
    pub reason_code: ReasonCode,
    pub lease_id: Option<String>,
    pub command_id: Option<String>,
    pub robot_id: Option<String>,
    pub edge_agent_id: Option<String>,
    pub mission_id: Option<String>,
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
        Self {
            event_type,
            decision,
            reason_code,
            lease_id: subject.lease_id,
            command_id: subject.command_id,
            robot_id: subject.robot_id,
            edge_agent_id: subject.edge_agent_id,
            mission_id: subject.mission_id,
            observed_at_unix_ms: subject.observed_at_unix_ms,
            summary,
        }
    }
}
