"""
BA Awards ETL Pipeline – Starter (Orchestrator only)
"""

import sys
from pathlib import Path

# Add data-pipeline directory to path BEFORE importing app modules
_data_pipeline_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_data_pipeline_dir))

import argparse
import logging

from app.config.config import ConfigLoader
from app.pipeline.extract.ba.awards_scraper import BAwardsScraper
from app.pipeline.transform.xlsx_to_csv_converter import XlsxToCsvConverter
from app.pipeline.load.import_csv_to_raw import import_csv_files, get_row_count
from app.pipeline.execution_tracker import ExecutionTracker
from app.pipeline.transform.normalize_awards import normalize_awards, clear_normalized_tables
from app.util.paths import resolve_path

logger = logging.getLogger(__name__)

SCRAPER_NAME = "ba_awards"


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


def run_pipeline(convert_to_csv: bool, load_to_db: bool, normalize: bool, clear_normalized: bool = False):
    config = ConfigLoader.load("ba_awards_config.json")
    database_url = config.get("database_url")

    logger.info("Starting BA Awards ETL pipeline")

    with ExecutionTracker(database_url, SCRAPER_NAME, source_country="BA") as tracker:
        tracker.set_parameters({
            "convert_to_csv": convert_to_csv,
            "load_to_db": load_to_db,
            "from_date": config.get("from_date"),
            "to_date": config.get("to_date")
        })

        # Extract
        xlsx_path = BAwardsScraper(config).run()
        logger.info(f"Downloaded: {xlsx_path}")
        tracker.set_output_file(str(xlsx_path))

        # Transform
        csv_path = None
        if convert_to_csv:
            csv_path = XlsxToCsvConverter(config).convert_file(xlsx_path)
            logger.info(f"Converted to CSV: {csv_path}")

        # Load
        if load_to_db:
            logger.info("Loading data into database...")
            stats = import_csv_files(
                folder_path=config.get("processed_directory"),
                source_country=config.get("source_country", "BA"),
                source_system=config.get("source_system", "EJN"),
                database_url=database_url
            )

            tracker.set_records_fetched(stats.get("total_rows", 0))
            tracker.set_records_inserted(stats.get("total_rows", 0))

            logger.info(f"Imported {stats['total_rows']} rows from {stats['successful']} file(s)")
            logger.info(f"Total records in award_raw: {get_row_count(database_url):,}")

    logger.info("Pipeline finished successfully")


def main():
    parser = argparse.ArgumentParser("BA Awards ETL")
    parser.add_argument("--no-convert", action="store_true", help="Skip CSV conversion")
    parser.add_argument("--no-load", action="store_true", help="Skip loading to database")
    parser.add_argument("--no-normalize", action="store_true", help="Skip normalization step")
    parser.add_argument("--clear-normalized", action="store_true", help="Clear normalized tables before re-normalizing")
    args = parser.parse_args()

    run_pipeline(
        convert_to_csv=not args.no_convert,
        load_to_db=not args.no_load,
        normalize=not args.no_normalize,
        clear_normalized=args.clear_normalized
    )


if __name__ == "__main__":
    config = ConfigLoader.load("ba_awards_config.json")
    setup_logging(config.get("log_directory", "data/logs"))
    main()
