# Z.AI Provider Configuration

The benchmark target and evaluator use the Z.AI GLM Coding Plan OpenAI-compatible endpoint:

`https://api.z.ai/api/coding/paas/v4`

The runner uses the OpenAI Python SDK only as a protocol client and calls the Chat Completions API (`/chat/completions`).

## Authentication

Configure a GitHub Actions repository secret:

`ZAI_API_KEY`

Never commit the API key.

## Defaults

- Target model: `GLM-5.1`
- Judge model: `GLM-5.1`
- Base URL: `https://api.z.ai/api/coding/paas/v4`

All can be overridden by environment variables or workflow inputs.

## Environment variables

```bash
export ZAI_API_KEY=...
export ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
export ZAI_TARGET_MODEL=GLM-5.1
export ZAI_JUDGE_MODEL=GLM-5.1
```

Optional:

```bash
export ZAI_MAX_TOKENS=4096
export ZAI_TEMPERATURE=1.0
```

The benchmark does not depend on provider-side conversation state. Multi-turn benchmark cases send their accumulated transcript explicitly on each request.
