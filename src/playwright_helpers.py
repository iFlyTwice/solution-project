import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def open_page(url, timeout=60000):
    """
    Opens a URL using Playwright and returns the page object.

    Args:
        url (str): The URL to open.
        timeout (int): The timeout for page loading in milliseconds.

    Returns:
        tuple: (page, context, browser, playwright)
    """
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(channel="chrome", headless=False, args=["--start-maximized"])
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=timeout)
        logging.info(f"Opened URL: {url}")
        return page, context, browser, playwright
    except PlaywrightTimeoutError:
        logging.error(f"Timeout while loading the page: {url}")
        raise
    except Exception as e:
        logging.exception(f"Failed to open URL: {url}")
        raise

async def close_resources(page, context, browser, playwright):
    """
    Closes the resources opened by Playwright.

    Args:
        page (Page): The Playwright Page object.
        context (Context): The Playwright BrowserContext.
        browser (Browser): The Playwright Browser.
        playwright (Playwright): The Playwright instance.
    """
    try:
        if page:
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
        logging.info("Playwright resources closed.")
    except Exception as e:
        logging.exception("Error closing Playwright resources.") 