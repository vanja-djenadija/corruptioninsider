"""
Live integration test for BAawardsScraper.
This test makes actual API calls - use sparingly!

Run with: pytest tests/test_awards_scraper_live.py -v --live
"""

import sys
from pathlib import Path
import pytest

# Add data-pipeline to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "data-pipeline"))

from app.pipeline.extract.ba.awards_scraper import BAawardsScraper
from app.config.config import ConfigLoader


@pytest.mark.live
class TestBAawardsScraperLive:
    """Live tests that make actual API calls."""

    @pytest.fixture
    def scraper(self, tmp_path):
        """Fixture for scraper with real config and temp download directory."""
        config = ConfigLoader.load()
        # Override download directory to use temp path
        config["download_directory"] = str(tmp_path)
        return BAawardsScraper(config)

    def test_live_export(self, scraper):
        """Test actual export from BA awards API."""
        # This makes a real API call
        result = scraper.run()

        # Verify result
        assert result is not None
        assert isinstance(result, Path)
        assert result.exists()
        assert result.suffix == ".xlsx"

        # Verify file is not empty
        file_size = result.stat().st_size
        assert file_size > 0, "Downloaded file is empty"
        print(f"\n✓ Downloaded file: {result.name} ({file_size:,} bytes)")

        # Verify file is valid XLSX (starts with PK ZIP header)
        with open(result, "rb") as f:
            header = f.read(4)
            assert header[:2] == b"PK", "File is not a valid ZIP/XLSX file"

    def test_live_export_with_custom_dates(self, tmp_path):
        """Test export with custom date range."""
        from datetime import datetime, timedelta

        # Get dates from last month
        today = datetime.now()
        from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d") + "T23:00:00.000Z"
        to_date = (today - timedelta(days=28)).strftime("%Y-%m-%d") + "T23:00:00.000Z"

        config = ConfigLoader.load()
        config["download_directory"] = str(tmp_path)
        config["from_date"] = from_date
        config["to_date"] = to_date

        scraper = BAawardsScraper(config)
        result = scraper.run()

        assert result is not None
        assert result.exists()
        print(f"\n✓ Downloaded awards from {from_date} to {to_date}")
        print(f"  File: {result.name} ({result.stat().st_size:,} bytes)")


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "live: marks tests as live tests that make actual API calls"
    )


if __name__ == "__main__":
    # Run with --live flag to execute live tests
    pytest.main([__file__, "-v", "--live", "-s"])
