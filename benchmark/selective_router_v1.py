#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from typing import Any

from zai_adapter import DEFAULT_BASE_URL, chat_completion

ROUTER_MODEL = os.getenv("ROUTER_V1_MODEL", "glm-5.3-flash")
ROUTER_BASE_URL = os.getenv("ROUTER_V1_BASE_URL", DEFAULT_BASE_URL)
ROUTER_KEY = os.getenv("ROUTER_V1_API_KEY") or os.environ.get("ZAI_API_KEY")
MAX_FORMAT_ATTEMPTS = 3

ROUTER_V1 = """Decide whether deep FULL reasoning is likely to add decision-relevant quality beyond an unstructured answer. Choose FULL only when the current user input materially requires at least one of: (1) distinguishing competing causal mechanisms with discriminating evidence or a consequential test; (2) designing or choosing an intervention under uncertainty where reversibility, monitoring, feedback, constraints, failure modes, or second-order effects can change the action; (3) integrating contradictory or sequential evidence where causal-model revision is decision-critical; (4) a consequential action under materially reducible causal uncertainty. Choose CONTROL for factual retrieval, direct explanation, straightforward computation, established procedure, low-consequence advice, or cases where added causal/engineering analysis is unlikely to change the answer or action. Difficulty, length, technical vocabulary, or the words 'test'/'experiment' alone are not reasons to choose FULL. Return JSON only: {\"mode\":\"FULL|CONTROL\",\"signals\":[\"short signal\"],\"confidence\":0.0}."""


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
        raise RuntimeError("ROUTER_V1_API_KEY or ZAI_API_KEY is required")
    old_temp = os.environ.get("ZAI_ROUTER_TEMPERATURE")
    os.environ["ZAI_ROUTER_TEMPERATURE"] = "0"
    last_format_error: Exception | None = None
    try:
        for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
            result = chat_completion(
                model=ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": ROUTER_V1},
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
