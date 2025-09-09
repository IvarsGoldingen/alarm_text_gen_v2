import logging
from tkinter import Tk, filedialog

from nicegui import app, ui

from src.config import default_settings
from src.config.logging_config import setup_logging
from src.config.settings_file_handler import load_settings, save_settings
from src.database.sa_tables import AlarmLanguage
from src.database.sqlite_helper import SqliteHelper
from src.translations.alarm_excel_handler import (
    create_email_alarm_text_file,
    get_alarms_from_excel,
    remove_invalid_symbols_from_alarm_names,
    write_alarm_texts_to_excel_file,
)
from src.translations.tags_to_text import (
    convert_tags_to_alarm_text,
)
from src.translations.translations_bundle_loader import get_translation_bundle_from_sql

"""
TODO: Process progress
TODO: Work freely on DB from UI 
"""

setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(default_settings.LOGGING_LVL_GLOBAL)
logger.info("Starting main")

app_settings = load_settings(default_settings.SETTINGS_FILE_PATH)

STYLE_BTN = "width: 200px; height: 50px;"
STYLE_SETTING_NAME = (
    "text-lg font-medium text-gray-700 dark:text-gray-300 min-w-[250px]"
)
STYLE_UNEDITTABLE_SETTING = (
    "text-sm font-mono px-3 py-1 rounded "
    "bg-gray-200 text-gray-800 "
    "dark:bg-gray-800 dark:text-gray-100"
)
STYLE_TITLE = "text-3xl font-bold mt-4"

OPEN_FILE_DIALOG_FOR_EXCEL = 1
OPEN_FILE_DIALOG_FOR_SCL = 2

excel_file_path_label: ui.label
scl_file_path_label: ui.label
language_btn: ui.button


def main():
    # Start application
    try:
        app.on_shutdown(stop_app)
        ui.run(host="0.0.0.0", dark=True, reload=False, port=5001, native=True)
    except KeyboardInterrupt:
        logging.info("Application stopped by keyboard interrupt")
        stop_app()


@ui.page("/")
def main_page():
    global excel_file_path_label, scl_file_path_label, language_btn, app_settings
    ui.label("Alarm text generator").classes(STYLE_TITLE)
    ui.button(
        "DB EDITOR PAGE", on_click=lambda: ui.navigate.to("/db_editor_page")
    ).style(STYLE_BTN)
    with ui.row().classes("items-center"):
        ui.label("Alarm excel file location").classes(STYLE_SETTING_NAME)
        excel_file_path_label = ui.label(app_settings.excel_file_path).classes(
            STYLE_UNEDITTABLE_SETTING
        )
        ui.button(
            "Select File", on_click=lambda: open_file_dialog(OPEN_FILE_DIALOG_FOR_EXCEL)
        ).style(STYLE_BTN)
    with ui.row().classes("items-center"):
        ui.label("Scl fucntions file location").classes(STYLE_SETTING_NAME)
        scl_file_path_label = ui.label(app_settings.scl_file_folder).classes(
            STYLE_UNEDITTABLE_SETTING
        )
        ui.button(
            "Select File", on_click=lambda: open_file_dialog(OPEN_FILE_DIALOG_FOR_SCL)
        ).style(STYLE_BTN)
    ui.button(
        "REMOVE INVALID SYMBOLS IN EXCEL", on_click=remove_invalid_symbols_in_excel
    ).style(STYLE_BTN)
    with ui.row():
        ui.button(
            "DO TRANSLATIONS IN EXCEL FILE", on_click=do_translations_on_excel_file
        ).style(STYLE_BTN)
        language_btn = ui.button(
            app_settings.language.value, on_click=change_language
        ).style(STYLE_BTN)
    ui.button(
        "CREATE SCL FUNCTION", on_click=create_scl_function_from_excel_file
    ).style(STYLE_BTN)
    ui.button("DO ALL", on_click=do_all).style(STYLE_BTN)
    with ui.row():
        ui.button("STOP APP", on_click=stop_app).style(STYLE_BTN)


# Page 1
@ui.page("/db_editor_page")
def db_editor_page():
    ui.label("DATABASE EDITOR").classes(STYLE_TITLE)
    ui.button("HOME", on_click=lambda: ui.navigate.to("/")).style(STYLE_BTN)
    table = ui.table(
        columns=[
            {"name": "id", "label": "ID", "field": "id"},
            {"name": "tag", "label": "Tag", "field": "tag"},
            {"name": "type", "label": "Type", "field": "type"},
            {"name": "lv", "label": "Latvian", "field": "lv"},
            {"name": "en", "label": "English", "field": "en"},
        ],
        rows=get_dict_for_db_editor(),
        row_key="id",
    ).classes("w-full")


def get_dict_for_db_editor() -> list[dict]:
    db = SqliteHelper()
    db.init_db(url=default_settings.DB_PATH)
    return db.get_all_tags_as_dict()


def change_language():
    global app_settings, language_btn
    all_languages = list(AlarmLanguage)
    idx = all_languages.index(app_settings.language)
    # Move to next language
    app_settings.language = all_languages[(idx + 1) % len(all_languages)]
    ui.notify(f"Changed clanguage to {app_settings.language.value}")
    language_btn.set_text(app_settings.language.value)


def open_file_dialog(file_type: int) -> None:
    global excel_file_path_label, scl_file_path_label
    # Create a hidden Tkinter root window
    root = Tk()
    root.withdraw()
    # Force the file dialog to stay on top
    root.attributes("-topmost", True)
    # Open native file picker
    if file_type == OPEN_FILE_DIALOG_FOR_EXCEL:
        path_to_use = filedialog.askopenfilename(
            initialdir=app_settings.excel_file_path
        )
    else:
        path_to_use = filedialog.askdirectory(initialdir=app_settings.scl_file_folder)

    if path_to_use:
        ui.notify(f"Selected: {path_to_use}")
        if file_type == OPEN_FILE_DIALOG_FOR_EXCEL:
            app_settings.excel_file_path = path_to_use
            excel_file_path_label.set_text(path_to_use)
        elif file_type == OPEN_FILE_DIALOG_FOR_SCL:
            app_settings.scl_file_folder = (
                path_to_use + "\\" + default_settings.ALARM_SCL_FILE_NAME
            )
            scl_file_path_label.set_text(path_to_use)
        else:
            logging.error("Unknown file type")
    root.destroy()  # Clean up Tkinter window


def new_file_location(new_value):
    logging.info(f"New location {new_value}")


def stop_app():
    logging.info("Stop app button pressed")
    save_settings(default_settings.SETTINGS_FILE_PATH, app_settings)
    app.shutdown()


def create_scl_function_from_excel_file():
    logging.info("Creating SCL function from excel file")
    create_email_alarm_text_file(
        app_settings.excel_file_path, app_settings.scl_file_folder
    )


def remove_invalid_symbols_in_excel():
    logging.info("Removing invalid symbols from excel")
    remove_invalid_symbols_from_alarm_names(app_settings.excel_file_path)


def do_translations_on_excel_file():
    logging.info("Doing translations in excel file")
    alarm_tag_list = get_alarms_from_excel(app_settings.excel_file_path)
    # Get all tag to text translations
    translation_bundle = get_translation_bundle_from_sql()
    logger.info(translation_bundle)
    translated_tags = convert_tags_to_alarm_text(
        alarm_tag_list, app_settings.language, translation_bundle
    )
    write_alarm_texts_to_excel_file(app_settings.excel_file_path, translated_tags)


def do_all():
    logging.info("Doing all")
    # Get all alarm tags
    remove_invalid_symbols_from_alarm_names(app_settings.excel_file_path)
    alarm_tag_list = get_alarms_from_excel(app_settings.excel_file_path)
    # Get all tag to text translations
    translation_bundle = get_translation_bundle_from_sql()
    logger.info(translation_bundle)
    translated_tags = convert_tags_to_alarm_text(
        alarm_tag_list, app_settings.language, translation_bundle
    )
    write_alarm_texts_to_excel_file(app_settings.excel_file_path, translated_tags)
    create_email_alarm_text_file(
        app_settings.excel_file_path, app_settings.scl_file_folder
    )


if __name__ == "__main__":
    main()
