from typing import List, Iterable, Any, Type, TypeVar
from abc import ABC, abstractmethod

DB = TypeVar("DB", bound="DatabaseBase")


class Document:
    """Interface for interacting with a document."""
    id: str
    content: str
    source: str


class DatabaseBase(ABC):
    @abstractmethod
    def add_contents(
        self,
        contents: Iterable[str],
        **kargs: Any
    ) -> List[str]:
        """Run more contents through the items and add to the database.

        Args:
            contents: Iterable of strings to add to the database.
            kwargs: database specific parameters

        Returns:
            List of ids from adding the texts into the database.
        """

    def add_documents(
        self,
        documents: List[Document],
        **kargs: Any
    ) -> List[str]:
        """Run more documents through the items and add to the database.

        Args:
            documents (List[Document]: Documents to add to the database.

        Returns:
            List[str]: List of IDs of the added contents.
        """
        contents = [document.content for document in documents]
        return self.add_contents(contents, **kargs)

    @classmethod
    @abstractmethod
    def get_contents(
        cls: Type[DB],
        contents: Iterable[str],
        **kargs: Any
    ) -> DB:
        """Return database initialized from contents."""

    @classmethod
    def get_documents(
        cls: Type[DB],
        documents: List[Document],
        **kargs: Any
    ) -> DB:
        """Return database initialized from documents."""
        contents = [document.content for document in documents]
        return cls.get_contents(contents, **kargs)
