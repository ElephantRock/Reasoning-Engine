from __future__ import annotations

import json
import unittest

import run_process_phase_b_v01_reviewed as runner
from process_phase_b_suite_v01 import CASES


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


if __name__ == "__main__":
    unittest.main()
