"""AI-powered module-level test coverage analysis using Gemini."""

import json
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

import google.generativeai as genai

from .module_analyzer import SemanticModule


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
class ModuleCoverageAnalysis:
    """Results from AI module coverage analysis."""
    module_name: str
    module_type: str
    coverage_percentage: int
    function_coverage: Dict[str, int]  # Per-function coverage within module
    coverage_gaps: List[str]
    existing_tests_quality: str
    recommendation: CoverageRecommendation
    missing_scenarios: List[str]
    priority: TestPriority
    reasoning: str
    integration_tests_needed: bool = False
    estimated_effort: str = "medium"
    complexity_assessment: str = "medium"


class ModuleCoverageAnalyzer:
    """AI-powered module-level test coverage analyzer using Gemini."""
    
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
    
    def analyze_module_coverage(
        self, 
        module: SemanticModule,
        existing_tests: Optional[str] = None,
        language: str = "c"
    ) -> Optional[ModuleCoverageAnalysis]:
        """Analyze test coverage for a complete module using AI."""
        
        if not self.model:
            return None
        
        try:
            prompt = self._construct_module_coverage_prompt(
                module, existing_tests, language
            )
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return self._parse_module_coverage_response(response.text, module)
            
        except Exception as e:
            print(f"Error analyzing coverage for module {module.name}: {e}")
            return None
        
        return None
    
    def _construct_module_coverage_prompt(
        self, 
        module: SemanticModule,
        existing_tests: Optional[str],
        language: str
    ) -> str:
        """Construct a comprehensive module coverage analysis prompt."""
        
        existing_tests_section = existing_tests if existing_tests else "None - No existing tests found for this module"
        
        # Build function list with code
        functions_section = ""
        for i, func in enumerate(module.functions, 1):
            functions_section += f"\n### Function {i}: {func.name}\n"
            functions_section += f"```{language}\n{func.source_code}\n```\n"
        
        # Build dependency information
        deps_section = ""
        if module.internal_dependencies:
            deps_section += f"Internal Dependencies: {', '.join(module.internal_dependencies)}\n"
        if module.external_dependencies:
            deps_section += f"External Dependencies: {', '.join(module.external_dependencies)}\n"
        
        return f"""
You are an expert software testing engineer analyzing a complete code module for test coverage. This is not just a single function, but a cohesive module containing multiple related functions that work together.

MODULE TO ANALYZE:
Module Name: {module.name}
Module Type: {module.module_type}
Description: {module.description}
Self-contained: {'Yes' if module.is_self_contained else 'No'}
Complexity Score: {module.complexity_score}

{deps_section}

MODULE FUNCTIONS:
{functions_section}

EXISTING TESTS:
```{language}
{existing_tests_section}
```

Please analyze this complete module and provide a comprehensive assessment in this EXACT JSON format:

{{
    "coverage_percentage": <0-100 integer for overall module coverage>,
    "function_coverage": {{
        "{module.functions[0].name if module.functions else 'unknown'}": <0-100 integer>,
        {', '.join(f'"{func.name}": <0-100 integer>' for func in module.functions[1:]) if len(module.functions) > 1 else ''}
    }},
    "coverage_gaps": ["gap1", "gap2", ...],
    "existing_tests_quality": "excellent/good/fair/poor/none",
    "recommendation": "sufficient/generate_new/generate_additional/enhance_existing",
    "missing_scenarios": [
        "Specific test scenario 1",
        "Specific test scenario 2",
        "..."
    ],
    "priority": "high/medium/low",
    "reasoning": "Detailed explanation of your module-level analysis and recommendation",
    "integration_tests_needed": true/false,
    "estimated_effort": "low/medium/high",
    "complexity_assessment": "simple/medium/complex/very_complex"
}}

MODULE-LEVEL ANALYSIS GUIDELINES:

1. **Module-Level Coverage**: Consider how the functions work together as a complete feature
2. **Inter-Function Dependencies**: Analyze how functions call each other within the module
3. **Integration Testing**: Assess if the module needs integration tests beyond unit tests
4. **End-to-End Scenarios**: Consider complete workflows that span multiple functions
5. **Module API Testing**: Test the module's external interface and contracts
6. **State Management**: If the module manages state, ensure state transitions are tested
7. **Error Propagation**: Test how errors are handled across function boundaries
8. **Resource Management**: Test resource allocation/deallocation across the module

ANALYSIS PRIORITIES:
- **HIGH**: Complex modules with multiple functions, state management, or external dependencies
- **MEDIUM**: Moderate complexity modules with some inter-function dependencies  
- **LOW**: Simple modules with independent functions or well-tested functionality

COVERAGE ASSESSMENT:
- Consider all execution paths across all functions in the module
- Evaluate integration points between functions
- Assess boundary conditions for the entire module's functionality
- Consider error conditions that might affect multiple functions
- Evaluate the module's contracts and API surface

RECOMMENDATION LOGIC:
- **sufficient**: Module coverage ≥ 85% with good integration tests
- **generate_additional**: Good unit tests exist but missing integration/workflow tests
- **enhance_existing**: Tests exist but poor quality or missing critical scenarios
- **generate_new**: No tests or very poor coverage across the module

Focus on practical test scenarios that validate the module as a cohesive unit, not just individual functions.

Provide ONLY the JSON response, no additional text.
"""
    
    def _parse_module_coverage_response(self, response_text: str, module: SemanticModule) -> Optional[ModuleCoverageAnalysis]:
        """Parse the AI response into a ModuleCoverageAnalysis object."""
        try:
            # Extract JSON from response (handle cases where there might be extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                'coverage_percentage', 'function_coverage', 'coverage_gaps', 
                'existing_tests_quality', 'recommendation', 'missing_scenarios', 
                'priority', 'reasoning'
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
            
            # Validate function coverage
            function_coverage = data.get('function_coverage', {})
            if not isinstance(function_coverage, dict):
                function_coverage = {}
            
            return ModuleCoverageAnalysis(
                module_name=module.name,
                module_type=module.module_type,
                coverage_percentage=int(data['coverage_percentage']),
                function_coverage=function_coverage,
                coverage_gaps=data['coverage_gaps'],
                existing_tests_quality=data['existing_tests_quality'],
                recommendation=recommendation,
                missing_scenarios=data['missing_scenarios'],
                priority=priority,
                reasoning=data['reasoning'],
                integration_tests_needed=data.get('integration_tests_needed', False),
                estimated_effort=data.get('estimated_effort', 'medium'),
                complexity_assessment=data.get('complexity_assessment', 'medium')
            )
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response as JSON: {e}")
            print(f"Response text: {response_text[:500]}...")
            return None
        except Exception as e:
            print(f"Error parsing module coverage analysis: {e}")
            return None
    
    def analyze_multiple_modules(
        self, 
        modules_with_tests: List[Dict]
    ) -> List[ModuleCoverageAnalysis]:
        """Analyze coverage for multiple modules."""
        results = []
        
        for module_data in modules_with_tests:
            analysis = self.analyze_module_coverage(
                module=module_data.get('module'),
                existing_tests=module_data.get('existing_tests'),
                language=module_data.get('language', 'c')
            )
            
            if analysis:
                results.append(analysis)
        
        return results
    
    def get_module_test_recommendations(self, analysis: ModuleCoverageAnalysis) -> Dict:
        """Get specific test recommendations for a module."""
        
        recommendations = {
            "unit_tests": [],
            "integration_tests": [],
            "workflow_tests": [],
            "edge_case_tests": [],
            "performance_tests": []
        }
        
        # Based on coverage gaps and missing scenarios
        for gap in analysis.coverage_gaps:
            if "integration" in gap.lower() or "workflow" in gap.lower():
                recommendations["integration_tests"].append(gap)
            elif "performance" in gap.lower() or "load" in gap.lower():
                recommendations["performance_tests"].append(gap)
            elif "edge" in gap.lower() or "boundary" in gap.lower():
                recommendations["edge_case_tests"].append(gap)
            else:
                recommendations["unit_tests"].append(gap)
        
        for scenario in analysis.missing_scenarios:
            if "end-to-end" in scenario.lower() or "complete" in scenario.lower():
                recommendations["workflow_tests"].append(scenario)
            elif "integration" in scenario.lower():
                recommendations["integration_tests"].append(scenario)
            else:
                recommendations["unit_tests"].append(scenario)
        
        # Add integration tests if needed
        if analysis.integration_tests_needed:
            recommendations["integration_tests"].append(
                f"Integration tests for {analysis.module_name} module functions working together"
            )
        
        return recommendations
    
    def generate_module_test_summary(self, analyses: List[ModuleCoverageAnalysis]) -> Dict:
        """Generate summary statistics for multiple module analyses."""
        
        if not analyses:
            return {
                "total_modules": 0,
                "avg_coverage": 0,
                "recommendations": {},
                "priority_distribution": {},
                "quality_distribution": {}
            }
        
        total_coverage = sum(a.coverage_percentage for a in analyses)
        avg_coverage = total_coverage / len(analyses)
        
        # Recommendation distribution
        recommendations = {}
        for analysis in analyses:
            rec = analysis.recommendation.value
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        # Priority distribution
        priorities = {}
        for analysis in analyses:
            pri = analysis.priority.value
            priorities[pri] = priorities.get(pri, 0) + 1
        
        # Quality distribution
        qualities = {}
        for analysis in analyses:
            qual = analysis.existing_tests_quality
            qualities[qual] = qualities.get(qual, 0) + 1
        
        return {
            "total_modules": len(analyses),
            "avg_coverage": round(avg_coverage, 1),
            "recommendations": recommendations,
            "priority_distribution": priorities,
            "quality_distribution": qualities,
            "modules_needing_integration_tests": sum(1 for a in analyses if a.integration_tests_needed),
            "high_priority_modules": sum(1 for a in analyses if a.priority == TestPriority.HIGH)
        }