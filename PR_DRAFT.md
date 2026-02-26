# maint: fix history limit, whitespace prompts, invalid API key + small cleanup

## Problem

Three maintenance gaps identified from code review (no formal bug issues open):

1. **History limit unbounded**: `GET /history?limit=999999` returns up to 999999 rows, enabling DoS and excessive DB load.
2. **Whitespace-only prompts accepted**: Prompt `"   \t  "` passes `min_length=1` and wastes OpenAI API calls.
3. **Invalid API key returns 500**: `AuthenticationError` from OpenAI is caught by generic `Exception` handler; clients get 500 instead of 503 (service unavailable).

## Solution

| Fix | Change |
|-----|--------|
| **History limit** | `_clamp_history_limit()` and `HISTORY_MAX_LIMIT = 100`; `limit` clamped before DB call |
| **Whitespace prompts** | `prompt_not_whitespace_only` validator on `AnalyzeRequest`; returns 422 with "Prompt cannot be whitespace-only" |
| **Invalid API key** | `except AuthenticationError` before generic `Exception`; returns 503 with error message |

## Refactor

- Use `status.HTTP_503_SERVICE_UNAVAILABLE` instead of literal `503` for API key errors (consistency with FastAPI constants).

## Changes

| File | Changes |
|------|---------|
| `app/main.py` | `HISTORY_MAX_LIMIT`, `_clamp_history_limit`, `except AuthenticationError`, `status.HTTP_503_SERVICE_UNAVAILABLE` |
| `app/models.py` | `prompt_not_whitespace_only` validator |
| `tests/test_main.py` | `test_history_limit_clamped`, `test_analyze_whitespace_only_prompt_rejected`, `test_analyze_invalid_api_key_returns_503` |

## Tests run

```
uv run pytest tests/ -v  → 50 passed (47 existing + 3 new)
uv run ruff check .     → All checks passed
```

## Reproduction

- **History**: `GET /history?limit=9999` → previously returned 9999 rows; now clamped to 100.
- **Whitespace**: `POST /analyze` with `{"prompt": "   \t  "}` → previously 200 (API call); now 422.
- **Invalid key**: `POST /analyze` with `{"prompt": "Test.", "api_key": "sk-invalid"}` → previously 500; now 503.

## Known risks

- **History limit**: 100 is arbitrary; may need tuning for power users.
- **Whitespace**: Prompts with only newlines (e.g. `"\n\n"`) are rejected; acceptable for analysis use case.
