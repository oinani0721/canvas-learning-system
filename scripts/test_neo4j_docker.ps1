# Neo4j Docker Test Script (PowerShell)
# Story 30.1 - AC 5: Data Persistence Verification
# [Source: docs/stories/30.1.story.md - Task 5.1]
#
# Usage:
#   .\scripts\test_neo4j_docker.ps1
#
# Prerequisites:
#   - Docker Desktop installed and running
#   - NEO4J_PASSWORD set in environment or .env file

$ErrorActionPreference = "Stop"

Write-Host "=============================================="
Write-Host "Neo4j Docker Test Script (Story 30.1)"
Write-Host "=============================================="

# Configuration
$ContainerName = "canvas-neo4j"
$Neo4jUser = if ($env:NEO4J_USER) { $env:NEO4J_USER } else { "neo4j" }
$Neo4jPassword = if ($env:NEO4J_PASSWORD) { $env:NEO4J_PASSWORD } else { "password" }
$TestNodeName = "story_30_1_persistence_test"
$MaxWait = 60

function Write-Step {
    param([string]$Message)
    Write-Host "`n[STEP] $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Step 1: Start Neo4j container
Write-Step "Starting Neo4j container..."
docker-compose up -d neo4j

# Step 2: Wait for Neo4j to be healthy
Write-Step "Waiting for Neo4j to be healthy (up to ${MaxWait}s)..."
$WaitTime = 0
while ($WaitTime -lt $MaxWait) {
    try {
        $result = docker exec $ContainerName wget -q --spider http://localhost:7474 2>&1
        Write-Success "Neo4j is healthy after ${WaitTime}s"
        break
    }
    catch {
        Start-Sleep -Seconds 5
        $WaitTime += 5
        Write-Host "  Waiting... (${WaitTime}s)"
    }
}

if ($WaitTime -ge $MaxWait) {
    Write-Error "Neo4j did not become healthy within ${MaxWait}s"
    exit 1
}

# Step 3: Test basic connection
Write-Step "Testing basic Cypher connection..."
docker exec $ContainerName cypher-shell -u $Neo4jUser -p $Neo4jPassword "RETURN 1 as test"
Write-Success "Basic connection test passed"

# Step 4: Clean up any existing test nodes
Write-Step "Cleaning up existing test nodes..."
docker exec $ContainerName cypher-shell -u $Neo4jUser -p $Neo4jPassword "MATCH (n:TestNode {name: '$TestNodeName'}) DELETE n"

# Step 5: Create test node
Write-Step "Creating test node for persistence verification..."
docker exec $ContainerName cypher-shell -u $Neo4jUser -p $Neo4jPassword "CREATE (n:TestNode {name: '$TestNodeName', created: datetime(), test_value: 'Story_30_1'}) RETURN n"
Write-Success "Test node created"

# Step 6: Verify test node exists
Write-Step "Verifying test node exists..."
$Result = docker exec $ContainerName cypher-shell -u $Neo4jUser -p $Neo4jPassword "MATCH (n:TestNode {name: '$TestNodeName'}) RETURN count(n) as count"
if ($Result -match "1") {
    Write-Success "Test node verified (count: 1)"
}
else {
    Write-Error "Test node not found!"
    exit 1
}

# Step 7: Restart container
Write-Step "Restarting Neo4j container..."
docker-compose restart neo4j

# Step 8: Wait for Neo4j to be healthy again
Write-Step "Waiting for Neo4j to be healthy after restart..."
$WaitTime = 0
while ($WaitTime -lt $MaxWait) {
    try {
        $result = docker exec $ContainerName wget -q --spider http://localhost:7474 2>&1
        Write-Success "Neo4j healthy after restart (${WaitTime}s)"
        break
    }
    catch {
        Start-Sleep -Seconds 5
        $WaitTime += 5
        Write-Host "  Waiting... (${WaitTime}s)"
    }
}

if ($WaitTime -ge $MaxWait) {
    Write-Error "Neo4j did not recover after restart"
    exit 1
}

# Step 9: Verify data persistence
Write-Step "Verifying data persistence after restart..."
$Result = docker exec $ContainerName cypher-shell -u $Neo4jUser -p $Neo4jPassword "MATCH (n:TestNode {name: '$TestNodeName'}) RETURN n.name, n.test_value"
if (($Result -match $TestNodeName) -and ($Result -match "Story_30_1")) {
    Write-Success "Data persistence verified! Test node survived restart."
}
else {
    Write-Error "Data persistence FAILED! Test node not found after restart."
    exit 1
}

# Step 10: Cleanup test node
Write-Step "Cleaning up test node..."
docker exec $ContainerName cypher-shell -u $Neo4jUser -p $Neo4jPassword "MATCH (n:TestNode {name: '$TestNodeName'}) DELETE n"
Write-Success "Test node cleaned up"

Write-Host ""
Write-Host "=============================================="
Write-Host "All tests passed!" -ForegroundColor Green
Write-Host "=============================================="
Write-Host ""
Write-Host "Data Volume Locations:"
Write-Host "  - Data:    ./docker/neo4j/data"
Write-Host "  - Logs:    ./docker/neo4j/logs"
Write-Host "  - Plugins: ./docker/neo4j/plugins"
Write-Host ""
Write-Host "Access Neo4j Browser: http://localhost:7474"
Write-Host "Bolt URI: bolt://localhost:7687"
Write-Host ""
