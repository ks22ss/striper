# PR Draft: maint: fix history limit, whitespace prompts, invalid API key + small cleanup

## Title
```
maint: fix history limit, whitespace prompts, invalid API key + small cleanup
```

## Description

### Problem
1. **History limit unbounded** – Clients could pass `limit=999999`, causing unnecessary DB load.
2. **Whitespace-only prompts** – Prompts like `"   "` passed validation and returned score 0; unclear UX.
3. **Invalid API key returned 500** – When the frontend provided an invalid OpenAI API key, `AuthenticationError` was caught by the generic handler and returned 500 instead of 503 (service unavailable).

### Solution
1. **Clamp history limit** – Limit is clamped to 1–100 via `_clamp_history_limit()` and `HISTORY_MAX_LIMIT` constant.
2. **Reject whitespace-only prompts** – Added `prompt_not_whitespace_only` validator on `AnalyzeRequest`; returns 422 with clear message.
3. **Handle AuthenticationError** – Added `except AuthenticationError` before generic `Exception`; returns 503 with error message.

### Refactor
- Extracted `HISTORY_MAX_LIMIT = 100` and `_clamp_history_limit()` for clarity and reuse.

### Changes
| File | Changes |
|------|---------|
| `app/main.py` | `_clamp_history_limit`, `HISTORY_MAX_LIMIT`, `except AuthenticationError` |
| `app/models.py` | `prompt_not_whitespace_only` validator on `AnalyzeRequest` |
| `tests/test_main.py` | `test_history_limit_clamped`, `test_analyze_whitespace_only_prompt_rejected`, `test_analyze_invalid_api_key_returns_503` |

### Tests run
```bash
uv run pytest tests/ -v
# 50 passed (47 existing + 3 new)
```

### Known risks
- **History limit 100** – May need tuning for power users; easy to change via `HISTORY_MAX_LIMIT`.
- **503 vs 401** – Invalid API key returns 503 (service unavailable) rather than 401 (unauthorized). Chosen for consistency with the existing "API key not configured" case.
