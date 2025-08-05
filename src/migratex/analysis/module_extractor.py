"""High-level module extractor for semantic code modules."""

from typing import List, Dict, Optional
from pathlib import Path
import logging

from .module_analyzer import ModuleAnalyzer, SemanticModule

logger = logging.getLogger(__name__)


class ModuleExtractor:
    """High-level interface for extracting self-contained semantic modules from codebases."""
    
    def __init__(self):
        self.analyzer = ModuleAnalyzer()
    
    def extract_modules_from_repository(
        self, 
        repository_path: str, 
        language: str = "c",
        max_modules: Optional[int] = None
    ) -> List[SemanticModule]:
        """Extract semantic modules from a repository.
        
        Args:
            repository_path: Path to the repository to analyze
            language: Programming language of the codebase
            max_modules: Maximum number of modules to extract (for cost control)
            
        Returns:
            List of SemanticModule objects representing self-contained code modules
        """
        
        repo_path = Path(repository_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repository_path}")
        
        logger.info(f"Extracting modules from {repository_path} (language: {language})")
        
        # Extract modules using the analyzer
        modules = self.analyzer.analyze_repository(repo_path, language)
        
        # Sort modules by complexity/importance
        modules = self._sort_modules_by_importance(modules)
        
        # Apply max_modules limit if specified
        if max_modules and len(modules) > max_modules:
            logger.info(f"Limiting to {max_modules} modules (found {len(modules)})")
            modules = modules[:max_modules]
        
        # Log extraction results
        stats = self.analyzer.get_module_statistics(modules)
        logger.info(f"Extracted {len(modules)} modules with {stats['total_functions']} total functions")
        logger.info(f"Module types: {stats['module_types']}")
        logger.info(f"Self-contained modules: {stats['self_contained_modules']}/{len(modules)} ({stats.get('self_contained_percentage', 0):.1f}%)")
        
        return modules
    
    def extract_modules_from_files(
        self, 
        file_paths: List[str], 
        language: str = "c",
        max_modules: Optional[int] = None
    ) -> List[SemanticModule]:
        """Extract semantic modules from specific files.
        
        Args:
            file_paths: List of file paths to analyze
            language: Programming language of the files
            max_modules: Maximum number of modules to extract
            
        Returns:
            List of SemanticModule objects
        """
        
        # For now, create a temporary analysis by processing files individually
        # In a more sophisticated implementation, we'd analyze cross-file dependencies
        
        from .language_parser import LanguageParser
        
        parser = LanguageParser()
        all_functions = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                functions = parser.extract_modules(content, language, file_path)
                functions = [f for f in functions if f.kind == "function"]
                all_functions.extend(functions)
                
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
                continue
        
        if not all_functions:
            return []
        
        # For single file analysis, each function becomes its own module
        # This is a simplified approach - ideally we'd still do some grouping
        modules = []
        for func in all_functions:
            module = SemanticModule(
                id=func.id,
                name=f"{func.name}_module",
                description=f"Single function module for {func.name}",
                functions=[func],
                internal_dependencies=set(),
                external_dependencies=set(func.dependencies),
                file_path=func.file_path,
                module_type="single_function",
                complexity_score=len(func.dependencies) * 2 + 10
            )
            modules.append(module)
        
        # Sort and limit
        modules = self._sort_modules_by_importance(modules)
        if max_modules and len(modules) > max_modules:
            modules = modules[:max_modules]
        
        logger.info(f"Extracted {len(modules)} modules from {len(file_paths)} files")
        return modules
    
    def _sort_modules_by_importance(self, modules: List[SemanticModule]) -> List[SemanticModule]:
        """Sort modules by importance/complexity for prioritized analysis."""
        
        def importance_score(module: SemanticModule) -> float:
            score = 0.0
            
            # Prefer modules with multiple functions (more semantic value)
            score += len(module.functions) * 20
            
            # Prefer self-contained modules
            if module.is_self_contained:
                score += 50
            
            # Prefer feature modules over single functions
            if module.module_type == "feature":
                score += 30
            elif module.module_type == "connected_component":
                score += 25
            elif module.module_type == "dependency_cluster":
                score += 20
            
            # Consider complexity but not too much
            score += min(module.complexity_score * 0.1, 20)
            
            # Prefer modules with meaningful names (not anonymous)
            if not any("anonymous" in func.name for func in module.functions):
                score += 10
            
            return score
        
        return sorted(modules, key=importance_score, reverse=True)
    
    def get_module_summary(self, modules: List[SemanticModule]) -> Dict:
        """Get a summary of extracted modules for display purposes."""
        
        if not modules:
            return {
                "total_modules": 0,
                "total_functions": 0,
                "module_breakdown": {},
                "complexity_distribution": {},
                "self_contained_count": 0
            }
        
        total_functions = sum(len(m.functions) for m in modules)
        self_contained = sum(1 for m in modules if m.is_self_contained)
        
        # Module type breakdown
        type_breakdown = {}
        for module in modules:
            type_breakdown[module.module_type] = type_breakdown.get(module.module_type, 0) + 1
        
        # Complexity distribution
        complexity_ranges = {
            "simple": 0,      # 0-50
            "moderate": 0,    # 51-150
            "complex": 0,     # 151-300
            "very_complex": 0 # 300+
        }
        
        for module in modules:
            if module.complexity_score <= 50:
                complexity_ranges["simple"] += 1
            elif module.complexity_score <= 150:
                complexity_ranges["moderate"] += 1
            elif module.complexity_score <= 300:
                complexity_ranges["complex"] += 1
            else:
                complexity_ranges["very_complex"] += 1
        
        return {
            "total_modules": len(modules),
            "total_functions": total_functions,
            "avg_functions_per_module": total_functions / len(modules),
            "module_breakdown": type_breakdown,
            "complexity_distribution": complexity_ranges,
            "self_contained_count": self_contained,
            "self_contained_percentage": (self_contained / len(modules)) * 100
        }
    
    def validate_module_quality(self, module: SemanticModule) -> Dict:
        """Validate module quality and provide feedback."""
        
        issues = []
        recommendations = []
        quality_score = 100.0
        
        # Check function count
        if len(module.functions) == 1:
            issues.append("Module contains only one function")
            quality_score -= 20
        elif len(module.functions) > 10:
            issues.append("Module contains too many functions (>10)")
            quality_score -= 30
        
        # Check self-containment
        if not module.is_self_contained:
            issues.append(f"Module has {len(module.external_dependencies)} external dependencies")
            quality_score -= 15
            recommendations.append("Consider including dependency functions in module")
        
        # Check naming
        anonymous_functions = [f.name for f in module.functions if "anonymous" in f.name]
        if anonymous_functions:
            issues.append(f"Module contains anonymous functions: {anonymous_functions}")
            quality_score -= 25
        
        # Check complexity
        if module.complexity_score > 400:
            issues.append("Module complexity is very high")
            quality_score -= 20
            recommendations.append("Consider breaking module into smaller pieces")
        elif module.complexity_score < 10:
            issues.append("Module complexity is very low")
            quality_score -= 10
        
        # Determine overall quality
        if quality_score >= 90:
            quality_level = "excellent"
        elif quality_score >= 75:
            quality_level = "good"
        elif quality_score >= 60:
            quality_level = "fair"
        else:
            quality_level = "poor"
        
        return {
            "quality_score": max(0, quality_score),
            "quality_level": quality_level,
            "issues": issues,
            "recommendations": recommendations,
            "is_suitable_for_translation": quality_score >= 50
        }
    
    def describe_module(self, module: SemanticModule) -> str:
        """Generate a human-readable description of a module."""
        
        function_names = ", ".join(f.name for f in module.functions)
        
        description = f"Module '{module.name}' ({module.module_type})\n"
        description += f"Functions: {function_names}\n"
        description += f"Internal Dependencies: {len(module.internal_dependencies)}\n"
        description += f"External Dependencies: {len(module.external_dependencies)}\n"
        description += f"Self-contained: {'Yes' if module.is_self_contained else 'No'}\n"
        description += f"Complexity Score: {module.complexity_score:.1f}\n"
        description += f"Description: {module.description}"
        
        return description