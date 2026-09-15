#!/usr/bin/env python3
"""Reviewed executable wrapper for Process-Constrained ARC Phase B v0.2.

This wrapper adds preregistered family-interleaved execution order, within-family
condition-position balancing, lossless partial-call logging, a target-visible
scaffold-neutralization boundary, and a hard execution authorization gate. The
repository intentionally contains no paid v0.2 workflow at this stage; a later
separately reviewed freeze/authorization change must set
`PHASE_B_V02_EXECUTION_AUTHORIZED=1` only after all executable identities are
frozen and the one-shot workflow boundary is in place.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import run_process_phase_b_v02 as core

OUT = Path(__file__).resolve().parent / "results_process_phase_b_v02"
CONDITION_ORDER_SCHEME = "family_balanced_cyclic_rotation_v1"
CASE_ORDER_SCHEME = "round_robin_four_families"

# Six cases cannot place four conditions exactly equally into four positions
# within one family. Each schedule makes every condition occupy every position
# once or twice. Across the four families, every condition occupies every global
# position exactly six times.
FAMILY_SHIFT_SCHEDULES: dict[str, tuple[int, ...]] = {
    "DEDUCTIVE_CONSTRAINT": (0, 1, 2, 3, 0, 1),
    "ABDUCTIVE_DIAGNOSTIC": (1, 2, 3, 0, 1, 2),
    "SEARCH_PLANNING": (2, 3, 0, 1, 2, 3),
    "DECISION_THEORETIC": (3, 0, 1, 2, 3, 0),
}


def balanced_case_order() -> list[dict[str, Any]]:
    buckets = {
        family: [case for case in core.CASES if case["family"] == family]
        for family in core.FAMILIES
    }
    for family, cases in buckets.items():
        if len(cases) != 6:
            raise ValueError(f"{family}: expected six cases, found {len(cases)}")
    return [buckets[family][rep] for rep in range(6) for family in core.FAMILIES]


def balanced_condition_order(family: str, family_rep_index: int) -> tuple[str, ...]:
    if family not in FAMILY_SHIFT_SCHEDULES:
        raise ValueError(f"unknown family for execution balancing: {family!r}")
    schedule = FAMILY_SHIFT_SCHEDULES[family]
    if family_rep_index not in range(len(schedule)):
        raise ValueError(f"family replicate index out of range: {family_rep_index}")
    conditions = list(core.CONDITIONS)
    shift = schedule[family_rep_index]
    return tuple(conditions[shift:] + conditions[:shift])


def validate_execution_order() -> None:
    family_seen = Counter()
    global_counts = Counter()
    family_counts = {family: Counter() for family in core.FAMILIES}
    for case in balanced_case_order():
        family = case["family"]
        rep = family_seen[family]
        family_seen[family] += 1
        order = balanced_condition_order(family, rep)
        for position, condition in enumerate(order, start=1):
            global_counts[(condition, position)] += 1
            family_counts[family][(condition, position)] += 1
    if dict(family_seen) != {family: 6 for family in core.FAMILIES}:
        raise RuntimeError("family case-order imbalance")
    for family in core.FAMILIES:
        for condition in core.CONDITIONS:
            for position in range(1, 5):
                if family_counts[family][(condition, position)] not in {1, 2}:
                    raise RuntimeError(
                        f"within-family position imbalance: {family}/{condition}/{position}"
                    )
    for condition in core.CONDITIONS:
        for position in range(1, 5):
            if global_counts[(condition, position)] != 6:
                raise RuntimeError(
                    f"global position imbalance: {condition}/{position}={global_counts[(condition, position)]}"
                )


def target_visible_system(system: str | None) -> str | None:
    """Remove comparator wording that is unnecessary for task execution.

    The scientific condition remains MATCHED_SCAFFOLD in internal metadata, but
    the model-facing system text does not need to be told that the scaffold is
    "matched" to another condition.
    """

    if system is None:
        return None
    return system.replace(
        "generic matched structured scaffold",
        "generic structured scaffold",
    )


def executable_model_call(system: str | None, request: dict[str, Any]) -> dict[str, Any]:
    """Executable provider boundary with technical/scientific failure separation.

    Provider/adapter exceptions happen before a valid target response is
    available for scientific interpretation. They therefore propagate as
    TechnicalIncomplete rather than being accidentally caught as task execution
    failures by family-level semantic handlers. Completed earlier calls are
    preserved by the core runner's TechnicalIncomplete re-wrapping path.
    """

    public_system = target_visible_system(system)
    try:
        return core.zai_model_call(public_system, request)
    except core.RequestFailure:
        raise
    except Exception as exc:
        raise core.TechnicalIncomplete(
            f"provider/model call raised {type(exc).__name__}: {exc}",
            [],
        ) from exc


def technical_partial_run(case: dict[str, Any], condition: str, exc: Exception) -> dict[str, Any]:
    calls = exc.calls if isinstance(exc, core.RequestFailure) else []
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
        "decision_regret_secondary": None,
    }


def validate_executable_boundary() -> None:
    core.validate_design()
    validate_execution_order()
    if int(os.getenv("ZAI_MAX_TOKENS", "0")) != core.TARGET_CAP:
        raise RuntimeError(f"ZAI_MAX_TOKENS must be {core.TARGET_CAP}")
    if float(os.getenv("ZAI_TEMPERATURE", "-1")) != core.TEMPERATURE:
        raise RuntimeError("ZAI_TEMPERATURE must be 0")
    if os.getenv("PHASE_B_V02_EXECUTION_AUTHORIZED") != "1":
        raise RuntimeError(
            "Phase B v0.2 execution is not authorized. A separately frozen one-shot workflow must set "
            "PHASE_B_V02_EXECUTION_AUTHORIZED=1 after review."
        )


def main() -> None:
    # This gate is deliberately evaluated before any model call. It is not a
    # substitute for the later one-shot workflow gate; it prevents accidental
    # execution while this reviewed runner exists without paid authorization.
    validate_executable_boundary()

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
                run = core.run_case_condition(case, condition, executable_model_call)
            except Exception as exc:
                partial_run = technical_partial_run(case, condition, exc)
                partial_run["case_execution_position"] = case_position + 1
                partial_run["family_rep_index"] = family_rep_index + 1
                partial_run["condition_execution_position"] = execution_position
                partial_run["condition_order"] = list(order)
                runs.append(partial_run)
                core.write_jsonl(runs_path, runs)
                partial = {
                    "measurement_version": "process-constrained-phase-b-v0.2",
                    "records_written": len(runs),
                    "complete": False,
                    "interrupted_at": {
                        "case_id": case["case_id"],
                        "condition": condition,
                    },
                    "error": f"{type(exc).__name__}: {exc}",
                    "case_order_scheme": CASE_ORDER_SCHEME,
                    "condition_order_scheme": CONDITION_ORDER_SCHEME,
                    "runs_sha256": core.sha256_bytes(runs_path.read_bytes()),
                }
                (OUT / "partial_meta.json").write_text(
                    json.dumps(partial, indent=2), encoding="utf-8"
                )
                raise

            run["decision_regret_secondary"] = core.decision_regret_secondary(case, run)
            run["case_execution_position"] = case_position + 1
            run["family_rep_index"] = family_rep_index + 1
            run["condition_execution_position"] = execution_position
            run["condition_order"] = list(order)
            runs.append(run)
            core.write_jsonl(runs_path, runs)

    summary = core.aggregate(runs)
    summary["case_order_scheme"] = CASE_ORDER_SCHEME
    summary["condition_order_scheme"] = CONDITION_ORDER_SCHEME
    summary_path = OUT / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = {
        "measurement_version": "process-constrained-phase-b-v0.2",
        "records": len(runs),
        "case_order_scheme": CASE_ORDER_SCHEME,
        "condition_order_scheme": CONDITION_ORDER_SCHEME,
        "runs_sha256": core.sha256_bytes(runs_path.read_bytes()),
        "summary_sha256": core.sha256_bytes(summary_path.read_bytes()),
        "complete": True,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {"decision": summary["program_decision"], "eligible": summary["eligible_families"]},
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
