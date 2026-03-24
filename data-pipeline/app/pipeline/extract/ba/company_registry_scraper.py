"""
API-based scraper for Bosnia and Herzegovina Company Registry (FIA).
Requires authentication via FIA identity API.
Fetches complete entity details including relations using parallel requests.
"""

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

from ._base_company_registry_scraper import BaseCompanyRegistryScraper, USER_AGENT

logger = logging.getLogger(__name__)

load_dotenv()


class BACompanyRegistryFIAScraper(BaseCompanyRegistryScraper):
    """
    Scraper for FIA (Financial-Intelligence Agency) company registry.
    Authenticates and fetches legal entity data.

    Can be used as a context manager:
        with BACompanyRegistryFIAScraper(config) as scraper:
            scraper.authenticate()
            data = scraper.get_all_legal_entities(year=2019)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)

        self.sign_in_endpoint = config.get("sign_in_endpoint")
        self.legal_entities_endpoint = config.get("legal_entities_endpoint")
        self.client_id = config.get("client_id")

        self._access_token: str | None = None

        self._email = os.getenv("FIA_EMAIL")
        self._password = os.getenv("FIA_PASSWORD")

        if not self._email or not self._password:
            raise ValueError("FIA_EMAIL and FIA_PASSWORD must be set in .env file")

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    def _get_base_headers(self) -> dict[str, str]:
        """Returns common headers for all requests."""
        return {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": USER_AGENT,
            "Accept-Language": "bs",
            "clientid": self.client_id,
        }

    def _get_auth_headers(self) -> dict[str, str]:
        """Returns headers for authentication requests."""
        headers = self._get_base_headers()
        headers["Content-Type"] = "application/json"
        headers["Referer"] = "https://identity.fia.ba/"
        return headers

    def _get_data_headers(self) -> dict[str, str]:
        """Returns headers for data API requests."""
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        headers = self._get_base_headers()
        headers["Origin"] = "https://fia.ba"
        headers["Referer"] = "https://fia.ba/"
        headers["Authorization"] = self._access_token
        return headers

    def _get_entities_endpoint(self) -> str:
        """Returns the endpoint URL for fetching entities."""
        return self.legal_entities_endpoint

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
        Build request parameters for FIA API.

        Args:
            year: The year to fetch data for
            search_type: Search type parameter
            legal_type: Legal entity type (1=business, 2=associations, etc.)
            is_public_entity: Filter for public entities
            page_size: Number of records per page
            page: Page number
            include_count: Whether to include total count in response

        Returns:
            Dictionary of request parameters
        """
        return {
            "PageSize": page_size,
            "includeCount": str(include_count).lower(),
            "legalEntityTypeId": legal_type,
            "Page": page,
            "year": year,
            "searchType": search_type,
            "isPublicEntity": str(is_public_entity).lower()
        }

    def authenticate(self) -> bool:
        """
        Authenticate with FIA identity API.

        Returns:
            True if successful, False otherwise.
        """
        payload = {
            "email": self._email,
            "password": self._password,
            "deviceToken": None,
            "redirectUrl": "https://fia.ba/bs"
        }

        logger.info("Signing in to FIA API...")

        try:
            response = self.session.post(
                self.sign_in_endpoint,
                json=payload,
                headers=self._get_auth_headers(),
                timeout=self.request_timeout
            )
            response.raise_for_status()

            data = response.json()
            self._access_token = data.get("accessToken") or data.get("token")

            if self._access_token:
                logger.info("[SUCCESS] Signed in to FIA API")
                return True

            logger.error("Sign in response did not contain access token")
            return False

        except requests.exceptions.RequestException as e:
            logger.error("Failed to sign in: %s", e)
            return False


# Backwards compatibility alias
BACompanyRegistryScraper = BACompanyRegistryFIAScraper
