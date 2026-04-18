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
    Navigate to `url` headlessly and return a compact JSON snapshot of all
    interactive elements (links, buttons, headings) on the page.

    Why NOT page.content():  returns full React HTML (500KB+) → token quota
                              exhausted on Gemini free tier for a single call.
    Why this approach:        page.evaluate() lets us cherry-pick only the
                              elements Playwright locators reference, giving
                              Gemini a <5KB payload with exactly what it needs.
    """
    EXTRACT_SCRIPT = """
    () => {
        const seen = new Set();
        const els  = [];
        const sel  = 'a, button, h1, h2, h3, h4, [role="button"], [role="link"], [role="heading"]';
        document.querySelectorAll(sel).forEach(el => {
            const text      = (el.innerText || el.textContent || '').trim().slice(0, 120);
            const ariaLabel = el.getAttribute('aria-label') || '';
            const role      = el.getAttribute('role') || el.tagName.toLowerCase();
            const href      = el.getAttribute('href') || '';
            const key       = role + '|' + text + '|' + ariaLabel;
            if ((text || ariaLabel) && !seen.has(key)) {
                seen.add(key);
                els.push({ tag: el.tagName, role, text, ariaLabel, href });
            }
        });
        return JSON.stringify(els, null, 2);
    }
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30_000)
        snapshot = page.evaluate(EXTRACT_SCRIPT)
        browser.close()
    return snapshot or "[]"


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
