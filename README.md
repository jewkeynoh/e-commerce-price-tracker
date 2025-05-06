# 🛒 Python E-commerce Price Tracker (Selenium Version)

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📘 Overview

This project tracks product prices on dynamic e-commerce websites using **Selenium** to automate browser rendering, which is crucial for JavaScript-heavy sites. It parses prices with **BeautifulSoup**, logs them into an **SQLite** database, and sends **email alerts** via Gmail when price drops occur.

> ⚠️ **Note**: Scraping JavaScript content requires Selenium. Sites needing login, CAPTCHA verification, or employing bot detection may block scraping attempts. Use responsibly and ethically.

## ✅ Features

* **Selenium-Powered Scraping**: Handles JavaScript-rendered pages.
* **Custom Configurations**: Define products, selectors, user agent, and price targets in `config.yaml`.
* **Price Monitoring**: Detects price drops below a target and previous price.
* **Email Alerts**: Notifies via Gmail with App Password authentication.
* **SQLite Storage**: Persists price history in `data/product_prices.db`.
* **Logging**: Logs activity and issues in `logs/price_tracker.log`.
* **Scheduling**: Uses `schedule` for automated periodic checks.
* **Modular Architecture**: Clean separation of scraping, tracking, and alerting.
* **Secure Credentials**: `.env` file for sensitive data.

## 📁 Project Structure

```
price_tracker/
├── venv/                  # Virtual environment
├── logs/
│   └── price_tracker.log  # Application logs
├── data/
│   └── product_prices.db  # SQLite database
├── .gitignore             # Ignores .env, venv/, logs/, data/, etc.
├── config.yaml            # Product config (URLs, CSS selectors, etc.)
├── alert_utils.py         # Email functions
├── scraper.py             # Selenium-based scraper
├── tracker.py             # Main execution logic
├── requirements.txt       # Python package dependencies
├── .env.example           # Template for credentials
├── .env                   # Actual credentials (excluded from Git)
└── README.md              # This file
```

## ⚙️ Prerequisites

* **Python 3.6+**
* **Google Chrome Browser** (updated)
* **pip** (Python package manager)
* **Git** (optional, for version control)

## 🚀 Setup Instructions

1. **Clone the Repository**

```bash
git clone <repo-url>
cd price_tracker
```

2. **Create & Activate Virtual Environment**

```bash
python -m venv venv

# Activate (choose your OS shell):
source venv/Scripts/activate       # Windows Git Bash/MINGW64
source venv/bin/activate           # Linux/macOS
.\venv\Scripts\activate.bat       # Windows CMD
.\venv\Scripts\Activate.ps1       # Windows PowerShell
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure Credentials**

```bash
cp .env.example .env
# Edit .env with your Gmail App Password & sender email
```

> 🔒 `.env` is already in `.gitignore` to avoid leaking secrets.

5. **Edit `config.yaml`**

* Replace sample product URLs.
* Set your `target_price`.
* Update `price_selector` and `name_selector` using browser DevTools (`document.querySelector(...)`).
* Adjust `selenium_wait_time`, `user_agent`, `schedule_interval_minutes`, and email `alert_settings`.

## ▶️ Usage

```bash
source venv/Scripts/activate  # Activate environment (choose your OS)
python tracker.py             # Start tracking loop
```

* Runs an initial check, then follows the configured interval.
* Operates headlessly unless modified (see below).
* Logs output to both console and `logs/price_tracker.log`.

## 🛠 Troubleshooting

| Problem                    | Solution                                                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **TimeoutException**       | Selector may be incorrect or wait time too short. Verify in DevTools and increase `selenium_wait_time`.         |
| **Non-headless Debugging** | Comment out `--headless` in `scraper.py` to observe browser behavior.                                           |
| **Blocked by Site**        | Login pages, CAPTCHAs, or errors = site is blocking Selenium. Remove the URL from config.                       |
| **WebDriver Errors**       | Ensure Chrome is updated. Let `webdriver-manager` auto-install. Alternatively, download and configure manually. |
| **Email Not Sending**      | Check `.env` values and log output. Ensure Gmail 2FA is enabled and correct App Password is used.               |
| **Price or Name is None**  | Check and refine selectors in `config.yaml` using browser DevTools.                                             |

---

## 🧪 Future Improvements

* Support for alternative email providers (e.g., SendGrid, SMTP relay)
* Captcha detection and optional alerting
* Multi-threaded scraping for faster processing
* Docker support for deployment

## 📜 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

## 🙏 Contributing

Feel free to fork, open issues, or submit PRs to enhance functionality, improve reliability, or expand compatibility with more sites.

---

Happy tracking! 📉💸

---
