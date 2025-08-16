#!/usr/bin/env python3
"""
Generate sample outputs for MigrateX terminal demonstrations.

This script creates static output examples showing each pipeline stage.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from migratex.analysis.language_parser import LanguageParser, ExtractedModule


def generate_module_tree_output():
    """Generate module tree visualization output."""
    console = Console(width=100)
    
    print("=" * 80)
    print("DEMO OUTPUT 1: MODULE EXTRACTION TREE VISUALIZATION")
    print("=" * 80)
    
    # Create sample modules
    sample_modules = [
        ExtractedModule(id="mod_001", name="buffer_init", kind="function", 
                       source_code="void buffer_init() {\n    /* 12 lines of init code */\n}", 
                       start_byte=100, end_byte=200, dependencies=[], exports=["buffer_init"], file_path="buffer.c"),
        ExtractedModule(id="mod_002", name="buffer_size", kind="function", 
                       source_code="size_t buffer_size() {\n    /* 8 lines */\n}", 
                       start_byte=250, end_byte=320, dependencies=[], exports=["buffer_size"], file_path="buffer.c"),
        ExtractedModule(id="mod_003", name="buffer_is_empty", kind="function", 
                       source_code="bool buffer_is_empty() {\n    /* 5 lines */\n}", 
                       start_byte=350, end_byte=400, dependencies=[], exports=["buffer_is_empty"], file_path="buffer.c"),
        ExtractedModule(id="mod_004", name="buffer_push", kind="function", 
                       source_code="int buffer_push() {\n    /* 18 lines of push logic */\n}", 
                       start_byte=450, end_byte=600, dependencies=["buffer_is_full", "calculate_next_index"], exports=["buffer_push"], file_path="buffer.c"),
        ExtractedModule(id="mod_005", name="buffer_pop", kind="function", 
                       source_code="int buffer_pop() {\n    /* 14 lines */\n}", 
                       start_byte=650, end_byte=750, dependencies=["buffer_is_empty"], exports=["buffer_pop"], file_path="buffer.c"),
        ExtractedModule(id="mod_006", name="buffer_resize", kind="function", 
                       source_code="void buffer_resize() {\n    /* 35 lines of complex logic */\n}", 
                       start_byte=800, end_byte=1200, dependencies=["malloc", "memcpy", "buffer_size", "buffer_init"], exports=["buffer_resize"], file_path="buffer.c"),
    ]
    
    from migratex.cli.visualizer import ModuleTreeVisualizer
    visualizer = ModuleTreeVisualizer()
    visualizer.display_presentation_tree(sample_modules)
    
    print("\n")


def generate_pipeline_progress_output():
    """Generate pipeline progress visualization output."""
    console = Console(width=100)
    
    print("=" * 80)
    print("DEMO OUTPUT 2: 10-STAGE PIPELINE PROGRESS")
    print("=" * 80)
    
    from migratex.cli.visualizer import ModuleTreeVisualizer
    visualizer = ModuleTreeVisualizer()
    
    # Show different pipeline stages
    stages = [
        ("🔍 AST Generation", 25),
        ("🤖 RAG Retrieval", 55),
        ("🔄 LLM Translation", 75),
        ("✅ Complete", 100)
    ]
    
    for stage_name, progress in stages:
        print(f"\nPipeline Stage: {stage_name} ({progress}%)")
        print("-" * 60)
        visualizer.display_pipeline_progress(stage_name, progress, progress//10, 10)
        print()


def generate_metadata_tracking_output():
    """Generate metadata tracking visualization output."""
    console = Console(width=100)
    
    print("=" * 80)
    print("DEMO OUTPUT 3: METADATA TRACKING & AUDIT TRAIL")
    print("=" * 80)
    
    from migratex.cli.metadata_visualizer import MetadataTrackingVisualizer
    visualizer = MetadataTrackingVisualizer(console)
    visualizer.create_sample_metadata()
    
    print("\n--- METADATA DASHBOARD ---")
    visualizer.display_metadata_dashboard()
    
    print("\n--- DEPENDENCY GRAPH ---")
    visualizer.display_dependency_graph_visualization()
    
    print("\n--- COMPLETE AUDIT TRAIL ---")
    sample_id = list(visualizer.metadata_records.keys())[0]
    visualizer.display_complete_audit_trail(sample_id)
    
    print("\n")


def generate_rag_system_output():
    """Generate RAG system visualization output."""
    console = Console(width=100)
    
    print("=" * 80)
    print("DEMO OUTPUT 4: RAG SYSTEM CONTEXT RETRIEVAL")
    print("=" * 80)
    
    from migratex.cli.visualizer import ModuleTreeVisualizer
    visualizer = ModuleTreeVisualizer()
    
    sample_query = "void buffer_init(CircularBuffer* buffer, size_t capacity) { buffer->data = malloc(capacity * sizeof(int)); }"
    
    sample_examples = [
        {"similarity": 0.942, "type": "Code Example", "description": "C struct initialization to Rust struct impl", "tokens": 340},
        {"similarity": 0.897, "type": "Style Guide", "description": "Rust memory safety patterns", "tokens": 285},
        {"similarity": 0.873, "type": "Pattern", "description": "Builder pattern for initialization", "tokens": 220},
        {"similarity": 0.841, "type": "Feedback", "description": "Human correction: avoid unsafe blocks", "tokens": 195},
        {"similarity": 0.819, "type": "Code Example", "description": "Circular buffer implementation", "tokens": 380},
    ]
    
    visualizer.display_rag_context_retrieval(sample_query, sample_examples)
    print("\n")


def generate_translation_results_output():
    """Generate translation results visualization output."""
    console = Console(width=100)
    
    print("=" * 80)
    print("DEMO OUTPUT 5: SIDE-BY-SIDE TRANSLATION RESULTS")
    print("=" * 80)
    
    from migratex.cli.visualizer import ModuleTreeVisualizer
    visualizer = ModuleTreeVisualizer()
    
    original_code = """void buffer_init(CircularBuffer* buffer, size_t capacity) {
    buffer->data = malloc(capacity * sizeof(int));
    buffer->size = capacity;
    buffer->head = 0;
    buffer->tail = 0;
    buffer->count = 0;
    
    if (buffer->data == NULL) {
        fprintf(stderr, "Memory allocation failed\\n");
        exit(1);
    }
}"""
    
    translated_code = """impl CircularBuffer {
    pub fn new(capacity: usize) -> Result<Self, BufferError> {
        let data = vec![0; capacity];
        Ok(CircularBuffer {
            data,
            capacity,
            head: 0,
            tail: 0,
            count: 0,
        })
    }
}"""
    
    metadata = {
        "deps_resolved": "0/0",
        "tests_generated": "5 test cases",
        "memory_safe": "✅ Verified",
        "time_taken": "4.2s",
        "tokens_used": "2,840"
    }
    
    visualizer.display_translation_results(original_code, translated_code, 0.947, metadata)
    print("\n")


def generate_success_metrics_output():
    """Generate final success metrics output."""
    console = Console(width=100)
    
    print("=" * 80)
    print("DEMO OUTPUT 6: FINAL SUCCESS METRICS & ACHIEVEMENTS")
    print("=" * 80)
    
    from migratex.cli.visualizer import ModuleTreeVisualizer
    visualizer = ModuleTreeVisualizer()
    
    visualizer.display_success_metrics(
        total_modules=23,
        successful=17,
        failed=2,
        cost_savings=0.22,
        time_taken=263.5  # 4m 23s
    )
    print("\n")


def main():
    """Generate all demo outputs."""
    console = Console()
    
    # Print header
    header = Panel(
        """
🚀 [bold bright_blue]MigrateX Terminal Demo Outputs[/bold bright_blue]

Generating sample outputs for each pipeline stage and visualization component.
These outputs demonstrate the compelling terminal experience of MigrateX.
        """.strip(),
        title="🎯 Demo Output Generator",
        border_style="bright_blue"
    )
    console.print(header)
    
    print("\n" + "=" * 100)
    print("MIGRATEX POC TERMINAL DEMONSTRATION OUTPUTS")
    print("=" * 100)
    
    # Generate all outputs
    generate_module_tree_output()
    generate_pipeline_progress_output()
    generate_metadata_tracking_output()
    generate_rag_system_output()
    generate_translation_results_output()
    generate_success_metrics_output()
    
    # Final summary
    print("=" * 100)
    print("DEMONSTRATION COMPLETE")
    print("=" * 100)
    print("\nKey Demonstrations Completed:")
    print("✅ Module Extraction Tree with Self-Contained Analysis")
    print("✅ 10-Stage Pipeline Progress Visualization")
    print("✅ Complete Metadata Tracking & Audit Trail")
    print("✅ RAG System Context Retrieval & Cost Optimization")
    print("✅ Side-by-Side Translation Results")
    print("✅ Final Success Metrics & Performance Comparison")
    print("\nThese outputs showcase MigrateX's intelligent approach to:")
    print("• Dependency-aware module extraction")
    print("• Cost-efficient RAG-powered translation")
    print("• Complete transformation metadata tracking")
    print("• Enterprise-grade audit compliance")
    print("• 68.7% Pass@1 success rate with 67% cost reduction")


if __name__ == "__main__":
    main()