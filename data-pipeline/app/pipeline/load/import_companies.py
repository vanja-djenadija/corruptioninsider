"""
Loader for importing company data from JSON into the database.
Handles deduplication using data hashes with batch inserts.
Tracks skipped companies with reasons in company_import_skip table.
"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError, DatabaseError, InterfaceError

from ...models.raw.company import Company, CompanyRelation, CompanyImportSkip

logger = logging.getLogger(__name__)

# Batch size for bulk inserts
BATCH_SIZE = 1000

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # Base delay in seconds (will be multiplied by attempt number)

# Skip reason constants
SKIP_REASON_MISSING_JIB = "MISSING_JIB"
SKIP_REASON_DUPLICATE_IN_DATABASE = "DUPLICATE_IN_DATABASE"
SKIP_REASON_DUPLICATE_IN_BATCH = "DUPLICATE_IN_BATCH"
SKIP_REASON_DB_CONFLICT = "DB_CONFLICT"
SKIP_REASON_DB_ERROR = "DB_ERROR"
SKIP_REASON_INVALID_DATA = "INVALID_DATA"


def _normalize_hash_value(value: Any) -> str:
    """Normalize a value for consistent hashing regardless of type representation."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return str(int(value)) if value == int(value) else str(value)
    return str(value)


def compute_company_hash(data: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of company data fields.
    Used to detect if company data has changed.
    Values are normalized to ensure consistent hashing across runs
    (e.g., float/int JIB, None vs missing fields, bool representation).
    """
    hash_fields = [
        jib_to_string(data.get("jib")),
        _normalize_hash_value(data.get("shortName")),
        _normalize_hash_value(data.get("longName")),
        _normalize_hash_value(data.get("municipality")),
        _normalize_hash_value(data.get("county")),
        _normalize_hash_value(data.get("address")),
        _normalize_hash_value(data.get("letterOfActivity")),
        _normalize_hash_value(data.get("activityCode")),
        _normalize_hash_value(data.get("activityCodeDescription")),
        _normalize_hash_value(data.get("registrationDateTime")),
        _normalize_hash_value(data.get("isPublicEntity")),
    ]
    hash_string = "|".join(hash_fields)
    return hashlib.sha256(hash_string.encode("utf-8")).hexdigest()


def compute_relation_hash(data: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of relation data fields.
    """
    hash_fields = [
        _normalize_hash_value(data.get("relationTypeId")),
        _normalize_hash_value(data.get("fullName")),
        _normalize_hash_value(data.get("share")),
        _normalize_hash_value(data.get("position")),
    ]
    hash_string = "|".join(hash_fields)
    return hashlib.sha256(hash_string.encode("utf-8")).hexdigest()


def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Could not parse date: %s", date_str)
        return None


def jib_to_string(jib: Any) -> str:
    """Convert JIB (which may be float) to string without decimals."""
    if jib is None:
        return ""
    if isinstance(jib, float):
        return str(int(jib))
    return str(jib)


def get_existing_company_keys(session, company_ids: Set[str]) -> Set[Tuple[str, str]]:
    """
    Get existing (company_id, data_hash) pairs from database.
    Used to identify duplicates before insertion.
    """
    if not company_ids:
        return set()

    existing = session.query(Company.company_id, Company.data_hash).filter(
        Company.company_id.in_(company_ids)
    ).all()

    return {(row.company_id, row.data_hash) for row in existing}


def record_skip(
    session,
    batch_id: str,
    source_file: str,
    entity: Dict[str, Any],
    skip_reason: str,
    skip_details: Optional[str] = None
) -> None:
    """
    Record a skipped company in the company_import_skip table.
    """
    skip_record = CompanyImportSkip(
        import_batch_id=batch_id,
        source_file=source_file,
        company_id=jib_to_string(entity.get("jib")) or None,
        company_short_name=entity.get("shortName"),
        company_long_name=entity.get("longName"),
        skip_reason=skip_reason,
        skip_details=skip_details,
        raw_data=json.dumps(entity, ensure_ascii=False, default=str),
        skipped_at=datetime.now()
    )
    session.add(skip_record)


def execute_with_retry(
    session,
    stmt,
    max_retries: int = MAX_RETRIES,
    retry_delay_base: float = RETRY_DELAY_BASE
) -> Tuple[int, Optional[str]]:
    """
    Execute a database statement with retry logic.

    Args:
        session: SQLAlchemy session
        stmt: The statement to execute
        max_retries: Maximum number of retry attempts
        retry_delay_base: Base delay between retries (multiplied by attempt number)

    Returns:
        Tuple of (rowcount, error_message). error_message is None on success.
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            result = session.execute(stmt)
            session.commit()
            return result.rowcount, None

        except (OperationalError, DatabaseError, InterfaceError) as e:
            last_error = str(e)
            session.rollback()

            if attempt < max_retries:
                delay = retry_delay_base * attempt
                logger.warning(
                    "Database error on attempt %d/%d: %s. Retrying in %.1f seconds...",
                    attempt, max_retries, last_error, delay
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Database error on final attempt %d/%d: %s. Giving up.",
                    attempt, max_retries, last_error
                )

        except Exception as e:
            # For unexpected errors, don't retry
            last_error = str(e)
            session.rollback()
            logger.error("Unexpected error during database operation: %s", last_error)
            break

    return 0, last_error


def import_companies_from_json(
    json_path: str,
    database_url: str,
    batch_size: int = BATCH_SIZE,
    track_skips: bool = True,
    max_retries: int = MAX_RETRIES,
    retry_delay_base: float = RETRY_DELAY_BASE,
    source: str | None = None
) -> Dict[str, int]:
    """
    Import companies from JSON file into database using batch inserts.
    Tracks skipped companies with reasons. Includes retry logic for database errors.

    Args:
        json_path: Path to the JSON file
        database_url: Database connection URL
        batch_size: Number of records per batch insert
        track_skips: Whether to record skipped companies in database
        max_retries: Maximum number of retry attempts for failed batches
        retry_delay_base: Base delay in seconds between retries (multiplied by attempt number)
        source: Data source identifier (e.g. 'fia', 'rs') stored on each company record

    Returns:
        Dictionary with import statistics
    """
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Generate unique batch ID for this import
    batch_id = str(uuid.uuid4())[:8]
    source_file = Path(json_path).name

    stats = {
        "total_in_file": 0,
        "companies_inserted": 0,
        "companies_skipped": 0,
        "companies_skipped_missing_jib": 0,
        "companies_skipped_duplicate_in_database": 0,
        "companies_skipped_duplicate_in_batch": 0,
        "companies_skipped_db_conflict": 0,
        "companies_skipped_db_error": 0,
        "batches_retried": 0,
        "relations_inserted": 0,
        "import_batch_id": batch_id,
    }

    try:
        # Load JSON data
        json_file = Path(json_path)
        with open(json_file, "r", encoding="utf-8") as f:
            entities = json.load(f)

        stats["total_in_file"] = len(entities)
        logger.info("Loaded %d entities from %s (batch_id: %s)", len(entities), json_path, batch_id)

        import_time = datetime.now()

        # First pass: identify all JIBs and compute hashes
        entities_with_jib = []
        all_jib_ids = set()

        for entity in entities:
            jib = jib_to_string(entity.get("jib"))
            if not jib:
                # Skip companies without JIB
                stats["companies_skipped"] += 1
                stats["companies_skipped_missing_jib"] += 1
                if track_skips:
                    record_skip(
                        session, batch_id, source_file, entity,
                        SKIP_REASON_MISSING_JIB,
                        "Company has no JIB (tax identification number)"
                    )
                continue

            data_hash = compute_company_hash(entity)
            entities_with_jib.append((entity, jib, data_hash))
            all_jib_ids.add(jib)

        # Get existing company keys to identify duplicates
        existing_keys = get_existing_company_keys(session, all_jib_ids)
        logger.info("Found %d existing company records for %d JIBs", len(existing_keys), len(all_jib_ids))

        # Second pass: prepare records, tracking duplicates
        company_records = []
        entity_relations = []
        batch_keys = set()  # Track keys added in this batch (for detecting duplicates within file)
        entity_by_key = {}  # Map (jib, hash) -> entity for tracking DB conflicts later

        for entity, jib, data_hash in entities_with_jib:
            key = (jib, data_hash)

            # Check if duplicate exists in database
            if key in existing_keys:
                stats["companies_skipped"] += 1
                stats["companies_skipped_duplicate_in_database"] += 1
                if track_skips:
                    record_skip(
                        session, batch_id, source_file, entity,
                        SKIP_REASON_DUPLICATE_IN_DATABASE,
                        f"Company with JIB {jib} and same data hash already exists in database"
                    )
                continue

            # Check if duplicate within this batch/file
            if key in batch_keys:
                stats["companies_skipped"] += 1
                stats["companies_skipped_duplicate_in_batch"] += 1
                if track_skips:
                    record_skip(
                        session, batch_id, source_file, entity,
                        SKIP_REASON_DUPLICATE_IN_BATCH,
                        f"Duplicate company with JIB {jib} found earlier in same import file"
                    )
                continue

            # Add to batch_keys to catch duplicates within this file
            batch_keys.add(key)

            # Store entity for potential DB conflict tracking
            entity_by_key[key] = entity

            record = {
                "company_id": jib,
                "data_hash": data_hash,
                "company_short_name": entity.get("shortName"),
                "company_long_name": entity.get("longName"),
                "municipality": entity.get("municipality"),
                "county": entity.get("county"),
                "address": entity.get("address"),
                "letter_of_activity": entity.get("letterOfActivity"),
                "activity_code": entity.get("activityCode"),
                "activity_code_description": entity.get("activityCodeDescription"),
                "registration_date": parse_datetime(entity.get("registrationDateTime")),
                "is_public_entity": entity.get("isPublicEntity"),
                "imported_at": import_time,
            }
            if source:
                record["source"] = source
            company_records.append(record)

            # Store relations for later processing
            relations = entity.get("legalEntityRelations", [])
            if relations:
                entity_relations.append((jib, data_hash, relations))

        # Commit skip records before bulk insert
        if track_skips:
            session.commit()

        # Batch insert companies with retry logic
        logger.info("Inserting %d new companies in batches of %d...", len(company_records), batch_size)
        for i in range(0, len(company_records), batch_size):
            batch = company_records[i:i + batch_size]
            batch_keys_for_insert = [(rec["company_id"], rec["data_hash"]) for rec in batch]

            stmt = insert(Company).values(batch)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=['company_id', 'data_hash']
            )

            # Execute with retry logic
            inserted_count, error = execute_with_retry(session, stmt, max_retries, retry_delay_base)

            if error:
                # Database error after all retries - record all batch records as failed
                stats["batches_retried"] += 1
                if track_skips:
                    for key in batch_keys_for_insert:
                        entity = entity_by_key.get(key)
                        if entity:
                            stats["companies_skipped"] += 1
                            stats["companies_skipped_db_error"] += 1
                            record_skip(
                                session, batch_id, source_file, entity,
                                SKIP_REASON_DB_ERROR,
                                f"Database error after {max_retries} retries: {error[:200]}"
                            )
                    session.commit()
                logger.error("Batch %d failed after retries: %d records not inserted", i // batch_size + 1, len(batch))
                continue

            stats["companies_inserted"] += inserted_count

            # Track DB conflicts (records that were rejected by database due to constraints)
            if track_skips and inserted_count < len(batch):
                # Find which records from this batch were actually inserted
                inserted_keys = set()
                for key in batch_keys_for_insert:
                    exists = session.query(Company).filter(
                        Company.company_id == key[0],
                        Company.data_hash == key[1]
                    ).first()
                    if exists:
                        inserted_keys.add(key)

                # Record skips for records that weren't inserted
                conflict_count = 0
                for key in batch_keys_for_insert:
                    if key not in inserted_keys:
                        entity = entity_by_key.get(key)
                        if entity:
                            stats["companies_skipped"] += 1
                            stats["companies_skipped_db_conflict"] += 1
                            conflict_count += 1
                            record_skip(
                                session, batch_id, source_file, entity,
                                SKIP_REASON_DB_CONFLICT,
                                f"Record rejected by database (possible race condition or constraint violation)"
                            )

                if conflict_count > 0:
                    session.commit()
                    logger.warning(
                        "Batch had %d DB conflicts: sent %d records, inserted %d",
                        conflict_count, len(batch), inserted_count
                    )

            if (i + batch_size) % 10000 == 0 or i + batch_size >= len(company_records):
                logger.info("Processed %d/%d companies...",
                           min(i + batch_size, len(company_records)), len(company_records))

        # Process relations - need to get company IDs first
        if entity_relations:
            logger.info("Processing %d entities with relations...", len(entity_relations))

            # Build lookup of (company_id, data_hash) -> id
            company_lookup = {}
            for jib, data_hash, _ in entity_relations:
                key = (jib, data_hash)
                if key not in company_lookup:
                    company = session.query(Company).filter(
                        Company.company_id == jib,
                        Company.data_hash == data_hash
                    ).first()
                    if company:
                        company_lookup[key] = company.id

            # Prepare relation records
            relation_records = []
            for jib, data_hash, relations in entity_relations:
                company_record_id = company_lookup.get((jib, data_hash))
                if not company_record_id:
                    continue

                for rel in relations:
                    rel_hash = compute_relation_hash(rel)
                    relation_records.append({
                        "company_record_id": company_record_id,
                        "data_hash": rel_hash,
                        "relation_type_id": rel.get("relationTypeId"),
                        "full_name": rel.get("fullName"),
                        "share": rel.get("share"),
                        "position": rel.get("position"),
                    })

            # Batch insert relations with retry logic
            if relation_records:
                logger.info("Inserting %d relations...", len(relation_records))
                for i in range(0, len(relation_records), batch_size):
                    batch = relation_records[i:i + batch_size]

                    stmt = insert(CompanyRelation).values(batch)
                    stmt = stmt.on_conflict_do_nothing(
                        index_elements=['company_record_id', 'relation_type_id', 'full_name', 'data_hash']
                    )

                    inserted_count, error = execute_with_retry(session, stmt, max_retries, retry_delay_base)
                    if error:
                        logger.error("Failed to insert relations batch after retries: %s", error)
                    else:
                        stats["relations_inserted"] += inserted_count

        logger.info("Import complete: %s", stats)

    except Exception as e:
        session.rollback()
        logger.error("Import failed: %s", e)
        raise
    finally:
        session.close()

    return stats


def get_company_count(database_url: str) -> int:
    """Get total count of companies in database."""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        return session.query(Company).count()
    finally:
        session.close()


def get_skip_summary(database_url: str, batch_id: Optional[str] = None) -> Dict[str, int]:
    """
    Get summary of skipped companies by reason.

    Args:
        database_url: Database connection URL
        batch_id: Optional batch ID to filter by

    Returns:
        Dictionary mapping skip reasons to counts
    """
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        from sqlalchemy import func

        query = session.query(
            CompanyImportSkip.skip_reason,
            func.count(CompanyImportSkip.id).label('count')
        )

        if batch_id:
            query = query.filter(CompanyImportSkip.import_batch_id == batch_id)

        query = query.group_by(CompanyImportSkip.skip_reason)

        results = query.all()
        return {row.skip_reason: row.count for row in results}

    finally:
        session.close()


def get_skipped_companies(
    database_url: str,
    batch_id: Optional[str] = None,
    skip_reason: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get list of skipped companies with details.

    Args:
        database_url: Database connection URL
        batch_id: Optional batch ID to filter by
        skip_reason: Optional skip reason to filter by
        limit: Maximum number of records to return

    Returns:
        List of dictionaries with skip details
    """
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        query = session.query(CompanyImportSkip)

        if batch_id:
            query = query.filter(CompanyImportSkip.import_batch_id == batch_id)
        if skip_reason:
            query = query.filter(CompanyImportSkip.skip_reason == skip_reason)

        query = query.order_by(CompanyImportSkip.skipped_at.desc()).limit(limit)

        results = []
        for skip in query.all():
            results.append({
                "id": skip.id,
                "import_batch_id": skip.import_batch_id,
                "source_file": skip.source_file,
                "company_id": skip.company_id,
                "company_short_name": skip.company_short_name,
                "company_long_name": skip.company_long_name,
                "skip_reason": skip.skip_reason,
                "skip_details": skip.skip_details,
                "skipped_at": skip.skipped_at.isoformat() if skip.skipped_at else None,
            })

        return results

    finally:
        session.close()
