---
name: auto-heal
description: Step-by-step workflow for diagnosing and fixing broken Playwright locators. Use when a test fails with TimeoutError, StrictModeViolation, or element-not-found. Covers snapshot-based diagnosis, locator mapping, Page Object update, and regression verification. Always load alongside chrome-devtools skill for inspection commands.
allowed-tools: Bash(playwright-cli:*)
---

# Auto-Heal Skill — Diagnosing and Fixing Broken Playwright Tests

Use this skill when a test fails with a locator error (`TimeoutError`, `StrictModeViolation`,
or element-not-found).  Following this workflow lets Copilot diagnose the root cause and
propose a corrected Page Object without guessing.

---

## When Auto-Heal Applies

- `TimeoutError: locator('…') exceeded 30000 ms` — element not found.
- `StrictModeViolation` — locator matches more than one element.
- `Error: Element is not visible / not enabled` — element exists but is hidden or disabled.
- Test was passing before a UI deployment — locator likely changed.

---

## Step 1: Identify the Failing Locator

Read the test error to find:
1. The test name and the assertion that failed.
2. The Page Object file and the locator attribute involved.

Example error:
```
FAILED tests/test_growth_creators.py::test_home_page_ctas
  TimeoutError: locator.to_be_visible exceeded 30000 ms
  Call log:  - expect.toBeVisible with timeout 30000ms
  Locator: page.get_by_role("link", name="Schedule Discovery Call")
```
→ Broken locator is `page.get_by_role("link", name="Schedule Discovery Call")` in `pages/home_page.py`.

---

## Step 2: Capture a Live Snapshot

```bash
playwright-cli open https://www.growthcreators.ai
playwright-cli snapshot --filename=heal-snapshot.yaml
```

The snapshot file shows the current accessibility tree.

---

## Step 3: Search the Snapshot for the Element

Look for the element that should match the broken locator.

```bash
# e.g. search for anything containing "Discovery" or "Call"
playwright-cli eval "Array.from(document.querySelectorAll('a,button')).map(el => el.innerText.trim()).filter(t => t.length > 0)"
```

Or read the snapshot YAML and grep for the word:
- If the role/name changed, note the **new** role + name.
- If the element moved inside a different container, note the parent role.

---

## Step 4: Confirm the Correct Locator

Once you have identified the element in the snapshot:

```bash
# Interact with the ref to confirm it is the right element
playwright-cli click e22      # replace with actual ref from snapshot
playwright-cli snapshot       # confirm expected navigation / state change
playwright-cli go-back
```

---

## Step 5: Propose the Healed Locator

Map the snapshot values to a Playwright Python locator using the table below.

| Old (broken) locator                              | Snapshot finding                        | Healed locator                                           |
|---------------------------------------------------|-----------------------------------------|----------------------------------------------------------|
| `get_by_role("link", name="Schedule Discovery …")` | role=link, name="Book a Discovery Call" | `get_by_role("link", name="Book a Discovery Call")`     |
| `get_by_role("button", name="Contact Us")`         | now rendered as `link`                  | `get_by_role("link", name="Contact Us")`                |
| `get_by_text("Sign Up")`                           | text changed to "Get Started"           | `get_by_text("Get Started")`                            |
| `get_by_test_id("hero-cta")`                       | testid removed, now role=button          | `get_by_role("button", name="…")`                       |

---

## Step 6: Update the Page Object

Edit the relevant file in `pages/` with the healed locator:

```python
# pages/home_page.py  — BEFORE
self.schedule_discovery_call: Locator = page.get_by_role(
    "link", name="Schedule Discovery Call", exact=True
)

# pages/home_page.py  — AFTER (example)
self.schedule_discovery_call: Locator = page.get_by_role(
    "link", name="Book a Discovery Call", exact=True
)
```

---

## Step 7: Verify the Fix

```bash
# Re-run only the previously failing test
pytest tests/test_growth_creators.py -v -k "test_home_page_ctas"
```

Expected output: `PASSED`.

---

## Step 8: Regression Check

```bash
# Run the full suite to confirm no other tests regressed
pytest tests/ -v
```

---

## Common Failure Patterns & Quick Fixes

| Symptom                             | Likely Cause                         | Fix Strategy                                                      |
|-------------------------------------|--------------------------------------|-------------------------------------------------------------------|
| `TimeoutError` on link locator      | Text or href changed after deploy    | Snapshot → find new name → update `get_by_role`                   |
| `StrictModeViolation`               | Same role+name now on multiple nodes | Narrow with `.filter(has_text=…)` or scope to a parent locator    |
| `Element not visible`               | Element hidden by CSS / JS           | Check console for JS errors; check `display` / `visibility` styles |
| Nav buttons missing                 | DOM restructured                     | Snapshot the `<nav>` subtree; check if `<button>` → `<a>` change  |
| Footer CTA not found                | CTA section moved inside page layout | Re-scope: `page.get_by_role("main").get_by_role("link", …)`       |

---

## Maintaining Heal Logs

After fixing a locator, record a short note in `pages/<page>.py` in a comment above the
locator so future runs have context:

```python
# Healed 2026-04-01: renamed from "Schedule Discovery Call" → "Book a Discovery Call"
self.schedule_discovery_call: Locator = page.get_by_role(
    "link", name="Book a Discovery Call", exact=True
)
```
