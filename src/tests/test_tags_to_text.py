import logging

from src.config.logging_config import setup_logging
from src.database.sa_tables import AlarmLanguage
from src.translations.tags_to_text import (
    convert_tags_to_alarm_text,
    is_str_place_holder,
)
from src.translations.translations_bundle_loader import get_translation_bundle_from_sql

setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.info("Starting tests")
test_alarm_list = ["softener_lla_salt_tank_16CP116"]


def main():
    # Get all alarm tags
    # Get all tag to text translations
    bundle = get_translation_bundle_from_sql()
    logger.info(bundle)
    print(is_str_place_holder(test_alarm_list[0], bundle))
    translated_tags = convert_tags_to_alarm_text(
        test_alarm_list, AlarmLanguage.LATVIAN, bundle
    )
    for tag in translated_tags:
        print(tag)


if __name__ == "__main__":
    main()
