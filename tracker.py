# -*- coding: utf-8 -*-
"""
Main application script for the E-commerce Price Tracker.
Fetches product pages using Selenium, parses prices, checks against targets/history,
sends alerts, and schedules periodic checks.
"""

# --- Imports & Dependencies ---
import logging
import sys
import time
import yaml  # Requires PyYAML
import schedule
import sqlite3
from pathlib import Path
from datetime import datetime
import threading  # For running alerts in background

# Import custom modules
try:
    import scraper  # Uses Selenium for scraping
    import alert_utils  # Alert utilities (e.g., email)
except ImportError as e:
    print(f"[CRITICAL ERROR] Failed to import required modules: {e}")
    sys.exit(1)

# --- Global Constants ---
CONFIG_FILE = 'config.yaml'
config_data = {}
db_connection = None
db_cursor = None

# --- Logger Setup ---
logger = logging.getLogger(__name__)  # Module-level logger

# --- Configuration Loading ---
def load_config(config_path):
    """Loads configuration from a YAML file and populates `config_data`."""
    global config_data
    print(f"Attempting to load configuration from {config_path}...")  # For initial debugging
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        if not config_data:
            print(f"[CRITICAL ERROR] Config file {config_path} is empty or invalid.")
            sys.exit(1)
    except FileNotFoundError:
        print(f"[CRITICAL ERROR] Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[CRITICAL ERROR] Error parsing configuration: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[CRITICAL ERROR] Unexpected config loading error: {e}")
        sys.exit(1)

# --- Logging Setup ---
def setup_logging():
    """Initializes structured logging based on configuration."""
    log_level_str = config_data.get('log_level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_file = Path(config_data.get('log_file', 'logs/price_tracker.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Override any pre-configured logging
    )

    # Reduce verbosity of noisy libraries
    for noisy_logger in ["requests", "urllib3", "selenium", "webdriver_manager"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    logger.info("Logging configured successfully.")

# --- Database Setup ---
def initialize_db():
    """Creates SQLite database and schema if they do not exist."""
    global db_connection, db_cursor
    db_path_str = config_data.get('database_file', 'data/product_prices.db')
    db_path = Path(db_path_str)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing database at: {db_path}")
    try:
        db_connection = sqlite3.connect(str(db_path), check_same_thread=False)
        db_cursor = db_connection.cursor()
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                url TEXT PRIMARY KEY,
                name TEXT,
                target_price REAL,
                last_price REAL,
                last_check_timestamp TEXT
            )
        """)
        db_connection.commit()
        logger.info("Database initialized.")
    except sqlite3.Error as e:
        logger.critical(f"Failed to initialize DB: {e}", exc_info=True)
        sys.exit(1)

# --- Database Operations ---
def get_product_from_db(url):
    """Fetches product record from DB by URL."""
    if not db_connection:
        return None
    try:
        local_cursor = db_connection.cursor()
        local_cursor.execute("SELECT name, target_price, last_price FROM products WHERE url = ?", (url,))
        result = local_cursor.fetchone()
        local_cursor.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Error retrieving product {url} from DB: {e}")
        return None

def update_product_in_db(url, name, target_price, current_price):
    """Inserts or updates a product in the database."""
    if not db_connection:
        return
    timestamp = datetime.now().isoformat()
    try:
        local_cursor = db_connection.cursor()
        local_cursor.execute("""
            INSERT INTO products (url, name, target_price, last_price, last_check_timestamp)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                name = excluded.name,
                target_price = excluded.target_price,
                last_price = excluded.last_price,
                last_check_timestamp = excluded.last_check_timestamp;
        """, (url, name, target_price, current_price, timestamp))
        db_connection.commit()
        logger.debug(f"DB updated for {url} at price {current_price}")
    except sqlite3.Error as e:
        logger.error(f"DB update failed for {url}: {e}")
    finally:
        if local_cursor:
            local_cursor.close()

# --- Price Check Core Logic ---
def check_price(product_config):
    """Performs the price check, sends alert if applicable, and updates DB."""
    url = product_config.get('url')
    name_config = product_config.get('name', 'Unknown Product')
    target_price = product_config.get('target_price')
    price_selector = product_config.get('price_selector')
    name_selector = product_config.get('name_selector')  # Optional

    if not url or not target_price or not price_selector:
        logger.warning(f"Invalid config: missing fields for {name_config}")
        return

    user_agent = config_data.get('user_agent', 'Mozilla/5.0')
    wait_time = config_data.get('selenium_wait_time', 20)

    html = scraper.fetch_html_with_selenium(url, user_agent, price_selector, wait_time)
    if not html:
        logger.error(f"HTML fetch failed for {name_config} ({url})")
        return

    current_price = scraper.parse_price(html, price_selector)
    if current_price is None:
        logger.error(f"Price parsing failed for {name_config}")
        return

    parsed_name = scraper.parse_product_name(html, name_selector)
    display_name = parsed_name if parsed_name else name_config

    db_data = get_product_from_db(url)
    last_price = db_data[2] if db_data else None

    logger.info(f"Check: '{display_name}' | Current: {current_price} | Target: {target_price} | Last: {last_price}")

    # --- Alert Decision Logic ---
    alert_needed = False
    alert_reason = ""

    if current_price <= target_price:
        if last_price is None or current_price <= last_price:
            alert_needed = True
            alert_reason = f"Price {current_price} is below target {target_price} and dropped from {last_price}!"
        else:
            logger.info("Below target, but not lower than last recorded. No alert.")
    elif last_price is not None and current_price <= last_price:
        logger.info("Price dropped, but above target. No alert.")

    if alert_needed:
        logger.warning(f"ALERT! {alert_reason}")
        subject = f"Price Alert: {display_name} is now {current_price}!"
        body = (
            f"Price drop detected for '{display_name}'!\n\n"
            f"Current Price: {current_price}\n"
            f"Target Price: {target_price}\n"
            f"Last Known Price: {last_price}\n\n"
            f"URL: {url}"
        )
        threading.Thread(
            target=alert_utils.send_email_alert,
            args=(subject, body, config_data),
            daemon=True
        ).start()

    update_product_in_db(url, display_name, target_price, current_price)

# --- Scheduler ---
def run_price_checks():
    """Executes price check for all configured products."""
    logger.info("--- Running scheduled price checks ---")
    products = config_data.get('products', [])
    if not products:
        logger.warning("No products configured for monitoring.")
        return

    delay = config_data.get('request_delay_seconds', 10)

    for i, product_config in enumerate(products):
        if i > 0:
            logger.debug(f"Waiting {delay}s before next check...")
            time.sleep(delay)
        try:
            check_price(product_config)
        except Exception as e:
            logger.error(f"Error checking {product_config.get('url')}: {e}", exc_info=True)

    logger.info("--- Completed price check batch ---")

# --- Main Application Entrypoint ---
def main():
    """Main lifecycle function: load config, setup, schedule, run."""
    load_config(CONFIG_FILE)
    setup_logging()
    logger.info("--- Starting Price Tracker ---")
    initialize_db()

    interval = config_data.get('schedule_interval_minutes', 60)

    if interval <= 0:
        logger.warning("Schedule interval invalid. Running once.")
        run_price_checks()
        logger.info("--- Finished Single Run ---")
        if db_connection: db_connection.close()
        return

    logger.info(f"Scheduling checks every {interval} minutes.")
    schedule.every(interval).minutes.do(run_price_checks)

    logger.info("Running initial check before scheduler loop...")
    run_price_checks()

    logger.info("Entering main scheduler loop. Press Ctrl+C to exit.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Graceful shutdown requested.")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
            logger.info("Retrying after 60 seconds...")
            time.sleep(60)

    if db_connection:
        logger.info("Closing DB connection.")
        db_connection.close()
    logger.info("--- Price Tracker Shut Down ---")

if __name__ == "__main__":
    main()
