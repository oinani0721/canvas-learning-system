# ⚠️ CARD-G8-2 (BATCH-2026-09-01-第八批) — 统一 /lint 骨架 + 首批三检查的裁判
#
# 被测物: backend/scripts/vault_lint.py (新)
# 本文件禁用 conftest —— 全部 helper 在文件内 (卡文硬约束)。
#
# 语义钉死点:
#   1. 三检查反例 (先红) —— 孤儿 / raw-derived 混入+recap 缺标记 / stale+corrupt 投影,
#      每个反例的 findings 非空断言 = 检查逻辑被删时本文件必须变红
#   2. 干净 fixture 全 ok + 退出码三态 (0/2/1) 与报告状态逐项一致
#   3. orphan 形态表 —— 别名/子路径/embed/heading锚/带.md/NFC-NFD/大小写/空[[]]/
#      frontmatter链/自链/检验白板链, 逐类标「判定/不判定」
#   4. freshness 同源锁 ≥6 组 —— **活 oracle 比对**: 构造 vault fixture 后同时调
#      真实 review_overview._vault_entry (spec_from_file_location 直载, 零包路由)
#      与 vault_lint._projection_status, 断言 status 逐字相等;
#      另附 17 组实测快照锚 (probe-B 2026-09-01 实测) 防 oracle 静默漂移
#   5. --json 与文本同源 —— 解析文本输出逐项比对 JSON (同源门)
#   6. 零写门 —— 源码写原语扫描 + fixture 真跑前后 shasum 逐字节相同
#   7. 配置/环境错误 → 退出码 3 (vault 不存在 / --now 非法 / 台账 ConfigError 接线)
#   8. --only / skipped 语义 —— 未跑的检查显式列出, 不伪造 ok
#   9. --help 门 —— 三检查名与退出码语义必须在输出里
#  10. live 只读跑通 (live 不可达时 skip; 跑前后全树 sha 逐字节相同)
#
# ⛔ oracle 加载纪律 (probe-B 实测 2026-09-01):
#   - **禁** `from app.api.v1.endpoints.review_overview import ...` 包路由 —— 实测 29.4s /
#     7875 模块 / import 期出站 HTTP (litellm 拉 model cost map) / 写 torchinductor tmp 目录。
#   - 必须 spec_from_file_location 直载文件: 实测 0.95s / 557 模块 / 审计事件 0。
#   - `sys.dont_write_bytecode = True` 必须在 exec_module **之前** —— 否则 oracle 的
#     `from app.config import ...` 闭包会往 backend/app/ 等 3 处写 8 个 .pyc (实测)。
#   - 零写若只看 endpoints/ 目录会假绿 —— 泄漏面在 app/、app/core/、app/utils/ 三处。

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

# ⛔ 必须先于一切被测/oracle 模块加载 —— pytest assertion rewrite 与 import 闭包
# 的 .pyc 写入都由它兜底 (卡文裁判命令另带 PYTHONDONTWRITEBYTECODE=1 双保险)
sys.dont_write_bytecode = True

BACKEND_DIR = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = BACKEND_DIR / "scripts"
for _p in (str(_SCRIPTS_DIR), str(BACKEND_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import vault_lint as vl  # noqa: E402

SCRIPT = _SCRIPTS_DIR / "vault_lint.py"
TODAY = date(2026, 8, 31)
NOW_ARG = "2026-08-31T12:00:00+08:00"

# ---------------------------------------------------------------------------
# oracle (真实 review_overview._vault_entry) —— spec_from_file_location 直载
# ---------------------------------------------------------------------------
_ORACLE = None


def _oracle():
    global _ORACLE
    if _ORACLE is None:
        import importlib.util

        path = BACKEND_DIR / "app" / "api" / "v1" / "endpoints" / "review_overview.py"
        spec = importlib.util.spec_from_file_location("_g82_review_overview_oracle", path)
        assert spec is not None and spec.loader is not None, f"oracle 无法载入: {path}"
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "_vault_entry"), "oracle 模块里没有 _vault_entry"
        _ORACLE = mod
    return _ORACLE


# ---------------------------------------------------------------------------
# fixture builders (全部 tmp_path, 不碰 live vault)
# ---------------------------------------------------------------------------
NODE_FM = "---\ntype: concept\n"


def _node(root: Path, name: str, body: str = "正文\n", extra_fm: str = "") -> None:
    """frontmatter = `---\\ntype: concept\\n{extra_fm}---\\n` —— extra_fm 的字段
    必须在闭合 `---` 之前 (曾有拼接 bug 把 source_board 拼成正文, 4 用例假红)。"""
    p = root / "节点" / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(NODE_FM + extra_fm + "---\n" + body, encoding="utf-8")


def _board(root: Path, name: str, body: str) -> None:
    p = root / "原白板" / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\ntype: whiteboard\n---\n" + body, encoding="utf-8")


def _exam(root: Path, name: str, body: str) -> None:
    p = root / "检验白板" / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\ntype: exam_board\n---\n" + body, encoding="utf-8")


def _projection(root: Path, generated_at: object) -> None:
    """最小合法 v3 投影 (probe-B 实测: 不带 boards/buckets 即可通过 _summarize)。"""
    payload = {
        "schema_version": 3,
        "generated_at": generated_at,
        "stats": {"due_nodes": 0},
        "top_boards": [],
        "upcoming": [],
        "due_nodes": [],
        "ineligible": {"placeholder": []},
    }
    d = root / "outputs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "今日复习.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _clean_vault(root: Path) -> Path:
    """全部检查 ok 的最小 vault: 1 节点有 source_board + 1 节点被板链 + 今日投影。"""
    _node(root, "有源", extra_fm='source_board: "[[原白板/板]]"\n')
    _node(root, "被链")
    _board(root, "板", "- [[节点/被链]]\n")
    _projection(root, "2026-08-31T09:05:05+08:00")
    return root


def _run_cli(vault: Path, *extra: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(vault), *extra],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


def _vault_digest(vault: Path) -> list[tuple[str, str]]:
    return sorted(
        (p.relative_to(vault).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
        for p in vault.rglob("*")
        if p.is_file()
    )


# ---------------------------------------------------------------------------
# 1. 三检查反例 (先红) —— 每个反例 findings 非空; 删掉对应检查逻辑此处必红
# ---------------------------------------------------------------------------
def test_orphan_counterexample_is_caught(tmp_path):
    root = tmp_path / "v"
    _node(root, "孤儿")
    res = vl.check_orphan_nodes(root)
    assert res.status == vl.WARN
    assert [f.subject for f in res.findings] == ["节点/孤儿.md"]


def test_raw_derived_counterexample_is_caught(tmp_path):
    root = tmp_path / "v"
    p = root / "节点" / "混入.md"
    p.parent.mkdir(parents=True)
    p.write_text("---\ntype: recap\n---\n派生内容\n", encoding="utf-8")  # wiki 区混入派生标记 → G3
    res = vl.check_raw_derived(root)
    assert res.status == vl.WARN
    # ⛔ G8-1 原生语义: G3 的 subject = ftype (同类聚合), 路径在 detail 里
    g3 = [f for f in res.findings if f.detail.startswith("[G3]")]
    assert g3, f"G3 未报: {[f.detail for f in res.findings]}"
    assert any(f.subject == "recap" and "节点/混入.md" in f.detail for f in g3)


def test_recap_missing_frontmatter_is_caught(tmp_path):
    root = tmp_path / "v"
    (root / "outputs").mkdir(parents=True)
    (root / "outputs" / "回顾-板-2026-08-31.md").write_text("# 无 frontmatter 的回顾\n", encoding="utf-8")
    res = vl.check_raw_derived(root)
    recap = [f for f in res.findings if "recap" in f.detail]
    assert recap, "回顾-* 缺 type: recap 未被报"
    assert res.details["recap_missing_type"] == 1


def test_freshness_stale_and_corrupt_are_caught(tmp_path):
    v_stale = tmp_path / "stale"
    _projection(v_stale, "2026-08-30T09:05:05+08:00")  # 昨日
    res = vl.check_projection_freshness(v_stale, TODAY)
    assert res.status == vl.WARN and res.details["projection_status"] == "stale"

    v_corrupt = tmp_path / "corrupt"
    (v_corrupt / "outputs").mkdir(parents=True)
    (v_corrupt / "outputs" / "今日复习.json").write_text("{不是json", encoding="utf-8")
    res = vl.check_projection_freshness(v_corrupt, TODAY)
    assert res.status == vl.FAIL and res.details["projection_status"] == "corrupt"


def test_clean_vault_all_ok_exit0(tmp_path):
    root = _clean_vault(tmp_path / "v")
    report = vl.run_checks(root, TODAY)
    assert [c.status for c in report.checks] == [vl.OK, vl.OK, vl.OK], [
        (c.name, c.status, c.summary) for c in report.checks
    ]
    assert vl.exit_code(report) == 0


# ---------------------------------------------------------------------------
# 2. 退出码三态 + CLI 集成
# ---------------------------------------------------------------------------
def test_exit_code_mapping():
    def report(*statuses: str) -> vl.LintReport:
        return vl.LintReport(
            vault="v",
            today="2026-08-31",
            checks=[vl.CheckResult(name=f"c{i}", status=s, summary="") for i, s in enumerate(statuses)],
        )

    assert vl.exit_code(report(vl.OK, vl.OK)) == 0
    assert vl.exit_code(report(vl.OK, vl.WARN)) == 2
    assert vl.exit_code(report(vl.WARN, vl.WARN)) == 2
    assert vl.exit_code(report(vl.OK, vl.FAIL)) == 1
    assert vl.exit_code(report(vl.WARN, vl.FAIL)) == 1  # fail 压过 warn


def test_cli_exit_codes_match_report(tmp_path):
    clean = _run_cli(_clean_vault(tmp_path / "clean"), "--now", NOW_ARG, "--json")
    assert clean.returncode == 0, clean.stderr

    orphan = tmp_path / "orphan"
    _node(orphan, "孤儿")
    _projection(orphan, "2026-08-31T09:05:05+08:00")
    r = _run_cli(orphan, "--now", NOW_ARG)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)

    corrupt = tmp_path / "corrupt"
    (corrupt / "outputs").mkdir(parents=True)
    (corrupt / "outputs" / "今日复习.json").write_text("break", encoding="utf-8")
    r = _run_cli(corrupt, "--now", NOW_ARG)
    assert r.returncode == 1

    r = _run_cli(tmp_path / "不存在", "--now", NOW_ARG)
    assert r.returncode == 3, "vault 不存在必须是配置错误 3, 不是 1"
    assert "配置/环境错误" in r.stderr


def test_cli_config_error_bad_now(tmp_path):
    r = _run_cli(_clean_vault(tmp_path / "v"), "--now", "not-a-date")
    assert r.returncode == 3
    assert "--now" in r.stderr


def test_config_error_from_ledger_wiring(tmp_path, monkeypatch):
    """台账 ConfigError → LintConfigError (→ 退出码 3) 的接线。

    注入的是**异常**而非假数据 —— 测的是 vault_lint 的错误路径接线, 不是用 mock 顶替实现。
    (台账 SHA 单边篡改的行为门在 test_vault_doc_roles.py, 那边退出 2。)
    """

    def boom(*a, **k):
        raise vl.cvr.ConfigError("指纹不符 (模拟单边改 yaml)")

    monkeypatch.setattr(vl.cvr, "load_rules", boom)
    with pytest.raises(vl.LintConfigError):
        vl.run_checks(tmp_path, TODAY)


# ---------------------------------------------------------------------------
# 3. orphan 形态表 —— 逐类「判定/不判定」(验收单「不比什么」表的数据源)
# ---------------------------------------------------------------------------
def test_orphan_link_forms(tmp_path):
    """每类 wikilink 形态的判定结论。meta = (形态说明, 是否判定为入链)。"""
    cases = [
        # (链接写法, 是否判定为入链)
        ("[[被链]]", True),  # 基本形
        ("[[被链|别名]]", True),  # 别名 —— 判定
        ("[[节点/被链]]", True),  # 子路径 —— 判定
        ("![[被链]]", True),  # embed —— 判定 (! 在捕获组外)
        ("[[被链#小节]]", True),  # heading 锚 —— 判定
        ("[[被链#^blockid]]", True),  # block 锚 —— 判定
        ("[[被链.md]]", True),  # 带扩展名 —— 判定
        ("[[别的节点]]", False),  # 链向别处 —— 不判定
        ("", False),  # 无正文链 —— 不判定
    ]
    for link, expected_inbound in cases:
        root = tmp_path / f"c{abs(hash(link))}"
        _node(root, "被链")
        _board(root, "板", f"- {link}\n")
        res = vl.check_orphan_nodes(root)
        subjects = [f.subject for f in res.findings]
        assert ("节点/被链.md" in subjects) != expected_inbound, (
            f"形态 {link!r}: 期望{'入链' if expected_inbound else '不判定'}, 实得 findings={subjects}"
        )


def test_orphan_nfc_nfd_and_casefold(tmp_path):
    # ⛔ 纯 CJK 无分解序列 (NFC=NFD 同字节), 必须用带组合标记的字符构造两种形态;
    #   live 节点/ 实测 14/14 全 NFC 存储 (2026-09-01 unicodedata 实查)
    nfc = "café"  # U+00E9
    nfd = unicodedata.normalize("NFD", nfc)  # e + U+0301
    assert nfc != nfd, "测试前提: 两种归一形态字节不同"

    # 文件名以 NFD 存盘 (macOS APFS 保留原字节), 正文用 NFC 链接 → 判定为入链
    root = tmp_path / "nfd-file"
    p = root / "节点" / f"{nfd}.md"
    p.parent.mkdir(parents=True)
    p.write_text(NODE_FM + "正文\n", encoding="utf-8")
    _board(root, "板", f"- [[{nfc}]]\n")
    assert (p.stem != nfc) and (unicodedata.normalize("NFC", p.stem) == nfc)
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f"NFD 文件名 + NFC 链接应为入链, 实报 {res.findings}"

    # 大小写: 链接大写、文件小写 (Obsidian/APFS 均不敏感) → 判定为入链
    root = tmp_path / "case"
    _node(root, "agent")
    _board(root, "板", "- [[Agent]]\n")
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f"大小写差异应为入链, 实报 {res.findings}"


def test_orphan_exclusions(tmp_path):
    """不判定面: frontmatter 链 / 自链 / 代码块外的其它目录来源。"""
    # frontmatter 里的 wikilink (source_note/up/derived-from) 不算入链 —— 否则
    # source_board 豁免条件变冗余, 两个条件各自不可证伪
    root = tmp_path / "fm-only"
    _node(root, "A", extra_fm='source_note: "[[某板]]"\nup: "[[B]]"\n')
    res = vl.check_orphan_nodes(root)
    assert [f.subject for f in res.findings] == ["节点/A.md"]

    # 自链不算 (节点 A 正文里的 [[A]])
    root = tmp_path / "self"
    _node(root, "A", body="- [[A]]\n")
    res = vl.check_orphan_nodes(root)
    assert [f.subject for f in res.findings] == ["节点/A.md"]

    # 检验白板正文也算入链源 (⚠️ live 上该支零正样本, 见 probe-F 2026-09-01;
    # 本 fixture 是它唯一的正样本 —— 不造这个用例, "三处入链源" 声明比证据宽)
    root = tmp_path / "exam"
    _node(root, "被链")
    _exam(root, "考卷", "- [[节点/被链]]\n")
    res = vl.check_orphan_nodes(root)
    assert res.findings == []


def test_orphan_source_board_exemption(tmp_path):
    root = tmp_path / "v"
    _node(root, "仅有源", extra_fm='source_board: "[[原白板/特征值与特征向量]]"\n')
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], "有 source_board 必须豁免 (probe-F: live 14/14 全有, 此豁免在 live 恒命中)"


# ---------------------------------------------------------------------------
# 3b. round-1 整改 —— 非语义 wikilink / symlink / AUTO 哨兵块 / fail-open / 判别力
# ---------------------------------------------------------------------------
def test_orphan_ignores_nonsemantic_wikilinks(tmp_path):
    """Codex round-1 HIGH-2/HIGH-4 + round-2 HIGH-4: 各类非语义 wikilink 载体都
    不算入链 —— 每种形态单独一组 fixture, 节点必须仍报孤儿。
    变异对照: 删掉 _strip_nonsemantic 后本组必红。"""
    variants = {
        "fenced": "```dataviewjs\n- [[被链]]\n```\n",
        "inline_code": "命令 `- [[被链]] -` 示例\n",
        "html_comment": "<!-- 说明: [[被链]] 已迁移 -->\n",
        "auto_sentinel": (
            "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py · 真相源 = 节点 frontmatter source_board\n"
            "     ⛔ 请勿手改：手改会在下次同步时被覆盖。 -->\n"
            "- [[被链]]\n"
            "<!-- /AUTO-GENERATED -->\n"
        ),
        "multiline": "[[\n被链\n]]\n",
        # round-2 HIGH-4 四组合法 Markdown 变体
        "fence4_with_fence3": "````text\n```\n- [[被链]]\n````\n",  # 四反引号栏内三反引号不关栏
        "double_tick_span": "见 `` [[被链]] `` 说明\n",  # 双反引号 code span
        "multiline_span": "前文 ``\n[[被链]]\n`` 后文\n",  # 跨行 code span
        "unclosed_comment": "<!-- 未闭合注释\n[[被链]]\n",  # 未闭合 comment 剥到 EOF
    }
    for name, board_body in variants.items():
        root = tmp_path / name
        _node(root, "被链")
        _board(root, "板", board_body)
        res = vl.check_orphan_nodes(root)
        subjects = [f.subject for f in res.findings]
        assert subjects == ["节点/被链.md"], f"{name} 形态的伪链豁免了真孤儿: findings={subjects}"


def test_orphan_symlink_never_read(tmp_path):
    """Codex round-1 HIGH-1 + round-2 HIGH-1 三旁路: 文件 symlink / 源目录本身是
    symlink / dangling symlink 都不能豁免真孤儿, 且全部显式记盲区。
    判别锚 = **blind 原因** (blind_detail): 各层防线各有专属原因, 拆任何一层
    都会让对应段红 —— 纵深防御不再吞掉判别力 (round-2 变异 M8/M12a/M12b
    首跑 SURVIVED 的教训: 每段 fixture 都有另一层兜底 = 无判别)。"""
    outside = tmp_path / "outside.md"
    outside.write_text("- [[被链]]\n", encoding="utf-8")
    root = tmp_path / "v"
    _node(root, "被链")

    # 旁路甲: 普通文件 symlink → vault 外 —— is_symlink 层在前, 原因必为 "symlink"
    # (M12a 拆该层后 falls through 到越界层, 原因变 resolves-outside-vault → 本断言红)
    link = root / "原白板" / "external.md"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/被链.md" in subjects, f"vault 外 symlink 内容豁免了真孤儿: {res.findings}"
    assert res.details["blind_detail"]["原白板/external.md"] == "symlink"
    assert res.status == vl.WARN

    # 旁路乙: **原白板 本身**是 symlink 指外 —— 实测 py3.14 rglob 不递归子目录
    # symlink, 但 root.is_dir() 跟随, 以外部目录为根枚举出的文件自身非 symlink:
    # 越界层是唯一防线 (round-2 HIGH-1 的原始形态)
    outside_dir = tmp_path / "outside-dir"
    outside_dir.mkdir()
    (outside_dir / "external2.md").write_text("- [[被链]]\n", encoding="utf-8")
    root2 = tmp_path / "v2"
    _node(root2, "被链")
    (root2 / "原白板").symlink_to(outside_dir, target_is_directory=True)
    res2 = vl.check_orphan_nodes(root2)
    subjects2 = [f.subject for f in res2.findings]
    assert "节点/被链.md" in subjects2, f"源目录 symlink 后代豁免了真孤儿: {res2.findings}"
    assert res2.details["blind_detail"]["原白板/external2.md"] == "resolves-outside-vault"

    # 旁路丙: dangling symlink —— is_file()==False 不得静默消失
    # (round-3 后由 _walk_md 枚举层先记, 原因带 cvr 的「既非目录也非普通文件」字样)
    root3 = tmp_path / "v3"
    _node(root3, "被链")
    (root3 / "原白板").mkdir()
    (root3 / "原白板" / "lost.md").symlink_to(tmp_path / "no-such-target.md")
    res3 = vl.check_orphan_nodes(root3)
    assert "节点/被链.md" in [f.subject for f in res3.findings]
    assert "原白板/lost.md" in res3.details["blind_detail"], f"dangling 必须显式可见: {res3.details['blind_detail']}"

    # 段丁 (is_symlink 层专属判别): 指 vault **内**的文件 symlink —— 越界层放行,
    # 只有 is_symlink 层拦截; 断言拦截原因 == "symlink"
    root4 = tmp_path / "v4"
    _node(root4, "被链")
    _node(root4, "真身")
    (root4 / "原白板").mkdir()
    (root4 / "原白板" / "alias.md").symlink_to(root4 / "节点" / "真身.md")
    res4 = vl.check_orphan_nodes(root4)
    assert res4.details["blind_detail"]["原白板/alias.md"] == "symlink", (
        f"指内 symlink 应由 is_symlink 层拦截并记原因: {res4.details}"
    )


def test_read_text_rejects_symlink_direct(tmp_path):
    """_read_text 的 is_symlink 分支的**直达判别门** (round-2 变异 M8):
    该分支是防御深度最后一道, 前置守卫正常时轮不到它 —— 直接单测锁它本身。"""
    target = tmp_path / "t.md"
    target.write_text("正文", encoding="utf-8")
    link = tmp_path / "l.md"
    link.symlink_to(target)
    assert vl._read_text(link) is None
    assert vl._read_text(target) == "正文"


def test_recap_symlink_outside_not_read(tmp_path):
    """Codex round-2 HIGH-1 第三旁路 + round-3 H1c: 指向 vault 外的 回顾-* symlink
    不得被 recap 子检查跟随读取 —— 记盲区, 且盲区存在时检查 ≥ warn (「没查全」≠「没问题」)。"""
    outside = tmp_path / "outside-recap.md"
    outside.write_text("---\ntype: recap\n---\n外部内容\n", encoding="utf-8")
    root = tmp_path / "v"
    (root / "outputs").mkdir(parents=True)
    (root / "outputs" / "回顾-outside.md").symlink_to(outside)
    res = vl.check_raw_derived(root)
    assert res.status == vl.WARN, f"recap 盲区存在必须 warn, 实为 {res.status}"
    assert res.details["recap_blind"], f"recap 越界 symlink 必须记盲区: {res.details}"


# ⛔ 此处曾残留一个旧版 test_orphan_symlink_never_read（无原因断言），后定义覆盖
#    前定义，pytest 一直在执行无判别力版本 —— 三变异 SURVIVED 的真凶。已删。
#    防回归门见 test_no_duplicate_test_names。


def test_orphan_missing_node_dir_fails_not_ok(tmp_path):
    """Codex round-1 HIGH-3: `节点/` 不存在 → fail —— 「没发现」≠「没去查」。"""
    (tmp_path / "空库").mkdir()
    res = vl.check_orphan_nodes(tmp_path / "空库")
    assert res.status == vl.FAIL
    assert res.findings, "必须有一条 finding 说明检查没查成"
    r = _run_cli(tmp_path / "空库", "--only", "orphan_nodes", "--now", NOW_ARG)
    assert r.returncode == 1, f"节点/ 缺失必须让 CLI 退 1, 实为 {r.returncode}"


def test_orphan_unreadable_node_is_blind_not_ok(tmp_path):
    """Codex round-1 HIGH-3: 唯一节点不可读 → 盲区 + warn, 不是「0 孤儿 ok」。"""
    root = tmp_path / "v"
    p = root / "节点" / "bad.md"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"\xff\xfe---\ntype: concept\n---\n")  # 非 UTF-8
    res = vl.check_orphan_nodes(root)
    assert res.status == vl.WARN, f"有盲区必须 warn (可能是孤儿), 实为 {res.status}"
    assert res.details["blind_spots"] == 1, f"盲区必须恰 1 条 (去重), 实为 {res.details}"


def test_orphan_frontmatter_of_other_files_has_no_power(tmp_path):
    """Codex round-1 HIGH-5 判别力: 别的文件的 frontmatter 指向 A, A 必须仍报孤儿。
    变异对照: 把 _split_frontmatter 变异成「全文当正文」后, 本用例必须红 ——
    (旧版只测 A 自己的 frontmatter, 杀不死该变异 = 门无判别力)。"""
    root = tmp_path / "v"
    _node(root, "A")
    p = root / "节点" / "B.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('---\ntype: concept\nup: "[[A]]"\n---\nB 正文\n', encoding="utf-8")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"B 的 frontmatter up 链豁免了 A: findings={subjects}"


def test_orphan_node_to_node_body_link_counts(tmp_path):
    """Codex round-1 HIGH-5 正向面: 节点正文互链 (节点→节点) 是有效入链。
    变异对照: 把 NODE_DIR 从入链源去掉后本用例必红。"""
    root = tmp_path / "v"
    _node(root, "A")
    _node(root, "B", body="- [[A]]\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" not in subjects, f"节点正文互链没被算作入链: findings={subjects}"
    assert "节点/B.md" in subjects  # B 链了 A 但没人链 B, 也无 source_board → 报


def test_orphan_empty_wikilink_literal(tmp_path):
    """Codex round-1/round-2 HIGH-5 判别力: 板里**只有**空链 `[[]]`/`[[ ]]` 时,
    A 必须仍报孤儿 —— 若实现错把空链映射成有效 target, 本用例必红
    (旧版同 fixture 里放了有效 [[A]], 空链变异杀不死 = 无判别力)。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "- [[]]\n- [[ ]]\n正文无链\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert subjects == ["节点/A.md"], f"空链豁免了 A (判别力失效): findings={subjects}"


def test_orphan_uppercase_md_link_and_null_source_board(tmp_path):
    """Codex round-1 MEDIUM-1a/1b: `[[X.MD]]` 大写扩展名也算入链;
    `source_board: null` 是 YAML null, 不豁免真孤儿。"""
    root = tmp_path / "md-case"
    _node(root, "x")
    _board(root, "板", "- [[X.MD]]\n")
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f"[[X.MD]] 应为入链 (与 cvr 的 suffix.lower() 同口径): {res.findings}"

    root = tmp_path / "null-src"
    _node(root, "y", extra_fm="source_board: null\n")
    res = vl.check_orphan_nodes(root)
    assert [f.subject for f in res.findings] == ["节点/y.md"], "source_board: null 不能豁免"


def test_orphan_subdir_node_crosslink_not_selfchain(tmp_path):
    """Codex round-1 MEDIUM-1c + round-2 MEDIUM-1a: 子目录节点 d1/A 链 [[d2/a]]
    是对 d2/a 的有效入链; 且 A **不因自己的出链被豁免** (自身贡献排除 ——
    旧实现 target "a" 的来源集合含 d1/A.md, A 被自己的链接豁免 = 假阴)。"""
    root = tmp_path / "v"
    sub1 = root / "节点" / "d1"
    sub2 = root / "节点" / "d2"
    sub1.mkdir(parents=True)
    sub2.mkdir(parents=True)
    (sub1 / "A.md").write_text(NODE_FM + "- [[d2/a]]\n", encoding="utf-8")
    (sub2 / "a.md").write_text(NODE_FM + "正文\n", encoding="utf-8")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/d2/a.md" not in subjects, f"d1/A 的跨子目录链被误当自链: findings={subjects}"
    assert "节点/d1/A.md" in subjects, f"A 被自己的出链豁免 (自身贡献未排除): findings={subjects}"


def test_orphan_quoted_null_is_string_not_yaml_null(tmp_path):
    """Codex round-2 MEDIUM-1b: `source_board: "null"` 是引号强制字符串 (YAML 语义),
    不是 null —— 它是**有效值**, 节点照常豁免。
    判别力: 若实现先剥引号再判 null 字面 (round-2 批的变异), 返回 None → 不豁免 →
    A 被报 → 本用例红。"""
    root = tmp_path / "v"
    _node(root, "q", extra_fm='source_board: "null"\n')
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f'带引号的 "null" 是有效字符串值, 应豁免 (被误判成 YAML null 才会报): {res.findings}'


def test_resolve_today_default_is_shanghai_not_host_local(monkeypatch):
    """Codex round-1 MEDIUM-2 + round-2 MEDIUM-2: 环境无关地锁死默认分支的时区语义。

    手法: 把 vl 命名空间的 datetime 类整个换成固定钟 (不读系统钟), 并把
    _TZ_SHANGHAI 换成 New York (UTC-5) —— 判别锚 = **时区对象本身**, 与宿主
    TZ/当前日期无关:
      - `astimezone(宿主本地)` mutant → NY 语义丢失 → 得 UTC 日 → 红;
      - `_utcnow().date()` mutant → 完全绕过时区 → 得 UTC 日 → 红;
      - `date.today()` mutant → 读系统真实钟 (宿主 +08 的今天) ≠ NY 日 → 红。
    """
    from datetime import datetime as real_datetime
    from zoneinfo import ZoneInfo

    class _FrozenDT(real_datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ARG003
            return cls(2026, 8, 31, 23, 0, tzinfo=timezone.utc)  # UTC 23:00 → NY 18:00 同日

    ny = ZoneInfo("America/New_York")
    monkeypatch.setattr(vl, "datetime", _FrozenDT)
    monkeypatch.setattr(vl, "_TZ_SHANGHAI", ny)
    assert vl.resolve_today(None) == date(2026, 8, 31), (
        "默认分支必须按 _TZ_SHANGHAI (此处=NY) 换算: UTC 23:00 = NY 18:00 = 08-31; "
        "宿主本地/UTC 直取/date.today() 等变异会给出不同结果"
    )


def test_cli_help_writes_no_pyc_without_env(tmp_path):
    """Codex round-1 BLOCKER-1 的行为门 + round-2 MEDIUM-4:
    无 PYTHONDONTWRITEBYTECODE 时 CLI 直跑 --help 也不得写任何 .pyc
    (隔离副本上实测, 生产 guard 行被删时本门必红)。
    副本三件套 (vault_lint + cvr + yaml) 同目录 —— vault_lint 以自身所在目录
    为 import 根, 拆开复制会 ModuleNotFoundError。"""
    import shutil

    for name in ("vault_lint.py", "check_vault_doc_roles.py", "vault_doc_roles.yaml"):
        shutil.copyfile(_SCRIPTS_DIR / name, tmp_path / name)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX")}
    proc = subprocess.run(
        [sys.executable, str(tmp_path / "vault_lint.py"), "--help"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    pycs = list(tmp_path.rglob("*.pyc"))
    assert pycs == [], f"无环境变量跑 --help 产生了字节码: {pycs}"


# ---------------------------------------------------------------------------
# 4. freshness 同源锁 —— 活 oracle 比对 + 实测快照锚
# ---------------------------------------------------------------------------
#: probe-B 2026-09-01 对真实 _vault_entry 的实测矩阵 (today=2026-08-31)。
#: 机制列来自逐条归因: DATE_COMPARE / REGEX_REJECT / ASTIMEZONE_RAISE(OverflowError) /
#: SUMMARIZE_TYPE_REJECT —— stale 一档盖 3 种机制, 只锁 status 对机制层变异是盲的,
#: 故 h2/h3 (唯二触达 OverflowError 兜底的用例) 必须在场。
FRESHNESS_MATRIX = [
    # (generated_at, 期望 oracle status, 机制)
    ("2026-08-31T09:05:05+08:00", "ok", "DATE_COMPARE"),
    ("2026-08-30T09:05:05+08:00", "stale", "DATE_COMPARE 昨日"),
    ("2026-08-31T01:05:05Z", "ok", "DATE_COMPARE Z 后缀"),
    ("2026-08-30T23:00:00Z", "ok", "DATE_COMPARE 跨午夜: UTC 昨日 23:00 = 上海今日"),
    ("2026-08-31T00:30:00+08:00", "ok", "DATE_COMPARE 上海今日凌晨"),
    ("2026-08-31T17:05:05Z", "stale", "DATE_COMPARE 上海日翻篇: UTC 17:05 = 上海次日"),
    ("2026-09-01T00:30:00+08:00", "stale", "DATE_COMPARE 次日"),
    ("2026-08-31", "stale", "REGEX_REJECT 纯日期"),
    ("2026-08-31T09:05:05", "stale", "REGEX_REJECT 无时区"),
    ("", "stale", "REGEX_REJECT 空串"),
    ("20260831", "stale", "REGEX_REJECT 数字串"),
    ("+9999-08-31T09:05:05+08:00", "stale", "REGEX_REJECT 年份越界"),
    ("2026-08-31T09:05:05+08:60", "stale", "REGEX_REJECT 非法分钟"),
    ("2026-08-31T09:05:05+15:00", "stale", "REGEX_REJECT 越界时区偏移"),
    ("9999-12-31T23:59:59+00:00", "stale", "ASTIMEZONE_RAISE OverflowError"),
    ("0001-01-01T00:00:00+14:00", "stale", "ASTIMEZONE_RAISE OverflowError"),
    (20260831, "corrupt", "SUMMARIZE_TYPE_REJECT 非字符串"),
]


@pytest.mark.parametrize("generated_at,expected,mechanism", FRESHNESS_MATRIX, ids=[m for _, _, m in FRESHNESS_MATRIX])
def test_freshness_lock_with_live_oracle(tmp_path, generated_at, expected, mechanism):
    """同源锁主断言 = **活比对**: 同一 fixture 同时喂真实 _vault_entry 与 _projection_status。"""
    root = tmp_path / "v"
    _projection(root, generated_at)
    entry = _oracle()._vault_entry(root, TODAY)
    status, _error, _gen = vl._projection_status(root, TODAY)
    assert status == entry["status"] == expected, (
        f"机制={mechanism}: vault_lint={status} oracle={entry['status']} 期望={expected} "
        f"oracle_error={entry.get('error')!r}"
    )
    if entry["status"] == "ok":
        assert entry["projection"]["generated_at"] is not None


def test_freshness_no_projection_matches_oracle(tmp_path):
    status, _e, _g = vl._projection_status(tmp_path, TODAY)
    entry = _oracle()._vault_entry(tmp_path, TODAY)
    assert status == entry["status"] == "no_projection"


def test_freshness_corrupt_report_content_differs_but_status_locks(tmp_path):
    """error 消息两侧各自措辞 (不锁内容), 只锁 status —— 如实声明, 不装同文。"""
    root = tmp_path / "v"
    (root / "outputs").mkdir(parents=True)
    (root / "outputs" / "今日复习.json").write_text("[]", encoding="utf-8")  # 合法 JSON 非 object
    status, error, _g = vl._projection_status(root, TODAY)
    entry = _oracle()._vault_entry(root, TODAY)
    assert status == entry["status"] == "corrupt"
    assert error  # vault_lint 侧必须给出台账可读的原因


def test_today_resolution_is_shanghai_not_host_local():
    # UTC 2026-08-31T23:00Z = 上海 2026-09-01 07:00 —— 上海日已翻篇
    assert vl.resolve_today("2026-08-31T23:00:00Z") == date(2026, 9, 1)
    # 无时区输入按上海解释 (不引入第二种默认)
    assert vl.resolve_today("2026-08-31") == date(2026, 8, 31)
    assert vl.resolve_today("2026-08-31T12:00:00+08:00") == date(2026, 8, 31)
    with pytest.raises(vl.LintConfigError):
        vl.resolve_today("garbage")


# ---------------------------------------------------------------------------
# 5. --json 与文本同源门
# ---------------------------------------------------------------------------
_TEXT_STATUS_RE = re.compile(r"^\[vault-lint\] (\S+) status=(\S+)", re.M)


def test_json_and_text_are_same_source(tmp_path):
    root = tmp_path / "v"
    _node(root, "孤儿")
    _projection(root, "2026-08-30T09:05:05+08:00")  # stale
    proc = _run_cli(root, "--now", NOW_ARG)
    assert proc.returncode == 2
    text_rows = dict(_TEXT_STATUS_RE.findall(proc.stdout))
    payload = json.loads(_run_cli(root, "--now", NOW_ARG, "--json").stdout)

    json_rows = {c["name"]: c["status"] for c in payload["checks"]}
    assert text_rows == json_rows, "文本与 JSON 的 per-check status 必须逐项相等 (同源)"
    assert proc.returncode == payload["summary"]["exit_code"]
    assert payload["summary"]["checks_skipped"] == []
    # 同一输入跑两次, JSON 输出必须语义稳定 (排除随机序/时间依赖)
    again = json.loads(_run_cli(root, "--now", NOW_ARG, "--json").stdout)
    assert again == payload, "同输入两次运行 JSON 输出不一致 —— 存在隐藏的非确定性"


def test_json_findings_match_text_findings(tmp_path):
    root = tmp_path / "v"
    _node(root, "孤儿甲")
    _node(root, "孤儿乙")
    _projection(root, "2026-08-31T09:05:05+08:00")
    text = _run_cli(root, "--now", NOW_ARG).stdout
    payload = json.loads(_run_cli(root, "--now", NOW_ARG, "--json").stdout)
    orphans = next(c for c in payload["checks"] if c["name"] == "orphan_nodes")
    assert {f["subject"] for f in orphans["findings"]} == {"节点/孤儿甲.md", "节点/孤儿乙.md"}
    for f in orphans["findings"]:
        assert f["subject"] in text, "JSON finding 必须也出现在文本渲染里"


# ---------------------------------------------------------------------------
# 6. --only / skipped
# ---------------------------------------------------------------------------
def test_only_skips_explicitly(tmp_path):
    root = _clean_vault(tmp_path / "v")
    report = vl.run_checks(root, TODAY, only=["orphan_nodes"])
    assert [c.name for c in report.checks] == ["orphan_nodes"]
    assert report.skipped == ["raw_derived_confusion", "projection_freshness"]
    assert vl.exit_code(report) == 0  # skipped 不参与聚合

    r = _run_cli(root, "--now", NOW_ARG, "--only", "orphan_nodes", "--json")
    payload = json.loads(r.stdout)
    assert payload["summary"]["checks_run"] == ["orphan_nodes"]
    assert payload["summary"]["checks_skipped"] == ["raw_derived_confusion", "projection_freshness"]

    # --only 场景的同源门: 文本的 status=skipped 行 ↔ JSON checks_skipped 逐项相等
    text = _run_cli(root, "--now", NOW_ARG, "--only", "orphan_nodes").stdout
    text_rows = dict(_TEXT_STATUS_RE.findall(text))
    assert set(text_rows) == set(payload["summary"]["checks_run"]) | set(payload["summary"]["checks_skipped"]), (
        f"文本检查行集合与 JSON 不一致: text={sorted(text_rows)}"
    )
    for name in payload["summary"]["checks_skipped"]:
        assert text_rows[name] == "skipped", f"{name} 在文本里必须是 skipped, 实为 {text_rows[name]}"


def test_argparse_usage_errors_exit_3_not_2(tmp_path):
    """Codex round-1 HIGH-6: argparse 默认 exit(2) 与「有 warn」的 2 撞码 ——
    用法错误归 3 (配置/环境错误族 = lint 没跑成)。"""
    # 缺 --vault
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    bad = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, env=env, timeout=60)
    assert bad.returncode == 3, f"缺 --vault 必须 rc=3 (用法错误), 实为 {bad.returncode}"
    assert "--vault" in bad.stderr
    # --only 非法值
    r = _run_cli(_clean_vault(tmp_path / "v"), "--only", "no_such_check")
    assert r.returncode == 3, f"--only 非法值必须 rc=3, 实为 {r.returncode}"
    assert "no_such_check" in r.stderr


# ---------------------------------------------------------------------------
# 7. 零写门
# ---------------------------------------------------------------------------
def test_vault_lint_source_has_no_write_primitives():
    src = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        r"\.write_text\(",
        r"\.write_bytes\(",
        r"\.mkdir\(",
        r"\.unlink\(",
        r"\.touch\(",
        r"\brmtree\b",
        r"\bshutil\.",
        r"os\.remove\(",
        r"os\.rename\(",
        r"""open\([^)]*["'][wax]""",
        r"\bmkstemp\b",
        r"\bNamedTemporaryFile\b",
    ]
    for pat in forbidden:
        assert not re.search(pat, src), f"vault_lint.py 含写原语 {pat!r} —— 违反零写铁律"


def test_vault_lint_never_writes_fixture(tmp_path):
    """真跑前后 fixture 全树 sha 逐字节相同 (三检查全跑 + CLI 子进程各一遍)。"""
    root = _clean_vault(tmp_path / "v")
    _node(root, "孤儿")
    before = _vault_digest(root)
    vl.run_checks(root, TODAY)
    assert _vault_digest(root) == before, "run_checks 改动了 vault"
    proc = _run_cli(root, "--now", NOW_ARG)
    assert _vault_digest(root) == before, "CLI 子进程改动了 vault"
    assert proc.returncode == 2  # 有孤儿, 顺带确认跑的是真检查


def test_bytecode_guard_is_armed():
    """元门: 本进程的 .pyc 写入开关必须是关的 (oracle exec 与被测模块 import 都依赖它)。

    probe-B 实测: 缺了它, oracle 的 import 闭包会往 backend/app/、app/core/、app/utils/
    三处写 8 个 .pyc —— 光看 endpoints/ 会假绿。
    """
    assert sys.dont_write_bytecode is True
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1", (
        "卡文裁判命令要求 PYTHONDONTWRITEBYTECODE=1; 缺失时 sys.dont_write_bytecode "
        "兜底仍成立, 但环境变量门是双保险的第二道, 不许悄悄失守"
    )


# ---------------------------------------------------------------------------
# 8. --help 门 (卡文裁判 3)
# ---------------------------------------------------------------------------
def test_help_lists_checks_and_exit_semantics():
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, env=env, timeout=60)
    assert proc.returncode == 0
    out = proc.stdout
    for name in vl.CHECKS:
        assert name in out, f"--help 缺检查名 {name}"
    for token in ("0", "2", "1", "3"):
        assert token in out
    assert "warn" in out and "fail" in out and "配置/环境错误" in out
    # Codex round-1 MEDIUM-4: 分级规则必须出现在 --help, 不能只活在源码里
    assert "节点/" in out and "不存在" in out, "--help 缺 orphan 的 fail 分级规则"
    assert "corrupt" in out and "stale" in out, "--help 缺 freshness 的分级规则"
    assert "scan 盲区" in out or "盲区" in out, "--help 缺 orphan 盲区降 warn 的规则"
    # Codex round-5 M3: raw_derived 的盲区触发 warn 须专属可见 (只查任意"盲区"会把
    # orphan 的盲区句当替身 —— round-6 LOW 判别力修正)
    assert re.search(r"raw_derived_confusion\s+\S[^\n]*\n\s+warn = [^\n]*\n\s+或存在扫描盲区 \(G8/G10/G11", out), (
        "--help 缺 raw_derived 专属的 G8/G10/G11 盲区 warn 规则 (逐行锚定, 防 DOTALL 跨段替身)"
    )
    assert "dont_write_bytecode" in out.lower(), "--help 缺零写兜底声明"


# ---------------------------------------------------------------------------
# 9. live 只读跑通 (live 不可达时 skip; 卡文裁判 2 的单测内缩样)
# ---------------------------------------------------------------------------
_LIVE_VAULT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault")


def test_live_vault_readonly_and_runs():
    if not _LIVE_VAULT.is_dir():
        pytest.skip(f"live vault 不可达: {_LIVE_VAULT}")
    before = _vault_digest(_LIVE_VAULT)
    report = vl.run_checks(_LIVE_VAULT, TODAY)
    assert _vault_digest(_LIVE_VAULT) == before, "live vault 被改动 —— 零写铁律被打破"
    assert vl.exit_code(report) in (0, 1, 2)
    # 卡文裁判 2 的单测侧缩影: rc 与 JSON summary 一致
    assert vl.exit_code(report) == vl.report_to_json(report)["summary"]["exit_code"]
    # orphan 检查的如实性: 节点数必须与 live 实况一致 (probe-F 实测 14)
    orphan = next(c for c in report.checks if c.name == "orphan_nodes")
    assert orphan.details["nodes_scanned"] > 0, "live 节点/ 扫描数为 0 —— 扫描根错了"


def test_no_duplicate_test_names():
    """⛔ 防回归门 (round-2 收官自审发现): 同名测试函数后定义覆盖前定义 ——
    pytest 收集只报一个, 被覆盖的判别力静默消失 (三变异 SURVIVED 的真凶)。
    本文件任何 test_* 重名 = 直接红。"""
    import ast as _ast

    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = [
        n.name
        for node in _ast.walk(tree)
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef))
        for n in [node]
        if n.name.startswith("test_")
    ]
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert dupes == [], f"存在重名测试 (后定义静默覆盖前定义): {dupes}"


# ---------------------------------------------------------------------------
# 3c. round-3 整改 —— 枚举层盲区 / 物理路径去重 / freshness 越界 / span 等长
# ---------------------------------------------------------------------------
def test_orphan_nested_symlink_dir_recorded_not_silent(tmp_path):
    """Codex round-3 H1a: `节点/sub -> vault 外目录` —— os.walk 不深入嵌套目录
    symlink, 其后代整棵不在扫描面 → 必须显式记盲区 (rglob 时代是 0 盲区静默消失);
    外部内容的 [[x]] 不得豁免 x。"""
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "A.md").write_text(NODE_FM + "- [[x]]\n", encoding="utf-8")
    root = tmp_path / "v"
    _node(root, "x")
    sub = root / "节点" / "sub"
    sub.parent.mkdir(parents=True, exist_ok=True)
    sub.symlink_to(outside_dir, target_is_directory=True)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/x.md" in subjects, f"嵌套 symlink 目录后代豁免了真孤儿: {res.findings}"
    assert any("sub" in rel for rel in res.details["blind_detail"]), (
        f"嵌套 symlink 目录必须记盲区: {res.details['blind_detail']}"
    )
    assert res.status == vl.WARN


def test_orphan_directory_alias_self_link_uses_realpath(tmp_path):
    """Codex round-3 H1b: `原白板 -> 节点/` 目录别名 —— 同一物理文件以别名路径
    贡献入链, 相对路径键会绕过自身排除。realpath 归并后 A 必须仍报孤儿。
    变异对照: 入链键退回相对路径后本用例红。"""
    outside_board = tmp_path / "real-board"
    outside_board.mkdir()
    root = tmp_path / "v"
    (root / "节点").mkdir(parents=True)
    (root / "节点" / "A.md").write_text(NODE_FM + "- [[A]]\n", encoding="utf-8")
    (root / "原白板").symlink_to(root / "节点", target_is_directory=True)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"目录别名的自贡献豁免了 A (realpath 归并失效): {res.findings}"


def test_orphan_unreadable_subtree_is_blind(tmp_path):
    """Codex round-3 H2: `节点/locked`(chmod 000)`/A.md` —— 不可读子树整棵消失
    时代已终结: os.walk(onerror) 必须把子树记为盲区, 且同目录其余节点照常判定。"""
    if os.geteuid() == 0:
        pytest.skip("root 用户不受 chmod 000 限制")
    root = tmp_path / "v"
    _node(root, "可见")
    locked = root / "节点" / "locked"
    locked.mkdir(parents=True)
    (locked / "A.md").write_text(NODE_FM + "正文\n", encoding="utf-8")
    locked.chmod(0o000)
    try:
        res = vl.check_orphan_nodes(root)
    finally:
        locked.chmod(0o755)  # 还原, 让 tmp_path 清理不炸
    assert any("locked" in rel for rel in res.details["blind_detail"]), (
        f"不可读子树必须记盲区: {res.details['blind_detail']}"
    )
    assert res.status == vl.WARN
    subjects = [f.subject for f in res.findings]
    assert "节点/locked/A.md" not in subjects  # 它不可读未判定, 不在 findings


def test_projection_symlink_outside_is_corrupt(tmp_path):
    """Codex round-3 H1d: `outputs -> vault 外目录` 且外部投影是当天 ——
    freshness 不得读取 vault 外文件, 判 corrupt (fail)。"""
    outside = tmp_path / "outside-outputs"
    (outside / "outputs").mkdir(parents=True)
    payload = {
        "schema_version": 3,
        "generated_at": "2026-08-31T09:05:05+08:00",
        "stats": {"due_nodes": 0},
        "top_boards": [],
        "upcoming": [],
        "due_nodes": [],
        "ineligible": {"placeholder": []},
    }
    (outside / "outputs" / "今日复习.json").write_text(json.dumps(payload), encoding="utf-8")
    root = tmp_path / "v"
    root.mkdir()
    (root / "outputs").symlink_to(outside / "outputs", target_is_directory=True)
    status, error, _gen = vl._projection_status(root, TODAY)
    assert status == "corrupt", f"越界投影必须 corrupt, 实为 {status} ({error})"
    assert "越出 vault" in (error or "") or "symlink" in (error or "")
    # ⛔ 如实登记: 越界面本实现比 oracle **严** (oracle 不查越界直接读) —— 同源锁只锁
    #    合法 v3 投影 (§「不比什么」), 这一分叉方向 = 更安全, 不做伪装对齐。


def test_code_span_equal_length_runs(tmp_path):
    """Codex round-3 H3: code span 开闭反引号必须等长 —— `` ``foo` [[A]]`` ``
    的单反引号不是双反引号 span 的 closer, [[A]] 在 span 内必须被剥。
    变异对照: 退回 `(`+)[^`]*`+` 后本用例红。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "``foo` [[A]]``\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert subjects == ["节点/A.md"], f"不等长 closer 让 [[A]] 逃出 span: findings={subjects}"


# ---------------------------------------------------------------------------
# 3d. round-4 整改 —— G8/G10/G11 盲区计入 raw_derived 状态 / CommonMark maximal run
# ---------------------------------------------------------------------------
def test_raw_derived_g8_blind_forces_warn(tmp_path):
    """Codex round-4 HIGH-1: G8/G10/G11 扫描面盲区 (不只 recap_blind) 必须让
    raw_derived ≥ warn —— `节点/sub -> vault 外` 时 G8 在场, 不得假绿 ok。
    CLI JSON 契约一并锁 (Codex round-4 M18-2: 只查内部 CheckResult 不够)。"""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "A.md").write_text(NODE_FM + "正文\n", encoding="utf-8")
    root = tmp_path / "v"
    (root / "节点").mkdir(parents=True)
    (root / "节点" / "sub").symlink_to(outside, target_is_directory=True)
    res = vl.check_raw_derived(root)
    assert res.status == vl.WARN, f"G8 盲区在场必须 warn, 实为 {res.status}"
    assert res.details["blind_spots"] >= 1
    # CLI JSON 契约: warn/blind_spots 必须透传到 --json 输出
    r = _run_cli(root, "--only", "raw_derived_confusion", "--now", NOW_ARG, "--json")
    payload = json.loads(r.stdout)
    chk = payload["checks"][0]
    assert chk["status"] == "warn" and chk["details"]["blind_spots"] >= 1, chk
    assert r.returncode == 2


def test_code_span_commonmark_maximal_run(tmp_path):
    """Codex round-4 HIGH-2 (MarkdownIt 对照): `` ``[[A]] ` foo`` `` 整体是一个
    双反引号 span —— (\\`+)[^\\`]*\\1 会回溯成空 span + 单反引号 span, [[A]] 逃出。
    maximal run 配对算法下 [[A]] 必须被剥, A 报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "``[[A]] ` foo``\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert subjects == ["节点/A.md"], f"maximal-run 语义缺失, [[A]] 逃出 span: {subjects}"


def test_projection_outside_guard_precedes_read(tmp_path, monkeypatch):
    """Codex round-4 M17: 越界守卫必须在**读取之前** —— 用注入「读取即炸」的
    _read_text 锁顺序 (只断言结果时, 「先读再返回 corrupt」的精准变异不被抓)。"""
    outside = tmp_path / "outside-outputs"
    (outside / "outputs").mkdir(parents=True)
    (outside / "outputs" / "今日复习.json").write_text("{}", encoding="utf-8")
    root = tmp_path / "v"
    root.mkdir()
    (root / "outputs").symlink_to(outside / "outputs", target_is_directory=True)

    def boom(_path: Path) -> None:
        raise AssertionError("越界投影不得被读取 —— 守卫必须在 _read_text 之前")

    monkeypatch.setattr(vl, "_read_text", boom)
    status, _error, _gen = vl._projection_status(root, TODAY)
    assert status == "corrupt"


# ---------------------------------------------------------------------------
# 3e. round-5 整改 —— code span closer 严格等长 / 剥除空格占位
# ---------------------------------------------------------------------------
def test_code_span_closer_must_equal_opener(tmp_path):
    """Codex round-5 HIGH-1 (MarkdownIt 对照): `` `x``[[A]]` `` 的 opener/closer
    均为单反引号 (content 含双反引号) —— "≥ opener" 是 fenced 的规则不是 span 的,
    双反引号不得充当单反引号 span 的 closer; [[A]] 在 span 内必须被剥, A 报孤儿。
    变异对照: M16 (closer 退回 >= 语义) 指定杀本用例。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "`x``[[A]]`\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert subjects == ["节点/A.md"], f"双反引号被误当 closer, [[A]] 逃出 span: {subjects}"


def test_code_span_removal_leaves_placeholder_not_concatenation(tmp_path):
    """Codex round-5 HIGH-2: 剥除 span 后必须**空格占位** —— 空串拼接会把
    "[`x`[A]]" 拼成原文不存在的 "[[A]]" 伪入链, 反向隐藏真孤儿 A。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "[`x`[A]]\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert subjects == ["节点/A.md"], f"空串拼接制造伪入链 [[A]]: {subjects}"


# ---------------------------------------------------------------------------
# 3f. round-6 整改 —— 非语义形态不采纳 (r7 重构为 token 流后由 M7 text 过滤承重)
# ---------------------------------------------------------------------------
def test_code_span_inside_wikilink_does_not_create_link(tmp_path):
    """Codex round-6 HIGH-1: `` [[A`x`]] `` 的 MarkdownIt 解析 = text("[[A") +
    code_span("x") + text("]]") —— 原文没有指向 A 的链接 (target 是 "A`x`" 这个
    不存在的文件)。区间法在原文上扫描, 不得把 span 剥除后的 "[[A ]]" 当成 A 的入链。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "[[A`x`]]\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"span 剥除制造了 A 的伪入链: {res.findings}"


def test_html_comment_inside_bracket_does_not_create_link(tmp_path):
    """Codex round-6 HIGH-2: "[<!--x-->[A]]" 原文没有 [[..]] —— 注释空串删除后
    拼接出的 "[[A]]" 是伪入链。区间法在原文上扫描, A 必须仍报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "[<!--x-->[A]]\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"注释删除拼接出伪入链 [[A]]: {res.findings}"


def test_escaped_backtick_is_not_delimiter(tmp_path):
    """Codex round-6 M1 (CommonMark backslash escapes): 反引号被转义后是普通文本 ——
    [[A]] 是**真入链**, 不得被剥掉并把 A 误报成孤儿 (旧行为的 fail-open)。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "\\`x [[A]]\\`\n")
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f"转义反引号后的真入链被剥掉, A 被误报: {res.findings}"


def test_code_span_does_not_span_blank_line(tmp_path):
    """Codex round-6 M2 (CommonMark: code span 不跨段落): "`x\\n\\n[[A]]`" 是两个
    text block, [[A]] 是**真入链** —— 跨空行配对会把它剥掉并误报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "`x\n\n[[A]]`\n")
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f"span 跨空行配对剥掉了真入链, A 被误报: {res.findings}"


# ---------------------------------------------------------------------------
# 3g. round-8 整改 —— AUTO 盲化等行数改写 (保 fence 连续性) / map 回原文转义判定
# ---------------------------------------------------------------------------
def test_auto_fence_cross_keeps_fence_state(tmp_path):
    """Codex round-8 H1: AUTO 段吞掉 fence opener 后, 跨段 fence 内的 [[A]] 不得
    被当正文入链 (切分逐段解析时代的 false-green)。等行数盲化保留 fence 标记行,
    整文解析 fence 状态连续 → A 报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py · source\n"
        "     note -->\n"
        "~~~text\n"
        "<!-- /AUTO-GENERATED -->\n"
        "[[A]]\n"
        "~~~\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"跨段 fence 状态丢失, [[A]] 被当入链: {res.findings}"


def test_unclosed_auto_segment_blinds_to_eof(tmp_path):
    """Codex round-8 H2: 未闭合 AUTO 段到 EOF 不得降级成普通正文 —— 机器成员
    [[A]] 必须保持盲, A 报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py · source\n     note -->\n- [[A]]\n"
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"未闭合 AUTO 段降级, 机器成员豁免了 A: {res.findings}"


def test_escaped_brackets_are_not_wikilink(tmp_path):
    """Codex round-8 H3a (Obsidian 规则): `\\[\\[A\\]\\]` 转义方括号不生成链接 ——
    不得采纳为 A 的入链 (真无链 baseline = A 报孤儿)。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "\\[\\[A\\]\\]\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"转义方括号被当真链接: {res.findings}"


def test_html_entity_brackets_fail_closed(tmp_path):
    """Codex round-8 H3b: `&#91;&#91;A&#93;&#93;` 实体解码后的 [[ 在原文中无裸 [[ ——
    不采纳 (fail-closed 多报孤儿方向); Obsidian 实体行为未定, 差异登记「不比什么」。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "&#91;&#91;A&#93;&#93;\n")
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"实体形式被当真链接: {res.findings}"


def test_missing_markdown_it_is_config_error(tmp_path, monkeypatch):
    """Codex round-8 M1: markdown_it 缺包 = 配置/环境错误 → LintConfigError (CLI rc=3),
    不许裸 ModuleNotFoundError 崩成 rc=1。sys.modules[name]=None 触发 import 语义的
    ImportError, 精准模拟缺包。"""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "markdown_it" or name.startswith("markdown_it."):
            raise ImportError("simulated missing markdown_it")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    setattr(vl, "_md", None)  # 重置 lazy 缓存
    with pytest.raises(vl.LintConfigError):
        vl._md_parser()
    with pytest.raises(vl.LintConfigError):
        vl.run_checks(_clean_vault(tmp_path / "v"), TODAY)  # run_checks 接线: 冒泡 → main 退 3
        # (须含 orphan_nodes —— mdit 只在 _wikilink_targets; 空目录 fail-fast 走不到)
    setattr(vl, "_md", None)  # 还原缓存, 防污染后续用例


# ---------------------------------------------------------------------------
# 3h. round-9 整改 —— AUTO 容器上下文 / 嵌套深度 / 逐 match 原文绑定
# ---------------------------------------------------------------------------
def test_auto_blinding_preserves_list_container(tmp_path):
    """Codex round-9 H1: list 容器内的 AUTO 段 —— 盲化行必须保留原行前导空白
    （列 0 注释会终止 list, fence 退化 code_block, [[A]] 泄漏为入链）。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "- item\n"
        "     <!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py source\n"
        "     note -->\n"
        "     ~~~text\n"
        "     <!-- /AUTO-GENERATED -->\n"
        "   [[A]]\n"
        "     ~~~\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"盲化行破坏 list 容器, [[A]] 泄漏: {res.findings}"


def test_auto_bad_info_string_not_fence(tmp_path):
    """Codex round-9 H1b: AUTO 段内 `` ```bad` [[A]] `` 的 info string 含反引号 ——
    按 CommonMark 不是 fence, 不得作为 fence 标记行原样保留; [[A]] 必须随行盲化。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py · source\n"
        "```bad` [[A]]\n"
        "<!-- /AUTO-GENERATED -->\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert subjects == ["节点/A.md"], f"坏 info string 行未随段盲化, [[A]] 泄漏为入链: {res.findings}"


def test_nested_auto_begin_depth(tmp_path):
    """Codex round-9 H2: 嵌套 BEGIN —— 外层未闭合时, 内层 BEGIN 的第一个 END 不得
    提前关闸（布尔状态机 → 深度计数）。[[A]] 仍在嵌套段内, 必须盲, A 报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py outer -->\n"
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py inner -->\n"
        "<!-- /AUTO-GENERATED -->\n"
        "[[A]]\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"嵌套 BEGIN 提前关闸, [[A]] 泄漏: {res.findings}"


def test_decoded_match_binds_to_raw_target(tmp_path):
    """Codex round-9 H3 逐 match 绑定: 同一 inline token 内 [[B]]（真）与
    \\[\\[A\\]\\]（转义假）并存时, 只有 B 采纳; A 的 decoded target 必须在原文
    裸 target 集合中有对应, 否则拒绝 → A 报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    _node(root, "B")
    _board(root, "板", "[[B]] and \\[\\[A\\]\\]\n")
    res = vl.check_orphan_nodes(root)
    subjects = sorted(f.subject for f in res.findings)
    assert subjects == ["节点/A.md"], f"逐 match 绑定失效 (A 应报 B 不应报): {subjects}"


def test_wikilink_row_model_matches_mdit(tmp_path):
    """Codex round-9 M5: 行模型统一 —— splitlines 会把 VT/FF 等当行界导致盲化行号与
    token.map 错位; 统一按 \\n 分割后, VT 分隔的真链接必须被采纳（A 不报）。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "前缀\x0b行\n[[A]]\n")
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f"VT 行模型错位导致真入链丢失: {res.findings}"


def test_double_backslash_escape_is_real_link(tmp_path):
    """Codex round-9 M7: 成对反斜杠（\\\\）后是真链接 —— 奇偶判定取代单字符负向断言;
    escaped 用例（单反斜杠）仍拒绝。"""
    root = tmp_path / "v"
    _node(root, "A")
    _board(root, "板", "\\\\[[A]]\n")  # 两个反斜杠 + [[A]] —— 成对反斜杠 = 字面反斜杠
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f"成对反斜杠后的真链接被误拒: {res.findings}"


# ---------------------------------------------------------------------------
# 3i. round-10 整改 —— fence 保留谓词收严 / 畸形 END 词边界 / 实体解码同基 / anomalies
# ---------------------------------------------------------------------------
def test_tilde_fence_info_with_backtick_kept(tmp_path):
    """Codex round-10 H1 —— **已选口径 (AUTO 段优先)**: info 含反引号的 tilde 行
    不是纯 fence 标记, 随段盲化 ([[A]] 采纳, A 不报); anomaly 披露盲化分支。
    (mdit fence 语义下 A 报——两种口径分歧登记验收单裁决点。)"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py source -->\n"
        "~~~lang`\n"
        "<!-- /AUTO-GENERATED -->\n"
        "[[A]]\n"
        "~~~\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    # ⛔ 已选口径 (r10, 裁决点): **AUTO 段优先** —— info 含反引号的行不是纯 fence
    # 标记, 随段盲化 ([[A]] 采纳, A 不报)。mdit fence 语义会判该行为 fence
    # ([[A]] 盲, A 报) —— 两种口径冲突, 本卡选 AUTO 优先 (段内是机器生成不受信),
    # 分歧登记验收单裁决点。anomaly 披露该行走了盲化分支。
    assert subjects == [], f"口径声明与实现不符 (期望 AUTO 优先盲化): {res.findings}"
    assert any("fence 标记行" in n for n in res.notes), "结构异常未在 notes 披露"


def test_malformed_end_does_not_close(tmp_path):
    """Codex round-10 H2: `<!-- /AUTO-GENERATEDNESS -->` 前缀匹配 END 正则曾提前
    关闸 —— 词边界限定后畸形 END 不减深度, [[A]] 仍盲, A 报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py outer -->\n"
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py inner -->\n"
        "<!-- /AUTO-GENERATEDNESS -->\n"
        "<!-- /AUTO-GENERATED -->\n"
        "[[A]]\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"畸形 END 提前关闸, [[A]] 泄漏: {res.findings}"


def test_entity_decoded_target_matches_unescaped_raw(tmp_path):
    """Codex round-10 H3 实体截断 —— **已选口径 (fail-closed)**: target 剥离链的
    `#` 截断（heading 锚点, 复制自 sync 原生语义）先于实体解码 —— `X&#65;` 的
    target 截为 "X&", 与 mdit 解码的 "XA" 不同基 → fail-closed 拒采纳 → XA 报
    孤儿。实体与 heading 锚的冲突登记「不比什么」（修复需上游 sync 语义变更）。"""
    root = tmp_path / "v"
    (root / "节点").mkdir(parents=True)
    (root / "原白板").mkdir()
    (root / "节点" / "XA.md").write_text("---\ntype: concept\n---\n正文\n", encoding="utf-8")
    (root / "原白板" / "板.md").write_text("---\ntype: whiteboard\n---\n[[X&#65;]] \\[\\[X&\\]\\]\n", encoding="utf-8")
    res = vl.check_orphan_nodes(root)
    subjects = sorted(f.subject for f in res.findings)
    assert subjects == ["节点/XA.md"], f"实体形态 target 应 fail-closed 拒采纳 (XA 报孤儿): {subjects}"


def test_auto_structure_anomaly_is_disclosed(tmp_path):
    """Codex round-10 收敛框架: AUTO 段结构异常 (生成器不产出的形态) 必须显式披露
    为盲区信号, 不得静默 —— anomalies 记入 notes, 检查状态 ≥ warn。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py source -->\n"
        "~~~text\n"
        "<!-- /AUTO-GENERATED -->\n"
        "[[A]]\n"
        "~~~\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    # fence 标记行保留 = 结构异常 (生成器不产出), 必须在 notes 披露
    assert any("fence 标记行" in n for n in res.notes), f"结构异常未披露: {res.notes}"
    assert res.status == vl.WARN


# ---------------------------------------------------------------------------
# 3i-2. round-11 整改锁定 —— END/BEGIN 词边界 / anomaly key 唯一
# ---------------------------------------------------------------------------
def test_hyphen_suffix_end_does_not_close(tmp_path):
    """Codex round-11 H2a: `/AUTO-GENERATED-NESS` 的连字符后缀不得匹配 END
    (lookahead 去掉 `|-` 分支) —— 深度不关, [[A]] 仍盲, A 报孤儿。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py outer -->\n"
        "<!-- /AUTO-GENERATED-NESS -->\n"
        "[[A]]\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    subjects = [f.subject for f in res.findings]
    assert "节点/A.md" in subjects, f"连字符后缀 END 提前关闸: {res.findings}"


def test_evil_suffix_begin_does_not_open(tmp_path):
    """Codex round-11 新发现: `sync_board_concepts.pyEVIL` 的 EVIL 后缀不得匹配
    BEGIN —— 真实 [[A]] 不得被盲化（A 不报）。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.pyEVIL -->\n[[A]]\n"
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    assert res.findings == [], f"EVIL 后缀 BEGIN 误开, [[A]] 被盲化: {res.findings}"


def test_auto_anomaly_keys_are_unique(tmp_path):
    """Codex round-11 anomaly 披露: 同文件多条 anomaly 不得同 dict key
    last-write-wins —— 每条独立可见（key 唯一化后逐条进 blind_detail）。"""
    root = tmp_path / "v"
    _node(root, "A")
    board_body = (
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py outer -->\n"
        "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py inner -->\n"
        "~~~text\n"
        "<!-- /AUTO-GENERATED -->\n"
        "[[A]]\n"
        "~~~\n"
    )
    _board(root, "板", board_body)
    res = vl.check_orphan_nodes(root)
    anomaly_notes = [n for n in res.notes if "AUTO 段结构异常" in n or "嵌套" in n or "fence 标记行" in n]
    assert anomaly_notes, f"结构异常未披露: {res.notes}"
