"""
API-based scraper for Republika Srpska Company Registry.
No authentication required - uses public API endpoint at bizreg.esrpska.com.
Uses POST requests with jTable offset-based pagination.
"""

import logging
import re
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ._base_company_registry_scraper import BaseCompanyRegistryScraper, USER_AGENT

logger = logging.getLogger(__name__)

# Form body sent with every POST request (static search criteria: all entities)
RS_FORM_BODY = "term=&opstinaId=0&osnivac=&djelatnostId=0"


class BACompanyRegistryRSScraper(BaseCompanyRegistryScraper):
    """
    Scraper for Republika Srpska company registry (bizreg.esrpska.com).
    Uses public API - no authentication required.
    POST-based with jTable offset pagination.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.legal_entities_endpoint = config.get("legal_entities_endpoint")

    @property
    def session(self) -> requests.Session:
        """Session with retry adapter for the slow RS server."""
        if self._session is None:
            self._session = requests.Session()
            retry = Retry(
                total=3,
                backoff_factor=2,
                status_forcelist=[502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        return self._session

    # ---------- Request override ----------

    def _make_request(self, endpoint: str, params: dict[str, Any], headers: dict[str, str]) -> requests.Response:
        """POST with form body and jTable query params."""
        return self.session.post(
            endpoint,
            params=params,
            data=RS_FORM_BODY,
            headers=headers,
            timeout=self.request_timeout
        )

    # ---------- Headers ----------

    def _get_base_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://bizreg.esrpska.com",
            "Referer": "http://bizreg.esrpska.com/",
        }

    def _get_data_headers(self) -> dict[str, str]:
        return self._get_base_headers()

    # ---------- Endpoint & params ----------

    def _get_entities_endpoint(self) -> str:
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
        """Build jTable query params. year/legal_type/search_type are ignored for RS."""
        return {
            "jtStartIndex": page * page_size,
            "jtPageSize": page_size,
        }

    def _update_params_for_page(
        self,
        params: dict[str, Any],
        page: int,
        page_size: int
    ) -> dict[str, Any]:
        """Offset-based pagination: jtStartIndex = page * page_size."""
        params = params.copy()
        params["jtStartIndex"] = page * page_size
        params["jtPageSize"] = page_size
        return params

    # ---------- Response parsing ----------

    def _extract_total_count(self, response_data: dict[str, Any]) -> int:
        if response_data.get("Result") != "OK":
            logger.error("RS API returned non-OK result: %s", response_data.get("Result"))
            return 0
        return response_data.get("TotalRecordCount", 0)

    def _extract_entities_from_response(self, response_data: dict[str, Any]) -> list[dict[str, Any]]:
        if response_data.get("Result") != "OK":
            logger.error("RS API returned non-OK result: %s", response_data.get("Result"))
            return []
        return response_data.get("Records", [])

    # ---------- Field transformation ----------

    @staticmethod
    def _parse_sjediste(sjediste: str | None) -> tuple[str, str]:
        """
        Parse Sjediste field into (municipality, address).
        Format examples: " , Municipality, City" or "Street, Municipality, City"
        Returns (municipality, address) where address is the first part.
        """
        if not sjediste:
            return ("", "")

        parts = [p.strip() for p in sjediste.split(",")]

        if len(parts) >= 3:
            address = parts[0] if parts[0] else ""
            municipality = parts[1] if parts[1] else ""
            return (municipality, address)
        elif len(parts) == 2:
            return (parts[1], parts[0])
        else:
            return ("", sjediste.strip())

    @staticmethod
    def _parse_djelatnost(djelatnost: str | None) -> tuple[str, str]:
        """
        Parse PreteznaDjelatnost into (activity_code, description).
        Format: "52.270 Some description text"
        """
        if not djelatnost:
            return ("", "")

        match = re.match(r"^([\d.]+)\s+(.*)", djelatnost.strip())
        if match:
            return (match.group(1), match.group(2))
        return ("", djelatnost.strip())

    def _transform_entity(self, entity: dict[str, Any]) -> dict[str, Any]:
        """Map RS API fields to common schema expected by the loader."""
        municipality, address = self._parse_sjediste(entity.get("Sjediste"))
        activity_code, activity_desc = self._parse_djelatnost(entity.get("PreteznaDjelatnost"))

        jib = entity.get("JIB")
        if jib is not None:
            jib = str(jib)

        return {
            "jib": jib,
            "shortName": entity.get("KratakNaziv") or "",
            "longName": entity.get("PoslovnoIme") or "",
            "municipality": municipality,
            "county": "",
            "address": address,
            "letterOfActivity": "",
            "activityCode": activity_code,
            "activityCodeDescription": activity_desc,
            "registrationDateTime": None,
            "isPublicEntity": False,
        }

    # ---------- Main export override ----------

    def run_full_export(
        self,
        year: int = 2019,
        search_type: int = 2,
        legal_types: list[int] | None = None,
        is_public_entity: bool = False,
        fetch_details: bool = False
    ) -> Path | None:
        """
        RS-specific export: no legal_type iteration, no detail fetching.
        Transforms RS entities to common schema before saving.
        """
        try:
            if not self.authenticate():
                raise RuntimeError("Authentication failed")

            logger.info("Fetching all RS legal entities...")
            entities = self.get_all_legal_entities()

            if entities is None:
                raise RuntimeError("Failed to fetch RS entities")

            if not entities:
                raise RuntimeError("No RS entities found")

            # Filter out deleted ("brisan") companies
            total_before = len(entities)
            entities = [
                e for e in entities
                if not (e.get("StatusPoslovniSubjekatOpis") or "").lower().startswith("brisan")
            ]
            filtered_count = total_before - len(entities)
            if filtered_count:
                logger.info("Filtered out %d deleted (brisan) entities", filtered_count)

            logger.info("Transforming %d RS entities to common schema...", len(entities))
            transformed = [self._transform_entity(e) for e in entities]

            filename = "legal_entities_rs.json"
            return self.save_to_json(transformed, filename)

        finally:
            self._cleanup()
