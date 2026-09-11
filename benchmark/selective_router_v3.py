#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from typing import Any

from zai_adapter import DEFAULT_BASE_URL, chat_completion

ROUTER_MODEL = os.getenv("ROUTER_V3_MODEL", "glm-5.3-flash")
ROUTER_BASE_URL = os.getenv("ROUTER_V3_BASE_URL", DEFAULT_BASE_URL)
ROUTER_KEY = os.getenv("ROUTER_V3_API_KEY") or os.environ.get("ZAI_API_KEY")
MAX_FORMAT_ATTEMPTS = 3

ROUTER_V3 = """Estimate the MARGINAL value of invoking the deep FULL reasoning policy beyond what a competent unstructured GLM-5.1 answer would already do. Do not classify absolute task complexity.

Choose FULL only when omitting deliberate structured mechanism/engineering reasoning is likely to materially reduce correctness or decision quality. Strong reasons for FULL include at least one of:
1) choosing among consequential interventions under uncertainty where tradeoffs, constraints, reversibility, monitoring, feedback, failure modes, or second-order effects can change the action;
2) integrating contradictory or sequential evidence where revising the causal model is central to the eventual decision;
3) designing a genuinely discriminating test among non-obvious competing mechanisms when resolving them is necessary before a costly, risky, or hard-to-reverse action;
4) allocating resources or selecting a policy where multiple interacting uncertainties make a one-step calculation or generic caveat insufficient.

Choose CONTROL when a competent answer can resolve the task with factual retrieval, direct explanation, straightforward computation, an established procedure, a simple crossover/sensitivity calculation, or an obvious causal-caution pattern such as: 'timing/correlation does not prove cause; check the obvious confounders or compare the affected groups.' Multiple possible causes alone are NOT enough for FULL. A costly context alone is NOT enough. Technical vocabulary, length, difficulty, and the words test/experiment/cause are NOT enough.

Important conservative rule: if the correct answer is basically one direct measurement, one straightforward comparison, or one obvious deconfounding step and deeper reasoning is unlikely to change the recommendation, choose CONTROL even if the prompt contains several plausible causes. When uncertain about marginal value, prefer CONTROL unless you can name a concrete way FULL reasoning is likely to change the answer or action.

Return JSON only: {\"mode\":\"FULL|CONTROL\",\"signals\":[\"short marginal-value signal\"],\"confidence\":0.0}."""


def parse_first_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    stripped = text.strip()
    try:
        value = json.loads(stripped)
        if not isinstance(value, dict):
            raise ValueError("router output must be a JSON object")
        return value
    except json.JSONDecodeError as original:
        for index, char in enumerate(stripped):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(stripped[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        raise original


def validate_route_payload(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload.get("mode")
    if mode not in {"FULL", "CONTROL"}:
        raise RuntimeError(f"invalid router mode: {payload}")
    signals = payload.get("signals", [])
    if not isinstance(signals, list) or not all(isinstance(x, str) for x in signals):
        raise RuntimeError(f"invalid router signals: {payload}")
    confidence = payload.get("confidence", 0.5)
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        raise RuntimeError(f"invalid router confidence: {payload}")
    return {"mode": mode, "signals": signals[:6], "confidence": float(confidence)}


def route_text(user_input: str) -> dict[str, Any]:
    if not ROUTER_KEY:
        raise RuntimeError("ROUTER_V3_API_KEY or ZAI_API_KEY is required")
    old_temp = os.environ.get("ZAI_ROUTER_TEMPERATURE")
    os.environ["ZAI_ROUTER_TEMPERATURE"] = "0"
    last_format_error: Exception | None = None
    try:
        for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
            result = chat_completion(
                model=ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": ROUTER_V3},
                    {"role": "user", "content": user_input},
                ],
                json_mode=True,
                api_key=ROUTER_KEY,
                base_url=ROUTER_BASE_URL,
                max_tokens_env="ZAI_ROUTER_MAX_TOKENS",
                temperature_env="ZAI_ROUTER_TEMPERATURE",
            )
            try:
                payload = validate_route_payload(parse_first_json_object(result["text"]))
            except (json.JSONDecodeError, RuntimeError, ValueError) as exc:
                last_format_error = exc
                if attempt == MAX_FORMAT_ATTEMPTS:
                    raise RuntimeError(f"router failed JSON/payload validation after {MAX_FORMAT_ATTEMPTS} attempts") from exc
                continue
            return {
                **payload,
                "usage": result["usage"],
                "model": ROUTER_MODEL,
                "base_url": ROUTER_BASE_URL,
                "format_attempts": attempt,
            }
    finally:
        if old_temp is None:
            os.environ.pop("ZAI_ROUTER_TEMPERATURE", None)
        else:
            os.environ["ZAI_ROUTER_TEMPERATURE"] = old_temp
    raise last_format_error or RuntimeError("router failed")


def route_case(case: dict[str, Any]) -> dict[str, Any]:
    turns = case.get("turns") or []
    if not turns or turns[0].get("turn") != 1:
        raise RuntimeError("case must have turn 1 before routing")
    return route_text(str(turns[0]["agent_input"]))
