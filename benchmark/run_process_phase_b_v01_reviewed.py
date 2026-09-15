#!/usr/bin/env python3
"""Final reviewed Phase-B executable surface.

This wrapper removes experiment-only identifiers from every model-facing request
and balances execution order prospectively. Internal case IDs and condition labels
remain in artifact keys and call IDs, but the target model sees only the public
task, common action catalog, remaining action budget, observations, and its
condition-specific control interface.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import run_process_phase_b_v01 as core

OUT = Path(__file__).resolve().parent / "results_process_phase_b_v01"
CONDITION_ORDER_SCHEME = "family_balanced_cyclic_rotation_v1"

# Six cases cannot place four conditions exactly equally into four positions
# within a single family. These preregistered cyclic-shift counts make every
# condition occupy every within-family execution position either once or twice,
# while the four families jointly yield exact 6-per-position global balance.
FAMILY_SHIFT_SCHEDULES: dict[str, tuple[int, ...]] = {
    "DEDUCTIVE_CONSTRAINT": (0, 0, 1, 1, 2, 3),
    "ABDUCTIVE_DIAGNOSTIC": (0, 1, 1, 2, 2, 3),
    "SEARCH_PLANNING": (0, 1, 2, 2, 3, 3),
    "DECISION_THEORETIC": (0, 0, 1, 2, 3, 3),
}


def _public_base_request(case: dict[str, Any], env: Any, condition: str, remaining_actions: int) -> dict[str, Any]:
    # `condition` is intentionally accepted for signature compatibility and
    # intentionally not emitted. Case IDs encode family abbreviations, so they
    # are also excluded from model-visible context.
    _ = condition
    return {
        "task": env.task_text(),
        "action_catalog": core.action_catalog(case["family"]),
        "remaining_environment_actions": remaining_actions,
    }


# The reviewed executor resolves this helper dynamically from the shared core.
core._base_request = _public_base_request

import run_process_phase_b_v01_exec as _exec  # noqa: E402

RequestFailure = _exec.RequestFailure
TechnicalIncomplete = _exec.TechnicalIncomplete
FormatFailure = _exec.FormatFailure
request_json = _exec.request_json
run_protocol_condition = _exec.run_protocol_condition
run_generic_condition = _exec.run_generic_condition
run_case_condition = _exec.run_case_condition
technical_partial_run = _exec.technical_partial_run


def balanced_case_order() -> list[dict[str, Any]]:
    """Interleave the four families so family is not confounded with run time."""
    buckets = {
        family: [case for case in core.CASES if case["family"] == family]
        for family in core.FAMILIES
    }
    return [buckets[family][rep] for rep in range(6) for family in core.FAMILIES]


def balanced_condition_order(family: str, family_rep_index: int) -> tuple[str, ...]:
    """Return the preregistered condition rotation for one family replicate."""
    if family not in FAMILY_SHIFT_SCHEDULES:
        raise ValueError(f"unknown family for execution balancing: {family!r}")
    schedule = FAMILY_SHIFT_SCHEDULES[family]
    if family_rep_index not in range(len(schedule)):
        raise ValueError(f"family replicate index out of range: {family_rep_index}")
    conditions = list(core.CONDITIONS)
    shift = schedule[family_rep_index]
    return tuple(conditions[shift:] + conditions[:shift])


def main() -> None:
    core.validate_design()
    if int(os.getenv("ZAI_MAX_TOKENS", "0")) != core.TARGET_CAP:
        raise RuntimeError(f"ZAI_MAX_TOKENS must be {core.TARGET_CAP}")
    if float(os.getenv("ZAI_TEMPERATURE", "-1")) != core.TEMPERATURE:
        raise RuntimeError("ZAI_TEMPERATURE must be 0")

    OUT.mkdir(exist_ok=True)
    runs: list[dict[str, Any]] = []
    runs_path = OUT / "runs.jsonl"
    execution_cases = balanced_case_order()
    family_seen = {family: 0 for family in core.FAMILIES}
    for case_position, case in enumerate(execution_cases):
        family = case["family"]
        family_rep_index = family_seen[family]
        family_seen[family] += 1
        order = balanced_condition_order(family, family_rep_index)
        for execution_position, condition in enumerate(order, start=1):
            print("run", case["case_id"], condition, flush=True)
            try:
                run = run_case_condition(case, condition, core.zai_model_call)
            except Exception as exc:
                runs.append(technical_partial_run(case, condition, exc))
                runs[-1]["case_execution_position"] = case_position + 1
                runs[-1]["family_rep_index"] = family_rep_index + 1
                runs[-1]["condition_execution_position"] = execution_position
                runs[-1]["condition_order"] = list(order)
                core.write_jsonl(runs_path, runs)
                partial = {
                    "measurement_version": "process-constrained-phase-b-v0.1",
                    "records_written": len(runs),
                    "complete": False,
                    "interrupted_at": {"case_id": case["case_id"], "condition": condition},
                    "error": f"{type(exc).__name__}: {exc}",
                    "case_order_scheme": "round_robin_four_families",
                    "condition_order_scheme": CONDITION_ORDER_SCHEME,
                    "runs_sha256": core.sha256_bytes(runs_path.read_bytes()),
                }
                (OUT / "partial_meta.json").write_text(json.dumps(partial, indent=2), encoding="utf-8")
                raise
            run["decision_regret_secondary"] = core.decision_regret_secondary(case, run)
            run["case_execution_position"] = case_position + 1
            run["family_rep_index"] = family_rep_index + 1
            run["condition_execution_position"] = execution_position
            run["condition_order"] = list(order)
            runs.append(run)
            core.write_jsonl(runs_path, runs)

    summary = core.aggregate(runs)
    summary["case_order_scheme"] = "round_robin_four_families"
    summary["condition_order_scheme"] = CONDITION_ORDER_SCHEME
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "measurement_version": "process-constrained-phase-b-v0.1",
        "records": len(runs),
        "case_order_scheme": "round_robin_four_families",
        "condition_order_scheme": CONDITION_ORDER_SCHEME,
        "runs_sha256": core.sha256_bytes(runs_path.read_bytes()),
        "summary_sha256": core.sha256_bytes(summary_path.read_bytes()),
        "complete": True,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"decision": summary["program_decision"], "eligible": summary["eligible_families"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
