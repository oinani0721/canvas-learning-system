"""G5-3 — 拆分稳定 ID 与 diff 契约裁判 (BATCH-2026-08-29-第六批 / CARD-G5-3)。

被测物: canvas-vault/.claude/skills/board-split/scripts/split_preview.py
(G5-2 交付的只读 preview 引擎, 本卡在其上做**加性**升级 schema_version 1→2)。

分层稳定 ID 设计 (本裁判钉死的契约):
  L1 身份键 (抗行号漂移) = (来源文件相对路径, clean_heading+NFC 归一后的标题路径,
     同路径出现序号 occurrence, 候选来源形态 basis) → 长度前缀编码 → sha256 → `bsa1-<16hex>`
  L2 内容指纹 (供 changed 判定) = 小节 span (rstrip / 丢空行 / NFC；含 fence 与 HTML 注释，
     不含 frontmatter / AUTO-GENERATED / Recent Activity 等机器生成段) → `cf1-<16hex>`

裁判覆盖 (卡片 (d) 钦定六类 + 契约面):
  1. 正文微调 → 同 stable_id, diff 判 changed(reason=content)
  2. 顺序调换 → 同 stable_id, diff 判 moved (最小移动集, 精确钉死集合)
  3. 行号漂移 → 同 stable_id, diff 判 unchanged (且断言 line_start 确实位移了)
  4. 改标题 → **新 stable_id + removed+added** —— ⚠ 这是**设计取舍**不是缺陷:
     引擎不做相似度改名识别 (那要引入非确定性), 标题实词一变即断 provenance,
     如实报两条; 边界清单见 docs/design/split-stable-id-contract.md §不稳定面
  5. 重名 — (a) 同文件同标题路径的两个小节靠 occurrence 分开成两个不同 ID
           (b) resolved_name 因 节点/ 池新增同名而改 → diff 判 changed(reason=name)
  6. 中文 NFC-NFD 归一 → 同 stable_id
  外加: schema v2 加性 (v1 字段清单逐个钉死) / diff 输入守卫 (拒 v1、拒跨板) /
        diff 二跑逐字节相等 / live ≥2 真实板两跑 stable_id 全等且 live 树零改动

fixtures 全部在 tmp_path 程序化构造 (NFD 进 git 会被平台归一化搅浑)。
⛔ 本目录禁建 conftest.py —— 所有 helper 就地定义。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "canvas-vault" / ".claude" / "skills" / "board-split" / "scripts" / "split_preview.py"

#: live vault (只读取证面) —— 不存在则跳过, 绝不构造替身冒充 live
LIVE_VAULT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault")
LIVE_BOARDS = ("CS188 lecture 2", "特征值与特征向量")

STABLE_ID_PREFIX = "bsa1-"
FINGERPRINT_PREFIX = "cf1-"

#: G5-2 (schema v1) 已有的候选字段 —— v2 必须**逐个**保留 (加性升级硬门)
V1_CANDIDATE_FIELDS = (
    "index",
    "suggested_name",
    "resolved_name",
    "name_conflict",
    "conflict_with",
    "conflict_in_preview",
    "conflict_unresolvable",
    "source_anchor",
    "derived_overlap",
    "basis",
)
V1_TOP_FIELDS = (
    "schema_version",
    "generator",
    "board",
    "board_file",
    "board_sha256",
    "sources",
    "board_members",
    "existing_node_pool_count",
    "scaffold_only",
    "scaffold_note",
    "candidates",
    "scale_gate",
    "not_executed_disclaimer",
)


def load_module():
    if not SCRIPT.exists():
        pytest.fail(f"被测脚本不存在: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("split_preview_g53", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(*args: str) -> subprocess.CompletedProcess:
    if not SCRIPT.exists():  # ⛔ 防「脚本不存在 → rc≠0 → 拒绝类断言假绿」
        pytest.fail(f"被测脚本不存在: {SCRIPT}")
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=180)


def run_preview(vault: Path, board: str, out_dir: Path, *extra: str) -> subprocess.CompletedProcess:
    return _run("--vault", str(vault), "--board", board, "--out-dir", str(out_dir), *extra)


def run_diff(old_json: Path, new_json: Path, out_dir: Path) -> subprocess.CompletedProcess:
    return _run("--diff", str(old_json), str(new_json), "--out-dir", str(out_dir))


# ────────────────────────── fixture 构造器 ──────────────────────────

BODY1 = "反射代理只看当前感知就决定行动，不保存历史也不预测未来，是最简单的一类代理。"
BODY2 = "第二行正文：代理函数把感知历史映射到行动，这是分析一切代理行为的数学起点。"
BODY_ALT = "第二行正文（微调版）：代理函数把感知历史映射到行动，这是分析代理的数学起点。"


def section(heading: str, body: list[str] | None = None, level: int = 2) -> str:
    body = body if body is not None else [BODY1, BODY2]
    return "#" * level + f" {heading}\n\n" + "\n".join(body) + "\n\n"


def board_doc(sections: list[str], pad_lines: int = 0) -> str:
    """板文件全文。pad_lines 只往 frontmatter 里塞行 —— frontmatter 属剥离段,
    塞行只造成**纯行号位移**, 不改任何小节内容 (行号漂移 fixture 的构造前提)。"""
    fm = ["---", "type: whiteboard"]
    fm += [f"pad_{i}: x" for i in range(pad_lines)]
    fm += ["---", ""]
    return "\n".join(fm) + "\n# 主板\n\n" + "".join(sections)


def make_vault(tmp_path: Path, board: str, doc: str, nodes: tuple[str, ...] = (), tag: str = "v") -> Path:
    vault = tmp_path / f"vault-{tag}"
    for d in ("原白板", "节点", "outputs"):
        (vault / d).mkdir(parents=True, exist_ok=True)
    (vault / "原白板" / f"{board}.md").write_text(doc, encoding="utf-8")
    for n in nodes:
        (vault / "节点" / f"{n}.md").write_text(f"# {n}\n", encoding="utf-8")
    return vault


def preview(tmp_path: Path, board: str, doc: str, tag: str, nodes: tuple[str, ...] = ()) -> tuple[dict, Path]:
    """构板 → 跑 preview → 返回 (JSON dict, JSON 路径)。"""
    vault = make_vault(tmp_path, board, doc, nodes=nodes, tag=tag)
    out = tmp_path / f"out-{tag}"
    r = run_preview(vault, board, out)
    assert r.returncode == 0, f"preview 失败: {r.stderr or r.stdout}"
    p = out / f"split-preview-{board}.json"
    return json.loads(p.read_text(encoding="utf-8")), p


def preview_in(vault: Path, board: str, out: Path) -> tuple[dict, Path]:
    """在**已存在的** vault 上跑 preview (用于两跑之间改动 节点/ 池的场景)。"""
    r = run_preview(vault, board, out)
    assert r.returncode == 0, f"preview 失败: {r.stderr or r.stdout}"
    p = out / f"split-preview-{board}.json"
    return json.loads(p.read_text(encoding="utf-8")), p


def diff_of(tmp_path: Path, old_json: Path, new_json: Path, tag: str = "d") -> dict:
    out = tmp_path / f"diff-{tag}"
    r = run_diff(old_json, new_json, out)
    assert r.returncode == 0, f"diff 失败: {r.stderr or r.stdout}"
    board = json.loads(new_json.read_text(encoding="utf-8"))["board"]
    return json.loads((out / f"split-diff-{board}.json").read_text(encoding="utf-8"))


def ids_by_name(data: dict) -> dict[str, str]:
    return {c["resolved_name"]: c["stable_id"] for c in data["candidates"]}


def states(diff: dict) -> dict[str, str]:
    """stable_id → state (仅四态 entries; unchanged 单列在 diff['unchanged'])。"""
    return {e["stable_id"]: e["state"] for e in diff["entries"]}


# ══════════════════════════ 0 · stable_id 形态与命名空间 ══════════════════════════


class TestStableIdShape:
    def test_prefix_namespace_and_basis(self, tmp_path):
        data, _ = preview(tmp_path, "板A", board_doc([section("反射代理"), section("理性代理")]), "a")
        assert data["schema_version"] == 2
        assert data["stable_id_namespace"] == "split-anchor/v1"
        # 与 board_manifest_service.ID_STABILITY="basename_v1_will_upgrade_in_1_5" 分属两层,
        # 自陈值必须不同 —— 防两套 ID 互相冒充
        assert data["id_stability"] == "split_anchor_v1"
        assert data["id_stability"] != "basename_v1_will_upgrade_in_1_5"
        assert len(data["candidates"]) == 2
        seen = set()
        for c in data["candidates"]:
            assert c["stable_id"].startswith(STABLE_ID_PREFIX)
            assert len(c["stable_id"]) == len(STABLE_ID_PREFIX) + 16
            assert c["content_fingerprint"].startswith(FINGERPRINT_PREFIX)
            b = c["stable_id_basis"]
            assert b["namespace"] == "split-anchor/v1"
            assert b["file"] == c["source_anchor"]["file"]
            assert b["occurrence"] == 1
            assert isinstance(b["heading_path_normalized"], list) and b["heading_path_normalized"]
            # ⛔ 身份键里不得含任何行号 (抗行号漂移的结构性保证)
            assert "line" not in json.dumps(b, ensure_ascii=False)
            seen.add(c["stable_id"])
        assert len(seen) == 2, "同板不同小节必须拿到不同 stable_id"

    def test_stable_id_is_pure_function_of_basis(self, tmp_path):
        """stable_id 必须能由 basis 三元组**独立复算** —— 契约可被第三方验证。"""
        mod = load_module()
        data, _ = preview(tmp_path, "板A", board_doc([section("反射代理")]), "b")
        c = data["candidates"][0]
        b = c["stable_id_basis"]
        assert (
            mod.compute_stable_id(b["file"], b["heading_path_normalized"], b["occurrence"], b["basis"])
            == c["stable_id"]
        )
        assert b["basis"] == c["basis"], "basis 既进身份键, 就必须在 basis 字典里可复算"


class TestSchemaV2Additive:
    def test_all_v1_fields_survive(self, tmp_path):
        data, _ = preview(tmp_path, "板A", board_doc([section("反射代理")]), "c")
        for f in V1_TOP_FIELDS:
            assert f in data, f"v2 丢了 v1 顶层字段: {f}"
        for c in data["candidates"]:
            for f in V1_CANDIDATE_FIELDS:
                assert f in c, f"v2 丢了 v1 候选字段: {f}"
            assert set(c["source_anchor"]) == {"file", "line_start", "line_end", "heading_path"}


# ══════════════════════════ 1 · 正文微调 → 同 ID + changed ══════════════════════════


class TestContentEdit:
    def test_body_edit_keeps_id_and_reports_changed(self, tmp_path):
        old_doc = board_doc([section("反射代理"), section("理性代理")])
        new_doc = board_doc([section("反射代理"), section("理性代理", [BODY1, BODY_ALT])])
        old, op = preview(tmp_path, "板A", old_doc, "old1")
        new, np_ = preview(tmp_path, "板A", new_doc, "new1")
        assert ids_by_name(old) == ids_by_name(new), "正文微调不得改变 stable_id"

        d = diff_of(tmp_path, op, np_, "1")
        target = ids_by_name(new)["理性代理"]
        assert states(d) == {target: "changed"}
        e = [x for x in d["entries"] if x["stable_id"] == target][0]
        assert e["change_reasons"] == ["content"]
        assert e["old"]["content_fingerprint"] != e["new"]["content_fingerprint"]
        assert e["moved"] is False
        assert d["summary"] == {"added": 0, "changed": 1, "removed": 0, "moved": 0, "unchanged": 1}


# ══════════════════════════ 2 · 顺序调换 → 同 ID + moved ══════════════════════════


class TestReorder:
    def test_swap_keeps_ids_and_reports_minimal_move_set(self, tmp_path):
        """⚠ 契约声明: moved = **最小移动集** (LCS 补集)。交换 B/C 只标记 C 一条,
        B 作为 LCS 锚点保持原位 —— 这是最小移动集的定义使然, 不是漏判。
        (少报优于过报: 秩比较法会把「把末项拖到最前」报成全员 moved, 信号即失效。)"""
        a, b, c = section("反射代理"), section("理性代理"), section("搜索问题")
        old, op = preview(tmp_path, "板A", board_doc([a, b, c]), "old2")
        new, np_ = preview(tmp_path, "板A", board_doc([a, c, b]), "new2")
        assert ids_by_name(old) == ids_by_name(new), "调序不得改变 stable_id"
        assert [x["resolved_name"] for x in new["candidates"]] == ["反射代理", "搜索问题", "理性代理"]

        d = diff_of(tmp_path, op, np_, "2")
        assert states(d) == {ids_by_name(new)["搜索问题"]: "moved"}
        e = d["entries"][0]
        assert e["change_reasons"] == []
        assert (e["old"]["index"], e["new"]["index"]) == (3, 2)
        assert (e["old"]["rank"], e["new"]["rank"]) == (2, 1)  # 共同集内 0-based 秩
        assert d["summary"]["moved"] == 1 and d["summary"]["unchanged"] == 2


class TestFingerprintCoverage:
    """契约 §3.1: 指纹**故意不复用**候选判定的剥离掩码。

    这是本卡最容易被做成「掩饰」的一处 —— 若指纹跟着剥离掩码走, 小节内代码块整块
    改写时指纹纹丝不动, diff 会一本正经地报「无变化」而实际全变了。
    这条测试就是那句声称的硬门: 代码块与 HTML 注释的改动**必须**被感知,
    同时 stable_id 必须不动（改的是内容不是身份）。
    """

    @staticmethod
    def _doc(code: str, comment: str) -> str:
        return (
            "---\ntype: whiteboard\n---\n\n# 主板\n\n## 甲小节\n\n"
            f"{BODY1}\n{BODY2}\n\n```python\n{code}\n```\n\n<!-- {comment} -->\n\n"
        )

    def test_fence_and_comment_edits_are_seen_by_fingerprint(self, tmp_path):
        base, _ = preview(tmp_path, "板A", self._doc("print(1)", "备注一"), "fp-a")
        fence, _ = preview(tmp_path, "板A", self._doc("print(999)", "备注一"), "fp-b")
        comment, _ = preview(tmp_path, "板A", self._doc("print(1)", "备注二"), "fp-c")
        b, f, c = base["candidates"][0], fence["candidates"][0], comment["candidates"][0]

        assert b["stable_id"] == f["stable_id"] == c["stable_id"], "改内容不该动身份"
        assert b["content_fingerprint"] != f["content_fingerprint"], (
            "⛔ 代码块整块改写必须被指纹感知 —— 否则 diff 报「无变化」就是掩饰（契约 §3.1）"
        )
        assert b["content_fingerprint"] != c["content_fingerprint"], "⛔ HTML 注释改动同样必须被指纹感知（契约 §3.1）"


class TestLcsMovedSemantics:
    """契约 §8.4 那句「选 LCS 而不选秩比较法」的量化依据 —— 直接对 _lcs_keep 单测。

    文档里写「秩比较会把末项拖到最前报成全员 moved」是一句**可证伪的定量声称**,
    不钉进测试就只是个说法。这里把两种算法在同一组输入上的输出并排锁死。
    """

    CASES = [
        (list("ABC"), list("ACB"), ["C"], ["C", "B"], "相邻交换"),
        (list("ABCD"), list("DABC"), ["D"], ["D", "A", "B", "C"], "末项拖到最前"),
        (list("ABCD"), list("ABCD"), [], [], "不动"),
    ]

    def test_lcs_vs_rank_comparison(self):
        mod = load_module()
        for old, new, want_lcs_moved, want_rank_moved, name in self.CASES:
            keep = mod._lcs_keep(old, new)
            lcs_moved = [x for x in new if x not in keep]
            ranks = {x: (old.index(x), new.index(x)) for x in new}
            rank_moved = [x for x in new if ranks[x][0] != ranks[x][1]]
            assert lcs_moved == want_lcs_moved, f"{name}: LCS 补集应为 {want_lcs_moved}, 实得 {lcs_moved}"
            assert rank_moved == want_rank_moved, f"{name}: 秩比较法对照值漂了（文档依据失效）"

    def test_lcs_is_deterministic_across_repeated_calls(self):
        """tie-break 必须确定 —— 同输入多次调用结果恒等（moved 报告的可重现性靠它）。"""
        mod = load_module()
        old, new = list("ABCDEF"), list("ADBECF")
        first = sorted(mod._lcs_keep(old, new))
        for _ in range(5):
            assert sorted(mod._lcs_keep(old, new)) == first


# ══════════════════════════ 3 · 行号漂移 → 同 ID + 无变化 ══════════════════════════


class TestLineDrift:
    def test_line_shift_is_not_a_change(self, tmp_path):
        secs = [section("反射代理"), section("理性代理")]
        old, op = preview(tmp_path, "板A", board_doc(secs), "old3")
        new, np_ = preview(tmp_path, "板A", board_doc(secs, pad_lines=5), "new3")
        assert ids_by_name(old) == ids_by_name(new)
        # 构造前提: 行号确实漂移了 (否则这条测试是空转)
        for o, n in zip(old["candidates"], new["candidates"], strict=True):
            assert n["source_anchor"]["line_start"] == o["source_anchor"]["line_start"] + 5
            assert n["source_anchor"]["line_end"] == o["source_anchor"]["line_end"] + 5
        assert old["board_sha256"] != new["board_sha256"]  # 文件本体确实变了

        d = diff_of(tmp_path, op, np_, "3")
        assert d["entries"] == []
        assert d["summary"] == {"added": 0, "changed": 0, "removed": 0, "moved": 0, "unchanged": 2}
        assert {u["stable_id"] for u in d["unchanged"]} == set(ids_by_name(new).values())


# ══════════════════════════ 4 · 改标题 → 新 ID (设计取舍) ══════════════════════════


class TestHeadingRename:
    def test_rename_yields_new_id_removed_plus_added(self, tmp_path):
        """⚠ 设计取舍 (不是缺陷, 契约文档 §不稳定面 #1 已声明):
        标题实词一变 → 换 ID → 报 removed + added, provenance 在此断开。
        引擎**不做**相似度改名识别 —— 那要引入阈值与非确定性, 与「同输入二跑
        逐字节相等」硬门冲突。改名后如需保 provenance, 由 G5-10 侧人工确认承接。"""
        old, op = preview(tmp_path, "板A", board_doc([section("反射代理"), section("理性代理")]), "old4")
        new, np_ = preview(tmp_path, "板A", board_doc([section("反射代理"), section("理性代理体")]), "new4")
        old_id, new_id = ids_by_name(old)["理性代理"], ids_by_name(new)["理性代理体"]
        assert old_id != new_id

        d = diff_of(tmp_path, op, np_, "4")
        assert states(d) == {old_id: "removed", new_id: "added"}
        assert d["summary"] == {"added": 1, "changed": 0, "removed": 1, "moved": 0, "unchanged": 1}
        assert "改标题" in d["tradeoff_note"] and "removed" in d["tradeoff_note"]

    def test_ancestor_rename_changes_whole_subtree(self, tmp_path):
        """改**祖先**标题 → 整棵子树换 ID (同属声明的不稳定面 #2)。"""
        sub = section("子小节", level=3)
        old, _ = preview(tmp_path, "板A", board_doc([section("父章节"), sub]), "old4b")
        new, _ = preview(tmp_path, "板A", board_doc([section("父章节改"), sub]), "new4b")
        old_sub = [c for c in old["candidates"] if c["resolved_name"] == "子小节"][0]
        new_sub = [c for c in new["candidates"] if c["resolved_name"] == "子小节"][0]
        assert old_sub["stable_id_basis"]["heading_path_normalized"] == ["主板", "父章节", "子小节"]
        assert new_sub["stable_id_basis"]["heading_path_normalized"] == ["主板", "父章节改", "子小节"]
        assert old_sub["stable_id"] != new_sub["stable_id"]

    def test_number_prefix_and_timestamp_do_not_change_id(self, tmp_path):
        """标题编号 / 时间戳标记变化**不**换 ID —— clean_heading 已吸收 (稳定面)。
        真实讲义板重编号是高频操作, 不吸收就等于稳定 ID 名存实亡。"""
        old, _ = preview(tmp_path, "板A", board_doc([section("2.1 反射代理 [05:50]()")]), "old4c")
        new, _ = preview(tmp_path, "板A", board_doc([section("3.4 反射代理 [11:02]()")]), "new4c")
        assert old["candidates"][0]["stable_id"] == new["candidates"][0]["stable_id"]
        assert old["candidates"][0]["stable_id_basis"]["heading_path_normalized"] == ["主板", "反射代理"]


# ══════════════════════════ 5 · 重名 ══════════════════════════


class TestDuplicateAndNameConflict:
    def test_duplicate_heading_path_split_by_occurrence(self, tmp_path):
        """同文件同标题路径的两个小节 —— occurrence 序号把它们分成两个 ID,
        否则候选↔ID 双射破裂, diff 会互相吞掉。"""
        doc = board_doc([section("例题"), section("例题", [BODY1, BODY_ALT])])
        data, _ = preview(tmp_path, "板A", doc, "5a")
        assert len(data["candidates"]) == 2
        c1, c2 = data["candidates"]
        assert c1["suggested_name"] == c2["suggested_name"] == "例题"
        assert (c1["resolved_name"], c2["resolved_name"]) == ("例题", "例题_2")
        assert (c1["stable_id_basis"]["occurrence"], c2["stable_id_basis"]["occurrence"]) == (1, 2)
        assert c1["stable_id"] != c2["stable_id"]
        assert c1["stable_id_basis"]["heading_path_normalized"] == c2["stable_id_basis"]["heading_path_normalized"]

    def test_pool_conflict_changes_resolved_name_and_is_reported(self, tmp_path):
        """两跑之间 节点/ 池新增同名文件 → resolved_name 由 X 变 X_2。
        内容没变但**确认创建时会落到不同文件名**, 因此必须判 changed(reason=name)。"""
        board = "板A"
        vault = make_vault(tmp_path, board, board_doc([section("反射代理")]), tag="5b")
        old, op = preview_in(vault, board, tmp_path / "out-5b-old")
        (vault / "节点" / "反射代理.md").write_text("# 反射代理\n", encoding="utf-8")
        new, np_ = preview_in(vault, board, tmp_path / "out-5b-new")

        assert old["candidates"][0]["resolved_name"] == "反射代理"
        assert new["candidates"][0]["resolved_name"] == "反射代理_2"
        assert old["candidates"][0]["stable_id"] == new["candidates"][0]["stable_id"], "重名解析不得改 stable_id"

        d = diff_of(tmp_path, op, np_, "5b")
        e = d["entries"][0]
        assert e["state"] == "changed"
        assert e["change_reasons"] == ["conflict", "name"]
        assert (e["old"]["resolved_name"], e["new"]["resolved_name"]) == ("反射代理", "反射代理_2")


# ══════════════════════════ 6 · 中文 NFC-NFD 归一 ══════════════════════════


class TestUnicodeNormalization:
    def test_nfd_heading_yields_same_stable_id(self, tmp_path):
        """纯汉字无 NFD 分解面 —— 中文笔记真正咬人的是混排的带调拼音 (macOS 落盘分解)。"""
        nfc_head = "特征值-tèzhēngzhí"
        nfd_head = unicodedata.normalize("NFD", nfc_head)
        assert nfd_head != nfc_head, "构造前提: 两种编码字节必须不同"
        a, _ = preview(tmp_path, "板A", board_doc([section(nfc_head)]), "6a")
        b, _ = preview(tmp_path, "板A", board_doc([section(nfd_head)]), "6b")
        assert a["candidates"][0]["stable_id"] == b["candidates"][0]["stable_id"]
        assert a["candidates"][0]["stable_id_basis"]["heading_path_normalized"] == ["主板", nfc_head]
        assert b["candidates"][0]["stable_id_basis"]["heading_path_normalized"] == ["主板", nfc_head]

    def test_nfd_body_does_not_change_fingerprint(self, tmp_path):
        body = ["特征值 tèzhēngzhí 是矩阵的固有量，满足 Av = λv 这条定义式，要背下来。", BODY2]
        nfd_body = [unicodedata.normalize("NFD", body[0]), body[1]]
        assert nfd_body != body
        a, _ = preview(tmp_path, "板A", board_doc([section("线代", body)]), "6c")
        b, _ = preview(tmp_path, "板A", board_doc([section("线代", nfd_body)]), "6d")
        assert a["candidates"][0]["content_fingerprint"] == b["candidates"][0]["content_fingerprint"]


# ══════════════════════════ 7 · diff 输入守卫与确定性 ══════════════════════════


class TestDiffGuards:
    def test_rejects_v1_schema_input(self, tmp_path):
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "7a")
        legacy = json.loads(p.read_text(encoding="utf-8"))
        legacy["schema_version"] = 1
        for c in legacy["candidates"]:
            c.pop("stable_id", None)
            c.pop("stable_id_basis", None)
            c.pop("content_fingerprint", None)
        old_p = tmp_path / "legacy.json"
        old_p.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
        reject_dir = tmp_path / "reject-7a"  # ⛔ 不得与 preview 的 out-<tag> 撞名, 否则零产物断言假绿
        r = run_diff(old_p, p, reject_dir)
        assert r.returncode != 0
        assert "schema_version" in (r.stdout + r.stderr)
        assert not reject_dir.exists(), "拒绝路径必须零产物"

    def test_rejects_cross_namespace_compare(self, tmp_path):
        """身份键换代（split-anchor/v1 → v2）后两代 ID 毫无可比性 —— 硬拒。
        不拒的话会产出一份「全部候选互报 removed+added」的假 diff, 读起来像整块板被重写了。
        （契约 §十 原本把这条列为「留给 v2 补」的缺口, 现已就地补上。）"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "7k")
        future = json.loads(p.read_text(encoding="utf-8"))
        # 真实的下一代产物两处都会是 v2（顶层 + 每条候选的 basis.namespace）；
        # 只改顶层会先被「basis 与顶层不一致」的交叉绑定守卫拦下, 测不到本条要测的东西。
        future["stable_id_namespace"] = "split-anchor/v2"
        for c in future["candidates"]:
            c["stable_id_basis"]["namespace"] = "split-anchor/v2"
        fp = tmp_path / "ns-v2.json"
        fp.write_text(json.dumps(future, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "out-ns"
        r = run_diff(p, fp, out)
        assert r.returncode != 0 and "stable_id_namespace" in (r.stdout + r.stderr)
        assert not out.exists(), "拒绝路径零产物"

    def test_rejects_missing_namespace(self, tmp_path):
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "7l")
        stripped = json.loads(p.read_text(encoding="utf-8"))
        stripped.pop("stable_id_namespace")
        sp = tmp_path / "ns-missing.json"
        sp.write_text(json.dumps(stripped, ensure_ascii=False), encoding="utf-8")
        r = run_diff(sp, p, tmp_path / "out-ns2")
        assert r.returncode != 0 and "stable_id_namespace" in (r.stdout + r.stderr)

    def test_rejects_cross_board_compare(self, tmp_path):
        _, pa = preview(tmp_path, "板A", board_doc([section("反射代理")]), "7b")
        _, pb = preview(tmp_path, "板B", board_doc([section("反射代理")]), "7c")
        r = run_diff(pa, pb, tmp_path / "out-7b")
        assert r.returncode != 0 and "同一块板" in (r.stdout + r.stderr)

    def test_rejects_missing_stable_id(self, tmp_path):
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "7d")
        broken = json.loads(p.read_text(encoding="utf-8"))
        broken["candidates"][0].pop("stable_id")
        bp = tmp_path / "broken.json"
        bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        r = run_diff(bp, p, tmp_path / "out-7d")
        assert r.returncode != 0 and "stable_id" in (r.stdout + r.stderr)

    def test_summary_accounting_balances_across_shapes(self, tmp_path):
        """记账恒等式: 四态 + unchanged 恰好覆盖两侧候选各一次, 不重不漏。
        对多种差异形态（纯增 / 纯删 / 改+调序混合 / 全换）逐一验算 ——
        diff 的全部价值就是这份账是准的。"""
        a, b, c, e = section("甲"), section("乙"), section("丙"), section("戊")
        shapes = [
            ([a, b], [a, b, c], "纯增"),
            ([a, b, c], [a, b], "纯删"),
            ([a, b, c], [c, section("乙", [BODY1, BODY_ALT]), a], "改+全调序"),
            ([a, b], [c, e], "全换"),
            ([a, b, c], [a, b, c], "不动"),
        ]
        for i, (old_secs, new_secs, name) in enumerate(shapes):
            _, op = preview(tmp_path, "板A", board_doc(old_secs), f"acc{i}o")
            _, np_ = preview(tmp_path, "板A", board_doc(new_secs), f"acc{i}n")
            d = diff_of(tmp_path, op, np_, f"acc{i}")
            s = d["summary"]
            n_new, n_old = len(new_secs), len(old_secs)
            assert s["added"] + s["changed"] + s["moved"] + s["unchanged"] == n_new, f"{name}: 新侧不平"
            assert s["removed"] + s["changed"] + s["moved"] + s["unchanged"] == n_old, f"{name}: 旧侧不平"
            assert len(d["entries"]) + len(d["unchanged"]) == n_new + s["removed"], f"{name}: 条目数不符"
            seen_states = {e_["stable_id"]: e_["state"] for e_ in d["entries"]}
            assert len(seen_states) == len(d["entries"]), f"{name}: 同一 stable_id 出现在多条 entry 里"
            assert not (set(seen_states) & {u["stable_id"] for u in d["unchanged"]}), (
                f"{name}: 同一候选同时进了 entries 和 unchanged"
            )

    def test_diff_is_byte_identical_on_rerun(self, tmp_path):
        _, op = preview(tmp_path, "板A", board_doc([section("反射代理"), section("理性代理")]), "7e")
        _, np_ = preview(
            tmp_path, "板A", board_doc([section("反射代理"), section("理性代理", [BODY1, BODY_ALT])]), "7f"
        )
        o1, o2 = tmp_path / "d1", tmp_path / "d2"
        assert run_diff(op, np_, o1).returncode == 0
        assert run_diff(op, np_, o2).returncode == 0
        for suffix in (".json", ".md"):
            a = (o1 / f"split-diff-板A{suffix}").read_bytes()
            b = (o2 / f"split-diff-板A{suffix}").read_bytes()
            assert a == b, f"diff 产物二跑不一致: {suffix}"

    def test_diff_md_is_human_readable(self, tmp_path):
        _, op = preview(tmp_path, "板A", board_doc([section("反射代理"), section("理性代理")]), "7g")
        _, np_ = preview(tmp_path, "板A", board_doc([section("反射代理"), section("理性代理体")]), "7h")
        out = tmp_path / "d3"
        assert run_diff(op, np_, out).returncode == 0
        md = (out / "split-diff-板A.md").read_text(encoding="utf-8")
        for word in ("新增", "内容变更", "移动", "移除", "未执行"):
            assert word in md, f"diff MD 缺少 {word}"

    def test_preview_mode_still_requires_vault_and_board(self):
        """加了 --diff 模式后, preview 模式缺参必须仍然明确拒绝 (不得静默跑空)。"""
        r = _run("--board", "板A")
        assert r.returncode != 0 and "--vault" in (r.stdout + r.stderr)

    def test_mismatched_scale_gate_raises_a_visible_warning(self, tmp_path):
        """两侧规模门阈值不同 → 被切掉的候选会伪装成 removed。
        这条坑光写进文档不够（读 diff 的人不会先翻文档）, 产物里必须当场告警。"""
        doc = board_doc([section(f"小节{i:02d}") for i in range(4)])
        vault = make_vault(tmp_path, "板A", doc, tag="sg")
        full, fp = preview_in(vault, "板A", tmp_path / "out-sg-full")
        r = run_preview(vault, "板A", tmp_path / "out-sg-cut", "--max-units", "2")
        assert r.returncode == 0
        cp = tmp_path / "out-sg-cut" / "split-preview-板A.json"
        cut = json.loads(cp.read_text(encoding="utf-8"))
        assert len(full["candidates"]) == 4 and len(cut["candidates"]) == 2

        d = diff_of(tmp_path, fp, cp, "sg")
        assert d["summary"]["removed"] == 2, "被规模门切掉的两条会显示为 removed —— 正是要告警的场景"
        blob = " ".join(d["warnings"])
        assert "规模门阈值不同" in blob, "阈值不一致必须告警"
        assert "内容变化" in blob, "必须点明「这不是内容变化」, 否则用户会误读 removed"
        assert "截断" in blob, "被截断的那一侧也要单独声明"
        out = tmp_path / "diff-sg"
        md = (out / "split-diff-板A.md").read_text(encoding="utf-8")
        assert "读这份 diff 之前先看这里" in md, "告警必须出现在人读产物的显眼处"

    def test_rejects_non_string_board(self, tmp_path):
        """board 会被拼进产物文件名 —— None / 数字必须当场拒绝, 不得 str() 成
        "None" / "123" 悄悄落盘 (自查实测过的真实缺陷, 此测试是它的回归门)。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "7i")
        base = json.loads(p.read_text(encoding="utf-8"))
        for i, (bad, tag) in enumerate(((None, "null"), (123, "int"), ("", "empty"))):
            broken = dict(base)
            broken["board"] = bad
            bp = tmp_path / f"board-bad-{i}.json"  # ⛔ 中性名: 参数不进路径
            bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
            out = tmp_path / f"reject-board-{i}"
            r = run_diff(bp, bp, out)
            assert r.returncode != 0, f"board={bad!r} 应被拒绝"
            assert "board" in (r.stdout + r.stderr)
            assert not out.exists(), f"board={bad!r} 拒绝路径必须零产物"

    def test_illegal_board_name_rejected_before_out_dir_is_created(self, tmp_path):
        """⛔ 次序门: 板名路径逃逸校验必须在建 out-dir **之前**。
        次序反了会「拒绝但已建空目录」—— 与 G5-2 Codex 三轮 H1 同型的错误,
        本条就是钉住那个次序 (先前实现确实踩了, 已修)。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "7j")
        broken = json.loads(p.read_text(encoding="utf-8"))
        broken["board"] = "../逃逸"
        bp = tmp_path / "board-escape.json"
        bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "out-board-escape"
        r = run_diff(bp, bp, out)
        assert r.returncode != 0 and "逃逸" in (r.stdout + r.stderr)
        assert not out.exists(), "拒绝路径连空目录都不该留下"


# ═══════════════ 7.5 · 契约 §4 边界清单矩阵（诚实性硬门） ═══════════════
#
# docs/design/split-stable-id-contract.md §4.1 列了 10 条「会换 ID」、§4.2 列了 10 条
# 「不换 ID」。本节把清单里**尚未被前面测试覆盖**的行逐条变成断言 —— 清单写在文档里
# 只是声明，钉进测试才是承诺。任何一条与实际不符, 要么改实现要么改文档, 不许两边打架。


def seed_board_doc(seed: str) -> str:
    """只有 Concepts 目录的脚手架板（板体零候选, 候选全部来自种子笔记）。"""
    return f"---\ntype: whiteboard\n---\n\n# 主板\n\n## Concepts\n\n- [[节点/{seed}]] — 种子 · 掌握度 — · 未考\n"


def preview_with_seed(tmp_path: Path, tag: str, seed: str, seed_doc: str) -> dict:
    vault = tmp_path / f"vault-{tag}"
    for d in ("原白板", "节点", "outputs"):
        (vault / d).mkdir(parents=True, exist_ok=True)
    (vault / "原白板" / "板A.md").write_text(seed_board_doc(seed), encoding="utf-8")
    (vault / "节点" / f"{seed}.md").write_text(seed_doc, encoding="utf-8")
    out = tmp_path / f"out-{tag}"
    r = run_preview(vault, "板A", out)
    assert r.returncode == 0, f"preview 失败: {r.stderr or r.stdout}"
    return json.loads((out / "split-preview-板A.json").read_text(encoding="utf-8"))


class TestUnstableSurface:
    """§4.1 会换 ID 的操作 —— 逐条实证「确实会换」（清单没说大话）。"""

    def test_moved_to_another_file_changes_id(self, tmp_path):
        """#3 小节搬到另一个文件 → file_rel 变 → 换 ID。
        构造上把两侧祖先标题写成**同一个词**, 隔离出「只有文件路径不同」这一个变量。"""
        sec = section("甲小节")
        in_board, _ = preview(tmp_path, "板A", "---\ntype: whiteboard\n---\n\n# 共同标题\n\n" + sec, "u3a")
        in_seed = preview_with_seed(tmp_path, "u3b", "种子", "---\ntype: concept\n---\n\n# 共同标题\n\n" + sec)
        b, s = in_board["candidates"][0], in_seed["candidates"][0]
        assert b["stable_id_basis"]["heading_path_normalized"] == s["stable_id_basis"]["heading_path_normalized"]
        assert b["content_fingerprint"] == s["content_fingerprint"]  # 内容逐字相同
        assert b["stable_id_basis"]["file"] != s["stable_id_basis"]["file"]
        assert b["stable_id"] != s["stable_id"], "跨文件搬家必须换 ID（清单 §4.1 #3）"

    def test_deleting_earlier_duplicate_shifts_occurrence(self, tmp_path):
        """#5 同名同父小节被删 → 其后同名者 occurrence 位移 → 换 ID。
        并且如实钉住后果: 幸存者**继承了**被删者的 ID（而不是拿到一个全新 ID）——
        这正是 occurrence 方案的代价, 文档 §4.1 #5 声明的就是它。"""
        dup1 = section("例题", [BODY1, BODY2])
        dup2 = section("例题", [BODY1, BODY_ALT])
        base, _ = preview(tmp_path, "板A", board_doc([dup1, dup2]), "u5a")
        after, _ = preview(tmp_path, "板A", board_doc([dup2]), "u5b")
        first_id, second_id = base["candidates"][0]["stable_id"], base["candidates"][1]["stable_id"]
        survivor = after["candidates"][0]
        assert survivor["content_fingerprint"] == base["candidates"][1]["content_fingerprint"]
        assert survivor["stable_id"] != second_id, "occurrence 位移 → 换 ID（清单 §4.1 #5）"
        assert survivor["stable_id"] == first_id, "幸存者继承 occurrence=1 的 ID —— 这是该方案如实的代价"

    def test_board_rename_changes_all_ids(self, tmp_path):
        """#6 板文件改名 → 全板换 ID。"""
        doc = board_doc([section("反射代理"), section("理性代理")])
        a, _ = preview(tmp_path, "板A", doc, "u6a")
        b, _ = preview(tmp_path, "板B", doc, "u6b")
        assert [c["content_fingerprint"] for c in a["candidates"]] == [
            c["content_fingerprint"] for c in b["candidates"]
        ]
        assert not ({c["stable_id"] for c in a["candidates"]} & {c["stable_id"] for c in b["candidates"]})

    def test_seed_whole_fallback_to_sections_changes_id(self, tmp_path):
        """#7 种子笔记从「整篇回退候选」变成有达标 ##+ 小节 → removed + added。"""
        whole = preview_with_seed(
            tmp_path, "u7a", "种子", "---\ntype: concept\n---\n\n# 讲义\n\n" + f"{BODY1}\n{BODY2}\n"
        )
        sectioned = preview_with_seed(
            tmp_path, "u7b", "种子", "---\ntype: concept\n---\n\n# 讲义\n\n" + section("子节")
        )
        assert whole["candidates"][0]["basis"] == "seed-note-whole"
        assert whole["candidates"][0]["stable_id_basis"]["heading_path_normalized"] == ["讲义"]
        assert sectioned["candidates"][0]["basis"] == "seed-note-section"
        assert sectioned["candidates"][0]["stable_id_basis"]["heading_path_normalized"] == ["讲义", "子节"]
        assert whole["candidates"][0]["stable_id"] != sectioned["candidates"][0]["stable_id"]

    def test_non_trailing_timestamp_is_not_absorbed(self, tmp_path):
        """#8 时间戳标记只在**行尾**被 clean_heading 吸收。
        不在行尾时它进身份键 → 改它就换 ID。这条边界如果不写明, 用户会以为
        「时间戳变化永远不影响 ID」—— 那是过度承诺。"""
        tail_a, _ = preview(tmp_path, "板A", board_doc([section("甲 [05:50]()")]), "u8a")
        tail_b, _ = preview(tmp_path, "板A", board_doc([section("甲 [06:50]()")]), "u8b")
        assert tail_a["candidates"][0]["stable_id"] == tail_b["candidates"][0]["stable_id"], (
            "行尾时间戳变化不该换 ID（§4.2）"
        )
        mid_a, _ = preview(tmp_path, "板A", board_doc([section("甲 [05:50]() 补充")]), "u8c")
        mid_b, _ = preview(tmp_path, "板A", board_doc([section("甲 [06:50]() 补充")]), "u8d")
        assert mid_a["candidates"][0]["stable_id"] != mid_b["candidates"][0]["stable_id"], (
            "非行尾时间戳变化会换 ID（§4.1 #8）—— 这是必须写明的边界"
        )


class TestStableSurface:
    """§4.2 不换 ID 的操作 —— 逐条实证「确实不换」（清单没说过头）。"""

    def test_trailing_whitespace_and_blank_lines_change_nothing(self, tmp_path):
        """行尾空白与空行增删: ID 不变**且指纹不变**（指纹归一化含 rstrip + 丢空行）。"""
        base, op = preview(tmp_path, "板A", board_doc([section("反射代理"), section("理性代理")]), "s1a")
        noisy_sec = "## 反射代理\n\n\n" + BODY1 + "   \n\n" + BODY2 + "\t\n\n\n"
        noisy, np_ = preview(tmp_path, "板A", board_doc([noisy_sec, section("理性代理")]), "s1b")
        assert base["candidates"][0]["stable_id"] == noisy["candidates"][0]["stable_id"]
        assert base["candidates"][0]["content_fingerprint"] == noisy["candidates"][0]["content_fingerprint"]
        d = diff_of(tmp_path, op, np_, "s1")
        assert d["entries"] == [] and d["summary"]["unchanged"] == 2

    def test_heading_level_change_keeping_ancestors_keeps_id(self, tmp_path):
        """层级调整**不改变祖先链**时 ID 不变 —— §4.1 #4 说的是「改变祖先链」才换,
        这条是它的反面锚: 只降级不换父, ID 必须稳住。"""
        a, _ = preview(tmp_path, "板A", board_doc([section("甲小节", level=2)]), "s2a")
        b, _ = preview(tmp_path, "板A", board_doc([section("甲小节", level=3)]), "s2b")
        assert a["candidates"][0]["stable_id_basis"]["heading_path_normalized"] == ["主板", "甲小节"]
        assert b["candidates"][0]["stable_id_basis"]["heading_path_normalized"] == ["主板", "甲小节"]
        assert a["candidates"][0]["stable_id"] == b["candidates"][0]["stable_id"]


# ═══════ 7.6 · 对抗审查（Codex round-1 + 6 镜头 workflow）发现的回归门 ═══════
#
# 下面每一条都对应一个**被实证复现过**的缺陷。它们不是补充覆盖率, 是防复发的门。


class TestReviewRegressions:
    def test_duplicate_seed_in_concepts_no_longer_kills_the_board(self, tmp_path):
        """审查发现: `## Concepts` 里同一份种子被列两行 → 同一文件被扫两遍 →
        四元组逐字相同 → stable_id 必撞 → 自检拒绝输出, 整块板拿不到 preview。
        相对 G5-2 这是**可用性倒退**。修法 = 源头按 NFC 去重 + sources 留痕。"""
        vault = tmp_path / "vault-dupseed"
        for d in ("原白板", "节点", "outputs"):
            (vault / d).mkdir(parents=True, exist_ok=True)
        (vault / "原白板" / "板A.md").write_text(
            "---\ntype: whiteboard\n---\n\n# 主板\n\n## Concepts\n\n"
            "- [[节点/种子]] — 种子 · 掌握度 — · 未考\n"
            "- [[节点/种子]] — 种子 · 掌握度 — · 未考\n",
            encoding="utf-8",
        )
        (vault / "节点" / "种子.md").write_text(
            "---\ntype: concept\n---\n\n# 讲义\n\n" + section("子节"), encoding="utf-8"
        )
        out = tmp_path / "out-dupseed"
        r = run_preview(vault, "板A", out)
        assert r.returncode == 0, f"重复种子不该让整块板失败: {r.stderr or r.stdout}"
        data = json.loads((out / "split-preview-板A.json").read_text(encoding="utf-8"))
        assert len(data["candidates"]) == 1, "同一份种子只该被扫一次"
        skipped = [s for s in data["sources"] if s.get("skipped")]
        assert skipped and "重复" in skipped[0]["skipped"], "被跳过的那一行必须留痕, 不能静默"

    def test_nfd_twin_seed_name_is_deduped(self, tmp_path):
        """更隐蔽的同一问题: Concepts 一行写 NFC 名、一行写 NFD 名, macOS 上指向同一文件。"""
        nfc_name = "特征值-tèzhēngzhí"
        nfd_name = unicodedata.normalize("NFD", nfc_name)
        assert nfd_name != nfc_name
        vault = tmp_path / "vault-nfdseed"
        for d in ("原白板", "节点", "outputs"):
            (vault / d).mkdir(parents=True, exist_ok=True)
        (vault / "原白板" / "板A.md").write_text(
            "---\ntype: whiteboard\n---\n\n# 主板\n\n## Concepts\n\n"
            f"- [[节点/{nfc_name}]] — 种子 · 掌握度 — · 未考\n"
            f"- [[节点/{nfd_name}]] — 种子 · 掌握度 — · 未考\n",
            encoding="utf-8",
        )
        (vault / "节点" / f"{nfc_name}.md").write_text(
            "---\ntype: concept\n---\n\n# 讲义\n\n" + section("子节"), encoding="utf-8"
        )
        r = run_preview(vault, "板A", tmp_path / "out-nfdseed")
        assert r.returncode == 0, f"NFD 孪生名不该让整块板失败: {r.stderr or r.stdout}"

    def test_fallback_name_has_no_line_number(self, tmp_path):
        """审查发现（Codex HIGH-1 + 两个镜头）: 归一化后标题为空的小节（`## .gitignore 的作用`
        首句被句读切空 / `## 一、` 被编号剥空）走 fallback 命名, 而 fallback 锚点原本含**行号**
        → 纯行号漂移就改名 → diff 报 changed(name), 与契约 §4.2「行号漂移不算变化」直接冲突。"""
        sec = section(".gitignore 的作用")
        old, op = preview(tmp_path, "板A", board_doc([sec, section("正常小节")]), "fb-a")
        new, np_ = preview(tmp_path, "板A", board_doc([sec, section("正常小节")], pad_lines=5), "fb-b")
        fb_old = [c for c in old["candidates"] if c["suggested_name"].startswith("derived-")]
        assert fb_old, "构造前提: 该标题必须真的走 fallback 命名"
        assert (
            new["candidates"][0]["source_anchor"]["line_start"] != old["candidates"][0]["source_anchor"]["line_start"]
        )
        assert [c["suggested_name"] for c in old["candidates"]] == [c["suggested_name"] for c in new["candidates"]]
        d = diff_of(tmp_path, op, np_, "fb")
        assert d["entries"] == [], f"纯行号漂移不该报任何变化, 实得 {states(d)}"

    def test_machine_generated_tail_does_not_pollute_fingerprint(self, tmp_path):
        """审查发现: 板尾的 Recent Activity / AUTO 段落在最后一条候选的 span 内
        （剥离后的标题不算标题, 前一节的 end 因而吞到 EOF）。指纹若把它算进去,
        每派生一次节点、机器刷新一次尾块, 就凭空多一条 changed(content)。"""
        head = "---\ntype: whiteboard\n---\n\n# 主板\n\n" + section("甲小节")

        def doc(activity: str) -> str:
            return head + f"## Recent Activity\n\n- {activity}\n"

        a, ap = preview(tmp_path, "板A", doc("2026-05-09T08:54:18Z: Whiteboard created"), "mg-a")
        b, bp = preview(tmp_path, "板A", doc("2026-08-30T01:02:03Z: Extracted [[节点/X]]"), "mg-b")
        assert a["candidates"][0]["source_anchor"]["line_end"] >= 10, "构造前提: span 确实吞到了尾块"
        assert a["candidates"][0]["content_fingerprint"] == b["candidates"][0]["content_fingerprint"], (
            "机器刷新的尾块不该算作用户内容变更"
        )
        assert diff_of(tmp_path, ap, bp, "mg")["entries"] == []

    def test_seed_whole_to_section_changes_id_via_basis(self, tmp_path):
        """Codex HIGH-2: 种子从 `# 讲义 + 正文` 变成 `## 讲义 + 同正文` 时,
        归一化路径同为 ["讲义"]、内容逐字不变, 原实现只有 basis 变 → diff 报 unchanged,
        而契约 §4.1 #7 声明的是 removed+added。修法 = basis 进身份键。"""
        body = f"{BODY1}\n{BODY2}\n"
        whole = preview_with_seed(tmp_path, "wb-a", "种子", "---\ntype: concept\n---\n\n# 讲义\n\n" + body)
        sect = preview_with_seed(tmp_path, "wb-b", "种子", "---\ntype: concept\n---\n\n## 讲义\n\n" + body)
        w, s = whole["candidates"][0], sect["candidates"][0]
        assert w["stable_id_basis"]["heading_path_normalized"] == s["stable_id_basis"]["heading_path_normalized"]
        assert w["content_fingerprint"] == s["content_fingerprint"]
        assert (w["basis"], s["basis"]) == ("seed-note-whole", "seed-note-section")
        assert w["stable_id"] != s["stable_id"], "契约 §4.1 #7 声明会换 ID, 就必须真的换"

    def test_duplicate_paths_are_flagged_as_identity_ambiguous(self, tmp_path):
        """Codex BLOCKER-1: 同路径重复项的 ID 绑的是「第 N 个槽位」不是内容单元 ——
        交换两条同名小节, 身份跟着槽位走、指纹对调, diff 报 changed×2 而非 moved。
        v1 不改这个语义（改了就得让「正文改动换 ID」, 更糟）, 但**必须标出来**并
        禁止 G5-10 据此持久化 provenance。本测试同时钉死行为与标记。"""
        a, b = section("例题", [BODY1, BODY2]), section("例题", [BODY1, BODY_ALT])
        old, op = preview(tmp_path, "板A", board_doc([a, b]), "amb-a")
        new, np_ = preview(tmp_path, "板A", board_doc([b, a]), "amb-b")
        for c in old["candidates"]:
            assert c["identity_ambiguous"] is True and c["ambiguous_group_size"] == 2
        # 行为如实钉死: 身份留在槽位, 指纹对调
        assert [c["stable_id"] for c in old["candidates"]] == [c["stable_id"] for c in new["candidates"]]
        assert [c["content_fingerprint"] for c in old["candidates"]] == [
            c["content_fingerprint"] for c in reversed(new["candidates"])
        ]
        d = diff_of(tmp_path, op, np_, "amb")
        assert d["summary"]["changed"] == 2 and d["summary"]["moved"] == 0
        assert any("身份**先天歧义**" in w for w in d["warnings"]), "歧义必须在产物里显式告警"
        assert all(e["new"]["identity_ambiguous"] for e in d["entries"])
        md = (tmp_path / "diff-amb" / "split-diff-板A.md").read_text(encoding="utf-8")
        assert "⚠身份歧义" in md, "标记必须出现在人读表格里 —— 只写进 JSON 等于没写"

    def test_truncation_suspect_flagged_when_board_grows_past_same_threshold(self, tmp_path):
        """5 个独立镜头同时命中: **两侧阈值相同**时, 板体跨过阈值也会把尾部
        「仍在板上、一字未动」的小节挤出窗口并报成 removed。"""
        secs = [section(f"节{i:02d}") for i in range(1, 6)]
        _, op = preview(tmp_path, "板A", board_doc(secs), "tr-a")
        r = run_preview(
            make_vault(tmp_path, "板A", board_doc([section("节00-新插入")] + secs), tag="tr-b"),
            "板A",
            tmp_path / "out-tr-b",
            "--max-units",
            "5",
        )
        assert r.returncode == 0
        # 旧侧也用同一阈值重跑, 保证「两侧阈值相同」这个前提成立
        r0 = run_preview(
            make_vault(tmp_path, "板A", board_doc(secs), tag="tr-a2"), "板A", tmp_path / "out-tr-a2", "--max-units", "5"
        )
        assert r0.returncode == 0
        op = tmp_path / "out-tr-a2" / "split-preview-板A.json"
        np_ = tmp_path / "out-tr-b" / "split-preview-板A.json"
        d = diff_of(tmp_path, op, np_, "tr")
        assert d["summary"]["removed"] == 1, "构造前提: 尾节确实被挤出窗口"
        removed = [e for e in d["entries"] if e["state"] == "removed"][0]
        assert removed["truncation_suspect"] is True, "被截断挤出的 removed 必须打嫌疑标记"
        assert any("截断" in w and "阈值相同" in w for w in d["warnings"])
        md = (tmp_path / "diff-tr" / "split-diff-板A.md").read_text(encoding="utf-8")
        assert "⚠截断嫌疑" in md

    def test_cross_vault_compare_warns(self, tmp_path):
        """审查发现: stable_id 只含 vault **内**相对路径 → 两个不同 vault 的同名板
        可以互比, 凭空伪造一份编辑史。落 vault 指纹并告警（不硬拒: 拿隔离副本比
        live 是合法用法, 本卡的四态演示就是）。"""
        a, ap = preview(tmp_path, "板A", board_doc([section("反射代理")]), "cv-a")
        b, bp = preview(tmp_path, "板A", board_doc([section("反射代理")]), "cv-b")
        assert a["vault_fingerprint"] != b["vault_fingerprint"], "构造前提: 两个 vault 目录不同"
        d = diff_of(tmp_path, ap, bp, "cv")
        assert any("不同 vault" in w for w in d["warnings"])

    def test_same_id_different_basis_is_refused(self, tmp_path):
        """Codex LOW: 同一 ID 两侧 basis 不同 —— 要么产物被改过、要么真发生截断碰撞,
        两种情况把它们当同一候选比都是错的, 原实现却报 unchanged。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "sb")
        tampered = json.loads(p.read_text(encoding="utf-8"))
        # ⚠ 原文与归一化路径要**同步**改（board_doc 的路径是 ["主板","反射代理"] 两层）——
        # 否则会先被「heading_path 正向归一化后与 heading_path_normalized 不符」拦下,
        # 测不到本条要测的 basis 一致性 / 复算对账。
        tampered["candidates"][0]["stable_id_basis"]["heading_path_normalized"] = ["主板", "完全不同"]
        tampered["candidates"][0]["source_anchor"]["heading_path"] = ["主板", "完全不同"]
        tp = tmp_path / "tampered.json"
        tp.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "reject-sb"  # ⛔ 不得与 preview() 的 out-<tag> 撞名
        r = run_diff(p, tp, out)
        assert r.returncode != 0 and "stable_id_basis" in (r.stdout + r.stderr)
        assert not out.exists()

    def test_derived_overlap_transition_gets_its_own_reason(self, tmp_path):
        """审查发现: 候选从「未派生」跃迁到「已派生为 [[节点/X]]」原先只表现为
        content 一个 reason, 读 diff 的人分不出「正文改了」和「这段已经被拆过了」——
        后者恰恰是 G5-10 最该知道的信号。"""
        plain = section("反射代理")
        with_callout = (
            "## 反射代理\n\n"
            + BODY1
            + "\n"
            + BODY2
            + "\n\n> [!relation/related_to]+ 已派生为 [[节点/某节点]] · 相关\n\n"
        )
        old, op = preview(tmp_path, "板A", board_doc([plain]), "ov-a")
        new, np_ = preview(tmp_path, "板A", board_doc([with_callout]), "ov-b")
        assert old["candidates"][0]["derived_overlap"]["overlapping"] is False
        assert new["candidates"][0]["derived_overlap"]["overlapping"] is True
        d = diff_of(tmp_path, op, np_, "ov")
        e = d["entries"][0]
        assert e["state"] == "changed" and "overlap" in e["change_reasons"]
        assert e["change_reasons"] == sorted(e["change_reasons"]), "change_reasons 必须字典序"

    def test_overlong_board_name_rejected_with_zero_products(self, tmp_path):
        """Codex round-1 MEDIUM: board 超长 → 先建 out-dir, 写入时 ENAMETOOLONG → 留下空目录。
        在 **preview 侧**测同一道 `validate_product_filename` 守卫 —— diff 侧要构造超长 board
        就得把 board_file / 候选来源 / sources 全部同步改, 那测的是别的门了。"""
        vault = make_vault(tmp_path, "板A", board_doc([section("反射代理")]), tag="long")
        out = tmp_path / "reject-long"
        r = run_preview(vault, "A" * 300, out)
        assert r.returncode != 0 and "过长" in (r.stdout + r.stderr)
        assert not out.exists(), "拒绝路径连空目录都不该留"

    def test_broken_source_anchor_rejected_before_any_write(self, tmp_path):
        """Codex MEDIUM: 坏 source_anchor 原先要到 MD 渲染期才 KeyError,
        此时 JSON 已落盘 → 留下半份产物。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "bad")
        broken = json.loads(p.read_text(encoding="utf-8"))
        broken["candidates"][0]["source_anchor"] = {}
        bp = tmp_path / "bad-anchor.json"
        bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "reject-bad"
        r = run_diff(bp, bp, out)
        assert r.returncode != 0 and "source_anchor" in (r.stdout + r.stderr)
        assert not out.exists()

    def test_pipe_in_heading_does_not_break_md_table(self, tmp_path):
        """审查发现: 标题含 `|`（条件概率 `P(A|B)`）会把表格列切错位,
        把「重名」「已派生重叠」这些告警挤出可见列 —— 告警看不见等于没有。"""
        vault = make_vault(tmp_path, "板A", board_doc([section("条件概率 P(A|B) 的定义")]), nodes=(), tag="pipe")
        out = tmp_path / "out-pipe"
        assert run_preview(vault, "板A", out).returncode == 0
        md = (out / "split-preview-板A.md").read_text(encoding="utf-8")
        row = [ln for ln in md.splitlines() if ln.startswith("| 1 |")][0]
        assert "\\|" in row, "表格单元格里的 | 必须转义"
        assert row.count("|") - row.count("\\|") == 8, "转义后列数必须与表头一致（7 列 → 8 个分隔符）"

    def test_occurrence_counts_all_sections_not_just_candidates(self, tmp_path):
        """审查发现该保证「零裁判」: occurrence 按**全部小节**计数而非仅候选。
        变异成「只数候选」时, 给一个原本不达标的同名小节补正文, 会让它后面的
        同名候选静默改号 —— provenance 错锚到另一小节。"""
        thin = "## 例题\n\n太短。\n\n"  # 不达标: 1 行 + 不足 60 字
        thick = section("例题", [BODY1, BODY2])
        data, _ = preview(tmp_path, "板A", board_doc([thin, thick]), "occ")
        assert len(data["candidates"]) == 1, "构造前提: 第一个同名小节不达标"
        assert data["candidates"][0]["stable_id_basis"]["occurrence"] == 2, (
            "occurrence 必须把不达标的同名小节也数进去（否则它后来达标时会连累后面改号）"
        )


class TestRound2Regressions:
    """Codex 第 2 轮（复核轮）新抓的 3 HIGH + 3 MEDIUM + 1 LOW 的回归门。"""

    def test_commented_out_recent_activity_does_not_swallow_user_text(self, tmp_path):
        """⛔ HIGH-1: 普通 HTML 注释里写着 `## Recent Activity` 时, 原实现把它当真标题、
        一路吞到下一个同级标题为止——**连同注释后面的用户正文一起吞掉**。被吞的正文
        不进指纹, 于是用户改了那段正文, diff 却报「无变化」。"""

        def doc(body: str) -> str:
            return (
                "---\ntype: whiteboard\n---\n\n# 主板\n\n## 甲小节\n\n"
                f"{BODY1}\n{BODY2}\n\n<!--\n## Recent Activity\n-->\n{body}\n"
            )

        a, ap = preview(tmp_path, "板A", doc("用户正文版本 A，这一行是真内容不是机器日志。"), "r2a")
        b, bp = preview(tmp_path, "板A", doc("用户正文版本 B，改了一个字就该被看见。"), "r2b")
        assert a["candidates"][0]["stable_id"] == b["candidates"][0]["stable_id"]
        assert a["candidates"][0]["content_fingerprint"] != b["candidates"][0]["content_fingerprint"], (
            "注释掉的 Recent Activity 不该吞掉其后的用户正文"
        )
        d = diff_of(tmp_path, ap, bp, "r2ra")
        assert [e["state"] for e in d["entries"]] == ["changed"]

    @pytest.mark.parametrize(
        "mutate,keyword",
        [
            (lambda d: d["candidates"][0].pop("identity_ambiguous"), "identity_ambiguous"),
            (lambda d: d["candidates"][0].pop("ambiguous_group_size"), "ambiguous_group_size"),
            (lambda d: d.pop("vault_fingerprint"), "vault_fingerprint"),
            (lambda d: d["candidates"][0].pop("stable_id_basis"), "stable_id_basis"),
            (lambda d: d["candidates"][0].update(index=[]), "index"),
            (lambda d: d["candidates"][0].update(suggested_name=None), "suggested_name"),
            (lambda d: d["candidates"][0].update(basis={}), "basis"),
            (lambda d: d["candidates"][0]["source_anchor"].update(line_start=None), "line_start"),
            (lambda d: d["candidates"][0]["stable_id_basis"].update(occurrence=0), "occurrence"),
            (lambda d: d["candidates"][0].update(identity_ambiguous=True), "自相矛盾"),
        ],
    )
    def test_missing_or_mistyped_safety_fields_are_refused(self, tmp_path, mutate, keyword):
        """⛔ HIGH-2: 只查字段「在不在」不够 —— 安全字段被删或类型不对时，
        三道处置会同时 **fail-open**（歧义投影成 false / 跨 vault 不告警 /
        basis 守卫因 None==None 被绕过），而 diff 照常 rc=0 输出一份看起来正常的报告。
        安全字段缺失必须等同于拒绝。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), f"r2f-{keyword}")
        broken = json.loads(p.read_text(encoding="utf-8"))
        mutate(broken)
        bp = tmp_path / "broken-field.json"  # ⛔ 中性名
        bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "reject-r2-field"
        r = run_diff(bp, bp, out)
        assert r.returncode != 0, f"{keyword} 异常时必须拒绝"
        assert keyword in (r.stdout + r.stderr), f"诊断里要点名 {keyword}"
        assert not out.exists(), "拒绝路径零产物"

    def test_second_product_rejection_leaves_no_first_product(self, tmp_path):
        """⛔ MEDIUM-1: 把第二份产物（MD）预置成 symlink, 原实现顺序写入 ——
        JSON 已落盘、MD 被写侧防御拒绝 → 留下半份产物。改为**先验完两个目标再落笔**。"""
        _, op = preview(tmp_path, "板A", board_doc([section("反射代理")]), "r2p-a")
        _, np_ = preview(tmp_path, "板A", board_doc([section("反射代理", [BODY1, BODY_ALT])]), "r2p-b")
        out = tmp_path / "pair-out"
        out.mkdir()
        victim = tmp_path / "outside-victim.md"
        victim.write_text("原样", encoding="utf-8")
        (out / "split-diff-板A.md").symlink_to(victim)

        r = run_diff(op, np_, out)
        assert r.returncode != 0 and "symlink" in (r.stdout + r.stderr)
        assert victim.read_text(encoding="utf-8") == "原样", "symlink 目标不得被写穿"
        assert not (out / "split-diff-板A.json").exists(), "第二份被拒时不得留下第一份"

    def test_nfc_nfd_equivalent_source_name_is_not_falsely_refused(self, tmp_path):
        """⛔ MEDIUM-2: 产物里 `stable_id_basis.file` 存的是原始路径, 而身份键对它做了 NFC。
        直接比 raw dict 会把「NFC/NFD 等价改名」判成 basis 不一致而**假拒绝** ——
        那种改名恰恰是契约 §4.2 明确归入稳定面的。"""
        nfc_name = "特征值-tèzhēngzhí"
        nfd_name = unicodedata.normalize("NFD", nfc_name)
        assert nfd_name != nfc_name
        seed_doc = "---\ntype: concept\n---\n\n# 讲义\n\n" + section("子节")
        a = preview_with_seed(tmp_path, "r2n-a", nfc_name, seed_doc)
        b = preview_with_seed(tmp_path, "r2n-b", nfd_name, seed_doc)
        ca, cb = a["candidates"][0], b["candidates"][0]
        assert ca["stable_id"] == cb["stable_id"], "构造前提: NFC/NFD 等价路径的 ID 相同"
        assert ca["stable_id_basis"]["file"] != cb["stable_id_basis"]["file"], "构造前提: raw file 字节不同"
        ap = tmp_path / "out-r2n-a" / "split-preview-板A.json"
        bp = tmp_path / "out-r2n-b" / "split-preview-板A.json"
        d = diff_of(tmp_path, ap, bp, "r2n")
        assert d["summary"]["unchanged"] == 1, "等价改名不该被 basis 守卫拒绝, 也不该报变化"

    def test_max_units_must_be_positive(self, tmp_path):
        """⛔ MEDIUM-3: `--max-units -1` 原先 rc=0, 还输出自相矛盾的
        `threshold=-1, kept=2, over_threshold=true`。"""
        vault = make_vault(tmp_path, "板A", board_doc([section("甲"), section("乙")]), tag="r2m")
        r = run_preview(vault, "板A", tmp_path / "out-r2m", "--max-units", "-1")
        assert r.returncode != 0 and "正整数" in (r.stdout + r.stderr)
        assert not (tmp_path / "out-r2m").exists()

    def test_payload_encoding_is_injective_under_nul_bytes(self, tmp_path):
        """⛔ LOW-2: 「标题正文不可能含 U+0000」这个假设不成立。载荷改长度前缀后,
        含 NUL 的标题也不能与别的段落切分方式撞车。"""
        mod = load_module()
        a = mod.compute_stable_id("f.md", ["a", "b"], 1, "board-body-section")
        b = mod.compute_stable_id("f.md", ["a\x00b"], 1, "board-body-section")
        assert a != b, "分段方式不同必须得到不同 ID（长度前缀编码保证单射）"
        c = mod.compute_stable_id("f.md", ["a"], 11, "board-body-section")
        e = mod.compute_stable_id("f.md", ["a", "1"], 1, "board-body-section")
        assert c != e


class TestRound3Regressions:
    """Codex 第 3 轮（二次复核）抓的 3 MEDIUM + 残余边界收口的回归门。"""

    @pytest.mark.parametrize("field", ["index", "ambiguous_group_size"])
    @pytest.mark.parametrize("val", [True, False])
    def test_bool_is_not_accepted_as_int_on_candidate(self, tmp_path, field, val):
        """⛔ `isinstance(True, int)` 在 Python 里为真 —— JSON 的 `true/false` 会被当整数放行。
        Codex round-3 用 166 组畸形 schema 实证: 有 8 组靠这个类型陷阱一路 rc=0。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), f"r3b-{field}-{val}")
        broken = json.loads(p.read_text(encoding="utf-8"))
        broken["candidates"][0][field] = val
        bp = tmp_path / f"bool-{val}.json"  # ⛔ field 不进路径
        bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / f"reject-bool-{val}"
        r = run_diff(bp, bp, out)
        assert r.returncode != 0 and field in (r.stdout + r.stderr)
        assert not out.exists()

    @pytest.mark.parametrize("path_expr", ["c['source_anchor']['line_start']", "c['stable_id_basis']['occurrence']"])
    def test_bool_is_not_accepted_as_int_nested(self, tmp_path, path_expr):
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), f"r3n-{abs(hash(path_expr)) % 997}")
        broken = json.loads(p.read_text(encoding="utf-8"))
        c = broken["candidates"][0]
        if "line_start" in path_expr:
            c["source_anchor"]["line_start"] = True
            keyword = "line_start"
        else:
            c["stable_id_basis"]["occurrence"] = True
            keyword = "occurrence"
        bp = tmp_path / "boolnested.json"  # ⛔ 中性名
        bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "reject-boolnested"
        r = run_diff(bp, bp, out)
        assert r.returncode != 0 and keyword in (r.stdout + r.stderr)
        assert not out.exists()

    def test_dangling_symlink_target_is_not_deleted_on_rejection(self, tmp_path):
        """⛔ MEDIUM: 回滚用 `Path.exists()` 判「本次新建」，而 dangling symlink 的
        `exists()` 为 False → 被误判成自己建的 → 拒绝路径把**用户既存的链接删掉**。
        这不是零产物问题，是破坏既有目录项。修法 = 用 `os.path.lexists()`。"""
        _, op = preview(tmp_path, "板A", board_doc([section("反射代理")]), "r3d-a")
        _, np_ = preview(tmp_path, "板A", board_doc([section("反射代理", [BODY1, BODY_ALT])]), "r3d-b")
        out = tmp_path / "dangling-out"
        out.mkdir()
        dangling_json = out / "split-diff-板A.json"
        dangling_json.symlink_to(tmp_path / "does-not-exist-target")
        assert not dangling_json.exists() and dangling_json.is_symlink()

        r = run_diff(op, np_, out)
        assert r.returncode != 0, "symlink 目标应被写侧防御拒绝"
        assert os.path.lexists(str(dangling_json)), "既存的 dangling symlink 不得被回滚误删"

    @pytest.mark.parametrize(
        "mutate,keyword",
        [
            (lambda c: c["stable_id_basis"].update(file="节点/别的文件.md"), "file"),
            (
                lambda c: c["stable_id_basis"].update(basis="seed-note-whole"),
                "basis",
            ),  # ⛔ 必须与原值不同, 否则是空变异
            (lambda c: c["stable_id_basis"].update(occurrence=7), "复算"),
            (
                lambda c: c["stable_id_basis"].update(heading_path_normalized=["伪造"]),
                "正向归一化",
            ),  # 改归一化路径 → 先被正向对账拦下
            (lambda c: c["stable_id_basis"].update(namespace="split-anchor/vX"), "namespace"),
            (lambda c: c.update(stable_id="bsa1-NOTHEX0000000000"), "stable_id"),
            (lambda c: c.update(content_fingerprint="cf1-xyz"), "content_fingerprint"),
            (lambda c: c["source_anchor"].update(line_start=99, line_end=1), "倒置"),
            (lambda c: c["source_anchor"].update(line_start=0), "正整数"),
            (lambda c: c.update(index=0), "正整数"),
        ],
    )
    def test_semantically_broken_but_well_typed_input_is_refused(self, tmp_path, mutate, keyword):
        """⛔ Codex round-3 点名的残余边界：13 类「类型都对、但语义被改坏」的输入原先能 rc=0。
        收口手段 = 交叉绑定（basis 三处与候选/顶层/anchor 对齐）+ **stable_id 复算**
        —— `stable_id_basis` 带齐了身份键的四个输入, 所以能直接算一遍对账。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), f"r3s-{keyword}-{abs(hash(keyword)) % 97}")
        broken = json.loads(p.read_text(encoding="utf-8"))
        mutate(broken["candidates"][0])
        bp = tmp_path / f"semantic-{abs(hash(str(broken))) % 9973}.json"  # ⛔ 中性名
        bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        out = bp.with_suffix(".outdir")
        r = run_diff(bp, bp, out)
        assert r.returncode != 0, f"{keyword}: 语义损坏的产物必须拒绝"
        # ⛔ 只看诊断文本, 且临时文件名必须中性 —— 早前把 keyword 拼进了路径,
        # 这条断言于是被**路径**满足而不是被诊断满足（自查抓到的假绿）。
        assert keyword in (r.stdout + r.stderr), f"{keyword}: 诊断要点名问题所在"
        assert not out.exists()

    @pytest.mark.parametrize("kind", ["悬空链接", "有效链接", "多引用文件", "只读文件", "目录"])
    def test_preexisting_target_of_any_shape_survives_rejection(self, tmp_path, kind):
        """把第二份产物的目标位置预置成五种文件系统形态，逐一验证拒绝时的三件事：
        ① 引擎拒绝（rc≠0）② **既存目录项原样保留**（内容/链接都不动）③ 不留第一份产物。
        「悬空链接」这一格是 Codex round-3 抓到的真缺陷（`exists()` 对它为 False,
        回滚会把它当自己建的删掉）——其余四格是它的对照组，防止只修一格。"""
        _, op = preview(tmp_path, "板A", board_doc([section("反射代理")]), f"shape-a-{kind}")
        _, np_ = preview(tmp_path, "板A", board_doc([section("反射代理", [BODY1, BODY_ALT])]), f"shape-b-{kind}")
        out = tmp_path / f"shape-out-{kind}"
        out.mkdir()
        tgt = out / "split-diff-板A.md"
        keep = None
        if kind == "悬空链接":
            tgt.symlink_to(tmp_path / "nope-does-not-exist")
        elif kind == "有效链接":
            keep = tmp_path / f"outside-{kind}"
            keep.write_text("原样", encoding="utf-8")
            tgt.symlink_to(keep)
        elif kind == "多引用文件":
            keep = tmp_path / f"outside-{kind}"
            keep.write_text("原样", encoding="utf-8")
            os.link(str(keep), str(tgt))
        elif kind == "只读文件":
            tgt.write_text("原样", encoding="utf-8")
            os.chmod(str(tgt), 0o444)
            keep = tgt
        else:
            tgt.mkdir()

        before = keep.read_text(encoding="utf-8") if keep is not None else None
        r = run_diff(op, np_, out)
        assert r.returncode != 0, f"{kind}: 应被写侧防御拒绝"
        assert os.path.lexists(str(tgt)), f"{kind}: 既存目录项不得被回滚误删"
        assert not (out / "split-diff-板A.json").exists(), f"{kind}: 不得留下第一份产物"
        if before is not None:
            assert keep.read_text(encoding="utf-8") == before, f"{kind}: 既存内容不得被写穿"

    def test_intact_product_still_passes_all_new_guards(self, tmp_path):
        """反面锚：加了这么多守卫之后，**未被篡改**的产物必须照常通过（防守卫过严）。"""
        _, op = preview(tmp_path, "板A", board_doc([section("甲"), section("乙"), section("丙")]), "r3ok-a")
        _, np_ = preview(tmp_path, "板A", board_doc([section("甲"), section("乙"), section("丙")]), "r3ok-b")
        d = diff_of(tmp_path, op, np_, "r3ok")
        assert d["summary"] == {"added": 0, "changed": 0, "removed": 0, "moved": 0, "unchanged": 3}


class TestRound4Regressions:
    """Codex 第 4 轮（终裁轮）抓的语义层 fail-open + **信任边界的可执行声明**。"""

    @pytest.mark.parametrize(
        "mutate,keyword",
        [
            (lambda d: d["candidates"][0]["source_anchor"].update(heading_path=["伪造标题"]), "正向归一化"),
            (lambda d: d["candidates"][0]["source_anchor"].update(heading_path=[]), "为空"),
            (lambda d: d.update(vault_fingerprint="   "), "vault_fingerprint"),
            (lambda d: d.update(vault_fingerprint="vf1-NOTHEX000000000"), "vault_fingerprint"),
            (lambda d: d["scale_gate"].update(total_candidates=999, over_threshold=False), "scale_gate"),
            (lambda d: d["scale_gate"].update(kept=99), "scale_gate"),
            (lambda d: d["scale_gate"].update(threshold=0), "scale_gate"),
        ],
    )
    def test_semantic_layer_fail_open_is_closed(self, tmp_path, mutate, keyword):
        """⛔ Codex round-4 实证：这些输入类型全对、交叉绑定全对、复算也过，却仍能 rc=0 ——
        伪造锚点混进 diff、截断告警被静默压掉。逐条堵上。"""
        _, p = preview(
            tmp_path, "板A", board_doc([section("反射代理")]), f"r4-{keyword}-{abs(hash(str(mutate))) % 997}"
        )
        broken = json.loads(p.read_text(encoding="utf-8"))
        mutate(broken)
        bp = tmp_path / f"r4-{abs(hash(json.dumps(broken, ensure_ascii=False))) % 9973}.json"  # ⛔ 中性名
        bp.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        out = bp.with_suffix(".outdir")
        r = run_diff(bp, bp, out)
        assert r.returncode != 0, f"{keyword}: 语义层篡改必须拒绝"
        # ⛔ 只看诊断文本, 且临时文件名必须中性 —— 早前把 keyword 拼进了路径,
        # 这条断言于是被**路径**满足而不是被诊断满足（自查抓到的假绿）。
        assert keyword in (r.stdout + r.stderr), f"{keyword}: 诊断要点名问题所在"
        assert not out.exists()

    def test_relabelled_namespace_on_both_sides_is_refused(self, tmp_path):
        """⛔ 两侧顶层与 basis 的 namespace **协同**改成别的代际时，同侧绑定、跨侧相等、
        复算三道全过（Codex round-4 实证）。所以必须再钉一道「只认本引擎这一代」。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "r4ns")
        fake = json.loads(p.read_text(encoding="utf-8"))
        fake["stable_id_namespace"] = "split-anchor/v999"
        for c in fake["candidates"]:
            c["stable_id_basis"]["namespace"] = "split-anchor/v999"
        fp = tmp_path / "ns999.json"
        fp.write_text(json.dumps(fake, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "reject-ns999"
        r = run_diff(fp, fp, out)
        assert r.returncode != 0 and "stable_id_namespace" in (r.stdout + r.stderr)
        assert not out.exists()

    def test_declared_limit_consistent_forgery_is_NOT_detectable(self, tmp_path):
        """⛔⛔ 这条测试**故意断言一个我们抓不住的情况** —— 它是契约 §8.2「信任边界」
        那段声明的可执行版本。

        ⚠ 这条测试自己被审查打回过一次（Codex round-6）：初版只把 `file` 改成
        `节点/…` 却没同步 `basis` / `sources` / `board_file` —— 那**不是**自洽伪品，
        而是「把可检查的不一致算进信任边界」，等于拿边界当挡箭牌。现已改成真正自洽的伪造。

        preview 产物**没有签名**，且 diff **不读 vault**。所以一份「每一处都互相对得上」
        的伪品 —— 来源文件、basis、sources、标题路径、stable_id 全部重新签成一套 ——
        与引擎产出的真品在结构上不可区分，哪怕它指向的文件根本不存在。

        本测试构造这样一份并断言它**被接受**。哪天有人加了签名或让 diff 校验来源存在性，
        这条测试会变红 —— 那时它就该被改成断言「拒绝」，并同步更新契约 §8.2。
        """
        mod = load_module()
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "r4forge")
        forged = json.loads(p.read_text(encoding="utf-8"))
        c = forged["candidates"][0]
        b = c["stable_id_basis"]
        fake_src = "节点/根本不存在的来源.md"
        # ⛔ 每一处都跟着改，才叫「自洽」：basis 形态、两处 file、sources 清单、身份键
        c["basis"] = b["basis"] = "seed-note-section"
        b["file"] = c["source_anchor"]["file"] = fake_src
        forged["sources"].append({"file": fake_src, "role": "seed", "sha256": "0" * 64})
        c["stable_id"] = mod.compute_stable_id(b["file"], b["heading_path_normalized"], b["occurrence"], b["basis"])
        c["suggested_name"] = mod.derive_concept_stub(
            mod.clean_heading(c["source_anchor"]["heading_path"][-1]),
            anchor=f"{fake_src}\x00{'/'.join(b['heading_path_normalized'])}\x00{b['basis']}\x00{b['occurrence']}",
        )
        c["resolved_name"] = c["suggested_name"]
        fp = tmp_path / "forged.json"
        fp.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "forged-out"
        r = run_diff(fp, fp, out)
        assert r.returncode == 0, (
            "**每一处都自洽**的伪品当前能通过——这是已声明的信任边界（产物无签名 + diff 不读 vault）。"
            f"若此处开始失败，说明引入了签名或来源存在性校验，请把本测试改为断言拒绝并更新契约 §8.2。"
            f"\n实际诊断: {r.stdout + r.stderr}"
        )
        assert json.loads((out / "split-diff-板A.json").read_text(encoding="utf-8"))["summary"]["unchanged"] == 1


class TestRound6Regressions:
    """Codex 第 6 轮：把「本可从 JSON 自身查出的矛盾」从信任边界里挪出来，逐条堵上。"""

    @pytest.mark.parametrize("case", ["来源目录", "已知取值", "复算不符", "id_stability", "sources"])
    def test_internally_checkable_forgery_is_refused(self, tmp_path, case):
        """⛔ 这五类原先都能 rc=0，而它们**无需读 vault** 就能从 JSON 内部对账出来 ——
        把它们算进「无签名所以查不出」的信任边界，就是拿边界当挡箭牌（Codex round-6 指正）。

        ⚠ 构造要点：前两类必须**连 stable_id 一起重算**，否则会先被复算对账拦下，
        测到的就是别的门了（这一点是补门时当场被红出来的）。
        """
        mod = load_module()
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), f"r6-{abs(hash(case)) % 977}")
        forged = json.loads(p.read_text(encoding="utf-8"))
        c = forged["candidates"][0]
        b = c["stable_id_basis"]

        def resign() -> None:
            b_file, hp, occ, bas = b["file"], b["heading_path_normalized"], b["occurrence"], b["basis"]
            c["stable_id"] = mod.compute_stable_id(b_file, hp, occ, bas)
            c["suggested_name"] = mod.derive_concept_stub(
                mod.clean_heading(c["source_anchor"]["heading_path"][-1]),
                anchor=f"{b_file}\x00{'/'.join(hp)}\x00{bas}\x00{occ}",
            )
            c["resolved_name"] = c["suggested_name"]

        if case == "来源目录":  # 板体候选却指向 节点/ —— 与 basis 的目录前缀矛盾
            b["file"] = c["source_anchor"]["file"] = "节点/不存在.md"
            forged["sources"].append({"file": "节点/不存在.md", "role": "seed", "sha256": "0" * 64})
            resign()
        elif case == "已知取值":
            c["basis"] = b["basis"] = "invented-basis"
            resign()
        elif case == "复算不符":  # 只伪造名称, 其余不动 → 名称复算对不上
            c["suggested_name"] = c["resolved_name"] = "伪造的名字"
        elif case == "id_stability":
            forged["id_stability"] = "invented_v999"
        else:
            forged["sources"] = []

        fp = tmp_path / f"r6-{abs(hash(json.dumps(forged, ensure_ascii=False))) % 9973}.json"  # 中性名
        fp.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
        out = fp.with_suffix(".outdir")
        r = run_diff(fp, fp, out)
        assert r.returncode != 0, f"{case}: 内部可查的矛盾必须拒绝"
        assert case in (r.stdout + r.stderr), f"{case}: 诊断要点名问题所在, 实得 {r.stdout + r.stderr}"
        assert not out.exists()

    def test_moving_section_to_another_parent_changes_id(self, tmp_path):
        """契约 §4.1 漏列的高频操作：**同一份笔记里换父**。
        `子小节` 从 `父甲` 挪到 `父乙`（没跨文件、没改自己的标题）→ 祖先链变 → 换 ID。
        UAT 原来写「同一份笔记里上下调序不变」也因此不准确（Codex round-6 指出）。"""
        sub_sec = section("子小节", level=3)
        before = board_doc([section("父甲"), sub_sec, section("父乙")])
        after = board_doc([section("父甲"), section("父乙"), sub_sec])
        a, _ = preview(tmp_path, "板A", before, "r6p-a")
        b, _ = preview(tmp_path, "板A", after, "r6p-b")
        ca = [c for c in a["candidates"] if c["resolved_name"] == "子小节"][0]
        cb = [c for c in b["candidates"] if c["resolved_name"] == "子小节"][0]
        assert ca["stable_id_basis"]["heading_path_normalized"] == ["主板", "父甲", "子小节"]
        assert cb["stable_id_basis"]["heading_path_normalized"] == ["主板", "父乙", "子小节"]
        assert ca["stable_id"] != cb["stable_id"], "换父 = 祖先链变 = 换 ID"


class TestRound5Regressions:
    """Codex 第 5 轮抓的两条内部不一致 + §4.1 三条此前未单独覆盖的边界行。"""

    def test_same_depth_forged_heading_path_is_refused(self, tmp_path):
        """⛔ HIGH: 只绑层数不够 —— 同层数的伪造标题能静默通过, 把伪造锚点送进 diff。
        我 round-4 写过「归一化有损、只能绑层数」, **那是错的**：不需要从归一化反推原文,
        把原文**再正向归一化一遍**比对即可。这属于无需读 vault 就能对账的内部不一致,
        不该被算进「无签名」那条边界（Codex round-5 指正）。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "r5hp")
        forged = json.loads(p.read_text(encoding="utf-8"))
        c = forged["candidates"][0]
        assert len(c["source_anchor"]["heading_path"]) == 2, "构造前提: 路径两层"
        c["source_anchor"]["heading_path"] = ["完全伪造的父标题", "完全伪造的子标题"]  # 同层数
        fp = tmp_path / "same-depth-forged.json"
        fp.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "reject-r5hp"
        r = run_diff(fp, fp, out)
        assert r.returncode != 0 and "正向归一化" in (r.stdout + r.stderr)
        assert not out.exists()

    def test_board_relabel_without_board_file_is_refused(self, tmp_path):
        """⛔ 只重标 `board`、不改 `board_file` 同样是无需读 vault 就能发现的不一致。"""
        _, p = preview(tmp_path, "板A", board_doc([section("反射代理")]), "r5bf")
        forged = json.loads(p.read_text(encoding="utf-8"))
        forged["board"] = "板Z"
        fp = tmp_path / "board-relabel.json"
        fp.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
        out = tmp_path / "reject-r5bf"
        r = run_diff(fp, fp, out)
        assert r.returncode != 0 and "board_file" in (r.stdout + r.stderr)
        assert not out.exists()

    def test_board_rename_changes_only_board_body_candidates(self, tmp_path):
        """⛔ 契约 §4.1 #6 原文写「板文件改名 → **全板**换 ID」—— 实测**不成立**
        （Codex round-5）。种子笔记候选的 `file_rel` 是 `节点/种子.md`，压根不含板名，
        所以改板名它们的 ID 纹丝不动。原有裁判只用了纯板体候选, 造成假完备感。
        本测试用**混合**构造（板体候选 + 种子候选）把真实行为钉死。"""

        def mixed(board: str) -> Path:
            v = tmp_path / f"vault-mix-{board}"
            for d in ("原白板", "节点", "outputs"):
                (v / d).mkdir(parents=True, exist_ok=True)
            (v / "原白板" / f"{board}.md").write_text(
                "---\ntype: whiteboard\n---\n\n# 主板\n\n"
                + section("板体小节")
                + "## Concepts\n\n- [[节点/种子]] — 种子 · 掌握度 — · 未考\n",
                encoding="utf-8",
            )
            (v / "节点" / "种子.md").write_text(
                "---\ntype: concept\n---\n\n# 讲义\n\n" + section("种子小节"), encoding="utf-8"
            )
            return v

        out = {}
        for board in ("板甲", "板乙"):
            o = tmp_path / f"out-mix-{board}"
            assert run_preview(mixed(board), board, o).returncode == 0
            d = json.loads((o / f"split-preview-{board}.json").read_text(encoding="utf-8"))
            out[board] = {c["resolved_name"]: (c["stable_id"], c["source_anchor"]["file"]) for c in d["candidates"]}
        a, b = out["板甲"], out["板乙"]
        assert set(a) == {"板体小节", "种子小节"}, f"构造前提: 两类候选都要有, 实得 {set(a)}"
        assert a["板体小节"][0] != b["板体小节"][0], "板体候选的 file_rel 含板名 → 改板名必换 ID"
        assert a["种子小节"][0] == b["种子小节"][0], (
            "种子候选的 file_rel 是 节点/种子.md, 不含板名 → 改板名**不**换 ID（§4.1 #6 必须这样写）"
        )
        assert a["种子小节"][1] == "节点/种子.md"

    def test_level_change_altering_ancestor_chain_changes_id(self, tmp_path):
        """§4.1 #4（此前只有反面锚，没有正面门）：层级调整**改变了祖先链**时换 ID。"""
        before = board_doc([section("父章节"), section("子小节", level=3)])
        after = board_doc([section("父章节"), section("子小节", level=2)])
        a, _ = preview(tmp_path, "板A", before, "r5l-a")
        b, _ = preview(tmp_path, "板A", after, "r5l-b")
        pa = [c for c in a["candidates"] if c["resolved_name"] == "子小节"][0]
        pb = [c for c in b["candidates"] if c["resolved_name"] == "子小节"][0]
        assert pa["stable_id_basis"]["heading_path_normalized"] == ["主板", "父章节", "子小节"]
        assert pb["stable_id_basis"]["heading_path_normalized"] == ["主板", "子小节"]
        assert pa["stable_id"] != pb["stable_id"]

    def test_inserting_duplicate_before_shifts_occurrence(self, tmp_path):
        """§4.1 #9（#5 的镜像，此前未单独覆盖）：在同名小节**前面**插一条同名的,
        后者 occurrence +1 → 换 ID, 且它原来的 ID 被新插入的那条接管。"""
        orig = section("例题", [BODY1, BODY2])
        inserted = section("例题", [BODY1, BODY_ALT])
        a, _ = preview(tmp_path, "板A", board_doc([orig]), "r5i-a")
        b, _ = preview(tmp_path, "板A", board_doc([inserted, orig]), "r5i-b")
        old_id = a["candidates"][0]["stable_id"]
        new_first, new_second = b["candidates"][0], b["candidates"][1]
        assert new_first["stable_id"] == old_id, "新插入的那条**接管**了原来的 ID"
        assert new_second["stable_id"] != old_id, "原来那条 occurrence 位移 → 换 ID"
        assert new_second["content_fingerprint"] == a["candidates"][0]["content_fingerprint"]

    def test_inline_html_comment_on_heading_dissolves_the_section(self, tmp_path):
        """§4.1 #10（此前只在文档里，无门）：给标题行加行内 HTML 注释,
        该行被注释掩码吃掉 → 不再算标题 → 小节整体消失。"""
        a, _ = preview(tmp_path, "板A", board_doc([section("甲小节")]), "r5c-a")
        b, _ = preview(tmp_path, "板A", board_doc([section("甲小节 <!-- 备注 -->")]), "r5c-b")
        assert [c["resolved_name"] for c in a["candidates"]] == ["甲小节"]
        assert not any(c["resolved_name"].startswith("甲小节") for c in b["candidates"]), (
            f"标题行带行内注释后该小节应消失, 实得 {[c['resolved_name'] for c in b['candidates']]}"
        )


# ══════════════════════════ 8 · live 真实板 (只读) ══════════════════════════


def _tree_digest(root: Path) -> str:
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            rel = p.relative_to(root).as_posix()
            try:
                st = p.lstat()
                h = "L" if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest()
            except OSError:
                h = "ERR"
                st = None
            rows.append(f"{rel}\t{h}\t{st.st_size if st else '-'}\t{st.st_mtime_ns if st else '-'}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


#: ⛔ Codex round-1 HIGH-3: live 判据原本靠 skip 兜底 —— 把 LIVE_VAULT 指到不存在的
#: 路径, 整套仍 exit 0「35 passed, 2 skipped」, 卡片 (d) 的「≥2 块真实板」悄悄落空。
#: 现在缺 live 一律**失败**; 只有显式设 G53_ALLOW_NO_LIVE=1（换机器/CI 无 vault）才降级为
#: skip, 且那种情况下卡片验收必须标 UNVERIFIED, 不计作绿。
_ALLOW_NO_LIVE = os.environ.get("G53_ALLOW_NO_LIVE") == "1"


class TestLiveRealBoards:
    @staticmethod
    def _require_live() -> None:
        if LIVE_VAULT.is_dir():
            return
        if _ALLOW_NO_LIVE:
            pytest.skip("G53_ALLOW_NO_LIVE=1: live vault 缺失 —— 卡片 (d) 判据本次 UNVERIFIED")
        pytest.fail(
            f"⛔ live vault 不存在: {LIVE_VAULT}\n"
            "  卡片 (d) 要求「≥2 块真实板两次运行 stable_id 完全一致」——缺 live 不能算绿。\n"
            "  换机器/CI 上确实没有 vault 时, 显式设 G53_ALLOW_NO_LIVE=1 降级为 skip, "
            "并在验收单上标 UNVERIFIED。"
        )

    def test_two_runs_on_real_boards_give_identical_stable_ids(self, tmp_path):
        self._require_live()
        for b in LIVE_BOARDS:
            if not (LIVE_VAULT / "原白板" / f"{b}.md").exists():
                pytest.fail(f"⛔ live vault 存在但板缺失: {b} —— 这是真问题, 不是可跳过的环境差异")
        before = _tree_digest(LIVE_VAULT)
        for b in LIVE_BOARDS:
            o1, o2 = tmp_path / f"r1-{b}", tmp_path / f"r2-{b}"
            assert run_preview(LIVE_VAULT, b, o1).returncode == 0
            assert run_preview(LIVE_VAULT, b, o2).returncode == 0
            d1 = json.loads((o1 / f"split-preview-{b}.json").read_text(encoding="utf-8"))
            d2 = json.loads((o2 / f"split-preview-{b}.json").read_text(encoding="utf-8"))
            assert d1["candidates"], f"live 板 {b} 应有候选 (0 候选则本条测试空转)"
            ids1 = [c["stable_id"] for c in d1["candidates"]]
            ids2 = [c["stable_id"] for c in d2["candidates"]]
            assert ids1 == ids2, f"live 板 {b} 两跑 stable_id 不一致"
            assert len(set(ids1)) == len(ids1), f"live 板 {b} stable_id 有碰撞"
            assert (o1 / f"split-preview-{b}.json").read_bytes() == (o2 / f"split-preview-{b}.json").read_bytes()
        assert _tree_digest(LIVE_VAULT) == before, "⛔ live vault 被改动 —— 只读红线破了"

    def test_live_diff_of_two_identical_runs_is_all_unchanged(self, tmp_path):
        self._require_live()
        b = LIVE_BOARDS[0]
        if not (LIVE_VAULT / "原白板" / f"{b}.md").exists():
            pytest.fail(f"⛔ live vault 存在但板缺失: {b} —— 这是真问题, 不是可跳过的环境差异")
        before = _tree_digest(LIVE_VAULT)
        o1, o2 = tmp_path / "lr1", tmp_path / "lr2"
        assert run_preview(LIVE_VAULT, b, o1).returncode == 0
        assert run_preview(LIVE_VAULT, b, o2).returncode == 0
        d = diff_of(tmp_path, o1 / f"split-preview-{b}.json", o2 / f"split-preview-{b}.json", "live")
        assert d["entries"] == []
        assert d["summary"]["unchanged"] == len(d["unchanged"]) > 0
        assert _tree_digest(LIVE_VAULT) == before
