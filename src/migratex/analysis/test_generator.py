"""AI-powered test generation using Gemini API."""

import os
import re
from typing import Dict, List, Optional

import google.generativeai as genai


class TestGenerator:
    """Generates unit tests for source code functions using Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or environment variable
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = None
        self._initialize_model()
        
        # Language-specific test templates
        self.test_templates = {
            "c": {
                "imports": "#include <assert.h>\n#include \"{header}\"",
                "function_template": "void test_{function_name}() {{\n    {assertions}\n}}",
                "assertion_template": "assert({function_call});",
            },
            "python": {
                "imports": "import pytest\nfrom {module} import {function_name}",
                "function_template": "def test_{function_name}():\n    {assertions}",
                "assertion_template": "assert {function_call}",
            },
        }
    
    def _initialize_model(self):
        """Initialize the Gemini model."""
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception:
            # For testing or when no API key is available
            self.model = None
    
    def generate_test(self, source_function: Dict) -> Optional[Dict]:
        """Generate a unit test for a given source function."""
        if not self.model:
            return None
            
        try:
            prompt = self._construct_prompt(source_function)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                test_name = self._extract_test_name(response.text, source_function["language"])
                return {
                    "test_name": test_name,
                    "test_content": response.text.strip(),
                    "source_function": source_function["name"],
                    "language": source_function["language"],
                    "file": source_function.get("file", ""),
                }
            
        except Exception as e:
            print(f"Error generating test for {source_function['name']}: {e}")
            return None
        
        return None
    
    def generate_tests_batch(self, source_functions: List[Dict]) -> List[Dict]:
        """Generate tests for multiple functions in batch."""
        results = []
        
        for func in source_functions:
            test_result = self.generate_test(func)
            if test_result:
                results.append(test_result)
        
        return results
    
    def _construct_prompt(self, source_function: Dict) -> str:
        """Construct a prompt for test generation based on the source function."""
        language = source_function["language"]
        func_name = source_function["name"]
        func_content = source_function["content"]
        
        if language == "c":
            return f"""
Generate a comprehensive unit test for this C function:

```c
{func_content}
```

Requirements:
- Create a test function named 'test_{func_name}'
- Use assert() for all test cases
- Include edge cases (null values, boundary conditions, error cases)
- Test at least 3-5 different scenarios
- Include necessary header files (#include <assert.h>)
- Follow C testing conventions

Return only the test function code, no explanations.
"""
        
        elif language == "python":
            return f"""
Generate a comprehensive unit test for this Python function:

```python
{func_content}
```

Requirements:
- Create a test function named 'test_{func_name}'
- Use assert statements for all test cases
- Include edge cases (None values, empty inputs, boundary conditions)
- Test at least 3-5 different scenarios
- Follow pytest conventions
- Import necessary modules

Return only the test function code, no explanations.
"""
        
        else:
            return f"""
Generate a unit test for this {language} function:

{func_content}

Create a comprehensive test function that covers multiple scenarios including edge cases.
"""
    
    def _extract_test_name(self, test_content: str, language: str) -> str:
        """Extract the test function name from generated content."""
        if language == "c":
            # Look for 'void test_functionname('
            match = re.search(r'void\s+(test_\w+)\s*\(', test_content)
            if match:
                return match.group(1)
        
        elif language == "python":
            # Look for 'def test_functionname('
            match = re.search(r'def\s+(test_\w+)\s*\(', test_content)
            if match:
                return match.group(1)
        
        # Fallback: try to find any test function pattern
        match = re.search(r'(test_\w+)', test_content)
        if match:
            return match.group(1)
        
        return "test_unknown"