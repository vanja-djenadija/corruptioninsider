"""
Selenium-based scraper class for award portal scrapers.
"""

import logging
from abc import abstractmethod
from pathlib import Path
from typing import Dict

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from ._base_scraper import BaseScraper
from ...util.paths import resolve_path

logger = logging.getLogger(__name__)


class SeleniumScraper(BaseScraper):
    """
    Abstract base class for Selenium-based award portal scrapers.
    """

    def __init__(self, config: Dict) -> None:
        # Initialize Selenium-specific attributes before calling super().__init__
        self.headless = config.get("headless_mode", False)
        self.wait_timeout = config.get("wait_timeout", 15)
        self.download_dir = resolve_path(config.get("raw_directory", "data/raw"))
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.driver = None
        self.wait = None

        # Validate Selenium-specific config
        self._validate_selenium_config(config)

        # Call parent __init__ which handles common config
        super().__init__(config)

    def _validate_selenium_config(self, config: Dict) -> None:
        """Validate Selenium-specific configuration parameters."""
        wait_timeout = config.get("wait_timeout", 15)
        if not isinstance(wait_timeout, (int, float)) or wait_timeout <= 0:
            raise ValueError(f"wait_timeout must be a positive number, got: {wait_timeout}")

    def _log_configuration(self) -> None:
        logger.info(
            f"""
{'=' * 60}
Scraper configuration:
  Download dir: {self.download_dir}
  Headless: {self.headless}
  Wait timeout: {self.wait_timeout}s
  Date range: {self.from_date} → {self.to_date}
{'=' * 60}
"""
        )

    # ---------- Lifecycle ----------

    def _before_run(self) -> None:
        """Initialize WebDriver before retry loop."""
        self.open()

    def _cleanup(self) -> None:
        """Close WebDriver after retry loop."""
        self.close()

    def open(self) -> None:
        """Initialize WebDriver."""
        self._initialize_driver()

    def close(self) -> None:
        """Close WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("[SUCCESS] Browser closed")
            finally:
                self.driver = None
                self.wait = None

    # ---------- Internals ----------

    def _initialize_driver(self) -> None:
        try:
            options = webdriver.ChromeOptions()

            if self.headless:
                options.add_argument("--headless=new")

            prefs = {
                "download.default_directory": str(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
            }
            options.add_experimental_option("prefs", prefs)

            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-gpu")

            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, self.wait_timeout)

            logger.info("WebDriver initialized")

        except WebDriverException as e:
            logger.error("Failed to initialize WebDriver", exc_info=True)
            raise

    # ---------- Abstract API ----------

    @abstractmethod
    def _build_url(self) -> str:
        """
        Builds the URL for the export page.
        Must be implemented by subclasses.
        """
        pass
