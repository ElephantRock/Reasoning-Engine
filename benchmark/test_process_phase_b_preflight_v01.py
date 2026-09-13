from __future__ import annotations

import unittest

from process_phase_b_suite_v01 import CASES, FAMILIES, make_environment, validate_suite
from protocol_environments_v03 import DIAGNOSTIC_PATTERNS, DecisionEnvironmentV3
from protocol_runtime_v03 import InvalidTransition, ProtocolRuntime, matched_scaffold_for, protocol_specs


class SuiteShapeTests(unittest.TestCase):
    def test_suite_validates(self) -> None:
        validate_suite()

    def test_six_cases_per_family(self) -> None:
        for family in FAMILIES:
            self.assertEqual(sum(c["family"] == family for c in CASES), 6)


class AntiTrivialityTests(unittest.TestCase):
    def test_feasibility_candidate_test_does_not_reveal_exact_optimum(self) -> None:
        case = next(c for c in CASES if c["family"] == "DEDUCTIVE_CONSTRAINT")
        env = make_environment(case)
        response = env.step("test_candidate", {"restart_minute": case["params"]["deadline"]})
        self.assertNotIn("minimum_restart", response)
        self.assertNotIn("slack", response)

    def test_diagnostic_no_single_check_outcome_uniquely_identifies_cause(self) -> None:
        checks = ("check_network", "compare_zones", "inspect_pool")
        causes = list(DIAGNOSTIC_PATTERNS)
        for check in checks:
            for outcome in (True, False):
                matching = [cause for cause in causes if DIAGNOSTIC_PATTERNS[cause][check] is outcome]
                self.assertGreaterEqual(len(matching), 2, (check, outcome, matching))

    def test_planning_suite_requires_two_distinct_terminal_branches(self) -> None:
        values = {c["params"]["new_shard_healthy"] for c in CASES if c["family"] == "SEARCH_PLANNING"}
        self.assertEqual(values, {True, False})

    def test_decision_suite_contains_pilot_buy_and_decline_optima(self) -> None:
        policies = set()
        for case in CASES:
            if case["family"] == "DECISION_THEORETIC":
                policies.add(make_environment(case).optimal_initial_policy())
        self.assertEqual(policies, {"pilot", "buy_annual", "decline"})

    def test_tasks_do_not_expose_hidden_case_fields(self) -> None:
        for case in CASES:
            text = make_environment(case).task_text().lower()
            for forbidden in ("hidden_cause", "hidden_good", "deterministic_signal", "minimum_restart"):
                self.assertNotIn(forbidden, text)


class ObjectiveEnvironmentTests(unittest.TestCase):
    def test_feasibility_rewards_exact_earliest_commitment(self) -> None:
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        env = make_environment(case)
        env.step("commit_restart", {"restart_minute": env.minimum_restart})
        self.assertEqual(env.score()["normalized_score"], 1.0)
        later = make_environment(case)
        later.step("commit_restart", {"restart_minute": env.minimum_restart + 10})
        self.assertEqual(later.score()["normalized_score"], 0.0)

    def test_diagnostic_needs_two_checks_for_full_credit(self) -> None:
        case = next(c for c in CASES if c["case_id"] == "PCB-AD01")
        env = make_environment(case)
        env.step("check_network")
        env.step("diagnose", {"cause": "route_change"})
        self.assertEqual(env.score()["normalized_score"], 0.4)
        supported = make_environment(case)
        supported.step("check_network")
        supported.step("compare_zones")
        supported.step("diagnose", {"cause": "route_change"})
        self.assertEqual(supported.score()["normalized_score"], 1.0)

    def test_planning_healthy_and_unhealthy_objective_paths(self) -> None:
        healthy = make_environment(next(c for c in CASES if c["case_id"] == "PCB-SP01"))
        for action, payload in (
            ("enable_dual_write", None),
            ("backfill", None),
            ("verify_checksum", None),
            ("shift_reads", {"percent": 100}),
            ("probe_health", None),
            ("finalize_migration", None),
        ):
            healthy.step(action, payload)
        self.assertEqual(healthy.score()["normalized_score"], 1.0)

        unhealthy = make_environment(next(c for c in CASES if c["case_id"] == "PCB-SP02"))
        for action, payload in (
            ("enable_dual_write", None),
            ("backfill", None),
            ("verify_checksum", None),
            ("shift_reads", {"percent": 100}),
            ("probe_health", None),
            ("rollback_reads", None),
            ("abort_migration", None),
        ):
            unhealthy.step(action, payload)
        self.assertEqual(unhealthy.score()["normalized_score"], 1.0)
        self.assertEqual(unhealthy.score()["terminal_branch"], "aborted")

    def test_decision_pilot_is_noisy_not_hidden_state_revelation(self) -> None:
        env = DecisionEnvironmentV3(
            prior_good=0.5,
            sensitivity=0.8,
            false_positive_rate=0.2,
            pilot_cost=10,
            buy_good_utility=100,
            buy_bad_utility=-100,
            hidden_good=False,
            deterministic_signal="good",
        )
        result = env.step("run_pilot")
        self.assertEqual(result, {"pilot_signal": "good"})
        self.assertNotIn("hidden_good", result)
        self.assertFalse(env.hidden_good)


class ProtocolContractTests(unittest.TestCase):
    def test_abductive_requires_two_distinct_hypotheses(self) -> None:
        case = next(c for c in CASES if c["case_id"] == "PCB-AD01")
        runtime = ProtocolRuntime(protocol_specs()["ABDUCTIVE_DIAGNOSTIC"], make_environment(case))
        with self.assertRaises(InvalidTransition):
            runtime.transition("HYPOTHESES", {"hypotheses": ["route_change"]})

    def test_abductive_cannot_commit_before_two_evidence_actions(self) -> None:
        case = next(c for c in CASES if c["case_id"] == "PCB-AD01")
        runtime = ProtocolRuntime(protocol_specs()["ABDUCTIVE_DIAGNOSTIC"], make_environment(case))
        runtime.transition("HYPOTHESES", {"hypotheses": ["route_change", "library_regression"]})
        runtime.transition("PREDICTIONS", {"predictions": {"route_change": "network pattern", "library_regression": "version pattern"}})
        runtime.transition("DISCRIMINATING_CHECK", {"check": "network"}, environment_action="check_network")
        # UPDATE requires the second evidence action; omitting it is rejected.
        with self.assertRaises(InvalidTransition):
            runtime.transition("UPDATE", {"ranking": ["route_change", "library_regression"], "evidence_used": ["network"]})

    def test_planning_protocol_follows_checkpoint_dependent_branch(self) -> None:
        case = next(c for c in CASES if c["case_id"] == "PCB-SP02")
        runtime = ProtocolRuntime(protocol_specs()["SEARCH_PLANNING"], make_environment(case))
        runtime.transition("ACTIONS", {"actions": ["safe migration", "premature commit"]}, environment_action="enable_dual_write")
        runtime.transition("CANDIDATE_PATHS", {"paths": ["verify then cut over", "commit immediately"]}, environment_action="backfill")
        runtime.transition("CONSTRAINT_CHECK", {"constraints": ["checksum before reads"]}, environment_action="verify_checksum")
        runtime.transition("BRANCH_OR_COMMIT", {"selected_path": "verified cutover"}, environment_action="shift_reads", action_payload={"percent": 100})
        checkpoint = runtime.transition("CHECKPOINT", {"checkpoint": "probe before irreversible finalization"}, environment_action="probe_health")
        self.assertFalse(checkpoint.environment_observation["new_shard_healthy"])
        runtime.transition("RECOVERY", {"recovery": "rollback"}, environment_action="rollback_reads")
        runtime.transition("FINISH", {"decision": "abort"}, environment_action="abort_migration")
        self.assertEqual(runtime.finish()["environment_score"]["normalized_score"], 1.0)

    def test_matched_scaffold_matches_budgets(self) -> None:
        for spec in protocol_specs().values():
            scaffold = matched_scaffold_for(spec)
            scaffold.validate()
            self.assertEqual(scaffold.max_transitions, spec.max_transitions)
            self.assertEqual(scaffold.action_budget, spec.action_budget)


if __name__ == "__main__":
    unittest.main()
