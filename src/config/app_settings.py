# --- Dataclass for settings ---
from dataclasses import dataclass

from src.config.default_settings import ALARM_EXCEL_FILE_PATH, ALARM_SCL_FILE_PATH
from src.database.sa_tables import AlarmLanguage


@dataclass
class AppSettings:
    excel_file_path: str = ALARM_EXCEL_FILE_PATH
    scl_file_folder: str = ALARM_SCL_FILE_PATH
    language: AlarmLanguage = AlarmLanguage.ENGLISH

    # Needed to store as JSON
    def to_dict(self):
        return {
            "excel_file_path": self.excel_file_path,
            "scl_file_path": self.scl_file_folder,
            "language": self.language.value,  # store enum as value
        }

    # Needed to load as JSON
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            excel_file_path=data["excel_file_path"],
            scl_file_folder=data["scl_file_path"],
            language=AlarmLanguage(data["language"]),
        )
