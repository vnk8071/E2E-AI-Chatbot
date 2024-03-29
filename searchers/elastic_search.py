import uuid
from typing import List, Optional, Dict, Any, Tuple
from abc import ABC

from searchers import SearchBase
from databases import Document


def _default_script_query(query: str, filter: Optional[dict]) -> Dict:
    if filter:
        ((key, value),) = filter.items()
        filter = {"match": {f"metadata.{key}.keyword": f"{value}"}}
    else:
        filter = {"match_all": {}}
    return {
        "query": {
            "bool": {
                "should": [
                    {"multi_match": {"query": f"{query}"}},
                    {"match_phrase": {"content": {"query": f"{query}", "boost": 2}}},
                ]
            }
        }
    }


class ElasticSearch(SearchBase, ABC):
    """Wrapper around Elasticsearch as a database."""

    def __init__(
        self,
        elasticsearch_host: str,
        index_name: str,
    ):
        """Initialize with necessary components."""
        try:
            import elasticsearch
        except ImportError:
            raise ImportError(
                "Could not import elasticsearch python package. "
                "Please install it with `poetry add elasticsearch`."
            )
        self.index_name = index_name
        try:
            self.client = elasticsearch.Elasticsearch(elasticsearch_host)
        except ValueError as e:
            raise ValueError(
                f"Your elasticsearch client string is mis-formatted. Got error: {e} "
            )

    def rec_to_actions(self, documents):
        for i, document in enumerate(documents):
            _id = str(uuid.uuid4())
            yield {
                "_op_type": "index",
                "_index": self.index_name,
                "content": document["content"],
                "metadata": document["metadata"],
                "_id": _id,
            }

    def add_contents(
        self,
        documents: List[Document],
        refresh_indices: bool = True,
        **kwargs: Any,
    ) -> List[str]:
        """Run more contents through the embeddings and add to the vectorstore.

        Args:
            contents: Iterable of strings to add to the vectorstore.
            metadatas: Optional list of metadatas associated with the contents.
            refresh_indices: bool to refresh ElasticSearch indices

        Returns:
            List of ids from adding the contents into the Elasticsearch.
        """
        try:
            from elasticsearch.helpers import bulk
        except ImportError:
            raise ImportError(
                "Could not import elasticsearch python package. "
                "Please install it with `poetry add elasticsearch`."
            )

        # check to see if the index already exists
        if not (self.client.indices.exists(index=self.index_name)):
            self.client.indices.create(index=self.index_name)

        bulk(self.client, self.rec_to_actions(documents))
        if refresh_indices:
            self.client.indices.refresh(index=self.index_name)

    def simple_search(
        self, query: str, k: int = 2, filter: Optional[dict] = None, **kwargs: Any
    ) -> List[Document]:
        """Return docs most similar to query.

        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 2.

        Returns:
            List of Documents most similar to the query.
        """
        docs_and_scores = self.simple_search_with_score(query, k, filter=filter)
        if docs_and_scores is not None:
            documents = [d[0] for d in docs_and_scores]
            return documents
        return None

    def simple_search_with_score(
        self, query: str, k: int = 2, filter: Optional[dict] = None, **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """Return docs most similar to query.
        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
        Returns:
            List of Documents most similar to the query.
        """
        try:
            script_query = _default_script_query(query, filter)
            response = self.client.search(
                index=self.index_name, body=script_query, size=k
            )
            hits = [hit for hit in response["hits"]["hits"]]
            docs_and_scores = [
                (
                    Document(
                        content=hit["_source"]["content"],
                        metadata=hit["_source"]["metadata"],
                    ),
                    hit["_score"],
                )
                for hit in hits
            ]
            return docs_and_scores
        except ValueError:
            return None

    @classmethod
    def get_contents(
        cls,
        contents: List[str],
        metadatas: Optional[List[dict]] = None,
        elasticsearch_host: Optional[str] = None,
        index_name: Optional[str] = None,
        refresh_indices: bool = True,
        **kwargs: Any,
    ):
        """Construct ElasticSearch wrapper from raw documents."""
        elasticsearch_host = elasticsearch_host
        index_name = index_name or uuid.uuid4().hex
        scoresearch = cls(elasticsearch_host, index_name, **kwargs)
        scoresearch.add_contents(
            contents, metadatas=metadatas, refresh_indices=refresh_indices
        )
        return scoresearch
