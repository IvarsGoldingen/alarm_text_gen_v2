import logging

from nicegui import app, ui

from src.config import settings
from src.config.logging_config import setup_logging
from src.database.sa_tables import AlarmLanguage
from src.translations.alarm_excel_handler import (
    get_alarms_from_excel,
    remove_invalid_symbols_from_alarm_names,
    write_alarm_texts_to_excel_file,
)
from src.translations.tags_to_text import (
    convert_tags_to_alarm_text,
)
from src.translations.translations_bundle_loader import get_translation_bundle_from_sql

"""
TODO: Create UI
TODO: FIle selection
TODO: Process progress
TODO: Work freely on DB from UI 
"""

setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LVL_GLOBAL)

logger.info("Starting main")


def main():
    with ui.column():
        ui.label("Alarm text generator").classes("text-3xl font-bold mt-4")
    # Start application
    try:
        ui.run(host="0.0.0.0", dark=True, reload=False, port=5001)
    except KeyboardInterrupt:
        logging.info("Application stopped by keyboard interrupt")
        stop_app()


def stop_app():
    logging.info("Stop app button pressed")
    app.shutdown()


def do_all():
    # Get all alarm tags
    remove_invalid_symbols_from_alarm_names(settings.ALARM_EXCEL_FILE_PATH)
    alarm_tag_list = get_alarms_from_excel(settings.ALARM_EXCEL_FILE_PATH)
    # Get all tag to text translations
    translation_bundle = get_translation_bundle_from_sql()
    logger.info(translation_bundle)
    translated_tags = convert_tags_to_alarm_text(
        alarm_tag_list, AlarmLanguage.ENGLISH, translation_bundle
    )
    write_alarm_texts_to_excel_file(settings.ALARM_EXCEL_FILE_PATH, translated_tags)


if __name__ == "__main__":
    main()
