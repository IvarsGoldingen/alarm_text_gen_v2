import logging

from sqlalchemy import create_engine, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, sessionmaker

from src.config import default_settings
from src.database.db_protocol import Db_proto
from src.database.sa_tables import Base, Tag, TagType

logger = logging.getLogger(__name__)
logger.setLevel(default_settings.LOGGING_LVL_GLOBAL)


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

    def get_all_tags_of_type(
        self,
        type_name: str | None = None,
        longest_first: bool = True,
        eager_load: bool = True,
    ) -> list[Tag]:
        """
        Args:
            type_name (str): if None then return all types
            longest_first (bool, optional): Get longest tags first - use this normally so when translating you don' t get half translated word. Defaults to True.
            eager_load: load eagerly - needed for code not to break, because no reference to DB is held at some points in code
        Returns:
            list[Tag]: _description_
        """
        logger.debug(f"Gettings tags of type {type_name}")
        tags_list: list[Tag] = []
        with self.SessionLocal() as session:
            try:
                query = session.query(Tag)
                if longest_first:
                    query = query.order_by(func.char_length(Tag.tag).desc())
                if type_name:
                    query = query.join(Tag.type_obj).filter(TagType.name == type_name)
                if eager_load:
                    query = query.options(joinedload(Tag.type_obj))
                tags_list = query.all()
                logger.debug(f"Found {len(tags_list)} tags")
                return tags_list
            except Exception as e:
                logger.error(f"Failed to get tags of type {type_name}. {e}")
        return tags_list

    def get_all_tags_as_dict(
        self,
        type_name: str | None = None,
    ) -> list[dict]:
        """
        Get tags as dictionary. Needed for UI
        Args:
            type_name (str | None, optional): If None return all types. Defaults to None.
        Returns:
            list[dict]: representing Tag objects
        """
        tags = self.get_all_tags_of_type(eager_load=True, type_name=type_name)
        return [
            {
                "id": t.id,
                "tag": t.tag,
                "type": t.type_obj.name,
                "lv": t.lv,
                "en": t.en,
            }
            for t in tags
        ]

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

    def get_all_types_as_dict(self) -> list[dict]:
        type_list = self.get_all_types()
        return [{"label": t.name, "value": t.id} for t in type_list]
