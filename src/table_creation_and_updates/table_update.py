import logging

from src.config import settings
from src.config.logging_config import setup_logging
from src.config.settings import DB_PATH
from src.database import sa_tables
from src.database.sa_tables import Types
from src.database.sqlite_helper import SqliteHelper
from src.translations.translation_bundle import TranslationBundle

setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LVL_GLOBAL)

logger.info("Starting table update")

no_translation_tags_to_insert = [
    "MB_DRIVER_MB_com_load_error",
    "safety_to_main",
    "safety_gd",
    "dly",
    "hmi",
    "logic_gd",
]
# Texts that indicate that there is no alarm - empty placeholder
placeholder_tags_to_insert = ["empty", "false", "alwaysfalse", "a", "Discretealarm"]
# placeholder translations
placeholder_translations = ["Alarm", "Trauksme"]  # EN, LV

words_to_insert = {
    "relay": ("relejs", "relay"),
    "safety": ("drošības", "safety"),
}
phrases_to_insert = {
    "safety_reset_ack_needed": (
        "nepieciešams drošības ķēdes reset",
        "safety chain reset needed",
    ),
    "boiler_filling_from_electrodes_enabled": (
        "katla pildīšana no elektrodiem aktīva",
        "boiler filling from electrodes enabled",
    ),
    "safety_chain_test_recommended": (
        "vēlam veikt drošības ķēdes testu",
        "safety chain test recommended",
    ),
}


def main():
    db = SqliteHelper()
    db.init_db(url=DB_PATH)
    bundle = get_translation_bundle()
    print(bundle)
    insert_no_translation_tags(db)
    insert_words(db)
    insert_phrases(db)
    insert_placeholder_tags(db)
    # insert_placeholder_translation(db)
    # get_all_of_type_and_print(db, sa_tables.Types.NO_TRANSLATION.value)
    # get_all_of_type_and_print(db, sa_tables.Types.PLACEHOLDER.value)
    # get_all_of_type_and_print(db, sa_tables.Types.PLACEHOLDER_TRANSLATION.value)
    bundle = get_translation_bundle()
    print(bundle)


def insert_words(db: SqliteHelper):
    for word_tag, translations in words_to_insert.items():
        db.insert_tag(
            tag=word_tag,
            type=sa_tables.Types.WORD.value,
            lv=translations[0],
            en=translations[1],
        )


def insert_phrases(db: SqliteHelper):
    for phrase_tag, translations in phrases_to_insert.items():
        db.insert_tag(
            tag=phrase_tag,
            type=sa_tables.Types.PHRASE.value,
            lv=translations[0],
            en=translations[1],
        )


def insert_no_translation_tags(db: SqliteHelper):
    for tag in no_translation_tags_to_insert:
        db.insert_tag(tag=tag, type=sa_tables.Types.NO_TRANSLATION.value, lv="", en="")


def insert_placeholder_tags(db: SqliteHelper):
    for tag in placeholder_tags_to_insert:
        db.insert_tag(
            tag=tag,
            type=sa_tables.Types.PLACEHOLDER.value,
            lv=placeholder_translations[0],
            en=placeholder_translations[1],
        )


def insert_placeholder_translation(db: SqliteHelper):
    db.insert_tag(
        tag=sa_tables.Types.PLACEHOLDER_TRANSLATION.value,
        type=sa_tables.Types.PLACEHOLDER_TRANSLATION.value,
        lv=placeholder_translations[0],
        en=placeholder_translations[1],
    )


def get_all_types_and_print(db: SqliteHelper):
    types = db.get_all_types()
    for type in types:
        print(type)


def get_all_of_type_and_print(db: SqliteHelper, type: str):
    print(f"Getting all tags of type {type}")
    tags = db.get_all_tags_of_type(type_name=type)
    for tag in tags:
        print(tag)


def get_translation_bundle() -> TranslationBundle:
    db = SqliteHelper()
    db.init_db(url=settings.DB_PATH)
    words = db.get_all_tags_of_type(type_name=Types.WORD.value)
    phrases = db.get_all_tags_of_type(type_name=Types.PHRASE.value)
    no_translations = db.get_all_tags_of_type(type_name=Types.NO_TRANSLATION.value)
    placeholders = db.get_all_tags_of_type(type_name=Types.PLACEHOLDER.value)
    placeholder_translation = db.get_all_tags_of_type(
        type_name=Types.PLACEHOLDER_TRANSLATION.value
    )[0]
    bundle = TranslationBundle(
        phrases=phrases,
        words=words,
        no_translation=no_translations,
        placeholders=placeholders,
        placeholder_translation=placeholder_translation,
    )
    return bundle


if __name__ == "__main__":
    main()
