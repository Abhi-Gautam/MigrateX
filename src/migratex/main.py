"""MigrateX CLI application."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from migratex.cli.visualizer import ModuleTreeVisualizer
from migratex.cli.analyze_command import run_enhanced_analysis
from migratex.cli.module_analyze_command import run_module_based_analysis
from migratex.cli.translate_command import run_translation_command
from migratex.cli.knowledge_command import (
    run_knowledge_add_example_command,
    run_knowledge_add_style_guide_command,
    run_knowledge_add_pattern_command,
    run_knowledge_add_feedback_command,
    run_knowledge_stats_command,
    run_knowledge_search_command,
    run_knowledge_export_command
)
from migratex.pipeline.orchestrator import MigrationOrchestrator
from migratex.analysis.language_parser import LanguageParser
from migratex.analysis.test_extractor import TestExtractor
from migratex.analysis.test_generator import TestGenerator
from migratex.directory_mapping.metadata_manager import MetadataManager

app = typer.Typer(
    name="migratex",
    help="Intelligent agentic pipeline for automated code translation",
    rich_markup_mode="rich",
)
console = Console()

SUPPORTED_LANGUAGES = {
    "rust": "Rust",
    "go": "Go",
    "python": "Python",
}

SOURCE_LANGUAGES = {
    "c": "C",
    "cpp": "C++",
    "java": "Java", 
    "csharp": "C#",
}

@app.command()
def translate(
    repository_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the source code repository to translate",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ],
    target_language: Annotated[
        str,
        typer.Argument(
            help="Target language for translation (rust, go, python)",
        ),
    ],
    source_language: Annotated[
        Optional[str],
        typer.Option(
            "--source", "-s",
            help="Source language (auto-detected if not specified)",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be translated without performing translation",
        ),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive", "-i",
            help="Enable interactive mode with visual progress",
        ),
    ] = True,
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output", "-o",
            help="Output directory for translated code",
        ),
    ] = None,
) -> None:
    """Translate source code from legacy languages to modern alternatives."""
    
    # Validate target language
    if target_language.lower() not in SUPPORTED_LANGUAGES:
        console.print(f"[red]Error:[/red] Unsupported target language '{target_language}'")
        console.print(f"Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}")
        raise typer.Exit(1)

    # Validate source language if provided
    if source_language and source_language.lower() not in SOURCE_LANGUAGES:
        console.print(f"[red]Error:[/red] Unsupported source language '{source_language}'")
        console.print(f"Supported languages: {', '.join(SOURCE_LANGUAGES.keys())}")
        raise typer.Exit(1)

    # Set default output directory
    if output_dir is None:
        output_dir = repository_path.parent / f"{repository_path.name}_{target_language}"

    # Display welcome message
    console.print(Panel.fit(
        Text("MigrateX - Intelligent Code Translation", style="bold blue"),
        subtitle=f"Translating to {SUPPORTED_LANGUAGES[target_language.lower()]}",
    ))

    try:
        # Initialize the migration orchestrator
        orchestrator = MigrationOrchestrator(
            source_path=repository_path,
            target_language=target_language.lower(),
            source_language=source_language.lower() if source_language else None,
            output_path=output_dir,
            dry_run=dry_run,
            interactive=interactive,
        )

        # Start the migration process
        orchestrator.run()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@app.command()
def analyze(
    repository_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the source code repository to analyze",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ],
    source_language: Annotated[
        Optional[str],
        typer.Option(
            "--source", "-s",
            help="Source language (auto-detected if not specified)",
        ),
    ] = None,
) -> None:
    """Analyze source code repository and display module structure."""
    
    console.print(Panel.fit(
        Text("MigrateX - Code Analysis", style="bold green"),
        subtitle="Analyzing repository structure",
    ))

    try:
        # Initialize visualizer
        visualizer = ModuleTreeVisualizer()
        
        # Analyze and display
        visualizer.analyze_repository(repository_path, source_language)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@app.command()
def test_extract(
    repository_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the source code repository to test",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ],
    generate_tests: Annotated[
        bool,
        typer.Option(
            "--generate", "-g",
            help="Generate missing tests using AI",
        ),
    ] = False,
    max_functions: Annotated[
        int,
        typer.Option(
            "--max-functions", "-m",
            help="Maximum number of functions to process (for cost control)",
        ),
    ] = 5,
) -> None:
    """Extract functions and optionally generate tests for a repository."""
    
    console.print(Panel.fit(
        Text("MigrateX - Test Extraction & Generation", style="bold cyan"),
        subtitle="Analyzing functions and generating tests",
    ))
    
    try:
        # Initialize components
        parser = LanguageParser()
        test_extractor = TestExtractor()
        test_generator = TestGenerator() if generate_tests else None
        metadata_manager = MetadataManager()
        
        console.print(f"\n🔍 Analyzing repository: {repository_path}")
        
        # Find source files
        source_files = [f for f in repository_path.rglob("*.c") if "test" not in f.name.lower()]
        console.print(f"Found {len(source_files)} C source files")
        
        # Extract functions
        all_functions = []
        for source_file in source_files:
            console.print(f"  📄 Parsing {source_file.name}...")
            with open(source_file, 'r') as f:
                content = f.read()
            
            modules = parser.extract_modules(content, "c", str(source_file))
            functions = [{
                "name": m.name, 
                "content": m.source_code, 
                "dependencies": m.dependencies, 
                "language": "c",
                "file": str(source_file)
            } for m in modules]
            
            console.print(f"    ✅ Extracted {len(functions)} functions")
            all_functions.extend(functions)
        
        console.print(f"\n📊 Total functions extracted: {len(all_functions)}")
        
        # Create metadata entries
        for func in all_functions:
            metadata_manager.create_function_metadata(func)
        
        # Find existing tests
        test_files = test_extractor.identify_test_files(repository_path, "c")
        console.print(f"\n🧪 Found {len(test_files)} test files")
        
        existing_tests = []
        for test_file in test_files:
            with open(test_file, 'r') as f:
                content = f.read()
            test_functions = test_extractor.extract_test_functions(content, "c")
            existing_tests.extend(test_functions)
        
        console.print(f"Found {len(existing_tests)} existing test functions")
        
        # Generate tests if requested
        if generate_tests and test_generator:
            console.print(f"\n🤖 Generating tests (limited to {max_functions} functions for cost control)...")
            
            functions_to_test = all_functions[:max_functions]
            generated_count = 0
            failed_count = 0
            
            for func in functions_to_test:
                console.print(f"  Generating test for {func['name']}...")
                result = test_generator.generate_test(func)
                
                if result:
                    console.print("    ✅ Generated successfully")
                    console.print(f"    📝 Test preview:")
                    # Show first few lines of generated test
                    preview_lines = result['test_content'].split('\n')[:5]
                    for line in preview_lines:
                        console.print(f"      {line}")
                    console.print("      ...")
                    
                    # Associate with metadata
                    metadata = metadata_manager.get_metadata_by_function_name(func['name'])
                    if metadata:
                        metadata_manager.associate_generated_test(metadata['id'], result)
                    
                    generated_count += 1
                else:
                    console.print("    ❌ Generation failed")
                    failed_count += 1
            
            console.print(f"\n📊 Test generation summary:")
            console.print(f"  ✅ Successfully generated: {generated_count}")
            console.print(f"  ❌ Failed: {failed_count}")
            
            if generated_count > 0:
                success_rate = (generated_count / (generated_count + failed_count)) * 100
                console.print(f"  📈 Success rate: {success_rate:.1f}%")
        
        # Summary
        console.print(f"\n📋 Analysis Summary:")
        console.print(f"  🔧 Functions found: {len(all_functions)}")
        console.print(f"  🧪 Existing tests: {len(existing_tests)}")
        if generate_tests:
            console.print(f"  🤖 Tests generated: {generated_count}")
        
        console.print(f"\n✅ Analysis complete!")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def analyze_and_generate(
    repository_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the source code repository to analyze",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ],
    max_functions: Annotated[
        int,
        typer.Option(
            "--max-functions", "-m",
            help="Maximum number of functions to analyze (for cost control)",
        ),
    ] = 5,
    coverage_threshold: Annotated[
        int,
        typer.Option(
            "--coverage-threshold", "-t",
            help="Minimum coverage percentage to skip test generation",
        ),
    ] = 80,
    generate_tests: Annotated[
        bool,
        typer.Option(
            "--generate/--no-generate",
            help="Generate tests for functions with insufficient coverage",
        ),
    ] = True,
    save_output: Annotated[
        bool,
        typer.Option(
            "--save-output/--no-save-output",
            help="Save analysis results to organized output directory",
        ),
    ] = True,
) -> None:
    """🤖 AI-powered code analysis with real-time progress display.
    
    This command provides enhanced analysis with:
    - Real-time progress visualization
    - AI-powered coverage analysis for each function
    - Intelligent test generation decisions
    - Comprehensive reporting and statistics
    """
    
    console.print(Panel.fit(
        Text("🤖 MigrateX Enhanced Analysis", style="bold magenta"),
        subtitle="AI-powered coverage analysis with real-time progress",
    ))
    
    try:
        run_enhanced_analysis(
            repository_path=str(repository_path),
            max_functions=max_functions,
            coverage_threshold=coverage_threshold,
            generate_tests=generate_tests,
            save_output=save_output
        )
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def analyze_modules(
    repository_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the source code repository to analyze",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ],
    max_modules: Annotated[
        int,
        typer.Option(
            "--max-modules", "-m",
            help="Maximum number of modules to analyze (for cost control)",
        ),
    ] = 5,
    coverage_threshold: Annotated[
        int,
        typer.Option(
            "--coverage-threshold", "-t",
            help="Minimum coverage percentage to skip test generation",
        ),
    ] = 80,
    generate_tests: Annotated[
        bool,
        typer.Option(
            "--generate/--no-generate",
            help="Generate tests for modules with insufficient coverage",
        ),
    ] = True,
    save_output: Annotated[
        bool,
        typer.Option(
            "--save-output/--no-save-output",
            help="Save analysis results to organized output directory",
        ),
    ] = True,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet/--verbose",
            help="Minimal output with summary only (no real-time progress)",
        ),
    ] = False,
) -> None:
    """🏗️ AI-powered semantic module analysis with CFG-based grouping.
    
    This command implements the true MigrateX architecture:
    - Extracts self-contained semantic modules using CFG analysis
    - Groups related functions based on dependency relationships
    - AI coverage analysis at the module level (not individual functions)
    - Intelligent test generation for complete modules
    - Cost per module instead of per function
    """
    
    console.print(Panel.fit(
        Text("🏗️ MigrateX Module Analysis", style="bold magenta"),
        subtitle="Semantic module extraction with AI-powered analysis",
    ))
    
    try:
        run_module_based_analysis(
            repository_path=str(repository_path),
            max_modules=max_modules,
            coverage_threshold=coverage_threshold,
            generate_tests=generate_tests,
            save_output=save_output,
            quiet=quiet
        )
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def translate_modules(
    repository_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the source code repository to translate",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ],
    target_language: Annotated[
        str,
        typer.Option(
            "--target", "-t",
            help="Target language for translation (rust, go, python, javascript, typescript)",
        ),
    ] = "rust",
    max_modules: Annotated[
        int,
        typer.Option(
            "--max-modules", "-m",
            help="Maximum number of modules to translate (for cost control)",
        ),
    ] = 3,
    project_name: Annotated[
        Optional[str],
        typer.Option(
            "--project-name", "-p",
            help="Name for the translated project",
        ),
    ] = None,
    output_dir: Annotated[
        Optional[str],
        typer.Option(
            "--output", "-o",
            help="Output directory to save translated project",
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet/--verbose",
            help="Minimal output with summary only",
        ),
    ] = False,
) -> None:
    """🔄 AI-powered code translation from C to modern languages.
    
    This command provides complete module translation:
    - Extracts semantic modules from source code
    - AI-powered translation with context awareness
    - Generates complete project structure with build files
    - Preserves semantic meaning and functionality
    - Supports Rust, Go, Python, JavaScript, TypeScript
    """
    
    console.print(Panel.fit(
        Text("🔄 MigrateX Code Translation", style="bold magenta"),
        subtitle="AI-powered semantic module translation",
    ))
    
    try:
        run_translation_command(
            repository_path=str(repository_path),
            target_language=target_language,
            max_modules=max_modules,
            project_name=project_name,
            output_dir=output_dir,
            quiet=quiet
        )
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Knowledge Base Management Commands
@app.command()
def knowledge_add_example(
    source_code: Annotated[str, typer.Option("--source", "-s", help="Source code to add")],
    target_code: Annotated[str, typer.Option("--target", "-t", help="Target code translation")],
    source_language: Annotated[str, typer.Option("--source-lang", help="Source language")] = "c",
    target_language: Annotated[str, typer.Option("--target-lang", help="Target language")] = "rust",
    description: Annotated[Optional[str], typer.Option("--desc", help="Description of the example")] = None,
    knowledge_base_path: Annotated[Optional[str], typer.Option("--kb-path", help="Knowledge base directory")] = None,
) -> None:
    """📝 Add a code translation example to the RAG knowledge base."""
    
    run_knowledge_add_example_command(
        source_code=source_code,
        target_code=target_code,
        source_language=source_language,
        target_language=target_language,
        description=description,
        knowledge_base_path=knowledge_base_path
    )


@app.command()
def knowledge_add_guide(
    title: Annotated[str, typer.Option("--title", help="Style guide title")],
    content: Annotated[str, typer.Option("--content", help="Style guide content")],
    language: Annotated[Optional[str], typer.Option("--language", help="Programming language")] = None,
    category: Annotated[str, typer.Option("--category", help="Style guide category")] = "general",
    knowledge_base_path: Annotated[Optional[str], typer.Option("--kb-path", help="Knowledge base directory")] = None,
) -> None:
    """📋 Add a style guide to the RAG knowledge base."""
    
    run_knowledge_add_style_guide_command(
        title=title,
        content=content,
        language=language,
        category=category,
        knowledge_base_path=knowledge_base_path
    )


@app.command()
def knowledge_add_pattern(
    name: Annotated[str, typer.Option("--name", help="Pattern name")],
    description: Annotated[str, typer.Option("--description", help="Pattern description")],
    example_code: Annotated[Optional[str], typer.Option("--example", help="Example code")] = None,
    language: Annotated[Optional[str], typer.Option("--language", help="Programming language")] = None,
    knowledge_base_path: Annotated[Optional[str], typer.Option("--kb-path", help="Knowledge base directory")] = None,
) -> None:
    """🏗️ Add an architectural pattern to the RAG knowledge base."""
    
    run_knowledge_add_pattern_command(
        name=name,
        description=description,
        example_code=example_code,
        language=language,
        knowledge_base_path=knowledge_base_path
    )


@app.command()
def knowledge_add_feedback(
    original_code: Annotated[str, typer.Option("--original", help="Original source code")],
    generated_translation: Annotated[str, typer.Option("--generated", help="Generated translation")],
    corrected_translation: Annotated[Optional[str], typer.Option("--corrected", help="Corrected translation")] = None,
    feedback_text: Annotated[Optional[str], typer.Option("--feedback", help="Human feedback text")] = None,
    rating: Annotated[Optional[int], typer.Option("--rating", help="Quality rating (1-5)")] = None,
    source_language: Annotated[str, typer.Option("--source-lang", help="Source language")] = "c",
    target_language: Annotated[str, typer.Option("--target-lang", help="Target language")] = "rust",
    knowledge_base_path: Annotated[Optional[str], typer.Option("--kb-path", help="Knowledge base directory")] = None,
) -> None:
    """💬 Add human feedback to the RAG knowledge base."""
    
    run_knowledge_add_feedback_command(
        original_code=original_code,
        generated_translation=generated_translation,
        corrected_translation=corrected_translation,
        feedback_text=feedback_text,
        rating=rating,
        source_language=source_language,
        target_language=target_language,
        knowledge_base_path=knowledge_base_path
    )


@app.command()
def knowledge_stats(
    knowledge_base_path: Annotated[Optional[str], typer.Option("--kb-path", help="Knowledge base directory")] = None,
) -> None:
    """📊 Display RAG knowledge base statistics."""
    
    run_knowledge_stats_command(knowledge_base_path=knowledge_base_path)


@app.command()
def knowledge_search(
    query: Annotated[str, typer.Option("--query", "-q", help="Search query")],
    source_language: Annotated[str, typer.Option("--source-lang", help="Source language")] = "c",
    target_language: Annotated[str, typer.Option("--target-lang", help="Target language")] = "rust",
    max_results: Annotated[int, typer.Option("--max", help="Maximum results to show")] = 5,
    knowledge_base_path: Annotated[Optional[str], typer.Option("--kb-path", help="Knowledge base directory")] = None,
) -> None:
    """🔍 Search the RAG knowledge base for relevant examples."""
    
    run_knowledge_search_command(
        query=query,
        source_language=source_language,
        target_language=target_language,
        max_results=max_results,
        knowledge_base_path=knowledge_base_path
    )


@app.command()
def knowledge_export(
    output_path: Annotated[str, typer.Option("--output", "-o", help="Output file path")],
    format: Annotated[str, typer.Option("--format", help="Export format")] = "json",
    knowledge_base_path: Annotated[Optional[str], typer.Option("--kb-path", help="Knowledge base directory")] = None,
) -> None:
    """📤 Export RAG knowledge base to a file."""
    
    run_knowledge_export_command(
        output_path=output_path,
        format=format,
        knowledge_base_path=knowledge_base_path
    )


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-v",
            help="Show version information",
        ),
    ] = None,
) -> None:
    """MigrateX: Intelligent agentic pipeline for automated code translation."""
    if version:
        from migratex import __version__
        console.print(f"MigrateX version {__version__}")
        raise typer.Exit()

if __name__ == "__main__":
    app()