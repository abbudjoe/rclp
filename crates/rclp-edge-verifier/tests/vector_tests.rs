use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};

use hmac::{Hmac, Mac};
use rclp_edge_verifier::canonical_json::canonical_json;
use rclp_edge_verifier::{
    verify_json_value, CapabilityConstraintRequirement, CapabilityLeaseClaims, EdgeCommand,
    FileReplayCache, GeofenceState, LocalContext, NetworkState, ReplayCache, ReplayConsumeResult,
    TrustedVerifierContext, VerificationDecision,
};
use serde::Deserialize;
use serde::Serialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

type HmacSha256 = Hmac<Sha256>;

static NEXT_REPLAY_CACHE_ID: AtomicUsize = AtomicUsize::new(1);

fn replay_cache_path(label: &str) -> PathBuf {
    let id = NEXT_REPLAY_CACHE_ID.fetch_add(1, Ordering::Relaxed);
    std::env::temp_dir().join(format!(
        "rclp-edge-verifier-{label}-{}-{id}",
        std::process::id()
    ))
}

fn replay_cache_with_seen<I, S>(nonces: I) -> FileReplayCache
where
    I: IntoIterator<Item = S>,
    S: Into<String>,
{
    let mut cache = FileReplayCache::new(replay_cache_path("durable"))
        .expect("test replay cache can be created");
    for nonce in nonces {
        assert!(cache.consume_nonce(&nonce.into()));
    }
    cache
}

fn fresh_replay_cache() -> FileReplayCache {
    replay_cache_with_seen(Vec::<String>::new())
}

#[derive(Default)]
struct NonDurableReplayCache {
    seen_nonces: HashSet<String>,
}

impl ReplayCache for NonDurableReplayCache {
    fn consume_nonce(&mut self, nonce: &str) -> bool {
        self.seen_nonces.insert(nonce.to_string())
    }

    fn consume_nonces(&mut self, nonces: &[String]) -> ReplayConsumeResult {
        let mut staged = self.seen_nonces.clone();
        for (index, nonce) in nonces.iter().enumerate() {
            if !staged.insert(nonce.clone()) {
                return ReplayConsumeResult::Rejected { index };
            }
        }
        self.seen_nonces = staged;
        ReplayConsumeResult::Consumed
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
        let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

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
fn verifier_rejects_non_durable_replay_cache_before_authority_decision() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut replay_cache = NonDurableReplayCache::default();

    let decision = verify_json_value(vector.input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
    assert!(decision.audit_event.lease_id.is_none());
    assert!(decision.audit_event.command_id.is_none());
    assert!(decision
        .audit_event
        .payload
        .get("summary")
        .and_then(Value::as_str)
        .is_some_and(|summary| summary.contains("durable replay cache is required")));
}

#[test]
fn file_replay_cache_preserves_replay_state_after_verifier_recreation() {
    let vector = load_vector("valid_remote_assist_lease");
    let cache_path = replay_cache_path("restart");
    let mut first_cache =
        FileReplayCache::new(&cache_path).expect("first replay cache can be created");
    let first = verify_json_value(
        vector.input.clone(),
        &vector.trusted_context,
        &mut first_cache,
    );
    assert_eq!(first.decision.as_str(), "allow");

    let mut restarted_cache =
        FileReplayCache::new(&cache_path).expect("restarted replay cache can be created");
    let second = verify_json_value(vector.input, &vector.trusted_context, &mut restarted_cache);

    assert_eq!(second.decision.as_str(), "deny");
    assert_eq!(second.reason_code.as_str(), "DENY_REPLAYED_COMMAND");
}

#[test]
fn file_replay_cache_preserves_lease_nonce_after_verifier_recreation() {
    let vector = load_vector("valid_remote_assist_lease");
    let cache_path = replay_cache_path("lease-restart");
    let mut first_cache =
        FileReplayCache::new(&cache_path).expect("first replay cache can be created");
    let first = verify_json_value(
        vector.input.clone(),
        &vector.trusted_context,
        &mut first_cache,
    );
    assert_eq!(first.decision.as_str(), "allow");

    let mut restarted_input = vector.input;
    resign_command_value(
        &mut restarted_input,
        "cmd-valid-remote-assist-after-restart",
        "cmd-nonce-valid-remote-assist-after-restart",
        &vector.trusted_context.command_hmac_secret,
    );
    let mut restarted_cache =
        FileReplayCache::new(&cache_path).expect("restarted replay cache can be created");
    let second = verify_json_value(
        restarted_input,
        &vector.trusted_context,
        &mut restarted_cache,
    );

    assert_eq!(second.decision.as_str(), "deny");
    assert_eq!(second.reason_code.as_str(), "DENY_REPLAYED_NONCE");
}

#[test]
fn file_replay_cache_writes_marker_and_rejects_duplicate_nonce() {
    let nonce = "nonce-durable-marker";
    let mut cache = FileReplayCache::new(replay_cache_path("durable-marker"))
        .expect("file replay cache can be created");

    assert!(cache.consume_nonce(nonce));
    let digest = Sha256::digest(nonce.as_bytes());
    let marker_path = cache.store_dir().join(hex::encode(digest));
    let marker = fs::read_to_string(marker_path).expect("nonce marker is committed");

    assert_eq!(marker, "nonce-durable-marker\n");
    assert!(!cache.consume_nonce(nonce));
}

#[test]
fn file_replay_cache_creates_nested_fresh_store_as_durable_shared() {
    let cache_path = replay_cache_path("fresh-parent")
        .join("nested")
        .join("store");
    let mut cache =
        FileReplayCache::new(&cache_path).expect("nested fresh replay cache can be created");

    assert!(cache.store_dir().is_dir());
    assert!(cache.durability().is_durable());
    assert!(cache.consume_nonce("nonce-nested-fresh-store"));
}

#[test]
fn lease_ttl_exact_policy_maximum_is_allowed() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut replay_cache = fresh_replay_cache();

    let decision = verify_json_value(vector.input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "allow");
    assert_eq!(decision.reason_code.as_str(), "ALLOW");
}

#[test]
fn lease_ttl_max_plus_one_is_rejected() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    let issued_at = input["lease"]["claims"]["issued_at"]
        .as_i64()
        .expect("vector lease has issued_at");
    input["lease"]["claims"]["lease_id"] = Value::from("lease-ttl-max-plus-one");
    input["lease"]["claims"]["nonce"] = Value::from("nonce-ttl-max-plus-one");
    input["lease"]["claims"]["expires_at"] =
        Value::from(issued_at + vector.trusted_context.max_lease_ttl_ms + 1);
    let claims: CapabilityLeaseClaims =
        serde_json::from_value(input["lease"]["claims"].clone()).expect("claims are well formed");
    input["lease"]["signature"] = Value::from(sign_claims(
        &claims,
        &vector.trusted_context.dev_hmac_secret,
    ));
    let mut replay_cache = fresh_replay_cache();

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_TTL_TOO_LONG");
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
    let mut replay_cache = fresh_replay_cache();

    let decision = verify_json_value(
        json!({"not": "a verification input"}),
        &vector.trusted_context,
        &mut replay_cache,
    );

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
    assert!(decision.audit_event.lease_id.is_none());
    assert!(decision.audit_event.command_id.is_none());
    assert_eq!(
        decision.audit_event.previous_audit_hash.as_deref(),
        Some("sha256:trusted-dev-audit-chain-head")
    );
}

#[test]
fn malformed_json_audit_events_have_unique_identities() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut replay_cache = fresh_replay_cache();

    let first = verify_json_value(
        json!({"not": "a verification input"}),
        &vector.trusted_context,
        &mut replay_cache,
    );
    let second = verify_json_value(
        json!({"not": "a verification input"}),
        &vector.trusted_context,
        &mut replay_cache,
    );

    assert_ne!(first.audit_event.audit_id, second.audit_event.audit_id);
    assert_ne!(first.audit_event.message_id, second.audit_event.message_id);
    assert_ne!(
        first.audit_event.identity_nonce,
        second.audit_event.identity_nonce
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
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

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
fn replayed_lease_nonce_does_not_poison_fresh_command_replay_state() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let first = verify_json_value(input.clone(), &vector.trusted_context, &mut replay_cache);
    assert_eq!(first.decision.as_str(), "allow");
    assert_eq!(first.reason_code.as_str(), "ALLOW");

    resign_command_value(
        &mut input,
        "cmd-valid-remote-assist-lease-replay",
        "cmd-nonce-valid-remote-assist-lease-replay",
        &vector.trusted_context.command_hmac_secret,
    );
    let second = verify_json_value(input.clone(), &vector.trusted_context, &mut replay_cache);
    assert_eq!(second.decision.as_str(), "deny");
    assert_eq!(second.reason_code.as_str(), "DENY_REPLAYED_NONCE");

    let third = verify_json_value(input, &vector.trusted_context, &mut replay_cache);
    assert_eq!(third.decision.as_str(), "deny");
    assert_eq!(third.reason_code.as_str(), "DENY_REPLAYED_NONCE");
}

#[test]
fn replay_cache_consumes_nonce_on_degrade_decision() {
    let vector = load_vector("network_degrade_denies_or_revokes");
    let mut input = vector.input;
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

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
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

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
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

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
    let mut replay_cache = fresh_replay_cache();

    let decision = verify_json_value(input, &trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
}

#[test]
fn authenticated_command_actor_mismatch_is_rejected_before_lease_checks() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["command"]["authenticated_agent_id"] = Value::from("fleet-agent:other");
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_COMMAND_AUTHENTICATED_AGENT_MISMATCH"
    );
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
    assert!(decision.audit_event.lease_id.is_none());
    assert!(decision.audit_event.command_id.is_none());
    assert!(decision.audit_event.robot_id.is_none());
    assert_eq!(
        decision
            .audit_event
            .payload
            .get("claimed_command_id")
            .and_then(Value::as_str),
        Some("cmd-valid-remote-assist")
    );
}

#[test]
fn command_payload_tamper_invalidates_command_signature() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["command"]["payload"]["tampered_after_signing"] = Value::Bool(true);
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_INVALID_COMMAND_SIGNATURE"
    );
}

#[test]
fn speed_limited_payload_accepts_supported_speed_aliases() {
    for (payload, command_id) in [
        (json!({"max_speed_mps": 0.25}), "cmd-speed-schema-max"),
        (json!({"speed_mps": 0.25}), "cmd-speed-schema-speed"),
        (
            json!({"max_speed_mps": 0.25, "speed_mps": 0.25}),
            "cmd-speed-schema-both",
        ),
    ] {
        let decision = verify_resigned_speed_payload(payload, command_id);

        assert_eq!(decision.decision.as_str(), "allow");
        assert_eq!(decision.reason_code.as_str(), "ALLOW");
    }
}

#[test]
fn speed_limited_payload_rejects_unknown_motion_fields() {
    for (payload, command_id) in [
        (
            json!({"max_speed_mps": 0.25, "motion": {"max_speed_mps": 99.0}}),
            "cmd-speed-schema-motion",
        ),
        (
            json!({"max_speed_mps": 0.25, "trajectory": [{"speed_mps": 99.0}]}),
            "cmd-speed-schema-trajectory",
        ),
        (
            json!({"max_speed_mps": 0.25, "vendor_motion": {"speed_mps": 99.0}}),
            "cmd-speed-schema-vendor",
        ),
    ] {
        let decision = verify_resigned_speed_payload(payload, command_id);

        assert_eq!(decision.decision.as_str(), "deny");
        assert_eq!(decision.reason_code.as_str(), "DENY_COMMAND_CONSTRAINT");
    }
}

#[test]
fn no_speed_payload_allows_empty_payload() {
    let decision = verify_resigned_no_speed_payload(json!({}), "cmd-no-speed-empty");

    assert_eq!(decision.decision.as_str(), "allow");
    assert_eq!(decision.reason_code.as_str(), "ALLOW");
}

#[test]
fn no_speed_payload_rejects_nonempty_uninterpreted_fields() {
    for (payload, command_id) in [
        (
            json!({"intent": "start_remote_assist"}),
            "cmd-no-speed-intent",
        ),
        (json!({"max_speed_mps": 0.25}), "cmd-no-speed-max"),
        (json!({"speed_mps": 0.25}), "cmd-no-speed-speed"),
    ] {
        let decision = verify_resigned_no_speed_payload(payload, command_id);

        assert_eq!(decision.decision.as_str(), "deny");
        assert_eq!(decision.reason_code.as_str(), "DENY_COMMAND_CONSTRAINT");
    }
}

#[test]
fn oversized_command_payload_is_rejected_before_hmac_canonicalization() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["command"]["payload"] = json!({"blob": "x".repeat(70_000)});
    input["command"]["signature"] = Value::from("00");
    let mut replay_cache = fresh_replay_cache();

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_COMMAND_SIGNED_MATERIAL_TOO_LARGE"
    );
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
}

#[test]
fn oversized_signed_command_field_is_rejected_before_hmac_canonicalization() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["command"]["command_id"] = Value::from("x".repeat(70_000));
    input["command"]["signature"] = Value::from("00");
    let mut replay_cache = fresh_replay_cache();

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_COMMAND_SIGNED_MATERIAL_TOO_LARGE"
    );
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
}

#[test]
fn deeply_nested_command_payload_is_rejected_before_hmac_canonicalization() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    let mut payload = json!({"speed_mps": 0.5});
    for _ in 0..40 {
        payload = json!([payload]);
    }
    input["command"]["payload"] = payload;
    input["command"]["signature"] = Value::from("00");
    let mut replay_cache = fresh_replay_cache();

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_COMMAND_SIGNED_MATERIAL_TOO_LARGE"
    );
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
}

#[test]
fn command_without_payload_is_malformed() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["command"]
        .as_object_mut()
        .expect("command is an object")
        .remove("payload");
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
    assert_eq!(decision.audit_event.event_type, "diagnostic");
}

#[test]
fn signed_lease_policy_digest_mismatch_is_rejected() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["lease"]["claims"]["policy_digest"] = Value::from("sha256:downgraded-policy");
    let claims: CapabilityLeaseClaims =
        serde_json::from_value(input["lease"]["claims"].clone()).expect("claims are well formed");
    input["lease"]["signature"] = Value::from(sign_claims(
        &claims,
        &vector.trusted_context.dev_hmac_secret,
    ));
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_POLICY_DIGEST_NOT_ACCEPTED"
    );
    assert_eq!(decision.audit_event.event_type, "command_rejected");
    assert!(decision.audit_event.authority_relevant);
    assert_eq!(
        decision.audit_event.lease_id.as_deref(),
        Some("lease-valid-remote-assist")
    );
    assert_eq!(
        decision.audit_event.command_id.as_deref(),
        Some("cmd-valid-remote-assist")
    );
    assert_eq!(decision.audit_event.robot_id.as_deref(), Some("rover-001"));
    assert_eq!(
        decision.audit_event.mission_id.as_deref(),
        Some("mission-001")
    );
    assert_eq!(
        decision.audit_event.payload["accepted_policy_id"].as_str(),
        Some("remote-assist-authority-v0")
    );
    assert_eq!(
        decision.audit_event.payload["accepted_policy_digest"].as_str(),
        Some("sha256:remote-assist-authority-v0-test-digest")
    );
    assert_eq!(
        decision.audit_event.payload["presented_policy_id"].as_str(),
        Some("remote-assist-authority-v0")
    );
    assert_eq!(
        decision.audit_event.payload["presented_policy_digest"].as_str(),
        Some("sha256:downgraded-policy")
    );
}

#[test]
fn pre_command_auth_policy_failure_is_diagnostic_non_authority() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["lease"]["claims"]["policy_digest"] = Value::from("sha256:downgraded-policy");
    input["command"]["signature"] = Value::Null;
    let claims: CapabilityLeaseClaims =
        serde_json::from_value(input["lease"]["claims"].clone()).expect("claims are well formed");
    input["lease"]["signature"] = Value::from(sign_claims(
        &claims,
        &vector.trusted_context.dev_hmac_secret,
    ));
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_POLICY_DIGEST_NOT_ACCEPTED"
    );
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
    assert!(decision.audit_event.lease_id.is_none());
    assert!(decision.audit_event.command_id.is_none());
    assert!(decision.audit_event.robot_id.is_none());
    assert_eq!(
        decision
            .audit_event
            .payload
            .get("claimed_command_id")
            .and_then(Value::as_str),
        Some("cmd-valid-remote-assist")
    );
}

#[test]
fn command_envelope_tamper_invalidates_command_signature() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["command"]["message_id"] = Value::from("msg-tampered-command-envelope");
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(
        decision.reason_code.as_str(),
        "DENY_INVALID_COMMAND_SIGNATURE"
    );
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
    assert!(decision.audit_event.command_id.is_none());
}

#[test]
fn lease_envelope_tamper_invalidates_lease_signature_after_command_auth() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["lease"]["claims"]["message_id"] = Value::from("msg-tampered-lease-envelope");
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_INVALID_SIGNATURE");
    assert_eq!(decision.audit_event.event_type, "command_rejected");
    assert!(decision.audit_event.authority_relevant);
    assert_eq!(
        decision.audit_event.command_id.as_deref(),
        Some("cmd-valid-remote-assist")
    );
    assert_eq!(
        decision.audit_event.payload["accepted_policy_id"].as_str(),
        Some("remote-assist-authority-v0")
    );
    assert_eq!(
        decision.audit_event.payload["accepted_policy_digest"].as_str(),
        Some("sha256:remote-assist-authority-v0-test-digest")
    );
    assert_eq!(
        decision.audit_event.payload["presented_policy_id"].as_str(),
        Some("remote-assist-authority-v0")
    );
    assert_eq!(
        decision.audit_event.payload["presented_policy_digest"].as_str(),
        Some("sha256:remote-assist-authority-v0-test-digest")
    );
}

#[test]
fn invalid_lease_after_command_auth_does_not_poison_command_replay_state() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut tampered = vector.input.clone();
    tampered["lease"]["claims"]["lease_id"] = Value::from("lease-tampered-before-authority");
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces.clone());

    let first = verify_json_value(tampered, &vector.trusted_context, &mut replay_cache);
    assert_eq!(first.decision.as_str(), "deny");
    assert_eq!(first.reason_code.as_str(), "DENY_INVALID_SIGNATURE");

    let second = verify_json_value(vector.input, &vector.trusted_context, &mut replay_cache);
    assert_eq!(second.decision.as_str(), "allow");
    assert_eq!(second.reason_code.as_str(), "ALLOW");
}

#[test]
fn unsupported_lease_envelope_before_command_auth_is_diagnostic() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["lease"]["claims"]["protocol_version"] = Value::from("999.0-unsupported");
    input["command"]["signature"] = Value::Null;
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
    assert_eq!(decision.audit_event.event_type, "diagnostic");
    assert!(!decision.audit_event.authority_relevant);
    assert!(decision.audit_event.lease_id.is_none());
    assert!(decision.audit_event.command_id.is_none());
}

#[test]
fn authority_decisions_carry_audit_commit_integrity_fields() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(vector.input, &vector.trusted_context, &mut replay_cache);
    let audit_event = &decision.audit_event;

    assert_eq!(audit_event.message_type, "audit_commit");
    assert_eq!(audit_event.protocol_version, "0.0.1-draft");
    assert!(audit_event.authority_relevant);
    assert!(audit_event.audit_id.starts_with("audit_"));
    assert!(audit_event.message_id.starts_with("msg_"));
    assert!(audit_event.event_sequence > 0);
    assert!(!audit_event.identity_nonce.is_empty());
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
        "event_sequence": audit_event.event_sequence,
        "identity_nonce": &audit_event.identity_nonce,
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
        "event_sequence": audit_event.event_sequence,
        "identity_nonce": &audit_event.identity_nonce,
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
        "event_sequence": audit_event.event_sequence,
        "identity_nonce": &audit_event.identity_nonce,
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
        "event_sequence": audit_event.event_sequence,
        "identity_nonce": &audit_event.identity_nonce,
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
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

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
    assert_eq!(decision.audit_event.event_type, "command_rejected");
    assert!(decision.audit_event.authority_relevant);
    assert_eq!(
        decision.audit_event.lease_id.as_deref(),
        Some("lease-valid-remote-assist")
    );
    assert_eq!(
        decision.audit_event.command_id.as_deref(),
        Some("cmd-valid-remote-assist")
    );
    assert_eq!(
        decision.audit_event.payload["accepted_policy_id"].as_str(),
        Some("remote-assist-authority-v0")
    );
    assert_eq!(
        decision.audit_event.payload["accepted_policy_digest"].as_str(),
        Some("sha256:downgraded-policy")
    );
    assert_eq!(
        decision.audit_event.payload["presented_policy_id"].as_str(),
        Some("remote-assist-authority-v0")
    );
    assert_eq!(
        decision.audit_event.payload["presented_policy_digest"].as_str(),
        Some("sha256:remote-assist-authority-v0-test-digest")
    );
}

#[test]
fn accepted_policy_digest_with_mismatched_policy_id_is_rejected() {
    let vector = load_vector("valid_remote_assist_lease");
    let input = vector.input;
    let mut trusted_context = vector.trusted_context;
    trusted_context.policy_id = "remote-assist-authority-downgraded".to_string();
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

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
    assert_eq!(decision.audit_event.event_type, "command_rejected");
    assert!(decision.audit_event.authority_relevant);
    assert_eq!(
        decision.audit_event.command_id.as_deref(),
        Some("cmd-valid-remote-assist")
    );
    assert_eq!(
        decision.audit_event.payload["accepted_policy_id"].as_str(),
        Some("remote-assist-authority-downgraded")
    );
    assert_eq!(
        decision.audit_event.payload["accepted_policy_digest"].as_str(),
        Some("sha256:remote-assist-authority-v0-test-digest")
    );
    assert_eq!(
        decision.audit_event.payload["presented_policy_id"].as_str(),
        Some("remote-assist-authority-v0")
    );
    assert_eq!(
        decision.audit_event.payload["presented_policy_digest"].as_str(),
        Some("sha256:remote-assist-authority-v0-test-digest")
    );
}

#[test]
fn issuer_capability_scope_mismatch_is_rejected() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut trusted_context = vector.trusted_context;
    trusted_context.issuer_capability_scopes[0].capabilities = vec!["mission_continue".to_string()];
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

    let decision = verify_json_value(vector.input, &trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_CAPABILITY_NOT_GRANTED");
}

#[test]
fn blank_geofence_ids_do_not_satisfy_required_geofence_constraint() {
    for geofence_id in ["", "   "] {
        let vector = load_vector("valid_remote_assist_lease");
        let mut input = vector.input;
        input["lease"]["claims"]["constraints"]["geofence_id"] = Value::from(geofence_id);
        input["local_context"]["geofence_state"]["geofence_id"] = Value::from(geofence_id);
        resign_lease_value(&mut input, &vector.trusted_context.dev_hmac_secret);
        resign_local_context_value(&mut input, &vector.trusted_context.state_hmac_secret);
        let mut replay_cache = fresh_replay_cache();

        let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

        assert_eq!(decision.decision.as_str(), "deny");
        assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");
    }
}

#[test]
fn blank_local_geofence_state_rejects_valid_geofence_constraint() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    input["local_context"]["geofence_state"]["geofence_id"] = Value::from("");
    resign_local_context_value(&mut input, &vector.trusted_context.state_hmac_secret);
    let mut replay_cache = fresh_replay_cache();

    let decision = verify_json_value(input, &vector.trusted_context, &mut replay_cache);

    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_GEOFENCE_VIOLATION");
}

#[test]
fn forged_local_context_without_matching_state_signature_is_rejected() {
    let denied_vector = load_vector("network_partition_rejected");
    let valid_vector = load_vector("valid_remote_assist_lease");
    let mut input = denied_vector.input;
    let mut replay_cache = replay_cache_with_seen(denied_vector.seen_nonces);

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
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);

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
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces.clone());
    let decision = verify_json_value(input.clone(), &multi_issuer_context, &mut replay_cache);
    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");

    let mut multi_command_context = vector.trusted_context.clone();
    multi_command_context
        .trusted_command_agent_ids
        .push("fleet-agent:second".to_string());
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces.clone());
    let decision = verify_json_value(input.clone(), &multi_command_context, &mut replay_cache);
    assert_eq!(decision.decision.as_str(), "deny");
    assert_eq!(decision.reason_code.as_str(), "DENY_MALFORMED_INPUT");

    let mut multi_state_context = vector.trusted_context;
    multi_state_context
        .trusted_state_edge_ids
        .push("edge-agent:second".to_string());
    let mut replay_cache = replay_cache_with_seen(vector.seen_nonces);
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

fn verify_resigned_speed_payload(payload: Value, command_id: &str) -> VerificationDecision {
    let vector = load_vector("max_speed_too_high_rejected");
    let mut input = vector.input;
    let trusted_context = vector.trusted_context;
    input["command"]["payload"] = payload;
    resign_command_value(
        &mut input,
        command_id,
        &format!("{command_id}-nonce"),
        &trusted_context.command_hmac_secret,
    );
    let mut replay_cache = fresh_replay_cache();
    verify_json_value(input, &trusted_context, &mut replay_cache)
}

fn verify_resigned_no_speed_payload(payload: Value, command_id: &str) -> VerificationDecision {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    let trusted_context = vector.trusted_context;
    input["command"]["payload"] = payload;
    resign_command_value(
        &mut input,
        command_id,
        &format!("{command_id}-nonce"),
        &trusted_context.command_hmac_secret,
    );
    let mut replay_cache = fresh_replay_cache();
    verify_json_value(input, &trusted_context, &mut replay_cache)
}

fn resign_lease_value(input: &mut Value, secret: &str) {
    let claims: CapabilityLeaseClaims =
        serde_json::from_value(input["lease"]["claims"].clone()).expect("claims are well formed");
    input["lease"]["signature"] = Value::from(sign_claims(&claims, secret));
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
    input["command"]["message_id"] = Value::from(format!("msg-{command_id}"));
    input["command"]["command_nonce"] = Value::from(command_nonce);
    let command: EdgeCommand =
        serde_json::from_value(input["command"].clone()).expect("command is well formed");
    input["command"]["signature"] = Value::from(sign_command(&command, secret));
}

fn resign_local_context_value(input: &mut Value, secret: &str) {
    let local_context: LocalContext = serde_json::from_value(input["local_context"].clone())
        .expect("local context is well formed");
    input["local_context"]["signature"] = Value::from(sign_local_context(&local_context, secret));
}

fn sign_local_context(context: &LocalContext, secret: &str) -> String {
    let payload = SignedLocalContext {
        robot_id: &context.robot_id,
        edge_agent_id: &context.edge_agent_id,
        authenticated_edge_agent_id: context.authenticated_edge_agent_id.as_deref().unwrap_or(""),
        mission_id: &context.mission_id,
        observed_at_unix_ms: context.observed_at_unix_ms,
        network_state: &context.network_state,
        geofence_state: &context.geofence_state,
    };
    let payload = canonical_json(&payload).expect("local context canonicalizes");
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).expect("HMAC accepts secret bytes");
    mac.update(payload.as_bytes());
    hex::encode(mac.finalize().into_bytes())
}

fn sign_command(command: &EdgeCommand, secret: &str) -> String {
    let payload = SignedCommand {
        protocol_version: &command.protocol_version,
        message_id: &command.message_id,
        correlation_id: &command.correlation_id,
        message_type: &command.message_type,
        command_id: &command.command_id,
        agent_id: &command.agent_id,
        authenticated_agent_id: &command.authenticated_agent_id,
        edge_agent_id: &command.edge_agent_id,
        robot_id: &command.robot_id,
        mission_id: &command.mission_id,
        capability: &command.capability,
        command_nonce: &command.command_nonce,
        created_at_unix_ms: command.created_at_unix_ms,
        payload: &command.payload,
    };
    let payload = canonical_json(&payload).expect("command canonicalizes");
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).expect("HMAC accepts secret bytes");
    mac.update(payload.as_bytes());
    hex::encode(mac.finalize().into_bytes())
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
struct SignedCommand<'a> {
    protocol_version: &'a str,
    message_id: &'a str,
    correlation_id: &'a str,
    message_type: &'a str,
    command_id: &'a str,
    agent_id: &'a str,
    authenticated_agent_id: &'a str,
    edge_agent_id: &'a str,
    robot_id: &'a str,
    mission_id: &'a str,
    capability: &'a str,
    command_nonce: &'a str,
    created_at_unix_ms: i64,
    payload: &'a Value,
}
