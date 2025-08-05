"""Integration tests for the LanguageParser class."""

import pytest
from pathlib import Path
from migratex.analysis.language_parser import LanguageParser, TREE_SITTER_AVAILABLE

@pytest.mark.skipif(not TREE_SITTER_AVAILABLE, reason="tree-sitter not available")
class TestLanguageParser:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LanguageParser()
    
    def test_parse_c_code(self):
        """Test parsing C code with LanguageParser."""
        c_code = """
        #include <stdio.h>
        
        int main() {
            printf("Hello, World!\\n");
            return 0;
        }
        """
        
        ast = self.parser.parse_code(c_code, "c")
        
        assert ast.kind == "translation_unit"
        assert len(ast.children) > 0
        assert "main" in ast.text
    
    def test_extract_modules_from_c_code(self):
        """Test extracting modules from C code."""
        c_code = """
        void helper() {
            // Helper function
        }
        
        int main() {
            helper();
            return 0;
        }
        """
        
        modules = self.parser.extract_modules(c_code, "c")
        
        assert len(modules) == 2
        
        # Find modules by name
        main_module = next((m for m in modules if m.name == "main"), None)
        helper_module = next((m for m in modules if m.name == "helper"), None)
        
        assert main_module is not None
        assert helper_module is not None
        
        assert main_module.kind == "function"
        assert helper_module.kind == "function"
        
        # Check that main module has helper as dependency
        assert "helper" in main_module.dependencies
    
    def test_extract_modules_from_python_code(self):
        """Test extracting modules from Python code."""
        python_code = """
        def calculate_sum(a, b):
            return a + b
        
        class Calculator:
            def multiply(self, x, y):
                return x * y
        
        def main():
            calc = Calculator()
            result = calculate_sum(1, 2)
            product = calc.multiply(3, 4)
            print(result, product)
        """
        
        modules = self.parser.extract_modules(python_code, "python")
        
        assert len(modules) >= 3  # At least calculate_sum, Calculator, main
        
        # Find modules
        calc_sum = next((m for m in modules if m.name == "calculate_sum"), None)
        calc_class = next((m for m in modules if m.name == "Calculator"), None)
        main_func = next((m for m in modules if m.name == "main"), None)
        
        assert calc_sum is not None
        assert calc_class is not None  
        assert main_func is not None
        
        assert calc_sum.kind == "function"
        assert calc_class.kind == "class"
        assert main_func.kind == "function"
    
    def test_unsupported_language(self):
        """Test that unsupported languages raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported language"):
            self.parser.parse_code("code", "unsupported_lang")
    
    def test_language_detection(self):
        """Test automatic language detection from file extensions."""
        test_cases = [
            (Path("test.c"), "c"),
            (Path("test.cpp"), "cpp"),
            (Path("test.java"), "java"),
            (Path("test.py"), "python"),
        ]
        
        for file_path, expected_lang in test_cases:
            detected_lang = self.parser._detect_language(file_path)
            assert detected_lang == expected_lang
    
    def test_unknown_file_extension(self):
        """Test that unknown file extensions raise ValueError."""
        with pytest.raises(ValueError, match="Cannot detect language"):
            self.parser._detect_language(Path("test.unknown"))

@pytest.mark.skipif(TREE_SITTER_AVAILABLE, reason="tree-sitter is available")  
def test_tree_sitter_not_available():
    """Test that LanguageParser raises ImportError when tree-sitter not available."""
    with pytest.raises(ImportError, match="tree-sitter libraries not available"):
        LanguageParser()