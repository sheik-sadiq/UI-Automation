from playwright.sync_api import Locator, Page


class BasePage:
    """Shared header, navigation, and footer locators common to all pages."""

    BASE_URL = "https://www.growthcreators.ai"

    def __init__(self, page: Page) -> None:
        self.page = page

        # --- Header navigation (nav items are <button> elements inside <header>) ---
        self._header = page.locator("header")
        self.nav_home: Locator = self._header.get_by_role("button", name="Home", exact=True).first
        self.nav_solutions: Locator = self._header.get_by_role("button", name="Solutions", exact=True).first
        self.nav_case_studies: Locator = self._header.get_by_role("button", name="Case Studies", exact=True).first
        self.nav_about_us: Locator = self._header.get_by_role("button", name="About Us", exact=True).first

        # --- Global action buttons (header area) ---
        # ⚠️  DELIBERATELY BROKEN for auto-heal validation (fake button rename)
        self.community_button: Locator = page.get_by_role("link", name="Join Community", exact=True)
        self.contact_us_button: Locator = self._header.get_by_role("link", name="Contact Us", exact=True).first

        # --- Footer "Contact Us" (inside the "Ready to Transform" CTA section) ---
        self.footer_contact_us: Locator = (
            page.locator("footer").get_by_role("link", name="Contact Us", exact=True)
        )

    def navigate(self, path: str = "/") -> None:
        """Navigate to a path relative to the base URL."""
        self.page.goto(path)

    def click_nav_solutions(self) -> None:
        """Click the Solutions nav item and wait for navigation."""
        self.nav_solutions.click()
        self.page.wait_for_url("**/solutions**")

    def click_nav_case_studies(self) -> None:
        """Click the Case Studies nav item and wait for navigation."""
        self.nav_case_studies.click()
        self.page.wait_for_url("**/case-studies**")

    def click_nav_about_us(self) -> None:
        """Click the About Us nav item and wait for navigation.

        The site routes to /about (not /about-us) when navigated via the nav
        button, even though a direct goto("/about-us") redirects there too.
        """
        self.nav_about_us.click()
        self.page.wait_for_url("**/about**")
