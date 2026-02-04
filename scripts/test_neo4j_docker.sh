#!/bin/bash
# Neo4j Docker Test Script
# Story 30.1 - AC 5: Data Persistence Verification
# [Source: docs/stories/30.1.story.md - Task 5.1]
#
# Usage:
#   ./scripts/test_neo4j_docker.sh
#
# Prerequisites:
#   - Docker and Docker Compose installed
#   - NEO4J_PASSWORD set in environment or .env file

set -e

echo "=============================================="
echo "Neo4j Docker Test Script (Story 30.1)"
echo "=============================================="

# Configuration
CONTAINER_NAME="canvas-neo4j"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}"
TEST_NODE_NAME="story_30_1_persistence_test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "\n${YELLOW}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Start Neo4j container
print_step "Starting Neo4j container..."
docker-compose up -d neo4j

# Step 2: Wait for Neo4j to be healthy
print_step "Waiting for Neo4j to be healthy (up to 60s)..."
WAIT_TIME=0
MAX_WAIT=60
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if docker exec $CONTAINER_NAME wget -q --spider http://localhost:7474 2>/dev/null; then
        print_success "Neo4j is healthy after ${WAIT_TIME}s"
        break
    fi
    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
    echo "  Waiting... (${WAIT_TIME}s)"
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    print_error "Neo4j did not become healthy within ${MAX_WAIT}s"
    exit 1
fi

# Step 3: Test basic connection
print_step "Testing basic Cypher connection..."
docker exec $CONTAINER_NAME cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "RETURN 1 as test"
print_success "Basic connection test passed"

# Step 4: Clean up any existing test nodes
print_step "Cleaning up existing test nodes..."
docker exec $CONTAINER_NAME cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD \
    "MATCH (n:TestNode {name: '$TEST_NODE_NAME'}) DELETE n"

# Step 5: Create test node
print_step "Creating test node for persistence verification..."
docker exec $CONTAINER_NAME cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD \
    "CREATE (n:TestNode {name: '$TEST_NODE_NAME', created: datetime(), test_value: 'Story_30_1'}) RETURN n"
print_success "Test node created"

# Step 6: Verify test node exists
print_step "Verifying test node exists..."
RESULT=$(docker exec $CONTAINER_NAME cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD \
    "MATCH (n:TestNode {name: '$TEST_NODE_NAME'}) RETURN count(n) as count" 2>/dev/null | tail -1)
if [[ "$RESULT" == *"1"* ]]; then
    print_success "Test node verified (count: 1)"
else
    print_error "Test node not found!"
    exit 1
fi

# Step 7: Restart container
print_step "Restarting Neo4j container..."
docker-compose restart neo4j

# Step 8: Wait for Neo4j to be healthy again
print_step "Waiting for Neo4j to be healthy after restart..."
WAIT_TIME=0
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if docker exec $CONTAINER_NAME wget -q --spider http://localhost:7474 2>/dev/null; then
        print_success "Neo4j healthy after restart (${WAIT_TIME}s)"
        break
    fi
    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
    echo "  Waiting... (${WAIT_TIME}s)"
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    print_error "Neo4j did not recover after restart"
    exit 1
fi

# Step 9: Verify data persistence
print_step "Verifying data persistence after restart..."
RESULT=$(docker exec $CONTAINER_NAME cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD \
    "MATCH (n:TestNode {name: '$TEST_NODE_NAME'}) RETURN n.name, n.test_value" 2>/dev/null | tail -1)
if [[ "$RESULT" == *"$TEST_NODE_NAME"* ]] && [[ "$RESULT" == *"Story_30_1"* ]]; then
    print_success "Data persistence verified! Test node survived restart."
else
    print_error "Data persistence FAILED! Test node not found after restart."
    exit 1
fi

# Step 10: Cleanup test node
print_step "Cleaning up test node..."
docker exec $CONTAINER_NAME cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD \
    "MATCH (n:TestNode {name: '$TEST_NODE_NAME'}) DELETE n"
print_success "Test node cleaned up"

echo ""
echo "=============================================="
echo -e "${GREEN}All tests passed!${NC}"
echo "=============================================="
echo ""
echo "Data Volume Locations:"
echo "  - Data:    ./docker/neo4j/data"
echo "  - Logs:    ./docker/neo4j/logs"
echo "  - Plugins: ./docker/neo4j/plugins"
echo ""
echo "Access Neo4j Browser: http://localhost:7474"
echo "Bolt URI: bolt://localhost:7687"
echo ""
