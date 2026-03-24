from sqlalchemy import Column, Integer, String, Boolean, Index
from ..base import Base


class ProcurementProcedure(Base):
    """Normalized procurement procedure entity."""
    __tablename__ = "procurement_procedure"

    id = Column(Integer, primary_key=True)
    number = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=True)
    type = Column(String(100), nullable=True)
    contract_type = Column(String(100), nullable=True)
    category = Column(String(500), nullable=True)
    subcategory = Column(String(500), nullable=True)

    # Procedure characteristics
    has_lots = Column(Boolean, nullable=True)
    is_auction_online = Column(Boolean, nullable=True)
    is_master_agreement = Column(Boolean, nullable=True)
    is_defense_and_security = Column(Boolean, nullable=True)
    is_joint_procurement = Column(Boolean, nullable=True)
    award_criterion = Column(String(500), nullable=True)

    __table_args__ = (
        Index('ix_procurement_procedure_type', 'type'),
    )

    def __repr__(self):
        return f"<ProcurementProcedure(id={self.id}, number='{self.number}', type='{self.type}')>"
