"""MigrateX CLI application."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from migratex.cli.visualizer import ModuleTreeVisualizer
from migratex.pipeline.orchestrator import MigrationOrchestrator

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