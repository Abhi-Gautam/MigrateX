"""Test extraction and generation functionality."""

import re
from pathlib import Path
from typing import Dict, List, Optional

import tree_sitter_c
import tree_sitter_python
from tree_sitter import Language, Parser


class TestExtractor:
    """Extracts existing tests or generates new ones for code functions."""
    
    def __init__(self):
        self.c_language = Language(tree_sitter_c.language())
        self.python_language = Language(tree_sitter_python.language())
        self.parser = Parser()
        
        # Test file patterns by language
        self.test_patterns = {
            "c": [
                r"test_.*\.c$",
                r".*_test\.c$", 
                r".*/tests/.*\.c$",
                r".*/test/.*\.c$",
                r".*/unit_tests/.*\.c$",
            ],
            "cpp": [
                r"test_.*\.(cpp|cc|cxx)$",
                r".*_test\.(cpp|cc|cxx)$",
                r".*/tests/.*\.(cpp|cc|cxx)$",
                r".*/test/.*\.(cpp|cc|cxx)$",
            ],
            "python": [
                r"test_.*\.py$",
                r".*_test\.py$",
                r".*/tests/.*\.py$",
                r".*/test/.*\.py$",
            ],
            "java": [
                r".*Test\.java$",
                r".*/test/.*\.java$",
                r".*/tests/.*\.java$",
            ],
        }
    
    def identify_test_files(self, project_root: Path, language: str) -> List[Path]:
        """Identify test files in a project based on naming conventions."""
        if language not in self.test_patterns:
            return []
        
        test_files = []
        patterns = self.test_patterns[language]
        
        # Get all files with the appropriate extension
        extensions = self._get_extensions_for_language(language)
        all_files = set()  # Use set to avoid duplicates
        for ext in extensions:
            all_files.update(project_root.rglob(f"*.{ext}"))
        
        # Filter files that match test patterns
        for file_path in all_files:
            file_str = str(file_path)
            for pattern in patterns:
                if re.search(pattern, file_str, re.IGNORECASE):
                    test_files.append(file_path)
                    break
        
        return test_files
    
    def extract_test_functions(self, content: str, language: str) -> List[Dict]:
        """Extract test functions from test file content."""
        if language == "c":
            return self._extract_c_test_functions(content)
        elif language == "python":
            return self._extract_python_test_functions(content)
        return []
    
    def associate_tests_with_functions(
        self, 
        source_functions: List[Dict], 
        test_functions: List[Dict]
    ) -> Dict[str, Dict]:
        """Associate test functions with their corresponding source functions."""
        associations = {}
        
        for source_func in source_functions:
            func_name = source_func["name"]
            best_match = None
            
            # Try to find a test function that matches this source function
            for test_func in test_functions:
                test_name = test_func["name"]
                
                # Enhanced heuristic: test function contains source function name
                # Handle cases like "parse_input" -> "test_parse_simple_input"
                if (func_name.lower() in test_name.lower() or 
                    any(part.lower() in test_name.lower() for part in func_name.split('_'))):
                    if best_match is None or len(test_name) < len(best_match["name"]):
                        best_match = test_func
            
            if best_match:
                associations[func_name] = {
                    "source_function": source_func,
                    "test_name": best_match["name"],
                    "test_file": best_match["file"],
                }
        
        return associations
    
    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for a given language."""
        extension_map = {
            "c": ["c", "h"],
            "cpp": ["cpp", "cc", "cxx", "hpp", "hxx"],
            "python": ["py"],
            "java": ["java"],
        }
        return extension_map.get(language, [])
    
    def _extract_c_test_functions(self, content: str) -> List[Dict]:
        """Extract test functions from C code using tree-sitter."""
        self.parser.language = self.c_language
        tree = self.parser.parse(content.encode())
        
        test_functions = []
        
        def traverse_node(node):
            if node.type == "function_definition":
                # Get function name
                for child in node.children:
                    if child.type == "function_declarator":
                        for grandchild in child.children:
                            if grandchild.type == "identifier":
                                func_name = content[grandchild.start_byte:grandchild.end_byte]
                                # Check if it's a test function (starts with "test_")
                                if func_name.startswith("test_"):
                                    test_functions.append({
                                        "name": func_name,
                                        "content": content[node.start_byte:node.end_byte],
                                        "start_line": node.start_point[0] + 1,
                                        "end_line": node.end_point[0] + 1,
                                    })
                                break
                        break
            
            # Continue traversing children
            for child in node.children:
                traverse_node(child)
        
        traverse_node(tree.root_node)
        return test_functions
    
    def _extract_python_test_functions(self, content: str) -> List[Dict]:
        """Extract test functions from Python code using tree-sitter."""
        self.parser.language = self.python_language
        tree = self.parser.parse(content.encode())
        
        test_functions = []
        
        def traverse_node(node):
            if node.type == "function_definition":
                # Get function name
                for child in node.children:
                    if child.type == "identifier":
                        func_name = content[child.start_byte:child.end_byte]
                        # Check if it's a test function (starts with "test_")
                        if func_name.startswith("test_"):
                            test_functions.append({
                                "name": func_name,
                                "content": content[node.start_byte:node.end_byte],
                                "start_line": node.start_point[0] + 1,
                                "end_line": node.end_point[0] + 1,
                            })
                        break
            
            # Continue traversing children
            for child in node.children:
                traverse_node(child)
        
        traverse_node(tree.root_node)
        return test_functions