# maint: fix analysis result lost on history save failure + small cleanup

## Problem

When `add_prompt_history` fails (e.g. DB disk full, lock, transient error), the analyze endpoint returns 500 and the user receives no analysis result—even though `run_stripe_analysis` succeeded. The user loses their work and gets a generic "Analysis failed" error.

**Reproduction:** Mock `add_prompt_history` to raise; call `POST /analyze` with valid prompt. Before fix: 500. After fix: 200 with full result.

## Solution

- Wrap `add_prompt_history` in a try/except. On failure, log a warning and still return the analysis result.
- User gets their score, improved prompt, and component breakdown; history save failure is non-fatal.

## Refactor

- Use `status.HTTP_503_SERVICE_UNAVAILABLE` instead of literal `503` for API key errors (semantic constant, consistent with FastAPI style).

## Tests

- **New:** `test_analyze_returns_result_when_history_save_fails` – mocks `add_prompt_history` to raise; asserts 200 and correct response body.
- Full suite: **49 passed**.

## Files changed

| File | Changes |
|------|---------|
| `app/main.py` | Try/except around `add_prompt_history`, log on failure; use `HTTP_503_SERVICE_UNAVAILABLE` |
| `tests/test_main.py` | New regression test |

## Known risks

- History save failures are logged but not surfaced to the client. Acceptable for v1; user still gets the primary value (analysis result). Future: optional `history_saved: false` in response if desired.
