"""Zero-cost protocol runtime for Adaptive Reasoning Controller v0.2 Phase A.

This module makes reasoning protocols explicit state machines. It contains no model
or network calls. A runtime validates legal reasoning-state transitions, accounts
for environment actions, preserves a complete trace, and refuses silent repair of
invalid transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


class ProtocolError(RuntimeError):
    """Base error for protocol/runtime violations."""


class InvalidTransition(ProtocolError):
    pass


class BudgetExceeded(ProtocolError):
    pass


class EnvironmentError(RuntimeError):
    pass


class Environment(Protocol):
    """Common environment contract independent of reasoning protocol."""

    def available_actions(self) -> tuple[str, ...]: ...

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]: ...

    def score(self) -> dict[str, float | int | bool]: ...


@dataclass(frozen=True)
class ProtocolSpec:
    name: str
    start_state: str
    terminal_states: frozenset[str]
    transitions: Mapping[str, frozenset[str]]
    max_transitions: int
    action_budget: int

    def validate(self) -> None:
        keys = set(self.transitions)
        if self.start_state not in keys:
            raise ValueError(f"{self.name}: start state missing from transition map")
        if self.max_transitions < 1:
            raise ValueError(f"{self.name}: max_transitions must be positive")
        if self.action_budget < 0:
            raise ValueError(f"{self.name}: action_budget cannot be negative")
        targets = set().union(*self.transitions.values()) if self.transitions else set()
        dangling = targets - keys
        if dangling:
            raise ValueError(f"{self.name}: transition targets missing from map {sorted(dangling)}")
        unknown_terminals = set(self.terminal_states) - keys
        if unknown_terminals:
            raise ValueError(f"{self.name}: unknown terminal states {sorted(unknown_terminals)}")
        for terminal in self.terminal_states:
            if self.transitions.get(terminal, frozenset()):
                raise ValueError(f"{self.name}: terminal state {terminal} has outgoing transitions")


@dataclass(frozen=True)
class TraceRecord:
    index: int
    from_state: str
    to_state: str
    payload: dict[str, Any]
    environment_action: str | None
    environment_observation: dict[str, Any] | None


@dataclass
class ProtocolRuntime:
    spec: ProtocolSpec
    environment: Environment
    state: str = field(init=False)
    transitions_used: int = field(default=0, init=False)
    actions_used: int = field(default=0, init=False)
    trace: list[TraceRecord] = field(default_factory=list, init=False)
    failed_actions: list[dict[str, Any]] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.spec.validate()
        self.state = self.spec.start_state

    @property
    def terminated(self) -> bool:
        return self.state in self.spec.terminal_states

    def legal_next_states(self) -> frozenset[str]:
        return self.spec.transitions.get(self.state, frozenset())

    def transition(
        self,
        to_state: str,
        payload: Mapping[str, Any],
        *,
        environment_action: str | None = None,
        action_payload: Mapping[str, Any] | None = None,
    ) -> TraceRecord:
        if self.terminated:
            raise InvalidTransition(f"{self.spec.name}: cannot transition after terminal state {self.state}")
        if self.transitions_used >= self.spec.max_transitions:
            raise BudgetExceeded(f"{self.spec.name}: transition budget exhausted")
        if to_state not in self.legal_next_states():
            raise InvalidTransition(
                f"{self.spec.name}: illegal transition {self.state} -> {to_state}; "
                f"legal={sorted(self.legal_next_states())}"
            )
        clean_payload = dict(payload)
        if not clean_payload:
            raise InvalidTransition(f"{self.spec.name}: transition payload must be non-empty")

        observation: dict[str, Any] | None = None
        if environment_action is not None:
            if self.actions_used >= self.spec.action_budget:
                raise BudgetExceeded(f"{self.spec.name}: environment-action budget exhausted")
            available = self.environment.available_actions()
            if environment_action not in available:
                raise EnvironmentError(
                    f"environment action {environment_action!r} unavailable; available={sorted(available)}"
                )
            # Count the attempt before execution so invalid tool/environment calls
            # cannot be used to obtain unbounded retries for free.
            self.actions_used += 1
            try:
                observation = self.environment.step(environment_action, action_payload)
            except Exception as exc:
                self.failed_actions.append(
                    {
                        "from_state": self.state,
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
            environment_observation=observation,
        )
        self.trace.append(record)
        return record

    def finish(self) -> dict[str, Any]:
        if not self.terminated:
            raise InvalidTransition(
                f"{self.spec.name}: cannot finish from non-terminal state {self.state}"
            )
        return {
            "protocol": self.spec.name,
            "terminal_state": self.state,
            "transitions_used": self.transitions_used,
            "actions_used": self.actions_used,
            "failed_actions": list(self.failed_actions),
            "trace": [
                {
                    "index": item.index,
                    "from_state": item.from_state,
                    "to_state": item.to_state,
                    "payload": item.payload,
                    "environment_action": item.environment_action,
                    "environment_observation": item.environment_observation,
                }
                for item in self.trace
            ],
            "environment_score": self.environment.score(),
        }


def _linear(name: str, states: tuple[str, ...], *, action_budget: int) -> ProtocolSpec:
    transitions: dict[str, frozenset[str]] = {}
    for i, state in enumerate(states):
        transitions[state] = frozenset({states[i + 1]}) if i + 1 < len(states) else frozenset()
    return ProtocolSpec(
        name=name,
        start_state=states[0],
        terminal_states=frozenset({states[-1]}),
        transitions=transitions,
        max_transitions=len(states) - 1,
        action_budget=action_budget,
    )


def protocol_specs() -> dict[str, ProtocolSpec]:
    """Return the Phase-A protocol registry.

    Only four protocols are authorized for the first deterministic prototype.
    Causal-experimental and systems-feedback remain design-only until an
    environment provides genuinely discriminating interventions/dynamics.
    """

    return {
        "DEDUCTIVE_CONSTRAINT": _linear(
            "DEDUCTIVE_CONSTRAINT",
            ("PREMISES", "CONSTRAINTS", "DERIVATION", "BOUNDARY_CHECK", "CONCLUSION"),
            action_budget=3,
        ),
        "ABDUCTIVE_DIAGNOSTIC": _linear(
            "ABDUCTIVE_DIAGNOSTIC",
            ("OBSERVATIONS", "HYPOTHESES", "PREDICTIONS", "DISCRIMINATING_CHECK", "UPDATE", "RANKING"),
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
                "RECOVERY": frozenset({"CHECKPOINT", "FINISH"}),
                "FINISH": frozenset(),
            },
            max_transitions=8,
            action_budget=6,
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
            action_budget=3,
        ),
    }


def matched_scaffold_for(spec: ProtocolSpec) -> ProtocolSpec:
    """Generic structured control matched on process and environment budgets.

    Linear protocols receive a linear scaffold with the same required number of
    transitions. SEARCH_PLANNING can terminate in six transitions or consume up
    to eight through recovery; its scaffold mirrors that 6--8 range with a
    generic CHECK/REFINE loop rather than forcing eight steps on every run.
    """

    if spec.name == "SEARCH_PLANNING":
        scaffold = ProtocolSpec(
            name=f"MATCHED_SCAFFOLD__{spec.name}",
            start_state="FRAME",
            terminal_states=frozenset({"DECIDE"}),
            transitions={
                "FRAME": frozenset({"PROCESS_1"}),
                "PROCESS_1": frozenset({"PROCESS_2"}),
                "PROCESS_2": frozenset({"PROCESS_3"}),
                "PROCESS_3": frozenset({"PROCESS_4"}),
                "PROCESS_4": frozenset({"CHECK"}),
                "CHECK": frozenset({"REFINE", "DECIDE"}),
                "REFINE": frozenset({"CHECK", "DECIDE"}),
                "DECIDE": frozenset(),
            },
            max_transitions=spec.max_transitions,
            action_budget=spec.action_budget,
        )
    else:
        states = tuple(["FRAME"] + [f"PROCESS_{i}" for i in range(1, spec.max_transitions)] + ["DECIDE"])
        scaffold = _linear(
            f"MATCHED_SCAFFOLD__{spec.name}",
            states,
            action_budget=spec.action_budget,
        )

    scaffold.validate()
    if scaffold.max_transitions != spec.max_transitions:
        raise AssertionError("matched scaffold transition budget mismatch")
    if scaffold.action_budget != spec.action_budget:
        raise AssertionError("matched scaffold action budget mismatch")
    return scaffold
