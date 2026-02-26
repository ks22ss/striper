# feat: use prompt from history

## Problem

Users viewing their prompt history had no way to re-use a past prompt. They had to manually copy-paste into the form, which is tedious for long prompts.

## Solution

- **Use button** on each history item: loads the full prompt into the prompt textarea and returns to the analyze form.
- **History toggle fix** (from `maint/history-view-toggle-fix`): the History button now correctly hides the form and shows history (instead of hiding the whole analyze section).

## Changes

| File | Changes |
|------|---------|
| `static/index.html` | Use button on history items, event delegation for click, `historyItems` storage, History toggle uses `formAndResultsEl` |
| `tests/test_main.py` | `test_ui_has_use_prompt_from_history` regression test |

## How to verify

1. Log in, run an analysis, then click **History**.
2. Confirm history items are visible (toggle fix).
3. Click **Use** on an item.
4. Confirm the prompt loads into the form and the view switches back to the analyze form.

## Tests

```
17 passed
```

## Known risks

- None. Uses existing `/history` API; no backend changes.
