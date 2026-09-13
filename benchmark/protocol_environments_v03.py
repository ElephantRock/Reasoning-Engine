"""Hardened deterministic environments for process-constrained ARC Phase-B preflight.

The environments are protocol-independent. They expose the same action universe to
all conditions, hide only predeclared environment state, and compute objective
scores without inspecting the reasoning-condition label.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from protocol_runtime_v03 import EnvironmentError


@dataclass
class FeasibilityEnvironmentV3:
    isolation: int
    calibration: int
    verification: int
    restart: int
    deadline: int
    shared_technician: bool
    committed_restart: int | None = None
    checks: int = 0

    @property
    def minimum_restart(self) -> int:
        middle = self.calibration + self.verification if self.shared_technician else max(self.calibration, self.verification)
        return self.isolation + middle + self.restart

    def task_text(self) -> str:
        resource = (
            "Calibration and verification require the same technician and cannot overlap."
            if self.shared_technician
            else "Calibration and verification use independent technicians and may overlap after isolation."
        )
        return (
            f"A maintenance window starts now. Isolation takes {self.isolation} minutes, calibration takes "
            f"{self.calibration} minutes, verification takes {self.verification} minutes, and restart takes "
            f"{self.restart} minutes. {resource} Restart can begin only after calibration and verification are "
            f"complete. The requested service deadline is minute {self.deadline}. No step can be shortened. "
            "What is the earliest defensible restart commitment, and can the requested deadline be promised?"
        )

    def available_actions(self) -> tuple[str, ...]:
        return ("inspect_constraints", "test_candidate", "commit_restart")

    def action_tags(self, action: str) -> frozenset[str]:
        return {
            "inspect_constraints": frozenset({"INSPECT"}),
            "test_candidate": frozenset({"TEST"}),
            "commit_restart": frozenset({"COMMIT"}),
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
                "deadline": self.deadline,
                "shared_technician": self.shared_technician,
            }
        if action == "test_candidate":
            self.checks += 1
            candidate = int(payload["restart_minute"])
            return {
                "candidate": candidate,
                "feasible": candidate >= self.minimum_restart,
                "deadline_satisfied": candidate <= self.deadline,
            }
        if action == "commit_restart":
            self.committed_restart = int(payload["restart_minute"])
            return {"commit_recorded": True}
        raise EnvironmentError(f"unknown feasibility action: {action}")

    def score(self) -> dict[str, float | int | bool | str]:
        exact = self.committed_restart == self.minimum_restart
        deadline_possible = self.minimum_restart <= self.deadline
        deadline_claim_correct = bool(
            self.committed_restart is not None
            and ((deadline_possible and self.committed_restart <= self.deadline) or (not deadline_possible and self.committed_restart > self.deadline))
        )
        return {
            "correct_terminal_decision": exact and deadline_claim_correct,
            "earliest_feasible_commitment": exact,
            "deadline_claim_correct": deadline_claim_correct,
            "constraint_checks": self.checks,
            "normalized_score": 1.0 if exact and deadline_claim_correct else 0.0,
        }


DIAGNOSTIC_PATTERNS: dict[str, dict[str, bool]] = {
    "route_change": {"check_network": True, "compare_zones": True, "inspect_pool": False},
    "library_regression": {"check_network": True, "compare_zones": False, "inspect_pool": True},
    "pool_exhaustion": {"check_network": False, "compare_zones": True, "inspect_pool": True},
    "upstream_policy": {"check_network": False, "compare_zones": False, "inspect_pool": False},
}


@dataclass
class DiagnosticEnvironmentV3:
    hidden_cause: str
    evidence_seen: list[str] = field(default_factory=list)
    diagnosis: str | None = None
    action_count: int = 0

    def __post_init__(self) -> None:
        if self.hidden_cause not in DIAGNOSTIC_PATTERNS:
            raise ValueError(f"unknown hidden cause {self.hidden_cause!r}")

    def task_text(self) -> str:
        return (
            "A production API began timing out after several overnight changes: a client-library deployment, "
            "provider network maintenance, a connection-pool configuration rollout, and an upstream policy update. "
            "The initial symptoms are compatible with more than one of these changes. You may request targeted checks "
            "before committing to the dominant cause. Identify the cause with the least unnecessary investigation."
        )

    def available_actions(self) -> tuple[str, ...]:
        return ("check_network", "compare_zones", "inspect_pool", "diagnose")

    def action_tags(self, action: str) -> frozenset[str]:
        if action == "diagnose":
            return frozenset({"COMMIT"})
        if action in {"check_network", "compare_zones", "inspect_pool"}:
            return frozenset({"EVIDENCE"})
        raise EnvironmentError(f"unknown diagnostic action: {action}")

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        self.action_count += 1
        if action in {"check_network", "compare_zones", "inspect_pool"}:
            if action in self.evidence_seen:
                raise EnvironmentError("the same diagnostic check cannot be repeated")
            self.evidence_seen.append(action)
            value = DIAGNOSTIC_PATTERNS[self.hidden_cause][action]
            labels = {
                "check_network": "network_anomaly_present",
                "compare_zones": "zone_local_pattern",
                "inspect_pool": "pool_anomaly_present",
            }
            return {labels[action]: value}
        if action == "diagnose":
            cause = str(payload.get("cause", "")).strip()
            if cause not in DIAGNOSTIC_PATTERNS:
                raise EnvironmentError("diagnose requires one of the declared candidate causes")
            self.diagnosis = cause
            return {"diagnosis_recorded": True}
        raise EnvironmentError(f"unknown diagnostic action: {action}")

    def score(self) -> dict[str, float | int | bool | str]:
        evidence_count = len(set(self.evidence_seen))
        correct = self.diagnosis == self.hidden_cause
        supported = correct and evidence_count >= 2
        extra = max(0, evidence_count - 2)
        normalized = (1.0 - 0.1 * extra) if supported else (0.4 if correct else 0.0)
        return {
            "correct_terminal_decision": correct,
            "supported_correct_diagnosis": supported,
            "evidence_checks": evidence_count,
            "unnecessary_extra_checks": extra,
            "environment_actions": self.action_count,
            "normalized_score": max(0.0, normalized),
        }


@dataclass
class PlanningEnvironmentV3:
    new_shard_healthy: bool
    dual_write: bool = False
    backfilled: bool = False
    checksum_verified: bool = False
    read_percent_new: int = 0
    health_checked: bool = False
    rolled_back: bool = False
    finalized: bool = False
    aborted: bool = False
    violations: int = 0
    action_count: int = 0

    def task_text(self) -> str:
        return (
            "A database must migrate to a new shard without planned downtime. Dual-write, backfill, checksum "
            "verification, gradual read shifting, health probing, rollback, finalization, and abort are available. "
            "The new shard's behavior under full production reads is not yet known. Finalization is irreversible. "
            "Complete the migration if the new shard is healthy; otherwise return safely to the old shard and abort."
        )

    def available_actions(self) -> tuple[str, ...]:
        return (
            "enable_dual_write",
            "backfill",
            "verify_checksum",
            "shift_reads",
            "probe_health",
            "rollback_reads",
            "finalize_migration",
            "abort_migration",
        )

    def action_tags(self, action: str) -> frozenset[str]:
        tags = {
            "enable_dual_write": {"EXECUTE"},
            "backfill": {"EXECUTE"},
            "verify_checksum": {"CHECK"},
            "shift_reads": {"EXECUTE"},
            "probe_health": {"CHECKPOINT"},
            "rollback_reads": {"ROLLBACK"},
            "finalize_migration": {"COMMIT"},
            "abort_migration": {"COMMIT"},
        }
        return frozenset(tags[action])

    def _require(self, condition: bool, message: str) -> None:
        if not condition:
            self.violations += 1
            raise EnvironmentError(message)

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        self.action_count += 1
        if action == "enable_dual_write":
            self._require(not self.finalized and not self.aborted, "migration already terminated")
            self.dual_write = True
        elif action == "backfill":
            self._require(self.dual_write, "backfill requires dual-write")
            self.backfilled = True
        elif action == "verify_checksum":
            self._require(self.backfilled, "checksum requires backfill")
            self.checksum_verified = True
        elif action == "shift_reads":
            self._require(self.checksum_verified, "read shift requires verified checksum")
            percent = int(payload.get("percent", 0))
            self._require(percent in range(10, 101, 10), "read shift must be a 10% increment")
            self._require(percent >= self.read_percent_new, "use rollback to move reads backwards")
            self.read_percent_new = percent
        elif action == "probe_health":
            self._require(self.read_percent_new == 100, "health probe requires 100% reads on new shard")
            self.health_checked = True
            return {"new_shard_healthy": self.new_shard_healthy}
        elif action == "rollback_reads":
            self._require(self.health_checked, "rollback decision requires a health checkpoint")
            self._require(not self.finalized, "rollback unavailable after finalization")
            self.read_percent_new = 0
            self.rolled_back = True
        elif action == "finalize_migration":
            self._require(self.health_checked, "finalization requires health checkpoint")
            self._require(self.new_shard_healthy, "cannot finalize an unhealthy shard")
            self._require(self.read_percent_new == 100, "finalization requires all reads on new shard")
            self.finalized = True
        elif action == "abort_migration":
            self._require(self.health_checked, "abort requires health checkpoint")
            self._require(not self.new_shard_healthy, "healthy shard should not be aborted")
            self._require(self.read_percent_new == 0 and self.rolled_back, "abort requires rollback to old shard")
            self.aborted = True
        else:
            raise EnvironmentError(f"unknown planning action: {action}")
        return {
            "dual_write": self.dual_write,
            "backfilled": self.backfilled,
            "checksum_verified": self.checksum_verified,
            "read_percent_new": self.read_percent_new,
            "health_checked": self.health_checked,
            "rolled_back": self.rolled_back,
            "finalized": self.finalized,
            "aborted": self.aborted,
        }

    def score(self) -> dict[str, float | int | bool | str]:
        correct = self.finalized if self.new_shard_healthy else self.aborted
        normalized = 1.0 if correct and self.violations == 0 else (0.5 if correct else 0.0)
        return {
            "correct_terminal_decision": bool(correct),
            "constraint_violations": self.violations,
            "environment_actions": self.action_count,
            "rollback_used": self.rolled_back,
            "terminal_branch": "finalized" if self.finalized else ("aborted" if self.aborted else "incomplete"),
            "normalized_score": normalized,
        }


@dataclass
class DecisionEnvironmentV3:
    prior_good: float
    sensitivity: float
    false_positive_rate: float
    pilot_cost: float
    buy_good_utility: float
    buy_bad_utility: float
    hidden_good: bool
    deterministic_signal: str
    pilot_run: bool = False
    decision: str | None = None
    action_count: int = 0

    def __post_init__(self) -> None:
        if not 0 < self.prior_good < 1:
            raise ValueError("prior_good must be between 0 and 1")
        if self.deterministic_signal not in {"good", "bad"}:
            raise ValueError("deterministic_signal must be good or bad")

    def task_text(self) -> str:
        return (
            f"A non-refundable annual commitment has utility {self.buy_good_utility:+.0f} if the product is good and "
            f"{self.buy_bad_utility:+.0f} if it is bad; declining has utility 0. Current probability the product is "
            f"good is {self.prior_good:.2f}. A pilot costs {self.pilot_cost:.0f}. The pilot returns a good signal with "
            f"probability {self.sensitivity:.2f} when the product is good and {self.false_positive_rate:.2f} when it is "
            "bad. Decide whether to pilot or act now, then make the final buy/decline decision using any signal obtained."
        )

    def available_actions(self) -> tuple[str, ...]:
        return ("run_pilot", "buy_annual", "decline")

    def action_tags(self, action: str) -> frozenset[str]:
        if action == "run_pilot":
            return frozenset({"EVIDENCE"})
        if action in {"buy_annual", "decline"}:
            return frozenset({"COMMIT"})
        raise EnvironmentError(f"unknown decision action: {action}")

    def _posterior(self, signal: str) -> float:
        p = self.prior_good
        if signal == "good":
            numerator = p * self.sensitivity
            denominator = numerator + (1 - p) * self.false_positive_rate
        else:
            numerator = p * (1 - self.sensitivity)
            denominator = numerator + (1 - p) * (1 - self.false_positive_rate)
        return numerator / denominator

    def expected_buy_utility(self, p_good: float) -> float:
        return p_good * self.buy_good_utility + (1 - p_good) * self.buy_bad_utility

    def optimal_initial_policy(self) -> str:
        buy_now = self.expected_buy_utility(self.prior_good)
        best_now = max(buy_now, 0.0)
        p_signal_good = self.prior_good * self.sensitivity + (1 - self.prior_good) * self.false_positive_rate
        post_good = self._posterior("good")
        post_bad = self._posterior("bad")
        after_good = max(self.expected_buy_utility(post_good), 0.0)
        after_bad = max(self.expected_buy_utility(post_bad), 0.0)
        pilot_value = -self.pilot_cost + p_signal_good * after_good + (1 - p_signal_good) * after_bad
        if pilot_value > best_now + 1e-9:
            return "pilot"
        return "buy_annual" if buy_now > 0 else "decline"

    def optimal_final_policy(self) -> str:
        p = self._posterior(self.deterministic_signal) if self.pilot_run else self.prior_good
        return "buy_annual" if self.expected_buy_utility(p) > 0 else "decline"

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        _ = payload
        self.action_count += 1
        if action == "run_pilot":
            if self.pilot_run or self.decision is not None:
                raise EnvironmentError("pilot unavailable after pilot/commitment")
            self.pilot_run = True
            return {"pilot_signal": self.deterministic_signal}
        if action in {"buy_annual", "decline"}:
            if self.decision is not None:
                raise EnvironmentError("decision already committed")
            self.decision = action
            return {"decision_recorded": True}
        raise EnvironmentError(f"unknown decision action: {action}")

    def score(self) -> dict[str, float | int | bool | str]:
        initial_optimal = self.optimal_initial_policy()
        if self.pilot_run:
            initial_policy_followed = initial_optimal == "pilot"
        else:
            initial_policy_followed = self.decision == initial_optimal
        final_optimal = self.optimal_final_policy()
        final_correct = self.decision == final_optimal

        if self.decision == "buy_annual":
            realized = self.buy_good_utility if self.hidden_good else self.buy_bad_utility
        elif self.decision == "decline":
            realized = 0.0
        else:
            realized = min(self.buy_bad_utility, -100.0)
        if self.pilot_run:
            realized -= self.pilot_cost

        normalized = 1.0 if initial_policy_followed and final_correct else (0.5 if final_correct else 0.0)
        return {
            "correct_terminal_decision": final_correct,
            "initial_policy_optimal": initial_policy_followed,
            "optimal_initial_policy": initial_optimal,
            "optimal_final_policy": final_optimal,
            "pilot_run": self.pilot_run,
            "realized_utility": realized,
            "environment_actions": self.action_count,
            "normalized_score": normalized,
        }
