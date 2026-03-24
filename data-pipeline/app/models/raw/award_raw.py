from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Numeric,
    Text
)
from ..base import Base


class AwardRaw(Base):
    __tablename__ = "award_raw"

    # === Technical / metadata ===
    id = Column(Integer, primary_key=True)
    source_country = Column(String(10), nullable=False)  # BA, AL, MK...
    source_system = Column(String(50), nullable=False)   # EJN, OpenProcurement...
    source_file = Column(String(255), nullable=True)     # original XLSX/CSV
    import_batch_id = Column(String(50), nullable=True)
    imported_at = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, nullable=True)

    # === Award / Lot ===
    lot_name = Column(String(500), nullable=True)
    main_cpv_code = Column(String(255), nullable=True)
    value = Column(Numeric(18, 2), nullable=True)
    annual_value = Column(Numeric(18, 2), nullable=True)
    monthly_value = Column(Numeric(18, 2), nullable=True)

    # === Dates ===
    contract_date = Column(DateTime, nullable=True)
    master_agreement_start_date = Column(DateTime, nullable=True)
    master_agreement_end_date = Column(DateTime, nullable=True)

    # === Contracting authority (DENORMALIZED) ===
    contracting_authority_name = Column(String(500), nullable=True)
    contracting_authority_tax_number = Column(String(100), nullable=True)
    contracting_authority_city_name = Column(String(255), nullable=True)
    contracting_authority_type = Column(String(100), nullable=True)
    contracting_authority_activity_type_name = Column(String(255), nullable=True)
    contracting_authority_administrative_unit_type = Column(String(100), nullable=True)
    contracting_authority_administrative_unit_name = Column(String(255), nullable=True)

    # === Procedure ===
    procedure_name = Column(String(500), nullable=True)
    procedure_number = Column(String(100), nullable=True)
    procedure_type = Column(String(100), nullable=True)
    contract_type = Column(String(100), nullable=True)
    contract_category_name = Column(String(500), nullable=True)
    contract_subcategory_name = Column(String(500), nullable=True)

    # === Procedure flags ===
    has_lots = Column(Boolean, nullable=True)
    is_auction_online = Column(Boolean, nullable=True)
    is_master_agreement = Column(Boolean, nullable=True)
    is_defense_and_security = Column(Boolean, nullable=True)
    is_joint_procurement = Column(Boolean, nullable=True)
    is_on_behalf_procurement = Column(Boolean, nullable=True)
    completed_with_negotiation = Column(Boolean, nullable=True)
    preferential_treatment_used = Column(Boolean, nullable=True)
    eu_funds_used = Column(Boolean, nullable=True)
    legal_remedies_used = Column(Boolean, nullable=True)
    is_contract_concluded = Column(Boolean, nullable=True)
    allowed_subcontracting = Column(Boolean, nullable=True)

    # === Award criteria & offers ===
    award_criterion = Column(String(500), nullable=True)
    number_of_received_offers = Column(Integer, nullable=True)
    number_of_acceptable_offers = Column(Integer, nullable=True)
    lowest_acceptable_offer_value = Column(Numeric(18, 2), nullable=True)
    highest_acceptable_offer_value = Column(Numeric(18, 2), nullable=True)

    # === Subcontracting ===
    subcontracting_share = Column(Numeric(18, 2), nullable=True)
    subcontracting_value = Column(Numeric(18, 2), nullable=True)

    # === Regulation ===
    regulation_quote_name = Column(String(255), nullable=True)

    # === Free text / reasons ===
    reasons_for_negotiated_procedure = Column(Text, nullable=True)

    # === Supplier (DENORMALIZED) ===
    supplier_name = Column(String(500), nullable=True)
    supplier_tax_number = Column(String(100), nullable=True)
    supplier_is_foreign = Column(Boolean, nullable=True)
    supplier_country = Column(String(100), nullable=True)
    supplier_size_category = Column(String(100), nullable=True)
    supplier_is_registered = Column(Boolean, nullable=True)
    other_suppliers_in_group = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<AwardRaw(id={self.id}, "
            f"authority='{self.contracting_authority_name}', "
            f"supplier='{self.supplier_name}', "
            f"value={self.value}, "
            f"contract_date={self.contract_date})>"
        )
