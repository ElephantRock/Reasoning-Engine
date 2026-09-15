from __future__ import annotations

import json
import unittest

import recover_process_phase_b_v02_r1 as recovery
import run_process_phase_b_v02 as core


class RecoveryClassificationTests(unittest.TestCase):
    def test_budget_exhaustion_is_scientific_failure_and_preserves_calls(self) -> None:
        case = next(case for case in core.CASES if case["case_id"] == "PCB2-AD01")

        def always_act(_system, request):
            action = next(iter(request["action_catalog"]))
            response = {
                "to_state": request["legal_next_states"][0],
                "payload": {"analysis": "public state"},
                "environment_action": action,
                "action_payload": {},
            }
            return {
                "text": json.dumps(response),
                "usage": {"input_tokens": 10, "output_tokens": 5, "latency_ms": 1},
                "finish_reason": "stop",
                "response_id": "stub",
            }

        run = recovery.run_protocol_condition_recovery(
            case,
            "MATCHED_SCAFFOLD",
            always_act,
        )
        self.assertEqual(run["status"], "execution_failure")
        self.assertIn("BudgetExceeded", run["error"])
        self.assertEqual(run["effective_normalized_score"], 0.0)
        self.assertEqual(run["actions_used"], 3)
        self.assertEqual(len(run["model_calls"]), 4)
        self.assertTrue(run["cost_logging_complete"])

    def test_frozen_prefix_and_pending_count(self) -> None:
        self.assertEqual(
            recovery.expected_source_keys(),
            [
                ("PCB2-DC01", "SPECIALIST"),
                ("PCB2-DC01", "MATCHED_SCAFFOLD"),
                ("PCB2-DC01", "FULL"),
                ("PCB2-DC01", "CONTROL"),
                ("PCB2-AD01", "MATCHED_SCAFFOLD"),
            ],
        )
        self.assertEqual(len(recovery.execution_schedule()), 96)
        self.assertEqual(len(recovery.execution_schedule()[5:]), 91)

    def test_source_reclassification_does_not_invent_lost_trace(self) -> None:
        source = {
            "case_id": "PCB2-AD01",
            "family": "ABDUCTIVE_DIAGNOSTIC",
            "condition": "MATCHED_SCAFFOLD",
            "status": "technical_incomplete",
            "error": recovery.RECLASSIFIED_ERROR,
            "protocol_complete": False,
            "environment_complete": False,
            "transitions_used": None,
            "actions_used": None,
            "failed_requests": [],
            "trace": [],
            "environment_score": {},
            "effective_normalized_score": None,
            "model_calls": [],
            "catastrophic_failure": False,
            "decision_regret_secondary": None,
            "case_execution_position": 2,
            "family_rep_index": 1,
            "condition_execution_position": 1,
            "condition_order": ["MATCHED_SCAFFOLD", "FULL", "CONTROL", "SPECIALIST"],
        }
        line = json.dumps(source) + "\n"
        corrected = recovery.reclassify_source_budget_failure(source, line)
        self.assertEqual(corrected["status"], "execution_failure")
        self.assertEqual(corrected["effective_normalized_score"], 0.0)
        self.assertEqual(corrected["actions_used"], 3)
        self.assertIsNone(corrected["transitions_used"])
        self.assertEqual(corrected["trace"], [])
        self.assertEqual(corrected["model_calls"], [])
        self.assertFalse(corrected["cost_logging_complete"])
        self.assertFalse(corrected["recovery_annotation"]["fabricated_data"])

    def test_usage_metrics_mark_missing_cost_log(self) -> None:
        rows = []
        for condition in core.CONDITIONS:
            for _ in range(24):
                rows.append(
                    {
                        "condition": condition,
                        "status": "success",
                        "actions_used": 1,
                        "model_calls": [
                            {
                                "usage": {
                                    "input_tokens": 10,
                                    "output_tokens": 5,
                                    "latency_ms": 2,
                                }
                            }
                        ],
                        "cost_logging_complete": True,
                    }
                )
        missing = next(row for row in rows if row["condition"] == "MATCHED_SCAFFOLD")
        missing["cost_logging_complete"] = False
        missing["model_calls"] = []
        summary = recovery.usage_summary_with_coverage(rows)
        self.assertEqual(summary["MATCHED_SCAFFOLD"]["cost_log_records"], 23)
        self.assertEqual(summary["MATCHED_SCAFFOLD"]["total_records"], 24)
        self.assertAlmostEqual(summary["MATCHED_SCAFFOLD"]["cost_log_coverage"], 23 / 24)
        self.assertEqual(summary["MATCHED_SCAFFOLD"]["mean_model_calls"], 1)
        self.assertEqual(summary["SPECIALIST"]["cost_log_records"], 24)


if __name__ == "__main__":
    unittest.main()
