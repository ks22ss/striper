# maint: fix analyze auth error handling + small cleanup

## Reproduction summary

When a user provides an invalid OpenAI API key in the analyze request (e.g. from the frontend API key input), the OpenAI SDK raises `AuthenticationError`. Previously this was caught by the generic `except Exception` and returned **500** with `"Analysis failed: Invalid API key"`. That is misleading: 500 suggests a server fault, while auth failures are client/config issues.

## Fix

- **Handle `openai.AuthenticationError`** explicitly: return **503** with `"Invalid API key"` for clearer semantics (service unavailable due to auth).
- **Extract `_analyze_error_to_http(exc)`** in `main.py`: centralizes exception → HTTP mapping (ValueError, AuthenticationError, generic Exception). Keeps the analyze endpoint simpler and the logic easier to test.

## Changes

| File | Change |
|------|--------|
| `app/main.py` | Import `AuthenticationError`; add `_analyze_error_to_http()`; use it in analyze handler |
| `tests/test_main.py` | `test_analyze_invalid_api_key_returns_503` – regression test for auth error path |

## Tests

```bash
.venv/bin/python -m pytest tests/ -v
# 50 passed
```

## Refactor note

`_analyze_error_to_http` replaces the previous inline try/except chain. Order of checks: `ValueError` (with `_is_api_key_error` for env-missing case) → `AuthenticationError` → fallback 500.

## Residual risks

- **Other OpenAI errors**: `RateLimitError`, `APITimeoutError`, etc. still return 500. Could be refined in a follow-up if needed.
- **Message exposure**: `str(exc)` in 500 responses may leak internal details; acceptable for this app’s scope.
