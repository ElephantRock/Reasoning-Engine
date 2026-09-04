from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Any

from openai import OpenAI

DEFAULT_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
# Backward-compatible alias used by the original Pilot 001 runner.
BASE_URL = os.getenv("ZAI_BASE_URL", DEFAULT_BASE_URL)


@lru_cache(maxsize=8)
def _client(api_key: str, base_url: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=base_url)


def chat_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    json_mode: bool = False,
    api_key: str | None = None,
    base_url: str | None = None,
    max_tokens_env: str = "ZAI_MAX_TOKENS",
    temperature_env: str = "ZAI_TEMPERATURE",
) -> dict[str, Any]:
    resolved_key = api_key or os.environ["ZAI_API_KEY"]
    resolved_base = base_url or BASE_URL
    client = _client(resolved_key, resolved_base)

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    max_tokens = os.getenv(max_tokens_env)
    if max_tokens:
        kwargs["max_tokens"] = int(max_tokens)

    temperature = os.getenv(temperature_env)
    if temperature:
        kwargs["temperature"] = float(temperature)

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_error: Exception | None = None
    for attempt in range(4):
        started = time.perf_counter()
        try:
            response = client.chat.completions.create(**kwargs)
            usage = response.usage
            choice = response.choices[0]
            return {
                "text": choice.message.content or "",
                "usage": {
                    "input_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
                    "output_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
                    "latency_ms": (time.perf_counter() - started) * 1000,
                },
                "response_id": response.id,
                "finish_reason": choice.finish_reason,
                "base_url": resolved_base,
            }
        except Exception as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(2**attempt)

    raise last_error or RuntimeError("Z.AI request failed")
