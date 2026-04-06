# UI Automation Framework — Copilot Instructions

You are an expert SDET assisting with a robust, scalable UI Test Automation framework.
Your goal is to write clean, maintainable, and flake-free Python code.

---

## Tech Stack

- **Framework:** Playwright for Python
- **Test Runner & Assertions:** Pytest and Playwright's `expect` module (`from playwright.sync_api import expect`)
- **Language:** Python 3.11+ (Strict typing preferred)

---

## Architectural Patterns: Page Object Model (POM)

- Strictly separate UI interactions from test logic.
- Page objects must be defined as Python classes. The `__init__` method must accept a Playwright `Page` object.
- Define locators as class attributes or properties within `__init__` using `self.page.locator()`.
- Test files (`test_*.py`) should only instantiate Page Objects, perform actions, and contain assertions.

---

## Locator Strategy & Assertions

- **Resilient Locators:** ALWAYS prioritise `get_by_test_id`, `get_by_role`, or `get_by_text`.
  Avoid brittle CSS or XPath selectors tied to the DOM structure.
- **Auto-Retrying Assertions:** NEVER use standard Python `assert` for UI states.
  ALWAYS use Playwright's `expect` (e.g. `expect(page.get_by_role("button")).to_be_visible()`).
- **No Hard Sleeps:** NEVER use `time.sleep()`.
  Rely on Playwright's actionability checks and web-first assertions.

---

## Coding Standards & Pytest Best Practices

- **Fixtures:** Use Pytest fixtures (in `conftest.py`) for setup, teardown, test data, and auth state.
  Avoid repetitive `setup_method` / `teardown_method` blocks.
- **Typing:** Use Python type hints for all function arguments and return types.
- **Clean Code:** Enforce DRY principles. Abstract complex UI interactions into reusable helper
  methods within the Page Objects.
- **Future-Proofing:** Write modular code that can be triggered or validated by external
  orchestration tools or automated workflows.

---

## Specialised Skills & Context

When working on specific domains in this repository, load the relevant skill file **first**
before generating any response or code.

| Domain | Skill File | When to Load |
|---|---|---|
| Playwright API, routing, network mocking | `.github/skills/playwright-python.md` | Any new Playwright code, advanced routing, context management |
| DOM inspection, console/network debugging | `.github/skills/chrome-devtools.md` | Diagnosing layout issues, inspecting live pages, writing new locators, **always load with auto-heal** |
| Auto-healing broken locators | `.github/skills/auto-heal.md` | Any `TimeoutError`, `StrictModeViolation`, or element-not-found failure — **load with chrome-devtools** |

### Loading a Skill

Read the file content before proceeding:

```
Read the file `.github/skills/chrome-devtools.md` and follow its instructions.
```

---

## Browser Inspection — No MCP Required

Do **not** rely on the Chrome DevTools MCP server for inspection tasks. Instead use the
`playwright-cli` tool as described in `.github/skills/chrome-devtools.md`:

1. **Inspect DOM:** `playwright-cli snapshot` → read the accessibility tree.
2. **Check Console:** `playwright-cli console` → find silent JS errors.
3. **Check Network:** `playwright-cli network` → spot failed API calls.
4. **Evaluate JS:** `playwright-cli eval "…"` → interrogate element attributes.
5. **Write Locators:** derive `get_by_role` / `get_by_test_id` from snapshot output — never guess.

---

## Auto-Heal Workflow

When a test fails due to a broken locator:

1. Load `.github/skills/auto-heal.md`.
2. Follow the step-by-step diagnosis → snapshot → locator mapping → Page Object update workflow.
3. Re-run the failing test to confirm the fix, then run the full suite for regression.
