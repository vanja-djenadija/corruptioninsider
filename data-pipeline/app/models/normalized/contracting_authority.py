from sqlalchemy import Column, Integer, String, Index
from ..base import Base


class ContractingAuthority(Base):
    """Normalized contracting authority (buyer) entity."""
    __tablename__ = "contracting_authority"

    id = Column(Integer, primary_key=True)
    tax_number = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    city = Column(String(255), nullable=True)
    type = Column(String(100), nullable=True)
    activity_type = Column(String(255), nullable=True)
    admin_unit_type = Column(String(100), nullable=True)
    admin_unit_name = Column(String(255), nullable=True)

    __table_args__ = (
        Index('ix_contracting_authority_name', 'name'),
    )

    def __repr__(self):
        return f"<ContractingAuthority(id={self.id}, name='{self.name}', tax_number='{self.tax_number}')>"
