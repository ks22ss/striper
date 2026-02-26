# feat: Copy improved prompt button

## Problem

After analysis, users receive an improved prompt but must manually select and copy it. There is no one-click way to copy the improved prompt to the clipboard.

## Solution

Add a **Copy** button next to the "Improved prompt" heading. On click:
- Copies the improved prompt text to the clipboard via `navigator.clipboard.writeText()`
- Shows brief "Copied!" feedback (green, 1.5s) then reverts to "Copy"
- On clipboard API failure, shows "Copy failed" briefly

## Changes

| File | Change |
|------|--------|
| `static/index.html` | Copy button in improved-prompt card header; click handler with clipboard + feedback |
| `tests/test_main.py` | `test_ui_has_copy_improved_prompt_button` regression test |

## Tests run

```bash
uv run pytest tests/ -v
# 48 passed
```

## Screenshots

- **Before:** Improved prompt displayed with no copy action
- **After:** "Copy" button appears next to "Improved prompt" heading; click copies text and shows "Copied!"

## Known risks

- **Clipboard API:** Requires secure context (HTTPS or localhost). In HTTP, `navigator.clipboard` may be undefined; the handler catches errors and shows "Copy failed".
- **Browser support:** `navigator.clipboard.writeText()` is supported in all modern browsers (Chrome 66+, Firefox 63+, Safari 13.1+).

## Residual risks

- None. Pure frontend change; no API or data model changes.
