from sqlmodel import SQLModel, Field, Index
from typing import Optional
from datetime import datetime
from decimal import Decimal


class Award(SQLModel, table=True):
    __tablename__ = "award"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    contracting_authority_id: int = Field(foreign_key="contracting_authority.id", index=True)
    procedure_id: int = Field(foreign_key="procurement_procedure.id", index=True)

    # Award details
    lot_name: Optional[str] = Field(default=None, max_length=500)
    main_cpv_code: Optional[str] = Field(default=None, max_length=255)

    # Values
    value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=2)
    annual_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=2)
    monthly_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=2)

    # Dates
    contract_date: Optional[datetime] = Field(default=None, index=True)
    master_agreement_start_date: Optional[datetime] = Field(default=None)
    master_agreement_end_date: Optional[datetime] = Field(default=None)

    # Offers
    number_of_received_offers: Optional[int] = Field(default=None)
    number_of_acceptable_offers: Optional[int] = Field(default=None)
    lowest_acceptable_offer_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=2)
    highest_acceptable_offer_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=2)

    # Flags
    eu_funds_used: Optional[bool] = Field(default=None)
    completed_with_negotiation: Optional[bool] = Field(default=None)
    preferential_treatment_used: Optional[bool] = Field(default=None)
    legal_remedies_used: Optional[bool] = Field(default=None)
    is_contract_concluded: Optional[bool] = Field(default=None)

    # Subcontracting
    allowed_subcontracting: Optional[bool] = Field(default=None)
    subcontracting_share: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=2)
    subcontracting_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=2)

    # Additional info
    regulation_quote_name: Optional[str] = Field(default=None, max_length=255)
    reasons_for_negotiated_procedure: Optional[str] = Field(default=None)

    # Traceability
    source_country: str = Field(max_length=10)
    source_system: str = Field(max_length=50)
    raw_award_id: Optional[int] = Field(default=None)

    __table_args__ = (
        Index('ix_award_value', 'value'),
        Index('ix_award_source', 'source_country', 'source_system'),
    )
