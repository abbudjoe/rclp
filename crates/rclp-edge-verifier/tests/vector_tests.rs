use std::collections::HashSet;
use std::fs;
use std::path::Path;

use hmac::{Hmac, Mac};
use rclp_edge_verifier::canonical_json::canonical_json;
use rclp_edge_verifier::{
    verify_json_value, CapabilityConstraintRequirement, CapabilityLeaseClaims, EdgeCommand,
    ReplayCache, TrustedVerifierContext,
};
use serde::Deserialize;
use serde::Serialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

type HmacSha256 = Hmac<Sha256>;

#[derive(Clone, Debug, Default)]
struct TestReplayCache {
    seen_nonces: HashSet<String>,
}

impl TestReplayCache {
    fn with_seen<I, S>(nonces: I) -> Self
    where
        I: IntoIterator<Item = S>,
        S: Into<String>,
    {
        Self {
            seen_nonces: nonces.into_iter().map(Into::into).collect(),
        }
    }
}

impl ReplayCache for TestReplayCache {
    fn consume_nonce(&mut self, nonce: &str) -> bool {
        self.seen_nonces.insert(nonce.to_string())
    }
}

#[derive(Debug, Deserialize)]
struct Vector {
    name: String,
    description: String,
    now_unix_ms: i64,
    trusted_context: TrustedVerifierContext,
    seen_nonces: Vec<String>,
    input: Value,
    expected: Expected,
}

#[derive(Debug, Deserialize)]
struct Expected {
    decision: String,
    reason_code: String,
}

#[test]
fn edge_verifier_vectors_match_expected_decisions() {
    let vector_dir =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../tests/vectors/edge_verifier");
    let mut paths = fs::read_dir(&vector_dir)
        .unwrap_or_else(|error| panic!("failed to read {}: {error}", vector_dir.display()))
        .map(|entry| entry.expect("failed to read vector directory entry").path())
        .filter(|path| path.extension().is_some_and(|ext| ext == "json"))
        .collect::<Vec<_>>();
    paths.sort();
    assert!(!paths.is_empty(), "expected edge verifier JSON vectors");

    for path in paths {
        let raw = fs::read_to_string(&path)
            .unwrap_or_else(|error| panic!("failed to read {}: {error}", path.display()));
        let vector: Vector = serde_json::from_str(&raw)
            .unwrap_or_else(|error| panic!("failed to parse {}: {error}", path.display()));
        assert!(
            !vector.description.trim().is_empty(),
            "{} must describe its scenario",
            vector.name
        );

        assert_eq!(
            vector.trusted_context.now_unix_ms, vector.now_unix_ms,
            "{} trusted context time must match vector metadata",
            vector.name
        );
        let input = vector.input;
        let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

        let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

        assert_eq!(
            decision.decision.as_str(),
            vector.expected.decision,
            "{} decision mismatch",
            vector.name
        );
        assert_eq!(
            decision.reason_code.as_str(),
            vector.expected.reason_code,
            "{} reason mismatch",
            vector.name
        );
        assert_eq!(
            decision.audit_event.reason_code.as_str(),
            vector.expected.reason_code,
            "{} audit reason mismatch",
            vector.name
        );
    }
}

#[test]
fn trusted_verifier_context_redacts_hmac_secrets() {
    let vector = load_vector("valid_remote_assist_lease");

    let debug_output = format!("{:?}", vector.trusted_context);
    assert!(!debug_output.contains("command-dev-test-secret"));
    assert!(!debug_output.contains("dev-test-secret"));
    assert!(!debug_output.contains("state-dev-test-secret"));
    assert!(debug_output.contains("<redacted>"));

    let serialized =
        serde_json::to_value(&vector.trusted_context).expect("trusted context serializes");
    assert!(serialized.get("command_hmac_secret").is_none());
    assert!(serialized.get("dev_hmac_secret").is_none());
    assert!(serialized.get("state_hmac_secret").is_none());
    assert_eq!(
        serialized.get("audit_chain_head").and_then(Value::as_str),
        Some("sha256:trusted-dev-audit-chain-head")
    );
}

#[test]
fn malformed_json_audit_event_binds_audit_chain_head() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut replay_cache = TestReplayCache::default();

    let decision = verify_json_value(
        json!({"not": "a verification input"}),
        &vector.trusted_context,
        &mut replay_cache,
    );

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
    assert_eq!(
        decision.audit_event.previous_audit_hash.as_deref(),
        Some("sha256:trusted-dev-audit-chain-head")
    );
}

#[test]
fn trusted_context_rejects_malformed_audit_chain_head_on_load() {
    let mut trusted_context =
        load_vector_value("valid_remote_assist_lease")["trusted_context"].clone();
    trusted_context["audit_chain_head"] = Value::from("");

    let error = serde_json::from_value::<TrustedVerifierContext>(trusted_context)
        .expect_err("empty audit_chain_head must not deserialize into trusted context");

    assert!(error.to_string().contains("audit_chain_head"));
}

#[test]
fn replay_cache_rejects_second_use_of_same_lease_nonce() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let first = verify_json_value(input.clone(), &vector.trusted_context, &mut replay_cache);
    assert_eq!(first.decision.as_str(), "allow");
    assert_eq!(first.reason_code.as_str(), "ALLOW");

    resign_command_value(
        &mut input,
        "cmd-valid-remote-assist-second",
        "cmd-nonce-valid-remote-assist-second",
        &vector.trusted_context.command_hmac_secret,
    );
    let second = verify_json_value(input, &vector.trusted_context, &mut replay_cache);
    assert_eq!(second.decision.as_str(), "deny");
    assert_eq!(second.reason_code.as_str(), "DENY_REPLAYED_NONCE");
}

#[test]
fn replay_cache_consumes_nonce_on_degrade_decision() {
    let vector = load_vector("network_degrade_denies_or_revokes");
    let mut input = vector.input;
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let first = verify_json_value(input.clone(), &vector.trusted_context, &mut replay_cache);
    assert_eq!(first.decision.as_str(), "degrade");
    assert_eq!(first.reason_code.as_str(), "DEGRADE_NETWORK_POLICY");

    resign_command_value(
        &mut input,
        "cmd-network-degrade-second",
        "cmd-nonce-network-degrade-second",
        &vector.trusted_context.command_hmac_secret,
    );
    let second = verify_json_value(input, &vector.trusted_context, &mut replay_cache);
    assert_eq!(second.decision.as_str(), "deny");
    assert_eq!(second.reason_code.as_str(), "DENY_REPLAYED_NONCE");
}

#[test]
fn replay_cache_rejects_second_use_of_same_signed_command() {
    let vector = load_vector("valid_remote_assist_lease");
    let input = vector.input;
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let first = verify_json_value(input.clone(), &vector.trusted_context, &mut replay_cache);
    assert_eq!(first.decision.as_str(), "allow");
    assert_eq!(first.reason_code.as_str(), "ALLOW");

    let second = verify_json_value(input, &vector.trusted_context, &mut replay_cache);
    assert_eq!(second.decision.as_str(), "deny");
    assert_eq!(second.reason_code.as_str(), "DENY_REPLAYED_COMMAND");
}

#[test]
fn hmac_valid_unsupported_capability_is_rejected_by_local_scope() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["lease"]["claims"]["lease_id"] = Value::from("lease-unsupported-capability");
    input["lease"]["claims"]["nonce"] = Value::from("nonce-unsupported-capability");
    input["lease"]["claims"]["capability"] = Value::from("forklift_override");
    input["lease"]["claims"]["constraints"] = Value::Object(Default::default());
    input["command"]["capability"] = Value::from("forklift_override");
    input["command"]["command_id"] = Value::from("cmd-unsupported-capability");
    input["command"]["command_nonce"] = Value::from("cmd-nonce-unsupported-capability");
    input["command"]["signature"] = Value::from(sign_command(
        &serde_json::from_value(input["command"].clone()).expect("command is well formed"),
        &vector.trusted_context.command_hmac_secret,
    ));
    let claims: CapabilityLeaseClaims =
        serde_json::from_value(input["lease"]["claims"].clone()).expect("claims are well formed");
    input["lease"]["signature"] = Value::from(sign_claims(
        &claims,
        &vector.trusted_context.dev_hmac_secret,
    ));
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_CAPABILITY_NOT_GRANTED");
}

#[test]
fn accepted_non_remote_capability_requires_declared_constraints() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    let mut trusted_context = vector.trusted_context;
    trusted_context
        .accepted_capabilities
        .push("mission_continue".to_string());
    trusted_context.issuer_capability_scopes[0]
        .capabilities
        .push("mission_continue".to_string());
    trusted_context
        .capability_constraint_requirements
        .push(CapabilityConstraintRequirement {
            capability: "mission_continue".to_string(),
            require_geofence_id: true,
            require_network_thresholds: false,
            require_fallback_on_degrade: false,
            require_max_speed_mps: true,
        });
    input["lease"]["claims"]["lease_id"] = Value::from("lease-empty-mission-continue");
    input["lease"]["claims"]["nonce"] = Value::from("nonce-empty-mission-continue");
    input["lease"]["claims"]["capability"] = Value::from("mission_continue");
    input["lease"]["claims"]["constraints"] = Value::Object(Default::default());
    input["command"]["capability"] = Value::from("mission_continue");
    input["command"]["command_id"] = Value::from("cmd-empty-mission-continue");
    input["command"]["command_nonce"] = Value::from("cmd-nonce-empty-mission-continue");
    input["command"]["signature"] = Value::from(sign_command(
        &serde_json::from_value(input["command"].clone()).expect("command is well formed"),
        &trusted_context.command_hmac_secret,
    ));
    let claims: CapabilityLeaseClaims =
        serde_json::from_value(input["lease"]["claims"].clone()).expect("claims are well formed");
    input["lease"]["signature"] =
        Value::from(sign_claims(&claims, &trusted_context.dev_hmac_secret));
    let mut replay_cache = TestReplayCache::default();

    let decision = verify_json_value(input, &trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
}

#[test]
fn authenticated_command_actor_mismatch_is_rejected_before_lease_checks() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["command"]["authenticated_agent_id"] = Value::from("fleet-agent:other");
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_COMMAND_AUTHENTICATED_AGENT_MISMATCH"
    );
}

#[test]
fn authority_decisions_carry_audit_commit_integrity_fields() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let decision = verify_json_value(vector.input, &vector.trusted_context, &mut replay_cache);
    let audit_event = &decision.audit_event;

    assert_eq!(audit_event.message_type, "audit_commit");
    assert_eq!(audit_event.protocol_version, "0.0.1-draft");
    assert!(audit_event.authority_relevant);
    assert!(audit_event.audit_id.starts_with("audit_"));
    assert!(audit_event.message_id.starts_with("msg_"));
    assert_eq!(audit_event.created_at, audit_event.created_at_unix_ms);
    assert_eq!(audit_event.payload_hash, stable_hash(&audit_event.payload));
    assert_eq!(audit_event.integrity_profile, "rclp-dev-sha256-v1");
    assert_eq!(
        audit_event.policy_id.as_deref(),
        Some("remote-assist-authority-v0")
    );
    assert_eq!(
        audit_event.policy_digest.as_deref(),
        Some("sha256:remote-assist-authority-v0-test-digest")
    );
    assert_eq!(
        audit_event.previous_audit_hash.as_deref(),
        Some("sha256:trusted-dev-audit-chain-head")
    );
    let proof_payload = json!({
        "audit_id": &audit_event.audit_id,
        "message_id": &audit_event.message_id,
        "message_type": &audit_event.message_type,
        "protocol_version": &audit_event.protocol_version,
        "correlation_id": &audit_event.correlation_id,
        "event_type": &audit_event.event_type,
        "actor_id": &audit_event.actor_id,
        "decision": &audit_event.decision,
        "reason_code": &audit_event.reason_code,
        "lease_id": &audit_event.lease_id,
        "command_id": &audit_event.command_id,
        "robot_id": &audit_event.robot_id,
        "edge_agent_id": &audit_event.edge_agent_id,
        "mission_id": &audit_event.mission_id,
        "summary": &audit_event.summary,
        "payload_hash": &audit_event.payload_hash,
        "authority_relevant": audit_event.authority_relevant,
        "integrity_profile": &audit_event.integrity_profile,
        "policy_id": &audit_event.policy_id,
        "policy_digest": &audit_event.policy_digest,
        "previous_audit_hash": &audit_event.previous_audit_hash,
        "state_refs": &audit_event.state_refs,
        "related_message_ids": &audit_event.related_message_ids,
        "created_at": audit_event.created_at,
        "created_at_unix_ms": audit_event.created_at_unix_ms,
        "observed_at_unix_ms": audit_event.observed_at_unix_ms,
    });
    assert_eq!(audit_event.integrity_proof, stable_hash(&proof_payload));
    let tampered_proof_payload = json!({
        "audit_id": &audit_event.audit_id,
        "message_id": &audit_event.message_id,
        "message_type": &audit_event.message_type,
        "protocol_version": &audit_event.protocol_version,
        "correlation_id": "tampered",
        "event_type": &audit_event.event_type,
        "actor_id": &audit_event.actor_id,
        "decision": &audit_event.decision,
        "reason_code": &audit_event.reason_code,
        "lease_id": &audit_event.lease_id,
        "command_id": &audit_event.command_id,
        "robot_id": &audit_event.robot_id,
        "edge_agent_id": &audit_event.edge_agent_id,
        "mission_id": &audit_event.mission_id,
        "summary": &audit_event.summary,
        "payload_hash": &audit_event.payload_hash,
        "authority_relevant": audit_event.authority_relevant,
        "integrity_profile": &audit_event.integrity_profile,
        "policy_id": &audit_event.policy_id,
        "policy_digest": &audit_event.policy_digest,
        "previous_audit_hash": &audit_event.previous_audit_hash,
        "state_refs": &audit_event.state_refs,
        "related_message_ids": &audit_event.related_message_ids,
        "created_at": audit_event.created_at,
        "created_at_unix_ms": audit_event.created_at_unix_ms,
        "observed_at_unix_ms": audit_event.observed_at_unix_ms,
    });
    assert_ne!(
        audit_event.integrity_proof,
        stable_hash(&tampered_proof_payload)
    );
    let decision_tampered_proof_payload = json!({
        "audit_id": &audit_event.audit_id,
        "message_id": &audit_event.message_id,
        "message_type": &audit_event.message_type,
        "protocol_version": &audit_event.protocol_version,
        "correlation_id": &audit_event.correlation_id,
        "event_type": &audit_event.event_type,
        "actor_id": &audit_event.actor_id,
        "decision": "Deny",
        "reason_code": &audit_event.reason_code,
        "lease_id": &audit_event.lease_id,
        "command_id": &audit_event.command_id,
        "robot_id": &audit_event.robot_id,
        "edge_agent_id": &audit_event.edge_agent_id,
        "mission_id": &audit_event.mission_id,
        "summary": &audit_event.summary,
        "payload_hash": &audit_event.payload_hash,
        "authority_relevant": audit_event.authority_relevant,
        "integrity_profile": &audit_event.integrity_profile,
        "policy_id": &audit_event.policy_id,
        "policy_digest": &audit_event.policy_digest,
        "previous_audit_hash": &audit_event.previous_audit_hash,
        "state_refs": &audit_event.state_refs,
        "related_message_ids": &audit_event.related_message_ids,
        "created_at": audit_event.created_at,
        "created_at_unix_ms": audit_event.created_at_unix_ms,
        "observed_at_unix_ms": audit_event.observed_at_unix_ms,
    });
    assert_ne!(
        audit_event.integrity_proof,
        stable_hash(&decision_tampered_proof_payload)
    );
    let previous_hash_tampered_proof_payload = json!({
        "audit_id": &audit_event.audit_id,
        "message_id": &audit_event.message_id,
        "message_type": &audit_event.message_type,
        "protocol_version": &audit_event.protocol_version,
        "correlation_id": &audit_event.correlation_id,
        "event_type": &audit_event.event_type,
        "actor_id": &audit_event.actor_id,
        "decision": &audit_event.decision,
        "reason_code": &audit_event.reason_code,
        "lease_id": &audit_event.lease_id,
        "command_id": &audit_event.command_id,
        "robot_id": &audit_event.robot_id,
        "edge_agent_id": &audit_event.edge_agent_id,
        "mission_id": &audit_event.mission_id,
        "summary": &audit_event.summary,
        "payload_hash": &audit_event.payload_hash,
        "authority_relevant": audit_event.authority_relevant,
        "integrity_profile": &audit_event.integrity_profile,
        "policy_id": &audit_event.policy_id,
        "policy_digest": &audit_event.policy_digest,
        "previous_audit_hash": "sha256:tampered-chain-head",
        "state_refs": &audit_event.state_refs,
        "related_message_ids": &audit_event.related_message_ids,
        "created_at": audit_event.created_at,
        "created_at_unix_ms": audit_event.created_at_unix_ms,
        "observed_at_unix_ms": audit_event.observed_at_unix_ms,
    });
    assert_ne!(
        audit_event.integrity_proof,
        stable_hash(&previous_hash_tampered_proof_payload)
    );
    assert!(audit_event.payload.get("reason_code").is_some());
    assert!(audit_event
        .related_message_ids
        .iter()
        .any(|id| id == "lease-valid-remote-assist"));
}

#[test]
fn policy_digest_downgrade_is_rejected_before_authorization() {
    let vector = load_vector("valid_remote_assist_lease");
    let input = vector.input;
    let mut trusted_context = vector.trusted_context;
    trusted_context.policy_digest = "sha256:downgraded-policy".to_string();
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_POLICY_DIGEST_NOT_ACCEPTED"
    );
    assert_eq!(
        decision.audit_event.policy_digest.as_deref(),
        Some("sha256:downgraded-policy")
    );
}

#[test]
fn accepted_policy_digest_with_mismatched_policy_id_is_rejected() {
    let vector = load_vector("valid_remote_assist_lease");
    let input = vector.input;
    let mut trusted_context = vector.trusted_context;
    trusted_context.policy_id = "remote-assist-authority-downgraded".to_string();
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_POLICY_DIGEST_NOT_ACCEPTED"
    );
    assert_eq!(
        decision.audit_event.policy_id.as_deref(),
        Some("remote-assist-authority-downgraded")
    );
}

#[test]
fn issuer_capability_scope_mismatch_is_rejected() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut trusted_context = vector.trusted_context;
    trusted_context.issuer_capability_scopes[0].capabilities = vec!["mission_continue".to_string()];
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let decision = verify_json_value(vector.input, &trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_CAPABILITY_NOT_GRANTED");
}

#[test]
fn forged_local_context_without_matching_state_signature_is_rejected() {
    let denied_vector = load_vector("network_partition_rejected");
    let valid_vector = load_vector("valid_remote_assist_lease");
    let mut input = denied_vector.input;
    let mut replay_cache = TestReplayCache::with_seen(denied_vector.seen_nonces);

    input["local_context"]["network_state"] =
        valid_vector.input["local_context"]["network_state"].clone();
    input["local_context"]["geofence_state"] =
        valid_vector.input["local_context"]["geofence_state"].clone();
    input["local_context"]["observed_at_unix_ms"] =
        valid_vector.input["local_context"]["observed_at_unix_ms"].clone();

    let decision = verify_json_value(input, &denied_vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_INVALID_STATE_SIGNATURE"
    );
}

#[test]
fn overflowing_state_freshness_window_fails_closed() {
    let vector = load_vector("valid_remote_assist_lease");
    let input = vector.input;
    let mut trusted_context = vector.trusted_context;
    trusted_context.max_state_age_ms = i64::MAX;
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
}

#[test]
fn dev_hmac_profile_rejects_multi_principal_trust_sets() {
    let vector = load_vector("valid_remote_assist_lease");
    let input = vector.input;

    let mut multi_issuer_context = vector.trusted_context.clone();
    multi_issuer_context
        .trusted_issuer_ids
        .push("issuer:second".to_string());
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces.clone());
    let decision = verify_json_value(input.clone(), &multi_issuer_context, &mut replay_cache);
    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");

    let mut multi_command_context = vector.trusted_context.clone();
    multi_command_context
        .trusted_command_agent_ids
        .push("fleet-agent:second".to_string());
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces.clone());
    let decision = verify_json_value(input.clone(), &multi_command_context, &mut replay_cache);
    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");

    let mut multi_state_context = vector.trusted_context;
    multi_state_context
        .trusted_state_edge_ids
        .push("edge-agent:second".to_string());
    let mut replay_cache = TestReplayCache::with_seen(vector.seen_nonces);
    let decision = verify_json_value(input, &multi_state_context, &mut replay_cache);
    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
}

fn load_vector(name: &str) -> Vector {
    serde_json::from_value(load_vector_value(name))
        .unwrap_or_else(|error| panic!("failed to parse vector {name}: {error}"))
}

fn load_vector_value(name: &str) -> Value {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/vectors/edge_verifier")
        .join(format!("{name}.json"));
    let raw = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("failed to read {}: {error}", path.display()));
    serde_json::from_str(&raw)
        .unwrap_or_else(|error| panic!("failed to parse {}: {error}", path.display()))
}

fn sign_claims(claims: &CapabilityLeaseClaims, secret: &str) -> String {
    let payload = canonical_json(claims).expect("claims canonicalize");
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).expect("HMAC accepts secret bytes");
    mac.update(payload.as_bytes());
    hex::encode(mac.finalize().into_bytes())
}

fn stable_hash(value: &Value) -> String {
    let canonical = canonical_json(value).expect("value canonicalizes");
    let digest = Sha256::digest(canonical.as_bytes());
    format!("sha256:{}", hex::encode(digest))
}

fn resign_command_value(input: &mut Value, command_id: &str, command_nonce: &str, secret: &str) {
    input["command"]["command_id"] = Value::from(command_id);
    input["command"]["command_nonce"] = Value::from(command_nonce);
    let command: EdgeCommand =
        serde_json::from_value(input["command"].clone()).expect("command is well formed");
    input["command"]["signature"] = Value::from(sign_command(&command, secret));
}

fn sign_command(command: &EdgeCommand, secret: &str) -> String {
    let payload = SignedCommand {
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
    let payload = canonical_json(&payload).expect("command canonicalizes");
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).expect("HMAC accepts secret bytes");
    mac.update(payload.as_bytes());
    hex::encode(mac.finalize().into_bytes())
}

#[derive(Serialize)]
struct SignedCommand<'a> {
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
