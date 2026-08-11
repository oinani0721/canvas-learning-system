"""`sync_board_concepts.py` 回归锁 (RAG-S2.6 独立审查处置)。

脚本住在 vault 里 (容器视角是数据卷不是代码), 与 decay_beta.py 同款:
契约测试用 sys.path import 真相源, 在 tmp vault 上跑真实读写。

每条测试对应一个**已复现**的审查发现 —— 全是会动用户真实白板文件的缺陷:
  H1 包络吞掉用户手写内容 (数据损坏, 已跑通完整触发链)
  H2 缺 `## Concepts` 段时假绿 (第一把锁不会红)
  H3 frontmatter 自由文本被逐字写进白板 (直通检验白板的信息隔离面)
  H4 与后端 _normalize_mastery 的口径分歧 (两把锁变成两台不同刻度的秤)
  H5 批次非原子 + 退出码歧义
  M6 权限 0644→0600 / M7 无 fsync / M9 行尾归一 / M10 doc_count 只改首处
  M11 断链 wikilink / M12 孤儿静默 / M13 sentinel 结构异常 / M14 .bak 二次覆盖
"""

from __future__ import annotations

import importlib.util
import os
import re
import stat
import sys
from pathlib import Path

import pytest

VAULT_SCRIPTS = Path(__file__).resolve().parents[3] / "canvas-vault" / ".claude" / "scripts"

#: BEGIN 注释块的收尾行末尾 (它也是 `-->` 结尾, 同样能被追加尾巴)
_SENTINEL_NOTE_TAIL = "Cmd+Shift+D 派生） -->"


def _load_module():
    sys.path.insert(0, str(VAULT_SCRIPTS))  # decay_beta 是它的同目录依赖
    spec = importlib.util.spec_from_file_location("sync_board_concepts", VAULT_SCRIPTS / "sync_board_concepts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sbc = _load_module()


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    (v / "原白板").mkdir(parents=True)
    (v / "节点").mkdir()
    return v


BOARD_TMPL = """---
type: whiteboard
doc_count: {doc_count}
---

# 板

## Concepts

{concepts}

## 其他段

正文不该被动。
"""


def _board(vault: Path, name: str = "板", concepts: str = "", doc_count: int = 0) -> Path:
    p = vault / "原白板" / f"{name}.md"
    p.write_text(BOARD_TMPL.format(concepts=concepts, doc_count=doc_count), encoding="utf-8")
    return p


def _node(vault: Path, name: str, *fm_lines: str, body: str = "真实正文。") -> Path:
    p = vault / "节点" / f"{name}.md"
    p.write_text("---\n" + "\n".join(fm_lines) + "\n---\n" + body + "\n", encoding="utf-8")
    return p


def _sync(vault: Path, *args: str) -> int:
    argv = sys.argv
    sys.argv = ["sync_board_concepts.py", "--vault", str(vault), *args]
    try:
        return sbc.main()
    finally:
        sys.argv = argv


# ══ H1: 段内用户手写内容绝不被删 (最严重 — 已复现的真实数据损坏) ══


def test_h1_user_handwritten_content_survives_sync(vault, capsys):
    """审查 H1 的完整触发链: 用户手写备忘 + plugin 在段尾追加裸 wikilink。

    包络实现下备忘正好夹在 sentinel 与游离行之间 → 被静默删除、无告警无备份。
    """
    _node(vault, "甲", 'source_board: "[[原白板/板]]"', "mastery_score: 0.3")
    _board(vault, concepts="- [[节点/甲]] — seed note")
    _sync(vault, "--board", "板")  # 先迁移出 sentinel

    text = (vault / "原白板" / "板.md").read_text(encoding="utf-8")
    handwritten = "> [!note]+ 我自己的分组备忘\n> 上面两个是行政类，下周把 asymptotics 补进来。"
    fence = "```text\n我贴的一段例子\n```"
    # ⛔ 复刻真实链路: 用户手写在 sentinel **块外**(END 之后, 块内属托管区);
    # 随后 plugin 的 appendBoardLines 在**整段边界前**追加裸行 —— 于是手写内容
    # 正好夹在 sentinel 与游离概念行之间, 包络实现会把它连坐删掉。
    text = text.replace(
        "\n## 其他段",
        "\n" + handwritten + "\n\n" + fence + "\n\n- [[节点/甲]] — extracted, weak (0.30)\n\n## 其他段",
    )
    (vault / "原白板" / "板.md").write_text(text, encoding="utf-8")

    _sync(vault, "--board", "板")
    after = (vault / "原白板" / "板.md").read_text(encoding="utf-8")

    assert "我自己的分组备忘" in after, "⛔ 用户手写 callout 被吞"
    assert "下周把 asymptotics 补进来" in after
    assert "我贴的一段例子" in after, "⛔ 用户 fenced code block 被吞"
    assert after.count("```") % 2 == 0, "⛔ 只剩孤儿栅栏, 全文渲染会错乱"
    assert after.count("- [[节点/甲]]") == 1, "游离概念行应被逐行收编, 不重复"


@pytest.mark.parametrize("where", ["end_sentinel", "begin_note_line"])
def test_h1b_text_appended_to_sentinel_line_survives(vault, where):
    """⛔ 2026-08-11 UAT 首次真实使用即踩中的同族漏网 (真实数据丢失)。

    Obsidian Live Preview 里 sentinel 渲染成可见文本, 用户想「在它下面写」
    很容易落到**行尾** ⇒ `_END_RE` 前缀匹配把整行(连同用户文字)判成 sentinel
    ⇒ 下次同步静默删除。修法是拆行保留, 不是拒绝这种写法。
    """
    _node(vault, "甲", 'source_board: "[[原白板/板]]"')
    p = _board(vault)
    _sync(vault, "--board", "板")

    text = p.read_text(encoding="utf-8")
    note = "我的备注：先补 asymptotics"
    if where == "end_sentinel":
        text = re.sub(r"(<!-- /AUTO-GENERATED[^\n]*-->)", r"\1" + note, text, count=1)
    else:  # BEGIN 注释块的收尾行 (`… 派生） -->`) 同样是 `-->` 结尾
        text = text.replace(_SENTINEL_NOTE_TAIL, _SENTINEL_NOTE_TAIL + note, 1)
    p.write_text(text, encoding="utf-8")

    _sync(vault, "--board", "板")
    after = p.read_text(encoding="utf-8")
    assert note in after, f"⛔ 追加在 {where} 行尾的用户文字被删除"
    assert _sync(vault, "--check") == 0, "拆行后必须收敛 (第二遍幂等)"
    assert note in p.read_text(encoding="utf-8"), "⛔ 第二遍同步又把它吃了"


def test_h1_horizontal_rule_and_prose_outside_block_survive(vault):
    """段外 `---` 水平线与散文原样保留 (真 vault 特征值板就长这样)。"""
    _node(vault, "甲", 'source_board: "[[原白板/板]]"')
    p = _board(vault, concepts="- [[节点/甲]] — seed\n\n---\n\n> [!info]+ 我手写的分栏说明\n> 这段绝不能删")
    _sync(vault, "--board", "板")
    after = p.read_text(encoding="utf-8")
    assert "\n---\n" in after and "我手写的分栏说明" in after and "这段绝不能删" in after


# ══ H2: 缺 `## Concepts` 段必须红 ══


def test_h2_missing_concepts_section_is_not_silently_green(vault, capsys):
    _node(vault, "甲", 'source_board: "[[原白板/板]]"')
    (vault / "原白板" / "板.md").write_text(
        "---\ntype: whiteboard\ndoc_count: 77\n---\n\n# 板\n\n没有目录段。\n", "utf-8"
    )
    rc = _sync(vault, "--check")
    out = capsys.readouterr().out
    assert rc == 2, "⛔ 缺目录段必须非零退出 (skill 降级判据按退出码走)"
    assert "已同步" not in out, "⛔ stdout 不得在没同步时说已同步"
    assert "无 `## Concepts` 段" in out


# ══ H3: frontmatter 自由文本不得被写进白板 ══


@pytest.mark.parametrize(
    ("fm_lines", "leak"),
    [
        (
            ["relationships:", "  - type: extends", "    target: 我一直搞不懂为什么特征值要用行列式，考试也总错"],
            "我一直搞不懂",
        ),
        (["derived-from: 老师说我这块基础差，要重学第三章"], "老师说我这块基础差"),
        (
            [
                "relationships:",
                "  - type: extends",
                "    description: 我不懂 target: 到底指什么，老师批评我这块",
                '    target: "[[节点/真源]]"',
            ],
            "老师批评我这块",
        ),
    ],
)
def test_h3_frontmatter_freetext_never_reaches_board(vault, fm_lines, leak):
    """派生来源只认真正的 wikilink; `target:` 正则必须锚在 key 位置。

    白板正是 start-exam-board 读的那张面 —— 泄漏直通信息隔离铁律。
    """
    _node(vault, "泄漏源", 'source_board: "[[原白板/板]]"', *fm_lines)
    p = _board(vault)
    _sync(vault, "--board", "板")
    after = p.read_text(encoding="utf-8")
    assert leak not in after, f"⛔ frontmatter 自由文本泄漏进白板: {leak}"
    assert "- [[节点/泄漏源]]" in after


def test_h3_real_wikilink_target_still_shown(vault):
    """正向对照: 合法 wikilink 的派生来源必须照常显示 (别一刀切成「派生」)。"""
    _node(
        vault,
        "派生甲",
        'source_board: "[[原白板/板]]"',
        "relationships:",
        "  - type: extends",
        '    target: "[[节点/种子]]"',
    )
    p = _board(vault)
    _sync(vault, "--board", "板")
    assert "派生自 种子" in p.read_text(encoding="utf-8")


# ══ H4: 与后端 _normalize_mastery 口径一致 ══


@pytest.mark.parametrize(
    ("fm_lines", "expect"),
    [
        (["mastery_a: 0", "mastery_b: 2", "mastery_level: 0.8"], "掌握度 —"),  # 非正 → 后端判损坏
        (["mastery_score: 0.75  # 手动校准"], "掌握度 0.75"),  # 行内注释必须剥
        (["mastery_score: 0.75", "mastery_score: 0.20"], "掌握度 0.20"),  # 重复 key 取最后
    ],
)
def test_h4_mastery_matches_backend_semantics(vault, fm_lines, expect):
    from app.services.board_manifest_service import _normalize_mastery

    _node(vault, "甲", 'source_board: "[[原白板/板]]"', *fm_lines)
    p = _board(vault)
    _sync(vault, "--board", "板")
    assert expect in p.read_text(encoding="utf-8")

    # 与后端逐值对照 (后端走真 YAML)
    import frontmatter as _fm

    fm = dict(_fm.load(str(vault / "节点" / "甲.md")).metadata or {})
    mastery, _ = _normalize_mastery(fm)
    backend = "掌握度 —" if mastery["score"] is None else f"掌握度 {mastery['score']:.2f}"
    assert backend == expect, f"两把锁口径分歧: 脚本={expect} 后端={backend}"


@pytest.mark.parametrize("rel_block", [["relationships: []"], ["relationships:"]])
def test_h4_empty_relationships_is_seed_not_derived(vault, rel_block):
    """`relationships: []` / null 在后端是 falsy → seed; 脚本判存在会说成 derived。"""
    _node(vault, "甲", 'source_board: "[[原白板/板]]"', *rel_block)
    p = _board(vault)
    _sync(vault, "--board", "板")
    assert "— 种子" in p.read_text(encoding="utf-8")


# ══ M6/M7/M9/M10/M14: 文件级不变量 ══


def test_m6_file_mode_preserved(vault):
    _node(vault, "甲", 'source_board: "[[原白板/板]]"')
    p = _board(vault)
    os.chmod(p, 0o644)
    _sync(vault, "--board", "板")
    assert stat.S_IMODE(p.stat().st_mode) == 0o644, "⛔ 同步不得静默改文件权限"


def test_m9_crlf_line_endings_preserved(vault):
    _node(vault, "甲", 'source_board: "[[原白板/板]]"')
    p = _board(vault)
    p.write_bytes(p.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    _sync(vault, "--board", "板")
    raw = p.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b""), "⛔ 行尾被归一"


def test_m10_duplicate_doc_count_all_replaced(vault):
    _node(vault, "甲", 'source_board: "[[原白板/板]]"')
    p = vault / "原白板" / "板.md"
    p.write_text(
        "---\ntype: whiteboard\ndoc_count: 1\nx: 1\ndoc_count: 99\n---\n\n## Concepts\n\n## 尾\n",
        encoding="utf-8",
    )
    _sync(vault, "--board", "板")
    assert "doc_count: 99" not in p.read_text(encoding="utf-8"), "⛔ 重复 key 时后端读最后一个"


def test_m14_backup_not_overwritten_on_second_run(vault):
    _node(vault, "甲", 'source_board: "[[原白板/板]]"')
    p = _board(vault, concepts="- [[节点/甲]] — 原始内容标记")
    _sync(vault, "--board", "板", "--backup")
    bak = p.with_suffix(".md.bak")
    assert "原始内容标记" in bak.read_text(encoding="utf-8")
    _node(vault, "乙", 'source_board: "[[原白板/板]]"')  # 制造第二次变更
    _sync(vault, "--board", "板", "--backup")
    assert "原始内容标记" in bak.read_text(encoding="utf-8"), "⛔ .bak 被二次覆盖, 真原件永久丢失"


# ══ M11/M12/M13: 结构性告警必须让 --check 红 ══


def test_m12_orphan_node_warned_and_check_red(vault, capsys):
    _node(vault, "孤儿", "type: concept")  # 无 source_board
    _board(vault)
    rc = _sync(vault, "--check")
    out = capsys.readouterr().out
    assert "孤儿节点" in out and rc == 1, "⛔ 孤儿节点静默剔除会让 doc_count 悄悄少算"


def test_m11_hostile_node_name_warned(vault, capsys):
    _node(vault, "对比A|B", 'source_board: "[[原白板/板]]"')
    _board(vault)
    rc = _sync(vault, "--check")
    out = capsys.readouterr().out
    assert "wikilink 敏感字符" in out and rc == 1, "⛔ 断链 wikilink 打脸方案 B 的立项理由"


def test_m13_broken_sentinel_structure_warned(vault, capsys):
    _node(vault, "甲", 'source_board: "[[原白板/板]]"')
    p = _board(vault)
    _sync(vault, "--board", "板")
    text = p.read_text(encoding="utf-8")
    p.write_text(text.replace("## 其他段", "<!-- /AUTO-GENERATED n=0 · synced 旧 -->\n\n## 其他段"), "utf-8")
    rc = _sync(vault, "--check")
    assert "结构异常" in capsys.readouterr().out and rc == 1


# ══ 幂等 + 与后端第二把锁双绿 ══


def test_idempotent_and_dual_lock_green(vault):
    from app.services.board_manifest_service import build_manifest

    (vault / "检验白板").mkdir()
    _node(vault, "种子", 'source_board: "[[原白板/板]]"', "mastery_score: 0.3")
    _node(vault, "派生", 'source_board: "[[原白板/板]]"', 'derived-from: "[[节点/种子]]"')
    _board(vault, doc_count=99)
    assert _sync(vault, "--all") == 0
    assert _sync(vault, "--check") == 0, "第二遍必须幂等"

    m = build_manifest(vault, board_id="板")
    assert m["dual_source_gap"] == {"concepts_only": [], "frontmatter_only": []}
    assert m["board"]["doc_count_declared"] == m["board"]["member_count_actual"] == 2
