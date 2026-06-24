import importlib
import json
from pathlib import Path
from typing import get_args

import yaml

from rclp_core.audit import AuditLog
from rclp_core.crypto import DemoKeyPair
from rclp_core.models import (
    AuditCommit,
    AuditEventType,
    Capability,
    CapabilityRequest,
    GeofenceState,
    RobotStateAssertion,
)
from rclp_core.network import profile
from rclp_core.policy import Policy, RequestReplayCache, _evaluate_policy_inputs, policy_digest


ROOT = Path(__file__).resolve().parents[1]
CENTRAL_AGENT_ID = "fleet-agent:v0.1"
EDGE_AGENT_ID = "edge-agent:rover-001"
ROBOT_ID = "rover-001"
MISSION_ID = "mission-001"
EDGE_KEY = DemoKeyPair()


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def signed_request(key: DemoKeyPair) -> CapabilityRequest:
    request = CapabilityRequest(
        requesting_agent_id=CENTRAL_AGENT_ID,
        authenticated_agent_id=CENTRAL_AGENT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        robot_id=ROBOT_ID,
        mission_id=MISSION_ID,
        capability=Capability.REMOTE_ASSIST,
        reason="conformance scenario",
    )
    request.signature = key.sign(request)
    return request


def robot_state(network_profile: str) -> RobotStateAssertion:
    state = RobotStateAssertion(
        robot_id=ROBOT_ID,
        edge_agent_id=EDGE_AGENT_ID,
        authenticated_edge_agent_id=EDGE_AGENT_ID,
        mission_id=MISSION_ID,
        network_state=profile(network_profile),
        geofence_state=GeofenceState(geofence_id="test-zone-a", inside=True),
    )
    state.signature = EDGE_KEY.sign(state)
    return state


def test_protocol_manifest_matches_exported_message_models():
    manifest = load_yaml("manifests/rclp_protocol_manifest.yaml")
    message_models = manifest["message_models"]

    assert manifest["messages"] == list(message_models)

    for message_name, contract in message_models.items():
        module_name, class_name = contract["python_model"].rsplit(".", 1)
        model = getattr(importlib.import_module(module_name), class_name)

        assert class_name == message_name
        required_fields = set(contract["required_fields"])
        runtime_required_fields = set(contract.get("runtime_required_fields", []))

        assert required_fields.issubset(model.model_fields)
        defaulted_required_fields = {
            field_name
            for field_name in required_fields
            if not model.model_fields[field_name].is_required()
        }

        assert runtime_required_fields == defaulted_required_fields
        if "message_type" in contract:
            message_type_field = model.model_fields["message_type"]
            if message_type_field.is_required():
                assert contract["message_type"] in get_args(message_type_field.annotation)
            else:
                assert message_type_field.default == contract["message_type"]


def test_protocol_manifest_required_fields_are_named_in_spec():
    manifest = load_yaml("manifests/rclp_protocol_manifest.yaml")
    spec = (ROOT / "docs/PROTOCOL_SPEC_DRAFT.md").read_text(encoding="utf-8")
    common_fields = {
        "protocol_version",
        "message_id",
        "correlation_id",
        "created_at",
        "message_type",
    }
    common_section = spec.split("## Message Types", maxsplit=1)[0]

    for message_name, contract in manifest["message_models"].items():
        section_start = spec.index(f"### {message_name}")
        next_section = spec.find("\n### ", section_start + 1)
        section = spec[section_start:] if next_section == -1 else spec[section_start:next_section]

        for field in contract["required_fields"]:
            field_marker = f"`{field}`"
            if field in common_fields:
                assert field_marker in common_section
            else:
                assert field_marker in section


def test_sample_replay_uses_stable_audit_event_types():
    sample = json.loads((ROOT / "examples/audit/sample_replay.json").read_text(encoding="utf-8"))
    stable_event_types = {event_type.value for event_type in AuditEventType}

    assert {event["event_type"] for event in sample["events"]}.issubset(stable_event_types)


def test_sample_replay_events_are_valid_audit_commits():
    sample = json.loads((ROOT / "examples/audit/sample_replay.json").read_text(encoding="utf-8"))
    log = AuditLog()

    for raw_event in sample["events"]:
        event = AuditCommit.model_validate(raw_event)
        assert event.correlation_id == sample["correlation_id"]
        log.append(event)

    assert [event.audit_id for event in log.events] == [
        raw_event["audit_id"] for raw_event in sample["events"]
    ]


def test_network_degrade_scenario_matches_current_policy_profile_behavior(tmp_path):
    scenario = load_yaml("examples/scenarios/network_degrade.yaml")
    policy = Policy.from_yaml(ROOT / "examples/policies/remote_assist_policy.yaml")
    key = DemoKeyPair()
    request = signed_request(key)
    trust_kwargs = {
        "agent_public_keys_by_id": {CENTRAL_AGENT_ID: key.public_key_b64},
        "edge_public_keys_by_id": {EDGE_AGENT_ID: EDGE_KEY.public_key_b64},
        "accepted_policy_digests": {policy_digest(policy)},
    }

    for index, step in enumerate(scenario["steps"]):
        if "expected_decision" not in step:
            continue
        decision, _, _, _ = _evaluate_policy_inputs(
            request,
            robot_state(step["profile"]),
            policy,
            **trust_kwargs,
            replay_cache=RequestReplayCache(tmp_path / f"request-replay-{index}.sqlite3"),
        )
        assert decision == step["expected_decision"]
