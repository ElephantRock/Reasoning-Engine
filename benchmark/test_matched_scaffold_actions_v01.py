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


if __name__ == "__main__":
    unittest.main()
