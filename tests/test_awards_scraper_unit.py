"""
Unit tests for BAawardsScraper class.
Tests individual methods without making actual API calls.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add data-pipeline to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "data-pipeline"))

from app.pipeline.extract.ba.awards_scraper import BAawardsScraper


class TestBAawardsScraperUnit:
    """Unit tests for BAawardsScraper methods."""

    @pytest.fixture
    def mock_config(self):
        """Fixture for mock configuration."""
        return {
            "download_directory": "test_downloads",
            "BA_EXPORT_ENDPOINT": "https://api.test.ejn.gov.ba/Api/Awards/GetExport",
            "max_retries": 3,
            "retry_delay": 1,
            "request_timeout": 30,
            "from_date": "2025-12-11T23:00:00.000Z",
            "to_date": "2025-12-13T23:00:00.000Z"
        }

    @pytest.fixture
    def scraper(self, mock_config, tmp_path):
        """Fixture for BAawardsScraper instance with temporary directory."""
        mock_config["download_directory"] = str(tmp_path)
        return BAawardsScraper(mock_config)

    def test_get_default_date_range(self, scraper):
        """Test default date range generation."""
        from_date, to_date = scraper._get_default_date_range()

        # Should return dates in ISO format with timezone
        assert from_date.endswith("T23:00:00.000Z")
        assert to_date.endswith("T23:00:00.000Z")

        # Parse dates
        from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

        # Verify date range (from_date should be before to_date)
        assert from_dt < to_dt

        # Verify approximate difference (should be 1 day)
        diff = to_dt - from_dt
        assert diff.days == 1

    def test_get_endpoint(self, scraper):
        """Test endpoint URL retrieval."""
        endpoint = scraper._get_endpoint()

        assert endpoint == "https://api.test.ejn.gov.ba/Api/Awards/GetExport"
        assert endpoint.startswith("https://")
        assert "GetExport" in endpoint

    def test_get_endpoint_missing_config(self, mock_config, tmp_path):
        """Test error when endpoint is missing from config."""
        mock_config["download_directory"] = str(tmp_path)
        del mock_config["BA_EXPORT_ENDPOINT"]

        scraper = BAawardsScraper(mock_config)

        with pytest.raises(ValueError, match="BA_EXPORT_ENDPOINT not found in config"):
            scraper._get_endpoint()

    def test_build_payload(self, scraper):
        """Test request payload construction."""
        payload = scraper._build_payload()

        # Check required fields
        assert "searchFromContractDate" in payload
        assert "searchUntilContractDate" in payload
        assert payload["searchFromContractDate"] == scraper.from_date
        assert payload["searchUntilContractDate"] == scraper.to_date

        # Check pagination
        assert payload["pageNumber"] == 1
        assert payload["pageSize"] == 10

        # Check search filters are initialized as empty
        assert payload["searchByLotIds"] == []
        assert payload["searchBySupplierIds"] == []
        assert payload["searchByContractingAuthorityIds"] == []

        # Check optional fields
        assert "sortColumns" in payload
        assert isinstance(payload["sortColumns"], list)

    def test_extract_download_url_success(self, scraper, capsys):
        """Test download URL extraction from response."""
        response_data = {
            "downloadUrl": "https://files.ejn.gov.ba/temp/test-file.xlsx",
            "status": "success"
        }

        url = scraper._extract_download_url(response_data)

        assert url == "https://files.ejn.gov.ba/temp/test-file.xlsx"

        # Check debug print output
        captured = capsys.readouterr()
        assert "Download Url" in captured.out
        assert "test-file.xlsx" in captured.out

    def test_extract_download_url_missing(self, scraper):
        """Test download URL extraction when URL is missing."""
        response_data = {
            "status": "error",
            "message": "No data found"
        }

        url = scraper._extract_download_url(response_data)

        assert url is None

    def test_get_headers(self, scraper):
        """Test HTTP headers construction."""
        headers = scraper._get_headers()

        # Check base headers
        assert "Accept" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

        # Check EJN-specific headers
        assert headers["Client-App"] == "Community"
        assert headers["Origin"] == "https://next.ejn.gov.ba"
        assert headers["Referer"] == "https://next.ejn.gov.ba/"

    def test_dates_from_config(self, mock_config, tmp_path):
        """Test that dates are correctly loaded from config."""
        mock_config["download_directory"] = str(tmp_path)
        scraper = BAawardsScraper(mock_config)

        assert scraper.from_date == "2025-12-11T23:00:00.000Z"
        assert scraper.to_date == "2025-12-13T23:00:00.000Z"

    def test_dates_default_when_not_in_config(self, mock_config, tmp_path):
        """Test that default dates are used when not in config."""
        mock_config["download_directory"] = str(tmp_path)
        del mock_config["from_date"]
        del mock_config["to_date"]

        scraper = BAawardsScraper(mock_config)

        # Should have default dates
        assert scraper.from_date is not None
        assert scraper.to_date is not None
        assert scraper.from_date.endswith("T23:00:00.000Z")
        assert scraper.to_date.endswith("T23:00:00.000Z")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
