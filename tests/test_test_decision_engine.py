"""Tests for intelligent test decision engine."""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

from migratex.analysis.test_decision_engine import TestDecisionEngine
from migratex.analysis.language_parser import LanguageParser

# Load environment variables
load_dotenv()


class TestTestDecisionEngine:
    """Test the intelligent test decision engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.decision_engine = TestDecisionEngine(coverage_threshold=80)
        self.language_parser = LanguageParser()
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_analyze_and_decide_real_repository(self):
        """Test decision engine on real CRUST-bench repository."""
        
        # Use CircularBuffer repository
        repo_path = Path("CRUST-bench/datasets/CBench/CircularBuffer")
        
        if not repo_path.exists():
            pytest.skip("CRUST-bench repository not available")
        
        # Extract functions using existing pipeline
        source_files = list(repo_path.glob("*.c"))
        assert len(source_files) > 0, "No C source files found"
        
        all_functions = []
        for source_file in source_files:
            with open(source_file, 'r') as f:
                content = f.read()
            
            # Extract functions using language parser
            modules = self.language_parser.extract_modules(content, "c", str(source_file))
            # Convert ExtractedModule objects to function dictionaries
            functions = []
            for module in modules:
                if module.kind == "function":
                    functions.append({
                        "name": module.name,
                        "content": module.source_code,
                        "language": "c"
                    })
            all_functions.extend(functions)
        
        assert len(all_functions) > 0, "No functions extracted"
        print(f"\n🔍 Extracted {len(all_functions)} functions from CircularBuffer")
        
        # Test decision engine with first 2 functions (cost control)
        test_functions = all_functions[:2]
        
        # Make decisions
        decisions = self.decision_engine.analyze_and_decide(test_functions, repo_path)
        
        assert len(decisions) == len(test_functions), "Should have decisions for all functions"
        
        print(f"\n📊 Test Decision Results:")
        for decision in decisions:
            print(f"  📋 Function: {decision.function_name}")
            print(f"     Decision: {decision.decision}")
            print(f"     Reason: {decision.reason}")
            if decision.coverage_analysis:
                print(f"     Coverage: {decision.coverage_analysis.coverage_percentage}%")
                print(f"     Quality: {decision.coverage_analysis.existing_tests_quality}")
                print(f"     Priority: {decision.coverage_analysis.priority.value}")
            print(f"     Generation Success: {decision.generation_success}")
            if decision.generated_tests:
                print(f"     Generated Test Preview:")
                print(f"       {decision.generated_tests[:200]}...")
            print()
        
        # Validate decisions
        for decision in decisions:
            assert decision.function_name in [f["name"] for f in test_functions]
            assert decision.decision in ["skip", "generate", "enhance"]
            assert len(decision.reason) > 0
            
            # If decided to generate, should have attempted generation
            if decision.decision == "generate":
                assert decision.generated_tests is not None or not decision.generation_success
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_decision_summary_generation(self):
        """Test decision summary generation."""
        
        repo_path = Path("CRUST-bench/datasets/CBench/CircularBuffer")
        
        if not repo_path.exists():
            pytest.skip("CRUST-bench repository not available")
        
        # Extract a few functions
        source_files = list(repo_path.glob("*.c"))
        all_functions = []
        for source_file in source_files[:1]:  # Just first file
            with open(source_file, 'r') as f:
                content = f.read()
            # Extract functions using language parser
            modules = self.language_parser.extract_modules(content, "c", str(source_file))
            # Convert ExtractedModule objects to function dictionaries
            functions = []
            for module in modules:
                if module.kind == "function":
                    functions.append({
                        "name": module.name,
                        "content": module.source_code,
                        "language": "c"
                    })
            all_functions.extend(functions[:3])  # First 3 functions only
        
        # Make decisions
        decisions = self.decision_engine.analyze_and_decide(all_functions, repo_path)
        
        # Generate summary
        summary = self.decision_engine.get_decision_summary(decisions)
        
        print(f"\n📈 Decision Summary:")
        print(f"  Total Functions: {summary['total_functions']}")
        print(f"  Functions Skipped: {summary['functions_skipped']}")
        print(f"  Functions for Generation: {summary['functions_for_generation']}")
        print(f"  Successful Generations: {summary['successful_generations']}")
        print(f"  Failed Generations: {summary['failed_generations']}")
        print(f"  Average Coverage: {summary['average_coverage']}%")
        print(f"  Skip Rate: {summary['skip_rate']}%")
        print(f"  Generation Success Rate: {summary['generation_success_rate']}%")
        
        # Validate summary
        assert summary['total_functions'] == len(decisions)
        assert summary['total_functions'] > 0
        assert summary['skip_rate'] >= 0 and summary['skip_rate'] <= 100
        if summary['functions_for_generation'] > 0:
            assert summary['generation_success_rate'] >= 0 and summary['generation_success_rate'] <= 100
    
    def test_decision_engine_without_api_key(self):
        """Test decision engine handles missing API key gracefully."""
        
        if os.getenv('GOOGLE_API_KEY'):
            pytest.skip("API key is available")
        
        # Create test function data
        test_functions = [
            {
                "name": "test_function",
                "content": "int test_function(int x) { return x * 2; }",
                "language": "c"
            }
        ]
        
        repo_path = Path(".")
        
        # Should handle gracefully without API
        decisions = self.decision_engine.analyze_and_decide(test_functions, repo_path)
        
        assert len(decisions) == 1
        decision = decisions[0]
        
        # Should make fallback decision
        assert decision.function_name == "test_function"
        assert decision.decision in ["skip", "generate"]
        assert "AI analysis failed" in decision.reason
        assert decision.coverage_analysis is None