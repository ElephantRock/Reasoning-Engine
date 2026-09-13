#!/usr/bin/env python3
"""Final reviewed Phase-B executable surface.

This wrapper removes experiment-only identifiers from every model-facing request.
Internal case IDs and condition labels remain in artifact keys and call IDs, but the
target model sees only the public task, common action catalog, remaining action
budget, observations, and its condition-specific control interface.
"""

from __future__ import annotations

from typing import Any

import run_process_phase_b_v01 as core


def _public_base_request(case: dict[str, Any], env: Any, condition: str, remaining_actions: int) -> dict[str, Any]:
    # `condition` is intentionally accepted for signature compatibility and
    # intentionally not emitted. Case IDs encode family abbreviations, so they
    # are also excluded from model-visible context.
    _ = condition
    return {
        "task": env.task_text(),
        "action_catalog": core.action_catalog(case["family"]),
        "remaining_environment_actions": remaining_actions,
    }


# The reviewed executor resolves this helper dynamically from the shared core.
# Patch it before importing the executor module so all model-facing requests use
# the public/blinded view.
core._base_request = _public_base_request

import run_process_phase_b_v01_exec as _exec  # noqa: E402

RequestFailure = _exec.RequestFailure
TechnicalIncomplete = _exec.TechnicalIncomplete
FormatFailure = _exec.FormatFailure
request_json = _exec.request_json
run_protocol_condition = _exec.run_protocol_condition
run_generic_condition = _exec.run_generic_condition
run_case_condition = _exec.run_case_condition
technical_partial_run = _exec.technical_partial_run


def main() -> None:
    _exec.main()


if __name__ == "__main__":
    main()
