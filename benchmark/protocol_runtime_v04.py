"""Phase-B v0.2 protocol-interface correction.

The underlying v0.3 state-machine semantics remain frozen and reusable. This
module adds a target-visible action contract derived mechanically from the same
TransitionRule and environment action tags that the runtime enforces.
"""

from __future__ import annotations

from typing import Any

from protocol_runtime_v03 import (  # re-export the frozen enforcement surface
    BudgetExceeded,
    Environment,
    EnvironmentError,
    InvalidTransition,
    ProtocolError,
    ProtocolRuntime,
    ProtocolSpec,
    TraceRecord,
    TransitionRule,
    matched_scaffold_for,
    protocol_specs,
    validate_semantic_payload,
)


def public_action_contract(spec: ProtocolSpec, to_state: str, environment: Environment) -> dict[str, Any]:
    """Return the exact environment-action legality enforced for `to_state`.

    This is intentionally derived from the runtime rule rather than duplicated in
    prose. In particular, an empty allowed-tag set is exposed as an explicit
    no-action contract instead of relying on the model to infer a negative rule.
    """

    if to_state not in spec.rules:
        raise KeyError(f"{spec.name}: no transition rule for {to_state!r}")
    rule = spec.rules[to_state]
    allowed_tags = set(rule.allowed_action_tags)

    if not allowed_tags:
        return {
            "environment_action_mode": "forbidden",
            "environment_action_required": False,
            "environment_action_must_be_null": True,
            "allowed_action_tags": [],
            "allowed_action_names": [],
        }

    available = list(environment.available_actions())
    if "ANY" in allowed_tags:
        allowed_names = available
    else:
        allowed_names = [
            action
            for action in available
            if set(environment.action_tags(action)) & allowed_tags
        ]

    return {
        "environment_action_mode": "required" if rule.action_required else "optional",
        "environment_action_required": bool(rule.action_required),
        "environment_action_must_be_null": False,
        "allowed_action_tags": sorted(allowed_tags),
        "allowed_action_names": allowed_names,
    }


def specialist_next_state_contracts(
    spec: ProtocolSpec,
    legal_next_states: list[str] | tuple[str, ...],
    environment: Environment,
    state_guidance: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Build one complete public semantic + action contract per legal next state."""

    return {
        state: {
            "payload_contract": state_guidance[state],
            "action_contract": public_action_contract(spec, state, environment),
        }
        for state in legal_next_states
    }
