# -*- coding: utf-8 -*-
"""
Functions for fetching HTML content and parsing product details.
"""
import requests
from bs4 import BeautifulSoup
import logging
import time
import re # For cleaning price string

logger = logging.getLogger(__name__)

def fetch_html(url, user_agent, delay_seconds=5):
    """
    Fetches HTML content for a given URL with specified user agent and delay.

    Args:
        url (str): The URL to fetch.
        user_agent (str): The User-Agent string to use.
        delay_seconds (int): Seconds to wait before making the request.

    Returns:
        str or None: The HTML content as text, or None if fetching fails.
    """
    # Apply delay before request
    logger.debug(f"Waiting {delay_seconds}s before fetching {url}")
    time.sleep(delay_seconds)

    headers = {'User-Agent': user_agent}
    logger.info(f"Fetching URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=20) # Add timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        logger.info(f"Successfully fetched URL: {url} (Status: {response.status_code})")
        # Use response.text for BeautifulSoup
        return response.text
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error while fetching {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def clean_price_string(price_str):
    """Removes currency symbols, commas, and whitespace, converts to float."""
    if price_str is None:
        return None
    try:
        # Remove non-digit characters except decimal point
        # Handles currency symbols (₱, $, etc.), commas, spaces
        cleaned = re.sub(r"[^0-9.]", "", price_str)
        # Handle cases where multiple decimal points might exist after cleaning
        parts = cleaned.split('.')
        if len(parts) > 2:
             # Join integer part and only the first fractional part
             cleaned = parts[0] + '.' + parts[1]
        elif len(parts) == 1:
             # No decimal point found
             cleaned = parts[0]
        # Prevent empty string from causing error
        if not cleaned:
             return None
        return float(cleaned)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not convert price string '{price_str}' to float: {e}")
        return None

def parse_price(html_content, css_selector):
    """
    Parses the price from HTML content using a CSS selector.

    Args:
        html_content (str): The HTML content of the page.
        css_selector (str): The CSS selector for the price element.

    Returns:
        float or None: The cleaned price as a float, or None if not found/parsed.
    """
    if not html_content:
        return None
    try:
        soup = BeautifulSoup(html_content, 'lxml') # Use lxml parser
        price_element = soup.select_one(css_selector)

        if price_element:
            price_text = price_element.get_text(strip=True)
            logger.debug(f"Found price text using selector '{css_selector}': '{price_text}'")
            cleaned_price = clean_price_string(price_text)
            if cleaned_price is not None:
                 logger.info(f"Parsed price: {cleaned_price}")
                 return cleaned_price
            else:
                 logger.warning(f"Could not clean price text: '{price_text}'")
                 return None
        else:
            logger.warning(f"Price element not found using selector: '{css_selector}'")
            return None
    except Exception as e:
        logger.error(f"Error parsing HTML content: {e}", exc_info=True)
        return None

def parse_product_name(html_content, css_selector):
    """
    Parses the product name from HTML content using a CSS selector.

    Args:
        html_content (str): The HTML content of the page.
        css_selector (str): The CSS selector for the name element.

    Returns:
        str or None: The product name, or None if not found.
    """
    if not html_content or not css_selector: # Allow skipping if no selector provided
        return None
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        name_element = soup.select_one(css_selector)
        if name_element:
            name_text = name_element.get_text(strip=True)
            logger.info(f"Parsed product name: '{name_text}'")
            return name_text
        else:
            logger.warning(f"Product name element not found using selector: '{css_selector}'")
            return None
    except Exception as e:
        logger.error(f"Error parsing product name: {e}", exc_info=True)
        return None