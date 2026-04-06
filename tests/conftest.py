import pytest
from playwright.sync_api import Browser, Page


@pytest.fixture()
def page(browser: Browser, base_url: str) -> Page:
    """Isolated browser page per test.

    Each test gets a fresh context so there is no shared state or
    order-dependency between tests.
    """
    context = browser.new_context(base_url=base_url)
    pg = context.new_page()
    yield pg
    context.close()


@pytest.fixture()
def home_url(base_url: str) -> str:
    """Return the base URL for the home page."""
    return base_url
