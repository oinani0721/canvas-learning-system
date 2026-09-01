"""backend/openapi.json 快照漂移门(进程内) — CARD-DEBT-openapi-sync

[BATCH-2026-09-01-第八批 / CARD-DEBT-openapi-sync]

两类断言, 缺一不可:
  1. **生产形态**: 用真实 `app.openapi()` 比对 committed 快照, 断言无漂移。
     这条是本门的主判据 —— 合成 fixture 再多也证明不了「仓里那份快照是新的」。
  2. **合成形态**: 用小 spec 逐条钉死归一化的五条规则(哪些差异该被吞、哪些必须
     暴露)。没有这几条, 第 1 条绿了也可能是「比对函数把一切都判等」。

不起 lifespan: 本文件只调 `check-openapi-drift.py` 的纯函数与 `load_live_schema()`,
后者内部对 `app.openapi()` 全程 socket-connect 禁闭, 从不构造 TestClient、
从不进入 `app.router.lifespan_context`。test_lockdown_actually_blocks 自证这一点。

本门证明什么: committed 快照与当前 app.openapi() 归一化后相等, 且归一化按预期
  吞掉/暴露了哪些差异。
本门不证明什么: 不验证实现是否符合 spec(那是同目录 test_openapi_contract.py 用
  schemathesis 在做), 不验证 CI workflow 会因漂移变红(需 push 后 GitHub 实跑,
  是本卡已知证据缺口), 不验证跨 Python 版本导出一致(本机 3.14 / CI 3.11 未对跑)。
"""

import copy
import importlib.util
import json
import socket
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
DRIFT_TOOL = REPO_ROOT / "scripts" / "spec-tools" / "check-openapi-drift.py"
SNAPSHOT = BACKEND_DIR / "openapi.json"

pytestmark = pytest.mark.contract


def _load_drift_module():
    """加载文件名带连字符的脚本(不能走普通 import)。"""
    spec = importlib.util.spec_from_file_location("_check_openapi_drift", DRIFT_TOOL)
    if spec is None or spec.loader is None:  # pragma: no cover — 路径错时立即失败
        raise RuntimeError(f"无法加载 {DRIFT_TOOL}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # 不往 scripts/spec-tools/ 落 __pycache__
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


drift = _load_drift_module()


@pytest.fixture(scope="module")
def live_schema():
    """真实 app.openapi()(import-only, 无 lifespan)。module 作用域: 只导出一次。"""
    return drift.load_live_schema()


@pytest.fixture(scope="module")
def committed_snapshot():
    assert SNAPSHOT.is_file(), f"committed 快照缺失: {SNAPSHOT}"
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


# ══════════════════════════════════════════════════════════════════════════
# 1. 生产形态: committed 快照 vs 真实 app.openapi()
# ══════════════════════════════════════════════════════════════════════════


def test_committed_snapshot_has_no_drift(committed_snapshot, live_schema):
    clean, details = drift.compare(committed_snapshot, live_schema)
    assert clean, (
        "backend/openapi.json 与 app.openapi() 已漂移。禁手改快照, 重生成:\n"
        "  cd backend && .venv/bin/python ../scripts/spec-tools/check-openapi-drift.py "
        "--write openapi.json\n差异前 20 条:\n" + "\n".join(details[:20])
    )


def test_snapshot_carries_generator_provenance(committed_snapshot):
    """快照必须由本脚本 --write 产出(禁手改的可核对痕迹)。"""
    info = committed_snapshot.get("info", {})
    assert info.get("x-generator") == drift.X_GENERATOR_NAME, (
        f"x-generator={info.get('x-generator')!r} — 快照应由 check-openapi-drift.py "
        "--write 生成; 手改或旧 export-openapi.py 产物不合规"
    )
    assert info.get("x-generated-at"), "快照缺 x-generated-at"


def test_lockdown_actually_blocks():
    """自证: socket 禁闭真的会拦 connect(否则「无 lifespan」是空话)。"""
    with pytest.raises(RuntimeError, match="socket connect blocked"):
        with drift.socket_connect_lockdown():
            socket.socket().connect(("127.0.0.1", 65000))
    # 退出上下文后必须还原, 不污染同进程其他测试
    assert socket.socket.connect.__name__ != "_blocked_connect"


# ══════════════════════════════════════════════════════════════════════════
# 2. 合成形态: 归一化五条规则各自的承重行为
# ══════════════════════════════════════════════════════════════════════════

BASE_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "t", "version": "1"},
    "paths": {
        "/a": {"get": {"responses": {"200": {"description": "ok"}}}},
        "/b": {"get": {"responses": {"200": {"description": "ok"}}}},
    },
    "components": {
        "schemas": {
            "S": {
                "type": "object",
                "required": ["beta", "alpha"],
                "properties": {
                    "alpha": {"type": "string", "enum": ["z", "a", "m"]},
                    "beta": {"type": "string"},
                },
            }
        }
    },
}


def _mutated(fn):
    spec = copy.deepcopy(BASE_SPEC)
    fn(spec)
    return spec


def test_volatile_keys_are_absorbed():
    """规则 1: info.x-generated-at / x-generator 差异不算漂移(防门恒红)。"""
    other = _mutated(
        lambda s: s["info"].update({"x-generated-at": "1999-01-01T00:00:00+00:00", "x-generator": "whatever"})
    )
    clean, _ = drift.compare(other, BASE_SPEC)
    assert clean, "只差易变键不应报漂移"


def test_dict_key_order_is_absorbed():
    """规则 2: 对象成员顺序无语义, 不算漂移。"""
    reordered = {
        "components": BASE_SPEC["components"],
        "paths": BASE_SPEC["paths"],
        "info": BASE_SPEC["info"],
        "openapi": BASE_SPEC["openapi"],
    }
    clean, _ = drift.compare(reordered, BASE_SPEC)
    assert clean, "仅 key 顺序不同不应报漂移"


def test_required_order_is_absorbed():
    """规则 3: required 是集合语义 — 顺序变化不算漂移。"""
    other = _mutated(lambda s: s["components"]["schemas"]["S"].update({"required": ["alpha", "beta"]}))
    clean, _ = drift.compare(other, BASE_SPEC)
    assert clean, "required 顺序变化不应报漂移(pydantic 按字段声明序生成)"


def test_required_membership_change_is_drift():
    """规则 3 的反面: required 集合**内容**变化必须暴露。"""
    other = _mutated(lambda s: s["components"]["schemas"]["S"].update({"required": ["alpha"]}))
    clean, details = drift.compare(other, BASE_SPEC)
    assert not clean, "required 少一个字段必须报漂移"
    assert any("S" in line and "required" in line for line in details), details


def test_required_duplicate_is_drift():
    """sorted 而非 set: 重复项不被吞。"""
    other = _mutated(lambda s: s["components"]["schemas"]["S"].update({"required": ["alpha", "beta", "beta"]}))
    clean, _ = drift.compare(other, BASE_SPEC)
    assert not clean, "required 出现重复项必须报漂移"


def test_required_boolean_form_untouched():
    """同名 key 的 Parameter Object 用法 required: true 是标量, 不走集合排序。"""
    with_param = _mutated(
        lambda s: s["paths"]["/a"]["get"].update({"parameters": [{"name": "q", "in": "query", "required": True}]})
    )
    flipped = copy.deepcopy(with_param)
    flipped["paths"]["/a"]["get"]["parameters"][0]["required"] = False
    clean, details = drift.compare(with_param, flipped)
    assert not clean, "required: true → false 必须报漂移"
    assert any("required" in line for line in details), details


def test_enum_order_is_drift():
    """规则 4: enum 有序语义 — 顺序变化必须暴露, 不得当集合吞掉。"""
    other = _mutated(lambda s: s["components"]["schemas"]["S"]["properties"]["alpha"].update({"enum": ["a", "m", "z"]}))
    clean, details = drift.compare(other, BASE_SPEC)
    assert not clean, "enum 顺序变化必须报漂移(取值顺序有语义)"
    assert any("enum" in line for line in details), details


def test_enum_value_change_is_drift():
    other = _mutated(
        lambda s: s["components"]["schemas"]["S"]["properties"]["alpha"].update({"enum": ["z", "a", "CHANGED"]})
    )
    clean, details = drift.compare(other, BASE_SPEC)
    assert not clean
    assert any("enum" in line for line in details), details


def test_path_removal_is_drift_and_names_the_path():
    other = _mutated(lambda s: s["paths"].pop("/b"))
    clean, details = drift.compare(other, BASE_SPEC)
    assert not clean, "缺一个 path 必须报漂移"
    assert any("/b" in line for line in details), f"摘要须点名 /b: {details}"


def test_path_addition_is_drift_and_names_the_path():
    other = _mutated(lambda s: s["paths"].update({"/c": {"get": {"responses": {"200": {"description": "ok"}}}}}))
    clean, details = drift.compare(other, BASE_SPEC)
    assert not clean
    assert any("/c" in line for line in details), f"摘要须点名 /c: {details}"


def test_description_change_is_drift():
    """归一化四条之外的一切差异原样暴露 — 连文案都算。"""
    other = _mutated(lambda s: s["paths"]["/a"]["get"]["responses"]["200"].update({"description": "changed"}))
    clean, _ = drift.compare(other, BASE_SPEC)
    assert not clean, "description 变化必须报漂移"


def test_bool_to_number_is_drift():
    """规则 5: Python 的 True == 1 会吞掉 bool↔数字真漂移, 必须显式打破。

    JSON 里 true 与 1 序列化不同, 是真实契约变更(default: true → default: 1
    改变客户端收到的值)。
    """
    other = _mutated(
        lambda s: s["components"]["schemas"]["S"]["properties"].update({"beta": {"type": "string", "default": 1}})
    )
    base_with_bool = _mutated(
        lambda s: s["components"]["schemas"]["S"]["properties"].update({"beta": {"type": "string", "default": True}})
    )
    clean, details = drift.compare(base_with_bool, other)
    assert not clean, "default true → 1 必须报漂移(Python True==1 的语言坑不许带进门)"
    assert any("boolean" in line and "number" in line for line in details), details


def test_int_vs_float_absorbed_as_json_number():
    """规则 5 的另一半: JSON 只有一个数字类型, 1 与 1.0 语义相同, 有意吸收。"""
    other = _mutated(
        lambda s: s["components"]["schemas"]["S"]["properties"].update({"beta": {"type": "string", "default": 1.0}})
    )
    base_with_int = _mutated(
        lambda s: s["components"]["schemas"]["S"]["properties"].update({"beta": {"type": "string", "default": 1}})
    )
    clean, _ = drift.compare(base_with_int, other)
    assert clean, "int↔float 同为 JSON number, 不应报漂移"


def test_enum_bool_vs_number_is_drift():
    """enum 里的 true 与 1 同样不可混(标签化覆盖数组元素)。"""
    base_bool = _mutated(
        lambda s: s["components"]["schemas"]["S"]["properties"].update(
            {"alpha": {"type": "string", "enum": [True, False]}}
        )
    )
    other_num = _mutated(
        lambda s: s["components"]["schemas"]["S"]["properties"].update({"alpha": {"type": "string", "enum": [1, 0]}})
    )
    clean, details = drift.compare(base_bool, other_num)
    assert not clean, "enum [true,false] → [1,0] 必须报漂移"
    assert any("boolean" in line and "number" in line for line in details), details


def test_write_roundtrip_produces_clean_json_structure():
    """--write 的 untag 往返: 落盘内容必须是纯 JSON(不得把类型标签序列化进去)。"""
    import tempfile

    with tempfile.TemporaryDirectory() as raw_tmp:
        target = Path(raw_tmp) / "snap.json"
        assert drift.write_snapshot(target) == 0
        spec = json.loads(target.read_text(encoding="utf-8"))
    # 若 untag 缺失/不完整, "openapi" 等标量字段会变成 ["string", "3.1.0"] 双元素数组
    assert isinstance(spec.get("openapi"), str), "'openapi' 字段被标签污染"
    assert isinstance(spec.get("info", {}).get("title"), str), "info.title 被标签污染"
    assert isinstance(spec.get("info", {}).get("x-generated-at"), str)
    assert isinstance(spec.get("paths"), dict)
    assert isinstance(spec.get("components", {}).get("schemas"), dict)


def test_canonicalize_does_not_mutate_input():
    """归一化不得就地改调用方的 spec(负控与门都依赖这一点)。"""
    original = copy.deepcopy(BASE_SPEC)
    drift.canonicalize(BASE_SPEC)
    assert BASE_SPEC == original, "canonicalize 污染了入参"
