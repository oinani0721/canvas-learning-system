"""
Unit tests for Docker Compose configuration.

Story 30.1 - AC 1: Docker Compose file with neo4j:5.26-community

[Source: docs/stories/30.1.story.md - AC 1]
[Source: docker-compose.yml]
"""

import pytest
import yaml
from pathlib import Path


# Resolve path: backend/tests/unit/ -> project root
_TEST_DIR = Path(__file__).parent
_PROJECT_ROOT = _TEST_DIR.parent.parent.parent
_DOCKER_COMPOSE_PATH = _PROJECT_ROOT / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose_config():
    """Load and parse docker-compose.yml."""
    assert _DOCKER_COMPOSE_PATH.exists(), (
        f"docker-compose.yml not found at {_DOCKER_COMPOSE_PATH}"
    )
    with open(_DOCKER_COMPOSE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def neo4j_service(compose_config):
    """Extract neo4j service from compose config."""
    services = compose_config.get("services", {})
    assert "neo4j" in services, "neo4j service not defined in docker-compose.yml"
    return services["neo4j"]


class TestDockerComposeNeo4jImage:
    """Test Neo4j Docker image configuration (AC1)."""

    def test_neo4j_image_is_community_526(self, neo4j_service):
        """neo4j service uses neo4j:5.26-community image."""
        assert neo4j_service["image"] == "neo4j:5.26-community"

    def test_neo4j_container_name(self, neo4j_service):
        """neo4j service has explicit container name."""
        assert "container_name" in neo4j_service
        assert neo4j_service["container_name"] == "canvas-learning-system-neo4j"


class TestDockerComposeNeo4jPorts:
    """Test Neo4j port mappings (AC1)."""

    def test_neo4j_has_port_mappings(self, neo4j_service):
        """neo4j service defines port mappings."""
        assert "ports" in neo4j_service
        assert len(neo4j_service["ports"]) >= 2

    def test_neo4j_http_port_mapped(self, neo4j_service):
        """HTTP Browser port (7474) is mapped to host."""
        ports = neo4j_service["ports"]
        # Port format: "host:container" — check container port 7474 is mapped
        port_strs = [str(p) for p in ports]
        has_http = any("7474" in p for p in port_strs)
        assert has_http, f"HTTP port 7474 not mapped. Ports: {port_strs}"

    def test_neo4j_bolt_port_mapped(self, neo4j_service):
        """Bolt protocol port (7687) is mapped to host."""
        ports = neo4j_service["ports"]
        port_strs = [str(p) for p in ports]
        has_bolt = any("7687" in p for p in port_strs)
        assert has_bolt, f"Bolt port 7687 not mapped. Ports: {port_strs}"


class TestDockerComposeNeo4jVolumes:
    """Test Neo4j volume mounts for data persistence (AC1, AC5)."""

    def test_neo4j_has_volumes(self, neo4j_service):
        """neo4j service defines volume mounts."""
        assert "volumes" in neo4j_service
        assert len(neo4j_service["volumes"]) >= 1

    def test_neo4j_data_volume(self, neo4j_service):
        """Data volume is mounted at /data."""
        volumes = neo4j_service["volumes"]
        has_data = any(":/data" in str(v) for v in volumes)
        assert has_data, f"Data volume not mounted at /data. Volumes: {volumes}"

    def test_neo4j_logs_volume(self, neo4j_service):
        """Logs volume is mounted at /logs."""
        volumes = neo4j_service["volumes"]
        has_logs = any(":/logs" in str(v) for v in volumes)
        assert has_logs, f"Logs volume not mounted at /logs. Volumes: {volumes}"


class TestDockerComposeNeo4jHealthcheck:
    """Test Neo4j healthcheck configuration (AC1)."""

    def test_neo4j_has_healthcheck(self, neo4j_service):
        """neo4j service defines a healthcheck."""
        assert "healthcheck" in neo4j_service

    def test_neo4j_healthcheck_has_test(self, neo4j_service):
        """Healthcheck defines a test command."""
        hc = neo4j_service["healthcheck"]
        assert "test" in hc
        # Test command should check HTTP endpoint
        test_cmd = hc["test"]
        test_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert "7474" in test_str or "wget" in test_str or "curl" in test_str

    def test_neo4j_healthcheck_has_interval(self, neo4j_service):
        """Healthcheck defines interval and retries."""
        hc = neo4j_service["healthcheck"]
        assert "interval" in hc
        assert "retries" in hc


class TestDockerComposeNeo4jRestartPolicy:
    """Test Neo4j restart policy (AC1)."""

    def test_neo4j_restart_unless_stopped(self, neo4j_service):
        """neo4j service uses restart: unless-stopped."""
        assert neo4j_service.get("restart") == "unless-stopped"
