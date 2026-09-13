#!/usr/bin/env python3
"""Reviewed executable wrapper for Process-Constrained ARC Phase B v0.1.

`run_process_phase_b_v01.py` contains the frozen study constants, prompts,
validation helpers, and aggregation logic. This module is the executable path. It
adds lossless call logging for failed/technical requests and prevents any further
environment action after the environment has reached a terminal commitment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

import run_process_phase_b_v01 as core
from process_phase_b_suite_v01 import CASES, make_environment
from protocol_runtime_v03 import EnvironmentError, InvalidTransition, ProtocolRuntime, matched_scaffold_for, protocol_specs

OUT = Path(__file__).resolve().parent / "results_process_phase_b_v01"
ModelCall = Callable[[str | None, dict[str, Any]], dict[str, Any]]


class RequestFailure(RuntimeError):
    def __init__(self, message: str, calls: list[dict[str, Any]]):
        super().__init__(message)
        self.calls = calls


class TechnicalIncomplete(RequestFailure):
    pass


class FormatFailure(RequestFailure):
    pass


def request_json(
    model_call: ModelCall,
    system: str | None,
    request: dict[str, Any],
    validator: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    call_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Get one substantive JSON request, permitting one formatting-only repair.

    No environment state is mutated until this function returns a valid object.
    Every completed model call is preserved even when the request ultimately
    fails or hits the completion ceiling.
    """

    calls: list[dict[str, Any]] = []
    repair_context: dict[str, str] | None = None
    last_error: Exception | None = None
    for attempt in range(1, core.MAX_FORMAT_ATTEMPTS + 1):
        payload = request if attempt == 1 else {
            **request,
            "format_repair": {
                "instruction": "Return the same intended request in valid JSON matching the required schema. No action from the invalid response was executed; do not change the intended action merely to obtain another attempt.",
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
        request = core._base_request(case, env, condition, spec.action_budget - runtime.actions_used)
        request.update({
            "current_state": runtime.state,
            "legal_next_states": legal,
            "public_history": core._history_from_runtime(runtime),
            "max_transitions": spec.max_transitions,
            "transitions_used": runtime.transitions_used,
        })
        if condition == "SPECIALIST":
            request["next_state_contracts"] = {
                state: core.STATE_GUIDANCE[case["family"]][state] for state in legal
            }
            request["instruction"] = (
                "Choose exactly one legal next state and satisfy its public contract. All actions remain visible in "
                "the common catalog; the runtime enforces protocol-specific timing."
            )
            system = core.SPECIALIST_SYSTEM
        else:
            request["instruction"] = (
                "Advance to one legal generic next state. payload must be {\"analysis\": \"concise public state\"}. "
                "Any listed environment action may be requested or omitted."
            )
            system = core.SCAFFOLD_SYSTEM

        try:
            parsed, turn_calls = request_json(
                model_call,
                system,
                request,
                core._validate_protocol_shape,
                call_id=f"{case['case_id']}:{condition}:turn:{turn_index}",
            )
            calls.extend(turn_calls)
            if core.environment_terminal(env) and parsed["environment_action"] is not None:
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
    env_complete = core.environment_terminal(env)
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
        "trace": [core.asdict(item) for item in runtime.trace],
        "environment_score": env_score,
        "effective_normalized_score": effective_score,
        "model_calls": calls,
        "catastrophic_failure": core.catastrophic_failure(case["family"], env, status),
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

    system = core.GENERIC_SYSTEM if condition == "CONTROL" else core.FROZEN_FULL + "\n\n" + core.GENERIC_SYSTEM
    for turn_index in range(1, max_turns + 1):
        if core.environment_terminal(env):
            break
        request = core._base_request(case, env, condition, spec.action_budget - actions_used)
        request.update({
            "public_history": public_history,
            "turn": turn_index,
            "maximum_turns": max_turns,
            "instruction": (
                "Request at most one environment action this turn, or null to deliberate without acting. Commit "
                "through an environment decision action before the turn budget expires."
            ),
        })
        try:
            parsed, turn_calls = request_json(
                model_call,
                system,
                request,
                core._validate_generic_shape,
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
                failed_requests.append({"turn": turn_index, "environment_action": action, "error": "action budget exhausted"})
                status = "execution_failure"
                error = "environment-action budget exhausted"
                break
            if action not in env.available_actions():
                failed_requests.append({"turn": turn_index, "environment_action": action, "error": "unknown environment action"})
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

    env_complete = core.environment_terminal(env)
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
        "catastrophic_failure": core.catastrophic_failure(case["family"], env, status),
    }


def run_case_condition(case: dict[str, Any], condition: str, model_call: ModelCall) -> dict[str, Any]:
    if condition in {"SPECIALIST", "MATCHED_SCAFFOLD"}:
        return run_protocol_condition(case, condition, model_call)
    if condition in {"FULL", "CONTROL"}:
        return run_generic_condition(case, condition, model_call)
    raise ValueError(f"unknown condition {condition!r}")


def technical_partial_run(case: dict[str, Any], condition: str, exc: Exception) -> dict[str, Any]:
    calls = exc.calls if isinstance(exc, RequestFailure) else []
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "condition": condition,
        "status": "technical_incomplete",
        "error": f"{type(exc).__name__}: {exc}",
        "protocol_complete": False,
        "environment_complete": False,
        "transitions_used": None,
        "actions_used": None,
        "failed_requests": [],
        "trace": [],
        "environment_score": {},
        "effective_normalized_score": None,
        "model_calls": calls,
        "catastrophic_failure": False,
    }


def main() -> None:
    core.validate_design()
    if int(os.getenv("ZAI_MAX_TOKENS", "0")) != core.TARGET_CAP:
        raise RuntimeError(f"ZAI_MAX_TOKENS must be {core.TARGET_CAP}")
    if float(os.getenv("ZAI_TEMPERATURE", "-1")) != core.TEMPERATURE:
        raise RuntimeError("ZAI_TEMPERATURE must be 0")

    OUT.mkdir(exist_ok=True)
    runs: list[dict[str, Any]] = []
    runs_path = OUT / "runs.jsonl"
    for case in CASES:
        for condition in core.CONDITIONS:
            print("run", case["case_id"], condition, flush=True)
            try:
                run = run_case_condition(case, condition, core.zai_model_call)
            except Exception as exc:
                # Transport/API failures and completion-ceiling failures are
                # technical interruptions, not scientific zeroes. Preserve the
                # partial call record and stop the study before interpretation.
                runs.append(technical_partial_run(case, condition, exc))
                core.write_jsonl(runs_path, runs)
                partial = {
                    "measurement_version": "process-constrained-phase-b-v0.1",
                    "records_written": len(runs),
                    "complete": False,
                    "interrupted_at": {"case_id": case["case_id"], "condition": condition},
                    "error": f"{type(exc).__name__}: {exc}",
                    "runs_sha256": core.sha256_bytes(runs_path.read_bytes()),
                }
                (OUT / "partial_meta.json").write_text(json.dumps(partial, indent=2), encoding="utf-8")
                raise
            run["decision_regret_secondary"] = core.decision_regret_secondary(case, run)
            runs.append(run)
            core.write_jsonl(runs_path, runs)

    summary = core.aggregate(runs)
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "measurement_version": "process-constrained-phase-b-v0.1",
        "records": len(runs),
        "runs_sha256": core.sha256_bytes(runs_path.read_bytes()),
        "summary_sha256": core.sha256_bytes(summary_path.read_bytes()),
        "complete": True,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"decision": summary["program_decision"], "eligible": summary["eligible_families"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
