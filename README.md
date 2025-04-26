# MigrateX: Intelligent Code Translation Pipeline

MigrateX is a sophisticated code translation system that leverages artificial intelligence to automatically translate source code between different programming languages while preserving functionality and maintaining code quality. Using a combination of Docker containers, RAG (Retrieval-Augmented Generation), and state-of-the-art language models, MigrateX provides reliable and maintainable code translations.

## Key Features

- **Intelligent Translation**: Preserves code semantics and patterns across languages
- **Context-Aware**: Uses RAG to incorporate relevant code patterns and best practices
- **Modular Architecture**: Containerized pipeline for easy deployment and scaling
- **Quality Assurance**: Automated test generation and execution
- **Language Support**: Handles multiple programming language pairs
- **Code Optimization**: Post-processing for idiomatic and efficient output

## Architecture

The pipeline consists of several stages, each running in its own Docker container:

1. **Ingestion (A)** - Clones repositories and preprocesses source code
2. **IR Generation (B-C)** - Generates and normalizes Intermediate Representation
3. **Chunking (D)** - Splits code into semantic chunks and generates embeddings
4. **RAG (E)** - Retrieves relevant context for translation
5. **Translation (F)** - Orchestrates LLM-based code translation
6. **Post-processing (G)** - Refactors and optimizes translated code
7. **Test Generation (H)** - Generates test cases for translated code
8. **Test Execution (I)** - Runs tests and collects metrics

## Use Cases

- Modernizing legacy codebases
- Cross-platform development
- API migration and adaptation
- Learning new programming languages
- Code maintenance and upgrades

## Prerequisites

- Docker and Docker Compose
- OpenAI API key (for translation stage)
- Git (for source code ingestion)
- Python 3.11+
- Rust (for post-processing)

## Setup

1. Clone this repository
2. Set environment variables:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```
3. Make the run script executable:
   ```bash
   chmod +x run-tests.sh
   ```

## Usage

Run the entire pipeline:

```bash
./run-tests.sh
```

This will:
1. Build all Docker containers
2. Execute each stage in sequence
3. Generate test results and metrics

## Directory Structure

```
.
├── .dockerignore                # Build artifacts to ignore
├── .gitignore                  
├── README.md                   
├── docker-compose.yml          # Container orchestration
├── run-tests.sh               # Main execution script
├── ingestion/                 # (A) Source code ingestion
├── irgen/                     # (B-C) IR generation
├── chunking/                  # (D) Code chunking
├── rag/                       # (E) Context retrieval
├── translate/                 # (F) LLM translation
├── post/                     # (G) Rust-based post-processing
├── testgen/                  # (H) Test generation
├── testexec/                 # (I) Test execution
└── .github/                  # CI/CD configuration
```

## Output

The pipeline generates several artifacts in the `data/` directory:
- `data/repos/` - Cloned repositories
- `data/ir/` - Intermediate representations
- `data/chunks/` - Code chunks and embeddings
- `data/rag_output/` - Retrieved context
- `data/translations/` - LLM translations
- `data/processed/` - Post-processed code
- `data/tests/` - Generated tests
- `data/test_results/` - Test execution metrics

## Development

Each component can be developed and tested independently:

1. Modify component code
2. Build the container: `docker-compose build <component>`
3. Run the component: `docker-compose up <component>`

## CI/CD

The project uses GitHub Actions for:
- Running the full pipeline
- Code linting (Python and Rust)
- Test execution and reporting

See `.github/workflows/ci.yml` for details.