"""
Integration tests for BAawardsScraper class.
Tests the full scraper workflow with mocked API responses.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest
import requests

# Add data-pipeline to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "data-pipeline"))

from app.pipeline.extract.ba.awards_scraper import BAawardsScraper


class TestBAawardsScraperIntegration:
    """Integration tests for BAawardsScraper full workflow."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Fixture for mock configuration with temp directory."""
        return {
            "download_directory": str(tmp_path),
            "BA_EXPORT_ENDPOINT": "https://api.test.ejn.gov.ba/Api/Awards/GetExport",
            "max_retries": 3,
            "retry_delay": 0.1,  # Short delay for tests
            "request_timeout": 30,
            "from_date": "2025-12-11T23:00:00.000Z",
            "to_date": "2025-12-13T23:00:00.000Z"
        }

    @pytest.fixture
    def mock_api_response(self):
        """Fixture for mock API response."""
        return {
            "downloadUrl": "https://files.ejn.gov.ba/temp/test-awards.xlsx",
            "status": "success",
            "recordCount": 42
        }

    @pytest.fixture
    def mock_file_content(self):
        """Fixture for mock XLSX file content."""
        return b"PK\x03\x04" + b"\x00" * 100  # Mock XLSX header + data

    def test_full_export_workflow_success(self, mock_config, mock_api_response, mock_file_content):
        """Test successful full export workflow."""
        with patch("app.pipeline.extract.api_base_scraper.requests.Session") as mock_session_class:
            # Setup mock session
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # Mock POST response (API call)
            mock_post_response = Mock()
            mock_post_response.json.return_value = mock_api_response
            mock_post_response.raise_for_status = Mock()
            mock_session.post.return_value = mock_post_response

            # Mock GET response (file download)
            mock_get_response = Mock()
            mock_get_response.iter_content.return_value = [mock_file_content]
            mock_get_response.headers = {}
            mock_get_response.raise_for_status = Mock()
            mock_session.get.return_value = mock_get_response

            # Create scraper and run
            scraper = BAawardsScraper(mock_config)
            result = scraper.run()

            # Verify result
            assert result is not None
            assert isinstance(result, Path)
            assert result.exists()
            assert result.suffix == ".xlsx"

            # Verify file content
            assert result.read_bytes() == mock_file_content

            # Verify API was called correctly
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args

            # Check endpoint
            assert call_args[0][0] == "https://api.test.ejn.gov.ba/Api/Awards/GetExport"

            # Check payload
            payload = call_args[1]["json"]
            assert payload["searchFromContractDate"] == "2025-12-11T23:00:00.000Z"
            assert payload["searchUntilContractDate"] == "2025-12-13T23:00:00.000Z"

            # Check headers
            headers = call_args[1]["headers"]
            assert headers["Client-App"] == "Community"
            assert headers["Origin"] == "https://next.ejn.gov.ba"

            # Verify file was downloaded
            mock_session.get.assert_called_once_with(
                "https://files.ejn.gov.ba/temp/test-awards.xlsx",
                stream=True,
                timeout=30
            )

    def test_export_with_retry_on_network_error(self, mock_config, mock_api_response, mock_file_content):
        """Test that scraper retries on network errors."""
        with patch("app.pipeline.extract.api_base_scraper.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # First call fails, second succeeds
            mock_post_response = Mock()
            mock_post_response.json.return_value = mock_api_response
            mock_post_response.raise_for_status = Mock()

            mock_session.post.side_effect = [
                requests.exceptions.ConnectionError("Network error"),
                mock_post_response
            ]

            # Mock successful file download
            mock_get_response = Mock()
            mock_get_response.iter_content.return_value = [mock_file_content]
            mock_get_response.headers = {}
            mock_get_response.raise_for_status = Mock()
            mock_session.get.return_value = mock_get_response

            # Run scraper
            scraper = BAawardsScraper(mock_config)
            result = scraper.run()

            # Should succeed after retry
            assert result is not None
            assert result.exists()

            # Should have called POST twice (first failed, second succeeded)
            assert mock_session.post.call_count == 2

    def test_export_fails_after_max_retries(self, mock_config):
        """Test that scraper fails after max retries."""
        with patch("app.pipeline.extract.api_base_scraper.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # All calls fail
            mock_session.post.side_effect = requests.exceptions.ConnectionError("Network error")

            # Run scraper
            scraper = BAawardsScraper(mock_config)

            with pytest.raises(RuntimeError, match="All export attempts failed"):
                scraper.run()

            # Should have tried max_retries times
            assert mock_session.post.call_count == 3

    def test_export_fails_on_missing_download_url(self, mock_config):
        """Test that scraper fails when API doesn't return download URL."""
        with patch("app.pipeline.extract.api_base_scraper.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # API response without download URL
            mock_post_response = Mock()
            mock_post_response.json.return_value = {
                "status": "error",
                "message": "No data found"
            }
            mock_post_response.raise_for_status = Mock()
            mock_session.post.return_value = mock_post_response

            # Run scraper
            scraper = BAawardsScraper(mock_config)

            # Will retry and eventually fail with "All export attempts failed"
            with pytest.raises(RuntimeError, match="All export attempts failed"):
                scraper.run()

            # Should have tried max_retries times
            assert mock_session.post.call_count == 3

    def test_export_fails_on_http_error_4xx(self, mock_config):
        """Test that scraper doesn't retry on 4xx errors."""
        with patch("app.pipeline.extract.api_base_scraper.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # Mock 400 Bad Request error
            mock_response = Mock()
            mock_response.status_code = 400
            http_error = requests.exceptions.HTTPError()
            http_error.response = mock_response

            mock_session.post.side_effect = http_error

            # Run scraper
            scraper = BAawardsScraper(mock_config)

            with pytest.raises(requests.exceptions.HTTPError):
                scraper.run()

            # Should NOT retry on 4xx errors
            assert mock_session.post.call_count == 1

    def test_file_naming_format(self, mock_config, mock_api_response, mock_file_content):
        """Test that downloaded files use correct naming format."""
        with patch("app.pipeline.extract.api_base_scraper.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # Mock successful API response
            mock_post_response = Mock()
            mock_post_response.json.return_value = mock_api_response
            mock_post_response.raise_for_status = Mock()
            mock_session.post.return_value = mock_post_response

            # Mock file download with Content-Disposition header
            mock_get_response = Mock()
            mock_get_response.iter_content.return_value = [mock_file_content]
            mock_get_response.headers = {
                "Content-Disposition": 'attachment; filename="awards-export.xlsx"'
            }
            mock_get_response.raise_for_status = Mock()
            mock_session.get.return_value = mock_get_response

            # Run scraper
            scraper = BAawardsScraper(mock_config)
            result = scraper.run()

            # Filename should be in YYYY-MM-DD.xlsx format
            assert result.name.endswith(".xlsx")
            # Should match date pattern YYYY-MM-DD
            name_without_ext = result.stem
            parts = name_without_ext.split("-")
            assert len(parts) == 3
            assert len(parts[0]) == 4  # Year
            assert len(parts[1]) == 2  # Month
            assert len(parts[2]) == 2  # Day

    def test_download_directory_created_if_not_exists(self, tmp_path):
        """Test that download directory is created if it doesn't exist."""
        non_existent_dir = tmp_path / "new_directory" / "nested"

        config = {
            "download_directory": str(non_existent_dir),
            "BA_EXPORT_ENDPOINT": "https://api.test.ejn.gov.ba/Api/Awards/GetExport",
            "max_retries": 3,
            "retry_delay": 0.1,
            "request_timeout": 30,
            "from_date": "2025-12-11T23:00:00.000Z",
            "to_date": "2025-12-13T23:00:00.000Z"
        }

        # Create scraper
        scraper = BAawardsScraper(config)

        # Directory should have been created
        assert non_existent_dir.exists()
        assert non_existent_dir.is_dir()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
