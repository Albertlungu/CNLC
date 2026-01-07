#!/bin/bash

# Comprehensive filter combination test script
# Tests all possible combinations of filters: search (name), category, and geolocation
# Also tests the dedicated ID endpoint at /api/businesses/<id>

# Default test values
RADIUS=20
LAT1=45.382865
LON1=-75.732837  # Merivale HS location
CATEGORY="restaurant"
SEARCH_NAME="Depanneur"
SEARCH_ID="2706036649"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Start the server
echo "Starting server..."
python backend/api/server.py & SERVER_PID=$!
sleep 3

# Function to run a test for /api/businesses endpoint (returns array with count)
run_test() {
    local test_name=$1
    local url=$2
    local output_file=$3

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
    echo "=========================================="
    echo "Test $TOTAL_TESTS: $test_name"
    echo "URL: $url"
    echo "=========================================="

    curl -s "$url" > "$output_file"

    # Check if response contains count field (valid response)
    if grep -q '"count":' "$output_file"; then
        local count=$(jq -r '.count' "$output_file" 2>/dev/null || echo "parse_error")
        if [ "$count" != "parse_error" ]; then
            echo -e "${GREEN}PASSED${NC} - Found $count results"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        fi
    fi

    # Check if it's an error response
    if grep -q '"error":' "$output_file"; then
        local error=$(jq -r '.error' "$output_file" 2>/dev/null || echo "unknown error")
        echo -e "${RED}FAILED${NC} - Error: $error"
    else
        echo -e "${RED}FAILED${NC} - Invalid response"
    fi

    FAILED_TESTS=$((FAILED_TESTS + 1))
    return 1
}

# Function to run a test for /api/businesses/<id> endpoint (returns single business object)
run_test_single() {
    local test_name=$1
    local url=$2
    local output_file=$3

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
    echo "=========================================="
    echo "Test $TOTAL_TESTS: $test_name"
    echo "URL: $url"
    echo "=========================================="

    curl -s "$url" > "$output_file"

    # Check if response contains business field (valid response)
    if grep -q '"business":' "$output_file"; then
        local business_name=$(jq -r '.business.name // "null"' "$output_file" 2>/dev/null || echo "parse_error")
        if [ "$business_name" != "parse_error" ] && [ "$business_name" != "null" ]; then
            echo -e "${GREEN}PASSED${NC} - Found business: $business_name"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        elif [ "$business_name" == "null" ]; then
            echo -e "${YELLOW}PASSED${NC} - No business found (valid response)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        fi
    fi

    # Check if it's an error response
    if grep -q '"error":' "$output_file"; then
        local error=$(jq -r '.error' "$output_file" 2>/dev/null || echo "unknown error")
        echo -e "${RED}FAILED${NC} - Error: $error"
    else
        echo -e "${RED}FAILED${NC} - Invalid response"
    fi

    FAILED_TESTS=$((FAILED_TESTS + 1))
    return 1
}

# Create output directory
mkdir -p ./tests/JSON/filter_tests

BASE_URL="http://127.0.0.1:5000/api/businesses"

# Health check first
echo "Running health check..."
curl -s "http://127.0.0.1:5000/health" > ./tests/JSON/health.json
if grep -q '"status": "healthy"' ./tests/JSON/health.json; then
    echo -e "${GREEN}Server is healthy${NC}"
else
    echo -e "${RED}Server health check failed${NC}"
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    exit 1
fi

# ============== Single Filter Tests ==============

echo ""
echo "######################################"
echo "# SINGLE FILTER TESTS"
echo "######################################"

# Test 1: No filters (baseline - get all businesses)
run_test "No filters" \
    "$BASE_URL" \
    "./tests/JSON/filter_tests/test_no_filters.json"

# Test 2: Search by name only
run_test "Search by name only" \
    "$BASE_URL?search=$SEARCH_NAME" \
    "./tests/JSON/filter_tests/test_search_name.json"

# Test 3: Get business by ID (dedicated endpoint)
run_test_single "Get business by ID" \
    "$BASE_URL/$SEARCH_ID" \
    "./tests/JSON/filter_tests/test_search_id.json"

# Test 4: Category filter only
run_test "Category filter only" \
    "$BASE_URL?category=$CATEGORY" \
    "./tests/JSON/filter_tests/test_category.json"

# Test 5: Geolocation filter only
run_test "Geolocation filter only" \
    "$BASE_URL?lat1=$LAT1&lon1=$LON1&radius=$RADIUS" \
    "./tests/JSON/filter_tests/test_geo.json"

# ============== Two Filter Combinations ==============

echo ""
echo "######################################"
echo "# TWO FILTER COMBINATIONS"
echo "######################################"

# Test 6: Search + Category
run_test "Search (name) + Category" \
    "$BASE_URL?search=$SEARCH_NAME&category=$CATEGORY" \
    "./tests/JSON/filter_tests/test_search_category.json"

# Test 7: Search + Geolocation
run_test "Search (name) + Geolocation" \
    "$BASE_URL?search=$SEARCH_NAME&lat1=$LAT1&lon1=$LON1&radius=$RADIUS" \
    "./tests/JSON/filter_tests/test_search_geo.json"

# Test 8: Category + Geolocation
run_test "Category + Geolocation" \
    "$BASE_URL?category=$CATEGORY&lat1=$LAT1&lon1=$LON1&radius=$RADIUS" \
    "./tests/JSON/filter_tests/test_category_geo.json"

# ============== Three Filter Combinations ==============

echo ""
echo "######################################"
echo "# THREE FILTER COMBINATIONS"
echo "######################################"

# Test 9: Search + Category + Geolocation (all filters combined)
run_test "Search (name) + Category + Geolocation" \
    "$BASE_URL?search=$SEARCH_NAME&category=$CATEGORY&lat1=$LAT1&lon1=$LON1&radius=$RADIUS" \
    "./tests/JSON/filter_tests/test_all_filters.json"

# ============== ID Endpoint Tests ==============

echo ""
echo "######################################"
echo "# ID ENDPOINT TESTS"
echo "######################################"

# Test 10: Get non-existent business by ID
run_test_single "Get non-existent business by ID" \
    "$BASE_URL/999999999" \
    "./tests/JSON/filter_tests/test_nonexistent_id.json"

# ============== Edge Cases ==============

echo ""
echo "######################################"
echo "# EDGE CASE TESTS"
echo "######################################"

# Test 13: Geolocation with only lat (missing lon)
run_test "Geolocation with only lat1 (should return all)" \
    "$BASE_URL?lat1=$LAT1" \
    "./tests/JSON/filter_tests/test_geo_incomplete_1.json"

# Test 14: Geolocation with only lon (missing lat)
run_test "Geolocation with only lon1 (should return all)" \
    "$BASE_URL?lon1=$LON1" \
    "./tests/JSON/filter_tests/test_geo_incomplete_2.json"

# Test 15: Empty search query
run_test "Empty search query" \
    "$BASE_URL?search=" \
    "./tests/JSON/filter_tests/test_empty_search.json"

# Test 16: Empty category
run_test "Empty category" \
    "$BASE_URL?category=" \
    "./tests/JSON/filter_tests/test_empty_category.json"

# Test 17: Very large radius
run_test "Very large radius (10000 km)" \
    "$BASE_URL?lat1=$LAT1&lon1=$LON1&radius=10000" \
    "./tests/JSON/filter_tests/test_large_radius.json"

# Test 18: Zero radius
run_test "Zero radius" \
    "$BASE_URL?lat1=$LAT1&lon1=$LON1&radius=0" \
    "./tests/JSON/filter_tests/test_zero_radius.json"

# Test 19: Non-existent search term
run_test "Non-existent search term" \
    "$BASE_URL?search=XYZNONEXISTENT123" \
    "./tests/JSON/filter_tests/test_nonexistent_search.json"

# Test 20: Non-existent category
run_test "Non-existent category" \
    "$BASE_URL?category=NONEXISTENTCATEGORY" \
    "./tests/JSON/filter_tests/test_nonexistent_category.json"

# ============== Test Summary ==============

echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${YELLOW}Some tests failed. Check output above for details.${NC}"
fi

# Clean up
echo ""
echo "Stopping server..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
echo "Server stopped."

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
else
    exit 1
fi
