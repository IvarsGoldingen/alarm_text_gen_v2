import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import default_settings
from src.database.sa_tables import Base

logger = logging.getLogger(__name__)
logger.setLevel(default_settings.LOGGING_LVL_GLOBAL)

DATABASE_URL = f"sqlite:///{default_settings.DB_PATH}"
# Create engine
engine = create_engine(DATABASE_URL, echo=False)
# Create session factory
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables if they don't exist."""
    logger.debug("Initing databases")
    Base.metadata.create_all(engine)


def insert_phrase(tag: str, lv: str, en: str):
    with SessionLocal() as session:
        hello = Phrase(tag=tag, lv=lv, en=en)
        session.add(hello)
        session.commit()
        logger.debug(f"Inserted phrase with tag='{tag}', lv='{lv}', en='{en}'")


def delete_phrase_by_tag(tag: str) -> bool:
    with SessionLocal() as session:
        item_to_delete = session.query(Phrase).filter_by(tag=tag).first()
        if item_to_delete:
            session.delete(item_to_delete)
            session.commit()
            return True
        else:
            logger.debug(f"No item to delete by tag {tag}")
            return False


from sqlalchemy import String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class Phrase(Base):
    __tablename__ = "phrases"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str]
    lv: Mapped[str]
    en: Mapped[str]

    def __repr__(self) -> str:
        return (
            f"Phrases(id={self.id!r}, tag={self.tag!r}, lv={self.lv!r}, en={self.en!r})"
        )


class Words(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    lv: Mapped[str]
    en: Mapped[str]

    def __repr__(self) -> str:
        return (
            f"Phrases(id={self.id!r}, tag={self.tag!r}, lv={self.lv!r}, en={self.en!r})"
        )
