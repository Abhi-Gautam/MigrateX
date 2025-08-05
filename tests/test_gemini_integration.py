"""Integration tests using real Gemini API."""

import os
import pytest
from dotenv import load_dotenv

from migratex.analysis.test_generator import TestGenerator

# Load environment variables
load_dotenv()


class TestGeminiIntegration:
    """Real API integration tests."""
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_generate_real_c_test(self):
        """Test actual test generation for a C function."""
        generator = TestGenerator()
        
        source_function = {
            "name": "add_numbers",
            "content": "int add_numbers(int a, int b) { return a + b; }",
            "language": "c",
            "file": "math.c"
        }
        
        result = generator.generate_test(source_function)
        
        assert result is not None
        assert "test_add_numbers" in result["test_name"]
        assert "assert" in result["test_content"]
        assert result["language"] == "c"
        print(f"Generated test:\n{result['test_content']}")
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_generate_real_python_test(self):
        """Test actual test generation for a Python function."""
        generator = TestGenerator()
        
        source_function = {
            "name": "factorial",
            "content": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            "language": "python",
            "file": "math.py"
        }
        
        result = generator.generate_test(source_function)
        
        assert result is not None
        assert "test_factorial" in result["test_name"]
        assert "assert" in result["test_content"]
        assert result["language"] == "python"
        print(f"Generated test:\n{result['test_content']}")
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_batch_generation(self):
        """Test batch generation with real API."""
        generator = TestGenerator()
        
        functions = [
            {
                "name": "multiply",
                "content": "int multiply(int a, int b) { return a * b; }",
                "language": "c",
                "file": "math.c"
            },
            {
                "name": "divide",
                "content": "double divide(double a, double b) { if (b != 0) return a / b; return 0; }",
                "language": "c", 
                "file": "math.c"
            }
        ]
        
        results = generator.generate_tests_batch(functions)
        
        assert len(results) == 2
        assert all(result is not None for result in results)
        
        for result in results:
            print(f"Generated test for {result['source_function']}:\n{result['test_content']}\n")