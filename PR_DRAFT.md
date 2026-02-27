# feat: add "Use as prompt" button for improved prompt

## Problem

After analysis, users must manually select and copy the improved prompt into the prompt field to re-analyze or iterate. This is tedious when refining prompts over multiple passes.

## Solution

Add a **Use as prompt** button next to the improved prompt. Clicking it:
- Loads the improved prompt into the prompt textarea
- Focuses the prompt input
- Scrolls the prompt field into view for quick editing or re-analysis

## Changes

| File | Change |
|------|--------|
| `static/index.html` | "Use as prompt" button in improved prompt card; click handler populates prompt textarea, focuses, and scrolls into view |
| `README.md` | UI section updated to mention the button |
| `tests/test_main.py` | New test `test_ui_includes_use_improved_as_prompt_button` |

## Tests

All 51 tests pass, including the new UI test.

```bash
python -m pytest tests/ -v
```

## Known risks

- None. Frontend-only change; no API or data model changes.
- Button does nothing when improved prompt is empty or "(unchanged)" (intended).
