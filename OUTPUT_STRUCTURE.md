# MigrateX Output Structure

This document explains the output directory structure used by MigrateX for organizing translation and analysis results.

## Directory Structure

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
    │   └── analysis_report.html               # HTML analysis report
    └── source_functions/                       # Extracted source functions
```

## Commands and Outputs

### Translation Command
```bash
uv run python src/migratex/main.py translate-modules REPO_PATH --target rust
```

**Output Location**: `migratex_output/translated_projects/{project}_{language}_{timestamp}/`

**Contains**:
- Complete translated projects ready for compilation
- Language-specific build files (Cargo.toml, setup.py, go.mod, etc.)
- Migration guides with detailed change documentation
- Translation metadata and success statistics

### Analysis Command
```bash
uv run python src/migratex/main.py analyze-modules REPO_PATH
```

**Output Location**: `migratex_output/{repository_name}_{timestamp}/`

**Contains**:
- Module extraction results and coverage analysis
- AI-generated test suites based on coverage gaps
- HTML reports for easy review
- Extracted function source code

## Key Files

### Translation Results (`translation_results.json`)
Contains complete translation metadata:
```json
{
  "project_name": "leftpad_rust",
  "source_language": "c", 
  "target_language": "rust",
  "success_rate": 100.0,
  "total_modules": 1,
  "successful_modules": 1,
  "modules": [
    {
      "source_name": "module_2_functions",
      "target_name": "module_2_functions", 
      "status": "completed",
      "confidence_score": 85.0,
      "translation_time": 17.6,
      "semantic_changes": [...],
      "translation_notes": [...]
    }
  ]
}
```

### Migration Guide (`MIGRATION_GUIDE.md`)
Human-readable documentation with:
- Translation summary and success metrics
- Module-by-module breakdown of changes
- API modifications and semantic differences
- Build instructions for the target language
- Next steps and manual review recommendations

## Output Management

- **Automatic Timestamping**: All outputs include timestamps to prevent conflicts
- **Git Exclusion**: The entire `migratex_output/` directory is excluded from version control
- **Self-Contained**: Each translation output is a complete, buildable project
- **Organized Structure**: Clear separation between translation and analysis outputs

## Example Usage

```bash
# Translate leftpad to Rust
uv run python src/migratex/main.py translate-modules CRUST-bench/datasets/CBench/leftpad --target rust

# Output: migratex_output/translated_projects/translated_leftpad_rust_20250805_215813/
# ├── src/
# │   ├── lib.rs
# │   ├── main.rs  
# │   └── module_2_functions.rs
# ├── Cargo.toml
# ├── MIGRATION_GUIDE.md
# └── translation_results.json

# Analyze CircularBuffer modules
uv run python src/migratex/main.py analyze-modules CRUST-bench/datasets/CBench/CircularBuffer

# Output: migratex_output/CircularBuffer_20250805_213417/
# ├── analysis/results.json
# ├── generated_tests/test_CircularBuffer_module.c
# ├── reports/analysis_report.html
# └── source_functions/CircularBufferPush.c
```

This structure ensures that all MigrateX outputs are organized, timestamped, and easily accessible while keeping the main project directory clean.