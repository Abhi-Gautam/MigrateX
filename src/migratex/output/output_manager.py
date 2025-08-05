"""Output directory management for MigrateX analysis results."""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import asdict

from ..analysis.test_decision_engine import TestDecision
from ..analysis.coverage_analyzer import CoverageAnalysis


class OutputManager:
    """Manages organized output directory structure for analysis results."""
    
    def __init__(self, base_output_dir: str = "migratex_output"):
        self.base_output_dir = Path(base_output_dir)
        self.current_session_dir: Optional[Path] = None
    
    def create_session_directory(self, repository_name: str) -> Path:
        """Create a new session directory for analysis results."""
        
        # Create base directory if it doesn't exist
        self.base_output_dir.mkdir(exist_ok=True)
        
        # Create session directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"{repository_name}_{timestamp}"
        self.current_session_dir = self.base_output_dir / session_name
        
        # Create directory structure
        self.current_session_dir.mkdir(exist_ok=True)
        (self.current_session_dir / "analysis").mkdir(exist_ok=True)
        (self.current_session_dir / "generated_tests").mkdir(exist_ok=True)
        (self.current_session_dir / "reports").mkdir(exist_ok=True)
        (self.current_session_dir / "source_functions").mkdir(exist_ok=True)
        
        return self.current_session_dir
    
    def save_analysis_results(
        self, 
        decisions: List[TestDecision],
        repository_path: str,
        settings: Dict
    ) -> None:
        """Save comprehensive analysis results."""
        
        if not self.current_session_dir:
            raise ValueError("No session directory created. Call create_session_directory first.")
        
        # Save main analysis results
        analysis_data = {
            "repository_path": repository_path,
            "analysis_timestamp": datetime.now().isoformat(),
            "settings": settings,
            "summary": self._create_analysis_summary(decisions),
            "decisions": []
        }
        
        # Process each decision
        for decision in decisions:
            decision_data = {
                "function_name": decision.function_name,
                "decision": decision.decision,
                "reason": decision.reason,
                "generation_success": decision.generation_success,
                "coverage_analysis": None,
                "existing_tests_found": decision.existing_tests is not None
            }
            
            # Add coverage analysis if available
            if decision.coverage_analysis:
                decision_data["coverage_analysis"] = {
                    "coverage_percentage": decision.coverage_analysis.coverage_percentage,
                    "coverage_gaps": decision.coverage_analysis.coverage_gaps,
                    "existing_tests_quality": decision.coverage_analysis.existing_tests_quality,
                    "recommendation": decision.coverage_analysis.recommendation.value,
                    "missing_scenarios": decision.coverage_analysis.missing_scenarios,
                    "priority": decision.coverage_analysis.priority.value,
                    "reasoning": decision.coverage_analysis.reasoning,
                    "estimated_effort": decision.coverage_analysis.estimated_effort
                }
            
            analysis_data["decisions"].append(decision_data)
        
        # Save analysis results
        analysis_file = self.current_session_dir / "analysis" / "results.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
    
    def save_generated_tests(self, decisions: List[TestDecision]) -> None:
        """Save generated tests to individual files."""
        
        if not self.current_session_dir:
            raise ValueError("No session directory created.")
        
        tests_dir = self.current_session_dir / "generated_tests"
        
        for decision in decisions:
            if decision.generated_tests and decision.generation_success:
                # Create test file
                test_filename = f"test_{decision.function_name}.c"
                test_file = tests_dir / test_filename
                
                with open(test_file, 'w') as f:
                    f.write(f"// Generated test for function: {decision.function_name}\n")
                    f.write(f"// Generation timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"// AI Decision: {decision.decision} - {decision.reason}\n\n")
                    f.write(decision.generated_tests)
    
    def save_source_functions(self, functions: List[Dict]) -> None:
        """Save extracted source functions for reference."""
        
        if not self.current_session_dir:
            raise ValueError("No session directory created.")
        
        functions_dir = self.current_session_dir / "source_functions"
        
        for func in functions:
            func_filename = f"{func['name']}.c"
            func_file = functions_dir / func_filename
            
            with open(func_file, 'w') as f:
                f.write(f"// Extracted function: {func['name']}\n")
                f.write(f"// Original file: {func.get('file_path', 'unknown')}\n")
                f.write(f"// Language: {func.get('language', 'c')}\n\n")
                f.write(func['content'])
    
    def generate_html_report(self, decisions: List[TestDecision], repository_path: str) -> Path:
        """Generate comprehensive HTML report."""
        
        if not self.current_session_dir:
            raise ValueError("No session directory created.")
        
        report_file = self.current_session_dir / "reports" / "analysis_report.html"
        
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MigrateX Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        .summary {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .function {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .coverage {{ display: inline-block; padding: 5px 10px; border-radius: 15px; color: white; font-weight: bold; }}
        .coverage.high {{ background-color: #4CAF50; }}
        .coverage.medium {{ background-color: #FF9800; }}
        .coverage.low {{ background-color: #F44336; }}
        .decision {{ display: inline-block; padding: 5px 10px; border-radius: 15px; color: white; font-weight: bold; }}
        .decision.skip {{ background-color: #9E9E9E; }}
        .decision.generate {{ background-color: #2196F3; }}
        .priority {{ display: inline-block; padding: 3px 8px; border-radius: 10px; color: white; font-size: 12px; }}
        .priority.high {{ background-color: #F44336; }}
        .priority.medium {{ background-color: #FF9800; }}
        .priority.low {{ background-color: #4CAF50; }}
        .test-preview {{ background-color: #f8f8f8; padding: 15px; border-radius: 5px; border-left: 4px solid #2196F3; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
        .stats {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .stat {{ background: white; padding: 15px; border-radius: 10px; text-align: center; min-width: 150px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 MigrateX Analysis Report</h1>
        <p><strong>Repository:</strong> {repository_path}</p>
        <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Functions Analyzed:</strong> {len(decisions)}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Analysis Summary</h2>
        <div class="stats">
            {self._generate_html_stats(decisions)}
        </div>
    </div>
    
    <h2>🔍 Function Analysis Details</h2>
    {self._generate_html_functions(decisions)}
    
</body>
</html>
        """
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        return report_file
    
    def generate_makefile(self, decisions: List[TestDecision]) -> Path:
        """Generate Makefile for compiling and running tests."""
        
        if not self.current_session_dir:
            raise ValueError("No session directory created.")
        
        makefile_path = self.current_session_dir / "Makefile"
        
        # Get list of generated test files
        generated_tests = [
            f"test_{d.function_name}" for d in decisions 
            if d.generated_tests and d.generation_success
        ]
        
        makefile_content = f"""# Generated Makefile for MigrateX tests
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -g
TEST_DIR = generated_tests
SRC_DIR = source_functions

# Test executables
TESTS = {' '.join(generated_tests)}

# Default target
all: $(TESTS)

# Pattern rule for building tests
test_%: $(TEST_DIR)/test_%.c
\t$(CC) $(CFLAGS) -o $@ $<

# Run all tests
test: $(TESTS)
\t@echo "Running all tests..."
\t@for test in $(TESTS); do \\
\t\techo "Running $$test..."; \\
\t\t./$$test || echo "$$test FAILED"; \\
\tdone

# Clean build artifacts
clean:
\trm -f $(TESTS)

# Install dependencies (if needed)
install-deps:
\t@echo "Installing test dependencies..."
\t@echo "No additional dependencies required for basic C tests"

.PHONY: all test clean install-deps

# Individual test targets:
"""
        
        for decision in decisions:
            if decision.generated_tests and decision.generation_success:
                makefile_content += f"""
test_{decision.function_name}: $(TEST_DIR)/test_{decision.function_name}.c
\t$(CC) $(CFLAGS) -o test_{decision.function_name} $(TEST_DIR)/test_{decision.function_name}.c

"""
        
        with open(makefile_path, 'w') as f:
            f.write(makefile_content)
        
        return makefile_path
    
    def create_readme(self, repository_path: str, decisions: List[TestDecision]) -> Path:
        """Create README for the output directory."""
        
        if not self.current_session_dir:
            raise ValueError("No session directory created.")
        
        readme_path = self.current_session_dir / "README.md"
        
        readme_content = f"""# MigrateX Analysis Results

## Overview

This directory contains the complete analysis results from MigrateX AI-powered code analysis.

**Repository Analyzed:** `{repository_path}`  
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Functions Analyzed:** {len(decisions)}

## Directory Structure

```
{self.current_session_dir.name}/
├── analysis/           # Analysis results and metadata
│   └── results.json   # Complete analysis data in JSON format
├── generated_tests/   # AI-generated test files
├── source_functions/  # Extracted source functions
├── reports/           # HTML and other reports
│   └── analysis_report.html
├── Makefile          # Build configuration for tests
└── README.md         # This file
```

## Quick Start

### View Analysis Results

1. **HTML Report**: Open `reports/analysis_report.html` in your browser for a comprehensive visual report
2. **JSON Data**: Check `analysis/results.json` for complete analysis data in machine-readable format

### Run Generated Tests

```bash
# Build all tests
make all

# Run all tests
make test

# Build and run a specific test
make test_functionName
./test_functionName

# Clean build artifacts
make clean
```

## Analysis Summary

{self._create_markdown_summary(decisions)}

## Generated Test Files

The following test files were generated based on AI coverage analysis:

"""
        
        for decision in decisions:
            if decision.generated_tests and decision.generation_success:
                readme_content += f"- `generated_tests/test_{decision.function_name}.c` - Tests for `{decision.function_name}()` function\n"
        
        readme_content += f"""

## Coverage Analysis Results

| Function | Coverage | Quality | Decision | Priority | AI Reasoning |
|----------|----------|---------|----------|----------|--------------|
"""
        
        for decision in decisions:
            coverage = "N/A"
            quality = "N/A"
            priority = "N/A"
            reasoning = decision.reason[:50] + "..." if len(decision.reason) > 50 else decision.reason
            
            if decision.coverage_analysis:
                coverage = f"{decision.coverage_analysis.coverage_percentage}%"
                quality = decision.coverage_analysis.existing_tests_quality
                priority = decision.coverage_analysis.priority.value
                reasoning = decision.coverage_analysis.reasoning[:50] + "..." if len(decision.coverage_analysis.reasoning) > 50 else decision.coverage_analysis.reasoning
            
            readme_content += f"| {decision.function_name} | {coverage} | {quality} | {decision.decision} | {priority} | {reasoning} |\n"
        
        readme_content += f"""

## About MigrateX

MigrateX is an AI-powered code analysis and translation tool that provides:

- **Intelligent Coverage Analysis**: Uses AI to evaluate test coverage and quality
- **Smart Test Generation**: Generates tests only when needed based on coverage gaps
- **Real-time Progress Tracking**: Live visualization of analysis progress
- **Comprehensive Reporting**: Detailed HTML and JSON reports

For more information, visit the MigrateX documentation.

---
*Generated by MigrateX v1.0 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        return readme_path
    
    def _create_analysis_summary(self, decisions: List[TestDecision]) -> Dict:
        """Create analysis summary statistics."""
        
        total = len(decisions)
        completed = sum(1 for d in decisions if d.coverage_analysis is not None)
        skipped = sum(1 for d in decisions if d.decision == "skip")
        generated = sum(1 for d in decisions if d.decision == "generate")
        successful_generations = sum(1 for d in decisions if d.generation_success)
        
        coverage_analyses = [d.coverage_analysis for d in decisions if d.coverage_analysis]
        avg_coverage = sum(ca.coverage_percentage for ca in coverage_analyses) / len(coverage_analyses) if coverage_analyses else 0
        
        return {
            "total_functions": total,
            "completed_analyses": completed,
            "skipped_generation": skipped,
            "generated_tests": generated,
            "successful_generations": successful_generations,
            "failed_generations": generated - successful_generations,
            "average_coverage": round(avg_coverage, 1),
            "generation_success_rate": round((successful_generations / generated) * 100, 1) if generated > 0 else 0
        }
    
    def _generate_html_stats(self, decisions: List[TestDecision]) -> str:
        """Generate HTML stats section."""
        
        summary = self._create_analysis_summary(decisions)
        
        return f"""
            <div class="stat">
                <div class="stat-value">{summary['total_functions']}</div>
                <div class="stat-label">Functions Analyzed</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary['average_coverage']}%</div>
                <div class="stat-label">Average Coverage</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary['successful_generations']}</div>
                <div class="stat-label">Tests Generated</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary['generation_success_rate']}%</div>
                <div class="stat-label">Generation Success</div>
            </div>
        """
    
    def _generate_html_functions(self, decisions: List[TestDecision]) -> str:
        """Generate HTML for function details."""
        
        html = ""
        
        for i, decision in enumerate(decisions, 1):
            coverage_class = "low"
            coverage_text = "N/A"
            
            if decision.coverage_analysis:
                coverage = decision.coverage_analysis.coverage_percentage
                coverage_text = f"{coverage}%"
                if coverage >= 80:
                    coverage_class = "high"
                elif coverage >= 50:
                    coverage_class = "medium"
                else:
                    coverage_class = "low"
            
            decision_class = decision.decision
            priority_class = decision.coverage_analysis.priority.value if decision.coverage_analysis else "medium"
            
            test_preview = ""
            if decision.generated_tests:
                test_lines = decision.generated_tests.split('\n')[:10]
                test_preview = f'<div class="test-preview">{"<br>".join(test_lines)}{"<br>..." if len(decision.generated_tests.split()) > 10 else ""}</div>'
            
            html += f"""
            <div class="function">
                <h3>📋 Function {i}: {decision.function_name}</h3>
                
                <p><strong>Coverage:</strong> <span class="coverage {coverage_class}">{coverage_text}</span></p>
                <p><strong>Decision:</strong> <span class="decision {decision_class}">{decision.decision.upper()}</span></p>
                {f'<p><strong>Priority:</strong> <span class="priority {priority_class}">{priority_class.upper()}</span></p>' if decision.coverage_analysis else ''}
                
                <p><strong>AI Reasoning:</strong> {decision.reason}</p>
                
                {f'<p><strong>Coverage Gaps:</strong> {", ".join(decision.coverage_analysis.coverage_gaps)}</p>' if decision.coverage_analysis and decision.coverage_analysis.coverage_gaps else ''}
                
                {f"<h4>Generated Test Preview:</h4>{test_preview}" if decision.generated_tests else ""}
            </div>
            """
        
        return html
    
    def _create_markdown_summary(self, decisions: List[TestDecision]) -> str:
        """Create markdown summary for README."""
        
        summary = self._create_analysis_summary(decisions)
        
        return f"""
- **Total Functions:** {summary['total_functions']}
- **Completed Analyses:** {summary['completed_analyses']}
- **Average Coverage:** {summary['average_coverage']}%
- **Tests Generated:** {summary['successful_generations']}
- **Generation Success Rate:** {summary['generation_success_rate']}%
"""