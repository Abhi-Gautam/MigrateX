#!/bin/bash

# Configuration
DATA_DIR="/data"
TESTS_DIR="${DATA_DIR}/tests"
RESULTS_DIR="${DATA_DIR}/test_results"
METRICS_FILE="${RESULTS_DIR}/metrics.json"

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Function to run tests and collect metrics
run_tests() {
    echo "Running tests from ${TESTS_DIR}..."
    
    # Run pytest with JSON output
    pytest "${TESTS_DIR}" \
        --json-report \
        --json-report-file="${METRICS_FILE}" \
        -v || true  # Continue even if tests fail
    
    # Calculate success rate
    total_tests=$(jq '.summary.total' "${METRICS_FILE}")
    passed_tests=$(jq '.summary.passed' "${METRICS_FILE}")
    success_rate=$(echo "scale=2; ${passed_tests}*100/${total_tests}" | bc)
    
    # Update metrics with success rate
    tmp_file=$(mktemp)
    jq --arg rate "${success_rate}" \
       '. + {"success_rate": $rate}' \
       "${METRICS_FILE}" > "${tmp_file}" && mv "${tmp_file}" "${METRICS_FILE}"
    
    echo "Tests completed. Results saved to ${METRICS_FILE}"
    echo "Success rate: ${success_rate}%"
}

# Main execution
run_tests