"""
BA Company Registry ETL Pipeline – Starter (Orchestrator only)
Supports FIA (FBiH) and RS (Republika Srpska) sources.
"""

import sys
from pathlib import Path

# Add data-pipeline directory to path BEFORE importing app modules
_data_pipeline_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_data_pipeline_dir))

import argparse
import logging

from app.config.config import ConfigLoader
from app.pipeline.extract.ba.company_registry_scraper import BACompanyRegistryScraper
from app.pipeline.extract.ba.company_registry_rs_scraper import BACompanyRegistryRSScraper
from app.pipeline.load.import_companies import import_companies_from_json, get_company_count
from app.pipeline.execution_tracker import ExecutionTracker
from app.util.paths import resolve_path

logger = logging.getLogger(__name__)

SCRAPER_NAME_FIA = "ba_company_registry"
SCRAPER_NAME_RS = "ba_company_registry_rs"


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


def run_fia_pipeline(load_to_db: bool, year: int) -> None:
    """Run FIA (FBiH) extraction and optional DB load."""
    config = ConfigLoader.load("ba_company_registry_config.json")
    database_url = config.get("database_url")

    logger.info("Starting FIA (FBiH) Company Registry extraction")

    scraper = BACompanyRegistryScraper(config)
    output_path = scraper.run_full_export(year=year)

    if not output_path:
        raise RuntimeError("Failed to export FIA data")

    logger.info("FIA data exported to: %s", output_path)

    if load_to_db:
        with ExecutionTracker(database_url, SCRAPER_NAME_FIA, source_country="BA") as tracker:
            tracker.set_parameters({"year": year, "load_to_db": load_to_db})
            tracker.set_output_file(str(output_path))

            logger.info("Loading FIA data into database...")
            stats = import_companies_from_json(
                json_path=str(output_path),
                database_url=database_url,
                source="fia"
            )

            tracker.set_records_fetched(stats.get("total_in_file", 0))
            tracker.set_records_inserted(stats.get("companies_inserted", 0))
            tracker.set_records_skipped(stats.get("companies_skipped", 0))

            logger.info("FIA import stats: %s", stats)
            logger.info("Total companies in database: %s", f"{get_company_count(database_url):,}")


def run_rs_pipeline(load_to_db: bool) -> None:
    """Run RS (Republika Srpska) extraction and optional DB load."""
    config = ConfigLoader.load("ba_company_registry_rs_config.json")
    database_url = config.get("database_url")

    logger.info("Starting RS (Republika Srpska) Company Registry extraction")

    scraper = BACompanyRegistryRSScraper(config)
    output_path = scraper.run_full_export(fetch_details=False)

    if not output_path:
        raise RuntimeError("Failed to export RS data")

    logger.info("RS data exported to: %s", output_path)

    if load_to_db:
        with ExecutionTracker(database_url, SCRAPER_NAME_RS, source_country="BA") as tracker:
            tracker.set_parameters({"load_to_db": load_to_db})
            tracker.set_output_file(str(output_path))

            logger.info("Loading RS data into database...")
            stats = import_companies_from_json(
                json_path=str(output_path),
                database_url=database_url,
                source="rs"
            )

            tracker.set_records_fetched(stats.get("total_in_file", 0))
            tracker.set_records_inserted(stats.get("companies_inserted", 0))
            tracker.set_records_skipped(stats.get("companies_skipped", 0))

            logger.info("RS import stats: %s", stats)
            logger.info("Total companies in database: %s", f"{get_company_count(database_url):,}")


def run_pipeline(load_to_db: bool, year: int, source: str):
    logger.info("Starting BA Company Registry ETL pipeline (source=%s)", source)

    if source in ("fia", "all"):
        try:
            run_fia_pipeline(load_to_db, year)
        except Exception as e:
            if source == "all":
                logger.warning("FIA pipeline failed (non-blocking): %s", e)
            else:
                raise

    if source in ("rs", "all"):
        try:
            run_rs_pipeline(load_to_db)
        except Exception as e:
            if source == "all":
                logger.warning("RS pipeline failed (non-blocking): %s", e)
            else:
                raise

    logger.info("Pipeline finished successfully")


def main():
    parser = argparse.ArgumentParser("BA Company Registry ETL")
    parser.add_argument("--no-load", action="store_true", help="Skip loading to database")
    parser.add_argument("--year", type=int, default=2025, help="Year to export data for (default: 2025)")
    parser.add_argument(
        "--source",
        choices=["fia", "rs", "all"],
        default="all",
        help="Which source to scrape: fia, rs, or all (default: all)"
    )
    args = parser.parse_args()

    run_pipeline(
        load_to_db=not args.no_load,
        year=args.year,
        source=args.source
    )


if __name__ == "__main__":
    config = ConfigLoader.load("ba_company_registry_config.json")
    setup_logging(config.get("log_directory", "data/logs"))
    main()
