from __future__ import annotations

import json
import unittest
from pathlib import Path

from process_phase_b_interface_v02 import ACTION_CATALOG, build_specialist_request
from process_phase_b_suite_v01 import CASES as V01_CASES, make_environment as make_environment_v01
from process_phase_b_suite_v02 import CASES, FAMILIES, make_environment, validate_suite
from protocol_environments_v03 import DIAGNOSTIC_PATTERNS
from protocol_runtime_v04 import ProtocolRuntime, protocol_specs, public_action_contract


ROOT = Path(__file__).resolve().parent


class FreshSuiteTests(unittest.TestCase):
    def test_suite_validates_and_is_balanced(self):
        validate_suite()
        self.assertEqual(len(CASES), 24)
        self.assertEqual(len({case["case_id"] for case in CASES}), 24)
        for family in FAMILIES:
            self.assertEqual(sum(case["family"] == family for case in CASES), 6)

    def test_no_exact_v01_case_or_parameter_cell_is_reused(self):
        old = json.loads((ROOT / "process_phase_b_cases_v01.json").read_text(encoding="utf-8"))
        self.assertTrue(all(not case["case_id"].startswith("PCB-") for case in CASES))
        old_cells = {(x["family"], json.dumps(x["params"], sort_keys=True)) for x in old}
        for case in CASES:
            cell = (case["family"], json.dumps(case["params"], sort_keys=True))
            self.assertNotIn(cell, old_cells)

    def test_public_task_texts_are_not_exact_v01_reuses(self):
        old_tasks = {make_environment_v01(case).task_text() for case in V01_CASES}
        new_tasks = {make_environment(case).task_text() for case in CASES}
        self.assertEqual(len(new_tasks), 24)
        self.assertTrue(new_tasks.isdisjoint(old_tasks))

    def test_decision_suite_contains_all_three_initial_policies(self):
        observed = {
            make_environment(case).optimal_initial_policy()
            for case in CASES
            if case["family"] == "DECISION_THEORETIC"
        }
        self.assertEqual(observed, {"pilot", "buy_annual", "decline"})

    def test_planning_suite_contains_both_objective_terminal_branches(self):
        health = {
            case["params"]["new_shard_healthy"]
            for case in CASES
            if case["family"] == "SEARCH_PLANNING"
        }
        self.assertEqual(health, {True, False})

    def test_diagnostic_single_check_outcome_never_uniquely_identifies_cause(self):
        actions = ("check_network", "compare_zones", "inspect_pool")
        for action in actions:
            for outcome in (True, False):
                causes = [
                    cause
                    for cause, pattern in DIAGNOSTIC_PATTERNS.items()
                    if pattern[action] is outcome
                ]
                self.assertGreaterEqual(len(causes), 2, (action, outcome, causes))


class DeductiveEndpointTests(unittest.TestCase):
    def _case(self):
        return next(case for case in CASES if case["family"] == "DEDUCTIVE_CONSTRAINT")

    def test_task_and_action_schema_unambiguously_score_service_restoration(self):
        env = make_environment(self._case())
        task = env.task_text()
        self.assertIn("FINISHED", task)
        self.assertIn("service is restored", task)
        self.assertIn("not the minute when restart begins", task)
        self.assertIn("commit_restoration", ACTION_CATALOG["DEDUCTIVE_CONSTRAINT"])
        self.assertNotIn("commit_restart", ACTION_CATALOG["DEDUCTIVE_CONSTRAINT"])
        self.assertEqual(
            ACTION_CATALOG["DEDUCTIVE_CONSTRAINT"]["commit_restoration"]["args"],
            {"service_restored_minute": "integer"},
        )

    def test_restart_start_minute_is_not_accepted_as_restoration_minute(self):
        env = make_environment(self._case())
        start = env.earliest_restart_start
        finish = env.minimum_restoration
        self.assertGreater(finish, start)
        result = env.step("test_candidate", {"service_restored_minute": start})
        self.assertFalse(result["feasible"])
        env.step("commit_restoration", {"service_restored_minute": finish})
        self.assertEqual(env.score()["normalized_score"], 1.0)

    def test_all_deductive_tasks_state_post_isolation_precedence_and_terminal_quantity(self):
        for case in CASES:
            if case["family"] != "DEDUCTIVE_CONSTRAINT":
                continue
            env = make_environment(case)
            task = env.task_text()
            self.assertIn("After isolation completes", task)
            self.assertIn("FINISHED", task)
            self.assertIn("not the minute when restart begins", task)
            public = env.step("inspect_constraints", {})
            self.assertEqual(public["terminal_quantity"], "service_restored_minute")


class SpecialistActionContractTests(unittest.TestCase):
    def _representative(self, family: str):
        return next(case for case in CASES if case["family"] == family)

    def test_action_catalog_exactly_matches_environment_action_universe(self):
        for family in FAMILIES:
            env = make_environment(self._representative(family))
            self.assertEqual(set(ACTION_CATALOG[family]), set(env.available_actions()))

    def test_public_contract_exactly_mirrors_runtime_action_tags_for_every_state(self):
        for family, spec in protocol_specs().items():
            env = make_environment(self._representative(family))
            for state, rule in spec.rules.items():
                contract = public_action_contract(spec, state, env)
                tags = set(rule.allowed_action_tags)
                if not tags:
                    self.assertEqual(contract["environment_action_mode"], "forbidden")
                    self.assertTrue(contract["environment_action_must_be_null"])
                    self.assertFalse(contract["environment_action_required"])
                    self.assertEqual(contract["allowed_action_names"], [])
                    self.assertEqual(contract["allowed_action_tags"], [])
                    continue

                expected = [
                    action
                    for action in env.available_actions()
                    if "ANY" in tags or set(env.action_tags(action)) & tags
                ]
                self.assertEqual(contract["allowed_action_names"], expected)
                self.assertTrue(set(contract["allowed_action_names"]) <= set(ACTION_CATALOG[family]))
                self.assertEqual(contract["allowed_action_tags"], sorted(tags))
                self.assertFalse(contract["environment_action_must_be_null"])
                self.assertEqual(
                    contract["environment_action_mode"],
                    "required" if rule.action_required else "optional",
                )
                self.assertEqual(contract["environment_action_required"], rule.action_required)

    def test_previously_hidden_negative_constraints_are_now_explicit(self):
        cases = {
            family: self._representative(family)
            for family in ("DEDUCTIVE_CONSTRAINT", "ABDUCTIVE_DIAGNOSTIC", "DECISION_THEORETIC")
        }
        targets = {
            "DEDUCTIVE_CONSTRAINT": "DERIVATION",
            "ABDUCTIVE_DIAGNOSTIC": "PREDICTIONS",
            "DECISION_THEORETIC": "OUTCOMES",
        }
        for family, state in targets.items():
            env = make_environment(cases[family])
            contract = public_action_contract(protocol_specs()[family], state, env)
            self.assertEqual(contract["environment_action_mode"], "forbidden")
            self.assertTrue(contract["environment_action_must_be_null"])
            self.assertEqual(contract["allowed_action_names"], [])

    def test_decision_information_value_is_explicitly_optional_and_limited_to_pilot(self):
        family = "DECISION_THEORETIC"
        env = make_environment(self._representative(family))
        contract = public_action_contract(protocol_specs()[family], "INFORMATION_VALUE", env)
        self.assertEqual(contract["environment_action_mode"], "optional")
        self.assertEqual(contract["allowed_action_names"], ["run_pilot"])
        self.assertFalse(contract["environment_action_must_be_null"])

    def test_specialist_request_contains_complete_contract_and_no_experiment_identifiers(self):
        for family in FAMILIES:
            case = self._representative(family)
            env = make_environment(case)
            runtime = ProtocolRuntime(protocol_specs()[family], env)
            request = build_specialist_request(case, env, runtime)
            serialized = json.dumps(request)
            self.assertNotIn(case["case_id"], serialized)
            self.assertNotIn(family, serialized)
            for label in ("SPECIALIST", "MATCHED_SCAFFOLD", "CONTROL", "FULL"):
                self.assertNotIn(label, serialized)
            self.assertEqual(set(request["next_state_contracts"]), set(runtime.legal_next_states()))
            for state, state_contract in request["next_state_contracts"].items():
                self.assertIn("payload_contract", state_contract)
                self.assertIn("action_contract", state_contract)
                self.assertIn("environment_action_mode", state_contract["action_contract"])
                self.assertIn("environment_action_must_be_null", state_contract["action_contract"])
                self.assertEqual(
                    state_contract["action_contract"],
                    public_action_contract(runtime.spec, state, env),
                )


if __name__ == "__main__":
    unittest.main()
