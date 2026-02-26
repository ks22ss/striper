# feat: light/dark theme toggle

## Problem

The UI is fixed to dark theme. Users in bright environments or with light-mode preference have no way to switch.

## Solution

Add a theme toggle button in the header. Clicking switches between light and dark mode. The choice is persisted in `localStorage` and restored on reload. Uses DaisyUI's built-in `data-theme` attribute; no new dependencies.

## Changes

| File | Change |
|------|--------|
| `static/index.html` | Theme toggle button, `getStoredTheme`/`setTheme`/`initTheme`, localStorage persistence |
| `tests/test_main.py` | `test_root_ui_includes_theme_toggle` – regression test |
| `README.md` | UI section mentions theme toggle |

- Default theme: dark (matches previous behavior)
- Button shows ☀ when dark (click to go light), ☽ when light (click to go dark)
- Toggle visible in header for all users (logged in or not)

## Tests

- Full suite: `uv run pytest tests/ -v` → **48 passed**
- Ruff: `uv run ruff check app/ tests/` → **All checks passed**
- Manual: Click toggle → theme switches; reload → preference persists

## Known risks

- None. Pure frontend; no API changes. DaisyUI themes are well-supported.

## Screenshots

N/A – standard light/dark toggle.
