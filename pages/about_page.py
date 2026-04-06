from playwright.sync_api import Page

from pages.base_page import BasePage


class AboutPage(BasePage):
    """Page Object for the About Us page (/about-us)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def open(self) -> "AboutPage":
        """Navigate to the About Us page."""
        self.navigate("/about-us")
        return self
