"""Frozen zero-cost Phase-B development-suite helpers.

No model or network calls are permitted in this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from protocol_environments_v03 import (
    DecisionEnvironmentV3,
    DiagnosticEnvironmentV3,
    FeasibilityEnvironmentV3,
    PlanningEnvironmentV3,
)

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "process_phase_b_cases_v01.json"
CASES: list[dict[str, Any]] = json.loads(CASES_PATH.read_text(encoding="utf-8"))

FAMILIES = (
    "DEDUCTIVE_CONSTRAINT",
    "ABDUCTIVE_DIAGNOSTIC",
    "SEARCH_PLANNING",
    "DECISION_THEORETIC",
)


def make_environment(case: dict[str, Any]):
    family = case["family"]
    params = dict(case["params"])
    if family == "DEDUCTIVE_CONSTRAINT":
        return FeasibilityEnvironmentV3(**params)
    if family == "ABDUCTIVE_DIAGNOSTIC":
        return DiagnosticEnvironmentV3(**params)
    if family == "SEARCH_PLANNING":
        return PlanningEnvironmentV3(**params)
    if family == "DECISION_THEORETIC":
        return DecisionEnvironmentV3(**params)
    raise ValueError(f"unknown family {family!r}")


def validate_suite() -> None:
    ids = [case["case_id"] for case in CASES]
    if len(CASES) != 24 or len(set(ids)) != 24:
        raise ValueError("Phase-B suite must contain 24 unique cases")
    for family in FAMILIES:
        count = sum(case["family"] == family for case in CASES)
        if count != 6:
            raise ValueError(f"{family}: expected 6 cases, found {count}")
    for case in CASES:
        env = make_environment(case)
        task = env.task_text()
        if not task.strip():
            raise ValueError(f"{case['case_id']}: empty task text")
        lowered = task.lower()
        for forbidden in ("hidden_cause", "hidden_good", "oracle_utility", "minimum_restart"):
            if forbidden in lowered:
                raise ValueError(f"{case['case_id']}: task leaks internal field {forbidden}")


if __name__ == "__main__":
    validate_suite()
    print("process Phase-B v0.1 suite validated")
