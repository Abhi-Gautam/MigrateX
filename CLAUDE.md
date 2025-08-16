# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running MigrateX

**IMPORTANT**: Always run MigrateX commands using `uv`:
```bash
uv run python src/migratex/main.py [command] [args]
```

## Common Development Commands

### Running Tests
```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_language_parser.py

# Run tests matching a pattern
uv run pytest -k "test_extract_functions"

# Run tests with verbose output
uv run pytest -v

# Run tests excluding slow tests
uv run pytest -m "not slow"

# Run single test method
uv run pytest tests/test_language_parser.py::TestLanguageParser::test_extract_functions_c
```

### Linting and Type Checking
```bash
# Run ruff linter
uv run ruff check src/ tests/

# Run ruff with auto-fix
uv run ruff check --fix src/ tests/

# Run type checking with mypy
uv run mypy src/

# Format code with ruff
uv run ruff format src/ tests/
```

### Development Workflow
```bash
# Install development dependencies
uv sync --dev

# Run pre-commit hooks manually
uv run pre-commit run --all-files

# Generate coverage report
uv run pytest --cov-report=html
# Open htmlcov/index.html in browser
```

## High-Level Architecture

MigrateX implements a 10-stage pipeline for automated code translation, built as a pure Python application:

### Core Components

1. **Language Analysis (`src/migratex/analysis/`)**
   - Uses tree-sitter Python bindings for AST parsing
   - `language_parser.py`: Handles multi-language parsing (C, C++, Java, Python)
   - `module_extractor.py`: Extracts functions, classes, and dependency graphs
   - Builds networkx graphs for dependency analysis

2. **Pipeline Orchestration (`src/migratex/pipeline/`)**
   - `orchestrator.py`: Manages the complete 10-stage translation pipeline
   - Handles state transitions, error recovery, and progress tracking
   - Coordinates between analysis, RAG, LLM translation, and validation stages

3. **RAG System (`src/migratex/rag/`)**
   - `rag_pipeline.py`: Implements retrieval-augmented generation
   - Stores code snippets, style guides, architectural patterns, and human feedback
   - Uses FAISS for vector similarity search with langchain integration
   - Reduces LLM token usage by ~70% through intelligent context selection

4. **Error Handling & Repair (`src/migratex/error_handling/`)**
   - `repair_engine.py`: Implements P2/P3 prompt repair loops from the research
   - `error_classifier.py`: Detects and categorizes translation errors
   - `repair_manager.py`: Tracks repair attempts and escalation logic

5. **Metadata & Directory Mapping (`src/migratex/directory_mapping/`)**
   - `metadata_schema.py`: Pydantic models for transformation tracking
   - `mapping_engine.py`: Language-aware directory structure transformations
   - `provenance_tracker.py`: Complete audit trail of transformations
   - Tracks: ID/UUID, source/target paths, dependencies, validation status, human feedback

6. **CLI & Visualization (`src/migratex/cli/`)**
   - `visualizer.py`: Rich-based tree views and progress displays
   - `interactive.py`: Textual-based interactive components for human review
   - Shows module extraction progress, dependency analysis, and translation status

### Key Design Patterns

1. **Module Extraction Strategy**
   - Extracts self-contained units (functions/classes) with dependency closure
   - Prioritizes modules with fewer external dependencies for translation
   - Maintains semantic relationships through metadata tracking

2. **Human-in-the-Loop Feedback**
   - Flag translations as "good" or "bad" during review
   - Corrections are stored and embedded back into RAG for continuous improvement
   - Feedback includes: original code, translation, correction, and explanatory comments

3. **Test-Driven Translation**
   - Extracts existing tests or generates new ones via Gemini API
   - Validates translations through sandboxed Docker execution
   - Uses behavioral testing to ensure semantic preservation

4. **Cost Optimization**
   - Intelligent chunking to reduce context size
   - RAG retrieval minimizes redundant LLM calls
   - Caches successful translations for reuse

## Project Principles

- **Semantic Preservation**: Maintain program behavior, not just syntax
- **Cost Efficiency**: Minimize LLM tokens via chunking and RAG (targeting 70% reduction)
- **Scalability**: Modular translation of independent, self-verifying units
- **Continuous Improvement**: Human-in-the-loop feedback strengthens retrieval corpus
- **Fail-Safe Defaults**: Early error detection via static analysis and semantic checks

## Development Methodology

The project strictly follows **Test-Driven Development (TDD)**:
1. Write a failing test first
2. Write minimal code to pass the test  
3. Refactor while keeping tests passing

Use `pytest` for Python tests.

## CLI Commands

### Analysis Commands
```bash
# Basic repository analysis with module extraction
uv run python src/migratex/main.py analyze <repository_path>

# Enhanced AI-powered analysis with coverage detection
uv run python src/migratex/main.py analyze-and-generate <repository_path> --max-functions 5

# Module-based semantic analysis (recommended)
uv run python src/migratex/main.py analyze-modules <repository_path> --max-modules 5
```

### Translation Commands
```bash
# Translate C code modules to Rust (or go, python, javascript, typescript)
uv run python src/migratex/main.py translate-modules <repository_path> --target rust --max-modules 3

# Legacy translate command (not recommended)
uv run python src/migratex/main.py translate <repository_path> rust
```

### Knowledge Base Management
```bash
# Add translation examples to RAG
uv run python src/migratex/main.py knowledge-add-example --source "<c_code>" --target "<rust_code>"

# Add style guides
uv run python src/migratex/main.py knowledge-add-guide --title "Rust Best Practices" --content "<guide_content>"

# Add architectural patterns
uv run python src/migratex/main.py knowledge-add-pattern --name "Builder Pattern" --description "<description>"

# Add human feedback
uv run python src/migratex/main.py knowledge-add-feedback --original "<code>" --generated "<translation>" --corrected "<fixed>"

# View knowledge base statistics
uv run python src/migratex/main.py knowledge-stats

# Search knowledge base
uv run python src/migratex/main.py knowledge-search --query "memory management" --max 5
```

## Key Dependencies

**Python**: `uv`, `typer`, `pytest`, `google-generativeai`, `langchain`, `faiss-cpu`, `docker`, `textual`, `tree-sitter`, `tree-sitter-c`, `tree-sitter-cpp`, `tree-sitter-java`, `tree-sitter-python`, `networkx`