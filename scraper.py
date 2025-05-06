# -*- coding: utf-8 -*-
"""
Functions for fetching fully rendered HTML content using Selenium
and parsing product details using BeautifulSoup.
"""

import logging
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager  # Simplifies cross-platform ChromeDriver setup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

def setup_webdriver(user_agent):
    """Sets up Chrome WebDriver with options.

    - Uses custom user-agent to reduce bot detection.
    - Configured for headless, sandboxed environments.
    - Uses webdriver-manager for reliability across systems.
    """
    logger.debug("Setting up Chrome WebDriver...")
    chrome_options = ChromeOptions()
    chrome_options.add_argument(f"user-agent={user_agent}")
    # chrome_options.add_argument("--headless=new")  # Recommended for production scraping
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")  # Required for many cloud/VPS environments
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.debug("WebDriver setup complete.")
        return driver
    except ValueError as e:
        # Often caused by Chrome/Driver version mismatch or no internet during download
        logger.error(f"WebDriver Manager Error: {e}")
        return None
    except WebDriverException as e:
        logger.error(f"WebDriverException during setup: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error setting up WebDriver: {e}", exc_info=True)
        return None

def fetch_html_with_selenium(url, user_agent, price_selector, wait_time=20):
    """
    Fetches fully rendered HTML content using Selenium and waits for the price element.

    - Uses explicit waits instead of sleep for efficiency.
    - Handles dynamic content rendering with post-load pause.
    - Ensures driver is properly shut down in all cases.
    """
    driver = setup_webdriver(user_agent)
    if not driver:
        return None

    html_content = None
    logger.info(f"Fetching URL with Selenium: {url}")
    try:
        driver.get(url)
        logger.info(f"Waiting up to {wait_time}s for price element ('{price_selector}')...")

        # Explicitly wait for price selector, more reliable than sleep
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, price_selector))
        )
        time.sleep(2)  # Safety buffer to allow full JS rendering
        html_content = driver.page_source
        logger.debug(f"Fetched page content of length: {len(html_content)}")
    except TimeoutException:
        logger.error(f"Timeout: Price element ('{price_selector}') not found in {wait_time}s")
    except WebDriverException as e:
        logger.error(f"WebDriver error while fetching: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        driver.quit()
        logger.debug("WebDriver closed after fetching.")

    return html_content

# ---------------------------------------------
# Parsing utilities for extracting structured data
# ---------------------------------------------

def clean_price_string(price_str):
    """Cleans and converts a raw price string to float.

    - Handles multiple currency symbols and noisy text.
    - Removes extra decimal points.
    - Logs failures without crashing pipeline.
    """
    if price_str is None:
        return None
    try:
        price_str = price_str.replace('₱', '').replace('$', '').replace(',', '').strip()
        cleaned = re.sub(r"[^0-9.]", "", price_str)
        parts = cleaned.split('.')
        if len(parts) > 2:
            cleaned = parts[0] + '.' + parts[1]
        elif len(parts) == 1:
            cleaned = parts[0]
        if not cleaned:
            return None
        return float(cleaned)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not convert price string '{price_str}' to float: {e}")
        return None

def parse_price(html_content, css_selector):
    """Extracts and parses price text from rendered HTML using a CSS selector.

    - Uses BeautifulSoup for fast parsing.
    - Logs selector failures for debugging CSS mismatch.
    - Separates HTML extraction from numerical parsing.
    """
    if not html_content:
        return None
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        price_element = soup.select_one(css_selector)
        if price_element:
            price_text = price_element.get_text(strip=True)
            logger.debug(f"Raw price text found: '{price_text}'")
            cleaned_price = clean_price_string(price_text)
            if cleaned_price is not None:
                logger.info(f"Parsed price: {cleaned_price}")
                return cleaned_price
            else:
                logger.warning(f"Price string could not be cleaned: '{price_text}'")
                return None
        else:
            logger.warning(f"No price element found for selector: '{css_selector}'")
            return None
    except Exception as e:
        logger.error(f"Error parsing price: {e}", exc_info=True)
        return None

def parse_product_name(html_content, css_selector):
    """Parses product name from HTML using a CSS selector.

    - Graceful failure if selector is missing or mismatched.
    - Reusable for various fields beyond just product names.
    """
    if not html_content or not css_selector:
        return None
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        name_element = soup.select_one(css_selector)
        if name_element:
            name_text = name_element.get_text(strip=True)
            logger.info(f"Parsed product name: '{name_text}'")
            return name_text
        else:
            logger.warning(f"No product name found for selector: '{css_selector}'")
            return None
    except Exception as e:
        logger.error(f"Error parsing product name: {e}", exc_info=True)
        return None
