"""CLI commands for RAG knowledge base management."""

import json
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..rag import RAGPipeline, RAGConfig


def run_knowledge_add_example_command(
    source_code: str,
    target_code: str,
    source_language: str = "c",
    target_language: str = "rust",
    description: Optional[str] = None,
    knowledge_base_path: Optional[str] = None
) -> None:
    """Add a code translation example to the knowledge base."""
    
    console = Console()
    
    try:
        # Initialize RAG pipeline
        config = RAGConfig(knowledge_base_path=knowledge_base_path)
        rag_pipeline = RAGPipeline(config=config)
        
        # Add the code example
        example_id = rag_pipeline.add_code_snippet(
            source_code=source_code,
            target_code=target_code,
            source_language=source_language,
            target_language=target_language,
            description=description or f"{source_language} to {target_language} translation example"
        )
        
        # Save the knowledge base
        if knowledge_base_path:
            rag_pipeline.save_knowledge_base(knowledge_base_path)
        
        console.print(f"✅ [green]Code example added successfully![/green]")
        console.print(f"   📝 Example ID: {example_id}")
        console.print(f"   🔄 Translation: {source_language} → {target_language}")
        
        if description:
            console.print(f"   📄 Description: {description}")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to add code example:[/red] {e}")


def run_knowledge_add_style_guide_command(
    title: str,
    content: str,
    language: Optional[str] = None,
    category: str = "general",
    knowledge_base_path: Optional[str] = None
) -> None:
    """Add a style guide to the knowledge base."""
    
    console = Console()
    
    try:
        # Initialize RAG pipeline
        config = RAGConfig(knowledge_base_path=knowledge_base_path)
        rag_pipeline = RAGPipeline(config=config)
        
        # Add the style guide
        guide_id = rag_pipeline.add_style_guide(
            title=title,
            content=content,
            language=language,
            category=category
        )
        
        # Save the knowledge base
        if knowledge_base_path:
            rag_pipeline.save_knowledge_base(knowledge_base_path)
        
        console.print(f"✅ [green]Style guide added successfully![/green]")
        console.print(f"   📝 Guide ID: {guide_id}")
        console.print(f"   📋 Title: {title}")
        console.print(f"   🏷️  Category: {category}")
        
        if language:
            console.print(f"   💻 Language: {language}")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to add style guide:[/red] {e}")


def run_knowledge_add_pattern_command(
    name: str,
    description: str,
    example_code: Optional[str] = None,
    language: Optional[str] = None,
    knowledge_base_path: Optional[str] = None
) -> None:
    """Add an architectural pattern to the knowledge base."""
    
    console = Console()
    
    try:
        # Initialize RAG pipeline
        config = RAGConfig(knowledge_base_path=knowledge_base_path)
        rag_pipeline = RAGPipeline(config=config)
        
        # Add the architectural pattern
        pattern_id = rag_pipeline.add_architectural_pattern(
            name=name,
            description=description,
            example_code=example_code,
            language=language
        )
        
        # Save the knowledge base
        if knowledge_base_path:
            rag_pipeline.save_knowledge_base(knowledge_base_path)
        
        console.print(f"✅ [green]Architectural pattern added successfully![/green]")
        console.print(f"   📝 Pattern ID: {pattern_id}")
        console.print(f"   🏗️  Name: {name}")
        
        if language:
            console.print(f"   💻 Language: {language}")
        
        if example_code:
            console.print(f"   📄 Includes example code")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to add architectural pattern:[/red] {e}")


def run_knowledge_add_feedback_command(
    original_code: str,
    generated_translation: str,
    corrected_translation: Optional[str] = None,
    feedback_text: Optional[str] = None,
    rating: Optional[int] = None,
    source_language: str = "c",
    target_language: str = "rust",
    knowledge_base_path: Optional[str] = None
) -> None:
    """Add human feedback to the knowledge base."""
    
    console = Console()
    
    # Validate rating
    if rating is not None and (rating < 1 or rating > 5):
        console.print("❌ [red]Rating must be between 1 and 5[/red]")
        return
    
    try:
        # Initialize RAG pipeline
        config = RAGConfig(knowledge_base_path=knowledge_base_path)
        rag_pipeline = RAGPipeline(config=config)
        
        # Add the feedback
        feedback_id = rag_pipeline.add_human_feedback(
            original_code=original_code,
            generated_translation=generated_translation,
            corrected_translation=corrected_translation,
            feedback_text=feedback_text,
            rating=rating,
            source_language=source_language,
            target_language=target_language
        )
        
        # Save the knowledge base
        if knowledge_base_path:
            rag_pipeline.save_knowledge_base(knowledge_base_path)
        
        console.print(f"✅ [green]Human feedback added successfully![/green]")
        console.print(f"   📝 Feedback ID: {feedback_id}")
        console.print(f"   🔄 Translation: {source_language} → {target_language}")
        
        if rating:
            console.print(f"   ⭐ Rating: {rating}/5")
        
        if corrected_translation:
            console.print(f"   ✏️  Includes correction")
        
        if feedback_text:
            console.print(f"   💬 Includes feedback text")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to add human feedback:[/red] {e}")


def run_knowledge_stats_command(
    knowledge_base_path: Optional[str] = None
) -> None:
    """Display knowledge base statistics."""
    
    console = Console()
    
    try:
        # Initialize RAG pipeline
        config = RAGConfig(knowledge_base_path=knowledge_base_path)
        rag_pipeline = RAGPipeline(config=config)
        
        # Get statistics
        stats = rag_pipeline.get_statistics()
        
        # Display overview
        overview_text = f"""
📊 **Knowledge Base Overview**

**Code Examples**: {stats['knowledge_base']['code_snippets']['total']} translations
**Style Guides**: {stats['knowledge_base']['style_guides']['total']} guides  
**Patterns**: {stats['knowledge_base']['architectural_patterns']['total']} patterns
**Human Feedback**: {stats['knowledge_base']['human_feedback']['total']} entries
**Vector Documents**: {stats['vector_store']['total_documents']} embedded documents
"""
        
        overview_panel = Panel(
            overview_text.strip(),
            title="🧠 RAG Knowledge Base Statistics",
            border_style="blue",
            padding=(1, 2)
        )
        
        console.print(overview_panel)
        
        # Code snippets breakdown
        if stats['knowledge_base']['code_snippets']['by_language_pair']:
            console.print("\n📝 [bold]Code Translation Examples by Language Pair:[/bold]")
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Language Pair", style="cyan")
            table.add_column("Count", justify="right")
            
            for lang_pair, count in stats['knowledge_base']['code_snippets']['by_language_pair'].items():
                table.add_row(lang_pair, str(count))
            
            console.print(table)
        
        # Style guides breakdown
        if stats['knowledge_base']['style_guides']['by_category']:
            console.print("\n📋 [bold]Style Guides by Category:[/bold]")
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Category", style="cyan")
            table.add_column("Count", justify="right")
            
            for category, count in stats['knowledge_base']['style_guides']['by_category'].items():
                table.add_row(category, str(count))
            
            console.print(table)
        
        # Human feedback breakdown
        if stats['knowledge_base']['human_feedback']['rating_distribution']:
            console.print("\n⭐ [bold]Human Feedback Rating Distribution:[/bold]")
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Rating", style="cyan")
            table.add_column("Count", justify="right")
            table.add_column("Quality", style="dim")
            
            quality_map = {5: "Excellent", 4: "Good", 3: "Average", 2: "Poor", 1: "Terrible"}
            
            for rating in sorted(stats['knowledge_base']['human_feedback']['rating_distribution'].keys(), reverse=True):
                count = stats['knowledge_base']['human_feedback']['rating_distribution'][rating]
                quality = quality_map.get(rating, "Unknown")
                table.add_row(f"{rating}/5", str(count), quality)
            
            console.print(table)
        
        # Vector store info
        console.print(f"\n🔍 [bold]Vector Store Information:[/bold]")
        console.print(f"   • Embedding Dimension: {stats['vector_store']['embedding_dimension']}")
        console.print(f"   • Total Documents: {stats['vector_store']['total_documents']}")
        console.print(f"   • Document Types: {', '.join(stats['vector_store']['document_types'].keys())}")
        
        if knowledge_base_path:
            console.print(f"\n📁 [bold]Knowledge Base Path:[/bold] {knowledge_base_path}")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to get knowledge base statistics:[/red] {e}")


def run_knowledge_search_command(
    query: str,
    source_language: str = "c",
    target_language: str = "rust",
    max_results: int = 5,
    knowledge_base_path: Optional[str] = None
) -> None:
    """Search the knowledge base for relevant examples."""
    
    console = Console()
    
    try:
        # Initialize RAG pipeline
        config = RAGConfig(knowledge_base_path=knowledge_base_path)
        rag_pipeline = RAGPipeline(config=config)
        
        # Perform search
        retrieved_docs, context_metadata = rag_pipeline.retrieve_context(
            query_code=query,
            source_language=source_language,
            target_language=target_language,
            max_results=max_results
        )
        
        console.print(f"🔍 [bold]Search Results for: '{query}'[/bold]")
        console.print(f"   🔄 Translation: {source_language} → {target_language}")
        console.print(f"   📊 Found {len(retrieved_docs)} relevant documents")
        
        if retrieved_docs:
            for i, doc in enumerate(retrieved_docs, 1):
                doc_type = doc.metadata.get("type", "unknown")
                similarity = doc.metadata.get("similarity_score", 0)
                
                # Create title based on document type
                if doc_type == "code_snippet":
                    title = f"Code Example {i} (Similarity: {similarity:.2f})"
                elif doc_type == "style_guide":
                    title = f"Style Guide {i}: {doc.metadata.get('title', 'Untitled')}"
                elif doc_type == "architectural_pattern":
                    title = f"Pattern {i}: {doc.metadata.get('name', 'Unnamed')}"
                elif doc_type == "human_feedback":
                    rating = doc.metadata.get("rating", "N/A")
                    title = f"Feedback {i} (Rating: {rating}/5)"
                else:
                    title = f"Document {i} ({doc_type})"
                
                # Truncate content for display
                content = doc.page_content
                if len(content) > 300:
                    content = content[:300] + "..."
                
                panel = Panel(
                    content,
                    title=title,
                    border_style="green",
                    padding=(1, 2)
                )
                
                console.print(f"\n{panel}")
        else:
            console.print("\n💭 [yellow]No relevant documents found. Try a different query or add more examples to the knowledge base.[/yellow]")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to search knowledge base:[/red] {e}")


def run_knowledge_export_command(
    output_path: str,
    format: str = "json",
    knowledge_base_path: Optional[str] = None
) -> None:
    """Export knowledge base to a file."""
    
    console = Console()
    
    if format not in ["json"]:
        console.print("❌ [red]Only JSON format is currently supported[/red]")
        return
    
    try:
        # Initialize RAG pipeline
        config = RAGConfig(knowledge_base_path=knowledge_base_path)
        rag_pipeline = RAGPipeline(config=config)
        
        # Get all knowledge base data
        stats = rag_pipeline.get_statistics()
        
        # Export to JSON
        export_data = {
            "metadata": {
                "export_format": format,
                "export_version": "1.0",
                "total_entries": (
                    stats['knowledge_base']['code_snippets']['total'] +
                    stats['knowledge_base']['style_guides']['total'] +
                    stats['knowledge_base']['architectural_patterns']['total'] +
                    stats['knowledge_base']['human_feedback']['total']
                )
            },
            "statistics": stats
        }
        
        # Save to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"✅ [green]Knowledge base exported successfully![/green]")
        console.print(f"   📁 Output file: {output_path}")
        console.print(f"   📊 Total entries: {export_data['metadata']['total_entries']}")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to export knowledge base:[/red] {e}")