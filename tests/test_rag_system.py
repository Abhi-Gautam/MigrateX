"""Tests for RAG system components."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from migratex.rag import (
    RAGPipeline, RAGConfig, KnowledgeBase, CodeSnippet, 
    StyleGuide, ArchitecturalPattern, HumanFeedback,
    VectorStore, ContextBuilder
)


class TestKnowledgeBase:
    """Test knowledge base functionality."""
    
    def test_add_code_snippet(self):
        """Test adding a code snippet."""
        kb = KnowledgeBase()
        
        snippet = CodeSnippet(
            source_code="int add(int a, int b) { return a + b; }",
            target_code="fn add(a: i32, b: i32) -> i32 { a + b }",
            source_language="c",
            target_language="rust",
            description="Simple addition function"
        )
        
        snippet_id = kb.add_code_snippet(snippet)
        
        assert snippet_id == snippet.id
        assert snippet_id in kb.code_snippets
        assert kb.code_snippets[snippet_id] == snippet
    
    def test_add_style_guide(self):
        """Test adding a style guide."""
        kb = KnowledgeBase()
        
        guide = StyleGuide(
            title="Rust Naming Conventions",
            content="Use snake_case for functions and variables.",
            language="rust",
            category="naming"
        )
        
        guide_id = kb.add_style_guide(guide)
        
        assert guide_id == guide.id
        assert guide_id in kb.style_guides
        assert kb.style_guides[guide_id] == guide
    
    def test_add_human_feedback(self):
        """Test adding human feedback."""
        kb = KnowledgeBase()
        
        feedback = HumanFeedback(
            original_code="int main() { return 0; }",
            generated_translation="fn main() { 0 }",
            corrected_translation="fn main() -> i32 { 0 }",
            feedback_text="Missing return type annotation",
            rating=3,
            source_language="c",
            target_language="rust"
        )
        
        feedback_id = kb.add_human_feedback(feedback)
        
        assert feedback_id == feedback.id
        assert feedback_id in kb.human_feedback
        assert kb.human_feedback[feedback_id] == feedback
    
    def test_find_code_snippets(self):
        """Test finding code snippets by criteria."""
        kb = KnowledgeBase()
        
        # Add multiple snippets
        snippet1 = CodeSnippet(
            source_code="int add(int a, int b) { return a + b; }",
            target_code="fn add(a: i32, b: i32) -> i32 { a + b }",
            source_language="c",
            target_language="rust",
            description="Addition function"
        )
        
        snippet2 = CodeSnippet(
            source_code="int multiply(int a, int b) { return a * b; }",
            target_code="func multiply(a int, b int) int { return a * b }",
            source_language="c",
            target_language="go",
            description="Multiplication function"
        )
        
        kb.add_code_snippet(snippet1)
        kb.add_code_snippet(snippet2)
        
        # Find by language pair
        rust_snippets = kb.find_code_snippets(source_language="c", target_language="rust")
        assert len(rust_snippets) == 1
        assert rust_snippets[0] == snippet1
        
        go_snippets = kb.find_code_snippets(source_language="c", target_language="go")
        assert len(go_snippets) == 1
        assert go_snippets[0] == snippet2
    
    def test_save_and_load(self):
        """Test saving and loading knowledge base."""
        kb = KnowledgeBase()
        
        # Add some data
        snippet = CodeSnippet(
            source_code="int test() { return 1; }",
            target_code="fn test() -> i32 { 1 }",
            source_language="c",
            target_language="rust",
            description="Test function"
        )
        kb.add_code_snippet(snippet)
        
        guide = StyleGuide(
            title="Test Style",
            content="Test content",
            category="test"
        )
        kb.add_style_guide(guide)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            kb.save(temp_path)
            
            # Load into new knowledge base
            new_kb = KnowledgeBase()
            new_kb.load(temp_path)
            
            # Verify data was loaded correctly
            assert len(new_kb.code_snippets) == 1
            assert len(new_kb.style_guides) == 1
            
            loaded_snippet = list(new_kb.code_snippets.values())[0]
            assert loaded_snippet.source_code == snippet.source_code
            assert loaded_snippet.target_code == snippet.target_code
            
            loaded_guide = list(new_kb.style_guides.values())[0]
            assert loaded_guide.title == guide.title
            assert loaded_guide.content == guide.content
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_get_statistics(self):
        """Test getting knowledge base statistics."""
        kb = KnowledgeBase()
        
        # Add some data
        kb.add_code_snippet(CodeSnippet(
            source_code="test1", target_code="test1",
            source_language="c", target_language="rust",
            description="Test 1"
        ))
        
        kb.add_code_snippet(CodeSnippet(
            source_code="test2", target_code="test2",
            source_language="c", target_language="go",
            description="Test 2"
        ))
        
        kb.add_style_guide(StyleGuide(
            title="Rust Guide", content="Content",
            language="rust", category="style"
        ))
        
        kb.add_human_feedback(HumanFeedback(
            original_code="test", generated_translation="test",
            rating=5, source_language="c", target_language="rust"
        ))
        
        stats = kb.get_statistics()
        
        assert stats["code_snippets"]["total"] == 2
        assert stats["code_snippets"]["by_language_pair"]["c->rust"] == 1
        assert stats["code_snippets"]["by_language_pair"]["c->go"] == 1
        assert stats["style_guides"]["total"] == 1
        assert stats["human_feedback"]["total"] == 1
        assert stats["human_feedback"]["positive"] == 1


class TestContextBuilder:
    """Test context builder functionality."""
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        builder = ContextBuilder()
        
        text = "This is a test string with some code\nand multiple lines"
        tokens = builder._estimate_tokens(text)
        
        # Should be roughly text length / 4 + newlines * 2
        expected = len(text) // 4 + text.count('\n') * 2
        assert tokens == expected
    
    def test_extract_key_points(self):
        """Test extracting key points from text.""" 
        builder = ContextBuilder()
        
        content = """
        # Style Guide
        - Use snake_case for variables
        - Use CamelCase for types
        * Avoid global variables
        1. Functions should be small
        2. Write clear comments
        """
        
        key_points = builder._extract_key_points(content, max_points=3)
        points = key_points.split('\n')
        
        # Should extract first 3 bullet/numbered points
        assert len([p for p in points if p.strip()]) <= 3
        assert any("snake_case" in point for point in points)


@pytest.mark.integration
class TestRAGPipeline:
    """Integration tests for RAG pipeline."""
    
    @patch('migratex.rag.rag_pipeline.genai')
    @patch('migratex.rag.rag_pipeline.GoogleGenerativeAIEmbeddings')
    def test_rag_pipeline_initialization(self, mock_embeddings, mock_genai):
        """Test RAG pipeline initialization."""
        # Mock the API key check
        mock_genai.configure = Mock()
        
        # Mock embeddings
        mock_embeddings_instance = Mock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        config = RAGConfig(
            embedding_model="test-model",
            similarity_threshold=0.8,
            max_context_tokens=4000
        )
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            pipeline = RAGPipeline(config=config)
            
            assert pipeline.config.embedding_model == "test-model"
            assert pipeline.config.similarity_threshold == 0.8
            assert pipeline.config.max_context_tokens == 4000
            assert pipeline.embeddings is not None
            assert pipeline.vector_store is not None
            assert pipeline.context_builder is not None
            assert pipeline.knowledge_base is not None
    
    @patch('migratex.rag.rag_pipeline.genai')
    @patch('migratex.rag.rag_pipeline.GoogleGenerativeAIEmbeddings')
    def test_add_code_snippet(self, mock_embeddings, mock_genai):
        """Test adding code snippet to RAG pipeline."""
        # Setup mocks
        mock_genai.configure = Mock()
        mock_embeddings_instance = Mock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            pipeline = RAGPipeline()
            
            # Mock vector store add_documents method
            pipeline.vector_store.add_documents = Mock(return_value=["doc_id_1"])
            
            snippet_id = pipeline.add_code_snippet(
                source_code="int add(int a, int b) { return a + b; }",
                target_code="fn add(a: i32, b: i32) -> i32 { a + b }",
                source_language="c",
                target_language="rust",
                description="Addition function"
            )
            
            assert snippet_id is not None
            assert snippet_id in pipeline.knowledge_base.code_snippets
            
            # Verify vector store was called
            pipeline.vector_store.add_documents.assert_called_once()
    
    @patch('migratex.rag.rag_pipeline.genai')
    @patch('migratex.rag.rag_pipeline.GoogleGenerativeAIEmbeddings')
    def test_get_statistics(self, mock_embeddings, mock_genai):
        """Test getting pipeline statistics."""
        # Setup mocks
        mock_genai.configure = Mock()
        mock_embeddings_instance = Mock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            pipeline = RAGPipeline()
            
            # Mock vector store statistics
            pipeline.vector_store.get_statistics = Mock(return_value={
                "total_documents": 5,
                "embedding_dimension": 768
            })
            
            stats = pipeline.get_statistics()
            
            assert "knowledge_base" in stats
            assert "vector_store" in stats
            assert "config" in stats
            assert stats["vector_store"]["total_documents"] == 5
            assert stats["config"]["embedding_model"] == "models/embedding-001"


if __name__ == "__main__":
    pytest.main([__file__])