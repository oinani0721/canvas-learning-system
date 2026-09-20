# 独立复核请求 — CARD-G4-13 · **round-2（H-1/H-2 整改复核；codex+zai GLM-5.3）**

> **本轮性质**：zcode 补审 r1（绑 `d06f7127`）报 **B0 / H2 / M3 / L6**，主 session 裁定「整改」。本轮 = **整改后的第 2 轮**：核 H-1/H-2 是否真修掉、修复有没有引入新问题。**M-1/M-2/M-3 与 L-1~L-6 只登记不改**（已写进 UAT），不在本轮整改面——若你认为其中哪条实际是 HIGH 级，请按 ④ 格式给出并说明升级理由。
>
> **审查绑定 = `2e0642aa`**（本卡修复 commit；只动两文件 + `_bmad-output` 证据）。PREV（修复前）= `18f31c44`（r1 存档 commit）。自证（车道预跑，非你执行）：`git --no-pager diff --stat --no-color 2e0642aa HEAD -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py` = **空**（HEAD == 2e0642aa）。
> **读取面 = cwd（车道树工作树）**。⛔ 只读；⛔ 不要改任何文件。
> **r1 两条 HIGH 的完整原文**在读取面里：`_bmad-output/审查/zcode-review-CARD-G4-13-r1.md`（`--json` 原文）· 可读拷贝 `_bmad-output/审查/evidence-g413/zcode-r1-review-response-20260919T233343.md`。

## ① 背景与最小读取面（⛔ 只读这些）

**r1 → r2 变更面（两文件；内嵌 diff 见 §① 末）**：

- `backend/scripts/gold_set_manifest_tool.py`：**只动 `verify_gold_set_file` 一段（`:278-317`）** —— 环境/输入错改走 `(False, 文案)`：① `yaml.YAMLError`（try/except）② 顶层非映射（`isinstance(m, dict)`）③ 已登记文件缺失（`sha256_of` 前 `exists`）④ 条目 `sha256` 非法（`isinstance(want_sha, str)`）。口径声明「对齐 `verify_all`（`:207-260`）」（r1 H-1）。
- `backend/tests/regression/test_gold_set_manifest_g413.py`：门⑤（`:329`）重构 + 新增 ⑧ 段（`:450-542`）+ helpers（`_flip_first_char` `:294` / `_tampered_manifest_copy` `:299`）+ 模块 docstring 第 5/6 条（r1 H-2/H-1 整改说明）。

**请读（最小面写死；均在 cwd 内）**：

- **内嵌 diff（本 §① 末）**：`git --no-pager diff --no-color 18f31c44 2e0642aa -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`（**264 行，先读它**）
- `backend/scripts/gold_set_manifest_tool.py`：`verify_gold_set_file` 全段（`:278-317`）+ `verify_all`（`:207-260`，对照口径）+ `rel_to_repo`（`:91-104`，契约声明「fail-closed 边界必须不崩」）+ `load_yaml`（`:79`）/ `sha256_of`（`:87`）
- `backend/tests/regression/test_gold_set_manifest_g413.py`：helpers（`:294-314`）+ ⑤ 全段（`:329-374`）+ ⑧ 全段（`:450-542`）+ 模块 docstring（`:1-30`）
- r1 评审全文：`_bmad-output/审查/zcode-review-CARD-G4-13-r1.md`；可读拷贝 `_bmad-output/审查/evidence-g413/zcode-r1-review-response-20260919T233343.md`（H-1 / H-2 定义与建议修法）
- r2 证据（**全名**，均在 `_bmad-output/审查/evidence-g413/`）：`negctl-r2-h2-oldpath-20260919T235337.txt`（旧路径探针：old=「在仓外」早退 / new=sha 比较）· `negctl-r2-h1-red-20260919T235527.txt`（先红：3 failed）· `gate-r2-green-20260919T235648.txt`（后绿：15 passed）· `named-r2-20260919T235713.txt`（37 passed）· `regression-r2-20260919T235713.txt`（1928 passed 红 0）· `unit-r2-20260920T000654.txt`（32 红 == close）· `jev-triage-2e0642aa.json`（分诊原始 JSON）
- UAT 上下文：`_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md`（§〇 / §三.1）· `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19-裁定清单.md`（文末 r1 补审节）

**内嵌 diff（原文，`18f31c44 → 2e0642aa`，两文件）：**

```diff
diff --git a/backend/scripts/gold_set_manifest_tool.py b/backend/scripts/gold_set_manifest_tool.py
index d57ce439..d15b1755 100644
--- a/backend/scripts/gold_set_manifest_tool.py
+++ b/backend/scripts/gold_set_manifest_tool.py
@@ -279,21 +279,35 @@ def verify_gold_set_file(path: Path, manifest_path: Path | None = None) -> tuple
     """**两个 runner 调的就是这个**：单份金集是否与 manifest 相符。
 
     返回 ``(是否相符, 一行说明)``。runner 拿到 ``False`` 就打印说明并 ``return 2``。
+    ⛔ 环境/输入错（manifest 解析失败 / 顶层非映射 / 已登记文件缺失 / 条目 sha 非法）
+    也走 ``(False, 文案)``、**不以异常逃逸**：它是两个 runner 的 fail-closed 边界，
+    崩溃会让 runner 以未捕获异常收场（exit 1 =「指标回退」档），把 rc=2
+    「环境/输入错」的语义污染掉（r1 H-1；口径对齐 ``verify_all``，2026-09-19 r2 整改）。
     """
     manifest_path = manifest_path or MANIFEST_PATH
     if not manifest_path.exists():
         return False, f"manifest 不存在: {manifest_path}"
-    m = load_yaml(manifest_path)
+    try:
+        m = load_yaml(manifest_path)
+    except yaml.YAMLError as exc:
+        return False, f"manifest 解析失败（环境/输入错）: {manifest_path} —— {exc}"
+    if not isinstance(m, dict):
+        return False, f"manifest 顶层不是映射（环境/输入错）: {manifest_path}（实测 {type(m).__name__}）"
     want = rel_to_repo(Path(path))
     if want is None:
         return False, f"{path} 在仓外 —— manifest 只登记仓内路径，无法校验"
     for entry in m.get("files") or []:
-        if entry["path"] != want:
+        if not isinstance(entry, dict) or entry.get("path") != want:
             continue
+        if not Path(path).exists():
+            return False, f"{want} 已登记但文件缺失（环境/输入错）: {path}"
+        want_sha = entry.get("sha256")
+        if not isinstance(want_sha, str):
+            return False, f"{want} manifest 条目的 sha256 缺失或非法（环境/输入错）: {want_sha!r}"
         actual = sha256_of(Path(path))
-        if actual != entry["sha256"]:
-            return False, f"{want} sha256 期望 {entry['sha256'][:12]}… 实测 {actual[:12]}…"
-        return True, f"OK {want} sha256={actual[:12]}… queries={entry['query_count']}"
+        if actual != want_sha:
+            return False, f"{want} sha256 期望 {want_sha[:12]}… 实测 {actual[:12]}…"
+        return True, f"OK {want} sha256={actual[:12]}… queries={entry.get('query_count')}"
     return False, f"{want} 未登记在 manifest 里"
 
 
diff --git a/backend/tests/regression/test_gold_set_manifest_g413.py b/backend/tests/regression/test_gold_set_manifest_g413.py
index 4818c264..49bc78bd 100644
--- a/backend/tests/regression/test_gold_set_manifest_g413.py
+++ b/backend/tests/regression/test_gold_set_manifest_g413.py
@@ -9,8 +9,15 @@
 3. ``gold_set_manifest.yaml`` 里每一项的 ``sha256`` 与**本测试自己实算**的一致
    —— 两侧来自不同的读法，不是同一个来源自证自己；
 4. **既有 83 条逐字不变**：用 ``git show 9c4e7e82:<path>`` 取旧文逐条比十个判分/元数据键；
-5. **两个 runner 真的接了校验**：``importlib`` 载入真 runner，把金集常量指向 tmp 副本，
-   篡改副本后走真 ``main()`` → rc=2 且文案含「不符」。
+5. **两个 runner 真的接了校验**：``importlib`` 载入真 runner（⚠️ **先载工具、后载
+   runner**，两者必须共用同一模块实例），把 manifest 常量指向**篡改 sha 的副本**
+   （真金集文件在位），走真 ``main()`` → rc=2 且文案含 **sha 比较签名**
+   （「sha256 期望…实测…」）。—— 2026-09-19 r2 整改：旧版把金集指向仓外 tmp 副本 +
+   死补丁打在另一模块实例上，经「在仓外」早退分支**假绿**（r1 H-2；探针存档
+   ``negctl-r2-h2-oldpath-*.txt``）。
+6. **``verify_gold_set_file`` 的 fail-closed 边界**：三类环境/输入错（manifest 解析
+   失败 / 顶层非映射 / 已登记文件缺失）返回 ``(False, 文案)``、**不抛异常**，且经
+   runner 真 ``main()`` 收场为 rc=2（r1 H-1，r2 整改 2026-09-19）。
 
 ⛔ 实现约束（卡文 §一(g)）：读**真实**四 yaml + 真实 manifest + 真实 runner 模块。
 不连库、不起 8011、不 mock yaml/sha。所有写操作都在 ``tmp_path`` 里。
@@ -284,54 +291,81 @@ def test_existing_entries_unchanged(path: Path, expected_old_count: int) -> None
 # ═══════════════════════════════════════════════════════════════════════════
 
 
-def _tmp_copy_sets(tmp_path: Path) -> dict:
-    """把四份金集 + manifest 拷进 tmp，返回 {原路径: tmp 路径}。"""
-    out = {}
-    for p in (*ALL_SETS, MANIFEST):
-        dst = tmp_path / p.name
-        dst.write_bytes(p.read_bytes())
-        out[p] = dst
-    return out
+def _flip_first_char(s: str) -> str:
+    """把一段 hex 的**首字符**翻一位（截断显示上也能看出「期望 ≠ 实测」）。"""
+    return ("0" if s[0] != "0" else "1") + s[1:]
+
+
+def _tampered_manifest_copy(tmp_path: Path, rel_path: str) -> Path:
+    """manifest 副本：把 ``rel_path`` 那一条的 ``sha256`` 首字符翻一位，其余原样。"""
+    doc = _load(MANIFEST)
+    hits = 0
+    for entry in doc.get("files") or []:
+        if entry.get("path") == rel_path:
+            entry["sha256"] = _flip_first_char(entry["sha256"])
+            hits += 1
+    assert hits == 1, f"{rel_path} 在 manifest 里应恰有 1 条，实得 {hits}"
+    dst = tmp_path / "gold_set_manifest.tampered.yaml"
+    dst.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
+    return dst
 
 
 @pytest.mark.parametrize(
-    ("runner_file", "argv", "alive_marker"),
+    ("runner_file", "argv", "shadow_rel"),
     [
-        ("run_vault_retrieval_regression.py", ["--shadow", "--no-hook"], None),
-        ("run_memory_retrieval_regression.py", ["--shadow", "--no-judge"], "backend"),
+        (
+            "run_vault_retrieval_regression.py",
+            ["--shadow", "--no-hook"],
+            "backend/tests/regression/vault_gold_set_shadow.yaml",
+        ),
+        (
+            "run_memory_retrieval_regression.py",
+            ["--shadow", "--no-judge"],
+            "backend/tests/regression/memory_gold_set_shadow.yaml",
+        ),
     ],
     ids=["vault", "memory"],
 )
 def test_runner_rejects_tampered_gold_set(
-    runner_file: str, argv: list, alive_marker, tmp_path: Path, monkeypatch, capsys
+    runner_file: str, argv: list, shadow_rel: str, tmp_path: Path, monkeypatch, capsys
 ) -> None:
-    """篡改金集副本后走**真的** ``main()`` → rc=2 且文案含「不符」。
-
-    这条门绑的是 **runner 的接线**，不是工具自测：把工具调用从 runner 里拿掉，
-    这条就会红（负控②）。
+    """篡改 **manifest 里的 sha** 后走**真的** ``main()`` → rc=2 且文案**含 sha 比较签名**。
+
+    ⚠️ r1 H-2 的教训：旧版把金集常量指向仓外 tmp 副本 ⇒ 走「在仓外」早退分支；
+    再叠一个打在**另一个模块实例**上的死补丁 —— rc=2 + 「不符」照样绿，但**根本没
+    走到 sha 比较**（探针存档 ``negctl-r2-h2-oldpath-*.txt``）。本版：
+    ① 先 ``_import_tool`` 再 ``_import_runner`` ⇒ runner 里的 ``verify_gold_set_file``
+    与本测试拿到的是**同一模块实例**（patch 不再可能是死补丁，下面有身份断言钉住）；
+    ② 真金集文件在位，只把 manifest 副本里对应条目的 sha 翻一位 ⇒ 必经 sha 比较。
+    **验伪锚**：断言文案含「sha256 期望…实测」（只有 sha 比较支路产得出）且不含
+    「在仓外」；**对照输入**：同一机制 + 未篡改 manifest ⇒ 校验放行（``OK``），
+    证明该拒绝支路对「sha 是否被改」敏感，不是恒真。
     """
-    copies = _tmp_copy_sets(tmp_path)
+    tool = _import_tool()  # ⚠️ 必须先于 runner：runner 的 `from … import` 复用这个实例
     runner = _import_runner(runner_file)
-    tool = _import_tool()
-
-    # 把 runner 与工具的路径常量都指向 tmp 副本
-    monkeypatch.setattr(runner, "GOLD_SET", copies[VAULT_GOLD if "vault" in runner_file else MEMORY_GOLD])
-    monkeypatch.setattr(runner, "SHADOW_SET", copies[VAULT_SHADOW if "vault" in runner_file else MEMORY_SHADOW])
-    monkeypatch.setattr(tool, "MANIFEST_PATH", copies[MANIFEST])
-    monkeypatch.setattr(runner, "GOLD_SET_MANIFEST", copies[MANIFEST], raising=False)
-
-    # 篡改：往 shadow 副本尾部追加一条 query（sha 立即变）
-    shadow = copies[VAULT_SHADOW if "vault" in runner_file else MEMORY_SHADOW]
-    shadow.write_text(
-        shadow.read_text(encoding="utf-8") + '\n  - id: tampered-g413\n    query: "篡改探针"\n',
-        encoding="utf-8",
+    assert runner.verify_gold_set_file is tool.verify_gold_set_file, (
+        "runner 用的不是本测试这个工具实例 —— manifest patch 会退化成死补丁（r1 H-2）"
     )
 
+    tampered = _tampered_manifest_copy(tmp_path, shadow_rel)
+    monkeypatch.setattr(tool, "MANIFEST_PATH", tampered)
+
     monkeypatch.setattr(sys, "argv", [runner_file, *argv])
     rc = runner.main()
     out = capsys.readouterr()
-    assert rc == 2, f"篡改金集后 {runner_file} 应 rc=2，实得 {rc}\n{out.out}\n{out.err}"
-    assert "不符" in (out.out + out.err), f"{runner_file} 的拒绝文案里没有「不符」：\n{out.out}\n{out.err}"
+    combined = out.out + out.err
+    assert rc == 2, f"篡改 manifest sha 后 {runner_file} 应 rc=2，实得 {rc}\n{combined}"
+    assert "不符" in combined, f"{runner_file} 的拒绝文案里没有「不符」：\n{combined}"
+    assert "sha256 期望" in combined and "实测" in combined, (
+        f"{runner_file} 的拒绝没有走到 sha 比较（缺「sha256 期望…实测」签名）：\n{combined}"
+    )
+    assert "在仓外" not in combined, f"{runner_file} 走了「在仓外」早退分支（= r1 H-2 假绿路径）：\n{combined}"
+
+    # 对照输入（验伪锚的另一半）：同一机制 + **未篡改** manifest ⇒ 放行（OK）
+    clean = tmp_path / "gold_set_manifest.clean.yaml"
+    clean.write_bytes(MANIFEST.read_bytes())
+    ok, detail = tool.verify_gold_set_file(BACKEND_ROOT.parent / shadow_rel, manifest_path=clean)
+    assert ok is True and detail.startswith("OK "), f"未篡改的对照输入应当放行，实得 {(ok, detail)!r}"
 
 
 # ═══════════════════════════════════════════════════════════════════════════
@@ -409,3 +443,82 @@ def test_collect_is_read_only(tmp_path: Path) -> None:
     assert all("source" in c and "ref" in c["source"] for c in data), "候选缺 source.ref"
     for p, content in before.items():
         assert p.read_bytes() == content, f"collect 改动了 vault 文件：{p}"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# ⑧ verify_gold_set_file 的 fail-closed 边界（r2 整改，zcode r1 H-1）
+# ═══════════════════════════════════════════════════════════════════════════
+
+#: 一份**典型**的合并冲突残骸（``<<<<<<<``）—— 生成文件进 git 后最常见的输入错形态。
+_CONFLICT_MANIFEST = "<<<<<<< HEAD\nrevision: 2\n=======\nrevision: 1\n>>>>>>> batch-branch\n"
+
+
+def test_verify_gold_set_file_input_errors_fail_closed(tmp_path: Path) -> None:
+    """四类环境/输入错返回 ``(False, 文案)``，**不得抛异常**（r1 H-1）。
+
+    修复前三类分别以 ``yaml.YAMLError`` / ``AttributeError`` / ``FileNotFoundError``
+    逃逸 ⇒ 两个 runner 以未捕获异常收场（exit 1 =「指标回退」档），把 rc=2 的
+    「环境/输入错」语义污染掉。
+    """
+    tool = _import_tool()
+
+    # ① manifest 带合并冲突标记 → YAMLError 不得逃逸
+    conflict = tmp_path / "conflict.yaml"
+    conflict.write_text(_CONFLICT_MANIFEST, encoding="utf-8")
+    ok, detail = tool.verify_gold_set_file(VAULT_GOLD, manifest_path=conflict)
+    assert ok is False and "解析失败" in detail, f"解析错未 fail-closed：{(ok, detail)!r}"
+
+    # ② manifest 顶层不是映射（yaml 出的是个列表）→ 不得崩在 .get
+    notmap = tmp_path / "notmap.yaml"
+    notmap.write_text("- just\n- a\n- list\n", encoding="utf-8")
+    ok, detail = tool.verify_gold_set_file(VAULT_GOLD, manifest_path=notmap)
+    assert ok is False and "不是映射" in detail, f"非映射未 fail-closed：{(ok, detail)!r}"
+
+    # ③ 已登记但文件缺失 → 不得崩在 sha256_of（FileNotFoundError）
+    ghost_rel = "backend/tests/regression/__g413_ghost__.yaml"
+    assert not (BACKEND_ROOT.parent / ghost_rel).exists(), f"探针文件不该存在：{ghost_rel}"
+    ghost_manifest = tmp_path / "ghost-manifest.yaml"
+    doc = _load(MANIFEST)
+    doc["files"][0]["path"] = ghost_rel  # 借 manifest 真骨架，只改一条的 path
+    ghost_manifest.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
+    ok, detail = tool.verify_gold_set_file(BACKEND_ROOT.parent / ghost_rel, manifest_path=ghost_manifest)
+    assert ok is False and "缺失" in detail, f"缺失文件未 fail-closed：{(ok, detail)!r}"
+
+    # ④ 条目 sha256 缺失/非法（非 str）→ 不得崩在 sha 比较/格式化
+    bad_sha_manifest = tmp_path / "bad-sha-manifest.yaml"
+    doc = _load(MANIFEST)
+    doc["files"][0]["sha256"] = None
+    bad_sha_manifest.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
+    ok, detail = tool.verify_gold_set_file(VAULT_GOLD, manifest_path=bad_sha_manifest)
+    assert ok is False and "sha256" in detail, f"sha 字段非法未 fail-closed：{(ok, detail)!r}"
+
+
+@pytest.mark.parametrize(
+    ("runner_file", "argv"),
+    [
+        ("run_vault_retrieval_regression.py", ["--shadow", "--no-hook"]),
+        ("run_memory_retrieval_regression.py", ["--shadow", "--no-judge"]),
+    ],
+    ids=["vault", "memory"],
+)
+def test_runner_reports_manifest_parse_error_as_rc2(
+    runner_file: str, argv: list, tmp_path: Path, monkeypatch, capsys
+) -> None:
+    """manifest 解析错经**真 main()** 收场为 rc=2 + 文案，而不是未捕获异常（r1 H-1 的原始危害）。
+
+    修复前 ``yaml.YAMLError`` 从 ``verify_gold_set_file`` 逃逸 ⇒ 未捕获异常收场
+    （exit 1 =「指标回退」档）；修复后走 ``(False, 文案)`` ⇒「不符 (解析失败…)」+ rc=2。
+    """
+    tool = _import_tool()  # ⚠️ 先于 runner（同 ⑤ 的死补丁教训）
+    runner = _import_runner(runner_file)
+
+    conflict = tmp_path / "conflict.yaml"
+    conflict.write_text(_CONFLICT_MANIFEST, encoding="utf-8")
+    monkeypatch.setattr(tool, "MANIFEST_PATH", conflict)
+
+    monkeypatch.setattr(sys, "argv", [runner_file, *argv])
+    rc = runner.main()  # 修复前：这里抛 yaml.YAMLError（测试红）
+    out = capsys.readouterr()
+    combined = out.out + out.err
+    assert rc == 2, f"{runner_file} 对解析错 manifest 应 rc=2，实得 {rc}\n{combined}"
+    assert "不符" in combined and "解析失败" in combined, f"{runner_file} 的文案没有「不符 (解析失败…)」：\n{combined}"
```

## ② 作者自述 —— 以下每一条请独立核对，不要采信

1. **H-1 修法**：`verify_gold_set_file` 覆盖四类输入错（`YAMLError` / 顶层非映射 / 已登记缺失 / 条目 sha 非法），全部返回 `(False, 文案)`、不以异常逃逸；runner 侧因此 rc=2 +「不符 (…)」文案，**不再 exit 1**（r1 的危害面）。修前实测：新负控测试对着旧工具跑 → 崩在 `yaml.scanner.ScannerError`（`negctl-r2-h1-red-*.txt`）。
2. **H-2 修法**：门⑤ —— ① `_import_tool()` 先行、`_import_runner()` 复用同一模块实例（`assert runner.verify_gold_set_file is tool.verify_gold_set_file` 钉住死补丁回归）；② 真金集在仓内、只把 manifest **副本**里对应条目的 sha 首字符翻一位 ⇒ 必到 sha 比较；③ **验伪锚**：断言文案含「sha256 期望…实测」且**不含**「在仓外」；④ **对照输入**：未篡改 manifest 副本 ⇒ `(True, "OK …")` 放行。
3. **先红后绿**：新/改测试对旧工具 = **3 failed / 12 passed**；修后 = **15 passed**（收集 15）；`ruff check` + `format --check` 双绿。
4. **旧路径探针**（独立于 pytest 的 scratchpad，输出已落档）：old 模式复现 r1 机制 → 含「在仓外」= True、含「sha256 期望」= False；new 模式 → 含「在仓外」= False、含「sha256 期望」= True。
5. **裁判**：点名套件 37 passed；`tests/regression` 目录级 **1928 passed / 6 skipped / 1 xfailed，红 0**（FAILED 集 ⊆ 修复前 close 集 = 空）；`tests/unit` **32 红 == close（nodeid diff rc=0）**，对基线 33 只少那条已知 flaky；地盘 diff（vs `18f31c44`，排除 `_bmad-output`）= 恰两文件。
6. **M/L 不动**：M-1/M-2/M-3、L-1~L-6 只登记不改；本轮未碰两 runner 判分逻辑、`gold_set_manifest.yaml` 数据、schema。

## ③ 请优先回答的问题（**已按 Jev 分诊 urgency 降序、REVIEW 标记者优先**；括号内对应 r1 条目）

**分诊表（jev-1.13.0，对 `2e0642aa`；JSON：`_bmad-output/审查/evidence-g413/jev-triage-2e0642aa.json`）**：

| 文件 | CHURN | URG↓ | REVIEW | TEST | risk | 判定 |
|---|---|---|---|---|---|---|
| `backend/scripts/gold_set_manifest_tool.py` | +19/-5 | **2.70** | 0.66 | 0.57 | error_handling | REVIEW |
| `backend/tests/regression/test_gold_set_manifest_g413.py` | +147/-34 | **2.68** | 0.79 | 0.93 | test_or_docs | REVIEW |

**A. `gold_set_manifest_tool.py`（URG 2.70 · risk=error_handling · REVIEW；r1 H-1）**

- A1：H-1 的四类覆盖是否**完备且真实** —— 修复后 `verify_gold_set_file` 还有没有别的异常逃逸面？（请对照输入自造，例如：`rel_to_repo` 的 `resolve()` 面 / `m.get("files")` 里条目是 dict 但缺 `path` 键 / `exists()` 与 `read_text` 之间的 TOCTOU / `entry.get("query_count")` 面。）
- A2：返回文案变化（新增四类前缀）与**既有消费者**是否兼容 —— 两个 runner 只把 detail 打进一句话；仓内有没有按字面断言旧消息的测试/脚本/协议条款会被打红（门未覆盖的路径）？
- A3：docstring 声称「口径对齐 `verify_all`」是否属实 —— 逐条对照两函数对**同一输入**的行为与 rc/布尔映射（`verify_all` 是 rc 三态、本函数是 bool；runner 把 False 统一映射 rc=2 —— 这层映射有没有信息丢失面？）。

**B. `test_gold_set_manifest_g413.py`（URG 2.68 · risk=test_or_docs · REVIEW；r1 H-2）**

- B1：门⑤的**验伪锚**是否真能抓住死补丁回归 —— 把 `_import_tool/_import_runner` 顺序调回去（或换成 `rule.verify_gold_set_file.__globals__` 失效的写法）时，哪条断言先红？identity 断言与文案断言各拦什么？有没有「改坏了但门仍绿」的**门未覆盖的路径**？
- B2：门⑤的**对照输入**（未篡改 ⇒ OK）是否足以证明拒绝支路非恒真；负断言「不含『在仓外』」的适用边界 —— 「仓外」早退路径本身仍是合法行为（`:291-293`），本断言会不会误伤未来的合法用例（如将来主动校验仓外文件的用例）？
- B3：⑧ 段四个 case 是否**各自**红在指定断言上（修前）；`test_runner_reports_manifest_parse_error_as_rc2` 的两个参数是否真跑了两条 runner 的**不同阶段**（memory 的校验在 `check_backend_alive()` 之前）？
- B4：测试对**仓内路径**（`BACKEND_ROOT.parent / shadow_rel`）与 `MANIFEST` 常量的依赖，在未来改名 / 挪目录时会不会退化成假绿（skip / 恒真）——有没有**对照输入**能暴露它？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 一句话结论
- `file:line`（精确到行）
- 一句复现思路，措辞请用「**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**」

如果某条只是风格或偏好，请标 LOW 并说明它不影响正确性。

## ⑤ 边界

- **只读**；不要修改任何文件；不要连库 / 起容器 / 跑需要网络的东西。
- 只审**本轮修复面**（两文件 + H-1/H-2 的闭合证据）。M-1/M-2/M-3、L-1~L-6 已登记不改（除非按 ④ 给出 HIGH 升级理由）。
- 不要评审两 runner 的判分逻辑、`gold_set_manifest.yaml` 数据、`manifest.schema.json`、G4-14 / R-SLO 面。
