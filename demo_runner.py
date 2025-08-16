#!/usr/bin/env python3
"""
Demo runner for MigrateX terminal presentations.

This script demonstrates the key features of MigrateX with compelling terminal visualizations.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

def main():
    """Run MigrateX demo presentations."""
    console = Console()
    
    console.clear()
    
    # Welcome screen
    welcome_text = """
🚀 [bold bright_blue]MigrateX Terminal Demo Suite[/bold bright_blue]

Choose a demonstration:

[bold]1.[/bold] 🎯 [bright_green]Full Interactive Demo[/bright_green] - Complete pipeline walkthrough
[bold]2.[/bold] 🌳 [bright_yellow]Module Tree Visualization[/bright_yellow] - Show extracted modules
[bold]3.[/bold] 📋 [bright_cyan]Metadata Tracking Demo[/bright_cyan] - Audit trail and provenance
[bold]4.[/bold] 🔄 [bright_magenta]Pipeline Progress Demo[/bright_magenta] - 10-stage pipeline visualization
[bold]5.[/bold] 🤖 [bright_blue]RAG System Demo[/bright_blue] - Context retrieval in action

[dim]Press 1-5 to select demo, or 'q' to quit...[/dim]
    """
    
    panel = Panel(
        welcome_text.strip(),
        title="🎯 MigrateX Demo Suite",
        border_style="bright_blue",
        padding=(1, 2)
    )
    
    console.print(Align.center(panel))
    
    choice = console.input("\nSelect demo (1-5 or q): ").strip().lower()
    
    if choice == 'q':
        console.print("👋 Thanks for trying MigrateX!")
        return
    
    console.clear()
    
    if choice == '1':
        run_full_demo(console)
    elif choice == '2':
        run_module_tree_demo(console)
    elif choice == '3':
        run_metadata_demo(console)
    elif choice == '4':
        run_pipeline_demo(console)
    elif choice == '5':
        run_rag_demo(console)
    else:
        console.print("[red]Invalid choice. Please select 1-5 or 'q'.[/red]")

def run_full_demo(console: Console):
    """Run the complete MigrateX demonstration."""
    from migratex.cli.demo_presentation import MigrateXDemoPresentation
    
    demo = MigrateXDemoPresentation(console)
    demo.run_full_demo("CircularBuffer")

def run_module_tree_demo(console: Console):
    """Run module tree visualization demo."""
    from migratex.analysis.language_parser import LanguageParser, ExtractedModule
    from migratex.cli.visualizer import ModuleTreeVisualizer
    
    # Create sample modules
    sample_modules = [
        ExtractedModule(name="buffer_init", kind="function", source_code="void buffer_init() { /* init code */ }", dependencies=[], file_path="buffer.c"),
        ExtractedModule(name="buffer_push", kind="function", source_code="int buffer_push() { /* push code */ }", dependencies=["buffer_is_full", "calculate_next_index"], file_path="buffer.c"),
        ExtractedModule(name="buffer_pop", kind="function", source_code="int buffer_pop() { /* pop code */ }", dependencies=["buffer_is_empty"], file_path="buffer.c"),
        ExtractedModule(name="buffer_resize", kind="function", source_code="void buffer_resize() { /* resize code */ }", dependencies=["malloc", "memcpy", "buffer_size", "buffer_init"], file_path="buffer.c"),
    ]
    
    visualizer = ModuleTreeVisualizer()
    visualizer.display_presentation_tree(sample_modules)
    
    console.input("\nPress Enter to continue...")

def run_metadata_demo(console: Console):
    """Run metadata tracking demonstration."""
    from migratex.cli.metadata_visualizer import MetadataTrackingVisualizer
    
    visualizer = MetadataTrackingVisualizer(console)
    visualizer.create_sample_metadata()
    
    console.print("[bold bright_cyan]MigrateX Metadata Tracking Demo[/bold bright_cyan]\n")
    
    console.input("Press Enter to view metadata dashboard...")
    visualizer.display_metadata_dashboard()
    
    console.input("\nPress Enter to view dependency graph...")
    visualizer.display_dependency_graph_visualization()
    
    console.input("\nPress Enter to view audit trail...")
    sample_id = list(visualizer.metadata_records.keys())[0]
    visualizer.display_complete_audit_trail(sample_id)

def run_pipeline_demo(console: Console):
    """Run pipeline progress demonstration."""
    from migratex.cli.visualizer import ModuleTreeVisualizer
    import time
    
    visualizer = ModuleTreeVisualizer()
    
    # Simulate pipeline stages
    stages = [
        ("📁 Repository Ingestion", 15),
        ("🔍 AST Generation", 25),
        ("📦 Module Chunking", 35),
        ("🤖 RAG Retrieval", 55),
        ("🔄 LLM Translation", 75),
        ("🧪 Test Generation", 85),
        ("⚡ Validation", 95),
        ("✅ Complete", 100)
    ]
    
    console.print("[bold bright_magenta]MigrateX Pipeline Demo[/bold bright_magenta]\n")
    
    for stage_name, progress in stages:
        visualizer.display_pipeline_progress(stage_name, progress, progress//10, 10)
        time.sleep(1.5)
    
    console.input("\nPipeline complete! Press Enter to continue...")

def run_rag_demo(console: Console):
    """Run RAG system demonstration."""
    from migratex.cli.visualizer import ModuleTreeVisualizer
    
    visualizer = ModuleTreeVisualizer()
    
    sample_query = "void buffer_init(CircularBuffer* buffer, size_t capacity) { buffer->data = malloc(capacity * sizeof(int)); buffer->size = capacity; buffer->head = 0; buffer->tail = 0; buffer->count = 0; }"
    
    sample_examples = [
        {"similarity": 0.942, "type": "Code Example", "description": "C struct initialization to Rust struct impl", "tokens": 340},
        {"similarity": 0.897, "type": "Style Guide", "description": "Rust memory safety patterns", "tokens": 285},
        {"similarity": 0.873, "type": "Pattern", "description": "Builder pattern for initialization", "tokens": 220},
        {"similarity": 0.841, "type": "Feedback", "description": "Human correction: avoid unsafe blocks", "tokens": 195},
        {"similarity": 0.819, "type": "Code Example", "description": "Circular buffer implementation", "tokens": 380},
    ]
    
    console.print("[bold bright_blue]MigrateX RAG System Demo[/bold bright_blue]\n")
    visualizer.display_rag_context_retrieval(sample_query, sample_examples)
    
    console.input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()