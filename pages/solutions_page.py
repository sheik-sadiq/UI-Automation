from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class SolutionsPage(BasePage):
    """Page Object for the Solutions page (/solutions)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

        # --- Solutions page CTA ---
        self.schedule_consultation: Locator = page.get_by_role(
            "link", name="Schedule Your Consultation", exact=True
        )

    def open(self) -> "SolutionsPage":
        """Navigate to the Solutions page."""
        self.navigate("/solutions")
        return self
