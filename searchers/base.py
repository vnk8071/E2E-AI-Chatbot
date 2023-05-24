from typing import List, Iterable, Any, Tuple, Type, TypeVar
from abc import ABC, abstractmethod

from databases import Document

DB = TypeVar("DB", bound="SearchBase")


class SearchBase(ABC):
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
        contents = [document["content"] for document in documents]
        return self.add_contents(contents, **kargs)

    def search(
        self,
        query: str,
        search_type: str,
        **kwargs: Any
    ) -> List[Document]:
        """Return docs most similar to query using specified search type."""
        if search_type == "simple":
            return self.simple_search(query, **kwargs)
        else:
            raise ValueError(
                f"search_type of {search_type} not allowed. Expected "
                "search_type to be 'simple'."
            )

    @abstractmethod
    def simple_search(
        self,
        query: str,
        k: int = 2,
        **kwargs: Any
    ) -> List[Document]:
        """Return docs most similar to query."""

    def simple_search_with_relevance_scores(
        self,
        query: str,
        k: int = 2,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return docs and relevance scores.

        Args:
            query: input text
            k: Number of Documents to return. Defaults to 2.
            **kwargs: kwargs to be passed to simple search. Should include:
                score_threshold: Optional, a floating point value to
                    filter the resulting set of retrieved docs

        Returns:
            List of Tuples of (doc, simple_score)
        """
        docs_and_simple_scores = self._simple_search_with_relevance_scores(
            query, k=k, **kwargs
        )

        score_threshold = kwargs.get("score_threshold")
        if score_threshold is not None:
            docs_and_simple_scores = [
                (doc, score)
                for doc, score in docs_and_simple_scores
                if score >= score_threshold
            ]
        return docs_and_simple_scores

    def _simple_search_with_relevance_scores(
        self,
        query: str,
        k: int = 2,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return docs and relevance scores.

        """
        raise NotImplementedError

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
