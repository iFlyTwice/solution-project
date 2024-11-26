import asyncio
import logging
import os
import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from constants import LINKS
import pywinauto
import time
import threading

async def async_open_link(url, name):
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--start-maximized"]
        )

        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        logging.info(f"Opened URL with Playwright: {name} - {url}")

        page_title = await page.title()
        logging.info(f"Page Title for {name}: {page_title}")

        await browser.close()

        await page.close()
        await context.close()
        await playwright.stop()

    except PlaywrightTimeoutError:
        logging.exception(f"Timeout while loading the page: {name} - {url}")
    except Exception as e:
        logging.exception(f"Failed to open URL with Playwright: {name} - {url}")

async def async_open_midway_access(username, pin, testing_mode=False, timeout=60000):
    """
    Automates MIDWAY ACCESS login with optional testing mode and customizable timeout.

    Args:
        username (str): User's username.
        pin (str): User's PIN.
        testing_mode (bool): Enable testing mode for detailed logs and screenshots.
        timeout (int): Timeout for page navigation in milliseconds.
    """
    try:
        log_debug_step(1, "Setting up Playwright.")
        playwright, browser, context, page = await setup_playwright()
        
        log_debug_step(2, f"Navigating to MIDWAY ACCESS URL: {LINKS['MIDWAY ACCESS']} with timeout={timeout}ms")
        await page.goto(LINKS["MIDWAY ACCESS"], timeout=timeout)
        logging.info("Opened MIDWAY ACCESS URL.")
        if testing_mode:
            await capture_screenshot(page, "midway_access_open.png", "Opened MIDWAY ACCESS URL")

        log_debug_step(3, "Filling in username and PIN.")
        await page.fill('#user_name', username)
        await page.fill('#password', pin)
        if testing_mode:
            await capture_screenshot(page, "midway_access_filled_form.png", "Filled login form")

        log_debug_step(4, "Submitting the login form.")
        await page.click('#verify_btn')
        await page.wait_for_load_state('networkidle', timeout=15000)
        logging.info("Submitted login form.")
        if testing_mode:
            await capture_screenshot(page, "midway_access_submit.png", "Submitted login form")

        log_debug_step(5, "Retrieving page title after login.")
        page_title = await page.title()
        logging.info(f"Page Title after login: {page_title}")

        await browser.close()
        await playwright.stop()
    except PlaywrightTimeoutError as te:
        log_error("MIDWAY ACCESS automation", te, LINKS["MIDWAY ACCESS"])
    except Exception as e:
        log_error("MIDWAY ACCESS automation", e, LINKS["MIDWAY ACCESS"])

async def async_open_reports_page(testing_mode=False, timeout=60000):
    """
    Opens the REPORTS page with optional testing mode and customizable timeout.

    Args:
        testing_mode (bool): Enable testing mode for detailed logs and screenshots.
        timeout (int): Timeout for page navigation in milliseconds.
    """
    try:
        log_debug_step(1, "Setting up Playwright.")
        playwright, browser, context, page = await setup_playwright()
        
        log_debug_step(2, f"Navigating to REPORTS URL: {LINKS['REPORTS']} with timeout={timeout}ms")
        await page.goto(LINKS["REPORTS"], timeout=timeout)
        logging.info("Opened REPORTS page with Playwright.")

        if testing_mode:
            await capture_screenshot(page, "reports_page_open.png", "Opened REPORTS page")

        await browser.close()
        await playwright.stop()
    except PlaywrightTimeoutError as te:
        log_error("REPORTS page automation", te, LINKS["REPORTS"])
    except Exception as e:
        log_error("REPORTS page automation", e, LINKS["REPORTS"])

async def capture_screenshot(page, filename, description):
    """
    Captures a screenshot of the current page and logs the action.

    Args:
        page: Playwright page instance.
        filename (str): Name of the file to save the screenshot.
        description (str): A description to log.
    """
    try:
        debug_folder = create_debug_folder()
        screenshot_path = os.path.join(debug_folder, filename)
        await page.screenshot(path=screenshot_path)
        logging.info(f"{description}. Screenshot saved: {screenshot_path}")
    except Exception as e:
        logging.exception(f"Failed to capture screenshot: {e}")

async def setup_playwright(channel="chrome", headless=False):
    """
    Sets up Playwright browser, context, and page instances.

    Args:
        channel (str): Browser channel to use (default: Chrome).
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        tuple: (playwright, browser, context, page)
    """
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            channel=channel,
            headless=headless,
            args=["--start-maximized"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        return playwright, browser, context, page
    except Exception as e:
        logging.exception("Failed to setup Playwright.")
        raise

def create_debug_folder():
    """
    Creates a timestamped folder for debug output.

    Returns:
        str: Path to the created debug folder.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"debug_output_{timestamp}"
        os.makedirs(folder_name, exist_ok=True)
        logging.info(f"Debug folder created: {folder_name}")
        return folder_name
    except Exception as e:
        logging.exception(f"Failed to create debug folder: {e}")
        return "debug_output"

def log_error(context, exception, url=None):
    """
    Logs errors with additional context.

    Args:
        context (str): Description of where the error occurred.
        exception (Exception): The caught exception.
        url (str): The URL being processed (optional).
    """
    if url:
        logging.exception(f"Error in {context} while processing URL: {url}. Exception: {exception}")
    else:
        logging.exception(f"Error in {context}. Exception: {exception}")

def log_debug_step(step, message):
    """
    Logs detailed steps for debugging.

    Args:
        step (int): Step number.
        message (str): Description of the step.
    """
    logging.debug(f"[Step {step}] {message}")

def reset_security_key():
    """
    Automates the reset process for a security key via Windows Settings using pywinauto.
    """
    try:
        # Start the Settings application
        logging.info("Opening Windows Settings...")
        app = pywinauto.Application(backend="uia").start(
            "explorer.exe shell:appsFolder\\windows.immersivecontrolpanel_cw5n1h2txyewy!microsoft.windows.immersivecontrolpanel"
        )

        # Wait for the Settings window to appear
        time.sleep(3)
        settings_window = app.window(title_re=".*Settings.*")

        # Navigate to the "Sign-in Options" page
        logging.info("Navigating to 'Sign-in options'...")
        settings_window.child_window(title="Sign-in options", control_type="ListItem").wait("exists", timeout=10).click_input()

        # Wait for the "Sign-in Options" page to load
        time.sleep(2)

        # Click the "Security Key" button
        logging.info("Clicking the 'Security Key' button...")
        settings_window.child_window(title="Security Key", control_type="Button").wait("exists", timeout=10).click_input()

        # Click the "Manage" button
        logging.info("Clicking the 'Manage' button...")
        settings_window.child_window(title="Manage", control_type="Button").wait("exists", timeout=10).click_input()

        # Click the "Reset" button
        logging.info("Clicking the 'Reset' button...")
        settings_window.child_window(title="Reset", control_type="Button").wait("exists", timeout=10).click_input()

        # Confirm the reset action (if applicable)
        logging.info("Confirming the reset action...")
        if settings_window.child_window(title="Yes", control_type="Button").exists(timeout=5):
            settings_window.child_window(title="Yes", control_type="Button").click_input()

        logging.info("Security key reset successfully completed!")

    except Exception as e:
        logging.error(f"An error occurred during the reset process: {e}")

def initiate_reset_security_key():
    reset_thread = threading.Thread(target=reset_security_key, daemon=True)
    reset_thread.start() 