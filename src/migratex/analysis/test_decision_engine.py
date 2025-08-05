"""Smart test decision engine based on AI coverage analysis."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .coverage_analyzer import CoverageAnalyzer, CoverageAnalysis, CoverageRecommendation
from .test_extractor import TestExtractor
from .test_generator import TestGenerator


@dataclass
class TestDecision:
    """Decision about test generation for a function."""
    function_name: str
    decision: str  # "skip", "generate", "enhance"
    reason: str
    coverage_analysis: Optional[CoverageAnalysis]
    existing_tests: Optional[str]
    generated_tests: Optional[str] = None
    generation_success: bool = False


class TestDecisionEngine:
    """Makes intelligent decisions about test generation based on AI analysis."""
    
    def __init__(self, coverage_threshold: int = 80):
        self.coverage_analyzer = CoverageAnalyzer()
        self.test_extractor = TestExtractor()
        self.test_generator = TestGenerator()
        self.coverage_threshold = coverage_threshold
    
    def analyze_and_decide(
        self, 
        functions: List[Dict], 
        repository_path: Path,
        progress_callback: Optional[callable] = None
    ) -> List[TestDecision]:
        """Analyze functions and make intelligent test generation decisions."""
        
        decisions = []
        
        # First, find all existing tests
        existing_tests_map = self._map_existing_tests(repository_path)
        
        for func in functions:
            func_name = func["name"]
            
            # Notify progress callback - starting analysis
            if progress_callback:
                progress_callback(func_name, "analyzing")
            
            try:
                decision = self._analyze_single_function(func, existing_tests_map, progress_callback)
                decisions.append(decision)
                
                # Notify progress callback - completed
                if progress_callback:
                    progress_callback(func_name, "completed", decision.coverage_analysis, decision)
                    
            except Exception as e:
                # Notify progress callback - failed
                if progress_callback:
                    progress_callback(func_name, "failed", error_message=str(e))
                
                # Create a failed decision
                failed_decision = TestDecision(
                    function_name=func_name,
                    decision="generate",  # Default fallback
                    reason=f"Analysis failed: {str(e)}",
                    coverage_analysis=None,
                    existing_tests=None,
                    generated_tests=None,
                    generation_success=False
                )
                decisions.append(failed_decision)
        
        return decisions
    
    def _map_existing_tests(self, repository_path: Path) -> Dict[str, str]:
        """Map function names to their existing tests."""
        
        # Find test files
        test_files = self.test_extractor.identify_test_files(repository_path, "c")
        
        existing_tests_map = {}
        
        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    test_content = f.read()
                
                # Extract test functions from this file
                test_functions = self.test_extractor.extract_test_functions(test_content, "c")
                
                # Try to associate test functions with source functions
                # This is a simple heuristic - could be improved
                for test_func in test_functions:
                    test_name = test_func["name"]
                    
                    # Extract likely function name from test name
                    # e.g., "test_CircularBufferCreate" -> "CircularBufferCreate"
                    if test_name.startswith("test_"):
                        likely_func_name = test_name[5:]  # Remove "test_" prefix
                        existing_tests_map[likely_func_name] = test_content
                    
                    # Also try without prefix variations
                    # e.g., "CircularBufferCreateTest" -> "CircularBufferCreate"  
                    if test_name.endswith("Test"):
                        likely_func_name = test_name[:-4]  # Remove "Test" suffix
                        existing_tests_map[likely_func_name] = test_content
                
            except Exception as e:
                print(f"Warning: Could not read test file {test_file}: {e}")
                continue
        
        return existing_tests_map
    
    def _analyze_single_function(
        self, 
        func: Dict, 
        existing_tests_map: Dict[str, str],
        progress_callback: Optional[callable] = None
    ) -> TestDecision:
        """Analyze a single function and decide on test generation."""
        
        func_name = func["name"]
        func_code = func["content"]
        
        # Check for existing tests
        existing_tests = existing_tests_map.get(func_name)
        
        # Notify progress callback - deciding coverage
        if progress_callback:
            progress_callback(func_name, "deciding")
        
        # Get AI coverage analysis
        coverage_analysis = self.coverage_analyzer.analyze_function_coverage(
            function_code=func_code,
            function_name=func_name,
            existing_tests=existing_tests,
            language=func.get("language", "c")
        )
        
        if not coverage_analysis:
            # Fallback decision if AI analysis fails
            if existing_tests:
                return TestDecision(
                    function_name=func_name,
                    decision="skip",
                    reason="AI analysis failed, but existing tests found",
                    coverage_analysis=None,
                    existing_tests=existing_tests
                )
            else:
                return TestDecision(
                    function_name=func_name,
                    decision="generate",
                    reason="AI analysis failed, no existing tests",
                    coverage_analysis=None,
                    existing_tests=None
                )
        
        # Make decision based on AI recommendation
        decision, reason = self._make_decision_from_analysis(coverage_analysis)
        
        # Execute the decision (generate tests if needed)
        generated_tests = None
        generation_success = False
        
        if decision == "generate":
            # Notify progress callback - generating tests
            if progress_callback:
                progress_callback(func_name, "generating")
            
            generated_tests, generation_success = self._generate_tests_for_function(func, coverage_analysis)
        
        return TestDecision(
            function_name=func_name,
            decision=decision,
            reason=reason,
            coverage_analysis=coverage_analysis,
            existing_tests=existing_tests,
            generated_tests=generated_tests,
            generation_success=generation_success
        )
    
    def _make_decision_from_analysis(self, analysis: CoverageAnalysis) -> Tuple[str, str]:
        """Make a decision based on AI coverage analysis."""
        
        recommendation = analysis.recommendation
        coverage = analysis.coverage_percentage
        
        if recommendation == CoverageRecommendation.SUFFICIENT:
            if coverage >= self.coverage_threshold:
                return "skip", f"Sufficient coverage ({coverage}%) - AI recommends no additional tests"
            else:
                return "generate", f"Coverage below threshold ({coverage}% < {self.coverage_threshold}%) despite AI recommendation"
        
        elif recommendation == CoverageRecommendation.GENERATE_NEW:
            return "generate", f"No existing tests - AI recommends generating comprehensive test suite"
        
        elif recommendation == CoverageRecommendation.GENERATE_ADDITIONAL:
            return "generate", f"Existing tests incomplete ({coverage}%) - AI recommends additional test scenarios"
        
        elif recommendation == CoverageRecommendation.ENHANCE_EXISTING:
            return "generate", f"Existing tests poor quality - AI recommends enhanced test suite"
        
        else:
            return "generate", f"Unknown recommendation - defaulting to generation"
    
    def _generate_tests_for_function(
        self, 
        func: Dict, 
        coverage_analysis: CoverageAnalysis
    ) -> Tuple[Optional[str], bool]:
        """Generate tests for a function based on coverage analysis."""
        
        try:
            # Create enhanced prompt based on AI analysis
            enhanced_func = func.copy()
            enhanced_func["coverage_gaps"] = coverage_analysis.coverage_gaps
            enhanced_func["missing_scenarios"] = coverage_analysis.missing_scenarios
            enhanced_func["ai_guidance"] = coverage_analysis.reasoning
            
            # Generate tests with AI guidance
            result = self.test_generator.generate_test(enhanced_func)
            
            if result:
                return result["test_content"], True
            else:
                return None, False
                
        except Exception as e:
            print(f"Error generating tests for {func['name']}: {e}")
            return None, False
    
    def get_decision_summary(self, decisions: List[TestDecision]) -> Dict:
        """Generate a summary of all test decisions."""
        
        total = len(decisions)
        skipped = sum(1 for d in decisions if d.decision == "skip")
        generated = sum(1 for d in decisions if d.decision == "generate")
        successful_generations = sum(1 for d in decisions if d.generation_success)
        
        avg_coverage = 0
        coverage_count = 0
        
        for decision in decisions:
            if decision.coverage_analysis and decision.coverage_analysis.coverage_percentage is not None:
                avg_coverage += decision.coverage_analysis.coverage_percentage
                coverage_count += 1
        
        if coverage_count > 0:
            avg_coverage = avg_coverage / coverage_count
        
        return {
            "total_functions": total,
            "functions_skipped": skipped,
            "functions_for_generation": generated,
            "successful_generations": successful_generations,
            "failed_generations": generated - successful_generations,
            "average_coverage": round(avg_coverage, 1),
            "skip_rate": round((skipped / total) * 100, 1) if total > 0 else 0,
            "generation_success_rate": round((successful_generations / generated) * 100, 1) if generated > 0 else 0
        }