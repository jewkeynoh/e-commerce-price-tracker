Markdown

# Python E-commerce Price Tracker

## Overview

This project monitors the prices of specified products on e-commerce websites. It periodically scrapes the product pages, extracts the current price, compares it against a target price and the previously recorded price, and sends an email alert if a significant price drop is detected.

It is built with robustness in mind, incorporating configuration management, error handling, persistent storage of last known prices (SQLite), logging, and polite scraping practices (User-Agent, delays).

**Disclaimer:** Web scraping can be fragile and depends heavily on the target website's structure, which can change without notice, breaking the scraper. Always respect the website's `robots.txt` and Terms of Service. Use this tool responsibly and ethically. Excessive scraping can lead to IP blocks.

## Features

* **Configurable Product List:** Define products to track (URL, target price, CSS selector) in `config.yaml`.
* **Price Parsing:** Extracts prices from HTML using CSS selectors.
* **Price Drop Detection:** Alerts only when the price drops below your target **and** is lower than the last recorded price.
* **Persistent Price History:** Uses an SQLite database (`data/product_prices.db`) to store the last known price for each product.
* **Email Alerts:** Sends email notifications for price drops (uses Gmail SMTP via App Password).
* **Scheduled Checks:** Uses the `schedule` library to run checks periodically (interval configurable in `config.yaml`).
* **Robust Scraping:** Includes User-Agent customization, request delays, basic error handling for network and parsing issues.
* **Secure Credential Handling:** Uses `.env` file for storing sensitive data like email passwords.
* **Detailed Logging:** Logs activities, errors, and price changes to console and `logs/price_tracker.log`.
* **Modular Code:** Logic separated into configuration, alerting, scraping, and tracking modules.

## Project Structure

```text
price_tracker/
├── venv/                   # Virtual environment
├── logs/
│   └── price_tracker.log   # Log file
├── data/
│   └── product_prices.db   # SQLite database for price history
├── .gitignore
├── config.yaml             # Main configuration file
├── alert_utils.py          # Email alert functions
├── scraper.py              # Functions for fetching and parsing HTML
├── tracker.py              # Main application script with scheduling
├── requirements.txt
├── .env.example            # Example credentials file
├── .env                    # Actual credentials (**DO NOT COMMIT**)
└── README.md               # This file
# Optional: LICENSE
Prerequisites
Python: 3.6+ recommended.
pip: Python package installer.
Setup and Configuration
Clone/Download: Get project files and cd into the price_tracker directory.
Create Virtual Environment:
Bash

python -m venv venv
Activate Virtual Environment:
Bash

# Windows Git Bash/MINGW64:
source venv/Scripts/activate
# Linux/macOS:
# source venv/bin/activate
# Windows CMD:
# .\venv\Scripts\activate.bat
Install Dependencies:
Bash

# Ensure venv is active
pip install -r requirements.txt
Configure Credentials (.env):
Copy .env.example to .env.
Edit .env and add your GMAIL_APP_PASSWORD. (Requires Google 2-Step Verification enabled and an App Password generated). You can optionally add EMAIL_SENDER here too.
Ensure .env is in .gitignore!
Configure Products and Settings (config.yaml):
Open config.yaml.
Crucially: Update the products list.
Replace sample URLs with the actual product URLs you want to track.
Set your desired target_price.
Find the correct CSS Selector (price_selector) for EACH product page. Use your browser's Developer Tools (Right-click on the price -> Inspect Element). Find a stable CSS class or ID for the element containing the price. This is the most fragile part and needs updating if the site changes. Add name_selector if you want to parse the name too.
Set your user_agent. Find yours easily at whatsmyuseragent.com.
Adjust request_delay_seconds (be polite, >= 10-15s is recommended).
Set schedule_interval_minutes.
Configure alert_settings (set enabled: True, add your recipient_email, ensure sender_email is set either here or in .env).
Save config.yaml.
Usage
Activate Virtual Environment:
Bash

source venv/Scripts/activate # Or your specific command
Run the Tracker:
Bash

python tracker.py
The script will perform an initial check of all products.
It will then enter a loop, checking prices based on the schedule_interval_minutes in config.yaml.
Check the console output and logs/price_tracker.log for activity.
Email alerts will be sent if price drop conditions are met.
Press Ctrl+C in the terminal to stop the tracker gracefully.
Finding CSS Selectors (Mini-Guide)
Open the product page in your web browser (e.g., Chrome, Firefox).
Right-click directly on the price element you want to track.
Select "Inspect" or "Inspect Element". This will open the Developer Tools, highlighting the HTML code for the price.
Look for unique attributes like class or id on the highlighted element or its parent elements.
Example: <span class="price-tag pdp-price_size_xl" id="price_display_id">₱1,999.00</span>
Construct a CSS Selector:
Using ID (best if available and unique): #price_display_id
Using Class: .pdp-price_size_xl (use dot prefix). If multiple classes, chain them: .price-tag.pdp-price_size_xl
Using element and class: span.pdp-price_size_xl
More complex selectors might be needed if simple ones aren't unique (e.g., finding a specific div first: #product-detail .price-section .final-price).
Test your selector in the DevTools console (e.g., in Chrome Console, type document.querySelector('#your_selector')) to see if it uniquely selects the price element.
Copy the working selector into the price_selector field in config.yaml for that product. Repeat for name_selector if desired.
Remember: These selectors WILL likely break when websites update their design!

License
MIT License recommended. Add a LICENSE file.

