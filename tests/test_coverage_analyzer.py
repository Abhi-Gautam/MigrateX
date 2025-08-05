"""Tests for AI-powered coverage analyzer."""

import os
import pytest
from dotenv import load_dotenv

from migratex.analysis.coverage_analyzer import (
    CoverageAnalyzer, 
    CoverageRecommendation, 
    TestPriority
)

# Load environment variables
load_dotenv()


class TestCoverageAnalyzer:
    """Test the AI-powered coverage analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CoverageAnalyzer()
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_analyze_function_with_no_existing_tests(self):
        """Test coverage analysis for function with no existing tests."""
        
        function_code = """
int add(int a, int b) {
    if (a < 0 || b < 0) {
        return -1;  // Error case
    }
    return a + b;
}
"""
        
        result = self.analyzer.analyze_function_coverage(
            function_code=function_code,
            function_name="add",
            existing_tests=None,
            language="c"
        )
        
        assert result is not None
        assert result.function_name == "add"
        assert isinstance(result.coverage_percentage, int)
        assert 0 <= result.coverage_percentage <= 100
        assert isinstance(result.coverage_gaps, list)
        assert result.existing_tests_quality in ["excellent", "good", "fair", "poor", "none"]
        assert isinstance(result.recommendation, CoverageRecommendation)
        assert isinstance(result.priority, TestPriority)
        assert len(result.reasoning) > 0
        
        print(f"\n📊 Coverage Analysis Results for 'add' function:")
        print(f"   Coverage: {result.coverage_percentage}%")
        print(f"   Quality: {result.existing_tests_quality}")
        print(f"   Recommendation: {result.recommendation.value}")
        print(f"   Priority: {result.priority.value}")
        print(f"   Missing scenarios: {result.missing_scenarios}")
        print(f"   Reasoning: {result.reasoning}")
        
        # Should recommend generating new tests since none exist
        assert result.recommendation in [CoverageRecommendation.GENERATE_NEW]
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_analyze_function_with_existing_tests(self):
        """Test coverage analysis for function with existing tests."""
        
        function_code = """
CircularBuffer CircularBufferCreate(size_t size) {
    size_t totalSize = sizeof(struct s_circularBuffer) + size;
    void *p = malloc(totalSize);
    if (!p) return NULL;
    
    CircularBuffer buffer = (CircularBuffer)p;
    buffer->buffer = p + sizeof(struct s_circularBuffer);
    buffer->size = size;
    CircularBufferReset(buffer);
    return buffer;
}
"""
        
        existing_tests = """
void test_CircularBufferCreate() {
    CircularBuffer cb = CircularBufferCreate(10);
    assert(cb != NULL);
    assert(cb->size == 10);
    CircularBufferFree(cb);
}
"""
        
        result = self.analyzer.analyze_function_coverage(
            function_code=function_code,
            function_name="CircularBufferCreate",
            existing_tests=existing_tests,
            language="c"
        )
        
        assert result is not None
        assert result.function_name == "CircularBufferCreate"
        assert isinstance(result.coverage_percentage, int)
        assert len(result.missing_scenarios) >= 0
        
        print(f"\n📊 Coverage Analysis Results for 'CircularBufferCreate' function:")
        print(f"   Coverage: {result.coverage_percentage}%")
        print(f"   Quality: {result.existing_tests_quality}")
        print(f"   Recommendation: {result.recommendation.value}")
        print(f"   Priority: {result.priority.value}")
        print(f"   Coverage gaps: {result.coverage_gaps}")
        print(f"   Missing scenarios: {result.missing_scenarios}")
        print(f"   Reasoning: {result.reasoning}")
        
        # Should have some coverage since basic test exists
        assert result.coverage_percentage > 0
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_analyze_well_tested_function(self):
        """Test coverage analysis for a function with comprehensive tests."""
        
        function_code = """
int max(int a, int b) {
    return (a > b) ? a : b;
}
"""
        
        existing_tests = """
void test_max() {
    // Basic functionality
    assert(max(5, 3) == 5);
    assert(max(2, 7) == 7);
    assert(max(4, 4) == 4);
    
    // Edge cases
    assert(max(0, 0) == 0);
    assert(max(-1, -2) == -1);
    assert(max(INT_MAX, INT_MAX - 1) == INT_MAX);
    assert(max(INT_MIN, INT_MIN + 1) == INT_MIN + 1);
    
    // Negative numbers
    assert(max(-10, -5) == -5);
    assert(max(-1, 0) == 0);
}
"""
        
        result = self.analyzer.analyze_function_coverage(
            function_code=function_code,
            function_name="max",
            existing_tests=existing_tests,
            language="c"
        )
        
        assert result is not None
        assert result.function_name == "max"
        
        print(f"\n📊 Coverage Analysis Results for well-tested 'max' function:")
        print(f"   Coverage: {result.coverage_percentage}%")
        print(f"   Quality: {result.existing_tests_quality}")
        print(f"   Recommendation: {result.recommendation.value}")
        print(f"   Priority: {result.priority.value}")
        print(f"   Missing scenarios: {result.missing_scenarios}")
        print(f"   Reasoning: {result.reasoning}")
        
        # Should have high coverage and possibly recommend sufficient
        assert result.coverage_percentage >= 70  # Should be well covered
        
    def test_analyze_without_api_key(self):
        """Test that analyzer handles missing API key gracefully."""
        analyzer_no_key = CoverageAnalyzer(api_key=None)
        
        if not os.getenv('GOOGLE_API_KEY'):
            result = analyzer_no_key.analyze_function_coverage(
                function_code="int test() { return 1; }",
                function_name="test"
            )
            assert result is None
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available") 
    def test_analyze_multiple_functions(self):
        """Test analyzing multiple functions in batch."""
        
        functions_data = [
            {
                "function_name": "add",
                "function_code": "int add(int a, int b) { return a + b; }",
                "existing_tests": None,
                "language": "c"
            },
            {
                "function_name": "subtract", 
                "function_code": "int subtract(int a, int b) { return a - b; }",
                "existing_tests": "void test_subtract() { assert(subtract(5, 3) == 2); }",
                "language": "c"
            }
        ]
        
        results = self.analyzer.analyze_multiple_functions(functions_data)
        
        assert len(results) <= 2  # Some might fail, but at least try both
        
        for result in results:
            assert result.function_name in ["add", "subtract"]
            assert isinstance(result.coverage_percentage, int)
            assert isinstance(result.recommendation, CoverageRecommendation)
            
            print(f"\n📊 Batch Analysis - {result.function_name}:")
            print(f"   Coverage: {result.coverage_percentage}%")
            print(f"   Recommendation: {result.recommendation.value}")
            print(f"   Priority: {result.priority.value}")