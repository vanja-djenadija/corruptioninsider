"""
BA Company Registry (Republika Srpska) ETL Pipeline – Standalone Starter
"""

import sys
from pathlib import Path

# Add data-pipeline directory to path BEFORE importing app modules
_data_pipeline_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_data_pipeline_dir))

import argparse
import logging

from app.config.config import ConfigLoader
from app.pipeline.extract.ba.company_registry_rs_scraper import BACompanyRegistryRSScraper
from app.pipeline.load.import_companies import import_companies_from_json, get_company_count
from app.pipeline.execution_tracker import ExecutionTracker
from app.util.paths import resolve_path

logger = logging.getLogger(__name__)

SCRAPER_NAME = "ba_company_registry_rs"


def setup_logging(log_directory: str) -> None:
    """Configure logging with file and console handlers."""
    log_dir = resolve_path(log_directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler()
        ]
    )


def run_pipeline(load_to_db: bool):
    config = ConfigLoader.load("ba_company_registry_rs_config.json")
    database_url = config.get("database_url")

    logger.info("Starting BA Company Registry (RS) ETL pipeline")

    # Extract (no detail endpoint for RS)
    scraper = BACompanyRegistryRSScraper(config)
    output_path = scraper.run_full_export(fetch_details=False)

    if not output_path:
        raise RuntimeError("Failed to export RS data")

    logger.info("Exported data to: %s", output_path)

    # Load
    if load_to_db:
        with ExecutionTracker(database_url, SCRAPER_NAME, source_country="BA") as tracker:
            tracker.set_parameters({"load_to_db": load_to_db})
            tracker.set_output_file(str(output_path))

            logger.info("Loading data into database...")
            stats = import_companies_from_json(
                json_path=str(output_path),
                database_url=database_url,
                source="rs"
            )

            tracker.set_records_fetched(stats.get("total_in_file", 0))
            tracker.set_records_inserted(stats.get("companies_inserted", 0))
            tracker.set_records_skipped(stats.get("companies_skipped", 0))

            logger.info("Import stats: %s", stats)
            logger.info("Total companies in database: %s", f"{get_company_count(database_url):,}")

    logger.info("Pipeline finished successfully")


def main():
    parser = argparse.ArgumentParser("BA Company Registry (RS) ETL")
    parser.add_argument("--no-load", action="store_true", help="Skip loading to database")
    args = parser.parse_args()

    run_pipeline(load_to_db=not args.no_load)


if __name__ == "__main__":
    config = ConfigLoader.load("ba_company_registry_rs_config.json")
    setup_logging(config.get("log_directory", "data/logs"))
    main()
