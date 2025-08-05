"""CLI visualization components using Rich."""

from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from migratex.analysis.language_parser import LanguageParser, ExtractedModule

console = Console()


class ModuleTreeVisualizer:
    """Visualizes module extraction and dependency trees."""
    
    def __init__(self):
        self.console = console
        self.parser = LanguageParser()
        
    def analyze_repository(self, repo_path: Path, source_language: Optional[str] = None) -> None:
        """Analyze repository and display results."""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing repository...", total=None)
            
            # Extract modules from all source files
            modules = []
            
            # Find all source files based on language
            if source_language:
                extensions = self._get_extensions_for_language(source_language)
            else:
                # Try to auto-detect by looking for common source files
                extensions = ['.c', '.h', '.cpp', '.hpp', '.cc', '.java', '.py']
            
            source_files = []
            for ext in extensions:
                source_files.extend(repo_path.rglob(f'*{ext}'))
            
            # Extract modules from each file
            for file_path in source_files:
                try:
                    # Auto-detect language from extension if not specified
                    lang = source_language or self.parser._detect_language(file_path)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    file_modules = self.parser.extract_modules(
                        code, lang, str(file_path)
                    )
                    
                    modules.extend(file_modules)
                except Exception as e:
                    # Skip files that can't be parsed
                    console.print(f"[yellow]Warning:[/yellow] Skipped {file_path}: {e}")
            
            progress.update(task, completed=100)
            
        self.display_module_tree(modules)
        self.display_dependency_analysis(modules)
        
    def display_module_tree(self, modules: List[ExtractedModule]) -> None:
        """Display extracted modules in tree format."""
        tree = Tree("📁 Extracted Modules")
        
        # Group modules by type
        functions_tree = tree.add("🔧 Functions")
        classes_tree = tree.add("📦 Classes")
        methods_tree = tree.add("🔨 Methods")
        
        for module in modules:
            if module.kind == "function":
                icon = "✅" if len(module.dependencies) == 0 else "⚠️"
                dep_info = f" ({len(module.dependencies)} deps)" if module.dependencies else ""
                functions_tree.add(f"{icon} {module.name}{dep_info}")
            elif module.kind == "class":
                icon = "✅" if len(module.dependencies) == 0 else "⚠️"
                dep_info = f" ({len(module.dependencies)} deps)" if module.dependencies else ""
                classes_tree.add(f"{icon} {module.name}{dep_info}")
            elif module.kind == "method":
                icon = "✅" if len(module.dependencies) == 0 else "⚠️"
                dep_info = f" ({len(module.dependencies)} deps)" if module.dependencies else ""
                methods_tree.add(f"{icon} {module.name}{dep_info}")
                
        console.print(tree)
        
    def display_dependency_analysis(self, modules: List[ExtractedModule]) -> None:
        """Display dependency analysis table."""
        table = Table(title="🔗 Dependency Analysis")
        table.add_column("Module", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Dependencies", style="green")
        table.add_column("Self-Contained", style="red")
        
        for module in modules:
            deps_str = ", ".join(module.dependencies[:3])
            if len(module.dependencies) > 3:
                deps_str += f" (+{len(module.dependencies) - 3} more)"
            
            is_self_contained = "✅" if len(module.dependencies) == 0 else "❌"
            
            table.add_row(
                module.name,
                module.kind,
                deps_str or "None",
                is_self_contained
            )
            
        console.print(table)
    
    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for a specific language."""
        language_extensions = {
            'c': ['.c', '.h'],
            'cpp': ['.cpp', '.hpp', '.cc', '.cxx', '.c++', '.hh', '.hxx'],
            'c++': ['.cpp', '.hpp', '.cc', '.cxx', '.c++', '.hh', '.hxx'],
            'java': ['.java'],
            'python': ['.py'],
            'c#': ['.cs'],
            'csharp': ['.cs'],
        }
        return language_extensions.get(language.lower(), [])
        
    def _mock_extract_modules(self, repo_path: Path) -> List[dict]:
        """Mock module extraction for testing."""
        # TODO: Replace with actual Rust library calls
        return [
            {
                "name": "main",
                "kind": "function", 
                "dependencies": ["printf", "helper_function"],
                "source_file": "main.c"
            },
            {
                "name": "helper_function",
                "kind": "function",
                "dependencies": ["strlen"],
                "source_file": "utils.c"
            },
            {
                "name": "Calculator",
                "kind": "class",
                "dependencies": ["math", "stdio"],
                "source_file": "calculator.c"
            }
        ]
        
    def display_translation_progress(self, modules: List[dict]) -> None:
        """Display translation progress with status indicators."""
        tree = Tree("🔄 Translation Progress")
        
        for module in modules:
            status_icon = "⏳"  # Default to pending
            if module.get("compiled", False):
                status_icon = "✅"
            elif module.get("translated", False):
                status_icon = "🔄"
            elif module.get("failed", False):
                status_icon = "❌"
                
            tree.add(f"{status_icon} {module['name']} → {module.get('target_name', 'pending')}")
            
        console.print(tree)
        
    def display_metadata_inspector(self, module_id: str, metadata: dict) -> None:
        """Display detailed metadata for a specific module."""
        panel_content = f"""
🆔 ID: {metadata.get('id', 'N/A')}
📍 Source: {metadata.get('source_path', 'N/A')}
🎯 Target: {metadata.get('target_path', 'N/A')}
🔗 Dependencies: {', '.join(metadata.get('dependencies', []))}
📊 Status: {metadata.get('status', 'pending')}
🛠️  Transforms: {', '.join(metadata.get('transforms', []))}
👤 Feedback: {metadata.get('human_feedback', 'None')}
        """
        
        panel = Panel(
            panel_content.strip(),
            title=f"📋 Module: {metadata.get('name', module_id)}",
            border_style="blue"
        )
        
        console.print(panel)