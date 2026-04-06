"""
UI Test Suite for https://www.growthcreators.ai/

Covers:
  1. Website operational check
  2. Header navigation links
  3. Global action buttons (Community / Contact Us)
  4. Home page CTAs (Schedule Discovery Call / footer Contact Us)
  5. About Us page CTA (footer Contact Us)
  6. Solutions page CTA (Schedule your Consultation)
  7. Case Studies page CTA (Start your success story)
"""

from playwright.sync_api import Page, expect

from pages.about_page import AboutPage
from pages.case_studies_page import CaseStudiesPage
from pages.home_page import HomePage
from pages.solutions_page import SolutionsPage


# ---------------------------------------------------------------------------
# Test 1 – Website is operational
# ---------------------------------------------------------------------------
def test_website_is_operational(page: Page, base_url: str) -> None:
    """Navigate to the base URL and verify the page loads successfully."""
    home = HomePage(page)
    home.open()

    expect(home.hero_heading).to_be_visible()


# ---------------------------------------------------------------------------
# Test 2 – Header navigation contains expected links
# ---------------------------------------------------------------------------
def test_header_navigation_links(page: Page, base_url: str) -> None:
    """Verify the main navigation contains Home, Solutions, Case Studies,
    and About us links."""
    home = HomePage(page)
    home.open()

    expect(home.nav_home).to_be_visible()
    expect(home.nav_solutions).to_be_visible()
    expect(home.nav_case_studies).to_be_visible()
    expect(home.nav_about_us).to_be_visible()


# ---------------------------------------------------------------------------
# Test 3 – Global action buttons are visible
# ---------------------------------------------------------------------------
def test_global_action_buttons(page: Page, base_url: str) -> None:
    """Verify 'Community' and 'Contact Us' buttons are visible on the main
    page."""
    home = HomePage(page)
    home.open()

    expect(home.community_button).to_be_visible()
    expect(home.contact_us_button).to_be_visible()


# ---------------------------------------------------------------------------
# Test 4 – Home page CTAs
# ---------------------------------------------------------------------------
def test_home_page_ctas(page: Page, base_url: str) -> None:
    """Verify 'Schedule Discovery Call' button is present and a 'Contact Us'
    button is located at the bottom of the page."""
    home = HomePage(page)
    home.open()

    expect(home.schedule_discovery_call).to_be_visible()
    expect(home.footer_contact_us).to_be_visible()


# ---------------------------------------------------------------------------
# Test 5 – About Us page CTA
# ---------------------------------------------------------------------------
def test_about_us_contact_us_button(page: Page, base_url: str) -> None:
    """Navigate to the About Us page and verify the footer 'Contact Us'
    button is present."""
    about = AboutPage(page)
    about.open()

    expect(about.footer_contact_us).to_be_visible()


# ---------------------------------------------------------------------------
# Test 6 – Solutions page CTA
# ---------------------------------------------------------------------------
def test_solutions_schedule_consultation_button(page: Page, base_url: str) -> None:
    """Navigate to the Solutions page and verify the 'Schedule your
    Consultation' button is present."""
    solutions = SolutionsPage(page)
    solutions.open()

    expect(solutions.schedule_consultation).to_be_visible()


# ---------------------------------------------------------------------------
# Test 7 – Case Studies page CTA
# ---------------------------------------------------------------------------
def test_case_studies_start_success_story_button(page: Page, base_url: str) -> None:
    """Navigate to the Case Studies page and verify the 'Start your success
    story' button is present."""
    case_studies = CaseStudiesPage(page)
    case_studies.open()

    expect(case_studies.start_success_story).to_be_visible()


# ---------------------------------------------------------------------------
# Test 8 – Clicking nav items routes to the correct pages
# ---------------------------------------------------------------------------
def test_nav_solutions_navigates_to_solutions_page(page: Page, base_url: str) -> None:
    """Click the Solutions nav item and verify the URL changes to /solutions."""
    home = HomePage(page)
    home.open()

    home.click_nav_solutions()

    expect(page).to_have_url(f"{base_url}/solutions")


def test_nav_case_studies_navigates_to_case_studies_page(page: Page, base_url: str) -> None:
    """Click the Case Studies nav item and verify the URL changes to /case-studies."""
    home = HomePage(page)
    home.open()

    home.click_nav_case_studies()

    expect(page).to_have_url(f"{base_url}/case-studies")


def test_nav_about_us_navigates_to_about_us_page(page: Page, base_url: str) -> None:
    """Click the About Us nav item and verify the URL changes to /about-us."""
    home = HomePage(page)
    home.open()

    home.click_nav_about_us()

    # The nav button routes to /about (the site also accepts /about-us via redirect)
    expect(page).to_have_url(f"{base_url}/about")


# ---------------------------------------------------------------------------
# Test 9 – Schedule Discovery Call CTA navigates away from the home page
# ---------------------------------------------------------------------------
def test_schedule_discovery_call_navigates(page: Page, base_url: str) -> None:
    """Click 'Schedule Discovery Call' and verify it opens a booking page.

    The CTA opens a new tab (popup), so we capture the popup and assert it
    navigated to a real URL rather than asserting the current page changed.
    """
    home = HomePage(page)
    home.open()

    with page.expect_popup() as popup_info:
        home.schedule_discovery_call.click()

    popup = popup_info.value
    popup.wait_for_load_state("domcontentloaded")
    # The popup must have navigated to a real URL (not blank)
    expect(popup).not_to_have_url("about:blank")
