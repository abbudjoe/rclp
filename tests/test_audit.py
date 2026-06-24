import json

import pytest
from pydantic import ValidationError

from rclp_core.audit import AuditLog, load_jsonl
from rclp_core.models import AuditCommit, AuditEventType, stable_json_hash


def test_audit_replay_groups_by_correlation():
    log = AuditLog()
    log.append(
        AuditCommit(
            correlation_id="corr_1",
            event_type=AuditEventType.CAPABILITY_REQUESTED,
            actor_id="x",
            robot_id="robot",
            mission_id="mission",
            summary="first",
        )
    )
    log.append(
        AuditCommit(
            correlation_id="corr_1",
            event_type=AuditEventType.CAPABILITY_DENIED,
            actor_id="x",
            robot_id="robot",
            mission_id="mission",
            summary="second",
        )
    )
    summary = log.replay_summary()
    assert "corr_1" in summary
    assert "requests:" in summary
    assert "decisions:" in summary
    assert "capability_requested" in summary
    assert "capability_denied" in summary
    replay = log.replay()["corr_1"]
    assert replay.requests[0].event_type == AuditEventType.CAPABILITY_REQUESTED
    assert replay.decisions[0].event_type == AuditEventType.CAPABILITY_DENIED


def test_audit_event_type_is_stable_enum():
    with pytest.raises(ValidationError):
        AuditCommit(
            correlation_id="corr_1",
            event_type="freeform_log_string",
            actor_id="x",
            summary="not stable",
        )


def test_audit_jsonl_round_trip_and_hash_chain(tmp_path):
    log = AuditLog()
    first = log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.CAPABILITY_ALLOWED,
        actor_id="issuer",
        robot_id="robot",
        mission_id="mission",
        summary="allow",
        payload={"decision": "allow"},
    )
    second = log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.COMMAND_REJECTED,
        actor_id="edge",
        robot_id="robot",
        mission_id="mission",
        summary="reject",
        payload={"reason_code": "NO_LEASE"},
    )

    assert first.payload_hash is not None
    assert first.integrity_proof is not None
    assert first.previous_audit_hash is None
    assert second.previous_audit_hash == first.integrity_proof

    path = tmp_path / "audit.jsonl"
    log.write_jsonl(path)
    loaded = load_jsonl(path, trusted_chain_head=log.chain_head)

    assert loaded == log.events
    assert loaded[0].event_type == AuditEventType.CAPABILITY_ALLOWED
    assert loaded[1].event_type == AuditEventType.COMMAND_REJECTED


def test_load_jsonl_rejects_unanchored_authority_events(tmp_path):
    log = AuditLog()
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.CAPABILITY_ALLOWED,
        actor_id="issuer",
        robot_id="robot",
        mission_id="mission",
        summary="allow",
        payload={"decision": "allow"},
    )
    path = tmp_path / "audit.jsonl"
    log.write_jsonl(path)

    with pytest.raises(ValueError, match="trusted audit chain head required"):
        load_jsonl(path)


def test_load_jsonl_rejects_recomputed_tamper_against_trusted_chain_head(tmp_path):
    log = AuditLog()
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.CAPABILITY_ALLOWED,
        actor_id="issuer",
        robot_id="robot",
        mission_id="mission",
        summary="allow",
        payload={"reason_code": "POLICY_SATISFIED"},
    )
    trusted_head = log.chain_head
    tampered = log.events[0].model_dump(mode="json")
    tampered["payload"]["reason_code"] = "FORGED_ALLOW"
    tampered["payload_hash"] = stable_json_hash(tampered["payload"])
    tampered_event = AuditCommit.model_validate(tampered)
    tampered["integrity_proof"] = AuditLog()._integrity_proof(tampered_event, None)
    path = tmp_path / "recomputed-tamper.jsonl"
    path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="trusted audit chain head"):
        load_jsonl(path, trusted_chain_head=trusted_head)


def test_audit_log_rejects_tampered_payload_hash():
    log = AuditLog()
    event = AuditCommit(
        correlation_id="corr_1",
        event_type=AuditEventType.COMMAND_REJECTED,
        actor_id="edge",
        robot_id="robot",
        mission_id="mission",
        summary="reject",
        payload={"reason_code": "NO_LEASE"},
        payload_hash="sha256:not-real",
    )

    with pytest.raises(ValueError, match="payload_hash does not match"):
        log.append(event)


def test_audit_log_rejects_authority_event_type_demoted_to_diagnostic_grade():
    log = AuditLog()
    event = AuditCommit(
        correlation_id="corr_1",
        event_type=AuditEventType.REVOCATION_REJECTED,
        actor_id="edge",
        robot_id="robot",
        mission_id="mission",
        summary="rejected",
        payload={"reason_code": "REVOCATION_CONTEXT_REQUIRED"},
        authority_relevant=False,
    )

    with pytest.raises(ValueError, match="authority event type"):
        log.append(event)


def test_load_jsonl_rejects_tampered_chain(tmp_path):
    log = AuditLog()
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.COMMAND_REJECTED,
        actor_id="edge",
        robot_id="robot",
        mission_id="mission",
        summary="reject",
        payload={"reason_code": "NO_LEASE"},
    )
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.FALLBACK_DECLARED,
        actor_id="edge",
        robot_id="robot",
        mission_id="mission",
        summary="fallback",
        payload={"fallback_action": "local_autonomy_only"},
    )
    tampered = [event.model_dump(mode="json") for event in log.events]
    tampered[1]["previous_audit_hash"] = "sha256:wrong"
    path = tmp_path / "audit.jsonl"
    path.write_text("\n".join(json.dumps(event) for event in tampered) + "\n")

    with pytest.raises(ValueError, match="previous_audit_hash"):
        load_jsonl(path)


def test_load_jsonl_rejects_tampered_authority_context(tmp_path):
    log = AuditLog()
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.CAPABILITY_ALLOWED,
        actor_id="issuer",
        robot_id="robot",
        mission_id="mission",
        summary="allow",
        payload={"reason_code": "POLICY_SATISFIED"},
        policy_id="policy-a",
        state_refs=["state-a"],
        related_message_ids=["request-a", "state-a"],
    )
    tampered = log.events[0].model_dump(mode="json")
    tampered["robot_id"] = "robot-other"
    path = tmp_path / "tampered-context.jsonl"
    path.write_text(json.dumps(tampered) + "\n")

    with pytest.raises(ValueError, match="integrity_proof"):
        load_jsonl(path)


def test_load_jsonl_rejects_unknown_context_outside_integrity_proof(tmp_path):
    log = AuditLog()
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.CAPABILITY_ALLOWED,
        actor_id="issuer",
        robot_id="robot",
        mission_id="mission",
        summary="allow",
        payload={"reason_code": "POLICY_SATISFIED"},
    )
    event = log.events[0].model_dump(mode="json")
    event["future_authority_context"] = {"robot_id": "robot-other"}
    path = tmp_path / "unknown-context.jsonl"
    path.write_text(json.dumps(event) + "\n")

    with pytest.raises(ValidationError, match="future_authority_context"):
        load_jsonl(path, trusted_chain_head=log.chain_head)


def test_load_jsonl_rejects_missing_payload_hash(tmp_path):
    log = AuditLog()
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.COMMAND_REJECTED,
        actor_id="edge",
        robot_id="robot",
        mission_id="mission",
        summary="reject",
        payload={"reason_code": "NO_LEASE"},
    )
    event = log.events[0].model_dump(mode="json")
    del event["payload_hash"]
    path = tmp_path / "missing-payload-hash.jsonl"
    path.write_text(json.dumps(event) + "\n")

    with pytest.raises(ValueError, match="payload_hash"):
        load_jsonl(path)


def test_load_jsonl_rejects_missing_common_envelope_fields(tmp_path):
    log = AuditLog()
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.COMMAND_REJECTED,
        actor_id="edge",
        robot_id="robot",
        mission_id="mission",
        summary="reject",
        payload={"reason_code": "NO_LEASE"},
    )
    event = log.events[0].model_dump(mode="json")
    del event["message_type"]
    path = tmp_path / "missing-message-type.jsonl"
    path.write_text(json.dumps(event) + "\n")

    with pytest.raises(ValueError, match="message_type"):
        load_jsonl(path)


def test_audit_log_rejects_duplicate_audit_ids():
    log = AuditLog()
    event = AuditCommit(
        correlation_id="corr_1",
        event_type=AuditEventType.DIAGNOSTIC,
        actor_id="x",
        summary="diagnostic",
    )
    log.append(event)
    with pytest.raises(ValueError, match="duplicate audit_id"):
        log.append(event)
