"""Test ingestion utilities."""
from typing import Any, Dict, Iterable, List, Optional, Sequence, Type

from langchain.schema import Document
from langchain.schema.embeddings import Embeddings
from langchain.schema.vectorstore import VST, VectorStore


class InMemoryVectorStore(VectorStore):
    """In-memory implementation of VectorStore using a dictionary."""

    def __init__(self) -> None:
        """Vector store interface for testing things in memory."""
        self.store: Dict[str, Document] = {}

    def delete(self, ids: Optional[Sequence[str]] = None, **kwargs: Any) -> None:
        """Delete the given documents from the store using their IDs."""
        if ids:
            for _id in ids:
                self.store.pop(_id, None)

    async def adelete(self, ids: Optional[Sequence[str]] = None, **kwargs: Any) -> None:
        """Delete the given documents from the store using their IDs."""
        if ids:
            for _id in ids:
                self.store.pop(_id, None)

    def add_documents(
        self,
        documents: Sequence[Document],
        *,
        ids: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add the given documents to the store (insert behavior)."""
        if ids and len(ids) != len(documents):
            raise ValueError(
                f"Expected {len(ids)} ids, got {len(documents)} documents."
            )

        if not ids:
            start_idx = max(self.store.keys(), default=0)
            ids = [str(x) for x in (range(start_idx, start_idx + len(documents)))]

        for _id, document in zip(ids, documents):
            if _id in self.store:
                raise ValueError(
                    f"Document with uid {_id} already exists in the store."
                )
            self.store[_id] = document
        return ids

    async def aadd_documents(
        self,
        documents: Sequence[Document],
        *,
        ids: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        if ids and len(ids) != len(documents):
            raise ValueError(
                f"Expected {len(ids)} ids, got {len(documents)} documents."
            )

        if not ids:
            start_idx = max(self.store.keys(), default=0)
            ids = [str(x) for x in (range(start_idx, start_idx + len(documents)))]

        for _id, document in zip(ids, documents):
            if _id in self.store:
                raise ValueError(
                    f"Document with uid {_id} already exists in the store."
                )
            self.store[_id] = document
        return list(ids)

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[Dict[Any, Any]]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add the given texts to the store (insert behavior)."""

        raise NotImplementedError()

    @classmethod
    def from_texts(
        cls: Type[VST],
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[Dict[Any, Any]]] = None,
        **kwargs: Any,
    ) -> VST:
        """Create a vector store from a list of texts."""
        raise NotImplementedError()

    def similarity_search(
        self, query: str, k: int = 4, **kwargs: Any
    ) -> List[Document]:
        """Find the most similar documents to the given query."""
        raise NotImplementedError()
