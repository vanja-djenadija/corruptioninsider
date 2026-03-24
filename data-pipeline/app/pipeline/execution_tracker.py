"""
Utility for tracking scraper execution history in the database.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models.raw.scraper_execution import ScraperExecution, ExecutionStatus

logger = logging.getLogger(__name__)


class ExecutionTracker:
    """
    Context manager for tracking scraper execution.

    Usage:
        with ExecutionTracker(database_url, "my_scraper", country="BA") as tracker:
            tracker.set_parameters({"year": 2019})
            # ... run scraper ...
            tracker.set_records_fetched(1000)
            tracker.set_records_inserted(950)
            tracker.set_records_skipped(50)
            tracker.set_output_file("/path/to/output.json")
    """

    def __init__(
        self,
        database_url: str,
        scraper_name: str,
        source_country: str | None = None
    ):
        self.database_url = database_url
        self.scraper_name = scraper_name
        self.source_country = source_country

        self._engine = create_engine(database_url)
        self._Session = sessionmaker(bind=self._engine)
        self._session = None
        self._execution: ScraperExecution | None = None

    def __enter__(self) -> "ExecutionTracker":
        self._session = self._Session()

        self._execution = ScraperExecution(
            scraper_name=self.scraper_name,
            source_country=self.source_country,
            started_at=datetime.now(),
            status=ExecutionStatus.RUNNING
        )
        self._session.add(self._execution)
        self._session.commit()

        logger.info(
            "Started execution tracking for %s (id=%d)",
            self.scraper_name, self._execution.id
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._execution is None:
            return

        self._execution.finished_at = datetime.now()

        if exc_type is not None:
            self._execution.status = ExecutionStatus.FAILED
            self._execution.error_message = "".join(
                traceback.format_exception(exc_type, exc_val, exc_tb)
            )
            logger.error(
                "Execution %d failed: %s",
                self._execution.id, exc_val
            )
        else:
            self._execution.status = ExecutionStatus.SUCCESS
            logger.info(
                "Execution %d completed successfully",
                self._execution.id
            )

        self._session.commit()
        self._session.close()

    @property
    def execution_id(self) -> int | None:
        return self._execution.id if self._execution else None

    def set_parameters(self, params: dict[str, Any]) -> None:
        """Store the parameters used for this execution."""
        if self._execution:
            self._execution.parameters = json.dumps(params, default=str)
            self._session.commit()

    def set_records_fetched(self, count: int) -> None:
        """Set the number of records fetched."""
        if self._execution:
            self._execution.records_fetched = count
            self._session.commit()

    def set_records_inserted(self, count: int) -> None:
        """Set the number of records inserted."""
        if self._execution:
            self._execution.records_inserted = count
            self._session.commit()

    def set_records_skipped(self, count: int) -> None:
        """Set the number of records skipped."""
        if self._execution:
            self._execution.records_skipped = count
            self._session.commit()

    def set_output_file(self, path: str) -> None:
        """Set the output file path."""
        if self._execution:
            self._execution.output_file = path
            self._session.commit()

    def set_error(self, error_message: str) -> None:
        """Manually set an error message."""
        if self._execution:
            self._execution.status = ExecutionStatus.FAILED
            self._execution.error_message = error_message
            self._session.commit()
