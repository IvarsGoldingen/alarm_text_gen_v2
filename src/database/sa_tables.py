import logging
from enum import Enum

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

from src.config import settings

"""
SQLAlchemy tables for translations
"""

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LVL_GLOBAL)

Base = declarative_base()


class MissingLanguageError(Exception):
    """Exception raised when a requested language column is missing."""

    pass


class AlarmLanguage(Enum):
    # These must be the same as atribute names in sa_tables.py
    ENGLISH = "en"
    LATVIAN = "lv"


class Types(Enum):
    # Word with translation
    WORD = "word"
    # Phrase with translation
    PHRASE = "phrase"
    # Tag that should be ignored
    NO_TRANSLATION = "no_translation"
    # Tag that should be converted to something generic like Alarm N (N alarm number)
    PLACEHOLDER = "placeholder"
    # The generic translation for all placeholders
    PLACEHOLDER_TRANSLATION = "placeholder_translation"


class TagType(Base):
    __tablename__ = "types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # back-reference to Tag of this type
    tags: Mapped[list["Tag"]] = relationship(back_populates="type_obj")

    def __repr__(self):
        return f"Type(id={self.id!r}, name={self.name!r})"


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[int] = mapped_column(ForeignKey("types.id"), nullable=False)
    # If more languages added update AlarmLanguage enum class
    lv: Mapped[str]
    en: Mapped[str]

    # Relationship property to access Type object
    type_obj: Mapped["TagType"] = relationship(back_populates="tags")

    def __repr__(self) -> str:
        return f"Tag(id={self.id!r}, tag={self.tag!r}, lv={self.lv!r}, en={self.en!r})"

    def translate(self, lang: AlarmLanguage) -> str:
        """get translation of tag

        Args:
            lang (AlarmLanguage): language

        Returns:
            str: translated text
        """
        try:
            translation = getattr(self, lang.value)
        except AttributeError:
            raise MissingLanguageError(f"No column defined for language f{lang.value}")
        if not translation:
            logger.error(f"No translation for {self.tag} in {lang.value}")
        return getattr(self, lang.value)
