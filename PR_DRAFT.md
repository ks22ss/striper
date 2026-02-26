# PR Draft: feat: use prompt from history

## Title
```
feat: use prompt from history
```

## Description

### Problem
When viewing prompt history, users could copy the improved prompt but had no quick way to load the **original** prompt back into the form for re-analysis or editing. They had to manually copy-paste or remember what they had submitted.

### Solution
Add a **Use** button next to the existing Copy button on each history item. Clicking it loads the original prompt into the prompt textarea, switches back to the analyze form, and lets the user re-run analysis or tweak the prompt.

### User value
- One-click load of a previous prompt for re-analysis
- Faster iteration when refining prompts
- No manual copy-paste from history

### Changes
| File | Changes |
|------|---------|
| `static/index.html` | "Use" and "Copy" buttons per history item, delegated click handler (Use: load prompt + switch view; Copy: clipboard), `lastHistoryItems` for lookup |
| `README.md` | Document Use and Copy in UI section |
| `tests/test_main.py` | `test_history_items_include_full_prompt_for_use_feature` – asserts history returns full prompt (no truncation) |

### Screenshots
History view now shows "Use" and "Copy" buttons on each card. Clicking "Use" loads the prompt into the form and returns to the analyze view.

### Tests run
```bash
uv run pytest tests/ -v
# 48 passed (47 existing + 1 new)
```

### Known risks
- **None**: Pure frontend change; no API or DB changes. History endpoint already returns full prompt.
- **Input field**: Optional input is not persisted in history; when using a prompt from history, the input field stays empty. Acceptable for v1.
