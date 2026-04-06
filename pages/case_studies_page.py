from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class CaseStudiesPage(BasePage):
    """Page Object for the Case Studies page (/case-studies)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

        # --- Case Studies page CTA ---
        self.start_success_story: Locator = page.get_by_role(
            "link", name="Start Your Success Story", exact=True
        )

    def open(self) -> "CaseStudiesPage":
        """Navigate to the Case Studies page."""
        self.navigate("/case-studies")
        return self
