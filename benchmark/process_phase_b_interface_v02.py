"""Target-visible Process-Constrained Phase-B v0.2 interface.

This module contains no model/network calls. It makes the operational contract of
SPECIALIST explicit and testable, including negative/no-action constraints.
"""

from __future__ import annotations

from typing import Any

from protocol_runtime_v04 import ProtocolRuntime, specialist_next_state_contracts


ACTION_CATALOG: dict[str, dict[str, dict[str, Any]]] = {
    "DEDUCTIVE_CONSTRAINT": {
        "inspect_constraints": {
            "args": {},
            "description": "Return the public task constraints in structured form.",
        },
        "test_candidate": {
            "args": {"service_restored_minute": "integer"},
            "description": "Test one proposed SERVICE-RESTORATION minute; returns feasibility but not the optimum.",
        },
        "commit_restoration": {
            "args": {"service_restored_minute": "integer"},
            "description": "Commit the final minute when restart is finished and service is restored.",
        },
    },
    "ABDUCTIVE_DIAGNOSTIC": {
        "check_network": {"args": {}, "description": "Check whether a network anomaly is present."},
        "compare_zones": {"args": {}, "description": "Check whether the pattern is localized by zone."},
        "inspect_pool": {"args": {}, "description": "Check whether the connection pool shows an anomaly."},
        "diagnose": {
            "args": {"cause": "route_change|library_regression|pool_exhaustion|upstream_policy"},
            "description": "Commit the dominant cause.",
        },
    },
    "SEARCH_PLANNING": {
        "enable_dual_write": {"args": {}, "description": "Enable dual writes to old and new shards."},
        "backfill": {"args": {}, "description": "Backfill historical rows."},
        "verify_checksum": {"args": {}, "description": "Verify the copied data."},
        "shift_reads": {
            "args": {"percent": "10..100 in increments of 10"},
            "description": "Move reads toward the new shard.",
        },
        "probe_health": {
            "args": {},
            "description": "Observe new-shard health after all reads are on it.",
        },
        "rollback_reads": {
            "args": {},
            "description": "Return reads to the old shard when rollback is still available.",
        },
        "finalize_migration": {
            "args": {},
            "description": "Irreversibly finalize a healthy migration.",
        },
        "abort_migration": {
            "args": {},
            "description": "Terminate an unhealthy migration after rollback.",
        },
    },
    "DECISION_THEORETIC": {
        "run_pilot": {"args": {}, "description": "Buy the noisy pilot signal at the stated cost."},
        "buy_annual": {"args": {}, "description": "Commit to the annual purchase."},
        "decline": {"args": {}, "description": "Decline the annual purchase."},
    },
}


STATE_GUIDANCE: dict[str, dict[str, str]] = {
    "DEDUCTIVE_CONSTRAINT": {
        "CONSTRAINTS": "payload.constraints must list at least two task-determining constraints.",
        "DERIVATION": "payload.supporting_constraints must list at least one constraint and payload.conclusion must state the derived service-restoration feasibility claim.",
        "BOUNDARY_CHECK": "payload.boundary_test must state the candidate service-restoration boundary being checked.",
        "CONCLUSION": "payload.decision must state the final service-restoration commitment.",
    },
    "ABDUCTIVE_DIAGNOSTIC": {
        "HYPOTHESES": "payload.hypotheses must contain at least two distinct candidate causes.",
        "PREDICTIONS": "payload.predictions must contain predictions for at least two hypotheses.",
        "DISCRIMINATING_CHECK": "payload.check states why the selected evidence discriminates alternatives.",
        "UPDATE": "payload.ranking must contain at least two hypotheses and payload.evidence_used must name the newly acquired evidence.",
        "RANKING": "payload.decision names the committed cause and payload.residual_uncertainty records remaining uncertainty.",
    },
    "SEARCH_PLANNING": {
        "ACTIONS": "payload.actions must list at least two relevant possible actions.",
        "CANDIDATE_PATHS": "payload.paths must list at least two materially different paths.",
        "CONSTRAINT_CHECK": "payload.constraints must list at least one binding prerequisite.",
        "BRANCH_OR_COMMIT": "payload.selected_path states the chosen path.",
        "CHECKPOINT": "payload.checkpoint states what is being checked before irreversible commitment.",
        "RECOVERY": "payload.recovery states the recovery decision.",
        "FINISH": "payload.decision states finalize/abort.",
    },
    "DECISION_THEORETIC": {
        "OUTCOMES": "payload.outcomes must represent at least two action/outcome alternatives.",
        "UNCERTAINTY": "payload.decision_relevant_uncertainty identifies the uncertainty that can change the decision.",
        "ASYMMETRIC_VALUE": "payload.value_comparison summarizes asymmetric value/cost tradeoffs.",
        "INFORMATION_VALUE": "payload.information_value states whether the pilot is worth buying.",
        "DECISION": "payload.decision states buy_annual or decline.",
        "REVERSAL_CONDITION": "payload.change_if states what evidence/assumption would reverse the decision.",
    },
}


SPECIALIST_SYSTEM_V02 = """You are executing an externally enforced reasoning protocol in a decision environment. Return JSON only. Do not reveal or simulate hidden chain-of-thought; put only concise public decision state in the requested payload. For the chosen legal next state, obey BOTH its payload_contract and action_contract exactly. The action_contract explicitly states whether an environment action is required, optional, or forbidden and lists the only allowed action names. If environment_action_must_be_null is true, environment_action MUST be null. Runtime-invalid transitions or action timing terminate the case; do not rely on a retry."""


def action_catalog(family: str) -> dict[str, dict[str, Any]]:
    return ACTION_CATALOG[family]


def public_history(runtime: ProtocolRuntime) -> list[dict[str, Any]]:
    return [
        {
            "state": item.to_state,
            "public_payload": item.payload,
            "environment_action": item.environment_action,
            "environment_observation": item.environment_observation,
        }
        for item in runtime.trace
    ]


def build_specialist_request(
    case: dict[str, Any],
    env: Any,
    runtime: ProtocolRuntime,
) -> dict[str, Any]:
    """Build the complete model-visible specialist request with no experiment labels."""

    legal = sorted(runtime.legal_next_states())
    family = case["family"]
    return {
        "task": env.task_text(),
        "action_catalog": action_catalog(family),
        "remaining_environment_actions": runtime.spec.action_budget - runtime.actions_used,
        "current_state": runtime.state,
        "legal_next_states": legal,
        "public_history": public_history(runtime),
        "max_transitions": runtime.spec.max_transitions,
        "transitions_used": runtime.transitions_used,
        "next_state_contracts": specialist_next_state_contracts(
            runtime.spec,
            legal,
            env,
            STATE_GUIDANCE[family],
        ),
        "instruction": (
            "Choose exactly one legal next state and satisfy its payload_contract and action_contract. "
            "Return exactly {\"to_state\":\"...\",\"payload\":{...},\"environment_action\":null|\"action_name\",\"action_payload\":{}}."
        ),
    }
