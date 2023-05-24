import logging
from typing import Any, Iterable, List, Type, Optional

from databases import DB, Document, DatabaseBase

logger = logging.getLogger(__name__)


class MongoDBClient(DatabaseBase):
    def __init__(
        self,
        mongodb_host: str = "mongodb://localhost:27017/",
        database_name: str = "document"
    ) -> None:
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
        self.mongo_database = self.mongo_client[database_name]
        self.mongo_connect = self.mongo_database[database_name]

    def check_database(
        self,
        database_test: str = "database_test"
    ) -> None:
        """"""
        if database_test in self.mongo_client.list_databases():
            logger.info("The database exists.")
        else:
            logger.info(f"The {database_test} not exists and auto create.")

    def add_contents(
            self,
            contents: Iterable[str],
            ids: Optional[List[str]] = None,
            **kargs: Any
    ) -> List[str]:
        self.mongo_connect.insert_many(documents=contents)
        return ids

    def get_contents(self):
        """"""
        return [doc for doc in self.mongo_connect.find()]

    @classmethod
    def _add_contents(
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
    def _get_documents(
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
        contents = [document.content for document in documents]
        return cls(
            contents=contents,
            mongodb_host=mongodb_host
        )


if __name__ == '__main__':
    mongo_database = MongoDBClient()
