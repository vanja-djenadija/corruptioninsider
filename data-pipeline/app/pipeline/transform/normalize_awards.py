"""
ETL script to normalize awards_raw data into relational tables.

Transforms denormalized awards_raw records into:
- contracting_authority
- supplier
- procurement_procedure
- award
- award_supplier
"""
import logging
import re
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.raw.award_raw import AwardRaw
from app.models.normalized.contracting_authority import ContractingAuthority
from app.models.normalized.supplier import Supplier
from app.models.normalized.procurement_procedure import ProcurementProcedure
from app.models.normalized.award import Award
from app.models.normalized.award_supplier import AwardSupplier

logger = logging.getLogger(__name__)


class AwardsNormalizer:
    """Normalizes awards_raw data into relational tables."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

        # Caches for deduplication (key -> id)
        self._authority_cache: dict[str, int] = {}  # tax_number -> id
        self._supplier_cache: dict[str, int] = {}   # (tax_number, name) -> id
        self._procedure_cache: dict[str, int] = {}  # number -> id

    def normalize_all(self, batch_size: int = 100) -> dict:
        """
        Normalize all records from awards_raw.

        Returns:
            dict with statistics about the normalization process
        """
        stats = {
            "raw_records_processed": 0,
            "contracting_authorities_created": 0,
            "suppliers_created": 0,
            "procedures_created": 0,
            "awards_created": 0,
            "award_suppliers_created": 0,
            "errors": 0,
        }

        with self.Session() as session:
            # Load existing entities into cache
            self._load_existing_entities(session)

            # Process raw records in batches
            offset = 0
            while True:
                raw_records = session.query(AwardRaw).offset(offset).limit(batch_size).all()
                if not raw_records:
                    break

                for raw in raw_records:
                    try:
                        self._process_raw_record(session, raw, stats)
                        stats["raw_records_processed"] += 1
                    except Exception as e:
                        logger.error(f"Error processing raw record {raw.id}: {e}")
                        stats["errors"] += 1
                        session.rollback()

                session.commit()
                offset += batch_size
                logger.info(f"Processed {offset} raw records...")

        logger.info(f"Normalization complete: {stats}")
        return stats

    def _load_existing_entities(self, session: Session):
        """Load existing entities into caches for deduplication."""
        # Load contracting authorities
        for ca in session.query(ContractingAuthority).all():
            self._authority_cache[ca.tax_number] = ca.id

        # Load suppliers (keyed by tax_number + name for uniqueness)
        for s in session.query(Supplier).all():
            key = self._supplier_key(s.tax_number, s.name)
            self._supplier_cache[key] = s.id

        # Load procedures
        for p in session.query(ProcurementProcedure).all():
            self._procedure_cache[p.number] = p.id

        logger.info(
            f"Loaded existing entities: {len(self._authority_cache)} authorities, "
            f"{len(self._supplier_cache)} suppliers, {len(self._procedure_cache)} procedures"
        )

    def _process_raw_record(self, session: Session, raw: AwardRaw, stats: dict):
        """Process a single raw record and create normalized entities."""

        # Skip records without required data
        if not raw.contracting_authority_tax_number or not raw.procedure_number:
            logger.warning(
                f"Skipping raw record {raw.id}: missing contracting_authority_tax_number or procedure_number"
            )
            return

        # 1. Get or create contracting authority
        authority_id = self._get_or_create_authority(session, raw, stats)

        # 2. Get or create procedure
        procedure_id = self._get_or_create_procedure(session, raw, stats)

        # 3. Get or create primary supplier
        primary_supplier_id = None
        if raw.supplier_name:
            primary_supplier_id = self._get_or_create_supplier(
                session, raw.supplier_tax_number, raw.supplier_name,
                raw.supplier_country, raw.supplier_is_foreign,
                raw.supplier_size_category, raw.supplier_is_registered, stats
            )

        # 4. Create award
        award = Award(
            contracting_authority_id=authority_id,
            procedure_id=procedure_id,
            lot_name=raw.lot_name,
            main_cpv_code=raw.main_cpv_code,
            value=raw.value,
            annual_value=raw.annual_value,
            monthly_value=raw.monthly_value,
            contract_date=raw.contract_date,
            master_agreement_start_date=raw.master_agreement_start_date,
            master_agreement_end_date=raw.master_agreement_end_date,
            number_of_received_offers=raw.number_of_received_offers,
            number_of_acceptable_offers=raw.number_of_acceptable_offers,
            lowest_acceptable_offer_value=raw.lowest_acceptable_offer_value,
            highest_acceptable_offer_value=raw.highest_acceptable_offer_value,
            eu_funds_used=raw.eu_funds_used,
            completed_with_negotiation=raw.completed_with_negotiation,
            preferential_treatment_used=raw.preferential_treatment_used,
            legal_remedies_used=raw.legal_remedies_used,
            is_contract_concluded=raw.is_contract_concluded,
            allowed_subcontracting=raw.allowed_subcontracting,
            subcontracting_share=raw.subcontracting_share,
            subcontracting_value=raw.subcontracting_value,
            regulation_quote_name=raw.regulation_quote_name,
            reasons_for_negotiated_procedure=raw.reasons_for_negotiated_procedure,
            source_country=raw.source_country,
            source_system=raw.source_system,
            raw_award_id=raw.id,
        )
        session.add(award)
        session.flush()  # Get the award ID
        stats["awards_created"] += 1

        # 5. Create award-supplier links
        if primary_supplier_id:
            award_supplier = AwardSupplier(
                award_id=award.id,
                supplier_id=primary_supplier_id,
                role='primary'
            )
            session.add(award_supplier)
            stats["award_suppliers_created"] += 1

        # 6. Parse and add consortium members
        if raw.other_suppliers_in_group:
            self._add_consortium_members(session, award.id, raw.other_suppliers_in_group, stats)

    def _get_or_create_authority(self, session: Session, raw: AwardRaw, stats: dict) -> int:
        """Get or create a contracting authority."""
        tax_number = raw.contracting_authority_tax_number

        if tax_number in self._authority_cache:
            return self._authority_cache[tax_number]

        authority = ContractingAuthority(
            tax_number=tax_number,
            name=raw.contracting_authority_name or "Unknown",
            city=raw.contracting_authority_city_name,
            type=raw.contracting_authority_type,
            activity_type=raw.contracting_authority_activity_type_name,
            admin_unit_type=raw.contracting_authority_administrative_unit_type,
            admin_unit_name=raw.contracting_authority_administrative_unit_name,
        )
        session.add(authority)
        session.flush()

        self._authority_cache[tax_number] = authority.id
        stats["contracting_authorities_created"] += 1
        return authority.id

    def _get_or_create_procedure(self, session: Session, raw: AwardRaw, stats: dict) -> int:
        """Get or create a procurement procedure."""
        number = raw.procedure_number

        if number in self._procedure_cache:
            return self._procedure_cache[number]

        procedure = ProcurementProcedure(
            number=number,
            name=raw.procedure_name,
            type=raw.procedure_type,
            contract_type=raw.contract_type,
            category=raw.contract_category_name,
            subcategory=raw.contract_subcategory_name,
            has_lots=raw.has_lots,
            is_auction_online=raw.is_auction_online,
            is_master_agreement=raw.is_master_agreement,
            is_defense_and_security=raw.is_defense_and_security,
            is_joint_procurement=raw.is_joint_procurement,
            award_criterion=raw.award_criterion,
        )
        session.add(procedure)
        session.flush()

        self._procedure_cache[number] = procedure.id
        stats["procedures_created"] += 1
        return procedure.id

    def _get_or_create_supplier(
        self, session: Session,
        tax_number: Optional[str], name: str,
        country: Optional[str] = None,
        is_foreign: Optional[bool] = None,
        size_category: Optional[str] = None,
        is_registered: Optional[bool] = None,
        stats: Optional[dict] = None
    ) -> int:
        """Get or create a supplier."""
        key = self._supplier_key(tax_number, name)

        if key in self._supplier_cache:
            return self._supplier_cache[key]

        supplier = Supplier(
            tax_number=tax_number,
            name=name,
            country=country,
            is_foreign=is_foreign,
            size_category=size_category,
            is_registered=is_registered,
        )
        session.add(supplier)
        session.flush()

        self._supplier_cache[key] = supplier.id
        if stats:
            stats["suppliers_created"] += 1
        return supplier.id

    def _add_consortium_members(self, session: Session, award_id: int, other_suppliers: str, stats: dict):
        """Parse other_suppliers_in_group and add as consortium members."""
        # The format appears to be a text field with supplier names/info
        # Parse by common delimiters (newlines, semicolons, commas)
        members = self._parse_consortium_members(other_suppliers)

        for member_name in members:
            member_name = member_name.strip()
            if not member_name:
                continue

            # For consortium members, we typically don't have tax numbers
            supplier_id = self._get_or_create_supplier(
                session,
                tax_number=None,
                name=member_name,
                stats=stats
            )

            # Check if this link already exists
            existing = session.query(AwardSupplier).filter_by(
                award_id=award_id, supplier_id=supplier_id
            ).first()

            if not existing:
                award_supplier = AwardSupplier(
                    award_id=award_id,
                    supplier_id=supplier_id,
                    role='consortium_member'
                )
                session.add(award_supplier)
                stats["award_suppliers_created"] += 1

    @staticmethod
    def _parse_consortium_members(text: str) -> list[str]:
        """Parse consortium members from text field."""
        if not text:
            return []

        # Try different delimiters
        # First try newlines
        if '\n' in text:
            return [m.strip() for m in text.split('\n') if m.strip()]

        # Then try semicolons
        if ';' in text:
            return [m.strip() for m in text.split(';') if m.strip()]

        # Finally try commas (but be careful with company names that contain commas)
        # Only split on comma if there are multiple and they look like separators
        if text.count(',') >= 2:
            parts = text.split(',')
            # If parts look like company names (have reasonable length), use them
            if all(len(p.strip()) > 5 for p in parts if p.strip()):
                return [m.strip() for m in parts if m.strip()]

        # Return as single entry if no clear delimiter
        return [text.strip()] if text.strip() else []

    @staticmethod
    def _supplier_key(tax_number: Optional[str], name: str) -> str:
        """Generate a unique key for supplier deduplication."""
        # Use tax_number if available, otherwise use name
        if tax_number:
            return f"tax:{tax_number}"
        return f"name:{name.lower().strip()}"


def normalize_awards(database_url: str, batch_size: int = 100) -> dict:
    """
    Normalize awards_raw data into relational tables.

    Args:
        database_url: PostgreSQL connection string
        batch_size: Number of records to process in each batch

    Returns:
        dict with statistics about the normalization process
    """
    normalizer = AwardsNormalizer(database_url)
    return normalizer.normalize_all(batch_size)


def clear_normalized_tables(database_url: str):
    """Clear all normalized tables (for re-running normalization)."""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # Delete in order respecting foreign keys
        session.query(AwardSupplier).delete()
        session.query(Award).delete()
        session.query(ProcurementProcedure).delete()
        session.query(Supplier).delete()
        session.query(ContractingAuthority).delete()
        session.commit()

    logger.info("Cleared all normalized tables")
