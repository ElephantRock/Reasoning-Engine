"""Corrected deterministic environments for Process-Constrained Phase B v0.2.

v0.4 preserves the hardened v0.3 causal mechanics for diagnostic, planning, and
decision tasks while giving the fresh v0.2 diagnostic/planning cases distinct
public scenario surfaces. The deductive environment is replaced with an explicitly
defined service-restoration endpoint so restart start time cannot be confused with
restart completion time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from protocol_runtime_v03 import EnvironmentError
from protocol_environments_v03 import (
    DecisionEnvironmentV3 as DecisionEnvironmentV4,
    DiagnosticEnvironmentV3,
    PlanningEnvironmentV3,
)


@dataclass
class FeasibilityEnvironmentV4:
    isolation: int
    calibration: int
    verification: int
    restart: int
    deadline: int
    shared_technician: bool
    committed_restoration: int | None = None
    checks: int = 0

    @property
    def earliest_restart_start(self) -> int:
        middle = (
            self.calibration + self.verification
            if self.shared_technician
            else max(self.calibration, self.verification)
        )
        return self.isolation + middle

    @property
    def minimum_restoration(self) -> int:
        return self.earliest_restart_start + self.restart

    def task_text(self) -> str:
        resource = (
            "After isolation completes, calibration and verification require the same technician and cannot overlap."
            if self.shared_technician
            else "After isolation completes, calibration and verification use independent technicians and may overlap."
        )
        return (
            f"A maintenance window starts now. Isolation takes {self.isolation} minutes, calibration takes "
            f"{self.calibration} minutes, verification takes {self.verification} minutes, and restart takes "
            f"{self.restart} minutes. {resource} Restart may begin only after calibration and verification are "
            f"complete. The requested service-restoration deadline is minute {self.deadline}. No step can be shortened. "
            "Your terminal commitment is the minute when restart has FINISHED and service is restored, not the minute "
            "when restart begins. What is the earliest defensible service-restoration minute, and can the requested "
            "service-restoration deadline be promised?"
        )

    def available_actions(self) -> tuple[str, ...]:
        return ("inspect_constraints", "test_candidate", "commit_restoration")

    def action_tags(self, action: str) -> frozenset[str]:
        return {
            "inspect_constraints": frozenset({"INSPECT"}),
            "test_candidate": frozenset({"TEST"}),
            "commit_restoration": frozenset({"COMMIT"}),
        }[action]

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        if action == "inspect_constraints":
            self.checks += 1
            return {
                "isolation": self.isolation,
                "calibration": self.calibration,
                "verification": self.verification,
                "restart": self.restart,
                "service_restoration_deadline": self.deadline,
                "shared_technician": self.shared_technician,
                "terminal_quantity": "service_restored_minute",
            }
        if action == "test_candidate":
            self.checks += 1
            candidate = int(payload["service_restored_minute"])
            return {
                "candidate_service_restored_minute": candidate,
                "feasible": candidate >= self.minimum_restoration,
                "deadline_satisfied": candidate <= self.deadline,
            }
        if action == "commit_restoration":
            self.committed_restoration = int(payload["service_restored_minute"])
            return {"commit_recorded": True, "terminal_quantity": "service_restored_minute"}
        raise EnvironmentError(f"unknown feasibility action: {action}")

    def score(self) -> dict[str, float | int | bool | str]:
        exact = self.committed_restoration == self.minimum_restoration
        deadline_possible = self.minimum_restoration <= self.deadline
        deadline_claim_correct = bool(
            self.committed_restoration is not None
            and (
                (deadline_possible and self.committed_restoration <= self.deadline)
                or (not deadline_possible and self.committed_restoration > self.deadline)
            )
        )
        return {
            "correct_terminal_decision": exact and deadline_claim_correct,
            "earliest_feasible_service_restoration": exact,
            "deadline_claim_correct": deadline_claim_correct,
            "constraint_checks": self.checks,
            "normalized_score": 1.0 if exact and deadline_claim_correct else 0.0,
        }


@dataclass
class DiagnosticEnvironmentV4(DiagnosticEnvironmentV3):
    scenario: str = "edge-api"

    def task_text(self) -> str:
        return (
            f"The {self.scenario} production service began timing out after several overnight changes: a client-library "
            "deployment, provider network maintenance, a connection-pool configuration rollout, and an upstream policy "
            "update. The initial symptoms are compatible with more than one change. You may request targeted checks "
            "before committing to the dominant cause. Identify the cause with the least unnecessary investigation."
        )


@dataclass
class PlanningEnvironmentV4(PlanningEnvironmentV3):
    scenario: str = "orders"

    def task_text(self) -> str:
        return (
            f"The {self.scenario} database must migrate to a new shard without planned downtime. Dual-write, backfill, "
            "checksum verification, gradual read shifting, health probing, rollback, finalization, and abort are "
            "available. The new shard's behavior under full production reads is not yet known. Finalization is "
            "irreversible. Complete the migration if the new shard is healthy; otherwise return safely to the old "
            "shard and abort."
        )
