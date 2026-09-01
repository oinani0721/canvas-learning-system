"""G5-6 — clear-inbox 只读盘点提名 preview 裁判 (BATCH-2026-08-31-第七批 / CARD-G5-6)。

被测物: canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
(scripts-only 只读引擎, 无 SKILL.md, 不触 EXPECTED_SKILLS)。

裁判覆盖 (卡片 (d) 钦定):
  A. R8 六判据正反例 —— C1 source URL / C2 AI 自述 / C3 空骨架 /
     C4 精确重复给正本路径 / C5 R{n} 归轮次 / C6 拿不准兜底, 每条正反各一
  B. 「拿不准」0 硬猜 —— 近似重复(difflib)恒不产出建议删; 兜底条目恒无去向;
     引擎不可达的去向词恒不出现
  C. 零写快照 —— tmp fixture 全树 sha256+mtime_ns+mode 前后全等 (out-dir 在树外)
  D. 确定性二跑 —— JSON 与 MD 逐字节相等
  E. 拒绝路径零产物 —— 非法标签 / 超 255B / 显式 inbox 不存在 / 坏 --now /
     batch-size 越界 / out-dir 祖先含 symlink, 一律 exit≠0 且 out-dir 无产物
  F. 分批与台账 —— ≤10 最旧优先 + deferred 清单 + Sleeping 台账 + 30 天标记
  G. 稳定 ID —— inb1- 前缀、路径决定、内容/mtime 无关、与 split anchor 不同空间

fixtures 全部在 tmp_path 程序化构造 (mtime 与 NFD 文件名进 git 会被平台搅浑),
构造逻辑即 fixture 定义。⛔ 本目录禁建 conftest.py, 故一切工具函数就地定义。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS = REPO_ROOT / "canvas-vault" / ".claude" / "skills"
SCRIPT = SKILLS / "clear-inbox" / "scripts" / "inbox_preview.py"
SPLIT_SCRIPT = SKILLS / "board-split" / "scripts" / "split_preview.py"

NOW_ISO = "2026-08-31T00:00:00+08:00"
NOW_DT = datetime.fromisoformat(NOW_ISO)

#: 判据编号 —— 卡片钦定次序, 落盘键与本元组逐字相同
CRITERIA = (
    "C1_source_url",
    "C2_ai_self_declared",
    "C3_empty_or_skeleton",
    "C4_exact_duplicate",
    "C5_round_filename",
    "C6_undecided",
)


# ───────────────────────── 工具 ─────────────────────────


def _exec_no_bytecode(spec, mod):
    """⛔ 裁判自己也不许往 vault 里落 `__pycache__` —— 否则「零写侧」的证据链
    是被测程序干净、而验证它的测试在旁边写文件。"""
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev


def load_module():
    if not SCRIPT.exists():
        pytest.fail(f"被测脚本不存在: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("inbox_preview", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    _exec_no_bytecode(spec, mod)
    return mod


def load_split_module():
    if not SPLIT_SCRIPT.exists():
        pytest.fail(f"复用来源脚本不存在: {SPLIT_SCRIPT}")
    spec = importlib.util.spec_from_file_location("split_preview_ref", SPLIT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    _exec_no_bytecode(spec, mod)
    return mod


def run_cli(vault: Path, out_dir: Path, *extra: str, now: str = NOW_ISO):
    # ⛔ 防「脚本不存在 → returncode≠0 → 拒绝类断言假绿」
    if not SCRIPT.exists():
        pytest.fail(f"被测脚本不存在: {SCRIPT}")
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--vault",
            str(vault),
            "--out-dir",
            str(out_dir),
            "--now",
            now,
            *extra,
        ],
        capture_output=True,
        text=True,
    )


def products(out_dir: Path, label: str = "_待处理") -> tuple[Path, Path]:
    return (
        out_dir / f"inbox-preview-{label}.json",
        out_dir / f"inbox-preview-{label}.md",
    )


def load_json(out_dir: Path, label: str = "_待处理") -> dict:
    return json.loads(products(out_dir, label)[0].read_text(encoding="utf-8"))


def no_products(out_dir: Path) -> bool:
    """拒绝路径必须零产物。⛔ 判据是「目录不存在, 或存在但**完全为空**」——
    原先只查 `inbox-preview-*`, 那样实现即便留下空目录、`.tmp` 半成品或换个名字的
    产物, 断言照样为真（Codex MEDIUM: 断言证明不了它声称证明的事）。"""
    if not out_dir.exists():
        return True
    return not any(out_dir.iterdir())


def snapshot(root: Path) -> dict:
    """全树取证: 每个条目 (sha256 | "dir") + st_mtime_ns + st_mode。
    ⛔ 只对**不含产物**的树使用 —— 产物落在树内会让本快照自证其罪式失效。"""
    out: dict[str, tuple] = {}
    for p in sorted(root.rglob("*")):
        st = p.lstat()
        if p.is_symlink():
            digest = "symlink:" + os.readlink(p)
        elif p.is_dir():
            digest = "dir"
        else:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
        out[str(p.relative_to(root))] = (digest, st.st_mtime_ns, st.st_mode)
    return out


def days_ago(n: float) -> float:
    return (NOW_DT - timedelta(days=n)).timestamp()


def mk(path: Path, text: str, age_days: float = 1.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    ts = days_ago(age_days)
    os.utime(path, (ts, ts))
    return path


def base_vault(tmp_path: Path) -> tuple[Path, Path]:
    """最小合法 vault + 空收件箱; 返回 (vault, out_dir)。out_dir 恒在 vault 树外。"""
    vault = tmp_path / "vault"
    (vault / "原白板").mkdir(parents=True)
    (vault / "节点").mkdir(parents=True)
    (vault / "_待处理").mkdir(parents=True)
    return vault, tmp_path / "out"


def item_by_name(data: dict, name: str) -> dict:
    for it in data["items"]:
        if it["name"] == name:
            return it
    raise AssertionError(f"提名清单里没有 {name!r}; 实有 {[i['name'] for i in data['items']]}")


# ───────────────────────── A. 六判据正反例 ─────────────────────────


def test_c1_source_url_positive_and_negative(tmp_path):
    """C1: frontmatter source 为 http(s) URL → 一手快照·留原地; 非 URL 不得命中。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(
        inbox / "剪藏-学费页.md",
        "---\nsource: https://deanza.edu/tuition\n---\n\n学费明细正文若干字, 足以过正文门。\n第二行正文。\n",
        age_days=5,
    )
    # 反例: source 不是 URL → 不得判一手
    mk(
        inbox / "非URL来源.md",
        "---\nsource: 我自己整理的\n---\n\n一些正文内容, 长度足够。\n第二行。\n",
        age_days=4,
    )
    assert run_cli(vault, out).returncode == 0
    data = load_json(out)

    pos = item_by_name(data, "剪藏-学费页.md")
    assert pos["criterion"] == "C1_source_url"
    assert pos["verdict"] == "留原地"
    assert pos["nomination_type"] == "primary-record"
    assert pos["confident"] is True
    assert "https://deanza.edu/tuition" in pos["basis"]

    neg = item_by_name(data, "非URL来源.md")
    assert neg["criterion"] != "C1_source_url"
    assert neg["nomination_type"] != "primary-record"


def test_c2_ai_self_declared_positive_and_negative(tmp_path):
    """C2: 文头自述 AI 生成 → 二手综合·归档 DR 目录; 标记落在文头窗口外不得命中。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(
        inbox / "三校转学率对比.md",
        "# 三校转学率对比\n\n> 本文由 Deep Research 生成\n\n正文若干行内容。\n再一行正文。\n",
        age_days=7,
    )
    # 反例: 同一标记出现在很靠后的位置(文头窗口之外) → 不得命中 C2
    tail = "\n".join(f"第 {i} 行普通正文。" for i in range(1, 60))
    mk(inbox / "尾部提及.md", f"# 普通笔记\n\n{tail}\n\n这里才说 由 Deep Research 生成\n", age_days=6)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)

    pos = item_by_name(data, "三校转学率对比.md")
    assert pos["criterion"] == "C2_ai_self_declared"
    assert pos["verdict"] == "归档"
    assert pos["nomination_type"] == "secondary-synthesis"
    assert pos["target_hint"] == "deep research 报告/"
    assert "Deep Research" in pos["basis"]

    neg = item_by_name(data, "尾部提及.md")
    assert neg["criterion"] != "C2_ai_self_declared"


def test_c2_round_filename_wins_target_dir(tmp_path):
    """C2 命中且文件名带 R{n}_ → 去向按轮次目录 (R8: 「或按 R{n} 归轮次」)。"""
    vault, out = base_vault(tmp_path)
    mk(
        vault / "_待处理" / "R99_深度调研.md",
        "# 调研\n\n由 AI 生成\n\n正文一行。\n正文两行。\n",
        age_days=3,
    )
    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] == "C2_ai_self_declared"
    assert it["target_hint"] == "R99/"


def test_basis_line_number_survives_empty_frontmatter(tmp_path):
    """依据里的行号是给人核对用的 —— 空 frontmatter（`---` 紧接 `---`）时不得偏移。

    早先版本用 `len(fm) + 2` 反推 frontmatter 跨度, 空 frontmatter 的 fm == []
    被当成「没有 frontmatter」, 行号整体少算 2。行号偏了等于没给依据。
    """
    vault, out = base_vault(tmp_path)
    # 第 1/2 行是空 frontmatter, 第 3 行才是标记行
    mk(
        vault / "_待处理" / "空frontmatter.md",
        "---\n---\n> 本文由 Deep Research 生成\n\n正文一。\n正文二。\n",
        age_days=3,
    )
    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] == "C2_ai_self_declared"
    assert "第 3 行" in it["basis"], f"行号算错了: {it['basis']}"


def test_c3_empty_and_skeleton_positive_and_negative(tmp_path):
    """C3: 0 字节 / 剥离后无正文的骨架 → 建议删; 有正文者不得命中。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "未命名 5.md", "", age_days=9)
    mk(inbox / "空骨架.md", "---\ntitle: t\n---\n\n# 标题\n\n## 小节\n\n- \n- \n\n<!-- 注释 -->\n", age_days=8)
    mk(inbox / "有正文.md", "# 标题\n\n这里有真正的正文内容。\n还有第二行。\n", age_days=7)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)

    zero = item_by_name(data, "未命名 5.md")
    assert zero["criterion"] == "C3_empty_or_skeleton"
    assert zero["verdict"] == "建议删"
    assert "0 字节" in zero["basis"]

    skel = item_by_name(data, "空骨架.md")
    assert skel["criterion"] == "C3_empty_or_skeleton"
    assert skel["verdict"] == "建议删"

    body = item_by_name(data, "有正文.md")
    assert body["criterion"] != "C3_empty_or_skeleton"
    assert body["verdict"] != "建议删"


def test_c4_exact_duplicate_gives_canonical_path(tmp_path):
    """C4 正例: 归一化正文逐字相等 → 建议删 + 正本相对路径。
    归一化须吸收行尾空白 / 空行 / NFD-NFC 差异 (三者同时施加)。"""
    vault, out = base_vault(tmp_path)
    body = "转学政策原文第一段。\n第二段内容 café。\n"
    mk(vault / "节点" / "政策正本.md", "# 正本\n\n" + body, age_days=40)
    # 收件箱副本: 行尾空白 + 多余空行 + NFD 形态
    dup = unicodedata.normalize("NFD", "转学政策原文第一段。   \n\n\n第二段内容 café。  \n")
    mk(vault / "_待处理" / "政策粘贴-重复.md", "# 抄来的\n\n" + dup, age_days=2)

    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] == "C4_exact_duplicate"
    assert it["verdict"] == "建议删"
    assert it["exact_duplicate_of"] == "节点/政策正本.md"
    assert it["confident"] is True


def test_c4_near_duplicate_never_suggests_delete(tmp_path):
    """C4 反例(卡片核心红线): 高相似但非逐字相等 → 只标疑似·拿不准, 绝不建议删。"""
    vault, out = base_vault(tmp_path)
    lines = [f"第 {i} 行完全相同的内容。" for i in range(1, 41)]
    mk(vault / "节点" / "长文正本.md", "# 正本\n\n" + "\n".join(lines) + "\n", age_days=40)
    mutated = list(lines)
    mutated[7] = "第 8 行被我改写过, 因此不是逐字重复。"
    mk(vault / "_待处理" / "长文疑似.md", "# 疑似\n\n" + "\n".join(mutated) + "\n", age_days=2)

    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["verdict"] != "建议删"
    assert it["exact_duplicate_of"] is None
    assert it["confident"] is False
    assert it["near_duplicates"], "近似重复必须被记录并呈现给用户"
    assert it["near_duplicates"][0]["path"] == "节点/长文正本.md"
    assert 0.9 <= it["near_duplicates"][0]["ratio"] < 1.0
    assert "疑似" in (it["uncertain_reason"] or "")


def test_c4_empty_body_never_enters_dup_index(tmp_path):
    """空正文不得互为「正本」—— 否则两个空骨架会互相支撑出一条有后果的建议删。"""
    vault, out = base_vault(tmp_path)
    mk(vault / "节点" / "库内空壳.md", "---\ntitle: x\n---\n\n# 只有标题\n", age_days=40)
    mk(vault / "_待处理" / "收件箱空壳.md", "---\ntitle: y\n---\n\n# 只有标题\n", age_days=2)

    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] == "C3_empty_or_skeleton"
    assert it["exact_duplicate_of"] is None, "空正文不得进重复索引"


def test_corpus_index_excludes_empty_bodies(tmp_path):
    """索引层自己的门。⛔ 与上一条**不是重复**: 上一条走端到端(受 nominate 的
    `if body` 兜底保护, 单删索引层杀不掉它); 本条直取 scan_corpus, 单删索引层即翻红。
    每层各有一道门, 才不会出现「删掉一层没人发现」。"""
    mod = load_module()
    vault, _ = base_vault(tmp_path)
    mk(vault / "节点" / "空壳甲.md", "---\ntitle: a\n---\n\n# 只有标题\n")
    mk(vault / "节点" / "空壳乙.md", "# 另一个只有标题\n\n## 二级\n\n- \n")
    mk(vault / "节点" / "有正文.md", "真正的正文一行。\n第二行。\n")

    index, bodies, stats = mod.scan_corpus(vault, [])
    assert "" not in index, "空正文进了重复索引 —— 两个空骨架会互为「正本」"
    assert stats["skipped_empty_body"] == 2
    assert stats["files_indexed"] == 1
    assert all(b for _, b in bodies)


def test_c5_round_filename_positive_and_negative(tmp_path):
    """C5: 文件名带 R{n}_ → 归档到轮次目录; 无下划线的 R 前缀不得命中。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "R82_批注回复-某主题.md", "# 回复\n\n正文一行内容。\n正文两行内容。\n", age_days=5)
    mk(inbox / "R82无下划线.md", "# 标题\n\n正文一行内容。\n正文两行内容。\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)

    pos = item_by_name(data, "R82_批注回复-某主题.md")
    assert pos["criterion"] == "C5_round_filename"
    assert pos["verdict"] == "归档"
    assert pos["target_hint"] == "R82/"
    assert pos["confident"] is True

    neg = item_by_name(data, "R82无下划线.md")
    assert neg["criterion"] != "C5_round_filename"


def test_c6_fallback_is_explicitly_undecided(tmp_path):
    """C6 兜底: 六判据全不命中 → 拿不准 + 提问, 且**不给任何去向**。"""
    vault, out = base_vault(tmp_path)
    mk(vault / "_待处理" / "面试思路草稿.md", "# 面试思路\n\n一些我自己的分析文字。\n第二行分析。\n", age_days=3)

    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] == "C6_undecided"
    assert it["verdict"] == "拿不准"
    assert it["confident"] is False
    assert it["target_hint"] is None
    assert it["nomination_type"] is None
    assert it["ask"], "兜底必须给出「需要你一句话」的具体问题"


def test_criteria_order_is_frozen_and_earlier_wins(tmp_path):
    """次序铁律: C1 命中时即便存在逐字重复, verdict 仍归 C1 —— 但重复证据必须留痕。"""
    vault, out = base_vault(tmp_path)
    body = "同一段被剪藏过两次的正文。\n第二行。\n"
    mk(vault / "节点" / "已有正本.md", body, age_days=40)
    mk(
        vault / "_待处理" / "剪藏且重复.md",
        "---\nsource: https://example.com/a\n---\n\n" + body,
        age_days=2,
    )
    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert tuple(data["criteria_order"]) == CRITERIA

    it = data["items"][0]
    assert it["criterion"] == "C1_source_url"
    assert it["verdict"] == "留原地"
    assert it["exact_duplicate_of"] == "节点/已有正本.md", "信息零丢失: 次序不改变, 证据仍在"
    assert any(c["kind"] == "exact_duplicate_under_other_verdict" for c in it["conflicts"])


def test_duplicate_within_batch_is_flagged_not_deleted(tmp_path):
    """批内两件逐字相同: 谁是正本不可判 → 只挂冲突, 不产出建议删。"""
    vault, out = base_vault(tmp_path)
    body = "# 同稿\n\n一模一样的正文内容。\n第二行。\n"
    mk(vault / "_待处理" / "甲.md", body, age_days=3)
    mk(vault / "_待处理" / "乙.md", body, age_days=2)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert {it["name"] for it in data["items"]} == {"甲.md", "乙.md"}, (
        "件数先锁死 —— 循环门在 items 为空/缺件时恒真 = 假绿 (round-8 §三)"
    )
    for it in data["items"]:
        assert it["verdict"] != "建议删"
        assert any(c["kind"] == "duplicate_within_batch" for c in it["conflicts"])


# ── Codex 对抗审查回归门（每条对应一个实证缺陷，修复前必红） ──


def test_code_indentation_is_not_normalized_away(tmp_path):
    """⛔ BLOCKER 回归: 逐字比对**不得**抹掉代码缩进。

    `if ok:` + 缩进 `run()` 与 `if ok:` + 顶格 `run()` 是语义完全不同的两段代码;
    原实现对每行 `.strip()` 后二者归一化结果相同 → 判「逐字相等」→ **建议删**。
    有后果的提名, 依据必须逐字。
    """
    vault, out = base_vault(tmp_path)
    mk(
        vault / "节点" / "代码正本.md",
        "# 正本\n\n```python\nif ok:\n    run()\n```\n",
        age_days=40,
    )
    mk(
        vault / "_待处理" / "代码副本.md",
        "# 副本\n\n```python\nif ok:\nrun()\n```\n",
        age_days=2,
    )

    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["verdict"] != "建议删", "缩进不同的两段代码被判成逐字重复"
    assert it["exact_duplicate_of"] is None


def test_fenced_code_only_file_is_not_a_skeleton(tmp_path):
    """⛔ BLOCKER 回归: 只有一段围栏代码的文件不得被判成空骨架。

    `~~~` 曾被当成「纯结构行」删掉, 围栏内的 `# comment` 又被当成 Markdown 标题删掉,
    于是整份文件"没有正文"→ 建议删。而文件头明明声明着「代码块内容留在正文里」——
    声明与实现对不上, 就是掩饰。
    """
    vault, out = base_vault(tmp_path)
    mk(
        vault / "_待处理" / "脚本片段.md",
        # ⛔ 围栏内**只有一行 `#` 注释**——这正是 Codex 的原始 repro。
        # 早先版本这里多写了一行 `rsync -a src/ dst/`: 那行不是标题也不是结构行,
        # 于是即便围栏状态机被拆掉它也能救活断言, 变异照样存活 = 门是虚的。
        "~~~\n# keep this shell comment\n~~~\n",
        age_days=3,
    )
    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] != "C3_empty_or_skeleton"
    assert it["verdict"] != "建议删"


def test_malformed_url_is_not_a_primary_record(tmp_path):
    """⛔ HIGH 回归: `https://?` 没有 host, 不构成「一手来源」的机械证据。"""
    vault, out = base_vault(tmp_path)
    mk(
        vault / "_待处理" / "假URL.md",
        "---\nsource: https://?\n---\n\n正文一。\n正文二。\n",
        age_days=3,
    )
    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] != "C1_source_url"
    assert it["nomination_type"] != "primary-record"


def test_topic_mention_is_not_ai_self_declaration(tmp_path):
    """⛔ HIGH 回归: 「Deep Research」作为**话题**出现 ≠ 自述由 AI 生成。
    手写的产品比较笔记不该被归档进 DR 报告目录 —— 那是给不出证据还硬给去向。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(
        inbox / "话题提及.md",
        "# Deep Research 产品比较\n\n我自己用下来的心得。\n第二行。\n",
        age_days=4,
    )
    mk(
        inbox / "真自述.md",
        "# 报告\n\n> 本文由 Deep Research 生成\n\n正文。\n第二行。\n",
        age_days=3,
    )

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert item_by_name(data, "话题提及.md")["criterion"] != "C2_ai_self_declared"
    assert item_by_name(data, "真自述.md")["criterion"] == "C2_ai_self_declared"


def test_body_wrapped_in_dashes_is_not_frontmatter(tmp_path):
    """⛔ HIGH 回归: `---` + 正文 + `---` 不是 frontmatter。
    原实现整段吞掉 → 正文为空 → 建议删。把用户正文误判成空文件的删除提名,
    比不提名坏得多。"""
    vault, out = base_vault(tmp_path)
    mk(vault / "_待处理" / "破折号包裹.md", "---\n这是唯一正文\n---\n", age_days=3)
    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] != "C3_empty_or_skeleton"
    assert it["verdict"] != "建议删"


def test_multiple_canonical_candidates_are_declared_not_asserted(tmp_path):
    """⛔ HIGH 回归: 库内有多份同正文时, 不得把字典序第一个**断言**为正本。
    建议删仍成立（收件箱这份相对它们是多余的）, 但「哪份是正本」必须明说不可判。"""
    vault, out = base_vault(tmp_path)
    body = "同一段被存过两次的正文。\n第二行。\n"
    mk(vault / "节点" / "甲本.md", body, age_days=40)
    (vault / "归档").mkdir()
    mk(vault / "归档" / "乙本.md", body, age_days=39)
    mk(vault / "_待处理" / "第三份.md", body, age_days=2)

    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] == "C4_exact_duplicate"
    assert it["verdict"] == "建议删"
    assert len(it["exact_duplicate_others"]) == 1
    assert any(c["kind"] == "multiple_canonical_candidates" for c in it["conflicts"])
    assert "不可判" in it["basis"]


def test_within_batch_dup_does_not_block_c4_when_corpus_canonical_exists(tmp_path):
    """⛔ MEDIUM 回归: 批内还有同稿, 不影响「库内已有一份」这条独立证据。
    原实现无条件否决 C4, 两件都掉进 C6 —— 明明有依据却说没有。"""
    vault, out = base_vault(tmp_path)
    body = "库内已经存着的一段正文。\n第二行。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(vault / "_待处理" / "甲.md", body, age_days=3)
    mk(vault / "_待处理" / "乙.md", body, age_days=2)

    assert run_cli(vault, out).returncode == 0
    items = load_json(out)["items"]
    assert {it["name"] for it in items} == {"甲.md", "乙.md"}, (
        "件数先锁死 —— 循环门在 items 为空/缺件时恒真 = 假绿 (round-8 §三)"
    )
    for it in items:
        assert it["criterion"] == "C4_exact_duplicate"
        assert it["exact_duplicate_of"] == "节点/库内正本.md"
        assert any(c["kind"] == "duplicate_within_batch" for c in it["conflicts"])


def test_yaml_inline_comment_does_not_hide_source_url(tmp_path):
    """⛔ MEDIUM 回归: `source: <url> # 官方来源` 的值是 URL, 注释不算值的一部分。"""
    vault, out = base_vault(tmp_path)
    mk(
        vault / "_待处理" / "带注释来源.md",
        "---\nsource: https://example.com/page # 官方来源\n---\n\n正文一。\n正文二。\n",
        age_days=3,
    )
    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] == "C1_source_url"
    assert "https://example.com/page" in it["basis"]
    assert "官方来源" not in it["basis"]


def test_non_regular_file_is_skipped_without_reading(tmp_path):
    """⛔ MEDIUM 回归: FIFO 不得被 read_bytes —— 那会直接挂住整个进程。"""
    vault, out = base_vault(tmp_path)
    os.mkfifo(vault / "_待处理" / "管道.md")
    mk(vault / "_待处理" / "正常.md", "# t\n\n正文一。\n正文二。\n", age_days=2)

    r = run_cli(vault, out)
    assert r.returncode == 0, "读到 FIFO 挂住了"
    data = load_json(out)
    assert [i["name"] for i in data["items"]] == ["正常.md"]
    assert any(x["name"] == "管道.md" for x in data["inventory"]["skipped"])


def test_criteria_order_c4_does_not_outrank_c2_c5(tmp_path):
    """⛔ MEDIUM 回归: 次序覆盖不能只有 C1+C4 一对。
    这里构造 C2/C5 与 C4 的冲突 —— 把实现里的 C4 上移到任一条之前, 本条必红。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    ai_body = "> 本文由 Deep Research 生成\n\n共有的正文。\n第二行。\n"
    mk(vault / "节点" / "AI正本.md", ai_body, age_days=40)
    mk(inbox / "AI副本.md", ai_body, age_days=5)
    rnd_body = "轮次材料的正文。\n第二行。\n"
    mk(vault / "节点" / "轮次正本.md", rnd_body, age_days=40)
    mk(inbox / "R77_副本.md", rnd_body, age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    ai = item_by_name(data, "AI副本.md")
    assert ai["criterion"] == "C2_ai_self_declared", "C4 抢在了 C2 前面"
    assert ai["exact_duplicate_of"] == "节点/AI正本.md"
    rnd = item_by_name(data, "R77_副本.md")
    assert rnd["criterion"] == "C4_exact_duplicate", "C5 抢在了 C4 前面"


def test_near_dup_scan_counts_are_actually_exercised(tmp_path):
    """⛔ LOW 回归: 「跳过 ≠ 无重复」的计数必须真的被算出来。
    原测试只查键存在 —— 把两个计数永久写死成 0 它也照样通过。"""
    vault, out = base_vault(tmp_path)
    long_body = "\n".join(f"第 {i} 行。" for i in range(1, 60)) + "\n"
    mk(vault / "节点" / "长正本.md", long_body, age_days=40)
    mk(vault / "节点" / "短文.md", "很短。\n第二行。\n", age_days=40)
    mk(
        vault / "_待处理" / "中等.md",
        "# t\n\n" + "\n".join(f"第 {i} 行。" for i in range(1, 58)) + "\n",
        age_days=2,
    )

    assert run_cli(vault, out).returncode == 0
    scan = load_json(out)["near_dup_scan"]
    assert scan["compared_pairs"] >= 1, "长度相近的一对必须真的比过"
    assert scan["skipped_length_prefilter"] >= 1, "长度差悬殊的一对必须计入跳过"


# ───────────────────────── B. 「拿不准」0 硬猜 ─────────────────────────


def test_engine_never_emits_human_only_verdicts(tmp_path):
    """「归入白板」「新建节点」需要语义判断 —— 引擎恒不产出, 且必须显式声明该边界。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "a.md", "# A\n\n正文内容一。\n正文内容二。\n", age_days=3)
    mk(inbox / "b.md", "---\nsource: https://x.test/p\n---\n\n正文。\n正文二。\n", age_days=2)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    vocab = data["verdict_vocabulary"]
    assert set(vocab["human_only"]) == {"归入白板", "新建节点"}
    assert vocab["human_only_note"]
    reachable = set(vocab["reachable_by_engine"])
    assert {it["name"] for it in data["items"]} == {"a.md", "b.md"}, (
        "件数先锁死 —— 循环门在 items 为空/缺件时恒真 = 假绿 (round-8 §三)"
    )
    for it in data["items"]:
        assert it["verdict"] in reachable
        assert it["verdict"] not in set(vocab["human_only"])


def test_no_destructive_nomination_without_mechanical_evidence(tmp_path):
    """全局不变式: 建议删 ⟸ 只能来自 C3(空/骨架) 或 C4(精确重复且给出正本)。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    body = "库内已有的一段正文。\n第二行。\n"
    mk(vault / "节点" / "正本.md", body, age_days=40)
    mk(inbox / "空的.md", "", age_days=9)
    mk(inbox / "骨架.md", "# 只有标题\n\n## 二级\n", age_days=8)
    mk(inbox / "重复的.md", body, age_days=7)
    mk(inbox / "普通的.md", "# 普通\n\n一些内容。\n再一行。\n", age_days=6)
    lines = [f"共同第 {i} 行。" for i in range(1, 41)]
    mk(vault / "节点" / "长正本.md", "\n".join(lines) + "\n", age_days=40)
    mutated = list(lines)
    mutated[3] = "这一行被改了。"
    mk(inbox / "近似的.md", "\n".join(mutated) + "\n", age_days=5)

    assert run_cli(vault, out).returncode == 0
    items = load_json(out)["items"]
    assert items, "items 为空时本门条件循环恒真 = 假绿 (round-4 MEDIUM)"
    for it in items:
        if it["verdict"] == "建议删":
            assert it["criterion"] in ("C3_empty_or_skeleton", "C4_exact_duplicate")
            if it["criterion"] == "C4_exact_duplicate":
                assert it["exact_duplicate_of"], "建议删(重复) 必须指出正本在哪"
        if it["confident"] is False:
            assert it["verdict"] == "拿不准"


def test_near_dup_scan_distinguishes_skipped_from_clean(tmp_path):
    """「没比对」与「比对过没有」必须在产物里可区分 —— 否则跳过会伪装成无重复。"""
    vault, out = base_vault(tmp_path)
    mk(vault / "_待处理" / "x.md", "# X\n\n正文一。\n正文二。\n", age_days=2)
    assert run_cli(vault, out).returncode == 0
    scan = load_json(out)["near_dup_scan"]
    for key in ("ratio_threshold", "body_char_cap", "compared_pairs", "skipped_oversize", "skipped_length_prefilter"):
        assert key in scan, f"near_dup_scan 缺 {key}"
    assert scan["ratio_threshold"] >= 0.9


# ───────────────────────── C. 零写快照 ─────────────────────────


def test_no_bytecode_cache_written_into_vault_skills(tmp_path):
    """⛔ 零写侧的第一现场（Codex 审查实证）: importlib 加载兄弟模块默认会在
    **board-split 目录**里写 `__pycache__/*.pyc` —— 既是往 vault 落文件, 也是
    伸手进另一条车道的地盘。

    (d) tmp 隔离重构 (CARD-G5-6b): 不再 rmtree checkout 里的 `__pycache__`
    (裁判不该动被测 checkout 的任何目录项), 改为把两个脚本按**同一相对布局**
    拷进 tmp (SCRIPT 的 `_SP_PATH` 由 `__file__` 推导, 布局一致副本才能定位
    它自己的 split_preview 副本), 在副本上跑 CLI 与 importlib 加载, 断言副本树
    下零 `__pycache__`。副本 sha256 必须等于 checkout 原件 —— 否则门测的是副本
    不是被测物。CLI 子进程**显式剥掉 PYTHONDONTWRITEBYTECODE**: 裁判命令带着
    它跑时, 子进程继承该变量会让 SCRIPT 内部的 dont_write_bytecode 保护永远
    不被考验(门空转); 在副本树上剥掉它, 内部保护成为唯一防线, 删掉保护当场
    在副本树留下缓存 → 门变红。
    """
    skills_copy = tmp_path / "skills"
    for src in (SCRIPT, SPLIT_SCRIPT):
        dst = skills_copy / src.relative_to(SKILLS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        assert hashlib.sha256(dst.read_bytes()).hexdigest() == hashlib.sha256(src.read_bytes()).hexdigest(), (
            f"副本与 checkout 原件不一致: {src}"
        )
    script_copy = skills_copy / SCRIPT.relative_to(SKILLS)

    vault, out = base_vault(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    r = subprocess.run(
        [
            sys.executable,
            str(script_copy),
            "--vault",
            str(vault),
            "--out-dir",
            str(out),
            "--now",
            NOW_ISO,
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, r.stderr[-300:]

    spec = importlib.util.spec_from_file_location("inbox_preview_tmpcopy", script_copy)
    mod = importlib.util.module_from_spec(spec)
    _exec_no_bytecode(spec, mod)
    assert mod._SP_PATH == skills_copy / SPLIT_SCRIPT.relative_to(SKILLS), (
        "副本没有解析到副本树里的 split_preview —— 布局与 checkout 不一致"
    )

    caches = sorted(p.relative_to(skills_copy) for p in skills_copy.rglob("__pycache__"))
    assert not caches, f"运行/导入在副本树落下了字节码缓存: {caches}"


def test_reject_out_dir_inside_inbox(tmp_path):
    """产物落进收件箱 → 第二跑会把上一次的产物当成待处理材料, 二跑不再逐字节相等。
    这种不成立要跑两次才看得见, 所以在入口直接拒绝。"""
    vault, _ = base_vault(tmp_path)
    inside = vault / "_待处理" / "outputs"
    r = run_cli(vault, inside)
    assert r.returncode != 0
    assert no_products(inside)
    assert not inside.exists(), "拒绝路径不得在收件箱里建目录"


def test_local_timezone_is_fixed_offset_not_tzdata_dependent(tmp_path):
    """人话时区必须是固定 +08:00: ZoneInfo 会给 1986-1991 套夏令时(实测 1988-07-01
    → +09:00), 于是同一份输入在装/不装 tzdata 的两台机器上产出不同字节 ——
    「二跑逐字节相等」就只在同一台机器上成立, 那不叫确定性。"""
    mod = load_module()
    for y in (1988, 2026):
        assert mod._TZ_SHANGHAI.utcoffset(datetime(y, 7, 1)) == timedelta(hours=8)


def test_zero_write_side_full_tree_snapshot(tmp_path):
    """全树 sha256+mtime_ns+mode 前后逐项相等 (out-dir 在 vault 树外)。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(vault / "节点" / "正本.md", "库内正文。\n第二行。\n", age_days=40)
    mk(vault / "原白板" / "板.md", "# 板\n\n## Concepts\n- 正本\n", age_days=30)
    mk(inbox / "空的.md", "", age_days=9)
    mk(inbox / "剪藏.md", "---\nsource: https://a.test/x\n---\n\n正文。\n二行。\n", age_days=5)
    mk(inbox / "重复.md", "库内正文。\n第二行。\n", age_days=4)
    mk(inbox / "Sleeping" / "睡着的.md", "---\nslept_at: 2026-07-01\n---\n\n正文。\n", age_days=20)

    before = snapshot(vault)
    assert run_cli(vault, out).returncode == 0
    after = snapshot(vault)
    assert before == after, "只读引擎修改了 vault 树"
    assert products(out)[0].exists() and products(out)[1].exists()


# ───────────────────────── D. 确定性二跑 ─────────────────────────


def test_deterministic_two_runs_byte_identical(tmp_path):
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(vault / "节点" / "正本.md", "库内正文。\n第二行。\n", age_days=40)
    for i in range(1, 6):
        mk(inbox / f"件{i}.md", f"# 件{i}\n\n正文 {i} 行一。\n正文 {i} 行二。\n", age_days=i)
    mk(inbox / "重复.md", "库内正文。\n第二行。\n", age_days=6)
    mk(inbox / "空.md", "", age_days=7)

    out1, out2 = tmp_path / "o1", tmp_path / "o2"
    assert run_cli(vault, out1).returncode == 0
    assert run_cli(vault, out2).returncode == 0
    for a, b in zip(products(out1), products(out2)):
        assert a.read_bytes() == b.read_bytes(), f"二跑不一致: {a.name}"


def test_md_escapes_pipe_in_names(tmp_path):
    """文件名含 | 时表格不得被切错列 —— 告警看不见等于没有。"""
    vault, out = base_vault(tmp_path)
    mk(vault / "_待处理" / "P(A|B) 条件概率.md", "# t\n\n正文一。\n正文二。\n", age_days=2)
    assert run_cli(vault, out).returncode == 0
    md = products(out)[1].read_text(encoding="utf-8")
    assert "P(A\\|B)" in md


# ───────────────────────── E. 拒绝路径零产物 ─────────────────────────


def test_reject_explicit_missing_inbox_dir(tmp_path):
    """显式 --inbox-dir 指向不存在的路径 = 用户写错了, 必须拒绝而非报「空仓」。"""
    vault, out = base_vault(tmp_path)
    r = run_cli(vault, out, "--inbox-dir", str(vault / "根本没有这个目录"))
    assert r.returncode != 0
    assert no_products(out)


def test_reject_bad_now(tmp_path):
    vault, out = base_vault(tmp_path)
    r = run_cli(vault, out, now="昨天下午")
    assert r.returncode != 0
    assert no_products(out)


def test_reject_batch_size_out_of_range(tmp_path):
    vault, out = base_vault(tmp_path)
    for bad in ("0", "11"):
        r = run_cli(vault, out, "--batch-size", bad)
        assert r.returncode != 0, f"--batch-size {bad} 应被拒绝 (D15 确认预算上限 10)"
        assert no_products(out)


def test_reject_illegal_label(tmp_path):
    """产物名取自 inbox 目录 basename → 非法字符必须在碰 out-dir **之前**拒绝。"""
    vault, out = base_vault(tmp_path)
    bad = vault / "..逃逸"
    bad.mkdir()
    r = run_cli(vault, out, "--inbox-dir", str(bad))
    assert r.returncode != 0
    assert no_products(out)


def test_reject_overlong_product_name(tmp_path):
    """255B 预检必须先于 out-dir 创建 —— 否则「拒绝但已留空目录」。"""
    vault, out = base_vault(tmp_path)
    # 240 字节（80 个三字节汉字）——单组件在 APFS/ext4 上都建得出来, 但产物名
    # `inbox-preview-` + 240 + `.json` = 259 字节越界。⛔ 原先用 540 字节的目录名,
    # 在 ext4 那种 255 **字节**上限的文件系统上 mkdir 自己就会失败, 测试根本走不到
    # 被测守卫（Codex MEDIUM 的可移植性问题；本机 APFS 按字符计所以侥幸能跑）。
    long_dir = vault / ("超" * 80)
    long_dir.mkdir()
    r = run_cli(vault, out, "--inbox-dir", str(long_dir))
    assert r.returncode != 0
    assert no_products(out)
    assert not out.exists(), "拒绝路径不得留下空的 out-dir"


def test_reject_symlinked_out_dir_parent(tmp_path):
    vault, _ = base_vault(tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    r = run_cli(vault, link / "out")
    assert r.returncode != 0
    assert no_products(real / "out")


def test_reject_symlinked_inbox_dir(tmp_path):
    vault, out = base_vault(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = vault / "_链接收件箱"
    link.symlink_to(outside, target_is_directory=True)
    r = run_cli(vault, out, "--inbox-dir", str(link))
    assert r.returncode != 0
    assert no_products(out)


def test_symlinked_item_is_skipped_with_trace(tmp_path):
    """收件箱内的 symlink 条目: 不跟随, 跳过并留痕 (不静默消失)。"""
    vault, out = base_vault(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("外部内容。\n", encoding="utf-8")
    (vault / "_待处理" / "链接.md").symlink_to(outside)
    mk(vault / "_待处理" / "正常.md", "# t\n\n正文一。\n正文二。\n", age_days=2)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert [i["name"] for i in data["items"]] == ["正常.md"]
    skipped = {s["name"]: s["reason"] for s in data["inventory"]["skipped"]}
    assert "链接.md" in skipped and "symlink" in skipped["链接.md"].lower()


# ───────────────────────── F. 分批 / 台账 / 空仓 ─────────────────────────


def test_batch_is_oldest_first_capped_at_ten(tmp_path):
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    for i in range(1, 24):  # 23 件, 年龄 1..23 天
        mk(inbox / f"件{i:02d}.md", f"# {i}\n\n正文一 {i}。\n正文二 {i}。\n", age_days=i)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    inv = data["inventory"]
    assert inv["total"] == 23
    assert inv["over_budget"] is True
    assert len(data["items"]) == 10
    # 最旧优先: 23 天的排第一, 14 天的排第十
    assert [i["name"] for i in data["items"]] == [f"件{n:02d}.md" for n in range(23, 13, -1)]
    assert len(inv["deferred"]) == 13
    assert inv["deferred"][0]["name"] == "件13.md"


def test_batch_size_override_within_budget(tmp_path):
    vault, out = base_vault(tmp_path)
    for i in range(1, 6):
        mk(vault / "_待处理" / f"f{i}.md", f"# {i}\n\n正文一。\n正文二。\n", age_days=i)
    assert run_cli(vault, out, "--batch-size", "3").returncode == 0
    data = load_json(out)
    assert len(data["items"]) == 3
    assert data["inventory"]["batch_size"] == 3


def test_sleeping_ledger_and_30d_mark(tmp_path):
    """Sleeping 台账: slept_at 优先于 mtime; ≥30 天打标; 不进本批提名。"""
    vault, out = base_vault(tmp_path)
    sleep = vault / "_待处理" / "Sleeping"
    # slept_at 40 天前 (frontmatter 为准, 与 mtime 刻意不一致)
    mk(sleep / "睡满的.md", "---\nslept_at: 2026-07-22\n---\n\n正文。\n", age_days=1)
    # 无 slept_at → 退回 mtime 12 天
    mk(sleep / "睡浅的.md", "# 无 frontmatter\n\n正文。\n", age_days=12)
    mk(vault / "_待处理" / "在批的.md", "# t\n\n正文一。\n正文二。\n", age_days=3)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    sl = data["sleeping"]
    assert sl["exists"] is True
    assert sl["count"] == 2
    assert sl["over_30d_count"] == 1
    assert sl["oldest_days"] == 40
    by = {s["name"]: s for s in sl["items"]}
    assert by["睡满的.md"]["slept_days"] == 40
    assert by["睡满的.md"]["slept_at_source"] == "frontmatter"
    assert by["睡满的.md"]["over_30d"] is True
    assert by["睡浅的.md"]["slept_days"] == 12
    assert by["睡浅的.md"]["slept_at_source"] == "mtime"
    assert by["睡浅的.md"]["over_30d"] is False
    # Sleeping 不进本批
    assert [i["name"] for i in data["items"]] == ["在批的.md"]


def test_sleeping_skips_are_traced_not_silent(tmp_path):
    """Sleeping/ 下的 symlink 与子目录不计入台账, 但必须留痕 —— 与收件箱同一条纪律。"""
    vault, out = base_vault(tmp_path)
    sleep = vault / "_待处理" / "Sleeping"
    mk(sleep / "正常.md", "---\nslept_at: 2026-08-01\n---\n\n正文。\n", age_days=5)
    (sleep / "子目录").mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("外部。\n", encoding="utf-8")
    (sleep / "链接.md").symlink_to(outside)

    assert run_cli(vault, out).returncode == 0
    sl = load_json(out)["sleeping"]
    assert [x["name"] for x in sl["items"]] == ["正常.md"]
    traced = {x["name"] for x in sl["skipped"]}
    assert traced == {"子目录", "链接.md"}, f"跳过项没留痕: {traced}"


def test_extreme_now_degrades_without_crashing(tmp_path):
    """极值 --now 不崩、不伪造: 人话时刻落占位串, 但整轮照常出产物。

    ⛔ 早先版本在 parse_now 装了一道「入口拒绝」守卫 —— 实测 aware datetime 的
    `.timestamp()` 对日历极值并不抛，那道守卫永远不会触发。装一道不会触发的守卫
    等于给自己发一张假的安全证书, 故删掉, 改钉真实可达的降级行为。
    这里选 +00:00 而不是 +14:00: 后者换到 Asia/Shanghai 仍是 9999 年内, 不触发降级。
    """
    vault, out = base_vault(tmp_path)
    r = run_cli(vault, out, now="9999-12-31T23:59:59+00:00")
    assert r.returncode == 0, r.stderr[-300:]
    data = load_json(out)
    assert data["now_utc"] == "9999-12-31T23:59:59Z"
    assert data["now_local"] == "unrepresentable", "+8h 溢出到 10000 年时必须落占位"


def test_far_future_mtime_reports_what_filesystem_stores(tmp_path):
    """⛔ 本条钉的是一个实证事实 + 一条诚实纪律。

    事实: `os.utime` 把 mtime 设到 9999 年时, macOS APFS **静默钳位**到 int64 纳秒
    上界(2262-04-11T23:47:16Z), `st_mtime` / `st_mtime_ns` 回读到的都是钳位值、不抛。
    纪律: 引擎必须**照实报文件系统里存着的那个值**, 既不崩、也不自己造一个。
    第一条断言把「钳位」这个前提本身钉住 —— 换个文件系统若不再钳位, 本条会失败提醒
    而不是继续绿着(前提失效的测试恒绿 = 假证书)。
    """
    vault, out = base_vault(tmp_path)
    p = mk(vault / "_待处理" / "远未来.md", "# t\n\n正文一。\n正文二。\n", age_days=1)
    far = 253402300799  # 9999-12-31T23:59:59Z
    os.utime(p, (far, far))
    stored = p.stat().st_mtime
    assert stored < far, "前提失效: 本平台 os.utime 未钳位远未来 mtime"

    r = run_cli(vault, out)
    assert r.returncode == 0, r.stderr[-300:]
    it = load_json(out)["items"][0]
    expected = datetime.fromtimestamp(stored, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert it["mtime_utc"] == expected, "引擎报的必须逐字等于文件系统存的, 不得自造"
    assert it["age_days"] < 0, "--now 远早于该 mtime, 负年龄如实呈现不夹逼"


def test_empty_inbox_receipt(tmp_path):
    vault, out = base_vault(tmp_path)
    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["inbox_exists"] is True
    assert data["inventory"]["total"] == 0
    assert data["items"] == []
    assert "空" in data["receipt"]
    assert data["last_cleanup"] is None
    assert data["last_cleanup_note"]


def test_missing_default_inbox_is_empty_receipt_not_error(tmp_path):
    """缺省 _待处理/ 尚未创建 = 该 vault 还没开始用收件箱 → 空仓回执 (live 取证路径)。"""
    vault = tmp_path / "vault"
    (vault / "原白板").mkdir(parents=True)
    (vault / "节点").mkdir(parents=True)
    out = tmp_path / "out"
    r = run_cli(vault, out)
    assert r.returncode == 0
    data = load_json(out)
    assert data["inbox_exists"] is False
    assert data["inventory"]["total"] == 0
    assert "尚未创建" in data["receipt"]


def test_subdirectories_other_than_sleeping_are_declared_skipped(tmp_path):
    vault, out = base_vault(tmp_path)
    mk(vault / "_待处理" / "某子目录" / "里面.md", "# x\n\n正文。\n正文二。\n", age_days=2)
    mk(vault / "_待处理" / "顶层.md", "# y\n\n正文。\n正文二。\n", age_days=3)
    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert [i["name"] for i in data["items"]] == ["顶层.md"]
    assert any(s["name"] == "某子目录" for s in data["inventory"]["skipped"])


def test_non_utf8_item_is_undecided_not_guessed(tmp_path):
    vault, out = base_vault(tmp_path)
    p = vault / "_待处理" / "扫描件.pdf"
    p.write_bytes(b"%PDF-1.4\n\xff\xfe\x00binary")
    ts = days_ago(3)
    os.utime(p, (ts, ts))
    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["verdict"] == "拿不准"
    assert it["confident"] is False
    assert it["text_readable"] is False


# ───────────────────────── G. 稳定 ID 与复用契约 ─────────────────────────


def test_stable_id_is_path_determined_and_content_agnostic(tmp_path):
    vault, _ = base_vault(tmp_path)
    # ⛔ 三个产物目录必须各自的父目录已存在 —— prepare_out_dir 明令不静默造祖先链
    r1, r2, r3 = tmp_path / "r1", tmp_path / "r2", tmp_path / "r3"
    p = mk(vault / "_待处理" / "稳定.md", "# a\n\n正文一。\n正文二。\n", age_days=3)
    assert run_cli(vault, r1).returncode == 0
    id1 = load_json(r1)["items"][0]["stable_id"]

    mk(vault / "_待处理" / "稳定.md", "# a\n\n完全不同的正文。\n第二行也不同。\n", age_days=9)
    assert run_cli(vault, r2).returncode == 0
    id2 = load_json(r2)["items"][0]["stable_id"]

    assert id1 == id2, "内容与 mtime 变化不得改变身份"
    assert id1.startswith("inb1-")

    mk(vault / "_待处理" / "另一个.md", "# b\n\n正文一。\n正文二。\n", age_days=2)
    assert run_cli(vault, r3).returncode == 0
    ids = {i["stable_id"] for i in load_json(r3)["items"]}
    assert len(ids) == 2, "不同路径必须不同 ID"
    assert p.exists()


def test_inbox_id_is_not_a_split_anchor_id():
    """两套 ID 空间不可互换: 同参直调 split 的 compute_stable_id 前缀不同、值不同。"""
    mod, sp = load_module(), load_split_module()
    mine = mod.compute_inbox_stable_id("_待处理/x.md")
    theirs = sp.compute_stable_id("_待处理/x.md", [], 1, "board-body-section")
    assert mine.startswith("inb1-")
    assert theirs.startswith(sp.STABLE_ID_PREFIX)
    assert mine != theirs
    assert mod.INBOX_ID_NAMESPACE == "inbox-item/v1"


def test_reuses_split_preview_helpers_by_import():
    """卡片 (c): 稳定 ID 与写侧防御复用 split_preview, 不得另起一套会漂移的实现。"""
    mod, sp = load_module(), load_split_module()
    assert mod._SP_PATH == SPLIT_SCRIPT, "复用来源必须正是 board-split 的 split_preview.py"
    for name in (
        "compute_stable_id",
        "write_pair_atomically_checked",
        "prepare_out_dir",
        "assert_symlink_free",
    ):
        assert hasattr(mod._SP, name), f"复用来源缺 {name}"
    # 标签字符类与 split_preview 同源 —— 平行定义必须逐字相同, 防两套判据漂移
    assert mod._BAD_LABEL.pattern == sp._BAD_NAME.pattern


def test_schema_version_frozen_at_one(tmp_path):
    vault, out = base_vault(tmp_path)
    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["schema_version"] == 1
    assert data["id_namespace"] == "inbox-item/v1"
    assert data["not_executed_disclaimer"]


# ─────────── H. round-2 定向整改回归门 (CARD-G5-6b: B3/H1/H2/H3/H4) ───────────
# 每道门先红后绿: 反例断言在前 (修复前必红), 正向对照在同一测试内 (防修过头)。


def test_fence_close_requires_same_char_min_length_and_bare_fence(tmp_path):
    """⛔ B3 回归: 关闭围栏 = 同字符 且 长度 ≥ 开启长度 且 围栏后仅空白
    (CommonMark 4.5)。

    原实现只比字符: ```` 里的 ``` 被当关闭、``` 后带 info string 的行也被当关闭,
    围栏内容 `# keep` 落到围栏外被 `_HEADING_RE` 剥掉 → 整份文件被误判成
    空骨架 → 建议删。
    """
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "四反引号.md", "````\n```\n# keep\n````\n", age_days=9)
    mk(inbox / "四波浪线.md", "~~~~\n~~~\n# keep\n~~~~\n", age_days=8)
    # CommonMark: 关闭围栏不得带 info string → ```python 是围栏内容, 不是关闭
    mk(inbox / "关闭带infostring.md", "```\n```python\n# keep\n```\n", age_days=7)
    # 同字符子句: ``` 围栏里的 ~~~ 行是内容, 不是关闭 (删掉同字符判断即翻红)
    mk(inbox / "混合字符.md", "```\n~~~\n# keep\n```\n", age_days=6)
    # 制表符缩进不构成围栏 (CommonMark: ≥4 列是缩进代码块); \t``` 不得提前关闭 ——
    # ⛔ 语料不得带正文行: 有正文行时「提前关闭」也杀不死断言, 变异会存活
    mk(inbox / "tab关闭围栏.md", "```\n\t```\n# 标题\n", age_days=5)
    # 围栏内容行哪怕每行都长得像围栏标记, 也是实质正文 (Markdown 围栏语法速查)
    mk(
        inbox / "围栏速查.md",
        "# Markdown 围栏语法速查\n\n## 空围栏怎么写\n\n````\n```\n```\n~~~\n~~~\n````\n",
        age_days=4,
    )
    # 正向对照: 只有围栏无内容 → 仍是空骨架; 正常围栏包着注释 → 仍非空骨架
    mk(inbox / "只有围栏.md", "````\n````\n", age_days=2)
    mk(inbox / "正常围栏.md", "```\n# keep\n```\n", age_days=1)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in (
        "四反引号.md",
        "四波浪线.md",
        "关闭带infostring.md",
        "混合字符.md",
        "tab关闭围栏.md",
        "围栏速查.md",
    ):
        it = item_by_name(data, name)
        assert it["criterion"] != "C3_empty_or_skeleton", f"{name} 的围栏内容被剥掉了"
        assert it["verdict"] != "建议删", name
    only = item_by_name(data, "只有围栏.md")
    assert only["criterion"] == "C3_empty_or_skeleton"
    assert only["verdict"] == "建议删"
    normal = item_by_name(data, "正常围栏.md")
    assert normal["criterion"] != "C3_empty_or_skeleton"
    assert normal["verdict"] != "建议删"


def test_url_without_host_is_not_primary_record(tmp_path):
    """⛔ H1 回归: `https://:443/x`、`https://user@/x` 没有 host —— 能过纯正则,
    但 `urlsplit(...).hostname` 为空, 不构成「一手来源」的机械证据。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(
        inbox / "空host端口.md",
        "---\nsource: https://:443/x\n---\n\n正文甲一。\n正文甲二。\n",
        age_days=4,
    )
    mk(
        inbox / "空host用户.md",
        "---\nsource: https://user@/x\n---\n\n正文乙一。\n正文乙二。\n",
        age_days=3,
    )
    # 正向对照: 带端口/查询/锚点的正常 URL 仍是一手来源
    mk(
        inbox / "带端口正常.md",
        "---\nsource: https://example.com:8443/a?b=c#d\n---\n\n正文丙一。\n正文丙二。\n",
        age_days=2,
    )

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in ("空host端口.md", "空host用户.md"):
        it = item_by_name(data, name)
        assert it["criterion"] != "C1_source_url", name
        assert it["nomination_type"] != "primary-record", name
        # ⛔ round-4 MEDIUM: 只排除 C1 曾放过「C3 删除」类回归 —— 负例必须
        # 同时钉住「没有破坏性提名、不自信、无去向」
        assert it["verdict"] != "建议删", name
        assert it["confident"] is False, name
        assert it["target_hint"] is None and it["nomination_type"] is None, name
    pos = item_by_name(data, "带端口正常.md")
    assert pos["criterion"] == "C1_source_url"
    assert pos["nomination_type"] == "primary-record"


def test_ai_marker_needs_boundary_after_literal(tmp_path):
    """⛔ H2 回归: 标记右侧必须满足边界规则 —— 话题提及不是生成断言, 不得被归档。
    ⛔ round-3 自审 H2-1 扩: 汉字收尾标记后须为行尾/空白/标点; ASCII 字母收尾
    标记(`Generated by AI`)后空白**不算**边界 —— `Generated by AI Lab` 是机构名,
    `本文由 AI 领域…` 是话题, 放行空白就是把边界规则对这些标记变成空操作。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(
        inbox / "版权话题.md",
        "# AI 生成内容的版权问题\n\n话题正文一。\n话题正文二。\n",
        age_days=9,
    )
    mk(
        inbox / "由字版权话题.md",
        "# 由 AI 生成内容的版权问题\n\n话题正文三。\n话题正文四。\n",
        age_days=8,
    )
    mk(
        inbox / "评测话题.md",
        "# Deep Research 生成质量评测\n\n评测正文一。\n评测正文二。\n",
        age_days=7,
    )
    mk(
        inbox / "本文由话题.md",
        "# 访谈整理\n\n本文由 AI 领域的三位研究者共同撰写，记录分歧。\n访谈正文二。\n",
        age_days=6,
    )
    mk(
        inbox / "英文机构.md",
        "# Lab notes\n\nGenerated by AI Lab researchers in Beijing.\n笔记正文二。\n",
        age_days=5,
    )
    # 正向对照: 行尾/标点/加粗收尾仍命中, 依据带行号与逐字片段
    mk(
        inbox / "行尾自述.md",
        "# 报告甲\n\n> 本文由 AI 生成\n\n自述正文一。\n自述正文二。\n",
        age_days=4,
    )
    mk(
        inbox / "标点自述.md",
        "# 报告乙\n\n由 AI 生成，仅供参考\n\n自述正文三。\n自述正文四。\n",
        age_days=3,
    )
    mk(
        inbox / "英文句点自述.md",
        "# Report\n\nThis draft was generated by AI.\n报告正文二。\n",
        age_days=2,
    )
    mk(
        inbox / "加粗自述.md",
        "# 报告丙\n\n**由 AI 生成**\n\n自述正文五。\n自述正文六。\n",
        age_days=1,
    )

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in (
        "版权话题.md",
        "由字版权话题.md",
        "评测话题.md",
        "本文由话题.md",
        "英文机构.md",
    ):
        it = item_by_name(data, name)
        assert it["criterion"] != "C2_ai_self_declared", name
        # ⛔ round-3 Codex MEDIUM: 只排除 C2 曾放过「整批被判 C3 建议删」的变异 ——
        # 负例必须同时钉住「没有被破坏性提名」
        assert it["verdict"] != "建议删", name
        assert it["confident"] is False, name
        assert it["target_hint"] is None and it["nomination_type"] is None, name
    tail = item_by_name(data, "行尾自述.md")
    assert tail["criterion"] == "C2_ai_self_declared"
    assert "第 3 行" in tail["basis"], f"依据必须带行号: {tail['basis']}"
    punct = item_by_name(data, "标点自述.md")
    assert punct["criterion"] == "C2_ai_self_declared"
    assert "由 AI 生成" in punct["basis"], f"依据必须带逐字片段: {punct['basis']}"
    en = item_by_name(data, "英文句点自述.md")
    assert en["criterion"] == "C2_ai_self_declared", "英文句点边界必须仍命中"
    bold = item_by_name(data, "加粗自述.md")
    assert bold["criterion"] == "C2_ai_self_declared", "Markdown 加粗收尾必须仍命中"


def test_bare_ai_markers_are_removed_from_table():
    """⛔ H2 回归(表锁): 裸词「AI 生成」「AI生成」是「由 AI 生成」「由AI生成」的
    严格子串; 截断形态「本文由 AI」「本报告由 AI」被「由 AI 生成」覆盖断言形态 ——
    从表中删除不丢任何带断言锚的命中, 只丢话题提及类误命中。"""
    mod = load_module()
    assert "AI 生成" not in mod.AI_MARKERS
    assert "AI生成" not in mod.AI_MARKERS
    assert "本文由 AI" not in mod.AI_MARKERS
    assert "本报告由 AI" not in mod.AI_MARKERS
    # ⛔ round-8 §三(真空通过): 全 `not in` 的表锁门在 `AI_MARKERS=()` 时照样绿 ——
    # 「什么都没有」满足一切否定断言。先锁住表里**必须还留着**的断言锚形态。
    for kept in ("由 AI 生成", "由AI生成", "Generated by AI", "由 Deep Research 生成"):
        assert kept in mod.AI_MARKERS, f"断言锚形态被删空/误删: {kept}"
    assert len(mod.AI_MARKERS) == len(set(mod.AI_MARKERS)), "表内不得有重复项"


def test_bare_url_line_is_not_a_frontmatter_key(tmp_path):
    """⛔ H3 回归: 正文行 `http://example.com/path` 里的 `http:` 不是 YAML 键 ——
    整篇不得被吞成 frontmatter 后判成「空骨架 → 建议删」, 更不得给出
    「其余皆空行」这类假依据。"""
    vault, out = base_vault(tmp_path)
    mk(vault / "_待处理" / "裸URL行.md", "---\nhttp://example.com/path\n---\n", age_days=3)
    # 正向对照: 真正的 frontmatter source 键仍走 C1
    mk(
        vault / "_待处理" / "真source.md",
        "---\nsource: http://example.com/path\n---\n\n正文一。\n正文二。\n",
        age_days=2,
    )
    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "裸URL行.md")
    assert it["criterion"] != "C3_empty_or_skeleton"
    assert it["verdict"] != "建议删"
    assert "其余皆空行" not in it["basis"], f"假依据: {it['basis']}"
    pos = item_by_name(data, "真source.md")
    assert pos["criterion"] == "C1_source_url"


def test_frontmatter_span_requires_key_then_space_or_eol():
    """⛔ H3 回归(纯函数): YAML 映射键必须是 `key:` 后接空白或行尾;
    `https://example.com` 的 `https:` 不满足 → span 必须为 0。"""
    mod = load_module()
    bad = "---\nhttps://example.com\n---\n\n正文。\n".splitlines()
    assert mod.frontmatter_span(bad) == 0
    good = "---\ntags:\n---\n\n正文。\n".splitlines()
    assert mod.frontmatter_span(good) == 3


def test_key_without_space_after_colon_falls_to_c6(tmp_path):
    """D2 连带钉住: `source:https://x`(冒号后无空格) 此后不再识别为键 → 该行成为
    正文、材料落 C6 拿不准 —— 方向安全(不误判一手), 且此偏差已写进文件头声明。"""
    vault, out = base_vault(tmp_path)
    mk(
        vault / "_待处理" / "无空格键.md",
        "---\nsource:https://example.com/x\n---\n\n正文一。\n正文二。\n",
        age_days=3,
    )
    assert run_cli(vault, out).returncode == 0
    it = load_json(out)["items"][0]
    assert it["criterion"] == "C6_undecided"
    assert it["verdict"] == "拿不准"


def test_md_multi_canonical_declares_undecidable_not_crowned(tmp_path):
    """⛔ H4 回归: JSON basis 声明「哪一份算正本不可判」时, 人读 MD §四不得再
    钦定「正本 `字典序首项`」—— 那与 basis 自相矛盾。单正本时 MD 仍明确给出
    正本路径 (正向对照同测, 防修过头)。只改 MD 渲染, JSON schema v1 冻结。"""
    vault, out = base_vault(tmp_path)
    body = "同一段被存过两次的正文。\n第二行。\n"
    mk(vault / "节点" / "甲本.md", body, age_days=40)
    (vault / "归档").mkdir()
    mk(vault / "归档" / "乙本.md", body, age_days=39)
    mk(vault / "_待处理" / "第三份.md", body, age_days=2)
    single = "只存过一次的正文。\n它的第二行。\n"
    mk(vault / "节点" / "唯一正本.md", single, age_days=40)
    mk(vault / "_待处理" / "唯一副本.md", single, age_days=3)

    assert run_cli(vault, out).returncode == 0
    md = products(out)[1].read_text(encoding="utf-8")
    multi_line = next(ln for ln in md.splitlines() if ln.startswith("- **第三份.md**"))
    assert "不可判" in multi_line, f"MD 钦定了正本: {multi_line}"
    assert "正本 `" not in multi_line, multi_line
    assert "另有副本" not in multi_line, multi_line
    # 不可判 ≠ 不给线索: 两个候选路径都要向人呈现
    assert "节点/甲本.md" in multi_line and "归档/乙本.md" in multi_line
    single_line = next(ln for ln in md.splitlines() if ln.startswith("- **唯一副本.md**"))
    assert "正本 `节点/唯一正本.md`" in single_line


def test_source_declared_clipping_is_never_suggested_for_deletion(tmp_path):
    """⛔ round-3 自审 H1-1/H3-1: C1 判据收窄后,「只有 frontmatter、没有正文」的
    剪藏不得从「留原地」翻成「空骨架 → 建议删」。

    未消化信号护栏 (显式偏差 15): frontmatter 有 source 声明 / 含解析不成键的行 /
    文件以未闭合 HTML 注释结尾 → 一律落 C6 拿不准, 永不判 C3。
    同时覆盖: 引号+行尾注释的 source 仍走 C1 (先剥注释再剥引号)、
    冒号前空格的键仍被解析、大写 scheme 仍是一手来源。
    """
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    # 护栏 A: source 声明了但不是合法 URL, 无正文 → 拿不准, 不建议删
    mk(inbox / "空host剪藏.md", "---\nsource: https://:443/x\n---\n", age_days=9)
    mk(inbox / "空host用户剪藏.md", "---\nsource: https://user@/x\n---\n", age_days=8)
    # 护栏 B: source 冒号后无空格排在合法键后面 → 该行被吞, 但解析不全不判空骨架
    mk(
        inbox / "书签无空格键.md",
        "---\ntitle: 论文摘录\nsource:https://arxiv.org/abs/2401.00001\n---\n",
        age_days=7,
    )
    # 正向对照: 合法 source + 无正文 → 仍 C1 留原地 (C1 在 C3 之前, 剪藏受保护)
    mk(inbox / "正常空剪藏.md", "---\nsource: https://ok.test/clip\n---\n", age_days=6)
    # 引号 + 行尾注释组合: 先剥注释再剥引号 → C1
    mk(
        inbox / "引号注释剪藏.md",
        '---\nsource: "https://quoted.test/x" # 官方来源\n---\n',
        age_days=5,
    )
    # 冒号前空格: `source : url` 也是合法 YAML 键 (pyyaml 同判) → C1
    mk(inbox / "冒号前空格剪藏.md", "---\nsource : https://spaced.test/x\n---\n", age_days=4)
    # 大写 scheme: RFC 3986 §3.1 大小写不敏感 → C1
    mk(
        inbox / "大写scheme.md",
        "---\nsource: HTTPS://Upper.Test/a\n---\n\n正文一。\n正文二。\n",
        age_days=3,
    )
    # 正向对照: 无 source 的纯空骨架 → 仍 C3 建议删 (护栏不得误伤存量判据)
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=2)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in ("空host剪藏.md", "空host用户剪藏.md", "书签无空格键.md"):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被护栏漏掉了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert it["confident"] is False, name
        assert it["target_hint"] is None and it["nomination_type"] is None, name
        # ⛔ round-4 MEDIUM: 护栏必须说清「为什么拿不准」, 不能只换 verdict 不给理由
        assert it["uncertain_reason"], name
    for name in (
        "正常空剪藏.md",
        "引号注释剪藏.md",
        "冒号前空格剪藏.md",
        "大写scheme.md",
    ):
        it = item_by_name(data, name)
        assert it["criterion"] == "C1_source_url", f"{name}: {it['basis']}"
        assert it["verdict"] == "留原地", name
    quoted = item_by_name(data, "引号注释剪藏.md")
    assert "官方来源" not in quoted["basis"], quoted["basis"]
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_unclosed_html_comment_never_suggested_for_deletion(tmp_path):
    """⛔ round-3 自审 B3-1: `<!--` 没等到 `-->` 就到文件尾时, 哪些内容被注释吞掉
    是引擎猜不了的 —— 不得据此判「空骨架 → 建议删」, 更不得给出
    「标题 0 行、代码围栏 0 行」这种与肉眼可见内容矛盾的假依据。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(
        inbox / "注释未闭合.md",
        "<!-- 说明: 粘贴时忘了闭合\n```python\n# keep\n这段正文其实存在\n",
        age_days=5,
    )
    # 正向对照: 闭合注释的空骨架 → 仍 C3 建议删 (护栏不误伤存量判据)
    mk(inbox / "闭合注释骨架.md", "---\ntitle: t\n---\n\n# 标题\n\n<!-- 注释 -->\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "注释未闭合.md")
    assert it["verdict"] != "建议删", f"未闭合注释的文件被建议删了: {it['basis']}"
    assert it["criterion"] == "C6_undecided"
    assert "其余皆空行" not in it["basis"], f"假依据: {it['basis']}"
    skeleton = item_by_name(data, "闭合注释骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_fence_close_trailing_whitespace_must_be_ascii(tmp_path):
    """⛔ round-3 Codex BLOCKER: 关闭围栏行尾只允许 ASCII 空白 (CommonMark 4.5)。

    `str.strip()` 接受一切 Unicode 空白 —— 行尾一个 U+00A0 (NBSP, 从网页复制
    常见) 曾让该行被当成合法关闭围栏, 围栏提前闭合, `# keep` 被剥 →
    「空骨架 → 建议删 confident=true」。NBSP 行在 CommonMark 里是围栏**内容**。
    """
    vault, out = base_vault(tmp_path)
    mk(
        vault / "_待处理" / "nbsp关闭.md",
        "```\n```\xa0\n# keep\n```\n",
        age_days=5,
    )
    # 正向对照: 行尾 ASCII 空白/制表符仍是合法关闭 (不得修过头) ——
    # ⛔ 语料必须是「只包围栏无内容」: 带真实内容行时断言杀不死变异
    mk(vault / "_待处理" / "ascii尾随.md", "```\n``` \t\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "nbsp关闭.md")
    assert it["criterion"] != "C3_empty_or_skeleton", f"NBSP 提前关闭了围栏: {it['basis']}"
    assert it["verdict"] != "建议删", it["basis"]
    pos = item_by_name(data, "ascii尾随.md")
    assert pos["criterion"] == "C3_empty_or_skeleton", "只包围栏无内容 → 仍空骨架"
    assert pos["verdict"] == "建议删"


def test_ai_suspect_without_body_never_suggested_for_deletion(tmp_path):
    """⛔ round-4 BLOCKER-1: 边界规则拒掉的 AI 自述嫌疑 × 无正文 → 不得判 C3 建议删。

    `generator: Generated by AI on March` 是肯定式生成断言, 但 ASCII 收尾标记
    的右边界(禁空白)把它拒了 —— 漏判本身方向安全, 可漏判后掉进 C3 就是把
    「引擎不敢确定的文件」当垃圾扔。护栏第 4 类信号: 裸子串在场即拦。"""
    vault, out = base_vault(tmp_path)
    mk(
        vault / "_待处理" / "英文断言仅头.md",
        "---\ngenerator: Generated by AI on March\n---\n",
        age_days=5,
    )
    # 正向对照: 无任何 AI 字样的纯空骨架 → 仍 C3 建议删 (护栏不得误伤存量判据)
    mk(vault / "_待处理" / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "英文断言仅头.md")
    assert it["verdict"] != "建议删", f"AI 嫌疑件被建议删了: {it['basis']}"
    assert it["criterion"] == "C6_undecided"
    assert it["confident"] is False
    assert it["target_hint"] is None and it["nomination_type"] is None
    assert "Generated by AI" in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_unparsed_source_with_duplicate_body_is_not_suggested_for_deletion(tmp_path):
    """⛔ round-4 BLOCKER-2: 非标准 source × 正文与库内逐字重复 → 不得建议删。

    C4 只证明「剥掉 frontmatter 后正文相等」, 不证明「整个文件多余」—— 这份
    还带着一个独有的来源声明(冒号后无空格, 键正则不认)。来源信息必须在建议里
    摆到台面上; 摆不出来就不许删。护栏拦在 C4 出口, 降 C6 且重复证据留痕。"""
    vault, out = base_vault(tmp_path)
    body = "这份正文和库里那份一字不差。\n第二行也相同。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(
        vault / "_待处理" / "带来源重复.md",
        "---\ntitle: 剪藏\nsource:https://unique.example/a\n---\n" + body,
        age_days=3,
    )
    # 正向对照: 无 source 的重复件 → 仍 C4 建议删 (护栏不得误伤存量判据)
    mk(vault / "_待处理" / "无来源重复.md", body, age_days=2)
    # 带普通元数据键的重复件 → 仍 C4 建议删, 但元数据必须挂冲突留痕
    mk(
        vault / "_待处理" / "带标签重复.md",
        "---\ntags: [剪藏, 待整理]\n---\n" + body,
        age_days=1,
    )

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "带来源重复.md")
    assert it["verdict"] != "建议删", f"带来源的重复件被建议删了: {it['basis']}"
    assert it["criterion"] == "C6_undecided"
    assert it["confident"] is False
    assert it["target_hint"] is None and it["nomination_type"] is None
    assert it["exact_duplicate_of"] == "节点/库内正本.md", "重复证据必须留痕"
    assert any(c["kind"] == "exact_duplicate_under_other_verdict" for c in it["conflicts"]), "重复证据必须挂冲突留痕"
    assert "unique.example" in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    dup = item_by_name(data, "无来源重复.md")
    assert dup["criterion"] == "C4_exact_duplicate"
    assert dup["verdict"] == "建议删"
    tagged = item_by_name(data, "带标签重复.md")
    assert tagged["criterion"] == "C4_exact_duplicate"
    assert tagged["verdict"] == "建议删"
    assert any(c["kind"] == "frontmatter_metadata_present" for c in tagged["conflicts"]), (
        "C4 删除前 frontmatter 元数据必须留痕"
    )


def test_source_like_keys_are_undigested_signals(tmp_path):
    """⛔ round-5 自审 F2 (BLOCKER): 来源声明信号不能只认字面 source 键 ——
    `url:`/`URL:`/`Source:` 等剪藏工具常见键名曾穿透全部信号: 无正文判 C3 建议删、
    带独有 URL 的重复件判 C4 建议删且 URL 零留痕。任意键的值为合法 URL 形态
    即为来源声明信号(降 C6); C1 仍只认 source 键(R8 稿约定), 信号只降级不扩大。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "url键书签.md", "---\nurl: https://clip.example/article-42\n---\n", age_days=7)
    mk(inbox / "大写Source键.md", "---\nSource: https://clip.example/other\n---\n", age_days=6)
    body = "这份正文和库里那份一字不差。\n第二行也相同。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(
        inbox / "url键重复件.md",
        "---\nurl: https://unique-source.example/a\n---\n" + body,
        age_days=5,
    )
    # 正向对照 1: 值不是 URL 的键不触发信号 → 纯空骨架仍 C3
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=4)
    # 正向对照 2: source 键 + 合法 URL → 仍 C1 (信号不扩大 C1)
    mk(inbox / "source键书签.md", "---\nsource: https://ok.test/x\n---\n", age_days=3)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in ("url键书签.md", "大写Source键.md"):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert "clip.example" in (it["uncertain_reason"] or ""), name
    dup = item_by_name(data, "url键重复件.md")
    assert dup["verdict"] != "建议删", f"URL 重复件被建议删了: {dup['basis']}"
    assert dup["exact_duplicate_of"] == "节点/库内正本.md"
    assert "unique-source.example" in (dup["uncertain_reason"] or "")
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"
    primary = item_by_name(data, "source键书签.md")
    assert primary["criterion"] == "C1_source_url"


def test_slept_at_is_undigested_signal(tmp_path):
    """⛔ round-5 自审 F3 (MEDIUM): slept_at 是引擎自己在 Sleeping 台账解析的
    账本状态键 —— 收件箱文件带它意味着「从 Sleeping 移回、正待处置」。
    带 slept_at 的重复件/骨架件曾被建议删且起睡时间戳零留痕。"""
    vault, out = base_vault(tmp_path)
    body = "从 Sleeping 移回来的正文。\n第二行。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(
        vault / "_待处理" / "移回重复件.md",
        "---\ntitle: 移回\nslept_at: 2026-08-01\n---\n" + body,
        age_days=5,
    )
    mk(vault / "_待处理" / "移回骨架.md", "---\nslept_at: 2026-07-01\n---\n\n# 只有标题\n", age_days=4)
    # 正向对照: 无 slept_at 的重复件 → 仍 C4 建议删
    mk(vault / "_待处理" / "普通重复件.md", body, age_days=3)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in ("移回重复件.md", "移回骨架.md"):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert "slept_at" in (it["uncertain_reason"] or ""), name
    dup = item_by_name(data, "普通重复件.md")
    assert dup["criterion"] == "C4_exact_duplicate"
    assert dup["verdict"] == "建议删"


def test_ai_case_and_whitespace_variants_are_undigested(tmp_path):
    """⛔ round-5 BLOCKER-1: AI 声明的大小写/Unicode 空白变体不得穿透字面量表
    与裸子串护栏 —— `generated by ai`(全小写)、`GENERATED BY AI`(全大写)、
    内部 NBSP 形态都曾在无正文时掉进 C3 建议删 confident=true。C2 匹配与
    护栏信号共用归一化(casefold + 空白折叠)。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "全小写AI声明.md", "---\ngenerator: generated by ai\n---\n", age_days=7)
    mk(inbox / "全大写AI声明.md", "---\ngenerator: GENERATED BY AI\n---\n", age_days=6)
    mk(inbox / "nbspAI声明.md", "---\ngenerator: Generated\xa0\xa0by\xa0AI\n---\n", age_days=5)
    # 正向对照: 无 AI 字样纯空骨架 → 仍 C3; 边界规则仍拒「生成」后挂字话题
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=4)
    mk(
        inbox / "话题提及.md",
        "# 标题\n\n由 AI 生成内容的版权讨论。\n话题正文一。\n话题正文二。\n",
        age_days=3,
    )

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in ("全小写AI声明.md", "全大写AI声明.md", "nbspAI声明.md"):
        it = item_by_name(data, name)
        # 归一化后这些行尾变体被 C2 **确定命中**（行尾满足 ASCII 边界）——
        # 比护栏 C6 更强且正确；关键是绝不再落 C3 建议删
        assert it["criterion"] == "C2_ai_self_declared", f"{name}: {it['basis']}"
        assert it["verdict"] == "归档", name
        assert "AI" in it["basis"], it["basis"]
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"
    topic = item_by_name(data, "话题提及.md")
    assert topic["criterion"] != "C2_ai_self_declared", "归一化不得扩 C2 到话题提及"


def test_damaged_url_alias_is_undigested(tmp_path):
    """⛔ round-5 BLOCKER-2: 损坏 URL 的来源键别名不得穿透护栏 —— 信号③b 原
    要求「值过合法 URL 判定」，`Source: https://:443/x`(损坏) 因此被当不存在
    而建议删。URL 前缀形态即算来源声明(与 source 键的 fail-closed 同口径)。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "坏Source别名.md", "---\nSource: https://:443/x\n---\n", age_days=6)
    body = "别名键重复件的正文。\n第二行。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(
        vault / "_待处理" / "坏url别名重复.md",
        "---\nurl: https://:443/broken\n---\n" + body,
        age_days=5,
    )
    # 正向对照: 值不是 URL 的别名键 → 不触发 → 纯空骨架仍 C3
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in ("坏Source别名.md", "坏url别名重复.md"):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert ":443" in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_natural_ai_word_is_undigested_signal(tmp_path):
    """⛔ round-6 BLOCKER-1: 自然语言肯定式 AI 声明（表外）不得穿透双层 ——
    `This report was generated by an AI system` 不含任何表项, 曾在无正文时
    掉进 C3 建议删。护栏级结构性信号: frontmatter 值或文头行含独立词「AI」
    (词边界) 即降 C6; C2 确定命中仍走有限表+边界 (宽匹配给话题发归档=硬猜)。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(
        vault / "_待处理" / "自然英文AI.md",
        "---\ngenerator: This report was generated by an AI system\n---\n",
        age_days=6,
    )
    # 正向对照: 无 AI 字样纯空骨架 → 仍 C3; 话题提及有正文 → 仍不进 C2
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=5)
    mk(
        inbox / "话题提及.md",
        "# 标题\n\n由 AI 生成内容的版权讨论。\n话题正文一。\n话题正文二。\n",
        age_days=4,
    )

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "自然英文AI.md")
    assert it["verdict"] != "建议删", f"表外 AI 声明被建议删了: {it['basis']}"
    assert it["criterion"] == "C6_undecided"
    assert "AI" in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"
    topic = item_by_name(data, "话题提及.md")
    assert topic["criterion"] != "C2_ai_self_declared"


def test_autolink_url_alias_is_undigested(tmp_path):
    """⛔ round-6 BLOCKER-2: Markdown autolink 角括号形态的来源别名不得穿透
    信号③b —— `URL: <https://…>` 首字符是 `<`, 曾绕过 http 前缀判定。"""
    vault, out = base_vault(tmp_path)
    mk(vault / "_待处理" / "角括号别名.md", "---\nURL: <https://example.test/x>\n---\n", age_days=6)
    # 正向对照: 值不是 URL 的键 → 纯空骨架仍 C3
    mk(vault / "_待处理" / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=5)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "角括号别名.md")
    assert it["verdict"] != "建议删", f"角括号别名被建议删了: {it['basis']}"
    assert it["criterion"] == "C6_undecided"
    assert "example.test" in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_backtick_info_string_is_not_a_fence_open(tmp_path):
    """⛔ round-6 BLOCKER-3: 反引号围栏的 info string 含反引号时不是合法开启行
    (CommonMark 4.4) —— ```foo`bar 曾被当开启、下一行被当关闭、正文再被
    标题剥掉 → 空骨架建议删。tilde 围栏的 info string 允许反引号。"""
    vault, out = base_vault(tmp_path)
    mk(vault / "_待处理" / "反引号info.md", "```foo`bar\n```\n# keep\n", age_days=6)
    # 正向对照: 合法 info string 开启 + 关闭 → 围栏正常 (内容行非空)
    mk(vault / "_待处理" / "正常info.md", "```python\n# keep\n```\n", age_days=5)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "反引号info.md")
    assert it["verdict"] != "建议删", f"非法 info string 围栏件被建议删了: {it['basis']}"
    assert it["criterion"] != "C3_empty_or_skeleton"
    normal = item_by_name(data, "正常info.md")
    assert normal["criterion"] != "C3_empty_or_skeleton", "合法围栏不得误伤"


def test_cjk_adjacent_ai_is_undigested_signal(tmp_path):
    """⛔ round-7 BLOCKER-1: CJK 邻接的 AI 字样没有 Unicode 词边界 ——
    `由AI系统生成` 曾穿透 \\bAI\\b 信号与有限表。词判定改「左右非 ASCII 字母」。"""
    vault, out = base_vault(tmp_path)
    mk(
        vault / "_待处理" / "CJK邻接AI.md",
        "---\ngenerator: 本报告由AI系统生成\n---\n",
        age_days=6,
    )
    # 正向对照: 无 AI 字样纯空骨架 → 仍 C3
    mk(vault / "_待处理" / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=5)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    it = item_by_name(data, "CJK邻接AI.md")
    assert it["verdict"] != "建议删", f"CJK 邻接 AI 被建议删了: {it['basis']}"
    assert it["criterion"] == "C6_undecided"
    assert "AI" in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_tab_and_nbsp_indented_heading_is_content(tmp_path):
    """⛔ round-7 BLOCKER-2: ATX 标题缩进必须限字面空格 —— `\\t# keep` 是缩进
    代码、`\\xa0# keep` 是普通正文, 都曾被 `^\\s{0,3}` 当标题剥掉 → 空骨架
    建议删 (与 B3-4 围栏缩进同族的教训)。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "tab缩进标题.md", "\t# keep\n", age_days=6)
    mk(inbox / "nbsp缩进标题.md", "\xa0# keep\n", age_days=5)
    # 正向对照: 顶格标题 + 无正文 → 仍 C3 建议删
    mk(inbox / "顶格标题.md", "# 标题\n\n## 小节\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in ("tab缩进标题.md", "nbsp缩进标题.md"):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] != "C3_empty_or_skeleton", name
    heading = item_by_name(data, "顶格标题.md")
    assert heading["criterion"] == "C3_empty_or_skeleton"
    assert heading["verdict"] == "建议删"


def test_wrapped_url_values_are_undigested_signals(tmp_path):
    """⛔ round-7 BLOCKER-3: 来源值判定必须 substring 级 —— YAML 标签
    (`!!str https://…`) 与引号包 Markdown 链接 (`"[来源](https://…)") 曾因
    前缀判定穿透。值内任意位置含 http(s):// 即算来源声明。"""
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "yaml标签URL.md", "---\nURL: !!str https://example.test/x\n---\n", age_days=6)
    mk(
        inbox / "md链接URL.md",
        '---\nURL: "[来源](https://example.test/x)"\n---\n',
        age_days=5,
    )
    # 正向对照: 值不含 http(s):// 的键 → 纯空骨架仍 C3
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    for name in ("yaml标签URL.md", "md链接URL.md"):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert "example.test" in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_frontmatter_map_value_fidelity():
    """⛔ round-3 自审 GATE-1/H3-3: _FM_KEY_RE 的**值提取**半边此前无任何门锁 ——
    回退旧正则 63 条照样全绿。本门锁三个行为: 值含冒号的键完整保留 /
    冒号前空格的键被解析 / 冒号后无空格仍不认键 (值不吞 URL)。"""
    mod = load_module()
    fm = mod.frontmatter_map(["created: 2026-01-01T00:00:00+08:00"])
    assert fm["created"] == "2026-01-01T00:00:00+08:00", "值里的冒号不得截断值"
    fm = mod.frontmatter_map(["title : x"])
    assert fm["title"] == "x", "冒号前空格的键 (pyyaml 认) 必须解析出值"
    fm = mod.frontmatter_map(["source:https://x"])
    assert "source" not in fm, "冒号后无空格不认键, URL 不得被吞成值"


# ───── I. round-8 定向整改回归门 (CARD-G5-6c: NBSP 标题 / 模型声明 / DOI 来源) ─────


def test_nbsp_after_hash_is_not_an_atx_heading(tmp_path):
    """⛔ round-8 BLOCKER-1: ATX 的**井号后分隔**也只认 ASCII 空格/制表符。

    前置缩进在 round-7 已收窄为字面空格, 但 `#{1,6}` 后仍写着 `(?:\\s|$)` ——
    Python `re` 的 `\\s` 在 str 模式下是 Unicode 语义, `#\\xa0keep`
    (字节 23c2a06b6565700a) 被当标题剥掉 → 「标题 1 行、实质正文 0 字符」
    → `建议删 + confident=true`。同一条规则的两半只修一半, 等于没修。
    """
    mod = load_module()
    # 纯函数半边: CommonMark §4.2 = 空格 / 制表符 / 行尾
    assert mod._HEADING_RE.match("# x"), "ASCII 空格必须仍是合法分隔"
    assert mod._HEADING_RE.match("#\tx"), "制表符是 CommonMark 合法分隔, 不得连坐收窄"
    assert mod._HEADING_RE.match("#"), "行尾 ATX (空标题) 必须仍成立"
    assert mod._HEADING_RE.match("   ###### x"), "3 空格缩进 + 六级标题仍成立"
    assert not mod._HEADING_RE.match("#\u00a0x"), "NBSP 不是 ATX 分隔 (round-8 BLOCKER-1)"
    # ⛔ 验伪锚: 防「按反例特判 NBSP」的窄修 —— 全角/EM 空格是同族 Unicode 空白
    assert not mod._HEADING_RE.match("#\u2003x"), "EM SPACE 同属 Unicode 空白, 不得只排 NBSP"
    assert not mod._HEADING_RE.match("#\u3000x"), "IDEOGRAPHIC SPACE 同上"
    assert not mod._HEADING_RE.match("#x"), "井号后无分隔本就不是标题 (口径不得放宽)"

    # 端到端半边: 真实 CLI
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "井号NBSP.md", "#\u00a0keep\n", age_days=6)
    # ⛔ 正向对照(验伪锚): 井号后制表符**是**标题 → 无正文仍 C3 建议删。
    # 若有人把修复写成只认空格 `(?:[ ]|$)`, 本条会红。
    mk(inbox / "井号TAB标题.md", "#\tonly heading\n", age_days=5)
    # 正向对照: 顶格空格标题 + 无正文 → 仍 C3 建议删
    mk(inbox / "顶格标题.md", "# 标题\n\n## 小节\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["items"], "items 为空则本门恒真 = 假绿"
    it = item_by_name(data, "井号NBSP.md")
    assert it["verdict"] != "建议删", f"NBSP 井号行被建议删了: {it['basis']}"
    assert it["criterion"] == "C6_undecided", it["criterion"]
    assert it["confident"] is False
    assert it["target_hint"] is None and it["nomination_type"] is None
    for name in ("井号TAB标题.md", "顶格标题.md"):
        ctrl = item_by_name(data, name)
        assert ctrl["criterion"] == "C3_empty_or_skeleton", f"{name}: {ctrl['basis']}"
        assert ctrl["verdict"] == "建议删", name


def test_model_version_generation_claim_is_undigested_signal(tmp_path):
    """⛔ round-8 BLOCKER-2: 带模型版本的真实生成声明穿透三层护栏。

    `generator: 由 GPT-4 生成` 既不在有限表 (表只到 `由 GPT 生成`, 差一个版本号),
    也没有独立词「AI」 → 无正文时 `建议删 + confident=true`。
    修法按**声明骨架**而非**枚举模型名** (卡文 §3 默认裁决): 模型名是开放集合,
    `由 <某物> 生成` / `generated by <某物>` 这个断言骨架是闭合的。
    ⚠️ 只降 C6, 绝不进 C2 —— 宽匹配给话题提及发确定归档就是硬猜。
    """
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    # round-8 反例原样
    mk(inbox / "GPT4声明.md", "---\ngenerator: 由 GPT-4 生成\n---\n", age_days=9)
    # ⛔ 同族(不得靠枚举): 换任意模型名/版本号都必须接住
    mk(inbox / "Gemini声明.md", "---\nnote: 本文由 Gemini 2.5 Pro 生成\n---\n", age_days=8)
    mk(inbox / "英文声明.md", "---\nnote: Generated by Llama-4-Maverick\n---\n", age_days=7)
    # 字段半边: 值里根本没有「生成」二字, 只有键名在声明
    mk(inbox / "仅键名声明.md", "---\ngenerator: claude-opus-4\n---\n", age_days=6)
    # C4 出口也必须拦(护栏是路径属性, 不能只拦 C3)
    body = "这份正文和库里那份一字不差。\n第二行也相同。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(inbox / "声明重复件.md", "---\ngenerator: 由 GPT-4o 生成\n---\n" + body, age_days=5)
    # 正向对照: 无任何生成声明的纯空骨架 → 仍 C3 建议删
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["items"], "items 为空则本门恒真 = 假绿"
    for name in ("GPT4声明.md", "Gemini声明.md", "英文声明.md"):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert it["confident"] is False, name
        assert it["target_hint"] is None and it["nomination_type"] is None, name
        assert "生成断言结构" in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    key_only = item_by_name(data, "仅键名声明.md")
    assert key_only["verdict"] != "建议删", key_only["basis"]
    assert key_only["criterion"] == "C6_undecided"
    kr = key_only["uncertain_reason"] or ""
    assert "generator" in kr and "生成来源" in kr, kr
    for name in ("GPT4声明.md", "Gemini声明.md", "英文声明.md", "仅键名声明.md"):
        r = item_by_name(data, name)["uncertain_reason"] or ""
        assert "既不认识这个键" not in r, f"{name} 落到了白名单兜底，生成信号没被测到: {r}"
    dup = item_by_name(data, "声明重复件.md")
    assert dup["verdict"] != "建议删", f"带生成声明的重复件被建议删了: {dup['basis']}"
    assert dup["criterion"] == "C6_undecided"
    assert dup["exact_duplicate_of"] == "节点/库内正本.md", "重复证据仍须留痕"
    # ⛔ 信号只降级, 不扩大 C2: 这些文件不得被判成「AI 自述 → 确定归档」
    for name in ("GPT4声明.md", "Gemini声明.md", "英文声明.md", "仅键名声明.md"):
        assert item_by_name(data, name)["criterion"] != "C2_ai_self_declared", name
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_doi_source_identifier_blocks_deletion(tmp_path):
    """⛔ round-8 HIGH: `Source: DOI:10.1000/xyz` 的唯一来源标识被当作不存在。

    两处缺口: `"source" in fm` 是**大小写敏感**的字面查找(取不到 `Source`),
    而值不含 `http(s)://` 时 `url_bearing_keys` 也接不住 → C3 `建议删 +
    confident=true`。护栏两侧都补: 键名归一(大小写/连字符) + DOI 值形态。
    ⚠️ DOI **不冒充 URL 也不升 C1**(卡文 §3): 只把来源摆上台面降 C6。
    """
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    # round-8 反例原样
    mk(inbox / "DOI来源.md", "---\nSource: DOI:10.1000/xyz\n---\n", age_days=9)
    # 键名归一半边: 值不是 URL 也不是 DOI, 靠键名接住
    mk(inbox / "大写SOURCE手抄.md", "---\nSOURCE: 手抄自 2019 年讲义 P37\n---\n", age_days=8)
    # 值形态半边: 键名不在别名表, 靠 DOI 形态接住
    mk(inbox / "identifier键DOI.md", "---\nidentifier: 10.1145/3292500.3330701\n---\n", age_days=7)
    # C4 出口也必须拦
    body = "这份正文和库里那份一字不差。\n第二行也相同。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(inbox / "DOI重复件.md", "---\ndoi: 10.1000/dup-only\n---\n" + body, age_days=6)
    # 正向对照 1: 无来源声明的纯空骨架 → 仍 C3 建议删
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=5)
    # 正向对照 2: 合法 source URL → 仍 C1(护栏不得扩大也不得挤掉判据)
    mk(inbox / "正常剪藏.md", "---\nsource: https://ok.test/clip\n---\n", age_days=4)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["items"], "items 为空则本门恒真 = 假绿"
    for name, frag in (
        ("DOI来源.md", "DOI:10.1000/xyz"),
        ("大写SOURCE手抄.md", "讲义 P37"),
        ("identifier键DOI.md", "10.1145/3292500.3330701"),
    ):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert it["confident"] is False, name
        assert it["target_hint"] is None and it["nomination_type"] is None, name
        # ⛔ 来源标识必须逐字留痕 —— 否则「拦住了」等于把线索一起吞掉
        assert frag in (it["uncertain_reason"] or ""), it["uncertain_reason"]
    # ⛔ 信号归属（round-2 MEDIUM-4）：必须是**来源族**信号接住的，不是白名单兜底。
    # 单独回退来源信号时兜底会接住材料、verdict 断言仍绿 —— 那条防线就没被测到。
    for name in ("DOI来源.md", "大写SOURCE手抄.md"):
        r = item_by_name(data, name)["uncertain_reason"] or ""
        assert "不是可机判的" in r, f"{name} 应由 source 键名归一接住: {r}"
        assert "既不认识这个键" not in r, f"{name} 落到了白名单兜底: {r}"
    for name in ("identifier键DOI.md", "DOI重复件.md"):
        r = item_by_name(data, name)["uncertain_reason"] or ""
        assert "DOI 来源标识" in r, f"{name} 应由 DOI 值形态接住: {r}"
        assert "既不认识这个键" not in r, f"{name} 落到了白名单兜底: {r}"
    # ⛔ DOI 不冒充 URL / 不升 C1
    doi_item = item_by_name(data, "DOI来源.md")
    assert doi_item["criterion"] != "C1_source_url", "DOI 不得被判成一手 URL"
    assert "DOI" in (doi_item["uncertain_reason"] or "")
    dup = item_by_name(data, "DOI重复件.md")
    assert dup["verdict"] != "建议删", f"带 DOI 的重复件被建议删了: {dup['basis']}"
    assert dup["criterion"] == "C6_undecided"
    assert dup["exact_duplicate_of"] == "节点/库内正本.md", "重复证据仍须留痕"
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"
    primary = item_by_name(data, "正常剪藏.md")
    assert primary["criterion"] == "C1_source_url"
    assert primary["verdict"] == "留原地"


# ── round-2 审查（Codex round-1）抓出的同族缝隙回归门 ──


def test_long_model_name_and_punctuated_generation_claims_are_undigested(tmp_path):
    """⛔ round-2 审查 BLOCKER: 生成声明骨架的三条缝隙——

    1. 中文骨架原写 `由[^。；！？\\n]{1,40}?生成`，**长度上界本身就是缝隙**：
       `本文由 openai-gpt-oss-120b-finetune-canvas-learning-system-v2026-09-01 生成`
       中间 65 字符，穿透后无正文被判 C3 确定删除；
    2. 英文骨架原写 `generated by \\S`（字面空格），`Generated by: GPT-4` 的
       `by` 后是冒号，不匹配；
    3. `Generated by<U+200B>GPT-4` 的零宽空格**不是** `str.isspace()` 认的空白，
       `ln.split()` 折叠不掉。护栏改走 `_norm_guard_line`（零宽→空格）。
    """
    mod = load_module()
    # 纯函数半边：上界去掉后骨架才真闭合
    long_name = "openai-gpt-oss-120b-finetune-canvas-learning-system-v2026-09-01"
    assert len(long_name) > 40, "反例必须真的超过原上界，否则本门是死门"
    assert mod._GEN_CLAIM_CN_RE.search(f"本文由 {long_name} 生成")
    assert mod._GEN_CLAIM_EN_RE.search("generated by: gpt-4"), "by 后标点必须放行"
    assert mod._GEN_CLAIM_EN_RE.search("generated by llama-4"), "原空格形态不得连坐"
    assert not mod._GEN_CLAIM_EN_RE.search("generated byte order mark"), "`byte` 不是 `by` —— 词边界必须挡住"
    assert not mod._GEN_CLAIM_EN_RE.search("generated by"), "光一句没有主语不算断言"
    assert mod._norm_guard_line("Generated by\u200bGPT-4") == "generated by gpt-4", (
        "零宽必须换成空格而非删除，否则 by 与 GPT 粘连、词边界照样认不出"
    )

    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "长模型名.md", f"---\nnote: 本文由 {long_name} 生成\n---\n", age_days=9)
    mk(inbox / "英文冒号.md", "---\nnote: Generated by: GPT-4\n---\n", age_days=8)
    mk(inbox / "英文零宽.md", "---\nnote: Generated by\u200bGPT-4\n---\n", age_days=7)
    # 正向对照: 白名单键 + 无正文 → 仍 C3 建议删（护栏不得吞掉存量判据）
    mk(inbox / "纯空骨架.md", "---\ntitle: t\ntags: x\n---\n\n# 只有标题\n", age_days=6)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["items"], "items 为空则本门恒真 = 假绿"
    for name in ("长模型名.md", "英文冒号.md", "英文零宽.md"):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert it["confident"] is False, name
        assert it["target_hint"] is None and it["nomination_type"] is None, name
        assert it["uncertain_reason"], name
        # ⛔ 信号归属：必须是**生成断言结构**接住的。这三份的键都是 `note`，
        # 不在白名单里，兜底同样能接住 —— 不锁信号就测不到骨架那一层。
        assert "生成断言结构" in it["uncertain_reason"], f"{name} 未由生成断言结构接住: {it['uncertain_reason']}"
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_duplicate_frontmatter_key_does_not_mask_source(tmp_path):
    """⛔ round-2 审查 BLOCKER: `frontmatter_map` 用 `setdefault` 只留**首值**，

        ---
        doi:
        doi: 10.1000/hidden
        ---

    折叠后只剩一个空值，所有基于 `fm.items()` 的护栏信号全扫不到那个 DOI ——
    同形 `url:` 反例同时穿透 C3 与 C4 两个出口。护栏改扫 `frontmatter_pairs`
    的全量键值对；判据侧的首值语义不动。
    """
    mod = load_module()
    pairs = mod.frontmatter_pairs(["doi:", "doi: 10.1000/hidden"])
    assert pairs == [("doi", ""), ("doi", "10.1000/hidden")], pairs
    assert mod.frontmatter_map(["doi:", "doi: 10.1000/hidden"]) == {"doi": ""}, (
        "判据侧首值语义必须保持不动 —— 改它是有后果的行为变更"
    )

    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    body = "这份正文和库里那份一字不差。\n第二行也相同。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(inbox / "重复DOI键.md", "---\ndoi:\ndoi: 10.1000/hidden\n---\n", age_days=9)
    mk(inbox / "重复URL键.md", "---\nurl:\nurl: https://example.test/hidden\n---\n", age_days=8)
    mk(
        inbox / "重复DOI重复件.md",
        "---\ndoi:\ndoi: 10.1000/dup-hidden\n---\n" + body,
        age_days=7,
    )
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=6)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["items"], "items 为空则本门恒真 = 假绿"
    for name, frag in (
        ("重复DOI键.md", "10.1000/hidden"),
        ("重复URL键.md", "example.test/hidden"),
        ("重复DOI重复件.md", "10.1000/dup-hidden"),
    ):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert it["confident"] is False, name
        r = it["uncertain_reason"] or ""
        assert frag in r, r
        # ⛔ 信号归属：兜底 reason 也会把值原样打出来，`frag in r` 单独不够判别。
        assert ("DOI 来源标识" in r) or ("来源 URL" in r), f"{name} 未由来源族接住: {r}"
        assert "既不认识这个键" not in r, f"{name} 落到了白名单兜底: {r}"
    dup = item_by_name(data, "重复DOI重复件.md")
    assert dup["exact_duplicate_of"] == "节点/库内正本.md", "C4 出口也要拦，且证据留痕"
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"


def test_unknown_nonempty_frontmatter_value_blocks_c3(tmp_path):
    """⛔ round-2 审查 HIGH: `citation: ISBN 978-7-111-54742-6` 不沾 URL 也不沾
    DOI，此前所有来源护栏都在**枚举危险键名/值形态**（fail-open），漏一个就是
    一条确定删除的路径。方向反转为 fail-closed: 白名单(`_HARMLESS_FM_KEYS`)之外
    的任何**非空** frontmatter 值都算未消化信息。

    两种漏判后果不对称——漏一个白名单项只是多落一次「拿不准」，漏一个来源键名
    是把用户材料确定删掉——所以默认值必须站在「拦住」那一侧。
    """
    mod = load_module()
    for k in ("title", "tags", "created", "aliases"):
        assert k in mod._HARMLESS_FM_KEYS, f"{k} 属常见无害元数据，不放行会毁掉 C3 召回"
    for k in ("citation", "source", "doi", "generator", "type", "status"):
        assert k not in mod._HARMLESS_FM_KEYS, f"{k} 可能承载独有信息，不得放行"

    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "ISBN来源.md", "---\ncitation: ISBN 978-7-111-54742-6\n---\n", age_days=9)
    mk(inbox / "馆藏号.md", "---\nshelfmark: TP311.13/K92-3\n---\n", age_days=8)
    # C4 出口同样要拦
    body = "这份正文和库里那份一字不差。\n第二行也相同。\n"
    mk(vault / "节点" / "库内正本.md", body, age_days=40)
    mk(inbox / "ISBN重复件.md", "---\ncitation: ISBN 978-7-111-11111-1\n---\n" + body, age_days=7)
    # ⛔ 正向对照(验伪锚): 全是白名单键 → 仍 C3 建议删。白名单若被写空，本条会红。
    mk(
        inbox / "纯白名单骨架.md",
        "---\ntitle: t\ntags: a\ncreated: 2026-01-01\naliases: b\n---\n\n# 只有标题\n",
        age_days=6,
    )
    # 正向对照: 空值的非白名单键不触发（「非空」是条件的一半）
    mk(inbox / "空值未知键.md", "---\ncitation:\n---\n\n# 只有标题\n", age_days=5)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["items"], "items 为空则本门恒真 = 假绿"
    for name, frag in (
        ("ISBN来源.md", "978-7-111-54742-6"),
        ("馆藏号.md", "TP311.13/K92-3"),
        ("ISBN重复件.md", "978-7-111-11111-1"),
    ):
        it = item_by_name(data, name)
        assert it["verdict"] != "建议删", f"{name} 被建议删了: {it['basis']}"
        assert it["criterion"] == "C6_undecided", name
        assert it["confident"] is False, name
        assert it["target_hint"] is None and it["nomination_type"] is None, name
        r = it["uncertain_reason"] or ""
        assert frag in r, r
        # ⛔ 信号归属：ISBN / 馆藏号不沾 URL 也不沾 DOI，必须**正好**由白名单兜底
        # 接住 —— 本门是这条防线唯一的门，锁不住归属就等于没锁。
        assert "既不认识这个键" in r, f"{name} 未由白名单兜底接住: {r}"
    assert item_by_name(data, "ISBN重复件.md")["exact_duplicate_of"] == "节点/库内正本.md"
    for name in ("纯白名单骨架.md", "空值未知键.md"):
        ctrl = item_by_name(data, name)
        assert ctrl["criterion"] == "C3_empty_or_skeleton", f"{name}: {ctrl['basis']}"
        assert ctrl["verdict"] == "建议删", name


def test_schema_v1_full_key_sets_are_frozen(tmp_path):
    """⛔ round-2 审查 MEDIUM: `test_schema_version_frozen_at_one` 只锁
    `schema_version`/`id_namespace`/disclaimer —— 删改大多数 top/item/nested 键
    仍能保持它绿。schema v1 是**冻结**契约，键集合必须整体上锁。

    期望值取自 round-2 审查报告 §二.3 实测清单（独立来源，不是从本次输出反抄
    —— 自抄期望值等于让门给自己签字，见 reference_gate_design_pitfalls）。
    """
    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "a.md", "# A\n\n正文内容一。\n正文内容二。\n", age_days=3)
    mk(inbox / "b.md", "---\nsource: https://x.test/p\n---\n\n正文。\n正文二。\n", age_days=2)
    (vault / "Sleeping").mkdir(exist_ok=True)
    mk(vault / "Sleeping" / "s.md", "---\nslept_at: 2026-07-01\n---\n\n睡着的。\n", age_days=40)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["schema_version"] == 1
    assert data["items"], "items 为空则 item_keys 断言恒真 = 假绿"

    expected_top = {
        "corpus",
        "criteria_order",
        "generator",
        "id_namespace",
        "id_stability",
        "inbox_dir",
        "inbox_exists",
        "inventory",
        "items",
        "label",
        "last_cleanup",
        "last_cleanup_note",
        "near_dup_scan",
        "not_executed_disclaimer",
        "now",
        "now_local",
        "now_utc",
        "receipt",
        "schema_version",
        "sleeping",
        "vault_fingerprint",
        "verdict_vocabulary",
    }
    expected_item = {
        "age_days",
        "ask",
        "basis",
        "confident",
        "conflicts",
        "criterion",
        "exact_duplicate_of",
        "exact_duplicate_others",
        "index",
        "mtime_local",
        "mtime_utc",
        "name",
        "near_duplicates",
        "nomination_type",
        "rel_path",
        "size_bytes",
        "stable_id",
        "target_hint",
        "text_readable",
        "type_uncertain",
        "uncertain_reason",
        "verdict",
    }
    expected_nested = {
        "corpus": {
            "file_cap",
            "files_indexed",
            "files_scanned",
            "skipped_empty_body",
            "skipped_symlink",
            "skipped_unreadable",
            "truncated",
        },
        "inventory": {
            "batch_max",
            "batch_rule",
            "batch_size",
            "deferred",
            "over_budget",
            "skipped",
            "total",
        },
        "sleeping": {
            "alert_threshold_days",
            "count",
            "dir",
            "exists",
            "items",
            "oldest_days",
            "over_30d_count",
            "skipped",
        },
        "near_dup_scan": {
            "body_char_cap",
            "compared_pairs",
            "length_prefilter_ratio",
            "note",
            "ratio_threshold",
            "skipped_length_prefilter",
            "skipped_oversize",
            "top_n_reported",
        },
        "verdict_vocabulary": {
            "all",
            "card_enumerated",
            "human_only",
            "human_only_note",
            "reachable_by_engine",
        },
    }
    assert set(data) == expected_top, f"顶层键集合漂移: {set(data) ^ expected_top}"
    for it in data["items"]:
        assert set(it) == expected_item, f"item 键集合漂移: {set(it) ^ expected_item}"
    for section, want in expected_nested.items():
        got = set(data[section])
        assert got == want, f"{section} 键集合漂移: {got ^ want}"


def test_nbsp_heading_narrowing_locks_each_consumer(tmp_path):
    """⛔ round-2 审查 LOW: NBSP 门只直锁正则，`_HEADING_RE` 的三处消费面
    (`has_substantive_content` / `skeleton_note` / `dup_body`) 仅由端到端间接覆盖。
    本门对三处各下一条纯函数断言 —— 未来任一消费点改口径会当场红。
    """
    mod = load_module()
    nbsp_line = "#\u00a0keep\n"
    tab_line = "#\tonly heading\n"

    # ① has_substantive_content：NBSP 行是正文，制表符行是标题（无正文）
    assert mod.has_substantive_content(nbsp_line) is True
    assert mod.has_substantive_content(tab_line) is False

    # ② skeleton_note：NBSP 行不得被计入「标题 N 行」
    note_nbsp = mod.skeleton_note(nbsp_line, len(nbsp_line.encode()))
    assert "标题 0 行" in note_nbsp, note_nbsp
    note_tab = mod.skeleton_note(tab_line, len(tab_line.encode()))
    assert "标题 1 行" in note_tab, note_tab

    # ③ dup_body：标题不进比对，故 NBSP 行必须**留在**归一化正文里
    assert mod.dup_body(nbsp_line) == "#\u00a0keep", mod.dup_body(nbsp_line)
    assert mod.dup_body(tab_line) == "", mod.dup_body(tab_line)
    # 连带：两份只差「井号后是 NBSP 还是制表符」的文件不得被判逐字相等
    assert mod.dup_body(nbsp_line) != mod.dup_body(tab_line)


def test_zero_width_split_marker_still_reads_as_ai_suspect(tmp_path):
    """⛔ round-2 负控 M-ZEROWIDTH 照出的**不承重层**，本门是它唯一的裁判。

    回退 `_norm_guard_line` 后套件一门都不红 —— 因为 `Generated by<ZWSP>GPT-4`
    在旧归一下**已经**命中生成骨架（骨架里的非词字符段/非句读字符类都吃零宽），
    一条修法顺手覆盖了另一条。`_norm_guard_line` 真正承重的只有 `raw_ai_marker`:
    零宽插在**标记表项中间**时（`Generated by<ZWSP>AI Lab`），不剥零宽就匹配不到
    表项，ai_suspect 信号哑火，材料改由靠后的 gen_claim 接住。

    ⚠️ 如实声明本门测的是**理由质量**不是安全: 两种情况材料都不会被删，
    差别只在 uncertain_reason 说的是「疑似 AI 自述」还是「生成断言结构」。
    留着这一层是因为前者对人更有用 —— 但不写成安全防线，也就不能假装它是。
    """
    mod = load_module()
    zw = "\u200b"

    # 纯函数半边: 零宽切断表项时，只有护栏归一能还原出表项
    def _raw_hit(line, norm_fn):
        n = norm_fn(line)
        return next((o for nm, o in zip(mod._AI_MARKERS_NORM, mod.AI_MARKERS) if nm in n), None)

    line = f"note: Generated by{zw}AI Lab"
    assert _raw_hit(line, mod._norm_ai_line) is None, "旧归一本就认不出（这是本门的前提）"
    assert _raw_hit(line, mod._norm_guard_line) == "Generated by AI"
    # C2 判据不得被这一层带宽：确定归档面必须原地不动
    assert mod.find_ai_marker(line) is None, "护栏加宽不得顺带扩大 C2 确定提名面"

    vault, out = base_vault(tmp_path)
    inbox = vault / "_待处理"
    mk(inbox / "零宽切断表项.md", f"---\nnote: Generated by{zw}AI Lab\n---\n", age_days=6)
    mk(inbox / "纯空骨架.md", "---\ntitle: t\n---\n\n# 只有标题\n", age_days=5)

    assert run_cli(vault, out).returncode == 0
    data = load_json(out)
    assert data["items"], "items 为空则本门恒真 = 假绿"
    it = item_by_name(data, "零宽切断表项.md")
    assert it["verdict"] != "建议删", it["basis"]
    assert it["criterion"] == "C6_undecided"
    assert it["confident"] is False
    # ⛔ 信号归属就是本门的全部判别力: 回退护栏归一后这里会变成「生成断言结构」
    r = it["uncertain_reason"] or ""
    assert "疑似 AI 生成自述" in r, f"未由 ai_suspect 接住（护栏归一没起作用）: {r}"
    skeleton = item_by_name(data, "纯空骨架.md")
    assert skeleton["criterion"] == "C3_empty_or_skeleton"
    assert skeleton["verdict"] == "建议删"
