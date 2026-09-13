from __future__ import annotations

import unittest

from protocol_environments_v02 import (
    DecisionEnvironment,
    DiagnosticEnvironment,
    FeasibilityEnvironment,
    PlanningEnvironment,
)
from protocol_runtime_v02 import (
    BudgetExceeded,
    EnvironmentError,
    InvalidTransition,
    ProtocolRuntime,
    matched_scaffold_for,
    protocol_specs,
)


class ProtocolSpecTests(unittest.TestCase):
    def test_registry_contains_only_authorized_phase_a_protocols(self) -> None:
        self.assertEqual(
            set(protocol_specs()),
            {
                "DEDUCTIVE_CONSTRAINT",
                "ABDUCTIVE_DIAGNOSTIC",
                "SEARCH_PLANNING",
                "DECISION_THEORETIC",
            },
        )

    def test_specs_and_matched_scaffolds_validate_and_match_budgets(self) -> None:
        for spec in protocol_specs().values():
            spec.validate()
            scaffold = matched_scaffold_for(spec)
            scaffold.validate()
            self.assertEqual(scaffold.max_transitions, spec.max_transitions)
            self.assertEqual(scaffold.action_budget, spec.action_budget)
            self.assertNotEqual(scaffold.name, spec.name)


class RuntimeSafetyTests(unittest.TestCase):
    def test_illegal_reasoning_transition_is_rejected_without_mutation(self) -> None:
        spec = protocol_specs()["DEDUCTIVE_CONSTRAINT"]
        env = FeasibilityEnvironment()
        runtime = ProtocolRuntime(spec, env)
        with self.assertRaises(InvalidTransition):
            runtime.transition("DERIVATION", {"claim": "skip constraints"})
        self.assertEqual(runtime.state, "PREMISES")
        self.assertEqual(runtime.transitions_used, 0)
        self.assertEqual(runtime.actions_used, 0)
        self.assertEqual(runtime.trace, [])

    def test_failed_environment_action_costs_budget_and_is_logged(self) -> None:
        spec = protocol_specs()["SEARCH_PLANNING"]
        env = PlanningEnvironment()
        runtime = ProtocolRuntime(spec, env)
        with self.assertRaises(EnvironmentError):
            runtime.transition(
                "ACTIONS",
                {"intent": "attempt premature backfill"},
                environment_action="backfill",
            )
        self.assertEqual(runtime.state, "STATE")
        self.assertEqual(runtime.transitions_used, 0)
        self.assertEqual(runtime.actions_used, 1)
        self.assertEqual(len(runtime.failed_actions), 1)
        self.assertEqual(env.violations, 1)

    def test_action_budget_cannot_be_exceeded(self) -> None:
        spec = protocol_specs()["DEDUCTIVE_CONSTRAINT"]
        env = FeasibilityEnvironment()
        runtime = ProtocolRuntime(spec, env)
        runtime.transition("CONSTRAINTS", {"x": 1}, environment_action="inspect_constraints")
        runtime.transition(
            "DERIVATION",
            {"x": 2},
            environment_action="test_deadline",
            action_payload={"restart_minute": 100},
        )
        runtime.transition("BOUNDARY_CHECK", {"x": 3}, environment_action="inspect_constraints")
        with self.assertRaises(BudgetExceeded):
            runtime.transition(
                "CONCLUSION",
                {"x": 4},
                environment_action="commit_restart",
                action_payload={"restart_minute": 105},
            )

    def test_finish_requires_terminal_state(self) -> None:
        runtime = ProtocolRuntime(
            protocol_specs()["DEDUCTIVE_CONSTRAINT"],
            FeasibilityEnvironment(),
        )
        with self.assertRaises(InvalidTransition):
            runtime.finish()


class EnvironmentTests(unittest.TestCase):
    def test_feasibility_environment_has_objective_boundary(self) -> None:
        env = FeasibilityEnvironment()
        result = env.step("test_deadline", {"restart_minute": 100})
        self.assertFalse(result["feasible"])
        self.assertEqual(result["minimum_restart_minute"], 105)
        env.step("commit_restart", {"restart_minute": 105})
        self.assertTrue(env.score()["correct_terminal_decision"])
        self.assertTrue(env.score()["deadline_promise_rejected"])

    def test_diagnostic_environment_hides_cause_behind_checks(self) -> None:
        env = DiagnosticEnvironment()
        self.assertEqual(env.evidence_seen, set())
        route = env.step("check_route")
        self.assertTrue(route["route_changed_overnight"])
        env.step("diagnose", {"cause": "route_change"})
        score = env.score()
        self.assertTrue(score["correct_terminal_decision"])
        self.assertTrue(score["supported_correct_diagnosis"])

    def test_planning_environment_enforces_prerequisites_and_rollback(self) -> None:
        env = PlanningEnvironment()
        with self.assertRaises(EnvironmentError):
            env.step("compact_old")
        env.step("enable_dual_write")
        env.step("backfill")
        env.step("verify_checksum")
        env.step("shift_reads", {"percent": 50})
        env.step("rollback_reads")
        self.assertEqual(env.read_percent_new, 0)
        self.assertFalse(env.compacted_old)

    def test_decision_environment_scores_information_and_realized_utility(self) -> None:
        env = DecisionEnvironment(product_good=False)
        signal = env.step("run_pilot")
        self.assertEqual(signal["pilot_signal"], "bad")
        env.step("decline")
        score = env.score()
        self.assertTrue(score["correct_terminal_decision"])
        self.assertEqual(score["realized_utility_k"], -23)
        self.assertEqual(score["regret_k"], 23)


class EndToEndTraceTests(unittest.TestCase):
    def test_deductive_protocol_can_complete_objective_task(self) -> None:
        runtime = ProtocolRuntime(
            protocol_specs()["DEDUCTIVE_CONSTRAINT"],
            FeasibilityEnvironment(),
        )
        runtime.transition("CONSTRAINTS", {"constraints": "shared technician"}, environment_action="inspect_constraints")
        runtime.transition(
            "DERIVATION",
            {"minimum": 105},
            environment_action="test_deadline",
            action_payload={"restart_minute": 100},
        )
        runtime.transition("BOUNDARY_CHECK", {"boundary": "104 fails, 105 succeeds"})
        runtime.transition(
            "CONCLUSION",
            {"decision": "do not promise 13:00"},
            environment_action="commit_restart",
            action_payload={"restart_minute": 105},
        )
        result = runtime.finish()
        self.assertTrue(result["environment_score"]["correct_terminal_decision"])
        self.assertEqual(result["actions_used"], 3)

    def test_abductive_protocol_can_acquire_discriminating_evidence(self) -> None:
        runtime = ProtocolRuntime(
            protocol_specs()["ABDUCTIVE_DIAGNOSTIC"],
            DiagnosticEnvironment(),
        )
        runtime.transition("HYPOTHESES", {"hypotheses": ["route_change", "library_regression"]})
        runtime.transition(
            "PREDICTIONS",
            {"prediction": "route effect should be zone-local"},
            environment_action="check_route",
        )
        runtime.transition(
            "DISCRIMINATING_CHECK",
            {"check": "compare same library across zones"},
            environment_action="check_library",
        )
        runtime.transition("UPDATE", {"ranking": ["route_change", "library_regression"]})
        runtime.transition(
            "RANKING",
            {"decision": "route_change"},
            environment_action="diagnose",
            action_payload={"cause": "route_change"},
        )
        result = runtime.finish()
        self.assertTrue(result["environment_score"]["supported_correct_diagnosis"])

    def test_planning_protocol_can_finish_safe_migration(self) -> None:
        runtime = ProtocolRuntime(
            protocol_specs()["SEARCH_PLANNING"],
            PlanningEnvironment(),
        )
        runtime.transition("ACTIONS", {"actions": "enumerated"}, environment_action="enable_dual_write")
        runtime.transition("CANDIDATE_PATHS", {"paths": ["safe", "premature cutover"]}, environment_action="backfill")
        runtime.transition("CONSTRAINT_CHECK", {"constraint": "checksum before reads"}, environment_action="verify_checksum")
        runtime.transition(
            "BRANCH_OR_COMMIT",
            {"branch": "cut over after verification"},
            environment_action="shift_reads",
            action_payload={"percent": 100},
        )
        runtime.transition("CHECKPOINT", {"checkpoint": "new reads healthy"}, environment_action="compact_old")
        runtime.transition("FINISH", {"decision": "migration complete"}, environment_action="finish")
        result = runtime.finish()
        self.assertTrue(result["environment_score"]["correct_terminal_decision"])
        self.assertEqual(result["environment_score"]["constraint_violations"], 0)

    def test_decision_protocol_can_use_information_before_commitment(self) -> None:
        runtime = ProtocolRuntime(
            protocol_specs()["DECISION_THEORETIC"],
            DecisionEnvironment(product_good=False),
        )
        runtime.transition("OUTCOMES", {"actions": ["buy", "pilot", "decline"]})
        runtime.transition("UNCERTAINTY", {"uncertainty": "local error rate"})
        runtime.transition("ASYMMETRIC_VALUE", {"downside": "nonrefundable annual license"})
        runtime.transition(
            "INFORMATION_VALUE",
            {"voi": "pilot can change decision"},
            environment_action="run_pilot",
        )
        runtime.transition(
            "DECISION",
            {"decision": "decline after bad pilot"},
            environment_action="decline",
        )
        runtime.transition("REVERSAL_CONDITION", {"change_if": "credible good local evidence"})
        result = runtime.finish()
        self.assertTrue(result["environment_score"]["correct_terminal_decision"])
        self.assertEqual(result["environment_score"]["realized_utility_k"], -23)


if __name__ == "__main__":
    unittest.main()
