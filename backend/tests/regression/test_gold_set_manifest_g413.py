"""CARD-G4-13 承重行为门：金集 ≥100 + 逐条用户裁定标签 + SHA 冻结 manifest + runner 接线。

[BATCH-2026-09-18-第十五批 / CARD-G4-13]

这个文件钉住八件**行为**（不是文本）：

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
6. **``verify_gold_set_file`` 的 fail-closed 边界**：环境/输入错一律返回
   ``(False, 文案)``、**不抛异常** —— r2 覆盖解析失败 / 顶层非映射 / 文件缺失 /
   sha 字段非法（r1 H-1）；r3 再扩 OSError+UnicodeDecodeError 族与 ``files``
   非列表（r2 复核 M-R2a/M-R2b）。每 case 独立成条测试 ⇒ 先红/后绿证据互不遮蔽
   （r2 的⑧四 case 串在一个函数里、先红被 case① 遮蔽 —— L-R2b）。
7. **``checklist`` → 勾选 → ``apply-verdicts`` 回写**：只**逐行**动
   ``user_verdict`` / ``verdict_by`` / ``verdict_at`` 三行（不得整段 safe_dump；
   M-2）；锚丢失 / 读不懂的勾选一律 fail-closed 不写（M-1 / L-1）。
8. **``collect`` 只读**（含 ``--out`` 不得落在 ``--vault`` 内的守卫）。

⛔ 实现约束（卡文 §一(g)）：读**真实**四 yaml + 真实 manifest + 真实 runner 模块。
不连库、不起 8011、不 mock yaml/sha。所有写操作都在 ``tmp_path`` 里。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
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


def _pick_other_verdict(avoid: str | None) -> tuple[str, str]:
    """选一个与现状不同的 verdict（保证回写一定有字节变化），返回 ``(值, 清单锚)``。

    ⚠️ 用户裁定完成后，首个条目可能已是 relevant —— 若测试仍硬勾 relevant，回写会退化成
    空操作，「恰 3 行变化」类断言就失去判别力（2026-09-20 实测踩过）。
    """
    v = "ambiguous" if avoid != "ambiguous" else "relevant"
    return v, f"verdict:{v}"


def _mark(lines: list, gid: str, anchor: str) -> list:
    """把清单里 ``gid`` 条的 ``anchor`` 勾选框打勾（就地改，返回同一 list）。"""
    for i, line in enumerate(lines):
        if f"<!-- gsid:{gid} -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and anchor in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    return lines
    raise AssertionError(f"清单里没找到 {gid} 的 {anchor} 勾选框")


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
    #: 每条 query 里**必须恰出现一次**的标注键。
    required = ("user_verdict", "verdict_by", "verdict_at", "source")
    #: **至多出现一次**的判分/元数据键（L-2：判分键也要进文本层防护）。
    optional = ("query", "language", "origin", "expect_hit", "expect_not_hit", "expect_any", "expect_empty")
    #: 容忍引号键（``"user_verdict":``）与任意缩进 —— r3 前的判据只认未加引号拼写。
    key_line = re.compile(r'^\s*"?([A-Za-z_]+)"?\s*:')
    for path in ALL_SETS:
        text = path.read_text(encoding="utf-8")
        blocks: list = []
        for ln in text.splitlines():
            if ln.startswith("  - id:"):
                blocks.append([])
            if blocks:
                blocks[-1].append(ln)
        # 反空转锚（r3 复核 MEDIUM）：扫不到块 / 块数与解析层不符 ⇒ 判据作废，不许静默通过。
        # 空集（memory shadow，0 条）合法地没有块 —— 只在有 query 的文件上要求块数相符。
        n_q = len(_queries(path))
        if n_q:
            assert blocks, f"{path.name}: 文本层一条 `  - id:` 都没扫到 —— 判据会空转"
            assert len(blocks) == n_q, f"{path.name}: 文本层 {len(blocks)} 块 vs 解析层 {n_q} 条"
        for b in blocks:
            counts: dict = {}
            for ln in b:
                m = key_line.match(ln)
                if m:
                    counts[m.group(1)] = counts.get(m.group(1), 0) + 1
            for key in required:
                if counts.get(key, 0) != 1:
                    problems.append(f"{path.name}: 一个 query 块里 {key} 出现 {counts.get(key, 0)} 次（应恰 1 次）")
            for key in optional:
                if counts.get(key, 0) > 1:
                    problems.append(f"{path.name}: 一个 query 块里 {key} 出现 {counts.get(key, 0)} 次（至多 1 次）")
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


def _pin_env_after_verify(monkeypatch, runner, runner_file: str) -> list:
    """把「校验先于环境检查」钉成**确定性**（M-3，r3）。

    r2 前：仅当 8011 恰好 down 时才真正检验顺序（backend up 时把校验挪到 alive
    之后门仍绿 —— 对照输入已由评审给出）。修后：

    * memory：``check_backend_alive`` 钉成 ``False`` 并**记录调用** —— 顺序若被挪后，
      本测试的「不符」断言会红；环境 up/down 都不再影响结论；返回列表在「校验先失败」
      场景应恒为空，对照测试则断言它恰为 ``["alive"]``（证 pin 真生效，r4：r3 版
      无法与「backend 恰好 down」区分）；
    * vault：``run_tiers`` 换成记录器 —— 校验若没有先行，记录器先被调用（返回的
      列表应恒为空）。
    """
    calls: list = []
    if "memory" in runner_file:

        def _alive() -> bool:
            calls.append("alive")
            return False

        monkeypatch.setattr(runner, "check_backend_alive", _alive)
    else:

        async def _recorder(gold):
            calls.append("run_tiers")
            raise RuntimeError("run_tiers 不该在校验失败前被调用（M-3 pin）")

        monkeypatch.setattr(runner, "run_tiers", _recorder)
    return calls


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
    calls = _pin_env_after_verify(monkeypatch, runner, runner_file)

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
    assert "manifest 只登记仓内路径" not in combined, (
        f"{runner_file} 走了「在仓外」早退分支（= r1 H-2 假绿路径）：\n{combined}"
    )
    assert calls == [], f"{runner_file}: 校验失败时不该先碰环境检查（M-3）—— 实际调用：{calls}"

    # 对照输入（验伪锚的另一半）：同一机制 + **未篡改** manifest ⇒ 放行（OK）
    clean = tmp_path / "gold_set_manifest.clean.yaml"
    clean.write_bytes(MANIFEST.read_bytes())
    ok, detail = tool.verify_gold_set_file(BACKEND_ROOT.parent / shadow_rel, manifest_path=clean)
    assert ok is True and detail.startswith("OK "), f"未篡改的对照输入应当放行，实得 {(ok, detail)!r}"


# ═══════════════════════════════════════════════════════════════════════════
# ⑥ apply-verdicts 往返
# ═══════════════════════════════════════════════════════════════════════════


def test_checklist_and_apply_verdicts_roundtrip(tmp_path: Path) -> None:
    """``checklist`` 出 md → 勾一条 → ``apply-verdicts`` 回写 → **只有那条的三行变**。

    M-2（r3）：回写必须**逐行原地**改三个标注字段 —— 不得整段 ``safe_dump`` 重写
    （那会抹掉 queries 段注释、flow→block、引号重排，产生与裁定无关的大面积 churn）。
    """
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes())
    before_lines = src.read_text(encoding="utf-8").splitlines()

    md = tmp_path / "checklist.md"
    n = tool.write_checklist([src], md)
    assert n >= 1, "checklist 一条都没写出来"
    text = md.read_text(encoding="utf-8")

    qs = _queries(src)
    before_vals = {q["id"]: q.get("user_verdict") for q in qs}
    target = qs[0]["id"]
    want, anchor = _pick_other_verdict(before_vals[target])
    assert f"<!-- gsid:{target} -->" in text, f"checklist 里没有 {target} 的隐藏锚"

    lines = _mark(text.splitlines(), target, anchor)
    # 清单尾部的「补审」文字段（粗体行 + 破折号）不是条目标题，不得被误当标题报问题
    lines += [
        "",
        "---",
        "",
        "## 补审（示例）",
        "",
        "> 本节无勾选框、无 gsid 锚。",
        "",
        "**结果（绑 `d06f7127` 的一轮）：BLOCKER 0 / HIGH 2** —— ⛔ 说明文字。",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-19T00:00:00Z")
    assert problems == [], f"apply-verdicts 报了问题：{problems}"
    assert changed == [target], f"应当只改 {target}，实得 {changed}"

    after = {q["id"]: q for q in _queries(src)}
    assert after[target]["user_verdict"] == want
    assert after[target]["verdict_by"] == "user"
    assert after[target]["verdict_at"] == "2026-09-19T00:00:00Z"
    assert all(q["user_verdict"] == before_vals[qid] for qid, q in after.items() if qid != target), "其余条目不该被动"

    # M-2：文本层逐行对账 —— 只许动目标那三行，且 queries 段注释原样保留。
    after_text = src.read_text(encoding="utf-8")
    after_lines = after_text.splitlines()
    assert len(after_lines) == len(before_lines), "回写不该增删行"
    diff = [i for i, (a, b) in enumerate(zip(before_lines, after_lines)) if a != b]
    assert len(diff) == 3, f"应恰有 3 行变化（三个标注字段），实测 {len(diff)} 行"
    keys = {before_lines[i].strip().split(":", 1)[0] for i in diff}
    assert keys == {"user_verdict", "verdict_by", "verdict_at"}, f"变动的不是三个标注字段：{keys}"
    assert "═══ definition_recall" in after_text, "queries 段的分节注释被抹掉了（M-2 回归）"


def test_apply_verdicts_anchor_loss_is_fail_closed(tmp_path: Path) -> None:
    """某条的隐藏锚被误删 ⇒ 它的勾选**不得**记到上一条头上（M-1，r3）。

    旧实现取「最近一个锚」：第 2 条的锚被删 ⇒ 勾选归给第 1 条，第 1 条被写坏、
    problems 为空、rc=0（fail-open）。修后：标题与锚交叉核对，对不上就不归属。
    """
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes())
    before = src.read_bytes()

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()

    qs_before = _queries(src)
    ids = [q["id"] for q in qs_before]
    first, second = ids[0], ids[1]
    before_vals = {q["id"]: q.get("user_verdict") for q in qs_before}
    _w2, anchor2 = _pick_other_verdict(before_vals[second])
    # 模拟 Obsidian 源码模式误删第 2 条的隐藏锚（渲染态里看不见它）
    lines = [ln for ln in lines if f"<!-- gsid:{second} -->" not in ln]
    for i, line in enumerate(lines):
        if line.strip().startswith(f"**{second}**"):
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and anchor2 in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-19T00:00:00Z")
    assert changed == [], f"锚丢失的勾选不该落到任何条目，实得 changed={changed}"
    assert problems, "锚丢失必须有 problems（fail-closed）"
    assert any(second in p for p in problems), f"problems 应点名 {second}：{problems}"
    assert src.read_bytes() == before, "锚丢失时不得写任何字节"
    assert _queries(src)[0]["user_verdict"] == before_vals[first], f"{first} 不该被动"


def test_apply_verdicts_checkbox_edge_cases_fail_closed(tmp_path: Path) -> None:
    """大写 ``[X]`` 要认；认得勾但读不出 verdict 的必须报 problems（L-1，r3）。

    旧实现：``- [X]`` 大小写敏感漏认；勾选行 verdict 锚不匹配时 ``continue`` 静默跳过 ——
    数据面没被写坏，但**告警面 fail-silent**（rc=0，只剩计数能察觉）。
    """
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes())
    qs_before = _queries(src)
    ids = [q["id"] for q in qs_before]
    first, second = ids[0], ids[1]
    before_vals = {q["id"]: q.get("user_verdict") for q in qs_before}
    want1, anchor1 = _pick_other_verdict(before_vals[first])
    _w2, anchor2 = _pick_other_verdict(before_vals[second])

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if f"<!-- gsid:{first} -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and anchor1 in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [X]", 1)
                    break
        if f"<!-- gsid:{second} -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and anchor2 in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1).replace(f"<!-- {anchor2} -->", "")
                    break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-19T00:00:00Z")
    assert changed == [first], f"大写 [X] 应被识别且只改 {first}，实得 {changed}"
    after = {q["id"]: q for q in _queries(src)}
    assert after[first]["user_verdict"] == want1
    assert after[second]["user_verdict"] == before_vals[second], f"{second} 的勾选读不出 verdict，不该被写"
    assert any(second in p for p in problems), f"{second} 的坏勾选必须有 problems：{problems}"


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


def test_collect_refuses_out_inside_vault(tmp_path: Path) -> None:
    """``--out`` 落在 ``--vault`` 内必须拒绝（L-3，r3）：collect 不许有任何写进 vault 的路径。"""
    tool = _import_tool()
    vault = tmp_path / "fake-vault"
    (vault / "节点").mkdir(parents=True)
    (vault / "节点" / "a.md").write_text("# a\n\n> [!question]+ 提问？\n", encoding="utf-8")
    inside = vault / "candidates.json"

    with pytest.raises(ValueError, match="不得落在"):
        tool.collect_candidates(vault, inside)
    assert not inside.exists(), "被拒绝的 out 不该留下任何文件"

    rc = tool.main(["collect", "--vault", str(vault), "--out", str(inside)])
    assert rc == 2, f"CLI 走 --out 落在 vault 内应 rc=2，实得 {rc}"
    assert not inside.exists(), "CLI 路径也不该写进 vault"


# ═══════════════════════════════════════════════════════════════════════════
# ⑧ verify_gold_set_file 的 fail-closed 边界（r2 整改，zcode r1 H-1）
# ═══════════════════════════════════════════════════════════════════════════

#: 一份**典型**的合并冲突残骸（``<<<<<<<``）—— 生成文件进 git 后最常见的输入错形态。
_CONFLICT_MANIFEST = "<<<<<<< HEAD\nrevision: 2\n=======\nrevision: 1\n>>>>>>> batch-branch\n"


@pytest.mark.parametrize(
    ("case", "expect_in_detail"),
    [
        ("conflict", "解析失败"),
        ("notmap", "不是映射"),
        ("ghost", "缺失"),
        ("bad-sha", "sha256"),
        ("manifest-is-dir", "不可读"),
        ("files-scalar", "files 字段非法"),
        ("registered-is-dir", "不可读"),
        ("entry-non-dict", "条目非法"),
        ("query-count-missing", "query_count"),
        ("non-utf8", "不可读"),
        ("files-empty", "未登记任何文件"),
        ("path-invalid", "不是路径"),
    ],
)
def test_verify_gold_set_file_input_errors_fail_closed(case: str, expect_in_detail: str, tmp_path: Path) -> None:
    """环境/输入错一律 ``(False, 文案)``、**不得抛异常**。

    修复前 ①②③ 分别以 ``yaml.YAMLError`` / ``AttributeError`` / ``FileNotFoundError``
    逃逸 ⇒ 两个 runner 以未捕获异常收场（exit 1 =「指标回退」档），把 rc=2 的
    「环境/输入错」语义污染掉（r1 H-1；④ 是 r2 bonus 覆盖）。

    r3 扩 ⑤⑥⑦（OSError/UnicodeDecodeError 族 + ``files`` 非列表 —— r2 复核
    M-R2a/M-R2b），并**按 case 独立成条测试**：先红/后绿证据可以 per-case 各自
    成立（r2 的四 case 串在一个函数里，先红被 case① 遮蔽 —— L-R2b）。

    r4 再扩 ⑧⑨⑩（非映射条目 / 缺 ``query_count`` / 非 UTF-8 bytes —— r3 复核
    ② 的残余逃逸面）。
    """
    tool = _import_tool()

    if case == "conflict":  # ① manifest 带合并冲突标记 → YAMLError 不得逃逸
        mf = tmp_path / "conflict.yaml"
        mf.write_text(_CONFLICT_MANIFEST, encoding="utf-8")
        target = VAULT_GOLD
    elif case == "notmap":  # ② 顶层不是映射 → 不得崩在 .get
        mf = tmp_path / "notmap.yaml"
        mf.write_text("- just\n- a\n- list\n", encoding="utf-8")
        target = VAULT_GOLD
    elif case == "ghost":  # ③ 已登记但文件缺失 → 不得崩在 sha256_of
        ghost_rel = "backend/tests/regression/__g413_ghost__.yaml"
        assert not (BACKEND_ROOT.parent / ghost_rel).exists(), f"探针文件不该存在：{ghost_rel}"
        mf = tmp_path / "ghost-manifest.yaml"
        doc = _load(MANIFEST)
        doc["files"][0]["path"] = ghost_rel  # 借 manifest 真骨架，只改一条的 path
        mf.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
        target = BACKEND_ROOT.parent / ghost_rel
    elif case == "bad-sha":  # ④ 条目 sha256 非法 → 不得崩在比较/格式化
        mf = tmp_path / "bad-sha-manifest.yaml"
        doc = _load(MANIFEST)
        doc["files"][0]["sha256"] = None
        mf.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
        target = VAULT_GOLD
    elif case == "manifest-is-dir":  # ⑤ manifest 是目录 → OSError 族（M-R2a）
        mf = tmp_path / "manifest-dir"
        mf.mkdir()
        target = VAULT_GOLD
    elif case == "files-scalar":  # ⑥ files 是非列表标量 → TypeError 逃逸（M-R2b）
        mf = tmp_path / "files-scalar.yaml"
        mf.write_text("files: 5\n", encoding="utf-8")
        target = VAULT_GOLD
    elif case == "registered-is-dir":  # ⑦ 已登记“文件”是目录 → sha 读取 OSError 族（M-R2a）
        rel = "backend/tests/regression"
        mf = tmp_path / "registered-dir.yaml"
        mf.write_text(
            yaml.safe_dump(
                {"files": [{"path": rel, "sha256": "0" * 64, "query_count": 0}]}, allow_unicode=True, width=100
            ),
            encoding="utf-8",
        )
        target = BACKEND_ROOT.parent / rel
    elif case == "entry-non-dict":  # ⑧ files 里混入非映射条目 → 整 manifest 拒绝
        rel = str(VAULT_GOLD.relative_to(BACKEND_ROOT.parent))
        mf = tmp_path / "entry-non-dict.yaml"
        doc = _load(MANIFEST)
        doc["files"] = [e for e in doc["files"] if e["path"] == rel] + ["garbage"]
        mf.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
        target = VAULT_GOLD
    elif case == "query-count-missing":  # ⑨ 目标条目缺 query_count → fail-closed
        rel = str(VAULT_GOLD.relative_to(BACKEND_ROOT.parent))
        mf = tmp_path / "query-count-missing.yaml"
        doc = _load(MANIFEST)
        for e in doc["files"]:
            if e["path"] == rel:
                e.pop("query_count")
        mf.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
        target = VAULT_GOLD
    elif case == "non-utf8":  # ⑩ manifest 不是 UTF-8 → UnicodeDecodeError 族
        mf = tmp_path / "non-utf8.yaml"
        mf.write_bytes(b"\xff\xfe\x00\x01not-utf8")
        target = VAULT_GOLD
    elif case == "files-empty":  # ⑪ 空 registry → fail-closed（r4：旧版与 totals 全 0 时 rc=0）
        mf = tmp_path / "files-empty.yaml"
        mf.write_text("files: []\n", encoding="utf-8")
        target = VAULT_GOLD
    elif case == "path-invalid":  # ⑫ 入参不是路径 → TypeError 不得逃逸（r4）
        mf = MANIFEST
        target = 5
    else:
        raise AssertionError(f"未知 case: {case}")

    ok, detail = tool.verify_gold_set_file(target, manifest_path=mf)
    assert ok is False, f"[{case}] 未 fail-closed：{(ok, detail)!r}"
    assert expect_in_detail in detail, f"[{case}] 文案缺「{expect_in_detail}」：{detail!r}"


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
    calls = _pin_env_after_verify(monkeypatch, runner, runner_file)

    conflict = tmp_path / "conflict.yaml"
    conflict.write_text(_CONFLICT_MANIFEST, encoding="utf-8")
    monkeypatch.setattr(tool, "MANIFEST_PATH", conflict)

    monkeypatch.setattr(sys, "argv", [runner_file, *argv])
    rc = runner.main()  # 修复前：这里抛 yaml.YAMLError（测试红）
    out = capsys.readouterr()
    combined = out.out + out.err
    assert rc == 2, f"{runner_file} 对解析错 manifest 应 rc=2，实得 {rc}\n{combined}"
    assert "不符" in combined and "解析失败" in combined, f"{runner_file} 的文案没有「不符 (解析失败…)」：\n{combined}"
    assert calls == [], f"{runner_file}: 校验失败时不该先碰环境检查（M-3）—— 实际调用：{calls}"


def test_memory_runner_verify_passes_then_alive_gate(monkeypatch, capsys) -> None:
    """对照输入（M-3）：干净 manifest + alive 钉 False ⇒ 两种 rc=2 的文案可区分。

    钉住 ``alive=False`` 后：还看到「不符」= 校验假红；看不到「backend 不可达」=
    pin 是死补丁。两者都满足 ⇒ 顺序与文案都可自动核查（不必等离线机器）。
    """
    _import_tool()  # ⚠️ 先于 runner：共用同一模块实例
    runner = _import_runner("run_memory_retrieval_regression.py")
    calls = _pin_env_after_verify(monkeypatch, runner, "run_memory_retrieval_regression.py")
    monkeypatch.setattr(sys, "argv", ["run_memory_retrieval_regression.py", "--shadow", "--no-judge"])

    rc = runner.main()
    out = capsys.readouterr()
    combined = out.out + out.err
    assert rc == 2, f"alive 钉 False 后应 rc=2，实得 {rc}\n{combined}"
    assert "backend 不可达" in combined, f"缺少「backend 不可达」——pin 可能没生效：\n{combined}"
    assert "不符" not in combined, f"干净 manifest 不该出现「不符」：\n{combined}"
    assert calls == ["alive"], f"pin 没生效（alive 没被调用）—— 对照不成立：{calls}"


def test_apply_verdicts_preserves_crlf_bytes(tmp_path: Path) -> None:
    """CRLF 金集：回写只许动目标三行，行尾不得被整文重写成 LF（r4）。

    r3 版 `read_text`/`write_text` 会做 universal-newline 归一化 ⇒ 整文件行尾被重写，
    而 roundtrip 的 `splitlines()` 对账看不见（r3 复核 MEDIUM）。
    """
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes().replace(b"\n", b"\r\n"))
    before = src.read_bytes().split(b"\r\n")

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    qs_before = _queries(src)
    target = qs_before[0]["id"]
    _want, anchor = _pick_other_verdict(qs_before[0].get("user_verdict"))
    lines = _mark(lines, target, anchor)
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert problems == [], f"CRLF 回写报了问题：{problems}"
    assert changed == [target], f"应只改 {target}，实得 {changed}"

    after = src.read_bytes()
    assert b"\r\n" in after, "行尾被整文重写成 LF 了（M-2 回归：字节级读写被破坏）"
    after_lines = after.split(b"\r\n")
    assert len(after_lines) == len(before), "回写不该增删行"
    diff = [i for i, (a, b) in enumerate(zip(before, after_lines)) if a != b]
    assert len(diff) == 3, f"CRLF 下应恰 3 行变化，实测 {len(diff)}"


def test_apply_verdicts_fake_id_lines_do_not_hijack_spans(tmp_path: Path) -> None:
    """block scalar 里的假 ``- id:`` 不夺权：写入必须落在**真条目**的三个标注行（r6）。

    r4 用「值序列对账」会整文件拒绝；r6 用 PyYAML 节点树行号定位 ⇒ 假行根本不参与
    （它不是任何映射键），真条目被正确更新，且假行所在的 query 正文一个字节不变。
    """
    tool = _import_tool()
    src = tmp_path / "mini.yaml"
    src.write_bytes(
        b"queries:\n"
        b"  - id: q1\n"
        b"    query: |\n"
        b"      - id: q1\n"
        b"      body-text\n"
        b"    user_verdict: pending\n"
        b"    verdict_by: null\n"
        b"    verdict_at: null\n"
    )
    before_lines = src.read_bytes().split(b"\n")

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if "<!-- gsid:q1 -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and "verdict:relevant" in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert problems == [], f"不该有 problems：{problems}"
    assert changed == ["q1"], f"应只改 q1，实得 {changed}"
    after = {q["id"]: q for q in _queries(src)}
    assert after["q1"]["user_verdict"] == "relevant"
    after_lines = src.read_bytes().split(b"\n")
    diff = [i for i, (a, b) in enumerate(zip(before_lines, after_lines)) if a != b]
    assert len(diff) == 3, f"应恰 3 行变化，实测 {len(diff)}"
    assert b"      - id: q1" in src.read_bytes(), "block scalar 正文（假行所在）被改动了"


def test_apply_verdicts_rejects_duplicate_id_blocks(tmp_path: Path) -> None:
    """同一 id 两个块 ⇒ 该条不动（r3 复核 MEDIUM：旧版 dict last-wins 只改最后一块）。"""
    tool = _import_tool()
    src = tmp_path / "dup.yaml"
    block = b'  - id: q1\n    query: "ask"\n    user_verdict: pending\n    verdict_by: null\n    verdict_at: null\n'
    src.write_bytes(b"queries:\n" + block + block)
    before = src.read_bytes()

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if "<!-- gsid:q1 -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and "verdict:relevant" in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert changed == [], f"重复 id 应拒绝该条，实得 changed={changed}"
    assert any("出现 2 次" in p for p in problems), f"应报「出现 2 次」：{problems}"
    assert src.read_bytes() == before, "拒绝时不得写任何字节"


def test_apply_verdicts_rejects_multiline_scalar(tmp_path: Path) -> None:
    """``verdict_by`` 里塞真换行 ⇒ 该条不动（r4：r3 守卫误查字面反斜杠-n 两字符）。"""
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes())
    before = src.read_bytes()

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    target = _queries(src)[0]["id"]
    for i, line in enumerate(lines):
        if f"<!-- gsid:{target} -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and "verdict:relevant" in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="a\nb", verdict_at="2026-09-20T00:00:00Z")
    assert changed == [], f"多行标量应拒绝该条，实得 changed={changed}"
    assert any("多行" in p for p in problems), f"应报「多行」：{problems}"
    assert src.read_bytes() == before, "拒绝时不得写任何字节"


def test_apply_verdicts_block_boundaries_and_embedded_anchors(tmp_path: Path) -> None:
    """r4 收紧：内嵌锚不夺权；``---`` / ``##`` 之后的勾选不归最后一条。"""
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes())
    qs_before = _queries(src)
    ids = [q["id"] for q in qs_before]
    first, last = ids[0], ids[-1]
    before_vals = {q["id"]: q.get("user_verdict") for q in qs_before}
    want, anchor = _pick_other_verdict(before_vals[first])

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(f"**{first}**"):
            lines[i] = line + " <!-- gsid:someone-else -->"  # 内嵌锚：不夺权
        if f"<!-- gsid:{first} -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and anchor in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
    # 补审段（--- 与 ## 之后）里放一个「勾」→ 不得归属最后一条
    lines += ["", "---", "", "## 补审（示例）", "", "- [x] 相关 —— 尾部署名用  <!-- verdict:irrelevant -->", ""]
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert changed == [first], f"只该写 {first}（内嵌锚不夺权），实得 {changed}"
    assert any("不在任何条目标题之下" in p for p in problems), f"尾部署名勾选应报 problems：{problems}"
    after = {q["id"]: q for q in _queries(src)}
    assert after[first]["user_verdict"] == want
    assert after[last]["user_verdict"] == before_vals[last], f"{last} 不该被尾部勾选波及"


@pytest.mark.parametrize(
    "case",
    [
        "entry-non-dict",
        "registered-top-list",
        "queries-not-list",
        "config-not-map",
        "files-empty",
        "queries-entry-non-mapping",
    ],
)
def test_verify_all_env_errors_are_rc2(case: str, tmp_path: Path, monkeypatch) -> None:
    """``verify_all`` 的 r4 形状守卫：坏清单 / 坏登记文档一律 rc=2（不得崩、不得 rc=0）。

    r3 复核 ②：登记文档解析成 list、``queries: 5``、``config: 5`` 时旧版会在
    ``doc.get`` / ``len(qs)`` / ``cfg.get`` 上崩 —— 崩不是 rc=2。
    """
    tool = _import_tool()
    root = tmp_path / "root"
    reg = root / "backend" / "tests" / "regression"
    reg.mkdir(parents=True)
    good = reg / "ok.yaml"
    good.write_text("config:\n  version: 1\nqueries: []\n", encoding="utf-8")
    rel = "backend/tests/regression/ok.yaml"

    if case == "registered-top-list":
        good.write_text("- a\n- b\n", encoding="utf-8")
    elif case == "queries-not-list":
        good.write_text("config:\n  version: 1\nqueries: 5\n", encoding="utf-8")
    elif case == "config-not-map":
        good.write_text("config: 5\nqueries: []\n", encoding="utf-8")

    manifest = {
        "files": [{"path": rel, "sha256": _sha256(good), "query_count": 0, "config_version": 1}],
        "totals": {"main_set_queries": 0, "cross_vault_attack": 0, "all_registered_queries": 0},
        "adjudication": {"status": "pending", "signed_by": None, "signed_at": None},
    }
    if case == "entry-non-dict":
        manifest["files"].append("garbage")
    elif case == "files-empty":
        manifest["files"] = []
    elif case == "queries-entry-non-mapping":
        good.write_text("config:\n  version: 1\nqueries:\n  - not-a-map\n", encoding="utf-8")
        manifest["files"][0]["sha256"] = _sha256(good)
    mf = tmp_path / "manifest.yaml"
    mf.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")

    monkeypatch.setattr(tool, "REPO_ROOT", root)
    monkeypatch.setattr(tool, "MAIN_SETS", ())
    rc, lines = tool.verify_all(mf)
    assert rc == 2, f"[{case}] 应 rc=2（环境/输入错），实得 {rc}：{lines}"
    assert rc != 0, f"[{case}] 不得 rc=0：{lines}"


def test_apply_verdicts_structural_alignment_blocks_hidden_fake_item(tmp_path: Path) -> None:
    """r4 复核 H-1 残余：只比「值序列」会被「隐藏真条目 + 丢弃区块内假行」骗过（r5 修）。

    构造（r4 复核给的受害形态）：真 q2 的 id 行写成 ``- "id": q2``、三标注字段写成
    引号键形态（文本层正则看不见）且**已等于本次目标值**；q2 自己的 ``query: |``
    块里放一条假 ``- id: q2`` + 三标注行，再用第二个 ``query:`` 键把它覆盖掉
    （解析层丢弃该块）。于是：候选序列 == 解析序列（值对账通过）、假行段落里字段
    恰一份、预检/全文档不变量也一致 ⇒ 写入落进被丢弃的 block scalar 正文。
    修后每个候选段落必须**单独按条目解析**并与整文档同序条目**逐键相同**，否则拒绝。
    """
    tool = _import_tool()
    src = tmp_path / "crafted.yaml"
    src.write_bytes(
        b"queries:\n"
        b"  - id: q1\n"
        b"    query: q1-body\n"
        b"    user_verdict: pending\n"
        b"    verdict_by: null\n"
        b"    verdict_at: null\n"
        b'  - "id": q2\n'
        b"    query: |\n"
        b"      - id: q2\n"
        b"      user_verdict: relevant\n"
        b"      verdict_by: user\n"
        b"      verdict_at: '2026-09-20T00:00:00Z'\n"
        b"    query: q2-body\n"
        b'    "user_verdict": irrelevant\n'
        b'    "verdict_by": user\n'
        b"    \"verdict_at\": '2026-09-20T00:00:00Z'\n"
    )
    before = src.read_bytes()

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if "<!-- gsid:q2 -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and "verdict:irrelevant" in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert changed == [], f"结构对账必须拒绝，实得 changed={changed}"
    assert problems, "必须报 problems（fail-closed）"
    assert src.read_bytes() == before, "拒绝时不得写任何字节（不得改写 block scalar 正文）"


def test_apply_verdicts_preserves_missing_trailing_newline(tmp_path: Path) -> None:
    """无尾换行的金集：回写不得给它补 ``\\n``，且只动目标三行（r4 复核 LOW③）。"""
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes().rstrip(b"\n"))
    before = src.read_bytes()
    assert not before.endswith(b"\n")

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    qs_before = _queries(src)
    target = qs_before[0]["id"]
    _want, anchor = _pick_other_verdict(qs_before[0].get("user_verdict"))
    lines = _mark(lines, target, anchor)
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert problems == [] and changed == [target]
    after = src.read_bytes()
    assert not after.endswith(b"\n"), "不得给无尾换行的文件补尾换行"
    before_lines, after_lines = before.split(b"\n"), after.split(b"\n")
    assert len(before_lines) == len(after_lines)
    diff = [i for i, (a, b) in enumerate(zip(before_lines, after_lines)) if a != b]
    assert len(diff) == 3, f"应恰 3 行变化，实测 {len(diff)}"


@pytest.mark.parametrize(
    ("case", "body", "fragment", "class_key"),
    [
        ("queries-non-mapping-entry", "config:\n  version: 1\nqueries:\n  - not-a-map\n", "queries", "query_type"),
        (
            "item-missing-query",
            "config:\n  version: 1\nqueries:\n  - id: q1\n",
            "缺 id 或 query",
            "query_type",
        ),
        ("config-missing", "queries:\n  - id: q1\n    query: body\n", "config", "query_type"),
        (
            "no-expectation-key",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n",
            "期望键",
            "query_type",
        ),
        (
            "config-numeric-type",
            'config:\n  version: 1\n  tolerance: "loose"\nqueries:\n  - id: q1\n    query: body\n'
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "tolerance",
            "query_type",
        ),
        (
            "memory-expect-any-missing",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n",
            "expect_any",
            "category",
        ),
        (
            "non-finite-number",
            "config:\n  version: 1\n  tolerance: .nan\nqueries:\n  - id: q1\n    query: body\n"
            "    expect_not_hit:\n      - path_glob: x\n        max_in_top_k: 0\n",
            "tolerance",
            "query_type",
        ),
        (
            "expect-any-non-str",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_any:\n      - 1\n",
            "expect_any",
            "category",
        ),
        (
            "explicit-null-numeric",
            "config:\n  version: 1\n  tolerance:\nqueries:\n  - id: q1\n    query: body\n"
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "tolerance",
            "query_type",
        ),
        (
            "explicit-null-not-hit",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n"
            "    expect_hit:\n      - file: f\n        grade: 1\n    expect_not_hit:\n",
            "expect_not_hit",
            "query_type",
        ),
        (
            "non-json-scalar",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    origin: 2020-01-01\n"
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "JSON",
            "query_type",
        ),
        (
            "empty-query-string",
            'config:\n  version: 1\nqueries:\n  - id: q1\n    query: ""\n'
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "空白串",
            "query_type",
        ),
        (
            "negative-max-in-top-k",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_hit: []\n"
            "    expect_not_hit:\n      - path_glob: x\n        max_in_top_k: -1\n",
            "expect_not_hit",
            "query_type",
        ),
        (
            "range-tolerance",
            "config:\n  version: 1\n  tolerance: 5\nqueries:\n  - id: q1\n    query: body\n"
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "tolerance",
            "query_type",
        ),
        (
            "expect-empty-with-expect-hit",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_empty: true\n"
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "自相矛盾",
            "query_type",
        ),
        (
            "delivery-hard-cap-type",
            'config:\n  version: 1\n  delivery:\n    hard_cap: "x"\nqueries:\n  - id: q1\n'
            "    query: body\n    expect_hit:\n      - file: f\n        grade: 1\n",
            "hard_cap",
            "query_type",
        ),
        (
            "huge-int-tolerance",
            "config:\n  version: 1\n  tolerance: " + "9" * 400 + "\nqueries:\n  - id: q1\n    query: body\n"
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "tolerance",
            "query_type",
        ),
        (
            "delivery-hard-cap-null",
            "config:\n  version: 1\n  delivery:\n    hard_cap:\nqueries:\n  - id: q1\n    query: body\n"
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "hard_cap",
            "query_type",
        ),
        (
            "empty-expect-any-string",
            'config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_any:\n      - ""\n',
            "expect_any",
            "category",
        ),
        (
            "empty-leak-markers",
            "config:\n  version: 1\n  leak_markers: []\nqueries:\n  - id: q1\n    query: body\n"
            "    expect_any:\n      - x\n",
            "leak_markers",
            "category",
        ),
        (
            "expect-hit-empty-file",
            'config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_hit:\n      - file: ""\n'
            "        grade: 1\n",
            "expect_hit",
            "query_type",
        ),
        (
            "expect-hit-grade-type",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_hit:\n      - file: f\n"
            "        grade:\n",
            "grade",
            "query_type",
        ),
        (
            "forbidden-path-globs-str",
            'config:\n  version: 1\n  forbidden:\n    path_globs: "qqq"\nqueries:\n  - id: q1\n'
            "    query: body\n    expect_hit:\n      - file: f\n        grade: 1\n",
            "path_globs",
            "query_type",
        ),
        (
            "contamination-doc-types-empty",
            "config:\n  version: 1\n  contamination:\n    doc_types: []\nqueries:\n  - id: q1\n"
            "    query: body\n    expect_hit:\n      - file: f\n        grade: 1\n",
            "doc_types",
            "query_type",
        ),
        (
            "int-bound-top-k",
            "config:\n  version: 1\n  top_k: " + "9" * 400 + "\nqueries:\n  - id: q1\n    query: body\n"
            "    expect_hit:\n      - file: f\n        grade: 1\n",
            "top_k",
            "query_type",
        ),
        (
            "whitespace-forbidden-marker",
            'config:\n  version: 1\n  forbidden:\n    markers: [" "]\nqueries:\n  - id: q1\n'
            "    query: body\n    expect_hit:\n      - file: f\n        grade: 1\n",
            "markers",
            "query_type",
        ),
        (
            "whitespace-expect-any",
            'config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_any:\n      - " "\n',
            "expect_any",
            "category",
        ),
        (
            "huge-max-in-top-k",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_hit:\n      - file: f\n"
            "        grade: 1\n    expect_not_hit:\n      - path_glob: x\n        max_in_top_k: " + "9" * 400 + "\n",
            "expect_not_hit",
            "query_type",
        ),
        (
            "grade-over-ten",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_hit:\n      - file: f\n"
            "        grade: 2000\n",
            "expect_hit",
            "query_type",
        ),
        (
            "contains-empty",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_hit:\n      - file: f\n"
            '        contains: ""\n        grade: 1\n',
            "expect_hit",
            "query_type",
        ),
        (
            "contains-zero",
            "config:\n  version: 1\nqueries:\n  - id: q1\n    query: body\n    expect_hit:\n      - file: f\n"
            "        contains: 0\n        grade: 1\n",
            "contains",
            "query_type",
        ),
    ],
)
def test_verify_gold_set_file_content_shape_fail_closed(
    case: str, body: str, fragment: str, class_key: str, tmp_path: Path, monkeypatch
) -> None:
    """r4 复核 ② / r5 复核 ①：金集「映射但不可跑」的形状 ⇒ (False, 文案)。

    修前 `verify_gold_set_file` 只核 sha/query_count ⇒ 返回 True，两个 runner 随后在
    ``q["query"]`` / ``gold["config"]`` 上 KeyError/AttributeError → exit 1。
    """
    tool = _import_tool()
    root = tmp_path / "root"
    reg = root / "backend" / "tests" / "regression"
    reg.mkdir(parents=True)
    bad = reg / "bad.yaml"
    bad.write_text(body, encoding="utf-8")
    n_q = len(_load(bad).get("queries") or [])
    rel = "backend/tests/regression/bad.yaml"
    mf = tmp_path / "manifest.yaml"
    mf.write_text(
        yaml.safe_dump(
            {"files": [{"path": rel, "sha256": _sha256(bad), "query_count": n_q, "class_key": class_key}]},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(tool, "REPO_ROOT", root)
    ok, detail = tool.verify_gold_set_file(bad, manifest_path=mf)
    assert ok is False, f"[{case}] 内容形状坏必须 fail-closed：{(ok, detail)!r}"
    assert fragment in detail, f"[{case}] 文案应点名「{fragment}」：{detail!r}"


def test_apply_verdicts_decoy_scalars_do_not_hijack_writes(tmp_path: Path) -> None:
    """r5 复核 H 的受害构造：被覆盖的同级 scalar 里的「完整伪条目」不得被当成写入目标。

    真条目的 id 行与三标注键全部写成引号形态（旧文本层正则看不见）；文件尾 ``dead: |``
    块 scalar 里放与真条目**逐键相同**的伪条目（值用格式变体如 ``user_verdict:  "irrelevant"``，
    解析层相同、字节不同），随后 ``dead: placeholder`` 覆盖整块。r5 的对账会全绿并把写入
    落进死区（`r6-decoy-red-on-r5-*.txt` 用 r5 源码实跑证明）；r6 起定位只看解析出的键
    ⇒ 真条目三行是引号形态 ⇒ **整条拒绝**，零字节写。
    """
    tool = _import_tool()
    src = tmp_path / "decoy.yaml"
    src.write_bytes(
        b"queries:\n"
        b'  - "id": q1\n'
        b"    query: q1-body\n"
        b'    "user_verdict": pending\n'
        b'    "verdict_by": null\n'
        b'    "verdict_at": null\n'
        b'  - "id": q2\n'
        b"    query: q2-body\n"
        b'    "user_verdict": irrelevant\n'
        b'    "verdict_by": user\n'
        b"    \"verdict_at\": '2026-09-20T00:00:00Z'\n"
        b"dead: |\n"
        b"  - id: q1\n"
        b"    query: q1-body\n"
        b"    user_verdict: pending\n"
        b"    verdict_by: null\n"
        b"    verdict_at: null\n"
        b"  - id: q2\n"
        b"    query: q2-body\n"
        b'    user_verdict:  "irrelevant"\n'
        b"    verdict_by: user\n"
        b"    verdict_at: '2026-09-20T00:00:00Z'\n"
        b"dead: placeholder\n"
    )
    before = src.read_bytes()

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if "<!-- gsid:q2 -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and "verdict:irrelevant" in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert changed == [], f"引号形态的真条目必须被拒绝，实得 changed={changed}"
    assert any("规范形态" in p for p in problems), f"应报「规范形态」problem：{problems}"
    assert src.read_bytes() == before, "拒绝时不得写任何字节（尤其不得改写死区）"


def test_apply_verdicts_precheck_blocks_corrupt_write(tmp_path: Path, monkeypatch) -> None:
    """预检分支有钉子：渲染出的值读回不等于目标 ⇒ 该条放弃、零写（r5 复核 ③ MEDIUM）。"""
    tool = _import_tool()
    src = tmp_path / "vault_gold_set.yaml"
    src.write_bytes(VAULT_GOLD.read_bytes())
    before = src.read_bytes()

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    target = _queries(src)[0]["id"]
    for i, line in enumerate(lines):
        if f"<!-- gsid:{target} -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and "verdict:relevant" in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    monkeypatch.setattr(tool, "_yaml_scalar", lambda value: "something-else")
    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert changed == [], f"预检失败必须零写，实得 changed={changed}"
    assert any("预检" in p for p in problems), f"应有预检 problem：{problems}"
    assert src.read_bytes() == before, "预检失败不得写任何字节"


def test_apply_verdicts_rejects_duplicate_annotation_key_lines(tmp_path: Path) -> None:
    """同一标注键在一个条目里出现两次（规范形态）⇒ 该条不动（节点树 found=2，r6）。"""
    tool = _import_tool()
    src = tmp_path / "dup-key.yaml"
    src.write_bytes(
        b"queries:\n"
        b"  - id: q1\n"
        b"    query: q1-body\n"
        b"    expect_any:\n"
        b"      - x\n"
        b"    user_verdict: pending\n"
        b"    user_verdict: pending\n"
        b"    verdict_by: null\n"
        b"    verdict_at: null\n"
    )
    before = src.read_bytes()

    md = tmp_path / "checklist.md"
    tool.write_checklist([src], md)
    lines = md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if "<!-- gsid:q1 -->" in line:
            for j in range(i, min(i + 8, len(lines))):
                if lines[j].lstrip().startswith("- [ ]") and "verdict:relevant" in lines[j]:
                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
                    break
            break
    md.write_text("\n".join(lines), encoding="utf-8")

    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-20T00:00:00Z")
    assert changed == [], f"重复标注键必须拒绝该条，实得 changed={changed}"
    assert any("缺失/重复" in p for p in problems), f"应报缺失/重复：{problems}"
    assert src.read_bytes() == before, "拒绝时不得写任何字节"


def test_vault_runner_maps_unexpected_exception_to_rc2(monkeypatch, capsys) -> None:
    """r8/r9/r10 复核反复点名：``_main`` 的未预期异常必须兜成 rc=2（r11）。

    未捕获异常会被 shell 记成 exit 1 —— 冒充「指标回退」档。兜底在最外层 main()。
    """
    _import_tool()
    runner = _import_runner("run_vault_retrieval_regression.py")
    monkeypatch.setattr(sys, "argv", ["run_vault_retrieval_regression.py", "--shadow", "--no-hook"])

    async def _fake_tiers(gold):
        return {"per_query": [{"returned": 1}], "metrics": {}, "hard_violations": [], "run_at": "x"}

    def _boom(*args, **kwargs):
        raise RuntimeError("sentinel-unexpected")

    monkeypatch.setattr(runner, "run_tiers", _fake_tiers)
    monkeypatch.setattr(runner, "print_report", _boom)
    rc = runner.main()
    out = capsys.readouterr()
    assert rc == 2, f"未预期异常应兜成 rc=2，实得 {rc}"
    assert "未预期异常" in (out.out + out.err), "兜底文案缺失"


def test_memory_runner_maps_unexpected_exception_to_rc2(monkeypatch, capsys) -> None:
    """同 vault 侧：memory runner 的未预期异常也兜成 rc=2（r11）。"""
    _import_tool()
    runner = _import_runner("run_memory_retrieval_regression.py")
    monkeypatch.setattr(runner, "check_backend_alive", lambda: True)
    monkeypatch.setattr(sys, "argv", ["run_memory_retrieval_regression.py", "--no-judge"])

    def _boom(*args, **kwargs):
        raise RuntimeError("sentinel-unexpected")

    monkeypatch.setattr(runner, "run_queries", _boom)
    rc = runner.main()
    out = capsys.readouterr()
    assert rc == 2, f"未预期异常应兜成 rc=2，实得 {rc}"
    assert "未预期异常" in (out.out + out.err), "兜底文案缺失"


def test_grade_ok_accepts_int_like_rejects_bool() -> None:
    """``_grade_ok``：0..10 的 int / 整值 float / ``int()`` 可解析数字串接受；bool 与越界拒绝。"""
    tool = _import_tool()
    assert tool._grade_ok(3) and tool._grade_ok(0)
    assert tool._grade_ok(2.0) and tool._grade_ok("2")
    # 与 runner 的 int() 接受面一致（含全角数字 / 正号 / 两侧空白）
    assert tool._grade_ok("２") and tool._grade_ok("+5") and tool._grade_ok(" 5 ")
    assert not tool._grade_ok(True) and not tool._grade_ok(-1)
    assert not tool._grade_ok(2.5) and not tool._grade_ok(None) and not tool._grade_ok("x")
    assert not tool._grade_ok(11) and not tool._grade_ok("11")


def test_verify_gold_set_file_accepts_runner_valid_shapes(tmp_path: Path, monkeypatch) -> None:
    """正向对照：runner 真能跑的「非最规范」形状不得误拒（r13 复核 LOW-2 的反面）。

    * ``expect_not_hit`` 条目**缺** ``max_in_top_k``（runner 默认 0）；
    * ``contains`` 是数字（vault runner 走 ``str()``）；
    * ``group_id: null``（= 服务端默认）与省略 ``language``。
    """
    tool = _import_tool()
    root = tmp_path / "root"
    reg = root / "backend" / "tests" / "regression"
    reg.mkdir(parents=True)
    good = reg / "ok.yaml"
    good.write_text(
        "config:\n  version: 1\n  group_id: null\n"
        "queries:\n"
        "  - id: q1\n"
        "    query: body\n"
        "    expect_hit:\n"
        "      - file: f\n"
        "        contains: 5\n"
        "        grade: 1\n"
        "    expect_not_hit:\n"
        "      - path_glob: x\n",
        encoding="utf-8",
    )
    rel = "backend/tests/regression/ok.yaml"
    mf = tmp_path / "manifest.yaml"
    mf.write_text(
        yaml.safe_dump(
            {"files": [{"path": rel, "sha256": _sha256(good), "query_count": 1, "class_key": "query_type"}]},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(tool, "REPO_ROOT", root)
    ok, detail = tool.verify_gold_set_file(good, manifest_path=mf)
    assert ok is True, f"runner 可跑的形状被误拒：{detail!r}"


def test_runner_wrapper_does_not_swallow_keyboard_interrupt(monkeypatch) -> None:
    """rc 兜底只收 ``Exception``：``KeyboardInterrupt`` 必须透传（r12/LOW-3）。"""
    _import_tool()
    runner = _import_runner("run_vault_retrieval_regression.py")
    monkeypatch.setattr(sys, "argv", ["run_vault_retrieval_regression.py", "--shadow", "--no-hook"])

    async def _fake_tiers(gold):
        return {"per_query": [{"returned": 1}], "metrics": {}, "hard_violations": [], "run_at": "x"}

    def _interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(runner, "run_tiers", _fake_tiers)
    monkeypatch.setattr(runner, "print_report", _interrupt)
    with pytest.raises(KeyboardInterrupt):
        runner.main()


def _approve_fixture(
    tmp_path: Path, tool, main_verdict: str = "relevant", shadow: str | None = None
) -> tuple[Path, Path, dict]:
    """建 approve 用的 tmp 根：main 主集 1 条 + 可选 shadow（``"pending"``/``"relevant"``）。

    返回 ``(root, manifest_path)``，并已把 tool 的 REPO_ROOT/GOLD_SETS/MAIN_SETS 指到 tmp。
    """
    root = tmp_path / "root"
    reg = root / "backend" / "tests" / "regression"
    reg.mkdir(parents=True)

    def _write(path: Path, verdict: str, with_query: bool) -> None:
        qs = (
            "queries:\n"
            "  - id: q1\n"
            "    query: body\n"
            f"    user_verdict: {verdict}\n"
            "    verdict_by: user\n"
            "    verdict_at: '2026-09-20T00:00:00Z'\n"
            "    source: {kind: synthetic, ref: null}\n"
            "    expect_hit:\n"
            "      - {file: f, grade: 1}\n"
        )
        path.write_text("config:\n  version: 1\n" + (qs if with_query else "queries: []\n"), encoding="utf-8")

    main = reg / "v_main.yaml"
    _write(main, main_verdict, True)
    golds = [(main, "query_type")]
    files = [
        {
            "path": "backend/tests/regression/v_main.yaml",
            "sha256": _sha256(main),
            "query_count": 1,
            "config_version": 1,
            "class_key": "query_type",
        }
    ]
    if shadow is not None:
        sh = reg / "v_shadow.yaml"
        _write(sh, shadow, True)
        golds.append((sh, "query_type"))
        files.append(
            {
                "path": "backend/tests/regression/v_shadow.yaml",
                "sha256": _sha256(sh),
                "query_count": 1,
                "config_version": 1,
                "class_key": "query_type",
            }
        )
    mf = reg / "gold_set_manifest.yaml"
    mf.write_text(
        tool.MANIFEST_HEADER
        + yaml.safe_dump(
            {
                "revision": 1,
                "frozen": True,
                "files": files,
                "totals": {
                    "main_set_queries": 1,
                    "cross_vault_attack": 0,
                    "all_registered_queries": 1 + (1 if shadow is not None else 0),
                },
                "adjudication": {"status": "pending", "signed_by": None, "signed_at": None, "checklist_path": None},
            },
            allow_unicode=True,
            sort_keys=False,
            width=100,
        ),
        encoding="utf-8",
    )
    monkeypatch_free = {
        "REPO_ROOT": root,
        "GOLD_SETS": tuple(golds),
        "MAIN_SETS": (main,),
    }
    return root, mf, monkeypatch_free


def test_approve_refuses_while_main_pending(tmp_path: Path, monkeypatch) -> None:
    """主集还有 pending 不许签字；**真 manifest 不参与**（tmp 隔离，r17 复核 H-1 整改）。"""
    tool = _import_tool()
    root, mf, patch = _approve_fixture(tmp_path, tool, main_verdict="pending")
    for k, v in patch.items():
        monkeypatch.setattr(tool, k, v)
    before = mf.read_bytes()
    rc = tool.approve_manifest(mf, "someone")
    assert rc != 0, "主集 pending 未清时 approve 必须拒绝"
    assert mf.read_bytes() == before, "被拒绝的 approve 不得改动 manifest"


def test_approve_allows_shadow_pending_but_keeps_it_pending(tmp_path: Path, monkeypatch) -> None:
    """shadow 的 pending **不在用户 session 面内**，不拦签字，且签字后它仍是 pending（r17 复核 H-2）。"""
    tool = _import_tool()
    root, mf, patch = _approve_fixture(tmp_path, tool, main_verdict="relevant", shadow="pending")
    for k, v in patch.items():
        monkeypatch.setattr(tool, k, v)
    rc = tool.approve_manifest(mf, "user", signed_at="2026-09-20T12:00:00Z")
    assert rc == 0, f"shadow pending 不该拦签字，实得 rc={rc}"
    man = tool.load_yaml(mf)
    assert man["adjudication"]["status"] == "approved"
    shadow_qs = tool.queries_of(root / "backend" / "tests" / "regression" / "v_shadow.yaml")
    assert shadow_qs[0]["user_verdict"] == "pending", "shadow 的 verdict 不该被签字动作改动"


def test_approve_rejects_empty_signed_by_on_clean_fixture(tmp_path: Path, monkeypatch) -> None:
    """干净副本上：空/纯空白签名必须拒（可判别 —— 无 pending 分支兜底，r17 复核 L-3②）。"""
    tool = _import_tool()
    root, mf, patch = _approve_fixture(tmp_path, tool)
    for k, v in patch.items():
        monkeypatch.setattr(tool, k, v)
    before = mf.read_bytes()
    assert tool.approve_manifest(mf, "   ") != 0
    assert tool.approve_manifest(mf, "") != 0
    assert mf.read_bytes() == before
    assert tool.load_yaml(mf)["adjudication"]["status"] == "pending"


def test_approve_sets_signature_and_verify_stays_green(tmp_path: Path, monkeypatch) -> None:
    """干净副本上 approve：置 approved + 签字，且 verify 仍 rc=0（原子替换 + 先验后换）。"""
    tool = _import_tool()
    root, mf, patch = _approve_fixture(tmp_path, tool)
    for k, v in patch.items():
        monkeypatch.setattr(tool, k, v)
    rc = tool.approve_manifest(mf, "user", signed_at="2026-09-20T12:00:00Z")
    assert rc == 0, f"干净副本应允许签字，实得 rc={rc}"
    man = tool.load_yaml(mf)
    assert man["adjudication"]["status"] == "approved"
    assert man["adjudication"]["signed_by"] == "user"
    assert man["adjudication"]["signed_at"] == "2026-09-20T12:00:00Z"
    rc2, lines2 = tool.verify_all(mf)
    assert rc2 == 0, f"签字后 verify 应 rc=0：{lines2}"


def test_approve_refuses_double_sign(tmp_path: Path, monkeypatch) -> None:
    """已 approved 后再签必须拒（不许静默覆写签名/回溯时间，r17 复核 M-3）。"""
    tool = _import_tool()
    root, mf, patch = _approve_fixture(tmp_path, tool)
    for k, v in patch.items():
        monkeypatch.setattr(tool, k, v)
    assert tool.approve_manifest(mf, "user", signed_at="2026-09-20T12:00:00Z") == 0
    signed = mf.read_bytes()
    assert tool.approve_manifest(mf, "impostor", signed_at="1999-01-01T00:00:00Z") != 0
    assert mf.read_bytes() == signed, "重复签署不得改动 manifest"
    assert tool.load_yaml(mf)["adjudication"]["signed_by"] == "user"


def test_approve_refuses_when_registry_shrinks(tmp_path: Path, monkeypatch) -> None:
    """manifest 登记路径 ≠ 四份金集（registry 缩水）⇒ 拒签（r17 复核 M-1）。

    构造：GOLD_SETS 有两份，但 manifest 只登记第一份 —— 全部 pending 时也不许签出 approved。
    """
    tool = _import_tool()
    root, mf, patch = _approve_fixture(tmp_path, tool, main_verdict="pending", shadow="relevant")
    for k, v in patch.items():
        monkeypatch.setattr(tool, k, v)
    man = tool.load_yaml(mf)
    man["files"] = [man["files"][0]]  # 缩水 registry：只剩第一份
    man["totals"] = {"main_set_queries": 1, "cross_vault_attack": 0, "all_registered_queries": 1}
    mf.write_text(
        tool.MANIFEST_HEADER + yaml.safe_dump(man, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8"
    )
    before = mf.read_bytes()
    assert tool.approve_manifest(mf, "impostor") != 0, "registry 缩水必须拒签"
    assert mf.read_bytes() == before


def test_approve_rejects_bad_at_and_missing_checklist(tmp_path: Path, monkeypatch) -> None:
    """``--at`` 必须 ISO8601；``--checklist`` 必须存在（r17 复核 L-1/L-2）。"""
    tool = _import_tool()
    root, mf, patch = _approve_fixture(tmp_path, tool)
    for k, v in patch.items():
        monkeypatch.setattr(tool, k, v)
    before = mf.read_bytes()
    assert tool.approve_manifest(mf, "user", signed_at="not-a-date") != 0
    assert tool.approve_manifest(mf, "user", checklist=str(tmp_path / "does-not-exist.md")) != 0
    assert mf.read_bytes() == before, "参数非法时不得改动 manifest"


def test_build_bump_resets_signature_and_forces_resign(tmp_path: Path, monkeypatch) -> None:
    """``build --bump-revision`` 必须把 approved 重置回 pending（旧签名入 history 留痕）。

    否则「内容已变的新 revision」会带着旧签字 verify 全绿 approved，而 approve 又拒重签
    —— 放行与误拒同时发生（r18 复核 M-4）。
    """
    tool = _import_tool()
    root, mf, patch = _approve_fixture(tmp_path, tool)
    for k, v in patch.items():
        monkeypatch.setattr(tool, k, v)

    assert tool.approve_manifest(mf, "user", signed_at="2026-09-20T12:00:00Z") == 0
    gold = root / "backend" / "tests" / "regression" / "v_main.yaml"
    gold.write_text(gold.read_text(encoding="utf-8") + "# content change\n", encoding="utf-8")

    assert tool.build_manifest(mf, "base", True, "内容变化") == 0
    man = tool.load_yaml(mf)
    assert man["revision"] == 2
    assert man["adjudication"]["status"] == "pending", "新 revision 必须回到 pending 等待重签"
    assert man["adjudication"]["signed_by"] is None
    assert man["revision_history"][-1].get("prev_adjudication", {}).get("signed_by") == "user"
    rc, lines = tool.verify_all(mf)
    assert rc == 0, f"升版后 verify 应 rc=0（pending 合法）：{lines}"

    # 新的 revision 可以（且必须）重新签字
    assert tool.approve_manifest(mf, "user", signed_at="2026-09-20T13:00:00Z") == 0
    assert tool.load_yaml(mf)["adjudication"]["signed_at"] == "2026-09-20T13:00:00Z"
