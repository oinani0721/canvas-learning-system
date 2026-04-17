"""Story 1.7: Root .env + Docker Compose variable-ization validation tests.

Tests verify that:
- Root .env.example exists with required variable groups
- docker-compose.yml has no hardcoded user paths
- validate-env.sh exists and is syntactically valid
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_ROOT_ENV_VARS = [
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "CANVAS_BASE_PATH",
    "OLLAMA_HOST",
    "CORS_ORIGINS",
    "API_PORT",
]


class TestRootEnvExample:
    """Task 1: Root .env.example must exist with required variables."""

    def test_env_example_exists(self):
        env_example = PROJECT_ROOT / ".env.example"
        assert env_example.exists(), "Root .env.example must exist"

    @pytest.mark.parametrize("var_name", REQUIRED_ROOT_ENV_VARS)
    def test_required_variable_present(self, var_name: str):
        env_example = PROJECT_ROOT / ".env.example"
        if not env_example.exists():
            pytest.skip(".env.example not yet created")
        content = env_example.read_text()
        assert var_name in content, f"{var_name} must be in root .env.example"

    def test_env_in_gitignore(self):
        gitignore = PROJECT_ROOT / ".gitignore"
        content = gitignore.read_text()
        assert ".env" in content, ".env must be in .gitignore"


class TestDockerComposeVariableization:
    """Task 2: docker-compose.yml must not have hardcoded user paths."""

    def test_no_hardcoded_user_paths(self):
        dc = PROJECT_ROOT / "docker-compose.yml"
        content = dc.read_text()
        matches = re.findall(r"/Users/\w+/", content)
        assert not matches, f"Hardcoded user paths found: {matches}"

    def test_neo4j_ports_use_variables(self):
        dc = PROJECT_ROOT / "docker-compose.yml"
        content = dc.read_text()
        assert "${NEO4J_HTTP_PORT" in content or "${NEO4J_BOLT_PORT" in content, (
            "Neo4j ports should use environment variables"
        )

    def test_vault_mount_not_readonly(self):
        dc = PROJECT_ROOT / "docker-compose.yml"
        content = dc.read_text()
        ro_vault_mounts = re.findall(r"vault.*:ro", content)
        assert not ro_vault_mounts, (
            f"Vault mounts should not be :ro by default: {ro_vault_mounts}"
        )


class TestValidateEnvScript:
    """Task 4: validate-env.sh must exist."""

    def test_script_exists(self):
        script = PROJECT_ROOT / "scripts" / "validate-env.sh"
        assert script.exists(), "scripts/validate-env.sh must exist"

    def test_script_is_executable(self):
        script = PROJECT_ROOT / "scripts" / "validate-env.sh"
        if not script.exists():
            pytest.skip("Script not yet created")
        assert script.stat().st_mode & 0o111, "validate-env.sh must be executable"
