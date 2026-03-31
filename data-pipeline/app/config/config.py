"""
Configuration loading and validation.
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent


class ConfigLoader:
    """Load and validate configuration from JSON config files."""

    @staticmethod
    def load(config_filename: str) -> Dict:
        config_path = CONFIG_DIR / config_filename

        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path.as_posix()}"
            )

        try:
            with config_path.open("r", encoding="utf-8") as f:
                raw = f.read()

            # Substitute ${VAR_NAME} with environment variables
            def replace_env(match):
                var_name = match.group(1)
                value = os.getenv(var_name)
                if value is None:
                    logger.warning("Environment variable %s not set", var_name)
                    return match.group(0)
                return value

            raw = re.sub(r'\$\{([^}]+)\}', replace_env, raw)
            config = json.loads(raw)

            logger.info("Configuration loaded from %s", config_path.as_posix())
            ConfigLoader._validate_config(config)
            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {config_path.as_posix()}: {e}")

    @staticmethod
    def _validate_config(config: Dict) -> None:
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