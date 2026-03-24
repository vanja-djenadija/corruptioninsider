from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..base import Base


class Award(Base):
    """Normalized award (contract) entity."""
    __tablename__ = "award"

    id = Column(Integer, primary_key=True)

    # Foreign keys
    contracting_authority_id = Column(Integer, ForeignKey('contracting_authority.id'), nullable=False, index=True)
    procedure_id = Column(Integer, ForeignKey('procurement_procedure.id'), nullable=False, index=True)

    # Award details
    lot_name = Column(String(500), nullable=True)
    main_cpv_code = Column(String(255), nullable=True)

    # Values
    value = Column(Numeric(18, 2), nullable=True)
    annual_value = Column(Numeric(18, 2), nullable=True)
    monthly_value = Column(Numeric(18, 2), nullable=True)

    # Dates
    contract_date = Column(DateTime, nullable=True, index=True)
    master_agreement_start_date = Column(DateTime, nullable=True)
    master_agreement_end_date = Column(DateTime, nullable=True)

    # Offers
    number_of_received_offers = Column(Integer, nullable=True)
    number_of_acceptable_offers = Column(Integer, nullable=True)
    lowest_acceptable_offer_value = Column(Numeric(18, 2), nullable=True)
    highest_acceptable_offer_value = Column(Numeric(18, 2), nullable=True)

    # Flags
    eu_funds_used = Column(Boolean, nullable=True)
    completed_with_negotiation = Column(Boolean, nullable=True)
    preferential_treatment_used = Column(Boolean, nullable=True)
    legal_remedies_used = Column(Boolean, nullable=True)
    is_contract_concluded = Column(Boolean, nullable=True)

    # Subcontracting
    allowed_subcontracting = Column(Boolean, nullable=True)
    subcontracting_share = Column(Numeric(18, 2), nullable=True)
    subcontracting_value = Column(Numeric(18, 2), nullable=True)

    # Additional info
    regulation_quote_name = Column(String(255), nullable=True)
    reasons_for_negotiated_procedure = Column(Text, nullable=True)

    # Traceability
    source_country = Column(String(10), nullable=False)
    source_system = Column(String(50), nullable=False)
    raw_award_id = Column(Integer, nullable=True)  # Link back to awards_raw.id

    # Relationships
    contracting_authority = relationship("ContractingAuthority", backref="awards")
    procedure = relationship("ProcurementProcedure", backref="awards")
    suppliers = relationship("AwardSupplier", back_populates="award")

    __table_args__ = (
        Index('ix_award_value', 'value'),
        Index('ix_award_source', 'source_country', 'source_system'),
    )

    def __repr__(self):
        return f"<Award(id={self.id}, value={self.value}, contract_date={self.contract_date})>"
