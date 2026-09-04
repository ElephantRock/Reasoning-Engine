from __future__ import annotations

import os
import time
from typing import Any

from openai import OpenAI

BASE_URL = os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/coding/paas/v4")
API_KEY = os.environ["ZAI_API_KEY"]

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def chat_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    json_mode: bool = False,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    max_tokens = os.getenv("ZAI_MAX_TOKENS")
    if max_tokens:
        kwargs["max_tokens"] = int(max_tokens)

    temperature = os.getenv("ZAI_TEMPERATURE")
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
            }
        except Exception as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(2**attempt)

    raise last_error or RuntimeError("Z.AI request failed")
