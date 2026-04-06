import re

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class HomePage(BasePage):
    """Page Object for the Home page (/)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

        # --- Hero section (heading word rotates, so match the static portion) ---
        self.hero_heading: Locator = page.get_by_role(
            "heading", name=re.compile(r"AI Strategy!"), level=1
        )

        # --- Home page CTAs ---
        self.schedule_discovery_call: Locator = page.get_by_role(
            "link", name="Schedule Discovery Call", exact=True
        )

    def open(self) -> "HomePage":
        """Navigate to the Home page."""
        self.navigate("/")
        return self

    def click_schedule_discovery_call(self) -> None:
        """Click the 'Schedule Discovery Call' CTA.

        The button opens a booking page in a new tab (popup).
        Capture the popup with page.expect_popup() in the test.
        """
        self.schedule_discovery_call.click()
