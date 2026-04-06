"""
DOM Inspection Utility — scripts/inspect_dom.py
================================================
Standalone helper for inspecting the live growthcreators.ai DOM.
Run manually when writing or debugging locators:

    python scripts/inspect_dom.py

This script is NOT part of the automated test suite.
"""
from playwright.sync_api import sync_playwright

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
