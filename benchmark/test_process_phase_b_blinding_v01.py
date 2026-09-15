from __future__ import annotations

import json
import unittest
from collections import Counter

import run_process_phase_b_v01_reviewed as runner
from process_phase_b_suite_v01 import CASES, FAMILIES


class CaptureModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, system, request):
        self.requests.append(request)
        response = self.responses.pop(0)
        return {
            "text": json.dumps(response),
            "finish_reason": "stop",
            "usage": {"input_tokens": 1, "output_tokens": 1, "latency_ms": 1},
            "response_id": f"capture-{len(self.requests)}",
        }


def protocol(to_state, payload, action=None, action_payload=None):
    return {
        "to_state": to_state,
        "payload": payload,
        "environment_action": action,
        "action_payload": action_payload or {},
    }


class TargetViewTests(unittest.TestCase):
    def assert_blinded(self, request):
        self.assertNotIn("case_id", request)
        self.assertNotIn("condition_interface", request)
        serialized = json.dumps(request)
        self.assertNotIn("PCB-DC01", serialized)
        self.assertNotIn("DEDUCTIVE_CONSTRAINT", serialized)
        self.assertNotIn("MATCHED_SCAFFOLD", serialized)
        self.assertNotIn("SPECIALIST", serialized)

    def test_generic_target_view_hides_case_and_condition_labels(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        model = CaptureModel([
            {"action": "commit_restart", "action_payload": {"restart_minute": 70}, "public_note": "commit earliest feasible restart"}
        ])
        result = runner.run_case_condition(case, "CONTROL", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(model.requests), 1)
        self.assert_blinded(model.requests[0])

    def test_specialist_target_view_hides_experimental_labels(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        model = CaptureModel([
            protocol("CONSTRAINTS", {"constraints": ["shared technician", "restart after both"]}, "inspect_constraints"),
            protocol("DERIVATION", {"supporting_constraints": ["shared technician"], "conclusion": "earliest 70"}),
            protocol("BOUNDARY_CHECK", {"boundary_test": "deadline 65"}, "test_candidate", {"restart_minute": 65}),
            protocol("CONCLUSION", {"decision": "commit 70"}, "commit_restart", {"restart_minute": 70}),
        ])
        result = runner.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        for request in model.requests:
            self.assert_blinded(request)


class ExecutionOrderTests(unittest.TestCase):
    CONDITIONS = ("SPECIALIST", "MATCHED_SCAFFOLD", "FULL", "CONTROL")

    def test_case_order_round_robins_families(self):
        order = runner.balanced_case_order()
        self.assertEqual(len(order), 24)
        for block_start in range(0, 24, 4):
            self.assertEqual(
                [case["family"] for case in order[block_start:block_start + 4]],
                list(FAMILIES),
            )

    def test_condition_order_is_balanced_within_each_family_and_globally(self):
        global_counts = Counter()
        per_family_counts = {family: Counter() for family in FAMILIES}
        distinct_orders = {family: set() for family in FAMILIES}

        for family in FAMILIES:
            for family_rep_index in range(6):
                order = runner.balanced_condition_order(family, family_rep_index)
                self.assertEqual(set(order), set(self.CONDITIONS))
                distinct_orders[family].add(order)
                for position, condition in enumerate(order, start=1):
                    global_counts[(condition, position)] += 1
                    per_family_counts[family][(condition, position)] += 1

        for family in FAMILIES:
            self.assertGreater(len(distinct_orders[family]), 1)
            for condition in self.CONDITIONS:
                for position in range(1, 5):
                    self.assertIn(per_family_counts[family][(condition, position)], {1, 2})

        for condition in self.CONDITIONS:
            for position in range(1, 5):
                self.assertEqual(global_counts[(condition, position)], 6)

    def test_execution_case_schedule_uses_each_family_rotation_once_per_rep(self):
        family_seen = Counter()
        observed_orders = {family: [] for family in FAMILIES}
        for case in runner.balanced_case_order():
            family = case["family"]
            rep = family_seen[family]
            family_seen[family] += 1
            observed_orders[family].append(runner.balanced_condition_order(family, rep))
        self.assertEqual(dict(family_seen), {family: 6 for family in FAMILIES})
        for family in FAMILIES:
            self.assertEqual(len(observed_orders[family]), 6)


if __name__ == "__main__":
    unittest.main()
