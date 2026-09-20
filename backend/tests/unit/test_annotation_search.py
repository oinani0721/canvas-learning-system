"""CARD-G1-1 — `scripts/annotation_search.py` 真数据行为门。

DD-03：不 mock 文件系统、不 monkeypatch 目标目录。tmp fixture 用 `tmp_path` 搭**真**
目录真文件；真数据用例直接读仓内真 `_bmad-output/` 与真 A01。

只读是本脚本的核心性质，所以 `test_readonly_*` 两条在跑前跑后各算一次树摘要并逐字比，
摘要排除本卡自己的落档目录 `审查/evidence-g11/` 与 `__pycache__`（否则裁判落档会让
「前后逐字同」假红——这是判据自伤，不是脚本写了文件）。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import annotation_search as mod  # noqa: E402

REAL_BMAD = REPO_ROOT / "_bmad-output"
REAL_A01 = REAL_BMAD / "审查" / "phase0a-annotation-truth" / "A01-source-boundary-draft.json"

ANCHOR_PLAN = "_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md"
ANCHOR_PLAN_LINE = 494
ANCHOR_CARD = "_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md"
ANCHOR_CARD_LINE = 163
# H1 整改（ZCode r2）真数据锚：中文容器头 + 空行 + 引用用户原话的布局。
ANCHOR_ZH = "_bmad-output/审查/2026-08-02-规模化结构检索-审查请求-给ChatGPT.md"
ANCHOR_ZH_LINE = 23
# H1R（ZCode r3）真数据锚：未括注定位符形态 `**用户批注 L128**:`。
ANCHOR_ZH_LOC = "_bmad-output/implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md"
ANCHOR_ZH_LOC_LINE = 174

# 与真 A01 同 root_id / privacy_ceiling 的最小副本（8 root）。fixture 自带，
# 这样「私人 root 从 A01 算出来」这件事在 fixture 上也是真的被算出来的。
MINIMAL_A01 = {
    "schema_version": "2.0-draft-test-copy",
    "source_roots": [
        {
            "root_id": "ROOT-REPO-CURRENT",
            "privacy_ceiling": "P2-personal",
            "proposed_action": "include-current-repo-after-ownership-classification",
        },
        {
            "root_id": "ROOT-GIT-REFS",
            "privacy_ceiling": "P2-personal",
            "proposed_action": "include-history-deduplicated-against-live-planes",
        },
        {
            "root_id": "ROOT-ANCHORED-PRD",
            "privacy_ceiling": "P1-project-internal",
            "proposed_action": "include-private-locator-public-commitment",
        },
        {
            "root_id": "ROOT-ACTIVE-VAULT",
            "privacy_ceiling": "P3-high-sensitive",
            "proposed_action": "private-layer-only-after-authorization",
        },
        {
            "root_id": "ROOT-EXTERNAL-PRIVATE-01",
            "privacy_ceiling": "P4-secret",
            "proposed_action": "private-layer-only-per-item-redaction-or-waiver",
        },
        {
            "root_id": "ROOT-TRANSCRIPTS",
            "privacy_ceiling": "P3-high-sensitive",
            "proposed_action": "pending-user-export-and-authorization",
        },
        {
            "root_id": "ROOT-GRAPHITI-MEMORY",
            "privacy_ceiling": "P3-high-sensitive",
            "proposed_action": "discovery-hint-only",
        },
        {
            "root_id": "ROOT-OTHER-BACKUPS",
            "privacy_ceiling": "P4-secret",
            "proposed_action": "pending-root-enumeration-and-authorization",
        },
    ],
}


def write_a01(base: Path, payload=None) -> Path:
    path = base / "a01.json"
    path.write_text(json.dumps(payload if payload is not None else MINIMAL_A01, ensure_ascii=False), encoding="utf-8")
    return path


def tree_digest(root: Path, skip_parts=()) -> str:
    """逐文件 sha256(相对路径 + 内容) 再总 sha —— 对内容与文件集合都敏感。"""
    digest = hashlib.sha256()
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            parts = rel.split(os.sep)
            if any(part in parts for part in skip_parts):
                continue
            rows.append((rel, full))
    for rel, full in sorted(rows):
        digest.update(rel.encode("utf-8", "surrogateescape"))
        with open(full, "rb") as handle:
            digest.update(hashlib.sha256(handle.read()).digest())
    return digest.hexdigest()


@pytest.fixture()
def six_forms(tmp_path: Path):
    """六形态各一份：单行粗体 / User2 换行续写 / ASCII 冒号 / blockquote callout /
    行内 callout / 空槽。每份单独一个文件，行号可精确断言。"""
    base = tmp_path / "tree"
    base.mkdir()
    (base / "f1-single.md").write_text("# 标题\n\n**User：单行粗体批注 kw-alpha**\n", encoding="utf-8")
    (base / "f2-user2.md").write_text(
        "前言\n\n**User2：**\n续写正文第一行 kw-alpha\n续写正文第二行\n\n尾巴\n", encoding="utf-8"
    )
    (base / "f3-ascii.md").write_text("抬头\n**User: ASCII 冒号批注 kw-alpha**\n", encoding="utf-8")
    (base / "f4-blockquote.md").write_text(
        "引子\n\n> [!question]+ 这是 blockquote 提问 kw-alpha\n> 第二行正文\n\n完\n", encoding="utf-8"
    )
    (base / "f5-inline.md").write_text("段落开头 [!error]+ 行内告警 kw-alpha 收尾\n", encoding="utf-8")
    (base / "f6-empty.md").write_text("模板\n\n**User：**\n\n下一段\n", encoding="utf-8")
    return base, write_a01(tmp_path)


def run_cli(argv, capsys):
    code = mod.main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# --------------------------------------------------------------------------
# (g)① 六形态 + 空槽
# --------------------------------------------------------------------------
def test_six_forms_hit_first_five_with_exact_lines(six_forms, capsys):
    base, a01 = six_forms
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-alpha", "--json"], capsys)
    assert code == 0, err
    records = json.loads(out)
    got = {(os.path.basename(r["path"]), r["line"]): r["marker"] for r in records}
    assert got == {
        ("f1-single.md", 3): "**User：",
        ("f2-user2.md", 3): "**User2：",
        ("f3-ascii.md", 2): "**User:",
        ("f4-blockquote.md", 3): "[!question]+",
        ("f5-inline.md", 1): "[!error]+",
    }
    assert len(set(got.values())) == 5, "五个形态的 marker 名必须各异"
    assert "f6-empty.md" not in out, "空槽默认不列"
    assert "empty=1" in err


def test_empty_slot_listed_only_with_include_empty(six_forms, capsys):
    base, a01 = six_forms
    code, out, err = run_cli(
        ["--root", str(base), "--a01", str(a01), "--keyword", "User", "--include-empty", "--json"], capsys
    )
    assert code == 0, err
    records = json.loads(out)
    empties = [r for r in records if r["empty"]]
    assert [os.path.basename(r["path"]) for r in empties] == ["f6-empty.md"]
    assert empties[0]["line"] == 3
    assert "empty=1" in err


def test_user2_continuation_is_captured_in_excerpt(six_forms, capsys):
    base, a01 = six_forms
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "续写正文第二行", "--json"], capsys)
    assert code == 0
    records = json.loads(out)
    assert len(records) == 1
    assert records[0]["excerpt"].split("\n") == ["**User2：**", "续写正文第一行 kw-alpha", "续写正文第二行"]


# --------------------------------------------------------------------------
# (g)①′ 中文容器头（H1 整改，ZCode r2 HIGH-1；评审样例 = 本 fixture 的 f7）
# --------------------------------------------------------------------------
@pytest.fixture()
def zh_container(tmp_path: Path):
    """中文粗体容器头四形态 + 三个负控输入。

    真数据对应：审查/2026-08-02-…:23（空行 + 引用）、验收单/Story-2.1-…:429
    （冒号在粗体外）、research/round-23-…:13（限定词「触发」）、
    implementation-artifacts/epic-1/1-8-…:174（未括注定位符，r3 HIGH-1R 补）。
    """
    base = tmp_path / "zh"
    base.mkdir()
    # 评审样例形态：冒号在粗体内，正文在**空行之后**的 blockquote 里
    (base / "f7-zh-inside.md").write_text(
        "**用户批注原文（这是本轮要回答的靶心）：**\n\n> 「我这里引用的真正原因 kw-zh」\n\n尾巴\n",
        encoding="utf-8",
    )
    # 冒号在粗体外（真数据 :429 形态，紧邻续行）
    (base / "f8-zh-outside.md").write_text(
        '> **用户批注（步骤 1，line 125）**：\n> "你这里给我的快捷键我无法使用 kw-zh"\n', encoding="utf-8"
    )
    # 限定词「触发」（真数据 round-23:13 形态）
    (base / "f9-zh-suffix.md").write_text('> **用户原话触发**:\n> "你这里返回笔记的精确片段 kw-zh"\n', encoding="utf-8")
    # 定位符形态（真数据 epic-1/1-8:174 形态——r3 HIGH-1R 补漏）
    (base / "f13-zh-locator.md").write_text(
        "3. **用户批注 L128**: 确认 Claudian 应自动检测 vault 变化 kw-zh\n", encoding="utf-8"
    )
    # 负控①：Claude 自述语（关键词与冒号之间夹长正文）不得命中
    (base / "f10-claude-label.md").write_text(
        "**用户原话 3 个 callout 名字对应 Canvas 真实机制**: 这是 Claude 自己的话 kw-zh\n", encoding="utf-8"
    )
    # 负控②：无冒号的 topic 描述不得命中
    (base / "f11-topic.md").write_text(
        "核心决策：**用户批注（Obsidian callout）是否应该直接写入 Graphiti 作为燃料**，kw-zh\n", encoding="utf-8"
    )
    # 负控③：裸中文形态（无粗体）属 T3 转述面，不得命中
    (base / "f12-naked.md").write_text("采纳用户原话：Claude 转述了用户的话 kw-zh\n", encoding="utf-8")
    return base, write_a01(tmp_path)


def test_zh_container_heads_hit_with_exact_lines(zh_container, capsys):
    base, a01 = zh_container
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-zh", "--json"], capsys)
    assert code == 0, err
    got = {(os.path.basename(r["path"]), r["line"]): r["marker"] for r in json.loads(out)}
    assert got == {
        ("f7-zh-inside.md", 1): "**用户批注原文（这是本轮要回答的靶心）：",
        ("f8-zh-outside.md", 1): "**用户批注（步骤 1，line 125）**：",
        ("f9-zh-suffix.md", 1): "**用户原话触发**:",
        ("f13-zh-locator.md", 1): "**用户批注 L128**:",
    }
    assert len(set(got.values())) == 4, "四个形态的 marker 文本必须各异"


def test_zh_container_blank_line_then_quote_is_not_empty(zh_container, capsys):
    """评审样例的真数据布局：标签行与引用之间隔一个空行 —— 必须仍可召回。

    修复前该布局被判空槽、默认不列（08-02:23 即此形态——marker 修好了却「看不见」）。
    """
    base, a01 = zh_container
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-zh", "--json"], capsys)
    assert code == 0, err
    assert "empty=0" in err
    record = [r for r in json.loads(out) if os.path.basename(r["path"]) == "f7-zh-inside.md"][0]
    assert record["empty"] is False
    assert record["excerpt"].split("\n") == [
        "**用户批注原文（这是本轮要回答的靶心）：**",
        "> 「我这里引用的真正原因 kw-zh」",
    ]


def test_zh_precision_controls_do_not_fire(zh_container, capsys):
    """负控三个：Claude 自述语 / 无冒号 topic / 裸中文转述 均不得出现。"""
    base, a01 = zh_container
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-zh", "--json"], capsys)
    assert code == 0
    names = {os.path.basename(r["path"]) for r in json.loads(out)}
    assert names == {"f7-zh-inside.md", "f8-zh-outside.md", "f9-zh-suffix.md", "f13-zh-locator.md"}


# --------------------------------------------------------------------------
# (g)② --story
# --------------------------------------------------------------------------
@pytest.fixture()
def story_tree(tmp_path: Path):
    base = tmp_path / "stories"
    base.mkdir()
    (base / "CARD-G1-1-in-path.md").write_text("**User：路径里带卡号的批注**\n", encoding="utf-8")
    (base / "in-body.md").write_text("**User：正文里写了 CARD-G1-1 的批注**\n", encoding="utf-8")
    (base / "neither.md").write_text("**User：既不在路径也不在正文**\n", encoding="utf-8")
    return base, write_a01(tmp_path)


def test_story_matches_path_or_body_only(story_tree, capsys):
    base, a01 = story_tree
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--story", "CARD-G1-1", "--json"], capsys)
    assert code == 0
    names = sorted(os.path.basename(r["path"]) for r in json.loads(out))
    assert names == ["CARD-G1-1-in-path.md", "in-body.md"]


def test_story_ids_backfilled(story_tree, capsys):
    """`story_ids` 是**词元抽取**，与 `--story` 的**子串包含**不是同一口径。

    路径 `CARD-G1-1-in-path.md` 抽出的词元就是 `CARD-G1-1-in-path`（卡号后缀本来就
    可以任意长，`CARD-PYRIGHT-TAIL-BEHAVIOR` 即是），不是 `CARD-G1-1`；两者共有的
    短形态 `G1-1` 才是两边都抽得到的。断言写实测值，不写「应该抽成什么」。
    """
    base, a01 = story_tree
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--story", "CARD-G1-1", "--json"], capsys)
    assert code == 0
    by_name = {os.path.basename(r["path"]): r["story_ids"] for r in json.loads(out)}
    assert by_name["CARD-G1-1-in-path.md"] == ["CARD-G1-1-in-path", "G1-1"]
    assert by_name["in-body.md"] == ["CARD-G1-1", "G1-1"]


def test_story_substring_match_can_overreach_longer_ids(story_tree, capsys):
    """如实 pin 子串包含的代价：`--story CARD-G1-1` 会连 `CARD-G1-1-in-path` 一起命中。

    这是为了让 `--story G1-1` 能找回 `CARD-G1-1` 而**选**的口径（卡文 §二.8 就同时传
    `--story CARD-G1-1 --story G1-1`），不是漏判。
    """
    base, a01 = story_tree
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--story", "G1-1", "--json"], capsys)
    assert code == 0
    names = sorted(os.path.basename(r["path"]) for r in json.loads(out))
    assert names == ["CARD-G1-1-in-path.md", "in-body.md"]


def test_story_matching_is_case_sensitive(story_tree, capsys):
    base, a01 = story_tree
    code, _, _ = run_cli(["--root", str(base), "--a01", str(a01), "--story", "card-g1-1", "--json"], capsys)
    assert code == 1


# --------------------------------------------------------------------------
# (g)③ 私人 root
# --------------------------------------------------------------------------
@pytest.fixture()
def vault_tree(tmp_path: Path):
    base = tmp_path / "repo"
    (base / "canvas-vault").mkdir(parents=True)
    (base / "canvas-vault" / "x.md").write_text("**User：私人 vault 里的批注 kw-private**\n", encoding="utf-8")
    (base / "public.md").write_text("**User：公开面的批注 kw-public**\n", encoding="utf-8")
    return base, write_a01(tmp_path)


def test_private_root_excluded_by_default(vault_tree, capsys):
    base, a01 = vault_tree
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-private", "--json"], capsys)
    # 命中数断言放在最前：负控①（私人 root 判定恒 False）要红在「返回了本不该返回的
    # 批注」上，而不是先被一条 rc 断言拦下——rc 只是后果，泄漏才是缺陷本身。
    assert json.loads(out) == [], "私人 root 的批注默认必须一条都不返回"
    assert "excluded_private_roots=['ROOT-ACTIVE-VAULT'" in err
    assert "canvas-vault" in err  # pruned_private_paths 显式汇总，不静默
    assert code == 1


def test_public_sibling_still_found(vault_tree, capsys):
    base, a01 = vault_tree
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-public", "--json"], capsys)
    assert code == 0
    assert len(json.loads(out)) == 1


def test_include_private_opens_the_vault(vault_tree, capsys):
    base, a01 = vault_tree
    code, out, err = run_cli(
        ["--root", str(base), "--a01", str(a01), "--keyword", "kw-private", "--include-private", "--json"], capsys
    )
    assert code == 0
    records = json.loads(out)
    assert len(records) == 1
    assert os.path.basename(records[0]["path"]) == "x.md"
    assert "excluded_private_roots=[]" in err


def test_root_pointing_into_private_root_is_refused(vault_tree, capsys):
    base, a01 = vault_tree
    code, _, err = run_cli(["--root", str(base / "canvas-vault"), "--a01", str(a01), "--keyword", "kw-private"], capsys)
    assert code == 2
    assert "ROOT-ACTIVE-VAULT" in err


def test_symlink_into_private_root_is_refused(vault_tree, capsys):
    base, a01 = vault_tree
    link = base.parent / "sneaky-link"
    os.symlink(base / "canvas-vault", link)
    code, _, err = run_cli(["--root", str(link), "--a01", str(a01), "--keyword", "kw-private"], capsys)
    assert code == 2, "realpath 口径：软链指进私人 root 同样拒扫"
    assert "ROOT-ACTIVE-VAULT" in err


@pytest.mark.parametrize("dirname", ["Canvas-Vault", "CANVAS-VAULT", "canvas-Vault"])
def test_case_variant_private_dir_is_pruned(dirname, tmp_path: Path, capsys):
    """大小写变体的 canvas-vault 同样不得泄漏。

    2026-09-19 实测：`os.path.realpath` 不归一大小写，而本机 macOS APFS 大小写不敏感
    ⇒ 未 casefold 前 `Canvas-Vault/` 下的批注被原样返回。这条是那次泄漏的回归门。
    """
    base = tmp_path / "repo"
    (base / dirname).mkdir(parents=True)
    (base / dirname / "x.md").write_text("**User：大小写变体私人内容 kw-ci**\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-ci", "--json"], capsys)
    assert json.loads(out) == [], f"{dirname} 下的私人批注不得返回"
    assert "ROOT-ACTIVE-VAULT" in err
    assert code == 1


def test_case_variant_root_is_refused(tmp_path: Path, capsys):
    base = tmp_path / "repo"
    (base / "Canvas-Vault").mkdir(parents=True)
    (base / "Canvas-Vault" / "x.md").write_text("**User：kw-ci**\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, _, err = run_cli(["--root", str(base / "Canvas-Vault"), "--a01", str(a01), "--keyword", "kw-ci"], capsys)
    assert code == 2
    assert "ROOT-ACTIVE-VAULT" in err


def test_blockquote_annotation_does_not_swallow_next_speaker(tmp_path: Path, capsys):
    """引用块批注区里，User 块不得吃到下一位发言人。

    真数据形态（研究/ 下 2 处实测）：`> **User：**` / `>` / `> **Claude（日期）：** …`。
    引用块里的「空行」是一个光秃秃的 `>`，str.strip() 判不出来。
    """
    base = tmp_path / "bq"
    base.mkdir()
    (base / "a.md").write_text(
        "> **User：**\n> 我的原话 kw-mine\n>\n> **Claude（2026-09-19）：** 回复 kw-claude\n",
        encoding="utf-8",
    )
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-mine", "--json"], capsys)
    assert code == 0
    records = json.loads(out)
    assert len(records) == 1
    assert "kw-claude" not in records[0]["excerpt"], "Claude 的回复不是「用户说过的话」"
    assert records[0]["excerpt"].split("\n") == ["> **User：**", "> 我的原话 kw-mine"]


def test_html_comment_hits_are_labelled_not_dropped(tmp_path: Path, capsys):
    """HTML 注释里的 marker 照常召回但带 in_html_comment 标注（契约 :134/:139）。

    真数据 26 行 / 6 文件落在注释区内，样例是被注释掉的填写模板。
    """
    base = tmp_path / "html"
    base.mkdir()
    (base / "a.md").write_text(
        "正文\n\n<!--\n> [!error]+ 注释掉的模板 kw-html\n-->\n\n**User：注释外的 kw-html**\n",
        encoding="utf-8",
    )
    a01 = write_a01(tmp_path)
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-html", "--json"], capsys)
    assert code == 0
    by_line = {r["line"]: r["in_html_comment"] for r in json.loads(out)}
    assert by_line == {4: True, 7: False}
    assert "html_comment=1" in err


def test_unknown_privacy_ceiling_is_treated_as_private(tmp_path: Path, capsys):
    """认不出的 privacy_ceiling 按私人处理（fail-closed），并在 stderr 说出来。"""
    payload = {"source_roots": [dict(r) for r in MINIMAL_A01["source_roots"]]}
    for entry in payload["source_roots"]:
        if entry["root_id"] == "ROOT-REPO-CURRENT":
            entry["privacy_ceiling"] = "P5-brand-new-level"
    a01 = write_a01(tmp_path, payload)
    private, _ = mod.load_private_root_ids(str(a01))
    assert "ROOT-REPO-CURRENT" in private


def test_privacy_ceiling_case_and_whitespace_are_normalized(tmp_path: Path):
    """`  p3-HIGH-sensitive ` 这种写法仍须判成私人，不能因大小写/空白漏判。"""
    payload = {"source_roots": [dict(r) for r in MINIMAL_A01["source_roots"]]}
    for entry in payload["source_roots"]:
        if entry["root_id"] == "ROOT-ACTIVE-VAULT":
            entry["privacy_ceiling"] = "  P3-HIGH-Sensitive "
    a01 = write_a01(tmp_path, payload)
    private, _ = mod.load_private_root_ids(str(a01))
    assert "ROOT-ACTIVE-VAULT" in private


def test_summary_separates_enforced_roots_from_unmapped_ones(capsys):
    """汇总行只把**真有路径可拦**的 root 报成已排除；其余另起一行如实说明。

    A01 算出 6 个私人 root，仓内只有 ROOT-ACTIVE-VAULT / ROOT-ANCHORED-PRD 有落地路径。
    把另外 4 个（含两个 P4-secret）一并写进 excluded_ 会读成「它们也被拦住了」。
    """
    code, _, err = run_cli(["--keyword", "codex", "--a01", str(REAL_A01)], capsys)
    assert code == 0
    assert "excluded_private_roots=['ROOT-ACTIVE-VAULT', 'ROOT-ANCHORED-PRD']" in err
    assert "private_roots_without_path=" in err
    for unmapped in ("ROOT-TRANSCRIPTS", "ROOT-GRAPHITI-MEMORY", "ROOT-OTHER-BACKUPS", "ROOT-EXTERNAL-PRIVATE-01"):
        assert unmapped in err


def test_unwalkable_directory_is_reported_not_silently_dropped(tmp_path: Path, capsys):
    """列不出来的目录进 unwalkable 桶并报数，不静默缩小分母（契约 :142 口径）。"""
    base = tmp_path / "walk"
    (base / "ok").mkdir(parents=True)
    (base / "ok" / "a.md").write_text("**User：可读的 kw-walk**\n", encoding="utf-8")
    locked = base / "locked"
    locked.mkdir()
    (locked / "b.md").write_text("**User：读不到的 kw-walk**\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    os.chmod(locked, 0o000)
    try:
        code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-walk", "--json"], capsys)
    finally:
        os.chmod(locked, 0o755)
    assert code == 0
    assert len(json.loads(out)) == 1
    assert "unwalkable=1" in err
    assert "unwalkable_dirs=" in err


def test_git_env_is_scrubbed_of_git_variables():
    """给 git 子进程的环境必须剃掉全部 GIT_*。

    GIT_DIR 会让它回答另一个仓库；GIT_TRACE* 会让它自己往文件里写——后者正好绕过
    零写 AST 门（门看得见 Python 源码的写调用，看不见子进程）。
    """
    env = mod.git_env()
    leaked = [k for k in env if k.startswith("GIT_") and k not in {"GIT_TERMINAL_PROMPT", "GIT_OPTIONAL_LOCKS"}]
    assert leaked == [], f"未剃掉的 GIT_* 变量：{leaked}"
    assert env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["GIT_TERMINAL_PROMPT"] == "0"


def test_private_lookup_keys_are_prefolded():
    """两张查找表的键必须已经是 fold_path 形态，否则大小写变体会静默漏判。"""
    for key in list(mod.PRIVATE_COMPONENT_ROOTS) + list(mod.PRIVATE_BASENAME_ROOTS):
        assert key == mod.fold_path(key), f"查找表键 {key!r} 未按 fold_path 归一"


def test_nested_private_dir_is_pruned(tmp_path: Path, capsys):
    """前缀比较够不到的位置（<root>/sub/canvas-vault/）由组件形态安全网兜住。"""
    base = tmp_path / "repo"
    (base / "sub" / "canvas-vault").mkdir(parents=True)
    (base / "sub" / "canvas-vault" / "deep.md").write_text("**User：深层私人批注 kw-deep**\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-deep", "--json"], capsys)
    assert code == 1
    assert json.loads(out) == []
    assert "ROOT-ACTIVE-VAULT" in err


# --------------------------------------------------------------------------
# (g)④ A01 fail-closed
# --------------------------------------------------------------------------
def test_a01_missing_is_fail_closed(tmp_path: Path, capsys):
    base = tmp_path / "t"
    base.mkdir()
    (base / "a.md").write_text("**User：随便 kw**\n", encoding="utf-8")
    code, _, err = run_cli(["--root", str(base), "--a01", str(tmp_path / "nope.json"), "--keyword", "kw"], capsys)
    assert code == 2
    assert "A01" in err


def test_a01_without_source_roots_is_fail_closed(tmp_path: Path, capsys):
    base = tmp_path / "t"
    base.mkdir()
    (base / "a.md").write_text("**User：随便 kw**\n", encoding="utf-8")
    a01 = write_a01(tmp_path, {"schema_version": "x"})
    code, _, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw"], capsys)
    assert code == 2
    assert "source_roots" in err


def test_a01_entry_missing_privacy_ceiling_is_fail_closed(tmp_path: Path, capsys):
    base = tmp_path / "t"
    base.mkdir()
    (base / "a.md").write_text("**User：随便 kw**\n", encoding="utf-8")
    broken = {"source_roots": [{"root_id": "ROOT-ACTIVE-VAULT"}]}
    a01 = write_a01(tmp_path, broken)
    code, _, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw"], capsys)
    assert code == 2
    assert "privacy_ceiling" in err


# --------------------------------------------------------------------------
# (g)⑤ 真数据锚
# --------------------------------------------------------------------------
def test_real_anchor_plan_line_494(capsys):
    code, out, _ = run_cli(["--keyword", "codex", "--a01", str(REAL_A01), "--json"], capsys)
    assert code == 0
    hits = [r for r in json.loads(out) if r["path"] == ANCHOR_PLAN and r["line"] == ANCHOR_PLAN_LINE]
    assert len(hits) == 1, f"计划书:{ANCHOR_PLAN_LINE} 必命中"
    record = hits[0]
    assert record["category"] == "审查"
    assert record["date"] == "2026-08-20"
    assert record["date_source"] == "filename"
    assert record["marker"].startswith("**User")


def test_real_anchor_card_line_163(capsys):
    code, out, _ = run_cli(["--keyword", "anki", "--a01", str(REAL_A01), "--json"], capsys)
    assert code == 0
    hits = [r for r in json.loads(out) if r["path"] == ANCHOR_CARD and r["line"] == ANCHOR_CARD_LINE]
    assert len(hits) == 1, f"08-25 卡文:{ANCHOR_CARD_LINE} 必命中"
    assert hits[0]["category"] == "goal-cards"
    assert hits[0]["date"] == "2026-08-25"


def test_real_anchor_zh_container_line_23(capsys):
    """H1 整改真数据锚：zcode r2 点名的关键文件（除该容器头外整文件零 marker）。"""
    code, out, _ = run_cli(["--keyword", "靶心", "--a01", str(REAL_A01), "--json"], capsys)
    assert code == 0
    hits = [r for r in json.loads(out) if r["path"] == ANCHOR_ZH and r["line"] == ANCHOR_ZH_LINE]
    assert len(hits) == 1, f"08-02 请求书:{ANCHOR_ZH_LINE} 必命中（H1 修复点）"
    assert hits[0]["marker"].startswith("**用户批注原文（")
    assert hits[0]["category"] == "审查"
    assert hits[0]["date"] == "2026-08-02"
    assert hits[0]["date_source"] == "filename"
    assert "真正担心的问题" in hits[0]["excerpt"], "空行后的引用必须进摘录（否则仍读作空批注）"


def test_real_anchor_zh_locator_line_174(capsys):
    """H1R 真数据锚：未括注定位符 `**用户批注 L128**:`（zcode r3 HIGH-1R 修复点）。"""
    code, out, _ = run_cli(["--keyword", "L128", "--a01", str(REAL_A01), "--json"], capsys)
    assert code == 0
    hits = [r for r in json.loads(out) if r["path"] == ANCHOR_ZH_LOC and r["line"] == ANCHOR_ZH_LOC_LINE]
    assert len(hits) == 1, f"epic-1/1-8:{ANCHOR_ZH_LOC_LINE} 必命中（H1R 修复点）"
    assert hits[0]["marker"] == "**用户批注 L128**:"


@pytest.mark.parametrize("keyword", ["FSRS", "跨vault", "README"])
def test_real_themes_are_non_empty(keyword, capsys):
    code, out, _ = run_cli(["--keyword", keyword, "--a01", str(REAL_A01), "--json"], capsys)
    assert code == 0
    assert len(json.loads(out)) >= 1, f"主题 {keyword} 在真 _bmad-output 上应至少 1 块"


def test_real_run_excludes_private_roots_and_reports_unreadable(capsys):
    code, _, err = run_cli(["--keyword", "codex", "--a01", str(REAL_A01), "--json"], capsys)
    assert code == 0
    assert "excluded_private_roots=['ROOT-ACTIVE-VAULT'" in err
    assert "unreadable=" in err


# --------------------------------------------------------------------------
# (g)⑥ 只读
# --------------------------------------------------------------------------
def test_readonly_on_fixture_tree(six_forms, capsys):
    base, a01 = six_forms
    before = tree_digest(base)
    run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-alpha"], capsys)
    assert tree_digest(base) == before


def test_readonly_on_real_bmad_output(capsys):
    skip = ("evidence-g11",)
    before = tree_digest(REAL_BMAD, skip_parts=skip)
    run_cli(["--keyword", "codex", "--story", "CARD-G1-1", "--a01", str(REAL_A01)], capsys)
    assert tree_digest(REAL_BMAD, skip_parts=skip) == before


# --------------------------------------------------------------------------
# (g)⑦ 确定性
# --------------------------------------------------------------------------
def test_json_output_is_byte_identical_across_runs(six_forms, capsys):
    base, a01 = six_forms
    argv = ["--root", str(base), "--a01", str(a01), "--keyword", "kw-alpha", "--json"]
    _, first, _ = run_cli(argv, capsys)
    _, second, _ = run_cli(argv, capsys)
    assert first == second


# --------------------------------------------------------------------------
# (g)⑧ 不可读桶
# --------------------------------------------------------------------------
def test_unreadable_files_counted_not_silently_zero(tmp_path: Path, capsys):
    base = tmp_path / "bad"
    base.mkdir()
    (base / "ok.md").write_text("**User：正常批注 kw-ok**\n", encoding="utf-8")
    (base / "nul.md").write_bytes(b"**User: has NUL kw-ok**\n\x00tail\n")
    (base / "latin.md").write_bytes(b"**User: bad utf8 kw-ok \xff\xfe**\n")
    a01 = write_a01(tmp_path)
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-ok", "--json"], capsys)
    assert code == 0
    assert "unreadable=2" in err
    names = [os.path.basename(r["path"]) for r in json.loads(out)]
    assert names == ["ok.md"]


# --------------------------------------------------------------------------
# (g)⑨ 日期优先级
# --------------------------------------------------------------------------
def test_date_source_priority(tmp_path: Path, capsys):
    base = tmp_path / "dates"
    base.mkdir()
    (base / "2026-01-02-both.md").write_text(
        "---\ndate: 2025-12-31\n---\n\n**User：两者都有 kw-date**\n", encoding="utf-8"
    )
    (base / "2026-03-04-only-name.md").write_text("**User：只有文件名 kw-date**\n", encoding="utf-8")
    (base / "plain.md").write_text("**User：都没有 kw-date**\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-date", "--json"], capsys)
    assert code == 0
    by_name = {os.path.basename(r["path"]): (r["date"], r["date_source"]) for r in json.loads(out)}
    assert by_name["2026-01-02-both.md"] == ("2025-12-31", "frontmatter")
    assert by_name["2026-03-04-only-name.md"] == ("2026-03-04", "filename")
    assert by_name["plain.md"] == ("unknown", "unknown")


# --------------------------------------------------------------------------
# (g)⑩ 退出码 + 其余 CLI
# --------------------------------------------------------------------------
def test_date_source_git_on_a_real_git_repo(tmp_path: Path, capsys):
    """git 档必须有自己的门——它是真数据上占比最大的一档（实测 92/251 ≈ 37%）。

    DD-03：不 mock `git_commit_date`，而是在 tmp_path 里 `git init` 建一个**真**仓库并
    真提交一次。文件名不带日期、正文无 frontmatter ⇒ 日期只能落到 git 这一档。
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    md = repo / "plain-name.md"
    md.write_text("**User：只有 git 能给出日期 kw-git**\n", encoding="utf-8")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"]
    subprocess.run([*git, "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run([*git, "add", "plain-name.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [*git, "commit", "-q", "-m", "seed", "--date=2021-03-04T00:00:00"],
        cwd=repo,
        check=True,
        capture_output=True,
        env={**os.environ, "GIT_COMMITTER_DATE": "2021-03-04T00:00:00"},
    )
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(repo), "--a01", str(a01), "--keyword", "kw-git", "--json"], capsys)
    assert code == 0
    records = json.loads(out)
    assert len(records) == 1
    assert records[0]["date_source"] == "git", "该文件只有 git 一档能给出日期"
    assert records[0]["date"] == "2021-03-04"


def test_unclosed_frontmatter_is_not_frontmatter(tmp_path: Path, capsys):
    """首行 `---` 若没有收尾，就是正文分隔线——不得把正文里的 date: 当成 frontmatter。

    2026-09-19 实测的回归：无下界扫描会把**围栏代码块里**的 `date: 1999-01-01`
    报成 `date_source=frontmatter`，即一个看起来权威的错日期。
    """
    base = tmp_path / "fm"
    base.mkdir()
    (base / "2026-05-06-thematic-break.md").write_text(
        "---\n# 标题\n\n```yaml\ndate: 1999-01-01\n```\n\n**User：这条是 2026 年写的 kw-fm**\n",
        encoding="utf-8",
    )
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-fm", "--json"], capsys)
    assert code == 0
    record = json.loads(out)[0]
    assert record["date_source"] == "filename"
    assert record["date"] == "2026-05-06"


@pytest.mark.parametrize(
    "filename,expected_date,expected_source",
    [
        ("ticket-1234-56-7890.md", None, None),  # 月 56 日 78 —— 不是日期，不得抠出来
        ("2026-02-30-impossible.md", None, None),  # 形状合法但日历上不存在
        ("2026-02-28-real.md", "2026-02-28", "filename"),  # 控制组：真日期必须认出来
    ],
)
def test_filename_date_must_be_a_real_calendar_date(filename, expected_date, expected_source, tmp_path, capsys):
    """报一个假日期比报 unknown 更坏：假值会被当事实引用，还会挡掉 git 那一档。"""
    base = tmp_path / "dates2"
    base.mkdir()
    (base / filename).write_text("**User：正文 kw-cal**\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-cal", "--json"], capsys)
    assert code == 0
    record = json.loads(out)[0]
    if expected_date is None:
        assert record["date_source"] != "filename", f"{filename} 不该被当成带日期的文件名"
    else:
        assert (record["date"], record["date_source"]) == (expected_date, expected_source)


def test_zero_hits_exits_1(six_forms, capsys):
    base, a01 = six_forms
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "绝不存在的词-zzz", "--json"], capsys)
    assert code == 1
    assert json.loads(out) == []


def test_no_keyword_and_no_story_exits_2(capsys):
    code, _, err = run_cli(["--root", str(REAL_BMAD)], capsys)
    assert code == 2
    assert "--keyword" in err


def test_category_filter(capsys):
    code, out, _ = run_cli(["--keyword", "anki", "--a01", str(REAL_A01), "--category", "goal-cards", "--json"], capsys)
    assert code == 0
    assert {r["category"] for r in json.loads(out)} == {"goal-cards"}


def test_context_limit_caps_continuation_lines(six_forms, capsys):
    base, a01 = six_forms
    code, out, _ = run_cli(
        ["--root", str(base), "--a01", str(a01), "--keyword", "kw-alpha", "--context", "1", "--json"], capsys
    )
    assert code == 0
    for record in json.loads(out):
        assert len(record["excerpt"].split("\n")) <= 2


def test_context_zero_does_not_turn_continuation_into_empty_slot(tmp_path: Path, capsys):
    """--context 改的是显示行数，不该改「这条批注是不是空槽」这个事实。

    2026-09-19 实测的回归：早先把「扫描续行的上限」和「显示上限」写成同一个数，
    --context 0 会让所有换行续写的批注 empty=1、默认不列——参数悄悄改了语义。
    """
    base = tmp_path / "ctx"
    base.mkdir()
    (base / "a.md").write_text("**User2：**\n续写正文 kw-ctx\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    for context in ("0", "1", "5"):
        code, out, err = run_cli(
            ["--root", str(base), "--a01", str(a01), "--keyword", "User2", "--context", context, "--json"],
            capsys,
        )
        assert "empty=0" in err, f"--context {context} 不得把有续行的批注判成空槽"
        assert code == 0
        assert len(json.loads(out)) == 1


def test_fenced_code_hits_are_labelled_not_dropped(tmp_path: Path, capsys):
    """围栏代码块里的 marker 照常召回，但必须带 in_fenced_code 标注并计入汇总。

    契约 §4.2 要求「用状态机识别 fenced code」——识别不等于排除。本仓实测 12.7%
    的 marker 行在围栏内，其中有真批注被引用进代码块，排除会丢真阳性。
    """
    base = tmp_path / "fence"
    base.mkdir()
    (base / "a.md").write_text(
        "正文\n\n```\n**User：围栏里的 kw-fence**\n```\n\n**User：围栏外的 kw-fence**\n",
        encoding="utf-8",
    )
    a01 = write_a01(tmp_path)
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-fence", "--json"], capsys)
    assert code == 0
    by_line = {r["line"]: r["in_fenced_code"] for r in json.loads(out)}
    assert by_line == {4: True, 7: False}
    assert "fenced=1" in err


def test_fence_marker_line_itself_is_not_a_hit(tmp_path: Path, capsys):
    """围栏起止行本身不参与 marker 匹配（对照输入：把 marker 写在围栏行上）。"""
    base = tmp_path / "fenceline"
    base.mkdir()
    (base / "a.md").write_text("```**User：不该命中 kw-fl**\n```\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-fl", "--json"], capsys)
    assert json.loads(out) == []
    assert code == 1


# --------------------------------------------------------------------------
# 门的变异存活面补洞（内部对抗复核 gates 维度实测：下列变异体原本全部「存活」，
# 即改坏它们之后本文件仍全绿。存活清单见 evidence-g11/gate-mutation-survey-*.txt）
# --------------------------------------------------------------------------
def test_git_env_is_actually_wired_into_the_subprocess(tmp_path: Path, monkeypatch, capsys):
    """证明 git_env() **接上了**，不只是存在。

    变异体 K_git_env_unwired（把 git_env 从 subprocess.run 上摘掉）原本存活——
    因为旧门只单测了这个函数的返回值，没有任何一条测试走过「它有没有被用上」。
    这里在调用方环境里塞一个坏掉的 GIT_DIR：若它漏进子进程，git 会去那个不存在的
    仓库找、返回非 0 ⇒ date_source 退成 unknown；接上了才仍是 git。
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "plain.md").write_text("**User：只有 git 能定日期 kw-wire**\n", encoding="utf-8")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"]
    subprocess.run([*git, "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run([*git, "add", "plain.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [*git, "commit", "-q", "-m", "seed", "--date=2019-07-08T00:00:00"],
        cwd=repo,
        check=True,
        capture_output=True,
        env={**os.environ, "GIT_COMMITTER_DATE": "2019-07-08T00:00:00"},
    )
    a01 = write_a01(tmp_path)

    # 对照组：环境干净时必须是 git 档（证明这条路径本来走得通）
    code, out, _ = run_cli(["--root", str(repo), "--a01", str(a01), "--keyword", "kw-wire", "--json"], capsys)
    assert code == 0
    assert json.loads(out)[0]["date_source"] == "git"

    # 负控输入：塞一个坏 GIT_DIR。接线成立 ⇒ 结果不变。
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "definitely-not-a-repo.git"))
    code, out, _ = run_cli(["--root", str(repo), "--a01", str(a01), "--keyword", "kw-wire", "--json"], capsys)
    assert code == 0
    record = json.loads(out)[0]
    assert record["date_source"] == "git", "调用方的 GIT_DIR 漏进了子进程 ⇒ git_env 没接上"
    assert record["date"] == "2019-07-08"


def test_tool_writes_nothing_anywhere_in_the_repo(capsys):
    """只读的量面必须覆盖**整个仓库**，不只是 `_bmad-output`。

    变异体 F_writes_outside（让脚本往目标目录之外写）原本存活：旧的只读门只对
    `_bmad-output` 与 fixture 树算摘要，仓里别处新增的文件一个都看不见。
    这里用 `git status --porcelain -uall` 覆盖全仓（排除本卡自己的落档目录）。
    """
    scope = ["--porcelain", "-uall", "--", ".", ":(exclude)_bmad-output/审查/evidence-g11"]

    def repo_status():
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=false", "status", *scope],
            cwd=REPO_ROOT,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        return proc.stdout

    before = repo_status()
    run_cli(["--keyword", "codex", "--story", "CARD-G1-1", "--a01", str(REAL_A01)], capsys)
    assert repo_status() == before, "运行前后全仓 git status 必须逐字同"


def test_prefix_rule_alone_catches_a_private_root_without_component_name(tmp_path: Path, capsys):
    """给前缀比较层一个**只有它能抓**的输入。

    变异体 A_no_prefix（摘掉前缀比较层）原本存活——因为所有私人面用例走的都是
    `canvas-vault` 这个目录名，组件名安全网把前缀层的覆盖面整个吃掉了
    （「加一道更强的门会吃掉旧门的测试面」）。ROOT-ANCHORED-PRD 的 `.gdr/_external`
    既不含 canvas-vault 组件、basename 也不是 PRD 文件名，只有前缀规则拦得住。
    """
    base = tmp_path / "repo"
    (base / ".gdr" / "_external").mkdir(parents=True)
    (base / ".gdr" / "_external" / "notes.md").write_text("**User：外部私人 kw-gdr**\n", encoding="utf-8")
    (base / "pub.md").write_text("**User：公开 kw-gdr**\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-gdr", "--json"], capsys)
    assert code == 0
    names = [os.path.basename(r["path"]) for r in json.loads(out)]
    assert names == ["pub.md"], ".gdr/_external 下的内容只能由前缀规则拦住"
    assert "ROOT-ANCHORED-PRD" in err


@pytest.mark.parametrize(
    "rel,expected",
    [
        ("验收单/批注回复/x.md", "批注回复"),
        ("研究/2026-08-27-批注回复-C2.md", "批注回复"),
        ("验收单/UAT-x.md", "验收单批注区"),
        ("审查/x.md", "审查"),
        ("研究/x.md", "研究"),
        ("implementation-artifacts/goal-cards/x.md", "goal-cards"),
        ("planning-artifacts/x.md", "planning-artifacts"),
        ("决策批注/x.md", "决策批注"),
        ("research/x.md", "其他"),
        ("review/x.md", "其他"),
        ("Session 3/x.md", "其他"),
    ],
)
def test_classify_covers_all_eight_buckets(rel, expected):
    """八类映射逐桶钉住（含 research/ 与 review/ 落「其他」这两条卡文 §〇 的规范口径）。

    变异体 D_thin_classify / D2_thin_classify_all（把 classify 削成只返回一类）原本
    全部存活——这张表此前一条断言都没有。
    """
    assert mod.classify(rel) == expected


def test_multiple_markers_on_one_line_all_reported(tmp_path: Path, capsys):
    """同一行上的多个 marker 必须逐个成条。

    变异体 E_first_marker_only（每行只取第一个 marker）原本存活。
    """
    base = tmp_path / "multi"
    base.mkdir()
    (base / "a.md").write_text("**User：正文 [!error]+ 同一行第二个 marker kw-multi**\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-multi", "--json"], capsys)
    assert code == 0
    records = json.loads(out)
    assert [r["marker"] for r in records] == ["**User：", "[!error]+"]
    assert {r["line"] for r in records} == {1}


def test_context_zero_shows_only_the_marker_line(tmp_path: Path, capsys):
    """`--context 0` 的摘录必须恰好 1 行。

    变异体 H_no_display_slice（去掉 `collected[:context]`）原本存活：旧用例用
    `--context 1`，而扫描下限也是 1，两者恰好等价 ⇒ 那一刀切不切都一样。
    """
    base = tmp_path / "ctx0"
    base.mkdir()
    (base / "a.md").write_text("**User2：**\n续写一 kw-c0\n续写二\n", encoding="utf-8")
    a01 = write_a01(tmp_path)
    code, out, err = run_cli(
        ["--root", str(base), "--a01", str(a01), "--keyword", "User2", "--context", "0", "--json"], capsys
    )
    assert code == 0
    assert json.loads(out)[0]["excerpt"].split("\n") == ["**User2：**"]
    assert "empty=0" in err, "--context 0 只改显示，不该把有续行的批注判成空槽"


def test_output_is_deterministic_across_separate_processes(six_forms):
    """确定性必须跨**进程**证，而且 stdout / stderr 都要比。

    两处教训都写在这里：
    * 变异体 G_nondet_stderr（汇总行掺进程号）原本存活，因为旧用例只比 stdout；
    * 补完 stderr 之后它**仍然**存活——旧用例在同一个进程里调两次 main()，
      `os.getpid()` 当然相同。同进程比两次证明不了跨进程确定性，
      PYTHONHASHSEED 决定的 set 迭代序、pid、启动时刻都从这个缝里漏过去。
    所以这里起两个真子进程，并刻意给它们**不同的 PYTHONHASHSEED**。
    """
    base, a01 = six_forms
    argv = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "annotation_search.py"),
        "--root",
        str(base),
        "--a01",
        str(a01),
        "--keyword",
        "kw-alpha",
        "--json",
    ]

    def run(seed):
        return subprocess.run(
            argv,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    first, second = run("0"), run("12345")
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr, "汇总行在两个进程之间必须逐字同"


def test_marker_table_shape():
    assert len(mod.MARKERS) == 11
    callouts = sorted(k[len(mod.CALLOUT_PREFIX) :] for k in mod.MARKERS if k.startswith(mod.CALLOUT_PREFIX))
    assert callouts == ["BMAD-ANNO", "error", "hint", "info", "note", "question", "tip", "todo", "warning"]
    assert "user_bold_zh" in mod.MARKERS


@pytest.mark.parametrize(
    "line,expected",
    [
        ("**User**：契约 :131 的拆开粗体形态", "**User**："),
        ("> [!todo]+ 📝 批注区（直接写 **User：**）", "[!todo]+"),
        ("> [!NOTE] Obsidian 的 callout 类型大小写不敏感", "[!NOTE]"),
        ("> [!WARNING] 同上", "[!WARNING]"),
        ("**User 修正：改口", "**User 修正："),
        ("**User Comment: english variant", "**User Comment:"),
        ("**用户批注原文（这是本轮要回答的靶心）：**", "**用户批注原文（这是本轮要回答的靶心）："),
        ("> **用户批注（步骤 1，line 125）**：", "**用户批注（步骤 1，line 125）**："),
        ("**用户原话触发**:", "**用户原话触发**:"),
        ("3. **用户批注 L128**: 确认 Claudian 应自动检测 vault 变化", "**用户批注 L128**:"),
    ],
)
def test_contract_t1_t2_variants_are_matched(line, expected):
    """契约 :131/:134 点名、且真数据里确实出现过的形态，逐条钉住。

    实测支撑：`**User**：` 1 处、`[!todo]+` 10 处、大写 callout 3 处（2026-09-19 于本树）；
    中文容器头 4 处真容器头（审查/2026-08-02-…:23、验收单/Story-2.1-…:429、
    research/round-23-…:13、implementation-artifacts/epic-1/1-8-…:174——r2/r3 两轮整改补测）。
    """
    hits = mod.find_markers(line)
    assert hits, f"{line!r} 应当命中"
    assert hits[0][1] == expected


def test_inline_bold_in_continuation_does_not_truncate_block(tmp_path: Path, capsys):
    """续行里的行内加粗是成对的，不该把批注块提前截断。

    旧规则「见到 ** 就停」会在第一条含行内加粗的续行处收尾，使同一条批注的剩余
    正文变成检索不到的面。
    """
    base = tmp_path / "pairs"
    base.mkdir()
    (base / "a.md").write_text(
        "**User：开头正文\n中间有**行内加粗**的一行\n结尾关键词 kw-tail**\n\n后面段落\n",
        encoding="utf-8",
    )
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-tail", "--json"], capsys)
    assert code == 0, "结尾在第三行的关键词必须仍在检索面内"
    records = json.loads(out)
    assert len(records) == 1
    assert records[0]["excerpt"].split("\n")[-1] == "结尾关键词 kw-tail**"


def test_closed_bold_annotation_does_not_swallow_following_reply(tmp_path: Path, capsys):
    """`**User：…**` 自闭合后紧跟的 Claude 回复不得被算进这条批注的摘录。"""
    base = tmp_path / "reply"
    base.mkdir()
    (base / "a.md").write_text(
        "**User：我的原话 kw-mine**\n> [!note]+ Claude 回复：这不是用户说的 kw-claude\n",
        encoding="utf-8",
    )
    a01 = write_a01(tmp_path)
    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-mine", "--json"], capsys)
    assert code == 0
    records = json.loads(out)
    assert len(records) == 1
    assert records[0]["excerpt"] == "**User：我的原话 kw-mine**"
    assert "kw-claude" not in records[0]["excerpt"]


def test_private_root_ids_are_derived_from_a01_not_hardcoded(tmp_path: Path):
    """把 A01 里 ROOT-ACTIVE-VAULT 降成 P2 ⇒ 它就不再是私人 root。"""
    payload = {"source_roots": [dict(r) for r in MINIMAL_A01["source_roots"]]}
    for entry in payload["source_roots"]:
        if entry["root_id"] == "ROOT-ACTIVE-VAULT":
            entry["privacy_ceiling"] = "P2-personal"
            entry["proposed_action"] = "include-current-repo"
    a01 = write_a01(tmp_path, payload)
    private, declared = mod.load_private_root_ids(str(a01))
    assert "ROOT-ACTIVE-VAULT" not in private
    assert len(declared) == 8
    real_private, real_declared = mod.load_private_root_ids(str(REAL_A01))
    assert "ROOT-ACTIVE-VAULT" in real_private
    assert "ROOT-ANCHORED-PRD" in real_private  # private-locator 口径
    assert len(real_private) == 6
    assert len(real_declared) == 8
