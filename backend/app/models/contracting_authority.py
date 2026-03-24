from sqlmodel import SQLModel, Field, Index
from typing import Optional


class ContractingAuthority(SQLModel, table=True):
    __tablename__ = "contracting_authority"

    id: Optional[int] = Field(default=None, primary_key=True)
    tax_number: str = Field(max_length=100, unique=True, index=True)
    name: str = Field(max_length=500)
    city: Optional[str] = Field(default=None, max_length=255)
    type: Optional[str] = Field(default=None, max_length=100)
    activity_type: Optional[str] = Field(default=None, max_length=255)
    admin_unit_type: Optional[str] = Field(default=None, max_length=100)
    admin_unit_name: Optional[str] = Field(default=None, max_length=255)

    __table_args__ = (
        Index('ix_contracting_authority_name', 'name'),
    )
