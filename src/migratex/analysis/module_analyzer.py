"""Advanced module analysis with CFG and dependency graph support."""

import networkx as nx
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .language_parser import LanguageParser, ExtractedModule

logger = logging.getLogger(__name__)


@dataclass
class SemanticModule:
    """Represents a self-contained semantic module with dependency closure."""
    id: str
    name: str
    description: str
    functions: List[ExtractedModule]
    internal_dependencies: Set[str] = field(default_factory=set)
    external_dependencies: Set[str] = field(default_factory=set)
    file_path: Optional[str] = None
    module_type: str = "feature"  # "feature", "utility", "data_structure", "algorithm"
    complexity_score: float = 0.0
    
    @property
    def source_code(self) -> str:
        """Get combined source code of all functions in the module."""
        return "\n\n".join(func.source_code for func in self.functions)
    
    @property
    def function_names(self) -> List[str]:
        """Get list of function names in this module."""
        return [func.name for func in self.functions]
    
    @property
    def is_self_contained(self) -> bool:
        """Check if module is self-contained (no external dependencies within the same codebase)."""
        # For now, consider a module self-contained if it has minimal external dependencies
        # This can be enhanced with more sophisticated analysis
        return len(self.external_dependencies) <= 3


class ModuleAnalyzer:
    """Advanced module analyzer with CFG and semantic grouping capabilities."""
    
    def __init__(self):
        self.language_parser = LanguageParser()
        self.call_graph: Optional[nx.DiGraph] = None
        self.function_map: Dict[str, ExtractedModule] = {}
        
    def analyze_repository(self, repo_path: Path, language: str = "c") -> List[SemanticModule]:
        """Analyze repository and extract semantic modules."""
        
        logger.info(f"Analyzing repository: {repo_path}")
        
        # Step 1: Extract all functions from repository
        all_functions = self._extract_all_functions(repo_path, language)
        logger.info(f"Extracted {len(all_functions)} functions")
        
        if not all_functions:
            return []
        
        # Step 2: Build call graph
        self.call_graph = self._build_call_graph(all_functions)
        logger.info(f"Built call graph with {self.call_graph.number_of_nodes()} nodes and {self.call_graph.number_of_edges()} edges")
        
        # Step 3: Group functions into semantic modules
        modules = self._group_functions_into_modules(all_functions)
        logger.info(f"Grouped functions into {len(modules)} semantic modules")
        
        # Step 4: Validate and enhance modules
        validated_modules = self._validate_and_enhance_modules(modules)
        logger.info(f"Validated {len(validated_modules)} self-contained modules")
        
        return validated_modules
    
    def _extract_all_functions(self, repo_path: Path, language: str) -> List[ExtractedModule]:
        """Extract all functions from repository files."""
        
        # Find source files
        extensions = {
            "c": ["*.c", "*.h"],
            "cpp": ["*.cpp", "*.hpp", "*.cc", "*.hh"],
            "java": ["*.java"],
            "python": ["*.py"]
        }
        
        patterns = extensions.get(language, ["*.c"])
        all_functions = []
        
        for pattern in patterns:
            for file_path in repo_path.rglob(pattern):
                # Skip test files for now (but not when they contain main functionality)
                if "test" in file_path.name.lower() and file_path.name.lower() != "test.c":
                    continue
                    
                try:
                    logger.info(f"Processing file: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    functions = self.language_parser.extract_modules(content, language, str(file_path))
                    logger.info(f"Extracted {len(functions)} modules from {file_path}")
                    
                    # Filter to only include functions (not classes for now)
                    functions = [f for f in functions if f.kind == "function"]
                    logger.info(f"Filtered to {len(functions)} functions from {file_path}")
                    all_functions.extend(functions)
                    
                    # Build function map for quick lookup
                    for func in functions:
                        self.function_map[func.name] = func
                        logger.debug(f"Added function to map: {func.name}")
                        
                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue
        
        return all_functions
    
    def _build_call_graph(self, functions: List[ExtractedModule]) -> nx.DiGraph:
        """Build call graph showing function dependencies."""
        
        graph = nx.DiGraph()
        
        # Add all functions as nodes
        for func in functions:
            graph.add_node(func.name, function=func)
        
        # Add edges based on dependencies
        for func in functions:
            for dep in func.dependencies:
                # Only add edge if dependency is another function in our codebase
                if dep in self.function_map and dep != func.name:
                    graph.add_edge(func.name, dep, type="calls")
                    logger.debug(f"Added call edge: {func.name} -> {dep}")
        
        return graph
    
    def _group_functions_into_modules(self, functions: List[ExtractedModule]) -> List[SemanticModule]:
        """Group related functions into semantic modules using multiple strategies."""
        
        if not self.call_graph:
            # Fallback: each function is its own module
            return [self._create_single_function_module(func) for func in functions]
        
        modules = []
        processed_functions = set()
        
        # Strategy 1: Semantic/Prefix-based grouping - HIGHEST PRIORITY
        prefix_modules = self._group_by_function_prefixes(functions, processed_functions)
        modules.extend(prefix_modules)
        logger.info(f"Created {len(prefix_modules)} semantic/prefix modules")
        
        # Strategy 2: Connected Components - find strongly connected groups (for remaining functions)
        connected_modules = self._group_by_connected_components(functions, processed_functions)
        modules.extend(connected_modules)
        logger.info(f"Created {len(connected_modules)} connected component modules")
        
        # Strategy 3: Dependency clustering - functions that depend on each other (for remaining functions)
        dependency_modules = self._group_by_dependency_clusters(functions, processed_functions)
        modules.extend(dependency_modules)
        logger.info(f"Created {len(dependency_modules)} dependency cluster modules")
        
        # Strategy 4: Remaining functions as individual modules (ONLY if really necessary)
        remaining_functions = [f for f in functions if f.name not in processed_functions]
        logger.info(f"Remaining unprocessed functions: {len(remaining_functions)}")
        
        # Only create single-function modules for important remaining functions
        for func in remaining_functions:
            # Skip functions with very low complexity or generic names
            if len(func.dependencies) >= 2 or len(func.name) >= 6:  # Some threshold for importance
                modules.append(self._create_single_function_module(func))
                processed_functions.add(func.name)
        
        return modules
    
    def _group_by_connected_components(self, functions: List[ExtractedModule], processed: Set[str]) -> List[SemanticModule]:
        """Group functions by connected components in call graph."""
        
        modules = []
        
        # Find weakly connected components (ignoring edge direction)
        undirected_graph = self.call_graph.to_undirected()
        components = list(nx.connected_components(undirected_graph))
        
        for component in components:
            # Only create modules for components with multiple functions
            if len(component) > 1 and not any(name in processed for name in component):
                
                component_functions = [self.function_map[name] for name in component if name in self.function_map]
                
                if len(component_functions) >= 2:  # At least 2 functions to make a meaningful module
                    module = self._create_semantic_module(
                        component_functions,
                        module_type="connected_component",
                        description=f"Connected component with {len(component_functions)} related functions"
                    )
                    modules.append(module)
                    processed.update(component)
                    
                    logger.debug(f"Created connected component module: {module.name} with functions {component}")
        
        return modules
    
    def _group_by_function_prefixes(self, functions: List[ExtractedModule], processed: Set[str]) -> List[SemanticModule]:
        """Group functions by common naming prefixes and semantic categories."""
        
        modules = []
        
        # Build semantic groups for mathematical/linear algebra functions
        semantic_groups = {
            "matrix": [],
            "vector": [],
            "test": [],
            "assert": [],
            "print": [],
            "get": [],
            "set": [],
            "is": [],
            "has": [],
        }
        
        # Also track specific prefixes
        prefix_groups = {}
        
        for func in functions:
            if func.name in processed:
                continue
            
            func_lower = func.name.lower()
            
            # Check semantic categories first
            grouped = False
            for category, group_list in semantic_groups.items():
                if category in func_lower:
                    group_list.append(func)
                    grouped = True
                    break
            
            # If not grouped semantically, try prefix extraction
            if not grouped:
                prefix = self._extract_function_prefix(func.name)
                if prefix and len(prefix) >= 3:
                    if prefix not in prefix_groups:
                        prefix_groups[prefix] = []
                    prefix_groups[prefix].append(func)
        
        # Create modules for semantic groups with multiple functions
        for category, group_functions in semantic_groups.items():
            if len(group_functions) >= 3:  # At least 3 functions for semantic groups
                module = self._create_semantic_module(
                    group_functions,
                    module_type="feature",
                    description=f"{category.title()} operations module"
                )
                modules.append(module)
                processed.update(func.name for func in group_functions)
                logger.debug(f"Created semantic module: {module.name} for '{category}' ({len(group_functions)} functions)")
        
        # Create modules for prefix groups with multiple functions
        for prefix, group_functions in prefix_groups.items():
            if len(group_functions) >= 2:  # At least 2 functions
                module = self._create_semantic_module(
                    group_functions,
                    module_type="feature",
                    description=f"Functions implementing {prefix} functionality"
                )
                modules.append(module)
                processed.update(func.name for func in group_functions)
                logger.debug(f"Created prefix-based module: {module.name} with prefix '{prefix}'")
        
        return modules
    
    def _group_by_dependency_clusters(self, functions: List[ExtractedModule], processed: Set[str]) -> List[SemanticModule]:
        """Group functions that have high dependency relationships."""
        
        modules = []
        
        # Find functions with high mutual dependencies
        for func in functions:
            if func.name in processed:
                continue
                
            # Find functions that this function calls and functions that call this function
            callee_functions = []
            caller_functions = []
            
            if self.call_graph.has_node(func.name):
                # Functions this function calls
                callees = list(self.call_graph.successors(func.name))
                callee_functions = [self.function_map[name] for name in callees if name in self.function_map and name not in processed]
                
                # Functions that call this function  
                callers = list(self.call_graph.predecessors(func.name))
                caller_functions = [self.function_map[name] for name in callers if name in self.function_map and name not in processed]
            
            # If there are strong bidirectional dependencies, create a module
            mutual_deps = set(f.name for f in callee_functions) & set(f.name for f in caller_functions)
            if mutual_deps:
                cluster_functions = [func] + [self.function_map[name] for name in mutual_deps]
                
                module = self._create_semantic_module(
                    cluster_functions,
                    module_type="dependency_cluster", 
                    description=f"Functions with mutual dependencies"
                )
                modules.append(module)
                processed.update(f.name for f in cluster_functions)
                
                logger.debug(f"Created dependency cluster module: {module.name}")
        
        return modules
    
    def _extract_function_prefix(self, function_name: str) -> Optional[str]:
        """Extract meaningful prefix from function name."""
        
        # Handle camelCase (e.g., CircularBufferCreate -> CircularBuffer)
        import re
        
        # Look for camelCase pattern
        camel_match = re.match(r'^([A-Z][a-z]+(?:[A-Z][a-z]*)*)[A-Z]', function_name)
        if camel_match:
            return camel_match.group(1)
        
        # Look for underscore pattern (e.g., list_create -> list)
        if '_' in function_name:
            parts = function_name.split('_')
            if len(parts) >= 2 and len(parts[0]) >= 3:
                return parts[0]
        
        # Look for common patterns
        for pattern in ['create', 'init', 'destroy', 'free', 'get', 'set', 'add', 'remove', 'push', 'pop']:
            if function_name.lower().endswith(pattern):
                prefix = function_name[:-len(pattern)]
                if len(prefix) >= 3:
                    return prefix
        
        return None
    
    def _create_semantic_module(self, functions: List[ExtractedModule], module_type: str, description: str) -> SemanticModule:
        """Create a semantic module from a group of functions."""
        
        import uuid
        
        # Generate module name based on primary function or common prefix
        if len(functions) == 1:
            module_name = f"{functions[0].name}_module"
        else:
            # Try to find common prefix
            names = [f.name for f in functions]
            common_prefix = self._find_common_prefix(names)
            if common_prefix and len(common_prefix) >= 3:
                module_name = f"{common_prefix}_module"
            else:
                module_name = f"module_{len(functions)}_functions"
        
        # Calculate internal and external dependencies
        all_function_names = {f.name for f in functions}
        internal_deps = set()
        external_deps = set()
        
        for func in functions:
            for dep in func.dependencies:
                if dep in all_function_names:
                    internal_deps.add(dep)
                elif dep in self.function_map:  # External to module but within codebase
                    external_deps.add(dep)
        
        # Calculate complexity score (simple heuristic)
        complexity_score = len(functions) * 10 + len(internal_deps) * 5 + len(external_deps) * 2
        
        return SemanticModule(
            id=str(uuid.uuid4()),
            name=module_name,
            description=description,
            functions=functions,
            internal_dependencies=internal_deps,
            external_dependencies=external_deps,
            file_path=functions[0].file_path if functions else None,
            module_type=module_type,
            complexity_score=complexity_score
        )
    
    def _create_single_function_module(self, func: ExtractedModule) -> SemanticModule:
        """Create a module containing a single function."""
        
        # Determine if external dependencies exist
        external_deps = {dep for dep in func.dependencies if dep in self.function_map}
        
        return SemanticModule(
            id=func.id,
            name=f"{func.name}_module",
            description=f"Single function module for {func.name}",
            functions=[func],
            internal_dependencies=set(),
            external_dependencies=external_deps,
            file_path=func.file_path,
            module_type="single_function",
            complexity_score=len(external_deps) * 2 + 10
        )
    
    def _find_common_prefix(self, names: List[str]) -> Optional[str]:
        """Find common prefix among function names."""
        if not names:
            return None
        
        if len(names) == 1:
            return self._extract_function_prefix(names[0])
        
        # Find longest common prefix
        prefix = names[0]
        for name in names[1:]:
            # Find common prefix between current prefix and this name
            common = ""
            for i, (c1, c2) in enumerate(zip(prefix, name)):
                if c1 == c2:
                    common += c1
                else:
                    break
            prefix = common
            
            # Stop if prefix becomes too short
            if len(prefix) < 3:
                break
        
        return prefix if len(prefix) >= 3 else None
    
    def _validate_and_enhance_modules(self, modules: List[SemanticModule]) -> List[SemanticModule]:
        """Validate modules and enhance them with dependency closure if needed."""
        
        validated_modules = []
        
        for module in modules:
            # Check if module needs dependency closure
            enhanced_module = self._ensure_dependency_closure(module)
            
            # Only include modules that meet quality criteria
            if self._meets_quality_criteria(enhanced_module):
                validated_modules.append(enhanced_module)
                logger.debug(f"Validated module: {enhanced_module.name} with {len(enhanced_module.functions)} functions")
            else:
                logger.debug(f"Rejected module: {module.name} - does not meet quality criteria")
        
        return validated_modules
    
    def _ensure_dependency_closure(self, module: SemanticModule) -> SemanticModule:
        """Ensure module includes its dependency closure for self-containment."""
        
        # For now, we'll keep the module as-is
        # In a more sophisticated implementation, we could add missing dependencies
        # that are within the same codebase to make the module truly self-contained
        
        return module
    
    def _meets_quality_criteria(self, module: SemanticModule) -> bool:
        """Check if module meets quality criteria for inclusion."""
        
        # Criteria 1: At least one function
        if not module.functions:
            return False
        
        # Criteria 2: Reasonable complexity (not too simple, not too complex)
        if module.complexity_score < 5:  # Too simple
            return False
        
        if module.complexity_score > 500:  # Too complex
            return False
        
        # Criteria 3: Functions should have meaningful names
        for func in module.functions:
            if len(func.name) < 2 or func.name.startswith('anonymous'):
                return False
        
        return True
    
    def get_module_statistics(self, modules: List[SemanticModule]) -> Dict:
        """Get statistics about the extracted modules."""
        
        if not modules:
            return {
                "total_modules": 0,
                "total_functions": 0,
                "avg_functions_per_module": 0,
                "self_contained_modules": 0,
                "module_types": {}
            }
        
        total_functions = sum(len(m.functions) for m in modules)
        self_contained = sum(1 for m in modules if m.is_self_contained)
        
        module_types = {}
        for module in modules:
            module_types[module.module_type] = module_types.get(module.module_type, 0) + 1
        
        return {
            "total_modules": len(modules),
            "total_functions": total_functions,
            "avg_functions_per_module": total_functions / len(modules),
            "self_contained_modules": self_contained,
            "self_contained_percentage": (self_contained / len(modules)) * 100,
            "module_types": module_types,
            "avg_complexity": sum(m.complexity_score for m in modules) / len(modules)
        }