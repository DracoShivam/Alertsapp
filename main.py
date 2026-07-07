import os
import sys
import json
import logging
import argparse
from dotenv import load_dotenv

from scrapers import get_scraper
from notifiers import get_notifier

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)
logger = logging.getLogger("job_tracker")

def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_state(state_path: str) -> dict:
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading state file {state_path}, initializing fresh: {e}")
    return {"seen_job_ids": []}

def save_state(state_path: str, state: dict):
    try:
        # Keep only the last 1000 IDs to avoid infinite file growth
        state["seen_job_ids"] = state["seen_job_ids"][-1000:]
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        logger.info(f"State saved to {state_path}")
    except Exception as e:
        logger.error(f"Failed to save state to {state_path}: {e}")

def main():
    # Load environment variables from .env
    load_dotenv(override=True)

    parser = argparse.ArgumentParser(description="Extensible Job Tracker Bot")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    parser.add_argument("--state", default="state.json", help="Path to state.json")
    parser.add_argument("--dry-run", action="store_true", help="Print matching jobs without sending alerts or saving state")
    parser.add_argument("--force", action="store_true", help="Alert on all matching jobs, ignoring state database")
    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception:
        return

    # Load state
    state = load_state(args.state)
    seen_ids = set(state.get("seen_job_ids", []))
    if args.force:
        seen_ids = set()

    sources = config.get("sources", [])
    if not sources:
        logger.warning("No job sources configured in config.json. Exiting.")
        return

    # Fetch jobs from all sources
    all_new_jobs_by_source = {}
    new_jobs_count = 0

    for source in sources:
        name = source.get("name", "Unknown Source")

        # Allow sources to be disabled via config
        if not source.get("enabled", True):
            logger.info(f"Skipping disabled source: '{name}'")
            continue

        scraper_type = source.get("type")
        url = source.get("url")
        filters = source.get("filters", {})
        selectors = source.get("selectors")  # Used by generic_html

        if not scraper_type or not url:
            logger.error(f"Invalid source config for {name}. Missing 'type' or 'url'.")
            continue

        try:
            scraper = get_scraper(scraper_type)
        except ValueError as e:
            logger.error(f"Failed to resolve scraper for {name}: {e}")
            continue

        # Scrape
        logger.info(f"Processing source '{name}' ({scraper_type})")
        if scraper_type == "generic_html":
            jobs = scraper.scrape(url, filters, selectors=selectors)
        else:
            jobs = scraper.scrape(url, filters)

        # Find new jobs
        new_jobs = []
        for job in jobs:
            job_id = job.get("id")
            if job_id not in seen_ids:
                new_jobs.append(job)
                
        if new_jobs:
            all_new_jobs_by_source[name] = new_jobs
            new_jobs_count += len(new_jobs)
            logger.info(f"[{name}] Found {len(new_jobs)} new matching positions!")
        else:
            logger.info(f"[{name}] No new matching positions found.")

    if new_jobs_count == 0:
        logger.info("No new jobs found across all sources. Nothing to alert.")
        return

    # Deliver notifications
    if args.dry_run:
        logger.info("--- DRY RUN MODE ---")
        for source_name, jobs in all_new_jobs_by_source.items():
            print(f"\n[Source: {source_name}]")
            for job in jobs:
                print(f" - {job['title']} ({job['department']}) @ {job['location']}")
                print(f"   Link: {job['link']}")
        return

    # Setup notifiers
    active_notifiers = []
    notifier_configs = config.get("notifications", {})
    
    for notifier_name, notifier_settings in notifier_configs.items():
        if notifier_settings.get("enabled", False):
            try:
                notifier = get_notifier(notifier_name, notifier_settings)
                active_notifiers.append(notifier)
                logger.info(f"Enabled notifier: {notifier.name}")
            except Exception as e:
                logger.error(f"Failed to initialize notifier {notifier_name}: {e}")

    if not active_notifiers:
        logger.warning("No notification channels enabled in config.json. Printing new jobs to console:")
        for source_name, jobs in all_new_jobs_by_source.items():
            print(f"\n[Source: {source_name}]")
            for job in jobs:
                print(f" - {job['title']} ({job['department']}) | {job['link']}")
        # Still update state to avoid printing again
        for source_name, jobs in all_new_jobs_by_source.items():
            for job in jobs:
                state["seen_job_ids"].append(job["id"])
        save_state(args.state, state)
        return

    # Send notifications
    for source_name, jobs in all_new_jobs_by_source.items():
        for notifier in active_notifiers:
            try:
                notifier.send_notification(jobs, source_name)
            except Exception as e:
                logger.error(f"Notifier {notifier.name} failed to deliver for {source_name}: {e}")

        # Update state for successfully processed jobs
        for job in jobs:
            state["seen_job_ids"].append(job["id"])

    # Persist state
    save_state(args.state, state)
    logger.info("Job tracking run completed successfully.")

if __name__ == "__main__":
    main()
