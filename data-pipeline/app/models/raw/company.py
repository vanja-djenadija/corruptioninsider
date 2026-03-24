from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from ..base import Base


class Company(Base):
    __tablename__ = "company"
    __table_args__ = (
        UniqueConstraint('company_id', 'data_hash', name='uq_company_id_data_hash'),
    )

    # === Primary key ===
    id = Column(Integer, primary_key=True)

    # === Company identification ===
    company_id = Column(String(20), nullable=False, index=True)  # JIB
    data_hash = Column(String(64), nullable=False)  # SHA256 hash of all fields

    # === Company names ===
    company_short_name = Column(String(500), nullable=True)
    company_long_name = Column(Text, nullable=True)

    # === Data source ===
    source = Column(String(20), nullable=True, index=True)  # 'fia', 'rs', etc.

    # === Location ===
    municipality = Column(String(255), nullable=True)
    county = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)

    # === Business activity ===
    letter_of_activity = Column(String(10), nullable=True)
    activity_code = Column(String(50), nullable=True)
    activity_code_description = Column(String(500), nullable=True)

    # === Registration ===
    registration_date = Column(DateTime, nullable=True)

    # === Flags ===
    is_public_entity = Column(Boolean, nullable=True)

    # === Metadata ===
    imported_at = Column(DateTime, nullable=True)

    # === Relationships ===
    relations = relationship("CompanyRelation", back_populates="company")

    def __repr__(self):
        return (
            f"<Company(id={self.id}, "
            f"company_id={self.company_id}, "
            f"name='{self.company_short_name}')>"
        )


class CompanyRelation(Base):
    __tablename__ = "company_relation"
    __table_args__ = (
        UniqueConstraint('company_record_id', 'relation_type_id', 'full_name', 'data_hash',
                         name='uq_company_relation'),
    )

    # === Primary key ===
    id = Column(Integer, primary_key=True)

    # === Foreign key to company record ===
    company_record_id = Column(Integer, ForeignKey("company.id"), nullable=False)

    # === Deduplication ===
    data_hash = Column(String(64), nullable=False)  # SHA256 hash of relation fields

    # === Relation details ===
    relation_type_id = Column(Integer, nullable=True)  # 1=owner, 2=director
    full_name = Column(Text, nullable=True)  # Text for long names
    share = Column(Numeric(18, 2), nullable=True)  # Ownership share
    position = Column(String(255), nullable=True)  # e.g., "Direktor"

    # === Relationships ===
    company = relationship("Company", back_populates="relations")

    def __repr__(self):
        return (
            f"<CompanyRelation(id={self.id}, "
            f"company_record_id={self.company_record_id}, "
            f"name='{self.full_name}', "
            f"type={self.relation_type_id})>"
        )


class CompanyImportSkip(Base):
    """
    Tracks companies that were skipped during import and the reason why.
    """
    __tablename__ = "company_import_skip"

    # === Primary key ===
    id = Column(Integer, primary_key=True)

    # === Import batch info ===
    import_batch_id = Column(String(50), nullable=False, index=True)
    source_file = Column(String(255), nullable=True)

    # === Company identification (from source data) ===
    company_id = Column(String(20), nullable=True)  # JIB (may be null if that's why it was skipped)
    company_short_name = Column(String(500), nullable=True)
    company_long_name = Column(Text, nullable=True)

    # === Skip reason ===
    skip_reason = Column(String(100), nullable=False, index=True)  # e.g., 'MISSING_JIB', 'DUPLICATE'
    skip_details = Column(Text, nullable=True)  # Additional details about why it was skipped

    # === Original data (for debugging) ===
    raw_data = Column(Text, nullable=True)  # JSON of original entity data

    # === Metadata ===
    skipped_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return (
            f"<CompanyImportSkip(id={self.id}, "
            f"company_id={self.company_id}, "
            f"reason='{self.skip_reason}')>"
        )
