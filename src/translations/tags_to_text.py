import logging
import re

from src.config import default_settings
from src.database.sa_tables import AlarmLanguage, Tag
from src.translations.translation_bundle import TranslationBundle

logger = logging.getLogger(__name__)
logger.setLevel(default_settings.LOGGING_LVL_GLOBAL)

# What symbol to use for placeholder
ALARM_TEXT_PLACEHOLDER = "*"
# How many loops to attempt for converting of tag
TRANSLATE_LOOPS = 10


def convert_tags_to_alarm_text(
    alarm_tags: list,
    language: AlarmLanguage,
    translation_bundle: TranslationBundle,
) -> list[str]:
    """_summary_

    Args:
        alarm_tags (list): _description_
        language (AlarmLanguage): _description_
        word_list (list[Tag]): _description_
        phrases_list (list[Tag]): _description_

    Returns:
        list[str]: _description_
    """
    alarm_texts: list[str] = []
    for i, alarm_tag in enumerate(alarm_tags):
        logger.debug(f"Handling alarm {i}:{alarm_tag}")
        success, alarm_text = get_al_text_from_tag(
            alarm_tag, language, translation_bundle
        )
        # Info messages of result
        if not success:
            logger.error(f"Failed to fully convert alarm nr {i + 1}, {alarm_tag}")
        else:
            logger.debug(f"Full success with alarm nr {i + 1}, {alarm_tag}")

        # Add created alarm to list
        if not alarm_text:
            alarm_text = f"{i} {alarm_tag}"
            logger.error(f"Could not get any text for tag {alarm_text}")
        elif alarm_text == ALARM_TEXT_PLACEHOLDER:
            # Place holder has only translations for lv and en
            if language.value == "lv":
                alarm_text = f"{translation_bundle.placeholder_translation.lv} {i + 1}"
            else:
                alarm_text = f"{translation_bundle.placeholder_translation.en} {i + 1}"
        else:
            # Alarm translation at least partially succesful
            # Strip spaces
            alarm_text = alarm_text.strip(" ")
            # capitalie the first letter, add ! in the end
            alarm_text = alarm_text[0].upper() + alarm_text[1:] + "!"
        alarm_texts.append(alarm_text)
    return alarm_texts


def get_al_text_from_tag(
    alarm_tag: str,
    language: AlarmLanguage,
    translation_bundle: TranslationBundle,
) -> tuple[bool, str]:
    """get alarm text from tag

    Args:
        alarm_tag (str): tag
        language (AlarmLanguage): language for text

    Returns:
        tuple[bool, str]: success, alarm text to use
    """
    # Before looping over possible translations check if tag is not just a placeholder
    if is_str_place_holder(alarm_tag, translation_bundle):
        return True, ALARM_TEXT_PLACEHOLDER
    alarm_tag_to_use = remove_unmeaningful_text_from_tag_str(alarm_tag)
    logger.debug(f"After removing unmeaningful text:{alarm_tag_to_use}")
    full_success, alarm_text = translate_tag_by_looping(
        alarm_tag_to_use, language, translation_bundle
    )
    return full_success, alarm_text


def translate_tag_by_looping(
    alarm_tag: str,
    language: AlarmLanguage,
    translation_bundle: TranslationBundle,
) -> tuple[bool, str]:
    """Go over tag and attempt to translate all of it
    Args:
        alarm_tag (str): _description_
        language (AlarmLanguage): _description_

    Returns:
        tuple[bool, str, str]: full_success, alarm text
    """

    alarm_text = ""
    rest_of_tag = alarm_tag
    full_success = True
    for _ in range(TRANSLATE_LOOPS):
        # Remove _ at end and beginning, will be there in loops after first
        rest_of_tag = rest_of_tag.strip("_").strip(" ")
        logger.debug(f"Loop nr {_ + 1}, rest of tag:{rest_of_tag}")
        if rest_of_tag == "":
            logger.debug("Rest of tag empty, all translated")
            # Nothing to search for any more
            return full_success, alarm_text
        if is_start_a_kks_code(rest_of_tag):
            # Start of tag is a KKS code
            alarm_text += f" {rest_of_tag.split('_')[0]}"
            rest_of_tag = "_".join(rest_of_tag.split("_")[1:])
            logger.debug("Start of tag is KKS code")
            continue
        # Look for no_translation text
        no_translation_txt_fnd, rest_of_tag = (
            look_for_no_translation_text_at_string_start(
                rest_of_tag, translation_bundle.no_translation
            )
        )
        if no_translation_txt_fnd:
            # Alarm text remains unichanged
            logger.debug(
                f"Tag starts with no translations text. Alarm text so far:{alarm_text}"
            )
            continue
        # Look for translation in lists. Start with phrases, then continue to words
        translation, rest_of_tag = look_for_translated_tag_at_at_string_start(
            rest_of_tag, translation_bundle, language
        )
        if translation:
            alarm_text += f" {translation}"
            logger.debug(f"Alarm text so far:{alarm_text}")
            continue
        number_str, rest_of_tag = extract_suplementary_number(rest_of_tag)
        if number_str:
            # Add number to alarm text.
            alarm_text += f" {number_str}"
            logger.debug(
                f"Tag starts with number {number_str}. Alarm text so far:{alarm_text}"
            )
            continue
        if is_start_letter_plus_number(rest_of_tag):
            # Start of tag is: p1, m1 or similar
            alarm_text += f" {rest_of_tag.split('_')[0]}"
            rest_of_tag = "_".join(rest_of_tag.split("_")[1:])
            logger.debug("Start of tag is string plus number")
            continue

        # DId not recognise anything defined in tag
        unrecognised_part, rest_of_tag = handle_unrecognised_tag_start(rest_of_tag)
        alarm_text = alarm_text + " " + unrecognised_part
        # Reset full succes if there was an unstranslated par of the tag
        full_success = False
    logger.warning(f"Was not able to translate all of tag in {TRANSLATE_LOOPS} loops")
    full_success = False
    # Add untranslated part to to alarm text
    alarm_text += f" {rest_of_tag}"
    return full_success, alarm_text


def look_for_translated_tag_at_at_string_start(
    tag: str, bundle: TranslationBundle, language: AlarmLanguage
) -> tuple[str, str]:
    # Look for translation in lists. Start with phrases, then continue to words
    for translation_list, label in [(bundle.phrases, "phrase"), (bundle.words, "word")]:
        translation, rest_of_tag = look_for_translation_at_string_start(
            tag, translation_list, language
        )
        if translation:
            logger.debug(f"Tag starts with {label}.")
            return translation, rest_of_tag
    return "", tag


def handle_unrecognised_tag_start(alarm_tag: str) -> tuple[str, str]:
    """Remove unrecognised part of tag so the rest can be translated
    Args:
        alarm_tag (str):

    Returns:
        tuple[str, str]: unrecognised_part, rest_of_tag
    """
    unrecognised_part = alarm_tag.split("_")[0]
    rest_of_tag = alarm_tag.replace(unrecognised_part, "")
    logging.warning(
        f"Could not get predefined info from tag. Tag text {alarm_tag}, Unrecognised part: {unrecognised_part}, condtinuing with  {rest_of_tag}"
    )
    return unrecognised_part, rest_of_tag


def look_for_translation_at_string_start(
    alarm_tag: str, translations_list: list[Tag], language: AlarmLanguage
) -> tuple[str, str]:
    """_summary_

    Args:
        alarm_tag (str): _description_
        translations_list (list[Tag]): _description_

    Returns:
        tuple[str, str]: translated alarm text (empty if was not found), rest of tag
    """
    for translation in translations_list:
        if alarm_tag.startswith(translation.tag):
            # Remove the translated tag from the string to use
            rest_of_tag = alarm_tag.replace(f"{translation.tag}", "", 1)
            return translation.translate(language), rest_of_tag
    # Did not find trasnaltion
    return "", alarm_tag


def look_for_no_translation_text_at_string_start(
    alarm_tag: str, no_translations_list: list[Tag]
) -> tuple[bool, str]:
    """_summary_

    Args:
        alarm_tag (str): _description_
        translations_list (list[Tag]): _description_

    Returns:
        tuple[bool, str]: true if no translation text was found + rest of tag after removing the text
    """
    for translation in no_translations_list:
        if alarm_tag.startswith(translation.tag):
            # Remove the translated tag from the string to use
            logger.debug(f"String starts with no translations text:{translation.tag}")
            rest_of_tag = alarm_tag.replace(f"{translation.tag}", "", 1)
            return True, rest_of_tag
    # Did not find trasnaltion
    return False, alarm_tag


def extract_suplementary_number(alarm_tag: str) -> tuple[str, str]:
    """If string something like this: 1_winter_alarm. Add the number to the string

    Args:
        alarm_tag (str): _description_

    Returns:
        tuple[str, str]: number string, rest of tag
    """
    number_str, rest_of_tag = "", alarm_tag
    if is_start_a_number(alarm_tag):
        number_str = alarm_tag.split("_")[0]
        logger.debug(f"String starts with supplementary number:{number_str}")
        # Remove the number from the string to use
        rest_of_tag = alarm_tag.replace(f"{number_str}", "", 1)
        logger.debug(f"After removing number:{rest_of_tag}")
    return number_str, rest_of_tag


def is_start_a_number(string: str) -> bool:
    nuber_str = string.split("_")[0]
    try:
        int(nuber_str)
        # String is an integer
        return True
    except ValueError:
        # string is not an integer
        return False


def remove_unmeaningful_text_from_tag_str(alarm_tag: str) -> str:
    """_summary_

    Args:
        alarm_tag (str): _description_

    Returns:
        str: _description_
    """
    return (
        alarm_tag.replace('_DB".Q', "")  # Timer blocks
        .replace("_DB", "_")  # Data blocks
        .replace(".", "_")
        .replace('"', "")
    )


def is_str_place_holder(alarm_tag: str, translations_bundle: TranslationBundle) -> bool:
    """check if text is just a placeholder not an actual alarm

    Args:
        alarm_tag (str): alarm tag to check for being a placeholder

    Returns:
        bool: true if is placeholder text
    """
    if alarm_tag in translations_bundle.placeholders:
        # alarm is placeholder with no number
        return True
    # remove "_" so empty_19 -> empty19
    no_underscores_text = alarm_tag.replace("_", "")
    logger.debug(f"no_underscores_text {no_underscores_text}")
    for place_holder in translations_bundle.placeholders:
        logger.debug(f"Compare w {place_holder.tag}")
        if is_string_with_number(no_underscores_text, place_holder.tag):
            # text is empty19, false21, a23 etc.
            return True
    return False


def is_string_with_number(text_to_search_in, string_to_detect) -> bool:
    """
    Check if text is string with number in end.
    Check that text is something like alarm123
    :param text_to_search_in: full text to seach in
    :param string_to_detect:string to look for
    """
    pattern = rf"{string_to_detect}([0-9]|[1-9][0-9]{{1,2}})$"
    return bool(re.match(pattern, text_to_search_in))


def is_start_a_kks_code(string: str) -> bool:
    # Tag sis divided by _
    str_start = string.split("_")[0]
    if is_str_kks_code(str_start):
        return True
    return False


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


def is_start_letter_plus_number(string: str) -> bool:
    # Tag sis divided by _
    str_start = string.split("_")[0]
    if is_str_letter_plus_number(str_start):
        return True
    return False


def is_str_letter_plus_number(string: str) -> bool:
    """
    Detect strings like p1, m1
    No translation needed for this. Handled to not show alarm message
    :param string:
    :return:
    """
    if string == "" or string is None:
        return False
    # Check if the string length is between 2 and 20 characters
    if not (2 <= len(string) <= 4):
        return False
    # Check if the string contains at least one letter and one number
    if not (any(c.isalpha() for c in string) and any(c.isdigit() for c in string)):
        return False
    # Check if the string contains only uppercase letters and digits
    if not re.match("^[a-z0-9]*$", string):
        return False
    # checks passed, string is a KKS code
    return True


def extract_kks(alarm_tag: str) -> tuple[str, str]:
    """Check if tag contains KKS code (10SAH11CT001, P1, TS1) and if it does extract it
    Args:
        alarm_tag (str): _description_

    Returns:
        tuple[str, str]: kks code, original tag with kks removed
    """
    logger.debug(f"Extracting KKS code from tag {alarm_tag}")
    kks_str, rest_of_tag = "", alarm_tag
    # Tag sis divided by _
    divided_tag = alarm_tag.split("_")
    # Check if any of the parts is a kks code
    for text in divided_tag:
        if is_str_kks_code(text):
            kks_str = text
            rest_of_tag = alarm_tag.replace(kks_str, "")
            rest_of_tag = rest_of_tag.replace("__", "_")
            rest_of_tag = rest_of_tag.strip("_")
            logger.debug(f"Extracted KKS code {kks_str} rest of ta {rest_of_tag}")
            return kks_str, rest_of_tag
    logger.debug("Did not find KKS code")
    return kks_str, rest_of_tag
