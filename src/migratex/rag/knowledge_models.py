"""Knowledge base models for RAG pipeline."""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class FeedbackRating(Enum):
    """Rating scale for human feedback."""
    EXCELLENT = 5
    GOOD = 4
    AVERAGE = 3
    POOR = 2
    TERRIBLE = 1


@dataclass
class CodeSnippet:
    """A code translation example."""
    source_code: str
    target_code: str
    source_language: str
    target_language: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeSnippet":
        """Create from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class StyleGuide:
    """Organizational coding standards and style guides."""
    title: str
    content: str
    language: str | None = None
    category: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StyleGuide":
        """Create from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class ArchitecturalPattern:
    """Architectural patterns and design guidelines."""
    name: str
    description: str
    example_code: str | None = None
    language: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArchitecturalPattern":
        """Create from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class HumanFeedback:
    """Human feedback on code translations."""
    original_code: str
    generated_translation: str
    corrected_translation: str | None = None
    feedback_text: str | None = None
    rating: int | None = None  # 1-5 scale
    source_language: str = "unknown"
    target_language: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HumanFeedback":
        """Create from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    @property
    def is_positive(self) -> bool:
        """Check if feedback is positive (rating >= 4 or has correction)."""
        if self.rating and self.rating >= 4:
            return True
        return self.corrected_translation is not None

    @property
    def feedback_quality(self) -> str:
        """Get qualitative feedback quality."""
        if not self.rating:
            return "unrated"

        if self.rating >= 4:
            return "positive"
        elif self.rating == 3:
            return "neutral"
        else:
            return "negative"


class KnowledgeBase:
    """
    Central repository for all knowledge types used in RAG.
    
    Manages code snippets, style guides, architectural patterns,
    and human feedback in a structured way with persistence.
    """

    def __init__(self):
        self.code_snippets: dict[str, CodeSnippet] = {}
        self.style_guides: dict[str, StyleGuide] = {}
        self.architectural_patterns: dict[str, ArchitecturalPattern] = {}
        self.human_feedback: dict[str, HumanFeedback] = {}

    def add_code_snippet(self, snippet: CodeSnippet) -> str:
        """Add a code snippet and return its ID."""
        self.code_snippets[snippet.id] = snippet
        return snippet.id

    def add_style_guide(self, guide: StyleGuide) -> str:
        """Add a style guide and return its ID."""
        self.style_guides[guide.id] = guide
        return guide.id

    def add_architectural_pattern(self, pattern: ArchitecturalPattern) -> str:
        """Add an architectural pattern and return its ID."""
        self.architectural_patterns[pattern.id] = pattern
        return pattern.id

    def add_human_feedback(self, feedback: HumanFeedback) -> str:
        """Add human feedback and return its ID."""
        self.human_feedback[feedback.id] = feedback
        return feedback.id

    def get_code_snippet(self, snippet_id: str) -> CodeSnippet | None:
        """Get a code snippet by ID."""
        return self.code_snippets.get(snippet_id)

    def get_style_guide(self, guide_id: str) -> StyleGuide | None:
        """Get a style guide by ID."""
        return self.style_guides.get(guide_id)

    def get_architectural_pattern(self, pattern_id: str) -> ArchitecturalPattern | None:
        """Get an architectural pattern by ID."""
        return self.architectural_patterns.get(pattern_id)

    def get_human_feedback(self, feedback_id: str) -> HumanFeedback | None:
        """Get human feedback by ID."""
        return self.human_feedback.get(feedback_id)

    def find_code_snippets(
        self,
        source_language: str | None = None,
        target_language: str | None = None,
        limit: int | None = None
    ) -> list[CodeSnippet]:
        """Find code snippets by criteria."""
        results = []

        for snippet in self.code_snippets.values():
            if source_language and snippet.source_language != source_language:
                continue
            if target_language and snippet.target_language != target_language:
                continue

            results.append(snippet)

            if limit and len(results) >= limit:
                break

        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def find_style_guides(
        self,
        language: str | None = None,
        category: str | None = None,
        limit: int | None = None
    ) -> list[StyleGuide]:
        """Find style guides by criteria."""
        results = []

        for guide in self.style_guides.values():
            if language and guide.language != language:
                continue
            if category and guide.category != category:
                continue

            results.append(guide)

            if limit and len(results) >= limit:
                break

        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def find_architectural_patterns(
        self,
        language: str | None = None,
        limit: int | None = None
    ) -> list[ArchitecturalPattern]:
        """Find architectural patterns by criteria."""
        results = []

        for pattern in self.architectural_patterns.values():
            if language and pattern.language != language:
                continue

            results.append(pattern)

            if limit and len(results) >= limit:
                break

        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def find_human_feedback(
        self,
        source_language: str | None = None,
        target_language: str | None = None,
        positive_only: bool = False,
        limit: int | None = None
    ) -> list[HumanFeedback]:
        """Find human feedback by criteria."""
        results = []

        for feedback in self.human_feedback.values():
            if source_language and feedback.source_language != source_language:
                continue
            if target_language and feedback.target_language != target_language:
                continue
            if positive_only and not feedback.is_positive:
                continue

            results.append(feedback)

            if limit and len(results) >= limit:
                break

        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        # Code snippet statistics
        snippet_languages = {}
        for snippet in self.code_snippets.values():
            key = f"{snippet.source_language}->{snippet.target_language}"
            snippet_languages[key] = snippet_languages.get(key, 0) + 1

        # Style guide statistics
        guide_languages = {}
        guide_categories = {}
        for guide in self.style_guides.values():
            if guide.language:
                guide_languages[guide.language] = guide_languages.get(guide.language, 0) + 1
            guide_categories[guide.category] = guide_categories.get(guide.category, 0) + 1

        # Feedback statistics
        feedback_ratings = {}
        positive_feedback = 0
        for feedback in self.human_feedback.values():
            if feedback.rating:
                feedback_ratings[feedback.rating] = feedback_ratings.get(feedback.rating, 0) + 1
            if feedback.is_positive:
                positive_feedback += 1

        return {
            "code_snippets": {
                "total": len(self.code_snippets),
                "by_language_pair": snippet_languages
            },
            "style_guides": {
                "total": len(self.style_guides),
                "by_language": guide_languages,
                "by_category": guide_categories
            },
            "architectural_patterns": {
                "total": len(self.architectural_patterns)
            },
            "human_feedback": {
                "total": len(self.human_feedback),
                "positive": positive_feedback,
                "rating_distribution": feedback_ratings
            }
        }

    def save(self, path: str) -> None:
        """Save knowledge base to JSON file."""
        data = {
            "code_snippets": {k: v.to_dict() for k, v in self.code_snippets.items()},
            "style_guides": {k: v.to_dict() for k, v in self.style_guides.items()},
            "architectural_patterns": {k: v.to_dict() for k, v in self.architectural_patterns.items()},
            "human_feedback": {k: v.to_dict() for k, v in self.human_feedback.items()},
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> None:
        """Load knowledge base from JSON file."""
        if not Path(path).exists():
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Load code snippets
        if "code_snippets" in data:
            self.code_snippets = {
                k: CodeSnippet.from_dict(v)
                for k, v in data["code_snippets"].items()
            }

        # Load style guides
        if "style_guides" in data:
            self.style_guides = {
                k: StyleGuide.from_dict(v)
                for k, v in data["style_guides"].items()
            }

        # Load architectural patterns
        if "architectural_patterns" in data:
            self.architectural_patterns = {
                k: ArchitecturalPattern.from_dict(v)
                for k, v in data["architectural_patterns"].items()
            }

        # Load human feedback
        if "human_feedback" in data:
            self.human_feedback = {
                k: HumanFeedback.from_dict(v)
                for k, v in data["human_feedback"].items()
            }

    def clear(self) -> None:
        """Clear all knowledge base data."""
        self.code_snippets.clear()
        self.style_guides.clear()
        self.architectural_patterns.clear()
        self.human_feedback.clear()
