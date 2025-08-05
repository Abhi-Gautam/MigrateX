"""CLI command for module translation using the Translation Engine."""

from pathlib import Path
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..analysis.module_extractor import ModuleExtractor
from ..translation.translation_engine import TranslationEngine
from ..translation.models import TranslationLanguage, BatchTranslationResult
from .clean_dashboard import CleanDashboard


def run_translation_command(
    repository_path: str,
    target_language: str = "rust",
    max_modules: int = 3,
    project_name: str = None,
    output_dir: str = None,
    quiet: bool = False
) -> None:
    """Run the translation command with clean progress display."""
    
    console = Console()
    repo_path = Path(repository_path)
    
    if not repo_path.exists():
        console.print(f"❌ [red]Repository path does not exist:[/red] {repository_path}")
        return
    
    # Validate target language
    try:
        target_lang = TranslationLanguage(target_language.lower())
    except ValueError:
        valid_languages = [lang.value for lang in TranslationLanguage]
        console.print(f"❌ [red]Invalid target language:[/red] {target_language}")
        console.print(f"Valid languages: {', '.join(valid_languages)}")
        return
    
    # Set default project name
    if not project_name:
        project_name = f"translated_{repo_path.name}"
    
    # Set default output directory within migratex_output
    if not output_dir:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"migratex_output/translated_projects/{project_name}_{target_language}_{timestamp}"
    
    if not quiet:
        console.print(f"🚀 [bold]Starting MigrateX Translation[/bold]")
        console.print(f"📂 Repository: {repository_path}")
        console.print(f"🎯 Target Language: {target_lang.value.title()}")
        console.print(f"📦 Max Modules: {max_modules}")
        console.print(f"🏷️  Project Name: {project_name}")
        console.print()
    
    # Initialize components
    module_extractor = ModuleExtractor()
    translation_engine = TranslationEngine()
    dashboard = CleanDashboard(console, quiet=quiet)
    
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
            console.print()
        else:
            console.print(f"🔍 Found {len(modules)} modules with {summary['total_functions']} functions")
        
        # Step 2: Initialize translation progress
        if not quiet:
            console.print("🔄 [yellow]Step 2: Starting AI-powered translation...[/yellow]")
        
        dashboard.initialize_modules(modules)
        dashboard.start_analysis()
        
        # Step 3: Perform batch translation with progress tracking
        def progress_callback(module_name: str, status: str, error_message=None):
            dashboard.update_module_status(module_name, status, error_message=error_message)
            
            if quiet:
                completed = sum(1 for m in dashboard.module_statuses.values() if m.status in ["completed", "failed"])
                total = len(dashboard.module_statuses)
                dashboard.print_quiet_progress(module_name, completed, total)
        
        # Perform translation with progress callbacks
        batch_result = translate_with_progress(
            translation_engine, modules, target_lang, project_name, progress_callback
        )
        
        # Step 4: Stop progress display and show results
        dashboard.stop_analysis()
        
        # Step 5: Display translation results
        display_translation_results(console, batch_result, quiet)
        
        # Step 6: Save output if requested
        if output_dir:
            save_translation_output(console, batch_result, output_dir, quiet)
        
    except Exception as e:
        console.print(f"[red]Translation Error:[/red] {e}")
        raise


def translate_with_progress(
    engine: TranslationEngine,
    modules: List,
    target_language: TranslationLanguage,
    project_name: str,
    progress_callback
) -> BatchTranslationResult:
    """Translate modules with progress callbacks."""
    
    batch_result = BatchTranslationResult(
        project_name=project_name,
        source_language="c",
        target_language=target_language
    )
    
    for module in modules:
        progress_callback(module.name, "analyzing")
        
        try:
            # Translate individual module
            result = engine.translate_module(module, target_language)
            batch_result.add_module_result(result)
            
            if result.is_successful:
                progress_callback(module.name, "completed")
            else:
                error_msg = "; ".join([e.message for e in result.errors[:2]])  # First 2 errors
                progress_callback(module.name, "failed", error_msg)
                
        except Exception as e:
            # Create a failed result
            from ..translation.models import TranslationResult, TranslationStatus
            failed_result = TranslationResult(
                source_module_name=module.name,
                target_module_name=f"{module.name}_failed",
                source_language="c",
                target_language=target_language,
                status=TranslationStatus.FAILED
            )
            failed_result.add_error("system", f"Translation failed: {str(e)}")
            batch_result.add_module_result(failed_result)
            progress_callback(module.name, "failed", str(e))
    
    # Generate project-level outputs
    engine._generate_project_structure(batch_result)
    engine._generate_build_files(batch_result)
    engine._generate_migration_documentation(batch_result)
    
    return batch_result


def display_translation_results(console: Console, batch_result: BatchTranslationResult, quiet: bool):
    """Display comprehensive translation results."""
    
    # Main summary
    summary_text = f"""
🎯 [bold green]Translation Complete![/bold green]

📊 [bold]Translation Results:[/bold]
   • Modules Translated: {batch_result.successful_modules}/{batch_result.total_modules}
   • Success Rate: {batch_result.success_rate:.1f}%
   • Total Translation Time: {batch_result.total_translation_time:.1f}s
   • Average Time per Module: {batch_result.total_translation_time/max(batch_result.total_modules, 1):.1f}s

🎯 [bold]Target Language:[/bold] {batch_result.target_language.value.title()}
📦 [bold]Project Name:[/bold] {batch_result.project_name}
"""
    
    summary_panel = Panel(
        summary_text.strip(),
        title="🔄 MigrateX Translation Summary",
        border_style="green",
        padding=(1, 2)
    )
    
    console.print("\\n")
    console.print(summary_panel)
    
    # Detailed results table (if not quiet)
    if not quiet and batch_result.module_results:
        console.print("\\n📋 [bold]Module Translation Details:[/bold]")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Module", style="cyan", width=25)
        table.add_column("Status", width=12)
        table.add_column("Confidence", width=12, justify="center")
        table.add_column("Time", width=8, justify="right")
        table.add_column("Notes", width=40)
        
        for result in batch_result.module_results:
            # Status with emoji
            if result.is_successful:
                status = "✅ Success"
                status_style = "green"
            else:
                status = "❌ Failed"
                status_style = "red"
            
            # Confidence
            confidence = f"{result.confidence_score:.0f}%" if result.confidence_score > 0 else "—"
            
            # Time
            time_str = f"{result.translation_time:.1f}s" if result.translation_time > 0 else "—"
            
            # Notes (first error or translation note)
            notes = ""
            if result.errors:
                notes = result.errors[0].message[:38] + "..." if len(result.errors[0].message) > 38 else result.errors[0].message
            elif result.translation_notes:
                notes = result.translation_notes[0][:38] + "..." if len(result.translation_notes[0]) > 38 else result.translation_notes[0]
            
            table.add_row(
                result.source_module_name[:23] + ("..." if len(result.source_module_name) > 23 else ""),
                f"[{status_style}]{status}[/{status_style}]",
                confidence,
                time_str,
                notes
            )
        
        console.print(table)
    
    # Show failed translations
    failed_results = batch_result.get_failed_results()
    if failed_results:
        console.print("\\n❌ [red]Failed Translations:[/red]")
        for result in failed_results:
            console.print(f"   • {result.source_module_name}:")
            for error in result.errors[:2]:  # Show first 2 errors
                console.print(f"     - {error.message}")
    
    # Show successful translations preview
    successful_results = batch_result.get_successful_results()
    if successful_results and not quiet:
        console.print("\\n✅ [green]Successful Translations:[/green]")
        for result in successful_results[:3]:  # Show first 3
            console.print(f"   • {result.source_module_name} → {result.target_module_name}")
            if result.semantic_changes:
                console.print(f"     Changes: {', '.join(result.semantic_changes[:2])}")


def save_translation_output(
    console: Console, 
    batch_result: BatchTranslationResult, 
    output_dir: str,
    quiet: bool
):
    """Save translation output to directory."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not quiet:
        console.print(f"\\n💾 [yellow]Saving translation output to: {output_path}[/yellow]")
    
    # Save project structure
    for file_path, content in batch_result.project_structure.items():
        full_path = output_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
    
    # Save build files
    for file_name, content in batch_result.build_files.items():
        (output_path / file_name).write_text(content, encoding='utf-8')
    
    # Save migration guide
    if batch_result.migration_guide:
        (output_path / "MIGRATION_GUIDE.md").write_text(batch_result.migration_guide, encoding='utf-8')
    
    # Save detailed results as JSON
    import json
    results_data = {
        "project_name": batch_result.project_name,
        "source_language": batch_result.source_language,
        "target_language": batch_result.target_language.value,
        "success_rate": batch_result.success_rate,
        "total_modules": batch_result.total_modules,
        "successful_modules": batch_result.successful_modules,
        "failed_modules": batch_result.failed_modules,
        "total_translation_time": batch_result.total_translation_time,
        "modules": [
            {
                "source_name": result.source_module_name,
                "target_name": result.target_module_name,
                "status": result.status.value,
                "confidence_score": result.confidence_score,
                "translation_time": result.translation_time,
                "errors": [{"type": e.error_type, "message": e.message} for e in result.errors],
                "warnings": [{"type": w.error_type, "message": w.message} for w in result.warnings],
                "semantic_changes": result.semantic_changes,
                "api_changes": result.api_changes,
                "translation_notes": result.translation_notes
            }
            for result in batch_result.module_results
        ]
    }
    
    (output_path / "translation_results.json").write_text(
        json.dumps(results_data, indent=2), encoding='utf-8'
    )
    
    console.print(f"✅ [green]Translation output saved to: {output_path}[/green]")
    console.print(f"   📄 Project files: {len(batch_result.project_structure)} files")
    console.print(f"   🔧 Build files: {len(batch_result.build_files)} files") 
    console.print(f"   📖 Migration guide: MIGRATION_GUIDE.md")
    console.print(f"   📊 Results summary: translation_results.json")