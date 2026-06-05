#!/bin/bash
# Test script for SapiSehat Backend API

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}SapiSehat Backend API Test${NC}\n"

# Check if server is running
echo "Checking if server is running..."
curl -s http://localhost:8000/api/health > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Server not running at http://localhost:8000${NC}"
    echo "Start the server with: python main.py"
    exit 1
fi

echo -e "${GREEN}✓ Server is running${NC}\n"

# Test health endpoint
echo "Testing /api/health endpoint..."
HEALTH=$(curl -s -X GET "http://localhost:8000/api/health" \
  -H "Content-Type: application/json")

if echo "$HEALTH" | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $HEALTH\n"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi

# Check if test image exists
TEST_IMAGE="test_image.jpg"
if [ ! -f "$TEST_IMAGE" ]; then
    echo -e "${RED}✗ Test image not found: $TEST_IMAGE${NC}"
    echo "Please provide a test image as 'test_image.jpg'"
    exit 1
fi

# Test predict endpoint
echo "Testing /api/predict endpoint with test image..."
PREDICT=$(curl -s -X POST "http://localhost:8000/api/predict" \
  -F "image=@$TEST_IMAGE")

if echo "$PREDICT" | grep -q "success"; then
    echo -e "${GREEN}✓ Prediction successful${NC}"
    echo "Response:"
    echo "$PREDICT" | python -m json.tool
else
    echo -e "${RED}✗ Prediction failed${NC}"
    echo "Response: $PREDICT"
    exit 1
fi

echo -e "\n${GREEN}All tests passed!${NC}"
