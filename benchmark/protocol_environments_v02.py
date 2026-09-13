"""Deterministic toy environments for process-constrained reasoning Phase A.

The environments expose a protocol-independent action universe. Different
reasoning protocols may constrain when the model is allowed to request an
action, but the environment itself never gives privileged evidence to a
particular protocol label.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from protocol_runtime_v02 import EnvironmentError


@dataclass
class FeasibilityEnvironment:
    """Objective constraint/feasibility toy environment."""

    committed_restart_minute: int | None = None
    checks: int = 0

    # Minutes after 11:20: 35 isolation + 30 calibration + 25 verification + 15 restart.
    minimum_restart_minute: int = 105
    deadline_minute: int = 100

    def available_actions(self) -> tuple[str, ...]:
        return ("inspect_constraints", "test_deadline", "commit_restart")

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        if action == "inspect_constraints":
            self.checks += 1
            return {
                "isolation": 35,
                "calibration": 30,
                "verification": 25,
                "restart": 15,
                "shared_technician": ("calibration", "verification"),
                "deadline_minute": self.deadline_minute,
            }
        if action == "test_deadline":
            self.checks += 1
            proposed = int(payload.get("restart_minute", self.deadline_minute))
            return {
                "proposed_restart_minute": proposed,
                "minimum_restart_minute": self.minimum_restart_minute,
                "feasible": proposed >= self.minimum_restart_minute,
                "slack": proposed - self.minimum_restart_minute,
            }
        if action == "commit_restart":
            proposed = int(payload["restart_minute"])
            self.committed_restart_minute = proposed
            return {"committed_restart_minute": proposed}
        raise EnvironmentError(f"unknown feasibility action: {action}")

    def score(self) -> dict[str, float | int | bool]:
        committed = self.committed_restart_minute
        return {
            "correct_terminal_decision": bool(committed is not None and committed >= self.minimum_restart_minute),
            "deadline_promise_rejected": bool(committed is not None and committed > self.deadline_minute),
            "constraint_checks": self.checks,
            "minimum_restart_minute": self.minimum_restart_minute,
        }


@dataclass
class DiagnosticEnvironment:
    """Hidden-cause environment with selectable evidence checks."""

    hidden_cause: str = "route_change"
    evidence_seen: set[str] = field(default_factory=set)
    diagnosis: str | None = None
    action_count: int = 0

    def available_actions(self) -> tuple[str, ...]:
        return ("check_route", "check_library", "check_resources", "diagnose")

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        self.action_count += 1
        if action == "check_route":
            self.evidence_seen.add(action)
            return {"route_changed_overnight": True, "affected_zone_matches": True}
        if action == "check_library":
            self.evidence_seen.add(action)
            return {"same_library_other_zones_near_baseline": True}
        if action == "check_resources":
            self.evidence_seen.add(action)
            return {"cpu_normal": True, "memory_normal": True}
        if action == "diagnose":
            cause = str(payload.get("cause", ""))
            if not cause:
                raise EnvironmentError("diagnose requires a non-empty cause")
            self.diagnosis = cause
            return {"diagnosis_recorded": cause}
        raise EnvironmentError(f"unknown diagnostic action: {action}")

    def score(self) -> dict[str, float | int | bool]:
        correct = self.diagnosis == self.hidden_cause
        discriminating = "check_route" in self.evidence_seen or "check_library" in self.evidence_seen
        return {
            "correct_terminal_decision": correct,
            "discriminating_evidence_acquired": discriminating,
            "supported_correct_diagnosis": bool(correct and discriminating),
            "environment_actions": self.action_count,
        }


@dataclass
class PlanningEnvironment:
    """Migration environment with prerequisites, rollback, and irreversible compaction."""

    dual_write: bool = False
    backfilled: bool = False
    checksum_verified: bool = False
    read_percent_new: int = 0
    compacted_old: bool = False
    finished: bool = False
    violations: int = 0
    action_count: int = 0

    def available_actions(self) -> tuple[str, ...]:
        # Constant action universe; preconditions are checked by step().
        return (
            "enable_dual_write",
            "backfill",
            "verify_checksum",
            "shift_reads",
            "rollback_reads",
            "compact_old",
            "finish",
        )

    def _require(self, condition: bool, message: str) -> None:
        if not condition:
            self.violations += 1
            raise EnvironmentError(message)

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        self.action_count += 1
        if action == "enable_dual_write":
            self._require(not self.compacted_old, "cannot enable dual-write after old shard compaction")
            self.dual_write = True
        elif action == "backfill":
            self._require(self.dual_write, "backfill requires dual-write first")
            self.backfilled = True
        elif action == "verify_checksum":
            self._require(self.backfilled, "checksum verification requires backfill")
            self.checksum_verified = True
        elif action == "shift_reads":
            self._require(self.checksum_verified, "read shift requires verified checksum")
            percent = int(payload.get("percent", 0))
            self._require(percent in range(10, 101, 10), "read shift must be a 10% increment")
            self._require(percent >= self.read_percent_new, "read shift cannot move backwards; use rollback_reads")
            self.read_percent_new = percent
        elif action == "rollback_reads":
            self._require(not self.compacted_old, "rollback unavailable after compaction")
            self.read_percent_new = 0
        elif action == "compact_old":
            self._require(self.checksum_verified, "compaction requires verified checksum")
            self._require(self.read_percent_new == 100, "compaction requires 100% reads on new shard")
            self.compacted_old = True
        elif action == "finish":
            self._require(self.compacted_old and self.read_percent_new == 100, "finish requires completed cutover")
            self.finished = True
        else:
            raise EnvironmentError(f"unknown planning action: {action}")
        return {
            "dual_write": self.dual_write,
            "backfilled": self.backfilled,
            "checksum_verified": self.checksum_verified,
            "read_percent_new": self.read_percent_new,
            "compacted_old": self.compacted_old,
            "finished": self.finished,
        }

    def score(self) -> dict[str, float | int | bool]:
        return {
            "correct_terminal_decision": self.finished,
            "constraint_violations": self.violations,
            "environment_actions": self.action_count,
            "rollback_still_available": not self.compacted_old,
        }


@dataclass
class DecisionEnvironment:
    """Toy value-of-information environment with objective realized utility."""

    product_good: bool = False
    pilot_run: bool = False
    decision: str | None = None
    action_count: int = 0

    def available_actions(self) -> tuple[str, ...]:
        return ("run_pilot", "buy_annual", "decline")

    def step(self, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        _ = payload
        self.action_count += 1
        if action == "run_pilot":
            if self.pilot_run:
                raise EnvironmentError("pilot can run only once")
            self.pilot_run = True
            return {"pilot_signal": "good" if self.product_good else "bad", "pilot_cost_k": 23}
        if action == "buy_annual":
            if self.decision is not None:
                raise EnvironmentError("decision already committed")
            self.decision = "buy_annual"
            return {"decision": self.decision}
        if action == "decline":
            if self.decision is not None:
                raise EnvironmentError("decision already committed")
            self.decision = "decline"
            return {"decision": self.decision}
        raise EnvironmentError(f"unknown decision action: {action}")

    def score(self) -> dict[str, float | int | bool]:
        # Utilities are in $k and intentionally simple: buying is +96 if the
        # product is good and -120 if bad. A pilot costs 23 before the final
        # decision. Declining has zero operating utility.
        if self.decision == "buy_annual":
            utility = 96 if self.product_good else -120
        elif self.decision == "decline":
            utility = 0
        else:
            utility = -150  # failure to commit is dominated in this toy task.
        if self.pilot_run:
            utility -= 23
        oracle = 96 if self.product_good else 0
        return {
            "correct_terminal_decision": self.decision == ("buy_annual" if self.product_good else "decline"),
            "pilot_run": self.pilot_run,
            "realized_utility_k": utility,
            "oracle_utility_k": oracle,
            "regret_k": oracle - utility,
            "environment_actions": self.action_count,
        }
