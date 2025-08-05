"""Smart module-level test decision engine based on AI coverage analysis."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .module_coverage_analyzer import ModuleCoverageAnalyzer, ModuleCoverageAnalysis, CoverageRecommendation
from .module_analyzer import SemanticModule
from .test_extractor import TestExtractor
from .test_generator import TestGenerator


@dataclass
class ModuleTestDecision:
    """Decision about test generation for a module."""
    module_name: str
    module_type: str
    decision: str  # "skip", "generate", "enhance"
    reason: str
    coverage_analysis: Optional[ModuleCoverageAnalysis]
    existing_tests: Optional[str]
    generated_tests: Optional[str] = None
    generation_success: bool = False
    functions_in_module: List[str] = None
    
    def __post_init__(self):
        if self.functions_in_module is None:
            self.functions_in_module = []


class ModuleTestDecisionEngine:
    """Makes intelligent decisions about test generation based on module-level AI analysis."""
    
    def __init__(self, coverage_threshold: int = 80):
        self.coverage_analyzer = ModuleCoverageAnalyzer()
        self.test_extractor = TestExtractor()
        self.test_generator = TestGenerator()
        self.coverage_threshold = coverage_threshold
    
    def analyze_and_decide(
        self, 
        modules: List[SemanticModule], 
        repository_path: Path,
        progress_callback: Optional[callable] = None
    ) -> List[ModuleTestDecision]:
        """Analyze modules and make intelligent test generation decisions."""
        
        decisions = []
        
        # First, find all existing tests for the repository
        existing_tests_map = self._map_existing_tests_to_modules(repository_path, modules)
        
        for module in modules:
            module_name = module.name
            
            # Notify progress callback - starting analysis
            if progress_callback:
                progress_callback(module_name, "analyzing")
            
            try:
                decision = self._analyze_single_module(module, existing_tests_map, progress_callback)
                decisions.append(decision)
                
                # Notify progress callback - completed
                if progress_callback:
                    progress_callback(module_name, "completed", decision.coverage_analysis, decision)
                    
            except Exception as e:
                # Notify progress callback - failed
                if progress_callback:
                    progress_callback(module_name, "failed", error_message=str(e))
                
                # Create a failed decision
                failed_decision = ModuleTestDecision(
                    module_name=module_name,
                    module_type=module.module_type,
                    decision="generate",  # Default fallback
                    reason=f"Analysis failed: {str(e)}",
                    coverage_analysis=None,
                    existing_tests=None,
                    generated_tests=None,
                    generation_success=False,
                    functions_in_module=module.function_names
                )
                decisions.append(failed_decision)
        
        return decisions
    
    def _map_existing_tests_to_modules(self, repository_path: Path, modules: List[SemanticModule]) -> Dict[str, str]:
        """Map existing tests to modules based on function names and patterns."""
        
        # Find test files
        test_files = self.test_extractor.identify_test_files(repository_path, "c")
        
        module_tests_map = {}
        
        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    test_content = f.read()
                
                # Extract test functions from this file
                test_functions = self.test_extractor.extract_test_functions(test_content, "c")
                
                # Try to associate test functions with modules
                for module in modules:
                    module_test_content = []
                    
                    for test_func in test_functions:
                        test_name = test_func["name"]
                        
                        # Check if test is related to any function in this module
                        for func_name in module.function_names:
                            if self._is_test_related_to_function(test_name, func_name):
                                module_test_content.append(test_func["content"])
                                break
                    
                    # If we found tests for this module, combine them
                    if module_test_content:
                        if module.name in module_tests_map:
                            module_tests_map[module.name] += "\n\n" + "\n\n".join(module_test_content)
                        else:
                            module_tests_map[module.name] = "\n\n".join(module_test_content)
                
            except Exception as e:
                print(f"Warning: Could not read test file {test_file}: {e}")
                continue
        
        return module_tests_map
    
    def _is_test_related_to_function(self, test_name: str, function_name: str) -> bool:
        """Check if a test is related to a specific function."""
        
        test_lower = test_name.lower()
        func_lower = function_name.lower()
        
        # Direct matches
        if func_lower in test_lower:
            return True
        
        # Pattern matches
        patterns = [
            f"test_{func_lower}",
            f"test{function_name}",
            f"{func_lower}_test",
            f"{function_name}Test"
        ]
        
        for pattern in patterns:
            if pattern.lower() in test_lower:
                return True
        
        return False
    
    def _analyze_single_module(
        self, 
        module: SemanticModule, 
        existing_tests_map: Dict[str, str],
        progress_callback: Optional[callable] = None
    ) -> ModuleTestDecision:
        """Analyze a single module and decide on test generation."""
        
        module_name = module.name
        
        # Check for existing tests
        existing_tests = existing_tests_map.get(module_name)
        
        # Notify progress callback - deciding coverage
        if progress_callback:
            progress_callback(module_name, "deciding")
        
        # Get AI coverage analysis for the entire module
        coverage_analysis = self.coverage_analyzer.analyze_module_coverage(
            module=module,
            existing_tests=existing_tests,
            language="c"  # TODO: Make this configurable
        )
        
        if not coverage_analysis:
            # Fallback decision if AI analysis fails
            if existing_tests:
                return ModuleTestDecision(
                    module_name=module_name,
                    module_type=module.module_type,
                    decision="skip",
                    reason="AI analysis failed, but existing tests found",
                    coverage_analysis=None,
                    existing_tests=existing_tests,
                    functions_in_module=module.function_names
                )
            else:
                return ModuleTestDecision(
                    module_name=module_name,
                    module_type=module.module_type,
                    decision="generate",
                    reason="AI analysis failed, no existing tests",
                    coverage_analysis=None,
                    existing_tests=None,
                    functions_in_module=module.function_names
                )
        
        # Make decision based on AI recommendation
        decision, reason = self._make_decision_from_analysis(coverage_analysis)
        
        # Execute the decision (generate tests if needed)
        generated_tests = None
        generation_success = False
        
        if decision == "generate":
            # Notify progress callback - generating tests
            if progress_callback:
                progress_callback(module_name, "generating")
            
            generated_tests, generation_success = self._generate_tests_for_module(module, coverage_analysis)
        
        return ModuleTestDecision(
            module_name=module_name,
            module_type=module.module_type,
            decision=decision,
            reason=reason,
            coverage_analysis=coverage_analysis,
            existing_tests=existing_tests,
            generated_tests=generated_tests,
            generation_success=generation_success,
            functions_in_module=module.function_names
        )
    
    def _make_decision_from_analysis(self, analysis: ModuleCoverageAnalysis) -> Tuple[str, str]:
        """Make a decision based on AI module coverage analysis."""
        
        recommendation = analysis.recommendation
        coverage = analysis.coverage_percentage
        
        if recommendation == CoverageRecommendation.SUFFICIENT:
            if coverage >= self.coverage_threshold:
                return "skip", f"Sufficient module coverage ({coverage}%) - AI recommends no additional tests"
            else:
                return "generate", f"Module coverage below threshold ({coverage}% < {self.coverage_threshold}%) despite AI recommendation"
        
        elif recommendation == CoverageRecommendation.GENERATE_NEW:
            return "generate", f"No existing tests for module - AI recommends generating comprehensive test suite"
        
        elif recommendation == CoverageRecommendation.GENERATE_ADDITIONAL:
            return "generate", f"Existing module tests incomplete ({coverage}%) - AI recommends additional test scenarios"
        
        elif recommendation == CoverageRecommendation.ENHANCE_EXISTING:
            return "generate", f"Existing module tests poor quality - AI recommends enhanced test suite"
        
        else:
            return "generate", f"Unknown recommendation - defaulting to generation"
    
    def _generate_tests_for_module(
        self, 
        module: SemanticModule, 
        coverage_analysis: ModuleCoverageAnalysis
    ) -> Tuple[Optional[str], bool]:
        """Generate tests for a module based on coverage analysis."""
        
        try:
            # Create enhanced module data for test generation
            enhanced_module_data = {
                "name": module.name,
                "type": module.module_type,
                "description": module.description,
                "functions": [],
                "coverage_gaps": coverage_analysis.coverage_gaps,
                "missing_scenarios": coverage_analysis.missing_scenarios,
                "ai_guidance": coverage_analysis.reasoning,
                "integration_tests_needed": coverage_analysis.integration_tests_needed,
                "complexity_assessment": coverage_analysis.complexity_assessment,
                "language": "c"
            }
            
            # Add function details
            for func in module.functions:
                func_data = {
                    "name": func.name,
                    "content": func.source_code,
                    "dependencies": list(func.dependencies)
                }
                enhanced_module_data["functions"].append(func_data)
            
            # Combine all function code for context
            combined_code = f"// Module: {module.name}\n// Type: {module.module_type}\n// Description: {module.description}\n\n"
            combined_code += module.source_code
            
            # Use the existing test generator with enhanced context
            # Note: This is a simplified approach - ideally we'd have a dedicated module test generator
            result = self.test_generator.generate_test({
                "name": module.name,
                "content": combined_code,
                "language": "c",
                "module_context": enhanced_module_data
            })
            
            if result:
                return result["test_content"], True
            else:
                return None, False
                
        except Exception as e:
            print(f"Error generating tests for module {module.name}: {e}")
            return None, False
    
    def get_decision_summary(self, decisions: List[ModuleTestDecision]) -> Dict:
        """Generate a summary of all module test decisions."""
        
        total = len(decisions)
        skipped = sum(1 for d in decisions if d.decision == "skip")
        generated = sum(1 for d in decisions if d.decision == "generate")
        successful_generations = sum(1 for d in decisions if d.generation_success)
        
        # Calculate total functions across all modules
        total_functions = sum(len(d.functions_in_module) for d in decisions)
        
        avg_coverage = 0
        coverage_count = 0
        
        for decision in decisions:
            if decision.coverage_analysis and decision.coverage_analysis.coverage_percentage is not None:
                avg_coverage += decision.coverage_analysis.coverage_percentage
                coverage_count += 1
        
        if coverage_count > 0:
            avg_coverage = avg_coverage / coverage_count
        
        # Count modules needing integration tests
        integration_needed = sum(
            1 for d in decisions 
            if d.coverage_analysis and d.coverage_analysis.integration_tests_needed
        )
        
        return {
            "total_modules": total,
            "total_functions": total_functions,
            "modules_skipped": skipped,
            "modules_for_generation": generated,
            "successful_generations": successful_generations,
            "failed_generations": generated - successful_generations,
            "average_coverage": round(avg_coverage, 1),
            "skip_rate": round((skipped / total) * 100, 1) if total > 0 else 0,
            "generation_success_rate": round((successful_generations / generated) * 100, 1) if generated > 0 else 0,
            "modules_needing_integration_tests": integration_needed,
            "avg_functions_per_module": round(total_functions / total, 1) if total > 0 else 0
        }
    
    def get_module_recommendations(self, decision: ModuleTestDecision) -> Dict:
        """Get specific test recommendations for a module."""
        
        if not decision.coverage_analysis:
            return {"recommendations": [], "priority": "medium"}
        
        return self.coverage_analyzer.get_module_test_recommendations(decision.coverage_analysis)