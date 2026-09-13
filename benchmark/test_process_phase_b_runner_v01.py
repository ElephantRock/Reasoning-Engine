from __future__ import annotations

import json
import unittest

import run_process_phase_b_v01 as core
import run_process_phase_b_v01_exec as runner
from process_phase_b_suite_v01 import CASES


class ScriptedModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, system, request):
        self.calls.append({"system": system, "request": request})
        if not self.responses:
            raise AssertionError("script exhausted")
        item = self.responses.pop(0)
        if isinstance(item, str):
            text, finish = item, "stop"
        else:
            text = item.get("text")
            if text is None:
                text = json.dumps(item.get("json", item))
            finish = item.get("finish_reason", "stop")
        return {
            "text": text,
            "finish_reason": finish,
            "usage": {"input_tokens": 10, "output_tokens": 5, "latency_ms": 1},
            "response_id": f"stub-{len(self.calls)}",
        }


def p(to_state, payload, action=None, action_payload=None):
    return {
        "to_state": to_state,
        "payload": payload,
        "environment_action": action,
        "action_payload": action_payload or {},
    }


def g(action=None, action_payload=None, note="public state"):
    return {"action": action, "action_payload": action_payload or {}, "public_note": note}


class RequestIntegrityTests(unittest.TestCase):
    def test_format_repair_records_both_calls(self):
        model = ScriptedModel(["not json", {"json": g(None, note="same intended request")}])
        value, calls = runner.request_json(
            model,
            core.GENERIC_SYSTEM,
            {"x": 1},
            core._validate_generic_shape,
            call_id="format-test",
        )
        self.assertIsNone(value["action"])
        self.assertEqual(len(calls), 2)
        self.assertIn("format_repair", calls[1]["request"])

    def test_length_failure_preserves_completed_call_record(self):
        model = ScriptedModel([{"text": "{", "finish_reason": "length"}])
        with self.assertRaises(runner.TechnicalIncomplete) as caught:
            runner.request_json(model, core.GENERIC_SYSTEM, {"x": 1}, core._validate_generic_shape, call_id="length-test")
        self.assertEqual(len(caught.exception.calls), 1)
        self.assertEqual(caught.exception.calls[0]["finish_reason"], "length")

    def test_semantic_invalid_request_gets_no_retry(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        model = ScriptedModel([{"json": p("DERIVATION", {"supporting_constraints": ["x"], "conclusion": "x"})}])
        result = runner.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "execution_failure")
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(len(result["model_calls"]), 1)


class SpecialistExecutionTests(unittest.TestCase):
    def test_deductive_specialist(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        model = ScriptedModel([
            {"json": p("CONSTRAINTS", {"constraints": ["shared technician", "restart after both checks"]}, "inspect_constraints")},
            {"json": p("DERIVATION", {"supporting_constraints": ["shared technician"], "conclusion": "earliest is 70"})},
            {"json": p("BOUNDARY_CHECK", {"boundary_test": "test requested deadline 65"}, "test_candidate", {"restart_minute": 65})},
            {"json": p("CONCLUSION", {"decision": "commit minute 70; deadline cannot be promised"}, "commit_restart", {"restart_minute": 70})},
        ])
        result = runner.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["effective_normalized_score"], 1.0)

    def test_abductive_specialist(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-AD01")
        model = ScriptedModel([
            {"json": p("HYPOTHESES", {"hypotheses": ["route_change", "library_regression"]})},
            {"json": p("PREDICTIONS", {"predictions": {"route_change": "network and zone evidence", "library_regression": "different pattern"}})},
            {"json": p("DISCRIMINATING_CHECK", {"check": "network"}, "check_network")},
            {"json": p("UPDATE", {"ranking": ["route_change", "library_regression"], "evidence_used": ["network", "zone"]}, "compare_zones")},
            {"json": p("RANKING", {"decision": "route_change", "residual_uncertainty": "other changes remain possible"}, "diagnose", {"cause": "route_change"})},
        ])
        result = runner.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["effective_normalized_score"], 1.0)
        self.assertEqual(result["actions_used"], 3)

    def test_planning_specialist_unhealthy_recovery_branch(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-SP02")
        model = ScriptedModel([
            {"json": p("ACTIONS", {"actions": ["safe migration", "premature finalization"]}, "enable_dual_write")},
            {"json": p("CANDIDATE_PATHS", {"paths": ["verify then cut over", "finalize early"]}, "backfill")},
            {"json": p("CONSTRAINT_CHECK", {"constraints": ["checksum before read shift"]}, "verify_checksum")},
            {"json": p("BRANCH_OR_COMMIT", {"selected_path": "verified cutover"}, "shift_reads", {"percent": 100})},
            {"json": p("CHECKPOINT", {"checkpoint": "probe health"}, "probe_health")},
            {"json": p("RECOVERY", {"recovery": "rollback unhealthy shard"}, "rollback_reads")},
            {"json": p("FINISH", {"decision": "abort after rollback"}, "abort_migration")},
        ])
        result = runner.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["effective_normalized_score"], 1.0)
        self.assertEqual(result["transitions_used"], 7)

    def test_decision_specialist_can_finish_protocol_after_environment_commit(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-DT02")
        model = ScriptedModel([
            {"json": p("OUTCOMES", {"outcomes": {"buy": "up/down", "pilot": "information", "decline": "zero"}})},
            {"json": p("UNCERTAINTY", {"decision_relevant_uncertainty": "product quality"})},
            {"json": p("ASYMMETRIC_VALUE", {"value_comparison": "large bad-state downside"})},
            {"json": p("INFORMATION_VALUE", {"information_value": "pilot can change commitment"}, "run_pilot")},
            {"json": p("DECISION", {"decision": "decline after bad signal"}, "decline")},
            {"json": p("REVERSAL_CONDITION", {"change_if": "strong positive local evidence"})},
        ])
        result = runner.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["environment_complete"])
        self.assertTrue(result["protocol_complete"])
        self.assertEqual(result["effective_normalized_score"], 1.0)


class ComparatorExecutionTests(unittest.TestCase):
    def test_matched_scaffold_common_actions_and_terminal_decision(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        model = ScriptedModel([
            {"json": p("PROCESS_1", {"analysis": "inspect"}, "inspect_constraints")},
            {"json": p("PROCESS_2", {"analysis": "derive"})},
            {"json": p("PROCESS_3", {"analysis": "test"}, "test_candidate", {"restart_minute": 65})},
            {"json": p("DECIDE", {"analysis": "commit"}, "commit_restart", {"restart_minute": 70})},
        ])
        result = runner.run_case_condition(case, "MATCHED_SCAFFOLD", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["effective_normalized_score"], 1.0)

    def test_post_terminal_environment_action_is_rejected(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        model = ScriptedModel([
            {"json": p("PROCESS_1", {"analysis": "commit early"}, "commit_restart", {"restart_minute": 70})},
            {"json": p("PROCESS_2", {"analysis": "try to act again"}, "inspect_constraints")},
        ])
        result = runner.run_case_condition(case, "MATCHED_SCAFFOLD", model)
        self.assertEqual(result["status"], "execution_failure")
        self.assertEqual(len(result["model_calls"]), 2)
        self.assertEqual(result["effective_normalized_score"], 0.0)

    def test_control_and_full_share_generic_interface(self):
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        for condition in ("CONTROL", "FULL"):
            model = ScriptedModel([
                {"json": g("test_candidate", {"restart_minute": 65}, "test deadline")},
                {"json": g(None, note="derive earliest feasible restart")},
                {"json": g("commit_restart", {"restart_minute": 70}, "commit exact earliest")},
            ])
            result = runner.run_case_condition(case, condition, model)
            self.assertEqual(result["status"], "success", condition)
            self.assertEqual(result["effective_normalized_score"], 1.0, condition)
            self.assertLessEqual(result["actions_used"], core.protocol_specs()[case["family"]].action_budget)


class AggregationTests(unittest.TestCase):
    def test_two_eligible_families_authorize_phase_c_design_only(self):
        runs = []
        eligible_families = {"DEDUCTIVE_CONSTRAINT", "ABDUCTIVE_DIAGNOSTIC"}
        for case in CASES:
            for condition in core.CONDITIONS:
                score = 0.5
                if case["family"] in eligible_families:
                    if condition == "SPECIALIST":
                        score = 1.0
                    elif condition == "MATCHED_SCAFFOLD":
                        score = 0.5
                runs.append({
                    "case_id": case["case_id"],
                    "family": case["family"],
                    "condition": condition,
                    "status": "success",
                    "environment_complete": True,
                    "effective_normalized_score": score,
                    "catastrophic_failure": False,
                    "model_calls": [],
                    "actions_used": 0,
                })
        summary = core.aggregate(runs)
        self.assertEqual(set(summary["eligible_families"]), eligible_families)
        self.assertEqual(summary["program_decision"], "DESIGN_PHASE_C_ELIGIBLE_SUBSET")

    def test_design_validation(self):
        core.validate_design()


if __name__ == "__main__":
    unittest.main()
