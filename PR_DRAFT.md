# PR Draft: maint: fix invalid API key + small cleanup

## Title
```
maint: fix invalid API key + small cleanup
```

## Description

### Problem
When the frontend provided an invalid OpenAI API key (e.g. `sk-invalid`), the OpenAI client raised `AuthenticationError`. The analyze endpoint caught it with the generic `Exception` handler and returned 500 "Analysis failed: ...". Users got a misleading server error instead of a clear API-key-related 503.

### Solution
- **Handle `AuthenticationError`** – Added `except AuthenticationError` before the generic `Exception` in the analyze endpoint. Returns 503 with the error message (e.g. "Invalid API key") for better UX.
- **Refactor** – Extracted `DEFAULT_SIMILARITY_THRESHOLD = 0.92` in `stripe.py` to avoid the magic number appearing in both the env default and the `ValueError` fallback.
- **History limit clamp** – Clamp `/history` `limit` param to 1–100 to prevent abuse.

### Changes
| File | Changes |
|------|---------|
| `app/main.py` | Import `AuthenticationError`; add `except AuthenticationError` → 503; use `status.HTTP_503_SERVICE_UNAVAILABLE`; add `HISTORY_MAX_LIMIT` and `_clamp_history_limit` |
| `app/stripe.py` | `DEFAULT_SIMILARITY_THRESHOLD` constant; use in `_get_similarity_threshold` |
| `tests/test_main.py` | `test_analyze_invalid_api_key_returns_503`, `test_history_limit_clamped` regression tests |

### Tests run
```bash
uv run pytest tests/ -v
# 49 passed
```

### Known risks
- **503 vs 401** – Invalid API key returns 503 (service unavailable) rather than 401 (unauthorized). Chosen for consistency with the existing "API key not configured" case, which also returns 503.
