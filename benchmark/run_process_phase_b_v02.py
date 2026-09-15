#!/usr/bin/env python3
"""Corrected Process-Constrained ARC Phase B v0.2 runner core.

The primary endpoint is environment-derived. No LLM judge is used. The module is
structured so execution logic can be tested with zero-cost stub models; the Z.AI
adapter is imported only by `zai_model_call`.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable

import reasoning_policies_v02 as frozen_policies
from process_phase_b_interface_v02 import (
    ACTION_CATALOG,
    SPECIALIST_SYSTEM_V02,
    build_specialist_request,
)
from process_phase_b_suite_v02 import CASES, FAMILIES, make_environment, validate_suite
from protocol_runtime_v04 import (
    EnvironmentError,
    InvalidTransition,
    ProtocolRuntime,
    matched_scaffold_for,
    protocol_specs,
    public_action_contract,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_process_phase_b_v02"
CONDITIONS = ("SPECIALIST", "MATCHED_SCAFFOLD", "FULL", "CONTROL")
TARGET_MODEL = os.getenv("ZAI_TARGET_MODEL", "glm-5.1")
TARGET_CAP = 16384
TEMPERATURE = 0.0
MAX_FORMAT_ATTEMPTS = 2
FROZEN_FULL = frozen_policies.FULL

ModelCall = Callable[[str | None, dict[str, Any]], dict[str, Any]]


class RequestFailure(RuntimeError):
    def __init__(self, message: str, calls: list[dict[str, Any]]):
        super().__init__(message)
        self.calls = calls


class TechnicalIncomplete(RequestFailure):
    """A provider/model call was technically incomplete; stop scientific aggregation."""


class FormatFailure(RequestFailure):
    pass


INTERACTIVE_SYSTEM = """You are operating an external decision environment. Return JSON only. Do not reveal or simulate hidden chain-of-thought. Put only concise, public, decision-relevant state in the requested fields. You may use only actions listed in the action catalog. Never invent observations; environment evidence is supplied only after an action is executed."""

GENERIC_SYSTEM = INTERACTIVE_SYSTEM + """
Each substantive turn may either request one listed environment action or use no environment action to deliberate. Return exactly: {\"action\": null|\"action_name\", \"action_payload\": {}, \"public_note\": \"concise rationale or decision state\"}. A terminal decision must be made through the corresponding environment commit action before the turn budget expires."""

SCAFFOLD_SYSTEM = INTERACTIVE_SYSTEM + """
You are in a generic matched structured scaffold. Follow the externally supplied generic next-state structure, but no specialist reasoning method is prescribed. Return exactly: {\"to_state\":\"...\",\"payload\":{\"analysis\":\"concise public state\"},\"environment_action\":null|\"action_name\",\"action_payload\":{}}."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")


def environment_terminal(env: Any) -> bool:
    if hasattr(env, "committed_restoration"):
        return env.committed_restoration is not None
    if hasattr(env, "diagnosis"):
        return env.diagnosis is not None
    if hasattr(env, "finalized") and hasattr(env, "aborted"):
        return bool(env.finalized or env.aborted)
    if hasattr(env, "decision"):
        return env.decision is not None
    raise TypeError(f"unknown environment type {type(env).__name__}")


def action_catalog(family: str) -> dict[str, dict[str, Any]]:
    return ACTION_CATALOG[family]


def _validate_protocol_shape(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value.get("to_state"), str) or not value["to_state"].strip():
        raise ValueError("to_state must be a non-empty string")
    if not isinstance(value.get("payload"), dict):
        raise ValueError("payload must be an object")
    action = value.get("environment_action")
    if action is not None and not isinstance(action, str):
        raise ValueError("environment_action must be string or null")
    action_payload = value.get("action_payload", {})
    if not isinstance(action_payload, dict):
        raise ValueError("action_payload must be an object")
    return {
        "to_state": value["to_state"],
        "payload": value["payload"],
        "environment_action": action,
        "action_payload": action_payload,
    }


def _validate_generic_shape(value: dict[str, Any]) -> dict[str, Any]:
    action = value.get("action")
    if action is not None and not isinstance(action, str):
        raise ValueError("action must be string or null")
    action_payload = value.get("action_payload", {})
    if not isinstance(action_payload, dict):
        raise ValueError("action_payload must be an object")
    note = value.get("public_note")
    if not isinstance(note, str) or not note.strip():
        raise ValueError("public_note must be a non-empty string")
    return {"action": action, "action_payload": action_payload, "public_note": note.strip()}


def request_json(
    model_call: ModelCall,
    system: str | None,
    request: dict[str, Any],
    validator: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    call_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Get one substantive JSON request, permitting one formatting-only repair."""

    calls: list[dict[str, Any]] = []
    repair_context: dict[str, str] | None = None
    last_error: Exception | None = None
    for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
        payload = request if attempt == 1 else {
            **request,
            "format_repair": {
                "instruction": (
                    "Return the same intended request in valid JSON matching the required schema. "
                    "No action from the invalid response was executed; do not change the intended action merely to obtain another attempt."
                ),
                "previous_visible_response": repair_context["visible_text"] if repair_context else "",
                "schema_error": repair_context["error"] if repair_context else "",
            },
        }
        result = model_call(system, payload)
        record = {
            "call_id": call_id,
            "attempt": attempt,
            "request": payload,
            "visible_text": result.get("text") or "",
            "usage": result.get("usage", {}),
            "finish_reason": result.get("finish_reason"),
            "response_id": result.get("response_id"),
        }
        calls.append(record)
        if result.get("finish_reason") == "length":
            raise TechnicalIncomplete(f"{call_id}: completion ceiling reached", calls)
        try:
            parsed = json.loads(result.get("text") or "")
            if not isinstance(parsed, dict):
                raise ValueError("top-level JSON must be an object")
            return validator(parsed), calls
        except Exception as exc:
            last_error = exc
            repair_context = {
                "visible_text": result.get("text") or "",
                "error": f"{type(exc).__name__}: {exc}",
            }
    raise FormatFailure(f"{call_id}: invalid JSON/schema after one repair: {last_error}", calls)


def zai_model_call(system: str | None, request: dict[str, Any]) -> dict[str, Any]:
    from zai_adapter import DEFAULT_BASE_URL, chat_completion

    if TARGET_MODEL != "glm-5.1":
        raise RuntimeError(f"Phase B v0.2 target must be glm-5.1, got {TARGET_MODEL}")
    if int(os.getenv("ZAI_MAX_TOKENS", "0")) != TARGET_CAP:
        raise RuntimeError(f"ZAI_MAX_TOKENS must be {TARGET_CAP}")
    if float(os.getenv("ZAI_TEMPERATURE", "-1")) != TEMPERATURE:
        raise RuntimeError("ZAI_TEMPERATURE must be 0")
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": json.dumps(request, ensure_ascii=False)})
    return chat_completion(
        model=TARGET_MODEL,
        messages=messages,
        json_mode=True,
        api_key=os.environ["ZAI_API_KEY"],
        base_url=os.getenv("ZAI_BASE_URL", DEFAULT_BASE_URL),
        max_tokens_env="ZAI_MAX_TOKENS",
        temperature_env="ZAI_TEMPERATURE",
    )


def _public_base_request(case: dict[str, Any], env: Any, remaining_actions: int) -> dict[str, Any]:
    """Common target-visible request surface; excludes experimental identifiers."""

    return {
        "task": env.task_text(),
        "action_catalog": action_catalog(case["family"]),
        "remaining_environment_actions": remaining_actions,
        "environment_terminal": environment_terminal(env),
    }


def _runtime_history(runtime: ProtocolRuntime) -> list[dict[str, Any]]:
    return [
        {
            "state": item.to_state,
            "public_payload": item.payload,
            "environment_action": item.environment_action,
            "environment_observation": item.environment_observation,
        }
        for item in runtime.trace
    ]


def run_protocol_condition(case: dict[str, Any], condition: str, model_call: ModelCall) -> dict[str, Any]:
    env = make_environment(case)
    specialist = protocol_specs()[case["family"]]
    spec = specialist if condition == "SPECIALIST" else matched_scaffold_for(specialist)
    runtime = ProtocolRuntime(spec, env)
    calls: list[dict[str, Any]] = []
    status = "success"
    error = ""

    while not runtime.terminated:
        turn_index = runtime.transitions_used + 1
        legal = sorted(runtime.legal_next_states())
        if condition == "SPECIALIST":
            request = build_specialist_request(case, env, runtime)
            request["environment_terminal"] = environment_terminal(env)
            system = SPECIALIST_SYSTEM_V02
        else:
            request = _public_base_request(case, env, spec.action_budget - runtime.actions_used)
            request.update({
                "current_state": runtime.state,
                "legal_next_states": legal,
                "public_history": _runtime_history(runtime),
                "max_transitions": spec.max_transitions,
                "transitions_used": runtime.transitions_used,
                "instruction": (
                    "Advance to exactly one legal generic next state. payload must be {\"analysis\": \"concise public state\"}. "
                    "Any listed environment action may be requested or omitted while the environment is non-terminal. "
                    "If environment_terminal is true, environment_action must be null."
                ),
            })
            system = SCAFFOLD_SYSTEM

        try:
            parsed, turn_calls = request_json(
                model_call,
                system,
                request,
                _validate_protocol_shape,
                call_id=f"{case['case_id']}:{condition}:turn:{turn_index}",
            )
            calls.extend(turn_calls)
            if environment_terminal(env) and parsed["environment_action"] is not None:
                raise InvalidTransition("environment is already terminal; no further environment action is legal")
            runtime.transition(
                parsed["to_state"],
                parsed["payload"],
                environment_action=parsed["environment_action"],
                action_payload=parsed["action_payload"],
            )
        except TechnicalIncomplete as exc:
            calls.extend(exc.calls)
            raise TechnicalIncomplete(str(exc), calls) from exc
        except FormatFailure as exc:
            calls.extend(exc.calls)
            status = "execution_failure"
            error = str(exc)
            break
        except (InvalidTransition, EnvironmentError, KeyError, ValueError, TypeError) as exc:
            status = "execution_failure"
            error = f"{type(exc).__name__}: {exc}"
            break

    protocol_complete = runtime.terminated
    env_complete = environment_terminal(env)
    if status == "success" and (not protocol_complete or not env_complete):
        status = "execution_failure"
        error = "protocol/environment did not both reach valid terminal state"

    env_score = env.score()
    effective_score = float(env_score.get("normalized_score", 0.0)) if status == "success" else 0.0
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "condition": condition,
        "status": status,
        "error": error,
        "protocol_complete": protocol_complete,
        "environment_complete": env_complete,
        "transitions_used": runtime.transitions_used,
        "actions_used": runtime.actions_used,
        "failed_requests": list(runtime.failed_requests),
        "trace": [asdict(item) for item in runtime.trace],
        "environment_score": env_score,
        "effective_normalized_score": effective_score,
        "model_calls": calls,
        "catastrophic_failure": catastrophic_failure(case["family"], env),
    }


def run_generic_condition(case: dict[str, Any], condition: str, model_call: ModelCall) -> dict[str, Any]:
    env = make_environment(case)
    spec = protocol_specs()[case["family"]]
    max_turns = spec.max_transitions
    calls: list[dict[str, Any]] = []
    public_history: list[dict[str, Any]] = []
    actions_used = 0
    failed_requests: list[dict[str, Any]] = []
    status = "success"
    error = ""

    system = GENERIC_SYSTEM if condition == "CONTROL" else FROZEN_FULL + "\n\n" + GENERIC_SYSTEM
    for turn_index in range(1, max_turns + 1):
        if environment_terminal(env):
            break
        request = _public_base_request(case, env, spec.action_budget - actions_used)
        request.update({
            "public_history": public_history,
            "turn": turn_index,
            "maximum_turns": max_turns,
            "instruction": (
                "Request at most one environment action this turn, or null to deliberate without acting. "
                "Commit through an environment decision action before the turn budget expires."
            ),
        })
        try:
            parsed, turn_calls = request_json(
                model_call,
                system,
                request,
                _validate_generic_shape,
                call_id=f"{case['case_id']}:{condition}:turn:{turn_index}",
            )
            calls.extend(turn_calls)
        except TechnicalIncomplete as exc:
            calls.extend(exc.calls)
            raise TechnicalIncomplete(str(exc), calls) from exc
        except FormatFailure as exc:
            calls.extend(exc.calls)
            status = "execution_failure"
            error = str(exc)
            break

        action = parsed["action"]
        observation = None
        if action is not None:
            if actions_used >= spec.action_budget:
                failed_requests.append({
                    "turn": turn_index,
                    "environment_action": action,
                    "error": "action budget exhausted",
                })
                status = "execution_failure"
                error = "environment-action budget exhausted"
                break
            if action not in env.available_actions():
                failed_requests.append({
                    "turn": turn_index,
                    "environment_action": action,
                    "error": "unknown environment action",
                })
                status = "execution_failure"
                error = f"unknown environment action {action!r}"
                break
            actions_used += 1
            try:
                observation = env.step(action, parsed["action_payload"])
            except Exception as exc:
                failed_requests.append({
                    "turn": turn_index,
                    "environment_action": action,
                    "action_payload": parsed["action_payload"],
                    "error": f"{type(exc).__name__}: {exc}",
                })
                status = "execution_failure"
                error = f"{type(exc).__name__}: {exc}"
                break
        public_history.append({
            "turn": turn_index,
            "public_note": parsed["public_note"],
            "environment_action": action,
            "environment_observation": observation,
        })

    env_complete = environment_terminal(env)
    if status == "success" and not env_complete:
        status = "execution_failure"
        error = "environment did not reach valid terminal state within turn budget"

    env_score = env.score()
    effective_score = float(env_score.get("normalized_score", 0.0)) if status == "success" else 0.0
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "condition": condition,
        "status": status,
        "error": error,
        "protocol_complete": None,
        "environment_complete": env_complete,
        "transitions_used": len(public_history),
        "actions_used": actions_used,
        "failed_requests": failed_requests,
        "trace": public_history,
        "environment_score": env_score,
        "effective_normalized_score": effective_score,
        "model_calls": calls,
        "catastrophic_failure": catastrophic_failure(case["family"], env),
    }


def catastrophic_failure(family: str, env: Any) -> bool:
    if family == "DEDUCTIVE_CONSTRAINT":
        committed = getattr(env, "committed_restoration", None)
        return bool(committed is not None and committed < env.minimum_restoration)
    if family == "SEARCH_PLANNING":
        return bool(getattr(env, "violations", 0) > 0)
    return False


def run_case_condition(case: dict[str, Any], condition: str, model_call: ModelCall) -> dict[str, Any]:
    if condition in {"SPECIALIST", "MATCHED_SCAFFOLD"}:
        return run_protocol_condition(case, condition, model_call)
    if condition in {"FULL", "CONTROL"}:
        return run_generic_condition(case, condition, model_call)
    raise ValueError(f"unknown condition {condition!r}")


def _usage_total(run: dict[str, Any], key: str) -> float:
    return sum(float((call.get("usage") or {}).get(key, 0) or 0) for call in run.get("model_calls", []))


def aggregate(runs: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {(case["case_id"], condition) for case in CASES for condition in CONDITIONS}
    keys = [(run["case_id"], run["condition"]) for run in runs]
    if len(runs) != 96 or len(set(keys)) != 96 or set(keys) != expected:
        raise ValueError("Phase B v0.2 aggregation requires the complete frozen 24x4 design")

    index = {(run["case_id"], run["condition"]): run for run in runs}
    family_rows: list[dict[str, Any]] = []
    for family in FAMILIES:
        cases = [case for case in CASES if case["family"] == family]
        specialist = [index[(case["case_id"], "SPECIALIST")] for case in cases]
        matched = [index[(case["case_id"], "MATCHED_SCAFFOLD")] for case in cases]
        full = [index[(case["case_id"], "FULL")] for case in cases]
        control = [index[(case["case_id"], "CONTROL")] for case in cases]
        spec_scores = [float(run["effective_normalized_score"]) for run in specialist]
        matched_scores = [float(run["effective_normalized_score"]) for run in matched]
        case_lifts = [spec_scores[i] - matched_scores[i] for i in range(6)]
        process_effect = mean(case_lifts)
        strict_wins = sum(lift > 0 for lift in case_lifts)
        valid_specialist = sum(
            run["status"] == "success" and run["environment_complete"] for run in specialist
        )
        catastrophic_specialist = sum(bool(run["catastrophic_failure"]) for run in specialist)
        catastrophic_matched = sum(bool(run["catastrophic_failure"]) for run in matched)
        comparison_access_valid = True  # mechanically checked by validate_design/static CI
        eligible = (
            process_effect >= 0.10
            and strict_wins >= 4
            and valid_specialist >= 5
            and catastrophic_specialist <= catastrophic_matched
            and comparison_access_valid
        )
        family_rows.append({
            "family": family,
            "specialist_mean": mean(spec_scores),
            "matched_scaffold_mean": mean(matched_scores),
            "full_mean": mean(float(run["effective_normalized_score"]) for run in full),
            "control_mean": mean(float(run["effective_normalized_score"]) for run in control),
            "process_effect": process_effect,
            "strict_case_wins": strict_wins,
            "case_lifts": {case["case_id"]: case_lifts[i] for i, case in enumerate(cases)},
            "valid_specialist_executions": valid_specialist,
            "specialist_catastrophic_failures": catastrophic_specialist,
            "matched_catastrophic_failures": catastrophic_matched,
            "comparison_access_valid": comparison_access_valid,
            "phase_c_eligible": eligible,
        })

    eligible_families = [row["family"] for row in family_rows if row["phase_c_eligible"]]
    if len(eligible_families) >= 2:
        decision = "DESIGN_PHASE_C_ELIGIBLE_SUBSET"
    elif len(eligible_families) == 1:
        decision = "ONE_SPECIALIST_NO_SELECTOR"
    else:
        decision = "STOP_PROCESS_CONSTRAINED_SELECTOR_PATH"

    condition_usage: dict[str, dict[str, float]] = {}
    for condition in CONDITIONS:
        subset = [run for run in runs if run["condition"] == condition]
        condition_usage[condition] = {
            "mean_model_calls": mean(len(run["model_calls"]) for run in subset),
            "mean_input_tokens": mean(_usage_total(run, "input_tokens") for run in subset),
            "mean_output_tokens": mean(_usage_total(run, "output_tokens") for run in subset),
            "mean_latency_ms": mean(_usage_total(run, "latency_ms") for run in subset),
            "mean_environment_actions": mean(float(run["actions_used"]) for run in subset),
            "execution_failure_rate": mean(1.0 if run["status"] != "success" else 0.0 for run in subset),
        }

    return {
        "measurement_version": "process-constrained-phase-b-v0.2",
        "target_model": TARGET_MODEL,
        "temperature": TEMPERATURE,
        "completion_token_ceiling": TARGET_CAP,
        "conditions": list(CONDITIONS),
        "primary_contrast": "SPECIALIST_minus_MATCHED_SCAFFOLD",
        "family_rows": family_rows,
        "eligible_families": eligible_families,
        "program_decision": decision,
        "condition_usage": condition_usage,
    }


def decision_regret_secondary(case: dict[str, Any], run: dict[str, Any]) -> float | None:
    if case["family"] != "DECISION_THEORETIC":
        return None
    env = make_environment(case)
    score = run["environment_score"]
    oracle = max(env.buy_good_utility, 0.0) if env.hidden_good else max(env.buy_bad_utility, 0.0)
    return float(oracle - float(score.get("realized_utility", 0.0)))


def validate_design() -> None:
    validate_suite()
    if TARGET_MODEL != "glm-5.1":
        raise RuntimeError(f"target model drift: {TARGET_MODEL}")
    if FROZEN_FULL != frozen_policies.FULL:
        raise RuntimeError("FULL prompt drift")
    for family, specialist in protocol_specs().items():
        scaffold = matched_scaffold_for(specialist)
        if scaffold.action_budget != specialist.action_budget:
            raise RuntimeError(f"{family}: action-budget mismatch")
        if scaffold.max_transitions != specialist.max_transitions:
            raise RuntimeError(f"{family}: max-transition mismatch")
        case = next(case for case in CASES if case["family"] == family)
        env = make_environment(case)
        if set(env.available_actions()) != set(ACTION_CATALOG[family]):
            raise RuntimeError(f"{family}: action catalog drift")
        for state, rule in specialist.rules.items():
            contract = public_action_contract(specialist, state, env)
            if rule.action_required and not contract["allowed_action_names"]:
                raise RuntimeError(f"{family}/{state}: required action has no public legal action")
            if not rule.allowed_action_tags:
                if not contract["environment_action_must_be_null"] or contract["allowed_action_names"]:
                    raise RuntimeError(f"{family}/{state}: no-action contract drift")


if __name__ == "__main__":
    validate_design()
    print("Process-Constrained Phase B v0.2 runner design validated; no paid run launched")
