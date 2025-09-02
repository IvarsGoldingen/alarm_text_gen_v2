from dataclasses import dataclass

from src.database.sa_tables import Tag


@dataclass
class TranslationBundle:
    """
    A bundle of list containing different type of translations
    """

    phrases: list[Tag]
    words: list[Tag]
    no_translation: list[Tag]
    placeholders: list[Tag]
    placeholder_translation: Tag

    def __repr__(self):
        return f"<TranslationBundle phrases={len(self.phrases)}, \
        words={len(self.words)}, \
        no translation={len(self.no_translation)}, \
        placeholders={len(self.placeholders)}, \
        placeholder translations \
        LV={self.placeholder_translation.lv} \
        EN={self.placeholder_translation.en}>"
