"""
DOM Inspection Utility — scripts/inspect_dom.py
================================================
Two modes of use:

  1. Callable function (used by heal_runner.py during automated healing):
         from scripts.inspect_dom import capture_dom_snapshot
         snapshot = capture_dom_snapshot("https://www.growthcreators.ai")

  2. Manual run (unchanged behaviour for human debugging):
         python scripts/inspect_dom.py
"""
from playwright.sync_api import sync_playwright


def capture_dom_snapshot(url: str) -> str:
    """
    Navigate to `url` headlessly and return the full page HTML.

    Uses page.content() — available in every Playwright version, no
    API-version constraints. The HTML is passed to the LLM so it can
    identify the current role/name/text of elements whose locators broke.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30_000)
        html = page.content()    # full rendered HTML — universally available
        browser.close()
    return html or ""


# ── Manual inspection block (unchanged) ──────────────────────────────────────
if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.growthcreators.ai", wait_until="networkidle")

        # Inspect all <header> / <nav> tags
        result = page.eval_on_selector_all(
            "header a, header button",
            "els => els.map(e => e.tagName + '|' + e.innerText.trim() + '|visible:' + (e.offsetParent !== null))"
        )
        print("=== HEADER ELEMENTS ===")
        for r in result:
            print(r)

        # Check how many times "Home" appears as an ARIA-role link
        home_links = page.get_by_role("link", name="Home", exact=True).count()
        print(f"\n=== role=link name=Home count: {home_links} ===")

        # All links visible in first screenful (look for header nav pattern)
        all_links = page.eval_on_selector_all(
            "a",
            "els => els.filter(e => e.offsetParent !== null).map(e => e.innerText.trim()).filter(t => t.length > 0 && t.length < 40)"
        )
        print("\n=== ALL VISIBLE LINKS ===")
        for r in all_links:
            print(r)

        browser.close()
