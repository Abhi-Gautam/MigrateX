"""RAG (Retrieval-Augmented Generation) pipeline for MigrateX code translation."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import google.generativeai as genai
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .context_builder import ContextBuilder
from .knowledge_models import (
    ArchitecturalPattern,
    CodeSnippet,
    HumanFeedback,
    KnowledgeBase,
    StyleGuide,
)
from .vector_store import VectorStore


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""
    embedding_model: str = "models/embedding-001"
    similarity_threshold: float = 0.7
    max_context_tokens: int = 8000
    max_retrieved_docs: int = 10
    knowledge_base_path: str | None = None
    cache_embeddings: bool = True


class RAGPipeline:
    """
    Main RAG pipeline for intelligent code translation context retrieval.
    
    Provides semantic search across multiple knowledge types:
    - Code snippets (source/target pairs)
    - Style guides (organizational standards)
    - Architectural patterns (design guidelines)
    - Human feedback (corrections and ratings)
    """

    def __init__(self, config: RAGConfig = None, api_key: str | None = None):
        self.config = config or RAGConfig()

        # Initialize Google AI
        if api_key:
            genai.configure(api_key=api_key)
        elif os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        else:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY environment variable or pass api_key parameter.")

        # Initialize components
        self.embeddings = GoogleGenerativeAIEmbeddings(model=self.config.embedding_model)
        self.vector_store = VectorStore(embeddings=self.embeddings)
        self.context_builder = ContextBuilder(config=self.config)
        self.knowledge_base = KnowledgeBase()

        # Load existing knowledge base if path provided
        if self.config.knowledge_base_path:
            self.load_knowledge_base(self.config.knowledge_base_path)

    def add_code_snippet(
        self,
        source_code: str,
        target_code: str,
        source_language: str,
        target_language: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Add a code translation example to the knowledge base."""
        snippet = CodeSnippet(
            source_code=source_code,
            target_code=target_code,
            source_language=source_language,
            target_language=target_language,
            description=description or f"{source_language} to {target_language} translation",
            metadata=metadata or {}
        )

        # Add to knowledge base
        snippet_id = self.knowledge_base.add_code_snippet(snippet)

        # Create document for vector storage
        doc_content = f"Source ({source_language}):\n{source_code}\n\nTarget ({target_language}):\n{target_code}"
        if description:
            doc_content = f"Description: {description}\n\n{doc_content}"

        document = Document(
            page_content=doc_content,
            metadata={
                "type": "code_snippet",
                "id": snippet_id,
                "source_language": source_language,
                "target_language": target_language,
                "description": description,
                **(metadata or {})
            }
        )

        # Add to vector store
        self.vector_store.add_documents([document])

        return snippet_id

    def add_style_guide(
        self,
        title: str,
        content: str,
        language: str | None = None,
        category: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Add a style guide or coding standard to the knowledge base."""
        guide = StyleGuide(
            title=title,
            content=content,
            language=language,
            category=category or "general",
            metadata=metadata or {}
        )

        # Add to knowledge base
        guide_id = self.knowledge_base.add_style_guide(guide)

        # Create document for vector storage
        doc_content = f"Style Guide: {title}\n\n{content}"

        document = Document(
            page_content=doc_content,
            metadata={
                "type": "style_guide",
                "id": guide_id,
                "title": title,
                "language": language,
                "category": category,
                **(metadata or {})
            }
        )

        # Add to vector store
        self.vector_store.add_documents([document])

        return guide_id

    def add_architectural_pattern(
        self,
        name: str,
        description: str,
        example_code: str | None = None,
        language: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Add an architectural pattern or design guideline."""
        pattern = ArchitecturalPattern(
            name=name,
            description=description,
            example_code=example_code,
            language=language,
            metadata=metadata or {}
        )

        # Add to knowledge base
        pattern_id = self.knowledge_base.add_architectural_pattern(pattern)

        # Create document for vector storage
        doc_content = f"Pattern: {name}\n\n{description}"
        if example_code:
            doc_content += f"\n\nExample:\n{example_code}"

        document = Document(
            page_content=doc_content,
            metadata={
                "type": "architectural_pattern",
                "id": pattern_id,
                "name": name,
                "language": language,
                **(metadata or {})
            }
        )

        # Add to vector store
        self.vector_store.add_documents([document])

        return pattern_id

    def add_human_feedback(
        self,
        original_code: str,
        generated_translation: str,
        corrected_translation: str | None = None,
        feedback_text: str | None = None,
        rating: int | None = None,
        source_language: str = "unknown",
        target_language: str = "unknown",
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Add human feedback about a translation."""
        feedback = HumanFeedback(
            original_code=original_code,
            generated_translation=generated_translation,
            corrected_translation=corrected_translation,
            feedback_text=feedback_text,
            rating=rating,
            source_language=source_language,
            target_language=target_language,
            metadata=metadata or {}
        )

        # Add to knowledge base
        feedback_id = self.knowledge_base.add_human_feedback(feedback)

        # Create document for vector storage
        doc_content = f"Original ({source_language}):\n{original_code}\n\n"
        doc_content += f"Generated Translation ({target_language}):\n{generated_translation}\n\n"

        if corrected_translation:
            doc_content += f"Corrected Translation:\n{corrected_translation}\n\n"

        if feedback_text:
            doc_content += f"Human Feedback: {feedback_text}"

        document = Document(
            page_content=doc_content,
            metadata={
                "type": "human_feedback",
                "id": feedback_id,
                "source_language": source_language,
                "target_language": target_language,
                "rating": rating,
                "has_correction": corrected_translation is not None,
                **(metadata or {})
            }
        )

        # Add to vector store
        self.vector_store.add_documents([document])

        return feedback_id

    def retrieve_context(
        self,
        query_code: str,
        source_language: str,
        target_language: str,
        context_type: str | None = None,
        max_results: int | None = None
    ) -> tuple[list[Document], dict[str, Any]]:
        """
        Retrieve relevant context for code translation.
        
        Returns:
            Tuple of (retrieved_documents, context_metadata)
        """
        max_results = max_results or self.config.max_retrieved_docs

        # Build search query
        search_query = f"Translate {source_language} to {target_language}:\n{query_code}"

        # Prepare search filters
        search_filters = {
            "source_language": source_language,
            "target_language": target_language
        }

        if context_type:
            search_filters["type"] = context_type

        # Perform semantic search
        retrieved_docs = self.vector_store.similarity_search(
            query=search_query,
            k=max_results,
            filter=search_filters,
            score_threshold=self.config.similarity_threshold
        )

        # Build context metadata
        context_metadata = {
            "query_code": query_code,
            "source_language": source_language,
            "target_language": target_language,
            "retrieved_count": len(retrieved_docs),
            "doc_types": list(set(doc.metadata.get("type", "unknown") for doc in retrieved_docs)),
            "avg_similarity": sum(doc.metadata.get("similarity_score", 0) for doc in retrieved_docs) / max(len(retrieved_docs), 1)
        }

        return retrieved_docs, context_metadata

    def build_translation_context(
        self,
        query_code: str,
        source_language: str,
        target_language: str,
        include_examples: bool = True,
        include_style_guides: bool = True,
        include_patterns: bool = True,
        include_feedback: bool = True
    ) -> str:
        """
        Build comprehensive translation context for LLM prompting.
        
        This is the main method used by the translation engine.
        """
        context_sections = []

        # Retrieve different types of context
        context_types = []
        if include_examples:
            context_types.append("code_snippet")
        if include_style_guides:
            context_types.append("style_guide")
        if include_patterns:
            context_types.append("architectural_pattern")
        if include_feedback:
            context_types.append("human_feedback")

        all_retrieved_docs = []
        for context_type in context_types:
            docs, _ = self.retrieve_context(
                query_code=query_code,
                source_language=source_language,
                target_language=target_language,
                context_type=context_type,
                max_results=3  # Limit per type
            )
            all_retrieved_docs.extend(docs)

        # Build context using ContextBuilder
        translation_context = self.context_builder.build_context(
            retrieved_docs=all_retrieved_docs,
            query_code=query_code,
            source_language=source_language,
            target_language=target_language
        )

        return translation_context

    def save_knowledge_base(self, path: str) -> None:
        """Save the knowledge base to disk."""
        kb_path = Path(path)
        kb_path.mkdir(parents=True, exist_ok=True)

        # Save knowledge base data
        self.knowledge_base.save(kb_path / "knowledge_base.json")

        # Save vector store
        self.vector_store.save(str(kb_path / "vector_store"))

    def load_knowledge_base(self, path: str) -> None:
        """Load knowledge base from disk."""
        kb_path = Path(path)

        if not kb_path.exists():
            print(f"Knowledge base path does not exist: {path}")
            return

        # Load knowledge base data
        if (kb_path / "knowledge_base.json").exists():
            self.knowledge_base.load(kb_path / "knowledge_base.json")

        # Load vector store
        if (kb_path / "vector_store").exists():
            self.vector_store.load(str(kb_path / "vector_store"))

    def get_statistics(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        kb_stats = self.knowledge_base.get_statistics()
        vector_stats = self.vector_store.get_statistics()

        return {
            "knowledge_base": kb_stats,
            "vector_store": vector_stats,
            "config": {
                "embedding_model": self.config.embedding_model,
                "similarity_threshold": self.config.similarity_threshold,
                "max_context_tokens": self.config.max_context_tokens,
                "max_retrieved_docs": self.config.max_retrieved_docs
            }
        }
