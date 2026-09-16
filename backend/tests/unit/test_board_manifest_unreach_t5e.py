"""CARD-T-UNREACH [BATCH-2026-09-11-第十四批]: except 顺序死分支复活后的行为门。

钉住 `boards.py::get_board_manifest_http` / `board_manifest_tools.py::get_board_manifest`
两处 `except pydantic.ValidationError` —— 它们原本是死分支 (`ValidationError` 是
`ValueError` 子类, 被上游 `except ValueError` 先接走), 注释宣称的「诚实 500 /
结构化错误」纵深兜底从未生效。本卡把它调到 `except ValueError` 之前后:

- schema 契约被破 (service 产出的数据过不了自身 response schema)
  → HTTP **500** / MCP 结构化「manifest 投影 schema 异常, 已记录日志」;
- 非 ValidationError 的普通 `ValueError` (如非法 board_id) 仍走 **422** /「非法参数: 」;
- `KeyError` (非 `ValueError` 子类) 不受 except 顺序调整影响, 仍 **404** / 原样 detail。

⛔ DD-03: 异常由**真** pydantic `model_validate` 失败产生 —— monkeypatch 只替换文件
I/O 协作者 `serve_manifest` 的返回值 (缺必填键的 dict), 驱动真实错误路径; 不伪造
异常对象、不用 MagicMock。

隔离: 直接 `asyncio.run` 协程 + monkeypatch, 不起 lifespan、不连 Neo4j (7691/7687)。
"""

from __future__ import annotations

import asyncio
import ast
from collections.abc import Callable
from typing import Any, Literal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import app.api.v1.endpoints.boards as boards_mod
import app.core.vault_scope as vault_scope_mod
import app.mcp.tools.board_manifest_tools as tools_mod
from app.api.v1.endpoints.boards import BoardManifestRequest, get_board_manifest_http
from app.mcp.tools.board_manifest_tools import GetBoardManifestInput, get_board_manifest
from app.models.board_manifest import project_manifest

# service 产出缺 `_ManifestEnvelope` 三个必填键 (source / source_status /
# id_stability) 的 dict —— `project_manifest` 的 `model_validate` 会真抛
# ValidationError。空 dict 是最小充分形态 (三键全缺)。
_View = Literal["study", "exam"]

_SCHEMA_BREAKING_RAW: dict[str, Any] = {}

_SCHEMA_ERROR_TEXT = "manifest 投影 schema 异常, 已记录日志"


def _serve_returns_schema_breaking(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    """替身 `serve_manifest`: 同步返回过不了 response schema 的 dict (真实错误路径)。"""
    return dict(_SCHEMA_BREAKING_RAW)


def _serve_raises(exc: BaseException) -> Callable[..., dict[str, Any]]:
    """替身 `serve_manifest`: 抛指定的非 ValidationError 异常 (对照组)。"""

    def _inner(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise exc

    return _inner


@pytest.fixture
def no_vault_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """放行 HTTP 端点的 vault 门 (不用下划线前缀: 那会被 pyright 判为未访问的私有函数)。

    `resolve_vault_scope` 在 `get_board_manifest_http` 内是**函数内 import**
    (每次调用才绑名) ⇒ 必须 patch **源模块** `app.core.vault_scope` 的属性;
    patch boards 模块的同名属性无效 (那里根本没有这个名字)。
    """
    monkeypatch.setattr(vault_scope_mod, "resolve_vault_scope", lambda *a, **k: None)


def _call_http(view: _View = "study") -> Any:
    return asyncio.run(get_board_manifest_http(BoardManifestRequest(vault_id="x", view=view)))


def _call_mcp(view: _View = "study") -> dict[str, Any]:
    return asyncio.run(get_board_manifest(GetBoardManifestInput(view=view)))


# ─────────────────────────────────────────────────────────────────────────────
# 前置自证: 触发面确实产生真 pydantic ValidationError, 且它确实是 ValueError 子类
# (缺陷根因)。这两条在改前改后都绿 —— 它们证明的是 pydantic 的 MRO 事实,
# 不是本卡的行为变化。
# ─────────────────────────────────────────────────────────────────────────────
def test_project_manifest_raises_real_validation_error() -> None:
    with pytest.raises(ValidationError) as exc_info:
        project_manifest(dict(_SCHEMA_BREAKING_RAW), "study")
    # 真 pydantic 校验失败: source / source_status / id_stability 三个必填键缺失
    assert len(exc_info.value.errors()) == 3
    # 缺陷根因: 正因为它是 ValueError, 上游 `except ValueError` 才能先接走它
    assert isinstance(exc_info.value, ValueError)


# ─────────────────────────────────────────────────────────────────────────────
# 结构门 (常驻): AST 断言 ValidationError 的 handler 索引 < ValueError 的索引。
# 不降级为「只要 except 在就算过」—— 顺序本身就是被修的东西。
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("module", "fn_name"),
    [(boards_mod, "get_board_manifest_http"), (tools_mod, "get_board_manifest")],
)
def test_validation_error_handler_precedes_value_error(module: Any, fn_name: str) -> None:
    path = module.__file__
    assert path is not None
    tree = ast.parse(open(path, encoding="utf-8").read())
    fn = next(n for n in ast.walk(tree) if getattr(n, "name", "") == fn_name)
    checked = 0
    for node in ast.walk(fn):
        if not isinstance(node, ast.Try):
            continue
        order = [getattr(h.type, "attr", getattr(h.type, "id", None)) for h in node.handlers]
        if "ValidationError" in order and "ValueError" in order:
            assert order.index("ValidationError") < order.index("ValueError"), (
                f"{path}::{fn_name} except 顺序 {order} —— ValidationError 被 ValueError 遮蔽成死分支"
            )
            checked += 1
    # 验伪锚: 若 handler 被改名/删掉导致上面的循环一次都没进, 这里会红,
    # 而不是「没有断言执行过」却报绿。
    assert checked == 1, f"{path}::{fn_name} 未找到同时含 ValidationError 与 ValueError 的 try"


# ─────────────────────────────────────────────────────────────────────────────
# 行为门 (本卡的行为变化, 改前必红)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("view", ["study", "exam"])
def test_http_schema_break_returns_500(monkeypatch: pytest.MonkeyPatch, view: _View, no_vault_gate: None) -> None:
    """schema 契约被破 → 诚实 500 (改前: 被 `except ValueError` 接走 = 422)。"""
    monkeypatch.setattr(boards_mod, "serve_manifest", _serve_returns_schema_breaking)
    with pytest.raises(HTTPException) as exc_info:
        _call_http(view)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == _SCHEMA_ERROR_TEXT


@pytest.mark.parametrize("view", ["study", "exam"])
def test_mcp_schema_break_returns_structured_error(monkeypatch: pytest.MonkeyPatch, view: _View) -> None:
    """schema 契约被破 → 结构化 schema 异常 (改前: error 以「非法参数: 」开头)。"""
    monkeypatch.setattr(tools_mod, "serve_manifest", _serve_returns_schema_breaking)
    out = _call_mcp(view)
    assert out["ok"] is False
    assert out["error"] == _SCHEMA_ERROR_TEXT
    assert out["manifest"] is None


# ─────────────────────────────────────────────────────────────────────────────
# 对照组 (改前改后两态都必须成立): 调顺序没有破坏 ValueError / KeyError 分支
# ─────────────────────────────────────────────────────────────────────────────
def test_http_plain_value_error_still_422(monkeypatch: pytest.MonkeyPatch, no_vault_gate: None) -> None:
    monkeypatch.setattr(boards_mod, "serve_manifest", _serve_raises(ValueError("bad board_id")))
    with pytest.raises(HTTPException) as exc_info:
        _call_http()
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "bad board_id"


def test_mcp_plain_value_error_still_invalid_param(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools_mod, "serve_manifest", _serve_raises(ValueError("bad board_id")))
    out = _call_mcp()
    assert out["ok"] is False
    assert out["error"] == "非法参数: bad board_id"


def test_http_key_error_still_404(monkeypatch: pytest.MonkeyPatch, no_vault_gate: None) -> None:
    """KeyError 非 ValueError 子类 ⇒ 不受 except 顺序调整影响。"""
    monkeypatch.setattr(boards_mod, "serve_manifest", _serve_raises(KeyError("no such board")))
    with pytest.raises(HTTPException) as exc_info:
        _call_http()
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "no such board"


def test_mcp_key_error_still_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools_mod, "serve_manifest", _serve_raises(KeyError("no such board")))
    out = _call_mcp()
    assert out["ok"] is False
    assert out["error"] == "no such board"
