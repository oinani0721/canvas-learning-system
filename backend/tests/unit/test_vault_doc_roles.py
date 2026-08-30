# ⚠️ CARD-G8-1 (BATCH-2026-08-29-第六批) — vault 文档角色台账的裁判
#
# 被测物: backend/scripts/vault_doc_roles.yaml + backend/scripts/check_vault_doc_roles.py
# 卡片判据 (e) 要求 ≥6 用例。本文件 = **52 个 test 函数 / 32 个编号语义组**
# (计数随每轮整改增长; round-4/round-5 各指出过一次文案滞后, 现按实数写)
# (round-4 LOW: 原文案写"本文件 11 个"是首版遗留, 未随三轮整改更新)。
#
# 语义钉死点:
#   1. schema 完整性 —— 每行**十个**必填字段 + 四值 role + **四值** rag_retrieval + id 唯一
#   2. 双列必填 —— rag_index / memory_write 双列俱在且为 bool; 缺一即退出 2
#   3. 分歧行必填理由 —— 双列不等必填 divergence_reason; 双列相等禁填 (防陈旧断言)
#   4. 指纹契约 —— yaml 全文 SHA-256 钉死在脚本常量, 单边改 yaml 即退出 2
#   5. 未登记类型检出 —— fixture vault 构造反例, 必须报 G1/G3/G4 且 --enforce 退出 1
#   6. 白名单与 G4-16 一致 —— 六取值 + census 裁定 + dashboard 口径差异如实登记
#   7. 反软化门 —— 禁裸通配 glob; known_gaps 禁通配字面量; G4-G7 永不可豁免
#   8. 零写入 —— 脚本源码无写原语 + 真跑后 vault 文件 shasum 不变
#   9. live vault 只读跑通 (live 不可达时 skip)
#  10. glob 引擎语义 (顺序敏感 ruleset 的地基)
#  11. root_files 顺序契约 —— 兜底行 `*.md` 必须在最后, 否则抢走黑名单行的命中
#  12. frontmatter_type 紧致性 —— 声明集必须恰好等于 live 实测集 (反过度声明)
#  13. 已登记分歧类不得被 scan() 当 bug 报 (Codex round-1 BLOCKER-1 回归)
#  14. 新分歧类必须被 scan() 抓到 —— reason 绑定 (Codex round-1 BLOCKER-2 回归)
#  15. 派生物 surface/identifier 与 repo_docs 受裁判 (Codex round-1 HIGH 回归)
#  16. 降级门 (--no-probe) 不得伪装成全量绿 (对抗审查 SURVIVED 项回归)
#  17. catch-all 判定是语义的而非字面量黑名单 (`**/?*` 等价写法回归)
#  18. frontmatter 读取与写侧逐字对齐 (`type : rogue` 绕过回归)
#  19. 跨角色 symlink 不得被已登记分歧类吞掉 (解析稳定性绑定回归)
#  20. 契约验结构而非 truthiness + any_level 治理作用域
#  21. frontmatter 读取与写侧**逐字等价**(直接对比真实写侧解析器, 12 形态)
#  22. 目录 symlink 的后代盲区必须显式报出 (G8)
#  23. 根级兜底行必须逐实例登记, 不得静默泛化归属 (G9)
#  24. glob **并集** catch-all + 空结构字段必须被拒
#
# ⛔ 本文件的存在理由: 台账最容易的作弊方式是"加个 catch-all glob 让检查恒绿",
#    或"把双准入面分歧当 bug 抹平"。用例 5/7 就是这两条的机械反例。

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import check_vault_doc_roles as cvr  # noqa: E402

REAL_YAML = _SCRIPTS_DIR / "vault_doc_roles.yaml"
SCRIPT = _SCRIPTS_DIR / "check_vault_doc_roles.py"
REPO_ROOT = Path(__file__).resolve().parents[3]
CENSUS_DOC = REPO_ROOT / "_bmad-output" / "审查" / "G4-16-doc-type-census-2026-08-28.md"


@pytest.fixture(scope="module")
def data() -> dict:
    return cvr.load_rules(REAL_YAML)


def _raw() -> str:
    return REAL_YAML.read_text(encoding="utf-8")


def _mutated_yaml(tmp_path: Path, mutate, name: str = "m") -> Path:
    """把台账拷贝一份并施加一处篡改 —— 用于证明每道门确实拦得住。"""
    doc = yaml.safe_load(_raw())
    mutate(doc)
    sub = tmp_path / name
    sub.mkdir(parents=True, exist_ok=True)
    out = sub / "vault_doc_roles.yaml"
    out.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out


def _make_fixture_vault_clean(root: Path) -> None:
    """只含**已登记**面的干净 fixture —— 用于隔离验证单一变量。"""
    (root / "节点").mkdir(parents=True)
    (root / "节点" / "good.md").write_text("---\ntype: concept\n---\n正文\n", encoding="utf-8")
    (root / "原白板").mkdir()
    (root / "原白板" / "board.md").write_text("---\ntype: whiteboard\n---\n板\n", encoding="utf-8")


def _make_fixture_vault(root: Path) -> None:
    """构造一个最小 fixture vault: 三条已登记面 + 三条反例。"""
    (root / "节点").mkdir(parents=True)
    (root / "节点" / "good.md").write_text("---\ntype: concept\n---\n正文\n", encoding="utf-8")
    (root / "原白板").mkdir()
    (root / "原白板" / "board.md").write_text("---\ntype: whiteboard\n---\n板\n", encoding="utf-8")
    # 反例 1: 未登记目录
    (root / "未登记目录").mkdir()
    (root / "未登记目录" / "x.md").write_text("# x\n", encoding="utf-8")
    # 反例 2+3: 已登记目录里的未登记 frontmatter type (同时是 doc_type 白名单外的野值)
    (root / "节点" / "wild.md").write_text("---\ntype: 野生类型\n---\n正文\n", encoding="utf-8")
    # 反例 4: 未登记的根级非 md 散文件
    (root / "未登记根文件.txt").write_text("x\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. schema 完整性
# ---------------------------------------------------------------------------
def test_schema_completeness(data):
    entries = list(cvr.iter_entries(data))
    assert len(entries) >= 30, f"台账条目过少 ({len(entries)}), 覆盖面可疑"

    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)), f"id 重复: {[i for i in ids if ids.count(i) > 1]}"

    for e in entries:
        for fld in cvr.REQUIRED_ENTRY_FIELDS:
            assert fld in e, f"{e.get('id')} 缺必填字段 {fld}"
            assert str(e[fld]).strip() != "", f"{e.get('id')} 的 {fld} 为空"
        assert e["role"] in cvr.VALID_ROLES, f"{e['id']} role={e['role']}"
        assert e["rag_retrieval"] in cvr.VALID_RETRIEVAL, f"{e['id']} rag_retrieval={e['rag_retrieval']}"
        assert isinstance(e["match"], dict), f"{e['id']} 的 match 必须是 mapping"
        if e.get("surface") in (None, "vault_file"):
            assert e["match"].get("dir_glob") or e["match"].get("file_glob"), (
                f"{e['id']} 的 match 缺 dir_glob/file_glob"
            )
        else:
            # store / http_response 行不落 vault 文件, 身份面走 identifier
            assert cvr._is_nonempty_str_mapping(e.get("identifier")), f"{e['id']} 缺 identifier"

    # 卡片 (a): live vault 全部现存一级目录必须有登记行 (机械枚举, 非口头承诺)
    must_cover = [
        "原白板",
        "节点",
        "检验白板",
        "验收单",
        "outputs",
        "raw",
        "templates",
        "wiki",
        "multimodal",
        ".claude",
        ".claudian",
        ".obsidian",
        ".quarantine",
        ".trash",
        "CS188",
        "CS189",
    ]
    for d in must_cover:
        assert cvr.resolve_dir_entry(data, d) is not None, f"一级目录 {d} 未被任何 dir_glob 覆盖"

    # 卡片 (a): 全部派生物类型逐条登记
    derived_ids = {e["id"] for e in data["derived_artifacts"]}
    for need in (
        "art-daily-review-json",
        "art-daily-review-md",
        "art-recap-report",
        "art-recap-scan-json",
        "art-mindmap-excalidraw",
        "art-overview-html",
        "art-lancedb-tables",
        "art-neo4j-groups",
        "art-graphiti-episodes",
    ):
        assert need in derived_ids, f"派生物 {need} 未登记"

    # repo 侧文档另节登记
    assert len(data["repo_docs"]) >= 5
    for rd in data["repo_docs"]:
        for fld in ("id", "role", "path_glob", "owner", "editable_by", "rag_index", "memory_write"):
            assert fld in rd, f"repo_docs {rd.get('id')} 缺 {fld}"
        assert rd["role"] in cvr.VALID_ROLES


# ---------------------------------------------------------------------------
# 2. 双列必填 (先红: 抽掉一列 → 退出 2)
# ---------------------------------------------------------------------------
def test_dual_columns_required(data, tmp_path):
    for e in cvr.iter_entries(data):
        assert isinstance(e["rag_index"], bool), f"{e['id']} rag_index 非 bool"
        assert isinstance(e["memory_write"], bool), f"{e['id']} memory_write 非 bool"
        if not e["rag_index"]:
            assert e["rag_retrieval"] == "not_indexed", f"{e['id']}: 未进索引却声称可检索"

    def drop_memory_write(doc):
        doc["vault_entries"][0].pop("memory_write")

    bad = _mutated_yaml(tmp_path, drop_memory_write, "drop-col")
    with pytest.raises(cvr.ConfigError, match="memory_write"):
        cvr.load_rules(bad, verify_sha=False)


# ---------------------------------------------------------------------------
# 3. 分歧行必填理由 (双向: 缺理由红 / 陈旧理由也红)
# ---------------------------------------------------------------------------
def test_divergence_rows_require_reason(data, tmp_path):
    diverging = [e for e in cvr.iter_entries(data) if e["rag_index"] != e["memory_write"]]
    assert diverging, "台账未登记任何双准入面分歧 —— 与实测不符 (live 实测有 1 条根级 md 分歧)"
    for e in diverging:
        reason = str(e.get("divergence_reason", "")).strip()
        assert len(reason) >= 20, f"{e['id']} 分歧行 divergence_reason 缺失或过短"
        # 分歧是登记对象不是修复对象 —— 理由里必须能看到"设计/by-design/不修"的定性
        assert any(k in reason for k in ("by-design", "设计", "只登记不修")), f"{e['id']} 未声明分歧属设计而非缺陷"
    for e in cvr.iter_entries(data):
        if e["rag_index"] == e["memory_write"]:
            assert not str(e.get("divergence_reason", "")).strip(), f"{e['id']} 双列一致却留了 divergence_reason"

    def flip_without_reason(doc):
        for e in doc["vault_entries"]:
            if e["id"] == "dir-jiedian":
                e["memory_write"] = False

    bad = _mutated_yaml(tmp_path, flip_without_reason, "flip")
    with pytest.raises(cvr.ConfigError, match="divergence_reason"):
        cvr.load_rules(bad, verify_sha=False)

    def stale_reason(doc):
        doc["vault_entries"][0]["divergence_reason"] = "陈旧断言" * 10

    bad2 = _mutated_yaml(tmp_path, stale_reason, "stale")
    with pytest.raises(cvr.ConfigError, match="陈旧断言|divergence_reason"):
        cvr.load_rules(bad2, verify_sha=False)


# ---------------------------------------------------------------------------
# 4. 指纹契约 (单边改 yaml = 退出 2, 伪绿不可达)
# ---------------------------------------------------------------------------
def test_fingerprint_contract(data, tmp_path):
    actual = hashlib.sha256(REAL_YAML.read_bytes()).hexdigest()
    assert actual == cvr.ROLES_SHA256, (
        f"台账指纹与脚本常量脱钩。刷新: python3 {SCRIPT} --print-roles-sha\n  实际 {actual}"
    )

    assert tuple(data.keys()) == cvr.EXPECTED_SECTIONS
    assert (
        tuple((v["value"], tuple(v["roles"]), v["census_verdict_tag"]) for v in data["doc_type_whitelist"]["values"])
        == cvr.EXPECTED_DOC_TYPES
    )
    assert data["root_files"][-1]["id"] == cvr.EXPECTED_LAST_ROOT_FILE_ID

    # --print-roles-sha 与手算一致
    out = subprocess.run([sys.executable, str(SCRIPT), "--print-roles-sha"], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == actual

    # 篡改一个字节 (改注释也算) → 指纹先于解析比对 → 退出 2
    tampered_dir = tmp_path / "tamper"
    tampered_dir.mkdir()
    tampered_script = tampered_dir / "check_vault_doc_roles.py"
    tampered_script.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    (tampered_dir / "vault_doc_roles.yaml").write_text(_raw() + "\n# tampered\n", encoding="utf-8")
    proc = subprocess.run(
        # --allow-degraded 是为了越过降级门的**前置**拒绝 (用例 16), 好让流程真正
        # 走到指纹比对那一步 —— 否则这里测到的是降级门而不是指纹契约。
        [
            sys.executable,
            str(tampered_script),
            "--enforce",
            "--vault",
            str(tmp_path),
            "--no-probe",
            "--allow-degraded",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "指纹不匹配" in proc.stderr


# ---------------------------------------------------------------------------
# 5. 未登记类型检出 (先红能力自证 —— 台账做软的话这条会失败)
# ---------------------------------------------------------------------------
def test_unregistered_types_detected(data, tmp_path):
    vault = tmp_path / "fixture-vault"
    vault.mkdir()
    _make_fixture_vault(vault)

    res = cvr.scan(data, vault, with_probe=True)
    codes = {f.code for f in res.findings}
    assert "G1" in codes, "未登记目录未被检出 —— dir_glob 可能被 catch-all 软化"
    assert "G3" in codes, "未登记 frontmatter type 未被检出"
    assert "G4" in codes, "doc_type 白名单外的野值未被检出"
    assert "G2" in codes, "未登记根级散文件未被检出"

    g1 = [f for f in res.findings if f.code == "G1"]
    assert any(f.subject == "未登记目录" for f in g1), [f.subject for f in g1]
    g3 = [f for f in res.findings if f.code == "G3"]
    assert any(f.subject == "野生类型" for f in g3), [f.subject for f in g3]
    assert all(f.blocking for f in res.findings if f.code in ("G1", "G2", "G3", "G4"))

    # 已登记面不误报
    assert not any("节点/good.md" in f.detail for f in res.findings)
    assert not any("原白板/board.md" in f.detail for f in res.findings)

    # CLI --enforce 必须退出 1
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    # --report 恒 0
    proc0 = subprocess.run(
        [sys.executable, str(SCRIPT), "--report", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc0.returncode == 0

    # --json 的 stdout 必须是**纯 JSON** —— import app.* 会往 stdout 打 structlog
    # INFO 行, 不改道就会让机器可读档不可解析 (实测踩过)。
    projson = subprocess.run(
        [sys.executable, str(SCRIPT), "--report", "--json", "--vault", str(vault)],
        capture_output=True,
        text=True,
    )
    payload = json.loads(projson.stdout)
    assert {f["code"] for f in payload["findings"]} >= {"G1", "G2", "G3", "G4"}
    assert payload["files_seen"] == 5 and payload["dirs_seen"] == 3


# ---------------------------------------------------------------------------
# 6. 白名单与 G4-16 census 一致
# ---------------------------------------------------------------------------
def test_doc_type_whitelist_aligns_with_g4_16(data):
    wl = data["doc_type_whitelist"]
    values = {v["value"]: v for v in wl["values"]}
    # 卡片 (c) 点名的六取值逐一登记
    assert set(values) == {"note", "whiteboard", "exam_board", "video_transcript", "concept", "dashboard"}

    by_id = {e["id"]: e for e in cvr.iter_entries(data)}
    for v in wl["values"]:
        assert v["census_verdict"].strip(), f"{v['value']} 缺 census 裁定"
        assert v["registered_by"], f"{v['value']} 未绑定任何台账条目"
        for ref in v["registered_by"]:
            assert ref in by_id, f"{v['value']} 引用了不存在的条目 {ref}"
        assert isinstance(v["live_rows_2026_08_28"], int)
        # ⛔ roles 必须由 registered_by 复算, 不许手写单值 (round-2 HIGH):
        #    `note` 横跨 wiki 的 `节点/` 与 raw 的 `raw/`、根级课程、multimodal,
        #    写单个 role 必然对其中一半撒谎。
        assert tuple(v["roles"]) == tuple(sorted({by_id[r]["role"] for r in v["registered_by"]})), (
            f"{v['value']} 的 roles={v['roles']} 与 registered_by 实际角色集不符"
        )
    assert tuple(values["note"]["roles"]) == ("raw", "wiki"), "note 跨角色的实证断言"

    # census 五值的裁定必须与 G4-16 §4 一致 (census 文档在库即逐条比对)
    if CENSUS_DOC.is_file():
        census = CENSUS_DOC.read_text(encoding="utf-8")
        for val in ("note", "video_transcript", "whiteboard", "exam_board", "concept"):
            assert val in census, f"census 文档里找不到取值 {val}"
        assert values["video_transcript"]["live_rows_2026_08_28"] == 2001
        assert values["concept"]["live_rows_2026_08_28"] == 117
        assert values["note"]["live_rows_2026_08_28"] == 69
        assert values["whiteboard"]["live_rows_2026_08_28"] == 16
        assert values["exam_board"]["live_rows_2026_08_28"] == 0
        # census §4 第六行是"空串/自由值", 不是 dashboard —— 台账必须如实登记该差异
        assert "空串" in census

    # dashboard: 卡片点名, census 缺席 —— 差异必须显式登记而非静默调和
    dash = values["dashboard"]
    assert dash["census_verdict_tag"] == "card_added__census_absent"
    assert "空串" in dash["census_verdict"], "dashboard 行未如实登记与 census 第六行的口径差异"
    assert dash["live_rows_2026_08_28"] == 0

    # census 的"值域未闭合"结论必须被保留, 不能因为登记了六个值就假装关门了
    assert wl["value_domain_closed"] is False
    unclosed = wl["unclosed_surface"]
    for surface in ("frontmatter", "add_documents", "image_ocr"):
        assert surface in unclosed, f"未闭合面漏登记 {surface}"

    # live vault 存在但不在 doc_type 值域内的 frontmatter type 必须另节登记
    outside = {t["type"] for t in data["frontmatter_types_outside_doc_type"]}
    assert {"recap", "mockup"} <= outside
    for t in data["frontmatter_types_outside_doc_type"]:
        assert t["why_not_doc_type"].strip() and t["owner_card"].strip()


# ---------------------------------------------------------------------------
# 7. 反软化门
# ---------------------------------------------------------------------------
def test_anti_softening_gates(data, tmp_path):
    # 7a. 禁裸通配
    for e in cvr.iter_entries(data):
        for key in ("dir_glob", "file_glob"):
            for pat in e["match"].get(key) or []:
                assert pat not in cvr.BARE_WILDCARDS, f"{e['id']} 的 {key} 含 catch-all {pat!r}"

    # 7b. known_gaps 只接受字面量, 且必带 reason + owner_card
    for gap in data["known_gaps"]:
        assert not any(ch in str(gap["literal"]) for ch in "*?["), gap
        assert gap["reason"].strip() and gap["owner_card"].strip()

    # 7c. 只有 G1/G2/G3 可豁免 —— G4/G5/G6/G7 是"台账与代码不符", 豁免它们 = 做软
    assert cvr.GAP_EXEMPTIBLE == frozenset({"G1", "G2", "G3"})

    def exempt_g5(doc):
        doc["known_gaps"].append(
            {
                "id": "GAP-CHEAT",
                "kind": "cheat",
                "literal": "节点",
                "finding_codes": ["G5"],
                "reason": "试图豁免台账与代码不符",
                "owner_card": "none",
            }
        )

    bad = _mutated_yaml(tmp_path, exempt_g5, "exempt")
    with pytest.raises(cvr.ConfigError, match="G5"):
        cvr.load_rules(bad, verify_sha=False)

    # 7d. 加 catch-all glob 也必须被拒
    def add_catch_all(doc):
        doc["vault_entries"].append(
            {
                "id": "dir-catch-all",
                "role": "raw",
                "match": {"dir_glob": ["**"], "frontmatter_type": ["(none)"]},
                "owner": "x",
                "editable_by": "x",
                "rag_index": False,
                "memory_write": False,
                "rag_retrieval": "not_indexed",
                "provenance": "x",
                "retention": "x",
            }
        )

    bad2 = _mutated_yaml(tmp_path, add_catch_all, "catchall")
    with pytest.raises(cvr.ConfigError, match="裸通配"):
        cvr.load_rules(bad2, verify_sha=False)


# ---------------------------------------------------------------------------
# 8. 零写入自证 (源码无写原语 + 真跑后 shasum 不变)
# ---------------------------------------------------------------------------
def test_checker_is_read_only(data, tmp_path):
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
    ]
    for pat in forbidden:
        assert not re.search(pat, src), f"校验脚本含写原语 {pat!r} —— 违反 live vault 只读铁律"

    vault = tmp_path / "ro-vault"
    vault.mkdir()
    _make_fixture_vault(vault)

    def digest() -> list[tuple[str, str]]:
        return sorted(
            (p.relative_to(vault).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
            for p in vault.rglob("*")
            if p.is_file()
        )

    before = digest()
    cvr.scan(data, vault, with_probe=True)
    subprocess.run([sys.executable, str(SCRIPT), "--report", "--vault", str(vault)], capture_output=True)
    assert digest() == before, "校验脚本改动了 vault 文件"


# ---------------------------------------------------------------------------
# 9. live vault 只读跑通 (live 不可达时 skip)
# ---------------------------------------------------------------------------
def test_live_vault_enforce_clean():
    try:
        live = cvr._default_vault()
    except cvr.ConfigError as exc:  # pragma: no cover - CI 无 live vault
        pytest.skip(f"live vault 不可达: {exc}")
    if not live.is_dir():  # pragma: no cover
        pytest.skip(f"live vault 不存在: {live}")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(live)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# 13. 已登记的分歧类**不得**被 scan() 当 bug 报 (Codex round-1 BLOCKER-1)
# ---------------------------------------------------------------------------
def test_registered_divergence_class_is_not_reported_as_bug(data, tmp_path):
    """`节点/FOO.MD` 命中已登记的 DIV-2, 必须只登记不判红。

    这是本卡最该防住的错: 条目声明的是该类文档的**常态**, by_design_divergences
    声明的是其**例外**。例外命中时判 G5/G6 = 把「登记对象」当成 bug 报。
    helper 单测拦不住这条 —— 必须走真实 scan()。
    """
    vault = tmp_path / "div2-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "节点" / "FOO.MD").write_text("---\ntype: concept\n---\n大写后缀\n", encoding="utf-8")

    res = cvr.scan(data, vault, with_probe=True)
    offending = [f for f in res.findings if "FOO.MD" in f.subject or "FOO.MD" in f.detail]
    assert not offending, f"已登记的 DIV-2 分歧被当成 bug 报了: {[(f.code, f.detail) for f in offending]}"
    assert "节点/FOO.MD" in res.probe_divergent
    assert any("FOO.MD" in m and "已登记分歧类" in m for m in res.info), res.info

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# 14. **新**分歧类必须被 scan() 抓到 (Codex round-1 BLOCKER-2)
# ---------------------------------------------------------------------------
def test_new_divergence_class_is_reported(data, tmp_path):
    """布尔对与 DIV-1 相同、但 reason 不同的新分歧类, 必须判 G6。

    两个反例都是根级 symlink（Codex round-1 实证）:
      alias-text.md        -> 节点/target.txt  → (True,ok) / (False,not_markdown)
      alias-blacklisted.md -> 检验白板/x.md    → (True,ok) / (False,blacklisted_dir)
    两者都不是 DIV-1 论证的 (ok, root_level), 只比布尔对就会被静默吞掉。
    """
    vault = tmp_path / "newdiv-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "节点" / "target.txt").write_text("txt\n", encoding="utf-8")
    (vault / "检验白板").mkdir()
    (vault / "检验白板" / "x.md").write_text("---\ntype: exam_board\n---\n考题\n", encoding="utf-8")
    (vault / "alias-text.md").symlink_to(vault / "节点" / "target.txt")
    (vault / "alias-blacklisted.md").symlink_to(vault / "检验白板" / "x.md")

    res = cvr.scan(data, vault, with_probe=True)
    g6 = {f.subject for f in res.findings if f.code == "G6"}
    assert "alias-text.md" in g6, [(f.code, f.subject) for f in res.findings]
    assert "alias-blacklisted.md" in g6, [(f.code, f.subject) for f in res.findings]

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    # ⛔ 不能只断言 rc=1 (round-2 MEDIUM): 这个 fixture 还会产生无关的 G3,
    #    撤掉 reason 绑定后 CLI 照样因 G3 退 1 —— rc 断言杀不掉那个 mutant。
    #    必须断言 CLI 输出里**确有两条 G6**。
    assert "G6" in proc.stdout, proc.stdout
    assert "alias-text.md" in proc.stdout and "alias-blacklisted.md" in proc.stdout, proc.stdout


# ---------------------------------------------------------------------------
# 15. 派生物 surface/identifier 与 repo_docs 也受裁判 (Codex round-1 HIGH)
# ---------------------------------------------------------------------------
def test_derived_surface_and_repo_docs_are_judged(data, tmp_path):
    for art in data["derived_artifacts"]:
        assert art["surface"] in cvr.VALID_SURFACES, art["id"]
        globs = (art["match"] or {}).get("file_glob") or []
        if art["surface"] == "vault_file":
            assert globs, f"{art['id']} 是 vault_file 却无 file_glob"
        else:
            assert art.get("identifier"), f"{art['id']} 无 file_glob 时必须有 identifier"

    for rd in data["repo_docs"]:
        for fld in cvr.REQUIRED_REPO_FIELDS:
            assert fld in rd and str(rd[fld]).strip(), f"repo_docs {rd.get('id')} 缺 {fld}"

    # 先红: store 行抽掉 identifier → 退出 2 (不再是"空且不可核对")
    def strip_identifier(doc):
        for a in doc["derived_artifacts"]:
            if a["id"] == "art-lancedb-tables":
                a.pop("identifier")

    bad = _mutated_yaml(tmp_path, strip_identifier, "no-ident")
    with pytest.raises(cvr.ConfigError, match="identifier"):
        cvr.load_rules(bad, verify_sha=False)

    # 先红: repo_docs 抽掉 rag_retrieval → 退出 2 (不再绕过裁判)
    def strip_repo_field(doc):
        doc["repo_docs"][0].pop("rag_retrieval")

    bad2 = _mutated_yaml(tmp_path, strip_repo_field, "no-repo-col")
    with pytest.raises(cvr.ConfigError, match="rag_retrieval"):
        cvr.load_rules(bad2, verify_sha=False)

    # 先红: 分歧类抽掉 reason 绑定 → 退出 2 (否则 G6 会被同向不同因的新分歧绕过)
    def strip_reason(doc):
        doc["admission_surfaces"]["by_design_divergences"][0].pop("memory_reason")

    bad3 = _mutated_yaml(tmp_path, strip_reason, "no-reason")
    with pytest.raises(cvr.ConfigError, match="memory_reason"):
        cvr.load_rules(bad3, verify_sha=False)


# ---------------------------------------------------------------------------
# 12. frontmatter_type 紧致性 (反"过度声明"软化路径)
# ---------------------------------------------------------------------------
def test_frontmatter_type_lists_are_tight(data):
    """声明的 frontmatter_type 必须**恰好等于** live vault 实测集。

    为什么需要这道门: G3 判"type 不在条目白名单内"。往白名单里多塞几个值
    (尤其 `(none)`) 就能悄悄让 G3 失效, 而 schema 检查、catch-all glob 检查
    都拦不住这种软化 —— 它长得完全合法。只有拿 live vault 实测集对账才拦得住。

    只对**有 live md 命中**的条目断言 (空目录/无实例条目跳过, 不制造脆性)。
    """
    try:
        live = cvr._default_vault()
    except cvr.ConfigError as exc:  # pragma: no cover - CI 无 live vault
        pytest.skip(f"live vault 不可达: {exc}")
    if not live.is_dir():  # pragma: no cover
        pytest.skip(f"live vault 不存在: {live}")

    observed: dict[str, set[str]] = {}
    for p in sorted(live.rglob("*.md")):
        rel = p.relative_to(live).as_posix()
        if rel.split("/")[0] == ".git":
            continue
        entry = cvr.resolve_file_entry(data, rel)
        if entry:
            observed.setdefault(entry["id"], set()).add(cvr.read_frontmatter_type(p))

    assert len(observed) >= 20, f"只有 {len(observed)} 个条目命中 live md, 覆盖面可疑"
    for eid, seen in sorted(observed.items()):
        entry = next(e for e in cvr.iter_entries(data) if e["id"] == eid)
        declared = set((entry.get("match") or {}).get("frontmatter_type") or [])
        assert declared == seen, (
            f"条目 {eid} 的 frontmatter_type 与 live 实测不符\n"
            f"  声明: {sorted(declared)}\n  实测: {sorted(seen)}\n"
            f"  多出的值 = 过度声明 (悄悄放宽 G3); 少掉的值 = 未登记类型 (G3 会报)"
        )


# ---------------------------------------------------------------------------
# 16. 降级门不得伪装成全量绿 (独立对抗审查 SURVIVED 项的回归门)
# ---------------------------------------------------------------------------
def test_degraded_gate_cannot_masquerade_as_full_pass(data, tmp_path):
    """`--no-probe` 会跳过 G5/G6/G7 —— 脚本契约自称这三类"永不可豁免"。

    独立对抗审查（2 个验证者一致判 SURVIVED）指出：一个 CLI flag 就能一次性废掉
    它们，而输出仍打印"台账双列与真实函数一致"并退 0 —— 那句话在没跑 probe 时
    **字面为假**。三道门：
      (1) --enforce + --no-probe 未显式声明降级 → 退出 2，拒绝执行；
      (2) 显式 --allow-degraded 后可跑，但必须打降级横幅、且不得声称双列一致；
      (3) JSON 档必须暴露 probe_skipped 与实际跑了哪几类检查。
    """
    vault = tmp_path / "degraded-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)

    # (1) 未声明降级 → 退出 2
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--no-probe", "--vault", str(vault)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "永不可豁免" in proc.stderr

    # (2) 显式声明后可跑, 但文案不得撒谎
    proc2 = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--no-probe", "--allow-degraded", "--vault", str(vault)],
        capture_output=True,
        text=True,
    )
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    assert "已跳过 G5/G6/G7" in proc2.stdout
    assert "台账双列与真实函数一致" not in proc2.stdout, "降级跑仍在声称跑了 probe —— 文案为假"

    # (3) JSON 暴露降级状态
    proc3 = subprocess.run(
        [sys.executable, str(SCRIPT), "--report", "--no-probe", "--json", "--vault", str(vault)],
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc3.stdout)
    assert payload["probe_skipped"] is True
    # round-6 MEDIUM 整改后: 跳过的**只有**需要真实函数求值的三类, 其余照跑
    assert payload["checks_skipped"] == ["G5", "G6", "G7"]
    assert set(payload["checks_run"]) == set(cvr.ALL_FINDING_CODES) - {"G5", "G6", "G7"}

    # 全量档反向对照: 不降级时文案照常, probe_skipped=False
    proc4 = subprocess.run(
        [sys.executable, str(SCRIPT), "--report", "--json", "--vault", str(vault)],
        capture_output=True,
        text=True,
    )
    full = json.loads(proc4.stdout)
    assert full["probe_skipped"] is False
    assert set(full["checks_run"]) == set(cvr.ALL_FINDING_CODES)
    assert full["checks_skipped"] == []


# ---------------------------------------------------------------------------
# 17. catch-all 判定必须是**语义**的, 不是字面量黑名单
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("pat", "expected"),
    [
        # 全局 catch-all
        ("**", True),
        ("**/*", True),
        ("*/**", True),
        ("/**", True),
        ("**/**", True),
        ("**/?*", True),  # ⛔ 字面量黑名单拦不住的等价写法 (对抗审查实证)
        # 顶层 catch-all: 吃不下 a/b, 但作为 dir_glob 会吞掉全部一级目录
        ("*", True),
        ("?*", True),
        # 正常 glob 不得误杀
        ("节点/**", False),
        ("raw/**", False),
        ("**/chunks/**", False),
        ("**/.obsidian/**", False),
        ("*.md", False),
        ("**/*.M[Dd]", False),
        ("outputs/回顾-*.md", False),
        ("[a-z]*", False),  # 吃不下 .hidden / 大写 / 中文
        ("?", False),
    ],
)
def test_catch_all_detection_is_semantic(pat, expected):
    assert cvr.is_catch_all(pat) is expected


# ---------------------------------------------------------------------------
# 18. frontmatter 读取必须与**写侧逐字对齐** (round-2 BLOCKER: `type : rogue` 绕过)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("---\ntype: concept\n---\nx\n", "concept"),
        # 手写正则 `^type:` 认不出的三种变体 —— PyYAML 与写侧 _parse_frontmatter 都认得,
        # 台账若判 (none), 野值就从 G3/G4 底下溜过去 (round-2 BLOCKER 实证)
        ("---\ntype : rogue\n---\nx\n", "rogue"),
        ('---\n"type": rogue2\n---\nx\n', "rogue2"),
        ("---\ntype:   rogue3   \n---\nx\n", "rogue3"),
        # 值大小写: 写侧 lancedb_client:2740 做 .lower().strip(), 本读取器必须同规则
        ("---\ntype: Concept\n---\nx\n", "concept"),
        # ⛔ key 大小写: 写侧是 frontmatter.get("type") **精确小写**, 取不到 TYPE ——
        #    本读取器也必须取不到, 否则会报出永远不会成为 doc_type 的假野值
        ("---\nTYPE: rogue4\n---\nx\n", "(none)"),
        # 无 frontmatter / 空块 / 坏 YAML 都不得炸
        ("no frontmatter\n", "(none)"),
        ("---\n---\nx\n", "(none)"),
        ("---\ntype: [unclosed\n---\nx\n", "(none)"),
    ],
)
def test_frontmatter_reader_matches_writer(tmp_path, body, expected):
    f = tmp_path / "n.md"
    f.write_text(body, encoding="utf-8")
    assert cvr.read_frontmatter_type(f) == expected


def test_rogue_type_variant_is_caught_by_scan(data, tmp_path):
    """`type : rogue` 必须真的触发 G3+G4, 而不是被读成 (none) 静默放过。"""
    vault = tmp_path / "rogue-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "节点" / "rogue.md").write_text("---\ntype : rogue\n---\n正文\n", encoding="utf-8")

    res = cvr.scan(data, vault, with_probe=True)
    assert "rogue" in {f.subject for f in res.findings if f.code == "G3"}
    assert "rogue" in {f.subject for f in res.findings if f.code == "G4"}
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# 19. 跨角色 symlink 不得被已登记分歧类吞掉 (round-2 BLOCKER)
# ---------------------------------------------------------------------------
def test_cross_role_symlink_is_not_covered_by_registered_divergence(data, tmp_path):
    """`检验白板/x.MD -> 节点/y.md` 与 DIV-2 的 pattern/scope/布尔对/reason 对**四者全等**,
    但成因是「check_vault_path 判 resolved 路径、should_index 判 lexical 路径」这个
    第三类现象。已登记分歧只为**解析稳定的普通文件**论证过 → 必须判红。
    """
    vault = tmp_path / "xrole-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "检验白板").mkdir()
    (vault / "检验白板" / "alias-into-node.MD").symlink_to(vault / "节点" / "good.md")

    res = cvr.scan(data, vault, with_probe=True)
    hit = [f for f in res.findings if f.subject == "检验白板/alias-into-node.MD"]
    assert hit, [(f.code, f.subject) for f in res.findings]
    assert {f.code for f in hit} & {"G5", "G6"}, [f.code for f in hit]

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr

    # 反向: 解析稳定的普通 .MD 仍属 DIV-2, 不得判红 —— 证明豁免没被一并关死
    vault2 = tmp_path / "xrole-vault2"
    vault2.mkdir()
    _make_fixture_vault_clean(vault2)
    (vault2 / "节点" / "PLAIN.MD").write_text("---\ntype: concept\n---\nx\n", encoding="utf-8")
    res2 = cvr.scan(data, vault2, with_probe=True)
    assert not [f for f in res2.findings if "PLAIN.MD" in f.subject], [(f.code, f.detail) for f in res2.findings]


def test_resolution_stability_helper(tmp_path):
    root = tmp_path / "v"
    (root / "a").mkdir(parents=True)
    (root / "a" / "f.md").write_text("x", encoding="utf-8")
    (root / "link.md").symlink_to(root / "a" / "f.md")
    assert cvr._is_resolution_stable(root, "a/f.md") is True
    assert cvr._is_resolution_stable(root, "link.md") is False


# ---------------------------------------------------------------------------
# 20. 契约必须验**结构**而非 truthiness (round-2 HIGH)
# ---------------------------------------------------------------------------
def test_contract_validates_structure_not_truthiness(data, tmp_path):
    def scalar_identifier(doc):
        for a in doc["derived_artifacts"]:
            if a["id"] == "art-lancedb-tables":
                a["identifier"] = "x"  # 标量, 不可核对

    def empty_repo_glob(doc):
        doc["repo_docs"][0]["path_glob"] = []

    def string_bool(doc):
        doc["repo_docs"][0]["rag_index"] = "false"  # 字符串伪布尔恒真

    def missing_governance_scope(doc):
        for rf in doc["root_files"]:
            if rf.get("scope") == "any_level":
                rf.pop("governance_scope")
                break

    def drop_resolution_binding(doc):
        doc["admission_surfaces"]["by_design_divergences"][0].pop("requires_resolution_stable")

    def disable_resolution_binding(doc):
        doc["admission_surfaces"]["by_design_divergences"][0]["requires_resolution_stable"] = False

    def wrong_doc_type_roles(doc):
        # ⚠️ 必须改**条目角色**而不是改 values.roles —— 后者会先被 EXPECTED_DOC_TYPES
        #    的逐条逐序契约拦住, 测不到"roles 由 registered_by 复算"这道门本身。
        for e in doc["vault_entries"]:
            if e["id"] == "dir-jiedian":
                e["role"] = "schema"  # note/concept 的 registered_by 角色集随之改变

    for mutate, name, pattern in [
        (scalar_identifier, "scalar-id", "identifier"),
        (empty_repo_glob, "empty-glob", "path_glob"),
        (string_bool, "str-bool", "bool"),
        (missing_governance_scope, "no-gov", "governance_scope"),
        (wrong_doc_type_roles, "bad-roles", "roles"),
        # ⛔ 这条绑定若可缺省或被单边置 false, round-2 BLOCKER 就在 yaml 侧一键复活
        (drop_resolution_binding, "no-resbind", "requires_resolution_stable"),
        (disable_resolution_binding, "off-resbind", "resolution_unstable_rationale"),
    ]:
        bad = _mutated_yaml(tmp_path, mutate, name)
        with pytest.raises(cvr.ConfigError, match=pattern):
            cvr.load_rules(bad, verify_sha=False)


def test_any_level_rows_declare_governance_scope(data):
    """any_level 行按 basename 抢在容器行之前命中, 必须声明治理只作用于根级。"""
    any_level = [r for r in data["root_files"] if r.get("scope") == "any_level"]
    assert len(any_level) >= 5
    for r in any_level:
        # 结构门: 所有 any_level 行都必须声明治理作用域 (脚本契约同步强制)
        assert r.get("governance_scope") == "root_only", r["id"]
        # 文本门: 只对做出**处置声明**("可安全删除")的行要求根级限定 —— 那才是会害人的谎。
        # 例: `.quarantine/UAT-x.md` 若继承根级的"可安全删除", 就与隔离区
        # "保留至人工处置、系统绝不自动清理" 直接冲突。
        if "可安全删除" in r["retention"]:
            assert "根级实例" in r["retention"], (
                f"{r['id']} 的 retention 声明了'可安全删除'却未限定为根级实例 —— "
                f"深层同名文件会继承这个处置结论, 与其所在容器的保留期冲突"
            )


# ---------------------------------------------------------------------------
# 21. frontmatter 读取与写侧**逐字等价** —— 直接对比真实写侧解析器 (round-3 BLOCKER)
# ---------------------------------------------------------------------------
_FM_CASES = [
    ("plain", "---\ntype: concept\n---\nx"),
    ("space-before-colon", "---\ntype : rogue\n---\nx"),
    ("quoted-key", '---\n"type": x\n---\nx'),
    ("value-case", "---\ntype: Concept\n---\nx"),
    ("upper-key", "---\nTYPE: x\n---\nx"),
    ("bad-yaml", "---\ntype: [un\n---\nx"),
    ("crlf", "---\r\ntype: rogue_crlf\r\n---\r\nx"),
    ("open-trailing-space", "---   \ntype: rogue_open\n---\nx"),
    ("close-trailing-space", "---\ntype: rogue_close\n---   \nx"),
    ("dots-terminator", "---\ntype: rogue_dot\n...\nx"),
    ("no-closing-marker", "---\ntype: rogue_noend\nx"),
    ("beyond-400-lines", "---\n" + "k: v\n" * 401 + "type: rogue_400\n---\nx"),
]


@pytest.mark.parametrize(("name", "body"), _FM_CASES, ids=[c[0] for c in _FM_CASES])
def test_frontmatter_reader_is_equivalent_to_writer(tmp_path, name, body):
    """必须与写侧 `LanceDBClient._parse_frontmatter` **逐字等价**, 而不是"差不多"。

    round-3 实证: 手写块提取漏判了首/尾分隔符尾随空白、超行数上限三类, 又对
    `...` 结束符与缺结束符造出两类假阳性。唯一不会漂的做法是**直接调用写侧那个函数** ——
    与"不重新实现准入判定"同一条原则。本用例把等价性钉死: 任何一侧改了都会红。
    """
    lancedb = pytest.importorskip("agentic_rag.clients.lancedb_client")
    f = tmp_path / "n.md"
    f.write_text(body, encoding="utf-8")
    fm, _body = lancedb.LanceDBClient._parse_frontmatter(body)
    writer = str(fm.get("type", "") or "").lower().strip() or cvr.NO_TYPE
    assert cvr.read_frontmatter_type(f) == writer, f"{name}: 与写侧不等价"


# ---------------------------------------------------------------------------
# 22. 目录 symlink 的后代不被 rglob 递归 → 必须显式报盲区 (round-3 BLOCKER)
# ---------------------------------------------------------------------------
def test_symlinked_directory_blindspot_is_reported(data, tmp_path):
    """`检验白板/alias -> ../节点` 会让整棵子树静默不在扫描面内。

    不跟进 (会成环), 但"0 finding"必须不能是"没看见"。生产刷新端点
    (backend/app/api/v1/endpoints/index.py) 会把任意相对路径交给 orchestrator,
    盲区是可达的。
    """
    vault = tmp_path / "dirlink-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "节点" / "PLAIN.MD").write_text("---\ntype: concept\n---\nx\n", encoding="utf-8")
    (vault / "检验白板").mkdir()
    (vault / "检验白板" / "alias-node-dir").symlink_to(vault / "节点", target_is_directory=True)

    # 先证明盲区确实存在 (rglob 不递归)
    seen = {p.relative_to(vault).as_posix() for p in vault.rglob("*")}
    assert "检验白板/alias-node-dir" in seen
    assert "检验白板/alias-node-dir/PLAIN.MD" not in seen, "rglob 行为变了, 本用例前提需重估"

    res = cvr.scan(data, vault, with_probe=True)
    g8 = {f.subject for f in res.findings if f.code == "G8"}
    assert "检验白板/alias-node-dir" in g8, [(f.code, f.subject) for f in res.findings]

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# 23. 根级兜底行不得把新 md 静默泛化成"用户 wiki" (round-3 HIGH)
# ---------------------------------------------------------------------------
def test_root_fallback_requires_per_instance_registration(data, tmp_path):
    """兜底行镜像的是**准入规则**, 断不了 owner/role/retention。

    一个机器生成的报告落在 vault 根目录, 若被兜底行静默吸收, 就会被读成
    "用户手写 wiki、不可重建"。故每个落到兜底行的根级 md 必须逐个登记。
    """
    vault = tmp_path / "rootmd-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "machine-generated-report.md").write_text("# 机器生成\n", encoding="utf-8")

    res = cvr.scan(data, vault, with_probe=True)
    g9 = {f.subject for f in res.findings if f.code == "G9"}
    assert "machine-generated-report.md" in g9, [(f.code, f.subject) for f in res.findings]

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr

    # 已登记的那一条不判红 (登记动作 = 写进 known_instances)
    fallback = next(r for r in data["root_files"] if r["id"] == cvr.EXPECTED_LAST_ROOT_FILE_ID)
    known = fallback["known_instances"]
    assert known, "兜底行必须有 known_instances"
    vault2 = tmp_path / "rootmd-vault2"
    vault2.mkdir()
    _make_fixture_vault_clean(vault2)
    (vault2 / known[0]).write_text("# 已登记\n", encoding="utf-8")
    res2 = cvr.scan(data, vault2, with_probe=True)
    assert not [f for f in res2.findings if f.code == "G9"], [(f.code, f.subject) for f in res2.findings]


# ---------------------------------------------------------------------------
# 24. glob **并集** catch-all 必须被拒 (round-3 HIGH)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("pats", "expected"),
    [
        # ⛔ 逐条都不是 catch-all, 合起来覆盖一切 —— round-3 实证的绕过路径
        (["**/.*", "**/[!.]*"], True),
        (["**"], True),
        ([".*", "[!.]*"], True),  # 顶层并集
        (["节点/**", "raw/**"], False),
        (["outputs/回顾-*.md", "outputs/今日复习.md"], False),
        ([], False),
    ],
)
def test_union_catch_all_detection(pats, expected):
    assert cvr.is_union_catch_all(pats) is expected


def test_union_catch_all_is_rejected_by_contract(data, tmp_path):
    def union_catch_all(doc):
        doc["vault_entries"].append(
            {
                "id": "dir-union-catch-all",
                "role": "raw",
                "match": {"dir_glob": ["**/.*", "**/[!.]*"], "frontmatter_type": ["(none)"]},
                "owner": "x",
                "editable_by": "x",
                "rag_index": False,
                "memory_write": False,
                "rag_retrieval": "not_indexed",
                "provenance": "x",
                "retention": "x",
            }
        )

    bad = _mutated_yaml(tmp_path, union_catch_all, "union-ca")
    # 两道门都能拦它: `names_something` (更严, 先触发) 与并集判定。任一命中即可。
    with pytest.raises(cvr.ConfigError, match="并集|不指名道姓"):
        cvr.load_rules(bad, verify_sha=False)

    # ⚠️ 如实记录一个**没做成**的构造: 我原想再补一个"两条都指名道姓、合起来却覆盖一切"
    #    的专属反例, 实测构造不出来 —— `**/x*` + `**/[!x]y*` 这类并集并不覆盖全部探针。
    #    这恰恰是 `names_something` 的设计效果: 要求每条 glob 至少指名一样东西之后,
    #    "全指名的并集 catch-all" 实质上不可构造。两道门是层级关系, 不是并列关系:
    #    names_something 先把"只圈地不指名"的模式挡在门外, 并集门兜住剩余情形。
    #    故此处不再伪造一个不成立的反例充数。


def test_empty_structures_are_rejected(data, tmp_path):
    """`None` / `[]` / `{}` 字符串化后非空, truthiness 校验会全部放行 (round-3 实证)。"""
    for bad_val, name in [(None, "none"), ([], "list"), ({}, "dict"), ("  ", "blank")]:

        def mutate(doc, _v=bad_val):
            doc["vault_entries"][0]["owner"] = _v

        bad = _mutated_yaml(tmp_path, mutate, f"empty-{name}")
        with pytest.raises(cvr.ConfigError, match="非空字符串"):
            cvr.load_rules(bad, verify_sha=False)


# ---------------------------------------------------------------------------
# 25. 每条 glob 必须**指名道姓** —— 对"跨行拆分 catch-all"的正面回答 (round-4 HIGH)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("pat", "expected"),
    [
        # ⛔ 只由通配符/字符类拼成 —— 不标识任何一类文档, 拆成两行就能糊住全场
        ("**/.*", False),
        ("**/[!.]*", False),
        ("[!x]*", False),
        (".*", False),
        ("*", False),
        ("**/*", False),
        # 指名道姓的正常 glob 一个都不能误杀
        ("节点/**", True),
        ("*.md", True),
        ("**/*.M[Dd]", True),
        ("**/_misc", True),
        ("**/chunks/**", True),
        (".claudian/sessions/**", True),
        ("outputs/回顾-*.md", True),
    ],
)
def test_every_glob_must_name_something(pat, expected):
    assert cvr.names_something(pat) is expected


def test_ledger_globs_all_name_something(data):
    """台账现有的每一条 glob 都必须指名道姓（否则这道门等于没上）。"""
    for e in cvr.iter_entries(data):
        for key in ("dir_glob", "file_glob"):
            for pat in e["match"].get(key) or []:
                assert cvr.names_something(pat), f"{e['id']} 的 {key} 含不指名道姓的 {pat!r}"
    for div in data["admission_surfaces"]["by_design_divergences"]:
        for pat in div["patterns"]:
            assert cvr.names_something(pat), f"{div['id']} 含不指名道姓的 {pat!r}"


# ---------------------------------------------------------------------------
# 26. 枚举盲区与越界读取 (round-4 BLOCKER: G10 / G11)
# ---------------------------------------------------------------------------
def test_dangling_symlink_is_reported_as_blind_spot(data, tmp_path):
    """dangling / self 指向的 symlink `is_dir()` 与 `is_file()` 都为 False,
    `rglob` 的两轮过滤会把它们一起滤没 —— 必须由 G10 报出。"""
    vault = tmp_path / "blind-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "节点" / "dangling.md").symlink_to(vault / "节点" / "does-not-exist.md")

    res = cvr.scan(data, vault, with_probe=True)
    g10 = {f.subject for f in res.findings if f.code == "G10"}
    assert "节点/dangling.md" in g10, [(f.code, f.subject) for f in res.findings]
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr


def test_external_symlink_is_reported_and_not_read(data, tmp_path):
    """指向 vault 外的文件 symlink 必须判红, **且其正文不得被读取**。

    round-4 实证: checker 此前在准入判断**之前**读 frontmatter, 于是外部目标的
    正文被照读进来 —— 一个只读的 vault 审计器不该跨出 vault 边界读别人的文件。
    """
    # ⛔ 外部目标的 type 必须**不在**容器(检验白板)的允许集内, 否则"去掉拒读"这个
    #    对照修改根本不会让本用例转红 —— exam_board 恰在允许集内、且该容器
    #    rag_index=False 不触发 G4, 弱断言会让 mutation 存活 (round-5 trace 指出)。
    outside = tmp_path / "outside-target.md"
    outside.write_text("---\ntype: 外部野值\n---\n外部内容\n", encoding="utf-8")
    vault = tmp_path / "escape-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "检验白板").mkdir()
    (vault / "检验白板" / "external.md").symlink_to(outside)

    res = cvr.scan(data, vault, with_probe=True)
    g11 = {f.subject for f in res.findings if f.code == "G11"}
    assert "检验白板/external.md" in g11, [(f.code, f.subject) for f in res.findings]
    # 拒读的机械证明: 外部目标的 `type: 外部野值` 不在容器允许集内 ——
    # 一旦被读, 必然产生 G3。所以"没有 G3"就等价于"没读过它"。
    assert not [f for f in res.findings if f.code == "G3" and "external.md" in f.detail], (
        "外部目标的 frontmatter 被读了 —— 拒读失效"
    )
    assert "外部野值" not in {f.subject for f in res.findings}

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--enforce", "--vault", str(vault)], capture_output=True, text=True
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr


def test_escape_is_reported_even_in_unregistered_dir(data, tmp_path):
    """越界是**路径事实**, 与能否归属无关 —— 未登记目录里的外逃链接照样判 G11。

    round-5 指出顺序缺口: G11 原先放在「无法归属则 continue」之后, 于是这类路径
    永远走不到判定; 若该目录再被合法 known_gaps 豁免 G1, 整条门一个 blocking
    finding 都不产生。
    """
    outside = tmp_path / "outside2.md"
    outside.write_text("---\ntype: 外部野值\n---\nx\n", encoding="utf-8")
    vault = tmp_path / "escape-unreg"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "未登记目录").mkdir()
    (vault / "未登记目录" / "external.md").symlink_to(outside)

    res = cvr.scan(data, vault, with_probe=True)
    g11 = {f.subject for f in res.findings if f.code == "G11"}
    assert "未登记目录/external.md" in g11, [(f.code, f.subject) for f in res.findings]


def test_resolves_inside_vault_helper(tmp_path):
    vault = tmp_path / "v"
    (vault / "a").mkdir(parents=True)
    (vault / "a" / "in.md").write_text("x", encoding="utf-8")
    out = tmp_path / "out.md"
    out.write_text("x", encoding="utf-8")
    (vault / "link-out.md").symlink_to(out)
    assert cvr._resolves_inside_vault(vault, "a/in.md") is True
    assert cvr._resolves_inside_vault(vault, "link-out.md") is False


def test_strict_utf8_matches_writer_skip(tmp_path):
    """非法 UTF-8: 写侧严格解码并整条跳过该文件 (不入库) → 无 doc_type。
    此前 checker 用 errors="replace" 硬读, 会得出写侧根本不会产生的 doc_type。"""
    f = tmp_path / "bad.md"
    f.write_bytes(b"---\ntype: rogue_bytes\n---\n\xff\xfe\n")
    assert cvr.read_frontmatter_type(f) == cvr.NO_TYPE


# ---------------------------------------------------------------------------
# 27. known_instances 必须是列表 —— 标量会让成员判定退化成子串匹配 (round-4 HIGH)
# ---------------------------------------------------------------------------
def test_known_instances_must_be_a_list(data, tmp_path):
    fallback = next(r for r in data["root_files"] if r["id"] == cvr.EXPECTED_LAST_ROOT_FILE_ID)
    assert isinstance(fallback["known_instances"], list)

    def scalar_known(doc):
        for rf in doc["root_files"]:
            if rf["id"] == cvr.EXPECTED_LAST_ROOT_FILE_ID:
                rf["known_instances"] = "chatgpt-adversarial-review-Q1Q2Q3-2026-05-12.md,future-report.md"

    bad = _mutated_yaml(tmp_path, scalar_known, "scalar-known")
    with pytest.raises(cvr.ConfigError, match="known_instances"):
        cvr.load_rules(bad, verify_sha=False)


# ---------------------------------------------------------------------------
# 28. 契约必须**强于或等于**台账头部的文字声明 (round-6 HIGH)
# ---------------------------------------------------------------------------
def test_contract_enforces_what_the_header_claims(data, tmp_path):
    """头部写了"id 全局唯一 / kebab-case / match 结构必填", 契约就必须真的拦。

    round-6 实证: 这三条此前全是**只写在注释里**的声明 —— duplicate_id / empty_match
    双双 ACCEPTED, 重复 id 的副本连同刷新过的指纹一起还能拿到 `0 finding / exit 0`。
    """

    def dup_id(doc):
        doc["vault_entries"].append(dict(doc["vault_entries"][0]))

    def bad_kebab(doc):
        doc["vault_entries"][0]["id"] = "Dir_Jiedian"

    def empty_match(doc):
        doc["vault_entries"][0]["match"] = {"frontmatter_type": ["(none)"]}

    def typo_divergence_scope(doc):
        doc["admission_surfaces"]["by_design_divergences"][0]["scope"] = "typo_scope"

    for mutate, name, pattern in [
        (dup_id, "dup-id", "id 重复"),
        (bad_kebab, "bad-kebab", "kebab-case"),
        (empty_match, "empty-match", "既无 dir_glob"),
        (typo_divergence_scope, "typo-scope", "scope"),
    ]:
        bad = _mutated_yaml(tmp_path, mutate, name)
        with pytest.raises(cvr.ConfigError, match=pattern):
            cvr.load_rules(bad, verify_sha=False)


def test_ledger_ids_are_unique_and_kebab(data):
    ids = [e["id"] for e in cvr.iter_entries(data)]
    assert len(ids) == len(set(ids))
    for i in ids:
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9.]+)*", i), i


# ---------------------------------------------------------------------------
# 29. 检索面不得一刀切: conditional 必须带说明 (round-6 HIGH)
# ---------------------------------------------------------------------------
def test_conditional_retrieval_requires_note(data, tmp_path):
    """`节点/**` 里无 type 且含 exam_question_id 的考察文件会被写侧推断为
    exam_board 从而被读侧排除 —— 声明 `included` 就是对信息隔离面撒谎。"""
    jiedian = next(e for e in data["vault_entries"] if e["id"] == "dir-jiedian")
    assert jiedian["rag_retrieval"] == "conditional"
    assert "exam_question_id" in jiedian["rag_retrieval_note"]

    def drop_note(doc):
        for e in doc["vault_entries"]:
            if e["id"] == "dir-jiedian":
                e.pop("rag_retrieval_note")

    bad = _mutated_yaml(tmp_path, drop_note, "no-cond-note")
    with pytest.raises(cvr.ConfigError, match="rag_retrieval_note"):
        cvr.load_rules(bad, verify_sha=False)


# ---------------------------------------------------------------------------
# 30. JSON 的 checks_run 必须与实际跑的检查一致 (round-6 MEDIUM)
# ---------------------------------------------------------------------------
def test_json_checks_run_reflects_reality(data, tmp_path):
    """round-6 实证: no-probe 下 G8/G9/G10/G11 照样跑, 而 JSON 只报 G1-G4。"""
    vault = tmp_path / "checksrun-vault"
    vault.mkdir()
    _make_fixture_vault_clean(vault)
    (vault / "节点" / "dangling.md").symlink_to(vault / "节点" / "nope.md")

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--report", "--json", "--no-probe", "--vault", str(vault)],
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    codes = {f["code"] for f in payload["findings"]}
    assert "G10" in codes, payload["findings"]
    assert "G10" in payload["checks_run"], payload["checks_run"]
    assert payload["checks_skipped"] == ["G5", "G6", "G7"]
    assert set(payload["checks_run"]).isdisjoint(payload["checks_skipped"])


# ---------------------------------------------------------------------------
# 31. 契约必须**验结构**到底, 不留 str().strip() 的真值缺口 (round-7)
# ---------------------------------------------------------------------------
def test_contract_rejects_stringified_empties(data, tmp_path):
    """`None` / `[]` / `{}` / `123` 经 `str(v).strip()` 后都非空 —— round-7 实测
    `rag_retrieval_note` 与 `resolution_unstable_rationale` 两处都被这样放行过。"""
    for bad_val, name in [(None, "none"), ([], "list"), ({}, "dict"), (123, "int"), ("  ", "blank")]:

        def drop_note(doc, _v=bad_val):
            for e in doc["vault_entries"]:
                if e["id"] == "dir-jiedian":
                    e["rag_retrieval_note"] = _v

        bad = _mutated_yaml(tmp_path, drop_note, f"note-{name}")
        with pytest.raises(cvr.ConfigError, match="rag_retrieval_note"):
            cvr.load_rules(bad, verify_sha=False)

    def bad_rationale(doc):
        d = doc["admission_surfaces"]["by_design_divergences"][0]
        d["requires_resolution_stable"] = False
        d["resolution_unstable_rationale"] = None

    bad = _mutated_yaml(tmp_path, bad_rationale, "rationale-none")
    with pytest.raises(cvr.ConfigError, match="resolution_unstable_rationale"):
        cvr.load_rules(bad, verify_sha=False)


def test_untyped_and_indexed_entries_must_be_conditional(data, tmp_path):
    """写侧的 exam_board 推断**不限目录** —— 任何"允许无 type 且进索引"的条目
    都不许一刀切声明 included (round-7 HIGH)。"""
    for e in cvr.iter_entries(data):
        if cvr.NO_TYPE in ((e.get("match") or {}).get("frontmatter_type") or []) and e["rag_index"]:
            assert e["rag_retrieval"] == "conditional", e["id"]
            assert cvr._nonempty_str(e.get("rag_retrieval_note")), e["id"]

    def flip_to_included(doc):
        for e in doc["vault_entries"]:
            if e["id"] == "dir-raw":
                e["rag_retrieval"] = "included"

    bad = _mutated_yaml(tmp_path, flip_to_included, "raw-included")
    with pytest.raises(cvr.ConfigError, match="conditional"):
        cvr.load_rules(bad, verify_sha=False)


def test_id_namespace_covers_repo_docs_and_kebab_is_strict(data, tmp_path):
    """id 唯一性/格式此前只覆盖三个 ledger 节, repo_docs 与跨节重复均被接受 (round-7)。"""

    def dup_across_sections(doc):
        doc["repo_docs"][0]["id"] = doc["vault_entries"][0]["id"]

    def dotted_id(doc):
        doc["vault_entries"][0]["id"] = "dir-foo.bar"

    for mutate, name, pattern in [
        (dup_across_sections, "xsection-dup", "id 重复"),
        (dotted_id, "dotted", "kebab-case"),
    ]:
        bad = _mutated_yaml(tmp_path, mutate, name)
        with pytest.raises(cvr.ConfigError, match=pattern):
            cvr.load_rules(bad, verify_sha=False)


def test_glob_must_be_list_of_nonempty_strings(data, tmp_path):
    """标量 glob 此前被静默接受; `[null]` 抛的是 TypeError 而不是 ConfigError。"""

    def scalar_glob(doc):
        doc["vault_entries"][0]["match"]["dir_glob"] = "节点"

    def null_element(doc):
        doc["vault_entries"][0]["match"]["dir_glob"] = [None]

    for mutate, name in [(scalar_glob, "scalar-glob"), (null_element, "null-glob")]:
        bad = _mutated_yaml(tmp_path, mutate, name)
        with pytest.raises(cvr.ConfigError):
            cvr.load_rules(bad, verify_sha=False)


def test_plain_row_cannot_self_declare_surface(data, tmp_path):
    """普通行自报 `surface: store` 即可绕过 match 必填检查 (round-7)。"""

    def fake_surface(doc):
        e = doc["vault_entries"][0]
        e["surface"] = "store"
        e["match"] = {"frontmatter_type": ["(none)"]}

    bad = _mutated_yaml(tmp_path, fake_surface, "fake-surface")
    with pytest.raises(cvr.ConfigError, match="surface"):
        cvr.load_rules(bad, verify_sha=False)


def test_malformed_config_raises_config_error_not_traceback(data, tmp_path):
    """契约校验必须是**总函数**: 畸形输入要变成 ConfigError(退出 2), 不是 traceback。"""

    def malformed(doc):
        doc["admission_surfaces"]["by_design_divergences"][0]["patterns"] = [123]

    bad = _mutated_yaml(tmp_path, malformed, "malformed")
    with pytest.raises(cvr.ConfigError):
        cvr.load_rules(bad, verify_sha=False)


def test_root_files_scope_enum(data, tmp_path):
    def typo_scope(doc):
        for rf in doc["root_files"]:
            if rf.get("scope") == "any_level":
                rf["scope"] = "any_levl"
                break

    bad = _mutated_yaml(tmp_path, typo_scope, "rf-typo-scope")
    with pytest.raises(cvr.ConfigError, match="scope"):
        cvr.load_rules(bad, verify_sha=False)


# ---------------------------------------------------------------------------
# 32. round-8 的四条绕过口 (repo_docs / _section 自报 / 空 glob / 引用完整性)
# ---------------------------------------------------------------------------
def test_round8_bypass_paths_are_closed(data, tmp_path):
    """每一条都是"门只装了一半"的形态: 装在 ledger 三节、漏了 repo_docs;
    信任了 yaml 自报的 `_section`; `or []` 把显式空列表当成没写。"""

    def repo_conditional_without_note(doc):
        doc["repo_docs"][0]["rag_retrieval"] = "conditional"

    def repo_declares_surface(doc):
        doc["repo_docs"][0]["surface"] = "store"

    def forged_section(doc):
        e = doc["vault_entries"][0]
        e["_section"] = "derived_artifacts"
        e["surface"] = "store"
        e["match"] = {}

    def explicit_empty_glob(doc):
        # ⚠️ 必须让 **sibling glob 非空** 才测得到这道门 —— 否则先被
        #    "match 既无 dir_glob 也无 file_glob" 那条更早的门拦住 (两道都对, 但测的不是同一条)。
        #    这正是 round-8 描述的形态: 一个 glob 显式为 []、另一个非空。
        doc["vault_entries"][0]["match"]["file_glob"] = []

    def divergence_null_reason(doc):
        doc["admission_surfaces"]["by_design_divergences"][0]["memory_reason"] = None

    for mutate, name, pattern in [
        (repo_conditional_without_note, "repo-cond", "rag_retrieval_note"),
        (repo_declares_surface, "repo-surface", "surface"),
        (forged_section, "forged-section", "surface"),
        (explicit_empty_glob, "empty-glob-list", "显式空列表"),
        (divergence_null_reason, "null-reason", "memory_reason"),
    ]:
        bad = _mutated_yaml(tmp_path, mutate, name)
        with pytest.raises(cvr.ConfigError, match=pattern):
            cvr.load_rules(bad, verify_sha=False)


def test_exam_board_registered_by_is_complete(data, tmp_path):
    """`exam_board` 的写侧推断**不限目录** —— 凡"允许无 type 且进索引"的条目
    都能产出它, 必须一并登记。checker 机械复算这份清单, 不接受漏登。"""
    producers = {
        e["id"]
        for e in cvr.iter_entries(data)
        if cvr.NO_TYPE in ((e.get("match") or {}).get("frontmatter_type") or []) and e["rag_index"]
    }
    eb = next(v for v in data["doc_type_whitelist"]["values"] if v["value"] == "exam_board")
    assert producers <= set(eb["registered_by"]), sorted(producers - set(eb["registered_by"]))

    def drop_one_producer(doc):
        for v in doc["doc_type_whitelist"]["values"]:
            if v["value"] == "exam_board":
                v["registered_by"] = [r for r in v["registered_by"] if r != "dir-raw"]

    bad = _mutated_yaml(tmp_path, drop_one_producer, "drop-producer")
    with pytest.raises(cvr.ConfigError, match="registered_by 漏了"):
        cvr.load_rules(bad, verify_sha=False)


def test_non_utf8_ledger_is_config_error(tmp_path):
    """非法 UTF-8 台账此前在 decode 处抛 UnicodeDecodeError, 越过 CLI 的
    ConfigError-only 捕获 → 用户看到 traceback 而不是"配置错误 exit 2"。"""
    bad = tmp_path / "vault_doc_roles.yaml"
    bad.write_bytes(b"schema_version: 1\n\xff\xfe\n")
    with pytest.raises(cvr.ConfigError, match="UTF-8"):
        cvr.load_rules(bad, verify_sha=False)


# ---------------------------------------------------------------------------
# 10. glob 引擎 (顺序敏感 ruleset 的地基)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("rel", "pat", "expected"),
    [
        ("节点", "节点", True),
        ("节点/sub", "节点/**", True),
        ("节点", "节点/**", True),  # `/**` **含零层** = 目录自身也匹配 (成对写法是冗余但显式)
        ("节点X", "节点/**", False),  # 但不会吃掉同前缀的兄弟目录
        ("节点/FOO.MD", "**/*.[Mm][Dd]", True),  # 字符类: DIV-2 大小写分歧模式的地基
        ("节点/foo.md", "**/*.[Mm][Dd]", True),
        ("节点/foo.txt", "**/*.[Mm][Dd]", False),
        ("原白板", "节点", False),
        (".obsidian", "**/.obsidian", True),
        ("raw/CS188/.obsidian", "**/.obsidian", True),
        ("raw/CS188/.obsidian/plugins", "**/.obsidian/**", True),
        ("a/b/chunks", "**/chunks", True),
        ("chunks", "**/chunks", True),
        ("Dashboard.md", "*.md", True),
        ("sub/Dashboard.md", "*.md", False),  # `*` 不跨 `/` —— 根级兜底行不会吃深层文件
        ("raw/CS 188-explanations", "**/*-explanations", True),
    ],
)
def test_glob_engine(rel, pat, expected):
    assert cvr.glob_match(rel, pat) is expected


def test_declared_divergence_matches_by_class_not_instance(data):
    """覆盖判定 = (pattern, scope, 布尔对, **reason 对**) 四者全等。"""
    declared = data["admission_surfaces"]["by_design_divergences"]
    cover = cvr._covered_by_declared_divergence

    # DIV-1 同类新实例 (根级 md, ok/root_level) → 已覆盖, 不该判红
    assert cover(declared, "brand-new-note.md", True, True, "ok", False, "root_level")
    # 深层文件出现同向分歧 → 不在 DIV-1 的 scope 内, 必须判红
    assert not cover(declared, "节点/x.md", False, True, "ok", False, "root_level")

    # DIV-2 登记了 0 live 实例, 但类仍然生效
    assert cover(declared, "节点/FOO.MD", False, False, "not_markdown", True, "ok")
    assert cover(declared, "节点/foo.Md", False, False, "not_markdown", True, "ok")
    # ⛔ 全小写 .md 的同向分歧 = 新类 —— DIV-2 的 pattern 刻意不吃它
    assert not cover(declared, "节点/foo.md", False, False, "not_markdown", True, "ok")
    # 方向不符不算覆盖
    assert not cover(declared, "节点/FOO.MD", False, True, "ok", False, "root_level")

    # ⛔ Codex round-1 BLOCKER-2 的两个真实反例: 布尔对相同但 **reason 不同**,
    #    绝不能被 DIV-1 吞掉 —— 否则 G6 对新分歧类彻底失效。
    assert not cover(declared, "alias-text.md", True, True, "ok", False, "not_markdown")
    assert not cover(declared, "alias-blacklisted.md", True, True, "ok", False, "blacklisted_dir")


# ---------------------------------------------------------------------------
# 11. root_files 顺序契约 (兜底行必须最后)
# ---------------------------------------------------------------------------
def test_root_files_order_contract(data):
    rows = data["root_files"]
    assert rows[-1]["id"] == cvr.EXPECTED_LAST_ROOT_FILE_ID
    assert rows[-1]["match"]["file_glob"] == ["*.md"]

    # 黑名单行必须先于兜底行命中 —— 否则 Untitled.md 会被判成"可索引根级笔记"
    assert cvr.resolve_file_entry(data, "Untitled.md")["id"] == "root-untitled-scratch"
    assert cvr.resolve_file_entry(data, "Dashboard.md")["id"] == "root-dashboard"
    assert cvr.resolve_file_entry(data, "CLAUDE.md")["id"] == "root-claude-md"
    assert cvr.resolve_file_entry(data, "UAT-x.md")["id"] == "root-uat-scratch"
    # 未命中黑名单的根级 md 才落到兜底行 (DIV-1 的落点)
    loose = cvr.resolve_file_entry(data, "chatgpt-adversarial-review-Q1Q2Q3-2026-05-12.md")
    assert loose["id"] == cvr.EXPECTED_LAST_ROOT_FILE_ID
    assert loose["rag_index"] is True and loose["memory_write"] is False

    # any_level 行按 basename 生效 (DEFAULT_VAULT_SKIP_FILES 是任意层级 basename 匹配)
    assert cvr.resolve_file_entry(data, "raw/CS188/CLAUDE.md")["id"] == "root-claude-md"
    assert cvr.resolve_file_entry(data, "raw/CS188/管道设计.md")["id"] == "root-pipeline-design"
    # 深层非黑名单 md 落到目录行, 不被根级兜底行吃掉
    assert cvr.resolve_file_entry(data, "节点/foo.md")["id"] == "dir-jiedian"
