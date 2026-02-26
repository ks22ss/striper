# feat: Use prompt from history

## Problem

Users viewing their prompt history had no way to reuse a past prompt. To re-analyze or edit a previous prompt, they had to manually copy it from the truncated preview and paste into the form.

## Solution

Add a **Use** button to each history item. Clicking it loads the full prompt into the form, switches back to the analyze section, and focuses the prompt textarea. Users can then re-analyze (e.g. with different input) or edit before submitting.

## Changes

| File | Changes |
|------|---------|
| `static/index.html` | Add "Use" button per history item; event delegation to load prompt and navigate back |
| `tests/test_main.py` | Add `test_root_html_includes_use_prompt_from_history` |
| `README.md` | Document history Use flow in UI section |

## Tests

48 tests pass (`uv run pytest tests/ -v`).

## Screenshots / Flow

1. User clicks **History**
2. History list shows past analyses with a **Use** button on each card
3. User clicks **Use** → prompt loads into form, view switches to analyze section, prompt textarea is focused
4. User can edit or click **Analyze** to re-run

## Known risks

- **Long prompts**: History items store full prompts; no change to backend. Frontend uses index-based lookup, so no large data in DOM attributes.
- **Empty history**: Use button only appears when history has items; no impact when empty.
