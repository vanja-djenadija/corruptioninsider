"""
API-based exporter for Bosnia and Herzegovina awards (EJN).
No Selenium. Uses official export endpoint.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any

from ..api_scraper import ApiScraper

logger = logging.getLogger(__name__)


class BAwardsScraper(ApiScraper):
    """
    Export awards data from EJN using official API endpoint.
    """

    # ------------------------------------------------------------------
    # Required abstract methods
    # ------------------------------------------------------------------

    def _get_default_date_range(self) -> Tuple[str, str]:
        """
        Default: contracts from 2 days ago to 1 day ago (23:00 UTC).
        """
        today = datetime.now().date()

        from_date = (
            today - timedelta(days=2)
        ).strftime("%Y-%m-%d") + "T23:00:00.000Z"

        to_date = (
            today - timedelta(days=1)
        ).strftime("%Y-%m-%d") + "T23:00:00.000Z"

        return from_date, to_date

    def _get_endpoint(self) -> str:
        """Returns the EJN API endpoint URL from config."""
        endpoint = self.config.get("ba_export_endpoint")
        if not endpoint:
            raise ValueError("ba_export_endpoint not found in config")
        return endpoint

    def _build_payload(self) -> Dict[str, Any]:
        """Builds the request payload for the EJN export API."""
        return {
            "searchByLotIds": [],
            "searchByRegulationQuoteIds": [],
            "searchByContractingAuthorityIds": [],
            "searchBySupplierIds": [],
            "searchByUnregisteredSupplierIds": [],
            "searchByProcedureIds": [],
            "searchByCpvCodeIds": [],
            "searchByNoticeIds": [],
            "searchByRegulationQuoteNegotiatedProcedureBasisIds": [],
            "searchByContractTypes": [],
            "searchByProcedureTypes": [],
            "searchByAwardCriteria": [],
            "searchFromContractDate": self.from_date,
            "searchUntilContractDate": self.to_date,
            "pageNumber": 1,
            "pageSize": 10,
            "sortColumns": [],
            "searchByParticipatingContractingAuthorityIds": None,
            "searchByInternationalAnnouncement": None,
        }

    def _extract_download_url(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extracts download URL from the API response."""
        download_url = response_data.get("downloadUrl")
        if download_url:
            logger.debug("Download URL: %s", download_url)
        return download_url

    def _get_headers(self) -> Dict[str, str]:
        """Returns EJN-specific headers."""
        headers = super()._get_headers()
        headers.update({
            "Client-App": "Community",
            "Origin": "https://next.ejn.gov.ba",
            "Referer": "https://next.ejn.gov.ba/",
        })
        return headers
