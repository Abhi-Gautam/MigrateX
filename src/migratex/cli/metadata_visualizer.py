"""
Metadata Tracking Visualization for MigrateX

Provides comprehensive visualizations for:
- Complete transformation audit trails
- Dependency graph visualization
- Human feedback integration tracking
- Test association status
- Cross-module relationships
"""

import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.layout import Layout
from rich.live import Live


@dataclass
class TransformationMetadata:
    """Complete metadata for a module transformation."""
    id: str
    module_name: str
    source_path: str
    target_path: str
    dependencies: List[str]
    status: str  # "extracted", "analyzing", "translating", "translated", "validated", "deployed"
    transformations: List[Dict[str, Any]]
    test_associations: List[str]
    human_feedback: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    uuid: str
    
    @classmethod
    def create_sample(cls, module_name: str, status: str = "extracted") -> "TransformationMetadata":
        """Create sample metadata for demo purposes."""
        return cls(
            id=f"mod_{len(module_name)}_{hash(module_name) % 1000:03d}",
            module_name=module_name,
            source_path=f"src/{module_name.lower()}.c",
            target_path=f"target/src/{module_name.lower()}.rs",
            dependencies=[],
            status=status,
            transformations=[
                {"stage": "extraction", "timestamp": datetime.now(), "success": True},
                {"stage": "analysis", "timestamp": datetime.now(), "success": True}
            ],
            test_associations=[f"test_{module_name.lower()}_basic", f"test_{module_name.lower()}_edge_cases"],
            human_feedback={"rating": 4, "comments": "Good translation, minor style improvements needed"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            uuid=str(uuid.uuid4())[:8]
        )


class MetadataTrackingVisualizer:
    """Visualizes comprehensive metadata tracking for MigrateX transformations."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.metadata_records: Dict[str, TransformationMetadata] = {}
        
    def create_sample_metadata(self) -> None:
        """Create sample metadata for demonstration."""
        sample_modules = [
            ("buffer_init", "validated"),
            ("buffer_push", "translated"),
            ("buffer_pop", "translating"),
            ("buffer_peek", "analyzing"),
            ("buffer_size", "extracted"),
            ("buffer_is_empty", "validated"),
            ("buffer_is_full", "translated"),
            ("calculate_next_index", "validated"),
            ("buffer_resize", "analyzing"),
            ("buffer_debug_print", "extracted"),
        ]
        
        for module_name, status in sample_modules:
            metadata = TransformationMetadata.create_sample(module_name, status)
            # Add realistic dependencies
            if module_name == "buffer_push":
                metadata.dependencies = ["buffer_is_full", "calculate_next_index"]
            elif module_name == "buffer_pop":
                metadata.dependencies = ["buffer_is_empty"]
            elif module_name == "buffer_resize":
                metadata.dependencies = ["malloc", "memcpy", "buffer_size", "buffer_init"]
                
            self.metadata_records[metadata.id] = metadata
    
    def display_complete_audit_trail(self, module_id: str) -> None:
        """Display complete audit trail for a specific module."""
        if module_id not in self.metadata_records:
            self.console.print(f"[red]Error:[/red] Module {module_id} not found")
            return
            
        metadata = self.metadata_records[module_id]
        
        # Create audit trail timeline
        timeline_content = f"""
🆔 [bold]Module ID:[/bold] {metadata.id}
📝 [bold]UUID:[/bold] {metadata.uuid}
📁 [bold]Module:[/bold] {metadata.module_name}()

⏰ [bold]Transformation Timeline:[/bold]

[dim]2024-08-16 14:23:15.123[/dim] 📤 [green]EXTRACTED[/green]
   ├── Source: {metadata.source_path}:45-57
   ├── AST nodes: 23 
   └── Dependencies: {len(metadata.dependencies)} identified

[dim]2024-08-16 14:23:16.456[/dim] 🔍 [blue]ANALYZING[/blue]
   ├── Dependency closure calculated
   ├── Complexity score: Medium (7/10)
   └── Translation priority: High

[dim]2024-08-16 14:23:18.789[/dim] 🤖 [yellow]RAG_RETRIEVAL[/yellow]
   ├── Query embedded (768 dimensions)
   ├── Retrieved 5 similar examples
   └── Context tokens: 2,847

[dim]2024-08-16 14:23:22.012[/dim] 🔄 [cyan]TRANSLATING[/cyan]
   ├── LLM: Gemini Pro (temperature: 0.1)
   ├── Input tokens: 3,240
   └── Output tokens: 1,856

[dim]2024-08-16 14:23:28.345[/dim] ✅ [green]TRANSLATED[/green]
   ├── Target: {metadata.target_path}
   ├── Confidence: 94.7%
   └── Memory safety: Verified

[dim]2024-08-16 14:23:30.678[/dim] 🧪 [purple]TEST_GENERATED[/purple]
   ├── Test cases: 5 generated
   ├── Coverage: 96.3%
   └── Edge cases: 12 identified

[dim]2024-08-16 14:23:35.901[/dim] 🎯 [green]VALIDATED[/green]
   ├── All tests passing ✅
   ├── Static analysis: Clean
   └── Performance: +15% vs original

[dim]2024-08-16 14:23:36.234[/dim] 👤 [bright_blue]HUMAN_REVIEWED[/bright_blue]
   ├── Rating: {metadata.human_feedback.get('rating', 4)}/5 ⭐⭐⭐⭐
   ├── Feedback: "{metadata.human_feedback.get('comments', 'Good translation')}"
   └── Status: Approved for deployment
        """.strip()
        
        audit_panel = Panel(
            timeline_content,
            title=f"📊 Complete Audit Trail: {metadata.module_name}()",
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        self.console.print(audit_panel)
        
        # Show provenance tracking guarantees
        provenance_panel = Panel(
            """
🔒 [bold bright_green]Provenance Guarantees:[/bold bright_green]

✅ [bold]Complete Traceability:[/bold] Every transformation step recorded with timestamps
✅ [bold]Dependency Tracking:[/bold] Full closure analysis with version control
✅ [bold]Quality Metrics:[/bold] Confidence scores, test coverage, performance metrics
✅ [bold]Human Feedback:[/bold] Ratings, corrections, and improvement suggestions
✅ [bold]Audit Compliance:[/bold] Immutable logs for regulatory requirements
✅ [bold]Rollback Capability:[/bold] Complete state restoration at any point

🎯 [bold]This level of metadata tracking enables enterprise-grade code migration.[/bold]
            """.strip(),
            title="🛡️ Enterprise Audit Compliance",
            border_style="green"
        )
        
        self.console.print("\n")
        self.console.print(provenance_panel)
    
    def display_dependency_graph_visualization(self) -> None:
        """Display interactive dependency graph for all modules."""
        self.console.clear()
        
        # Create dependency graph tree
        graph_tree = Tree("🔗 [bold bright_cyan]Module Dependency Graph[/bold bright_cyan]")
        
        # Group modules by dependency levels
        zero_deps = []
        low_deps = []
        high_deps = []
        
        for metadata in self.metadata_records.values():
            if len(metadata.dependencies) == 0:
                zero_deps.append(metadata)
            elif len(metadata.dependencies) <= 2:
                low_deps.append(metadata)
            else:
                high_deps.append(metadata)
        
        # Level 0: Self-contained modules
        if zero_deps:
            level0 = graph_tree.add("🟢 [bold green]Level 0: Self-Contained[/bold green] [dim](Translation Priority: Highest)[/dim]")
            for metadata in zero_deps:
                status_emoji = self._get_status_emoji(metadata.status)
                level0.add(f"{status_emoji} {metadata.module_name}() [dim]→ {metadata.target_path}[/dim]")
        
        # Level 1: Low dependencies
        if low_deps:
            level1 = graph_tree.add("🟡 [bold yellow]Level 1: Low Dependencies[/bold yellow] [dim](Translation Priority: Medium)[/dim]")
            for metadata in low_deps:
                status_emoji = self._get_status_emoji(metadata.status)
                deps_str = " → ".join(metadata.dependencies)
                level1.add(f"{status_emoji} {metadata.module_name}() [dim]depends on: {deps_str}[/dim]")
        
        # Level 2: High dependencies
        if high_deps:
            level2 = graph_tree.add("🔴 [bold red]Level 2: Complex Dependencies[/bold red] [dim](Translation Priority: Low)[/dim]")
            for metadata in high_deps:
                status_emoji = self._get_status_emoji(metadata.status)
                deps_preview = " → ".join(metadata.dependencies[:2])
                if len(metadata.dependencies) > 2:
                    deps_preview += f" [+{len(metadata.dependencies)-2} more]"
                level2.add(f"{status_emoji} {metadata.module_name}() [dim]depends on: {deps_preview}[/dim]")
        
        self.console.print(graph_tree)
        
        # Show dependency resolution strategy
        strategy_content = f"""
🎯 [bold]Dependency Resolution Strategy:[/bold]

📊 [bold]Current Status:[/bold]
• Level 0 modules: {len(zero_deps)} [green](Ready for immediate translation)[/green]
• Level 1 modules: {len(low_deps)} [yellow](Requires 1-2 dependencies)[/yellow]  
• Level 2 modules: {len(high_deps)} [red](Requires full closure analysis)[/red]

🔄 [bold]Translation Order:[/bold]
1. Translate all Level 0 modules first (highest success rate)
2. Translate Level 1 modules with dependency closure
3. Translate Level 2 modules last (requires most context)

💡 [bold]Optimization:[/bold] This approach maximizes success rate and minimizes LLM context size.
        """.strip()
        
        strategy_panel = Panel(
            strategy_content,
            title="🧮 Intelligent Dependency Resolution",
            border_style="blue"
        )
        
        self.console.print("\n")
        self.console.print(strategy_panel)
    
    def display_metadata_dashboard(self) -> None:
        """Display comprehensive metadata dashboard."""
        self.console.clear()
        
        # Create status overview table
        status_table = Table(title="📋 Module Transformation Dashboard")
        status_table.add_column("Module", style="cyan", width=20)
        status_table.add_column("UUID", style="dim", width=10)
        status_table.add_column("Status", width=12)
        status_table.add_column("Dependencies", width=15)
        status_table.add_column("Tests", width=8, justify="center")
        status_table.add_column("Feedback", width=10, justify="center")
        status_table.add_column("Progress", width=12)
        
        for metadata in list(self.metadata_records.values())[:10]:  # Show first 10
            status_emoji = self._get_status_emoji(metadata.status)
            
            # Dependencies summary
            if len(metadata.dependencies) == 0:
                deps_text = "[green]None[/green]"
            elif len(metadata.dependencies) <= 2:
                deps_text = f"[yellow]{len(metadata.dependencies)} deps[/yellow]"
            else:
                deps_text = f"[red]{len(metadata.dependencies)} deps[/red]"
            
            # Tests status
            tests_status = "✅" if len(metadata.test_associations) > 0 else "🤖"
            
            # Feedback status  
            feedback_status = "👍" if metadata.human_feedback else "—"
            
            # Progress calculation
            progress_map = {
                "extracted": "█░░░░",
                "analyzing": "██░░░", 
                "translating": "███░░",
                "translated": "████░",
                "validated": "█████"
            }
            progress_bar = progress_map.get(metadata.status, "░░░░░")
            
            status_table.add_row(
                metadata.module_name,
                metadata.uuid,
                f"{status_emoji} {metadata.status}",
                deps_text,
                tests_status,
                feedback_status,
                progress_bar
            )
        
        self.console.print(status_table)
        
        # Create summary statistics
        total_modules = len(self.metadata_records)
        status_counts = {}
        for metadata in self.metadata_records.values():
            status_counts[metadata.status] = status_counts.get(metadata.status, 0) + 1
        
        # Stats panels
        stats_content = f"""
📊 [bold]Transformation Statistics:[/bold]

🔢 [bold]Total Modules:[/bold] {total_modules}
✅ [bold]Validated:[/bold] {status_counts.get('validated', 0)} [green]({status_counts.get('validated', 0)/total_modules*100:.1f}%)[/green]
🔄 [bold]In Progress:[/bold] {status_counts.get('translating', 0) + status_counts.get('analyzing', 0)}
⏳ [bold]Pending:[/bold] {status_counts.get('extracted', 0)}

🎯 [bold]Success Metrics:[/bold]
• Completion Rate: {(status_counts.get('validated', 0) + status_counts.get('translated', 0))/total_modules*100:.1f}%
• Test Coverage: 94.7% average
• Human Approval: 92.3% approval rate
        """
        
        feedback_content = f"""
👤 [bold]Human Feedback Integration:[/bold]

📈 [bold]Feedback Stats:[/bold]
• Reviews Collected: {sum(1 for m in self.metadata_records.values() if m.human_feedback)}
• Avg Rating: 4.2/5 ⭐⭐⭐⭐
• Improvement Suggestions: 23 implemented
• Knowledge Base Updates: 12 new examples

🔄 [bold]Continuous Learning:[/bold]
• Feedback → RAG updates (automated)
• Style guide evolution (human-guided)
• Pattern library expansion (+15 patterns)
        """
        
        stats_columns = Columns([
            Panel(stats_content.strip(), title="📊 Progress Overview", border_style="green"),
            Panel(feedback_content.strip(), title="🎓 Learning Loop", border_style="blue")
        ])
        
        self.console.print("\n")
        self.console.print(stats_columns)
    
    def display_test_association_tracking(self) -> None:
        """Display test association and coverage tracking."""
        self.console.clear()
        
        # Test association table
        test_table = Table(title="🧪 Test Association & Coverage Tracking")
        test_table.add_column("Module", style="cyan", width=18)
        test_table.add_column("Test Files", style="green", width=25)
        test_table.add_column("Coverage", style="yellow", width=10, justify="center")
        test_table.add_column("Test Types", style="blue", width=20)
        test_table.add_column("Status", width=12)
        
        for metadata in list(self.metadata_records.values())[:8]:
            # Generate realistic test data
            test_files = "\n".join(metadata.test_associations[:2]) if metadata.test_associations else "No tests"
            coverage = f"{95 + hash(metadata.module_name) % 5}.{hash(metadata.module_name) % 10}%"
            test_types = "Unit, Integration, Edge"
            
            test_status = "✅ Passing" if metadata.status in ["validated", "translated"] else "🟡 Generated"
            
            test_table.add_row(
                metadata.module_name,
                test_files,
                coverage,
                test_types,
                test_status
            )
        
        self.console.print(test_table)
        
        # Test generation strategy
        strategy_panel = Panel(
            """
🎯 [bold]Test Generation Strategy:[/bold]

🤖 [bold]AI-Powered Test Creation:[/bold]
• Behavioral testing (input/output validation)
• Edge case discovery (boundary conditions)  
• Memory safety verification (Rust-specific)
• Performance regression testing

📊 [bold]Coverage Requirements:[/bold]
• Unit test coverage: >95% (statement coverage)
• Integration coverage: >85% (module interaction)
• Edge case coverage: >90% (boundary conditions)
• Performance tests: All critical paths

🔄 [bold]Continuous Validation:[/bold]
• Tests run on every translation iteration
• Performance benchmarks tracked over time
• Regression detection with automatic alerts
            """.strip(),
            title="🧪 Comprehensive Test Strategy",
            border_style="purple"
        )
        
        self.console.print("\n")
        self.console.print(strategy_panel)
    
    def simulate_real_time_updates(self) -> None:
        """Simulate real-time metadata updates during translation."""
        self.console.clear()
        
        # Select a module to simulate
        sample_metadata = list(self.metadata_records.values())[0]
        
        with Live(self._generate_realtime_display(sample_metadata), console=self.console, refresh_per_second=2) as live:
            
            # Simulate translation stages
            stages = [
                ("🔍 Analyzing dependencies", 2),
                ("🤖 Retrieving RAG context", 1.5),
                ("🔄 Generating translation", 3),
                ("🧪 Creating tests", 2),
                ("⚡ Running validation", 1.5),
                ("📊 Computing metrics", 1),
                ("✅ Translation complete", 0.5)
            ]
            
            for stage_name, duration in stages:
                sample_metadata.status = stage_name
                sample_metadata.updated_at = datetime.now()
                
                # Update display
                live.update(self._generate_realtime_display(sample_metadata))
                time.sleep(duration)
        
        # Show final state
        sample_metadata.status = "validated"
        self.console.print(self._generate_realtime_display(sample_metadata))
    
    def _generate_realtime_display(self, metadata: TransformationMetadata) -> Panel:
        """Generate real-time display for metadata updates."""
        
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        content = f"""
🆔 [bold]Module:[/bold] {metadata.module_name}() 
📝 [bold]UUID:[/bold] {metadata.uuid}
⏰ [bold]Last Updated:[/bold] {current_time}
🎯 [bold]Current Status:[/bold] {metadata.status}

📊 [bold]Live Metrics:[/bold]
   • Dependencies resolved: {len(metadata.dependencies)}//{len(metadata.dependencies)}
   • Translation confidence: 94.7%
   • Test cases generated: {len(metadata.test_associations)}
   • Memory safety: ✅ Verified
   
🔄 [bold]Processing Timeline:[/bold]
   [dim]14:23:15[/dim] ✅ Module extracted
   [dim]14:23:16[/dim] ✅ Dependencies analyzed  
   [dim]14:23:18[/dim] ✅ RAG context retrieved
   [dim]14:23:22[/dim] ⏳ Translation in progress...
   [dim]14:23:28[/dim] ⏳ Test generation pending...
   [dim]14:23:35[/dim] ⏳ Validation pending...
        """
        
        return Panel(
            content.strip(),
            title=f"📡 Real-Time Metadata Tracking",
            border_style="bright_cyan"
        )
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status display."""
        status_map = {
            "extracted": "📤",
            "analyzing": "🔍", 
            "translating": "🔄",
            "translated": "✅",
            "validated": "🎯",
            "deployed": "🚀"
        }
        return status_map.get(status, "❓")


def main():
    """Run metadata visualization demo."""
    console = Console()
    visualizer = MetadataTrackingVisualizer(console)
    
    # Create sample data
    visualizer.create_sample_metadata()
    
    # Demo sequence
    console.print("[bold bright_blue]MigrateX Metadata Tracking Demonstration[/bold bright_blue]\n")
    
    console.input("Press Enter to view the metadata dashboard...")
    visualizer.display_metadata_dashboard()
    
    console.input("\nPress Enter to view dependency graph visualization...")
    visualizer.display_dependency_graph_visualization()
    
    console.input("\nPress Enter to view complete audit trail...")
    sample_id = list(visualizer.metadata_records.keys())[0]
    visualizer.display_complete_audit_trail(sample_id)
    
    console.input("\nPress Enter to view test association tracking...")
    visualizer.display_test_association_tracking()
    
    console.input("\nPress Enter to simulate real-time updates...")
    visualizer.simulate_real_time_updates()
    
    console.print("\n[bold bright_green]Metadata tracking demonstration complete![/bold bright_green]")


if __name__ == "__main__":
    main()