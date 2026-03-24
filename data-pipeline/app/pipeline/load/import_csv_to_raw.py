"""
CSV to PostgreSQL importer for award_raw table.
Maps Bosnian CSV column names to English database columns.
"""

import os
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ...models.base import Base
from ...models.raw.award_raw import AwardRaw
from ...util.paths import resolve_path

load_dotenv()

logger = logging.getLogger(__name__)

# Column mapping: CSV column name (Bosnian) -> Database column name (English)
COLUMN_MAPPING = {
    "Ugovorni organ (UO)": "contracting_authority_name",
    "UO: Opcina": "contracting_authority_city_name",
    "UO: PIB": "contracting_authority_tax_number",
    "UO: Vrsta": "contracting_authority_type",
    "UO: Djelatnost": "contracting_authority_activity_type_name",
    "UO: Adm. nivo": "contracting_authority_administrative_unit_type",
    "UO: Adm. jedinica": "contracting_authority_administrative_unit_name",
    "Naziv postupka": "procedure_name",
    "Broj postupka": "procedure_number",
    "Vrsta postupka": "procedure_type",
    "Vrsta ugovora": "contract_type",
    "Kategorija ugovora": "contract_category_name",
    "Potkategorija ugovora": "contract_subcategory_name",
    "Podjela na lotove?": "has_lots",
    "Aukcija?": "is_auction_online",
    "Okvirni sporazum (OS)?": "is_master_agreement",
    "Odbrana i sigurnost?": "is_defense_and_security",
    "Zajednicka nabavka?": "is_joint_procurement",
    "Nabavka u ime drugih?": "is_on_behalf_procurement",
    "Kriterij za dodjelu ugovora": "award_criterion",
    "Razlozi za primjenu pregovarackog postupka": "reasons_for_negotiated_procedure",
    "Zalba na postupak?": "legal_remedies_used",
    "Lot": "lot_name",
    "Glavni CPV kod": "main_cpv_code",
    "Zavrseno kroz pregovaracki postupak?": "completed_with_negotiation",
    "Da li su koristena sredstva EU?": "eu_funds_used",
    "Da li je zakljucen ugovor u ovom postupku?": "is_contract_concluded",
    "Primjena preferencijalnog tretmana?": "preferential_treatment_used",
    "Clan zakona": "regulation_quote_name",
    "Datum zakljucenja ugovora": "contract_date",
    "Broj primljenih ponuda": "number_of_received_offers",
    "Broj prihvatljivih ponuda": "number_of_acceptable_offers",
    "Vrijednost najnize prihvatljive ponude": "lowest_acceptable_offer_value",
    "Vrijednost najvise prihvatljive ponude": "highest_acceptable_offer_value",
    "Vrijednost ugovora/okvirnog sporazuma": "value",
    "Godisnja vrijednost ugovora/okvirnog sporazuma": "annual_value",
    "Mjesecna vrijednost ugovora/okvirnog sporazuma": "monthly_value",
    "Datum pocetka okvirnog sporazuma": "master_agreement_start_date",
    "Datum zavrsetka okvirnog sporazuma": "master_agreement_end_date",
    "Moguce podugovaranje?": "allowed_subcontracting",
    "Dio podugovaranja u procentima": "subcontracting_share",
    "Vrijednost podugovaranja bez PDV-a": "subcontracting_value",
    "Odabrani ponudjac / nosilac grupe ponudjaca (PON)": "supplier_name",
    "PON: IDB/JMBG": "supplier_tax_number",
    "PON: Inostrani?": "supplier_is_foreign",
    "PON: Drzava": "supplier_country",
    "PON: Kategorija velicine": "supplier_size_category",
    "PON: Registrovan?": "supplier_is_registered",
    "Ostali ponudjaci u grupi": "other_suppliers_in_group",
}

# Boolean columns that need conversion from "Da"/"Ne" to True/False
BOOLEAN_COLUMNS = [
    "has_lots", "is_auction_online", "is_master_agreement",
    "is_defense_and_security", "is_joint_procurement", "is_on_behalf_procurement",
    "completed_with_negotiation", "preferential_treatment_used", "eu_funds_used",
    "legal_remedies_used", "is_contract_concluded", "allowed_subcontracting",
    "supplier_is_foreign", "supplier_is_registered"
]

# Date columns that need parsing
DATE_COLUMNS = [
    "contract_date", "master_agreement_start_date", "master_agreement_end_date"
]

# Numeric columns
NUMERIC_COLUMNS = [
    "value", "annual_value", "monthly_value",
    "lowest_acceptable_offer_value", "highest_acceptable_offer_value",
    "subcontracting_share", "subcontracting_value",
    "number_of_received_offers", "number_of_acceptable_offers"
]


def get_engine(database_url: Optional[str] = None):
    """
    Create SQLAlchemy engine.

    Args:
        database_url: Database connection URL. If None, falls back to DATABASE_URL env var.
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("No database_url provided and DATABASE_URL environment variable not set")
    return create_engine(database_url)


def parse_boolean(value) -> Optional[bool]:
    """Convert 'Da'/'Ne' to True/False."""
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, bool):
        return value
    val_str = str(value).strip().lower()
    if val_str in ("da", "yes", "true", "1"):
        return True
    if val_str in ("ne", "no", "false", "0"):
        return False
    return None


def parse_date(value) -> Optional[datetime]:
    """Parse date string to datetime."""
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, datetime):
        return value

    date_formats = ["%d.%m.%Y.", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]
    for fmt in date_formats:
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse date: {value}")
    return None


def parse_numeric(value) -> Optional[float]:
    """Parse numeric value, handling European format."""
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)

    try:
        # Handle European format (1.234,56 -> 1234.56)
        val_str = str(value).strip()
        # Remove thousand separators and convert decimal comma
        val_str = val_str.replace(".", "").replace(",", ".")
        return float(val_str)
    except ValueError:
        logger.warning(f"Could not parse numeric: {value}")
        return None


def process_row(row: Dict, source_country: str, source_system: str,
                source_file: str, batch_id: str) -> Dict:
    """Process a single row and return a dictionary for AwardRaw."""
    record = {
        "source_country": source_country,
        "source_system": source_system,
        "source_file": source_file,
        "import_batch_id": batch_id,
        "imported_at": datetime.now(),
    }

    for csv_col, db_col in COLUMN_MAPPING.items():
        if csv_col in row:
            value = row[csv_col]

            if db_col in BOOLEAN_COLUMNS:
                record[db_col] = parse_boolean(value)
            elif db_col in DATE_COLUMNS:
                record[db_col] = parse_date(value)
            elif db_col in NUMERIC_COLUMNS:
                record[db_col] = parse_numeric(value)
            else:
                # String column
                if pd.isna(value) or value == "":
                    record[db_col] = None
                else:
                    record[db_col] = str(value).strip()

    return record


def import_csv_file(
    csv_path: Path,
    session,
    source_country: str = "BA",
    source_system: str = "EJN",
    batch_size: int = 500
) -> int:
    """
    Import a single CSV file into award_raw table.

    Args:
        csv_path: Path to CSV file
        session: SQLAlchemy session
        source_country: Country code (default: BA)
        source_system: Source system name (default: EJN)
        batch_size: Number of records to commit at once

    Returns:
        Number of rows imported
    """
    logger.info(f"Importing: {csv_path}")

    # Generate batch ID
    batch_id = str(uuid.uuid4())[:8]
    source_file = str(csv_path.name)

    try:
        # Read CSV with UTF-8-BOM encoding (Excel exports)
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        total_rows = len(df)
        logger.info(f"  Found {total_rows} rows in CSV")

        imported = 0
        records = []

        for idx, row in df.iterrows():
            record_dict = process_row(
                row.to_dict(),
                source_country,
                source_system,
                source_file,
                batch_id
            )
            records.append(AwardRaw(**record_dict))

            # Batch insert
            if len(records) >= batch_size:
                session.bulk_save_objects(records)
                session.commit()
                imported += len(records)
                logger.info(f"  Imported {imported}/{total_rows} rows...")
                records = []

        # Insert remaining records
        if records:
            session.bulk_save_objects(records)
            session.commit()
            imported += len(records)

        logger.info(f"  Successfully imported {imported} rows")
        return imported

    except Exception as e:
        logger.error(f"  Import failed: {e}")
        session.rollback()
        raise


def import_csv_files(
    folder_path: Optional[str] = None,
    pattern: str = "*.csv",
    source_country: str = "BA",
    source_system: str = "EJN",
    database_url: Optional[str] = None
) -> Dict:
    """
    Import all CSV files from a folder.

    Args:
        folder_path: Path to folder (default: data/processed/ba/awards)
        pattern: File pattern (default: *.csv)
        source_country: Country code
        source_system: Source system name
        database_url: Database connection URL (falls back to DATABASE_URL env var)

    Returns:
        Dictionary with import statistics
    """
    # Resolve folder path (handles both relative and absolute paths)
    if folder_path is None:
        folder = resolve_path("data/processed/ba/awards")
    else:
        folder = resolve_path(folder_path)

    # Find CSV files
    csv_files = sorted(folder.glob(pattern))

    if not csv_files:
        logger.warning(f"No CSV files found in {folder}")
        return {"total_files": 0, "successful": 0, "failed": 0, "total_rows": 0}

    logger.info(f"Found {len(csv_files)} CSV file(s)")
    for f in csv_files:
        logger.info(f"  - {f.name}")

    # Create database session
    engine = get_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    stats = {
        "total_files": len(csv_files),
        "successful": 0,
        "failed": 0,
        "total_rows": 0,
        "files": []
    }

    logger.info("=" * 60)
    logger.info(f"Starting import at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        for csv_file in csv_files:
            try:
                rows = import_csv_file(
                    csv_file, session, source_country, source_system
                )
                stats["successful"] += 1
                stats["total_rows"] += rows
                stats["files"].append({
                    "name": csv_file.name,
                    "rows": rows,
                    "status": "success"
                })
            except Exception as e:
                logger.error(f"Failed to import {csv_file.name}: {e}")
                stats["failed"] += 1
                stats["files"].append({
                    "name": csv_file.name,
                    "rows": 0,
                    "status": "failed",
                    "error": str(e)
                })
    finally:
        session.close()

    # Print summary
    logger.info("=" * 60)
    logger.info("IMPORT COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Files processed:  {stats['total_files']}")
    logger.info(f"  Successful:     {stats['successful']}")
    logger.info(f"  Failed:         {stats['failed']}")
    logger.info(f"Total rows:       {stats['total_rows']:,}")
    logger.info("=" * 60)

    return stats


def get_row_count(database_url: Optional[str] = None) -> int:
    """
    Get current row count in award_raw table.

    Args:
        database_url: Database connection URL (falls back to DATABASE_URL env var)
    """
    engine = get_engine(database_url)
    session = sessionmaker(bind=engine)()
    try:
        return session.query(AwardRaw).count()
    finally:
        session.close()


def clear_table(database_url: Optional[str] = None, confirm: bool = False) -> bool:
    """
    Clear all data from award_raw table.

    Args:
        database_url: Database connection URL (falls back to DATABASE_URL env var)
        confirm: Must be True to execute

    Returns:
        True if cleared, False otherwise
    """
    if not confirm:
        logger.warning("clear_table called without confirmation")
        return False

    engine = get_engine(database_url)
    session = sessionmaker(bind=engine)()

    try:
        deleted = session.query(AwardRaw).delete()
        session.commit()
        logger.info(f"Cleared {deleted} rows from award_raw")
        return True
    except Exception as e:
        logger.error(f"Failed to clear table: {e}")
        session.rollback()
        return False
    finally:
        session.close()


