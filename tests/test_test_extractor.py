"""Tests for test extraction and generation functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from migratex.analysis.test_extractor import TestExtractor


class TestTestExtractorFunctionality:
    """Test cases for TestExtractor functionality."""
    
    def test_identify_test_files_in_c_project(self):
        """Test identification of test files in a C project structure."""
        # Create a mock project structure
        project_root = Path("/mock/project")
        
        extractor = TestExtractor()
        
        # Mock file system with typical C test structure
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [
                Path("/mock/project/test_main.c"),
                Path("/mock/project/tests/test_utils.c"),
                Path("/mock/project/src/main.c"),  # Not a test file
                Path("/mock/project/unit_tests/test_parser.c"),
            ]
            
            test_files = extractor.identify_test_files(project_root, "c")
            
            assert len(test_files) == 3
            assert Path("/mock/project/test_main.c") in test_files
            assert Path("/mock/project/tests/test_utils.c") in test_files
            assert Path("/mock/project/unit_tests/test_parser.c") in test_files
            assert Path("/mock/project/src/main.c") not in test_files
    
    def test_identify_test_files_in_python_project(self):
        """Test identification of test files in a Python project structure."""
        project_root = Path("/mock/python_project")
        
        extractor = TestExtractor()
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [
                Path("/mock/python_project/test_main.py"),
                Path("/mock/python_project/tests/test_utils.py"),
                Path("/mock/python_project/src/main.py"),  # Not a test file
                Path("/mock/python_project/test_suite/test_parser.py"),
            ]
            
            test_files = extractor.identify_test_files(project_root, "python")
            
            assert len(test_files) == 3
            assert Path("/mock/python_project/test_main.py") in test_files
            assert Path("/mock/python_project/tests/test_utils.py") in test_files
            assert Path("/mock/python_project/test_suite/test_parser.py") in test_files
    
    def test_extract_test_functions_from_c_file(self):
        """Test extraction of test functions from C test file."""
        test_content = '''
        #include <assert.h>
        #include "main.h"
        
        void test_add_function() {
            assert(add(2, 3) == 5);
            assert(add(-1, 1) == 0);
        }
        
        void test_multiply_function() {
            assert(multiply(2, 3) == 6);
        }
        
        void helper_function() {
            // Not a test function
        }
        '''
        
        extractor = TestExtractor()
        test_functions = extractor.extract_test_functions(test_content, "c")
        
        assert len(test_functions) == 2
        assert "test_add_function" in [func["name"] for func in test_functions]
        assert "test_multiply_function" in [func["name"] for func in test_functions]
        assert "helper_function" not in [func["name"] for func in test_functions]
    
    def test_associate_tests_with_source_functions(self):
        """Test association of test functions with source code functions."""
        extractor = TestExtractor()
        
        # Mock source functions
        source_functions = [
            {"name": "add", "file": "math.c"},
            {"name": "multiply", "file": "math.c"},
            {"name": "parse_input", "file": "parser.c"},
        ]
        
        # Mock test functions
        test_functions = [
            {"name": "test_add_function", "file": "test_math.c"},
            {"name": "test_multiply_function", "file": "test_math.c"},
            {"name": "test_parse_simple_input", "file": "test_parser.c"},
        ]
        
        associations = extractor.associate_tests_with_functions(
            source_functions, test_functions
        )
        
        assert len(associations) == 3
        assert associations["add"]["test_name"] == "test_add_function"
        assert associations["multiply"]["test_name"] == "test_multiply_function"
        assert associations["parse_input"]["test_name"] == "test_parse_simple_input"