import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.database.db_protocol import Db_proto
from src.database.sa_tables import Base, Tag, TagType

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LVL_GLOBAL)


class SqliteHelper(Db_proto):
    def init_db(self, **kwargs) -> None:
        logger.info(f"Initing database with URL {kwargs.get('url', 'no URL')}")
        """Create all tables if they don't exist."""
        db_url: str | None = kwargs.get("url")
        if db_url is None:
            raise ValueError("Missing required parameter url")
        final_url = f"sqlite:///{db_url}"
        # Create engine
        self.engine = create_engine(final_url, echo=False)
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.debug("Initing databases")
        Base.metadata.create_all(self.engine)

    def insert_tag(self, tag: str, type: str, lv: str, en: str) -> None:
        logger.debug(f"Inserting tag='{tag}', type='{type}', lv='{lv}', en='{en}'")
        with self.SessionLocal() as session:
            # get type by name
            type = session.query(TagType).filter_by(name=type).first()
            if not type:
                raise ValueError("Non existant TagType")
            tag_to_add = Tag(tag=tag, type=type.id, lv=lv, en=en)
            try:
                session.add(tag_to_add)
                session.commit()
                logger.debug(f"Inserted phrase with tag='{tag}', lv='{lv}', en='{en}'")
            except IntegrityError:
                session.rollback()
                logger.warning(f"Tag '{tag}' already exists.")

    def delete_tag(self, tag: str) -> bool:
        with self.SessionLocal() as session:
            item_to_delete = session.query(Tag).filter_by(tag=tag).first()
            if item_to_delete:
                session.delete(item_to_delete)
                session.commit()
                return True
            else:
                logger.debug(f"No item to delete by tag {tag}")
                return False

    def create_type(self, name: str) -> None:
        logger.info(f"Creating type {name}")
        new_type = TagType(name=name)
        with self.SessionLocal() as session:
            try:
                session.add(new_type)
                session.commit()
            except IntegrityError:
                session.rollback()
                logger.warning(f"Type with name '{name}' already exists.")

    def get_all_tags_of_type(self, type_name: str) -> list[Tag]:
        logger.debug(f"Gettings tags of type {type_name}")
        tags_list: list[Tag] = []
        with self.SessionLocal() as session:
            try:
                tags_list = (
                    session.query(Tag)
                    .join(Tag.type_obj)
                    .filter(TagType.name == type_name)
                    .all()
                )
                logger.debug(f"Found {len(tags_list)} tags")
                return tags_list
            except Exception as e:
                logger.error(f"Failed to get tags of type {type_name}. {e}")
        return tags_list

    def get_all_tags(self) -> list[Tag]:
        tags_list: list[Tag] = []
        with self.SessionLocal() as session:
            try:
                tags_list = session.query(Tag).all()
                logger.debug(f"Found {len(tags_list)} tags")
                return tags_list
            except Exception as e:
                logger.error(f"Failed to get all tags. {e}")
        return tags_list

    def get_all_types(self) -> list[TagType]:
        types_list: list[TagType] = []
        with self.SessionLocal() as session:
            try:
                types_list = session.query(TagType).all()
                logger.debug(f"Found {len(types_list)} types")
                return types_list
            except Exception as e:
                logger.error(f"Failed to get all types. {e}")
        return types_list
