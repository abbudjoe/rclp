use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;

use rclp_edge_verifier::{verify_json_value, AuditEvent, FileReplayCache, ReplayCache};
use serde::Deserialize;
use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Deserialize)]
struct VectorInput {
    trusted_context: rclp_edge_verifier::TrustedVerifierContext,
    #[serde(default)]
    seen_nonces: Vec<String>,
    input: Value,
}

#[derive(Debug, Serialize)]
struct CliDecision {
    decision: String,
    reason_code: String,
    audit_event: AuditEvent,
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(2);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut args = env::args_os();
    let program = args
        .next()
        .and_then(|value| value.into_string().ok())
        .unwrap_or_else(|| "rclp-edge-verify".to_string());
    let Some(vector_path) = args.next() else {
        return Err(format!("usage: {program} <vector.json> [replay-cache-dir]").into());
    };
    let replay_cache_dir = args
        .next()
        .map(PathBuf::from)
        .unwrap_or_else(default_replay_cache_dir);
    if args.next().is_some() {
        return Err(format!("usage: {program} <vector.json> [replay-cache-dir]").into());
    }

    let raw = fs::read_to_string(&vector_path)?;
    let vector: VectorInput = serde_json::from_str(&raw)?;
    let mut replay_cache = FileReplayCache::new(&replay_cache_dir)?;
    for nonce in vector.seen_nonces {
        if !replay_cache.consume_nonce(&nonce) {
            return Err(format!("failed to seed replay nonce: {nonce}").into());
        }
    }

    let decision = verify_json_value(vector.input, &vector.trusted_context, &mut replay_cache);
    let output = CliDecision {
        decision: decision.decision.as_str().to_string(),
        reason_code: decision.reason_code.as_str().to_string(),
        audit_event: decision.audit_event,
    };
    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}

fn default_replay_cache_dir() -> PathBuf {
    env::temp_dir().join(format!("rclp-edge-verify-{}", std::process::id()))
}
