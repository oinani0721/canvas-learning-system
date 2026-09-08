"""
Unit tests for Neo4j configuration in Settings.

Story 30.1 - AC 2: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE, NEO4J_ENABLED

[Source: docs/stories/30.1.story.md - AC 2]
[Source: backend/app/config.py:324-347]
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config import Settings

# ── 契约演进（f718d040, 2026-05-08 "feat(round-23): stage 1 硬化 ship"）─────────
# 该 commit 给 Settings 加了 config.py:274 `validate_security_defaults`
# (mode="after")：当 `is_local` 为假时，空 NEO4J_PASSWORD 或空 INTERNAL_API_KEY
# 直接 raise（fail-closed）。而 `is_local` = DEBUG and (CORS 含 localhost/127.0.0.1)。
#
# 本文件全部用例都 `clear=True` 清空环境来测「默认值」，于是 DEBUG 回落到
# config.py:112-113 的 default=False ⇒ is_local 为假 ⇒ Settings 构造期必抛，
# 9 条测试全红。这是**契约演进未跟测**，不是回归。
#
# 处置：把「本地开发」这一前提显式化（DEBUG=true；CORS_ORIGINS 的默认值
# config.py:166-169 已含 http://localhost:3000，无需额外设置），让 Settings 能
# 构造出来，从而继续断言它原本要断言的那些 NEO4J_* 默认值 / env 解析。
#
# ⚠️ 为什么这不是「为求绿而放宽」：DEBUG 不在任何一条断言的对象里——实测加上
# DEBUG=true 后 NEO4J_URI/USER/DATABASE/ENABLED 与 NEO4J_PASSWORD("" 空串) 全部
# 保持原值，`test_neo4j_password_empty_default` 断言的空密码语义**未被喂饱**
# （若改成塞一个 NEO4J_PASSWORD 才是自证，卡文明令禁止）。
# 与之配套，本文件末尾新增 TestSecurityDefaultsFailClosed 作**反向锚**：锁住
# 「生产形态（DEBUG 缺省 + 空 INTERNAL_API_KEY）仍然必抛」这一契约本身，
# 避免「让 9 条变绿」把 fail-closed 的覆盖一起弄没。          [CARD-RED-C2]
_LOCAL_DEV_ENV = {"DEBUG": "true"}


class TestNeo4jSettingsDefaults:
    """Test Neo4j settings have correct defaults (AC2)."""

    def test_neo4j_enabled_default_true(self):
        """NEO4J_ENABLED defaults to True."""
        with patch.dict(os.environ, _LOCAL_DEV_ENV, clear=True):
            settings = Settings(
                _env_file=None,
                NEO4J_PASSWORD="test",
            )
            assert settings.NEO4J_ENABLED is True
            assert settings.neo4j_enabled is True

    def test_neo4j_uri_default(self):
        """NEO4J_URI defaults to bolt://localhost:7687."""
        with patch.dict(os.environ, _LOCAL_DEV_ENV, clear=True):
            settings = Settings(_env_file=None)
            assert settings.NEO4J_URI == "bolt://localhost:7687"
            assert settings.neo4j_uri == "bolt://localhost:7687"

    def test_neo4j_user_default(self):
        """NEO4J_USER defaults to 'neo4j'."""
        with patch.dict(os.environ, _LOCAL_DEV_ENV, clear=True):
            settings = Settings(_env_file=None)
            assert settings.NEO4J_USER == "neo4j"
            assert settings.neo4j_user == "neo4j"

    def test_neo4j_database_default(self):
        """NEO4J_DATABASE defaults to 'neo4j'."""
        with patch.dict(os.environ, _LOCAL_DEV_ENV, clear=True):
            settings = Settings(_env_file=None)
            assert settings.NEO4J_DATABASE == "neo4j"
            assert settings.neo4j_database == "neo4j"

    def test_neo4j_password_empty_default(self):
        """NEO4J_PASSWORD defaults to empty string (user must set it)."""
        with patch.dict(os.environ, _LOCAL_DEV_ENV, clear=True):
            settings = Settings(_env_file=None)
            assert settings.NEO4J_PASSWORD == ""
            assert settings.neo4j_password == ""


class TestNeo4jSettingsFromEnv:
    """Test Neo4j settings load from environment variables (AC2)."""

    def test_neo4j_settings_from_env(self):
        """All 5 Neo4j env vars are correctly loaded."""
        env = {
            **_LOCAL_DEV_ENV,  # f718d040 起需显式声明本地开发，见文件头
            "NEO4J_ENABLED": "true",
            "NEO4J_URI": "bolt://custom-host:7688",
            "NEO4J_USER": "admin",
            "NEO4J_PASSWORD": "s3cret_p@ss",
            "NEO4J_DATABASE": "canvas_db",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings(_env_file=None)

            assert settings.neo4j_enabled is True
            assert settings.neo4j_uri == "bolt://custom-host:7688"
            assert settings.neo4j_user == "admin"
            assert settings.neo4j_password == "s3cret_p@ss"
            assert settings.neo4j_database == "canvas_db"

    def test_neo4j_enabled_false_from_env(self):
        """NEO4J_ENABLED=false correctly parsed as bool False."""
        with patch.dict(
            os.environ, {**_LOCAL_DEV_ENV, "NEO4J_ENABLED": "false"}, clear=True
        ):
            settings = Settings(_env_file=None)
            assert settings.neo4j_enabled is False

    def test_neo4j_enabled_case_insensitive(self):
        """NEO4J_ENABLED accepts 'False' (case-insensitive)."""
        with patch.dict(
            os.environ, {**_LOCAL_DEV_ENV, "NEO4J_ENABLED": "False"}, clear=True
        ):
            settings = Settings(_env_file=None)
            assert settings.neo4j_enabled is False

    def test_neo4j_uri_with_different_port(self):
        """NEO4J_URI accepts non-standard ports."""
        with patch.dict(
            os.environ,
            {**_LOCAL_DEV_ENV, "NEO4J_URI": "bolt://localhost:7689"},
            clear=True,
        ):
            settings = Settings(_env_file=None)
            assert settings.neo4j_uri == "bolt://localhost:7689"


# ═══════════════════════════════════════════════════════════════════════════════
# 反向锚：fail-closed 契约本身（配套上面 9 条的 _LOCAL_DEV_ENV 改动）
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityDefaultsFailClosed:
    """f718d040 引入的 config.py:274 validate_security_defaults 必须仍然 fail-closed。

    这个类是上面 9 条改动的**反向锚**：那 9 条通过声明 DEBUG=true 走进
    `is_local` 分支才能构造出 Settings；如果哪天有人把 `is_local` 的条件放宽、
    或把这两处 raise 降级成 warning，上面 9 条**照样绿**（它们本来就走本地分支），
    缺陷会静默通过。这里正面锁住「生产形态必须抛」，让那种放宽有地方变红。

    ⛔ 不得为了让本类通过而修改 config.py:274-298（卡文 §三 禁改）。
    """

    def test_production_shape_without_neo4j_password_raises(self):
        """DEBUG 缺省（生产形态）+ NEO4J_ENABLED + 空 NEO4J_PASSWORD ⇒ 必须抛。"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc:
                Settings(_env_file=None)
        assert "NEO4J_PASSWORD must be set explicitly outside local dev" in str(exc.value)

    def test_production_shape_without_internal_api_key_raises(self):
        """DEBUG 缺省 + 已给 NEO4J_PASSWORD + 空 INTERNAL_API_KEY ⇒ 必须抛。

        单独一条：密码给了之后第一道门放行，才能验到第二道门（否则永远只看到
        NEO4J_PASSWORD 那条报错，INTERNAL_API_KEY 这道门是否还在无从判断）。
        """
        with patch.dict(os.environ, {"NEO4J_PASSWORD": "x"}, clear=True):
            with pytest.raises(ValidationError) as exc:
                Settings(_env_file=None)
        assert "INTERNAL_API_KEY required outside local dev" in str(exc.value)

    def test_local_dev_shape_does_not_raise(self):
        """对照组：DEBUG=true + 默认 CORS（含 localhost）⇒ 不抛。

        没有这一条，上面两条无法区分「fail-closed 生效」与「Settings 根本构造不出来」。
        """
        with patch.dict(os.environ, _LOCAL_DEV_ENV, clear=True):
            settings = Settings(_env_file=None)
        assert settings.DEBUG is True
        assert "localhost" in settings.CORS_ORIGINS
        assert settings.NEO4J_PASSWORD == ""
