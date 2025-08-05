"""Clean, minimal dashboard for module-level analysis progress."""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.text import Text
from rich.align import Align

from ..analysis.module_analyzer import SemanticModule
from ..analysis.module_coverage_analyzer import ModuleCoverageAnalysis, CoverageRecommendation, TestPriority


@dataclass
class ModuleAnalysisStatus:
    """Status of module analysis progress."""
    module_name: str
    module_type: str
    function_count: int
    status: str  # "pending", "analyzing", "completed", "failed"
    coverage_analysis: Optional[ModuleCoverageAnalysis] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None


class CleanDashboard:
    """Minimal, clean dashboard for module analysis progress."""
    
    def __init__(self, console: Optional[Console] = None, quiet: bool = False):
        self.console = console or Console()
        self.quiet = quiet
        self.module_statuses: Dict[str, ModuleAnalysisStatus] = {}
        self.overall_progress: Optional[Progress] = None
        self.overall_task: Optional[TaskID] = None
        self.live_display: Optional[Live] = None
        self.start_time: Optional[float] = None
        
    def initialize_modules(self, modules: List[SemanticModule]) -> None:
        """Initialize progress tracking for all modules."""
        self.module_statuses = {}
        self.start_time = time.time()
        
        for module in modules:
            self.module_statuses[module.name] = ModuleAnalysisStatus(
                module_name=module.name,
                module_type=module.module_type,
                function_count=len(module.functions),
                status="pending"
            )
    
    def start_analysis(self) -> None:
        """Start the analysis with minimal display."""
        if self.quiet:
            return
            
        total_modules = len(self.module_statuses)
        total_functions = sum(s.function_count for s in self.module_statuses.values())
        
        self.console.print(f"\n🤖 [bold cyan]Starting Module Analysis[/bold cyan]")
        self.console.print(f"📦 Modules to analyze: {total_modules}")
        self.console.print(f"⚙️  Total functions: {total_functions}")
        self.console.print("")
        
        # Create simple progress bar
        self.overall_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=self.console
        )
        
        self.overall_task = self.overall_progress.add_task(
            "Analyzing modules", 
            total=total_modules
        )
        
        self.live_display = Live(
            self._generate_simple_display(),
            console=self.console,
            refresh_per_second=1
        )
        self.live_display.start()
    
    def update_module_status(
        self, 
        module_name: str, 
        status: str,
        coverage_analysis: Optional[ModuleCoverageAnalysis] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update status for a specific module."""
        if module_name not in self.module_statuses:
            return
            
        module_status = self.module_statuses[module_name]
        old_status = module_status.status
        
        # Update status
        module_status.status = status
        module_status.coverage_analysis = coverage_analysis
        module_status.error_message = error_message
        
        # Track timing
        if old_status == "pending" and status != "pending":
            module_status.start_time = time.time()
        elif status in ["completed", "failed"]:
            module_status.end_time = time.time()
        
        # Update overall progress
        if self.overall_progress and self.overall_task is not None:
            completed_count = sum(
                1 for m in self.module_statuses.values() 
                if m.status in ["completed", "failed"]
            )
            self.overall_progress.update(self.overall_task, completed=completed_count)
        
        # Update live display
        if self.live_display and not self.quiet:
            self.live_display.update(self._generate_simple_display())
    
    def _generate_simple_display(self) -> Panel:
        """Generate a simple, clean display."""
        
        # Overall progress
        progress_text = ""
        if self.overall_progress:
            with self.console.capture() as capture:
                self.console.print(self.overall_progress)
            progress_text = capture.get()
        
        # Current module status
        current_module = None
        for module_status in self.module_statuses.values():
            if module_status.status == "analyzing":
                current_module = module_status
                break
        
        current_text = "Initializing..."
        if current_module:
            current_text = f"🔍 Analyzing: {current_module.module_name} ({current_module.function_count} functions)"
        
        # Simple stats
        completed = sum(1 for m in self.module_statuses.values() if m.status == "completed")
        failed = sum(1 for m in self.module_statuses.values() if m.status == "failed")
        total = len(self.module_statuses)
        
        stats_text = f"✅ Completed: {completed}  ❌ Failed: {failed}  📦 Total: {total}"
        
        # Combine into simple layout
        display_content = f"{progress_text}\n{current_text}\n\n{stats_text}"
        
        return Panel(
            display_content.strip(),
            title="🤖 MigrateX Module Analysis",
            border_style="cyan",
            padding=(1, 1)
        )
    
    def stop_analysis(self) -> None:
        """Stop the live display."""
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
    
    def print_final_summary(self) -> None:
        """Print a comprehensive final summary."""
        if not self.module_statuses:
            return
        
        # Calculate statistics
        total_modules = len(self.module_statuses)
        completed = sum(1 for m in self.module_statuses.values() if m.status == "completed")
        failed = sum(1 for m in self.module_statuses.values() if m.status == "failed")
        total_functions = sum(m.function_count for m in self.module_statuses.values())
        
        # Coverage statistics
        coverage_analyses = [
            m.coverage_analysis for m in self.module_statuses.values() 
            if m.coverage_analysis
        ]
        
        avg_coverage = 0
        if coverage_analyses:
            avg_coverage = sum(ca.coverage_percentage for ca in coverage_analyses) / len(coverage_analyses)
        
        # Recommendation statistics
        recommendations = {}
        priorities = {}
        for analysis in coverage_analyses:
            rec = analysis.recommendation.value
            recommendations[rec] = recommendations.get(rec, 0) + 1
            
            pri = analysis.priority.value
            priorities[pri] = priorities.get(pri, 0) + 1
        
        # Calculate total time
        total_time = 0
        if self.start_time:
            total_time = time.time() - self.start_time
        
        # Create summary panel
        summary_text = f"""
🎯 [bold green]Module Analysis Complete![/bold green]

📊 [bold]Analysis Results:[/bold]
   • Modules Analyzed: {completed}/{total_modules}
   • Total Functions: {total_functions}
   • Analysis Failures: {failed}
   • Total Time: {total_time:.1f}s
   • Average Time per Module: {total_time/max(completed, 1):.1f}s

🧪 [bold]Coverage Analysis:[/bold]
   • Average Coverage: {avg_coverage:.1f}%
   • Modules with Coverage Data: {len(coverage_analyses)}
"""
        
        # Add recommendation breakdown
        if recommendations:
            summary_text += "\n🤖 [bold]AI Recommendations:[/bold]\n"
            for rec, count in recommendations.items():
                emoji = {"sufficient": "✅", "generate_new": "🔧", "generate_additional": "➕", "enhance_existing": "⚡"}.get(rec, "❓")
                summary_text += f"   • {emoji} {rec.replace('_', ' ').title()}: {count}\n"
        
        # Add priority breakdown
        if priorities:
            summary_text += "\n📋 [bold]Priority Distribution:[/bold]\n"
            for pri, count in priorities.items():
                emoji = {"high": "🔥", "medium": "🟡", "low": "🟢"}.get(pri, "❓")
                summary_text += f"   • {emoji} {pri.title()}: {count}\n"
        
        final_panel = Panel(
            summary_text.strip(),
            title="🏁 MigrateX Analysis Summary",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(final_panel)
        
        # Show module details if requested
        if not self.quiet and coverage_analyses:
            self._print_module_details()
        
        # Show any failures
        failed_modules = [
            m for m in self.module_statuses.values() 
            if m.status == "failed"
        ]
        
        if failed_modules:
            self.console.print("\n❌ [red]Failed Modules:[/red]")
            for module in failed_modules:
                error_msg = module.error_message or "Unknown error"
                self.console.print(f"   • {module.module_name}: {error_msg}")
    
    def _print_module_details(self) -> None:
        """Print detailed module analysis results."""
        
        self.console.print("\n📋 [bold]Module Analysis Details:[/bold]")
        
        # Create detailed table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Module", style="cyan", width=25)
        table.add_column("Type", width=15)
        table.add_column("Functions", width=10, justify="center")
        table.add_column("Coverage", width=10, justify="center")
        table.add_column("Quality", width=12, justify="center")
        table.add_column("Recommendation", width=15)
        table.add_column("Priority", width=8, justify="center")
        
        for module_status in self.module_statuses.values():
            if module_status.status != "completed" or not module_status.coverage_analysis:
                continue
                
            analysis = module_status.coverage_analysis
            
            # Format cells
            module_name = module_status.module_name[:23] + ("..." if len(module_status.module_name) > 23 else "")
            module_type = module_status.module_type
            function_count = str(module_status.function_count)
            coverage = f"{analysis.coverage_percentage}%"
            quality = analysis.existing_tests_quality
            recommendation = analysis.recommendation.value.replace('_', ' ').title()
            priority = self._get_priority_emoji(analysis.priority) + " " + analysis.priority.value.upper()
            
            table.add_row(
                module_name,
                module_type,
                function_count,
                coverage,
                quality,
                recommendation,
                priority
            )
        
        self.console.print(table)
    
    def _get_priority_emoji(self, priority: TestPriority) -> str:
        """Get emoji for priority level."""
        priority_map = {
            TestPriority.HIGH: "🔥",
            TestPriority.MEDIUM: "🟡",
            TestPriority.LOW: "🟢"
        }
        return priority_map.get(priority, "❓")
    
    def print_quiet_progress(self, current_module: str, completed: int, total: int) -> None:
        """Print minimal progress for quiet mode."""
        if not self.quiet:
            return
            
        percentage = (completed / total) * 100 if total > 0 else 0
        self.console.print(f"[{completed}/{total}] ({percentage:.0f}%) Analyzing: {current_module}")