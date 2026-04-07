from sqlmodel import SQLModel, Field, Index
from typing import Optional


class Supplier(SQLModel, table=True):
    __tablename__ = "supplier"

    id: Optional[int] = Field(default=None, primary_key=True)
    tax_number: Optional[str] = Field(default=None, max_length=100, index=True)
    name: str = Field(max_length=500)
    country: Optional[str] = Field(default=None, max_length=100)
    is_foreign: Optional[bool] = Field(default=None)
    size_category: Optional[str] = Field(default=None, max_length=100)
    is_registered: Optional[bool] = Field(default=None)

    __table_args__ = (
        Index('ix_supplier_name', 'name'),
        Index('ix_supplier_tax_name', 'tax_number', 'name'),
    )
