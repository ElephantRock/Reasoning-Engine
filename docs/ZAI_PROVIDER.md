# Z.AI Provider Configuration

The benchmark target and evaluator use the Z.AI OpenAI-compatible Chat Completions protocol.

Default base URL:

`https://api.z.ai/api/coding/paas/v4`

The runner uses the OpenAI Python SDK only as a protocol client and calls the Chat Completions API (`/chat/completions`).

## Authentication

Configure a GitHub Actions repository secret:

`ZAI_API_KEY`

Never commit the API key.

## Defaults

- Target model: `glm-5.1`
- Judge model: `glm-5.1`
- Base URL: `https://api.z.ai/api/coding/paas/v4`

All can be overridden by environment variables or workflow inputs.

## Environment variables

```bash
export ZAI_API_KEY=...
export ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
export ZAI_TARGET_MODEL=glm-5.1
export ZAI_JUDGE_MODEL=glm-5.1
```

Optional:

```bash
export ZAI_MAX_TOKENS=4096
export ZAI_TEMPERATURE=1.0
```

## Coding-plan endpoint caveat

Z.AI documents `https://api.z.ai/api/coding/paas/v4` as the dedicated GLM Coding Plan endpoint and describes it for supported coding-tool scenarios. Its documentation recommends the general endpoint `https://api.z.ai/api/paas/v4` for other use cases.

The benchmark intentionally keeps `ZAI_BASE_URL` configurable. If the Coding Plan endpoint rejects or disallows the custom benchmark runner, switch the workflow input or environment variable to the general endpoint without changing experiment logic.

## Experimental behavior

The benchmark does not depend on provider-side conversation state. Multi-turn benchmark cases send their accumulated transcript explicitly on each request.

Z.AI Chat Completions usage fields `prompt_tokens` and `completion_tokens` are recorded as benchmark input and output token usage. Judge/router calls request JSON mode (`response_format={"type":"json_object"}`) for machine-readable outputs.
