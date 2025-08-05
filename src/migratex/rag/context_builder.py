"""Context builder for intelligent LLM prompt construction."""

import re
from dataclasses import dataclass
from typing import Any

from langchain.schema import Document


@dataclass
class ContextSection:
    """A section of context with metadata."""
    title: str
    content: str
    priority: int  # Lower number = higher priority
    token_estimate: int
    source_type: str  # code_snippet, style_guide, etc.


class ContextBuilder:
    """
    Intelligent context builder for LLM prompts.
    
    Constructs optimized prompts that include relevant examples,
    style guidelines, architectural patterns, and human feedback
    while staying within token limits.
    """

    def __init__(self, config=None):
        self.config = config
        self.max_tokens = config.max_context_tokens if config else 8000
        self.token_buffer = 1000  # Reserve tokens for query and response

    def build_context(
        self,
        retrieved_docs: list[Document],
        query_code: str,
        source_language: str,
        target_language: str,
        include_query: bool = True
    ) -> str:
        """
        Build comprehensive translation context from retrieved documents.
        
        Args:
            retrieved_docs: Documents retrieved from vector store
            query_code: Code to be translated
            source_language: Source programming language
            target_language: Target programming language
            include_query: Whether to include the query code in context
        
        Returns:
            Formatted context string for LLM prompt
        """
        # Organize documents by type
        context_sections = self._organize_documents(retrieved_docs, source_language, target_language)

        # Prioritize and filter sections by token budget
        prioritized_sections = self._prioritize_sections(context_sections, query_code)

        # Build the final context
        context_parts = []

        # Add system instruction
        context_parts.append(self._build_system_instruction(source_language, target_language))

        # Add context sections
        for section in prioritized_sections:
            context_parts.append(f"\n## {section.title}\n\n{section.content}")

        # Add the query if requested
        if include_query:
            context_parts.append(self._build_query_section(query_code, source_language, target_language))

        return "\n".join(context_parts)

    def _organize_documents(
        self,
        docs: list[Document],
        source_language: str,
        target_language: str
    ) -> list[ContextSection]:
        """Organize retrieved documents into structured context sections."""
        sections = []

        # Group documents by type
        doc_groups = {
            "code_snippet": [],
            "style_guide": [],
            "architectural_pattern": [],
            "human_feedback": []
        }

        for doc in docs:
            doc_type = doc.metadata.get("type", "unknown")
            if doc_type in doc_groups:
                doc_groups[doc_type].append(doc)

        # Build sections for each type
        if doc_groups["code_snippet"]:
            sections.append(self._build_code_examples_section(doc_groups["code_snippet"]))

        if doc_groups["style_guide"]:
            sections.append(self._build_style_guide_section(doc_groups["style_guide"]))

        if doc_groups["architectural_pattern"]:
            sections.append(self._build_patterns_section(doc_groups["architectural_pattern"]))

        if doc_groups["human_feedback"]:
            sections.append(self._build_feedback_section(doc_groups["human_feedback"]))

        return sections

    def _build_code_examples_section(self, docs: list[Document]) -> ContextSection:
        """Build section for code translation examples."""
        content_parts = []

        for i, doc in enumerate(docs[:3], 1):  # Limit to top 3 examples
            similarity = doc.metadata.get("similarity_score", 0)
            content_parts.append(f"### Example {i} (Similarity: {similarity:.2f})\n")
            content_parts.append(doc.page_content)
            content_parts.append("")  # Empty line

        content = "\n".join(content_parts)

        return ContextSection(
            title="Similar Code Translation Examples",
            content=content,
            priority=1,  # High priority
            token_estimate=self._estimate_tokens(content),
            source_type="code_snippet"
        )

    def _build_style_guide_section(self, docs: list[Document]) -> ContextSection:
        """Build section for style guides and coding standards."""
        content_parts = []

        for doc in docs[:2]:  # Limit to top 2 style guides
            title = doc.metadata.get("title", "Style Guide")
            content_parts.append(f"### {title}\n")

            # Extract key points from style guide content
            guide_content = doc.page_content
            key_points = self._extract_key_points(guide_content)
            content_parts.append(key_points)
            content_parts.append("")

        content = "\n".join(content_parts)

        return ContextSection(
            title="Coding Standards & Style Guidelines",
            content=content,
            priority=2,  # Medium-high priority
            token_estimate=self._estimate_tokens(content),
            source_type="style_guide"
        )

    def _build_patterns_section(self, docs: list[Document]) -> ContextSection:
        """Build section for architectural patterns."""
        content_parts = []

        for doc in docs[:2]:  # Limit to top 2 patterns
            pattern_name = doc.metadata.get("name", "Pattern")
            content_parts.append(f"### {pattern_name}\n")
            content_parts.append(doc.page_content)
            content_parts.append("")

        content = "\n".join(content_parts)

        return ContextSection(
            title="Relevant Architectural Patterns",
            content=content,
            priority=3,  # Medium priority
            token_estimate=self._estimate_tokens(content),
            source_type="architectural_pattern"
        )

    def _build_feedback_section(self, docs: list[Document]) -> ContextSection:
        """Build section for human feedback and corrections."""
        content_parts = []

        # Prioritize positive feedback and corrections
        positive_docs = [d for d in docs if d.metadata.get("has_correction", False) or d.metadata.get("rating", 0) >= 4]
        relevant_docs = positive_docs[:2] if positive_docs else docs[:2]

        for i, doc in enumerate(relevant_docs, 1):
            rating = doc.metadata.get("rating", "N/A")
            content_parts.append(f"### Feedback Example {i} (Rating: {rating})\n")

            # Extract key insights from feedback
            feedback_summary = self._summarize_feedback(doc.page_content)
            content_parts.append(feedback_summary)
            content_parts.append("")

        content = "\n".join(content_parts)

        return ContextSection(
            title="Human Feedback & Best Practices",
            content=content,
            priority=2,  # Medium-high priority (valuable insights)
            token_estimate=self._estimate_tokens(content),
            source_type="human_feedback"
        )

    def _prioritize_sections(
        self,
        sections: list[ContextSection],
        query_code: str
    ) -> list[ContextSection]:
        """Prioritize and filter sections based on token budget and relevance."""
        # Sort by priority (lower number = higher priority)
        sections.sort(key=lambda x: x.priority)

        # Calculate available tokens
        system_tokens = 200  # Estimate for system instruction
        query_tokens = self._estimate_tokens(query_code) + 100  # Query + prompt overhead
        available_tokens = self.max_tokens - self.token_buffer - system_tokens - query_tokens

        # Select sections that fit within token budget
        selected_sections = []
        used_tokens = 0

        for section in sections:
            if used_tokens + section.token_estimate <= available_tokens:
                selected_sections.append(section)
                used_tokens += section.token_estimate
            else:
                # Try to include a truncated version if it's high priority
                if section.priority <= 2 and used_tokens < available_tokens * 0.8:
                    truncated_section = self._truncate_section(section, available_tokens - used_tokens)
                    if truncated_section:
                        selected_sections.append(truncated_section)
                break

        return selected_sections

    def _build_system_instruction(self, source_language: str, target_language: str) -> str:
        """Build system instruction for the translation task."""
        return f"""# Code Translation Task

You are an expert software engineer tasked with translating code from {source_language.title()} to {target_language.title()}.

## Guidelines:
1. **Semantic Preservation**: Maintain the exact behavior and logic of the original code
2. **Idiomatic Code**: Write code that follows {target_language.title()} best practices and conventions
3. **Style Consistency**: Follow the coding standards provided below
4. **Error Handling**: Adapt error handling patterns to {target_language.title()} conventions
5. **Performance**: Consider performance implications of the translation

## Context:
The following sections provide relevant examples, guidelines, and feedback to help you create high-quality translations."""

    def _build_query_section(self, query_code: str, source_language: str, target_language: str) -> str:
        """Build the query section with the code to translate."""
        return f"""
## Translation Request

Please translate the following {source_language.title()} code to {target_language.title()}:

```{source_language.lower()}
{query_code}
```

**Requirements:**
- Preserve all functionality and behavior
- Follow the style guidelines provided above
- Include appropriate comments and documentation
- Handle errors appropriately for {target_language.title()}
- Return only the translated code with brief explanatory comments if needed
"""

    def _extract_key_points(self, content: str, max_points: int = 5) -> str:
        """Extract key points from style guide content."""
        lines = content.split("\n")
        key_points = []

        for line in lines:
            line = line.strip()
            # Look for bullet points, numbered items, or headers
            if (line.startswith("-") or line.startswith("*") or
                line.startswith("#") or re.match(r"^\d+\.", line)):
                key_points.append(line)
                if len(key_points) >= max_points:
                    break

        if not key_points:
            # If no structured points found, take first few sentences
            sentences = re.split(r"[.!?]+", content)
            key_points = [s.strip() for s in sentences[:3] if s.strip()]

        return "\n".join(key_points)

    def _summarize_feedback(self, feedback_content: str) -> str:
        """Summarize human feedback to extract key insights."""
        # Look for feedback text after "Human Feedback:" or similar markers
        feedback_match = re.search(r"Human Feedback:\s*(.+?)(?:\n\n|\Z)", feedback_content, re.DOTALL)

        if feedback_match:
            feedback_text = feedback_match.group(1).strip()
            # Limit length
            if len(feedback_text) > 200:
                feedback_text = feedback_text[:200] + "..."
            return f"**Key Insight:** {feedback_text}"

        # If no explicit feedback found, extract from corrected translation
        if "Corrected Translation:" in feedback_content:
            return "**Key Insight:** Human provided corrected version - refer to the corrected code above."

        return "**Key Insight:** Positive example from human evaluation."

    def _truncate_section(self, section: ContextSection, max_tokens: int) -> ContextSection | None:
        """Truncate a section to fit within token limit."""
        if max_tokens < 50:  # Not worth truncating if too small
            return None

        # Estimate how much content we can keep
        content_lines = section.content.split("\n")
        target_lines = int(len(content_lines) * (max_tokens / section.token_estimate))

        truncated_content = "\n".join(content_lines[:target_lines]) + "\n\n[... content truncated ...]"

        return ContextSection(
            title=section.title + " (Truncated)",
            content=truncated_content,
            priority=section.priority,
            token_estimate=max_tokens,
            source_type=section.source_type
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Simple estimation: ~4 characters per token for code
        return len(text) // 4 + text.count("\n") * 2  # Add extra for newlines

    def get_context_summary(self, context: str) -> dict[str, Any]:
        """Get summary statistics about the built context."""
        sections = context.split("## ")

        return {
            "total_sections": len(sections) - 1,  # Subtract 1 for the part before first section
            "estimated_tokens": self._estimate_tokens(context),
            "character_count": len(context),
            "sections": [s.split("\n")[0] for s in sections[1:]]  # Section titles
        }
