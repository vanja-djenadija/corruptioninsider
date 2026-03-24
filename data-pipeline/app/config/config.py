"""
Configuration loading and validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# Config directory path
CONFIG_DIR = Path(__file__).resolve().parent


class ConfigLoader:
    """Load and validate configuration from JSON config files."""

    @staticmethod
    def load(config_filename: str) -> Dict:
        """
        Load configuration from specified config file in the config directory.

        Args:
            config_filename: Name of the config file (e.g., 'ba_awards_config.json')

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file contains invalid JSON or fails validation
        """
        config_path = CONFIG_DIR / config_filename

        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path.as_posix()}"
            )

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)

            logger.info(
                "Configuration loaded from %s",
                config_path.as_posix(),
            )

            ConfigLoader._validate_config(config)
            return config

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in {config_path.as_posix()}: {e}"
            )

    @staticmethod
    def _validate_config(config: Dict) -> None:
        """
        Validate configuration values.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        if "headless_mode" in config and not isinstance(config.get("headless_mode"), bool):
            raise ValueError("headless_mode must be a boolean")

        if "wait_timeout" in config:
            if not isinstance(config.get("wait_timeout"), int) or config.get("wait_timeout") <= 0:
                raise ValueError("wait_timeout must be a positive integer")

        if "raw_directory" in config and not isinstance(config.get("raw_directory"), str):
            raise ValueError("raw_directory must be a string")

        if "max_retries" in config:
            if not isinstance(config.get("max_retries"), int) or config.get("max_retries") < 0:
                raise ValueError("max_retries must be a non-negative integer")
