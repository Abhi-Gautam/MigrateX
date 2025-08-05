"""Vector store management for RAG pipeline using FAISS."""

import json
from pathlib import Path
from typing import Any

import numpy as np
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain_community.vectorstores import FAISS


class VectorStore:
    """
    FAISS-based vector store for semantic search in RAG pipeline.
    
    Provides efficient similarity search with metadata filtering
    and persistence capabilities.
    """

    def __init__(self, embeddings: Embeddings, index_name: str = "migratex_knowledge"):
        self.embeddings = embeddings
        self.index_name = index_name
        self.vector_store: FAISS | None = None
        self.document_metadata: dict[str, dict[str, Any]] = {}

    def add_documents(self, documents: list[Document]) -> list[str]:
        """Add documents to the vector store."""
        if not documents:
            return []

        if self.vector_store is None:
            # Create new vector store
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            # Add to existing vector store
            self.vector_store.add_documents(documents)

        # Store document metadata
        doc_ids = []
        for i, doc in enumerate(documents):
            # Generate a document ID if not present
            doc_id = doc.metadata.get("id", f"doc_{len(self.document_metadata) + i}")
            doc.metadata["doc_id"] = doc_id
            self.document_metadata[doc_id] = doc.metadata.copy()
            doc_ids.append(doc_id)

        return doc_ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
        score_threshold: float | None = None
    ) -> list[Document]:
        """
        Perform similarity search with optional filtering.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter: Metadata filter criteria
            score_threshold: Minimum similarity score threshold
        
        Returns:
            List of relevant documents with similarity scores in metadata
        """
        if self.vector_store is None:
            return []

        # Perform similarity search with scores
        docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k*2)  # Get more to allow filtering

        # Apply score threshold
        if score_threshold is not None:
            docs_with_scores = [
                (doc, score) for doc, score in docs_with_scores
                if score >= score_threshold
            ]

        # Apply metadata filters
        if filter:
            filtered_docs = []
            for doc, score in docs_with_scores:
                if self._matches_filter(doc.metadata, filter):
                    filtered_docs.append((doc, score))
            docs_with_scores = filtered_docs

        # Limit results and add scores to metadata
        results = []
        for doc, score in docs_with_scores[:k]:
            doc.metadata["similarity_score"] = float(score)
            results.append(doc)

        return results

    def similarity_search_by_vector(
        self,
        embedding: list[float],
        k: int = 5,
        filter: dict[str, Any] | None = None
    ) -> list[Document]:
        """Search by pre-computed embedding vector."""
        if self.vector_store is None:
            return []

        # Convert to numpy array
        query_embedding = np.array(embedding, dtype=np.float32)

        # Perform search
        docs_with_scores = self.vector_store.similarity_search_by_vector(query_embedding, k=k*2)

        # Apply filters (similar to text search)
        if filter:
            filtered_docs = []
            for doc in docs_with_scores:
                if self._matches_filter(doc.metadata, filter):
                    filtered_docs.append(doc)
            docs_with_scores = filtered_docs

        return docs_with_scores[:k]

    def get_relevant_documents(
        self,
        query_code: str,
        source_language: str,
        target_language: str,
        document_types: list[str] | None = None,
        k: int = 5
    ) -> list[Document]:
        """
        Get documents relevant to a specific translation task.
        
        Optimized for code translation scenarios.
        """
        # Build comprehensive search query
        search_query = f"""
        Translate from {source_language} to {target_language}:
        
        {query_code}
        """

        # Build filter criteria
        filter_criteria = {
            "source_language": source_language,
            "target_language": target_language
        }

        if document_types:
            # For multiple types, we'll search each type separately and combine
            all_results = []
            for doc_type in document_types:
                type_filter = filter_criteria.copy()
                type_filter["type"] = doc_type

                results = self.similarity_search(
                    query=search_query,
                    k=max(1, k // len(document_types)),  # Distribute k across types
                    filter=type_filter
                )
                all_results.extend(results)

            # Sort by similarity score and limit
            all_results.sort(key=lambda x: x.metadata.get("similarity_score", 0), reverse=True)
            return all_results[:k]
        else:
            return self.similarity_search(
                query=search_query,
                k=k,
                filter=filter_criteria
            )

    def _matches_filter(self, metadata: dict[str, Any], filter_criteria: dict[str, Any]) -> bool:
        """Check if document metadata matches filter criteria."""
        for key, value in filter_criteria.items():
            if key not in metadata:
                return False

            # Handle different comparison types
            doc_value = metadata[key]

            if isinstance(value, list):
                # Value must be in the list
                if doc_value not in value:
                    return False
            elif isinstance(value, dict):
                # Advanced filtering (e.g., range queries)
                if "min" in value and doc_value < value["min"]:
                    return False
                if "max" in value and doc_value > value["max"]:
                    return False
            else:
                # Exact match
                if doc_value != value:
                    return False

        return True

    def delete_documents(self, doc_ids: list[str]) -> int:
        """Delete documents by their IDs."""
        if self.vector_store is None:
            return 0

        # Note: FAISS doesn't support direct deletion by ID
        # This is a limitation we'll document
        deleted_count = 0
        for doc_id in doc_ids:
            if doc_id in self.document_metadata:
                del self.document_metadata[doc_id]
                deleted_count += 1

        # For now, we'll mark documents as deleted in metadata
        # A full rebuild would be needed to actually remove them from the index
        return deleted_count

    def get_document_count(self) -> int:
        """Get total number of documents in the store."""
        if self.vector_store is None:
            return 0
        return self.vector_store.index.ntotal

    def get_statistics(self) -> dict[str, Any]:
        """Get vector store statistics."""
        if self.vector_store is None:
            return {
                "total_documents": 0,
                "embedding_dimension": 0,
                "document_types": {},
                "languages": {}
            }

        # Analyze document metadata
        doc_types = {}
        languages = {}
        source_languages = {}
        target_languages = {}

        for metadata in self.document_metadata.values():
            # Document types
            doc_type = metadata.get("type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

            # Languages
            if "language" in metadata:
                lang = metadata["language"]
                languages[lang] = languages.get(lang, 0) + 1

            if "source_language" in metadata:
                lang = metadata["source_language"]
                source_languages[lang] = source_languages.get(lang, 0) + 1

            if "target_language" in metadata:
                lang = metadata["target_language"]
                target_languages[lang] = target_languages.get(lang, 0) + 1

        return {
            "total_documents": self.get_document_count(),
            "embedding_dimension": self.vector_store.index.d if self.vector_store else 0,
            "document_types": doc_types,
            "languages": languages,
            "source_languages": source_languages,
            "target_languages": target_languages,
            "metadata_documents": len(self.document_metadata)
        }

    def save(self, directory_path: str) -> None:
        """Save vector store to disk."""
        dir_path = Path(directory_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        if self.vector_store is not None:
            # Save FAISS index
            self.vector_store.save_local(str(dir_path))

        # Save document metadata
        metadata_path = dir_path / "document_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.document_metadata, f, indent=2, ensure_ascii=False)

    def load(self, directory_path: str) -> bool:
        """
        Load vector store from disk.
        
        Returns:
            True if successful, False otherwise
        """
        dir_path = Path(directory_path)

        if not dir_path.exists():
            return False

        try:
            # Load FAISS index
            if (dir_path / "index.faiss").exists():
                self.vector_store = FAISS.load_local(str(dir_path), self.embeddings)

            # Load document metadata
            metadata_path = dir_path / "document_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, encoding="utf-8") as f:
                    self.document_metadata = json.load(f)

            return True

        except Exception as e:
            print(f"Error loading vector store: {e}")
            return False

    def rebuild_index(self, batch_size: int = 100) -> None:
        """
        Rebuild the FAISS index from scratch.
        
        Useful for removing deleted documents or optimizing the index.
        """
        if self.vector_store is None:
            return

        # Get all documents
        all_docs = []

        # This is a simplified rebuild - in practice, we'd need to
        # reconstruct documents from stored metadata and content
        print("Index rebuild not fully implemented - requires document content storage")

    def clear(self) -> None:
        """Clear all data from the vector store."""
        self.vector_store = None
        self.document_metadata.clear()
