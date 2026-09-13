from __future__ import annotations

import unittest

from process_phase_b_suite_v01 import CASES, make_environment
from protocol_runtime_v03 import ProtocolRuntime, matched_scaffold_for, protocol_specs


class MatchedScaffoldActionTests(unittest.TestCase):
    def test_generic_scaffold_can_use_common_environment_actions(self) -> None:
        case = next(c for c in CASES if c["case_id"] == "PCB-DC01")
        specialist = protocol_specs()[case["family"]]
        scaffold = matched_scaffold_for(specialist)
        runtime = ProtocolRuntime(scaffold, make_environment(case))
        runtime.transition(
            "PROCESS_1",
            {"analysis": "inspect task constraints"},
            environment_action="inspect_constraints",
        )
        self.assertEqual(runtime.actions_used, 1)
        self.assertEqual(runtime.trace[0].environment_action, "inspect_constraints")

    def test_planning_scaffold_can_terminate_in_six_or_seven_transitions(self) -> None:
        case = next(c for c in CASES if c["case_id"] == "PCB-SP01")
        scaffold = matched_scaffold_for(protocol_specs()["SEARCH_PLANNING"])

        short = ProtocolRuntime(scaffold, make_environment(case))
        for state in ("PROCESS_1", "PROCESS_2", "PROCESS_3", "PROCESS_4", "PROCESS_5", "DECIDE"):
            short.transition(state, {"analysis": state})
        self.assertEqual(short.finish()["transitions_used"], 6)

        long = ProtocolRuntime(scaffold, make_environment(case))
        for state in ("PROCESS_1", "PROCESS_2", "PROCESS_3", "PROCESS_4", "PROCESS_5", "PROCESS_6", "DECIDE"):
            long.transition(state, {"analysis": state})
        self.assertEqual(long.finish()["transitions_used"], 7)


if __name__ == "__main__":
    unittest.main()
