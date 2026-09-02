#!/bin/bash

# RootLearn Smoke Tests
# Quick validation that deployment is working

set -e

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
TIMEOUT=10

echo "==================================="
echo "RootLearn Deployment Smoke Tests"
echo "==================================="
echo "Backend URL: ${BACKEND_URL}"
echo "Frontend URL: ${FRONTEND_URL}"
echo ""

FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -n "Testing ${name}... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${TIMEOUT} "${url}" 2>/dev/null || echo "000")
    
    if [ "${response}" = "${expected_status}" ]; then
        echo "✓ OK (${response})"
    else
        echo "✗ FAILED (got ${response}, expected ${expected_status})"
        FAILED=$((FAILED + 1))
    fi
}

# Backend tests
echo "Backend Tests:"
echo "--------------"
test_endpoint "Health Check" "${BACKEND_URL}/health" 200
test_endpoint "API Docs" "${BACKEND_URL}/docs" 200
test_endpoint "OpenAPI Schema" "${BACKEND_URL}/openapi.json" 200
test_endpoint "Metrics" "${BACKEND_URL}/metrics" 200

# Test session creation (requires valid request)
echo -n "Testing Session Creation API... "
session_response=$(curl -s -X POST "${BACKEND_URL}/api/v1/sessions" \
    -H "Content-Type: application/json" \
    -d '{"user_id": "00000000-0000-0000-0000-000000000000", "prompt": "test"}' \
    --max-time ${TIMEOUT} -w "\n%{http_code}" 2>/dev/null || echo "000")

session_status=$(echo "$session_response" | tail -n1)
if [ "${session_status}" = "201" ] || [ "${session_status}" = "200" ]; then
    echo "✓ OK (${session_status})"
    
    # Extract session_id for cleanup
    session_id=$(echo "$session_response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ -n "${session_id}" ]; then
        # Clean up test session
        curl -s -X DELETE "${BACKEND_URL}/api/v1/sessions/${session_id}" > /dev/null 2>&1 || true
    fi
else
    echo "✗ FAILED (${session_status})"
    FAILED=$((FAILED + 1))
fi

echo ""

# Frontend tests
echo "Frontend Tests:"
echo "--------------"
test_endpoint "Landing Page" "${FRONTEND_URL}" 200
test_endpoint "Frontend Health" "${FRONTEND_URL}" 200

echo ""

# Database connectivity (if we can access backend logs)
echo "Database Tests:"
echo "--------------"
echo -n "Testing Database Connectivity... "
if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U rootlearn > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    FAILED=$((FAILED + 1))
fi

echo ""

# Summary
echo "==================================="
if [ ${FAILED} -eq 0 ]; then
    echo "✓ All smoke tests passed!"
    echo "==================================="
    exit 0
else
    echo "✗ ${FAILED} test(s) failed"
    echo "==================================="
    exit 1
fi
