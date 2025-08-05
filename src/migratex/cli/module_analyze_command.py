"""Enhanced module-based analyze command with clean dashboard."""

from pathlib import Path
from typing import List
from rich.console import Console

from ..analysis.module_extractor import ModuleExtractor
from ..analysis.module_test_decision_engine import ModuleTestDecisionEngine
from .clean_dashboard import CleanDashboard
from ..output.output_manager import OutputManager


def run_module_based_analysis(
    repository_path: str,
    max_modules: int = 5,
    coverage_threshold: int = 80,
    generate_tests: bool = True,
    save_output: bool = True,
    quiet: bool = False
) -> None:
    """Run module-based analysis with clean dashboard."""
    
    console = Console()
    repo_path = Path(repository_path)
    
    if not repo_path.exists():
        console.print(f"❌ [red]Repository path does not exist:[/red] {repository_path}")
        return
    
    if not quiet:
        console.print(f"🔍 [bold]Starting Module-Based MigrateX Analysis[/bold]")
        console.print(f"📂 Repository: {repository_path}")
        console.print(f"🎯 Max Modules: {max_modules}")
        console.print(f"📊 Coverage Threshold: {coverage_threshold}%")
        console.print(f"🤖 Generate Tests: {'Yes' if generate_tests else 'No'}")
    
    # Initialize components
    module_extractor = ModuleExtractor()
    decision_engine = ModuleTestDecisionEngine(coverage_threshold=coverage_threshold)
    dashboard = CleanDashboard(console, quiet=quiet)
    output_manager = OutputManager() if save_output else None
    
    try:
        # Step 1: Extract semantic modules
        if not quiet:
            console.print("🔍 [yellow]Step 1: Extracting semantic modules...[/yellow]")
        
        modules = module_extractor.extract_modules_from_repository(
            repository_path, 
            language="c",
            max_modules=max_modules
        )
        
        if not modules:
            console.print("❌ [red]No modules found in repository[/red]")
            return
        
        # Show module extraction summary
        summary = module_extractor.get_module_summary(modules)
        if not quiet:
            console.print(f"✅ [green]Found {len(modules)} semantic modules[/green]")
            console.print(f"   📊 Total Functions: {summary['total_functions']}")
            console.print(f"   🏗️  Module Types: {summary['module_breakdown']}")
            console.print(f"   🔒 Self-contained: {summary['self_contained_count']}/{len(modules)} ({summary['self_contained_percentage']:.1f}%)")
            console.print()
        else:
            console.print(f"🔍 Found {len(modules)} modules with {summary['total_functions']} functions")
        
        # Step 2: Initialize clean dashboard
        if not quiet:
            console.print("🚀 [yellow]Step 2: Starting AI module coverage analysis...[/yellow]")
        
        dashboard.initialize_modules(modules)
        dashboard.start_analysis()
        
        # Step 3: Run module-level analysis with progress callbacks
        def progress_callback(module_name: str, status: str, coverage_analysis=None, decision=None, error_message=None):
            dashboard.update_module_status(
                module_name, status, coverage_analysis, error_message
            )
            
            # Also show quiet progress if in quiet mode
            if quiet:
                completed = sum(1 for m in dashboard.module_statuses.values() if m.status in ["completed", "failed"])
                total = len(dashboard.module_statuses)
                dashboard.print_quiet_progress(module_name, completed, total)
        
        decisions = decision_engine.analyze_and_decide(
            modules, 
            repo_path, 
            progress_callback=progress_callback
        )
        
        # Step 4: Stop display and show final results
        dashboard.stop_analysis()
        dashboard.print_final_summary()
        
        # Step 5: Save output if requested
        if save_output and output_manager:
            console.print("\\n💾 [yellow]Step 5: Saving analysis results...[/yellow]")
            
            # Create session directory
            repo_name = Path(repository_path).name
            session_dir = output_manager.create_session_directory(repo_name)
            
            # Save all results (adapted for modules)
            settings = {
                "max_modules": max_modules,
                "coverage_threshold": coverage_threshold,
                "generate_tests": generate_tests,
                "analysis_type": "module_based"
            }
            
            # Convert module decisions to function-like format for compatibility
            # Create a simple decision-like class for compatibility
            class DecisionLike:
                def __init__(self, decision_data):
                    self.function_name = decision_data["function_name"]
                    self.decision = decision_data["decision"]
                    self.reason = decision_data["reason"]
                    self.coverage_analysis = decision_data["coverage_analysis"]
                    self.existing_tests = decision_data["existing_tests"]
                    self.generated_tests = decision_data["generated_tests"]
                    self.generation_success = decision_data["generation_success"]
            
            function_like_decisions = []
            for decision in decisions:
                # Create a decision-like object for each module
                decision_data = {
                    "function_name": decision.module_name,
                    "decision": decision.decision,
                    "reason": decision.reason,
                    "coverage_analysis": decision.coverage_analysis,
                    "existing_tests": decision.existing_tests,
                    "generated_tests": decision.generated_tests,
                    "generation_success": decision.generation_success
                }
                function_like_decisions.append(DecisionLike(decision_data))
            
            # Save using adapted format
            output_manager.save_analysis_results(function_like_decisions, repository_path, settings)
            output_manager.save_generated_tests(function_like_decisions)
            
            # Save module source code
            module_functions = []
            for module in modules:
                for func in module.functions:
                    module_functions.append({
                        "name": func.name,
                        "content": func.source_code,
                        "language": "c",
                        "file_path": func.file_path,
                        "module": module.name
                    })
            output_manager.save_source_functions(module_functions)
            
            # Generate reports and build files
            html_report = output_manager.generate_html_report(function_like_decisions, repository_path)
            makefile = output_manager.generate_makefile(function_like_decisions)
            readme = output_manager.create_readme(repository_path, function_like_decisions)
            
            console.print(f"✅ [green]Results saved to:[/green] {session_dir}")
            console.print(f"   📄 HTML Report: {html_report}")
            console.print(f"   🔧 Makefile: {makefile}")
            console.print(f"   📖 README: {readme}")
        
        # Step 6: Show detailed module results
        show_detailed_module_results(console, modules, decisions, generate_tests)
        
    except KeyboardInterrupt:
        if progress_manager.live_display:
            progress_manager.stop_live_display()
        console.print("\\n⚠️ [yellow]Analysis interrupted by user[/yellow]")
    except Exception as e:
        if progress_manager.live_display:
            progress_manager.stop_live_display()
        console.print(f"\\n❌ [red]Analysis failed:[/red] {str(e)}")
        raise


def show_detailed_module_results(console: Console, modules: List, decisions: List, generate_tests: bool) -> None:
    """Show detailed module analysis results."""
    
    console.print("\\n" + "="*80)
    console.print("🔍 [bold]Detailed Module Analysis Results[/bold]")
    console.print("="*80)
    
    for i, (module, decision) in enumerate(zip(modules, decisions), 1):
        console.print(f"\\n📋 [bold cyan]Module {i}: {module.name}[/bold cyan]")
        console.print(f"   🏗️  Type: {module.module_type}")
        console.print(f"   📝 Description: {module.description}")
        console.print(f"   🔧 Functions: {', '.join(module.function_names)}")
        console.print(f"   🔒 Self-contained: {'Yes' if module.is_self_contained else 'No'}")
        console.print(f"   🔢 Complexity: {module.complexity_score:.1f}")
        
        # Coverage Analysis
        if decision.coverage_analysis:
            ca = decision.coverage_analysis
            console.print(f"   📊 Module Coverage: {ca.coverage_percentage}%")
            console.print(f"   🏷️  Test Quality: {ca.existing_tests_quality}")
            console.print(f"   🎯 Priority: {ca.priority.value}")
            console.print(f"   🔗 Integration Tests Needed: {'Yes' if ca.integration_tests_needed else 'No'}")
            console.print(f"   💭 AI Reasoning: {ca.reasoning[:100]}...")
            
            if ca.coverage_gaps:
                console.print(f"   🕳️  Coverage Gaps: {', '.join(ca.coverage_gaps[:2])}")
            
            if ca.missing_scenarios:
                console.print(f"   🔍 Missing Scenarios: {len(ca.missing_scenarios)} identified")
        
        # Decision
        console.print(f"   ⚡ AI Decision: [bold]{decision.decision.upper()}[/bold] - {decision.reason}")
        
        # Generated Tests
        if generate_tests and decision.generated_tests:
            console.print(f"   ✅ Test Generation: [green]Success[/green]")
            console.print(f"   📝 Test Preview:")
            # Show first few lines of generated test
            test_lines = decision.generated_tests.split('\\n')[:5]
            for line in test_lines:
                console.print(f"       {line}")
            if len(decision.generated_tests.split('\\n')) > 5:
                console.print("       ...")
        elif generate_tests and decision.decision == "generate":
            console.print(f"   ❌ Test Generation: [red]Failed[/red]")
        elif decision.decision == "skip":
            console.print(f"   ⏭️  Test Generation: [dim]Skipped (sufficient coverage)[/dim]")
    
    console.print("\\n" + "="*80)
    console.print("✨ [bold green]Module Analysis Complete![/bold green]")
    console.print("="*80)