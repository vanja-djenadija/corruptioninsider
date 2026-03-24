"""
XLSX to CSV converter with support for structured directory layouts.
Converts procurement data files while preserving directory structure.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from ...util.paths import resolve_path

logger = logging.getLogger(__name__)


class XlsxToCsvConverter:
    """
    Converts XLSX files to CSV format while preserving directory structure.
    """

    def __init__(self, config: Dict) -> None:
        """
        Initialize the converter.

        Args:
            config: Configuration dictionary from ConfigLoader
        """
        self.config = config

        # Resolve paths relative to data-pipeline root
        self.raw_dir = resolve_path(config.get("raw_directory", "data/raw"))
        self.processed_dir = resolve_path(config.get("processed_directory", "data/processed"))

        # Ensure output directory exists
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Converter initialized:")
        logger.info(f"  Raw directory: {self.raw_dir}")
        logger.info(f"  Processed directory: {self.processed_dir}")


    def find_xlsx_files(
        self,
        country: Optional[str] = None,
        data_type: Optional[str] = None,
        pattern: Optional[str] = None,
    ) -> List[Path]:
        """
        Find XLSX files, optionally filtered by country and/or data type.

        Args:
            country: Filter by country code (e.g., 'ba', 'rs')
            data_type: Filter by data type (e.g., 'awards', 'contracts')
            pattern: Custom glob pattern (overrides country/data_type)

        Returns:
            List of Path objects for found XLSX files
        """
        if pattern:
            search_pattern = pattern
        elif country and data_type:
            search_pattern = f"{country}/{data_type}/procurement-*.xlsx"
        elif country:
            search_pattern = f"{country}/**/procurement-*.xlsx"
        elif data_type:
            search_pattern = f"**/{data_type}/procurement-*.xlsx"
        else:
            search_pattern = "**/procurement-*.xlsx"

        files = sorted(self.raw_dir.glob(search_pattern))
        logger.info(f"Found {len(files)} XLSX files matching pattern: {search_pattern}")
        return files

    def is_converted(self, xlsx_path: Path) -> bool:
        """
        Check if an XLSX file has already been converted to CSV.

        Args:
            xlsx_path: Path to the XLSX file

        Returns:
            True if a corresponding CSV file exists
        """
        csv_path = self._get_csv_path(xlsx_path)
        return csv_path.exists()

    def _get_csv_path(self, xlsx_path: Path) -> Path:
        """
        Generate the output CSV path while preserving directory structure.

        Args:
            xlsx_path: Path to the XLSX file

        Returns:
            Path where the CSV file should be saved
        """
        # Get relative path from raw directory
        try:
            relative_path = xlsx_path.relative_to(self.raw_dir)
        except ValueError:
            # If file is not under raw_dir, just use the filename
            relative_path = Path(xlsx_path.name)

        # Change extension to .csv
        csv_relative_path = relative_path.with_suffix(".csv")

        # Build full output path
        csv_path = self.processed_dir / csv_relative_path

        return csv_path

    @staticmethod
    def _get_metadata_path(csv_path: Path) -> Path:
        """
        Generate the metadata file path for a CSV file.

        Args:
            csv_path: Path to the CSV file

        Returns:
            Path where the metadata JSON should be saved
        """
        return csv_path.with_suffix(".json")

    def convert_file(
        self,
        xlsx_path: Path,
        force: bool = False,
        validate: bool = True,
    ) -> Optional[Path]:
        """
        Convert a single XLSX file to CSV.

        Args:
            xlsx_path: Path to the XLSX file
            force: If True, reconvert even if CSV already exists
            validate: If True, perform data validation

        Returns:
            Path to the created CSV file, or None if conversion failed
        """
        try:
            # Check if already converted
            if not force and self.is_converted(xlsx_path):
                logger.info(f"Skipping (already converted): {xlsx_path.name}")
                return None

            logger.info(f"Converting: {xlsx_path}")

            # Read XLSX
            df = pd.read_excel(xlsx_path, engine="openpyxl")
            initial_rows = len(df)
            initial_cols = len(df.columns)

            logger.info(f"  Loaded {initial_rows} rows, {initial_cols} columns")

            # Data cleaning
            df = df.dropna(how="all")
            final_rows = len(df)

            removed_rows = initial_rows - final_rows
            if removed_rows > 0:
                logger.warning(f"  Removed {removed_rows} empty rows")

            # Optional validation
            validation_warnings = []
            if validate:
                validation_warnings = self._validate_data(df)

            # Generate output path
            csv_path = self._get_csv_path(xlsx_path)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            # Save as CSV with UTF-8 encoding and proper quoting
            # QUOTE_NONNUMERIC quotes all non-numeric fields to handle special chars
            df.to_csv(
                csv_path,
                index=False,
                encoding="utf-8-sig",
                quoting=csv.QUOTE_NONNUMERIC,
            )

            # Generate metadata
            metadata = self._generate_metadata(
                xlsx_path=xlsx_path,
                csv_path=csv_path,
                initial_rows=initial_rows,
                final_rows=final_rows,
                columns=df.columns.tolist(),
                validation_warnings=validation_warnings,
            )

            # Save metadata
            metadata_path = self._get_metadata_path(csv_path)
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"  [OK] Converted to: {csv_path} ({final_rows} rows)")
            if validation_warnings:
                logger.warning(f"  [WARNING] {len(validation_warnings)} validation warnings")

            return csv_path

        except Exception as e:
            logger.error(f"  [FAILED] Conversion failed for {xlsx_path}: {e}", exc_info=True)
            return None

    @staticmethod
    def _validate_data(df: pd.DataFrame) -> List[str]:
        """
        Perform basic data validation.

        Args:
            df: DataFrame to validate

        Returns:
            List of validation warning messages
        """
        warnings = []

        # Check for completely empty columns
        empty_cols = df.columns[df.isna().all()].tolist()
        if empty_cols:
            warnings.append(f"Empty columns: {', '.join(empty_cols)}")

        # Check for duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate rows")

        # Check data types (all object/string is suspicious)
        if all(df[col].dtype == "object" for col in df.columns):
            warnings.append("All columns are string type (possible parsing issue)")

        return warnings

    def _generate_metadata(
        self,
        xlsx_path: Path,
        csv_path: Path,
        initial_rows: int,
        final_rows: int,
        columns: List[str],
        validation_warnings: List[str],
    ) -> Dict:
        """
        Generate metadata for the conversion.

        Args:
            xlsx_path: Source XLSX file path
            csv_path: Output CSV file path
            initial_rows: Number of rows before cleaning
            final_rows: Number of rows after cleaning
            columns: List of column names
            validation_warnings: List of validation warnings

        Returns:
            Metadata dictionary
        """
        return {
            "source_file": str(xlsx_path.relative_to(self.raw_dir)),
            "output_file": str(csv_path.relative_to(self.processed_dir)),
            "conversion_timestamp": datetime.now().isoformat(),
            "rows": {
                "initial": initial_rows,
                "final": final_rows,
                "removed": initial_rows - final_rows,
            },
            "columns": {
                "count": len(columns),
                "names": columns,
            },
            "validation_warnings": validation_warnings,
            "converter_version": "2.0",
        }

    def convert_all(
        self,
        country: Optional[str] = None,
        data_type: Optional[str] = None,
        pattern: Optional[str] = None,
        force: bool = False,
        validate: bool = True,
    ) -> Dict[str, int]:
        """
        Batch convert all matching XLSX files.

        Args:
            country: Filter by country code
            data_type: Filter by data type
            pattern: Custom glob pattern
            force: If True, reconvert existing files
            validate: If True, perform data validation

        Returns:
            Dictionary with conversion statistics
        """
        files = self.find_xlsx_files(country=country, data_type=data_type, pattern=pattern)

        stats = {
            "total": len(files),
            "converted": 0,
            "skipped": 0,
            "failed": 0,
        }

        logger.info(f"\nStarting batch conversion of {stats['total']} files...")

        for idx, xlsx_file in enumerate(files, 1):
            logger.info(f"\n[{idx}/{stats['total']}] Processing: {xlsx_file.name}")

            result = self.convert_file(xlsx_file, force=force, validate=validate)

            if result is not None:
                stats["converted"] += 1
            elif self.is_converted(xlsx_file):
                stats["skipped"] += 1
            else:
                stats["failed"] += 1

        logger.info("\n" + "=" * 60)
        logger.info("Batch conversion complete:")
        logger.info(f"  Total files: {stats['total']}")
        logger.info(f"  Converted: {stats['converted']}")
        logger.info(f"  Skipped: {stats['skipped']}")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info("=" * 60)

        return stats

    def get_latest_xlsx(
        self,
        country: Optional[str] = None,
        data_type: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Get the most recently created XLSX file.

        Args:
            country: Filter by country code
            data_type: Filter by data type

        Returns:
            Path to the latest file, or None if no files found
        """
        files = self.find_xlsx_files(country=country, data_type=data_type)
        if not files:
            return None

        # Sort by creation time, most recent first
        return max(files, key=lambda p: p.stat().st_ctime)

    def get_subdirectory_info(self) -> Dict[str, int]:
        """
        Get information about subdirectories in raw_dir and their XLSX file counts.

        Returns:
            Dictionary mapping subdirectory paths to XLSX file counts
        """
        info = {}

        # Check if raw_dir exists
        if not self.raw_dir.exists():
            return info

        # Scan first two levels of subdirectories
        try:
            for country_dir in self.raw_dir.iterdir():
                if country_dir.is_dir() and not country_dir.name.startswith('.'):
                    country_count = len(list(country_dir.glob("**/*.xlsx")))
                    # Include ALL directories, even empty ones
                    info[str(country_dir.relative_to(self.raw_dir))] = country_count
        except (OSError, PermissionError):
            # Handle permission errors gracefully
            pass

        return info


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the converter.

    Args:
        verbose: If True, set log level to DEBUG
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "converter.log"),
            logging.StreamHandler(),
        ],
    )
