import logging
import uuid
from typing import Any, Iterable, List, Type, Optional

from databases import DB, Document, DatabaseBase

logger = logging.getLogger()


class MongoDBClient(DatabaseBase):
    def __init__(self, mongodb_host: str = "mongodb://localhost:27017/") -> None:
        """Initialize with MongoDB client."""
        try:
            from pymongo import MongoClient
        except ImportError:
            raise ValueError(
                "Could not import pymongo python package. "
                "Please install it with `poetry install pymongo`."
            )
        self.mongodb_host = mongodb_host
        self.mongo_client = MongoClient(self.mongodb_host)

    def check_database(
        self,
        database_test: str = "database_test"
    ) -> None:
        """"""
        database = self.mongo_client[database_test]
        logger.info(database)
        # mongodb_list = database.list_database_names()
        # if database_test in mongodb_list:
        #     logger.info("The database exists.")

    def add_contents(
            self,
            contents: Iterable[str],
            ids: Optional[List[str]] = None,
            **kargs: Any
    ) -> List[str]:
        if ids is None:
            ids = [str(uuid.uuid1()) for _ in contents]
        self.mongo_client.insert_many(contents=contents, ids=ids)
        return ids

    @classmethod
    def get_contents(
        cls: Type[DB],
        contents: Iterable[str],
        mongodb_host: str = "mongodb://localhost:27017/",
        **kargs: Any
    ) -> DB:
        """Create a Mongo database from a list of documents.

        Args:
            content <Iterable[str]>: List of contents to add to the database.
            mongodb_host <str>: Mongo host
        Returns:
            MongoDBClient: MongoDBClient database.
        """
        mongo_collection = cls(
            mongodb_host=mongodb_host
        )
        mongo_collection.add_contents(contents=contents)
        return mongo_collection

    @classmethod
    def get_documents(
        cls: Type[DB],
        documents: List[Document],
        mongodb_host: str = "mongodb://localhost:27017/",
        **kargs: Any
    ) -> DB:
        """Create a Mongo database from a list of documents.

        Args:
            documents <List[Document]>: List of documents to add to the database.
            mongodb_host <str>: Mongo host
        Returns:
            MongoDBClient: MongoDBClient database.
        """
        contents = [doc.page_content for doc in documents]
        return cls(
            contents=contents,
            mongodb_host=mongodb_host
        )


if __name__ == '__main__':
    mongo_database = MongoDBClient()
