# maint: fix history view never showing + limit validation + small cleanup

## Problem

1. **Bug:** Clicking "History" hid the parent `analyze-section`, which contained both the form/results and the history list. The history section was a child of analyze-section, so it was hidden too—history never appeared.
2. **UX:** After analysis, status showed "Done" with no confirmation that results were saved to history.
3. **API:** `/history?limit=0` or `limit=101` was accepted; no validation.

## Solution

1. **Fix:** Wrap form + results in `form-and-results` div. Toggle `form-and-results` vs `history-section` (siblings). History button hides form-and-results and shows history-section; Back button reverses. Both stay inside analyze-section.
2. **UX:** Change status to "Done. Saved to history." after successful analysis.
3. **API:** Add `Query(ge=1, le=100)` for `/history` limit.
4. **Refactor:** Extract `fake_auth()` context manager in tests; replace repeated override + try/finally with `with fake_auth():`.

## Changes

| File | Change |
|------|--------|
| `static/index.html` | Add `form-and-results` wrapper; fix History/Back toggle; "Done. Saved to history." |
| `app/main.py` | `limit: int = Query(50, ge=1, le=100)` |
| `tests/test_main.py` | `fake_auth()` context manager; `test_ui_has_history_toggle_structure`, `test_ui_includes_saved_to_history_feedback`, `test_history_limit_validation`; refactor 7 tests to use `fake_auth()` |

## Tests run

```bash
uv run pytest tests/ -v
# 50 passed
```

```bash
ruff check app tests
# All checks passed
```

## Reproduction (bug)

Before fix: Log in → History → History list never appears (parent section hidden).

## Residual risks

- None. Toggle logic is localized; limit validation is standard FastAPI.
