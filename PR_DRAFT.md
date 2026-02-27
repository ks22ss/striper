# feat: add Use as prompt button for improved prompt

## Problem

After analyzing a prompt, users often want to re-analyze the improved version or refine it further. Today they must manually copy the improved prompt and paste it into the prompt field. This is an extra step that interrupts the workflow.

## Solution

Add a **Use as prompt** button next to the improved prompt. When clicked, it loads the improved prompt into the prompt textarea, focuses it, and scrolls it into view. Users can then re-analyze or edit and analyze in one click.

## Changes

| File | Change |
|------|--------|
| `static/index.html` | "Use as prompt" button next to Copy; click handler populates prompt field, focuses, and scrolls into view |
| `README.md` | UI section updated to mention Use as prompt |
| `tests/test_main.py` | New test `test_ui_includes_use_improved_as_prompt_button` |

## Tests

- 51 tests pass (including `test_ui_includes_use_improved_as_prompt_button`)
- No backend changes; frontend-only

## Known risks

- None. Button is disabled when improved prompt is empty or "(unchanged)".
