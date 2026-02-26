# feat: Use improved prompt as new prompt

## Problem

After analysis, users see the improved prompt but must manually select and copy it into the prompt textarea to re-analyze or iterate. This adds friction to the refine-and-retry workflow.

## Solution

Add a **Use as new prompt** button next to the improved prompt. Clicking it populates the prompt textarea with the improved text, focuses the field, and triggers any input listeners (e.g. character count). Users can then edit or click Analyze to re-run.

## Changes

| File | Change |
|------|--------|
| `static/index.html` | Button in improved-prompt card; click handler sets `promptInput.value`, focuses, dispatches `input` event |
| `tests/test_main.py` | `test_root_html_includes_use_improved_button` – asserts button id and label in served HTML |
| `README.md` | UI section mentions "Use as new prompt" |

## Tests

```bash
uv run pytest tests/ -v
# 49 passed
```

## Screenshots

N/A – simple button addition.

## Known risks

- **Empty prompt**: If `improved_prompt` is empty or "(unchanged)", the button still loads that string into the textarea. User can clear or edit.
- **No clipboard**: This feature loads into the form only; it does not copy to clipboard. Use case is in-app iteration.
