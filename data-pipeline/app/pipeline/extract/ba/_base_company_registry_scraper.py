"""
Base class for Bosnia and Herzegovina Company Registry scrapers.
Provides common functionality for pagination, parallel fetching, and data saving.
"""

import json
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

from ....util.paths import resolve_path

logger = logging.getLogger(__name__)

# Default concurrency for parallel requests
DEFAULT_CONCURRENCY = 10

# User agent for all requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
)


class BaseCompanyRegistryScraper(ABC):
    """
    Base class for company registry scrapers.
    Handles session management, pagination, parallel fetching, and data saving.

    Can be used as a context manager:
        with Scraper(config) as scraper:
            scraper.authenticate()
            data = scraper.get_all_legal_entities(year=2019)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.download_dir = resolve_path(config.get("raw_directory", "data/raw/ba/company_registry"))
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.request_timeout = config.get("request_timeout", 60)

        self._session: requests.Session | None = None

    def __enter__(self) -> "BaseCompanyRegistryScraper":
        self._session = requests.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._cleanup()

    @property
    def session(self) -> requests.Session:
        """Lazy initialization of session."""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def authenticate(self) -> bool:
        """
        Authenticate with the API if required.
        Default implementation does nothing (no auth needed).
        Override in subclasses that require authentication.

        Returns:
            True if successful or not needed, False otherwise.
        """
        return True

    @property
    def is_authenticated(self) -> bool:
        """
        Check if authenticated.
        Override in subclasses that require authentication.
        """
        return True

    def get_all_legal_entities(
        self,
        year: int = 2019,
        search_type: int = 2,
        legal_type: int = 1,
        is_public_entity: bool = False,
        page_size: int | None = None
    ) -> list[dict[str, Any]] | None:
        """
        Fetch all legal entities for a given year using pagination.

        Args:
            year: The year to fetch data for
            search_type: Search type parameter
            legal_type: Legal entity type (1=business companies, 2=associations/foundations, etc.)
            is_public_entity: Filter for public entities
            page_size: Number of records per page

        Returns:
            List of legal entity dictionaries, or None if failed.
        """
        if page_size is None:
            page_size = self.config.get("page_size", 1000)

        params = self._build_entities_params(
            year=year,
            search_type=search_type,
            legal_type=legal_type,
            is_public_entity=is_public_entity,
            page_size=10,
            page=0,
            include_count=True
        )

        logger.info("Fetching legal entities count...")

        try:
            response = self._make_request(
                self._get_entities_endpoint(),
                params=params,
                headers=self._get_data_headers()
            )
            response.raise_for_status()

            data = response.json()
            total_count = self._extract_total_count(data)
            logger.info("Total entities: %d", total_count)

            if total_count == 0:
                logger.warning("No entities found")
                return []

            return self._fetch_all_pages(params, page_size, total_count)

        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch legal entities: %s", e)
            return None

    def _fetch_all_pages(
        self,
        params: dict[str, Any],
        page_size: int,
        total_count: int
    ) -> list[dict[str, Any]]:
        """Fetch all pages of legal entities."""
        all_entities = []
        total_pages = (total_count + page_size - 1) // page_size

        for page in range(total_pages):
            # Update params for pagination
            updated_params = self._update_params_for_page(params, page, page_size)

            logger.info(
                "Fetching page %d/%d (%d entities per page)...",
                page + 1, total_pages, page_size
            )

            response = self._make_request(
                self._get_entities_endpoint(),
                params=updated_params,
                headers=self._get_data_headers()
            )
            response.raise_for_status()

            data = response.json()
            entities = self._extract_entities_from_response(data)
            all_entities.extend(entities)

            logger.info(
                "Fetched %d entities (total so far: %d)",
                len(entities), len(all_entities)
            )

            if len(entities) < page_size:
                break

        logger.info("[SUCCESS] Fetched %d legal entities total", len(all_entities))
        return all_entities

    def get_entity_details(self, entity_id: int) -> dict[str, Any] | None:
        """
        Fetch complete details for a single entity by ID.

        Args:
            entity_id: The entity ID to fetch

        Returns:
            Entity details dictionary, or None if failed.
        """
        url = f"{self._get_entities_endpoint()}/{entity_id}"

        try:
            response = self.session.get(
                url,
                headers=self._get_data_headers(),
                timeout=self.request_timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.warning("Failed to fetch entity %d: %s", entity_id, e)
            return None

    def fetch_all_entity_details(
        self,
        entities: list[dict[str, Any]],
        concurrency: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch complete details for all entities using parallel requests.

        Args:
            entities: List of entities with 'id' field
            concurrency: Number of parallel requests (default: 10)

        Returns:
            List of complete entity details.
        """
        if concurrency is None:
            concurrency = self.config.get("concurrency", DEFAULT_CONCURRENCY)

        # Extract IDs from entities
        entity_ids = [e.get("id") for e in entities if e.get("id")]
        total = len(entity_ids)

        if total == 0:
            logger.warning("No entity IDs found to fetch details for")
            return entities

        logger.info(
            "Fetching details for %d entities with %d parallel requests...",
            total, concurrency
        )

        detailed_entities = []
        failed_count = 0
        completed = 0

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Submit all tasks
            future_to_id = {
                executor.submit(self.get_entity_details, eid): eid
                for eid in entity_ids
            }

            # Process completed tasks
            for future in as_completed(future_to_id):
                entity_id = future_to_id[future]
                completed += 1

                try:
                    result = future.result()
                    if result:
                        detailed_entities.append(result)
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.warning("Error fetching entity %d: %s", entity_id, e)
                    failed_count += 1

                # Log progress every 1000 entities
                if completed % 1000 == 0 or completed == total:
                    logger.info(
                        "Progress: %d/%d entities fetched (%d failed)",
                        completed, total, failed_count
                    )

        logger.info(
            "[SUCCESS] Fetched details for %d entities (%d failed)",
            len(detailed_entities), failed_count
        )
        return detailed_entities

    def save_to_json(self, data: Any, filename: str) -> Path:
        """
        Save data to a JSON file in the download directory.

        Args:
            data: Data to save
            filename: Name of the file (without path)

        Returns:
            Path to the saved file.
        """
        file_path = self.download_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("[SUCCESS] Saved data to %s", file_path)
        return file_path

    def run_full_export(
        self,
        year: int = 2019,
        search_type: int = 2,
        legal_types: list[int] | None = None,
        is_public_entity: bool = False,
        fetch_details: bool = True
    ) -> Path | None:
        """
        Main entry point: authenticate, fetch all legal entities, and save to JSON.

        Args:
            year: The year to fetch data for
            search_type: Search type parameter
            legal_types: List of legal entity type IDs to fetch (default: [1, 2])
            is_public_entity: Filter for public entities
            fetch_details: If True, fetch complete details for each entity

        Returns:
            Path to the saved JSON file, or None if failed.
        """
        if legal_types is None:
            legal_types = [1, 2]

        try:
            if not self.authenticate():
                raise RuntimeError("Authentication failed")

            all_entities = []
            for legal_type in legal_types:
                logger.info("Fetching legal entity type %d...", legal_type)
                entities = self.get_all_legal_entities(
                    year=year,
                    search_type=search_type,
                    legal_type=legal_type,
                    is_public_entity=is_public_entity
                )

                if entities is None:
                    logger.warning("Failed to fetch entities for legal type %d, skipping", legal_type)
                    continue

                logger.info("Fetched %d entities for legal type %d", len(entities), legal_type)
                all_entities.extend(entities)

            if not all_entities:
                raise RuntimeError("Failed to fetch entities for any legal type")

            logger.info("Total entities across all types: %d", len(all_entities))

            # Fetch complete details for each entity
            if fetch_details:
                logger.info("Fetching complete details for each entity...")
                all_entities = self.fetch_all_entity_details(all_entities)

            filename = f"legal_entities_{year}.json"
            return self.save_to_json(all_entities, filename)

        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Close the requests session."""
        if self._session is not None:
            self._session.close()
            self._session = None
            logger.info("[SUCCESS] Session closed")

    # ---------- Helper methods that can be overridden ----------

    def _make_request(self, endpoint: str, params: dict[str, Any], headers: dict[str, str]) -> requests.Response:
        """
        Make an HTTP request. Default is GET.
        Override in subclasses that need POST or different request methods.
        """
        return self.session.get(endpoint, params=params, headers=headers, timeout=self.request_timeout)

    def _extract_total_count(self, response_data: dict[str, Any]) -> int:
        """
        Extract total count from initial response.
        Default implementation looks for 'count' field.
        Override if API uses different field name.
        """
        return response_data.get("count", 0)

    def _extract_entities_from_response(self, response_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract entities list from API response.
        Default implementation checks if response is list or has 'resultList' field.
        Override if API uses different structure.
        """
        if isinstance(response_data, list):
            return response_data
        return response_data.get("resultList", [])

    def _update_params_for_page(
        self,
        params: dict[str, Any],
        page: int,
        page_size: int
    ) -> dict[str, Any]:
        """
        Update request parameters for a specific page.
        Default implementation updates PageSize, Page, and includeCount.
        Override if API uses different parameter names.
        """
        params = params.copy()
        params["PageSize"] = page_size
        params["Page"] = page
        params["includeCount"] = "false"
        return params

    # ---------- Abstract methods - must be implemented by subclasses ----------

    @abstractmethod
    def _get_base_headers(self) -> dict[str, str]:
        """
        Returns base headers for all requests.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _get_data_headers(self) -> dict[str, str]:
        """
        Returns headers for data API requests.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _get_entities_endpoint(self) -> str:
        """
        Returns the endpoint URL for fetching entities.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _build_entities_params(
        self,
        year: int,
        search_type: int,
        legal_type: int,
        is_public_entity: bool,
        page_size: int,
        page: int,
        include_count: bool
    ) -> dict[str, Any]:
        """
        Build request parameters for fetching entities.
        Must be implemented by subclasses.

        Args:
            year: The year to fetch data for
            search_type: Search type parameter
            legal_type: Legal entity type
            is_public_entity: Filter for public entities
            page_size: Number of records per page
            page: Page number
            include_count: Whether to include total count in response

        Returns:
            Dictionary of request parameters
        """
        pass
