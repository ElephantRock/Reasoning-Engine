#!/usr/bin/env python3
"""Frozen Recovery 1 for Process-Constrained Phase B v0.2.

Recovery principle:
- preserve the four complete source records exactly;
- mechanically reclassify the fifth source record, an uncaught protocol
  BudgetExceeded, as the per-condition scientific execution failure that the
  frozen generic comparator already uses for action-budget exhaustion;
- never regenerate those five cells;
- execute only the remaining 91 cells in the original frozen order;
- stop again on a genuine technical/provider interruption.

The underlying cases, prompts, environment semantics, target model, temperature,
token ceiling, execution balancing, and eligibility gates are unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable

import run_process_phase_b_v02 as core
import run_process_phase_b_v02_reviewed as reviewed
from protocol_runtime_v04 import BudgetExceeded

OUT = Path(__file__).resolve().parent / "results_process_phase_b_v02_recovery1"
SOURCE_RUNS_ENV = "PHASE_B_V02_RECOVERY1_SOURCE_RUNS"
SOURCE_RUNS_SHA256 = "23887fab0915ad8c727cd2d817b6015e9fe188d8c0fd75f92caf0f522f3c2843"
SOURCE_RUN_ID = 35034720355
SOURCE_ARTIFACT_ID = 10422887717
SOURCE_ARTIFACT_DIGEST = "sha256:642590fc450cfd90dc7157249111a87ceffe2491fe6baf3935b727a599abc104"
SOURCE_RECORD_COUNT = 5
RECLASSIFIED_KEY = ("PCB2-AD01", "MATCHED_SCAFFOLD")
RECLASSIFIED_ERROR = (
    "BudgetExceeded: MATCHED_SCAFFOLD__ABDUCTIVE_DIAGNOSTIC: "
    "environment-action budget exhausted"
)

ModelCall = Callable[[str | None, dict[str, Any]], dict[str, Any]]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def execution_schedule() -> list[tuple[dict[str, Any], str, int, int, tuple[str, ...]]]:
    """Return the exact frozen 96-cell execution schedule with metadata."""
    rows: list[tuple[dict[str, Any], str, int, int, tuple[str, ...]]] = []
    family_seen = {family: 0 for family in core.FAMILIES}
    for case_position, case in enumerate(reviewed.balanced_case_order(), start=1):
        family = case["family"]
        family_rep_index = family_seen[family]
        family_seen[family] += 1
        order = reviewed.balanced_condition_order(family, family_rep_index)
        for condition_position, condition in enumerate(order, start=1):
            rows.append((case, condition, case_position, family_rep_index + 1, order))
    if len(rows) != 96:
        raise RuntimeError(f"expected 96 scheduled cells, found {len(rows)}")
    return rows


def expected_source_keys() -> list[tuple[str, str]]:
    return [(case["case_id"], condition) for case, condition, *_ in execution_schedule()[:5]]


def load_source_runs(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    if digest != SOURCE_RUNS_SHA256:
        raise RuntimeError(f"source runs SHA mismatch: {digest}")

    text = raw.decode("utf-8")
    raw_lines = text.splitlines(keepends=True)
    if len(raw_lines) != SOURCE_RECORD_COUNT:
        raise RuntimeError(f"expected {SOURCE_RECORD_COUNT} source records, found {len(raw_lines)}")
    if any(not line.endswith("\n") for line in raw_lines):
        raise RuntimeError("source runs must be newline-terminated")

    rows = [json.loads(line) for line in raw_lines]
    keys = [(row.get("case_id"), row.get("condition")) for row in rows]
    if keys != expected_source_keys():
        raise RuntimeError(f"source execution prefix drift: {keys}")

    for row in rows[:4]:
        if row.get("status") != "success" or row.get("effective_normalized_score") is None:
            raise RuntimeError(f"completed source row is not complete: {row.get('case_id')}/{row.get('condition')}")

    interrupted = rows[4]
    if (interrupted.get("case_id"), interrupted.get("condition")) != RECLASSIFIED_KEY:
        raise RuntimeError("unexpected interrupted source key")
    if interrupted.get("status") != "technical_incomplete":
        raise RuntimeError("source interrupted row is not the frozen technical_incomplete record")
    if interrupted.get("error") != RECLASSIFIED_ERROR:
        raise RuntimeError(f"source interruption error drift: {interrupted.get('error')!r}")
    if interrupted.get("effective_normalized_score") is not None:
        raise RuntimeError("source interrupted row unexpectedly has a scientific score")
    if interrupted.get("model_calls") != []:
        raise RuntimeError("source interrupted row unexpectedly retained model calls")

    return rows, raw_lines


def reclassify_source_budget_failure(row: dict[str, Any], source_line: str) -> dict[str, Any]:
    """Mechanically correct the frozen fifth row without inventing lost trace data."""
    if (row.get("case_id"), row.get("condition")) != RECLASSIFIED_KEY:
        raise RuntimeError("only the frozen PCB2-AD01/MATCHED_SCAFFOLD row may be reclassified")
    if row.get("error") != RECLASSIFIED_ERROR:
        raise RuntimeError("reclassification error string mismatch")

    corrected = dict(row)
    corrected["status"] = "execution_failure"
    corrected["effective_normalized_score"] = 0.0
    corrected["actions_used"] = core.protocol_specs()["ABDUCTIVE_DIAGNOSTIC"].action_budget
    corrected["cost_logging_complete"] = False
    corrected["recovery_annotation"] = {
        "recovery": "process-constrained-phase-b-v0.2-recovery1",
        "classification": "scientific_execution_failure_from_uncaught_budget_exhaustion",
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_record_sha256": sha256_bytes(source_line.encode("utf-8")),
        "lost_fields": [
            "provider-call records for this cell",
            "completed pre-failure protocol trace for this cell",
            "exact transitions_used for this cell",
        ],
        "fabricated_data": False,
    }
    return corrected


def run_protocol_condition_recovery(
    case: dict[str, Any],
    condition: str,
    model_call: ModelCall,
) -> dict[str, Any]:
    """Frozen v0.2 protocol execution with only BudgetExceeded classification fixed."""
    env = core.make_environment(case)
    specialist = core.protocol_specs()[case["family"]]
    spec = specialist if condition == "SPECIALIST" else core.matched_scaffold_for(specialist)
    runtime = core.ProtocolRuntime(spec, env)
    calls: list[dict[str, Any]] = []
    status = "success"
    error = ""

    while not runtime.terminated:
        turn_index = runtime.transitions_used + 1
        legal = sorted(runtime.legal_next_states())
        if condition == "SPECIALIST":
            request = core.build_specialist_request(case, env, runtime)
            request["environment_terminal"] = core.environment_terminal(env)
            system = core.SPECIALIST_SYSTEM_V02
        else:
            request = core._public_base_request(case, env, spec.action_budget - runtime.actions_used)
            request.update(
                {
                    "current_state": runtime.state,
                    "legal_next_states": legal,
                    "public_history": core._runtime_history(runtime),
                    "max_transitions": spec.max_transitions,
                    "transitions_used": runtime.transitions_used,
                    "instruction": (
                        'Advance to exactly one legal generic next state. payload must be '
                        '{"analysis": "concise public state"}. Any listed environment action '
                        "may be requested or omitted while the environment is non-terminal. "
                        "If environment_terminal is true, environment_action must be null."
                    ),
                }
            )
            system = core.SCAFFOLD_SYSTEM

        try:
            parsed, turn_calls = core.request_json(
                model_call,
                system,
                request,
                core._validate_protocol_shape,
                call_id=f"{case['case_id']}:{condition}:turn:{turn_index}",
            )
            calls.extend(turn_calls)
            if core.environment_terminal(env) and parsed["environment_action"] is not None:
                raise core.InvalidTransition(
                    "environment is already terminal; no further environment action is legal"
                )
            runtime.transition(
                parsed["to_state"],
                parsed["payload"],
                environment_action=parsed["environment_action"],
                action_payload=parsed["action_payload"],
            )
        except core.TechnicalIncomplete as exc:
            calls.extend(exc.calls)
            raise core.TechnicalIncomplete(str(exc), calls) from exc
        except core.FormatFailure as exc:
            calls.extend(exc.calls)
            status = "execution_failure"
            error = str(exc)
            break
        except (
            BudgetExceeded,
            core.InvalidTransition,
            core.EnvironmentError,
            KeyError,
            ValueError,
            TypeError,
        ) as exc:
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
        "trace": [asdict(item) for item in runtime.trace],
        "environment_score": env_score,
        "effective_normalized_score": effective_score,
        "model_calls": calls,
        "catastrophic_failure": core.catastrophic_failure(case["family"], env),
        "cost_logging_complete": True,
    }


def run_case_condition_recovery(
    case: dict[str, Any],
    condition: str,
    model_call: ModelCall,
) -> dict[str, Any]:
    if condition in {"SPECIALIST", "MATCHED_SCAFFOLD"}:
        return run_protocol_condition_recovery(case, condition, model_call)
    run = core.run_generic_condition(case, condition, model_call)
    run["cost_logging_complete"] = True
    return run


def serialize_combined(
    preserved_source_lines: list[str],
    recovery_rows: list[dict[str, Any]],
) -> bytes:
    if len(preserved_source_lines) != 4:
        raise RuntimeError("exactly four original source lines must be preserved byte-for-byte")
    head = "".join(preserved_source_lines)
    tail = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in recovery_rows)
    return (head + tail).encode("utf-8")


def write_combined(
    path: Path,
    preserved_source_lines: list[str],
    recovery_rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(serialize_combined(preserved_source_lines, recovery_rows))


def usage_summary_with_coverage(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Descriptive cost metrics exclude cells whose original call log was lost."""
    result: dict[str, dict[str, Any]] = {}
    for condition in core.CONDITIONS:
        subset = [run for run in runs if run["condition"] == condition]
        logged = [run for run in subset if run.get("cost_logging_complete", True)]
        action_rows = [run for run in subset if run.get("actions_used") is not None]
        if not logged:
            raise RuntimeError(f"{condition}: no complete cost logs")
        result[condition] = {
            "mean_model_calls": mean(len(run.get("model_calls", [])) for run in logged),
            "mean_input_tokens": mean(core._usage_total(run, "input_tokens") for run in logged),
            "mean_output_tokens": mean(core._usage_total(run, "output_tokens") for run in logged),
            "mean_latency_ms": mean(core._usage_total(run, "latency_ms") for run in logged),
            "mean_environment_actions": mean(float(run["actions_used"]) for run in action_rows),
            "execution_failure_rate": mean(
                1.0 if run["status"] != "success" else 0.0 for run in subset
            ),
            "cost_log_records": len(logged),
            "total_records": len(subset),
            "cost_log_coverage": len(logged) / len(subset),
        }
    return result


def aggregate_recovery(runs: list[dict[str, Any]]) -> dict[str, Any]:
    summary = core.aggregate(runs)
    summary["condition_usage"] = usage_summary_with_coverage(runs)
    summary["recovery"] = {
        "name": "process-constrained-phase-b-v0.2-recovery1",
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_runs_sha256": SOURCE_RUNS_SHA256,
        "reclassified_source_cell": {
            "case_id": RECLASSIFIED_KEY[0],
            "condition": RECLASSIFIED_KEY[1],
            "from_status": "technical_incomplete",
            "to_status": "execution_failure",
            "effective_normalized_score": 0.0,
            "reason": RECLASSIFIED_ERROR,
        },
        "regenerated_source_cells": 0,
        "new_cells_executed": 91,
        "cost_logging_limitation": (
            "The source PCB2-AD01/MATCHED_SCAFFOLD provider-call log was lost by the "
            "uncaught BudgetExceeded defect. Primary outcome classification is recoverable; "
            "descriptive call/token/latency means exclude that one cell."
        ),
    }
    return summary


def validate_recovery_design() -> None:
    core.validate_design()
    reviewed.validate_execution_order()
    if os.getenv("PHASE_B_V02_RECOVERY1_AUTHORIZED") not in {None, "", "0", "1"}:
        raise RuntimeError("invalid PHASE_B_V02_RECOVERY1_AUTHORIZED value")
    if expected_source_keys() != [
        ("PCB2-DC01", "SPECIALIST"),
        ("PCB2-DC01", "MATCHED_SCAFFOLD"),
        ("PCB2-DC01", "FULL"),
        ("PCB2-DC01", "CONTROL"),
        ("PCB2-AD01", "MATCHED_SCAFFOLD"),
    ]:
        raise RuntimeError("frozen source prefix no longer matches execution schedule")
    pending = execution_schedule()[SOURCE_RECORD_COUNT:]
    if len(pending) != 91:
        raise RuntimeError(f"expected 91 pending cells, found {len(pending)}")


def main() -> None:
    validate_recovery_design()
    if os.getenv("PHASE_B_V02_RECOVERY1_AUTHORIZED") != "1":
        raise RuntimeError(
            "Recovery 1 is not authorized. A separately reviewed one-shot recovery workflow "
            "must set PHASE_B_V02_RECOVERY1_AUTHORIZED=1."
        )

    source_value = os.getenv(SOURCE_RUNS_ENV, "").strip()
    if not source_value:
        raise RuntimeError(f"{SOURCE_RUNS_ENV} must point to the frozen source runs.jsonl")
    source_path = Path(source_value).resolve()
    source_rows, source_lines = load_source_runs(source_path)

    OUT.mkdir(exist_ok=True)
    combined_path = OUT / "combined_runs.jsonl"
    summary_path = OUT / "summary.json"

    preserved_lines = source_lines[:4]
    corrected_source = reclassify_source_budget_failure(source_rows[4], source_lines[4])
    corrected_source["decision_regret_secondary"] = None
    recovery_rows: list[dict[str, Any]] = [corrected_source]
    write_combined(combined_path, preserved_lines, recovery_rows)

    resolved = set(expected_source_keys())

    for case, condition, case_position, family_rep_index, order in execution_schedule():
        key = (case["case_id"], condition)
        if key in resolved:
            continue

        print("recover", case["case_id"], condition, flush=True)
        try:
            run = run_case_condition_recovery(case, condition, reviewed.executable_model_call)
        except Exception as exc:
            partial_run = reviewed.technical_partial_run(case, condition, exc)
            partial_run["cost_logging_complete"] = bool(partial_run.get("model_calls"))
            partial_run["case_execution_position"] = case_position
            partial_run["family_rep_index"] = family_rep_index
            partial_run["condition_execution_position"] = list(order).index(condition) + 1
            partial_run["condition_order"] = list(order)
            recovery_rows.append(partial_run)
            write_combined(combined_path, preserved_lines, recovery_rows)
            partial = {
                "measurement_version": "process-constrained-phase-b-v0.2-recovery1",
                "records_written": 4 + len(recovery_rows),
                "complete": False,
                "interrupted_at": {"case_id": case["case_id"], "condition": condition},
                "error": f"{type(exc).__name__}: {exc}",
                "source_run_id": SOURCE_RUN_ID,
                "source_artifact_id": SOURCE_ARTIFACT_ID,
                "source_runs_sha256": SOURCE_RUNS_SHA256,
                "combined_runs_sha256": sha256_bytes(combined_path.read_bytes()),
            }
            (OUT / "partial_meta.json").write_text(
                json.dumps(partial, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            raise

        run["decision_regret_secondary"] = core.decision_regret_secondary(case, run)
        run["case_execution_position"] = case_position
        run["family_rep_index"] = family_rep_index
        run["condition_execution_position"] = list(order).index(condition) + 1
        run["condition_order"] = list(order)
        recovery_rows.append(run)
        resolved.add(key)
        write_combined(combined_path, preserved_lines, recovery_rows)

    combined = [json.loads(line) for line in combined_path.read_text(encoding="utf-8").splitlines()]
    if len(combined) != 96:
        raise RuntimeError(f"recovery completed with {len(combined)} records instead of 96")

    summary = aggregate_recovery(combined)
    summary["case_order_scheme"] = reviewed.CASE_ORDER_SCHEME
    summary["condition_order_scheme"] = reviewed.CONDITION_ORDER_SCHEME
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    meta = {
        "measurement_version": "process-constrained-phase-b-v0.2-recovery1",
        "complete": True,
        "records": len(combined),
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_artifact_digest": SOURCE_ARTIFACT_DIGEST,
        "source_runs_sha256": SOURCE_RUNS_SHA256,
        "preserved_complete_source_records": 4,
        "mechanically_reclassified_source_records": 1,
        "regenerated_source_records": 0,
        "new_cells_executed": 91,
        "combined_runs_sha256": sha256_bytes(combined_path.read_bytes()),
        "summary_sha256": sha256_bytes(summary_path.read_bytes()),
    }
    (OUT / "recovery_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "decision": summary["program_decision"],
                "eligible": summary["eligible_families"],
                "records": len(combined),
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
