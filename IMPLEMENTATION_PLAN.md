# Technical Documentation: MigrateX CLI

## 1. Overview

This document outlines the technical specification and development roadmap for the **MigrateX CLI**, a proof-of-concept (POC) tool for the agentic code translation system described in the MigrateX white paper. The CLI will be a language-agnostic application that takes a source code repository as input and translates it to a target language, providing detailed progress and context monitoring throughout the process.

## 2. Core Principles

The development of the MigrateX CLI will be guided by the following principles, derived from the white paper:

*   **Semantic Preservation:** Prioritize the preservation of program semantics across translation boundaries, not just syntax.
*   **Cost Efficiency:** Minimize token usage and expensive LLM calls via retrieval-augmented techniques and chunking.
*   **Scalability:** Modularize translation into independent, self-verifying units that can scale to large repositories.
*   **Continuous Improvement:** Use human-in-the-loop feedback to incrementally strengthen the retrieval corpus and reduce future error rates.
*   **Fail-Safe Defaults:** Detect translation failures early via static analysis, coverage estimation, and semantic round-trip checks, rather than propagating errors downstream.

## 3. Architecture & Tech Stack

We will adopt a pure Python approach for rapid development and deployment:

*   **Python:** The entire application will be written in Python, leveraging its rich ecosystem of libraries for language analysis, AI integration, and CLI development. This includes:
    - `typer` for the CLI interface with rich terminal output
    - `tree-sitter` Python bindings for AST parsing and language analysis
    - `langchain` and `langchain-google-genai` for the RAG pipeline and LLM integration
    - `google-generativeai` for direct Gemini API interaction
    - `networkx` for dependency graph analysis and manipulation
    - `ast` and `tokenize` (built-in) for Python-specific code analysis
    - `docker` for sandboxed compilation and testing
    - `textual` for interactive terminal interfaces

This approach gives us rapid development, excellent debugging capabilities, and access to Python's extensive AI and data processing ecosystem without the complexity of FFI bindings.

## 4. Metadata-Driven Architecture

Following the research paper's sophisticated approach, MigrateX will implement a comprehensive metadata system that treats each code entity with a detailed transformation record inspired by data lineage concepts:

### Metadata Schema Fields
*   **ID/UUID:** Unique identifier for each code unit
*   **Source/Target Paths:** Original and migrated file/module paths for directory mapping
*   **Language/Version:** Source and target language specifications (e.g., .NET 7.0 → Go 1.18)
*   **Dependencies:** Complete dependency graph including imports, calls, and type references
*   **Context Snippet:** Surrounding code and comments for semantic disambiguation
*   **Transform Stage:** Current processing stage with validation markers
*   **Validation Status:** Compilation, test, and review status with rollback points
*   **Transformation Log:** Complete audit trail of all changes and repair attempts
*   **Human Feedback:** User corrections, ratings, and explanatory comments

### Directory Mapping Examples
The system will handle sophisticated organizational transformations:
```
Source .NET Repository:              Target Go Repository:
MyApp/Controllers/WeatherController  → controllers/weather_controller.go
MyApp/Models/WeatherForecast        → models/weather_forecast.go  
MyApp/Services/WeatherService       → services/weather_service.go
MyApp.Tests/WeatherServiceTests     → tests/weather_service_test.go
```

### Provenance Tracking
Every transformation maintains complete lineage:
*   Which original module produced each class/function
*   What transformations were applied (loops, error handling, type conversions)
*   Which repair loops were triggered and their outcomes
*   Human review decisions and corrections applied

### CLI Visualization Examples
The metadata system will provide rich visualizations:

**Module Extraction Tree:**
```
📁 Source Analysis
├── 🔍 MyApp.Controllers (3 modules extracted)
│   ├── ✅ WeatherController.cs → controllers/weather_controller.go
│   ├── ⚠️  UserController.cs → controllers/user_controller.go (2 dependencies)
│   └── 🔄 BaseController.cs → controllers/base_controller.go (processing...)
├── 📦 MyApp.Models (2 modules)
│   ├── ✅ WeatherForecast.cs → models/weather_forecast.go
│   └── ✅ User.cs → models/user.go
└── 🧪 Tests (auto-generated)
    ├── 🆕 weather_controller_test.go (generated)
    └── 🆕 user_controller_test.go (generated)
```

**Metadata Inspector:**
```
📋 Module: WeatherController.cs
├── 🆔 ID: uuid-1234-5678
├── 📍 Source: MyApp/Controllers/WeatherController.cs
├── 🎯 Target: controllers/weather_controller.go
├── 🔗 Dependencies: [WeatherForecast, ILogger, HttpContext]
├── 📊 Status: ✅ Compiled → ✅ Tested → ⏳ Review Pending
├── 🛠️  Transforms: [async→goroutine, LINQ→for-range, Exception→error]
└── 👤 Human Feedback: "Approved - good error handling"
```

## 5. The RAG Knowledge Base

The RAG is not just for code. It is a dynamic, living knowledge base of your organization's engineering practices. The vector database will be structured to store different types of information, each with specific metadata:

1.  **Code Snippets:** Semantically similar code examples, as originally planned.
2.  **Style Guides:** Markdown documents describing your organization's coding standards (e.g., "All comments must be in this format...", "API endpoints should be structured as...").
3.  **Architectural Patterns:** Documents describing approved architectural patterns or technology choices.
4.  **Human Feedback:** Curated examples of past "good" and "bad" translations, along with the human-provided corrections or reasoning.

When building a prompt for the LLM, we will query for multiple types of context to ensure the generated code is not only functionally correct but also adheres to organizational standards.

## 6. The Human Feedback Loop

The core of the "Continuous Improvement" principle is a robust feedback loop:

1.  **Flagging:** During the CLI process, you can flag any translation as "good" or "bad".
2.  **Correction:** For "bad" translations, the CLI will prompt you to provide the corrected code or a natural language comment explaining what was wrong.
3.  **Storage:** This feedback (the original code, the bad translation, the correction, and your comment) will be stored as a structured record in our metadata store.
4.  **Integration into RAG:** These verified corrections are then processed and embedded back into the vector database. A "good" translation becomes a positive example for future retrievals. A "bad" translation with its correction becomes a powerful "what-not-to-do" example, which can be used to refine prompts or even for fine-tuning models in the future.

## 7. Development Methodology

This project will strictly follow **Test-Driven Development (TDD)**. For every piece of functionality, we will:

1.  **Write a failing test:** Before writing any implementation code, we will write a test that describes the desired functionality and fails because the functionality does not yet exist.
2.  **Write the minimal code to pass the test:** We will write the simplest possible code to make the test pass.
3.  **Refactor:** We will then refactor the code to improve its design, while ensuring that all tests continue to pass.

This approach will ensure that our code is well-tested, robust, and maintainable. We will use `pytest` for all our Python tests.

## 8. Project Structure

The project will be organized as a monorepo with the following structure:

```
/MigrateX/
|-- IMPLEMENTATION_PLAN.md
|-- pyproject.toml # For uv and ruff configuration
|-- src/
|   |-- migratex/
|   |   |-- __init__.py
|   |   |-- main.py # Typer CLI application
|   |   |-- pipeline/
|   |   |   |-- __init__.py
|   |   |   |-- orchestrator.py
|   |   |-- analysis/
|   |   |   |-- __init__.py
|   |   |   |-- language_parser.py # Tree-sitter based language parsing
|   |   |   |-- module_extractor.py # Module extraction and dependency analysis
|   |   |-- rag/
|   |   |   |-- __init__.py
|   |   |   |-- rag_pipeline.py
|   |   |-- cli/
|   |   |   |-- __init__.py
|   |   |   |-- visualizer.py # Rich-based CLI visualizations
|   |   |   |-- interactive.py # Textual-based interactive components
|   |   |-- error_handling/
|   |   |   |-- __init__.py
|   |   |   |-- repair_engine.py # P2/P3 prompt repair loops
|   |   |   |-- error_classifier.py # Error detection and classification
|   |   |   |-- repair_manager.py # Repair attempt tracking and escalation
|   |   |-- directory_mapping/
|   |   |   |-- __init__.py
|   |   |   |-- metadata_schema.py # Pydantic models for transformation tracking
|   |   |   |-- mapping_engine.py # Language-aware directory transformations
|   |   |   |-- provenance_tracker.py # Audit trail and transformation logging
|   |   |   |-- context_preserver.py # Context snapshot and preservation
|   |   |   |-- validation_manager.py # Transformation stage tracking
|   |   |-- reporting/
|   |       |-- __init__.py
|   |       |-- dashboard.py
|-- tests/
|   |-- test_*.py
|-- .gitignore
```

## 9. Milestones

The development of the MigrateX CLI will be divided into the following independently testable milestones:

### Milestone 1: Project Setup, Language-Agnostic Parser, and Module Extraction

*   **Goal:** Create the basic structure of the Python CLI application and the core language analysis system with self-contained module extraction.
*   **Deliverables:**
    *   A Python CLI application using `typer` that accepts the path to a source repository and the target language as input.
    *   A Python language analysis system that can parse source files using `tree-sitter`, generate ASTs/CFGs, and extract self-contained modules with dependency closure.
    *   **Module Extraction Engine:** Extract functions, classes, and their complete dependency graphs into self-contained units.
    *   **CLI Visualization:** Interactive tree view showing extracted modules, their dependencies, and extraction progress.
    *   A metadata store tracking parsing progress and module relationships.
*   **Packages and Tools:**
    *   **Python:** `uv`, `typer`, `pytest`, `tree-sitter`, `networkx` (for dependency graphs), `rich` (for CLI visualization), `textual` (for interactive displays)
*   **Testing (TDD):**
    *   Write a failing test in Python for parsing source code with tree-sitter.
    *   Implement the tree-sitter Python bindings integration to make the test pass.
    *   Write a failing test for parsing a simple code string and extracting dependencies.
    *   Implement the tree-sitter logic and dependency analysis using networkx to make the test pass.
    *   Write a failing test for CLI module tree visualization.
    *   Implement the interactive module display using `rich` trees.

### Milestone 2: Associated Test Extraction/Generation

*   **Goal:** Implement the functionality to either extract existing tests or generate new ones for each "unit of functionality" (e.g., a function).
*   **Deliverables:**
    *   A module that can identify and extract existing unit tests from the source repository.
    *   A module that can generate new unit tests for a given function using the Gemini API.
    *   The ability to associate the extracted/generated tests with their corresponding functions in the metadata store.
*   **Packages and Tools:**
    *   **Python:** `google-generativeai`, `pytest`
*   **Testing (TDD):**
    *   Write a failing test for identifying test files in a sample project structure.
    *   Implement the logic to find and parse test files.
    *   Write a failing test for generating a test for a simple function.
    *   Implement the Gemini API call to generate the test.

### Milestone 3: RAG Pipeline for Organizational Context

*   **Goal:** Implement the RAG pipeline for code translation, including the ability to store and retrieve organizational context.
*   **Deliverables:**
    *   A module for creating embeddings of the source code and organizational documents and storing them in a vector database.
    *   A module for retrieving relevant code snippets and organizational documents from the vector database based on a given query.
    *   A module for generating the translated code using the Gemini API, with the retrieved context.
*   **Packages and Tools:**
    *   **Python:** `langchain` (or similar), `faiss-cpu` (or other vector store), `google-generativeai`, `pytest`
*   **Testing (TDD):**
    *   Write a failing test for embedding a document and storing it in the vector store.
    *   Implement the embedding and storage logic.
    *   Write a failing test for retrieving a document from the vector store.
    *   Implement the retrieval logic.

### Milestone 4: Test Compilation, Error Handling, and Iterative Repair

*   **Goal:** Implement compilation testing, automatic error detection, and iterative repair loops (P2/P3 prompts) for robust code translation.
*   **Deliverables:**
    *   A module for compiling the translated code in a sandboxed environment.
    *   **Iterative Repair Engine:** Automatic detection and repair of compilation errors (P2 prompts) and test failures (P3 prompts).
    *   **Error Classification System:** Categorize errors (syntax, semantic, compilation, runtime) and route to appropriate repair strategies.
    *   **Repair Loop Manager:** Track repair attempts, prevent infinite loops, and escalate to human review when needed.
    *   CLI progress indicators showing repair attempts and success rates.
*   **Packages and Tools:**
    *   **Python:** `docker`, `pytest`, `rich` (for progress bars), `google-generativeai`
*   **Testing (TDD):**
    *   Write a failing test for compiling a simple "hello world" program in a Docker container.
    *   Implement the Docker compilation logic.
    *   Write a failing test for detecting and classifying compilation errors.
    *   Implement the error detection and classification system.
    *   Write a failing test for P2 prompt (syntax error repair).
    *   Implement the P2 repair loop with LLM integration.
    *   Write a failing test for P3 prompt (test failure repair).
    *   Implement the P3 repair loop and test validation.

### Milestone 5: Sophisticated Directory Mapping and Interactive Review

*   **Goal:** Implement metadata-driven directory reconstruction with full provenance tracking and context preservation.
*   **Deliverables:**
    *   **Metadata Schema:** Comprehensive tracking system for code transformations with unique IDs, source/target paths, dependencies, and context snapshots.
    *   **Directory Mapping Engine:** Language-aware structure transformation (e.g., `.NET/Controllers` → `Go/controllers`, `MyApp/Models` → `models/`).
    *   **Provenance Tracking:** Complete audit trail from original code to final placement with transformation logs.
    *   **Context Preservation:** Maintain surrounding code snippets, docstrings, and semantic clues for each translated unit.
    *   **Validation Status System:** Track transformation stages (parsed, transpiled, tested, validated) with rollback capabilities.
    *   **Interactive Review Mode:** Side-by-side comparison with metadata visualization and edit capabilities.
    *   **CLI Mapping Visualizer:** Tree view showing source→target mappings with metadata overlays.
*   **Packages and Tools:**
    *   **Python:** `textual` (interactive UI), `difflib` (comparison), `pydantic` (metadata schemas), `rich` (tree visualization), `pytest`
*   **Testing (TDD):**
    *   Write a failing test for metadata schema creation and validation.
    *   Implement the comprehensive metadata model with Pydantic.
    *   Write a failing test for language-specific directory mapping rules.
    *   Implement the mapping engine with .NET→Go, Java→Python transformations.
    *   Write a failing test for provenance tracking throughout transformation.
    *   Implement the audit trail system with transformation logging.
    *   Write a failing test for context snapshot preservation.
    *   Implement context extraction and association with metadata.
    *   Write a failing test for interactive review with metadata display.
    *   Implement the enhanced review UI with provenance information.

### Milestone 6: Context Monitoring and Progress Visualization

*   **Goal:** Implement comprehensive monitoring of LLM context usage and migration progress visualization.
*   **Deliverables:**
    *   A module for tracking the size and content of the context being sent to the Gemini API.
    *   **Real-time Dashboard:** CLI dashboard showing translation progress, error rates, token usage, and costs.
    *   **Context Optimization:** Dynamic context sizing and relevance scoring to optimize LLM performance.
    *   A "context score" that warns the user if the context is becoming too large or unfocused.
*   **Packages and Tools:**
    *   **Python:** `textual` (for the dashboard), `rich` (for progress visualization), `pytest`
*   **Testing (TDD):**
    *   Write a failing test for tracking the token count of a prompt.
    *   Implement the token counting logic.
    *   Write a failing test for real-time progress display.
    *   Implement the dashboard display logic.
    *   Write a failing test for context optimization.
    *   Implement dynamic context sizing and scoring.