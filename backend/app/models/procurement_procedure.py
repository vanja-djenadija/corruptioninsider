from sqlmodel import SQLModel, Field, Index
from typing import Optional


class ProcurementProcedure(SQLModel, table=True):
    __tablename__ = "procurement_procedure"

    id: Optional[int] = Field(default=None, primary_key=True)
    number: str = Field(max_length=100, unique=True, index=True)
    name: Optional[str] = Field(default=None, max_length=500)
    type: Optional[str] = Field(default=None, max_length=100)
    contract_type: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=500)
    subcategory: Optional[str] = Field(default=None, max_length=500)

    # Procedure characteristics
    has_lots: Optional[bool] = Field(default=None)
    is_auction_online: Optional[bool] = Field(default=None)
    is_master_agreement: Optional[bool] = Field(default=None)
    is_defense_and_security: Optional[bool] = Field(default=None)
    is_joint_procurement: Optional[bool] = Field(default=None)
    award_criterion: Optional[str] = Field(default=None, max_length=500)

    __table_args__ = (
        Index('ix_procurement_procedure_type', 'type'),
    )
