# UI-Automation

![Playwright Tests](https://github.com/sheik-sadiq/UI-Automation/actions/workflows/playwright.yml/badge.svg)

End-to-end UI test suite for [https://www.growthcreators.ai](https://www.growthcreators.ai) built with **Python**, **Playwright**, and **pytest**. Tests are structured using the **Page Object Model (POM)** pattern for maintainability and scalability.

This repository is also a showcase of **AI-assisted test maintenance**: a set of Copilot skill files under `.github/skills/` enable GitHub Copilot to automatically inspect live pages, diagnose broken locators, and apply healed Page Object fixes — all without relying on external MCP servers.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Page Object Model](#page-object-model)
- [AI Skills & Auto-Heal](#ai-skills--auto-heal)
- [Contributing](#contributing)

---

## Tech Stack

| Tool | Purpose |
|---|---|
| [Python 3.x](https://www.python.org/) | Test language |
| [Playwright](https://playwright.dev/python/) | Browser automation |
| [pytest](https://docs.pytest.org/) | Test runner & assertions |
| [pytest-playwright](https://pypi.org/project/pytest-playwright/) | Playwright–pytest integration |

---

## Project Structure

```
UI-Automation/
├── .github/
│   ├── copilot-instructions.md   # GitHub Copilot workspace instructions
│   └── skills/                   # Copilot skill files (loaded on demand)
│       ├── playwright-python.md  # Playwright API, routing, network mocking
│       ├── chrome-devtools.md    # DOM/console/network inspection via playwright-cli
│       ├── auto-heal.md          # Step-by-step broken-locator diagnosis & fix
│       └── playwright-references/
│           ├── request-mocking.md
│           ├── running-code.md
│           ├── session-management.md
│           ├── storage-state.md
│           ├── test-generation.md
│           ├── tracing.md
│           └── video-recording.md
├── pages/                        # Page Object Model layer
│   ├── __init__.py
│   ├── base_page.py              # Shared locators & nav-click helpers
│   ├── home_page.py              # Home page (/) locators & actions
│   ├── about_page.py             # About Us page (/about-us) locators & actions
│   ├── solutions_page.py         # Solutions page (/solutions) locators & actions
│   └── case_studies_page.py      # Case Studies page (/case-studies) locators & actions
├── scripts/                      # Standalone utilities (not part of the test suite)
│   └── inspect_dom.py            # Live DOM inspector — run manually when writing locators
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # pytest fixtures (isolated page per test)
│   └── test_growth_creators.py   # All test cases
├── .gitignore                    # Excludes venv, cache, and report artefacts
├── pytest.ini                    # pytest configuration (base URL)
├── requirements.txt              # Python dependencies
└── README.md
```

---

## Prerequisites

- **Python 3.8+** installed and available on your `PATH`
- **pip** package manager

---

## Installation

**1. Clone the repository**

```bash
git clone <repository-url>
cd UI-Automation
```

**2. Create and activate a virtual environment** *(recommended)*

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

**3. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**4. Install Playwright browsers**

```bash
playwright install
```

---

## Configuration

All configuration lives in `pytest.ini`:

```ini
[pytest]
base_url = https://www.growthcreators.ai
```

To run tests against a different environment, override `base_url` at the command line:

```bash
pytest --base-url https://staging.growthcreators.ai
```

---

## Running Tests

**Run the full test suite**

```bash
pytest tests/test_growth_creators.py -v
```

**Run a single test by name**

```bash
pytest tests/test_growth_creators.py -v -k "test_website_is_operational"
```

**Run in headed mode** (browser visible)

```bash
pytest tests/test_growth_creators.py -v --headed
```

**Run in a specific browser** (chromium | firefox | webkit)

```bash
pytest tests/test_growth_creators.py -v --browser firefox
```

**Slow down execution for debugging**

```bash
pytest tests/test_growth_creators.py -v --headed --slowmo 500
```

**Generate an HTML report**

```bash
pytest tests/test_growth_creators.py -v --html=report.html --self-contained-html
```

> `pytest-html` must be installed: `pip install pytest-html`

---

## Test Coverage

| # | Test Name | Type | Description |
|---|---|---|---|
| 1 | `test_website_is_operational` | Visibility | Navigates to the home page and verifies the hero heading is visible |
| 2 | `test_header_navigation_links` | Visibility | Asserts Home, Solutions, Case Studies, and About Us nav links are present |
| 3 | `test_global_action_buttons` | Visibility | Verifies Community and Contact Us buttons appear in the header |
| 4 | `test_home_page_ctas` | Visibility | Checks Schedule Discovery Call and footer Contact Us CTAs on the home page |
| 5 | `test_about_us_contact_us_button` | Visibility | Navigates to `/about-us` and verifies the footer Contact Us CTA is visible |
| 6 | `test_solutions_schedule_consultation_button` | Visibility | Navigates to `/solutions` and verifies the Schedule Your Consultation CTA |
| 7 | `test_case_studies_start_success_story_button` | Visibility | Navigates to `/case-studies` and verifies the Start Your Success Story CTA |
| 8 | `test_nav_solutions_navigates_to_solutions_page` | Interaction | Clicks the Solutions nav item and asserts the URL changes to `/solutions` |
| 9 | `test_nav_case_studies_navigates_to_case_studies_page` | Interaction | Clicks the Case Studies nav item and asserts the URL changes to `/case-studies` |
| 10 | `test_nav_about_us_navigates_to_about_us_page` | Interaction | Clicks the About Us nav item and asserts the URL changes to `/about-us` |
| 11 | `test_schedule_discovery_call_navigates` | Interaction | Clicks the Schedule Discovery Call CTA and asserts the browser navigates away |

---

## Page Object Model

The suite follows the **Page Object Model** pattern to separate test logic from UI interaction details.

```
BasePage
├── Shared locators: header nav, Community button, Contact Us button, footer CTA
├── click_nav_solutions()     → clicks and waits for /solutions
├── click_nav_case_studies()  → clicks and waits for /case-studies
├── click_nav_about_us()      → clicks and waits for /about-us
│
├── HomePage  (extends BasePage)
│   ├── hero_heading
│   ├── schedule_discovery_call
│   ├── click_schedule_discovery_call()
│   └── open() → navigates to /
│
├── AboutPage  (extends BasePage)
│   └── open() → navigates to /about-us
│
├── SolutionsPage  (extends BasePage)
│   ├── schedule_consultation
│   └── open() → navigates to /solutions
│
└── CaseStudiesPage  (extends BasePage)
    ├── start_success_story
    └── open() → navigates to /case-studies
```

Adding a new page:
1. Create `pages/new_page.py` extending `BasePage`.
2. Define locators in `__init__` and an `open()` method.
3. Import and use it in your test file.

---

## AI Skills & Auto-Heal

This repository ships a set of **Copilot skill files** under `.github/skills/` that teach GitHub Copilot how to diagnose and fix broken tests without relying on external MCP servers or manual investigation.

### How it works

All browser inspection is done via the `playwright-cli` tool (zero extra tokens, no MCP):

| Need | Command | Skill file |
|---|---|---|
| Inspect the live DOM | `playwright-cli snapshot` | `chrome-devtools.md` |
| Read console errors | `playwright-cli console` | `chrome-devtools.md` |
| Inspect network traffic | `playwright-cli network` | `chrome-devtools.md` |
| Mock a broken API | `playwright-cli route "…"` | `playwright-python.md` |
| Fix a broken locator | full 8-step workflow | `auto-heal.md` |

### Auto-Heal workflow (when a test breaks)

```
1. Read the error → identify the failing locator and the page
2. Load .github/skills/auto-heal.md
3. Run: playwright-cli open <url>
4. Run: playwright-cli snapshot --filename=heal-snapshot.yaml
5. Find the changed element in the snapshot (new role / name / testid)
6. Update the Page Object locator in pages/<page>.py
7. pytest tests/ -v -k "<failing_test>"   ← confirm fix
8. pytest tests/ -v                        ← full regression
```

### Skill files reference

| File | Purpose |
|---|---|
| `.github/skills/playwright-python.md` | Playwright API, routing, context management, test code generation |
| `.github/skills/chrome-devtools.md` | DOM inspection, console/network debugging, JS evaluation, screenshots |
| `.github/skills/auto-heal.md` | Broken-locator triage, locator mapping table, heal-log convention |
| `.github/skills/playwright-references/*.md` | Deep-dive references: tracing, video, storage, request mocking, sessions |

---

## Contributing

1. Fork the repository and create a feature branch (`git checkout -b feat/your-feature`).
2. Follow the existing POM structure — add new pages under `pages/` and new tests under `tests/`.
3. Ensure all tests pass before opening a pull request: `pytest tests/ -v`.
4. Keep locators in the page objects; keep assertions in the test files.
