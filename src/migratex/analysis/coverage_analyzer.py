"""AI-powered test coverage analysis using Gemini."""

import json
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

import google.generativeai as genai


class CoverageRecommendation(Enum):
    """Test coverage recommendations from AI analysis."""
    SUFFICIENT = "sufficient"
    GENERATE_NEW = "generate_new" 
    GENERATE_ADDITIONAL = "generate_additional"
    ENHANCE_EXISTING = "enhance_existing"


class TestPriority(Enum):
    """Priority levels for test generation."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CoverageAnalysis:
    """Results from AI coverage analysis."""
    function_name: str
    coverage_percentage: int
    coverage_gaps: List[str]
    existing_tests_quality: str
    recommendation: CoverageRecommendation
    missing_scenarios: List[str]
    priority: TestPriority
    reasoning: str
    estimated_effort: str = "medium"


class CoverageAnalyzer:
    """AI-powered test coverage analyzer using Gemini."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or environment variable
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini model."""
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception:
            # For testing or when no API key is available
            self.model = None
    
    def analyze_function_coverage(
        self, 
        function_code: str, 
        function_name: str,
        existing_tests: Optional[str] = None,
        language: str = "c"
    ) -> Optional[CoverageAnalysis]:
        """Analyze test coverage for a function using AI."""
        
        if not self.model:
            return None
        
        try:
            prompt = self._construct_coverage_prompt(
                function_code, function_name, existing_tests, language
            )
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return self._parse_coverage_response(response.text, function_name)
            
        except Exception as e:
            print(f"Error analyzing coverage for {function_name}: {e}")
            return None
        
        return None
    
    def _construct_coverage_prompt(
        self, 
        function_code: str, 
        function_name: str,
        existing_tests: Optional[str],
        language: str
    ) -> str:
        """Construct a comprehensive coverage analysis prompt."""
        
        existing_tests_section = existing_tests if existing_tests else "None - No existing tests found"
        
        return f"""
You are an expert software testing engineer. Analyze the test coverage for this {language.upper()} function and provide a comprehensive assessment.

FUNCTION TO ANALYZE:
```{language}
{function_code}
```

EXISTING TESTS:
```{language}
{existing_tests_section}
```

Please analyze the function and existing tests, then provide your assessment in this EXACT JSON format:

{{
    "coverage_percentage": <0-100 integer>,
    "coverage_gaps": ["gap1", "gap2", ...],
    "existing_tests_quality": "excellent/good/fair/poor/none",
    "recommendation": "sufficient/generate_new/generate_additional/enhance_existing",
    "missing_scenarios": [
        "Specific test scenario 1",
        "Specific test scenario 2",
        "..."
    ],
    "priority": "high/medium/low",
    "reasoning": "Detailed explanation of your analysis and recommendation",
    "estimated_effort": "low/medium/high"
}}

ANALYSIS GUIDELINES:
1. **Coverage Assessment**: Consider all code paths, edge cases, error conditions, boundary values
2. **Quality Evaluation**: Rate existing tests on completeness, edge cases, error handling
3. **Gap Identification**: Specifically identify what scenarios are missing
4. **Smart Recommendations**: 
   - "sufficient" if coverage ≥ 90% with good edge cases
   - "generate_additional" if existing tests are good but missing scenarios
   - "enhance_existing" if tests exist but are incomplete/poor quality
   - "generate_new" if no tests or very poor coverage
5. **Priority Assessment**: 
   - "high" for functions with complex logic, memory management, error handling
   - "medium" for standard business logic
   - "low" for simple getters/setters or well-tested functions

Focus on practical, meaningful test scenarios that would catch real bugs. Consider:
- Null/invalid input handling
- Boundary conditions (min/max values, empty inputs)
- Memory management (allocation failures, leaks)
- Error conditions and error handling paths
- State validation and side effects
- Integration with dependencies

Provide ONLY the JSON response, no additional text.
"""
    
    def _parse_coverage_response(self, response_text: str, function_name: str) -> Optional[CoverageAnalysis]:
        """Parse the AI response into a CoverageAnalysis object."""
        try:
            # Extract JSON from response (handle cases where there might be extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                'coverage_percentage', 'coverage_gaps', 'existing_tests_quality',
                'recommendation', 'missing_scenarios', 'priority', 'reasoning'
            ]
            
            for field in required_fields:
                if field not in data:
                    print(f"Missing required field '{field}' in AI response")
                    return None
            
            # Parse enums
            try:
                recommendation = CoverageRecommendation(data['recommendation'])
                priority = TestPriority(data['priority'])
            except ValueError as e:
                print(f"Invalid enum value in AI response: {e}")
                return None
            
            return CoverageAnalysis(
                function_name=function_name,
                coverage_percentage=int(data['coverage_percentage']),
                coverage_gaps=data['coverage_gaps'],
                existing_tests_quality=data['existing_tests_quality'],
                recommendation=recommendation,
                missing_scenarios=data['missing_scenarios'],
                priority=priority,
                reasoning=data['reasoning'],
                estimated_effort=data.get('estimated_effort', 'medium')
            )
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response as JSON: {e}")
            print(f"Response text: {response_text[:500]}...")
            return None
        except Exception as e:
            print(f"Error parsing coverage analysis: {e}")
            return None
    
    def analyze_multiple_functions(
        self, 
        functions_with_tests: List[Dict]
    ) -> List[CoverageAnalysis]:
        """Analyze coverage for multiple functions."""
        results = []
        
        for func_data in functions_with_tests:
            analysis = self.analyze_function_coverage(
                function_code=func_data.get('function_code', ''),
                function_name=func_data.get('function_name', ''),
                existing_tests=func_data.get('existing_tests'),
                language=func_data.get('language', 'c')
            )
            
            if analysis:
                results.append(analysis)
        
        return results