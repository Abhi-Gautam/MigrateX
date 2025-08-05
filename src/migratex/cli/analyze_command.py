"""Enhanced analyze command with real-time progress display."""

from pathlib import Path
from typing import List, Dict
from rich.console import Console

from ..analysis.language_parser import LanguageParser
from ..analysis.test_decision_engine import TestDecisionEngine
from .progress_display import ProgressDisplayManager
from ..output.output_manager import OutputManager


def run_enhanced_analysis(
    repository_path: str,
    max_functions: int = 5,
    coverage_threshold: int = 80,
    generate_tests: bool = True,
    save_output: bool = True
) -> None:
    """Run enhanced analysis with real-time progress display."""
    
    console = Console()
    repo_path = Path(repository_path)
    
    if not repo_path.exists():
        console.print(f"❌ [red]Repository path does not exist:[/red] {repository_path}")
        return
    
    console.print(f"🔍 [bold]Starting Enhanced MigrateX Analysis[/bold]")
    console.print(f"📂 Repository: {repository_path}")
    console.print(f"🎯 Max Functions: {max_functions}")
    console.print(f"📊 Coverage Threshold: {coverage_threshold}%")
    console.print(f"🤖 Generate Tests: {'Yes' if generate_tests else 'No'}")
    console.print()
    
    # Initialize components
    language_parser = LanguageParser()
    decision_engine = TestDecisionEngine(coverage_threshold=coverage_threshold)
    progress_manager = ProgressDisplayManager(console)
    output_manager = OutputManager() if save_output else None
    
    try:
        # Step 1: Extract functions
        console.print("🔍 [yellow]Step 1: Extracting functions...[/yellow]")
        functions = extract_functions_from_repository(repo_path, language_parser, max_functions)
        
        if not functions:
            console.print("❌ [red]No functions found in repository[/red]")
            return
        
        console.print(f"✅ [green]Found {len(functions)} functions[/green]")
        console.print()
        
        # Step 2: Initialize progress display
        console.print("🚀 [yellow]Step 2: Starting AI coverage analysis...[/yellow]")
        progress_manager.initialize_functions(functions)
        progress_manager.start_live_display()
        
        # Step 3: Run analysis with progress callbacks
        def progress_callback(func_name: str, status: str, coverage_analysis=None, decision=None, error_message=None):
            progress_manager.update_function_status(
                func_name, status, coverage_analysis, decision, error_message
            )
        
        decisions = decision_engine.analyze_and_decide(
            functions, 
            repo_path, 
            progress_callback=progress_callback
        )
        
        # Step 4: Stop live display and show final results
        progress_manager.stop_live_display()
        progress_manager.print_final_summary()
        
        # Step 5: Save output if requested
        if save_output and output_manager:
            console.print("\n💾 [yellow]Step 5: Saving analysis results...[/yellow]")
            
            # Create session directory
            repo_name = Path(repository_path).name
            session_dir = output_manager.create_session_directory(repo_name)
            
            # Save all results
            settings = {
                "max_functions": max_functions,
                "coverage_threshold": coverage_threshold,
                "generate_tests": generate_tests
            }
            
            output_manager.save_analysis_results(decisions, repository_path, settings)
            output_manager.save_generated_tests(decisions)
            output_manager.save_source_functions(functions)
            
            # Generate reports and build files
            html_report = output_manager.generate_html_report(decisions, repository_path)
            makefile = output_manager.generate_makefile(decisions)
            readme = output_manager.create_readme(repository_path, decisions)
            
            console.print(f"✅ [green]Results saved to:[/green] {session_dir}")
            console.print(f"   📄 HTML Report: {html_report}")
            console.print(f"   🔧 Makefile: {makefile}")
            console.print(f"   📖 README: {readme}")
        
        # Step 6: Show detailed results
        show_detailed_results(console, decisions, generate_tests)
        
    except KeyboardInterrupt:
        if progress_manager.live_display:
            progress_manager.stop_live_display()
        console.print("\n⚠️ [yellow]Analysis interrupted by user[/yellow]")
    except Exception as e:
        if progress_manager.live_display:
            progress_manager.stop_live_display()
        console.print(f"\n❌ [red]Analysis failed:[/red] {str(e)}")
        raise


def extract_functions_from_repository(
    repo_path: Path, 
    language_parser: LanguageParser, 
    max_functions: int
) -> List[Dict]:
    """Extract functions from repository."""
    
    # Find source files (focusing on C for now)
    source_files = list(repo_path.glob("*.c"))
    if not source_files:
        # Try subdirectories
        source_files = list(repo_path.glob("**/*.c"))
    
    all_functions = []
    
    for source_file in source_files:
        if len(all_functions) >= max_functions:
            break
            
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract modules using language parser
            modules = language_parser.extract_modules(content, "c", str(source_file))
            
            # Convert ExtractedModule objects to function dictionaries
            for module in modules:
                if module.kind == "function" and len(all_functions) < max_functions:
                    all_functions.append({
                        "name": module.name,
                        "content": module.source_code,
                        "language": "c",
                        "file_path": str(source_file)
                    })
        
        except Exception as e:
            # Skip files that can't be processed
            continue
    
    return all_functions


def show_detailed_results(console: Console, decisions: List, generate_tests: bool) -> None:
    """Show detailed analysis results."""
    
    console.print("\n" + "="*80)
    console.print("🔍 [bold]Detailed Analysis Results[/bold]")
    console.print("="*80)
    
    for i, decision in enumerate(decisions, 1):
        console.print(f"\n📋 [bold cyan]Function {i}: {decision.function_name}[/bold cyan]")
        
        # Coverage Analysis
        if decision.coverage_analysis:
            ca = decision.coverage_analysis
            console.print(f"   📊 Coverage: {ca.coverage_percentage}%")
            console.print(f"   🏷️  Quality: {ca.existing_tests_quality}")
            console.print(f"   🎯 Priority: {ca.priority.value}")
            console.print(f"   💭 Reasoning: {ca.reasoning[:100]}...")
            
            if ca.coverage_gaps:
                console.print(f"   🕳️  Coverage Gaps: {', '.join(ca.coverage_gaps[:3])}")
            
            if ca.missing_scenarios:
                console.print(f"   🔍 Missing Scenarios: {len(ca.missing_scenarios)} identified")
        
        # Decision
        console.print(f"   ⚡ AI Decision: [bold]{decision.decision.upper()}[/bold] - {decision.reason}")
        
        # Generated Tests
        if generate_tests and decision.generated_tests:
            console.print(f"   ✅ Test Generation: [green]Success[/green]")
            console.print(f"   📝 Test Preview:")
            # Show first few lines of generated test
            test_lines = decision.generated_tests.split('\n')[:5]
            for line in test_lines:
                console.print(f"       {line}")
            if len(decision.generated_tests.split('\n')) > 5:
                console.print("       ...")
        elif generate_tests and decision.decision == "generate":
            console.print(f"   ❌ Test Generation: [red]Failed[/red]")
        elif decision.decision == "skip":
            console.print(f"   ⏭️  Test Generation: [dim]Skipped (sufficient coverage)[/dim]")
    
    console.print("\n" + "="*80)
    console.print("✨ [bold green]Analysis Complete![/bold green]")
    console.print("="*80)