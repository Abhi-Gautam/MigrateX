"""Enhanced progress display for per-function coverage analysis."""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.tree import Tree
from rich.text import Text
from rich.align import Align

from ..analysis.test_decision_engine import TestDecision
from ..analysis.coverage_analyzer import CoverageAnalysis, CoverageRecommendation, TestPriority


@dataclass
class FunctionAnalysisStatus:
    """Status of function analysis progress."""
    function_name: str
    status: str  # "pending", "analyzing", "deciding", "generating", "completed", "failed"
    coverage_analysis: Optional[CoverageAnalysis] = None
    decision: Optional[TestDecision] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None


class ProgressDisplayManager:
    """Enhanced progress display showing per-function coverage analysis."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.function_statuses: Dict[str, FunctionAnalysisStatus] = {}
        self.overall_progress: Optional[Progress] = None
        self.overall_task: Optional[TaskID] = None
        self.live_display: Optional[Live] = None
        
    def initialize_functions(self, functions: List[Dict]) -> None:
        """Initialize progress tracking for all functions."""
        self.function_statuses = {}
        for func in functions:
            self.function_statuses[func["name"]] = FunctionAnalysisStatus(
                function_name=func["name"],
                status="pending"
            )
    
    def start_live_display(self) -> None:
        """Start the live progress display."""
        self.overall_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=self.console
        )
        
        total_functions = len(self.function_statuses)
        self.overall_task = self.overall_progress.add_task(
            "🤖 AI Coverage Analysis", 
            total=total_functions
        )
        
        self.live_display = Live(
            self._generate_display(),
            console=self.console,
            refresh_per_second=2,
            vertical_overflow="visible"
        )
        self.live_display.start()
    
    def stop_live_display(self) -> None:
        """Stop the live progress display."""
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
    
    def update_function_status(
        self, 
        function_name: str, 
        status: str,
        coverage_analysis: Optional[CoverageAnalysis] = None,
        decision: Optional[TestDecision] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update status for a specific function."""
        if function_name not in self.function_statuses:
            return
            
        func_status = self.function_statuses[function_name]
        old_status = func_status.status
        
        # Update status
        func_status.status = status
        func_status.coverage_analysis = coverage_analysis
        func_status.decision = decision
        func_status.error_message = error_message
        
        # Track timing
        if old_status == "pending" and status != "pending":
            func_status.start_time = time.time()
        elif status in ["completed", "failed"]:
            func_status.end_time = time.time()
        
        # Update overall progress
        if self.overall_progress and self.overall_task is not None:
            completed_count = sum(
                1 for f in self.function_statuses.values() 
                if f.status in ["completed", "failed"]
            )
            self.overall_progress.update(self.overall_task, completed=completed_count)
        
        # Update live display
        if self.live_display:
            self.live_display.update(self._generate_display())
    
    def _generate_display(self) -> Panel:
        """Generate the complete display layout."""
        
        # Create main components
        overall_panel = self._create_overall_progress_panel()
        detailed_table = self._create_detailed_function_table()
        summary_panel = self._create_summary_panel()
        
        # Combine into columns - create the columns content separately
        columns_content = Columns([
            Panel(detailed_table, title="🔍 Function Analysis Details", border_style="blue"),
            Panel(summary_panel, title="📊 Analysis Summary", border_style="green")
        ])
        
        # Create layout without string interpolation
        from rich.console import Group
        layout_group = Group(
            overall_panel,
            "",  # Empty line
            columns_content
        )
        
        # Stack overall progress on top
        final_layout = Panel(
            layout_group,
            title="🤖 MigrateX AI Coverage Analysis",
            border_style="bright_magenta",
            padding=(1, 2)
        )
        
        return final_layout
    
    def _create_overall_progress_panel(self) -> str:
        """Create overall progress display."""
        if not self.overall_progress:
            return "Initializing..."
        
        # Render progress bar to string
        with self.console.capture() as capture:
            self.console.print(self.overall_progress)
        
        return capture.get()
    
    def _create_detailed_function_table(self) -> Table:
        """Create detailed function analysis table."""
        table = Table(show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("Function", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Coverage", width=10, justify="center")
        table.add_column("Quality", width=10, justify="center")
        table.add_column("Decision", width=12)
        table.add_column("Priority", width=8, justify="center")
        table.add_column("Time", width=8, justify="right")
        
        for func_name, status in self.function_statuses.items():
            # Status with emoji
            status_text = self._get_status_display(status.status)
            
            # Coverage percentage
            coverage_text = "—"
            if status.coverage_analysis:
                coverage_text = f"{status.coverage_analysis.coverage_percentage}%"
            
            # Test quality
            quality_text = "—"
            if status.coverage_analysis:
                quality_text = status.coverage_analysis.existing_tests_quality
            
            # Decision
            decision_text = "—"
            if status.decision:
                decision_text = self._get_decision_display(status.decision.decision)
            
            # Priority
            priority_text = "—"
            if status.coverage_analysis:
                priority_text = self._get_priority_display(status.coverage_analysis.priority)
            
            # Elapsed time
            time_text = "—"
            if status.start_time:
                if status.end_time:
                    elapsed = status.end_time - status.start_time
                    time_text = f"{elapsed:.1f}s"
                else:
                    elapsed = time.time() - status.start_time
                    time_text = f"{elapsed:.1f}s"
            
            table.add_row(
                func_name[:18] + ("..." if len(func_name) > 18 else ""),
                status_text,
                coverage_text,
                quality_text,
                decision_text,
                priority_text,
                time_text
            )
        
        return table
    
    def _create_summary_panel(self) -> str:
        """Create analysis summary panel."""
        total = len(self.function_statuses)
        completed = sum(1 for f in self.function_statuses.values() if f.status == "completed")
        failed = sum(1 for f in self.function_statuses.values() if f.status == "failed")
        analyzing = sum(1 for f in self.function_statuses.values() if f.status in ["analyzing", "deciding", "generating"])
        pending = total - completed - failed - analyzing
        
        # Coverage statistics
        coverage_analyses = [
            f.coverage_analysis for f in self.function_statuses.values() 
            if f.coverage_analysis
        ]
        
        avg_coverage = 0
        if coverage_analyses:
            avg_coverage = sum(ca.coverage_percentage for ca in coverage_analyses) / len(coverage_analyses)
        
        # Decision statistics
        decisions = [f.decision for f in self.function_statuses.values() if f.decision]
        skip_decisions = sum(1 for d in decisions if d.decision == "skip")
        generate_decisions = sum(1 for d in decisions if d.decision == "generate")
        successful_generations = sum(1 for d in decisions if d.generation_success)
        
        # Build summary text
        summary_lines = [
            f"📋 [bold]Total Functions:[/bold] {total}",
            f"✅ [green]Completed:[/green] {completed}",
            f"❌ [red]Failed:[/red] {failed}",
            f"🔄 [yellow]Analyzing:[/yellow] {analyzing}",
            f"⏳ [dim]Pending:[/dim] {pending}",
            "",
            f"📊 [bold]Coverage Analysis:[/bold]",
            f"   Average Coverage: {avg_coverage:.1f}%",
            f"   Analyses Complete: {len(coverage_analyses)}/{total}",
            "",
            f"🤖 [bold]AI Decisions:[/bold]",
            f"   Skip Generation: {skip_decisions}",
            f"   Generate Tests: {generate_decisions}",
            f"   Successful Gens: {successful_generations}",
        ]
        
        return "\n".join(summary_lines)
    
    def _get_status_display(self, status: str) -> Text:
        """Get formatted status display."""
        status_map = {
            "pending": ("⏳", "dim"),
            "analyzing": ("🔍", "blue"),
            "deciding": ("🤔", "yellow"),
            "generating": ("🤖", "cyan"),
            "completed": ("✅", "green"),
            "failed": ("❌", "red")
        }
        
        emoji, style = status_map.get(status, ("❓", "dim"))
        return Text(f"{emoji} {status.title()}", style=style)
    
    def _get_decision_display(self, decision: str) -> Text:
        """Get formatted decision display."""
        decision_map = {
            "skip": ("⏭️", "dim"),
            "generate": ("🔧", "green"),
            "enhance": ("⚡", "yellow")
        }
        
        emoji, style = decision_map.get(decision, ("❓", "dim"))
        return Text(f"{emoji} {decision.title()}", style=style)
    
    def _get_priority_display(self, priority: TestPriority) -> Text:
        """Get formatted priority display."""
        priority_map = {
            TestPriority.HIGH: ("🔥", "red"),
            TestPriority.MEDIUM: ("🟡", "yellow"),
            TestPriority.LOW: ("🟢", "green")
        }
        
        emoji, style = priority_map.get(priority, ("❓", "dim"))
        return Text(f"{emoji} {priority.value.upper()}", style=style)
    
    def print_final_summary(self) -> None:
        """Print final analysis summary."""
        if not self.function_statuses:
            return
        
        # Calculate final statistics
        total = len(self.function_statuses)
        completed = sum(1 for f in self.function_statuses.values() if f.status == "completed")
        failed = sum(1 for f in self.function_statuses.values() if f.status == "failed")
        
        coverage_analyses = [
            f.coverage_analysis for f in self.function_statuses.values() 
            if f.coverage_analysis
        ]
        
        decisions = [f.decision for f in self.function_statuses.values() if f.decision]
        skip_decisions = sum(1 for d in decisions if d.decision == "skip")
        generate_decisions = sum(1 for d in decisions if d.decision == "generate")
        successful_generations = sum(1 for d in decisions if d.generation_success)
        
        # Calculate total time
        times = [
            f.end_time - f.start_time for f in self.function_statuses.values()
            if f.start_time and f.end_time
        ]
        total_time = sum(times) if times else 0
        
        # Create final summary panel
        summary_text = f"""
🎯 [bold green]Analysis Complete![/bold green]

📊 [bold]Final Results:[/bold]
   • Functions Analyzed: {completed}/{total}
   • Analysis Failures: {failed}
   • Total Time: {total_time:.1f}s
   • Average Time per Function: {total_time/max(completed, 1):.1f}s

🤖 [bold]AI Coverage Analysis:[/bold]
   • Coverage Analyses: {len(coverage_analyses)}
   • Average Coverage: {sum(ca.coverage_percentage for ca in coverage_analyses)/max(len(coverage_analyses), 1):.1f}%

⚡ [bold]Test Generation Decisions:[/bold]
   • Skip Generation: {skip_decisions}
   • Generate Tests: {generate_decisions}
   • Successful Generations: {successful_generations}
   • Generation Success Rate: {(successful_generations/max(generate_decisions, 1)*100):.1f}%
        """
        
        final_panel = Panel(
            summary_text.strip(),
            title="🏁 MigrateX Analysis Summary",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(final_panel)
        
        # Show any failures
        failed_functions = [
            f for f in self.function_statuses.values() 
            if f.status == "failed"
        ]
        
        if failed_functions:
            self.console.print("\n❌ [red]Failed Functions:[/red]")
            for func in failed_functions:
                error_msg = func.error_message or "Unknown error"
                self.console.print(f"   • {func.function_name}: {error_msg}")