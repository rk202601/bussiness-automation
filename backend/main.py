"""
main.py — Entry point for the Google Maps Lead Scraper.

Orchestrates configuration loading, scraping, and Firestore insertion.
"""

import gc
import logging
import random
import sys
import time

from config import Config
from scraper import GoogleMapsScraper
from firestore import FirestoreManager


def setup_logging() -> None:
    """Configure logging to console and a timestamped file inside logs/."""
    import os
    from datetime import datetime

    log_format = "%(asctime)s  %(levelname)-8s  %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Create logs/ folder if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Timestamped log filename — one file per execution
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(logs_dir, f"scraper_{timestamp}.log")

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_format, date_format))
    root.addHandler(console)

    # File handler — writes to logs/scraper_YYYY-MM-DD_HH-MM-SS.log
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root.addHandler(file_handler)

    # Log the file path so user knows where logs are saved
    logging.getLogger(__name__).info("Log file: %s", log_file)


BATCH_SIZE      = 10   # Save to Firestore every N leads
BROWSER_RESTART = 20   # Restart browser every N leads extracted (frees RAM)


def _save_in_batches(
    db: FirestoreManager,
    leads: list,
    grand_total: int,
    grand_added: int,
    grand_duplicates: int,
    logger: logging.Logger,
) -> tuple[int, int, int]:
    """Split leads into BATCH_SIZE chunks, save each to Firestore with log banners."""
    for i in range(0, len(leads), BATCH_SIZE):
        chunk = leads[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        logger.info("")
        logger.info("  +-------------------------------------------------+")
        logger.info("  |  [DB] Saving batch #%d (%d leads) to Firebase...", batch_num, len(chunk))
        logger.info("  +-------------------------------------------------+")
        try:
            result = db.add_leads(chunk)
            grand_total     += result["total"]
            grand_added     += result["added"]
            grand_duplicates += result["duplicates"]
            logger.info("  |  [DB] Saved! added=%d  duplicates=%d", result["added"], result["duplicates"])
            logger.info("  +-------------------------------------------------+")
            logger.info("")
        except Exception:
            logger.exception("  [DB] Failed to save batch #%d.", batch_num)
            grand_total += len(chunk)
    return grand_total, grand_added, grand_duplicates


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("  Google Maps Lead Scraper - Starting")
    logger.info("=" * 60)

    # ── 1. Load configuration ────────────────────────────────
    try:
        config = Config()
    except SystemExit:
        return

    logger.info("Configuration loaded:\n%s", config.summary())

    total_combinations = len(config.TARGET_CITIES) * len(config.SEARCH_KEYWORDS)
    logger.info("Will process %d city x keyword combinations.", total_combinations)

    # ── 2. Connect to Firestore ──────────────────────────────
    try:
        db = FirestoreManager(
            credentials_file=config.FIREBASE_CREDENTIALS_FILE,
            collection_name=config.FIRESTORE_COLLECTION,
        )
    except Exception:
        logger.exception("Failed to connect to Firestore. Aborting.")
        return

    # ── 3. Scrape and insert ─────────────────────────────────
    grand_total         = 0
    grand_added         = 0
    grand_duplicates    = 0
    start_time          = time.time()
    leads_since_restart = 0   # cumulative extracted since last browser restart
    pending_batch: list = []  # live buffer of unsaved leads (flushed to Firestore every 10 leads)

    scraper = GoogleMapsScraper(
        headless=config.HEADLESS,
        scroll_pause=config.SCROLL_PAUSE_SEC,
        action_delay=config.ACTION_DELAY_SEC,
    )

    def handle_new_lead(lead) -> None:
        nonlocal grand_total, grand_added, grand_duplicates, leads_since_restart, pending_batch
        pending_batch.append(lead)
        leads_since_restart += 1

        # ── Save batch to Firestore every BATCH_SIZE (10) leads ──
        if len(pending_batch) >= BATCH_SIZE:
            grand_total, grand_added, grand_duplicates = _save_in_batches(
                db, pending_batch, grand_total, grand_added, grand_duplicates, logger
            )
            pending_batch.clear()

        # ── Restart browser every BROWSER_RESTART (20) leads ──
        if leads_since_restart >= BROWSER_RESTART:
            logger.info("")
            logger.info("  +==================================================+")
            logger.info("  |  [BROWSER] %d leads done — restarting browser    |", leads_since_restart)
            logger.info("  |  Closing browser, killing zombies & clearing RAM |")
            logger.info("  +==================================================+")
            try:
                scraper.stop()
            except Exception:
                pass
            gc.collect()
            time.sleep(3)
            scraper.start()
            leads_since_restart = 0
            logger.info("  |  [BROWSER] Browser restarted & RAM/zombies cleared|")
            logger.info("  +==================================================+")
            logger.info("")

    try:
        scraper.start()

        for city_idx, city in enumerate(config.TARGET_CITIES, 1):
            for kw_idx, keyword in enumerate(config.SEARCH_KEYWORDS, 1):
                combo = f"[{city_idx}/{len(config.TARGET_CITIES)}] [{kw_idx}/{len(config.SEARCH_KEYWORDS)}]"
                query = f"{keyword} in {city}"
                logger.info("")
                logger.info("-" * 60)
                logger.info("%s  Searching: %s", combo, query)
                logger.info("-" * 60)

                try:
                    leads = scraper._search_and_extract(
                        keyword=keyword,
                        city=city,
                        state=config.TARGET_STATE,
                        on_lead=handle_new_lead,
                    )
                except Exception:
                    logger.exception("Scraping failed for '%s' — continuing to next.", query)
                    continue

                if not leads:
                    logger.info("No leads found for '%s'.", query)
                    continue

                # Flush any remaining leads from this query batch (e.g. if query had 15 leads, flush the last 5)
                if pending_batch:
                    grand_total, grand_added, grand_duplicates = _save_in_batches(
                        db, pending_batch, grand_total, grand_added, grand_duplicates, logger
                    )
                    pending_batch.clear()

    except KeyboardInterrupt:
        logger.info("")
        logger.info("  +==================================================+")
        logger.info("  |  [CTRL+C] Interrupted by user.                   |")

        if pending_batch:
            logger.info("  |  Storing %d remaining entries to Firestore...    |", len(pending_batch))
            logger.info("  +==================================================+")
            logger.info("")
            grand_total, grand_added, grand_duplicates = _save_in_batches(
                db, pending_batch, grand_total, grand_added, grand_duplicates, logger
            )
            pending_batch.clear()
            logger.info("")
            logger.info("  +==================================================+")
            logger.info("  |  [CTRL+C] All entries saved. Exiting safely.     |")
            logger.info("  +==================================================+")
        else:
            logger.info("  |  No unsaved entries in buffer. Exiting.          |")
            logger.info("  +==================================================+")

        logger.info("")

    finally:
        try:
            scraper.stop()
        except Exception:
            pass  # Ignore browser close errors on interrupt

    # ── 4. Summary ───────────────────────────────────────────
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    logger.info("")
    logger.info("=" * 60)
    logger.info("  FINAL SUMMARY")
    logger.info("=" * 60)
    logger.info("  Total leads found:      %d", grand_total)
    logger.info("  New leads added:        %d", grand_added)
    logger.info("  Duplicates skipped:     %d", grand_duplicates)
    logger.info("  Time elapsed:           %dm %ds", minutes, seconds)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
