"""文件名黑名单的作用域契约锁 — P2-02（Codex 对抗审查 2026-08-19）。

背景
----
A-4 把 `excalibrain.md` 直接加进 `DEFAULT_VAULT_SKIP_FILES`，而该表是**任意层级
basename** 匹配。Codex 指出两个后果：

  1. **误排**：`节点/excalibrain.md` 这类用户完全可能手写的深层同名笔记也被排除。
     根级那一份是 ExcaliBrain 插件的运行时产物，深层同名文件没有任何理由被
     判定为工具产物。
  2. **漏排**：`fnmatch` 在 POSIX 下大小写敏感，`ExcaliBrain.md` 会漏网 ——
     而插件在不同版本/平台上写出的文件名大小写并不稳定。

修复引入第二张表 `DEFAULT_VAULT_SKIP_ROOT_FILES`（仅根级 + casefold 精确比较），
并把四条消费路径全部收敛到同一个 `_is_skipped_vault_file`。

⛔ 不使用 mock：直接调用真实判定函数 + 真实临时 vault 目录树走 os.walk。
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from agentic_rag.clients.lancedb_client import (
    DEFAULT_VAULT_SKIP_FILES,
    DEFAULT_VAULT_SKIP_ROOT_FILES,
    _is_skipped_vault_file,
)


def _skipped(rel_path: str) -> bool:
    return _is_skipped_vault_file(rel_path, DEFAULT_VAULT_SKIP_FILES)


# ── 核心：仅根级语义 ───────────────────────────────────────────────────────


def test_root_level_plugin_file_is_skipped():
    """根级 excalibrain.md 是插件运行时产物 → 排除。"""
    assert _skipped("excalibrain.md")


@pytest.mark.parametrize(
    "deep_path",
    [
        "节点/excalibrain.md",
        "原白板/excalibrain.md",
        "raw/notes/excalibrain.md",
    ],
)
def test_deep_same_name_note_is_not_skipped(deep_path):
    """⛔ Codex 反例的修复点：深层同名笔记是合法学习内容，不得误排。"""
    assert not _skipped(deep_path), f"{deep_path} 被误排 —— 仅根级规则漏到了深层，用户手写笔记会静默消失"


@pytest.mark.parametrize("variant", ["ExcaliBrain.md", "EXCALIBRAIN.md", "Excalibrain.md"])
def test_root_level_case_variants_are_skipped(variant):
    """⛔ Codex 反例的另一半：大小写变体在根级也必须挡住（casefold）。"""
    assert _skipped(variant), f"根级 {variant} 漏排 —— 插件文件名大小写并不稳定"


def test_deep_case_variants_still_not_skipped():
    """casefold 只作用于根级，不得连带把深层变体也排掉。"""
    assert not _skipped("节点/ExcaliBrain.md")


def test_similar_names_are_not_over_matched():
    """不做通配 —— 用户手写的近似名不受影响（沿用 A-4 原有的防误伤意图）。"""
    for ok in ("excalibrain-笔记.md", "my-excalibrain.md", "excalibrain2.md"):
        assert not _skipped(ok), f"{ok} 被过度匹配"


# ── 任意层级表的语义不受影响 ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "path",
    [
        "CLAUDE.md",
        "节点/CLAUDE.md",
        "raw/deep/UAT-1.md",
        "原白板/未命名.md",
        "a/b/c/foo.excalidraw.md",
    ],
)
def test_anywhere_level_blacklist_still_applies_at_any_depth(path):
    """DEFAULT_VAULT_SKIP_FILES 保持任意层级语义，不能被本次改动收窄。"""
    assert _skipped(path), f"{path} 应在任意层级被排除"


def test_normal_learning_content_passes():
    for ok in ("节点/recursion.md", "原白板/CS 61B.md", "raw/lecture-1.md"):
        assert not _skipped(ok)


# ── 路径分隔符归一 ─────────────────────────────────────────────────────────


def test_windows_style_separator_normalized():
    """rel_path 可能带 os.sep；判定前必须归一，否则根级判断会失效。"""
    assert not _skipped("节点\\excalibrain.md".replace("\\", "/"))
    assert _skipped("./excalibrain.md".replace("./", ""))


def test_leading_slash_does_not_break_root_detection():
    assert _skipped("/excalibrain.md")


# ── 四路一致性（同一判定函数） ─────────────────────────────────────────────


def test_orchestrator_should_index_uses_same_rule():
    """orchestrator 准入门与索引路径必须给出一致判定。"""
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    orch = VaultIndexOrchestrator.__new__(VaultIndexOrchestrator)
    orch._skip_dirs = [".git"]

    ok_deep, reason_deep = orch.should_index("节点/excalibrain.md")
    ok_root, reason_root = orch.should_index("excalibrain.md")

    assert ok_deep is True, f"orchestrator 误排深层同名笔记 (reason={reason_deep})"
    assert ok_root is False and reason_root == "blacklisted_file"


def test_full_scan_and_single_file_agree(tmp_path):
    """全量扫描与单文件判定对同一组文件给出相同结论。"""
    vault = Path(tempfile.mkdtemp(prefix="p202-scope-"))
    try:
        (vault / "节点").mkdir(parents=True)
        (vault / "excalibrain.md").write_text("plugin runtime", encoding="utf-8")
        (vault / "节点" / "excalibrain.md").write_text("# 我的笔记", encoding="utf-8")
        (vault / "节点" / "recursion.md").write_text("# 递归", encoding="utf-8")

        walked = []
        import os

        for root, _dirs, files in os.walk(vault):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), vault)
                if not _is_skipped_vault_file(rel, DEFAULT_VAULT_SKIP_FILES):
                    walked.append(rel.replace(os.sep, "/"))

        assert "节点/excalibrain.md" in walked, "全量扫描漏掉了合法深层笔记"
        assert "节点/recursion.md" in walked
        assert "excalibrain.md" not in walked, "全量扫描收了根级插件文件"
    finally:
        shutil.rmtree(vault, ignore_errors=True)


# ── 表本身的健康性 ─────────────────────────────────────────────────────────


def test_root_table_has_no_glob_patterns():
    """仅根级表刻意不支持通配 —— 出现 * 说明有人误加，会重蹈误伤覆辙。"""
    for name in DEFAULT_VAULT_SKIP_ROOT_FILES:
        assert "*" not in name and "?" not in name, (
            f"仅根级表不应含通配符: {name!r}（用精确名，避免 excalibrain* 吃掉手写笔记）"
        )


def test_excalibrain_moved_out_of_anywhere_table():
    """excalibrain.md 必须已从任意层级表移走，否则仅根级规则形同虚设。"""
    assert "excalibrain.md" not in DEFAULT_VAULT_SKIP_FILES, (
        "excalibrain.md 仍留在任意层级表里 —— 深层同名笔记依旧被误排"
    )
