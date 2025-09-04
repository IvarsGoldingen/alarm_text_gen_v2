# --- Dataclass for settings ---
from dataclasses import dataclass

from src.config.default_settings import ALARM_EXCEL_FILE_PATH, ALARM_SCL_FILE_PATH
from src.database.sa_tables import AlarmLanguage


@dataclass
class AppSettings:
    excel_file_path: str = ALARM_EXCEL_FILE_PATH
    scl_file_path: str = ALARM_SCL_FILE_PATH
    language: AlarmLanguage = AlarmLanguage.ENGLISH
