# 🧪 How to Test MigrateX Yourself

This guide shows you how to test MigrateX's Milestone 2 capabilities on real CRUST-bench repositories.

## 🚀 Quick Start

### 1. Setup & Verification

First, run the setup verification script:

```bash
python test_migratex.py
```

This will check:
- ✅ CRUST-bench directory exists
- ✅ API key is configured
- ✅ Available repositories
- 📚 Show you test commands

### 2. Basic Function Analysis (No API calls)

Test the language parser and function extraction:

```bash
uv run python -m migratex test-extract CRUST-bench/datasets/CBench/CircularBuffer
```

**Expected Output:**
```
🔍 Analyzing repository: CRUST-bench/datasets/CBench/CircularBuffer
Found 1 C source files
  📄 Parsing circular_buffer.c...
    ✅ Extracted 11 functions

📊 Total functions extracted: 11
🧪 Found 1 test files
Found 0 existing test functions

📋 Analysis Summary:
  🔧 Functions found: 11
  🧪 Existing tests: 0
✅ Analysis complete!
```

### 3. AI Test Generation (Uses API)

Generate tests for functions using real Gemini API:

```bash
# Generate tests for 2 functions (cost-controlled)
uv run python -m migratex test-extract CRUST-bench/datasets/CBench/CircularBuffer --generate --max-functions 2
```

**Expected Output:**
```
🤖 Generating tests (limited to 2 functions for cost control)...
  Generating test for CircularBuffer...
    ✅ Generated successfully
    📝 Test preview:
      ```c
      #include <stdio.h>
      #include <stdlib.h>
      #include <assert.h>
      // ... comprehensive test code ...
      ```
      ...
```

## 📚 Test Different Repository Types

### Small & Simple: CircularBuffer
```bash
uv run python -m migratex test-extract CRUST-bench/datasets/CBench/CircularBuffer --generate --max-functions 3
```
- **11 functions** in 1 file
- Data structure with memory management
- Perfect for testing basic functionality

### Large & Complex: Linear-Algebra-C  
```bash
uv run python -m migratex test-extract CRUST-bench/datasets/CBench/Linear-Algebra-C --generate --max-functions 3
```
- **87 functions** across 3 files
- Mathematical operations, multi-file dependencies
- Tests multi-file parsing capabilities

### Parser-Heavy: SimpleXML
```bash
uv run python -m migratex test-extract CRUST-bench/datasets/CBench/SimpleXML --generate --max-functions 2
```
- **24 functions** in 2 files
- XML parsing, vector operations
- Tests complex string processing

### Utility Library: leftpad
```bash
uv run python -m migratex test-extract CRUST-bench/datasets/CBench/leftpad --generate --max-functions 2
```
- Simple string utility functions
- Great for seeing clean, focused test generation

## 🧪 Run Comprehensive Integration Tests

### Full Automated Test Suite
```bash
# Run all integration tests (takes ~2-3 minutes)
uv run pytest tests/test_crust_bench_integration.py -v -s
```

This runs:
- **CircularBuffer** complete workflow
- **Linear-Algebra-C** multi-file parsing
- **SimpleXML** parsing accuracy
- **Repository structure analysis**

### Comprehensive Summary Report
```bash
# Generate detailed report with test examples (takes ~3-4 minutes)
uv run pytest tests/test_integration_summary_generator.py -v -s
```

**Shows:**
- **122 functions** extracted across 3 repositories
- **100% AI generation success rate**
- **Real generated test examples**
- Complete success criteria assessment

## 📊 What You'll See

### 1. Function Extraction Results
- ✅ **Accurate parsing** of complex C code with pointers, structs, memory management
- ✅ **Multi-file dependency tracking**
- ✅ **Complete function signatures and bodies**

### 2. AI Test Generation Quality
- ✅ **Comprehensive edge cases**: Zero values, boundary conditions, error handling
- ✅ **Proper C syntax**: Includes, assertions, memory management
- ✅ **Multiple test scenarios**: 3-5 different test cases per function
- ✅ **Context-aware**: Tests match the function's actual behavior

### 3. Example Generated Test
For `CircularBufferCreate()`, MigrateX generates:
```c
void test_CircularBufferCreate() {
    // Test Case 1: Basic creation and initialization
    size_t buffer_size1 = 10;
    CircularBuffer buffer1 = CircularBufferCreate(buffer_size1);
    assert(buffer1 != NULL);
    assert(buffer1->size == buffer_size1);
    
    // Test Case 2: Zero size buffer
    // Test Case 3: Large size buffer  
    // Test Case 4: Multiple creations
    // Test Case 5: Reset functionality
    // ... comprehensive coverage
}
```

## 💡 Pro Tips

### Cost Control
- Use `--max-functions N` to limit API calls
- Start with `--max-functions 1` for testing
- Each function generation costs ~0.01-0.02 USD

### Testing Strategy
1. **Start simple**: Test basic analysis without `--generate`
2. **Try small repos**: CircularBuffer, leftpad
3. **Scale up**: Linear-Algebra-C for multi-file testing
4. **Run full suite**: Integration tests for comprehensive validation

### Troubleshooting
- **API key issues**: Check `.env` file has `GOOGLE_API_KEY=...`
- **No functions found**: Ensure you're pointing to a C repository
- **Generation failures**: Check internet connection and API key validity

## 🎯 Success Criteria

When testing, you should see:

✅ **Language Parser Success**
- Extract 10+ functions from CircularBuffer
- Extract 80+ functions from Linear-Algebra-C
- Handle complex C constructs (pointers, structs, memory management)

✅ **AI Generator Success**  
- Generate syntactically correct C tests
- Include multiple test cases with edge conditions
- 90%+ success rate for API calls

✅ **Integration Success**
- Complete end-to-end workflow without errors
- Proper metadata tracking and function-test associations
- Real value demonstration on production codebases

## 🚀 What This Proves

By testing MigrateX on CRUST-bench, you're validating that:

1. **It works on real code** - Not contrived examples, but actual open-source C libraries
2. **It scales** - From simple utilities to complex multi-file projects  
3. **It generates quality** - AI tests that are comprehensive and contextually appropriate
4. **It's production-ready** - Reliable parsing, error handling, and integration

Ready to see MigrateX in action? Start with the quick setup verification:

```bash
python test_migratex.py
```