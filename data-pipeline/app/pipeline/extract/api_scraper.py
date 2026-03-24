"""
API-based scraper class for award portal scrapers.
"""

import logging
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

import requests
from requests.exceptions import HTTPError

from ._base_scraper import BaseScraper
from ...util.paths import resolve_path

logger = logging.getLogger(__name__)


class ApiScraper(BaseScraper):
    """
    Abstract base class for API-based award portal scrapers.
    """

    def __init__(self, config: Dict) -> None:
        # Initialize API-specific attributes before calling super().__init__
        self.download_dir = resolve_path(config.get("raw_directory", "data/raw"))
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.request_timeout = config.get("request_timeout", 60)
        self.session = requests.Session()

        # Validate API-specific config
        self._validate_api_config(config)

        # Call parent __init__ which handles common config
        super().__init__(config)

    def _validate_api_config(self, config: Dict) -> None:
        """Validate API-specific configuration parameters."""
        request_timeout = config.get("request_timeout", 60)
        if not isinstance(request_timeout, (int, float)) or request_timeout <= 0:
            raise ValueError(f"request_timeout must be a positive number, got: {request_timeout}")

        raw_directory = config.get("raw_directory", "data/raw")
        if not isinstance(raw_directory, str) or not raw_directory.strip():
            raise ValueError(f"raw_directory must be a non-empty string, got: {raw_directory}")

    def _log_configuration(self) -> None:
        logger.info(
            f"""
{'=' * 60}
Scraper configuration:
  Download dir: {self.download_dir}
  Request timeout: {self.request_timeout}s
  Max retries: {self.max_retries}
  Retry delay: {self.retry_delay}s
  Date range: {self.from_date} to {self.to_date}
{'=' * 60}
"""
        )

    # ---------- Lifecycle ----------

    def _cleanup(self) -> None:
        """Close the requests session."""
        if self.session:
            try:
                self.session.close()
                logger.info("[SUCCESS] Session closed")
            finally:
                self.session = None

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Override retry logic to handle HTTP-specific errors.
        Don't retry client errors (4xx).
        """
        if isinstance(exception, HTTPError):
            if exception.response is not None and 400 <= exception.response.status_code < 500:
                logger.error(
                    f"Client error {exception.response.status_code}, not retrying",
                    exc_info=True,
                )
                return False
        return True

    # ---------- Internals ----------

    def _perform_export(self) -> Path:
        """
        Executes the API export workflow.
        Returns path to downloaded file.
        """
        endpoint = self._get_endpoint()
        payload = self._build_payload()
        headers = self._get_headers()

        logger.info(
            "Requesting export from %s to %s",
            self.from_date,
            self.to_date,
        )

        response = self.session.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=self.request_timeout,
        )

        response.raise_for_status()
        data = response.json()

        download_url = self._extract_download_url(data)
        if not download_url:
            raise RuntimeError("Export API did not return a valid download URL")

        logger.info("Download URL received: %s", download_url)

        return self._download_file(download_url)

    def _download_file(self, url: str) -> Path:
        """
        Downloads a file from the given URL.
        Returns the path to the downloaded file.
        """
        response = self.session.get(url, stream=True, timeout=self.request_timeout)
        response.raise_for_status()

        filename = self._extract_filename(url, response)
        file_path = self.download_dir / filename

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info("[SUCCESS] File downloaded: %s", file_path)
        return file_path

    def _extract_filename(self, url: str, response: requests.Response) -> str:
        """
        Generates filename based on current date in format YEAR-MONTH-DAY.xlsx
        Can be overridden by subclasses for custom logic.
        """
        # Get file extension from Content-Disposition header or URL
        extension = ".xlsx"  # Default extension

        if "Content-Disposition" in response.headers:
            content_disp = response.headers["Content-Disposition"]
            if "filename=" in content_disp:
                original_filename = content_disp.split("filename=")[-1].strip('"')
                # Extract extension from original filename
                if "." in original_filename:
                    extension = "." + original_filename.rsplit(".", 1)[-1]
        else:
            # Extract extension from URL
            url_filename = url.split("/")[-1]
            if "." in url_filename:
                extension = "." + url_filename.rsplit(".", 1)[-1]

        # Generate date-based filename: YEAR-MONTH-DAY.extension
        today = datetime.now()
        filename = f"{today.year:04d}-{today.month:02d}-{today.day:02d}{extension}"

        return filename

    def _get_headers(self) -> Dict[str, str]:
        """
        Returns default headers for API requests.
        Can be overridden by subclasses.
        """
        return {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

    # ---------- Abstract API ----------

    @abstractmethod
    def _get_endpoint(self) -> str:
        """
        Returns the API endpoint URL.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _build_payload(self) -> Dict[str, Any]:
        """
        Builds the request payload for the export API.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _extract_download_url(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        Extracts the download URL from the API response.
        Must be implemented by subclasses.
        Returns None if URL cannot be extracted.
        """
        pass
