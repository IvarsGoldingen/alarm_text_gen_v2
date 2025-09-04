import logging
import os

from src.config import default_settings
from src.config.default_settings import DB_PATH
from src.config.logging_config import setup_logging
from src.database import sa_tables
from src.database.sqlite_helper import SqliteHelper
from src.table_creation_and_updates import table_update
from src.table_creation_and_updates.old_dics import phrases, words

setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(default_settings.LOGGING_LVL_GLOBAL)


def main_fc():
    create_all_from_zero()


def create_all_from_zero():
    # create folder for script files
    check_if_folder_exists_or_create(default_settings.FILE_LOC)
    db = SqliteHelper()
    db.init_db(url=DB_PATH)
    create_types(db)
    convert_old_dicts_to_db(db)
    table_update.insert_no_translation_tags(db)
    table_update.insert_placeholder_tags(db)
    table_update.insert_placeholder_translation(db)


def create_types(db: SqliteHelper):
    for type in sa_tables.Types:
        db.create_type(type.value)


def get_all_types_and_print(db: SqliteHelper):
    types = db.get_all_types()
    for type in types:
        print(type)


def convert_old_dicts_to_db(db: SqliteHelper):
    for word_tag, translations in words.items():
        db.insert_tag(
            tag=word_tag,
            type=sa_tables.Types.WORD.value,
            lv=translations[1],
            en=translations[0],
        )
    for phrase_tag, translations in phrases.items():
        db.insert_tag(
            tag=phrase_tag,
            type=sa_tables.Types.PHRASE.value,
            lv=translations[1],
            en=translations[0],
        )


def check_if_folder_exists_or_create(folder_path: str) -> None:
    """
    Checks if the folder exists, and creates it if it does not.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.info(f"Folder {folder_path} created")


if __name__ == "__main__":
    main_fc()
