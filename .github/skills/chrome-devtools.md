---
name: chrome-devtools
description: Browser inspection without MCP — DOM snapshots, console/network debugging, JS evaluation, and locator writing. Use when diagnosing layout issues, inspecting live pages, analysing failed network requests, or writing new Page Object locators from a live accessibility tree.
allowed-tools: Bash(playwright-cli:*)
---

# Chrome DevTools Skill — Browser Inspection Without MCP

Use this skill when you need to inspect a live page, debug a failing locator, analyse
network traffic, or read console errors.  All techniques here work via the
`playwright-cli` tool so **no MCP server is required** and no extra tokens are consumed
by external tool calls.

---

## 1. Accessibility Tree (DOM Snapshot)

The snapshot is the primary way to see what elements exist and how Playwright sees them.

```bash
playwright-cli open https://example.com
playwright-cli snapshot
```

The output is a YAML accessibility tree.  Each node shows:
- `ref`  — the ref id you pass to click/fill/etc. (e.g. `e14`)
- `role` — ARIA role (`button`, `link`, `textbox`, …)
- `name` — accessible name (what you use in `get_by_role(name=…)`)

**Targeted snapshot of a single element:**
```bash
playwright-cli snapshot e14
```

**Save snapshot to file for comparison:**
```bash
playwright-cli snapshot --filename=before.yaml
# … perform actions …
playwright-cli snapshot --filename=after.yaml
```

---

## 2. Finding a Broken Locator

When a test throws `TimeoutError: locator … not found`:

```bash
# 1. Navigate to the failing page
playwright-cli open https://your-app.com/failing-page

# 2. Capture the full snapshot
playwright-cli snapshot

# 3. Search the YAML output for the expected text / role
#    e.g. if "Schedule Discovery Call" link is missing, look for any link with "Discovery"
```

Read the snapshot and locate the closest matching element.  Note its `role` and `name`,
then update the Page Object locator accordingly.

---

## 3. Console Log Inspection

```bash
# Show all console messages
playwright-cli console

# Filter to warnings and errors only
playwright-cli console warning
playwright-cli console error
```

Use this to catch silent JS errors that cause elements to not render.

---

## 4. Network Request Inspection

```bash
# List all network requests made since the page loaded
playwright-cli network
```

Output includes: method, URL, status code, response time.

**Identify failed API calls:**
Look for entries with status `4xx` or `5xx` — these commonly cause missing UI elements.

```bash
# Mock a failing endpoint to isolate the UI
playwright-cli route "**/api/broken-endpoint" --status=200 --body='{"data":[]}'
playwright-cli reload
playwright-cli snapshot
```

---

## 5. JavaScript Evaluation

Run arbitrary JS in the page context to interrogate the DOM directly:

```bash
# Get the page title
playwright-cli eval "document.title"

# Read an element's text content by ref
playwright-cli eval "el => el.textContent" e14

# Check if an element exists by CSS selector (for debugging only — do NOT use CSS in tests)
playwright-cli eval "document.querySelector('[data-testid=\"submit-btn\"]')?.textContent"

# Get computed styles
playwright-cli eval "el => getComputedStyle(el).display" e14

# Check aria attributes on an element
playwright-cli eval "el => JSON.stringify({role: el.getAttribute('role'), ariaLabel: el.getAttribute('aria-label')})" e14
```

---

## 6. Screenshots for Visual Debugging

```bash
# Full-page screenshot
playwright-cli screenshot --filename=debug-page.png

# Screenshot a single element
playwright-cli screenshot e14 --filename=debug-element.png
```

---

## 7. Tracing (Step-by-Step Playback)

Record a Playwright trace for post-mortem analysis:

```bash
playwright-cli open https://example.com
playwright-cli tracing-start
playwright-cli click e3
playwright-cli fill e5 "test value"
playwright-cli tracing-stop   # saves trace.zip
```

Open the trace in the Playwright Trace Viewer:
```bash
playwright show-trace trace.zip
```

---

## 8. Storage & Auth State Inspection

```bash
# List all cookies
playwright-cli cookie-list

# Read a specific cookie
playwright-cli cookie-get session_id

# Dump all localStorage
playwright-cli localstorage-list

# Read a single key
playwright-cli localstorage-get token
```

---

## 9. Workflow: Localising a Layout Shift

```bash
playwright-cli open https://your-app.com
playwright-cli resize 1920 1080
playwright-cli screenshot --filename=desktop.png

playwright-cli resize 375 812
playwright-cli screenshot --filename=mobile.png
```

Compare screenshots to pinpoint the breakpoint where the layout shifts.

---

## 10. Generating Playwright Python Locators from a Snapshot

After taking a snapshot, convert the `role` and `name` values directly:

| Snapshot field        | Playwright Python locator                                     |
|-----------------------|--------------------------------------------------------------|
| `role: button`        | `page.get_by_role("button", name="…")`                       |
| `role: link`          | `page.get_by_role("link", name="…")`                         |
| `role: textbox`       | `page.get_by_role("textbox", name="…")`                      |
| `role: heading`       | `page.get_by_role("heading", name="…", level=N)`             |
| `data-testid="…"`     | `page.get_by_test_id("…")`                                   |
| visible text only     | `page.get_by_text("…", exact=True)`                          |

Always prefer the first matched role/name pair in the snapshot for maximum resilience.
