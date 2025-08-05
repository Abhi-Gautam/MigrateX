"""Translation result models and data structures."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid


class TranslationStatus(Enum):
    """Status of a translation operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class TranslationLanguage(Enum):
    """Supported translation languages."""
    RUST = "rust"
    GO = "go"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


@dataclass
class TranslationContext:
    """Context information for guiding translation decisions."""
    source_language: str
    target_language: TranslationLanguage
    module_type: str  # "feature", "utility", "data_structure", etc.
    dependencies: List[str] = field(default_factory=list)
    existing_tests: Optional[str] = None
    architectural_patterns: List[str] = field(default_factory=list)
    performance_requirements: Optional[str] = None
    safety_requirements: Optional[str] = None
    
    
@dataclass 
class TranslationError:
    """Represents an error that occurred during translation."""
    error_type: str  # "syntax", "semantic", "dependency", "api"
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    severity: str = "error"  # "error", "warning", "info"


@dataclass
class TranslationResult:
    """Complete result of a translation operation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_module_name: str = ""
    target_module_name: str = ""
    source_language: str = ""
    target_language: TranslationLanguage = TranslationLanguage.RUST
    status: TranslationStatus = TranslationStatus.PENDING
    
    # Core translation outputs
    translated_code: str = ""
    translated_tests: str = ""
    build_configuration: Dict[str, Any] = field(default_factory=dict)
    
    # Translation metadata
    translation_notes: List[str] = field(default_factory=list)
    semantic_changes: List[str] = field(default_factory=list)
    api_changes: List[str] = field(default_factory=list)
    performance_notes: List[str] = field(default_factory=list)
    
    # Quality metrics
    confidence_score: float = 0.0  # 0-100
    complexity_delta: float = 0.0  # Change in complexity
    translation_time: float = 0.0  # Time taken in seconds
    
    # Error handling
    errors: List[TranslationError] = field(default_factory=list)
    warnings: List[TranslationError] = field(default_factory=list)
    
    # AI reasoning
    ai_reasoning: str = ""
    alternative_approaches: List[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if translation has any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if translation has any warnings."""
        return len(self.warnings) > 0
    
    @property
    def is_successful(self) -> bool:
        """Check if translation completed successfully."""
        return self.status == TranslationStatus.COMPLETED and not self.has_errors
    
    def add_error(self, error_type: str, message: str, line_number: Optional[int] = None, 
                  suggestion: Optional[str] = None, severity: str = "error"):
        """Add an error to the translation result."""
        error = TranslationError(
            error_type=error_type,
            message=message,
            line_number=line_number,
            suggestion=suggestion,
            severity=severity
        )
        
        if severity == "error":
            self.errors.append(error)
        else:
            self.warnings.append(error)
    
    def add_semantic_change(self, change: str):
        """Add a semantic change note."""
        self.semantic_changes.append(change)
    
    def add_api_change(self, change: str):
        """Add an API change note."""
        self.api_changes.append(change)
    
    def add_translation_note(self, note: str):
        """Add a general translation note."""
        self.translation_notes.append(note)


@dataclass
class BatchTranslationResult:
    """Result of translating multiple modules together."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str = ""
    source_language: str = ""
    target_language: TranslationLanguage = TranslationLanguage.RUST
    
    # Individual translation results
    module_results: List[TranslationResult] = field(default_factory=list)
    
    # Project-level outputs
    project_structure: Dict[str, str] = field(default_factory=dict)  # file_path -> content
    build_files: Dict[str, str] = field(default_factory=dict)  # Cargo.toml, go.mod, etc.
    documentation: str = ""
    migration_guide: str = ""
    
    # Batch statistics
    total_modules: int = 0
    successful_modules: int = 0
    failed_modules: int = 0
    total_translation_time: float = 0.0
    
    # Cross-module analysis
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    shared_utilities: List[str] = field(default_factory=list)
    architectural_recommendations: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of translations."""
        if self.total_modules == 0:
            return 0.0
        return (self.successful_modules / self.total_modules) * 100
    
    @property
    def all_errors(self) -> List[TranslationError]:
        """Get all errors from all module translations."""
        errors = []
        for result in self.module_results:
            errors.extend(result.errors)
        return errors
    
    @property
    def all_warnings(self) -> List[TranslationError]:
        """Get all warnings from all module translations."""
        warnings = []
        for result in self.module_results:
            warnings.extend(result.warnings)
        return warnings
    
    def add_module_result(self, result: TranslationResult):
        """Add a module translation result to the batch."""
        self.module_results.append(result)
        self.total_modules += 1
        
        if result.is_successful:
            self.successful_modules += 1
        else:
            self.failed_modules += 1
        
        self.total_translation_time += result.translation_time
    
    def get_successful_results(self) -> List[TranslationResult]:
        """Get only the successful translation results."""
        return [r for r in self.module_results if r.is_successful]
    
    def get_failed_results(self) -> List[TranslationResult]:
        """Get only the failed translation results."""
        return [r for r in self.module_results if not r.is_successful]