#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

# pilot.py still contains the provider-neutral experiment logic plus its legacy
# OpenAI client initialization. A dummy key prevents import-time validation;
# all actual model calls are replaced below by the Z.AI adapter.
os.environ.setdefault("OPENAI_API_KEY", "unused-provider-shim")

import pilot  # noqa: E402
from zai_adapter import BASE_URL, chat_completion  # noqa: E402

TARGET = os.getenv("ZAI_TARGET_MODEL", "glm-5.1")
JUDGE = os.getenv("ZAI_JUDGE_MODEL", TARGET)

pilot.TARGET = TARGET
pilot.JUDGE = JUDGE

JSON_SYSTEM_PROMPTS = {
    pilot.ROUTER,
    pilot.PROTO_JUDGE,
    pilot.OUTCOME_JUDGE,
    pilot.PAIRWISE_JUDGE,
}


def zai_call(system, messages, model):
    wire_messages = []
    if system:
        wire_messages.append({"role": "system", "content": system})
    wire_messages.extend(messages)
    return chat_completion(
        model=model,
        messages=wire_messages,
        json_mode=system in JSON_SYSTEM_PROMPTS,
    )


pilot.call = zai_call


def annotate_report():
    report_path = Path(__file__).resolve().parent / "results" / "pilot_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["provider"] = "z.ai"
    report["api_protocol"] = "openai-chat-completions"
    report["base_url"] = BASE_URL
    report["target_model"] = TARGET
    report["judge_model"] = JUDGE
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    pilot.main()
    annotate_report()
