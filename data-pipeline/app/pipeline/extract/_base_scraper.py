"""
Base scraper class for all award portal scrapers.
Contains common retry logic, configuration validation, and date handling.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all award portal scrapers.
    Provides common functionality for retry logic, config validation, and date handling.
    """

    # Non-retryable exceptions (configuration/programming errors)
    NON_RETRYABLE_EXCEPTIONS = (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        NotImplementedError,
    )

    def __init__(self, config: Dict) -> None:
        self.config = config
        self._validate_config(config)

        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 5)

        self.from_date, self.to_date = self._parse_dates(config)

        logger.info(f"{self.__class__.__name__} configured")
        self._log_configuration()

    def _validate_config(self, config: Dict) -> None:
        """Validate common configuration parameters."""
        max_retries = config.get("max_retries", 3)
        if not isinstance(max_retries, int) or max_retries < 1:
            raise ValueError(f"max_retries must be a positive integer, got: {max_retries}")

        retry_delay = config.get("retry_delay", 5)
        if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            raise ValueError(f"retry_delay must be a non-negative number, got: {retry_delay}")

    def _parse_dates(self, config: Dict) -> Tuple[str, str]:
        """Parse date range from config or use defaults."""
        if config.get("from_date") and config.get("to_date"):
            return config["from_date"], config["to_date"]
        return self._get_default_date_range()

    def run(self):
        """
        Public entry point for scraper.
        Handles retries and lifecycle with exponential backoff.
        """
        self._before_run()

        try:
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(f"Export attempt {attempt}/{self.max_retries}")
                    result = self._perform_export()
                    if result is not None:
                        return result
                except self.NON_RETRYABLE_EXCEPTIONS:
                    logger.error(
                        "Non-retryable exception encountered, failing immediately",
                        exc_info=True,
                    )
                    raise
                except Exception as e:
                    if not self._should_retry(e, attempt):
                        raise

                    logger.warning(
                        f"Attempt {attempt} failed: {type(e).__name__}: {e}",
                        exc_info=True,
                    )

                    if attempt < self.max_retries:
                        # Exponential backoff: base_delay * 2^(attempt - 1)
                        delay = self.retry_delay * (2 ** (attempt - 1))
                        logger.info(f"Retrying in {delay}s with exponential backoff")
                        time.sleep(delay)

            raise RuntimeError("All export attempts failed")

        finally:
            self._cleanup()

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if the exception should trigger a retry.
        Can be overridden by subclasses for custom retry logic.
        """
        return True

    def _before_run(self) -> None:
        """
        Hook called before the retry loop starts.
        Can be overridden by subclasses for initialization.
        """
        pass

    def _cleanup(self) -> None:
        """
        Hook called after the retry loop ends.
        Can be overridden by subclasses for cleanup.
        """
        pass

    # ---------- Abstract API ----------

    @abstractmethod
    def _get_default_date_range(self) -> Tuple[str, str]:
        """
        Returns default (from_date, to_date) tuple.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _perform_export(self):
        """
        Performs the actual export operation.
        Must be implemented by subclasses.

        Must return:
        - path to downloaded file
        OR
        - list of paths
        """
        pass

    @abstractmethod
    def _log_configuration(self) -> None:
        """
        Logs the scraper configuration.
        Must be implemented by subclasses.
        """
        pass
