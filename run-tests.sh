#!/bin/bash

# Exit on any error
set -e

# Configuration
DATA_DIR="./data"
RESULTS_DIR="${DATA_DIR}/test_results"
FINAL_REPORT="${RESULTS_DIR}/final_report.json"

# Ensure data directory exists
mkdir -p "${DATA_DIR}"

echo "Starting TransCoder pipeline..."

# Run all services in sequence
echo "1. Running ingestion stage..."
docker-compose up ingestion --build
echo "✓ Ingestion complete"

echo "2. Running IR generation..."
docker-compose up irgen --build
echo "✓ IR generation complete"

echo "3. Running chunking and embedding..."
docker-compose up chunking --build
echo "✓ Chunking complete"

echo "4. Running RAG..."
docker-compose up rag --build
echo "✓ RAG complete"

echo "5. Running translation..."
docker-compose up translate --build
echo "✓ Translation complete"

echo "6. Running post-processing..."
docker-compose up post --build
echo "✓ Post-processing complete"

echo "7. Running test generation..."
docker-compose up testgen --build
echo "✓ Test generation complete"

echo "8. Running test execution..."
docker-compose up testexec --build
echo "✓ Test execution complete"

# Generate final report
if [ -f "${RESULTS_DIR}/metrics.json" ]; then
    echo "Generating final report..."
    cp "${RESULTS_DIR}/metrics.json" "${FINAL_REPORT}"
    
    # Add timestamp
    tmp_file=$(mktemp)
    jq --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
       '. + {"timestamp": $arg}' \
       "${FINAL_REPORT}" > "${tmp_file}" && mv "${tmp_file}" "${FINAL_REPORT}"
    
    echo "Final report saved to ${FINAL_REPORT}"
    
    # Display summary
    echo "=== Test Results Summary ==="
    jq -r '"Success Rate: \(.success_rate)%"' "${FINAL_REPORT}"
    jq -r '"Total Tests: \(.summary.total)"' "${FINAL_REPORT}"
    jq -r '"Passed Tests: \(.summary.passed)"' "${FINAL_REPORT}"
else
    echo "Warning: No test metrics found"
fi

echo "Pipeline execution completed"