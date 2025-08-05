"""Tests for metadata integration with test extraction and generation."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from migratex.analysis.test_extractor import TestExtractor
from migratex.analysis.test_generator import TestGenerator
from migratex.directory_mapping.metadata_manager import MetadataManager


class TestMetadataIntegrationFunctionality:
    """Test cases for metadata integration functionality."""
    
    def test_create_metadata_entry_for_extracted_function(self):
        """Test creation of metadata entry when function is extracted."""
        metadata_manager = MetadataManager()
        
        extracted_function = {
            "name": "calculate_sum",
            "content": "int calculate_sum(int a, int b) { return a + b; }",
            "language": "c",
            "file": "/project/src/math.c",
            "start_line": 10,
            "end_line": 12,
            "dependencies": ["stdio.h"]
        }
        
        metadata_id = metadata_manager.create_function_metadata(extracted_function)
        
        assert metadata_id is not None
        assert isinstance(metadata_id, str)
        
        # Verify metadata was stored
        metadata = metadata_manager.get_metadata(metadata_id)
        assert metadata["source_function"]["name"] == "calculate_sum"
        assert metadata["source_function"]["language"] == "c"
        assert metadata["status"] == "extracted"
    
    def test_associate_existing_test_with_function_metadata(self):
        """Test association of existing tests with function metadata."""
        metadata_manager = MetadataManager()
        
        # Create function metadata
        function_metadata = {
            "name": "multiply",
            "content": "int multiply(int a, int b) { return a * b; }",
            "language": "c",
            "file": "/project/src/math.c"
        }
        
        func_id = metadata_manager.create_function_metadata(function_metadata)
        
        # Simulate found existing test
        existing_test = {
            "name": "test_multiply",
            "content": "void test_multiply() { assert(multiply(3, 4) == 12); }",
            "file": "/project/tests/test_math.c",
            "language": "c"
        }
        
        # Associate test with function
        metadata_manager.associate_existing_test(func_id, existing_test)
        
        # Verify association
        metadata = metadata_manager.get_metadata(func_id)
        assert metadata["test_info"]["test_name"] == "test_multiply"
        assert metadata["test_info"]["test_type"] == "existing" 
        assert metadata["test_info"]["test_file"] == "/project/tests/test_math.c"
        assert metadata["status"] == "test_associated"
    
    def test_associate_generated_test_with_function_metadata(self):
        """Test association of AI-generated tests with function metadata."""
        metadata_manager = MetadataManager()
        
        # Create function metadata
        function_metadata = {
            "name": "divide",
            "content": "double divide(double a, double b) { return a / b; }",
            "language": "c",
            "file": "/project/src/math.c"
        }
        
        func_id = metadata_manager.create_function_metadata(function_metadata)
        
        # Simulate generated test
        generated_test = {
            "test_name": "test_divide",
            "test_content": "void test_divide() { assert(divide(10.0, 2.0) == 5.0); }",
            "language": "c",
            "source_function": "divide"
        }
        
        # Associate generated test
        metadata_manager.associate_generated_test(func_id, generated_test)
        
        # Verify association
        metadata = metadata_manager.get_metadata(func_id)
        assert metadata["test_info"]["test_name"] == "test_divide"
        assert metadata["test_info"]["test_type"] == "generated"
        assert "test_divide" in metadata["test_info"]["test_content"]
        assert metadata["status"] == "test_generated"
    
    def test_complete_test_workflow_integration(self):
        """Test complete workflow: extract -> generate test -> associate metadata."""
        extractor = TestExtractor()
        generator = TestGenerator(api_key="test_key")
        metadata_manager = MetadataManager()
        
        # Step 1: Extract function (simulated)
        extracted_function = {
            "name": "fibonacci",
            "content": "int fibonacci(int n) { if (n <= 1) return n; return fibonacci(n-1) + fibonacci(n-2); }",
            "language": "c",
            "file": "/project/src/algorithms.c",
            "dependencies": []
        }
        
        # Step 2: Create metadata entry
        func_id = metadata_manager.create_function_metadata(extracted_function)
        
        # Step 3: Check for existing tests (none found)
        existing_tests = []  # Simulated empty result
        
        # Step 4: Generate test using AI
        with patch.object(generator, 'model') as mock_model:
            mock_response = Mock()
            mock_response.text = """void test_fibonacci() {
    assert(fibonacci(0) == 0);
    assert(fibonacci(1) == 1);
    assert(fibonacci(5) == 5);
    assert(fibonacci(8) == 21);
}"""
            mock_model.generate_content.return_value = mock_response
            
            generated_test = generator.generate_test(extracted_function)
        
        # Step 5: Associate generated test with metadata
        metadata_manager.associate_generated_test(func_id, generated_test)
        
        # Step 6: Verify complete workflow
        final_metadata = metadata_manager.get_metadata(func_id)
        
        assert final_metadata["source_function"]["name"] == "fibonacci"
        assert final_metadata["test_info"]["test_name"] == "test_fibonacci"
        assert final_metadata["test_info"]["test_type"] == "generated"
        assert final_metadata["status"] == "test_generated"
        assert "fibonacci(0) == 0" in final_metadata["test_info"]["test_content"]
    
    def test_metadata_retrieval_by_function_name(self):
        """Test retrieval of metadata by function name."""
        metadata_manager = MetadataManager()
        
        # Create multiple function metadata entries
        functions = [
            {"name": "add", "language": "c", "file": "math.c"},
            {"name": "subtract", "language": "c", "file": "math.c"},
            {"name": "parse", "language": "c", "file": "parser.c"}
        ]
        
        ids = []
        for func in functions:
            func_id = metadata_manager.create_function_metadata(func)
            ids.append(func_id)
        
        # Test retrieval by function name
        add_metadata = metadata_manager.get_metadata_by_function_name("add")
        assert add_metadata is not None
        assert add_metadata["source_function"]["name"] == "add"
        
        # Test non-existent function
        nonexistent = metadata_manager.get_metadata_by_function_name("nonexistent")
        assert nonexistent is None
    
    def test_metadata_status_tracking(self):
        """Test status tracking throughout the test association process."""
        metadata_manager = MetadataManager()
        
        function_metadata = {
            "name": "sort_array",
            "content": "void sort_array(int arr[], int n) { /* implementation */ }",
            "language": "c",
            "file": "/project/src/sort.c"
        }
        
        func_id = metadata_manager.create_function_metadata(function_metadata)
        
        # Initial status should be 'extracted'
        metadata = metadata_manager.get_metadata(func_id)
        assert metadata["status"] == "extracted"
        
        # Update status when test generation starts
        metadata_manager.update_status(func_id, "generating_test")
        metadata = metadata_manager.get_metadata(func_id)
        assert metadata["status"] == "generating_test"
        
        # Update status when test is generated
        generated_test = {
            "test_name": "test_sort_array",
            "test_content": "void test_sort_array() { /* test implementation */ }",
            "language": "c"
        }
        
        metadata_manager.associate_generated_test(func_id, generated_test)
        metadata = metadata_manager.get_metadata(func_id)
        assert metadata["status"] == "test_generated"