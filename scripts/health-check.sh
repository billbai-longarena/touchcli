#!/bin/bash
# Health check script
# Verifies all services are healthy

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🏥 Performing health checks..."
echo ""

# Counter
PASSED=0
FAILED=0

# Function to check endpoint
check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    echo -n "Checking $name... "

    if response=$(curl -s -w "%{http_code}" -o /dev/null "$url" 2>/dev/null); then
        if [ "$response" = "$expected_status" ]; then
            echo -e "${GREEN}✅${NC}"
            ((PASSED++))
        else
            echo -e "${RED}❌ (HTTP $response)${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${RED}❌ (Connection failed)${NC}"
        ((FAILED++))
    fi
}

# Check services
check_endpoint "Frontend" "http://localhost:3000/health"
check_endpoint "API" "http://localhost:8000/health"
check_endpoint "Gateway" "http://localhost:8080/health"

# Check databases
echo ""
echo "Checking databases..."

echo -n "PostgreSQL... "
if docker-compose exec -T postgres pg_isready -U touchcli_user -d touchcli_dev &> /dev/null; then
    echo -e "${GREEN}✅${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌${NC}"
    ((FAILED++))
fi

echo -n "Redis... "
if docker-compose exec -T redis redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌${NC}"
    ((FAILED++))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Health Check Summary:"
echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All services healthy!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some services are unhealthy${NC}"
    exit 1
fi
