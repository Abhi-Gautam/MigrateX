"""Core LLM-powered translation engine for semantic modules."""

import json
import os
import re
import time
from typing import Optional, List, Dict, Any
import logging

import google.generativeai as genai

from ..analysis.module_analyzer import SemanticModule
from .models import (
    TranslationResult, TranslationContext, TranslationStatus, 
    TranslationLanguage, BatchTranslationResult
)

logger = logging.getLogger(__name__)


class TranslationEngine:
    """LLM-powered engine for translating semantic modules between programming languages."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp"):
        """Initialize the translation engine.
        
        Args:
            api_key: Google API key for Gemini (defaults to environment variable)
            model_name: Name of the Gemini model to use
        """
        # Translation configuration - set first
        self.max_retries = 3
        self.temperature = 0.1  # Low temperature for consistent code generation
        self.timeout_seconds = 60
        
        # Model initialization
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = model_name
        self.model = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the Gemini model."""
        try:
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    self.model_name,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=8192
                    )
                )
                logger.info(f"Initialized {self.model_name} for translation")
            else:
                logger.warning("No API key provided - translation will not work")
        except Exception as e:
            logger.error(f"Failed to initialize translation model: {e}")
            self.model = None
    
    def translate_module(
        self, 
        module: SemanticModule,
        target_language: TranslationLanguage,
        context: Optional[TranslationContext] = None
    ) -> TranslationResult:
        """Translate a semantic module to a target language.
        
        Args:
            module: The semantic module to translate
            target_language: Target programming language
            context: Additional context for translation decisions
            
        Returns:
            TranslationResult with the translated code and metadata
        """
        start_time = time.time()
        
        # Create result object
        result = TranslationResult(
            source_module_name=module.name,
            target_module_name=self._generate_target_module_name(module.name, target_language),
            source_language="c",  # Assuming C for now
            target_language=target_language,
            status=TranslationStatus.IN_PROGRESS
        )
        
        if not self.model:
            result.add_error("configuration", "Translation model not initialized - check API key")
            result.status = TranslationStatus.FAILED
            return result
        
        try:
            # Build translation context
            if not context:
                context = self._build_default_context(module, target_language)
            
            # Generate translation prompt
            prompt = self._construct_translation_prompt(module, target_language, context)
            
            # Perform translation with retries
            translation_response = self._translate_with_retries(prompt)
            
            if translation_response:
                # Parse and validate response
                self._parse_translation_response(translation_response, result, module)
                
                # Set success status if no errors
                if not result.has_errors:
                    result.status = TranslationStatus.COMPLETED
                    result.confidence_score = self._calculate_confidence_score(result)
                else:
                    result.status = TranslationStatus.PARTIAL
            else:
                result.add_error("llm", "Failed to get translation response from LLM")
                result.status = TranslationStatus.FAILED
                
        except Exception as e:
            logger.error(f"Translation failed for module {module.name}: {e}")
            result.add_error("system", f"Translation system error: {str(e)}")
            result.status = TranslationStatus.FAILED
        
        # Record timing
        result.translation_time = time.time() - start_time
        
        logger.info(f"Translation completed for {module.name} -> {result.target_module_name} "
                   f"(status: {result.status.value}, time: {result.translation_time:.2f}s)")
        
        return result
    
    def translate_batch(
        self,
        modules: List[SemanticModule],
        target_language: TranslationLanguage,
        project_name: str = "translated_project"
    ) -> BatchTranslationResult:
        """Translate multiple modules as a cohesive project.
        
        Args:
            modules: List of semantic modules to translate
            target_language: Target programming language
            project_name: Name for the translated project
            
        Returns:
            BatchTranslationResult with all translation results and project structure
        """
        logger.info(f"Starting batch translation of {len(modules)} modules to {target_language.value}")
        
        batch_result = BatchTranslationResult(
            project_name=project_name,
            source_language="c",
            target_language=target_language
        )
        
        # Analyze module dependencies for translation order
        translation_order = self._determine_translation_order(modules)
        
        # Translate modules in dependency order
        for module in translation_order:
            logger.info(f"Translating module: {module.name}")
            
            # Build context with already translated modules
            context = self._build_batch_context(module, target_language, batch_result)
            
            # Translate individual module
            module_result = self.translate_module(module, target_language, context)
            batch_result.add_module_result(module_result)
            
            # Generate progress feedback
            progress = (len(batch_result.module_results) / len(modules)) * 100
            logger.info(f"Batch progress: {progress:.1f}% ({batch_result.successful_modules} successful, "
                       f"{batch_result.failed_modules} failed)")
        
        # Generate project-level outputs
        self._generate_project_structure(batch_result)
        self._generate_build_files(batch_result)
        self._generate_migration_documentation(batch_result)
        
        logger.info(f"Batch translation completed: {batch_result.success_rate:.1f}% success rate")
        return batch_result
    
    def _construct_translation_prompt(
        self, 
        module: SemanticModule, 
        target_language: TranslationLanguage,
        context: TranslationContext
    ) -> str:
        """Construct a comprehensive translation prompt for the LLM."""
        
        # Build function details
        functions_section = ""
        for i, func in enumerate(module.functions, 1):
            functions_section += f"\\n### Function {i}: {func.name}\\n"
            functions_section += f"```c\\n{func.source_code}\\n```\\n"
            if func.dependencies:
                functions_section += f"Dependencies: {', '.join(func.dependencies)}\\n"
        
        # Build context information
        context_section = f"""
MODULE CONTEXT:
- Module Name: {module.name}
- Module Type: {module.module_type}
- Description: {module.description}
- Self-contained: {'Yes' if module.is_self_contained else 'No'}
- Internal Dependencies: {', '.join(module.internal_dependencies) if module.internal_dependencies else 'None'}
- External Dependencies: {', '.join(module.external_dependencies) if module.external_dependencies else 'None'}
- Complexity Score: {module.complexity_score}
"""
        
        # Language-specific guidance
        target_guidance = self._get_language_specific_guidance(target_language)
        
        return f"""
You are an expert software engineer specializing in automated code translation. You must translate a complete C module to {target_language.value.title()} while preserving semantic meaning and functionality.

{context_section}

SOURCE MODULE FUNCTIONS:
{functions_section}

EXISTING TESTS (for reference):
```c
{context.existing_tests or 'No existing tests available'}
```

{target_guidance}

TRANSLATION REQUIREMENTS:

1. **Semantic Preservation**: Maintain the exact same behavior and functionality
2. **Idiomatic Code**: Write natural, idiomatic {target_language.value.title()} code
3. **Memory Safety**: Leverage {target_language.value.title()}'s memory safety features appropriately
4. **Error Handling**: Implement proper error handling for the target language
5. **Performance**: Maintain or improve performance characteristics
6. **API Consistency**: Keep similar function signatures where possible
7. **Documentation**: Include comprehensive documentation and comments

RESPONSE FORMAT:
Provide your translation as a JSON object with this EXACT structure:

{{
    "translated_code": "// Complete {target_language.value.title()} module code here",
    "translated_tests": "// Complete {target_language.value.title()} test code here",
    "build_configuration": {{
        "dependencies": ["dep1", "dep2"],
        "build_features": ["feature1"],
        "compiler_flags": ["-flag1"]
    }},
    "translation_notes": [
        "Note about translation decision 1",
        "Note about translation decision 2"
    ],
    "semantic_changes": [
        "Change in behavior or API if any"
    ],
    "api_changes": [
        "Changes to function signatures or interfaces"
    ],
    "performance_notes": [
        "Performance implications of translation"
    ],
    "confidence_score": 85,
    "ai_reasoning": "Detailed explanation of translation approach and key decisions",
    "alternative_approaches": [
        "Alternative approach 1 that was considered",
        "Alternative approach 2 that was considered"
    ]
}}

CRITICAL GUIDELINES:
- Translate ALL functions in the module
- Ensure the translated code compiles and runs correctly
- Preserve all original functionality and edge cases
- Use appropriate {target_language.value.title()} idioms and patterns
- Include comprehensive error handling
- Add clear documentation for complex translations
- Consider memory management and ownership carefully
- Maintain or improve performance characteristics

CRITICAL: Your response must be ONLY valid JSON, nothing else. No markdown code blocks, no explanations, no additional text. Just pure JSON starting with {{ and ending with }}.

Example format:
{{
    "translated_code": "// Rust code here",
    "translated_tests": "// Rust tests here",
    "build_configuration": {{"dependencies": ["serde"]}},
    "translation_notes": ["Note 1"],
    "semantic_changes": [],
    "api_changes": [],
    "performance_notes": [],
    "confidence_score": 85,
    "ai_reasoning": "Translation explanation",
    "alternative_approaches": []
}}
"""
    
    def _get_language_specific_guidance(self, target_language: TranslationLanguage) -> str:
        """Get language-specific translation guidance."""
        
        guidance_map = {
            TranslationLanguage.RUST: """
RUST-SPECIFIC GUIDANCE:
- Use appropriate ownership (owned, borrowed, mutable) for each parameter
- Leverage Rust's type system for safety (Option<T>, Result<T, E>)
- Use Vec<T> for dynamic arrays, slices for array parameters
- Implement proper error handling with Result types
- Use structs for complex data types, enums for variants
- Consider lifetimes for borrowed data
- Use Rust naming conventions (snake_case for variables/functions)
- Add #[derive] attributes where appropriate
- Use std library collections (HashMap, BTreeMap, etc.) when suitable
- Implement proper Drop trait for resource cleanup if needed
""",
            
            TranslationLanguage.GO: """
GO-SPECIFIC GUIDANCE:
- Use Go naming conventions (camelCase for private, PascalCase for public)
- Implement proper error handling with error return values
- Use slices for dynamic arrays, arrays for fixed-size
- Use structs for complex data types, interfaces for abstractions
- Implement proper resource cleanup with defer statements
- Use Go's built-in types (map, slice, channel) appropriately
- Consider goroutines for concurrent operations if applicable
- Use packages properly for module organization
- Implement String() methods for custom types
- Use context.Context for cancellation and timeouts where needed
""",
            
            TranslationLanguage.PYTHON: """
PYTHON-SPECIFIC GUIDANCE:
- Use Python naming conventions (snake_case for functions/variables)
- Leverage Python's type hints for better code documentation
- Use appropriate Python data structures (list, dict, set, tuple)
- Implement proper exception handling with try/except
- Use classes for complex data types, dataclasses for simple ones
- Leverage Python standard library (collections, itertools, etc.)
- Use context managers (with statements) for resource management
- Follow PEP 8 style guidelines
- Add docstrings for all functions and classes
- Consider using ABC (Abstract Base Classes) for interfaces
"""
        }
        
        return guidance_map.get(target_language, "")
    
    def _translate_with_retries(self, prompt: str) -> Optional[str]:
        """Perform translation with retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Translation attempt {attempt + 1}/{self.max_retries}")
                
                response = self.model.generate_content(prompt)
                
                if response and response.text:
                    return response.text
                else:
                    logger.warning(f"Empty response on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"All translation attempts failed")
                    return None
                
                # Wait before retry
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _parse_translation_response(
        self, 
        response_text: str, 
        result: TranslationResult,
        module: SemanticModule
    ):
        """Parse the LLM translation response and populate the result."""
        try:
            # Log response for debugging
            logger.debug(f"Raw LLM response (first 500 chars): {response_text[:500]}")
            
            # Try multiple approaches to extract JSON
            json_str = None
            
            # Helper function to find balanced JSON
            def find_balanced_json(text):
                # Find first opening brace
                start = text.find('{')
                if start == -1:
                    return None
                
                # Count braces to find the matching closing brace
                brace_count = 0
                for i, char in enumerate(text[start:], start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return text[start:i+1]
                return None
            
            # Try to extract JSON using balanced brace matching
            json_str = find_balanced_json(response_text)
            
            if not json_str:
                # Fallback: Look for JSON within code blocks  
                code_block_match = re.search(r'```(?:json)?\\s*\\n?(\\{[^`]*\\})\\s*\\n?```', response_text, re.DOTALL)
                if code_block_match:
                    json_str = code_block_match.group(1)
            
            if not json_str:
                result.add_error("parsing", "No JSON found in LLM response")
                logger.error(f"Failed to find JSON in response: {response_text[:200]}...")
                return
            
            logger.debug(f"Extracted JSON (first 200 chars): {json_str[:200]}")
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['translated_code', 'ai_reasoning']
            for field in required_fields:
                if field not in data:
                    result.add_error("parsing", f"Missing required field '{field}' in response")
                    return
            
            # Populate result with parsed data
            result.translated_code = data.get('translated_code', '')
            result.translated_tests = data.get('translated_tests', '')
            result.build_configuration = data.get('build_configuration', {})
            result.translation_notes = data.get('translation_notes', [])
            result.semantic_changes = data.get('semantic_changes', [])
            result.api_changes = data.get('api_changes', [])
            result.performance_notes = data.get('performance_notes', [])
            result.confidence_score = float(data.get('confidence_score', 0))
            result.ai_reasoning = data.get('ai_reasoning', '')
            result.alternative_approaches = data.get('alternative_approaches', [])
            
            # Validate translated code quality
            self._validate_translation_quality(result, module)
            
        except json.JSONDecodeError as e:
            result.add_error("parsing", f"Failed to parse JSON response: {e}")
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Response text: {response_text[:1000]}...")
        except Exception as e:
            result.add_error("parsing", f"Error processing translation response: {e}")
            logger.error(f"Response processing error: {e}")
    
    def _validate_translation_quality(self, result: TranslationResult, module: SemanticModule):
        """Validate the quality of the translated code."""
        
        # Check if code is not empty
        if not result.translated_code.strip():
            result.add_error("quality", "Translated code is empty")
            return
        
        # Check if all original functions are present
        original_functions = {func.name for func in module.functions}
        translated_code = result.translated_code.lower()
        
        missing_functions = []
        for func_name in original_functions:
            # Simple heuristic - look for function name in translated code
            if func_name.lower() not in translated_code:
                missing_functions.append(func_name)
        
        if missing_functions:
            result.add_error("completeness", 
                           f"Missing functions in translation: {', '.join(missing_functions)}")
        
        # Check confidence score
        if result.confidence_score < 50:
            result.add_error("confidence", 
                           f"Low confidence score: {result.confidence_score}%",
                           suggestion="Review translation carefully before use")
    
    def _calculate_confidence_score(self, result: TranslationResult) -> float:
        """Calculate a confidence score for the translation."""
        base_score = result.confidence_score or 70.0
        
        # Adjust based on errors and warnings
        if result.has_errors:
            base_score -= len(result.errors) * 15
        
        if result.has_warnings:
            base_score -= len(result.warnings) * 5
        
        # Adjust based on completeness
        if not result.translated_code.strip():
            base_score = 0
        
        return max(0, min(100, base_score))
    
    def _generate_target_module_name(self, source_name: str, target_language: TranslationLanguage) -> str:
        """Generate appropriate target module name based on language conventions."""
        
        # Remove common C suffixes
        base_name = source_name.replace('_module', '').replace('Module', '')
        
        if target_language == TranslationLanguage.RUST:
            # Convert to snake_case
            return re.sub(r'([A-Z])', r'_\\1', base_name).lower().strip('_')
        elif target_language == TranslationLanguage.GO:
            # Convert to PascalCase for public packages
            return ''.join(word.capitalize() for word in re.split(r'[_\\s]+', base_name))
        elif target_language == TranslationLanguage.PYTHON:
            # Convert to snake_case
            return re.sub(r'([A-Z])', r'_\\1', base_name).lower().strip('_')
        
        return base_name
    
    def _build_default_context(self, module: SemanticModule, target_language: TranslationLanguage) -> TranslationContext:
        """Build default translation context for a module."""
        return TranslationContext(
            source_language="c",
            target_language=target_language,
            module_type=module.module_type,
            dependencies=list(module.external_dependencies),
            architectural_patterns=self._infer_architectural_patterns(module)
        )
    
    def _infer_architectural_patterns(self, module: SemanticModule) -> List[str]:
        """Infer architectural patterns from the module structure."""
        patterns = []
        
        if module.module_type == "data_structure":
            patterns.append("data_structure")
        elif module.module_type == "algorithm":
            patterns.append("algorithmic")
        elif "buffer" in module.name.lower():
            patterns.append("buffer_management")
        elif any("get" in func.name.lower() for func in module.functions):
            patterns.append("accessor_pattern")
        
        return patterns
    
    def _determine_translation_order(self, modules: List[SemanticModule]) -> List[SemanticModule]:
        """Determine optimal order for translating modules based on dependencies."""
        # Simple topological sort based on dependencies
        # For now, just prioritize self-contained modules first
        
        self_contained = [m for m in modules if m.is_self_contained]
        dependent = [m for m in modules if not m.is_self_contained]
        
        return self_contained + dependent
    
    def _build_batch_context(
        self, 
        module: SemanticModule, 
        target_language: TranslationLanguage,
        batch_result: BatchTranslationResult
    ) -> TranslationContext:
        """Build context for batch translation including previously translated modules."""
        
        context = self._build_default_context(module, target_language)
        
        # Add information about already translated modules
        successful_translations = batch_result.get_successful_results()
        if successful_translations:
            context.architectural_patterns.extend([
                f"follows_pattern_from_{result.source_module_name}" 
                for result in successful_translations
            ])
        
        return context
    
    def _generate_project_structure(self, batch_result: BatchTranslationResult):
        """Generate project directory structure for the translated project."""
        
        target_lang = batch_result.target_language
        
        if target_lang == TranslationLanguage.RUST:
            batch_result.project_structure = {
                "src/lib.rs": self._generate_rust_lib_file(batch_result),
                "src/main.rs": self._generate_rust_main_file(batch_result),
                **{f"src/{result.target_module_name}.rs": result.translated_code 
                   for result in batch_result.get_successful_results()}
            }
        elif target_lang == TranslationLanguage.GO:
            batch_result.project_structure = {
                "main.go": self._generate_go_main_file(batch_result),
                **{f"{result.target_module_name}.go": result.translated_code 
                   for result in batch_result.get_successful_results()}
            }
        elif target_lang == TranslationLanguage.PYTHON:
            batch_result.project_structure = {
                "__init__.py": "",
                "main.py": self._generate_python_main_file(batch_result),
                **{f"{result.target_module_name}.py": result.translated_code 
                   for result in batch_result.get_successful_results()}
            }
    
    def _generate_build_files(self, batch_result: BatchTranslationResult):
        """Generate build configuration files for the target language."""
        
        target_lang = batch_result.target_language
        
        if target_lang == TranslationLanguage.RUST:
            batch_result.build_files["Cargo.toml"] = self._generate_cargo_toml(batch_result)
        elif target_lang == TranslationLanguage.GO:
            batch_result.build_files["go.mod"] = self._generate_go_mod(batch_result)
        elif target_lang == TranslationLanguage.PYTHON:
            batch_result.build_files["setup.py"] = self._generate_setup_py(batch_result)
            batch_result.build_files["requirements.txt"] = self._generate_requirements_txt(batch_result)
    
    def _generate_migration_documentation(self, batch_result: BatchTranslationResult):
        """Generate documentation for the migration."""
        
        successful_results = batch_result.get_successful_results()
        failed_results = batch_result.get_failed_results()
        
        migration_guide = f"""
# Migration Guide: {batch_result.project_name}

## Translation Summary
- **Source Language**: {batch_result.source_language.upper()}
- **Target Language**: {batch_result.target_language.value.title()}
- **Success Rate**: {batch_result.success_rate:.1f}%
- **Modules Translated**: {len(successful_results)}/{batch_result.total_modules}

## Successfully Translated Modules

"""
        
        for result in successful_results:
            migration_guide += f"""
### {result.source_module_name} → {result.target_module_name}
- **Confidence**: {result.confidence_score:.1f}%
- **Translation Time**: {result.translation_time:.2f}s

**Key Changes:**
{chr(10).join(f"- {change}" for change in result.semantic_changes) if result.semantic_changes else "- No semantic changes"}

**Translation Notes:**
{chr(10).join(f"- {note}" for note in result.translation_notes) if result.translation_notes else "- No special notes"}

"""
        
        if failed_results:
            migration_guide += f"""
## Failed Translations

"""
            for result in failed_results:
                migration_guide += f"""
### {result.source_module_name} (FAILED)
**Errors:**
{chr(10).join(f"- {error.message}" for error in result.errors)}

"""
        
        migration_guide += f"""
## Build Instructions

1. Navigate to the project directory
2. Follow the build instructions for {batch_result.target_language.value.title()}
3. Run tests to verify functionality
4. Review any failed translations and manual fixes needed

## Next Steps

1. Review all translation notes and warnings
2. Run comprehensive tests
3. Performance benchmark against original
4. Manual review of complex translations
5. Integration testing

---
*Generated by MigrateX Translation Engine*
"""
        
        batch_result.migration_guide = migration_guide.strip()
    
    # Helper methods for generating language-specific files
    def _generate_rust_lib_file(self, batch_result: BatchTranslationResult) -> str:
        successful_results = batch_result.get_successful_results()
        modules = [f"pub mod {result.target_module_name};" for result in successful_results]
        return "\\n".join(modules)
    
    def _generate_rust_main_file(self, batch_result: BatchTranslationResult) -> str:
        return f'''fn main() {{
    println!("Hello from {batch_result.project_name}!");
    // Add your main logic here
}}'''
    
    def _generate_cargo_toml(self, batch_result: BatchTranslationResult) -> str:
        return f'''[package]
name = "{batch_result.project_name.lower().replace(' ', '_')}"
version = "0.1.0"
edition = "2021"

[dependencies]
# Add dependencies as needed
'''
    
    def _generate_go_main_file(self, batch_result: BatchTranslationResult) -> str:
        return f'''package main

import "fmt"

func main() {{
    fmt.Println("Hello from {batch_result.project_name}!")
    // Add your main logic here
}}'''
    
    def _generate_go_mod(self, batch_result: BatchTranslationResult) -> str:
        module_name = batch_result.project_name.lower().replace(' ', '_')
        return f'''module {module_name}

go 1.19
'''
    
    def _generate_python_main_file(self, batch_result: BatchTranslationResult) -> str:
        return f'''"""Main entry point for {batch_result.project_name}."""

def main():
    print("Hello from {batch_result.project_name}!")
    # Add your main logic here

if __name__ == "__main__":
    main()
'''
    
    def _generate_setup_py(self, batch_result: BatchTranslationResult) -> str:
        project_name = batch_result.project_name.lower().replace(' ', '_')
        return f'''from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Add dependencies as needed
    ],
)
'''
    
    def _generate_requirements_txt(self, batch_result: BatchTranslationResult) -> str:
        return "# Add Python dependencies here\\n"