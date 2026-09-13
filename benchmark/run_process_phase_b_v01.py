#!/usr/bin/env python3
"""Interactive runner for the frozen Process-Constrained ARC Phase B v0.1 design.

The primary endpoint is environment-derived. No LLM judge is used. The module is
structured so execution logic can be tested with a zero-cost stub model; the
Z.AI adapter is imported only by `zai_model_call`.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Mapping

from process_phase_b_suite_v01 import CASES, FAMILIES, make_environment, validate_suite
from protocol_runtime_v03 import EnvironmentError, InvalidTransition, ProtocolRuntime, protocol_specs, matched_scaffold_for
import reasoning_policies_v02 as frozen_policies

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_process_phase_b_v01"
CONDITIONS = ("SPECIALIST", "MATCHED_SCAFFOLD", "FULL", "CONTROL")
TARGET_MODEL = os.getenv("ZAI_TARGET_MODEL", "glm-5.1")
TARGET_CAP = 16384
TEMPERATURE = 0.0
MAX_FORMAT_ATTEMPTS = 2  # initial call + one formatting/schema-only repair

# The final executable authorization will freeze Git blob identities separately.
FROZEN_FULL = frozen_policies.FULL

ModelCall = Callable[[str | None, dict[str, Any]], dict[str, Any]]


class TechnicalIncomplete(RuntimeError):
    """A target call was technically incomplete; stop before scientific interpretation."""


class FormatFailure(RuntimeError):
    pass


ACTION_CATALOG: dict[str, dict[str, dict[str, Any]]] = {
    "DEDUCTIVE_CONSTRAINT": {
        "inspect_constraints": {"args": {}, "description": "Return the public task constraints in structured form."},
        "test_candidate": {"args": {"restart_minute": "integer"}, "description": "Test one proposed restart minute; returns feasibility but not the optimum."},
        "commit_restart": {"args": {"restart_minute": "integer"}, "description": "Commit the final restart minute."},
    },
    "ABDUCTIVE_DIAGNOSTIC": {
        "check_network": {"args": {}, "description": "Check whether a network anomaly is present."},
        "compare_zones": {"args": {}, "description": "Check whether the pattern is localized by zone."},
        "inspect_pool": {"args": {}, "description": "Check whether the connection pool shows an anomaly."},
        "diagnose": {"args": {"cause": "route_change|library_regression|pool_exhaustion|upstream_policy"}, "description": "Commit the dominant cause."},
    },
    "SEARCH_PLANNING": {
        "enable_dual_write": {"args": {}, "description": "Enable dual writes to old and new shards."},
        "backfill": {"args": {}, "description": "Backfill historical rows."},
        "verify_checksum": {"args": {}, "description": "Verify the copied data."},
        "shift_reads": {"args": {"percent": "10..100 in increments of 10"}, "description": "Move reads toward the new shard."},
        "probe_health": {"args": {}, "description": "Observe new-shard health after all reads are on it."},
        "rollback_reads": {"args": {}, "description": "Return reads to the old shard when rollback is still available."},
        "finalize_migration": {"args": {}, "description": "Irreversibly finalize a healthy migration."},
        "abort_migration": {"args": {}, "description": "Terminate an unhealthy migration after rollback."},
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
        "DERIVATION": "payload.supporting_constraints must list at least one constraint and payload.conclusion must state the derived feasibility claim.",
        "BOUNDARY_CHECK": "payload.boundary_test must state the candidate/boundary being checked; use a TEST action.",
        "CONCLUSION": "payload.decision must state the final commitment; use a COMMIT action.",
    },
    "ABDUCTIVE_DIAGNOSTIC": {
        "HYPOTHESES": "payload.hypotheses must contain at least two distinct candidate causes.",
        "PREDICTIONS": "payload.predictions must contain predictions for at least two hypotheses.",
        "DISCRIMINATING_CHECK": "payload.check states why the selected evidence discriminates; use an EVIDENCE action.",
        "UPDATE": "payload.ranking must contain at least two hypotheses and payload.evidence_used must name the newly acquired evidence; use a second EVIDENCE action.",
        "RANKING": "payload.decision names the committed cause and payload.residual_uncertainty records remaining uncertainty; use the diagnose COMMIT action.",
    },
    "SEARCH_PLANNING": {
        "ACTIONS": "payload.actions must list at least two relevant possible actions; perform one EXECUTE action.",
        "CANDIDATE_PATHS": "payload.paths must list at least two materially different paths; perform one EXECUTE action.",
        "CONSTRAINT_CHECK": "payload.constraints must list at least one binding prerequisite; perform a CHECK action.",
        "BRANCH_OR_COMMIT": "payload.selected_path states the chosen path; perform one EXECUTE action.",
        "CHECKPOINT": "payload.checkpoint states what is being checked before irreversible commitment; perform the CHECKPOINT action.",
        "RECOVERY": "payload.recovery states the recovery decision; perform a ROLLBACK action.",
        "FINISH": "payload.decision states finalize/abort; perform the appropriate COMMIT action.",
    },
    "DECISION_THEORETIC": {
        "OUTCOMES": "payload.outcomes must represent at least two action/outcome alternatives.",
        "UNCERTAINTY": "payload.decision_relevant_uncertainty identifies the uncertainty that can change the decision.",
        "ASYMMETRIC_VALUE": "payload.value_comparison summarizes asymmetric value/cost tradeoffs.",
        "INFORMATION_VALUE": "payload.information_value states whether the pilot is worth buying; run_pilot is optional here.",
        "DECISION": "payload.decision states buy_annual or decline; use the matching COMMIT action.",
        "REVERSAL_CONDITION": "payload.change_if states what evidence/assumption would reverse the decision; no environment action is needed.",
    },
}

INTERACTIVE_SYSTEM = """You are operating an external decision environment. Return JSON only. Do not reveal or simulate hidden chain-of-thought. Put only concise, public, decision-relevant state in the requested fields. You may use only actions listed in the action catalog. Never invent observations; environment evidence is supplied only after an action is executed."""

GENERIC_SYSTEM = INTERACTIVE_SYSTEM + """
Each substantive turn may either request one listed environment action or use no environment action to deliberate. Return exactly: {\"action\": null|\"action_name\", \"action_payload\": {}, \"public_note\": \"concise rationale or decision state\"}. A terminal decision must be made through the corresponding environment commit action before the turn budget expires."""

SCAFFOLD_SYSTEM = INTERACTIVE_SYSTEM + """
You are in a generic matched structured scaffold. Follow the externally supplied generic next-state structure, but no specialist reasoning method is prescribed. Return exactly: {\"to_state\":\"...\",\"payload\":{\"analysis\":\"concise public state\"},\"environment_action\":null|\"action_name\",\"action_payload\":{}}."""

SPECIALIST_SYSTEM = INTERACTIVE_SYSTEM + """
You are executing an externally enforced reasoning protocol. The runtime supplies the legal next state and public payload contract. Return exactly: {\"to_state\":\"...\",\"payload\":{...},\"environment_action\":null|\"action_name\",\"action_payload\":{}}. Runtime-invalid transitions or semantically invalid action timing terminate the case; do not rely on a retry."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")


def environment_terminal(env: Any) -> bool:
    if hasattr(env, "committed_restart"):
        return env.committed_restart is not None
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
    calls: list[dict[str, Any]] = []
    last_error: Exception | None = None
    repair_context: dict[str, Any] | None = None
    for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
        payload = request if attempt == 1 else {
            **request,
            "format_repair": {
                "instruction": "Return the same intended request in valid JSON matching the required schema. Do not change environment state; no action from the invalid response was executed.",
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
            raise TechnicalIncomplete(f"{call_id}: target call reached completion ceiling")
        try:
            parsed = json.loads(result.get("text") or "")
            if not isinstance(parsed, dict):
                raise ValueError("top-level JSON must be an object")
            return validator(parsed), calls
        except Exception as exc:
            last_error = exc
            repair_context = {"visible_text": result.get("text") or "", "error": f"{type(exc).__name__}: {exc}"}
    raise FormatFailure(f"{call_id}: invalid JSON/schema after one repair: {last_error}")


def zai_model_call(system: str | None, request: dict[str, Any]) -> dict[str, Any]:
    from zai_adapter import DEFAULT_BASE_URL, chat_completion

    if TARGET_MODEL != "glm-5.1":
        raise RuntimeError(f"Phase B target must be glm-5.1, got {TARGET_MODEL}")
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


def _history_from_runtime(runtime: ProtocolRuntime) -> list[dict[str, Any]]:
    return [
        {
            "state": item.to_state,
            "public_payload": item.payload,
            "environment_action": item.environment_action,
            "environment_observation": item.environment_observation,
        }
        for item in runtime.trace
    ]


def _base_request(case: dict[str, Any], env: Any, condition: str, remaining_actions: int) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "task": env.task_text(),
        "condition_interface": condition,
        "action_catalog": action_catalog(case["family"]),
        "remaining_environment_actions": remaining_actions,
    }


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
        request = _base_request(case, env, condition, spec.action_budget - runtime.actions_used)
        request.update({
            "current_state": runtime.state,
            "legal_next_states": legal,
            "public_history": _history_from_runtime(runtime),
            "max_transitions": spec.max_transitions,
            "transitions_used": runtime.transitions_used,
        })
        if condition == "SPECIALIST":
            request["next_state_contracts"] = {state: STATE_GUIDANCE[case["family"]][state] for state in legal}
            request["instruction"] = "Choose exactly one legal next state and satisfy its public contract. All actions remain visible in the common catalog; the runtime enforces protocol-specific timing."
            system = SPECIALIST_SYSTEM
        else:
            request["instruction"] = "Advance to one legal generic next state. payload must be {\"analysis\": \"concise public state\"}. Any listed environment action may be requested or omitted."
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
            runtime.transition(
                parsed["to_state"],
                parsed["payload"],
                environment_action=parsed["environment_action"],
                action_payload=parsed["action_payload"],
            )
        except TechnicalIncomplete:
            raise
        except (FormatFailure, InvalidTransition, EnvironmentError, KeyError, ValueError, TypeError) as exc:
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
        "catastrophic_failure": catastrophic_failure(case["family"], env, status),
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
        request = _base_request(case, env, condition, spec.action_budget - actions_used)
        request.update({
            "public_history": public_history,
            "turn": turn_index,
            "maximum_turns": max_turns,
            "instruction": "Request at most one environment action this turn, or null to deliberate without acting. Commit through an environment decision action before the turn budget expires.",
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
        except TechnicalIncomplete:
            raise
        except FormatFailure as exc:
            status = "execution_failure"
            error = f"{type(exc).__name__}: {exc}"
            break

        action = parsed["action"]
        observation = None
        if action is not None:
            if actions_used >= spec.action_budget:
                status = "execution_failure"
                error = "environment-action budget exhausted"
                break
            if action not in env.available_actions():
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
        "catastrophic_failure": catastrophic_failure(case["family"], env, status),
    }


def catastrophic_failure(family: str, env: Any, status: str) -> bool:
    # The frozen gate is specifically about severe constraint/irreversibility
    # failures, not ordinary wrong answers.
    if family == "DEDUCTIVE_CONSTRAINT":
        committed = getattr(env, "committed_restart", None)
        return bool(committed is not None and committed < env.minimum_restart)
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
        raise ValueError("Phase B aggregation requires the complete frozen 24x4 design")

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
        valid_specialist = sum(run["status"] == "success" and run["environment_complete"] for run in specialist)
        catastrophic_specialist = sum(bool(run["catastrophic_failure"]) for run in specialist)
        catastrophic_matched = sum(bool(run["catastrophic_failure"]) for run in matched)
        eligible = (
            process_effect >= 0.10
            and strict_wins >= 4
            and valid_specialist >= 5
            and catastrophic_specialist <= catastrophic_matched
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
            "phase_c_eligible": eligible,
        })

    eligible = [row["family"] for row in family_rows if row["phase_c_eligible"]]
    if len(eligible) >= 2:
        decision = "DESIGN_PHASE_C_ELIGIBLE_SUBSET"
    elif len(eligible) == 1:
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
        "measurement_version": "process-constrained-phase-b-v0.1",
        "target_model": TARGET_MODEL,
        "temperature": TEMPERATURE,
        "completion_token_ceiling": TARGET_CAP,
        "conditions": list(CONDITIONS),
        "primary_contrast": "SPECIALIST_minus_MATCHED_SCAFFOLD",
        "family_rows": family_rows,
        "eligible_families": eligible,
        "program_decision": decision,
        "condition_usage": condition_usage,
    }


def decision_regret_secondary(case: dict[str, Any], run: dict[str, Any]) -> float | None:
    if case["family"] != "DECISION_THEORETIC":
        return None
    env = make_environment(case)
    score = run["environment_score"]
    # Hindsight oracle knows the realized product state and does not need a pilot.
    oracle = max(env.buy_good_utility, 0.0) if env.hidden_good else max(env.buy_bad_utility, 0.0)
    return float(oracle - float(score.get("realized_utility", 0.0)))


def validate_design() -> None:
    validate_suite()
    if TARGET_MODEL != "glm-5.1":
        raise RuntimeError(f"target model drift: {TARGET_MODEL}")
    if FROZEN_FULL != frozen_policies.FULL:
        raise RuntimeError("FULL prompt drift")
    for family, spec in protocol_specs().items():
        scaffold = matched_scaffold_for(spec)
        if scaffold.action_budget != spec.action_budget:
            raise RuntimeError(f"{family}: action-budget mismatch")
        # Same environment object supplies action universe to every condition.
        case = next(case for case in CASES if case["family"] == family)
        env = make_environment(case)
        if set(env.available_actions()) != set(ACTION_CATALOG[family]):
            raise RuntimeError(f"{family}: action catalog drift")


def main() -> None:
    validate_design()
    if int(os.getenv("ZAI_MAX_TOKENS", "0")) != TARGET_CAP:
        raise RuntimeError(f"ZAI_MAX_TOKENS must be {TARGET_CAP}")
    if float(os.getenv("ZAI_TEMPERATURE", "-1")) != TEMPERATURE:
        raise RuntimeError("ZAI_TEMPERATURE must be 0")
    OUT.mkdir(exist_ok=True)
    runs: list[dict[str, Any]] = []
    runs_path = OUT / "runs.jsonl"
    try:
        for case in CASES:
            for condition in CONDITIONS:
                print("run", case["case_id"], condition, flush=True)
                run = run_case_condition(case, condition, zai_model_call)
                run["decision_regret_secondary"] = decision_regret_secondary(case, run)
                runs.append(run)
                write_jsonl(runs_path, runs)
    except Exception:
        write_jsonl(runs_path, runs)
        partial = {
            "measurement_version": "process-constrained-phase-b-v0.1",
            "records_completed": len(runs),
            "complete": False,
            "runs_sha256": sha256_bytes(runs_path.read_bytes()) if runs_path.exists() else None,
        }
        (OUT / "partial_meta.json").write_text(json.dumps(partial, indent=2), encoding="utf-8")
        raise

    summary = aggregate(runs)
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "measurement_version": "process-constrained-phase-b-v0.1",
        "records": len(runs),
        "runs_sha256": sha256_bytes(runs_path.read_bytes()),
        "summary_sha256": sha256_bytes(summary_path.read_bytes()),
        "complete": True,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"decision": summary["program_decision"], "eligible": summary["eligible_families"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
