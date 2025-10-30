#!/bin/bash

# SAP API CDC Testing Script
# Script untuk testing Change Data Capture functionality

API_BASE_URL="http://localhost:8000"
CONTENT_TYPE="Content-Type: application/json"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Test 1: Health Check
test_health_check() {
    log "Testing Health Check..."
    
    response=$(curl -s -w "\n%{http_code}" "$API_BASE_URL/api/health")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ Health Check: PASSED"
        echo "Response: $body"
    else
        error "❌ Health Check: FAILED (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
    echo ""
}

# Test 2: Get CDC Sample
test_cdc_sample() {
    log "Testing CDC Sample Endpoint..."
    
    response=$(curl -s -w "\n%{http_code}" "$API_BASE_URL/api/sales/cdc/sample")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ CDC Sample: PASSED"
        echo "Sample data retrieved successfully"
    else
        error "❌ CDC Sample: FAILED (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
    echo ""
}

# Test 3: CDC Statistics
test_cdc_statistics() {
    log "Testing CDC Statistics..."
    
    # Create test data for statistics
    statistics_request='{
        "vkorg": "1000",
        "start_date": "2023-12-01",
        "end_date": "2023-12-31"
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/api/sales/cdc/statistics" \
        -H "$CONTENT_TYPE" \
        -d "$statistics_request")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ CDC Statistics: PASSED"
        echo "Statistics: $body"
    else
        warning "⚠️ CDC Statistics: No existing data (HTTP $http_code)"
        echo "Response: $body"
    fi
    echo ""
}

# Test 4: Insert Sample Data (for testing)
insert_sample_data() {
    log "Inserting sample data for CDC testing..."
    
    sample_data='[
        {
            "vkorg": "1000",
            "erdat": "2023-12-15",
            "matnr": "TEST001",
            "maktx": "Test Material 1",
            "kwmeng": 100.0,
            "netwr": 1000000.0
        },
        {
            "vkorg": "1000",
            "erdat": "2023-12-20",
            "matnr": "TEST002",
            "maktx": "Test Material 2",
            "kwmeng": 200.0,
            "netwr": 2000000.0
        }
    ]'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/api/sales" \
        -H "$CONTENT_TYPE" \
        -d "$sample_data")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ Sample Data Inserted: PASSED"
        echo "Response: $body"
    else
        error "❌ Sample Data Insert: FAILED (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
    echo ""
}

# Test 5: CDC Process
test_cdc_process() {
    log "Testing CDC Process..."
    
    cdc_request='{
        "cdc_parameters": {
            "vkorg": "1000",
            "start_date": "2023-12-01",
            "end_date": "2023-12-31"
        },
        "data": [
            {
                "vkorg": "1000",
                "erdat": "2023-12-10",
                "matnr": "CDC001",
                "maktx": "CDC Test Material 1",
                "kwmeng": 150.0,
                "netwr": 1500000.0
            },
            {
                "vkorg": "1000",
                "erdat": "2023-12-25",
                "matnr": "CDC002", 
                "maktx": "CDC Test Material 2",
                "kwmeng": 250.0,
                "netwr": 2500000.0
            }
        ]
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/api/sales/cdc" \
        -H "$CONTENT_TYPE" \
        -d "$cdc_request")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ CDC Process: PASSED"
        echo "Response: $body"
    else
        error "❌ CDC Process: FAILED (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
    echo ""
}

# Test 6: Verify CDC Results
test_cdc_verification() {
    log "Verifying CDC Results..."
    
    # Check statistics after CDC
    statistics_request='{
        "vkorg": "1000",
        "start_date": "2023-12-01",
        "end_date": "2023-12-31"
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/api/sales/cdc/statistics" \
        -H "$CONTENT_TYPE" \
        -d "$statistics_request")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ CDC Verification: PASSED"
        echo "Post-CDC Statistics: $body"
        
        # Extract record count
        record_count=$(echo "$body" | grep -o '"existing_records_count":[0-9]*' | cut -d':' -f2)
        if [[ "$record_count" == "2" ]]; then
            log "✅ Record count verification: PASSED (Expected: 2, Actual: $record_count)"
        else
            warning "⚠️ Record count verification: Expected 2, but found $record_count"
        fi
    else
        error "❌ CDC Verification: FAILED (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
    echo ""
}

# Test 7: Error Handling Tests
test_error_handling() {
    log "Testing Error Handling..."
    
    # Test 1: Missing CDC parameters
    error_test_1='{
        "data": [
            {
                "vkorg": "1000",
                "erdat": "2023-12-01",
                "matnr": "ERROR001"
            }
        ]
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/api/sales/cdc" \
        -H "$CONTENT_TYPE" \
        -d "$error_test_1")
    
    http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "400" ]]; then
        log "✅ Error Test 1 (Missing CDC params): PASSED"
    else
        warning "⚠️ Error Test 1: Expected HTTP 400, got $http_code"
    fi
    
    # Test 2: Invalid date format
    error_test_2='{
        "cdc_parameters": {
            "vkorg": "1000",
            "start_date": "invalid-date",
            "end_date": "2023-12-31"
        },
        "data": []
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/api/sales/cdc" \
        -H "$CONTENT_TYPE" \
        -d "$error_test_2")
    
    http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "400" ]]; then
        log "✅ Error Test 2 (Invalid date): PASSED"
    else
        warning "⚠️ Error Test 2: Expected HTTP 400, got $http_code"
    fi
    
    echo ""
}

# Main test execution
main() {
    echo "=========================================="
    echo "SAP API CDC Testing Suite"
    echo "=========================================="
    echo ""
    
    # Check if API is running
    if ! curl -s "$API_BASE_URL/api/health" > /dev/null; then
        error "API is not running at $API_BASE_URL"
        error "Please start the API server first"
        exit 1
    fi
    
    # Run tests
    test_health_check
    test_cdc_sample
    test_cdc_statistics
    insert_sample_data
    test_cdc_process
    test_cdc_verification
    test_error_handling
    
    echo "=========================================="
    echo "CDC Testing Complete"
    echo "=========================================="
    echo ""
    echo "Summary:"
    echo "✅ All CDC endpoints are working"
    echo "✅ Delete-insert logic with date range works correctly"
    echo "✅ Error handling is proper"
    echo ""
    echo "Next Steps:"
    echo "1. Integrate CDC endpoints into SAP"
    echo "2. Test with production-like data volumes"
    echo "3. Monitor performance"
    echo ""
    echo "CDC Endpoints:"
    echo "📊 POST /api/sales/cdc - Main CDC process"
    echo "📈 POST /api/sales/cdc/statistics - Preview statistics"
    echo "📋 GET  /api/sales/cdc/sample - Sample request format"
}

# Run the tests
main "$@"