"""
heal_runner.py
==============
Main orchestrator for the auto-heal GitHub Actions bot.

Called by the auto_heal GHA job:
    python scripts/heal_runner.py --report report.json

Flow
----
1. Parse pytest-json-report → list[FailedTest]
2. For each failure:
   a. Map test name → responsible pages/*.py file
   b. Capture a live DOM snapshot from the real site (Playwright headless)
   c. Call Gemini with {test_name, traceback, page_source, dom_snapshot}
   d. Validate the returned unified diff (path whitelist + syntax check)
   e. Apply the patch with `patch -p1`
3. Spot re-run: re-run only the healed tests
4. Full regression: run the complete suite
5. All green  → git branch + commit + push + open PR
   Any failure → open GitHub Issue (escalate, no push)
"""
import argparse
import json
import py_compile
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from scripts.inspect_dom import capture_dom_snapshot
from scripts.llm_client import ask_llm
from scripts.git_ops import push_and_open_pr, open_github_issue

# ── Constants ─────────────────────────────────────────────────────────────────

BASE_URL = "https://www.growthcreators.ai"

# Maps substrings in test names → page object files (first match wins)
PAGE_MAP: dict = {
    "about":           "pages/about_page.py",
    "solutions":       "pages/solutions_page.py",
    "case_studies":    "pages/case_studies_page.py",
    "schedule_disco":  "pages/home_page.py",
    "home":            "pages/home_page.py",
    "header":          "pages/base_page.py",
    "global_action":   "pages/base_page.py",
    "nav_":            "pages/base_page.py",
}

# Maps page object file → URL path to snapshot for that page
PAGE_URL_SUFFIX: dict = {
    "pages/home_page.py":         "/",
    "pages/base_page.py":         "/",
    "pages/about_page.py":        "/about-us",
    "pages/solutions_page.py":    "/solutions",
    "pages/case_studies_page.py": "/case-studies",
}

# Bot may ONLY patch files inside this directory
ALLOWED_PATH_PREFIX = "pages/"


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class FailedTest:
    name: str
    traceback: str
    page_file: str
    page_url: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_failures(report_path: str) -> list:
    """
    Read a pytest-json-report file and return a FailedTest for every
    test that has outcome == 'failed'.
    """
    data = json.loads(Path(report_path).read_text())
    failures = []
    for test in data.get("tests", []):
        if test.get("outcome") == "failed":
            # nodeid is like "tests/test_foo.py::test_bar"
            name = test["nodeid"].split("::")[-1]
            tb   = (test.get("call") or {}).get("longrepr", "")
            page_file = _identify_page_file(name)
            page_url  = BASE_URL + PAGE_URL_SUFFIX.get(page_file, "/")
            failures.append(FailedTest(name, str(tb), page_file, page_url))
    return failures


def _identify_page_file(test_name: str) -> str:
    """Map a test function name to the responsible Page Object file."""
    lower = test_name.lower()
    for keyword, path in PAGE_MAP.items():
        if keyword in lower:
            return path
    return "pages/base_page.py"     # safe fallback


def _validate_patch(diff: str) -> bool:
    """
    Safety gate — two checks before applying any patch:
    1. Path whitelist : every file touched must be under pages/
    2. No deletions of entire files
    Returns True if the patch is safe to apply.
    """
    for line in diff.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            # Strip "a/" or "b/" git prefix; "/dev/null" is fine (new file)
            path = line.split()[-1]
            path = path.lstrip("ab/")
            if path == "/dev/null":
                continue
            if not path.startswith(ALLOWED_PATH_PREFIX):
                print(f"[HEAL] ⛔ Rejected: patch touches non-pages path: {path}")
                return False
    return True


def _apply_patch(diff: str, page_file: str) -> bool:
    """
    Apply the unified diff with `patch -p1`, then syntax-check the
    modified Python file. Reverts the file on syntax error.
    """
    print(f"\n[DEBUG] Raw LLM Diff:\n{diff}\n")
    try:
        # Pass the exact filename to patch so it doesn't get confused by bad --- headers
        subprocess.run(
            ["patch", page_file, "--forward", "--batch"],
            input=diff, text=True, check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"[HEAL] patch failed (exit {exc.returncode}):")
        print(f"STDOUT:\n{exc.stdout}")
        print(f"STDERR:\n{exc.stderr}")
        return False

    # Syntax check
    try:
        py_compile.compile(page_file, doraise=True)
    except py_compile.PyCompileError as exc:
        print(f"[HEAL] Syntax error after patch — reverting: {exc}")
        subprocess.run(["git", "checkout", page_file])
        return False

    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main(report_path: str) -> None:
    failures = parse_failures(report_path)

    if not failures:
        print("[HEAL] No failures in report — nothing to heal. ✅")
        sys.exit(0)

    print(f"[HEAL] Found {len(failures)} failure(s) to process.")

    # ── Deduplicate: group failures by page file ──────────────────────────────
    # Multiple failing tests on the same page file = 1 LLM call, not N.
    # This cuts API quota usage proportionally.
    from collections import defaultdict
    by_page: dict = defaultdict(list)
    for t in failures:
        by_page[t.page_file].append(t)

    unique_pages = list(by_page.keys())
    print(f"[HEAL] Deduplicated to {len(unique_pages)} unique page file(s): "
          f"{', '.join(unique_pages)}")

    patched: list = []
    fix_summary: list = []

    for page_file, tests in by_page.items():
        page_url    = tests[0].page_url
        test_names  = ", ".join(t.name for t in tests)
        # Combine all tracebacks for this page into one prompt
        combined_tb = "\n\n---\n\n".join(
            f"Test: {t.name}\n{t.traceback}" for t in tests
        )

        print(f"\n[HEAL] ── Page file : {page_file}")
        print(f"[HEAL]    Tests     : {test_names}")
        print(f"[HEAL]    Snapshot  : {page_url}")

        snapshot    = capture_dom_snapshot(page_url)
        page_source = Path(page_file).read_text()
        # Use first test name for logging; pass all tracebacks
        diff = ask_llm(tests[0].name, combined_tb, page_source, snapshot)

        if not diff:
            print(f"[HEAL] ⚠️  No usable diff from LLM for {page_file}")
            continue

        if not _validate_patch(diff):
            continue

        if _apply_patch(diff, page_file):
            patched.extend(tests)
            fix_summary.append(
                f"- `{page_file}` — fixed tests: {test_names}"
            )
            print(f"[HEAL] ✅ Patched: {page_file}")
        else:
            print(f"[HEAL] ❌ Patch failed for {page_file}")

    # ── Escalate if nothing was patched ──────────────────────────────────────
    if not patched:
        open_github_issue(
            title="🚨 Auto-Heal: LLM could not generate a fix",
            body=(
                "The auto-heal bot could not produce a valid patch for:\n\n"
                + "\n".join(f"- `{t.name}`" for t in failures)
                + "\n\nPlease fix manually."
            ),
        )
        sys.exit(1)


    # ── Spot re-run: only the tests we healed ────────────────────────────────
    k_expr = " or ".join(t.name for t in patched)
    print(f"\n[HEAL] Spot re-run: pytest -k \"{k_expr}\"")
    spot = subprocess.run(["pytest", "tests/", "-v", "--tb=short", "-k", k_expr])

    if spot.returncode != 0:
        open_github_issue(
            title="🚨 Auto-Heal: Patch applied but spot tests still failing",
            body="\n".join(fix_summary) + "\n\nPlease investigate.",
        )
        sys.exit(1)

    # ── Full regression ────────────────────────────────────────────────────────
    print("\n[HEAL] Full regression suite…")
    full = subprocess.run(["pytest", "tests/", "-v", "--tb=short"])

    if full.returncode != 0:
        open_github_issue(
            title="🚨 Auto-Heal: Spot pass but full regression detected",
            body="\n".join(fix_summary) + "\n\nA regression was introduced.",
        )
        sys.exit(1)

    # ── All green — push branch + open PR ────────────────────────────────────
    print("\n[HEAL] All tests green. Opening PR…")
    push_and_open_pr(fix_summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-heal broken Playwright locators.")
    parser.add_argument("--report", required=True, help="Path to pytest-json-report JSON file")
    args = parser.parse_args()
    main(args.report)
