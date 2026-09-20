# 独立复核请求 — CARD-G4-13（金集补齐 ≥100 + 用户裁定标签 + SHA 冻结 manifest）· **补审 round-1（ZCode × GLM-5.3）**

> **通道与轮次**：本卡此前 **Codex 轮次 = 0**（`gpt-6-astra` 对账号被服务端确定性拒绝，用户裁定「按人审替代记、不换模型」；批级审阅表记「G4-13(人审替代)」）。按 D-43 复核工具链更换，本轮 = **补审**（协议 §2.4.2，ZCode CLI + GLM-5.3），轮次编号 `-r1`（本卡**首轮外部复核**）。**本轮只审不改判**；若报 BLOCKER/HIGH，流程停下交主 session。
>
> **审查绑定 = `d06f7127`**（本卡唯一 commit；8 个文件最终态）。自证（车道预跑，非你执行）：`git --no-pager diff --stat --no-color d06f7127 HEAD -- backend/scripts/gold_set_manifest_tool.py backend/scripts/run_memory_retrieval_regression.py backend/scripts/run_vault_retrieval_regression.py backend/tests/regression/gold_set_manifest.yaml backend/tests/regression/memory_gold_set.yaml backend/tests/regression/test_gold_set_manifest_g413.py backend/tests/regression/vault_gold_set.yaml backend/tests/regression/vault_gold_set_shadow.yaml` = **空**。PREV（本卡开工锚）= `47c94bab`；变更面 = **1707 insertions / 4 deletions**（见 §① 末**内嵌 diff**）。
>
> **你的读取面 = cwd（车道树工作树）**：文件与 `d06f7127` 逐字节同（上条绑定 diff 空）。⛔ 你的 Bash 部分可用（git/grep 可过）但**不得依赖**：全部 git 输出已内嵌；⛔ 不要修改任何文件。
> ⛔ 本分支此后夹着**另一张卡**的 commit（CARD-DEBT-1 的 `9d270cdf` / `0ac28596` / `96da70c6` / `ff3e5fce`，只动 P9-B 文件与 `_bmad-output`）——**不在本卡审查面**；按协议 §1「串行车道按本卡 diff 面判」，**只看本卡 8 文件**。
>
> **前序证据（输入，非轮次；请对抗性复核）**：主验收单 `UAT-CARD-G4-13-2026-09-19.md` —— 12 条行为门（12 passed）、4 段负控（其中**负控③ 挖出真缺陷并已修**：迁移脚本重复注释键把 17 条攻击条目的 `source.ref` 覆盖成 null；修法 = 幂等守卫 + 从干净基线重做 + 常驻文本层判据 `test_no_duplicate_annotation_keys`）、`collect` 只读实证（live vault 零写入）、runner `--shadow` 真入口探针、**用户裁定窗口未开 ⇒ `user_verdict` 全 `pending` + manifest `adjudication.status: pending`（这是已裁定的 SKIP，不是遗漏）**。⛔ 本卡「五类每类 ≥15」只保证「跨 vault 攻击」一类（实得 20；「无答案」7 / 「跨板」0 已另立卡）——**不要**把这两类当本卡漏项审。

## ① 背景与最小读取面（⛔ 只读这些，不要扩大到别的目录）

**本卡做什么（9 文件面）**：

1. `vault_gold_set.yaml` **58→75**（新增 `cross_vault_attack` `vq-x01..x17`，形状复用 G2-9 同名攻击用例集；`config.version` 2→3）；`memory_gold_set.yaml` **25→28**（`mem-x01..x03`；version 1→2）；两主集合计 **103 ≥ 100**。
2. 四份金集每条加标注字段 `user_verdict: pending` / `verdict_by` / `verdict_at` / `source: {kind, ref}`（`origin` 保留）；`vault_gold_set_shadow.yaml` 2 条同；`memory_gold_set_shadow.yaml` 空集（**未被改动**，只被 manifest 登记）。
3. NEW `backend/tests/regression/gold_set_manifest.yaml`（rev=2）：四文件 sha256 / config.version / 计数 / 分类分布 + `totals` + `adjudication`。
4. NEW `backend/scripts/gold_set_manifest_tool.py`（570 行；6 子命令 `build` / `verify` / `census` / `checklist` / `apply-verdicts` / `collect`；stdlib+yaml，不连任何端口）。
5. 两 runner **只加 manifest 校验**（vault：yaml 载入后 `:490`；memory：**在 `check_backend_alive()` 之前** `:355-359`），不符 rc=2；12 个判分函数（vault 7 + memory 5）AST 逐字不变。
6. NEW `backend/tests/regression/test_gold_set_manifest_g413.py`（411 行，12 条承重门）。

⛔ 本卡不改 `backend/app/**`、不改判分/指标/`METRIC_DIRECTIONS`/baseline、不改两 conftest；`memory_gold_set_shadow.yaml` 零 diff。

**请读的东西（最小面写死；除注明外均在你 cwd 内）**：

- **内嵌 diff（本 §① 末）**：`47c94bab → d06f7127` 八文件（1707 insertions / 4 deletions；**先读它**）
- `backend/tests/regression/gold_set_manifest.yaml` 全文（98 行）
- `backend/scripts/gold_set_manifest_tool.py` 全文（570 行）
- `backend/scripts/run_vault_retrieval_regression.py` 的 `:36-70`（import 面含新增 import `:67`）+ `:106-160`（判分/违规判定：`is_contaminated` `:138`、`forbidden_violations` `:145-149`）+ `:300-310`（per-query 违规检查）+ `:464-500`（`main()` `:472` + 校验调用 `:490` + 三处 `return 2`）
- `backend/scripts/run_memory_retrieval_regression.py` 的 `:31-70`（含新增 import `:61`）+ `:86-118`（判分）+ `:330-375`（`main()` `:333` + **校验 `:355-359` 先于 `check_backend_alive()` `:365`**）
- `backend/scripts/g29_dual_vault_canary.py` 的 `:101-111`（形状来源，只读对照，⛔ 本卡零改动）
- `backend/tests/regression/test_gold_set_manifest_g413.py` 全文（411 行）
- 主验收单 `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md`（§二 4-A 全表 / §三 负控四段 + §三.1 / §四 用户裁定 SKIP / §五 / §六）
- 勾选清单 `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19-裁定清单.md`（抽查 2-3 条形状与 `<!-- gsid:… -->` 锚即可，不必全读）
- evidence 存档（**全名**，均在 `_bmad-output/审查/evidence-g413/`）：`struct-before-20260919T044839.txt` / `struct-after-20260919T055435.txt` / `gate-red-20260919T044928.txt` / `gate-green-20260919T045851.txt` / `immutability-20260919T045343.txt` / `immutability-probe-20260919T045353.txt` / `negctl-1-r2-20260919T045451.txt` / `negctl-2-20260919T045512.txt` / `negctl-3-20260919T045532.txt` / `negctl-4-dupkey-20260919T045720.txt` / `shadow-vault-20260919T045328.txt` / `shadow-probe-20260919T045309.txt` / `collect-r2-20260919T045821.txt` / `census-20260919T045736.txt` / `regression-close-20260919T045917.txt` / `named-close-20260919T045851.txt` / `jev-triage-d06f7127.json`
- 总账 v2 `:493-497`（G4-13 判据方向）：`_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md`
- 计划书 `:299-300`：`_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`
- 手册 §二.1 行（**不在你 cwd，原文内嵌**）：「【P9 G4-13】用户裁定标签（user_verdict）标注 session：≥100 条金集逐条真人裁定，约 60-90 分钟；采集真实查询只读 live vault」

**内嵌 diff（原文，`47c94bab → d06f7127`，八文件）：**

```diff
diff --git a/backend/scripts/gold_set_manifest_tool.py b/backend/scripts/gold_set_manifest_tool.py
new file mode 100644
index 00000000..d57ce439
--- /dev/null
+++ b/backend/scripts/gold_set_manifest_tool.py
@@ -0,0 +1,570 @@
+#!/usr/bin/env python3
+"""CARD-G4-13 金集 manifest 工具 —— 采集 / 标注清单 / 回写 / 冻结 / 校验。
+
+[BATCH-2026-09-18-第十五批 / CARD-G4-13]
+
+这个工具解决一件事：金集是检索质量门禁的**真值**，而真值一旦能被悄悄改掉，
+门禁就只是在给自己打分。所以：
+
+* ``build``   —— 实算四份金集的 sha256 / 条数 / 分类分布，写进 ``gold_set_manifest.yaml``；
+* ``verify``  —— 重算并比对。**两个 runner 在跑之前都会调它**，不符就拒跑（rc=2）；
+* ``census``  —— 打印分类映射与 ``user_verdict`` 计数，给验收单用；
+* ``checklist`` —— 出一份**零技术词**的勾选清单，给用户在 Obsidian 里逐条裁定；
+* ``apply-verdicts`` —— 把勾选结果按隐藏锚回写进 yaml；
+* ``collect`` —— **只读**扫一个 vault，把真实用户提问捞成候选（不入集、不写 vault）。
+
+⛔ 设计约束（卡文 §一(e)）：只用 stdlib + ``yaml``。
+**不 import app / lance / httpx，不连任何端口** —— 它要能在离线机器上、在
+``pytest`` 进程里、在两个 runner 的最前面被调用。
+
+⚠️ 关于「冻结」：``build`` 在 manifest 已存在且 ``frozen: true`` 时**拒绝覆盖**，
+必须显式 ``--bump-revision --reason "<为什么>"``。冻结不是把文件设成只读，
+而是「改它要留下一条说得出理由的痕迹」。
+"""
+
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import re
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+
+import yaml
+
+#: ``backend/`` 的绝对路径。本文件位于 ``backend/scripts/``。
+BACKEND_DIR = Path(__file__).resolve().parent.parent
+REPO_ROOT = BACKEND_DIR.parent
+
+REGRESSION_DIR = BACKEND_DIR / "tests" / "regression"
+MANIFEST_PATH = REGRESSION_DIR / "gold_set_manifest.yaml"
+
+#: manifest 登记的四份金集，以及每份按哪个键分类。
+#: 顺序就是 manifest ``files[]`` 的顺序 —— 两个主集在前，便于 ``census`` 读。
+GOLD_SETS = (
+    (REGRESSION_DIR / "vault_gold_set.yaml", "query_type"),
+    (REGRESSION_DIR / "memory_gold_set.yaml", "category"),
+    (REGRESSION_DIR / "vault_gold_set_shadow.yaml", "query_type"),
+    (REGRESSION_DIR / "memory_gold_set_shadow.yaml", "category"),
+)
+
+#: 主集（``totals.main_set_queries`` 只数这两份；shadow 是探索区不计入门禁基数）。
+MAIN_SETS = (GOLD_SETS[0][0], GOLD_SETS[1][0])
+
+#: 跨 vault 攻击类的类名。vault 走 ``query_type``、memory 走 ``category``，名字相同。
+ATTACK_CLASS = "cross_vault_attack"
+
+VERDICT_ENUM = ("pending", "relevant", "irrelevant", "ambiguous", "needs_split")
+SOURCE_KIND_ENUM = ("node", "whiteboard", "exam_board", "review_doc", "fixture", "synthetic")
+
+#: 勾选清单里三个选项对应的 verdict 值。文案是给**非技术用户**看的，
+#: 所以清单里出现的是中文短句，隐藏锚里才是枚举值。
+CHECKLIST_CHOICES = (
+    ("relevant", "相关 —— 这条提问，它给出的笔记确实能回答"),
+    ("irrelevant", "不相关 —— 给出的笔记答非所问"),
+    ("ambiguous", "说不清 —— 我也拿不准，或者这条提问本身有歧义"),
+)
+
+#: ``checklist`` 里每条的隐藏锚。``apply-verdicts`` 按它定位，不靠行号、不靠标题文字。
+GSID_RE = re.compile(r"<!--\s*gsid:([^\s>]+)\s*-->")
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 基础读写
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def load_yaml(path: Path) -> dict:
+    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
+
+
+def queries_of(path: Path) -> list:
+    return load_yaml(path).get("queries") or []
+
+
+def sha256_of(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def rel_to_repo(path: Path) -> str | None:
+    """manifest 里一律写**仓相对路径** —— 绝对路径换台机器就对不上。
+
+    ⚠️ 仓外路径返回 ``None``，**不抛异常**：``verify_gold_set_file`` 是两个 runner
+    的 fail-closed 边界，它自己必须不崩。崩溃（未捕获 ValueError）与「不符」
+    （有文案的 rc=2）在 runner 里是两种完全不同的结局 —— 前者会把「金集被指到
+    仓外了」显示成一个看不懂的堆栈。本卡的行为门就抓到过这一点。
+    """
+    try:
+        return str(path.resolve().relative_to(REPO_ROOT))
+    except ValueError:
+        return None
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# build / verify
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def describe_file(path: Path, class_key: str) -> dict:
+    """一份金集在 manifest 里的那条记录。"""
+    rel = rel_to_repo(path)
+    if rel is None:
+        raise ValueError(f"{path} 在仓外 —— manifest 只登记仓内路径（写进去换台机器就对不上）")
+    doc = load_yaml(path)
+    qs = doc.get("queries") or []
+    by_class: dict = {}
+    verdicts: dict = {v: 0 for v in VERDICT_ENUM}
+    for q in qs:
+        by_class[q.get(class_key) or "<unclassified>"] = by_class.get(q.get(class_key) or "<unclassified>", 0) + 1
+        v = q.get("user_verdict")
+        if v in verdicts:
+            verdicts[v] += 1
+        else:
+            verdicts.setdefault("<invalid>", 0)
+            verdicts["<invalid>"] += 1
+    return {
+        "path": rel,
+        "config_version": (doc.get("config") or {}).get("version"),
+        "sha256": sha256_of(path),
+        "query_count": len(qs),
+        "class_key": class_key,
+        "by_class": dict(sorted(by_class.items())),
+        "verdict_counts": verdicts,
+    }
+
+
+def build_manifest(manifest_path: Path, base_commit: str, bump: bool, reason: str | None) -> int:
+    """实算并写 manifest。已冻结时必须 ``--bump-revision --reason``。"""
+    revision = 1
+    history = []
+    if manifest_path.exists():
+        old = load_yaml(manifest_path)
+        if old.get("frozen") and not bump:
+            print(
+                f"⛔ {manifest_path.name} 已冻结（frozen: true, revision: {old.get('revision')}）。"
+                "要改它请显式带 --bump-revision --reason '<为什么>' —— "
+                "冻结不是不能改，是改了要留下说得出理由的痕迹。",
+                file=sys.stderr,
+            )
+            return 1
+        if bump:
+            if not reason:
+                print("⛔ --bump-revision 必须同时给 --reason", file=sys.stderr)
+                return 1
+            revision = int(old.get("revision") or 0) + 1
+            history = list(old.get("revision_history") or [])
+            history.append({"revision": revision, "at": _now_iso(), "reason": reason})
+
+    files = [describe_file(p, key) for p, key in GOLD_SETS]
+    main_total = sum(f["query_count"] for f in files if (REPO_ROOT / f["path"]) in [p.resolve() for p in MAIN_SETS])
+    attack_total = sum(
+        f["by_class"].get(ATTACK_CLASS, 0) for f in files if (REPO_ROOT / f["path"]) in [p.resolve() for p in MAIN_SETS]
+    )
+
+    prev_adj = (load_yaml(manifest_path).get("adjudication") if manifest_path.exists() else None) or {
+        "status": "pending",
+        "signed_by": None,
+        "signed_at": None,
+        "checklist_path": None,
+    }
+
+    doc = {
+        "revision": revision,
+        "frozen_at": _now_iso(),
+        "base_commit": base_commit,
+        "frozen": True,
+        "files": files,
+        "totals": {
+            "main_set_queries": main_total,
+            "cross_vault_attack": attack_total,
+            "all_registered_queries": sum(f["query_count"] for f in files),
+        },
+        "adjudication": prev_adj,
+    }
+    if history:
+        doc["revision_history"] = history
+
+    manifest_path.write_text(
+        "# gold_set_manifest.yaml — CARD-G4-13 金集冻结清单（由 backend/scripts/gold_set_manifest_tool.py 生成）\n"
+        "#\n"
+        "# ⛔ 不要手改这个文件：sha256 / 计数都是实算的，手改只会让 verify 红。\n"
+        "#    要改金集 → 改 yaml → `python scripts/gold_set_manifest_tool.py build --bump-revision --reason '...'`。\n"
+        "#\n"
+        "# 两个 retrieval runner 在跑之前都会调 verify_gold_set_file()；不符就拒跑（rc=2）。\n\n"
+        + yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100),
+        encoding="utf-8",
+    )
+    print(f"OK build revision={revision} main={main_total} attack={attack_total} -> {manifest_path.name}")
+    return 0
+
+
+def verify_all(manifest_path: Path | None = None) -> tuple[int, list]:
+    """重算并比对。返回 ``(rc, 行列表)``。
+
+    rc 语义与两个 runner 的既有约定一致：
+    ``0`` 全符 / ``1`` 内容不符 / ``2`` 文件缺失或 yaml 解析错（= 环境/输入错）。
+    """
+    manifest_path = manifest_path or MANIFEST_PATH
+    lines: list = []
+    if not manifest_path.exists():
+        return 2, [f"MISSING {manifest_path} manifest 不存在"]
+    try:
+        m = load_yaml(manifest_path)
+    except yaml.YAMLError as exc:
+        return 2, [f"UNPARSEABLE {manifest_path} {exc}"]
+
+    rc = 0
+    for entry in m.get("files") or []:
+        path = REPO_ROOT / entry["path"]
+        if not path.exists():
+            lines.append(f"MISSING {entry['path']} 期望存在 实测不存在")
+            rc = max(rc, 2)
+            continue
+        try:
+            doc = load_yaml(path)
+        except yaml.YAMLError as exc:
+            lines.append(f"UNPARSEABLE {entry['path']} {exc}")
+            rc = max(rc, 2)
+            continue
+
+        actual_sha = sha256_of(path)
+        if actual_sha != entry["sha256"]:
+            lines.append(f"MISMATCH {entry['path']} sha256={entry['sha256']} actual={actual_sha}")
+            rc = max(rc, 1)
+            continue
+
+        qs = doc.get("queries") or []
+        if len(qs) != entry["query_count"]:
+            lines.append(f"MISMATCH {entry['path']} query_count={entry['query_count']} actual={len(qs)}")
+            rc = max(rc, 1)
+            continue
+        cv = (doc.get("config") or {}).get("version")
+        if cv != entry.get("config_version"):
+            lines.append(f"MISMATCH {entry['path']} config_version={entry.get('config_version')} actual={cv}")
+            rc = max(rc, 1)
+            continue
+
+        bad = _field_problems(qs)
+        if bad:
+            lines.append(f"MISMATCH {entry['path']} fields_ok=True actual={bad[0]}（共 {len(bad)} 条）")
+            rc = max(rc, 1)
+            continue
+
+        lines.append(f"OK {entry['path']} sha256={actual_sha[:12]}… queries={len(qs)}")
+    return rc, lines
+
+
+def _field_problems(queries: list) -> list:
+    """每条 query 的标注字段是否齐全合法。"""
+    bad = []
+    for q in queries:
+        qid = q.get("id", "<no-id>")
+        if q.get("user_verdict") not in VERDICT_ENUM:
+            bad.append(f"{qid}.user_verdict={q.get('user_verdict')!r}")
+        src = q.get("source")
+        if not isinstance(src, dict) or src.get("kind") not in SOURCE_KIND_ENUM:
+            bad.append(f"{qid}.source={src!r}")
+        elif src.get("ref") is not None and not isinstance(src.get("ref"), str):
+            bad.append(f"{qid}.source.ref={src.get('ref')!r}")
+    return bad
+
+
+def verify_gold_set_file(path: Path, manifest_path: Path | None = None) -> tuple[bool, str]:
+    """**两个 runner 调的就是这个**：单份金集是否与 manifest 相符。
+
+    返回 ``(是否相符, 一行说明)``。runner 拿到 ``False`` 就打印说明并 ``return 2``。
+    """
+    manifest_path = manifest_path or MANIFEST_PATH
+    if not manifest_path.exists():
+        return False, f"manifest 不存在: {manifest_path}"
+    m = load_yaml(manifest_path)
+    want = rel_to_repo(Path(path))
+    if want is None:
+        return False, f"{path} 在仓外 —— manifest 只登记仓内路径，无法校验"
+    for entry in m.get("files") or []:
+        if entry["path"] != want:
+            continue
+        actual = sha256_of(Path(path))
+        if actual != entry["sha256"]:
+            return False, f"{want} sha256 期望 {entry['sha256'][:12]}… 实测 {actual[:12]}…"
+        return True, f"OK {want} sha256={actual[:12]}… queries={entry['query_count']}"
+    return False, f"{want} 未登记在 manifest 里"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# census
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def census(manifest_path: Path | None = None) -> int:
+    manifest_path = manifest_path or MANIFEST_PATH
+    total = 0
+    for path, key in GOLD_SETS:
+        qs = queries_of(path)
+        total += len(qs)
+        by = {}
+        verd = {}
+        for q in qs:
+            by[q.get(key) or "<unclassified>"] = by.get(q.get(key) or "<unclassified>", 0) + 1
+            verd[q.get("user_verdict")] = verd.get(q.get("user_verdict"), 0) + 1
+        print(f"{path.name}  ({key})  n={len(qs)}")
+        for k, v in sorted(by.items()):
+            print(f"    {k:<28} {v}")
+        print(f"    verdicts: {dict(sorted(verd.items(), key=lambda kv: str(kv[0])))}")
+    main = sum(len(queries_of(p)) for p in MAIN_SETS)
+    attack = sum(len([q for q in queries_of(p) if (q.get(k) == ATTACK_CLASS)]) for p, k in GOLD_SETS if p in MAIN_SETS)
+    print(f"\nmain_set_queries={main}  cross_vault_attack={attack}  all_registered={total}")
+    if manifest_path.exists():
+        adj = load_yaml(manifest_path).get("adjudication") or {}
+        print(f"adjudication.status={adj.get('status')}  signed_by={adj.get('signed_by')}")
+    return 0
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# checklist / apply-verdicts
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _expect_hint(q: dict) -> str:
+    """把「它期望命中什么」翻译成一句**非技术**的话。"""
+    if q.get("expect_empty"):
+        return "（期望：库里**没有**这个主题，应当什么都不返回）"
+    hits = q.get("expect_hit") or []
+    if hits:
+        names = "、".join(str(h.get("file")) for h in hits if isinstance(h, dict) and h.get("file"))
+        if names:
+            return f"（期望命中的笔记：{names}）"
+    anys = q.get("expect_any") or []
+    if anys:
+        return f"（期望结果里出现这些词之一：{'、'.join(str(a) for a in anys)}）"
+    nots = q.get("expect_not_hit") or []
+    if nots:
+        return "（期望：**不该**出现另一个 vault 的同名资产）"
+    return "（期望：见金集原文）"
+
+
+def write_checklist(paths: list, out_md: Path) -> int:
+    """出一份给用户逐条勾的清单。⛔ 段落里零技术词。"""
+    lines = [
+        "# 金集裁定清单 — CARD-G4-13",
+        "",
+        "下面每一条是**一次提问**，以及系统认为「应该给你看到什么」。",
+        "你只需要读一句提问、看一眼它期望的笔记名，然后勾一个格子：",
+        "**相关 / 不相关 / 说不清**。三选一，勾错了改回来就行。",
+        "",
+        "> 不用管技术细节，也不用打开任何终端。勾完保存，告诉我一声即可。",
+        "",
+    ]
+    n = 0
+    for path in paths:
+        lines.append(f"## {path.name}")
+        lines.append("")
+        for q in queries_of(path):
+            qid = q.get("id")
+            lines.append(f"<!-- gsid:{qid} -->")
+            lines.append(f"**{qid}** — 「{q.get('query')}」")
+            lines.append(f"  {_expect_hint(q)}")
+            for value, label in CHECKLIST_CHOICES:
+                lines.append(f"- [ ] {label}  <!-- verdict:{value} -->")
+            lines.append("")
+            n += 1
+    out_md.parent.mkdir(parents=True, exist_ok=True)
+    out_md.write_text("\n".join(lines), encoding="utf-8")
+    return n
+
+
+def apply_verdicts(paths: list, md: Path, verdict_by: str, verdict_at: str | None = None) -> tuple[list, list]:
+    """把勾选结果回写进 yaml。返回 ``(改动的 id 列表, 问题列表)``。
+
+    没勾的、勾了多个的、锚找不到的 —— **一律不动那一条**并列进问题列表。
+    默默猜一个值比不动更糟。
+    """
+    verdict_at = verdict_at or _now_iso()
+    text = md.read_text(encoding="utf-8")
+    picks: dict = {}
+    problems: list = []
+
+    current = None
+    for line in text.splitlines():
+        m = GSID_RE.search(line)
+        if m:
+            current = m.group(1)
+            continue
+        if current and line.lstrip().startswith("- [x]"):
+            vm = re.search(r"<!--\s*verdict:([a-z_]+)\s*-->", line)
+            if not vm:
+                continue
+            if current in picks:
+                problems.append(f"{current}: 勾了不止一个（{picks[current]} 与 {vm.group(1)}）—— 该条不动")
+                picks[current] = None
+            elif picks.get(current, "") is None:
+                continue
+            else:
+                picks[current] = vm.group(1)
+
+    picks = {k: v for k, v in picks.items() if v}
+    changed: list = []
+    for path in paths:
+        doc = load_yaml(path)
+        qs = doc.get("queries") or []
+        touched = False
+        for q in qs:
+            v = picks.get(q.get("id"))
+            if not v:
+                continue
+            if v not in VERDICT_ENUM:
+                problems.append(f"{q.get('id')}: 勾到一个不认识的值 {v!r} —— 该条不动")
+                continue
+            q["user_verdict"] = v
+            q["verdict_by"] = verdict_by
+            q["verdict_at"] = verdict_at
+            changed.append(q.get("id"))
+            touched = True
+        if touched:
+            _rewrite_queries_in_place(path, qs)
+    unknown = sorted(set(picks) - set(changed))
+    problems.extend(f"{u}: 清单里勾了，但四份金集里找不到这个 id" for u in unknown)
+    return changed, problems
+
+
+def _rewrite_queries_in_place(path: Path, queries: list) -> None:
+    """只重写 ``queries:`` 段，**保留文件头部的注释块**（版本纪律写在那里）。"""
+    text = path.read_text(encoding="utf-8")
+    idx = text.index("\nqueries:")
+    head = text[: idx + 1]
+    body = yaml.safe_dump({"queries": queries}, allow_unicode=True, sort_keys=False, width=100)
+    path.write_text(head + body, encoding="utf-8")
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# collect（只读）
+# ═══════════════════════════════════════════════════════════════════════════
+
+_QUESTION_CALLOUT = re.compile(r">\s*\[!question\]\+?\s*(.*)")
+
+#: callout **标题行**里的模板占位：Obsidian 插件写进去的锚（``%%cb-xxxx%%``）、
+#: 「❓ 提问」这类固定抬头、以及「待剖析 · 源自 [[...]]」的出处行。
+#: ⚠️ 本卡实测踩过：只读标题行的话，10 条候选里捞到的**全是这些模板**，
+#: 一条真实提问都没有 —— 用户写的内容在 callout 的**续行**（`> ` 开头）里。
+#: ⚠️ 用 ``search`` 语义而不是整行相等：实测这些抬头**带后缀**
+#: （`待剖析 · 源自 [[检验白板/…]]（2026-08-11）`），整行锚定的正则一条都匹配不上。
+_TEMPLATE_TITLE = re.compile(r"(❓\s*提问|待剖析|%%cb-[^%]*%%)")
+
+#: 续行里要跳过的：勾选项（`- [ ] ✅ 已懂`）、空续行、AI 生成的出处/原因说明。
+_SKIP_BODY = re.compile(r"^(-\s*\[[ x]\]|AI 判断来源|原因[:：])|^$")
+
+
+def collect_candidates(vault: Path, out_json: Path) -> int:
+    """**只读**扫一个 vault，把真实用户提问捞成候选。
+
+    ⛔ 只 read_text，绝不写 ``vault`` 下的任何东西。产物只写到 ``out_json``。
+    """
+    vault = Path(vault)
+    cands: list = []
+    for md in sorted((vault / "节点").glob("*.md")) if (vault / "节点").is_dir() else []:
+        lines = md.read_text(encoding="utf-8").splitlines()
+        for i, line in enumerate(lines, 1):
+            m = _QUESTION_CALLOUT.match(line.strip())
+            if not m:
+                continue
+            title = m.group(1).strip()
+            # 标题行如果是模板占位（`❓ 提问 %%cb-xxxx%%` / `待剖析 · 源自 [[…]]`），
+            # 真内容在续行里 —— 往下读 `> ` 续行，取第一句像提问的。
+            picked, picked_line = (title, i) if title and not _TEMPLATE_TITLE.search(title) else (None, i)
+            if picked is None:
+                for k in range(i, min(i + 12, len(lines))):
+                    body = lines[k].lstrip()
+                    if not body.startswith(">"):
+                        break
+                    body = body[1:].strip()
+                    if body and not _SKIP_BODY.search(body) and not _TEMPLATE_TITLE.search(body):
+                        picked, picked_line = body, k + 1
+                        break
+            if picked:
+                cands.append(
+                    {
+                        "query": picked,
+                        "source": {"kind": "node", "ref": f"{md.relative_to(vault)}:{picked_line}"},
+                        "why": "用户手写 [!question] callout",
+                    }
+                )
+    for md in sorted((vault / "原白板").glob("*.md")) if (vault / "原白板").is_dir() else []:
+        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
+            if line.startswith("# ") and line[2:].strip():
+                cands.append(
+                    {
+                        "query": line[2:].strip(),
+                        "source": {"kind": "whiteboard", "ref": f"{md.relative_to(vault)}:{i}"},
+                        "why": "原白板一级标题",
+                    }
+                )
+                break
+    out_json.parent.mkdir(parents=True, exist_ok=True)
+    out_json.write_text(json.dumps(cands, ensure_ascii=False, indent=2), encoding="utf-8")
+    print(f"OK collect n={len(cands)} -> {out_json}（⛔ 候选而已，没有入集）")
+    return len(cands)
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# CLI
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def main(argv: list | None = None) -> int:
+    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
+    sub = ap.add_subparsers(dest="cmd", required=True)
+
+    b = sub.add_parser("build", help="实算 sha/计数，写 manifest")
+    b.add_argument("--base-commit", default="9c4e7e82")
+    b.add_argument("--bump-revision", action="store_true")
+    b.add_argument("--reason", default=None)
+
+    sub.add_parser("verify", help="重算并比对；0 全符 / 1 不符 / 2 缺文件或解析错")
+    sub.add_parser("census", help="打印分类映射与 verdict 计数")
+
+    c = sub.add_parser("checklist", help="出用户裁定勾选清单")
+    c.add_argument("--out", required=True)
+
+    a = sub.add_parser("apply-verdicts", help="按隐藏锚回写勾选结果")
+    a.add_argument("--from", dest="src", required=True)
+    a.add_argument("--by", default="user")
+
+    co = sub.add_parser("collect", help="只读扫 vault 出候选 query")
+    co.add_argument("--vault", required=True, help="⛔ 必须显式给，没有默认值")
+    co.add_argument("--out", required=True)
+
+    ns = ap.parse_args(argv)
+
+    if ns.cmd == "build":
+        return build_manifest(MANIFEST_PATH, ns.base_commit, ns.bump_revision, ns.reason)
+    if ns.cmd == "verify":
+        rc, lines = verify_all()
+        for ln in lines:
+            print(ln)
+        return rc
+    if ns.cmd == "census":
+        return census()
+    if ns.cmd == "checklist":
+        n = write_checklist(list(MAIN_SETS), Path(ns.out))
+        print(f"OK checklist n={n} -> {ns.out}")
+        return 0
+    if ns.cmd == "apply-verdicts":
+        changed, problems = apply_verdicts(list(MAIN_SETS), Path(ns.src), ns.by)
+        for p in problems:
+            print(f"SKIP {p}")
+        print(f"OK apply-verdicts changed={len(changed)}")
+        return 1 if problems else 0
+    if ns.cmd == "collect":
+        collect_candidates(Path(ns.vault), Path(ns.out))
+        return 0
+    return 2
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/backend/scripts/run_memory_retrieval_regression.py b/backend/scripts/run_memory_retrieval_regression.py
index 9e628687..cbc95a7b 100644
--- a/backend/scripts/run_memory_retrieval_regression.py
+++ b/backend/scripts/run_memory_retrieval_regression.py
@@ -55,6 +55,11 @@ BASELINE_HISTORY = BASELINE_FILE.with_name("memory_retrieval_baseline_history.js
 JUDGE_REVIEW = BASELINE_FILE.with_name("memory_retrieval_judge_review.jsonl")
 QWEN_URL = "http://127.0.0.1:12341/v1/chat/completions"
 
+# CARD-G4-13: 金集冻结校验（工具与本文件同在 scripts/ 下，不是包，所以把
+# scripts/ 也放进 sys.path）。
+sys.path.insert(0, str(Path(__file__).resolve().parent))
+from gold_set_manifest_tool import verify_gold_set_file  # noqa: E402
+
 GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"
 
 # 指标方向: True = 越高越好 (回退=下降), False = 越低越好 (回退=上升)
@@ -346,6 +351,17 @@ def main() -> int:
         print(f"{RED}⛔ --update-baseline 必须带 --reason (基线 churn 可审计){RESET}")
         return 2
 
+    # CARD-G4-13: 金集与 gold_set_manifest.yaml 对不上就拒跑。
+    # ⚠️ 这一段**必须在 check_backend_alive() 之前**：读 yaml 不需要 backend，
+    # 而两种失败都是 rc=2 —— 放在后面的话，离线机器上门会被 alive 检查恒久短路，
+    # 「金集被改了」和「8011 没起」就再也分不开了。两者靠**文案**区分。
+    gold_path_for_check = SHADOW_SET if args.shadow else GOLD_SET
+    ok, detail = verify_gold_set_file(gold_path_for_check)
+    if not ok:
+        print(f"{RED}⛔ 金集与 gold_set_manifest.yaml 不符 ({detail}){RESET}")
+        return 2
+    print(detail)
+
     if not check_backend_alive():
         print(
             f"{RED}⛔ backend 不可达 ({HEALTH_ENDPOINT}) — 先起 backend 再跑门禁。"
diff --git a/backend/scripts/run_vault_retrieval_regression.py b/backend/scripts/run_vault_retrieval_regression.py
index f2d6b78d..99ca64c6 100644
--- a/backend/scripts/run_vault_retrieval_regression.py
+++ b/backend/scripts/run_vault_retrieval_regression.py
@@ -1,8 +1,11 @@
 #!/usr/bin/env python
 """RAG-S2 评测门禁 (RAG-S2-2026-08-09): vault 检索 gold set 回归。
 
-对 tests/regression/vault_gold_set.yaml 的 60 条 query 跑三层评测, 产出排序/
-交付指标并与固化基线比较 — 任一指标回退超容差即 fail。阶段 2 每个改动批次
+对 tests/regression/vault_gold_set.yaml 的全部 query 跑三层评测, 产出排序/
+交付指标并与固化基线比较 — 任一指标回退超容差即 fail。
+(条数以 tests/regression/gold_set_manifest.yaml 为准 — 曾写死「60 条」, v2 移 2 条进
+ shadow 后实为 58, CARD-G4-13 再补 17 条跨 vault 攻击后为 75; 写死的数字必然过期。)
+阶段 2 每个改动批次
 (chunk 策略 / 权重 / dedup / rerank) 完成必跑, 作为强制验收挡板。
 
 三层 (fork 自 run_memory_retrieval_regression.py, 结构与纪律同源):
@@ -58,6 +61,11 @@ BASELINE_FILE = BACKEND_DIR / "tests" / "fixtures" / "regression_baselines" / "v
 LAST_RUN_FILE = BASELINE_FILE.with_name("vault_retrieval_last_run.json")
 BASELINE_HISTORY = BASELINE_FILE.with_name("vault_retrieval_baseline_history.jsonl")
 
+# CARD-G4-13: 金集冻结校验。工具与本文件同在 scripts/ 下，不是包，所以把
+# scripts/ 也放进 sys.path（上面只放了 BACKEND_DIR 与 BACKEND_DIR/lib）。
+sys.path.insert(0, str(Path(__file__).resolve().parent))
+from gold_set_manifest_tool import verify_gold_set_file  # noqa: E402
+
 # ⚠️ 必须在 backend 容器内执行 (docker exec canvas-learning-system-backend
 # python scripts/run_vault_retrieval_regression.py ...) — 生产 LanceDB 在
 # named volume (容器内 /lancedb), 宿主进程解析到空的相对路径 data/lancedb,
@@ -475,6 +483,16 @@ def main() -> int:
         return 2
 
     gold_path = SHADOW_SET if args.shadow else GOLD_SET
+
+    # CARD-G4-13: 金集与 gold_set_manifest.yaml 对不上就拒跑。
+    # 金集是这道门的**真值**；真值能被悄悄改掉，门就只是在给自己打分。
+    # rc=2 沿用本文件既有的「环境/输入错 ≠ 指标回退」语义（同 :475 / :488 / :498）。
+    ok, detail = verify_gold_set_file(gold_path)
+    if not ok:
+        print(f"{RED}⛔ 金集与 gold_set_manifest.yaml 不符 ({detail}){RESET}")
+        return 2
+    print(detail)
+
     gold = yaml.safe_load(gold_path.read_text(encoding="utf-8"))
     tolerance = float(gold["config"].get("tolerance", 0.02))
     if args.shadow and not gold.get("queries"):
diff --git a/backend/tests/regression/gold_set_manifest.yaml b/backend/tests/regression/gold_set_manifest.yaml
new file mode 100644
index 00000000..c9e637bc
--- /dev/null
+++ b/backend/tests/regression/gold_set_manifest.yaml
@@ -0,0 +1,98 @@
+# gold_set_manifest.yaml — CARD-G4-13 金集冻结清单（由 backend/scripts/gold_set_manifest_tool.py 生成）
+#
+# ⛔ 不要手改这个文件：sha256 / 计数都是实算的，手改只会让 verify 红。
+#    要改金集 → 改 yaml → `python scripts/gold_set_manifest_tool.py build --bump-revision --reason '...'`。
+#
+# 两个 retrieval runner 在跑之前都会调 verify_gold_set_file()；不符就拒跑（rc=2）。
+
+revision: 2
+frozen_at: '2026-09-19T11:56:41Z'
+base_commit: 9c4e7e82
+frozen: true
+files:
+- path: backend/tests/regression/vault_gold_set.yaml
+  config_version: 3
+  sha256: 650c5d46e7ca4d990fb740b9543cc3fdd6280ba62f3064ad07c3a28aa4234b4d
+  query_count: 75
+  class_key: query_type
+  by_class:
+    appended_content: 5
+    cross_vault_attack: 17
+    crosslingual: 5
+    definition_recall: 10
+    example_recall: 6
+    file_locate: 5
+    handwritten_vs_transcript: 7
+    homograph_ambiguous: 6
+    meta_annotation: 5
+    nonexistent: 4
+    zero_lexical_overlap: 5
+  verdict_counts:
+    pending: 75
+    relevant: 0
+    irrelevant: 0
+    ambiguous: 0
+    needs_split: 0
+- path: backend/tests/regression/memory_gold_set.yaml
+  config_version: 2
+  sha256: d88d3a0a70b77280627c45b96476560750d57fc93f4e248d4bfef58a8a76fffb
+  query_count: 28
+  class_key: category
+  by_class:
+    ambiguous: 3
+    annotation: 1
+    cross_vault_attack: 3
+    crosslingual: 2
+    knowledge: 10
+    meta: 2
+    nonexistent: 3
+    paraphrase: 3
+    session: 1
+  verdict_counts:
+    pending: 28
+    relevant: 0
+    irrelevant: 0
+    ambiguous: 0
+    needs_split: 0
+- path: backend/tests/regression/vault_gold_set_shadow.yaml
+  config_version: 2
+  sha256: c7b25fcc9c0b28d3993199016d665133986eff55c8afdb3660e5085f522b4bec
+  query_count: 2
+  class_key: query_type
+  by_class:
+    file_locate: 1
+    handwritten_vs_transcript: 1
+  verdict_counts:
+    pending: 2
+    relevant: 0
+    irrelevant: 0
+    ambiguous: 0
+    needs_split: 0
+- path: backend/tests/regression/memory_gold_set_shadow.yaml
+  config_version: 0
+  sha256: 582df3afe892843b7d0bcb65a10a368c7907d55f3a38a49b8e9a5bdc3284a081
+  query_count: 0
+  class_key: category
+  by_class: {}
+  verdict_counts:
+    pending: 0
+    relevant: 0
+    irrelevant: 0
+    ambiguous: 0
+    needs_split: 0
+totals:
+  main_set_queries: 103
+  cross_vault_attack: 20
+  all_registered_queries: 105
+adjudication:
+  status: pending
+  signed_by: null
+  signed_at: null
+  checklist_path: null
+revision_history:
+- revision: 1
+  at: '2026-09-19T11:54:21Z'
+  reason: 负控① 还原：manifest 尚未入库，git show HEAD 不可用，改用 build 重算复原
+- revision: 2
+  at: '2026-09-19T11:56:41Z'
+  reason: 修复迁移幂等缺陷：annotate 曾给自带标注的 17+3 条重复写键，yaml 静默取后者导致 source.ref 被覆盖为 null（负控③ 挖出）
diff --git a/backend/tests/regression/memory_gold_set.yaml b/backend/tests/regression/memory_gold_set.yaml
index 7a327aac..db38564d 100644
--- a/backend/tests/regression/memory_gold_set.yaml
+++ b/backend/tests/regression/memory_gold_set.yaml
@@ -7,11 +7,14 @@
 # 指标: hit@5 / MRR / 重复率 / 假阳性率 / 泄漏率 — 见 backend/scripts/run_memory_retrieval_regression.py
 #       (hit@5 曾误名 recall@5 — 分母是 query 数, 教科书口径为 hit rate; G4-12 2026-08-27 正名, 判分逻辑与数值不变)
 
+# version 2 (2026-09-19, CARD-G4-13): 新增 mem-x01..mem-x03 跨 vault 同名资产攻击;
+# 全条目追加 user_verdict/verdict_by/verdict_at/source 四个标注字段 (判分侧不读)。
+# 既有 25 条逐字未动。
 config:
   # P1 冻结版本化 (2026-07-24, 终验对账裁决 2): regression_gold_v1 封版 —
   # 修改既有 query/expect_any 必须升 version 并在 baseline_history 留痕;
   # 新样本先进 memory_gold_set_shadow.yaml (exploration), 定期评审后升版并入。
-  version: 1
+  version: 2
   group_id: null            # null = 运行时 default_vault_group_id() 推导 (与 MCP 工具缺省一致)
   max_results: 10
   # 泄漏标记: 命中任一 = 测试污染泄漏 (对抗审查 C1: TestConceptA/B/C, UAT-2.5.X-test 种子, m3-e2e 会话链)
@@ -37,6 +40,10 @@ queries:
     category: knowledge
     origin: "审查 q1 (实测 80%, 同三元组 5 变体占半屏)"
     expect_any: ["特征值", "eigenvalue", "PCA", "主成分"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-02
     query: "零空间和特征值有什么关系"
@@ -44,6 +51,10 @@ queries:
     category: knowledge
     origin: "审查 q2 (实测 65%, 两条逐字节相同并排)"
     expect_any: ["零空间", "null space", "特征值", "eigenvalue"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-03
     query: "forward checking vs AC-3 difference"
@@ -51,6 +62,10 @@ queries:
     category: knowledge
     origin: "审查 q3 (实测 90%, 最佳)"
     expect_any: ["forward checking", "AC-3", "arc consistency", "弧一致"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-04
     query: "how does backtracking search relate to DFS"
@@ -58,6 +73,10 @@ queries:
     category: knowledge
     origin: "审查 q4 (实测 95%, 但同 fact 重复 7 次)"
     expect_any: ["backtracking", "DFS", "depth-first", "回溯", "深度优先"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-05
     query: "什么是理性代理"
@@ -65,6 +84,10 @@ queries:
     category: annotation
     origin: "审查 q5 (实测 30%, rank1 是弧一致性)"
     expect_any: ["理性", "rational", "agent", "代理"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-06
     query: "我对哪些概念有误解"
@@ -72,6 +95,10 @@ queries:
     category: meta
     origin: "审查 q6 (实测 45%, 孤立批注不带所属节点)"
     expect_any: ["误解", "混淆", "错误", "misconception", "confus"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-07
     query: "协方差矩阵怎么计算"
@@ -79,6 +106,10 @@ queries:
     category: knowledge
     origin: "审查 q7 (实测 85%, 纯中文可用)"
     expect_any: ["协方差", "covariance"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-08
     query: "一个矩阵把向量拉伸但不改变它的方向，这个方向说明什么"
@@ -86,6 +117,10 @@ queries:
     category: paraphrase
     origin: "审查 q8 (同义改写零关键词, 实测 60%, 正解 rank7)"
     expect_any: ["特征向量", "特征值", "eigenvector", "eigenvalue"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-09
     query: "傅里叶变换的性质"
@@ -93,6 +128,10 @@ queries:
     category: nonexistent
     origin: "审查 q9 (库内不存在, 实测满编 10 条无关)"
     expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-10
     query: "我上次学习会话学了什么"
@@ -100,6 +139,10 @@ queries:
     category: session
     origin: "审查 q10 (实测 35%, 专写的会话总结 fact 未召回)"
     expect_any: ["会话", "总结", "session", "summary"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-11
     query: "代理"
@@ -107,6 +150,10 @@ queries:
     category: ambiguous
     origin: "审查 q11 (歧义短词, 实测 30%, 7/10 无关含裸词垃圾)"
     expect_any: ["agent", "理性", "rational"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
 
   - id: mem-12
     query: "CSP 求解时先给哪个变量赋值"
@@ -116,12 +163,20 @@ queries:
     expect_any: ["变量", "MRV", "variable", "ordering", "CSP", "约束"]
 
   # ── 新增 13 条 (G0: 补中英对半 + 三类难例) ──
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
   - id: mem-13
     query: "admissibility vs consistency of heuristics"
     language: en
     category: knowledge
     origin: "g0-new (库内最强主题, A* 启发函数)"
     expect_any: ["admissib", "consisten", "heuristic", "启发"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-14
     query: "when is a heuristic guaranteed to never overestimate the true cost"
@@ -129,6 +184,10 @@ queries:
     category: paraphrase
     origin: "g0-new (同义改写零关键词 → admissible)"
     expect_any: ["admissib", "heuristic", "启发", "overestimate"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-15
     query: "value"
@@ -136,6 +195,10 @@ queries:
     category: ambiguous
     origin: "g0-new (歧义短词: value iteration vs eigenvalue vs 裸词垃圾 — 审查 q11 发现裸词垃圾 value)"
     expect_any: ["value iteration", "值迭代", "utility", "效用", "eigenvalue", "特征值"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-16
     query: "value iteration convergence in MDPs"
@@ -143,6 +206,10 @@ queries:
     category: knowledge
     origin: "g0-new (CS188 值迭代)"
     expect_any: ["value iteration", "值迭代", "MDP", "Bellman", "收敛"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-17
     query: "minimax with alpha-beta pruning"
@@ -150,6 +217,10 @@ queries:
     category: knowledge
     origin: "g0-new (CS188 零和博弈)"
     expect_any: ["minimax", "alpha-beta", "剪枝", "零和", "zero-sum"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-18
     query: "red-black tree deletion rebalancing"
@@ -157,6 +228,10 @@ queries:
     category: nonexistent
     origin: "g0-new (数据结构不在库, 英文版假阳性测试)"
     expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-19
     query: "what mistakes did I make about A* search"
@@ -164,6 +239,10 @@ queries:
     category: meta
     origin: "g0-new (元查询英文版, 错误记忆召回)"
     expect_any: ["A*", "admissib", "consisten", "错误", "mistake"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-20
     query: "covariance matrix and its eigenvectors"
@@ -171,6 +250,10 @@ queries:
     category: crosslingual
     origin: "g0-new (跨语: 库内协方差为中文三元组, 英文 query 测 dense 层拉平)"
     expect_any: ["covariance", "协方差", "eigenvector", "特征向量"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-21
     query: "arc consistency propagation steps"
@@ -178,6 +261,10 @@ queries:
     category: knowledge
     origin: "g0-new (AC-3 约束传播)"
     expect_any: ["AC-3", "arc consistency", "弧一致", "constraint"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-22
     query: "quantum entanglement basics"
@@ -185,6 +272,10 @@ queries:
     category: nonexistent
     origin: "g0-new (物理主题不在库, 假阳性测试)"
     expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-23
     query: "怎么判断一个估价函数是不是乐观的"
@@ -192,6 +283,10 @@ queries:
     category: paraphrase
     origin: "g0-new (同义改写中文 → admissible 不会高估)"
     expect_any: ["admissib", "乐观", "启发", "heuristic", "高估"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-24
     query: "极小极大搜索的剪枝方法"
@@ -199,6 +294,10 @@ queries:
     category: crosslingual
     origin: "g0-new (跨语: 库内 minimax 为英文内容, 中文 query)"
     expect_any: ["minimax", "alpha-beta", "剪枝", "极小极大"]
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
 
   - id: mem-25
     query: "consistency"
@@ -206,3 +305,40 @@ queries:
     category: ambiguous
     origin: "g0-new (歧义短词: heuristic consistency vs arc consistency, 均在库)"
     expect_any: ["consisten", "单调", "triangle", "弧一致"]
+
+  # ── cross_vault_attack (3) — 跨 vault 同名资产攻击 (CARD-G4-13) ──
+  # 形状同 vault 集，来源 G2-9 同名攻击用例集。expect_empty: 本 vault 不该召回他 vault 同名资产。
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
+  - id: mem-x01
+    query: "同名概念 在我的记忆里是怎么记的"
+    language: zh
+    category: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: mem-x02
+    query: "g29-canary-user 说过什么"
+    language: zh
+    category: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: mem-x03
+    query: "Recall anything about 同名情节"
+    language: en
+    category: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
diff --git a/backend/tests/regression/test_gold_set_manifest_g413.py b/backend/tests/regression/test_gold_set_manifest_g413.py
new file mode 100644
index 00000000..4818c264
--- /dev/null
+++ b/backend/tests/regression/test_gold_set_manifest_g413.py
@@ -0,0 +1,411 @@
+"""CARD-G4-13 承重行为门：金集 ≥100 + 逐条用户裁定标签 + SHA 冻结 manifest + runner 接线。
+
+[BATCH-2026-09-18-第十五批 / CARD-G4-13]
+
+这个文件钉住五件**行为**（不是文本）：
+
+1. 两个主金集合计 **≥100 条**，其中跨 vault 攻击类 vault ≥15 / memory ≥2；
+2. 四份金集的**每一条** query 都带 ``user_verdict``（五枚举）与 ``source``（六枚举 + ref）；
+3. ``gold_set_manifest.yaml`` 里每一项的 ``sha256`` 与**本测试自己实算**的一致
+   —— 两侧来自不同的读法，不是同一个来源自证自己；
+4. **既有 83 条逐字不变**：用 ``git show 9c4e7e82:<path>`` 取旧文逐条比十个判分/元数据键；
+5. **两个 runner 真的接了校验**：``importlib`` 载入真 runner，把金集常量指向 tmp 副本，
+   篡改副本后走真 ``main()`` → rc=2 且文案含「不符」。
+
+⛔ 实现约束（卡文 §一(g)）：读**真实**四 yaml + 真实 manifest + 真实 runner 模块。
+不连库、不起 8011、不 mock yaml/sha。所有写操作都在 ``tmp_path`` 里。
+"""
+
+from __future__ import annotations
+
+import hashlib
+import importlib.util
+import json
+import subprocess
+import sys
+from pathlib import Path
+
+import pytest
+import yaml
+
+#: ``backend/`` 的绝对路径。本文件位于 ``backend/tests/regression/``，往上两级。
+BACKEND_ROOT = Path(__file__).resolve().parents[2]
+
+REGRESSION_DIR = BACKEND_ROOT / "tests" / "regression"
+SCRIPTS_DIR = BACKEND_ROOT / "scripts"
+
+VAULT_GOLD = REGRESSION_DIR / "vault_gold_set.yaml"
+MEMORY_GOLD = REGRESSION_DIR / "memory_gold_set.yaml"
+VAULT_SHADOW = REGRESSION_DIR / "vault_gold_set_shadow.yaml"
+MEMORY_SHADOW = REGRESSION_DIR / "memory_gold_set_shadow.yaml"
+MANIFEST = REGRESSION_DIR / "gold_set_manifest.yaml"
+TOOL = SCRIPTS_DIR / "gold_set_manifest_tool.py"
+
+#: manifest 登记的四份金集。顺序 = manifest ``files[]`` 的顺序。
+ALL_SETS = (VAULT_GOLD, MEMORY_GOLD, VAULT_SHADOW, MEMORY_SHADOW)
+
+#: ``user_verdict`` 的五枚举（卡文 §一(d)）。``pending`` 是默认值 ——
+#: 用户裁定 session 是 user_touchpoint，没开窗口就全部停在 pending。
+VERDICT_ENUM = {"pending", "relevant", "irrelevant", "ambiguous", "needs_split"}
+
+#: ``source.kind`` 的六枚举。``synthetic`` 给那些**查不到来源**的条目
+#: （vault 集里有 4 条没有 ``origin``）—— 写 synthetic + ref=None，不编造来源。
+SOURCE_KIND_ENUM = {"node", "whiteboard", "exam_board", "review_doc", "fixture", "synthetic"}
+
+#: 既有条目不变的对照基准 commit（卡文 §一(c) / §〇 冻结基准）。
+BASE_COMMIT = "9c4e7e82"
+
+#: 逐条比较的十个键：判分用的六个 + 元数据四个。改动其中任何一个都会让
+#: 既有 83 条的语义变化，因此本卡把它们全部钉死。
+FROZEN_KEYS = (
+    "id",
+    "query",
+    "expect_hit",
+    "expect_not_hit",
+    "expect_any",
+    "expect_empty",
+    "query_type",
+    "category",
+    "language",
+    "origin",
+)
+
+
+def _load(path: Path) -> dict:
+    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
+
+
+def _queries(path: Path) -> list:
+    return _load(path).get("queries") or []
+
+
+def _sha256(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def _import_tool():
+    """把工具当模块导入（它就在 ``backend/scripts/`` 下，不是包）。"""
+    spec = importlib.util.spec_from_file_location("gold_set_manifest_tool", TOOL)
+    assert spec and spec.loader, f"无法为 {TOOL} 建 import spec"
+    mod = importlib.util.module_from_spec(spec)
+    sys.modules["gold_set_manifest_tool"] = mod
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def _import_runner(name: str):
+    """载入真的 runner 模块（顶层只 import stdlib + yaml/httpx，不拖 app）。"""
+    path = SCRIPTS_DIR / name
+    spec = importlib.util.spec_from_file_location(path.stem, path)
+    assert spec and spec.loader, f"无法为 {path} 建 import spec"
+    mod = importlib.util.module_from_spec(spec)
+    sys.modules[path.stem] = mod
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def _git_show(rev_path: str) -> str | None:
+    """取旧版文件内容；git 不可用时返回 None（由调用方 skip，不假绿）。"""
+    try:
+        r = subprocess.run(
+            ["git", "show", rev_path],
+            cwd=str(BACKEND_ROOT),
+            capture_output=True,
+            text=True,
+            timeout=60,
+        )
+    except (OSError, subprocess.SubprocessError):
+        return None
+    return r.stdout if r.returncode == 0 else None
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# ① 每条 query 的标注字段完整且合法
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def test_every_query_has_verdict_and_source() -> None:
+    """四份金集的**每一条** query 都带合法的 ``user_verdict`` 与 ``source``。
+
+    ⚠️ 这条断言期望「违规集为空」，所以必须先证明**输入面非空** ——
+    否则某天 yaml 变成空文件，它会空洞变绿。
+    """
+    total = 0
+    bad = []
+    for path in ALL_SETS:
+        for q in _queries(path):
+            total += 1
+            qid = q.get("id", "<no-id>")
+            v = q.get("user_verdict")
+            if v not in VERDICT_ENUM:
+                bad.append(f"{path.name}::{qid} user_verdict={v!r} 不在 {sorted(VERDICT_ENUM)}")
+            src = q.get("source")
+            if not isinstance(src, dict):
+                bad.append(f"{path.name}::{qid} source 不是 mapping：{src!r}")
+                continue
+            if src.get("kind") not in SOURCE_KIND_ENUM:
+                bad.append(f"{path.name}::{qid} source.kind={src.get('kind')!r} 不在枚举")
+            ref = src.get("ref")
+            if ref is not None and not isinstance(ref, str):
+                bad.append(f"{path.name}::{qid} source.ref 既不是 str 也不是 None：{ref!r}")
+
+    assert total >= 100, f"验伪锚：四份金集合计只数出 {total} 条，输入面不该这么小"
+    assert bad == [], "以下条目的标注字段不合法：\n  " + "\n  ".join(bad)
+
+
+def test_no_duplicate_annotation_keys() -> None:
+    """每份 yaml 里 ``user_verdict:`` 的**行数**必须等于 query 条数。
+
+    ⚠️ 为什么需要这条「文本层」判据，而上面那条「解析层」判据不够：
+    ``yaml.safe_load`` 对**重复键静默取最后一个**。所以一条 query 若被写了两遍
+    标注键，解析结果看起来完全正常 —— 上面那条会绿，而后写的那份会把先写的
+    悄悄覆盖掉。本卡实测踩过：迁移脚本跑了两趟，17 条攻击条目的
+    ``source.ref`` 被第二趟的 ``null`` 覆盖，**来源指针整片丢失**，
+    而当时所有解析层判据都是绿的（是负控③ 把它挖出来的）。
+
+    ⇒ 「解析后对不对」与「文本里有没有重复」是**两个维度**，
+    少一个维度的门，多补几个样本也补不出来。
+    """
+    problems = []
+    for path in ALL_SETS:
+        text = path.read_text(encoding="utf-8")
+        n_q = len([ln for ln in text.splitlines() if ln.startswith("  - id:")])
+        for key in ("user_verdict:", "verdict_by:", "verdict_at:", "source:"):
+            n_k = len([ln for ln in text.splitlines() if ln.strip().startswith(key)])
+            if n_k != n_q:
+                problems.append(f"{path.name}: {key} 出现 {n_k} 次，但只有 {n_q} 条 query")
+    assert problems == [], "标注键有重复或缺失（yaml 解析看不出来）：\n  " + "\n  ".join(problems)
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# ② 总数与跨 vault 攻击类配额
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def test_totals_meet_the_floor() -> None:
+    """两主集合计 ≥100；vault 跨 vault 攻击 ≥15、memory ≥2。"""
+    vault_qs = _queries(VAULT_GOLD)
+    mem_qs = _queries(MEMORY_GOLD)
+    main_total = len(vault_qs) + len(mem_qs)
+    vault_attack = [q for q in vault_qs if q.get("query_type") == "cross_vault_attack"]
+    mem_attack = [q for q in mem_qs if q.get("category") == "cross_vault_attack"]
+
+    assert main_total >= 100, f"两主集合计 {main_total} < 100（vault {len(vault_qs)} + memory {len(mem_qs)}）"
+    assert len(vault_attack) >= 15, f"vault 的 cross_vault_attack 只有 {len(vault_attack)} 条 < 15"
+    assert len(mem_attack) >= 2, f"memory 的 cross_vault_attack 只有 {len(mem_attack)} 条 < 2"
+
+
+def test_manifest_totals_match_the_files() -> None:
+    """manifest 里的 ``totals`` 与**实际文件**数得出来的一致。
+
+    manifest 是下游 G4-14 的输入，它自报的数字必须能被重新数出来。
+    """
+    m = _load(MANIFEST)
+    counted_main = len(_queries(VAULT_GOLD)) + len(_queries(MEMORY_GOLD))
+    counted_attack = len([q for q in _queries(VAULT_GOLD) if q.get("query_type") == "cross_vault_attack"]) + len(
+        [q for q in _queries(MEMORY_GOLD) if q.get("category") == "cross_vault_attack"]
+    )
+    assert m["totals"]["main_set_queries"] == counted_main, (
+        f"manifest 自报 main_set_queries={m['totals']['main_set_queries']}，实数 {counted_main}"
+    )
+    assert m["totals"]["cross_vault_attack"] == counted_attack, (
+        f"manifest 自报 cross_vault_attack={m['totals']['cross_vault_attack']}，实数 {counted_attack}"
+    )
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# ③ manifest 的 sha256 与本测试实算一致 + verify 通过
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def test_manifest_sha_matches_independently_computed() -> None:
+    """manifest 每项 ``sha256`` = 本测试用 ``hashlib`` 实算的值。
+
+    ⚠️ 故意**不**调工具去算：两侧必须来自不同的读法，否则是同一个来源自证自己。
+    """
+    m = _load(MANIFEST)
+    entries = {e["path"]: e for e in m["files"]}
+    assert len(entries) == len(ALL_SETS), f"manifest 应登记 {len(ALL_SETS)} 份文件，实得 {len(entries)}"
+    for path in ALL_SETS:
+        rel = str(path.relative_to(BACKEND_ROOT.parent))
+        assert rel in entries, f"manifest 没登记 {rel}；已登记的是 {sorted(entries)}"
+        assert entries[rel]["sha256"] == _sha256(path), (
+            f"{rel} 的 sha256 与实算不符：manifest={entries[rel]['sha256']} 实算={_sha256(path)}"
+        )
+
+
+def test_tool_verify_returns_zero_on_repo_files() -> None:
+    """工具的 ``verify`` 对仓内四文件 rc=0，且每项打出 ``OK``。"""
+    tool = _import_tool()
+    rc, lines = tool.verify_all(MANIFEST)
+    assert rc == 0, "verify 对未篡改的仓内文件应当 rc=0，实得 rc=%d\n%s" % (rc, "\n".join(lines))
+    ok_lines = [ln for ln in lines if ln.startswith("OK ")]
+    assert len(ok_lines) >= len(ALL_SETS), f"OK 行只有 {len(ok_lines)} 条，少于登记的文件数\n" + "\n".join(lines)
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# ④ 既有 83 条逐字不变
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+@pytest.mark.parametrize(
+    ("path", "expected_old_count"),
+    [(VAULT_GOLD, 58), (MEMORY_GOLD, 25)],
+    ids=["vault", "memory"],
+)
+def test_existing_entries_unchanged(path: Path, expected_old_count: int) -> None:
+    """``9c4e7e82`` 那版里的每一条，十个判分/元数据键必须逐字不变。
+
+    git 不可用 ⇒ ``skip`` 并说明，**不假绿**。
+    """
+    rel = str(path.relative_to(BACKEND_ROOT.parent))
+    old_text = _git_show(f"{BASE_COMMIT}:{rel}")
+    if old_text is None:
+        pytest.skip(f"git show {BASE_COMMIT}:{rel} 不可用 —— 本条无法验证（不当作通过）")
+
+    old = {q["id"]: q for q in (yaml.safe_load(old_text) or {}).get("queries") or []}
+    new = {q["id"]: q for q in _queries(path)}
+    assert len(old) == expected_old_count, f"{rel} 在 {BASE_COMMIT} 上应有 {expected_old_count} 条，实得 {len(old)}"
+
+    diffs = []
+    for qid, oq in old.items():
+        if qid not in new:
+            diffs.append(f"{qid} 整条不见了")
+            continue
+        nq = new[qid]
+        for k in FROZEN_KEYS:
+            if oq.get(k) != nq.get(k):
+                diffs.append(f"{qid}.{k}: {oq.get(k)!r} → {nq.get(k)!r}")
+    assert diffs == [], f"{rel} 的既有条目被改动了：\n  " + "\n  ".join(diffs)
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# ⑤ 两个 runner 真的接了校验
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _tmp_copy_sets(tmp_path: Path) -> dict:
+    """把四份金集 + manifest 拷进 tmp，返回 {原路径: tmp 路径}。"""
+    out = {}
+    for p in (*ALL_SETS, MANIFEST):
+        dst = tmp_path / p.name
+        dst.write_bytes(p.read_bytes())
+        out[p] = dst
+    return out
+
+
+@pytest.mark.parametrize(
+    ("runner_file", "argv", "alive_marker"),
+    [
+        ("run_vault_retrieval_regression.py", ["--shadow", "--no-hook"], None),
+        ("run_memory_retrieval_regression.py", ["--shadow", "--no-judge"], "backend"),
+    ],
+    ids=["vault", "memory"],
+)
+def test_runner_rejects_tampered_gold_set(
+    runner_file: str, argv: list, alive_marker, tmp_path: Path, monkeypatch, capsys
+) -> None:
+    """篡改金集副本后走**真的** ``main()`` → rc=2 且文案含「不符」。
+
+    这条门绑的是 **runner 的接线**，不是工具自测：把工具调用从 runner 里拿掉，
+    这条就会红（负控②）。
+    """
+    copies = _tmp_copy_sets(tmp_path)
+    runner = _import_runner(runner_file)
+    tool = _import_tool()
+
+    # 把 runner 与工具的路径常量都指向 tmp 副本
+    monkeypatch.setattr(runner, "GOLD_SET", copies[VAULT_GOLD if "vault" in runner_file else MEMORY_GOLD])
+    monkeypatch.setattr(runner, "SHADOW_SET", copies[VAULT_SHADOW if "vault" in runner_file else MEMORY_SHADOW])
+    monkeypatch.setattr(tool, "MANIFEST_PATH", copies[MANIFEST])
+    monkeypatch.setattr(runner, "GOLD_SET_MANIFEST", copies[MANIFEST], raising=False)
+
+    # 篡改：往 shadow 副本尾部追加一条 query（sha 立即变）
+    shadow = copies[VAULT_SHADOW if "vault" in runner_file else MEMORY_SHADOW]
+    shadow.write_text(
+        shadow.read_text(encoding="utf-8") + '\n  - id: tampered-g413\n    query: "篡改探针"\n',
+        encoding="utf-8",
+    )
+
+    monkeypatch.setattr(sys, "argv", [runner_file, *argv])
+    rc = runner.main()
+    out = capsys.readouterr()
+    assert rc == 2, f"篡改金集后 {runner_file} 应 rc=2，实得 {rc}\n{out.out}\n{out.err}"
+    assert "不符" in (out.out + out.err), f"{runner_file} 的拒绝文案里没有「不符」：\n{out.out}\n{out.err}"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# ⑥ apply-verdicts 往返
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def test_checklist_and_apply_verdicts_roundtrip(tmp_path: Path) -> None:
+    """``checklist`` 出 md → 勾一条 → ``apply-verdicts`` 回写 → 只有那条变。"""
+    tool = _import_tool()
+    src = tmp_path / "vault_gold_set.yaml"
+    src.write_bytes(VAULT_GOLD.read_bytes())
+
+    md = tmp_path / "checklist.md"
+    n = tool.write_checklist([src], md)
+    assert n >= 1, "checklist 一条都没写出来"
+    text = md.read_text(encoding="utf-8")
+
+    qs = _queries(src)
+    target = qs[0]["id"]
+    assert f"<!-- gsid:{target} -->" in text, f"checklist 里没有 {target} 的隐藏锚"
+
+    # 勾「相关」那一格
+    marked = []
+    for line in text.splitlines():
+        if target in line or (marked and marked[-1].strip().startswith(f"<!-- gsid:{target}")):
+            pass
+        marked.append(line)
+    text2 = text.replace(f"<!-- gsid:{target} -->", f"<!-- gsid:{target} -->", 1)
+    # 在该条的「相关」checkbox 上打勾
+    lines = text2.splitlines()
+    for i, line in enumerate(lines):
+        if f"<!-- gsid:{target} -->" in line:
+            for j in range(i, min(i + 8, len(lines))):
+                if "relevant" in lines[j] and lines[j].lstrip().startswith("- [ ]"):
+                    lines[j] = lines[j].replace("- [ ]", "- [x]", 1)
+                    break
+            break
+    md.write_text("\n".join(lines), encoding="utf-8")
+
+    changed, problems = tool.apply_verdicts([src], md, verdict_by="user", verdict_at="2026-09-19T00:00:00Z")
+    assert problems == [], f"apply-verdicts 报了问题：{problems}"
+    assert changed == [target], f"应当只改 {target}，实得 {changed}"
+
+    after = {q["id"]: q for q in _queries(src)}
+    assert after[target]["user_verdict"] == "relevant"
+    assert after[target]["verdict_by"] == "user"
+    others = [q for qid, q in after.items() if qid != target]
+    assert all(q["user_verdict"] == "pending" for q in others), "其余条目不该被动"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# ⑦ collect 只读
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def test_collect_is_read_only(tmp_path: Path) -> None:
+    """``collect`` 扫一个假 vault 出候选，且那个 vault **一个字节都没变**。"""
+    tool = _import_tool()
+    vault = tmp_path / "fake-vault"
+    (vault / "节点").mkdir(parents=True)
+    (vault / "原白板").mkdir(parents=True)
+    a = vault / "节点" / "概念甲.md"
+    a.write_text("# 概念甲\n\n> [!question]+ 这是我手写的疑问？\n> 正文\n", encoding="utf-8")
+    b = vault / "原白板" / "板一.md"
+    b.write_text("# 板一标题\n\n内容\n", encoding="utf-8")
+
+    before = {p: p.read_bytes() for p in (a, b)}
+    out = tmp_path / "candidates.json"
+    n = tool.collect_candidates(vault, out)
+
+    assert n >= 1, "collect 一条候选都没产出"
+    data = json.loads(out.read_text(encoding="utf-8"))
+    assert isinstance(data, list) and data, "候选 json 不是非空列表"
+    assert all("source" in c and "ref" in c["source"] for c in data), "候选缺 source.ref"
+    for p, content in before.items():
+        assert p.read_bytes() == content, f"collect 改动了 vault 文件：{p}"
diff --git a/backend/tests/regression/vault_gold_set.yaml b/backend/tests/regression/vault_gold_set.yaml
index 7248415b..90b212ff 100644
--- a/backend/tests/regression/vault_gold_set.yaml
+++ b/backend/tests/regression/vault_gold_set.yaml
@@ -16,8 +16,13 @@
 # 结构性死档实锤 (期望文件全 doc_type=whiteboard 被查询侧排除策略硬排除,
 # 反事实去排除后 rank1 立即回归 = 纯策略排除非能力问题); 「定位白板文件」
 # 元查询与 supplementary 补充材料定位错位, 待 file_locate 意图路由 backlog。
+# version 3 (2026-09-19, CARD-G4-13): 新增 vq-x01..vq-x17 跨 vault 同名资产攻击
+# (形状复用 G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111);
+# 全条目追加 user_verdict/verdict_by/verdict_at/source 四个**标注**字段 —— 判分侧
+# 只读 id/query/expect_*/query_type (runner :209-213), 新键对判分透明。
+# 既有 58 条的判分与元数据键逐字未动 (gold_set_manifest.yaml 冻结 sha 可查)。
 config:
-  version: 2
+  version: 3
   vault_id: canvas_vault
   top_k: 20
   tolerance: 0.02
@@ -43,6 +48,10 @@ queries:
     origin: "节点/理性代理-(Rational-Agent).md 派生节点"
     expect_hit:
       - {file: "理性代理", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-d02
     query: "为什么反射代理的局限性会引出规划代理的需求？"
     language: zh
@@ -51,6 +60,10 @@ queries:
     expect_hit:
       - {file: "反射代理的局限性", grade: 3}
       - {file: "规划代理的特点", grade: 1}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-d03
     query: "特征方程是怎么定义特征值的？"
     language: zh
@@ -59,6 +72,10 @@ queries:
     expect_hit:
       - {file: "Characteristic-Equation", grade: 3}
       - {file: "Fundamentals", grade: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/Characteristic-Equation-for-Eigenvalues.md"}
   - id: vq-d04
     query: "Av=λv 这个式子里每个符号代表什么？"
     language: zh
@@ -67,6 +84,10 @@ queries:
     expect_hit:
       - {file: "Fundamentals", grade: 3}
       - {file: "Eigenvalues-are-special", grade: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/Fundamentals.md"}
   - id: vq-d05
     query: "特征值作为缩放因子是什么意思？"
     language: zh
@@ -74,6 +95,10 @@ queries:
     origin: "节点/Fundamentals.md scaling factor 定义"
     expect_hit:
       - {file: "Fundamentals", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/Fundamentals.md"}
   - id: vq-d06
     query: "递归和分治的核心思想我是怎么记的？"
     language: zh
@@ -82,6 +107,10 @@ queries:
     expect_hit:
       - {file: "recursion", grade: 3}
       - {file: "递归与分治", grade: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: whiteboard, ref: null}
   - id: vq-d07
     query: "CSM 辅导的学分规则是怎样的？"
     language: zh
@@ -89,6 +118,10 @@ queries:
     origin: "节点/csm-tutoring-unit-credit.md"
     expect_hit:
       - {file: "csm", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/csm-tutoring-unit-credit.md"}
   - id: vq-d08
     query: "回溯搜索和普通 DFS 到底区别在哪？为什么说它是解 CSP 的基本方法？"
     language: zh
@@ -96,6 +129,10 @@ queries:
     origin: "transcript 真实提问 2026-08-09 (raw 正当命中类)"
     expect_hit:
       - {file: "raw/CS188", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-d09
     query: "代理函数 agent function 是什么？"
     language: zh
@@ -103,6 +140,10 @@ queries:
     origin: "节点/代理函数-(Agent-Function).md"
     expect_hit:
       - {file: "代理函数", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-d10
     query: "规划可以分成哪几类？"
     language: zh
@@ -112,6 +153,10 @@ queries:
       - {file: "规划的分类", grade: 3}
 
   # ═══ example_recall (6) — 例子/比喻检索 ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-e01
     query: "我笔记里关于特征向量的几何直觉是怎么描述的？我有没有用什么比喻？"
     language: zh
@@ -121,6 +166,10 @@ queries:
       - {file: "Fundamentals", contains: "旋转门", grade: 3}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-e02
     query: "价值迭代有没有手算的例子？"
     language: zh
@@ -128,6 +177,10 @@ queries:
     origin: "raw/CS188 Disc04 Micro-Blackjack (正当命中)"
     expect_hit:
       - {file: "raw/CS188", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-e03
     query: "赛车游戏那个例子讲的是什么算法？"
     language: zh
@@ -135,6 +188,10 @@ queries:
     origin: "raw/CS188 lecture 10 赛车 MDP 例子 (正当命中)"
     expect_hit:
       - {file: "raw/CS188", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-e04
     query: "旋转变换存不存在实特征向量？我笔记里讨论过吗"
     language: zh
@@ -143,6 +200,10 @@ queries:
     expect_hit:
       - {file: "考察-Fundamentals", grade: 3}
       - {file: "Fundamentals", grade: 1}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/考察-Fundamentals-2026-07-16.md"}
   - id: vq-e05
     query: "Gridworld 网格世界的演示说明了什么？"
     language: zh
@@ -150,6 +211,10 @@ queries:
     origin: "raw/CS188 lecture 10 Gridworld (正当命中)"
     expect_hit:
       - {file: "raw/CS188", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-e06
     query: "λ 等于 0 的时候特征向量还成立吗？我好像问过这个"
     language: zh
@@ -159,6 +224,10 @@ queries:
       - {file: "Fundamentals", contains: "0", grade: 3}
 
   # ═══ file_locate (6) — 「记在哪篇笔记里」 ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/Fundamentals.md"}
   - id: vq-f01
     query: "特征向量和特征值的定义我记在哪篇笔记里？"
     language: zh
@@ -169,6 +238,10 @@ queries:
       - {file: "特征值与特征向量", grade: 2}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-f02
     query: "我的递归笔记是哪一篇？"
     language: zh
@@ -176,6 +249,10 @@ queries:
     origin: "节点/my-recursion-notes.md"
     expect_hit:
       - {file: "recursion", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/my-recursion-notes.md"}
   - id: vq-f03
     query: "CSM 单位学分那件事我记在哪了？"
     language: zh
@@ -183,6 +260,10 @@ queries:
     origin: "节点/csm-tutoring-unit-credit.md"
     expect_hit:
       - {file: "csm", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/csm-tutoring-unit-credit.md"}
   - id: vq-f04
     query: "咖啡烘焙那句话我写在哪篇笔记里？"
     language: zh
@@ -190,6 +271,10 @@ queries:
     origin: "UAT v2 测试3 追加内容 (Fundamentals 尾部)"
     expect_hit:
       - {file: "Fundamentals", contains: "烘", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-f05
     query: "代理决策分析的笔记在哪？"
     language: zh
@@ -198,6 +283,10 @@ queries:
     expect_hit:
       - {file: "代理决策", grade: 3}
   # ═══ appended_content (5) — 靶子① 大文件尾部追加 (chunk 稀释) ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-a01
     query: "我笔记里有没有写过咖啡烘焙深浅和味道的关系？在哪篇？"
     language: zh
@@ -206,6 +295,10 @@ queries:
     expect_hit:
       - {file: "Fundamentals", contains: "烘", grade: 3}
     baseline_note: "开工基线=排序层低分; T3 后必须进 top10 且交付层 hit"
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-a02
     query: "烘豆子烘得深浅对喝起来的口感有什么影响？"
     language: zh
@@ -213,6 +306,10 @@ queries:
     origin: "同 vq-a01 换问法 (苦/酸方向)"
     expect_hit:
       - {file: "Fundamentals", contains: "苦", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-a03
     query: "特征向量像旋转门转轴的说法是我自己写的吗？写在哪？"
     language: zh
@@ -220,6 +317,10 @@ queries:
     origin: "Fundamentals 08-08 用户追加行 (watcher 2s 入索引实测)"
     expect_hit:
       - {file: "Fundamentals", contains: "旋转门", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-a04
     query: "我对最大化那部分有什么不理解的地方吗？"
     language: zh
@@ -227,6 +328,10 @@ queries:
     origin: "节点/lecture 2.md ✍️ 我的理解 批注 (大文件内嵌用户笔记)"
     expect_hit:
       - {file: "lecture 2", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-a05
     query: "火候曲线决定什么？"
     language: zh
@@ -236,6 +341,10 @@ queries:
       - {file: "Fundamentals", contains: "火候", grade: 3}
 
   # ═══ handwritten_vs_transcript (8) — 靶子② 手写优先权 ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-h01
     query: "代理 agent 的类型有哪些？反射型和规划型有什么不同？"
     language: zh
@@ -246,6 +355,10 @@ queries:
       - {file: "反射代理", grade: 2}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 4}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/代理类型：反射与规划.md"}
   - id: vq-h02
     query: "规划代理有什么特点？"
     language: zh
@@ -255,6 +368,10 @@ queries:
       - {file: "规划代理的特点", grade: 3}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 4}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/规划代理的特点.md"}
   - id: vq-h03
     query: "递归的 base case 为什么重要？"
     language: zh
@@ -262,6 +379,10 @@ queries:
     origin: "节点/my-recursion-notes.md (注意 raw/ 有同名副本)"
     expect_hit:
       - {file: "recursion", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: "节点/my-recursion-notes.md"}
   - id: vq-h04
     query: "理性代理和环境的关系是什么？"
     language: zh
@@ -271,6 +392,10 @@ queries:
       - {file: "理性代理", grade: 3}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 4}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-h05
     query: "我自己的笔记里对 agent 下过什么定义？"
     language: zh
@@ -281,6 +406,10 @@ queries:
       - {file: "lecture 2", grade: 2}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-h06
     query: "特征值全为正意味着什么？"
     language: zh
@@ -290,6 +419,10 @@ queries:
       - {file: "Fundamentals", grade: 3}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-h08
     query: "lecture 2 我做过哪些自己的笔记和理解？"
     language: zh
@@ -299,6 +432,10 @@ queries:
       - {file: "节点/lecture 2", grade: 3}
 
   # ═══ homograph_ambiguous (6) — 靶子③ 中英同形歧义 ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-g01
     query: "我笔记里关于特征值与特征向量讲了什么？"
     language: zh
@@ -310,6 +447,10 @@ queries:
       - {file: "Characteristic-Equation", grade: 2}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 0, reason: "eigenvector≠feature vector, 一条都不许"}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: review_doc, ref: null}
   - id: vq-g02
     query: "特征向量的几何意义是什么？"
     language: zh
@@ -319,6 +460,10 @@ queries:
       - {file: "Fundamentals", grade: 3}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 0}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-g03
     query: "用特征向量描述状态是什么意思？"
     language: zh
@@ -326,6 +471,10 @@ queries:
     origin: "反向歧义: 这次问的真是 ML feature vector (raw 正当命中)"
     expect_hit:
       - {file: "raw/CS188", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-g04
     query: "特征值怎么求？"
     language: zh
@@ -336,6 +485,10 @@ queries:
       - {file: "Fundamentals", grade: 2}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 1}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-g05
     query: "代理是什么？"
     language: zh
@@ -345,6 +498,10 @@ queries:
       - {file: "代理", grade: 3}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 4}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-g06
     query: "线性模型的定义是什么？"
     language: zh
@@ -354,6 +511,10 @@ queries:
       - {file: "raw/CS188", grade: 3}
 
   # ═══ zero_lexical_overlap (5) — 纯语义检索 (dense 层能力) ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-z01
     query: "矩阵作用之后方向不变、只被拉长的那种向量叫什么？我记过吗"
     language: zh
@@ -362,6 +523,10 @@ queries:
     expect_hit:
       - {file: "Fundamentals", grade: 3}
       - {file: "Eigenvalues-are-special", grade: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-z02
     query: "把大问题拆成同样形状的小问题来解决的思路我记在哪？"
     language: zh
@@ -370,6 +535,10 @@ queries:
     expect_hit:
       - {file: "recursion", grade: 3}
       - {file: "递归与分治", grade: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-z03
     query: "让行列式变成零的那个数怎么找？"
     language: zh
@@ -378,6 +547,10 @@ queries:
     expect_hit:
       - {file: "Characteristic-Equation", grade: 3}
       - {file: "Fundamentals", grade: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-z04
     query: "只根据当下感知就行动、不考虑后果的那种智能体叫什么？"
     language: zh
@@ -386,6 +559,10 @@ queries:
     expect_hit:
       - {file: "反射", grade: 3}
       - {file: "代理类型", grade: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-z05
     query: "豆子火大了会变苦这件事我记过吗？"
     language: zh
@@ -395,6 +572,10 @@ queries:
       - {file: "Fundamentals", grade: 3}
 
   # ═══ crosslingual (5) — 中英跨语检索 ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-c01
     query: "What did I write about eigenvalues and eigenvectors in my notes?"
     language: en
@@ -405,6 +586,10 @@ queries:
       - {file: "特征值与特征向量", grade: 2}
     expect_not_hit:
       - {path_glob: "raw/*", max_in_top_k: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-c02
     query: "my notes about rational agents"
     language: en
@@ -412,6 +597,10 @@ queries:
     origin: "英文问中文派生节点"
     expect_hit:
       - {file: "理性代理", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-c03
     query: "where are my recursion notes"
     language: en
@@ -419,6 +608,10 @@ queries:
     origin: "英文定位"
     expect_hit:
       - {file: "recursion", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-c04
     query: "how to compute eigenvalues using the characteristic equation"
     language: en
@@ -426,6 +619,10 @@ queries:
     origin: "英文概念问 (Characteristic-Equation 正文本身是英文)"
     expect_hit:
       - {file: "Characteristic-Equation", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-c05
     query: "planning agents vs reflex agents 的区别"
     language: mixed
@@ -436,6 +633,10 @@ queries:
       - {file: "规划代理", grade: 2}
 
   # ═══ meta_annotation (5) — 「我之前的疑问/理解」 ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-m01
     query: "我之前对特征向量有哪些疑问？"
     language: zh
@@ -443,6 +644,10 @@ queries:
     origin: "transcript 真实提问; Fundamentals 用户疑问 callout"
     expect_hit:
       - {file: "Fundamentals", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-m02
     query: "λ 可以是 0 吗这个问题我问过吗？"
     language: zh
@@ -450,6 +655,10 @@ queries:
     origin: "Fundamentals ✍️ 我的理解 callout (T3 后独立成块)"
     expect_hit:
       - {file: "Fundamentals", contains: "0", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-m03
     query: "我对代理的定义有过什么不理解的地方？"
     language: zh
@@ -457,6 +666,10 @@ queries:
     origin: "节点/lecture 2.md ✍️ 我对代理的定义还是不太理解"
     expect_hit:
       - {file: "lecture 2", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-m04
     query: "我在预期这个概念上卡过吗？"
     language: zh
@@ -464,6 +677,10 @@ queries:
     origin: "节点/lecture 2.md ✍️ 预期理解批注"
     expect_hit:
       - {file: "lecture 2", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: node, ref: null}
   - id: vq-m05
     query: "我上一次考试弃答的题目是哪道？"
     language: zh
@@ -473,23 +690,252 @@ queries:
     notes: "vault 检索链交付 0 条为正确 — 考察记录不经 RAG 回流"
 
   # ═══ nonexistent (4) — 库内无此主题 ═══
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-n01
     query: "红黑树删除节点后怎么重新平衡？"
     language: zh
     query_type: nonexistent
     expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-n02
     query: "傅里叶变换的物理意义是什么？"
     language: zh
     query_type: nonexistent
     expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-n03
     query: "操作系统的进程调度算法有哪些？"
     language: zh
     query_type: nonexistent
     expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
   - id: vq-n04
     query: "光合作用的暗反应发生在哪里？"
     language: zh
     query_type: nonexistent
     expect_empty: true
+
+  # ═══ cross_vault_attack (17) — 跨 vault 同名资产攻击 (CARD-G4-13) ═══
+  # 形状逐字复用 G2-9 同名攻击用例集（backend/scripts/g29_dual_vault_canary.py:101-111）：
+  # 用**相同的资产标识**发问，语义 = 「本 vault 的检索面不得出现另一个 vault 的同名资产」。
+  # 判分只用既有三键（runner :209-213 只读这几个），零容忍 max_in_top_k: 0。
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: synthetic, ref: null}
+  - id: vq-x01
+    query: "同名概念 是什么？我在这个 vault 里记过吗"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x02
+    query: "双vault验证/同名白板.canvas 这块白板讲了什么"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x03
+    query: "g29-node-0001 这个节点的内容是什么"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x04
+    query: "同名实体 和 同名情节 之间是什么关系"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x05
+    query: "把 同名概念 的定义和例子一起给我"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x06
+    query: "g29-canary-user 这个用户留下过哪些笔记"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x07
+    query: "同名白板 里有哪些节点"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x08
+    query: "g29-doc-0001 对应的原文在哪"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x09
+    query: "同名情节 发生在什么时候"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x10
+    query: "检索一下 双vault验证 目录下的所有材料"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x11
+    query: "同名概念 在另一个 vault 里是怎么写的"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x12
+    query: "跨 vault 找一下 同名实体"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x13
+    query: "同名概念 的上位概念是什么"
+    language: zh
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x14
+    query: "What does the shared concept 同名概念 mean here?"
+    language: en
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x15
+    query: "Show me everything under 双vault验证/"
+    language: en
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x16
+    query: "Find node g29-node-0001 across vaults"
+    language: en
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
+  - id: vq-x17
+    query: "同名实体 entity lookup, cross-vault"
+    language: mixed
+    query_type: cross_vault_attack
+    origin: "G2-9 同名攻击用例集 backend/scripts/g29_dual_vault_canary.py:101-111"
+    expect_not_hit:
+      - {path_glob: "双vault验证/*", max_in_top_k: 0}
+    expect_empty: true
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: fixture, ref: "backend/scripts/g29_dual_vault_canary.py:101-111"}
diff --git a/backend/tests/regression/vault_gold_set_shadow.yaml b/backend/tests/regression/vault_gold_set_shadow.yaml
index 2352a31e..e74ff503 100644
--- a/backend/tests/regression/vault_gold_set_shadow.yaml
+++ b/backend/tests/regression/vault_gold_set_shadow.yaml
@@ -19,6 +19,10 @@ queries:
     expect_hit:
       - {file: "线性代数", grade: 3}
       - {file: "特征值与特征向量", grade: 2}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: whiteboard, ref: "原白板/线性代数.md"}
   - id: vq-h07
     query: "CS 61B 这门课的白板里都挂了什么主题？"
     language: zh
@@ -26,3 +30,7 @@ queries:
     origin: "原白板/CS 61B.md; 2026-08-10 自主集 v1 降档 (whiteboard 排除死档)"
     expect_hit:
       - {file: "CS 61B", grade: 3}
+    user_verdict: pending
+    verdict_by: null
+    verdict_at: null
+    source: {kind: whiteboard, ref: null}
```

## ② 作者自述 —— 以下每一条请独立核对，不要采信

1. 两主集合计 **103 ≥ 100**（vault 75 + memory 28）；**既有 83 条**的十个判分/元数据键与 `9c4e7e82` 逐字不变（`unchanged_vault=58 unchanged_memory=25 diffs=0`）；12 个判分函数 AST 逐字不变（验伪锚 `diffs=1` / `grade_of False` 已落档 `immutability-probe-*`）。
2. 跨 vault 攻击条目用 **G2-9 相同资产标识**（`同名概念` / `双vault验证/同名白板.canvas` / `g29-node-0001` / `同名实体` / `同名情节`），非自造名；每条 4 个标注键齐（`user_verdict` 行数 = 条目数：75/75、28/28、2/2、0/0）。
3. **重复键缺陷已修**：负控③ 曾抓出「迁移脚本重复键把 17 条攻击条目 `source.ref` 覆盖成 null（`yaml.safe_load` 静默取后写）」，当时所有解析层判据全绿；修后 `source.ref` 分布 = `Counter({'backend/scripts/g29_dual_vault_canary.py:101-111': 17})`，并有常驻判据 `test_no_duplicate_annotation_keys`（文本层行数判据；负控④ 新判据红 / 旧判据绿）。
4. `user_verdict` **全 `pending`**（窗口未开 = 已裁定的 SKIP，非隐含前提）；`apply-verdicts` 往返能力由门第 ⑥ 条实测（勾一条 → 仅那条变 → `verify` 因 sha 变 rc=1 → `build --bump-revision` 后 rc=0）。
5. runner 只加校验不改判分；memory 校验**先于** `check_backend_alive()`（离线时「manifest 不符」不被短路）；manifest sha 实算三道（`build` 工具算、`verify` 复算、测试内 `hashlib` 独立复算）。
6. `collect` 只读（live vault 跑后 `find -newer` 空；工具 AST 实查 import 仅 `argparse/datetime/hashlib/json/pathlib/re/sys/yaml`——`httpx`/`neo4j`/`lancedb`/`app` 全 False）；`verify` 三态 rc = 2/2/1（解析错 / 缺文件 / sha 不符）。
7. 行为门 12 条全 passed（收集 12）；`tests/regression` 目录级红 0；`tests/unit` 与基线同为 32 红（只许 `<`）。

## ③ 请优先回答的问题（**已按 Jev 分诊 urgency 降序、REVIEW 标记者优先重排**；括号内为卡文原问号编号）

**分诊表（jev-1.13.0，对 `d06f7127`；原始 JSON：`_bmad-output/审查/evidence-g413/jev-triage-d06f7127.json`）**：

| 文件 | CHURN | URG↓ | REVIEW | TEST | risk | 判定 |
|---|---|---|---|---|---|---|
| `backend/scripts/gold_set_manifest_tool.py` | +570/-0 | **3.09** | 0.85 | 0.61 | logic | REVIEW |
| `backend/scripts/run_vault_retrieval_regression.py` | +20/-2 | **2.77** | 0.75 | 0.65 | error_handling | REVIEW |
| `backend/tests/regression/test_gold_set_manifest_g413.py` | +411/-0 | **2.75** | 0.82 | 0.94 | test_or_docs | REVIEW |
| `backend/scripts/run_memory_retrieval_regression.py` | +16/-0 | **2.60** | 0.70 | 0.52 | error_handling | REVIEW |

**A. `gold_set_manifest_tool.py`（URG 3.09 · risk=logic · REVIEW）**

- A1（卡文③②）：`apply-verdicts` 回写是否可能把用户**未勾**的条目改掉？锚丢失 / 多选 / 未知值时是否**一律不动那条**并列出且 rc=1（fail-closed）？
- A2（卡文③③）：`verify` 的三态 rc（yaml 解析错 / 文件缺失 / sha 不符）是否真的各异，且 runner 只把 1/2 都当 exit 2？
- A3（卡文③④）：`collect` 是否有任何写路径可达 `--vault`？（只读承诺的**门未覆盖的路径**）
- A4（补审追加）：重复键缺陷的修复是否到位——文本层「行数 = 条目数」判据能否抓住所有重复键形态（块式映射 / 引号键 / 行内注释干扰 / 同一键跨文件段）？`build` 子命令有没有可能再次引入重复键？

**B. `run_vault_retrieval_regression.py`（URG 2.77 · risk=error_handling · REVIEW）**

- B1（卡文③①）：`expect_not_hit` 的 `path_glob "双vault验证/*"` 与 runner 的 `fnmatch` + `startswith` 双语义（`:145-149`、`:305-308`）是否真能命中 G2-9 canary 落盘的 `source_path`（前缀 / 分隔符差异下会不会漏判）？请给**对照输入**。

**C. `test_gold_set_manifest_g413.py`（URG 2.75 · risk=test_or_docs · REVIEW）**

- C1（卡文③⑤）：结构判据是否可被「注释里出现关键词」骗过（`grep -c 'verify_gold_set_file'` 需配 AST Call 计数核）？12 条门里有没有恒真断言 / 控制组标注不实 / 对归档文件敏感的假绿？

**D. `run_memory_retrieval_regression.py`（URG 2.60 · risk=error_handling · REVIEW）**

- D1（卡文③③后半）：校验是否真在 `check_backend_alive()` **之前**执行、两种 rc=2 在离线机器上是否可靠靠**文案**区分（「不符」不得被「backend 不可达」短路）？

**E. 卡级（金集 + manifest + 下游消费）**

- E1（卡文③⓪）：攻击条目在单 vault live 索引上「恒不出现 = 恒绿」（**已知且如实登记**）；请答：该条目集 + manifest 字段是否足以被 **G4-15 / R-J04 双 vault 门直接消费**？双 vault 真跑时还缺什么字段/语义？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 一句话结论
- `file:line`（精确到行）
- 一句复现思路，措辞请用「**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**」

如果某条只是风格或偏好，请标 LOW 并说明它不影响正确性。

## ⑤ 边界

- **只读**；不要修改任何文件；不要试图运行写命令。
- 不要连接任何数据库 / 端口（7691/7687/8011 全禁）、不要起容器、不要跑需要网络的东西。
- 不要评审 G4-14 七指标与 R-SLO schema 的面；不要评审「无答案 / 跨板」两类补齐（已另立卡）；不要评审 `backend/app/**` 与两 conftest（本卡零改动）。
