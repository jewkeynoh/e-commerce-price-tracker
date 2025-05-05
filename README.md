# 🛒 Python E-commerce Price Tracker

## Overview

This Python-based tool monitors prices of specified products on e-commerce websites. It periodically scrapes product pages, extracts current prices, compares them to your target and previously recorded prices, and sends email alerts when a price drop is detected.

Designed for robustness and reliability, the tool includes:

* Configuration management via YAML
* Persistent storage using SQLite
* Error handling and logging
* Polite scraping (User-Agent headers, request delays)

> ⚠️ **Disclaimer**: Web scraping is sensitive to site structure changes and may break unexpectedly. Always respect `robots.txt`, terms of service, and scrape responsibly. Excessive scraping may lead to IP bans.

---

## ✨ Features

* **Configurable Product List**: Define products (URL, target price, CSS selectors) via `config.yaml`
* **Accurate Price Parsing**: Extracts prices using CSS selectors
* **Smart Price Drop Detection**: Alerts only if the price is below your target *and* lower than the last known price
* **Persistent Price History**: Stores last known prices in `SQLite` at `data/product_prices.db`
* **Email Notifications**: Alerts you via Gmail SMTP (App Password required)
* **Scheduled Price Checks**: Uses `schedule` to run at intervals (configurable)
* **Polite and Resilient Scraping**: Includes User-Agent customization, delays, and error handling
* **Secure Credentials**: Stores sensitive info in a `.env` file
* **Detailed Logging**: Tracks events and errors in `logs/price_tracker.log`
* **Modular Code**: Clean separation of config, scraping, alerting, and tracking logic

---

## 📁 Project Structure

```
price_tracker/
├── venv/                     # Python virtual environment
├── logs/
│   └── price_tracker.log     # Log output
├── data/
│   └── product_prices.db     # SQLite database
├── .gitignore
├── config.yaml               # Main configuration file
├── alert_utils.py            # Email alert logic
├── scraper.py                # HTML scraping utilities
├── tracker.py                # Main runner with scheduling
├── requirements.txt
├── .env.example              # Template for sensitive info
├── .env                      # Actual secrets (**DO NOT COMMIT**)
└── README.md                 # This file
```

---

## ⚙️ Prerequisites

* **Python** 3.6+
* **pip** (Python package manager)

---

## 🛠️ Setup and Configuration

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourname/price-tracker.git
   cd price-tracker
   ```

2. **Create and Activate Virtual Environment**

   ```bash
   python -m venv venv
   # Windows (Git Bash):
   source venv/Scripts/activate
   # macOS/Linux:
   # source venv/bin/activate
   # Windows CMD:
   # .\venv\Scripts\activate.bat
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure `.env` for Credentials**

   * Copy `.env.example` to `.env`
   * Add your Gmail App Password
   * Optional: Add your email as `EMAIL_SENDER`

5. **Edit `config.yaml`**

   * Add your product URLs, `target_price`, and CSS `price_selector`
   * Optionally add `name_selector`
   * Update the `user_agent` string (find yours at [whatsmyuseragent.com](https://www.whatsmyuseragent.com/))
   * Adjust:

     * `request_delay_seconds` (≥10–15s recommended)
     * `schedule_interval_minutes`
     * `alert_settings` (enable alerts, set `recipient_email`)

---

## ▶️ Usage

1. **Activate Environment**

   ```bash
   source venv/Scripts/activate  # or the appropriate command
   ```

2. **Run the Tracker**

   ```bash
   python tracker.py
   ```

* The script checks all products once, then runs periodically based on your config.
* Watch the terminal or `logs/price_tracker.log` for activity.
* Press `Ctrl+C` to stop the process gracefully.

---

## 🔍 Finding CSS Selectors (Mini Guide)

1. Open the product page in Chrome/Firefox.

2. Right-click the price → **Inspect**.

3. Look for an element with class/id near the price:

   ```html
   <span class="price-tag pdp-price_size_xl" id="price_display_id">₱1,999.00</span>
   ```

4. Create a selector:

   * By ID: `#price_display_id`
   * By class: `.price-tag.pdp-price_size_xl`
   * By tag + class: `span.pdp-price_size_xl`

5. Test in browser console:

   ```js
   document.querySelector('#your_selector')
   ```

6. Paste the working selector in `config.yaml` under `price_selector`.
   Do the same for `name_selector` if desired.

> ⚠️ **Note**: CSS selectors often break when site layouts change.

---

## 🪖 License

This project is licensed under the [MIT License](LICENSE).
