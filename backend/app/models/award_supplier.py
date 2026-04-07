from sqlmodel import SQLModel, Field, Index
from typing import Optional


class AwardSupplier(SQLModel, table=True):
    __tablename__ = "award_supplier"

    id: Optional[int] = Field(default=None, primary_key=True)
    award_id: int = Field(foreign_key="award.id", index=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    role: str = Field(default="primary", max_length=50)

    __table_args__ = (
        Index('ix_award_supplier_role', 'role'),
    )
