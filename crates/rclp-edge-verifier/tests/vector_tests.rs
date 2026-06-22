use std::fs;
use std::path::Path;

use rclp_edge_verifier::{verify_json_value, InMemoryReplayCache, TrustedVerifierContext};
use serde::Deserialize;
use serde_json::Value;

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
        let mut replay_cache = InMemoryReplayCache::with_seen(vector.seen_nonces);

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
fn replay_cache_rejects_second_use_of_same_lease_nonce() {
    let vector = load_vector("valid_remote_assist_lease");
    let mut input = vector.input;
    let mut replay_cache = InMemoryReplayCache::with_seen(vector.seen_nonces);

    let first = verify_json_value(input.clone(), &vector.trusted_context, &mut replay_cache);
    assert_eq!(first.decision.as_str(), "allow");
    assert_eq!(first.reason_code.as_str(), "ALLOW");

    input["command"]["command_id"] = Value::from("cmd-valid-remote-assist-second");
    let second = verify_json_value(input, &vector.trusted_context, &mut replay_cache);
    assert_eq!(second.decision.as_str(), "deny");
    assert_eq!(second.reason_code.as_str(), "DENY_REPLAYED_NONCE");
}

fn load_vector(name: &str) -> Vector {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/vectors/edge_verifier")
        .join(format!("{name}.json"));
    let raw = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("failed to read {}: {error}", path.display()));
    serde_json::from_str(&raw)
        .unwrap_or_else(|error| panic!("failed to parse {}: {error}", path.display()))
}
