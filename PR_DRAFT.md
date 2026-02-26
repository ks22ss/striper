# feat: show "Saved to history" feedback after analysis

## Problem

After a successful prompt analysis, the UI shows "Done" but gives no confirmation that the result was persisted to the user's history. Users may wonder whether their analysis was saved.

## Solution

Update the status message on successful analysis from "Done" to "Done. Saved to history." so users get immediate reassurance that the result is stored.

## Changes

| File | Change |
|------|--------|
| `static/index.html` | Set `statusEl.textContent = 'Done. Saved to history.'` on successful analyze response |
| `tests/test_main.py` | Add `test_ui_includes_saved_to_history_feedback` to assert the string appears in served UI |

## Tests run

```bash
uv run pytest tests/ -v
# 48 passed
```

```bash
ruff check app tests
# All checks passed
```

## Known risks

- **None.** Pure frontend change; no API or backend modifications. The message is shown only after a successful `/analyze` response, which already implies the backend saved to history.

## Screenshots

Before: status shows "Done"  
After: status shows "Done. Saved to history."
