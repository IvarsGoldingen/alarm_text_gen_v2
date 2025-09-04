import logging

FILE_LOC = "C:/py_scripts/alarm_text_gen_v2"
DB_NAME = "tags_to_alarms_v4.db"
DB_PATH = FILE_LOC + "/" + DB_NAME
ALARM_EXCEL_FILE_NAME = "HMIAlarms.xlsx"
ALARM_EXCEL_FILE_PATH = FILE_LOC + "/" + ALARM_EXCEL_FILE_NAME
ALARM_SCL_FILE_NAME = "scl_alarm_fc.txt"
ALARM_SCL_FILE_PATH = FILE_LOC + "/" + ALARM_SCL_FILE_NAME
LOGGING_LVL_GLOBAL = logging.INFO
SETTINGS_FILE_NAME = "settings_al_gen.json"
SETTINGS_FILE_PATH = FILE_LOC + "/" + SETTINGS_FILE_NAME
