from typing import Tuple
import logging
from tag_to_text_dicts import (
    AlarmLanguage,
    AlarmType,
    ALARM_TAG_TO_TYPE_DICT,
    sensor_alarms,
    device_alarms,
    power_alarms,
    digital_sensor_alarms,
    sensor_types,
    generic_phrases,
    generic_words,
    empty_alarm_text,
    place_holder_text
)
import re

"""
TODO:
in get_generic_text_from_tag understand when unhandled text is left over
handle unknown alarms
"""


logging.basicConfig(level=logging.DEBUG)


def test():
    logging.info("TEST START")
    test_list = ["\"lvl_sw_fault_boiler_circuit_feed_tank\""]
    for al in test_list:
        logging.info(al)
    # tag = test_list[0]
    # print(f"Tag is {tag}")
    # tag = tag.strip("\"")
    # print(f"Tag is {tag}")
    # print(tag.startswith("volt_"))
    TagConverter.convert_tags_to_alarm_text(test_list, language=AlarmLanguage.LATVIAN)


class TagConverter:
    GENERIC_PHRASE_SEARCH_LOOPS = 8
    # USED TO INDICATE THAT ALARM is empty and should have generic text and number
    ALARM_TEXT_PLACEHOLDER = "*"

    @staticmethod
    def convert_tags_to_alarm_text(alarm_tags: list, language: AlarmLanguage) -> list:
        alarm_texts = []
        for i, alarm_tag in enumerate(alarm_tags):
            logging.debug(f"Handling alarm number {i+1}, {alarm_tag}")
            alarm_tag = alarm_tag.strip('"')
            logging.debug(f"After stripping |{alarm_tag}|")
            alarm_type = TagConverter.detect_alarm_type(alarm_tag)
            alarm_type_method = METHOD_MAP.get(alarm_type)
            logging.debug(f"Alarm type is {alarm_type}")
            # Call text generation method depending on alarm type
            full_success, alarm_text = alarm_type_method(alarm_tag, language)
            if not full_success:
                logging.error(f"Failed to fully convert alarm nr {i+1}, {alarm_tag}")
            else:
                logging.debug(f"Full success with alarm nr {i+1}, {alarm_tag}")
            if alarm_text is None:
                alarm_text = f"{i} {alarm_tag}"
                logging.error(f"Could not get text for tag {alarm_text}")
            elif alarm_text == TagConverter.ALARM_TEXT_PLACEHOLDER:
                alarm_text = f"{empty_alarm_text[language.value]} {i + 1}"
            else:
                # Strip spaces
                alarm_text = alarm_text.strip(" ")
                # capitalie the first letter
                alarm_text = alarm_text[0].upper() + alarm_text[1:]
            # if alarm_type == alarm_type.UNKNOWN:
            #     print(f"{alarm_tag}\t {alarm_text}")
            logging.debug(f"Final result {alarm_tag}\t {alarm_text}")
            alarm_texts.append(alarm_text)
        return alarm_texts



    @staticmethod
    def handle_sensor_alarm_tag(alarm_tag: str, language: AlarmLanguage) -> Tuple[bool,str]:
        """
        Alarms that look like this:
        press_b_circuit_return_10NDA90CP001_DB".PV_HLA_E
        :param alarm_tag:
        :return:
        """
        full_success = False
        logging.debug("handle_sensor_alarm_tag")
        alarm_tag = alarm_tag.strip(" ")
        # press_b_circuit_return_10NDA90CP001_DB" PV_HLA_E
        try:
            alarm_tag_start, alarm_type = alarm_tag.split('.')
        except ValueError as e:
            # When there is no . in the middle
            alarm_tag_start, alarm_type = TagConverter.split_sensor_al_text(alarm_tag)
            if alarm_type is None:
                logging.error(f"Failed split tag {alarm_tag}")
                return full_success, alarm_tag
        logging.debug(f"alarm_tag_start {alarm_tag_start} alarm_type {alarm_type}")
        alarm_tag_start = alarm_tag_start.replace("_DB\"", "")
        alarm_tag_start = alarm_tag_start.replace("\"", "")
        expected_kks = alarm_tag_start.split("_")[-1]
        kks_str = ""
        if TagConverter.is_str_kks_code(expected_kks):
            kks_str = expected_kks
            alarm_tag_start = alarm_tag_start.replace(kks_str, "")
            alarm_tag_start = alarm_tag_start.strip("_")
        # Pressure b_circuit_return_10NDA90CP001_DB"
        alarm_text_start, rest_of_tag = TagConverter.get_sensor_type_text(alarm_tag_start, language)
        # Get "low level alarm" etc.
        sensor_alarm_type = sensor_alarms.get(alarm_type)[language.value]
        # Get middle text from generic phrases and words
        sensor_generic_text, rest_of_tag = TagConverter.get_generic_text_from_tag(rest_of_tag, language)
        if rest_of_tag == "":
            full_success = True
        if kks_str != "" and kks_str is not None:
            return full_success, f"{alarm_text_start}{sensor_generic_text} {sensor_alarm_type} {kks_str}!"
        else:
            return full_success, f"{alarm_text_start}{sensor_generic_text} {sensor_alarm_type}!"



    @staticmethod
    def handle_device_alarms_from_fb_blocks(alarm_tag: str, language: AlarmLanguage) -> Tuple[bool,str]:
        """
        vlv_glycol_heating_10NDA70AA151".fb_error
        pump_b2_1_10NDA50AP001".warning_fault
        pump_b2_1_10NDA50AP001".local_remote
        vlv_glycol_heating_10NDA70AA151_not_at_sp".fault
        :param alarm_tag:
        :param language:
        :return:
        """
        full_success = False
        logging.debug("handle_device_alarms_from_fb_blocks")
        alarm_tag_start, alarm_tag_type = alarm_tag.split('.')
        logging.debug(f"alarm_tag_start: {alarm_tag_start}, alarm_tag_type: {alarm_tag_type}")
        # specific block have double ending before and after dot
        alarm_tag_start = alarm_tag_start.replace("_not_at_sp", "")
        alarm_tag_start = alarm_tag_start.replace("_move_fault", "")
        alarm_tag_start = alarm_tag_start.replace("_DB", "")
        alarm_tag_start = alarm_tag_start.strip(" ").strip("\"")
        logging.debug(f"alarm_tag_start after cleanup: {alarm_tag_start}")
        expected_kks = alarm_tag_start.split("_")[-1]
        kks_str = ""
        if TagConverter.is_str_kks_code(expected_kks):
            kks_str = expected_kks
            alarm_tag_start = alarm_tag_start.replace(kks_str, "")
            alarm_tag_start = alarm_tag_start.strip("_")
        # Get "fault" etc.
        device_alarm_type = ""
        try:
            device_alarm_type = device_alarms.get(alarm_tag_type)[language.value]
        except TypeError:
            logging.error(f"Did not find alarm in device_alarms fo text {alarm_tag_type}")
        # Get middle text from generic phrases and words
        device_generic_text, rest_of_tag = TagConverter.get_generic_text_from_tag(alarm_tag_start, language)
        if rest_of_tag == "":
            full_success = True
        else:
            logging.debug(f"Rest of alarms_from_fb is {rest_of_tag}, not full success")
        device_generic_text = device_generic_text.strip(" ")
        device_alarm_type = device_alarm_type.strip(" ")
        kks_str = kks_str.strip(" ")

        if device_alarm_type != "":
            return full_success, f"{device_generic_text} {device_alarm_type} {kks_str}!"
        else:
            return full_success, f"{device_generic_text} {kks_str}!"

    @staticmethod
    def get_sensor_type_text(alarm_tag_start: str, language: AlarmLanguage) -> Tuple[str, str]:
        for key, value in sensor_types.items():
            if alarm_tag_start.startswith(key):
                rest_of_str = alarm_tag_start.replace(key, "", 1)
                return sensor_types.get(key)[language.value], rest_of_str
        # if not in dicts just return start of same string
        logging.error(f"Could not find sensor type for {alarm_tag_start}")
        tag_start = alarm_tag_start.split("_")[0]
        return tag_start, alarm_tag_start.replace(tag_start, "")

    @staticmethod
    def get_generic_text_from_tag(alarm_tag_middle: str, language: AlarmLanguage) -> Tuple[str, str]:
        """
        From sensor input string would look like this
        b_circuit_return_10NDA90CP001_DB"
        :param alarm_tag_middle:
        :param language:
        :return:
        """
        logging.debug(f"get_generic_text_from_tag {alarm_tag_middle}")
        tag_str_to_use = alarm_tag_middle.replace("_DB", "")
        tag_str_to_use = tag_str_to_use.strip("\"")
        alarm_text_to_return = ""
        rest_of_tag = tag_str_to_use
        logging.debug(f"After clean up {tag_str_to_use}")
        for _ in range(TagConverter.GENERIC_PHRASE_SEARCH_LOOPS):
            logging.debug(f"Loop nr: {_+1} {tag_str_to_use}")
            tag_str_to_use = tag_str_to_use.strip("_")
            logging.debug(f"After stripping |{tag_str_to_use}|")
            if tag_str_to_use == "":
                return alarm_text_to_return, tag_str_to_use
            while TagConverter.does_str_start_with_supplementary_number(tag_str_to_use):
                # string something like this: 1_winter_alarm. Add the number to the string
                number_str = tag_str_to_use.split("_")[0]
                logging.debug(f"String starts with supplementary number {number_str}")
                alarm_text_to_return = alarm_text_to_return + " " + number_str
                # Remove the number from the string to use
                tag_str_to_use = tag_str_to_use.replace(f"{number_str}", "", 1)
                tag_str_to_use = tag_str_to_use.strip("_").strip(" ")
                logging.debug(f"After removing number alarm_text_to_return{alarm_text_to_return} tag_str_to_use {tag_str_to_use}")
            if TagConverter.is_str_kks_code(tag_str_to_use):
                logging.debug(f"String is KKS code {tag_str_to_use}")
                # Add KKS to alarm text
                alarm_text_to_return = alarm_text_to_return + " " + tag_str_to_use
                return alarm_text_to_return, ""
            if tag_str_to_use == "":
                rest_of_tag = tag_str_to_use
                break
            # first search for phrase then induvidual words
            alarm_text, rest_of_tag = TagConverter.find_text_in_tag_from_dict(generic_phrases, tag_str_to_use, language)
            if alarm_text is None and rest_of_tag is None:
                logging.debug("Did not find phrases for tag")
                # did not find phrase in tag, search for word
                alarm_text, rest_of_tag = TagConverter.find_text_in_tag_from_dict(generic_words, tag_str_to_use,
                                                                                  language)
                if alarm_text is None and rest_of_tag is None:
                    # Did not find word in tag, check if it is a KKS code
                    # check if it is not KKS
                    logging.debug("Did not find generic text for tag")
                    expected_kks = tag_str_to_use.split("_")[0]
                    logging.debug(f"expected_kks {expected_kks}")
                    if TagConverter.is_str_kks_code(expected_kks):
                        # Add the KKS to the alarm text to return
                        alarm_text_to_return = alarm_text_to_return + " " + expected_kks
                        # Remove the KKS from rest of the string
                        tag_str_to_use = tag_str_to_use.replace(expected_kks, "")
                        tag_str_to_use = tag_str_to_use.strip("_")
                    else:
                        logging.debug("Start is not KKS")
                        # did not find KKS code either
                        unrecognised_part = tag_str_to_use.split("_")[0]
                        alarm_text_to_return = alarm_text_to_return + " " + unrecognised_part
                        tag_str_to_use = tag_str_to_use.replace(unrecognised_part, "")
                        tag_str_to_use = tag_str_to_use.strip("_")
                        logging.warning(f"Could not get predefined info from tag. Tag text {alarm_tag_middle}, Unrecognised part: {unrecognised_part}, condtinuing with  {tag_str_to_use}")
                else:
                    logging.debug("Did not find phrases for tag")
                    alarm_text_to_return = alarm_text_to_return + " " + alarm_text
                    tag_str_to_use = rest_of_tag
            else:
                # found generic phrase in alarm tag
                alarm_text_to_return = alarm_text_to_return + " " + alarm_text
                tag_str_to_use = rest_of_tag
        return alarm_text_to_return, rest_of_tag

    @staticmethod
    def does_str_start_with_supplementary_number(string: str) -> bool:
        nuber_str = string.split("_")[0]
        try:
            int(nuber_str)
            # String is an integer
            return True
        except ValueError:
            # string is not an integer
            return False

    @staticmethod
    def is_str_kks_code(string: str) -> bool:
        """
        Detect strings like 10SAH11CT001, P1, TS1
        :param string:
        :return:
        """
        if string == "" or string is None:
            return False
        # Check if the string length is between 2 and 20 characters
        if not (2 <= len(string) <= 20):
            return False
        # Check if the string contains at least one letter and one number
        if not (any(c.isalpha() for c in string) and any(c.isdigit() for c in string)):
            return False
        # Check if the string contains only uppercase letters and digits
        if not re.match("^[A-Z0-9]*$", string):
            return False
        # checks passed, string is a KKS code
        return True

    @staticmethod
    def find_text_in_tag_from_dict(dic_to_use: dict, tag_text: str, language: AlarmLanguage) -> Tuple[str, str]:
        for key, value in dic_to_use.items():
            if tag_text.startswith(key):
                rest_of_str = tag_text.replace(key, "",1)
                return dic_to_use.get(key)[language.value], rest_of_str
        return None, None

    @staticmethod
    def handle_device_alarm_tag(alarm_tag: str, language: AlarmLanguage) -> Tuple[bool,str]:
        if "." in alarm_tag:
            """
            Tag is a bit from a function block, example:
            pump_glycol_10PGA20AP001_move_fault.move_fault
            pump_nw_3_summer_10NDA13AP001".local_remote
            """
            full_success, return_text = TagConverter.handle_device_alarms_from_fb_blocks(alarm_tag, language)
        else:
            """
            Tag is an input
            pump_circ_3_summer_vfd_on_10NDA13AP001
            pump_nw_filter_rdy_10NDA11AP001
            """
            full_success, return_text = TagConverter.handle_device_alarms_from_inputs(alarm_tag, language)
        return full_success, return_text

    @staticmethod
    def handle_device_alarms_from_inputs(alarm_tag: str, language: AlarmLanguage) -> Tuple[bool,str]:
        logging.debug("handle_device_alarms_from_inputs")
        full_success = False
        # tags like this pump_circ_1_winter_vfd_on_10NDA10AP001
        expected_kks = alarm_tag.split("_")[-1]
        kks_str = ""
        if TagConverter.is_str_kks_code(expected_kks):
            kks_str = expected_kks
            alarm_tag = alarm_tag.replace(kks_str, "")
            alarm_tag = alarm_tag.strip("_")
        alarm_text, rest_of_tag = TagConverter.get_generic_text_from_tag(alarm_tag, language)
        if rest_of_tag == "":
            full_success = True
        logging.debug(f"handle_device_alarms_from_inputs returning alarm_text |{alarm_text}| kks_str |{kks_str}|")
        return full_success, f"{alarm_text} {kks_str}".strip() + "!"

    @staticmethod
    def handle_power_alarm_tag(alarm_tag: str, language: AlarmLanguage) -> Tuple[bool,str]:
        """
        Alarms that look like this:
        pwr_mains_ok
        :param alarm_tag:
        :return:
        """
        full_success = False
        logging.debug("handle_power_alarm_tag")
        alarm_tag_to_use = alarm_tag.replace("pwr_", "", 1)
        logging.debug(f"Tag after removing pwr: {alarm_tag_to_use}")
        alarm_text, rest_of_str = TagConverter.find_text_in_tag_from_dict(power_alarms, alarm_tag_to_use, language)
        logging.debug(f"After dict: alarm_text {alarm_text} rest_of_str {rest_of_str}|")
        if alarm_text and not rest_of_str:
            full_success = True
            return full_success, f"{alarm_text}!"
        alarm_text, rest_of_tag = TagConverter.get_generic_text_from_tag(alarm_tag_to_use, language)
        if not rest_of_tag and alarm_text:
            full_success = True
        return full_success, f"{alarm_text}!"

    @staticmethod
    def handle_digital_sensor_alarm_tag(alarm_tag: str, language: AlarmLanguage) -> Tuple[bool,str]:
        """
        sw_press_max_10NDA50CP001_DB".Q
        :param alarm_tag:
        :param language:
        :return:
        """
        logging.debug(f"handle_digital_sensor_alarm_tag {alarm_tag}")
        full_success = False
        alarm_tag = alarm_tag.replace("_DB\".Q", "")
        alarm_tag = alarm_tag.replace("_DB", "")
        expected_kks = alarm_tag.split("_")[-1]
        kks_str = ""
        if TagConverter.is_str_kks_code(expected_kks):
            kks_str = expected_kks
            alarm_tag = alarm_tag.replace(kks_str, "")
            alarm_tag = alarm_tag.strip("_")
        device_alarm_type, rest_of_str = TagConverter.get_digital_sensor_type_text(alarm_tag, language)
        alarm_text, rest_of_tag = TagConverter.get_generic_text_from_tag(rest_of_str, language)
        if rest_of_tag == "":
            full_success = True
        else:
            logging.debug(f"Rest of tag {rest_of_tag} not empty, not full success")
        device_alarm_type = device_alarm_type.strip(" ")
        alarm_text = alarm_text.strip(" ")
        return full_success, f"{device_alarm_type} {alarm_text} {kks_str}".strip() + "!"

    @staticmethod
    def get_digital_sensor_type_text(alarm_tag_start: str, language: AlarmLanguage) -> Tuple[str, str]:
        for key, value in digital_sensor_alarms.items():
            if alarm_tag_start.startswith(key):
                rest_of_str = alarm_tag_start.replace(key, "", 1)
                return digital_sensor_alarms.get(key)[language.value], rest_of_str
        # if not in dicts just return start of same string
        print(f"Could not find sensor type for {alarm_tag_start}")
        tag_start = alarm_tag_start.split("_")[0]
        return tag_start, alarm_tag_start.replace(tag_start, "")

    @staticmethod
    def handle_unknown_alarm_tag(alarm_tag: str, language: AlarmLanguage) -> Tuple[bool,str]:
        full_success = False
        logging.debug("handle_unknown_alarm_tag")
        alarm_tag_to_use = alarm_tag
        if TagConverter.check_if_alarm_text_is_place_holder(alarm_tag_to_use):
            full_success = True
            return full_success, TagConverter.ALARM_TEXT_PLACEHOLDER
        # remove unmeaningful text
        alarm_tag_to_use = (alarm_tag_to_use.replace("_DB\".Q", "")
                            .replace("_DB", "_")
                            .replace(".", "_")
                            .replace("\"", ""))
        alarm_end_text = ""
        alarm_type_text, rest_of_tag = TagConverter.find_text_in_tag_end_from_dict(device_alarms, alarm_tag_to_use,
                                                                                   language)
        if alarm_type_text is not None and rest_of_tag is not None:
            alarm_end_text = alarm_type_text
            alarm_tag_to_use = rest_of_tag
        # check if end has KKS
        expected_kks = alarm_tag_to_use.split("_")[-1]
        if TagConverter.is_str_kks_code(expected_kks):
            kks_str = expected_kks
            alarm_end_text = alarm_end_text + " " + kks_str
            alarm_tag_to_use = alarm_tag_to_use.replace(kks_str, "")
            alarm_tag_to_use = alarm_tag_to_use.strip("_")
        alarm_text, rest_of_tag = TagConverter.get_generic_text_from_tag(alarm_tag_to_use, language)
        alarm_end_text = alarm_end_text.strip(" ")
        alarm_text = alarm_text.strip(" ")
        if alarm_text and not rest_of_tag:
            full_success = True
        else:
            logging.debug(f"Not full success, alarm text is {alarm_text}, rest_of_tag {rest_of_tag}!")
        if alarm_text != "" and alarm_end_text == "":
            return full_success,f"{alarm_text}!"
        elif alarm_text != "" or alarm_end_text != "":
            return full_success,f"{alarm_text} {alarm_end_text}!"
        else:
            # If not able to generate text return tag
            return full_success, alarm_tag

    @staticmethod
    def find_text_in_tag_end_from_dict(dic_to_use: dict, tag_text: str, language: AlarmLanguage) -> Tuple[str, str]:
        for key, value in dic_to_use.items():
            if tag_text.endswith(key):
                rest_of_str = tag_text.replace(key, "")
                return dic_to_use.get(key)[language.value], rest_of_str
        return None, None

    @staticmethod
    def check_if_alarm_text_is_place_holder(alarm_tag: str):
        if alarm_tag in place_holder_text:
            # alarm is placeholder with no number
            return True
        # remove "_" so empty_19 -> empty19
        no_underscores_text = alarm_tag.replace("_", "")
        for place_holder in place_holder_text:
            if TagConverter.is_string_with_number(no_underscores_text, place_holder):
                # text is empty19, false21, a23 etc.
                return True
        return False

    @staticmethod
    def is_string_with_number(text_to_search_in, string_to_detect):
        pattern = rf"{string_to_detect}([0-9]|[1-9][0-9]{{1,2}})$"
        return bool(re.match(pattern, text_to_search_in))

    @staticmethod
    def detect_alarm_type(alarm_tag: str):
        logging.debug("Detecting alarm type")
        for alarm_type, alarm_tag_start_list in ALARM_TAG_TO_TYPE_DICT.items():
            logging.debug(f"Alarm type {alarm_type}")
            for alarm_tag_start in alarm_tag_start_list:
                logging.debug(f"alarm_tag_start {alarm_tag_start}")
                if alarm_tag.startswith(alarm_tag_start):
                    return alarm_type
        return AlarmType.UNKNOWN

    @staticmethod
    def split_sensor_al_text(input_string: str):
        pattern = r"(.*)_("
        for key in sensor_alarms.keys():
            pattern = pattern+key+'|'
        pattern = pattern[:-1]#remove last |
        pattern = pattern + ")$"
        match = re.match(pattern, input_string)
        if match:
            return match.group(1), match.group(2)
        return input_string, None


METHOD_MAP = {
    AlarmType.SENSOR_ALARM: TagConverter.handle_sensor_alarm_tag,
    AlarmType.DEVICE_ALARM: TagConverter.handle_device_alarm_tag,
    AlarmType.POWER_ALARM: TagConverter.handle_power_alarm_tag,
    AlarmType.DIGITAL_SENSOR_ALARM: TagConverter.handle_digital_sensor_alarm_tag,
    AlarmType.UNKNOWN: TagConverter.handle_unknown_alarm_tag
}

if __name__ == '__main__':
    test()
