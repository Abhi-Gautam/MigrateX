"""Tests for AI-powered test generation functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from migratex.analysis.test_generator import TestGenerator


class TestTestGeneratorFunctionality:
    """Test cases for TestGenerator functionality."""
    
    def test_generate_test_for_c_function(self):
        """Test generation of test for a C function using Gemini API."""
        generator = TestGenerator()
        
        source_function = {
            "name": "add",
            "content": "int add(int a, int b) { return a + b; }",
            "language": "c",
            "file": "math.c"
        }
        
        expected_test = '''
        #include <assert.h>
        #include "math.h"
        
        void test_add() {
            assert(add(2, 3) == 5);
            assert(add(-1, 1) == 0);
            assert(add(0, 0) == 0);
        }
        '''
        
        # Mock the Gemini API response
        with patch.object(generator, 'model') as mock_model:
            mock_response = Mock()
            mock_response.text = expected_test.strip()
            mock_model.generate_content.return_value = mock_response
            
            result = generator.generate_test(source_function)
            
            assert result is not None
            assert "test_add" in result["test_name"]
            assert "assert(add(2, 3) == 5)" in result["test_content"]
            assert result["language"] == "c"
            mock_model.generate_content.assert_called_once()
    
    def test_generate_test_for_python_function(self):
        """Test generation of test for a Python function using Gemini API."""
        generator = TestGenerator()
        
        source_function = {
            "name": "factorial",
            "content": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            "language": "python",
            "file": "math.py"
        }
        
        expected_test = '''
        import pytest
        from math import factorial
        
        def test_factorial():
            assert factorial(0) == 1
            assert factorial(1) == 1
            assert factorial(5) == 120
            assert factorial(3) == 6
        '''
        
        with patch.object(generator, 'model') as mock_model:
            mock_response = Mock()
            mock_response.text = expected_test.strip()
            mock_model.generate_content.return_value = mock_response
            
            result = generator.generate_test(source_function)
            
            assert result is not None
            assert "test_factorial" in result["test_name"]
            assert "assert factorial(5) == 120" in result["test_content"]
            assert result["language"] == "python"
    
    def test_generate_multiple_tests_batch(self):
        """Test generation of multiple tests in batch."""
        generator = TestGenerator()
        
        source_functions = [
            {
                "name": "add",
                "content": "int add(int a, int b) { return a + b; }",
                "language": "c",
                "file": "math.c"
            },
            {
                "name": "subtract", 
                "content": "int subtract(int a, int b) { return a - b; }",
                "language": "c",
                "file": "math.c"
            }
        ]
        
        with patch.object(generator, 'model') as mock_model:
            mock_responses = [
                Mock(text="void test_add() { assert(add(2, 3) == 5); }"),
                Mock(text="void test_subtract() { assert(subtract(5, 3) == 2); }")
            ]
            mock_model.generate_content.side_effect = mock_responses
            
            results = generator.generate_tests_batch(source_functions)
            
            assert len(results) == 2
            assert results[0]["test_name"] == "test_add"
            assert results[1]["test_name"] == "test_subtract"
            assert mock_model.generate_content.call_count == 2
    
    def test_api_error_handling(self):
        """Test handling of API errors during test generation."""
        generator = TestGenerator()
        
        source_function = {
            "name": "divide",
            "content": "int divide(int a, int b) { return a / b; }",
            "language": "c",
            "file": "math.c"
        }
        
        with patch.object(generator, 'model') as mock_model:
            mock_model.generate_content.side_effect = Exception("API Error")
            
            result = generator.generate_test(source_function)
            
            assert result is None
    
    def test_prompt_construction_for_c(self):
        """Test that prompts are constructed correctly for C functions.""" 
        generator = TestGenerator()
        
        source_function = {
            "name": "max",
            "content": "int max(int a, int b) { return (a > b) ? a : b; }",
            "language": "c",
            "file": "utils.c"
        }
        
        with patch.object(generator, 'model') as mock_model:
            mock_response = Mock()
            mock_response.text = "void test_max() { assert(max(5, 3) == 5); }"
            mock_model.generate_content.return_value = mock_response
            
            generator.generate_test(source_function)
            
            # Check that the prompt was constructed correctly
            call_args = mock_model.generate_content.call_args[0][0]
            assert "C function" in call_args
            assert "max" in call_args
            assert "int max(int a, int b)" in call_args
            assert "assert" in call_args
    
    def test_prompt_construction_for_python(self):
        """Test that prompts are constructed correctly for Python functions."""
        generator = TestGenerator()
        
        source_function = {
            "name": "is_palindrome",
            "content": "def is_palindrome(s):\n    return s == s[::-1]",
            "language": "python", 
            "file": "strings.py"
        }
        
        with patch.object(generator, 'model') as mock_model:
            mock_response = Mock()
            mock_response.text = "def test_is_palindrome():\n    assert is_palindrome('racecar') == True"
            mock_model.generate_content.return_value = mock_response
            
            generator.generate_test(source_function)
            
            # Check that the prompt was constructed correctly
            call_args = mock_model.generate_content.call_args[0][0]
            assert "Python function" in call_args
            assert "is_palindrome" in call_args
            assert "def is_palindrome" in call_args
            assert "assert" in call_args