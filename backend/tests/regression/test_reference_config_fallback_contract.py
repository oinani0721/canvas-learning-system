"""引用优先级配置的降级契约锁 — P1-05（Codex 对抗审查 2026-08-19）。

背景
----
`app/core/reference_config.py` 曾在配置文件缺失/损坏时静默退回一份硬编码
fallback：`videos/lectures 1.5` · `videos/discussions 1.4` · `max_references 5`。

那是 RAG-S2 T2（2026-08-09）权重翻转**之前**的旧值，方向与正式配置**相反** ——
它把视频转录系统性加权到用户手写笔记之上，正是那次翻转要纠正的问题。于是
R11-BATCH2 T1 虽然把三方 JSON 同步一致了，代码里仍留着第二份「旧真相」，
配置一旦读不到就回到用户初衷的反面。

更隐蔽的是：`_CONFIG_PATH.exists()` 为 False 时不进 except 分支，连 warning
都没有 —— 纯静默降级。

本文件锁住修复后的语义：**中性降级**（零加权）而非方向性旧权重。

⛔ 不使用 mock：全部用真实临时 JSON 文件 + monkeypatch 模块级路径常量，
走真实的 open/json.load 代码路径（DD-03）。
"""

from __future__ import annotations

import json

import pytest

from app.core import reference_config


@pytest.fixture(autouse=True)
def _reset_module_cache():
    """`_config` 是模块级缓存，测试间必须清零，否则前一个用例的结果会串味。"""
    reference_config._config = None
    yield
    reference_config._config = None


def _point_config_at(monkeypatch, path):
    monkeypatch.setattr(reference_config, "_CONFIG_PATH", path)


# ── 正常路径 ───────────────────────────────────────────────────────────────


def test_reads_real_config_when_present(monkeypatch, tmp_path):
    """配置在位时按文件内容返回，不受 fallback 干扰。"""
    cfg = tmp_path / "reference_priority.json"
    cfg.write_text(
        json.dumps(
            {
                "source_priorities": [
                    {"pattern": "节点/**", "weight": 1.5, "label": "手写"},
                    {"pattern": "**/videos/lectures/**", "weight": 1.0, "label": "讲义"},
                ],
                "max_references": 10,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _point_config_at(monkeypatch, cfg)

    prios = reference_config.get_source_priorities()
    weights = {p["pattern"]: p["weight"] for p in prios}

    assert weights["节点/**"] == 1.5
    assert weights["**/videos/lectures/**"] == 1.0
    assert reference_config.get_max_references() == 10


# ── 降级路径：缺失 ─────────────────────────────────────────────────────────


def test_missing_file_degrades_to_neutral_not_legacy_weights(monkeypatch, tmp_path):
    """文件不存在 → 空规则列表（零加权），而**不是**旧的方向性权重。"""
    _point_config_at(monkeypatch, tmp_path / "does-not-exist.json")

    prios = reference_config.get_source_priorities()

    assert prios == [], f"降级应为零加权，实际拿到 {len(prios)} 条规则: {prios}"
    assert reference_config.get_max_references() == 10


def test_missing_file_logs_error_not_silence(monkeypatch, tmp_path, caplog):
    """缺失必须留下 ERROR 痕迹 —— 原实现在这条路径上完全静默。"""
    _point_config_at(monkeypatch, tmp_path / "does-not-exist.json")

    with caplog.at_level("ERROR", logger=reference_config.logger.name):
        reference_config.get_source_priorities()

    assert any(
        "reference_priority.json" in r.message or "reference_priority.json" in r.getMessage() for r in caplog.records
    ), "配置缺失时没有任何 ERROR 日志 —— 静默降级是本次要修的核心问题"


# ── 降级路径：损坏 ─────────────────────────────────────────────────────────


def test_corrupt_json_degrades_to_neutral(monkeypatch, tmp_path):
    """JSON 语法错误 → 中性降级，不抛异常、不回旧权重。"""
    cfg = tmp_path / "reference_priority.json"
    cfg.write_text("{ this is not valid json ", encoding="utf-8")
    _point_config_at(monkeypatch, cfg)

    assert reference_config.get_source_priorities() == []
    assert reference_config.get_max_references() == 10


# ── 核心防回归锁 ───────────────────────────────────────────────────────────


def test_fallback_never_ranks_videos_above_handwritten(monkeypatch, tmp_path):
    """⛔ 方向锁：任何降级路径都不得让 videos 的权重高于 节点/（手写）。

    这是 P1-05 的实质 —— 旧 fallback 恰好违反它（videos 1.5 而 节点/ 不在表内，
    等价于手写走 1.0 默认、视频 1.5 提权）。
    """
    for label, path in (
        ("missing", tmp_path / "nope.json"),
        ("corrupt", tmp_path / "bad.json"),
    ):
        if label == "corrupt":
            path.write_text("[[[", encoding="utf-8")
        reference_config._config = None
        _point_config_at(monkeypatch, path)

        prios = reference_config.get_source_priorities()
        video_w = [p["weight"] for p in prios if "video" in p.get("pattern", "")]
        node_w = [p["weight"] for p in prios if "节点" in p.get("pattern", "")]

        assert not video_w or max(video_w) <= (max(node_w) if node_w else 1.0), (
            f"降级路径 {label} 把 videos 排到了手写笔记之上: videos={video_w} 节点={node_w}"
        )


def test_no_legacy_weight_literals_remain_in_module(monkeypatch, tmp_path):
    """源码级锁：模块内不得再出现旧 fallback 的特征数值组合。

    旧值是 videos/lectures=1.5 与 videos/discussions=1.4 同时出现。单独的 1.5
    是合法的（正式配置里 节点/** 就是 1.5），所以只锁「1.4 + videos/discussions」
    这个仅属于旧 fallback 的组合。
    """
    src = __import__("pathlib").Path(reference_config.__file__).read_text(encoding="utf-8")

    assert '"videos/discussions/**"' not in src, "模块内仍硬编码 videos/discussions 规则 —— 旧 fallback 未清除干净"
    assert '"max_references": 5' not in src, "模块内仍硬编码 max_references=5（旧 fallback 值）"


# ── P1-06 schema 校验（Codex 复核 2026-08-19 追加）─────────────────────────


@pytest.mark.parametrize(
    "label,content",
    [
        ("根为数组", "[]"),
        ("根为 null", "null"),
        ("根为字符串", '"hello"'),
        ("空对象", "{}"),
        ("source_priorities 非数组", '{"source_priorities": {}}'),
        ("规则非对象", '{"source_priorities": ["x"]}'),
        ("规则缺 pattern", '{"source_priorities": [{"weight": 1.0}]}'),
        ("规则缺 weight", '{"source_priorities": [{"pattern": "a/**"}]}'),
        ("pattern 非字符串", '{"source_priorities": [{"pattern": 1, "weight": 1.0}]}'),
        ("weight 非数值", '{"source_priorities": [{"pattern": "a/**", "weight": "x"}]}'),
        ("weight 为 inf", '{"source_priorities": [{"pattern": "a/**", "weight": 1e999}]}'),
        ("weight 为 bool", '{"source_priorities": [{"pattern": "a/**", "weight": true}]}'),
        ("max_references 为 0", '{"source_priorities": [], "max_references": 0}'),
        ("max_references 非整数", '{"source_priorities": [], "max_references": "many"}'),
    ],
)
def test_malformed_schema_degrades_neutrally_without_crashing(monkeypatch, tmp_path, label, content):
    """⛔ 合法 JSON ≠ 合法结构。上一轮只挡语法错误，这些会在请求期崩溃或泄漏旧值。

    Codex 复核实测的两个反例：
      input=[]  → AttributeError: 'list' object has no attribute 'get'
      input={}  → max_references 落回旧值 5（get_max_references 的默认参数）
    """
    cfg = tmp_path / "reference_priority.json"
    cfg.write_text(content, encoding="utf-8")
    _point_config_at(monkeypatch, cfg)

    # 不得抛异常
    prios = reference_config.get_source_priorities()
    max_refs = reference_config.get_max_references()

    assert prios == [], f"[{label}] schema 不合法时应中性降级，实得 {prios}"
    assert max_refs == 10, f"[{label}] max_references 泄漏了非中性值 {max_refs}（旧 fallback 是 5）"


def test_get_max_references_never_falls_back_to_legacy_five(monkeypatch, tmp_path):
    """源码级锁：get_max_references 的默认参数不得是旧值 5。

    这正是 Codex 复核抓到的第二处真相源 —— 上一轮改了 _load_config 却漏了这里。
    """
    src = __import__("pathlib").Path(reference_config.__file__).read_text(encoding="utf-8")

    assert '.get("max_references", 5)' not in src, (
        "get_max_references 仍以 5 为默认值 —— config 为 {} 时会从这里泄漏回旧行为"
    )


def test_valid_config_still_accepted_after_validator(monkeypatch, tmp_path):
    """校验器不得误杀正常配置（含可选 label 缺失、int 权重）。"""
    cfg = tmp_path / "reference_priority.json"
    cfg.write_text(
        json.dumps(
            {
                "source_priorities": [
                    {"pattern": "节点/**", "weight": 1.5, "label": "手写"},
                    {"pattern": "raw/**", "weight": 1},  # int 权重 + 无 label
                ],
                "max_references": 10,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _point_config_at(monkeypatch, cfg)

    prios = reference_config.get_source_priorities()

    assert len(prios) == 2
    assert prios[0]["weight"] == 1.5
    assert prios[1]["weight"] == 1.0, "int 权重应被归一为 float"


def test_apply_source_priority_is_identity_under_neutral_fallback(monkeypatch, tmp_path):
    """零加权时 apply_source_priority 必须原样返回（含顺序），不误改 score。"""
    _point_config_at(monkeypatch, tmp_path / "absent.json")

    results = [
        {"score": 0.9, "metadata": {"canvas_file": "videos/lectures/l1.md"}},
        {"score": 0.5, "metadata": {"canvas_file": "节点/recursion.md"}},
    ]
    out = reference_config.apply_source_priority(results)

    assert [r["score"] for r in out] == [0.9, 0.5], "中性降级下不应改动任何 score"
    assert out is results, "空规则应短路直接返回原对象"
