from sqlalchemy import Column, Integer, String, Boolean, Index
from ..base import Base


class Supplier(Base):
    """Normalized supplier (vendor) entity."""
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True)
    tax_number = Column(String(100), nullable=True, index=True)
    name = Column(String(500), nullable=False)
    country = Column(String(100), nullable=True)
    is_foreign = Column(Boolean, nullable=True)
    size_category = Column(String(100), nullable=True)
    is_registered = Column(Boolean, nullable=True)

    __table_args__ = (
        Index('ix_supplier_name', 'name'),
        # Composite unique constraint: same supplier can have different entries if unregistered
        Index('ix_supplier_tax_name', 'tax_number', 'name'),
    )

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', tax_number='{self.tax_number}')>"
