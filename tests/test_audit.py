import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from rclp_core.audit import (
    LOAD_REQUIRED_FIELDS,
    AuditLog,
    audit_batch_auth_violation,
    audit_batch_event_violation,
    create_signed_audit_batch,
    load_jsonl,
)
from rclp_core.crypto import DemoKeyPair
from rclp_core.models import AuditBatchCommit, AuditCommit, AuditEventType, stable_json_hash


ROOT = Path(__file__).resolve().parents[1]


def test_audit_conformance_schema_matches_runtime_required_fields():
    schema = json.loads(
        (ROOT / "manifests/rclp_audit_conformance_schema.json").read_text(encoding="utf-8")
    )

    assert set(schema["required"]) == LOAD_REQUIRED_FIELDS
    assert schema["properties"]["message_type"]["const"] == "audit_commit"
    assert set(schema["properties"]["event_type"]["enum"]) == {
        event_type.value for event_type in AuditEventType
    }
    assert set(schema["x-rclp-authority-event-types"]) == {
        AuditEventType.CAPABILITY_REQUESTED.value,
        AuditEventType.NETWORK_STATE_ASSERTED.value,
        AuditEventType.CAPABILITY_ALLOWED.value,
        AuditEventType.CAPABILITY_DENIED.value,
        AuditEventType.CAPABILITY_DEGRADED.value,
        AuditEventType.COMMAND_ALLOWED.value,
        AuditEventType.COMMAND_REJECTED.value,
        AuditEventType.LEASE_REVOKED.value,
        AuditEventType.REVOCATION_REJECTED.value,
        AuditEventType.FALLBACK_DECLARED.value,
    }


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


def test_load_jsonl_rejects_demoted_authority_event_without_explicit_diagnostic_import(
    tmp_path,
):
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
    demoted = log.events[0].model_dump(mode="json")
    demoted.update(
        {
            "event_type": AuditEventType.DIAGNOSTIC.value,
            "authority_relevant": False,
            "robot_id": None,
            "mission_id": None,
            "summary": "diagnostic-looking imported event",
        }
    )
    demoted_event = AuditCommit.model_validate(demoted)
    demoted["integrity_proof"] = AuditLog()._integrity_proof(demoted_event, None)
    path = tmp_path / "demoted-authority.jsonl"
    path.write_text(json.dumps(demoted) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="trusted audit chain head required"):
        load_jsonl(path)
    with pytest.raises(ValueError, match="trusted audit chain head"):
        load_jsonl(path, trusted_chain_head=log.chain_head)

    loaded = load_jsonl(path, import_profile="diagnostic_only")
    assert loaded[0].event_type == AuditEventType.DIAGNOSTIC
    assert loaded[0].authority_relevant is False


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


@pytest.mark.parametrize("required_field", ["payload_hash", "integrity_proof"])
def test_load_jsonl_rejects_null_required_integrity_field_before_model_repair(
    tmp_path,
    required_field,
):
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
    event[required_field] = None
    path = tmp_path / f"null-{required_field}.jsonl"
    path.write_text(json.dumps(event) + "\n")

    with pytest.raises(ValueError, match=required_field):
        load_jsonl(path, trusted_chain_head=log.chain_head)


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


def test_signed_audit_batch_authenticates_committed_hash_chain():
    key = DemoKeyPair()
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
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.COMMAND_ALLOWED,
        actor_id="edge",
        robot_id="robot",
        mission_id="mission",
        summary="forward",
        payload={"command_id": "cmd_1"},
    )

    batch = create_signed_audit_batch(
        log.events,
        signed_by="audit-signer",
        signer=key.sign,
    )

    assert audit_batch_event_violation(batch, log.events) is None
    assert audit_batch_auth_violation(batch, {"audit-signer": key.public_key_b64}) is None


def test_signed_audit_batch_rejects_tampered_events_and_batch_metadata():
    key = DemoKeyPair()
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
    batch = create_signed_audit_batch(
        log.events,
        signed_by="audit-signer",
        signer=key.sign,
    )
    tampered_events = [
        log.events[0],
        log.events[1].model_copy(update={"summary": "forged fallback"}),
    ]
    tampered_batch = batch.model_copy(update={"batch_hash": "sha256:" + ("0" * 64)})

    assert (
        audit_batch_event_violation(batch, tampered_events) == "AUDIT_BATCH_INTEGRITY_PROOF_INVALID"
    )
    assert (
        audit_batch_auth_violation(tampered_batch, {"audit-signer": key.public_key_b64})
        == "AUDIT_BATCH_SIGNATURE_INVALID"
    )


def test_signed_audit_batch_refuses_to_sign_tampered_committed_events():
    key = DemoKeyPair()
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
    tampered_events = [
        log.events[0],
        log.events[1].model_copy(update={"payload": {"fallback_action": "forged"}}),
    ]

    with pytest.raises(ValueError, match="AUDIT_BATCH_EVENT_PAYLOAD_HASH_INVALID"):
        create_signed_audit_batch(
            tampered_events,
            signed_by="audit-signer",
            signer=key.sign,
        )


def test_signed_audit_batch_rejects_non_contiguous_or_duplicate_event_batches():
    key = DemoKeyPair()
    first_log = AuditLog()
    second_log = AuditLog()
    for log, correlation_id in [
        (first_log, "corr_1"),
        (second_log, "corr_2"),
    ]:
        log.record(
            correlation_id=correlation_id,
            event_type=AuditEventType.COMMAND_REJECTED,
            actor_id="edge",
            robot_id="robot",
            mission_id="mission",
            summary="reject",
            payload={"reason_code": "NO_LEASE"},
        )
        log.record(
            correlation_id=correlation_id,
            event_type=AuditEventType.FALLBACK_DECLARED,
            actor_id="edge",
            robot_id="robot",
            mission_id="mission",
            summary="fallback",
            payload={"fallback_action": "local_autonomy_only"},
        )
    batch = create_signed_audit_batch(
        first_log.events,
        signed_by="audit-signer",
        signer=key.sign,
    )

    out_of_order = list(reversed(first_log.events))
    duplicate_id = [first_log.events[0], first_log.events[0]]
    mixed_log = [first_log.events[0], second_log.events[1]]

    assert audit_batch_event_violation(batch, out_of_order) == "AUDIT_BATCH_PREVIOUS_HASH_MISMATCH"
    assert audit_batch_event_violation(batch, duplicate_id) == "AUDIT_BATCH_DUPLICATE_AUDIT_ID"
    assert audit_batch_event_violation(batch, mixed_log) == "AUDIT_BATCH_PREVIOUS_HASH_MISMATCH"
    with pytest.raises(ValueError, match="AUDIT_BATCH_PREVIOUS_HASH_MISMATCH"):
        create_signed_audit_batch(
            out_of_order,
            signed_by="audit-signer",
            signer=key.sign,
        )
    with pytest.raises(ValueError, match="AUDIT_BATCH_DUPLICATE_AUDIT_ID"):
        create_signed_audit_batch(
            duplicate_id,
            signed_by="audit-signer",
            signer=key.sign,
        )
    with pytest.raises(ValueError, match="AUDIT_BATCH_PREVIOUS_HASH_MISMATCH"):
        create_signed_audit_batch(
            mixed_log,
            signed_by="audit-signer",
            signer=key.sign,
        )


def test_signed_audit_batch_rejects_missing_or_unknown_signature_algorithm():
    key = DemoKeyPair()
    log = AuditLog()
    log.record(
        correlation_id="corr_1",
        event_type=AuditEventType.DIAGNOSTIC,
        actor_id="diagnostic-agent",
        summary="diagnostic",
        authority_relevant=False,
    )
    batch = create_signed_audit_batch(
        log.events,
        signed_by="audit-signer",
        signer=key.sign,
    )
    raw_batch = batch.model_dump(mode="json")
    raw_batch.pop("signature_alg")
    missing_alg = AuditBatchCommit.model_validate(raw_batch)
    unknown_alg = batch.model_copy(update={"signature_alg": "RCLP-UNKNOWN"})

    assert (
        audit_batch_auth_violation(missing_alg, {"audit-signer": key.public_key_b64})
        == "AUDIT_BATCH_SIGNATURE_ALGORITHM_MISSING"
    )
    assert (
        audit_batch_auth_violation(unknown_alg, {"audit-signer": key.public_key_b64})
        == "AUDIT_BATCH_SIGNATURE_ALGORITHM_UNSUPPORTED"
    )
