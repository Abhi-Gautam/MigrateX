# MigrateX

An intelligent agentic pipeline for automated code translation from legacy languages to modern, memory-safe alternatives.

## Overview

MigrateX addresses the critical challenge of modernizing legacy codebases by providing a comprehensive, language-agnostic framework that combines compiler-grade analysis, retrieval-augmented generation (RAG), and automated testing. The system translates code from C/C++, Java, and .NET to safer, more productive languages like Rust and Go while preserving semantic fidelity and ensuring production-ready output.

## Key Features

- **Semantic Preservation**: Maintains program behavior across translation boundaries, not just syntactic conversion
- **Cost Efficiency**: Reduces LLM token usage by up to 70% through intelligent chunking and RAG techniques
- **Automated Testing**: Generates comprehensive test suites and validates translations through delta testing
- **Continuous Learning**: Incorporates human feedback to improve translation quality over time
- **Enterprise Scale**: Handles large codebases through modular, containerized pipeline stages

## Quick Start

### Prerequisites
- Python 3.11 or higher
- UV package manager
- Google Gemini API key (set as `GOOGLE_API_KEY` environment variable)

### Installation
```bash
git clone https://github.com/your-org/MigrateX.git
cd MigrateX
uv sync --dev
```

### Basic Usage
```bash
# Analyze a repository and extract modules
uv run python src/migratex/main.py analyze-modules path/to/repository --max-modules 5

# Translate C code to Rust
uv run python src/migratex/main.py translate-modules path/to/repository --target rust --max-modules 3

# View available commands
uv run python src/migratex/main.py --help
```

## Architecture

MigrateX implements a 10-stage pipeline:

1. **Source Repository Ingestion** - Language detection and repository analysis
2. **IR Generation & Normalization** - AST/CFG extraction and module creation
3. **Function Chunking** - Dependency-aware code segmentation
4. **RAG Layer** - Semantic code retrieval and context augmentation
5. **LLM Translation** - Multi-model ensemble translation with voting
6. **Test Generation** - Automated unit test creation using Test-IR metamodel
7. **Test Execution** - Sandboxed validation and behavioral verification
8. **Human Review** - Interactive correction and quality assurance
9. **Directory Mapping** - Project structure reconstruction
10. **Continuous Learning** - Feedback integration and corpus enhancement

## Performance Metrics

Based on evaluation against CRUST-Bench and real-world codebases:

- **68.7% Pass@1 Rate** - 1.4× better than baseline LLM approaches
- **85.1% Compilation Success** - Without manual intervention
- **70% Token Reduction** - Compared to naive LLM translation
- **1.83 kLoC/hour** - Translation throughput
- **$0.23 per kLoC** - Cost efficiency (6× improvement over alternatives)

## Project Status

This repository contains the research foundation and implementation roadmap for MigrateX. The project is currently in the proof-of-concept development phase, with a hybrid Python-Rust architecture designed for production scalability.

## Research Foundation

The system is based on comprehensive research addressing key challenges in automated code translation:

- **Hallucination Mitigation**: Context-aware prompting reduces LLM errors
- **Cross-file Dependencies**: Dependency closure analysis ensures complete translations
- **Code Quality**: Automated adherence to target language idioms and safety practices
- **Verification**: Multi-layered testing approach including behavioral validation

## Development Approach

MigrateX follows Test-Driven Development (TDD) methodology with strict emphasis on:
- Semantic correctness validation
- Cost-efficient LLM usage
- Scalable modular architecture
- Human-in-the-loop quality assurance

## Commands Reference

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

# Legacy translate command
uv run python src/migratex/main.py translate <repository_path> rust
```

### Knowledge Base Management
```bash
# Add translation examples to RAG
uv run python src/migratex/main.py knowledge-add-example --source "<c_code>" --target "<rust_code>"

# Add style guides
uv run python src/migratex/main.py knowledge-add-guide --title "Rust Best Practices" --content "<guide_content>"

# View knowledge base statistics
uv run python src/migratex/main.py knowledge-stats

# Search knowledge base
uv run python src/migratex/main.py knowledge-search --query "memory management" --max 5
```

## Testing

### Running Tests
```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_language_parser.py

# Run tests excluding slow tests
uv run pytest -m "not slow"

# Run single test method
uv run pytest tests/test_language_parser.py::TestLanguageParser::test_extract_functions_c
```

### Development Commands
```bash
# Run ruff linter
uv run ruff check src/ tests/

# Run type checking with mypy
uv run mypy src/

# Format code with ruff
uv run ruff format src/ tests/
```

## Output Structure

MigrateX organizes outputs in a structured directory format:

```
migratex_output/
├── translated_projects/                         # Translation outputs
│   ├── {project_name}_{target_lang}_{timestamp}/
│   │   ├── src/                                # Translated source code
│   │   ├── Cargo.toml / setup.py / go.mod     # Build files
│   │   ├── MIGRATION_GUIDE.md                 # Detailed migration documentation
│   │   └── translation_results.json           # Translation metadata and results
│   └── ...
└── {repository_name}_{timestamp}/               # Analysis outputs
    ├── analysis/
    │   └── results.json                        # Analysis results
    ├── generated_tests/                        # AI-generated test files
    ├── reports/
    │   └── analysis_report.html               # Detailed HTML analysis report
    ├── source_functions/                      # Extracted function files
    ├── Makefile                              # Generated build configuration
    └── README.md                             # Analysis summary
```

## Demo & Testing

To test MigrateX with the provided CRUST-bench examples:

```bash
# Run setup verification
python test_migratex.py

# Test on CircularBuffer example (compelling demo)
uv run python src/migratex/main.py analyze-modules CRUST-bench/datasets/CBench/CircularBuffer --max-modules 8
uv run python src/migratex/main.py translate-modules CRUST-bench/datasets/CBench/CircularBuffer --target rust --max-modules 3

# Interactive demo presentation
uv run python demo_runner.py
```

## Technical Architecture

The system follows a pure Python approach for rapid development with these core components:

### Core Components
1. **Language Analysis** (`src/migratex/analysis/`) - Tree-sitter based AST parsing and module extraction
2. **Pipeline Orchestration** (`src/migratex/pipeline/`) - 10-stage translation pipeline management
3. **RAG System** (`src/migratex/rag/`) - Retrieval-augmented generation with FAISS vector search
4. **Error Handling** (`src/migratex/error_handling/`) - P2/P3 prompt repair loops
5. **Metadata Tracking** (`src/migratex/directory_mapping/`) - Complete transformation audit trails
6. **CLI & Visualization** (`src/migratex/cli/`) - Rich-based progress displays and interactive components

### Key Design Patterns
- **Module Extraction Strategy**: Self-contained units with dependency closure
- **Human-in-the-Loop Feedback**: Continuous learning from corrections
- **Test-Driven Translation**: Behavioral validation through automated testing
- **Cost Optimization**: 70% token reduction via intelligent chunking and RAG

---

*For research foundation details, see the paper in [Docs/Paper/](Docs/Paper/).*