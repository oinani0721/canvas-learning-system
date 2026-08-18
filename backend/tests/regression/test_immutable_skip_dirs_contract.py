"""索引安全边界的不可撤销契约锁 — P1-02（Codex 对抗审查 2026-08-19）。

背景
----
`VAULT_INDEX_SKIP_DIRS` 是一个 env 可**整体替换**的逗号串。设
`VAULT_INDEX_SKIP_DIRS=.git` 就能一次性撤掉全部黑名单。

Codex 指出这让 A-9 的 `_待处理`/`_archive` 形同虚设。独立核验进一步发现问题
**比审查说的更大**：`检验白板` 与 `验收单` 自 2026-07-10 检验白板 v1 审计起就
与其它项写在同一条串里，共享完全相同的可撤销性 —— 即**信息隔离铁律
（Karpicke d=1.50，考题绝不能经 RAG 回流）一直可以被一行 env 撤销**。

核验实测的防御层数（决定硬底范围与优先级）：
  - 检验白板：双层 —— 目录黑名单 + 读侧 exclude_doc_types（靠 frontmatter
    `type: exam_board` 或 exam_question_id 推断）
  - 验收单 / _待处理 / _archive：**单层** —— frontmatter 无 doc_type，读侧不挡，
    目录黑名单是唯一防线

因此硬底范围取的是「全部信息隔离面 + A-9 新边界 + 仓库内部目录」，而非审查
建议的「只锁 _待处理/_archive」。

⛔ 不使用 mock：用 monkeypatch.setenv + 真实重建 Settings，走真实 pydantic
env 解析路径（DD-03）。
"""

from __future__ import annotations

import fnmatch

import pytest

from app.config import IMMUTABLE_VAULT_SKIP_DIRS, Settings


def _blocked(path: str, skip_dirs: list[str]) -> bool:
    """复刻两条索引路径的判定语义：对 rel_path 逐段 fnmatch。"""
    return any(fnmatch.fnmatch(part, pat) for part in path.split("/")[:-1] for pat in skip_dirs)


# ── 核心反例：env 撤不掉硬底 ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "hostile_env",
    [
        ".git",  # Codex 原始反例：只留一项
        "",  # 极端：整串清空
        "node_modules,templates",  # 看似合理但漏掉全部安全面
    ],
)
def test_env_override_cannot_remove_isolation_boundaries(monkeypatch, hostile_env):
    """任何 env 覆盖都不得让信息隔离面变成可索引。"""
    monkeypatch.setenv("VAULT_INDEX_SKIP_DIRS", hostile_env)
    skip_dirs = Settings().effective_vault_skip_dirs()

    for victim in ("检验白板/exam.md", "验收单/uat.md", "_待处理/碎片.md", "_archive/old.md"):
        assert _blocked(victim, skip_dirs), (
            f"env VAULT_INDEX_SKIP_DIRS={hostile_env!r} 撤掉了安全边界，{victim} 变为可索引"
        )


def test_env_override_still_allows_additions(monkeypatch):
    """env 仍可**追加**新的排除项 —— 硬底只加不减，不冻结配置能力。"""
    monkeypatch.setenv("VAULT_INDEX_SKIP_DIRS", "自定义排除目录")
    skip_dirs = Settings().effective_vault_skip_dirs()

    assert _blocked("自定义排除目录/x.md", skip_dirs), "env 追加的目录未生效"
    assert _blocked("检验白板/exam.md", skip_dirs), "追加时硬底丢失"


def test_learning_content_still_indexable_under_hard_floor(monkeypatch):
    """硬底不得误伤正常学习内容。"""
    monkeypatch.setenv("VAULT_INDEX_SKIP_DIRS", ".git")
    skip_dirs = Settings().effective_vault_skip_dirs()

    for ok in ("节点/recursion.md", "原白板/CS 61B.md", "raw/lecture-1.md"):
        assert not _blocked(ok, skip_dirs), f"硬底误伤了学习内容: {ok}"


# ── 硬底内容与两侧一致性 ───────────────────────────────────────────────────


def test_hard_floor_covers_all_isolation_surfaces():
    """硬底必须覆盖信息隔离面 —— 漏一项就等于那一项仍可被 env 撤销。"""
    for required in ("检验白板", "验收单", "_待处理", "_archive"):
        assert required in IMMUTABLE_VAULT_SKIP_DIRS, f"{required} 不在不可撤销硬底里，仍可被一行 env 撤销"


def test_lib_and_app_hard_floors_stay_identical():
    """lib 侧硬底必须与 app 权威源逐字一致（lib 不能 import app，无法单源）。"""
    from agentic_rag.clients.lancedb_client import (
        IMMUTABLE_VAULT_SKIP_DIRS as LIB_IMMUTABLE,
    )

    assert set(LIB_IMMUTABLE) == set(IMMUTABLE_VAULT_SKIP_DIRS), (
        "两侧硬底漂移：\n"
        f"  仅 app 有: {sorted(set(IMMUTABLE_VAULT_SKIP_DIRS) - set(LIB_IMMUTABLE))}\n"
        f"  仅 lib 有: {sorted(set(LIB_IMMUTABLE) - set(IMMUTABLE_VAULT_SKIP_DIRS))}"
    )


def test_hard_floor_is_subset_of_default_config():
    """硬底应已全部出现在默认配置串里 —— 否则默认态与硬底态行为不一致，易误判。"""
    default_dirs = {d.strip() for d in Settings().VAULT_INDEX_SKIP_DIRS.split(",") if d.strip()}

    missing = set(IMMUTABLE_VAULT_SKIP_DIRS) - default_dirs
    assert not missing, f"硬底项未出现在默认配置串中: {sorted(missing)}"


# ── lib 层独立防线（调用方传参也撤不掉） ───────────────────────────────────


def test_lib_union_holds_even_when_caller_passes_hostile_list():
    """lib 层是最后一道：调用方显式传一个不含安全面的列表，也要被 union 回来。"""
    from agentic_rag.clients.lancedb_client import _with_immutable_skip_dirs

    merged = _with_immutable_skip_dirs([".git"])

    for required in ("检验白板", "验收单", "_待处理", "_archive"):
        assert required in merged, f"lib union 未补回 {required}"
    assert merged[0] == ".git", "union 应保持调用方原顺序在前"


def test_lib_union_is_idempotent():
    """重复 union 不产生重复项（避免黑名单无限膨胀）。"""
    from agentic_rag.clients.lancedb_client import _with_immutable_skip_dirs

    once = _with_immutable_skip_dirs([".git"])
    twice = _with_immutable_skip_dirs(once)

    assert once == twice
    assert len(twice) == len(set(twice)), f"union 产生了重复项: {twice}"
