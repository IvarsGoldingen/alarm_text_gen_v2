from logging import DEBUG
import logging
logging.basicConfig(level=logging.INFO)
from excel_rw import ExcelRW
from tag_to_text_converter import TagConverter
from tag_to_text_dicts import AlarmLanguage


""" This script is used to generate alarm texts from tags in an Excel file.
TODO: rewrite structure of the code, so that it is more readable and easier to maintain.
TODO: Possibly move to a database instead of dictionaries for translations
TODO: Add nice GUI
TODO: Handle excel file being open
"""

def main_fc():
    main = Main()
    done = False
    task_nr = ask_for_task()
    if task_nr == 1:
        language = ask_for_language()
        main.start(language)
    elif task_nr == 2:
        main.start_create_alarm_central_file_only()
    else:
        raise Exception("Invalid task")
    main.remove_invalid_symbols_from_alarm_names()
    print("Removed invalid symbols from alarm names")

def ask_for_task() -> int:
    while True:
        result = input("Select task: 1 - update HMIalarms excel + alarm text fc, 2 alarm text fc only: ")
        if result == "1":
            return 1
        elif result == "2":
            return 2
        else:
            print("Invalid input")

def ask_for_language() -> AlarmLanguage:
    while True:
        result = input("Select language: en - English, lv - Latvian: ")
        if result == "en" or result == "EN":
            return AlarmLanguage.ENGLISH
        elif result == "lv" or result == "LV":
            return AlarmLanguage.LATVIAN
        else:
            print("Invalid input")

class Main:

    LANGUAGE = AlarmLanguage.LATVIAN
    FILE_LOC = 'C:\\py_scripts\\alarm_text_gen'
    FILE_NAME = "HMIAlarms"
    FILE_EXT = "xlsx"
    FILE_PATH = f"{FILE_LOC}\\{FILE_NAME}.{FILE_EXT}"
    FILE_NAME_ALARM_CENTRAL = "email_fc"
    FILE_EXT_ALARM_CENTRAL = ".txt"
    FILE_PATH_ALARM_CENTRAL = f"{FILE_LOC}\\{FILE_NAME_ALARM_CENTRAL}.{FILE_EXT_ALARM_CENTRAL}"

    def __int__(self):
        pass

    def start(self, language: AlarmLanguage):
        alarm_tag_list = ExcelRW.get_alarm_tags_as_list(self.FILE_PATH)
        alarm_text_list = TagConverter.convert_tags_to_alarm_text(alarm_tag_list, language)
        ExcelRW.write_alarm_texts_to_excel_file(self.FILE_PATH, alarm_text_list)
        ExcelRW.create_email_alarm_text_file(self.FILE_PATH, self.FILE_PATH_ALARM_CENTRAL)

    def start_create_alarm_central_file_only(self):
        ExcelRW.create_email_alarm_text_file(self.FILE_PATH, self.FILE_PATH_ALARM_CENTRAL)
    
    def remove_invalid_symbols_from_alarm_names(self):
        ExcelRW.remove_invalid_symbols_from_alarm_names(self.FILE_PATH)

if __name__ == '__main__':
    main_fc()