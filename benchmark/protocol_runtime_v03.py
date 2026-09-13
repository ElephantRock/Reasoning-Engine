"""Hardened zero-cost protocol runtime for process-constrained ARC Phase B preflight.

This module contains no model or network calls. It turns a reasoning protocol into
an externally validated state machine with payload contracts, action-tag rules,
trace guards, budgets, and complete audit logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


class ProtocolError(RuntimeError):
    pass


class InvalidTransition(ProtocolError):
    pass


class BudgetExceeded(ProtocolError):
    pass


class EnvironmentError(RuntimeError):
    pass


class Environment(Protocol):
    def available_actions(self) -> tuple[str, ...]: ...

    def action_tags(self, action: str) -> frozenset[str]: ...

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]: ...

    def score(self) -> dict[str, float | int | bool | str]: ...


@dataclass(frozen=True)
class TransitionRule:
    required_keys: frozenset[str] = frozenset()
    allowed_action_tags: frozenset[str] = frozenset()
    action_required: bool = False


@dataclass(frozen=True)
class ProtocolSpec:
    name: str
    start_state: str
    terminal_states: frozenset[str]
    transitions: Mapping[str, frozenset[str]]
    rules: Mapping[str, TransitionRule]
    max_transitions: int
    action_budget: int

    def validate(self) -> None:
        if self.start_state not in self.transitions:
            raise ValueError(f"{self.name}: start state missing")
        if self.max_transitions < 1 or self.action_budget < 0:
            raise ValueError(f"{self.name}: invalid budgets")
        states = set(self.transitions)
        for targets in self.transitions.values():
            states.update(targets)
        if not self.terminal_states <= states:
            raise ValueError(f"{self.name}: unknown terminal state")
        for terminal in self.terminal_states:
            if self.transitions.get(terminal, frozenset()):
                raise ValueError(f"{self.name}: terminal state {terminal} has outgoing transitions")
        required_rule_states = states - {self.start_state}
        missing_rules = required_rule_states - set(self.rules)
        if missing_rules:
            raise ValueError(f"{self.name}: missing transition rules for {sorted(missing_rules)}")


@dataclass(frozen=True)
class TraceRecord:
    index: int
    from_state: str
    to_state: str
    payload: dict[str, Any]
    environment_action: str | None
    environment_action_tags: tuple[str, ...]
    environment_observation: dict[str, Any] | None


def _list_at_least(payload: Mapping[str, Any], key: str, n: int) -> None:
    value = payload.get(key)
    if not isinstance(value, list) or len(value) < n:
        raise InvalidTransition(f"payload field {key!r} must be a list with at least {n} items")


def _mapping_or_list_at_least(payload: Mapping[str, Any], key: str, n: int) -> None:
    value = payload.get(key)
    if isinstance(value, list) and len(value) >= n:
        return
    if isinstance(value, dict) and len(value) >= n:
        return
    raise InvalidTransition(f"payload field {key!r} must contain at least {n} entries")


def validate_semantic_payload(protocol: str, state: str, payload: Mapping[str, Any]) -> None:
    """Validate observable public protocol-state content, never hidden cognition."""

    if protocol == "DEDUCTIVE_CONSTRAINT":
        if state == "CONSTRAINTS":
            _list_at_least(payload, "constraints", 2)
        elif state == "DERIVATION":
            _list_at_least(payload, "supporting_constraints", 1)
        elif state == "CONCLUSION" and not str(payload.get("decision", "")).strip():
            raise InvalidTransition("deductive conclusion requires a non-empty decision")

    elif protocol == "ABDUCTIVE_DIAGNOSTIC":
        if state == "HYPOTHESES":
            _list_at_least(payload, "hypotheses", 2)
            normalized = {str(item).strip().lower() for item in payload["hypotheses"]}
            if len(normalized) < 2:
                raise InvalidTransition("abductive hypotheses must contain at least two distinct alternatives")
        elif state == "PREDICTIONS":
            _mapping_or_list_at_least(payload, "predictions", 2)
        elif state == "UPDATE":
            _list_at_least(payload, "ranking", 2)
        elif state == "RANKING":
            if not str(payload.get("decision", "")).strip():
                raise InvalidTransition("diagnostic ranking requires a decision")
            if "residual_uncertainty" not in payload:
                raise InvalidTransition("diagnostic ranking requires residual_uncertainty")

    elif protocol == "SEARCH_PLANNING":
        if state == "ACTIONS":
            _list_at_least(payload, "actions", 2)
        elif state == "CANDIDATE_PATHS":
            _list_at_least(payload, "paths", 2)
        elif state == "CONSTRAINT_CHECK":
            _list_at_least(payload, "constraints", 1)
        elif state == "FINISH" and not str(payload.get("decision", "")).strip():
            raise InvalidTransition("planning finish requires a decision")

    elif protocol == "DECISION_THEORETIC":
        if state == "OUTCOMES":
            _mapping_or_list_at_least(payload, "outcomes", 2)
        elif state == "UNCERTAINTY" and "decision_relevant_uncertainty" not in payload:
            raise InvalidTransition("decision protocol requires decision_relevant_uncertainty")
        elif state == "DECISION" and not str(payload.get("decision", "")).strip():
            raise InvalidTransition("decision state requires a decision")
        elif state == "REVERSAL_CONDITION" and not str(payload.get("change_if", "")).strip():
            raise InvalidTransition("reversal condition requires change_if")


@dataclass
class ProtocolRuntime:
    spec: ProtocolSpec
    environment: Environment
    state: str = field(init=False)
    transitions_used: int = field(default=0, init=False)
    actions_used: int = field(default=0, init=False)
    trace: list[TraceRecord] = field(default_factory=list, init=False)
    failed_requests: list[dict[str, Any]] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.spec.validate()
        self.state = self.spec.start_state

    @property
    def terminated(self) -> bool:
        return self.state in self.spec.terminal_states

    def legal_next_states(self) -> frozenset[str]:
        return self.spec.transitions.get(self.state, frozenset())

    def successful_action_tags(self) -> list[frozenset[str]]:
        return [frozenset(item.environment_action_tags) for item in self.trace if item.environment_action]

    def _guard_history(self, to_state: str) -> None:
        if self.spec.name == "ABDUCTIVE_DIAGNOSTIC" and to_state == "RANKING":
            evidence_actions = sum("EVIDENCE" in tags for tags in self.successful_action_tags())
            if evidence_actions < 2:
                raise InvalidTransition("diagnostic commitment requires at least two successful evidence actions")
        if self.spec.name == "SEARCH_PLANNING" and to_state == "FINISH":
            checkpoint_actions = sum("CHECKPOINT" in tags for tags in self.successful_action_tags())
            if checkpoint_actions < 1:
                raise InvalidTransition("planning finish requires a successful checkpoint action")

    def transition(
        self,
        to_state: str,
        payload: Mapping[str, Any],
        *,
        environment_action: str | None = None,
        action_payload: Mapping[str, Any] | None = None,
    ) -> TraceRecord:
        if self.terminated:
            raise InvalidTransition(f"{self.spec.name}: transition after terminal state {self.state}")
        if self.transitions_used >= self.spec.max_transitions:
            raise BudgetExceeded(f"{self.spec.name}: transition budget exhausted")
        if to_state not in self.legal_next_states():
            raise InvalidTransition(
                f"{self.spec.name}: illegal transition {self.state} -> {to_state}; legal={sorted(self.legal_next_states())}"
            )
        clean_payload = dict(payload)
        if not clean_payload:
            raise InvalidTransition(f"{self.spec.name}: transition payload must be non-empty")

        rule = self.spec.rules[to_state]
        missing = rule.required_keys - set(clean_payload)
        if missing:
            raise InvalidTransition(f"{self.spec.name}:{to_state}: missing payload keys {sorted(missing)}")
        validate_semantic_payload(self.spec.name, to_state, clean_payload)
        self._guard_history(to_state)

        observation: dict[str, Any] | None = None
        tags: frozenset[str] = frozenset()
        if environment_action is None:
            if rule.action_required:
                raise InvalidTransition(f"{self.spec.name}:{to_state}: environment action is required")
        else:
            if self.actions_used >= self.spec.action_budget:
                raise BudgetExceeded(f"{self.spec.name}: environment-action budget exhausted")
            if environment_action not in self.environment.available_actions():
                raise EnvironmentError(f"unknown/unavailable environment action {environment_action!r}")
            tags = self.environment.action_tags(environment_action)
            if rule.allowed_action_tags and not (tags & rule.allowed_action_tags):
                raise InvalidTransition(
                    f"{self.spec.name}:{to_state}: action {environment_action!r} tags={sorted(tags)} "
                    f"do not satisfy allowed tags={sorted(rule.allowed_action_tags)}"
                )
            if not rule.allowed_action_tags:
                raise InvalidTransition(f"{self.spec.name}:{to_state}: environment action not allowed in this state")

            # Every attempted environment action consumes budget, including failures.
            self.actions_used += 1
            try:
                observation = self.environment.step(environment_action, action_payload)
            except Exception as exc:
                self.failed_requests.append(
                    {
                        "state": self.state,
                        "requested_to_state": to_state,
                        "environment_action": environment_action,
                        "action_payload": dict(action_payload or {}),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                raise

        previous = self.state
        self.state = to_state
        self.transitions_used += 1
        record = TraceRecord(
            index=len(self.trace) + 1,
            from_state=previous,
            to_state=to_state,
            payload=clean_payload,
            environment_action=environment_action,
            environment_action_tags=tuple(sorted(tags)),
            environment_observation=observation,
        )
        self.trace.append(record)
        return record

    def finish(self) -> dict[str, Any]:
        if not self.terminated:
            raise InvalidTransition(f"{self.spec.name}: cannot finish from {self.state}")
        return {
            "protocol": self.spec.name,
            "terminal_state": self.state,
            "transitions_used": self.transitions_used,
            "actions_used": self.actions_used,
            "failed_requests": list(self.failed_requests),
            "trace": [
                {
                    "index": item.index,
                    "from_state": item.from_state,
                    "to_state": item.to_state,
                    "payload": item.payload,
                    "environment_action": item.environment_action,
                    "environment_action_tags": list(item.environment_action_tags),
                    "environment_observation": item.environment_observation,
                }
                for item in self.trace
            ],
            "environment_score": self.environment.score(),
        }


def _linear(
    name: str,
    states: tuple[str, ...],
    rules: Mapping[str, TransitionRule],
    *,
    action_budget: int,
) -> ProtocolSpec:
    transitions: dict[str, frozenset[str]] = {}
    for i, state in enumerate(states):
        transitions[state] = frozenset({states[i + 1]}) if i + 1 < len(states) else frozenset()
    return ProtocolSpec(
        name=name,
        start_state=states[0],
        terminal_states=frozenset({states[-1]}),
        transitions=transitions,
        rules=rules,
        max_transitions=len(states) - 1,
        action_budget=action_budget,
    )


def protocol_specs() -> dict[str, ProtocolSpec]:
    return {
        "DEDUCTIVE_CONSTRAINT": _linear(
            "DEDUCTIVE_CONSTRAINT",
            ("PREMISES", "CONSTRAINTS", "DERIVATION", "BOUNDARY_CHECK", "CONCLUSION"),
            {
                "CONSTRAINTS": TransitionRule(frozenset({"constraints"}), frozenset({"INSPECT"})),
                "DERIVATION": TransitionRule(frozenset({"supporting_constraints", "conclusion"})),
                "BOUNDARY_CHECK": TransitionRule(frozenset({"boundary_test"}), frozenset({"TEST"}), True),
                "CONCLUSION": TransitionRule(frozenset({"decision"}), frozenset({"COMMIT"}), True),
            },
            action_budget=3,
        ),
        "ABDUCTIVE_DIAGNOSTIC": _linear(
            "ABDUCTIVE_DIAGNOSTIC",
            ("OBSERVATIONS", "HYPOTHESES", "PREDICTIONS", "DISCRIMINATING_CHECK", "UPDATE", "RANKING"),
            {
                "HYPOTHESES": TransitionRule(frozenset({"hypotheses"})),
                "PREDICTIONS": TransitionRule(frozenset({"predictions"})),
                "DISCRIMINATING_CHECK": TransitionRule(frozenset({"check"}), frozenset({"EVIDENCE"}), True),
                "UPDATE": TransitionRule(frozenset({"ranking", "evidence_used"}), frozenset({"EVIDENCE"}), True),
                "RANKING": TransitionRule(
                    frozenset({"decision", "residual_uncertainty"}), frozenset({"COMMIT"}), True
                ),
            },
            action_budget=3,
        ),
        "SEARCH_PLANNING": ProtocolSpec(
            name="SEARCH_PLANNING",
            start_state="STATE",
            terminal_states=frozenset({"FINISH"}),
            transitions={
                "STATE": frozenset({"ACTIONS"}),
                "ACTIONS": frozenset({"CANDIDATE_PATHS"}),
                "CANDIDATE_PATHS": frozenset({"CONSTRAINT_CHECK"}),
                "CONSTRAINT_CHECK": frozenset({"BRANCH_OR_COMMIT"}),
                "BRANCH_OR_COMMIT": frozenset({"CHECKPOINT"}),
                "CHECKPOINT": frozenset({"RECOVERY", "FINISH"}),
                "RECOVERY": frozenset({"FINISH"}),
                "FINISH": frozenset(),
            },
            rules={
                "ACTIONS": TransitionRule(frozenset({"actions"}), frozenset({"EXECUTE"}), True),
                "CANDIDATE_PATHS": TransitionRule(frozenset({"paths"}), frozenset({"EXECUTE"}), True),
                "CONSTRAINT_CHECK": TransitionRule(frozenset({"constraints"}), frozenset({"CHECK"}), True),
                "BRANCH_OR_COMMIT": TransitionRule(frozenset({"selected_path"}), frozenset({"EXECUTE"}), True),
                "CHECKPOINT": TransitionRule(frozenset({"checkpoint"}), frozenset({"CHECKPOINT"}), True),
                "RECOVERY": TransitionRule(frozenset({"recovery"}), frozenset({"ROLLBACK"}), True),
                "FINISH": TransitionRule(frozenset({"decision"}), frozenset({"COMMIT"}), True),
            },
            max_transitions=7,
            action_budget=7,
        ),
        "DECISION_THEORETIC": _linear(
            "DECISION_THEORETIC",
            (
                "ACTIONS",
                "OUTCOMES",
                "UNCERTAINTY",
                "ASYMMETRIC_VALUE",
                "INFORMATION_VALUE",
                "DECISION",
                "REVERSAL_CONDITION",
            ),
            {
                "OUTCOMES": TransitionRule(frozenset({"outcomes"})),
                "UNCERTAINTY": TransitionRule(frozenset({"decision_relevant_uncertainty"})),
                "ASYMMETRIC_VALUE": TransitionRule(frozenset({"value_comparison"})),
                "INFORMATION_VALUE": TransitionRule(frozenset({"information_value"}), frozenset({"EVIDENCE"})),
                "DECISION": TransitionRule(frozenset({"decision"}), frozenset({"COMMIT"}), True),
                "REVERSAL_CONDITION": TransitionRule(frozenset({"change_if"})),
            },
            action_budget=2,
        ),
    }


def matched_scaffold_for(spec: ProtocolSpec) -> ProtocolSpec:
    """Generic structure matched on maximum transitions and action budget.

    The scaffold omits specialist semantic validation and action-tag timing. Its
    environment action universe is still the exact same environment object.
    """

    states = tuple(["FRAME"] + [f"PROCESS_{i}" for i in range(1, spec.max_transitions)] + ["DECIDE"])
    transitions: dict[str, frozenset[str]] = {}
    rules: dict[str, TransitionRule] = {}
    for i, state in enumerate(states):
        transitions[state] = frozenset({states[i + 1]}) if i + 1 < len(states) else frozenset()
        if i > 0:
            rules[state] = TransitionRule(frozenset({"analysis"}), frozenset({"ANY"}))
    # Generic action timing is intentionally unconstrained. The experiment runner
    # interprets ANY as permitting any environment action while preserving the
    # same action budget. This spec is used for budget/turn matching in preflight.
    return ProtocolSpec(
        name=f"MATCHED_SCAFFOLD__{spec.name}",
        start_state=states[0],
        terminal_states=frozenset({states[-1]}),
        transitions=transitions,
        rules=rules,
        max_transitions=spec.max_transitions,
        action_budget=spec.action_budget,
    )
