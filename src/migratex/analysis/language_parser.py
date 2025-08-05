"""Tree-sitter based language parsing for MigrateX."""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import logging

try:
    import tree_sitter
    import tree_sitter_c
    import tree_sitter_cpp
    import tree_sitter_java
    import tree_sitter_python
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    tree_sitter = None
    tree_sitter_c = None
    tree_sitter_cpp = None
    tree_sitter_java = None
    tree_sitter_python = None

logger = logging.getLogger(__name__)

@dataclass
class AstNode:
    """Represents a node in the Abstract Syntax Tree."""
    kind: str
    start_byte: int
    end_byte: int
    start_row: int
    start_column: int
    end_row: int
    end_column: int
    text: str
    children: List['AstNode']

@dataclass
class ExtractedModule:
    """Represents an extracted code module (function, class, etc.)."""
    id: str
    name: str
    kind: str  # 'function', 'class', 'method', etc.
    source_code: str
    start_byte: int
    end_byte: int
    dependencies: List[str]
    exports: List[str]
    file_path: Optional[str] = None

class LanguageParser:
    """Tree-sitter based language parser for code analysis."""
    
    SUPPORTED_LANGUAGES = {
        "c": "c",
        "cpp": "cpp", 
        "c++": "cpp",
        "java": "java",
        "python": "python",
        "javascript": "javascript",
        "typescript": "typescript",
        "go": "go",
        "c#": "c_sharp",
        "csharp": "c_sharp",
    }
    
    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter libraries not available. "
                "Install with: pip install tree-sitter tree-sitter-languages"
            )
        self._parsers = {}
    
    def _get_parser(self, language: str) -> tree_sitter.Parser:
        """Get or create a parser for the specified language."""
        language = language.lower()
        
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        
        if language not in self._parsers:
            ts_language_name = self.SUPPORTED_LANGUAGES[language]
            
            # Get the appropriate language binding
            language_module_map = {
                "c": tree_sitter_c,
                "cpp": tree_sitter_cpp,
                "java": tree_sitter_java,
                "python": tree_sitter_python,
                "c_sharp": None,  # Not available yet
            }
            
            lang_module = language_module_map.get(ts_language_name)
            if lang_module is None:
                raise ValueError(f"Language module not available for: {ts_language_name}")
            
            ts_language_raw = lang_module.language()
            ts_language = tree_sitter.Language(ts_language_raw)
            parser = tree_sitter.Parser(ts_language)
            self._parsers[language] = parser
        
        return self._parsers[language]
    
    def parse_code(self, code: str, language: str) -> AstNode:
        """Parse source code and return AST root node."""
        parser = self._get_parser(language)
        
        code_bytes = code.encode('utf-8')
        tree = parser.parse(code_bytes)
        
        return self._convert_node_to_ast(tree.root_node, code_bytes)
    
    def parse_file(self, file_path: Path, language: Optional[str] = None) -> AstNode:
        """Parse a source file and return AST root node."""
        if language is None:
            language = self._detect_language(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        return self.parse_code(code, language)
    
    def extract_modules(self, code: str, language: str, file_path: Optional[str] = None) -> List[ExtractedModule]:
        """Extract modules (functions, classes) from source code."""
        parser = self._get_parser(language)
        code_bytes = code.encode('utf-8')
        tree = parser.parse(code_bytes)
        
        modules = []
        self._extract_modules_from_node(tree.root_node, code_bytes, language, modules, file_path)
        
        return modules
    
    def _convert_node_to_ast(self, node: tree_sitter.Node, source_bytes: bytes) -> AstNode:
        """Convert tree-sitter node to AstNode."""
        try:
            text = node.text.decode('utf-8')
        except UnicodeDecodeError:
            text = node.text.decode('utf-8', errors='replace')
        
        children = [
            self._convert_node_to_ast(child, source_bytes)
            for child in node.children
        ]
        
        return AstNode(
            kind=node.type,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            start_row=node.start_point[0],
            start_column=node.start_point[1],
            end_row=node.end_point[0],
            end_column=node.end_point[1],
            text=text,
            children=children
        )
    
    def _extract_modules_from_node(
        self, 
        node: tree_sitter.Node, 
        source_bytes: bytes, 
        language: str,
        modules: List[ExtractedModule],
        file_path: Optional[str] = None
    ):
        """Extract modules from a tree-sitter node."""
        
        # Define module types for different languages
        module_types = {
            "c": ["function_definition"],
            "cpp": ["function_definition", "class_specifier"],
            "java": ["method_declaration", "class_declaration", "constructor_declaration"],
            "python": ["function_definition", "class_definition"],
            "javascript": ["function_declaration", "class_declaration", "method_definition"],
            "typescript": ["function_declaration", "class_declaration", "method_definition"],
            "go": ["function_declaration", "type_declaration"],
            "c_sharp": ["method_declaration", "class_declaration", "constructor_declaration"]
        }
        
        lang_key = self.SUPPORTED_LANGUAGES.get(language.lower(), language.lower())
        relevant_types = module_types.get(lang_key, ["function_definition", "class_definition"])
        
        if node.type in relevant_types:
            module = self._create_module_from_node(node, source_bytes, language, file_path)
            if module:
                modules.append(module)
        
        # Recursively process children
        for child in node.children:
            self._extract_modules_from_node(child, source_bytes, language, modules, file_path)
    
    def _create_module_from_node(
        self, 
        node: tree_sitter.Node, 
        source_bytes: bytes, 
        language: str,
        file_path: Optional[str] = None
    ) -> Optional[ExtractedModule]:
        """Create an ExtractedModule from a tree-sitter node."""
        
        try:
            source_code = node.text.decode('utf-8')
        except UnicodeDecodeError:
            source_code = node.text.decode('utf-8', errors='replace')
        
        # Extract name
        name = self._extract_name_from_node(node, source_bytes)
        if not name:
            name = f"anonymous_{node.type}"
        
        # Extract dependencies (simplified - just identifiers)
        dependencies = self._extract_dependencies_from_node(node, source_bytes)
        
        # Determine module kind
        kind = self._node_type_to_module_kind(node.type)
        
        # Generate unique ID
        import uuid
        module_id = str(uuid.uuid4())
        
        return ExtractedModule(
            id=module_id,
            name=name,
            kind=kind,
            source_code=source_code,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            dependencies=list(dependencies),
            exports=[name],  # Export itself
            file_path=file_path
        )
    
    def _extract_name_from_node(self, node: tree_sitter.Node, source_bytes: bytes) -> Optional[str]:
        """Extract the name/identifier from a node."""
        
        # Look for function declarator or class name patterns
        def find_identifier_recursive(n: tree_sitter.Node, depth: int = 0) -> Optional[str]:
            # Limit recursion depth
            if depth > 3:
                return None
                
            # Direct identifier
            if n.type in ["identifier", "type_identifier"]:
                try:
                    return n.text.decode('utf-8')
                except UnicodeDecodeError:
                    return n.text.decode('utf-8', errors='replace')
            
            # For function definitions, look for function_declarator
            if n.type == "function_declarator":
                for child in n.children:
                    if child.type == "identifier":
                        try:
                            return child.text.decode('utf-8')
                        except UnicodeDecodeError:
                            return child.text.decode('utf-8', errors='replace')
            
            # For class definitions, look for the class name
            if n.type in ["class_specifier", "class_declaration"]:
                for child in n.children:
                    if child.type in ["identifier", "type_identifier"]:
                        try:
                            return child.text.decode('utf-8')
                        except UnicodeDecodeError:
                            return child.text.decode('utf-8', errors='replace')
            
            # Recursively search children
            for child in n.children:
                result = find_identifier_recursive(child, depth + 1)
                if result:
                    return result
            
            return None
        
        return find_identifier_recursive(node)
    
    def _extract_dependencies_from_node(self, node: tree_sitter.Node, source_bytes: bytes) -> Set[str]:
        """Extract dependencies (identifiers) from a node."""
        dependencies = set()
        
        def collect_identifiers(n: tree_sitter.Node):
            if n.type == "identifier":
                try:
                    identifier = n.text.decode('utf-8')
                    # Filter out common keywords and the function's own name
                    if len(identifier) > 1 and not identifier.startswith('_'):
                        dependencies.add(identifier)
                except UnicodeDecodeError:
                    pass
            
            for child in n.children:
                collect_identifiers(child)
        
        collect_identifiers(node)
        return dependencies
    
    def _node_type_to_module_kind(self, node_type: str) -> str:
        """Convert tree-sitter node type to module kind."""
        type_mapping = {
            "function_definition": "function",
            "function_declaration": "function", 
            "method_declaration": "method",
            "method_definition": "method",
            "class_definition": "class",
            "class_declaration": "class",
            "class_specifier": "class",
            "constructor_declaration": "constructor",
            "type_declaration": "type"
        }
        
        return type_mapping.get(node_type, "unknown")
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        extension_mapping = {
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cxx': 'cpp', 
            '.cc': 'cpp',
            '.hpp': 'cpp',
            '.java': 'java',
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.cs': 'c_sharp'
        }
        
        suffix = file_path.suffix.lower()
        if suffix in extension_mapping:
            return extension_mapping[suffix]
        
        raise ValueError(f"Cannot detect language for file: {file_path}")

# Factory function for easy access
def create_parser() -> LanguageParser:
    """Create a new LanguageParser instance."""
    return LanguageParser()