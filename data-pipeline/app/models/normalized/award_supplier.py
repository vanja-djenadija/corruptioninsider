from sqlalchemy import Column, Integer, String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from ..base import Base


class AwardSupplier(Base):
    """Junction table for many-to-many relationship between awards and suppliers."""
    __tablename__ = "award_supplier"

    id = Column(Integer, primary_key=True)
    award_id = Column(Integer, ForeignKey('award.id'), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey('supplier.id'), nullable=False, index=True)
    role = Column(String(50), nullable=False, default='primary')  # 'primary' or 'consortium_member'

    # Relationships
    award = relationship("Award", back_populates="suppliers")
    supplier = relationship("Supplier", backref="award_links")

    __table_args__ = (
        UniqueConstraint('award_id', 'supplier_id', name='uq_award_supplier'),
        Index('ix_award_supplier_role', 'role'),
    )

    def __repr__(self):
        return f"<AwardSupplier(award_id={self.award_id}, supplier_id={self.supplier_id}, role='{self.role}')>"
