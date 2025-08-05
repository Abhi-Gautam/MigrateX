"""Tests for Python tree-sitter based language parsing."""

import pytest
from pathlib import Path

def test_tree_sitter_import():
    """Test that tree-sitter can be imported."""
    try:
        import tree_sitter
        import tree_sitter_c
        assert tree_sitter
        assert tree_sitter_c
    except ImportError:
        pytest.fail("tree-sitter libraries not available - install with: pip install tree-sitter tree-sitter-c")

def test_parse_simple_c_code():
    """Test parsing simple C code with tree-sitter."""
    try:
        import tree_sitter
        import tree_sitter_c
        
        # Get C language parser
        c_language = tree_sitter.Language(tree_sitter_c.language())
        parser = tree_sitter.Parser(c_language)
        
        c_code = b"""
        int main() {
            return 0;
        }
        """
        
        tree = parser.parse(c_code)
        root_node = tree.root_node
        
        assert root_node.type == "translation_unit"
        assert len(root_node.children) > 0
        
    except ImportError:
        pytest.skip("tree-sitter libraries not available")

def test_extract_function_from_c_code():
    """Test extracting function information from C code."""
    try:
        import tree_sitter
        import tree_sitter_c
        
        # Get C language parser
        c_language = tree_sitter.Language(tree_sitter_c.language())
        parser = tree_sitter.Parser(c_language)
        
        c_code = b"""
        #include <stdio.h>
        
        void helper_function() {
            printf("Helper");
        }
        
        int main() {
            helper_function();
            return 0;
        }
        """
        
        tree = parser.parse(c_code)
        
        # Find function definitions
        functions = []
        
        def find_functions(node):
            if node.type == "function_definition":
                # Extract function name
                for child in node.children:
                    if child.type == "function_declarator":
                        for grandchild in child.children:
                            if grandchild.type == "identifier":
                                func_name = c_code[grandchild.start_byte:grandchild.end_byte].decode()
                                functions.append(func_name)
                                break
            
            for child in node.children:
                find_functions(child)
        
        find_functions(tree.root_node)
        
        assert "main" in functions
        assert "helper_function" in functions
        assert len(functions) == 2
        
    except ImportError:
        pytest.skip("tree-sitter libraries not available")

def test_dependency_extraction():
    """Test extracting dependencies from parsed code."""
    try:
        import tree_sitter
        import tree_sitter_c
        
        # Get C language parser
        c_language = tree_sitter.Language(tree_sitter_c.language())
        parser = tree_sitter.Parser(c_language)
        
        c_code = b"""
        int add(int a, int b) {
            return a + b;
        }
        
        int multiply(int x, int y) {
            int result = add(x, y);  // depends on add function
            return result * 2;
        }
        """
        
        tree = parser.parse(c_code)
        
        # Find function calls (simplified dependency detection)
        function_calls = []
        
        def find_calls(node):
            if node.type == "call_expression":
                func_node = node.children[0]  # function identifier
                if func_node.type == "identifier":
                    call_name = c_code[func_node.start_byte:func_node.end_byte].decode()
                    function_calls.append(call_name)
            
            for child in node.children:
                find_calls(child)
        
        find_calls(tree.root_node)
        
        assert "add" in function_calls
        
    except ImportError:
        pytest.skip("tree-sitter libraries not available")