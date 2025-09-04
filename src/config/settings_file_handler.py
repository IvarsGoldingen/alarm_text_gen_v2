import json
import logging
import os
from dataclasses import asdict

from src.config.app_settings import AppSettings
from src.config.default_settings import LOGGING_LVL_GLOBAL

logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LVL_GLOBAL)


# --- Load settings ---
def load_settings(file_path: str) -> AppSettings:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            settings = AppSettings(**data)
            logger.info("Loaded settings file")
        except (json.JSONDecodeError, TypeError):
            logger.error("Corrupted settings file")
            settings = AppSettings()
    else:
        # Settings file does not exist, use defaults
        logger.warning("Settigns file does not exist")
        settings = AppSettings()
    return settings


# --- Save settings ---
def save_settings(file_path: str, settings: AppSettings) -> None:
    with open(file_path, "w") as f:
        json.dump(asdict(settings), f, indent=4)
        logger.info("Saved settings file")
