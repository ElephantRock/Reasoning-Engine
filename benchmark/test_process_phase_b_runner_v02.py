from __future__ import annotations

import json
import os
import unittest
from collections import Counter
from unittest.mock import patch

import run_process_phase_b_v02 as core
import run_process_phase_b_v02_reviewed as runner
from process_phase_b_suite_v02 import CASES, FAMILIES


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
        value, calls = core.request_json(
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
        with self.assertRaises(core.TechnicalIncomplete) as caught:
            core.request_json(
                model,
                core.GENERIC_SYSTEM,
                {"x": 1},
                core._validate_generic_shape,
                call_id="length-test",
            )
        self.assertEqual(len(caught.exception.calls), 1)
        self.assertEqual(caught.exception.calls[0]["finish_reason"], "length")

    def test_semantic_invalid_request_gets_no_retry(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DC01")
        model = ScriptedModel([
            {"json": p("DERIVATION", {"supporting_constraints": ["x"], "conclusion": "x"})}
        ])
        result = core.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "execution_failure")
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(len(result["model_calls"]), 1)


class SpecialistExecutionTests(unittest.TestCase):
    def test_deductive_specialist_uses_unambiguous_restoration_endpoint(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DC01")
        model = ScriptedModel([
            {"json": p("CONSTRAINTS", {"constraints": ["shared technician", "restart after both checks"]}, "inspect_constraints")},
            {"json": p("DERIVATION", {"supporting_constraints": ["shared technician"], "conclusion": "earliest service restoration is minute 48"})},
            {"json": p("BOUNDARY_CHECK", {"boundary_test": "test minute 47"}, "test_candidate", {"service_restored_minute": 47})},
            {"json": p("CONCLUSION", {"decision": "restore at minute 48"}, "commit_restoration", {"service_restored_minute": 48})},
        ])
        result = core.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["effective_normalized_score"], 1.0)
        derivation_request = model.calls[1]["request"]
        contract = derivation_request["next_state_contracts"]["DERIVATION"]["action_contract"]
        self.assertEqual(contract["environment_action_mode"], "forbidden")
        self.assertTrue(contract["environment_action_must_be_null"])

    def test_abductive_specialist(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-AD01")
        model = ScriptedModel([
            {"json": p("HYPOTHESES", {"hypotheses": ["upstream_policy", "route_change", "library_regression"]})},
            {"json": p("PREDICTIONS", {"predictions": {"upstream_policy": "no network or zone signal", "route_change": "zone pattern"}})},
            {"json": p("DISCRIMINATING_CHECK", {"check": "network"}, "check_network")},
            {"json": p("UPDATE", {"ranking": ["upstream_policy", "library_regression"], "evidence_used": ["network false"]}, "compare_zones")},
            {"json": p("RANKING", {"decision": "upstream_policy", "residual_uncertainty": "low after two checks"}, "diagnose", {"cause": "upstream_policy"})},
        ])
        result = core.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["effective_normalized_score"], 1.0)
        self.assertEqual(result["actions_used"], 3)

    def test_planning_specialist_unhealthy_recovery_branch(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-SP01")
        model = ScriptedModel([
            {"json": p("ACTIONS", {"actions": ["safe migration", "premature finalization"]}, "enable_dual_write")},
            {"json": p("CANDIDATE_PATHS", {"paths": ["verify then cut over", "finalize early"]}, "backfill")},
            {"json": p("CONSTRAINT_CHECK", {"constraints": ["checksum before read shift"]}, "verify_checksum")},
            {"json": p("BRANCH_OR_COMMIT", {"selected_path": "verified cutover"}, "shift_reads", {"percent": 100})},
            {"json": p("CHECKPOINT", {"checkpoint": "probe health"}, "probe_health")},
            {"json": p("RECOVERY", {"recovery": "rollback unhealthy shard"}, "rollback_reads")},
            {"json": p("FINISH", {"decision": "abort after rollback"}, "abort_migration")},
        ])
        result = core.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["effective_normalized_score"], 1.0)
        self.assertEqual(result["transitions_used"], 7)

    def test_decision_specialist_no_action_states_are_explicit_and_protocol_finishes(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DT02")
        model = ScriptedModel([
            {"json": p("OUTCOMES", {"outcomes": {"buy": "up/down", "pilot": "information", "decline": "zero"}})},
            {"json": p("UNCERTAINTY", {"decision_relevant_uncertainty": "product quality"})},
            {"json": p("ASYMMETRIC_VALUE", {"value_comparison": "bad-state downside is large"})},
            {"json": p("INFORMATION_VALUE", {"information_value": "pilot can change the commitment"}, "run_pilot")},
            {"json": p("DECISION", {"decision": "decline after bad signal"}, "decline")},
            {"json": p("REVERSAL_CONDITION", {"change_if": "strong positive local evidence"})},
        ])
        result = core.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["environment_complete"])
        self.assertTrue(result["protocol_complete"])
        self.assertEqual(result["effective_normalized_score"], 1.0)
        first_contract = model.calls[0]["request"]["next_state_contracts"]["OUTCOMES"]["action_contract"]
        self.assertTrue(first_contract["environment_action_must_be_null"])
        final_request = model.calls[-1]["request"]
        self.assertTrue(final_request["environment_terminal"])
        final_contract = final_request["next_state_contracts"]["REVERSAL_CONDITION"]["action_contract"]
        self.assertTrue(final_contract["environment_action_must_be_null"])


class ComparatorExecutionTests(unittest.TestCase):
    def test_matched_scaffold_common_actions_and_terminal_decision(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DC01")
        model = ScriptedModel([
            {"json": p("PROCESS_1", {"analysis": "inspect"}, "inspect_constraints")},
            {"json": p("PROCESS_2", {"analysis": "derive"})},
            {"json": p("PROCESS_3", {"analysis": "test"}, "test_candidate", {"service_restored_minute": 47})},
            {"json": p("DECIDE", {"analysis": "commit"}, "commit_restoration", {"service_restored_minute": 48})},
        ])
        result = core.run_case_condition(case, "MATCHED_SCAFFOLD", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["effective_normalized_score"], 1.0)

    def test_post_terminal_matched_action_is_rejected(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DT03")
        model = ScriptedModel([
            {"json": p("PROCESS_1", {"analysis": "commit now"}, "buy_annual")},
            {"json": p("PROCESS_2", {"analysis": "try to act after commit"}, "run_pilot")},
        ])
        result = core.run_case_condition(case, "MATCHED_SCAFFOLD", model)
        self.assertEqual(result["status"], "execution_failure")
        self.assertEqual(len(result["model_calls"]), 2)
        self.assertEqual(result["effective_normalized_score"], 0.0)

    def test_control_and_full_share_generic_environment_interface(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DC01")
        for condition in ("CONTROL", "FULL"):
            model = ScriptedModel([
                {"json": g("test_candidate", {"service_restored_minute": 47}, "test boundary")},
                {"json": g(None, note="derive earliest service restoration")},
                {"json": g("commit_restoration", {"service_restored_minute": 48}, "commit exact restoration")},
            ])
            result = core.run_case_condition(case, condition, model)
            self.assertEqual(result["status"], "success", condition)
            self.assertEqual(result["effective_normalized_score"], 1.0, condition)
            self.assertLessEqual(result["actions_used"], core.protocol_specs()[case["family"]].action_budget)


class BlindingTests(unittest.TestCase):
    def assert_blinded(self, request):
        serialized = json.dumps(request)
        self.assertNotIn("case_id", request)
        self.assertNotIn("condition_interface", request)
        self.assertNotIn("PCB2-", serialized)
        for family in FAMILIES:
            self.assertNotIn(family, serialized)
        for label in core.CONDITIONS:
            self.assertNotIn(label, serialized)

    def test_generic_target_view_hides_experimental_identifiers(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DC01")
        model = ScriptedModel([
            {"json": g("commit_restoration", {"service_restored_minute": 48}, "commit exact restoration")}
        ])
        result = core.run_case_condition(case, "CONTROL", model)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(model.calls), 1)
        self.assert_blinded(model.calls[0]["request"])

    def test_specialist_target_view_hides_experimental_identifiers(self):
        case = next(c for c in CASES if c["case_id"] == "PCB2-DC01")
        model = ScriptedModel([
            {"json": p("CONSTRAINTS", {"constraints": ["shared technician", "restart after both"]}, "inspect_constraints")},
            {"json": p("DERIVATION", {"supporting_constraints": ["shared technician"], "conclusion": "restoration 48"})},
            {"json": p("BOUNDARY_CHECK", {"boundary_test": "minute 47"}, "test_candidate", {"service_restored_minute": 47})},
            {"json": p("CONCLUSION", {"decision": "restore 48"}, "commit_restoration", {"service_restored_minute": 48})},
        ])
        result = core.run_case_condition(case, "SPECIALIST", model)
        self.assertEqual(result["status"], "success")
        for call in model.calls:
            self.assert_blinded(call["request"])


class ExecutionOrderTests(unittest.TestCase):
    def test_case_order_round_robins_families(self):
        order = runner.balanced_case_order()
        self.assertEqual(len(order), 24)
        for block_start in range(0, 24, 4):
            self.assertEqual(
                [case["family"] for case in order[block_start:block_start + 4]],
                list(FAMILIES),
            )

    def test_condition_order_balanced_within_family_and_globally(self):
        global_counts = Counter()
        per_family_counts = {family: Counter() for family in FAMILIES}
        for family in FAMILIES:
            for rep in range(6):
                order = runner.balanced_condition_order(family, rep)
                self.assertEqual(set(order), set(core.CONDITIONS))
                for position, condition in enumerate(order, start=1):
                    global_counts[(condition, position)] += 1
                    per_family_counts[family][(condition, position)] += 1
        for family in FAMILIES:
            for condition in core.CONDITIONS:
                for position in range(1, 5):
                    self.assertIn(per_family_counts[family][(condition, position)], {1, 2})
        for condition in core.CONDITIONS:
            for position in range(1, 5):
                self.assertEqual(global_counts[(condition, position)], 6)
        runner.validate_execution_order()


class AggregationAndAuthorizationTests(unittest.TestCase):
    def test_two_eligible_families_authorize_phase_c_design_only(self):
        runs = []
        eligible_families = {"DEDUCTIVE_CONSTRAINT", "ABDUCTIVE_DIAGNOSTIC"}
        for case in CASES:
            for condition in core.CONDITIONS:
                score = 0.5
                if case["family"] in eligible_families:
                    score = 1.0 if condition == "SPECIALIST" else 0.5
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
        runner.validate_execution_order()

    def test_reviewed_main_is_hard_blocked_without_separate_authorization(self):
        with patch.dict(
            os.environ,
            {"ZAI_MAX_TOKENS": "16384", "ZAI_TEMPERATURE": "0"},
            clear=False,
        ):
            os.environ.pop("PHASE_B_V02_EXECUTION_AUTHORIZED", None)
            with self.assertRaisesRegex(RuntimeError, "not authorized"):
                runner.validate_executable_boundary()


if __name__ == "__main__":
    unittest.main()
