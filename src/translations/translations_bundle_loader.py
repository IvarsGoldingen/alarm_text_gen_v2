from src.config import settings
from src.database.sa_tables import Types
from src.database.sqlite_helper import SqliteHelper
from src.translations.translation_bundle import TranslationBundle


def get_translation_bundle_from_sql() -> TranslationBundle:
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
