from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import run_process_phase_b_v02 as core
import run_process_phase_b_v02_reviewed as runner
from process_phase_b_suite_v02 import CASES


class ExecutableProviderBoundaryTests(unittest.TestCase):
    def test_provider_exception_is_technical_not_scientific_failure(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DC01")
        with patch.object(core, "zai_model_call", side_effect=ValueError("transport decode failure")):
            with self.assertRaises(core.TechnicalIncomplete) as caught:
                core.run_case_condition(case, "SPECIALIST", runner.executable_model_call)
        self.assertIn("provider/model call raised ValueError", str(caught.exception))
        self.assertEqual(caught.exception.calls, [])

    def test_completed_calls_are_preserved_before_later_provider_exception(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DC01")
        first = {
            "text": '{"to_state":"CONSTRAINTS","payload":{"constraints":["shared technician","restart after both checks"]},"environment_action":"inspect_constraints","action_payload":{}}',
            "finish_reason": "stop",
            "usage": {"input_tokens": 10, "output_tokens": 5, "latency_ms": 1},
            "response_id": "first-completed-call",
        }
        with patch.object(
            core,
            "zai_model_call",
            side_effect=[first, RuntimeError("provider unavailable")],
        ):
            with self.assertRaises(core.TechnicalIncomplete) as caught:
                core.run_case_condition(case, "SPECIALIST", runner.executable_model_call)
        self.assertEqual(len(caught.exception.calls), 1)
        self.assertEqual(caught.exception.calls[0]["response_id"], "first-completed-call")

    def test_scaffold_system_hides_matched_comparator_wording(self):
        captured = {}

        def fake_call(system, request):
            captured["system"] = system
            captured["request"] = request
            return {
                "text": '{"ok":true}',
                "finish_reason": "stop",
                "usage": {},
                "response_id": "capture",
            }

        with patch.object(core, "zai_model_call", side_effect=fake_call):
            runner.executable_model_call(core.SCAFFOLD_SYSTEM, {"probe": True})
        self.assertNotIn("matched", captured["system"].lower())
        self.assertNotIn("MATCHED_SCAFFOLD", captured["system"])
        self.assertIn("generic structured scaffold", captured["system"])

    def test_authorization_gate_precedes_executable_provider_boundary(self):
        with patch.dict(
            os.environ,
            {"ZAI_MAX_TOKENS": "16384", "ZAI_TEMPERATURE": "0"},
            clear=False,
        ):
            os.environ.pop("PHASE_B_V02_EXECUTION_AUTHORIZED", None)
            with patch.object(runner, "executable_model_call") as model_call:
                with self.assertRaisesRegex(RuntimeError, "not authorized"):
                    runner.main()
                model_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
