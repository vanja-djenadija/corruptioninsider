"""
Model for tracking scraper execution history.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Enum
)
import enum
from ..base import Base


class ExecutionStatus(enum.Enum):
    """Status of a scraper execution."""
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ScraperExecution(Base):
    """
    Tracks scraper execution history for auditing and debugging.
    """
    __tablename__ = "scraper_execution"

    id = Column(Integer, primary_key=True)

    # Scraper identification
    scraper_name = Column(String(100), nullable=False, index=True)
    source_country = Column(String(10), nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    # Status
    status = Column(
        Enum(ExecutionStatus),
        nullable=False,
        default=ExecutionStatus.RUNNING
    )
    error_message = Column(Text, nullable=True)

    # Statistics
    records_fetched = Column(Integer, nullable=True)
    records_inserted = Column(Integer, nullable=True)
    records_skipped = Column(Integer, nullable=True)

    # Output
    output_file = Column(String(500), nullable=True)

    # Parameters used
    parameters = Column(Text, nullable=True)  # JSON string of parameters

    def __repr__(self):
        return (
            f"<ScraperExecution(id={self.id}, "
            f"scraper='{self.scraper_name}', "
            f"status={self.status.value}, "
            f"started_at={self.started_at})>"
        )
