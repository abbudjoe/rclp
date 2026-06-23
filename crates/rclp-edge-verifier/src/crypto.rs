use hmac::{Hmac, Mac};
use serde::Serialize;
use sha2::Sha256;

use crate::canonical_json::canonical_json;
use crate::errors::VerifierError;
use crate::types::{CapabilityLeaseClaims, EdgeCommand, GeofenceState, LocalContext, NetworkState};

pub const DEV_HMAC_SHA256_ALG: &str = "RCLP-DEV-HMAC-SHA256";

type HmacSha256 = Hmac<Sha256>;

pub fn verify_dev_hmac_sha256(
    claims: &CapabilityLeaseClaims,
    signature_hex: &str,
    secret: &str,
) -> Result<(), VerifierError> {
    verify_hmac_sha256(claims, signature_hex, secret)
}

pub fn verify_dev_hmac_sha256_local_context(
    context: &LocalContext,
    signature_hex: &str,
    secret: &str,
) -> Result<(), VerifierError> {
    let payload = SignedLocalContext {
        robot_id: &context.robot_id,
        edge_agent_id: &context.edge_agent_id,
        authenticated_edge_agent_id: context.authenticated_edge_agent_id.as_deref().unwrap_or(""),
        mission_id: &context.mission_id,
        observed_at_unix_ms: context.observed_at_unix_ms,
        network_state: &context.network_state,
        geofence_state: &context.geofence_state,
    };
    verify_hmac_sha256(&payload, signature_hex, secret)
}

pub fn verify_dev_hmac_sha256_command(
    command: &EdgeCommand,
    signature_hex: &str,
    secret: &str,
) -> Result<(), VerifierError> {
    let payload = SignedEdgeCommand {
        command_id: &command.command_id,
        agent_id: &command.agent_id,
        authenticated_agent_id: &command.authenticated_agent_id,
        edge_agent_id: &command.edge_agent_id,
        robot_id: &command.robot_id,
        mission_id: &command.mission_id,
        capability: &command.capability,
        command_nonce: &command.command_nonce,
        created_at_unix_ms: command.created_at_unix_ms,
        max_speed_mps: command.max_speed_mps,
    };
    verify_hmac_sha256(&payload, signature_hex, secret)
}

fn verify_hmac_sha256<T: Serialize>(
    payload: &T,
    signature_hex: &str,
    secret: &str,
) -> Result<(), VerifierError> {
    let signature = hex::decode(signature_hex)?;
    let payload = canonical_json(payload)?;
    let mut mac =
        HmacSha256::new_from_slice(secret.as_bytes()).map_err(|_| VerifierError::InvalidMac)?;
    mac.update(payload.as_bytes());
    mac.verify_slice(&signature)
        .map_err(|_| VerifierError::InvalidMac)
}

#[derive(Serialize)]
struct SignedLocalContext<'a> {
    robot_id: &'a str,
    edge_agent_id: &'a str,
    authenticated_edge_agent_id: &'a str,
    mission_id: &'a str,
    observed_at_unix_ms: i64,
    network_state: &'a NetworkState,
    geofence_state: &'a GeofenceState,
}

#[derive(Serialize)]
struct SignedEdgeCommand<'a> {
    command_id: &'a str,
    agent_id: &'a str,
    authenticated_agent_id: &'a str,
    edge_agent_id: &'a str,
    robot_id: &'a str,
    mission_id: &'a str,
    capability: &'a str,
    command_nonce: &'a str,
    created_at_unix_ms: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_speed_mps: Option<f64>,
}
