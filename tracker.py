# -*- coding: utf-8 -*-
"""
Main application script for the E-commerce Price Tracker.
Fetches product pages, parses prices, checks against targets/history,
sends alerts, and schedules periodic checks.
"""

import logging
import sys
import time
import yaml # Requires PyYAML
import schedule
import sqlite3
from pathlib import Path
from datetime import datetime

# Import utility functions
try:
    import config # Assuming config loads yaml or has constants
    import scraper
    import alert_utils
except ImportError as e:
    print(f"[CRITICAL ERROR] Failed to import required modules: {e}")
    sys.exit(1)

# --- Global Variables ---
CONFIG_FILE = 'config.yaml'
config_data = {}
db_connection = None
db_cursor = None

# --- Logging Setup ---
# Note: Configure logging basicConfig *before* any logging calls
def setup_logging():
    """Configures logging based on config file."""
    log_level_str = config_data.get('log_level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_file = Path(config_data.get('log_file', 'logs/price_tracker.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True) # Ensure log dir exists

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Suppress noisy logs from libraries if needed
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.info("Logging configured.")

# --- Configuration Loading ---
def load_config(config_path):
    """Loads configuration from a YAML file."""
    global config_data
    logger.info(f"Loading configuration from {config_path}...")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        if not config_data:
            logger.critical(f"Config file {config_path} is empty or invalid.")
            sys.exit(1)
        logger.info("Configuration loaded successfully.")
        # Basic validation (example)
        if 'products' not in config_data or not config_data['products']:
             logger.warning("No products found in configuration!")
        if 'user_agent' not in config_data:
             logger.warning("User-Agent not specified in configuration!")

    except FileNotFoundError:
        logger.critical(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.critical(f"Error parsing configuration file {config_path}: {e}")
        sys.exit(1)
    except Exception as e:
         logger.critical(f"Unexpected error loading config: {e}", exc_info=True)
         sys.exit(1)


# --- Database Setup & Operations ---
def initialize_db():
    """Initializes the SQLite database and table if they don't exist."""
    global db_connection, db_cursor
    db_path = Path(config_data.get('database_file', 'data/product_prices.db'))
    db_path.parent.mkdir(parents=True, exist_ok=True) # Ensure data dir exists
    logger.info(f"Initializing database at: {db_path}")
    try:
        db_connection = sqlite3.connect(str(db_path))
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
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.critical(f"Database error during initialization: {e}")
        sys.exit(1)

def get_product_from_db(url):
    """Retrieves product data (including last price) from the database."""
    if not db_cursor: return None
    try:
        db_cursor.execute("SELECT name, target_price, last_price FROM products WHERE url = ?", (url,))
        return db_cursor.fetchone() # Returns (name, target, last) or None
    except sqlite3.Error as e:
        logger.error(f"Database error getting product {url}: {e}")
        return None

def update_product_in_db(url, name, target_price, current_price):
    """Updates or inserts product data into the database."""
    if not db_connection or not db_cursor: return
    timestamp = datetime.now().isoformat()
    try:
        # Use INSERT OR REPLACE (or separate INSERT and UPDATE)
        db_cursor.execute("""
            INSERT INTO products (url, name, target_price, last_price, last_check_timestamp)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                name = excluded.name,
                target_price = excluded.target_price,
                last_price = excluded.last_price,
                last_check_timestamp = excluded.last_check_timestamp;
        """, (url, name, target_price, current_price, timestamp))
        db_connection.commit()
        logger.debug(f"Database updated for {url} with price {current_price}")
    except sqlite3.Error as e:
        logger.error(f"Database error updating product {url}: {e}")

# --- Main Price Checking Logic ---
def check_price(product_config):
    """Checks the price for a single product and sends alert if needed."""
    url = product_config.get('url')
    name_config = product_config.get('name', 'Unknown Product') # Use config name as default
    target_price = product_config.get('target_price')
    price_selector = product_config.get('price_selector')
    name_selector = product_config.get('name_selector') # Optional

    if not url or not target_price or not price_selector:
        logger.warning(f"Skipping product due to missing config (url, target_price, or price_selector): {name_config}")
        return

    user_agent = config_data.get('user_agent', 'Mozilla/5.0') # Default UA if not set
    delay = config_data.get('request_delay_seconds', 10)

    html = scraper.fetch_html(url, user_agent, delay)
    if not html:
        logger.error(f"Failed to fetch HTML for {name_config} ({url}). Skipping check.")
        # Consider adding retry logic here for robustness
        return

    current_price = scraper.parse_price(html, price_selector)
    if current_price is None:
        logger.error(f"Failed to parse price for {name_config} ({url}). Skipping check.")
        # Maybe website structure changed? Log this clearly.
        return

    # Get name from page if selector provided, otherwise use config name
    parsed_name = scraper.parse_product_name(html, name_selector)
    display_name = parsed_name if parsed_name else name_config

    # Get last known price from DB
    db_data = get_product_from_db(url)
    last_price = db_data[2] if db_data and db_data[2] is not None else None

    logger.info(f"Checked '{display_name}': Current Price={current_price}, Target={target_price}, Last Known={last_price}")

    # --- Alert Logic ---
    alert_needed = False
    alert_reason = ""

    # Condition 1: Price dropped below target *and* is lower than the last known price (if available)
    if current_price < target_price:
        if last_price is None or current_price < last_price:
             alert_needed = True
             alert_reason = f"Price dropped below target ({target_price}) and last known price ({last_price})!"
        else:
             logger.info(f"Price ({current_price}) is below target ({target_price}), but not lower than last known ({last_price}). No alert.")
    # Condition 2: Alert if price dropped significantly since last check, even if not below target yet? (Optional)
    # elif last_price is not None and current_price < last_price * 0.9: # e.g., 10% drop
    #    alert_needed = True
    #    alert_reason = f"Price dropped significantly since last check (from {last_price})!"

    if alert_needed:
        logger.warning(f"ALERT! Price drop for '{display_name}'. {alert_reason}")
        subject = f"Price Alert: {display_name}"
        body = (f"Price drop detected for '{display_name}'!\n\n"
                f"Current Price: {current_price}\n"
                f"Target Price: {target_price}\n"
                f"Last Price: {last_price}\n"
                f"Reason: {alert_reason}\n\n"
                f"URL: {url}")
        # Run alert sending in a separate thread to avoid blocking checks
        alert_thread = threading.Thread(
             target=alert_utils.send_email_alert,
             args=(subject, body, config_data), # Pass global config
             daemon=True)
        alert_thread.start()

    # --- Update Database ---
    # Update DB regardless of alert, to store the current price as the new 'last_price'
    update_product_in_db(url, display_name, target_price, current_price)


# --- Job Scheduler Function ---
def run_price_checks():
    """Runs the price check for all configured products."""
    logger.info("Starting scheduled price checks...")
    products = config_data.get('products', [])
    if not products:
        logger.warning("No products configured to check.")
        return

    for product_config in products:
        try:
            check_price(product_config)
            # Note: The delay *between* requests is handled inside scraper.fetch_html
        except Exception as e:
            # Catch errors during a single product check to allow others to run
            logger.error(f"Unexpected error checking product {product_config.get('url')}: {e}", exc_info=True)

    logger.info("Finished scheduled price checks.")


# --- Main Execution ---
def main():
    """Loads config, initializes DB, schedules job, and runs scheduler."""
    # Load config first to get logging settings
    load_config(CONFIG_FILE)
    # Now setup logging based on loaded config
    setup_logging()

    logger.info("--- Price Tracker Application Starting ---")
    initialize_db()

    # Schedule the job
    interval = config_data.get('schedule_interval_minutes', 60)
    logger.info(f"Scheduling price checks to run every {interval} minutes.")
    schedule.every(interval).minutes.do(run_price_checks)

    # Run the check once immediately on startup
    logger.info("Running initial price check...")
    run_price_checks()

    # Keep the script running to execute scheduled jobs
    logger.info("Entering main scheduling loop. Press Ctrl+C to exit.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1) # Check every second if job is due
        except KeyboardInterrupt:
            logger.info("Ctrl+C detected. Shutting down scheduler...")
            break
        except Exception as e:
             logger.error(f"Error in main scheduling loop: {e}", exc_info=True)
             # Decide whether to break or continue after an error
             time.sleep(60) # Wait a bit before retrying loop

    # --- Cleanup ---
    if db_connection:
        logger.info("Closing database connection.")
        db_connection.close()
    logger.info("--- Price Tracker Application Stopped ---")


if __name__ == "__main__":
    main()