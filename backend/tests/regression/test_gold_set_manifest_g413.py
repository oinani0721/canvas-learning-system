"""CARD-G4-13 承重行为门：金集 ≥100 + 逐条用户裁定标签 + SHA 冻结 manifest + runner 接线。

[BATCH-2026-09-18-第十五批 / CARD-G4-13]

这个文件钉住五件**行为**（不是文本）：

1. 两个主金集合计 **≥100 条**，其中跨 vault 攻击类 vault ≥15 / memory ≥2；
2. 四份金集的**每一条** query 都带 ``user_verdict``（五枚举）与 ``source``（六枚举 + ref）；
3. ``gold_set_manifest.yaml`` 里每一项的 ``sha256`` 与**本测试自己实算**的一致
   —— 两侧来自不同的读法，不是同一个来源自证自己；
4. **既有 83 条逐字不变**：用 ``git show 9c4e7e82:<path>`` 取旧文逐条比十个判分/元数据键；
5. **两个 runner 真的接了校验**：``importlib`` 载入真 runner（⚠️ **先载工具、后载
   runner**，两者必须共用同一模块实例），把 manifest 常量指向**篡改 sha 的副本**
   （真金集文件在位），走真 ``main()`` → rc=2 且文案含 **sha 比较签名**
   （「sha256 期望…实测…」）。—— 2026-09-19 r2 整改：旧版把金集指向仓外 tmp 副本 +
   死补丁打在另一模块实例上，经「在仓外」早退分支**假绿**（r1 H-2；探针存档
   ``negctl-r2-h2-oldpath-*.txt``）。
6. **``verify_gold_set_file`` 的 fail-closed 边界**：三类环境/输入错（manifest 解析
   失败 / 顶层非映射 / 已登记文件缺失）返回 ``(False, 文案)``、**不抛异常**，且经
   runner 真 ``main()`` 收场为 rc=2（r1 H-1，r2 整改 2026-09-19）。

⛔ 实现约束（卡文 §一(g)）：读**真实**四 yaml + 真实 manifest + 真实 runner 模块。
不连库、不起 8011、不 mock yaml/sha。所有写操作都在 ``tmp_path`` 里。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

#: ``backend/`` 的绝对路径。本文件位于 ``backend/tests/regression/``，往上两级。
BACKEND_ROOT = Path(__file__).resolve().parents[2]

REGRESSION_DIR = BACKEND_ROOT / "tests" / "regression"
SCRIPTS_DIR = BACKEND_ROOT / "scripts"

VAULT_GOLD = REGRESSION_DIR / "vault_gold_set.yaml"
MEMORY_GOLD = REGRESSION_DIR / "memory_gold_set.yaml"
VAULT_SHADOW = REGRESSION_DIR / "vault_gold_set_shadow.yaml"
MEMORY_SHADOW = REGRESSION_DIR / "memory_gold_set_shadow.yaml"
MANIFEST = REGRESSION_DIR / "gold_set_manifest.yaml"
TOOL = SCRIPTS_DIR / "gold_set_manifest_tool.py"

#: manifest 登记的四份金集。顺序 = manifest ``files[]`` 的顺序。
ALL_SETS = (VAULT_GOLD, MEMORY_GOLD, VAULT_SHADOW, MEMORY_SHADOW)

#: ``user_verdict`` 的五枚举（卡文 §一(d)）。``pending`` 是默认值 ——
#: 用户裁定 session 是 user_touchpoint，没开窗口就全部停在 pending。
VERDICT_ENUM = {"pending", "relevant", "irrelevant", "ambiguous", "needs_split"}

#: ``source.kind`` 的六枚举。``synthetic`` 给那些**查不到来源**的条目
#: （vault 集里有 4 条没有 ``origin``）—— 写 synthetic + ref=None，不编造来源。
SOURCE_KIND_ENUM = {"node", "whiteboard", "exam_board", "review_doc", "fixture", "synthetic"}

#: 既有条目不变的对照基准 commit（卡文 §一(c) / §〇 冻结基准）。
BASE_COMMIT = "9c4e7e82"

#: 逐条比较的十个键：判分用的六个 + 元数据四个。改动其中任何一个都会让
#: 既有 83 条的语义变化，因此本卡把它们全部钉死。
FROZEN_KEYS = (
    "id",
    "query",
    "expect_hit",
    "expect_not_hit",
    "expect_any",
    "expect_empty",
    "query_type",
    "category",
    "language",
    "origin",
)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _queries(path: Path) -> list:
    return _load(path).get("queries") or []


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _import_tool():
    """把工具当模块导入（它就在 ``backend/scripts/`` 下，不是包）。"""
    spec = importlib.util.spec_from_file_location("gold_set_manifest_tool", TOOL)
    assert spec and spec.loader, f"无法为 {TOOL} 建 import spec"
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gold_set_manifest_tool"] = mod
    spec.loader.exec_module(mod)
    return mod


def _import_runner(name: str):
    """载入真的 runner 模块（顶层只 import stdlib + yaml/httpx，不拖 app）。"""
    path = SCRIPTS_DIR / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader, f"无法为 {path} 建 import spec"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)
    return mod


def _git_show(rev_path: str) -> str | None:
    """取旧版文件内容；git 不可用时返回 None（由调用方 skip，不假绿）。"""
    try:
        r = subprocess.run(
            ["git", "show", rev_path],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


# ═══════════════════════════════════════════════════════════════════════════
# ① 每条 query 的标注字段完整且合法
# ═══════════════════════════════════════════════════════════════════════════


def test_every_query_has_verdict_and_source() -> None:
    """四份金集的**每一条** query 都带合法的 ``user_verdict`` 与 ``source``。

    ⚠️ 这条断言期望「违规集为空」，所以必须先证明**输入面非空** ——
    否则某天 yaml 变成空文件，它会空洞变绿。
    """
    total = 0
    bad = []
    for path in ALL_SETS:
        for q in _queries(path):
            total += 1
            qid = q.get("id", "<no-id>")
            v = q.get("user_verdict")
            if v not in VERDICT_ENUM:
                bad.append(f"{path.name}::{qid} user_verdict={v!r} 不在 {sorted(VERDICT_ENUM)}")
            src = q.get("source")
            if not isinstance(src, dict):
                bad.append(f"{path.name}::{qid} source 不是 mapping：{src!r}")
                continue
            if src.get("kind") not in SOURCE_KIND_ENUM:
                bad.append(f"{path.name}::{qid} source.kind={src.get('kind')!r} 不在枚举")
            ref = src.get("ref")
            if ref is not None and not isinstance(ref, str):
                bad.append(f"{path.name}::{qid} source.ref 既不是 str 也不是 None：{ref!r}")

    assert total >= 100, f"验伪锚：四份金集合计只数出 {total} 条，输入面不该这么小"
    assert bad == [], "以下条目的标注字段不合法：\n  " + "\n  ".join(bad)


def test_no_duplicate_annotation_keys() -> None:
    """每份 yaml 里 ``user_verdict:`` 的**行数**必须等于 query 条数。

    ⚠️ 为什么需要这条「文本层」判据，而上面那条「解析层」判据不够：
    ``yaml.safe_load`` 对**重复键静默取最后一个**。所以一条 query 若被写了两遍
    标注键，解析结果看起来完全正常 —— 上面那条会绿，而后写的那份会把先写的
    悄悄覆盖掉。本卡实测踩过：迁移脚本跑了两趟，17 条攻击条目的
    ``source.ref`` 被第二趟的 ``null`` 覆盖，**来源指针整片丢失**，
    而当时所有解析层判据都是绿的（是负控③ 把它挖出来的）。

    ⇒ 「解析后对不对」与「文本里有没有重复」是**两个维度**，
    少一个维度的门，多补几个样本也补不出来。
    """
    problems = []
    for path in ALL_SETS:
        text = path.read_text(encoding="utf-8")
        n_q = len([ln for ln in text.splitlines() if ln.startswith("  - id:")])
        for key in ("user_verdict:", "verdict_by:", "verdict_at:", "source:"):
            n_k = len([ln for ln in text.splitlines() if ln.strip().startswith(key)])
            if n_k != n_q:
                problems.append(f"{path.name}: {key} 出现 {n_k} 次，但只有 {n_q} 条 query")
    assert problems == [], "标注键有重复或缺失（yaml 解析看不出来）：\n  " + "\n  ".join(problems)


# ═══════════════════════════════════════════════════════════════════════════
# ② 总数与跨 vault 攻击类配额
# ═══════════════════════════════════════════════════════════════════════════


def test_totals_meet_the_floor() -> None:
    """两主集合计 ≥100；vault 跨 vault 攻击 ≥15、memory ≥2。"""
    vault_qs = _queries(VAULT_GOLD)
    mem_qs = _queries(MEMORY_GOLD)
    main_total = len(vault_qs) + len(mem_qs)
    vault_attack = [q for q in vault_qs if q.get("query_type") == "cross_vault_attack"]
    mem_attack = [q for q in mem_qs if q.get("category") == "cross_vault_attack"]

    assert main_total >= 100, f"两主集合计 {main_total} < 100（vault {len(vault_qs)} + memory {len(mem_qs)}）"
    assert len(vault_attack) >= 15, f"vault 的 cross_vault_attack 只有 {len(vault_attack)} 条 < 15"
    assert len(mem_attack) >= 2, f"memory 的 cross_vault_attack 只有 {len(mem_attack)} 条 < 2"


def test_manifest_totals_match_the_files() -> None:
    """manifest 里的 ``totals`` 与**实际文件**数得出来的一致。

    manifest 是下游 G4-14 的输入，它自报的数字必须能被重新数出来。
    """
    m = _load(MANIFEST)
    counted_main = len(_queries(VAULT_GOLD)) + len(_queries(MEMORY_GOLD))
    counted_attack = len([q for q in _queries(VAULT_GOLD) if q.get("query_type") == "cross_vault_attack"]) + len(
        [q for q in _queries(MEMORY_GOLD) if q.get("category") == "cross_vault_attack"]
    )
    assert m["totals"]["main_set_queries"] == counted_main, (
        f"manifest 自报 main_set_queries={m['totals']['main_set_queries']}，实数 {counted_main}"
    )
    assert m["totals"]["cross_vault_attack"] == counted_attack, (
        f"manifest 自报 cross_vault_attack={m['totals']['cross_vault_attack']}，实数 {counted_attack}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# ③ manifest 的 sha256 与本测试实算一致 + verify 通过
# ═══════════════════════════════════════════════════════════════════════════


def test_manifest_sha_matches_independently_computed() -> None:
    """manifest 每项 ``sha256`` = 本测试用 ``hashlib`` 实算的值。

    ⚠️ 故意**不**调工具去算：两侧必须来自不同的读法，否则是同一个来源自证自己。
    """
    m = _load(MANIFEST)
    entries = {e["path"]: e for e in m["files"]}
    assert len(entries) == len(ALL_SETS), f"manifest 应登记 {len(ALL_SETS)} 份文件，实得 {len(entries)}"
    for path in ALL_SETS:
        rel = str(path.relative_to(BACKEND_ROOT.parent))
        assert rel in entries, f"manifest 没登记 {rel}；已登记的是 {sorted(entries)}"
        assert entries[rel]["sha256"] == _sha256(path), (
            f"{rel} 的 sha256 与实算不符：manifest={entries[rel]['sha256']} 实算={_sha256(path)}"
        )


def test_tool_verify_returns_zero_on_repo_files() -> None:
    """工具的 ``verify`` 对仓内四文件 rc=0，且每项打出 ``OK``。"""
    tool = _import_tool()
    rc, lines = tool.verify_all(MANIFEST)
    assert rc == 0, "verify 对未篡改的仓内文件应当 rc=0，实得 rc=%d\n%s" % (rc, "\n".join(lines))
    ok_lines = [ln for ln in lines if ln.startswith("OK ")]
    assert len(ok_lines) >= len(ALL_SETS), f"OK 行只有 {len(ok_lines)} 条，少于登记的文件数\n" + "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# ④ 既有 83 条逐字不变
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("path", "expected_old_count"),
    [(VAULT_GOLD, 58), (MEMORY_GOLD, 25)],
    ids=["vault", "memory"],
)
def test_existing_entries_unchanged(path: Path, expected_old_count: int) -> None:
    """``9c4e7e82`` 那版里的每一条，十个判分/元数据键必须逐字不变。

    git 不可用 ⇒ ``skip`` 并说明，**不假绿**。
    """
    rel = str(path.relative_to(BACKEND_ROOT.parent))
    old_text = _git_show(f"{BASE_COMMIT}:{rel}")
    if old_text is None:
        pytest.skip(f"git show {BASE_COMMIT}:{rel} 不可用 —— 本条无法验证（不当作通过）")

    old = {q["id"]: q for q in (yaml.safe_load(old_text) or {}).get("queries") or []}
    new = {q["id"]: q for q in _queries(path)}
    assert len(old) == expected_old_count, f"{rel} 在 {BASE_COMMIT} 上应有 {expected_old_count} 条，实得 {len(old)}"

    diffs = []
    for qid, oq in old.items():
        if qid not in new:
            diffs.append(f"{qid} 整条不见了")
            continue
        nq = new[qid]
        for k in FROZEN_KEYS:
            if oq.get(k) != nq.get(k):
                diffs.append(f"{qid}.{k}: {oq.get(k)!r} → {nq.get(k)!r}")
    assert diffs == [], f"{rel} 的既有条目被改动了：\n  " + "\n  ".join(diffs)


# ═══════════════════════════════════════════════════════════════════════════
# ⑤ 两个 runner 真的接了校验
# ═══════════════════════════════════════════════════════════════════════════


def _flip_first_char(s: str) -> str:
    """把一段 hex 的**首字符**翻一位（截断显示上也能看出「期望 ≠ 实测」）。"""
    return ("0" if s[0] != "0" else "1") + s[1:]


def _tampered_manifest_copy(tmp_path: Path, rel_path: str) -> Path:
    """manifest 副本：把 ``rel_path`` 那一条的 ``sha256`` 首字符翻一位，其余原样。"""
    doc = _load(MANIFEST)
    hits = 0
    for entry in doc.get("files") or []:
        if entry.get("path") == rel_path:
            entry["sha256"] = _flip_first_char(entry["sha256"])
            hits += 1
    assert hits == 1, f"{rel_path} 在 manifest 里应恰有 1 条，实得 {hits}"
    dst = tmp_path / "gold_set_manifest.tampered.yaml"
    dst.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return dst


@pytest.mark.parametrize(
    ("runner_file", "argv", "shadow_rel"),
    [
        (
            "run_vault_retrieval_regression.py",
            ["--shadow", "--no-hook"],
            "backend/tests/regression/vault_gold_set_shadow.yaml",
        ),
        (
            "run_memory_retrieval_regression.py",
            ["--shadow", "--no-judge"],
            "backend/tests/regression/memory_gold_set_shadow.yaml",
        ),
    ],
    ids=["vault", "memory"],
)
def test_runner_rejects_tampered_gold_set(
    runner_file: str, argv: list, shadow_rel: str, tmp_path: Path, monkeypatch, capsys
) -> None:
    """篡改 **manifest 里的 sha** 后走**真的** ``main()`` → rc=2 且文案**含 sha 比较签名**。

    ⚠️ r1 H-2 的教训：旧版把金集常量指向仓外 tmp 副本 ⇒ 走「在仓外」早退分支；
    再叠一个打在**另一个模块实例**上的死补丁 —— rc=2 + 「不符」照样绿，但**根本没
    走到 sha 比较**（探针存档 ``negctl-r2-h2-oldpath-*.txt``）。本版：
    ① 先 ``_import_tool`` 再 ``_import_runner`` ⇒ runner 里的 ``verify_gold_set_file``
    与本测试拿到的是**同一模块实例**（patch 不再可能是死补丁，下面有身份断言钉住）；
    ② 真金集文件在位，只把 manifest 副本里对应条目的 sha 翻一位 ⇒ 必经 sha 比较。
    **验伪锚**：断言文案含「sha256 期望…实测」（只有 sha 比较支路产得出）且不含
    「在仓外」；**对照输入**：同一机制 + 未篡改 manifest ⇒ 校验放行（``OK``），
    证明该拒绝支路对「sha 是否被改」敏感，不是恒真。
    """
    tool = _import_tool()  # ⚠️ 必须先于 runner：runner 的 `from … import` 复用这个实例
    runner = _import_runner(runner_file)
    assert runner.verify_gold_set_file is tool.verify_gold_set_file, (
        "runner 用的不是本测试这个工具实例 —— manifest patch 会退化成死补丁（r1 H-2）"
    )

    tampered = _tampered_manifest_copy(tmp_path, shadow_rel)
    monkeypatch.setattr(tool, "MANIFEST_PATH", tampered)

    monkeypatch.setattr(sys, "argv", [runner_file, *argv])
    rc = runner.main()
    out = capsys.readouterr()
    combined = out.out + out.err
    assert rc == 2, f"篡改 manifest sha 后 {runner_file} 应 rc=2，实得 {rc}\n{combined}"
    assert "不符" in combined, f"{runner_file} 的拒绝文案里没有「不符」：\n{combined}"
    assert "sha256 期望" in combined and "实测" in combined, (
        f"{runner_file} 的拒绝没有走到 sha 比较（缺「sha256 期望…实测」签名）：\n{combined}"
    )
    assert "在仓外" not in combined, f"{runner_file} 走了「在仓外」早退分支（= r1 H-2 假绿路径）：\n{combined}"

    # 对照输入（验伪锚的另一半）：同一机制 + **未篡改** manifest ⇒ 放行（OK）
    clean = tmp_path / "gold_set_manifest.clean.yaml"
    clean.write_bytes(MANIFEST.read_bytes())
    ok, detail = tool.verify_gold_set_file(BACKEND_ROOT.parent / shadow_rel, manifest_path=clean)
    assert ok is True and detail.startswith("OK "), f"未篡改的对照输入应当放行，实得 {(ok, detail)!r}"


# ═══════════════════════════════════════════════════════════════════════════
# ⑥ apply-verdicts 往返
# ═══════════════════════════════════════════════════════════════════════════


def test_checklist_and_apply_verdicts_roundtrip(tmp_path: Path) -> None:
    """``checklist`` 出 md → 勾一条 → ``apply-verdicts`` 回写 → 只有那条变。"""
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes())

    md = tmp_path / "checklist.md"
    n = tool.write_checklist([src], md)
    assert n >= 1, "checklist 一条都没写出来"
    text = md.read_text(encoding="utf-8")

    qs = _queries(src)
    target = qs[0]["id"]
    assert f"<!-- gsid:{target} -->" in text, f"checklist 里没有 {target} 的隐藏锚"

    # 勾「相关」那一格
    marked = []
    for line in text.splitlines():
        if target in line or (marked and marked[-1].strip().startswith(f"<!-- gsid:{target}")):
            pass
        marked.append(line)
    text2 = text.replace(f"<!-- gsid:{target} -->", f"<!-- gsid:{target} -->", 1)
    # 在该条的「相关」checkbox 上打勾
    lines = text2.splitlines()
    for i, line in enumerate(lines):
        if f"<!-- gsid:{target} -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if "relevant" in lines[j] and lines[j].lstrip().startswith("- [ ]"):
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-19T00:00:00Z")
    assert problems == [], f"apply-verdicts 报了问题：{problems}"
    assert changed == [target], f"应当只改 {target}，实得 {changed}"

    after = {q["id"]: q for q in _queries(src)}
    assert after[target]["user_verdict"] == "relevant"
    assert after[target]["verdict_by"] == "user"
    others = [q for qid, q in after.items() if qid != target]
    assert all(q["user_verdict"] == "pending" for q in others), "其余条目不该被动"


# ═══════════════════════════════════════════════════════════════════════════
# ⑦ collect 只读
# ═══════════════════════════════════════════════════════════════════════════


def test_collect_is_read_only(tmp_path: Path) -> None:
    """``collect`` 扫一个假 vault 出候选，且那个 vault **一个字节都没变**。"""
    tool = _import_tool()
    vault = tmp_path / "fake-vault"
    (vault / "节点").mkdir(parents=True)
    (vault / "原白板").mkdir(parents=True)
    a = vault / "节点" / "概念甲.md"
    a.write_text("# 概念甲\n\n> [!question]+ 这是我手写的疑问？\n> 正文\n", encoding="utf-8")
    b = vault / "原白板" / "板一.md"
    b.write_text("# 板一标题\n\n内容\n", encoding="utf-8")

    before = {p: p.read_bytes() for p in (a, b)}
    out = tmp_path / "candidates.json"
    n = tool.collect_candidates(vault, out)

    assert n >= 1, "collect 一条候选都没产出"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list) and data, "候选 json 不是非空列表"
    assert all("source" in c and "ref" in c["source"] for c in data), "候选缺 source.ref"
    for p, content in before.items():
        assert p.read_bytes() == content, f"collect 改动了 vault 文件：{p}"


# ═══════════════════════════════════════════════════════════════════════════
# ⑧ verify_gold_set_file 的 fail-closed 边界（r2 整改，zcode r1 H-1）
# ═══════════════════════════════════════════════════════════════════════════

#: 一份**典型**的合并冲突残骸（``<<<<<<<``）—— 生成文件进 git 后最常见的输入错形态。
_CONFLICT_MANIFEST = "<<<<<<< HEAD\nrevision: 2\n=======\nrevision: 1\n>>>>>>> batch-branch\n"


def test_verify_gold_set_file_input_errors_fail_closed(tmp_path: Path) -> None:
    """四类环境/输入错返回 ``(False, 文案)``，**不得抛异常**（r1 H-1）。

    修复前三类分别以 ``yaml.YAMLError`` / ``AttributeError`` / ``FileNotFoundError``
    逃逸 ⇒ 两个 runner 以未捕获异常收场（exit 1 =「指标回退」档），把 rc=2 的
    「环境/输入错」语义污染掉。
    """
    tool = _import_tool()

    # ① manifest 带合并冲突标记 → YAMLError 不得逃逸
    conflict = tmp_path / "conflict.yaml"
    conflict.write_text(_CONFLICT_MANIFEST, encoding="utf-8")
    ok, detail = tool.verify_gold_set_file(VAULT_GOLD, manifest_path=conflict)
    assert ok is False and "解析失败" in detail, f"解析错未 fail-closed：{(ok, detail)!r}"

    # ② manifest 顶层不是映射（yaml 出的是个列表）→ 不得崩在 .get
    notmap = tmp_path / "notmap.yaml"
    notmap.write_text("- just\n- a\n- list\n", encoding="utf-8")
    ok, detail = tool.verify_gold_set_file(VAULT_GOLD, manifest_path=notmap)
    assert ok is False and "不是映射" in detail, f"非映射未 fail-closed：{(ok, detail)!r}"

    # ③ 已登记但文件缺失 → 不得崩在 sha256_of（FileNotFoundError）
    ghost_rel = "backend/tests/regression/__g413_ghost__.yaml"
    assert not (BACKEND_ROOT.parent / ghost_rel).exists(), f"探针文件不该存在：{ghost_rel}"
    ghost_manifest = tmp_path / "ghost-manifest.yaml"
    doc = _load(MANIFEST)
    doc["files"][0]["path"] = ghost_rel  # 借 manifest 真骨架，只改一条的 path
    ghost_manifest.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    ok, detail = tool.verify_gold_set_file(BACKEND_ROOT.parent / ghost_rel, manifest_path=ghost_manifest)
    assert ok is False and "缺失" in detail, f"缺失文件未 fail-closed：{(ok, detail)!r}"

    # ④ 条目 sha256 缺失/非法（非 str）→ 不得崩在 sha 比较/格式化
    bad_sha_manifest = tmp_path / "bad-sha-manifest.yaml"
    doc = _load(MANIFEST)
    doc["files"][0]["sha256"] = None
    bad_sha_manifest.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    ok, detail = tool.verify_gold_set_file(VAULT_GOLD, manifest_path=bad_sha_manifest)
    assert ok is False and "sha256" in detail, f"sha 字段非法未 fail-closed：{(ok, detail)!r}"


@pytest.mark.parametrize(
    ("runner_file", "argv"),
    [
        ("run_vault_retrieval_regression.py", ["--shadow", "--no-hook"]),
        ("run_memory_retrieval_regression.py", ["--shadow", "--no-judge"]),
    ],
    ids=["vault", "memory"],
)
def test_runner_reports_manifest_parse_error_as_rc2(
    runner_file: str, argv: list, tmp_path: Path, monkeypatch, capsys
) -> None:
    """manifest 解析错经**真 main()** 收场为 rc=2 + 文案，而不是未捕获异常（r1 H-1 的原始危害）。

    修复前 ``yaml.YAMLError`` 从 ``verify_gold_set_file`` 逃逸 ⇒ 未捕获异常收场
    （exit 1 =「指标回退」档）；修复后走 ``(False, 文案)`` ⇒「不符 (解析失败…)」+ rc=2。
    """
    tool = _import_tool()  # ⚠️ 先于 runner（同 ⑤ 的死补丁教训）
    runner = _import_runner(runner_file)

    conflict = tmp_path / "conflict.yaml"
    conflict.write_text(_CONFLICT_MANIFEST, encoding="utf-8")
    monkeypatch.setattr(tool, "MANIFEST_PATH", conflict)

    monkeypatch.setattr(sys, "argv", [runner_file, *argv])
    rc = runner.main()  # 修复前：这里抛 yaml.YAMLError（测试红）
    out = capsys.readouterr()
    combined = out.out + out.err
    assert rc == 2, f"{runner_file} 对解析错 manifest 应 rc=2，实得 {rc}\n{combined}"
    assert "不符" in combined and "解析失败" in combined, f"{runner_file} 的文案没有「不符 (解析失败…)」：\n{combined}"
