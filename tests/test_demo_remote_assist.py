import json

from rclp_agents import demo_remote_assist


def _section(output: str, title: str) -> str:
    marker = f"### {title}\n"
    start = output.index(marker) + len(marker)
    next_marker = output.find("\n### ", start)
    if next_marker == -1:
        return output[start:].strip()
    return output[start:next_marker].strip()


def test_demo_remote_assist_outputs_full_local_authority_flow(capsys):
    demo_remote_assist.main()
    output = capsys.readouterr().out

    assert "RCLP remote_assist local protocol demonstration" in output
    assert "not a certified safety system" in output

    setup = json.loads(_section(output, "setup"))
    assert setup["central_agent"]["agent_id"] == "fleet-agent:v0.1"
    assert setup["edge_agent"]["agent_id"] == "edge-agent:rover-001"
    assert setup["robot"]["robot_id"] == "rover-001"
    assert setup["mission"]["mission_id"] == "mission-001"
    assert setup["geofence"]["geofence_id"] == "test-zone-a"
    assert setup["policy_id"] == "remote-assist-authority-v0"
    assert setup["deterministic_network_profiles"] == [
        "normal",
        "degraded_teleop",
        "uplink_bad",
        "partition",
    ]
    assert setup["impaired_demo_profile"] == "degraded_teleop"

    normal_decision = json.loads(_section(output, "normal_network_decision"))
    assert normal_decision["decision"] == "allow"
    assert normal_decision["reason_code"] == "POLICY_SATISFIED"
    assert normal_decision["lease"]["capability"] == "remote_assist"
    assert normal_decision["lease"]["signature"]

    valid_gate_result = json.loads(_section(output, "command_gate_with_valid_lease"))
    assert valid_gate_result["allowed"] is True
    assert valid_gate_result["reason_code"] == "LEASE_VALID"
    assert valid_gate_result["audit_id"].startswith("audit_")
    assert valid_gate_result["fallback_action"] is None
    assert valid_gate_result["fallback_declaration"] is None

    missing_lease_result = json.loads(_section(output, "command_without_valid_lease"))
    assert missing_lease_result["decision"] == "deny"
    assert missing_lease_result["reason_code"] == "NO_LEASE"
    assert missing_lease_result["summary"] == "command without a valid lease was rejected"
    assert missing_lease_result["safe_alternatives"] == ["local_autonomy_only"]
    assert missing_lease_result["retry_after_seconds"] is None
    assert missing_lease_result["audit_id"].startswith("audit_")
    assert missing_lease_result["gate_result"]["allowed"] is False
    assert missing_lease_result["gate_result"]["audit_id"] == missing_lease_result["audit_id"]
    assert missing_lease_result["gate_result"]["fallback_action"] == "local_autonomy_only"
    assert (
        missing_lease_result["gate_result"]["fallback_declaration"]["correlation_id"]
        == "corr_demo_remote_assist"
    )

    degraded_decision = json.loads(_section(output, "impaired_network_decision"))
    assert degraded_decision["decision"] == "degrade"
    assert degraded_decision["reason_code"] == "NETWORK_LATENCY_DEGRADED"
    assert degraded_decision["safe_alternatives"] == ["crawl_to_safe_zone"]

    revocation = json.loads(_section(output, "lease_revocation"))
    assert revocation["reason_code"] == "NETWORK_PROFILE_REVOKE"
    assert revocation["fallback_action"] == "crawl_to_safe_zone"

    revoked_gate_result = json.loads(_section(output, "command_gate_after_network_revocation"))
    assert revoked_gate_result["decision"] == "deny"
    assert revoked_gate_result["reason_code"] == "LEASE_REVOKED"
    assert revoked_gate_result["safe_alternatives"] == ["crawl_to_safe_zone"]
    assert revoked_gate_result["retry_after_seconds"] == 30
    assert revoked_gate_result["audit_id"].startswith("audit_")
    assert revoked_gate_result["gate_result"]["allowed"] is False
    assert revoked_gate_result["gate_result"]["audit_id"] == revoked_gate_result["audit_id"]
    assert revoked_gate_result["gate_result"]["fallback_action"] == "crawl_to_safe_zone"
    assert (
        revoked_gate_result["gate_result"]["fallback_declaration"]["correlation_id"]
        == "corr_demo_remote_assist"
    )

    audit_events = [
        json.loads(line) for line in _section(output, "audit_jsonl").splitlines() if line.strip()
    ]
    event_types = [event["event_type"] for event in audit_events]
    assert event_types == [
        "demo_setup",
        "capability_requested",
        "network_state_asserted",
        "capability_allowed",
        "command_allowed",
        "command_rejected",
        "fallback_declared",
        "network_state_asserted",
        "capability_degraded",
        "lease_revoked",
        "fallback_declared",
        "command_rejected",
        "fallback_declared",
    ]
    assert {event["correlation_id"] for event in audit_events} == {"corr_demo_remote_assist"}
    assert all(event["audit_id"].startswith("audit_") for event in audit_events)
    assert all(event["message_type"] == "audit_commit" for event in audit_events)
    assert all(event["payload_hash"].startswith("sha256:") for event in audit_events)
    assert all(event["integrity_profile"] == "local_hash_chain_v0" for event in audit_events)
    assert all(event["integrity_proof"].startswith("sha256:") for event in audit_events)
    assert audit_events[0]["previous_audit_hash"] is None
    assert audit_events[1]["previous_audit_hash"] == audit_events[0]["integrity_proof"]
    fallback_payloads = [
        event["payload"] for event in audit_events if event["event_type"] == "fallback_declared"
    ]
    assert {payload["correlation_id"] for payload in fallback_payloads} == {
        "corr_demo_remote_assist"
    }

    replay = _section(output, "incident_replay_summary")
    assert "requests:" in replay
    assert "decisions:" in replay
    assert "enforcement:" in replay
    assert "revocations:" in replay
    assert "fallbacks:" in replay
    assert "capability_allowed" in replay
    assert "reason=POLICY_SATISFIED" in replay
    assert "command_rejected" in replay
    assert "reason=NO_LEASE" in replay
    assert "capability_degraded" in replay
    assert "reason=NETWORK_LATENCY_DEGRADED" in replay
    assert "reason=LEASE_REVOKED" in replay


def test_demo_remote_assist_can_switch_impaired_profile(capsys):
    demo_remote_assist.main(impaired_network_profile="uplink_bad")
    output = capsys.readouterr().out

    setup = json.loads(_section(output, "setup"))
    assert setup["impaired_demo_profile"] == "uplink_bad"

    impaired_decision = json.loads(_section(output, "impaired_network_decision"))
    assert impaired_decision["decision"] == "deny"
    assert impaired_decision["reason_code"] == "NETWORK_UPLINK_TOO_LOW"
    assert impaired_decision["safe_alternatives"] == ["crawl_to_safe_zone"]

    audit_events = [
        json.loads(line) for line in _section(output, "audit_jsonl").splitlines() if line.strip()
    ]
    assert "capability_denied" in [event["event_type"] for event in audit_events]
