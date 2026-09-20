# CARD-G5-7 补审 round-7（ZCode × GLM-5.3，协议 §2.4.2）— clear-inbox 执行侧 + undo_journal（绑最终态）

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根（--cwd）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`10a2799e510602dad4a1d267040701e8bdd80d28`**（本卡文件末次改动 commit；其后的 HEAD 只含 `_bmad-output/` 归档，三份文件零改动 —— `git --no-pager diff --stat --no-color 10a2799e HEAD -- <三份文件>` = 空；工作树干净）。

本地 Obsidian vault 的「待处理收件箱清仓」工具链。上一张卡做了**只读**的盘点提名 preview；本卡补**执行侧**：读 preview 的 JSON + 用户逐条拍板的 decisions，把材料 copy / 硬链接 / move / 移入回收目录 / 留原地，并落一本可一键撤销的账。**默认路径 0 物理删除**是本卡的核心不变量（AST 门数 `Call` 节点，不数文本）。在本卡语境里「覆盖」与「删除」同等严重 —— 用户的文件被无声换掉就是弄丢。

本卡新增恰三份文件：
- `canvas-vault/.claude/scripts/undo_journal.py`（NEW，共用模块，G5-10 复用）
- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py`（NEW，执行侧 CLI）
- `backend/tests/skills/test_g5_7_inbox_apply.py`（NEW，承重行为用例）

三份文件的**全量 diff 内嵌在附录 A**（本通道 `--mode build` 禁 Bash，读不了 git；三份文件都是新增，diff 即全文，未经删改）。本卡为**最终态复核**：三份文件是定稿版本，不需要对照更早版本。

为读懂契约，还需要看这些**既有**文件的片段（本卡只读、零改动；你可直接从仓内读文件）：
- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py`：`:266-292`（加载器）/ `:300-330`（常量）/ `:385-396`（verdict 词表）/ `:1876-1914`（提名字段）/ `:1917-1983`（item 键与跳过口径）/ `:2143-2186`（JSON 顶层键与 `vault_fingerprint` 算式）/ `:2395-2479`（main 准入次序）
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py`：`:1734-1860`（写侧物理原语；本卡只复用其中的 `assert_symlink_free`）

另有一段**历史**生产改动（X1 三处，+14/-5，本轮兼作其独立复审）：`git --no-pager diff --no-color ac949f6f 69fce02c -- canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py`，**内嵌在附录 B**。

判定上下文（本卡只读引用）：
- 「X1 G5-6c-R1」行：`_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:30`（卡文写 `:31`）
- 第十批裁定「合」：同上台账 `:178`
- 总账 v2：`_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:534`（做什么）与 `:1051`（R8「删」语义 SUPERSEDED，本卡收敛为「回收目录留痕」）

⛔ 本通道已禁 Bash / Write（会得到 `No permission client configured`）：不要运行任何命令；git 输出已全部内嵌；读文件 + 内嵌文本足以完成本轮审查。

## ② 作者自述请独立核对（当成**待验证的命题**，不是事实）

逐条给出：成立 / 不成立（附 file:line）/ 范围过宽（说明差在哪）。

1. **默认路径 0 物理删除**（AST 门 F2 数 `Call` 节点）；
2. **undo 全树逐字节 + mtime 一致**（撤销后全树 hash/mtime 与批次前逐字相同）；
3. **中断重跑幂等**（同输入同 `batch_id` + journal 复核）；
4. **准入次序「守卫全过再碰 work-dir」**（任一守卫不过即整批拒绝且连 `outputs/` 都不建出来）；
5. **执行侧对 strip 文本字段零消费**（`basis` / `ask` / `uncertain_reason` / `criterion` / `near_duplicates` 等经 strip 的文本字段零消费，F4 AST 门）；
6. **不加 SKILL.md**（scripts-only）；
7. **不改 P5/P6 文件**（`inbox_preview.py` / `split_preview.py` / `skill_portability_lint.py` 零改动）。

## ③ 按重要性排序的问题

0. `recycle` 双确认能否被 decisions 文件伪装（`confirm` 字段类型 / 真值判定；`--confirm-recycle` 与逐件 confirm 缺一是否真拒）；
1. undo 逆序还原在「同一批既 move 又 recycle 同一路径」或「目标路径被用户事后改动」时是否会覆盖用户新内容（应比 sha 后拒绝）；
2. journal 单行原子追加在写一半掉电时的半行如何被重跑识别（应按解析失败行截断处理、不当 done）；
3. `batch_id` 由三份输入 sha 派生，preview 文件被重新生成（内容同、路径同）是否仍幂等；
4. provenance frontmatter 插入对无 frontmatter / 非 UTF-8 / CRLF 文件的处理（不得把 CRLF 归一，见 T7 系坑）；
5. `link` 硬链接跨卷 `EXDEV` 的回执是否精确、是否留半态；
6. target 白名单是否用 realpath 且拒绝祖先 symlink（`O_NOFOLLOW` 只管末段）；
7. X1 三处改动（`ac949f6f..69fce02c`，附录 B）本身是否引入缺陷。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**
（措辞请用上面四类，不要用攻防演练类措辞 —— 本审查的边界是代码正确性与数据安全。）

结尾给出计数行：`BLOCKER n / HIGH n / MEDIUM n / LOW n`。没找到问题就明说「无」——「没找到」是有价值的结论，凑数不是。请用中文输出。

## ⑤ 边界

- **只读**：不要修改任何文件；不要尝试运行命令或写盘（build 模式已阻断 Bash/Write）。
- 不连任何数据库或网络服务（本卡零外部依赖）。
- 不评价 `undo_journal.py` 将来被 G5-10 复用时的白板派生语义（那是下一张卡）。
- 不评价 G8-2c。
- `split_preview.py` / `inbox_preview.py` 是别的车道的地盘，本卡只读；对它们内部实现（附录 B 的 X1 三处除外）的意见请标注「移交」，不要计为本卡的 BLOCKER/HIGH。

---

## 附录 A：本卡三份文件全量 diff

以下 = `git --no-pager diff --no-color 9c4e7e82 10a2799e -- backend/tests/skills/test_g5_7_inbox_apply.py canvas-vault/.claude/scripts/undo_journal.py canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py` 的**完整输出**（未经删改）：

=== 附录A 开始 ===
diff --git a/backend/tests/skills/test_g5_7_inbox_apply.py b/backend/tests/skills/test_g5_7_inbox_apply.py
new file mode 100644
index 00000000..d1c839c0
--- /dev/null
+++ b/backend/tests/skills/test_g5_7_inbox_apply.py
@@ -0,0 +1,4160 @@
+"""G5-7 — clear-inbox 执行侧裁判 (BATCH-2026-09-18-第十五批 / CARD-G5-7)。
+
+被测物:
+  canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py   (执行侧 CLI)
+  canvas-vault/.claude/scripts/undo_journal.py                     (共用备份/journal/撤销)
+
+裁判覆盖 (卡片 (g) 钦定):
+  A. 三方案落地 —— copy 保 mtime + provenance; link 同 inode 且无 provenance;
+     move 逐字节 + mtime 逐等
+  B. 「删」的双重显式确认 —— 缺 --confirm-recycle 或缺逐件 confirm 一律整批拒绝、
+     零写 (连 work-dir 都不许建出来); 双确认后移入回收目录留痕
+  C. undo 全树逐字节 —— sha256 + st_mtime_ns + st_mode 三项逐等; copy/link 产物
+     进 recycle/undone/ 而不是被删
+  D. 中断重跑幂等 —— 真实 chmod 注入失败 (禁 mock) 后重跑同输入, 终态与一次跑完
+     逐项相等、journal 无重复 done 行
+  E. 准入次序 —— 指纹不符 / preview 过期 / 未知 stable_id / target 越界 /
+     dst 已被占 一律拒绝且零写
+  F. 默认路径 0 物理删除 —— F2 AST 门 (数 Call 节点, 不数文本) 入树常驻,
+     F4 文本字段零消费门同上
+
+fixtures 全部在 tmp_path 程序化构造, preview 由**真的**跑一次 inbox_preview.py CLI
+得到 (DD-03 禁 mock: 不手搓 preview JSON, 否则测的是自己编的契约)。
+⛔ 本目录禁建 conftest.py, 故一切工具函数就地定义 (与 test_g5_6 同口径, 不 import
+它 —— 跨测试文件 import 会让两卡的裁判互相牵连)。
+"""
+
+from __future__ import annotations
+
+import ast
+import hashlib
+import importlib.util
+import json
+import os
+import shutil
+import stat
+import subprocess
+import sys
+from datetime import datetime, timedelta
+from pathlib import Path
+
+import pytest
+
+REPO_ROOT = Path(__file__).resolve().parents[3]
+SKILLS = REPO_ROOT / "canvas-vault" / ".claude" / "skills"
+PREVIEW_SCRIPT = SKILLS / "clear-inbox" / "scripts" / "inbox_preview.py"
+APPLY_SCRIPT = SKILLS / "clear-inbox" / "scripts" / "inbox_apply.py"
+JOURNAL_SCRIPT = REPO_ROOT / "canvas-vault" / ".claude" / "scripts" / "undo_journal.py"
+
+NOW_ISO = "2026-09-18T00:00:00+08:00"
+NOW_DT = datetime.fromisoformat(NOW_ISO)
+INBOX = "_待处理"
+
+#: 本卡两份新脚本 —— F2/F4 结构门的作用面
+NEW_SCRIPTS = (JOURNAL_SCRIPT, APPLY_SCRIPT)
+
+#: F2 门的删除原语名单 (按 Call 节点的 func 名/属性名比对)
+DELETE_PRIMITIVES = frozenset({"remove", "unlink", "rmtree", "rmdir", "send2trash"})
+
+#: F4 门: 这些是 preview 里经过裸 .strip() 的自由文本字段 (X1 开放面 ①)。
+#: 执行侧数据面对它们必须零消费 —— 消费了, 那 13 行的 Unicode 口径就进了写侧。
+STRIPPED_TEXT_FIELDS = frozenset(
+    {
+        "basis",
+        "ask",
+        "uncertain_reason",
+        "criterion",
+        "near_duplicates",
+        "conflicts",
+        "exact_duplicate_others",
+    }
+)
+
+
+# ───────────────────────── 工具 ─────────────────────────
+
+
+def require_script(p: Path) -> Path:
+    """⛔ 防「脚本不存在 → returncode≠0 → 拒绝类断言假绿」: 先红阶段全部用例
+    必须因**这一条**而红, 而不是因为 import 错误或夹具错。"""
+    if not p.is_file():
+        pytest.fail(f"被测脚本不存在: {p}")
+    return p
+
+
+def sha256_of(p: Path) -> str:
+    return hashlib.sha256(p.read_bytes()).hexdigest()
+
+
+def snapshot(root: Path, skip: tuple[str, ...] = ()) -> dict:
+    """全树取证: 每个条目 (sha256 | "dir" | "symlink:…") + st_mtime_ns + st_mode + nlink。
+
+    `skip` 是相对 root 的路径前缀 —— 产物目录必须排除, 否则快照自证其罪式失效。
+
+    ⛔ 口径里必须有 `st_nlink`: 少了它,「还原成一份独立文件」与「还原成一条与 backup/
+    或 vault 内另一份共享 inode 的**硬链接**」在快照上**逐项相同** —— 全树 undo 门
+    看不见这一类回退（全卡复核 L10）。inode 号本身不能进快照（跨跑不稳定）, 而 nlink
+    恰好就是能分辨这件事的那个量。
+    """
+    out: dict[str, tuple] = {}
+    for p in sorted(root.rglob("*")):
+        rel = str(p.relative_to(root))
+        if any(rel == s or rel.startswith(s + os.sep) for s in skip):
+            continue
+        st = p.lstat()
+        if p.is_symlink():
+            digest = "symlink:" + os.readlink(p)
+        elif p.is_dir():
+            digest = "dir"
+        else:
+            digest = hashlib.sha256(p.read_bytes()).hexdigest()
+        # 目录的 nlink 随子项增减而变, 不是本判据要盯的东西, 故只对非目录记。
+        out[rel] = (digest, st.st_mtime_ns, st.st_mode, None if p.is_dir() else st.st_nlink)
+    return out
+
+
+def days_ago(n: float) -> float:
+    return (NOW_DT - timedelta(days=n)).timestamp()
+
+
+def mk(path: Path, text: str, age_days: float = 1.0) -> Path:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(text, encoding="utf-8")
+    ts = days_ago(age_days)
+    os.utime(path, (ts, ts))
+    return path
+
+
+def mk_bytes(path: Path, raw: bytes, age_days: float = 1.0) -> Path:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_bytes(raw)
+    ts = days_ago(age_days)
+    os.utime(path, (ts, ts))
+    return path
+
+
+def base_vault(tmp_path: Path) -> tuple[Path, Path]:
+    """最小合法 vault + 空收件箱; 返回 (vault, preview_out_dir)。
+
+    preview 产物目录恒在 vault **树外** —— 否则它会进全树快照, 让零写断言失效。
+    """
+    vault = tmp_path / "vault"
+    (vault / "原白板").mkdir(parents=True)
+    (vault / "节点").mkdir(parents=True)
+    (vault / "归档").mkdir(parents=True)
+    (vault / INBOX).mkdir(parents=True)
+    return vault, tmp_path / "preview-out"
+
+
+def run_preview(vault: Path, out_dir: Path, now: str = NOW_ISO):
+    require_script(PREVIEW_SCRIPT)
+    return subprocess.run(
+        [
+            sys.executable,
+            str(PREVIEW_SCRIPT),
+            "--vault",
+            str(vault),
+            "--out-dir",
+            str(out_dir),
+            "--now",
+            now,
+        ],
+        capture_output=True,
+        text=True,
+    )
+
+
+def make_preview(vault: Path, out_dir: Path, now: str = NOW_ISO) -> Path:
+    """真跑一次 preview CLI, 返回 JSON 产物路径 (DD-03: 不手搓契约)。"""
+    r = run_preview(vault, out_dir, now)
+    assert r.returncode == 0, f"preview 生成失败: {r.returncode}\n{r.stderr}"
+    p = out_dir / f"inbox-preview-{INBOX}.json"
+    assert p.is_file(), f"preview 产物缺席: {p}"
+    return p
+
+
+def preview_items(preview_json: Path) -> dict[str, dict]:
+    data = json.loads(preview_json.read_text(encoding="utf-8"))
+    return {it["stable_id"]: it for it in data["items"]}
+
+
+def id_of(preview_json: Path, name: str) -> str:
+    for sid, it in preview_items(preview_json).items():
+        if it["name"] == name:
+            return sid
+    raise AssertionError(f"preview 里找不到条目: {name}")
+
+
+def write_decisions(path: Path, decisions: list[dict]) -> Path:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(
+        json.dumps({"schema_version": 1, "decisions": decisions}, ensure_ascii=False, indent=2) + "\n",
+        encoding="utf-8",
+    )
+    return path
+
+
+def run_apply(vault: Path, preview: Path, decisions: Path, *extra: str, now=NOW_ISO, env=None):
+    require_script(APPLY_SCRIPT)
+    require_script(JOURNAL_SCRIPT)
+    return subprocess.run(
+        [
+            sys.executable,
+            str(APPLY_SCRIPT),
+            "--vault",
+            str(vault),
+            "--preview",
+            str(preview),
+            "--decisions",
+            str(decisions),
+            "--now",
+            now,
+            *extra,
+        ],
+        capture_output=True,
+        text=True,
+        env=env,
+    )
+
+
+def run_undo(vault: Path, journal: Path, *extra: str, now=NOW_ISO):
+    require_script(APPLY_SCRIPT)
+    require_script(JOURNAL_SCRIPT)
+    return subprocess.run(
+        [
+            sys.executable,
+            str(APPLY_SCRIPT),
+            "--vault",
+            str(vault),
+            "--undo",
+            str(journal),
+            "--now",
+            now,
+            *extra,
+        ],
+        capture_output=True,
+        text=True,
+    )
+
+
+def files_only(snap: dict) -> dict:
+    """只取普通文件那一层 —— 目录的 mtime 另有一套判据 (见下面那条用例的注释)。"""
+    return {k: v for k, v in snap.items() if v[0] != "dir"}
+
+
+def no_outputs(vault: Path) -> bool:
+    """拒绝路径的零写判据 —— 连 outputs/ 这一级都不许被建出来。"""
+    return not (vault / "outputs").exists()
+
+
+def work_root(vault: Path) -> Path:
+    """缺省 work-dir —— 与 inbox_apply.py 的缺省值同口径。"""
+    return vault / "outputs" / "clear-inbox"
+
+
+def only_batch_dir(vault: Path) -> Path:
+    root = work_root(vault)
+    dirs = sorted(d for d in root.iterdir() if d.is_dir())
+    assert len(dirs) == 1, f"期望恰一个批次目录, 实得 {dirs}"
+    return dirs[0]
+
+
+def journal_rows(batch_dir: Path) -> list[dict]:
+    raw = (batch_dir / "journal.jsonl").read_text(encoding="utf-8")
+    # ⛔ 只按 "\n" 切: splitlines() 会在 U+2028/U+2029 处多切一刀, 把一条合法记录
+    # 切成两条非法 JSON (记忆坑 splitlines_breaks_jsonl_on_u2028)。
+    rows = []
+    for line in raw.split("\n"):
+        if line.strip():
+            rows.append(json.loads(line))
+    return rows
+
+
+def ast_delete_call_count(paths) -> int:
+    """F2 门: 数 ast.Call 节点, **不数文本** —— 注释 / 字符串字面量 / `if False`
+    里的字样都不该算, 而文本 grep 会把它们算进来 (记忆坑 gate_must_count_ast_calls)。"""
+    n = 0
+    for f in paths:
+        tree = ast.parse(Path(f).read_text(encoding="utf-8"))
+        for node in ast.walk(tree):
+            if not isinstance(node, ast.Call):
+                continue
+            fn = node.func
+            if isinstance(fn, ast.Attribute) and fn.attr in DELETE_PRIMITIVES:
+                n += 1
+            elif isinstance(fn, ast.Name) and fn.id in DELETE_PRIMITIVES:
+                n += 1
+    return n
+
+
+def ast_string_constants(path: Path) -> set[str]:
+    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
+    return {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
+
+
+# ───────────────────────── A. 三方案落地 ─────────────────────────
+
+
+def test_copy_preserves_mtime_and_writes_provenance(tmp_path):
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "笔记.md", "# 标题\n\n正文一行\n", age_days=3)
+    src_sha, src_mtime = sha256_of(src), src.stat().st_mtime_ns
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "笔记.md"), "action": "copy", "target": "节点"}],
+    )
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode == 0, r.stdout + r.stderr
+
+    dst = vault / "节点" / "笔记.md"
+    assert dst.is_file()
+    assert dst.stat().st_mtime_ns == src_mtime, "copy 必须保 mtime (纳秒逐等)"
+    assert src.is_file() and sha256_of(src) == src_sha, "原件必须一个字节都不动"
+
+    body = dst.read_text(encoding="utf-8")
+    assert body.startswith("---"), "copy 的 .md 目标必须带 frontmatter"
+    assert "clear_inbox_provenance:" in body
+    assert f"{INBOX}/笔记.md" in body, "provenance 必须写下原路径"
+    batch_dir = only_batch_dir(vault)
+    assert batch_dir.name in body, "provenance 必须写下 batch_id"
+    assert "正文一行" in body, "provenance 不得吃掉正文"
+
+
+def test_link_shares_inode_and_writes_no_provenance(tmp_path):
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "硬链.md", "# 硬链\n\n原文\n", age_days=2)
+    src_sha = sha256_of(src)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "硬链.md"), "action": "link", "target": "节点"}],
+    )
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode == 0, r.stdout + r.stderr
+
+    dst = vault / "节点" / "硬链.md"
+    assert dst.stat().st_ino == src.stat().st_ino, "link 必须是硬链接 (同 inode)"
+    assert sha256_of(src) == src_sha, "link 不得改动原件字节"
+    assert "clear_inbox_provenance" not in dst.read_text(encoding="utf-8"), (
+        "link 与原件同 inode, 写 provenance 等于改原件 —— 必须不写"
+    )
+
+
+def test_move_is_byte_exact_and_mtime_exact(tmp_path):
+    vault, out = base_vault(tmp_path)
+    # 非 .md: provenance 只对 .md 生效, 于是「目标 sha == 备份 sha == 原 sha」才成立
+    src = mk_bytes(vault / INBOX / "扫描件.txt", b"raw\x00bytes\r\nline\n", age_days=5)
+    src_sha, src_mtime = sha256_of(src), src.stat().st_mtime_ns
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "扫描件.txt"), "action": "move", "target": "归档"}],
+    )
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode == 0, r.stdout + r.stderr
+
+    assert not src.exists(), "move 之后原路径必须不存在"
+    dst = vault / "归档" / "扫描件.txt"
+    assert sha256_of(dst) == src_sha
+    assert dst.stat().st_mtime_ns == src_mtime
+
+    batch_dir = only_batch_dir(vault)
+    backup = batch_dir / "backup" / INBOX / "扫描件.txt"
+    assert sha256_of(backup) == src_sha, "备份必须与原件逐字节相同"
+
+
+def test_move_md_writes_provenance_and_keeps_backup_pristine(tmp_path):
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "搬家.md", "---\ntitle: 旧\n---\n\n正文\n", age_days=4)
+    src_sha = sha256_of(src)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "搬家.md"), "action": "move", "target": "归档"}],
+    )
+
+    assert run_apply(vault, pv, dec).returncode == 0
+    dst = vault / "归档" / "搬家.md"
+    body = dst.read_text(encoding="utf-8")
+    assert "clear_inbox_provenance:" in body
+    assert "title: 旧" in body, "既有 frontmatter 键必须保留"
+    batch_dir = only_batch_dir(vault)
+    backup = batch_dir / "backup" / INBOX / "搬家.md"
+    assert sha256_of(backup) == src_sha, "备份是 op 之前的快照, 不含 provenance"
+
+
+# ───────────────────────── B. 「删」的双重显式确认 ─────────────────────────
+
+
+def test_recycle_without_confirm_flag_is_zero_write(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "废稿.md", "# 废稿\n", age_days=9)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "废稿.md"), "action": "recycle", "confirm": True}],
+    )
+    before = snapshot(vault)
+
+    r = run_apply(vault, pv, dec)  # ⛔ 故意不给 --confirm-recycle
+    assert r.returncode != 0
+    assert snapshot(vault) == before, "缺 --confirm-recycle 必须整批拒绝、零写"
+    assert no_outputs(vault), "拒绝路径连 outputs/ 这一级都不许建出来"
+
+
+def test_recycle_without_per_item_confirm_is_zero_write(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "废稿2.md", "# 废稿2\n", age_days=9)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "废稿2.md"), "action": "recycle", "confirm": False}],
+    )
+    before = snapshot(vault)
+
+    r = run_apply(vault, pv, dec, "--confirm-recycle")  # 有 flag, 缺逐件 confirm
+    assert r.returncode != 0
+    assert snapshot(vault) == before, "缺逐件 confirm 必须整批拒绝、零写"
+    assert no_outputs(vault)
+
+
+def test_recycle_rejects_truthy_non_boolean_confirm(tmp_path):
+    """confirm 必须是**布尔真**, 不是「真值」—— 否则 "no" / 1 / [] 之类都能蒙混过关。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "废稿3.md", "# 废稿3\n", age_days=9)
+    pv = make_preview(vault, out)
+    before = snapshot(vault)
+    for bogus in ("true", 1, ["yes"], {"k": "v"}):
+        dec = write_decisions(
+            tmp_path / "d.json",
+            [
+                {
+                    "stable_id": id_of(pv, "废稿3.md"),
+                    "action": "recycle",
+                    "confirm": bogus,
+                }
+            ],
+        )
+        r = run_apply(vault, pv, dec, "--confirm-recycle")
+        assert r.returncode != 0, f"confirm={bogus!r} 不该被当成确认"
+        assert snapshot(vault) == before
+        assert no_outputs(vault)
+
+
+def test_recycle_double_confirmed_leaves_trace(tmp_path):
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "该删.md", "# 该删\n\n没用了\n", age_days=12)
+    src_sha, src_mtime = sha256_of(src), src.stat().st_mtime_ns
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "该删.md"), "action": "recycle", "confirm": True}],
+    )
+
+    r = run_apply(vault, pv, dec, "--confirm-recycle")
+    assert r.returncode == 0, r.stdout + r.stderr
+
+    assert not src.exists(), "双确认后原路径不再有它"
+    batch_dir = only_batch_dir(vault)
+    recycled = batch_dir / "recycle" / INBOX / "该删.md"
+    assert recycled.is_file(), "「删」= 移入回收目录留痕, 不是物理删除"
+    assert sha256_of(recycled) == src_sha, "留痕必须逐字节保全"
+    assert recycled.stat().st_mtime_ns == src_mtime
+
+    rows = [r for r in journal_rows(batch_dir) if r.get("op") == "recycle"]
+    assert rows, "journal 必须留下 recycle 行"
+    done = [r for r in rows if r["state"] == "done"]
+    assert len(done) == 1
+    assert done[0]["sha256_before"] == src_sha
+    assert done[0]["src"] == f"{INBOX}/该删.md"
+
+
+# ───────────────────────── C. undo 全树逐字节 ─────────────────────────
+
+
+def build_mixed_batch(tmp_path):
+    """一批里 copy / link / move / recycle 各 ≥1 —— undo 门的输入面。
+
+    ⛔ **必须含一件 move 的 .md**（戊）: 非 .md 的 move 不写 provenance, 而 os.replace
+    本来就保 mtime —— 只用 .txt 的话, undo 里那次还原 mtime 的 os.utime 根本走不到,
+    这道门就绿在了「os.replace 自己保了 mtime」这道更早的判据上。本卡负控② 第一次跑
+    SURVIVED (3 passed) 就是这么暴露出来的。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "甲.md", "# 甲\n\n甲的正文\n", age_days=1)
+    mk(vault / INBOX / "乙.md", "# 乙\n\n乙的正文\n", age_days=2)
+    mk_bytes(vault / INBOX / "丙.txt", b"binary\x01\x02\n", age_days=3)
+    mk(vault / INBOX / "丁.md", "# 丁\n", age_days=4)
+    mk(vault / INBOX / "戊.md", "---\ntitle: 戊\n---\n\n戊的正文\n", age_days=5)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "戊.md"), "action": "move", "target": "节点"},
+            {"stable_id": id_of(pv, "甲.md"), "action": "copy", "target": "节点"},
+            {"stable_id": id_of(pv, "乙.md"), "action": "link", "target": "原白板"},
+            {"stable_id": id_of(pv, "丙.txt"), "action": "move", "target": "归档"},
+            {"stable_id": id_of(pv, "丁.md"), "action": "recycle", "confirm": True},
+        ],
+    )
+    return vault, pv, dec
+
+
+def test_undo_restores_whole_tree_byte_exact(tmp_path):
+    vault, pv, dec = build_mixed_batch(tmp_path)
+    before = snapshot(vault, skip=("outputs",))
+
+    r = run_apply(vault, pv, dec, "--confirm-recycle")
+    assert r.returncode == 0, r.stdout + r.stderr
+    batch_dir = only_batch_dir(vault)
+    assert snapshot(vault, skip=("outputs",)) != before, "执行后该有变化, 否则门空转"
+    # 敏感性锚: 搬走的那份 .md 确实被 provenance 改过内容(于是 undo 必须靠备份还原,
+    # 那条还原 mtime 的 os.utime 才承重), 否则本门只是在验 os.replace 的自带行为。
+    moved_md = (vault / "节点" / "戊.md").read_bytes()
+    assert b"clear_inbox_provenance:" in moved_md
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stdout + u.stderr
+
+    after = snapshot(vault, skip=("outputs",))
+    # ⛔ 加 `st_nlink` 进快照之后立刻显形的一项: 0 物理删除的**必然代价** —— link 的撤销
+    # 把硬链接产物**移进** recycle/undone/ 而不是解链, 于是源文件的 nlink 比批前多 1。
+    # 这不是回退（回执 note 早就声明了「已移进 recycle/undone/ 留痕, 没有做任何物理
+    # 删除」）, 但它此前**从未被任何一条断言碰过** —— 旧快照口径里根本没有 nlink
+    # （全卡复核 L10）。所以这里不是放宽判据, 是把这项后果**显式钉住**:
+    # 差异只许出现在这一个条目上、只许是 +1、而且那条多出来的链接必须**确实在**
+    # recycle/undone/ 里（否则它就是漏在别处的一条野链接）。
+    linked_src = f"{INBOX}/乙.md"
+    assert after.keys() == before.keys(), "全树条目集合必须一致"
+    for k in before:
+        if k == linked_src:
+            assert after[k][:3] == before[k][:3], f"{k} 的 sha256/mtime_ns/mode 必须逐等"
+            assert after[k][3] == before[k][3] + 1, (
+                f"{k} 的 nlink 应恰好比批前多 1（撤销出来的那条硬链接）, 实得 {before[k][3]} → {after[k][3]}"
+            )
+            continue
+        assert after[k] == before[k], f"{k} 四项必须逐等: {before[k]} → {after[k]}"
+    undone = batch_dir / "recycle" / "undone"
+    src_ino = (vault / INBOX / "乙.md").stat().st_ino
+    assert undone.is_dir() and any(p.is_file() and p.stat().st_ino == src_ino for p in undone.rglob("*")), (
+        "多出来的那条硬链接不在 recycle/undone/ 里 —— 它去哪了?"
+    )
+
+    undone = batch_dir / "recycle" / "undone"
+    names = sorted(p.name for p in undone.rglob("*") if p.is_file())
+    assert any(n.endswith("甲.md") for n in names), "copy 产物必须进 undone/ 而不是被删"
+    assert any(n.endswith("乙.md") for n in names), "link 产物必须进 undone/"
+
+
+def test_undo_refuses_when_target_modified_after_apply(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk_bytes(vault / INBOX / "戊.txt", "原始内容\n".encode(), age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "戊.txt"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+
+    dst = vault / "归档" / "戊.txt"
+    dst.write_text("用户事后改过的新内容\n", encoding="utf-8")
+    tampered = snapshot(vault, skip=("outputs",))
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0, "目标被改过还原回去会让 mtime 说谎 —— 必须拒绝"
+    assert snapshot(vault, skip=("outputs",)) == tampered, "拒绝路径不得动任何文件"
+
+
+def test_undo_refuses_when_source_path_reoccupied(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "己.md", "# 己\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "己.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+
+    # 用户在原路径又放了一份**新**材料 —— 还原不得把它盖掉
+    mk(vault / INBOX / "己.md", "# 这是后来放进来的另一份\n", age_days=0.1)
+    occupied = snapshot(vault, skip=("outputs",))
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert snapshot(vault, skip=("outputs",)) == occupied
+
+
+# ───────────────────────── D. 中断重跑幂等 ─────────────────────────
+
+
+def test_rerun_after_injected_failure_is_idempotent(tmp_path):
+    """真实注入 (禁 mock): 把第 2 件的目标目录 chmod 0o500 让写失败。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "a1.md", "# a1\n", age_days=1)
+    mk(vault / INBOX / "a2.md", "# a2\n", age_days=2)
+    mk(vault / INBOX / "a3.md", "# a3\n", age_days=3)
+    pv = make_preview(vault, out)
+    # preview 最旧优先 ⇒ a3(3天) → a2(2天) → a1(1天); 决策按 preview 次序给
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "a3.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "a2.md"), "action": "copy", "target": "节点"},
+            {"stable_id": id_of(pv, "a1.md"), "action": "copy", "target": "归档"},
+        ],
+    )
+
+    blocked = vault / "节点"
+    orig_mode = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        r1 = run_apply(vault, pv, dec)
+        assert r1.returncode != 0, "第 2 件写不进去, 绝不能报完成"
+    finally:
+        os.chmod(blocked, orig_mode)
+
+    batch_dir = only_batch_dir(vault)
+    receipt = json.loads((batch_dir / "receipt.json").read_text(encoding="utf-8"))
+    assert receipt["ok"] is False
+    assert receipt["completed"] == 1, "已完成件数必须精确, 不含糊"
+    assert receipt["failed"]["stable_id"] == id_of(pv, "a2.md")
+    assert receipt["failed"]["index"] == 2
+    assert "journal" in receipt
+
+    r2 = run_apply(vault, pv, dec)  # 同输入重跑
+    assert r2.returncode == 0, r2.stdout + r2.stderr
+    assert only_batch_dir(vault) == batch_dir, "同输入必须落同一个批次目录"
+
+    for name, target in (("a3.md", "归档"), ("a2.md", "节点"), ("a1.md", "归档")):
+        assert (vault / target / name).is_file(), f"{name} 未落地"
+
+    rows = journal_rows(batch_dir)
+    done_ids = [r["stable_id"] for r in rows if r["state"] == "done"]
+    assert len(done_ids) == len(set(done_ids)), f"journal 出现重复 done 行: {done_ids}"
+    assert len(done_ids) == 3
+
+
+def test_half_written_journal_tail_is_sealed_and_rerun_completes(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "b1.md", "# b1\n", age_days=1)
+    mk(vault / INBOX / "b2.md", "# b2\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "b2.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "b1.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    blocked = vault / "节点"
+    orig_mode = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        assert run_apply(vault, pv, dec).returncode != 0
+    finally:
+        os.chmod(blocked, orig_mode)
+
+    batch_dir = only_batch_dir(vault)
+    jp = batch_dir / "journal.jsonl"
+    # 模拟掉电: 末尾留一条没写完、没换行结尾的半行
+    with open(jp, "ab") as f:
+        f.write(b'{"seq": 9, "state": "plan')
+
+    r2 = run_apply(vault, pv, dec)
+    assert r2.returncode == 0, r2.stdout + r2.stderr
+
+    raw = jp.read_text(encoding="utf-8")
+    parsed, bad = [], 0
+    for line in raw.split("\n"):
+        if not line.strip():
+            continue
+        try:
+            parsed.append(json.loads(line))
+        except json.JSONDecodeError:
+            bad += 1
+    assert bad == 1, "半行该被封口并忽略, 而不是污染后续记录"
+    done_ids = [r["stable_id"] for r in parsed if r.get("state") == "done"]
+    assert len(done_ids) == len(set(done_ids)) == 2
+
+
+def test_corrupt_middle_journal_line_is_refused(tmp_path):
+    """中间损坏 ≠ 掉电截断: 绝不猜, 整批拒绝。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "c1.md", "# c1\n", age_days=1)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "c1.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    jp = batch_dir / "journal.jsonl"
+    rows = jp.read_text(encoding="utf-8").split("\n")
+    rows.insert(1, "{坏行不是合法 JSON")
+    jp.write_text("\n".join(rows), encoding="utf-8")
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    assert "journal" in (r.stdout + r.stderr)
+
+
+# ───────────────────────── E. 准入次序 (全拒零写) ─────────────────────────
+
+
+def test_stale_preview_is_rejected_zero_write(tmp_path):
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "过期.md", "# 过期\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "过期.md"), "action": "copy", "target": "节点"}],
+    )
+    # preview 之后材料被改动 ⇒ preview 过期
+    src.write_text("# 过期\n\n又加了一段\n", encoding="utf-8")
+    before = snapshot(vault)
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    assert "preview" in (r.stdout + r.stderr)
+    assert snapshot(vault) == before
+    assert no_outputs(vault)
+
+
+def test_vault_fingerprint_mismatch_is_rejected_zero_write(tmp_path):
+    vault_a, out_a = base_vault(tmp_path / "A")
+    mk(vault_a / INBOX / "指纹.md", "# 指纹\n", age_days=3)
+    pv = make_preview(vault_a, out_a)
+
+    vault_b, _ = base_vault(tmp_path / "B")
+    mk(vault_b / INBOX / "指纹.md", "# 指纹\n", age_days=3)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "指纹.md"), "action": "copy", "target": "节点"}],
+    )
+    before = snapshot(vault_b)
+
+    r = run_apply(vault_b, pv, dec)  # 拿 A 的 preview 去动 B
+    assert r.returncode != 0
+    assert snapshot(vault_b) == before
+    assert no_outputs(vault_b)
+
+
+def test_unknown_stable_id_is_rejected_zero_write(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "已知.md", "# 已知\n", age_days=3)
+    pv = make_preview(vault, out)
+    before = snapshot(vault)
+    for bogus in ("inb1-deadbeefdeadbeef", id_of(pv, "已知.md") + "x"):
+        dec = write_decisions(
+            tmp_path / "d.json",
+            [{"stable_id": bogus, "action": "copy", "target": "节点"}],
+        )
+        r = run_apply(vault, pv, dec)
+        assert r.returncode != 0, f"未知 id {bogus} 该被拒"
+        assert snapshot(vault) == before
+        assert no_outputs(vault)
+
+
+def test_duplicate_stable_id_is_rejected_zero_write(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "重复.md", "# 重复\n", age_days=3)
+    pv = make_preview(vault, out)
+    sid = id_of(pv, "重复.md")
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": sid, "action": "copy", "target": "节点"},
+            {"stable_id": sid, "action": "move", "target": "归档"},
+        ],
+    )
+    before = snapshot(vault)
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    assert snapshot(vault) == before
+    assert no_outputs(vault)
+
+
+def test_target_escape_variants_are_rejected_zero_write(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "越界.md", "# 越界\n", age_days=3)
+    pv = make_preview(vault, out)
+    sid = id_of(pv, "越界.md")
+
+    outside = tmp_path / "vault-外"
+    outside.mkdir()
+    (vault / "指向外面").symlink_to(outside, target_is_directory=True)
+
+    before = snapshot(vault)
+    bad_targets = [
+        "../逃逸",
+        "节点/../../逃逸",
+        str(outside),  # 绝对路径
+        INBOX,  # 指回收件箱
+        f"{INBOX}/子目录",
+        ".obsidian/插件",
+        ".claude/scripts",
+        "outputs",
+        "outputs/clear-inbox",
+        "指向外面/落点",  # 祖先含 symlink
+    ]
+    for t in bad_targets:
+        dec = write_decisions(
+            tmp_path / "d.json",
+            [{"stable_id": sid, "action": "copy", "target": t}],
+        )
+        r = run_apply(vault, pv, dec)
+        assert r.returncode != 0, f"target={t!r} 该被拒"
+        assert snapshot(vault) == before, f"target={t!r} 拒绝路径必须零写"
+        assert no_outputs(vault), f"target={t!r} 不许建 outputs/"
+
+
+def test_source_swapped_to_symlink_after_preview_is_rejected(tmp_path):
+    """preview 之后把材料换成一条 symlink —— size/mtime 都对得上, 只有
+    `lstat` 分得出来。不查这一条, 「跟着链接走」就能把 vault 外的文件搬进来。"""
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "正常.md", "# 正常\n", age_days=4)
+    pv = make_preview(vault, out)
+    sid = id_of(pv, "正常.md")
+
+    # ⛔ 诱饵必须放在**收件箱内**且同字节同 mtime: 指向 vault 外的话, `source_path`
+    # 的 realpath 父目录检查会先把它拒掉, 本门就绿在更早的那道判据上 —— 把
+    # `check_source_fresh` 的 lstat 改成 stat 也照样绿 (Codex round-5 MEDIUM-4)。
+    # ⛔ 诱饵的 age_days 故意跟真身**不同**: 同龄的话两者 mtime 本来就撞在一起,
+    # 下面那一步「对齐」就成了空操作, 门会绿在巧合上而不是绿在 lstat 判据上
+    # （独立复核 L-5 实证: 原写法 `os.utime(decoy, ns=(decoy…,) * 2)` 是拿自己的
+    # mtime 盖自己, 一个字节都没改变）。
+    src_mtime_ns = src.stat().st_mtime_ns
+    decoy = mk(vault / INBOX / "诱饵.md", "# 正常\n", age_days=9)
+    assert decoy.stat().st_mtime_ns != src_mtime_ns, "对照没拉开, 下一步的对齐等于没做"
+    os.replace(src, tmp_path / "stash.md")  # 挪走真身, 不做物理删除
+    (vault / INBOX / "正常.md").symlink_to(decoy)
+    os.utime(decoy, ns=(src_mtime_ns, src_mtime_ns))  # 显式对齐到 preview 记下的那个 mtime
+    before = snapshot(vault)
+    assert (vault / INBOX / "正常.md").stat().st_size == decoy.stat().st_size
+    assert (vault / INBOX / "正常.md").stat().st_mtime_ns == src_mtime_ns, (
+        "新鲜度那道门会先把它拒掉, 本门就绿在更早的判据上了"
+    )
+    assert Path(os.path.realpath(vault / INBOX / "正常.md")).parent == (vault / INBOX).resolve()
+
+    dec = write_decisions(tmp_path / "d.json", [{"stable_id": sid, "action": "copy", "target": "节点"}])
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    assert snapshot(vault) == before
+    assert no_outputs(vault)
+
+
+def test_preexisting_destination_is_rejected_zero_write(tmp_path):
+    """dst 已被占 ⇒ 整批拒绝。没有这道守卫,「覆写幂等」就成了静默覆盖用户文件。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "同名.md", "# 收件箱那份\n", age_days=3)
+    mk(vault / "节点" / "同名.md", "# 用户早就有的那份\n", age_days=30)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "同名.md"), "action": "copy", "target": "节点"}],
+    )
+    before = snapshot(vault)
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    assert snapshot(vault) == before
+    assert no_outputs(vault)
+
+
+def test_failure_receipt_lists_precise_state(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "e1.md", "# e1\n", age_days=1)
+    mk(vault / INBOX / "e2.md", "# e2\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "e2.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "e1.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    blocked = vault / "节点"
+    orig_mode = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        r = run_apply(vault, pv, dec)
+    finally:
+        os.chmod(blocked, orig_mode)
+
+    assert r.returncode != 0
+    assert "完成" in (r.stdout + r.stderr) or "失败" in (r.stdout + r.stderr)
+    batch_dir = only_batch_dir(vault)
+    receipt = json.loads((batch_dir / "receipt.json").read_text(encoding="utf-8"))
+    assert receipt["ok"] is False
+    assert receipt["completed"] == 1
+    assert receipt["failed"]["index"] == 2
+    assert receipt["failed"]["stable_id"] == id_of(pv, "e1.md")
+    assert receipt["failed"]["reason"]
+    assert (batch_dir / "receipt.md").is_file()
+    rows = journal_rows(batch_dir)
+    assert sum(1 for x in rows if x["state"] == "done") == 1, "前 k-1 件必须已落 done"
+
+
+# ───────────────────────── provenance 的字节纪律 ─────────────────────────
+
+
+def test_provenance_preserves_crlf_and_skips_non_utf8(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk_bytes(
+        vault / INBOX / "回车.md",
+        b"---\r\ntitle: CRLF\r\n---\r\n\r\n# CRLF \xe6\xad\xa3\xe6\x96\x87\r\n",
+        age_days=2,
+    )
+    mk_bytes(vault / INBOX / "乱码.md", b"\xff\xfe\x00bad bytes\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "回车.md"), "action": "copy", "target": "节点"},
+            {"stable_id": id_of(pv, "乱码.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+
+    crlf = (vault / "节点" / "回车.md").read_bytes()
+    assert b"clear_inbox_provenance:" in crlf
+    assert b"\r\n" in crlf
+    assert crlf.count(b"\n") == crlf.count(b"\r\n"), "不得把 CRLF 归一成 LF"
+
+    garbled = vault / "节点" / "乱码.md"
+    assert garbled.read_bytes() == b"\xff\xfe\x00bad bytes\n", (
+        "非 UTF-8 文件必须原样复制, 不写 provenance、不改一个字节"
+    )
+    batch_dir = only_batch_dir(vault)
+    rows = {r["stable_id"]: r for r in journal_rows(batch_dir) if r["state"] == "done"}
+    skipped = [r for r in rows.values() if str(r.get("provenance", "")).startswith("skipped")]
+    assert skipped, "跳过 provenance 必须在 journal 里如实留痕"
+
+
+def test_provenance_is_idempotent_on_rerun(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "幂等.md", "# 幂等\n\n正文\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "幂等.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    dst = vault / "节点" / "幂等.md"
+    first = dst.read_bytes()
+    assert run_apply(vault, pv, dec).returncode == 0
+    assert dst.read_bytes() == first, "重跑同输入必须逐字节幂等"
+    assert first.count(b"clear_inbox_provenance") == 1
+
+
+# ───────────────────────── F. 结构门入树 ─────────────────────────
+
+
+def test_no_delete_primitives_in_new_scripts(tmp_path):
+    """F2: 默认路径 0 物理删除。数 AST Call 节点, 并带同跑验伪锚。"""
+    for p in NEW_SCRIPTS:
+        require_script(p)
+    probe = tmp_path / "probe_rm.py"
+    probe.write_text("import os, shutil\nos.remove('x')\nshutil.rmtree('y')\n", encoding="utf-8")
+    assert ast_delete_call_count([probe]) == 2, "验伪锚: 门必须真数得到 Call 节点"
+    assert ast_delete_call_count(NEW_SCRIPTS) == 0, "两份新脚本的默认路径上不得出现任何物理删除原语"
+
+
+def test_apply_does_not_consume_stripped_text_fields(tmp_path):
+    """F4: 执行侧对 preview 里经裸 .strip() 的自由文本字段零消费。"""
+    require_script(APPLY_SCRIPT)
+    probe = tmp_path / "probe_basis.py"
+    probe.write_text('it = {}\nx = it["basis"]\n', encoding="utf-8")
+    assert ast_string_constants(probe) & STRIPPED_TEXT_FIELDS == {"basis"}, "验伪锚: 门必须真抓得到字段名常量"
+    hit = sorted(ast_string_constants(APPLY_SCRIPT) & STRIPPED_TEXT_FIELDS)
+    assert hit == [], f"执行侧消费了经 strip 的文本字段: {hit}"
+
+
+def test_no_bytecode_cache_written_into_vault_scripts(tmp_path):
+    """⛔ 被测脚本会用 spec_from_file_location 加载兄弟模块 —— 默认会在**vault 里**
+    落 __pycache__。零写侧不是「不改用户的 md」, 是「除产物外一个字节都不落」。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "缓存.md", "# 缓存\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "缓存.md"), "action": "copy", "target": "节点"}],
+    )
+    watched = (
+        REPO_ROOT / "canvas-vault" / ".claude" / "scripts",
+        SKILLS / "clear-inbox" / "scripts",
+        SKILLS / "board-split" / "scripts",
+    )
+    before = {d: sorted(p.name for p in d.rglob("*")) for d in watched}
+    # ⛔ 必须把 PYTHONDONTWRITEBYTECODE 摘掉再跑 —— 留着它, 保护来自**跑法**而不是
+    # 被测脚本, 这条门就恒绿在别人的功劳上 (假绿)。
+    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
+    assert "PYTHONDONTWRITEBYTECODE" not in env
+    assert run_apply(vault, pv, dec, env=env).returncode == 0
+    for d in watched:
+        assert sorted(p.name for p in d.rglob("*")) == before[d], f"被测脚本往 vault 目录里落了文件: {d}"
+
+
+def test_apply_has_no_skill_md_and_only_two_scripts():
+    """scripts-only: 不加 SKILL.md (会触 EXPECTED_SKILLS 9 份漂移)。"""
+    skill_dir = SKILLS / "clear-inbox"
+    require_script(APPLY_SCRIPT)
+    assert not (skill_dir / "SKILL.md").exists()
+    assert sorted(p.name for p in skill_dir.iterdir()) == ["scripts"]
+    assert sorted(p.name for p in (skill_dir / "scripts").iterdir()) == [
+        "inbox_apply.py",
+        "inbox_preview.py",
+    ]
+
+
+def test_skip_action_writes_nothing_but_journal(tmp_path):
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "留原地.md", "# 留原地\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "留原地.md"), "action": "skip"}],
+    )
+    before = snapshot(vault, skip=("outputs",))
+    r = run_apply(vault, pv, dec)
+    assert r.returncode == 0, r.stdout + r.stderr
+    assert snapshot(vault, skip=("outputs",)) == before, "skip 不许动 vault 任何文件"
+    rows = journal_rows(only_batch_dir(vault))
+    assert any(x["op"] == "skip" and x["state"] == "done" for x in rows)
+
+
+# ─────────── Codex round-1 的 15 条意见: 每条一道门 ───────────
+#
+# ⛔ 修完不配门 = 这些路径从此无人看管: 结构变了、行为没门盯着, 下一个人重构时
+# 全绿却是假修复。下面每一条都点名它锁住的是哪一条意见。
+
+
+def load_journal_module():
+    """把共用模块当模块加载 —— 有些性质 (frontmatter 文本处理) 在函数层面判最准。"""
+    require_script(JOURNAL_SCRIPT)
+    spec = importlib.util.spec_from_file_location("undo_journal_under_test", JOURNAL_SCRIPT)
+    mod = importlib.util.module_from_spec(spec)
+    prev = sys.dont_write_bytecode
+    sys.dont_write_bytecode = True
+    try:
+        spec.loader.exec_module(mod)
+    finally:
+        sys.dont_write_bytecode = prev
+    return mod
+
+
+def rewrite_journal(batch_dir: Path, rows: list[dict]) -> None:
+    jp = batch_dir / "journal.jsonl"
+    jp.write_text(
+        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
+        encoding="utf-8",
+    )
+
+
+def drop_rows(batch_dir: Path, state: str) -> None:
+    """摘掉某个状态的行 —— 模拟「动作做了但那一行还没落盘」的中断态。"""
+    rewrite_journal(batch_dir, [r for r in journal_rows(batch_dir) if r.get("state") != state])
+
+
+def test_planned_row_alone_does_not_authorize_overwriting_user_file(tmp_path):
+    """Codex #1: `planned` 行只说明「本批打算写这里」, 不证明「那里现在的东西是我的」。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "占位.md", "# 收件箱那份\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "占位.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    # ⛔ `drop_rows` 只摘 done —— round-4 之后状态机多了 `acting`, 所以这里剩下的是
+    # **planned + acting**, 最新状态是 acting 而不是 planned。原注释写「只剩 planned」
+    # 与事实不符, 会让人以为这条门在钉 planned 的语义（全卡复核 L8）。
+    drop_rows(batch_dir, "done")  # 剩 planned + acting = 「做了但没记 done」
+
+    dst = vault / "节点" / "占位.md"
+    dst.write_text("# 用户中断之后自己放的新内容\n", encoding="utf-8")
+    mine = dst.read_bytes()
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "落点上不是自家产物时必须拒绝, 而不是覆写"
+    assert dst.read_bytes() == mine, "用户的文件一个字节都不能被动"
+
+
+def test_recycle_destination_is_also_ownership_checked(tmp_path):
+    """Codex #2: 回收目录不是法外之地 —— 它的落点同样要过归属守卫。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "回收占位.md", "# 该回收\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "回收占位.md"), "action": "recycle", "confirm": True}],
+    )
+    assert run_apply(vault, pv, dec, "--confirm-recycle").returncode == 0
+    batch_dir = only_batch_dir(vault)
+    drop_rows(batch_dir, "done")
+
+    recycled = batch_dir / "recycle" / INBOX / "回收占位.md"
+    recycled.write_text("# 别的东西\n", encoding="utf-8")
+    mine = recycled.read_bytes()
+    mk(vault / INBOX / "回收占位.md", "# 该回收\n", age_days=3)  # 让源回到位
+
+    r = run_apply(vault, pv, dec, "--confirm-recycle")
+    assert r.returncode != 0
+    assert recycled.read_bytes() == mine
+
+
+def test_temp_file_name_is_unique_and_never_truncates_a_neighbour(tmp_path):
+    """Codex #3: 固定名 + O_TRUNC 会截断同名的用户文件; 唯一名 + O_EXCL 不会。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "临时.md", "# 临时\n", age_days=3)
+    # ⛔ 诱饵必须**恰好是旧实现会生成的那个名字**, 否则这条断言恒真、测不到任何东西。
+    # 原写法是 `临时.md.undo-journal.tmp`：少了开头的点、后缀又写成 `.tmp` 而不是
+    # `-tmp`，与固定名实现 `.{name}{TMP_SUFFIX}` 和当前唯一名实现
+    # `.{name}.{pid}-{uuid8}{TMP_SUFFIX}` 都不相等 —— 把实现改回固定名 + O_TRUNC，
+    # 103 条门仍然全绿，而用户那份文件会被清空后改名掉（全卡复核 HIGH-E 实测）。
+    uj_mod = load_journal_module()
+    bait = mk(vault / "节点" / f".临时.md{uj_mod.TMP_SUFFIX}", "用户自己的东西\n", age_days=30)
+    bait_bytes = bait.read_bytes()
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "临时.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    assert bait.read_bytes() == bait_bytes, "同名邻居被截断了"
+    # ⛔ 诱饵本身就带 TMP_SUFFIX（那正是它作为诱饵的意义），要把它排除在「残片」之外，
+    # 否则这条断言会因为诱饵存在而恒红 —— 换成正确诱饵之后才显形的连带影响。
+    leftovers = [p.name for p in (vault / "节点").iterdir() if uj_mod.TMP_SUFFIX in p.name and p.name != bait.name]
+    assert leftovers == [], f"成功路径不该留下临时文件: {leftovers}"
+
+
+def test_inbox_swapped_to_symlink_ancestor_is_rejected(tmp_path):
+    """Codex #4: 只查末段不够 —— 把整个收件箱搬走再用一条链接接回来, 末段仍是普通文件。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "祖先.md", "# 祖先\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "祖先.md"), "action": "copy", "target": "节点"}],
+    )
+    elsewhere = tmp_path / "收件箱搬到外面"
+    os.replace(vault / INBOX, elsewhere)
+    (vault / INBOX).symlink_to(elsewhere, target_is_directory=True)
+    before = snapshot(vault)
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    assert snapshot(vault) == before
+    assert no_outputs(vault)
+
+
+def test_undo_refuses_when_destination_became_a_symlink(tmp_path):
+    """Codex #4 的 undo 半边: 落点被换成链接时, 比 sha 会比到链接指向的那份上。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "链替.md", "# 链替\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "链替.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    dst = vault / "归档" / "链替.md"
+    # ⛔ 诱饵与落点**逐字节相同** —— 这样 sha 判据分不出来, 只有「这是不是一条
+    # symlink」这一问能挡住它。否则本门会绿在 sha 不符上, 换个内容相同的诱饵就穿了。
+    decoy = tmp_path / "诱饵.md"
+    decoy.write_bytes(dst.read_bytes())
+    os.utime(decoy, ns=(dst.stat().st_mtime_ns,) * 2)
+    os.replace(dst, tmp_path / "真身.md")
+    dst.symlink_to(decoy)
+    tampered = snapshot(vault, skip=("outputs",))
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert snapshot(vault, skip=("outputs",)) == tampered
+
+
+def test_undo_refuses_a_journal_from_another_vault(tmp_path):
+    """Codex #5: 一本 A 的账配上 --vault B, 会拿 B 的同名文件去还原 A 的记录。
+
+    ⚠️ 本门钉的是**行为**（拒绝 + 零动 B），不是某一道具体守卫。实测: 把
+    `_assert_bound_to` 的调用删掉, 本门**仍绿** —— 因为「创建上界 = 当前 vault」
+    那道守卫也会拒 (A 的批次目录不在 B 之内)。两道守卫各自独立成立, 但别把本门
+    当成「绑定检查承重」的证明。`_assert_bound_to` 的承重证明在
+    `test_journal_without_fingerprint_is_refused`: 删掉那次调用, 那一条会变红。
+    """
+    vault_a, out_a = base_vault(tmp_path / "A")
+    mk(vault_a / INBOX / "跨库.md", "# A 的\n", age_days=3)
+    pv_a = make_preview(vault_a, out_a)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv_a, "跨库.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault_a, pv_a, dec).returncode == 0
+    batch_dir = only_batch_dir(vault_a)
+
+    vault_b, _ = base_vault(tmp_path / "B")
+    # ⛔ 把 B 造成「除了不是同一个 vault, 其它一切都对得上」的样子: 落点与 A 的产物
+    # 逐字节相同（owned_product 分不出来）, 原路径也有一份与 A 原件逐字节+同 mtime
+    # 的文件（还原后的复核也分不出来）。这样只剩「这本账绑的是哪个 vault」这一问
+    # 能挡住它 —— 否则本门会绿在别的判据上, 把 _assert_bound_to 删掉也照样绿。
+    (vault_b / "节点").mkdir(parents=True, exist_ok=True)
+    (vault_b / "节点" / "跨库.md").write_bytes((vault_a / "节点" / "跨库.md").read_bytes())
+    a_src = vault_a / INBOX / "跨库.md"
+    b_src = vault_b / INBOX / "跨库.md"
+    b_src.write_bytes(a_src.read_bytes())
+    os.utime(b_src, ns=(a_src.stat().st_mtime_ns,) * 2)
+    os.chmod(b_src, stat.S_IMODE(a_src.stat().st_mode))
+    before_b = snapshot(vault_b)
+
+    u = run_undo(vault_b, batch_dir / "journal.jsonl")
+    assert u.returncode != 0, "账本没绑 vault 就会动到别处的同名文件"
+    assert snapshot(vault_b) == before_b
+
+
+def test_undo_refuses_modified_copy_product_before_moving_it(tmp_path):
+    """Codex #6: 「发现改动先拒绝」必须发生在搬动**之前**, 不是搬完再说。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "改过.md", "# 改过\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "改过.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    dst = vault / "节点" / "改过.md"
+    dst.write_text("# 用户后来改的\n", encoding="utf-8")
+    mine = dst.read_bytes()
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert dst.is_file() and dst.read_bytes() == mine, "拒绝就不该已经把它搬走了"
+    assert not (batch_dir / "recycle" / "undone").exists()
+
+
+def test_rerun_after_successful_move_and_recycle_is_idempotent(tmp_path):
+    """Codex #7: 取源动作做完之后, 源本来就不在了 —— 那不是 preview 过期。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "搬走.md", "# 搬走\n", age_days=2)
+    mk(vault / INBOX / "回收.md", "# 回收\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "回收.md"), "action": "recycle", "confirm": True},
+            {"stable_id": id_of(pv, "搬走.md"), "action": "move", "target": "归档"},
+        ],
+    )
+    assert run_apply(vault, pv, dec, "--confirm-recycle").returncode == 0
+    settled = snapshot(vault, skip=("outputs",))
+
+    r2 = run_apply(vault, pv, dec, "--confirm-recycle")
+    assert r2.returncode == 0, r2.stdout + r2.stderr
+    assert snapshot(vault, skip=("outputs",)) == settled
+    rows = journal_rows(only_batch_dir(vault))
+    done = [r["stable_id"] for r in rows if r.get("state") == "done"]
+    assert len(done) == len(set(done)) == 2
+
+
+def test_undo_covers_an_item_acted_but_not_committed(tmp_path):
+    """Codex #8 上半: 动了盘却没来得及记 done 的那一件, 撤销不能漏掉。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "漏记.md", "# 漏记\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "漏记.md"), "action": "move", "target": "归档"}],
+    )
+    before = snapshot(vault, skip=("outputs",))
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    drop_rows(batch_dir, "done")
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stdout + u.stderr
+    # ⛔ 只比文件层: `done` 行被摘掉 ⇒ 账上没有「op 之后各目录的 mtime」这个基准 ⇒
+    # 无法证明这期间没人动过那些目录 ⇒ 按新加的守卫**不改**它们的时间。这是对的:
+    # 拿不出证据就不要动, 而不是硬改回去把可能存在的改动盖掉。
+    after = snapshot(vault, skip=("outputs",))
+    assert files_only(after) == files_only(before)
+    receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert receipt["dirs_retimed"] == []
+    assert receipt["dirs_not_retimed"], "没改目录时间就必须在回执里说明为什么"
+
+
+def test_second_undo_after_lost_undone_row_completes(tmp_path):
+    """Codex #8 下半: 已搬回原路径、但 undone 行没落盘 —— 再撤销一次该补记而不是停住。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "补记.md", "# 补记\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "补记.md"), "action": "move", "target": "归档"}],
+    )
+    before = snapshot(vault, skip=("outputs",))
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    drop_rows(batch_dir, "undone")
+
+    u2 = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u2.returncode == 0, u2.stdout + u2.stderr
+    assert snapshot(vault, skip=("outputs",)) == before
+    assert any(r.get("state") == "undone" for r in journal_rows(batch_dir))
+
+
+def test_tail_line_missing_final_newline_is_sealed(tmp_path):
+    """Codex #9: 尾行 JSON 完整、只差结尾换行, 直接追加会把两条熔成一条。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "缺换行1.md", "# a\n", age_days=1)
+    mk(vault / INBOX / "缺换行2.md", "# b\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "缺换行2.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "缺换行1.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    blocked = vault / "节点"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        assert run_apply(vault, pv, dec).returncode != 0
+    finally:
+        os.chmod(blocked, orig)
+    jp = only_batch_dir(vault) / "journal.jsonl"
+    raw = jp.read_bytes()
+    assert raw.endswith(b"\n")
+    jp.write_bytes(raw[:-1])  # 只摘掉最后一个换行
+
+    assert run_apply(vault, pv, dec).returncode == 0
+    rows = journal_rows(only_batch_dir(vault))  # 解析不了就会在这里抛
+    done = [r["stable_id"] for r in rows if r.get("state") == "done"]
+    assert len(done) == len(set(done)) == 2
+
+
+def test_undo_seals_a_half_written_tail_before_appending(tmp_path):
+    """Codex #10: 撤销也要先封口 —— 否则 undone 行接到半行屁股上, 撤销记账被吞。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "撤销封口.md", "# 撤销封口\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "撤销封口.md"), "action": "move", "target": "归档"}],
+    )
+    before = snapshot(vault, skip=("outputs",))
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    jp = batch_dir / "journal.jsonl"
+    with open(jp, "ab") as f:
+        f.write(b'{"seq": 9, "state": "pla')
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stdout + u.stderr
+    assert snapshot(vault, skip=("outputs",)) == before
+    raw = jp.read_text(encoding="utf-8")
+    parsed, bad = [], 0
+    for line in raw.split("\n"):
+        if not line.strip():
+            continue
+        try:
+            parsed.append(json.loads(line))
+        except json.JSONDecodeError:
+            bad += 1
+    assert bad == 1, "半行该被封口, 而不是把 undone 行吃进去"
+    assert any(r.get("state") == "undone" for r in parsed), "撤销记账丢了"
+
+
+def test_file_mode_survives_move_and_undo(tmp_path):
+    """Codex #11: 溯源写入换掉的是 inode, 权限位不会自己跟过去。"""
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "私密.md", "# 私密\n\n正文\n", age_days=3)
+    os.chmod(src, 0o600)
+    before = snapshot(vault, skip=("outputs",))
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "私密.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    dst = vault / "归档" / "私密.md"
+    assert stat.S_IMODE(dst.stat().st_mode) == 0o600, "搬过去之后权限位被放宽了"
+
+    batch_dir = only_batch_dir(vault)
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    assert snapshot(vault, skip=("outputs",)) == before
+
+
+def test_receipt_pair_leaves_no_zero_byte_artifacts(tmp_path):
+    """Codex #12: 回执改成「两份 tmp 都写好再双双就位」—— 不预建 0 字节产物, 零 unlink。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "回执.md", "# 回执\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "回执.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    for stem in ("receipt.json", "receipt.md"):
+        p = batch_dir / stem
+        assert p.is_file() and p.stat().st_size > 0
+    strays = [p.name for p in batch_dir.rglob("*") if "undo-journal-tmp" in p.name]
+    assert strays == [], f"留下了临时文件: {strays}"
+    # ⛔ 行为面分不出新旧实现 (成功路径两者都不留残片; 出问题要并发才看得见), 所以
+    # 这一条靠结构判据钉: 执行侧不得再调那个「先 O_CREAT 建出来、失败按路径 unlink
+    # 回滚」的成对写 —— 那条回滚路径在并发下会删到别人刚放上去的同名目录项。
+    src_text = APPLY_SCRIPT.read_text(encoding="utf-8")
+    assert "write_pair_atomically_checked" not in src_text
+    assert "write_pair_atomically" in src_text
+
+
+def test_undo_does_not_retime_a_directory_touched_after_apply(tmp_path):
+    """Codex #13: 执行之后用户动过那个目录, 把时间改回批前会掩盖那次改动。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "目录时间.md", "# 目录时间\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "目录时间.md"), "action": "copy", "target": "节点"}],
+    )
+    pre_batch_ns = (vault / "节点").stat().st_mtime_ns
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    mk(vault / "节点" / "用户后来放的.md", "# 无关\n", age_days=0.1)
+
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert "节点" not in receipt["dirs_retimed"]
+    assert any(x["dir"] == "节点" for x in receipt["dirs_not_retimed"])
+    assert (vault / "节点" / "用户后来放的.md").is_file()
+    # ⛔ 光查回执不够: 回执照常分类、实盘却被改回批前值, 本门照样绿。必须查实盘。
+    assert (vault / "节点").stat().st_mtime_ns != pre_batch_ns
+
+
+def test_created_directories_are_reported_and_left_behind(tmp_path):
+    """Codex #14: 撤销不会删掉本次新建的目录 —— 那就必须在回执里说出口。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "新目录.md", "# 新目录\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "新目录.md"), "action": "copy", "target": "归档/二〇二六"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    receipt = json.loads((batch_dir / "receipt.json").read_text(encoding="utf-8"))
+    assert "归档/二〇二六" in receipt["created_dirs"]
+
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    assert (vault / "归档" / "二〇二六").is_dir(), "0 物理删除 ⇒ 空目录留着"
+    undo_receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert "归档/二〇二六" in undo_receipt["created_dirs"]
+
+
+def test_strip_provenance_handles_blank_lines_and_quoted_key(tmp_path):
+    """Codex #15: 块里夹空行不算出块; 引号形式的同名键也要认。"""
+    uj = load_journal_module()
+    nl = b"\n"
+    body = b'title: t\nclear_inbox_provenance:\n  batch_id: "x"\n\n  op: "copy"\nother_key:\n  kept: 1\n'
+    out = uj.strip_provenance_block(body, nl)
+    assert b"batch_id" not in out, "空行让它提前收手, 剩下的子行被下一个 mapping 收编了"
+    assert b'  op: "copy"' not in out
+    assert b"other_key:" in out and b"  kept: 1" in out
+
+    quoted = b'"clear_inbox_provenance":\n  batch_id: "x"\ntitle: t\n'
+    out2 = uj.strip_provenance_block(quoted, nl)
+    assert b"clear_inbox_provenance" not in out2
+    assert b"title: t" in out2
+
+
+def test_unterminated_frontmatter_is_left_untouched(tmp_path):
+    """自查: `---` 开了头却没收尾时, 在它上面再插一份会把原文挤进正文。看不懂就别动。"""
+    vault, out = base_vault(tmp_path)
+    raw = b"---\ntitle: never closed\n\n# \xe6\xad\xa3\xe6\x96\x87\n"
+    mk_bytes(vault / INBOX / "未收尾.md", raw, age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "未收尾.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    assert (vault / "节点" / "未收尾.md").read_bytes() == raw, "看不懂结构的文件被改了"
+    batch_dir = only_batch_dir(vault)
+    done = [r for r in journal_rows(batch_dir) if r.get("state") == "done"]
+    assert done[0]["provenance"] == "skipped:unterminated-frontmatter", "跳过必须在账上留痕"
+
+
+def test_work_dir_inside_inbox_is_rejected_zero_write(tmp_path):
+    """自查: 备份与回收件不能落进**正在清理的那个目录**。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "工作目录.md", "# 工作目录\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "工作目录.md"), "action": "copy", "target": "节点"}],
+    )
+    before = snapshot(vault)
+    r = run_apply(vault, pv, dec, "--work-dir", f"{INBOX}/work")
+    assert r.returncode != 0
+    assert snapshot(vault) == before
+    assert not (vault / INBOX / "work").exists()
+
+
+# ─────────── Codex round-2 的 18 条意见: 每条一道门 ───────────
+
+
+def journal_module_fixture(tmp_path):
+    """给模块级性质用的最小批次账本（不经 CLI）。"""
+    uj = load_journal_module()
+    root = tmp_path / "root"
+    root.mkdir()
+    j = uj.BatchJournal(root / "work", "b0", root=root, fingerprint="vf1-test")
+    j.ensure_dirs()
+    return uj, j, root
+
+
+def test_batch_marker_alone_is_not_ownership(tmp_path):
+    """Codex round-2 H1: 保留印记、改掉正文的产物**不是**自家产物。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "印记.md", "# 印记\n\n原正文\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "印记.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    # ⛔ `drop_rows` 只摘 done —— round-4 之后状态机多了 `acting`, 所以这里剩下的是
+    # **planned + acting**, 最新状态是 acting 而不是 planned。原注释写「只剩 planned」
+    # 与事实不符, 会让人以为这条门在钉 planned 的语义（全卡复核 L8）。
+    drop_rows(batch_dir, "done")  # 剩 planned + acting = 「做了但没记 done」
+
+    dst = vault / "节点" / "印记.md"
+    body = dst.read_text(encoding="utf-8")
+    assert batch_dir.name in body  # 印记确实还在
+    dst.write_text(body.replace("原正文", "用户后来改的正文"), encoding="utf-8")
+    mine = dst.read_bytes()
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "保留印记不等于归属 —— 这份被改过的内容不该被覆盖"
+    assert dst.read_bytes() == mine
+
+
+def test_undo_finishes_a_half_restored_item(tmp_path):
+    """Codex round-2 H2: 字节回来了、时间还没盖回去时, 重试必须**收尾**而不是谎报完成。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "半还原.md", "# 半还原\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "半还原.md"), "action": "move", "target": "归档"}],
+    )
+    before = snapshot(vault, skip=("outputs",))
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    # 人工造出「已搬回原路径、但时间没盖回去、undone 也没记」的中断态
+    os.replace(vault / "归档" / "半还原.md", vault / INBOX / "半还原.md")
+    os.utime(vault / INBOX / "半还原.md", (0, 0))
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stdout + u.stderr
+    assert files_only(snapshot(vault, skip=("outputs",))) == files_only(before)
+
+
+def test_undo_after_reapply_is_not_masked_by_old_undone(tmp_path):
+    """Codex round-2 H3: `planned → undone → done` 是合法历史, 不能被旧 undone 屏蔽。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "再执行.md", "# 再执行\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "再执行.md"), "action": "copy", "target": "节点"}],
+    )
+    before = snapshot(vault, skip=("outputs",))
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    assert not (vault / "节点" / "再执行.md").exists()
+
+    assert run_apply(vault, pv, dec).returncode == 0, "撤销之后再执行一次"
+    assert (vault / "节点" / "再执行.md").is_file()
+
+    u2 = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u2.returncode == 0, u2.stdout + u2.stderr
+    assert not (vault / "节点" / "再执行.md").exists(), "重新执行出来的那一份撤不掉"
+    assert files_only(snapshot(vault, skip=("outputs",))) == files_only(before)
+
+
+def test_read_only_markdown_can_still_be_undone(tmp_path):
+    """Codex round-2 H4: 保留权限不能换来「搬得动、撤不回」。"""
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "只读.md", "# 只读\n\n正文\n", age_days=3)
+    os.chmod(src, 0o444)
+    before = snapshot(vault, skip=("outputs",))
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "只读.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stdout + u.stderr
+    assert snapshot(vault, skip=("outputs",)) == before
+    assert stat.S_IMODE((vault / INBOX / "只读.md").stat().st_mode) == 0o444
+
+
+def test_undone_dir_swapped_to_symlink_is_rejected(tmp_path):
+    """Codex round-2 H5: 撤销的新落点也要过 symlink 守卫。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "外泄.md", "# 外泄\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "外泄.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    outside = tmp_path / "vault-外面"
+    outside.mkdir()
+    (batch_dir / "recycle" / "undone").symlink_to(outside, target_is_directory=True)
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert sorted(p.name for p in outside.iterdir()) == [], "产物被搬到 vault 外面去了"
+    assert (vault / "节点" / "外泄.md").is_file(), "拒绝就不该已经搬走"
+
+
+def test_undo_verifies_backup_before_overwriting(tmp_path):
+    """Codex round-2 H6: 备份要在**动手之前**验; 事后再验时正确产物已经被盖掉了。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "坏备份.md", "# 坏备份\n\n正文\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "坏备份.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    dst = vault / "归档" / "坏备份.md"
+    good = dst.read_bytes()
+    (batch_dir / "backup" / INBOX / "坏备份.md").write_bytes("备份被弄坏了\n".encode())
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert dst.is_file() and dst.read_bytes() == good, "正确的产物在拒绝之前就被覆盖了"
+    assert not (vault / INBOX / "坏备份.md").exists()
+
+
+def test_backup_write_never_clobbers_a_hardlinked_neighbour(tmp_path):
+    """Codex round-2 H7: 备份落点被换成指向用户文件的硬链接时, 不能连它一起改写。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    src = root / "源.md"
+    src.write_bytes(b"source bytes\n")
+    victim = root / "用户的东西.md"
+    victim.write_bytes(b"user content\n")
+    bak_path = j.backup_root / "源.md"
+    os.link(victim, bak_path)  # 备份落点 = 用户文件的另一个名字
+
+    j.backup(src, "源.md")
+    assert victim.read_bytes() == b"user content\n", "连着的那份用户文件被改写了"
+    assert bak_path.read_bytes() == b"source bytes\n"
+    assert os.stat(bak_path).st_ino != os.stat(victim).st_ino
+
+
+def test_journal_without_fingerprint_is_refused(tmp_path):
+    """Codex round-2 H8: 「指纹出现在集合里」对缺失与混合两种账本都放行。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "无指纹.md", "# 无指纹\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "无指纹.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    rows = journal_rows(batch_dir)
+    for r in rows:
+        r.pop("vault_fingerprint", None)
+    rewrite_journal(batch_dir, rows)
+    before = snapshot(vault, skip=("outputs",))
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert snapshot(vault, skip=("outputs",)) == before
+
+
+def test_tampered_preview_cannot_point_outside_the_inbox(tmp_path):
+    """Codex round-2 H9: preview 的 JSON 用户改得动, `rel_path` 必须卡形状。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "正常件.md", "# 正常件\n", age_days=3)
+    outside = mk(tmp_path / "vault外.md", "# 不该被搬走\n", age_days=3)
+    pv = make_preview(vault, out)
+    data = json.loads(pv.read_text(encoding="utf-8"))
+    st = outside.stat()
+    data["items"][0]["rel_path"] = "../vault外.md"
+    data["items"][0]["name"] = "vault外.md"
+    data["items"][0]["size_bytes"] = st.st_size
+    tampered = tmp_path / "tampered.json"
+    tampered.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": data["items"][0]["stable_id"], "action": "move", "target": "归档"}],
+    )
+    before = snapshot(vault)
+
+    r = run_apply(vault, tampered, dec)
+    assert r.returncode != 0
+    assert outside.is_file(), "vault 外的文件被搬走了"
+    assert snapshot(vault) == before
+    assert no_outputs(vault)
+
+
+def test_never_acted_planned_does_not_block_earlier_undo(tmp_path):
+    """Codex round-2 M1: 一条没动过盘的 planned 不该把前面已完成的挡在后面。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "先做.md", "# 先做\n", age_days=1)
+    mk(vault / INBOX / "没做.md", "# 没做\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "没做.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "先做.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    before = snapshot(vault, skip=("outputs",))
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    # ⛔ 夹具必须**真的**只剩 planned: 只删 done 的话 acting 还在, 走的是「动过盘」
+    # 那条分支, 本门就测不到它声称的 planned 分支 (Codex round-4 M4)。
+    rows = [r for r in journal_rows(batch_dir) if not (r.get("seq") == 2 and r.get("state") in ("done", "acting"))]
+    rewrite_journal(batch_dir, rows)
+    assert not any(r.get("seq") == 2 and r.get("state") == "acting" for r in rows)
+    # 既然「没执行过」, 盘上就不该有它的产物
+    os.replace(vault / "归档" / "没做.md", tmp_path / "假装没做过.md")
+    os.replace(vault / "节点" / "先做.md", batch_dir / "stale-先做.md")
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stdout + u.stderr
+    assert files_only(snapshot(vault, skip=("outputs",))) == files_only(before)
+
+
+def test_two_consecutive_bad_tail_lines_are_still_readable(tmp_path):
+    """Codex round-2 M2: 封口本身再被打断, 这本账不能就此读不回来。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "两次断.md", "# 两次断\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "两次断.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    jp = batch_dir / "journal.jsonl"
+    with open(jp, "ab") as f:
+        f.write(b'{"seq": 9, "state": "pla')  # 第一次掉电
+        f.write(b'\n{"schema_ver')  # 封口哨兵也写到一半
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode == 0, r.stdout + r.stderr
+    # ⛔ 这里不能用 journal_rows(): 它对每一行硬 json.loads, 两条坏尾行会让**测试自己**
+    # 炸掉, 于是判据测的是测试的健壮性而不是被测代码的。按封口口径宽容地读。
+    done = []
+    for line in (batch_dir / "journal.jsonl").read_text(encoding="utf-8").split("\n"):
+        if not line.strip():
+            continue
+        try:
+            row = json.loads(line)
+        except json.JSONDecodeError:
+            continue
+        if row.get("state") == "done":
+            done.append(row["stable_id"])
+    assert len(done) == len(set(done)) == 1
+
+
+def test_dir_retime_needs_an_unbroken_chain(tmp_path):
+    """Codex round-2 M3: 「最后一步之后没人动过」不等于「整批期间没人动过」。
+
+    ⛔ 两件的落点必须**不同**: 都指向被 chmod 的那个目录, 第一件就失败了, 「seq1 成功
+    seq2 失败」这个前提根本没发生（Codex round-3 M11 抓到的就是这个）。这里 seq1 落
+    `归档`（成功）、seq2 落 `节点`（被挡）, 共同触碰的目录是 `_待处理`。
+    实际触发的是 `pre != at_act` 那一支：seq2 的「之前」是上一次跑留下的陈旧读数。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "链1.md", "# 链1\n", age_days=1)
+    mk(vault / INBOX / "链2.md", "# 链2\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "链2.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "链1.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    pre_batch_ns = (vault / INBOX).stat().st_mtime_ns
+    blocked = vault / "节点"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        assert run_apply(vault, pv, dec).returncode != 0  # seq1 成功, seq2 失败
+    finally:
+        os.chmod(blocked, orig)
+    assert (vault / "归档" / "链2.md").is_file(), "前提: 第一件确实成功了"
+    # 两步之间用户往共同触碰的那个目录里放了东西
+    mk(vault / INBOX / "批中插入.md", "# 批中插入\n", age_days=0.1)
+    assert run_apply(vault, pv, dec).returncode == 0
+
+    batch_dir = only_batch_dir(vault)
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert INBOX not in receipt["dirs_retimed"], "链断了还把目录时间改回去 = 掩盖了那次插入"
+    assert any(x["dir"] == INBOX for x in receipt["dirs_not_retimed"])
+    assert (vault / INBOX / "批中插入.md").is_file()
+    assert (vault / INBOX).stat().st_mtime_ns != pre_batch_ns, "实盘时间被改回批前值了"
+
+
+def test_strip_provenance_handles_comment_lines(tmp_path):
+    """Codex round-2 M4: 块里夹一行顶格注释同样不算出块。"""
+    uj = load_journal_module()
+    body = b'title: t\nclear_inbox_provenance:\n  batch_id: "x"\n# a comment\n  op: "copy"\nother_key:\n  kept: 1\n'
+    out = uj.strip_provenance_block(body, b"\n")
+    assert b"batch_id" not in out
+    assert b'  op: "copy"' not in out
+    assert b"other_key:" in out and b"  kept: 1" in out
+
+
+def test_settled_link_rechecks_the_hardlink_relation(tmp_path):
+    """Codex round-2 M7: 硬链接的「完成」是一种关系, 不只是一份内容。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "关系.md", "# 关系\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "关系.md"), "action": "link", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    src = vault / INBOX / "关系.md"
+    os.replace(src, tmp_path / "原件挪走.md")
+    (vault / INBOX / "关系.md").write_text("# 关系\n", encoding="utf-8")  # 同内容, 不同 inode
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "硬链接关系已断, 不该报完成"
+
+
+def test_failed_pair_publish_parks_its_tmp(tmp_path):
+    """Codex round-2 L1: 最后那一步 os.replace 失败时, tmp 也要进 stale/。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    (j.batch_dir / "receipt.md").mkdir()  # 让第二份的就位必然失败
+    try:
+        uj.write_pair_atomically(
+            [(j.batch_dir / "receipt.json", b"{}\n"), (j.batch_dir / "receipt.md", b"# x\n")],
+            j.stale_root,
+        )
+        raise AssertionError("该失败却成功了")
+    except (OSError, uj.JournalError):
+        pass
+    strays = [p for p in j.batch_dir.iterdir() if uj.TMP_SUFFIX in p.name]
+    assert strays == [], f"残片留在批次目录里: {strays}"
+    assert j.stale_root.is_dir() and any(j.stale_root.iterdir()), "残片该进 stale/ 留痕"
+
+
+def test_rerun_receipt_keeps_created_dirs(tmp_path):
+    """Codex round-2 L2: 重跑不能把「本次新建的目录」这条如实声明抹掉。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "重跑目录.md", "# 重跑目录\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "重跑目录.md"), "action": "copy", "target": "归档/新层"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    receipt = json.loads((batch_dir / "receipt.json").read_text(encoding="utf-8"))
+    assert "归档/新层" in receipt["created_dirs"]
+
+
+# ─────────── Codex round-3 的 14 条意见: 每条一道门 ───────────
+
+
+def test_undo_touches_nothing_when_source_became_a_symlink(tmp_path):
+    """round-3 H1: chmod/utime 跟随 symlink —— 拒绝必须发生在动手之前。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "源链.md", "# 源链\n", age_days=3)
+    outside = mk(tmp_path / "vault外的东西.md", "# 别人的\n", age_days=30)
+    os.chmod(outside, 0o644)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "源链.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    os.replace(vault / INBOX / "源链.md", tmp_path / "真身.md")
+    (vault / INBOX / "源链.md").symlink_to(outside)
+    before_mode = stat.S_IMODE(outside.stat().st_mode)
+    before_ns = outside.stat().st_mtime_ns
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert stat.S_IMODE(outside.stat().st_mode) == before_mode, "拒绝之前已经改了别人的权限"
+    assert outside.stat().st_mtime_ns == before_ns, "拒绝之前已经改了别人的时间"
+    # ⛔ 还要断言**产物没被搬走**: 只查外部文件的话, 删掉「搬产物之前先验源」那道
+    # 检查, 后面的 _finish_restore 仍会拒绝, 本门照样绿 —— 而产物已经进 undone 了
+    # (Codex round-4 M7)。
+    assert (vault / "节点" / "源链.md").is_file(), "拒绝了, 却已经把产物搬走"
+    assert not (batch_dir / "recycle" / "undone").exists()
+
+
+def test_planned_row_claims_no_destination_at_all(tmp_path):
+    """round-3 H2: 还没动盘的 planned 不该认领落点上任何东西, 哪怕字节一样。"""
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "同字节.md", "# 同字节\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "同字节.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    # 只留 planned（排了期但还没动盘）
+    rewrite_journal(batch_dir, [r for r in journal_rows(batch_dir) if r.get("state") == "planned"])
+    dst = vault / "节点" / "同字节.md"
+    dst.write_bytes(src.read_bytes())  # 用户自己放了一份逐字节相同的独立文件
+    mine = dst.read_bytes()
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "planned 阶段落点上不该有我们的东西, 出现了就得停下问"
+    assert dst.read_bytes() == mine
+
+
+def test_backup_path_holding_a_user_file_is_parked_not_replaced(tmp_path):
+    """round-3 H3: 备份落点上那份独立的用户文件不能被 os.replace 换掉。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    src = root / "源.md"
+    src.write_bytes(b"source bytes\n")
+    bak_path = j.backup_root / "源.md"
+    bak_path.write_bytes(b"user put this here\n")
+
+    j.backup(src, "源.md")
+    assert bak_path.read_bytes() == b"source bytes\n"
+    parked = [p for p in j.stale_root.rglob("*") if p.is_file()]
+    assert any(p.read_bytes() == b"user put this here\n" for p in parked), "用户那份被换掉且没留痕"
+
+
+def test_stale_dir_swapped_to_symlink_keeps_residue_inside(tmp_path):
+    """round-3 H4: stale/ 被指到 vault 外时, 残片就地留着, 不搬出去。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    outside = root.parent / "外面"
+    outside.mkdir()
+    j.stale_root.symlink_to(outside, target_is_directory=True)
+    (j.batch_dir / "receipt.md").mkdir()  # 让第二份就位必然失败
+    try:
+        uj.write_pair_atomically(
+            [(j.batch_dir / "receipt.json", b"{}\n"), (j.batch_dir / "receipt.md", b"# x\n")],
+            j.stale_root,
+        )
+        raise AssertionError("该失败却成功了 —— 下面那条「期望为空」的断言会空转")
+    except (OSError, uj.JournalError) as e:
+        notes = " ".join(getattr(e, "__notes__", []) or [])
+    # ⛔ 「期望为空」的判据必须先证**输入面非空**: 没有上面那个哨兵、也不看残片去了哪,
+    # 这条断言在「压根没产生残片」时同样绿（全卡复核 L11）。
+    assert uj.TMP_SUFFIX in notes, f"没有残片产生, 这条门在空转: {notes}"
+    assert sorted(p.name for p in outside.iterdir()) == [], "残片被搬到 vault 外面去了"
+    inside = [p.name for p in j.batch_dir.iterdir() if uj.TMP_SUFFIX in p.name]
+    assert inside, "残片既不在 vault 外、也不在批次目录里 —— 它去哪了?"
+
+
+def test_sealed_bad_line_stays_readable_after_more_records(tmp_path):
+    """round-3 H5: 封过口的坏行, 后面再写记录也不能变回「中间损坏」。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "封口后.md", "# 封口后\n", age_days=1)
+    mk(vault / INBOX / "封口后2.md", "# 封口后2\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "封口后2.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "封口后.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    blocked = vault / "节点"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        assert run_apply(vault, pv, dec).returncode != 0
+    finally:
+        os.chmod(blocked, orig)
+    batch_dir = only_batch_dir(vault)
+    with open(batch_dir / "journal.jsonl", "ab") as f:
+        f.write(b'{"seq": 9, "state": "pla')
+
+    assert run_apply(vault, pv, dec).returncode == 0, "第一次: 封口 + 补做"
+    # 封口之后账上又写了正常记录 —— 再读一次必须仍然读得回来
+    r3 = run_apply(vault, pv, dec)
+    assert r3.returncode == 0, r3.stdout + r3.stderr
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stdout + u.stderr
+
+
+def test_resume_writes_the_provenance_the_journal_promised(tmp_path):
+    """round-3 H6: 续跑要用账上记的 prov_meta, 不是本次重算的。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "续跑溯源.md", "# 续跑溯源\n\n正文\n", age_days=1)
+    mk(vault / INBOX / "挡路.md", "# 挡路\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "挡路.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "续跑溯源.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    blocked = vault / "节点"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        assert run_apply(vault, pv, dec, now=NOW_ISO).returncode != 0
+    finally:
+        os.chmod(blocked, orig)
+    batch_dir = only_batch_dir(vault)
+    planned = [r for r in journal_rows(batch_dir) if r.get("seq") == 2 and r.get("state") == "planned"][0]
+    promised = planned["prov_meta"]["applied_at_utc"]
+
+    # ⛔ 换一个 --now 续跑: 账上承诺的时刻不能因为这次跑得晚而改变
+    later = "2026-09-19T08:00:00+08:00"
+    r2 = run_apply(vault, pv, dec, now=later)
+    assert r2.returncode == 0, r2.stdout + r2.stderr
+    body = (vault / "节点" / "续跑溯源.md").read_text(encoding="utf-8")
+    assert promised in body, f"写进去的溯源时刻与账上承诺的不一致: 期望 {promised}"
+
+    u = run_undo(vault, batch_dir / "journal.jsonl", now=later)
+    assert u.returncode == 0, u.stdout + u.stderr
+
+
+def test_undo_of_an_acting_move_with_provenance_completes(tmp_path):
+    """round-3 H7: 动过盘但没记 done 的 move, 产物带着溯源, 撤销照样要回得去。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "半态溯源.md", "# 半态溯源\n\n正文\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "半态溯源.md"), "action": "move", "target": "归档"}],
+    )
+    before = snapshot(vault, skip=("outputs",))
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    drop_rows(batch_dir, "done")  # 只剩 planned + acting
+    # 人工造出「已搬回原路径、溯源还留在上面」的中断态
+    os.replace(vault / "归档" / "半态溯源.md", vault / INBOX / "半态溯源.md")
+    assert "clear_inbox_provenance" in (vault / INBOX / "半态溯源.md").read_text(encoding="utf-8")
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stdout + u.stderr
+    # ⛔ 只比文件层: done 行被摘掉 ⇒ 账上没有「操作后的目录时间」这个基准 ⇒ 按守卫
+    # **不改**目录时间（拿不出证据就不动）。这与 test_undo_covers_an_item_... 同理。
+    assert files_only(snapshot(vault, skip=("outputs",))) == files_only(before)
+    receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert receipt["dirs_not_retimed"], "没改目录时间就必须在回执里说明为什么"
+
+
+def test_no_raw_copyfile_on_production_paths(tmp_path):
+    """round-3 H8: 正式落点一律经 tmp + os.replace, 不留半截文件。"""
+    for f in NEW_SCRIPTS:
+        require_script(f)
+        src = f.read_text(encoding="utf-8")
+        assert "shutil.copyfile(" not in src, f"{f.name} 仍在用会先截断的 copyfile"
+    uj = load_journal_module()
+    # ⛔ 只查拼写不够: 把 helper 改成 open(dst,"wb") + copyfileobj 本门照样绿
+    # (Codex round-4 M5)。加一条行为断言 —— 原子替换必然换 inode, 截断式复制不会。
+    src = tmp_path / "src.bin"
+    src.write_bytes(b"new content\n")
+    dst = tmp_path / "dst.bin"
+    dst.write_bytes(b"old content\n")
+    old_ino = dst.stat().st_ino
+    uj.copy_file_atomically(src, dst, tmp_path / "stale")
+    assert dst.read_bytes() == b"new content\n"
+    assert dst.stat().st_ino != old_ino, "落点 inode 没变 = 是就地截断写, 不是原子替换"
+
+
+def test_apply_also_refuses_a_journal_without_fingerprint(tmp_path):
+    """round-3 H9: 绑定检查只在撤销侧做是不够的 —— apply 也采信这些行。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "apply绑定.md", "# apply绑定\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "apply绑定.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    rows = journal_rows(batch_dir)
+    for r in rows:
+        r.pop("vault_fingerprint", None)
+    rewrite_journal(batch_dir, rows)
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "apply 拿一本不绑 vault 的账也能报完成"
+
+
+def test_dir_chain_slot_is_keyed_by_seq(tmp_path):
+    """round-3 M10: 写 at_act/post 时盲取 chain[-1] 会污染上一步的环。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    d = root / "甲目录"
+    d.mkdir()
+    # ⛔ 把实盘时间调成第 2 件那个读数: 这样「现值 ≠ 最后一环」那道**更早**的判据
+    # 失效, 只剩「这一环属不属于当前 seq」能分辨 —— 否则本门会绿在旧码上。
+    os.utime(d, ns=(999, 999))
+    rows = [
+        {
+            "seq": 1,
+            "state": uj.STATE_DONE,
+            "op": "copy",
+            "dir_mtimes": {"甲目录": 100},
+            "dir_mtimes_at_act": {"甲目录": 100},
+            "dir_mtimes_after": {"甲目录": 200},
+            "vault_fingerprint": "vf1-test",
+        },
+        {
+            "seq": 2,
+            "state": uj.STATE_DONE,
+            "op": "copy",
+            "dir_mtimes": {},
+            "dir_mtimes_at_act": {},
+            "dir_mtimes_after": {"甲目录": 999},  # 它自己的 pre 里没有这个目录
+            "vault_fingerprint": "vf1-test",
+        },
+    ]
+    assert d.stat().st_mtime_ns == 999, "前提: 实盘时间 == 第 2 件的 post"
+    to_retime, skipped = j._dir_retime_plan(rows, root)
+    assert "甲目录" not in to_retime, "第 2 件的读数被写进了第 1 件的环"
+    assert any(x["dir"] == "甲目录" for x in skipped)
+
+
+def test_non_markdown_is_skipped_without_reading_it(tmp_path):
+    """round-3 M12: 后缀判断要在整份读入之前 —— 大 PDF/视频不该进内存。"""
+    uj = load_journal_module()
+    big = tmp_path / "不是markdown.pdf"
+    big.write_bytes(b"%PDF-1.4\n")
+    os.chmod(big, 0o000)  # 读不了: 一旦它去读就会抛
+    try:
+        assert uj.write_provenance(big, {"batch_id": "x"}) == "skipped:not-markdown"
+    finally:
+        os.chmod(big, 0o644)
+
+
+def test_first_receipt_failure_parks_the_other_tmp(tmp_path):
+    """round-3 L13: 第一份就位失败时, 还没发布的那几份 tmp 也要进 stale/。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    (j.batch_dir / "receipt.json").mkdir()  # 让**第一份**就位失败
+    try:
+        uj.write_pair_atomically(
+            [(j.batch_dir / "receipt.json", b"{}\n"), (j.batch_dir / "receipt.md", b"# x\n")],
+            j.stale_root,
+        )
+        raise AssertionError("该失败却成功了")
+    except (OSError, uj.JournalError):
+        pass
+    strays = [p.name for p in j.batch_dir.iterdir() if uj.TMP_SUFFIX in p.name]
+    assert strays == [], f"第二份 tmp 留在正式目录里: {strays}"
+    assert len([p for p in j.stale_root.iterdir() if p.is_file()]) == 2
+
+
+def test_second_undo_still_reports_created_dirs(tmp_path):
+    """round-3 L14: 再撤销一次不能把「留下的空目录」这条声明抹掉。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "二次撤销.md", "# 二次撤销\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "二次撤销.md"), "action": "copy", "target": "归档/新层二"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert "归档/新层二" in receipt["created_dirs"]
+    assert (vault / "归档" / "新层二").is_dir()
+
+
+# ─────────── Codex round-4 的 14 条意见: 每条一道门 ───────────
+
+
+def test_equal_length_edit_after_acting_is_refused(tmp_path):
+    """round-4 H1: 大小 + 秒级 mtime 相等就放行 —— 等长改写能穿过去。"""
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "等长.md", "# AAAA\n", age_days=3)
+    mtime_ns = src.stat().st_mtime_ns
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "等长.md"), "action": "move", "target": "节点"}],
+    )
+    blocked = vault / "节点"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        assert run_apply(vault, pv, dec).returncode != 0
+    finally:
+        os.chmod(blocked, orig)
+    batch_dir = only_batch_dir(vault)
+    assert any(r.get("state") == "acting" for r in journal_rows(batch_dir))
+
+    src.write_text("# BBBB\n", encoding="utf-8")  # 等长
+    os.utime(src, ns=(mtime_ns, mtime_ns))  # 连 mtime 都保持
+    assert src.stat().st_size == 7
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "账上已有 sha 却还信粗判据 —— 新内容会被旧内容盖掉"
+    assert src.read_text(encoding="utf-8") == "# BBBB\n"
+
+
+def test_backup_reuse_requires_an_independent_inode(tmp_path):
+    """round-4 H2: 内容一样但与别处共享 inode 的「备份」不是独立快照。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    src = root / "源.md"
+    src.write_bytes(b"same bytes\n")
+    victim = root / "用户的东西.md"
+    victim.write_bytes(b"same bytes\n")  # 与源**逐字节相同**
+    os.utime(victim, ns=(123456789, 123456789))
+    victim_ns = victim.stat().st_mtime_ns
+    bak_path = j.backup_root / "源.md"
+    os.link(victim, bak_path)
+
+    j.backup(src, "源.md")
+    assert victim.stat().st_mtime_ns == victim_ns, "沿用共享 inode 的备份, 改到了用户文件的时间"
+    assert os.lstat(bak_path).st_nlink == 1, "备份仍与别处共享 inode = 不是独立快照"
+    assert os.stat(bak_path).st_ino != os.stat(victim).st_ino
+
+
+def test_seal_covers_only_the_lines_it_sealed(tmp_path):
+    """round-4 H3: 封口哨兵只覆盖它当初封的那几行, 不是「往前跨过任意坏行」。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    good = {"seq": 1, "state": uj.STATE_ACTING, "op": "copy", "vault_fingerprint": "vf1-test", "batch_id": "b0"}
+    rows = [
+        json.dumps(
+            {"seq": 1, "state": uj.STATE_PLANNED, "op": "copy", "vault_fingerprint": "vf1-test", "batch_id": "b0"},
+            ensure_ascii=False,
+        ),
+        json.dumps(good, ensure_ascii=False),
+        '{"seq": 1, "state": "do',  # 半条 done —— 当初封的就是这一条
+        json.dumps({"state": uj.STATE_TAIL_SEALED, "sealed_bad_count": 1}, ensure_ascii=False),
+    ]
+    j.journal_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
+    assert len(j.read_rows()) == 3, "前提: 这份账本来读得回来"
+
+    # 现在让那条**本来完整**的 acting 行也坏掉 —— 它不在哨兵的覆盖面里
+    rows[1] = '{"seq": 1, "state": "acti'
+    j.journal_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
+    try:
+        j.read_rows()
+        raise AssertionError("后来损坏的完整业务行被当成旧封口区放过了")
+    except uj.JournalError as e:
+        assert "中间存在损坏记录" in str(e)
+
+
+def test_rerun_after_action_completed_but_uncommitted(tmp_path):
+    """round-4 H4: 主动作做完、done 没落账时重跑, 自家产物不能被判成外来文件。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "未记账.md", "# 未记账\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "未记账.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    drop_rows(batch_dir, "done")  # 只剩 planned + acting, 产物仍在落点
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode == 0, r.stdout + r.stderr
+    assert (vault / "节点" / "未记账.md").is_file()
+
+
+def test_journal_from_another_batch_is_refused(tmp_path):
+    """round-4 H5: 同一个 vault 里还有「另一批」这回事 —— 绑定要连批次一起核。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "跨批.md", "# 跨批\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec_a = write_decisions(
+        tmp_path / "a.json",
+        [{"stable_id": id_of(pv, "跨批.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec_a).returncode == 0
+    batch_a = only_batch_dir(vault)
+    a_rows = journal_rows(batch_a)
+
+    dec_b = write_decisions(
+        tmp_path / "b.json",
+        [{"stable_id": id_of(pv, "跨批.md"), "action": "copy", "target": "归档"}],
+    )
+    # B 批的批次号由输入决定 —— 先跑一次拿到它的目录, 再把 A 的账原样塞进去
+    blocked = vault / "归档"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        run_apply(vault, pv, dec_b)
+    finally:
+        os.chmod(blocked, orig)
+    batch_b = next(d for d in work_root(vault).iterdir() if d.is_dir() and d != batch_a)
+    rewrite_journal(batch_b, a_rows)
+
+    r = run_apply(vault, pv, dec_b)
+    assert r.returncode != 0, "拿 A 批的账去复核 B 批, 会拿 A 的落点报完成"
+    assert not (vault / "归档" / "跨批.md").exists()
+
+
+def test_receipt_does_not_silently_overwrite_a_user_file(tmp_path):
+    """round-4 H6: 「产物可以重新生成」不构成覆盖它的理由 —— 那里可能是别人的文件。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    victim = j.batch_dir / "receipt.md"
+    victim.write_bytes("用户自己放的东西\n".encode())
+    uj.write_pair_atomically(
+        [(j.batch_dir / "receipt.json", b"{}\n"), (victim, b"# new\n")],
+        j.stale_root,
+    )
+    assert victim.read_bytes() == b"# new\n"
+    parked = [p.read_bytes() for p in j.stale_root.rglob("*") if p.is_file()]
+    assert "用户自己放的东西\n".encode() in parked, "被无声覆盖了, 没留痕"
+
+
+def test_unknown_state_is_treated_as_corruption(tmp_path):
+    """round-4 M1: 认不出来的 state 不能静默忽略 —— 那会让状态悄悄退回上一步。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    rows = [
+        json.dumps({"seq": 1, "state": uj.STATE_PLANNED, "op": "copy", "batch_id": "b0"}, ensure_ascii=False),
+        json.dumps({"seq": 1, "state": "actinh", "op": "copy", "batch_id": "b0"}, ensure_ascii=False),
+        json.dumps({"seq": 1, "state": uj.STATE_DONE, "op": "copy", "batch_id": "b0"}, ensure_ascii=False),
+    ]
+    j.journal_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
+    try:
+        j.read_rows()
+        raise AssertionError("拼错的 state 被当成不存在")
+    except uj.JournalError as e:
+        assert "认不出来" in str(e), str(e)
+
+    # ⛔ 账**尾**的未知 state 同样要拒。把它和「半行」用同一个哨兵值表示的话, 它会
+    # 顺带继承半行的尾部容忍 —— 一条完整但状态拼错的尾行就又被忽略, 最新状态悄悄
+    # 退回上一步 (Codex round-5 HIGH-3)。
+    tail_rows = [
+        json.dumps({"seq": 1, "state": uj.STATE_PLANNED, "op": "copy", "batch_id": "b0"}, ensure_ascii=False),
+        json.dumps({"seq": 1, "state": "actinh", "op": "copy", "batch_id": "b0"}, ensure_ascii=False),
+    ]
+    j.journal_path.write_text("\n".join(tail_rows) + "\n", encoding="utf-8")
+    try:
+        j.read_rows()
+        raise AssertionError("账尾的未知 state 被当成半行忽略了")
+    except uj.JournalError as e:
+        assert "认不出来" in str(e), str(e)
+
+
+def test_undo_requires_the_journal_file_itself(tmp_path):
+    """round-4 M2: 只取父目录再固定读 journal.jsonl = 用户指错文件也照样撤。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "指错.md", "# 指错\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "指错.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    before = snapshot(vault, skip=("outputs",))
+
+    u = run_undo(vault, batch_dir / "receipt.json")
+    assert u.returncode != 0, "指了 receipt.json 却把 journal.jsonl 撤了"
+    assert snapshot(vault, skip=("outputs",)) == before
+
+
+def test_backup_failure_still_produces_a_precise_receipt(tmp_path):
+    """round-4 M3: 备份/记账失败也要走失败回执流程, 不能直接抛出去。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "b先.md", "# b先\n", age_days=1)
+    mk(vault / INBOX / "b后.md", "# b后\n", age_days=2)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "b后.md"), "action": "copy", "target": "归档"},
+            {"stable_id": id_of(pv, "b先.md"), "action": "copy", "target": "节点"},
+        ],
+    )
+    # 先跑一次让批次目录成型, 再把第二件的备份落点预置成 symlink
+    blocked = vault / "节点"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        run_apply(vault, pv, dec)
+    finally:
+        os.chmod(blocked, orig)
+    batch_dir = only_batch_dir(vault)
+    drop_rows(batch_dir, "acting")
+    rewrite_journal(batch_dir, [r for r in journal_rows(batch_dir) if r.get("seq") != 2])
+    bak = batch_dir / "backup" / INBOX / "b先.md"
+    os.replace(bak, tmp_path / "旧备份.md")
+    bak.symlink_to(tmp_path / "旧备份.md")
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    receipt = json.loads((batch_dir / "receipt.json").read_text(encoding="utf-8"))
+    assert receipt["ok"] is False
+    assert receipt["failed"]["index"] == 2, "备份失败也要说清停在第几件"
+    assert receipt["completed"] == 1
+    # ⛔ 必须断言这份回执是**本次**写的: 否则旧码把异常直接抛出去时, 读到的是上一次
+    # 跑留下的那份回执, 上面三条照样成立 —— 绿在陈旧证据上 (Codex round-4 M3)。
+    assert "备份落点" in receipt["failed"]["reason"], receipt["failed"]["reason"]
+
+
+def test_dir_retime_rejects_a_broken_ring_chain(tmp_path):
+    """round-4 M6: 跨环断裂这一条要能**独立**承重 —— 别让别的条件先把它挡了。
+
+    ⚠️ 这是一道**补覆盖**的门, 不是修缺陷的门: 跨环比较自 round-3 起就是对的,
+    所以它在旧代码上也绿。它锁住的是「将来谁把这条比较删掉」。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    d = root / "乙目录"
+    d.mkdir()
+    os.utime(d, ns=(400, 400))  # 实盘 == 最后一环的 post
+    rows = [
+        {
+            "seq": 1,
+            "state": uj.STATE_DONE,
+            "op": "copy",
+            "dir_mtimes": {"乙目录": 100},
+            "dir_mtimes_at_act": {"乙目录": 100},  # pre == at_act, 这一条不触发
+            "dir_mtimes_after": {"乙目录": 200},
+            "vault_fingerprint": "vf1-test",
+        },
+        {
+            "seq": 2,
+            "state": uj.STATE_DONE,
+            "op": "copy",
+            "dir_mtimes": {"乙目录": 300},  # ≠ 上一步的 post(200) ⇒ 两步之间被动过
+            "dir_mtimes_at_act": {"乙目录": 300},
+            "dir_mtimes_after": {"乙目录": 400},
+            "vault_fingerprint": "vf1-test",
+        },
+    ]
+    to_retime, skipped = j._dir_retime_plan(rows, root)
+    assert "乙目录" not in to_retime
+    assert any(x["dir"] == "乙目录" and "之间" in x["why"] for x in skipped), skipped
+
+
+def test_park_failure_reports_where_the_residue_is(tmp_path):
+    """round-4 L1: 「就地留着」是安全选择, 但得说得出留在哪儿。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    outside = root.parent / "外面2"
+    outside.mkdir()
+    j.stale_root.symlink_to(outside, target_is_directory=True)
+    (j.batch_dir / "receipt.md").mkdir()
+    try:
+        uj.write_pair_atomically(
+            [(j.batch_dir / "receipt.json", b"{}\n"), (j.batch_dir / "receipt.md", b"# x\n")],
+            j.stale_root,
+        )
+        raise AssertionError("该失败却成功了")
+    except (OSError, uj.JournalError) as e:
+        notes = " ".join(getattr(e, "__notes__", []))
+        assert "残片位置" in notes, "调用方无从知道哪一份残片需要处理"
+        assert uj.TMP_SUFFIX in notes
+
+
+# ─────────── Codex round-5（末轮）的意见: 每条一道门 ───────────
+
+
+def test_receipt_refuses_when_the_foreign_file_cannot_be_parked(tmp_path):
+    """round-5 HIGH-1: 留存不成功就不许覆盖 —— 明知留不住还盖 = 无声弄丢。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    victim = j.batch_dir / "receipt.md"
+    victim.write_bytes("用户的东西\n".encode())
+    mine = victim.read_bytes()
+    # stale/ 被占成普通文件 ⇒ 停放必然失败
+    os.replace(j.stale_root, root / "stale-挪走") if j.stale_root.exists() else None
+    j.stale_root.write_bytes(b"not a dir\n")
+    try:
+        uj.write_pair_atomically(
+            [(j.batch_dir / "receipt.json", b"{}\n"), (victim, b"# new\n")],
+            j.stale_root,
+            owned_shas={},
+        )
+        raise AssertionError("留不住却还是覆盖了")
+    except (OSError, uj.JournalError):
+        pass
+    assert victim.read_bytes() == mine, "用户的文件被无声盖掉了"
+
+
+def test_provenance_write_does_not_park_the_business_file(tmp_path):
+    """round-5 HIGH-2: 留存逻辑的作用域只到回执, 不能碰业务文件。
+
+    round-5 曾把它接进通用的 `_replace_or_park`, 于是每写一次溯源就把刚复制好的
+    那一份挪进 stale/, 中间还留出「正式路径两头都不在」的窗口。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "作用域.md", "# 作用域\n\n正文\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "作用域.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    assert "clear_inbox_provenance" in (vault / "节点" / "作用域.md").read_text(encoding="utf-8")
+    stale = batch_dir / "stale"
+    parked = sorted(p.name for p in stale.rglob("*")) if stale.exists() else []
+    assert parked == [], f"业务文件被留存逻辑挪走了: {parked}"
+
+
+def test_rerun_does_not_pile_up_old_receipts(tmp_path):
+    """round-5 补答: 自家上一版回执直接让位, 不每次堆两份。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "不堆积.md", "# 不堆积\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "不堆积.md"), "action": "copy", "target": "节点"}],
+    )
+    for _ in range(3):
+        assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    stale = batch_dir / "stale"
+    piled = sorted(p.name for p in stale.rglob("*")) if stale.exists() else []
+    assert piled == [], f"重跑把旧回执堆进 stale/: {piled}"
+
+
+def test_sentinel_without_count_covers_exactly_one_line(tmp_path):
+    """独立复核 M-2: 没有计数的哨兵**只**覆盖紧邻的那一条坏行, 不往前跨整段。
+
+    曾经为了「兼容旧账本」把它放宽成「往前跨过整段连续坏行」—— 兼容面其实是空集
+    (本工具尚未发布), 换掉的却是 round-4 H3 判为 HIGH 的那条安全性质: 一条本来
+    **完整**的 acting 行后来损坏了, 只要它紧挨着旧封口区就会被一起放过, 于是最新
+    状态悄悄退回 planned, 撤销报「未执行」而产物还在。
+
+    两档场景一起断言: 只有一条坏行 ⇒ 照常读回（兼容面确实还在）;
+    多出一条 ⇒ 必须拒绝, 不许静默吞掉。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    planned = json.dumps({"seq": 1, "state": uj.STATE_PLANNED, "op": "copy", "batch_id": "b0"}, ensure_ascii=False)
+    done = json.dumps({"seq": 1, "state": uj.STATE_DONE, "op": "copy", "batch_id": "b0"}, ensure_ascii=False)
+    sentinel = json.dumps({"state": uj.STATE_TAIL_SEALED}, ensure_ascii=False)  # 无计数
+
+    # ① 对照档: 哨兵紧邻**一条**坏行 —— 当初封的就是它, 照常读回。
+    j.journal_path.write_text("\n".join([planned, '{"schema_ver', sentinel, done]) + "\n", encoding="utf-8")
+    states = [r.get("state") for r in j.read_rows()]
+    assert states == [uj.STATE_PLANNED, uj.STATE_TAIL_SEALED, uj.STATE_DONE], states
+
+    # ② 性质档: 哨兵前面**两条**坏行 —— 靠外那条 (= 后来才损坏的 acting) 不在
+    #    覆盖面内, 必须报「中间损坏」而不是当没看见。
+    j.journal_path.write_text(
+        "\n".join([planned, '{"seq": 1, "state": "acti', '{"schema_ver', sentinel, done]) + "\n",
+        encoding="utf-8",
+    )
+    try:
+        rows = j.read_rows()
+        raise AssertionError(f"越界的坏行被静默吞了, 读回 {[r.get('state') for r in rows]}")
+    except uj.JournalError as e:
+        assert "中间存在损坏记录" in str(e), str(e)
+
+
+def test_receipt_failure_does_not_swallow_the_original_error(tmp_path):
+    """round-5 MEDIUM-2: 回执自己写不成, 不能把原始失败摘要一起吞掉。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "吞摘要.md", "# 吞摘要\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "吞摘要.md"), "action": "copy", "target": "节点"}],
+    )
+    blocked = vault / "节点"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        run_apply(vault, pv, dec)
+    finally:
+        os.chmod(blocked, orig)
+    batch_dir = only_batch_dir(vault)
+    os.replace(batch_dir / "receipt.md", batch_dir / "receipt-旧.md")
+    (batch_dir / "receipt.md").mkdir()  # 让回执发布必然失败
+
+    os.chmod(blocked, 0o500)
+    try:
+        r = run_apply(vault, pv, dec)
+    finally:
+        os.chmod(blocked, orig)
+    assert r.returncode != 0
+    assert "停在第 1 件" in r.stderr, f"原始失败摘要被回执的失败吞了: {r.stderr[:300]}"
+    assert "回执没写成" in r.stderr
+
+
+# ─────────── 车道自查（末轮整改的自我对抗复核；非独立审查）───────────
+
+
+def test_preserve_refuses_when_there_is_nowhere_to_park(tmp_path):
+    """自查①: 没有 stale/ 可留痕时, 不是「留不住」而是「不许盖」。
+
+    `_park_stale(stale_dir=None)` 返回 None, 拿它跟原路径比会判成「停放成功」——
+    HIGH-1 那个洞会从默认参数上重新开一次。
+    """
+    uj = load_journal_module()
+    victim = tmp_path / "别人的.md"
+    victim.write_bytes("用户的东西\n".encode())
+    assert uj.preserve_foreign_file(victim, None, None) is False
+    assert victim.read_bytes() == "用户的东西\n".encode()
+    # 对照: 落点空着 / 落点就是自家上一版产物（**内容 sha 相等**）时照常放行
+    assert uj.preserve_foreign_file(tmp_path / "不存在.md", None, None) is True
+    assert uj.preserve_foreign_file(victim, None, uj.sha256_file(victim)) is True
+    # ⛔ 归属只认可计算的等式: 对不上的 sha 不给放行, 不许退回「差不多像我们的」。
+    assert uj.preserve_foreign_file(victim, None, "0" * 64) is False
+    assert victim.read_bytes() == "用户的东西\n".encode()
+
+
+def test_undo_receipt_failure_still_says_how_many_were_restored(tmp_path):
+    """独立复核 LOW-2 的**撤销**那一半: 回执写不成时也得说清已经撤了几件。
+
+    这条和 `test_undo_receipt_failure_does_not_swallow_the_undo_error` 不是同一件事:
+    那条测的是「撤销**失败** + 回执失败」, 走的是 die(); 这条测的是「撤销**成功** +
+    只有回执失败」—— 只有这条路径会打印「已撤销 N 件」。管道的两半都要有门。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "撤了几件.md", "# 撤了几件\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "撤了几件.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    (batch_dir / "undo-receipt.md").mkdir()  # 撤销本身会成功, 只有它的回执写不成
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert "回执没写成" in u.stderr
+    assert "已撤销 1 件" in u.stderr, f"没说撤了几件: {u.stderr[:400]}"
+    # ⛔ 敏感性锚: 材料确实已经回去了 —— 「回执没写成」不等于「没撤成」, 这条门要是
+    # 绿在「撤销其实也失败了」上, 它就测不到本来要测的东西。
+    assert (vault / INBOX / "撤了几件.md").is_file()
+    assert not (vault / "归档" / "撤了几件.md").exists()
+
+
+def test_undo_receipt_failure_does_not_swallow_the_undo_error(tmp_path):
+    """自查②: MEDIUM-2 的修复在**撤销**那一半也要生效（管道不能只修一半）。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "撤销回执.md", "# 撤销回执\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "撤销回执.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    # 让撤销必然失败（落点被换成 symlink）, 且让它的失败回执也写不成
+    dst = vault / "归档" / "撤销回执.md"
+    os.replace(dst, tmp_path / "真身.md")
+    dst.symlink_to(tmp_path / "真身.md")
+    (batch_dir / "undo-receipt.md").mkdir()
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert "symlink" in u.stderr, f"撤销失败的原因被回执的失败吞了: {u.stderr[:300]}"
+    assert "回执没写成" in u.stderr
+    # ⛔ 「没被吞掉」还不够 —— 两个失败叠在一起时很容易退化成一屏栈回溯,
+    # 那种输出对着它的人读不出「我的文件现在在哪」（独立复核 L-4）。
+    assert "Traceback" not in u.stderr, f"吐了栈, 不是人能读的摘要: {u.stderr[:400]}"
+    clean = [ln for ln in u.stderr.split("\n") if ln.startswith("✗ ")]
+    assert clean, f"没有一行干净的 ✗ 摘要: {u.stderr[:400]}"
+    assert any("symlink" in ln for ln in clean), f"摘要行里没说失败原因: {clean}"
+
+
+# ─────────── 独立复核（第三方 Agent 对抗性审查 293f8d6a..HEAD）的门 ───────────
+
+
+def test_foreign_receipt_quoting_the_batch_id_is_still_preserved(tmp_path):
+    """独立复核 H-1: 「正文里出现了 batch_id」不是归属证明。
+
+    上一版拿 `batch_id in 文件字节` 认自家产物 —— 那是本模块自己第 3 条铁律
+    (「判据是可计算的等式, 不是子串启发式」) 正面禁止的写法。落点上任何一份**抄了
+    批次号**的用户笔记都会被零留痕覆盖; 撤销模式下 batch_id 还是从目录名来的,
+    连长度都不受约束。
+
+    对照输入: 同一处落点、同一次重跑, 唯一差别是那份用户文件的正文里有没有批次号。
+    两种都必须留痕。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "抄了批次号.md", "# 抄了批次号\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "抄了批次号.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    batch_id = batch_dir.name
+    assert batch_id, "拿不到批次号, 下面的对照就立不住"
+
+    mine = f"# 我的清仓笔记\n\n这一批是 {batch_id}, 我打算明天再看。\n".encode()
+    (batch_dir / "receipt.md").write_bytes(mine)
+    assert run_apply(vault, pv, dec).returncode == 0
+
+    stale = batch_dir / "stale"
+    kept = [p for p in stale.rglob("*") if p.is_file()] if stale.exists() else []
+    assert any(p.read_bytes() == mine for p in kept), (
+        f"抄了批次号的用户文件被零留痕覆盖了; stale/ 里只有 {[p.name for p in kept]}"
+    )
+    assert "clear-inbox" in (batch_dir / "receipt.md").read_text(encoding="utf-8"), "留痕是留下了, 但新回执没发布出来"
+
+
+def test_receipt_validation_moves_nothing_before_it_refuses(tmp_path):
+    """独立复核 M-1: 拒绝要在**动盘之前**做完。
+
+    上一版把会动盘的「停放」放进了校验循环: 第一份已经被挪进 stale/, 第二份才因为
+    落点不合规而拒绝 —— 官方路径两头都不在, 而且一个字都不说。
+
+    未被拦下的输入: 第一份落点上是别人的文件（可留痕）、第二份落点是一条 symlink。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    a = j.batch_dir / "receipt.json"
+    b = j.batch_dir / "receipt.md"
+    a.write_bytes("用户写在 json 落点上的东西\n".encode())
+    b.symlink_to(root / "别处.md")
+    before = a.read_bytes()
+
+    try:
+        uj.write_pair_atomically([(a, b"{}\n"), (b, b"# x\n")], j.stale_root)
+        raise AssertionError("落点是 symlink 却还是写了")
+    except uj.JournalError as e:
+        assert "symlink" in str(e), str(e)
+
+    assert a.is_file() and a.read_bytes() == before, "第一份在拒绝之前就被挪走了"
+    moved = [p for p in j.stale_root.rglob("*") if p.is_file()] if j.stale_root.exists() else []
+    assert moved == [], f"只读校验段动了盘: {[p.name for p in moved]}"
+
+
+def test_receipt_failure_tells_where_the_residue_is(tmp_path):
+    """独立复核 M-3: 残片位置挂在异常的 `__notes__` 上, 打印时得跟着出来。
+
+    模块里写着「残片位置挂到异常上, 让调用方说得出去看哪一份」—— 但调用方只打印
+    `str(e)`, notes 不在里面, 这句承诺在真实链路上是断的。
+    """
+    uj = load_journal_module()
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "残片.md", "# 残片\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "残片.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    os.replace(batch_dir / "receipt.md", batch_dir / "receipt-旧.md")
+    (batch_dir / "receipt.md").mkdir()  # 让回执发布必然失败
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    assert "回执没写成" in r.stderr
+    assert "残片位置" in r.stderr, f"只说了写不成, 没说残片在哪: {r.stderr[:500]}"
+    assert uj.TMP_SUFFIX in r.stderr, f"残片位置没给出可以照着找的文件名: {r.stderr[:500]}"
+    # 独立复核 LOW-2: 「回执没写成」不说完成数, 用户无从判断材料动没动。
+    assert "材料已按拍板处理: 1/1 件" in r.stderr, f"没说已完成几件: {r.stderr[:500]}"
+
+
+# ─────── 第二轮独立复核（9ad71fe9..67951095，5 视角 + 逐条对抗验伪）的门 ───────
+# ⛔ 这一轮存活的 6 条去重成 3 个真缺陷，其中两个是**上一轮整改自己引入的回退**。
+
+
+def test_receipt_refusal_publishes_nothing_when_the_stale_dir_is_unusable(tmp_path):
+    """round-2 D-1: 「有地方留痕」是**动盘的前提**，不是动盘途中才发现的事。
+
+    两段式整改只在 `stale_dir is None` 时于校验段拒绝；`stale_dir` 有值但**不可用**
+    （被占成普通文件 / symlink / 祖先链含 symlink）时校验段照样放行，真正的拒绝被推迟
+    到逐条 replace 的循环里 —— 第一份已经就位之后，第二份才说「留不住」。于是发布出去
+    的一对回执互相矛盾：机器读的 .json 是本次的，人读的 .md 还是用户那份。
+
+    对照输入 = 两段式**之前**的同一条输入：那时它是零写的。所以这是整改自己引入的回退。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    a = j.batch_dir / "receipt.json"  # 落点空着 ⇒ 第一次 replace 一定会把它就位
+    b = j.batch_dir / "receipt.md"
+    b.write_bytes("用户的东西\n".encode())  # 外来文件 ⇒ 需要留痕
+    if j.stale_root.exists():
+        os.replace(j.stale_root, root / "stale-挪开")
+    j.stale_root.write_bytes(b"not a dir\n")  # 留痕目录被占成普通文件 ⇒ 留不住
+
+    try:
+        uj.write_pair_atomically([(a, b'{"run": 2}\n'), (b, b"# run2\n")], j.stale_root)
+        raise AssertionError("留不住却还是写了")
+    except (OSError, uj.JournalError) as e:
+        assert "留痕" in str(e), str(e)
+
+    assert not os.path.lexists(str(a)), "第一份已经发布出去了 —— 一对回执从此互相矛盾"
+    assert b.read_bytes() == "用户的东西\n".encode(), "用户的文件被盖掉了"
+    leftovers = sorted(p.name for p in j.batch_dir.iterdir() if uj.TMP_SUFFIX in p.name)
+    assert leftovers == [], f"正式批次目录里留了 tmp 残片: {leftovers}"
+
+
+def test_failed_undo_does_not_append_to_an_unsealed_journal(tmp_path):
+    """round-2 D-2: 工具不能在它刚宣布「拒绝在看不懂的账上继续动盘」的那条路径上，
+    反手把这本账写坏。
+
+    `record_receipt_shas` 是全模块唯一一个可能在 `load()` 自己抛过之后仍被调用到的
+    `_append` 点：撤销失败 → 写失败回执 → 落账。账尾「完整但缺结尾换行」时直接
+    O_APPEND，末行会和新记录粘成一条烂行 —— 那条 done 行从此解析不出来，最新状态
+    静默退回 acting。
+
+    没被拦下的输入：一本第 2 行损坏、且末行完整但缺结尾换行的账（两种都是模块自己
+    建模过的真实态）。对照输入：同一本账末尾补一个 `\n`。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "别写坏账.md", "# 别写坏账\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "别写坏账.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    jp = batch_dir / "journal.jsonl"
+
+    rows = [ln for ln in jp.read_text(encoding="utf-8").split("\n") if ln.strip()]
+    rows = [r for r in rows if '"receipt_sha"' not in r]  # 让末行是一条业务记录
+    assert rows and '"done"' in rows[-1], rows[-1][:150] if rows else "空账"
+    tail = rows[-1]
+    damaged = "\n".join([rows[0], '{"seq": 1, "state": "acti'] + rows[1:])
+    jp.write_text(damaged, encoding="utf-8")  # ⛔ 末尾**不**补换行
+    before = jp.read_bytes()
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    assert "中间存在损坏记录" in u.stderr, f"拒绝的理由变了: {u.stderr[:300]}"
+    after = jp.read_bytes()
+    assert tail in after.decode("utf-8"), "末行那条完整记录被新追加的内容粘掉了"
+    assert after == before, f"账本被就地改写了（{len(before)} → {len(after)} 字节）"
+
+
+def test_residue_location_points_at_a_file_that_actually_exists(tmp_path):
+    """round-2 D-3: M-3 把「残片位置」端到用户面前了，那它就必须指得准。
+
+    `_replace_or_park` 失败时自己已经把 tmp 挪进 `stale/`，却把 `_park_stale` 的返回值
+    丢了 —— 调用方只能报 tmp 的**旧**路径，用户照着去找是空的，残片其实躺在 stale/ 里。
+    既有门只 grep `残片位置` 与后缀两个字面量，路径写错也恒绿（= 绿在更弱的判据上）。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    (j.batch_dir / "receipt.md").mkdir()  # 第二份落点是目录 ⇒ 它的 replace 必失败
+    try:
+        uj.write_pair_atomically(
+            [(j.batch_dir / "receipt.json", b"{}\n"), (j.batch_dir / "receipt.md", b"# x\n")],
+            j.stale_root,
+        )
+        raise AssertionError("该失败却成功了")
+    except (OSError, uj.JournalError) as e:
+        notes = " ".join(getattr(e, "__notes__", []) or [])
+
+    assert "残片位置" in notes, notes
+    listed = [p.strip() for p in notes.split("残片位置: ", 1)[1].split(" / ") if p.strip()]
+    assert listed, notes
+    missing = [p for p in listed if not os.path.lexists(p)]
+    assert missing == [], f"报出来的残片路径查无此文件: {missing}"
+    # ⛔ 敏感性锚: 残片确实被挪进了 stale/，所以「路径存在」不是因为它压根没被挪走。
+    assert any(str(j.stale_root) in p for p in listed), f"残片没进 stale/: {listed}"
+
+
+def test_park_failure_inside_the_move_segment_still_refuses_to_overwrite(tmp_path):
+    """⛔ 补回被更强的门吃掉的那一格覆盖面。
+
+    D-1 加的前置门（校验段先证 stale 可用）让
+    `test_receipt_refuses_when_the_foreign_file_cannot_be_parked` 现在在**第一段**就被
+    拒 —— 于是第二段里「留不住就不许覆盖」那一支再也没有任何用例走到，删掉它全绿。
+
+    这道门用一个**静态可判为可用、实际却留不住**的 stale/（真目录、非 symlink、祖先
+    干净，但不可写）把第二段重新盖上：前置门放行 → 进到动盘段 → 停放失败 → 仍然拒绝
+    覆盖，且此时**一份都还没发布**（留痕全做完才 replace）。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    a = j.batch_dir / "receipt.json"
+    b = j.batch_dir / "receipt.md"
+    b.write_bytes("用户的东西\n".encode())
+    j.stale_root.mkdir(parents=True, exist_ok=True)
+    orig = stat.S_IMODE(j.stale_root.stat().st_mode)
+    os.chmod(j.stale_root, 0o500)  # 真目录 ⇒ 前置门放行；不可写 ⇒ 实际停放必失败
+    try:
+        # ⛔ 敏感性锚: 前置门**确实放行**了, 所以下面的拒绝只可能来自动盘段。
+        uj.assert_stale_dir_usable(j.stale_root, what="回执落点")
+        try:
+            uj.write_pair_atomically([(a, b'{"run": 2}\n'), (b, b"# run2\n")], j.stale_root)
+            raise AssertionError("留不住却还是写了")
+        except (OSError, uj.JournalError) as e:
+            assert "无法留痕" in str(e), f"拒绝的理由不是动盘段那一条: {e}"
+    finally:
+        os.chmod(j.stale_root, orig)
+
+    assert b.read_bytes() == "用户的东西\n".encode(), "用户的文件被盖掉了"
+    assert not os.path.lexists(str(a)), "留痕还没做完就先发布了一份"
+
+
+# ═══ 全卡独立对抗性复核（绑最终 HEAD 5207f899，8 维度 + 逐条 3 路验伪）的门 ═══
+# ⛔ 前面每一轮都只读了一段 delta；这是第一次有人读全卡。裁定 BLOCKER 5 / HIGH 6，
+#    去重成 7 个缺陷族，全部是「写到 vault 之外 / 把用户文件搬出 vault」这一类。
+
+
+def test_undo_refuses_a_journal_outside_the_vault_and_writes_nothing(tmp_path):
+    """全卡复核 BLOCKER-A: 撤销侧也必须有「写入面在 vault 内」这条边界。
+
+    apply 侧有 `resolve_work_dir`（「--work-dir 必须落在 vault 内, 拒绝越界」），
+    撤销侧原先**一条都没有**：`--undo` 指到哪里，回执 / `stale/` / 账目追加就落到哪里。
+
+    未被拦下的输入：一个与本工具毫无关系、恰好叫 `journal.jsonl` 的用户笔记。
+    实测（整改前）rc=**0**、打印「✓ 已撤销 0 件」，而那个目录里多出
+    `undo-receipt.json` / `undo-receipt.md` / `stale/`，用户同名文件被挪进 stale/。
+    """
+    vault, out = base_vault(tmp_path)
+    outside = tmp_path / "我的笔记"
+    outside.mkdir()
+    (outside / "journal.jsonl").write_text("# 我自己的日志\n这不是清仓账本\n", encoding="utf-8")
+    (outside / "undo-receipt.json").write_text('{"我的":"东西"}\n', encoding="utf-8")
+    before = snapshot(outside)
+
+    u = run_undo(vault, outside / "journal.jsonl")
+    assert u.returncode != 0, f"越界的账本被接受了: {u.stdout[:300]}"
+    assert "vault 内" in u.stderr or "越界" in u.stderr, u.stderr[:300]
+    assert snapshot(outside) == before, "vault 之外的目录被动过了"
+    assert no_outputs(vault), "拒绝路径把 outputs/ 建出来了"
+
+
+def test_undo_bound_to_another_vault_leaves_that_batch_byte_identical(tmp_path):
+    """全卡复核 BLOCKER-B: 被判「不是当前 vault 的」之后，一个字节都不许往那儿写。
+
+    原先：① `undo()` 第一句就是 `load()`，而 `load()` 内含 `seal_tail_if_needed()`
+    会往对方账本**追加**封口哨兵 —— 拒绝是在改写过对方账本之后才说出口的；
+    ② 拒绝路径仍无条件写失败回执，把对方批次**真实的** `undo-receipt` 零留痕覆盖成
+    「共 0 件 · 中途停下」，并往对方账本追加一条带**本 vault** 指纹的 receipt_sha 行。
+
+    `undo-receipt.md` 是用户唯一读得懂的「我的东西还原了没有」的凭证。
+    """
+    vault_a, out_a = base_vault(tmp_path / "A")
+    mk(vault_a / INBOX / "甲的材料.md", "# 甲\n", age_days=3)
+    pv_a = make_preview(vault_a, out_a)
+    dec_a = write_decisions(
+        tmp_path / "da.json",
+        [{"stable_id": id_of(pv_a, "甲的材料.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault_a, pv_a, dec_a).returncode == 0
+    batch_a = only_batch_dir(vault_a)
+    assert run_undo(vault_a, batch_a / "journal.jsonl").returncode == 0
+    receipt_before = (batch_a / "undo-receipt.json").read_bytes()
+    assert b'"ok": true' in receipt_before, "前置没成立: A 的撤销回执应当是成功的"
+    before = snapshot(batch_a)
+
+    # ⛔ 场景必须让账本**落在 B 的 vault 内**: BLOCKER-A 的边界门现在会先把
+    # 「--undo 指向 vault 外」整条拒掉（我自己加的那道更强的门吃掉了「跨 vault 指错」
+    # 这条路径的覆盖面）。真正还走得到绑定判据、而且同样真实的形态是: 用户把 A 的
+    # 批次目录**拷进** B 的 outputs/ 里（备份还原 / 同步工具 / 手动整理都会这样）。
+    vault_b, _ = base_vault(tmp_path / "B")
+    dst_batch = vault_b / "outputs" / "clear-inbox" / batch_a.name
+    dst_batch.parent.mkdir(parents=True, exist_ok=True)
+    shutil.copytree(batch_a, dst_batch)
+    copied_before = snapshot(dst_batch)
+
+    u = run_undo(vault_b, dst_batch / "journal.jsonl")
+    assert u.returncode != 0
+    assert "不是当前 vault 的" in u.stderr, u.stderr[:300]
+    assert snapshot(dst_batch) == copied_before, "被拒绝的那本账所在的批次目录被动过了"
+    assert (dst_batch / "undo-receipt.json").read_bytes() == receipt_before, "那份真实的撤销回执被换成了一句假话"
+    # A 自己当然也不许被碰
+    assert snapshot(batch_a) == before, "A 的批次目录被动过了"
+
+
+def test_undo_does_not_seal_a_journal_it_is_about_to_refuse(tmp_path):
+    """全卡复核 BLOCKER-B（模块级）: 封口不能发生在绑定判定之前。
+
+    对照输入：同一本账、同一个半行尾巴，唯一差别是 fingerprint 对不对得上。
+    对得上 ⇒ 正常封口；对不上 ⇒ 文件**逐字节不变**。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    rows = [
+        json.dumps(
+            {
+                "seq": 1,
+                "state": uj.STATE_DONE,
+                "op": "copy",
+                "batch_id": j.batch_id,
+                "vault_fingerprint": "别人的指纹",
+                "src": "_待处理/x.md",
+                "dst": "节点/x.md",
+            },
+            ensure_ascii=False,
+        ),
+        '{"seq": 1, "state": "act',  # 半行尾巴 ⇒ 正常路径下会被封口
+    ]
+    j.journal_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
+    before = j.journal_path.read_bytes()
+
+    try:
+        j.undo(root / "vault", "我的指纹")
+        raise AssertionError("别人的账被接受了")
+    except uj.JournalNotOursError as e:
+        assert "不是当前 vault 的" in str(e), str(e)
+    assert j.journal_path.read_bytes() == before, "拒绝之前先把对方的账封口了（封口 = 往对方文件里追加内容）"
+
+
+def test_undo_refuses_a_journal_row_pointing_outside_the_vault(tmp_path):
+    """全卡复核 BLOCKER-C: 账本里的 src/dst 是**用户改得动的输入**，要卡形状。
+
+    执行侧对同一类输入（preview 的 `rel_path`）卡死了形状，注释原话是
+    「一条 `../outside.md` 就能让执行侧去搬 vault 外的文件」；撤销侧却直接
+    `vault / row["src"]`。实测（整改前）：把一条 done 行的 `src` 改成
+    `../外面/被搬出去.md`，撤销 rc=0 打印「✓ 已撤销 1 件」，材料被搬出 vault。
+
+    `assert_symlink_free` 挡不住这条 —— 它比的是 normpath 与 realpath，
+    对**无 symlink 的** `../` 路径两者相等，一律放行。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "搬家.md", "# 搬家\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "搬家.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+
+    rows = journal_rows(batch_dir)
+    hit = 0
+    for r in rows:
+        if r.get("state") == "done" and r.get("src"):
+            r["src"] = "../外面/被搬出去.md"
+            hit += 1
+    assert hit == 1, f"前置没成立: 期望恰一条 done 行带 src, 实得 {hit}"
+    rewrite_journal(batch_dir, rows)
+    before = snapshot(vault, skip=("outputs",))
+    outside_before = sorted(p.name for p in tmp_path.iterdir())
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0, f"带 `..` 的账本被采信了: {u.stdout[:300]}"
+    assert "越界" in u.stderr or ".." in u.stderr, u.stderr[:300]
+    assert snapshot(vault, skip=("outputs",)) == before, "vault 树被动过了"
+    assert sorted(p.name for p in tmp_path.iterdir()) == outside_before, "vault 外多出了东西"
+
+
+def test_undo_skips_untrustworthy_dir_mtime_keys_but_still_restores(tmp_path):
+    """最终 HEAD 独立复核 H-A + delta 复核 HIGH-1：这道门钉的是**两个**性质。
+
+    `dir_mtimes` / `_at_act` / `_after` 的键是账本里的不可信输入，而账本就躺在 vault 里
+    （用户手改、同步工具改都够得着）。它只驱动撤销收尾那句 `os.utime`。
+
+    1. **安全**：不可信的键**绝不**导致 vault 之外被写（原缺陷：`d = vault / rel`，
+       pathlib 遇绝对路径丢掉 base、`..` 交给内核解析，两道现存判据全部放行 ⇒
+       `os.utime` 打到 vault 外，rc=0 还把该路径当成功项列进回执）。
+    2. **可用**：坏键只让**那个目录的时间**不还原，**不得否决整批材料还原**。
+       初版整改在这里 fail-closed 抛出，后果是整批撤不回来、CLI 无跳过开关、
+       且抛出点落在会写回执那一支 ⇒ 把上一次成功撤销的 undo-receipt 换成「共 0 件」
+       （M5 那条不变量被重新打破）。只钉「拒绝」的门会把那个回退判成正确。
+
+    三条负控输入各测一臂：词法越界 / 祖先链 symlink（realpath 那一半） / 坏的时间值。
+    """
+    import os as _os
+    import json as _json
+
+    outside = tmp_path / "vault外的目录"
+    outside.mkdir()
+    (outside / "别人的东西.md").write_text("# 别动我\n", encoding="utf-8")
+    (outside / "2026").mkdir()
+    mt_outside = _os.stat(outside).st_mtime_ns
+    mt_outside_sub = _os.stat(outside / "2026").st_mtime_ns
+
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "普通.md", "# 普通\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "普通.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    mt_nodes = _os.stat(vault / "节点").st_mtime_ns
+    moved = vault / "归档" / "普通.md"
+    assert moved.is_file(), "前置没成立: apply 没把材料搬到 归档/"
+
+    # 祖先链那一臂: 另建一条 vault 内的 symlink 指向 vault 外, 键写 "链/2026"。
+    # 末段 2026 是真目录 ⇒ is_symlink(d) 为假; d.is_dir() 跟随 symlink 为真
+    # ⇒ 只有 realpath 正向包含判定拦得住它。
+    # ⛔ 不能拿 归档/ 来做这条: 把它换掉材料就跟着没了, 撤销会因「去处已不存在」
+    # 合法失败 —— 前置自己毁掉了要测的东西, 门就测不到它声称测的事了。
+    (vault / "链").symlink_to(outside, target_is_directory=True)
+
+    keys = {
+        "../vault外的目录": 111,  # 词法越界
+        "链/2026": 222,  # 祖先链 symlink（末段不是 symlink）
+    }
+    rows = journal_rows(batch_dir)
+    hit = 0
+    for r in rows:
+        if r.get("state") == "done":
+            # 单步链: pre == at_act, post == 该目录**当下**的 mtime ⇒ 三道链判据全成立,
+            # 整改前这两条必然进 to_retime。
+            r["dir_mtimes"] = dict(keys)
+            r["dir_mtimes_at_act"] = dict(keys)
+            r["dir_mtimes_after"] = {"../vault外的目录": mt_outside, "链/2026": mt_outside_sub}
+            r["dir_mtimes"]["坏值目录"] = "不是数字"  # 坏值那一臂（int() 就拦下）
+            r["dir_mtimes_at_act"]["坏值目录"] = "不是数字"
+            r["dir_mtimes_after"]["坏值目录"] = "也不是数字"
+            # ⛔ 越界数值那一臂: int(10**30) **成功**, 到 os.utime 才抛 OverflowError
+            # (本机实测「timestamp out of range for platform time_t」), 它不是 OSError。
+            # 键必须指向一个**真实存在**的 vault 内目录 —— 否则 d.is_dir() 先把它跳过,
+            # 这一臂就永远走不到 os.utime, 等于没测（空洞门）。
+            # 这一臂同时钉住 delta 复核 MEDIUM-4: 收尾 retime 失败不得把「已还原 N 件」
+            # 写成 0 件, 也不得让整批撤销失败。
+            _huge = 10**30
+            r["dir_mtimes"]["节点"] = _huge
+            r["dir_mtimes_at_act"]["节点"] = _huge
+            r["dir_mtimes_after"]["节点"] = _os.stat(vault / "节点").st_mtime_ns
+            hit += 1
+    assert hit == 1, f"前置没成立: 期望恰一条 done 行, 实得 {hit}"
+    rewrite_journal(batch_dir, rows)
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+
+    # ── 性质 1: 安全 ──────────────────────────────────────────────────
+    assert _os.stat(outside).st_mtime_ns == mt_outside, "vault 外那个目录的 mtime 被改了 —— 这是一次落在 vault 之外的写"
+    assert _os.stat(outside / "2026").st_mtime_ns == mt_outside_sub, (
+        "祖先链是 symlink 时写穿到了 vault 之外（末段判据看不到祖先）"
+    )
+    assert (outside / "别人的东西.md").read_text(encoding="utf-8") == "# 别动我\n"
+    assert _os.stat(vault / "节点").st_mtime_ns == mt_nodes, (
+        "越界数值被写进了目录时间（os.utime 抛的 OverflowError 没被接住）"
+    )
+
+    # ── 性质 2: 可用 ──────────────────────────────────────────────────
+    assert u.returncode == 0, f"装饰性字段里的坏键否决了整批还原（初版 fail-closed 的回退）: {u.stderr[-400:]}"
+    assert "Traceback" not in (u.stderr or ""), f"坏值走成了裸栈: {u.stderr[-400:]}"
+    assert (vault / INBOX / "普通.md").is_file(), "材料没有被还原回 待处理/"
+
+    # ── 三条负控输入都要在回执里**留痕**，不能静默吞掉 ────────────────
+    rec = _json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    blob = _json.dumps(rec, ensure_ascii=False)
+    for k in ("../vault外的目录", "链/2026", "坏值目录", "节点"):
+        assert k in blob, f"回执里没有留下 {k!r} 未还原时间的记录（静默吞掉了）"
+
+
+def test_undo_writes_nothing_when_the_journal_is_unreadable(tmp_path):
+    """最终 HEAD 独立复核 H-B：零写契约原先挂在**异常类型**上，那是钩子不是不变量。
+
+    撤销侧的「一个字节都不写」只挂在 `JournalNotOursError` 上；而 `read_rows()`
+    对「读得出行、但 state 认不出来」的账抛的是**普通 `JournalError`**，于是它落进
+    会写回执的那个 except —— `--undo` 指向 vault 内任何一个恰好叫 `journal.jsonl`
+    的用户文件，都会在那个目录留下 undo-receipt，并把同名用户文件挪进新建的 `stale/`。
+
+    判据钉**整个目录逐字节不变**，而不是「没有 undo-receipt.json」：后者挡不住
+    换个文件名写、也挡不住 `stale/` 里的搬动。
+    """
+    vault, _out = base_vault(tmp_path)
+    mine = vault / "节点" / "我的记录"
+    mine.mkdir(parents=True)
+    # 一个恰好叫 journal.jsonl 的用户文件：行读得出来，state 认不出来。
+    (mine / "journal.jsonl").write_text('{"state": "我随手记的", "备注": "这不是批次账"}\n', encoding="utf-8")
+    # 同名用户文件：整改前会被无声挪进新建的 stale/。
+    (mine / "undo-receipt.md").write_text("# 我自己写的收据\n", encoding="utf-8")
+
+    before = {p.relative_to(mine).as_posix(): p.read_bytes() for p in mine.rglob("*") if p.is_file()}
+    assert len(before) == 2, f"前置没成立: {sorted(before)}"
+
+    u = run_undo(vault, mine / "journal.jsonl")
+
+    after = {p.relative_to(mine).as_posix(): p.read_bytes() for p in mine.rglob("*") if p.is_file()}
+    assert after == before, (
+        f"往一个读不懂的账所在目录写了东西 —— 多出/改动: {sorted(set(after) ^ set(before)) or '内容被改'}"
+    )
+    assert not (mine / "stale").exists(), "建了 stale/ 并把用户文件挪了进去"
+    assert u.returncode != 0, f"读不懂的账被采信了: {u.stdout[:300]}"
+
+
+def test_undo_shape_gate_covers_dst_and_backup_not_just_src(tmp_path):
+    """最终 HEAD 独立复核 H-C：形状门原先只喂了 `src`。
+
+    `safe_join` 挂在 src / dst / backup 三个字段上，但门只对 `src` 喂过对照输入 ——
+    另外两条的 `safe_join` 是**零覆盖**，谁把它们摘掉门都不会红。这道门把三个字段
+    逐个喂一遍，锁住的是「三条都在」，不是「有一条在」。
+    """
+    # ⛔ 判据钉**哪道守卫开的火**，不钉「最终拒绝了」。初版只断言 rc≠0 + 零写，
+    # 负控实测：把 `dst` 的 safe_join 摘掉后该门**仍绿** —— 因为 `../外面/落到外面.md`
+    # 本就不存在，更早那道「产物已不在落点」先拒绝了，结果一模一样。
+    # safe_join 的措辞里带着各字段自己的 what 标签，只有它能区分是谁拒的。
+    WHAT = {"src": "原路径", "dst": "落点", "backup": "备份路径"}
+    for field, bad in (
+        ("src", "../外面/被搬出去.md"),
+        ("dst", "../外面/落到外面.md"),
+        ("backup", "../../外面/备份跑出去.md"),
+    ):
+        vault, out = base_vault(tmp_path / field)
+        mk(vault / INBOX / "材料.md", "# 材料\n", age_days=3)
+        pv = make_preview(vault, out)
+        dec = write_decisions(
+            tmp_path / field / "d.json",
+            [{"stable_id": id_of(pv, "材料.md"), "action": "move", "target": "归档"}],
+        )
+        assert run_apply(vault, pv, dec).returncode == 0
+        batch_dir = only_batch_dir(vault)
+
+        rows = journal_rows(batch_dir)
+        hit = 0
+        for r in rows:
+            if r.get("state") == "done" and r.get(field):
+                r[field] = bad
+                hit += 1
+        assert hit == 1, f"[{field}] 前置没成立: 期望恰一条 done 行带该字段, 实得 {hit}"
+        rewrite_journal(batch_dir, rows)
+        before = snapshot(vault, skip=("outputs",))
+
+        # ⛔ 取名面必须**恰好**等于主张: 「vault **外**的树没变」。
+        # 初版比直接子项名 ⇒ 结构上不可能失败; 改比整棵子树又**太宽** ——
+        # 把 vault 自己也算进去了, 于是 vault 内正常写的 undo-receipt 也被判成变化。
+        # 过度修正和原缺陷一样是错的。
+        def _outside_tree(base=tmp_path / field, v=vault):
+            return sorted(p.relative_to(base).as_posix() for p in base.rglob("*") if p != v and v not in p.parents)
+
+        outside_tree_before = _outside_tree()
+
+        u = run_undo(vault, batch_dir / "journal.jsonl")
+        assert u.returncode != 0, f"[{field}] 带 `..` 的账本被采信了: {u.stdout[:300]}"
+        assert WHAT[field] in u.stderr and "越界" in u.stderr, (
+            f"[{field}] 开火的不是形状门（绿在更早那道判据上了）: {u.stderr[-300:]}"
+        )
+        assert snapshot(vault, skip=("outputs",)) == before, f"[{field}] vault 树被动过了"
+        # delta 复核 LOW-9: 原先比直接子项名, 坏路径落不到那一层 ⇒ 判据不可能失败。
+        after_tree = _outside_tree()
+        assert after_tree == outside_tree_before, (
+            f"[{field}] vault 外的树变了: {sorted(set(after_tree) ^ set(outside_tree_before))[:6]}"
+        )
+
+
+def test_undo_refuses_a_file_that_is_not_a_batch_journal(tmp_path):
+    """全卡复核 HIGH-D: 「指错了文件」不能和「这一批确实撤完了」输出逐字相同。
+
+    `_assert_bound_to` 的判据是「每一条业务记录都绑着当前 vault」—— 对 `rows == []`
+    是**空真**；`read_rows()` 又把「整份文件解析不出 JSON」归成掉电截断的尾巴。
+    于是任意文本文件都会一路通过，打印「✓ 已撤销 0 件」并 rc=0。
+    """
+    vault, out = base_vault(tmp_path)
+    fake = vault / "outputs" / "clear-inbox" / "看起来像个批次" / "journal.jsonl"
+    fake.parent.mkdir(parents=True)
+    fake.write_text("# 这不是账本\n只是一份普通笔记\n", encoding="utf-8")
+    before = snapshot(fake.parent)
+
+    u = run_undo(vault, fake)
+    assert u.returncode != 0, f"非账本文件被当成空账通过了: {u.stdout[:300]}"
+    assert "不是一本清仓账本" in u.stderr, u.stderr[:300]
+    assert "已撤销 0 件" not in u.stdout, "输出与「确实撤完了」无法区分"
+    assert snapshot(fake.parent) == before, "被拒绝的文件所在目录被动过了"
+
+
+def test_target_whitelist_is_case_insensitive(tmp_path):
+    """全卡复核 HIGH-F: 落点黑名单在它实际运行的平台上守不住自己声明要守的目录。
+
+    macOS 默认卷大小写不敏感，而 `os.path.realpath` **不做**大小写规范化：
+    `realpath('<v>/.Claude')` 原样返回 `.Claude`，但它和 `.claude` 是同一个目录。
+    实测（整改前）：target 写 `.Claude` / `.Obsidian` / `Outputs` 一律 rc=0，
+    材料分别落进 `.claude/` / `.obsidian/` / `outputs/`——首段只差一个字母的大小写。
+    """
+    vault, out = base_vault(tmp_path)
+    (vault / ".claude").mkdir()
+    (vault / ".obsidian").mkdir()
+    mk(vault / INBOX / "材料.md", "# 材料\n", age_days=3)
+    pv = make_preview(vault, out)
+    sid = id_of(pv, "材料.md")
+    before = snapshot(vault, skip=("outputs",))
+
+    for bad in (".Claude", ".Obsidian", "Outputs", "OUTPUTS", "_待处理".upper()):
+        dec = write_decisions(tmp_path / "d.json", [{"stable_id": sid, "action": "copy", "target": bad}])
+        r = run_apply(vault, pv, dec)
+        assert r.returncode != 0, f"target={bad!r} 被接受了"
+        assert snapshot(vault, skip=("outputs",)) == before, f"target={bad!r} 动了盘"
+        assert no_outputs(vault), f"target={bad!r} 把 outputs/ 建出来了"
+
+    # ⛔ 对照锚: 正常 target 照常放行 —— 证明上面的拒绝不是「什么都拒」。
+    dec = write_decisions(tmp_path / "ok.json", [{"stable_id": sid, "action": "copy", "target": "节点"}])
+    assert run_apply(vault, pv, dec).returncode == 0
+    assert (vault / "节点" / "材料.md").is_file()
+
+
+def test_link_half_state_park_refuses_a_symlinked_stale_dir(tmp_path):
+    """全卡复核 HIGH-G: A_LINK 半态停放是全卡唯一一处没过 symlink 守卫的搬动。
+
+    原先是裸 `os.makedirs(stale_root, exist_ok=True)` + `os.replace`——而
+    `os.makedirs(..., exist_ok=True)` 对「指向已存在目录的 symlink」是静默成功的。
+    于是 `stale/` 被换成指向 vault 外的 symlink 时，落点上那份**用户的**文件会被
+    无声搬出 vault，而工具报「✓ 全部完成」。同模块两个同型落点（`_park_stale` /
+    `backup`）都查了 symlink，只有这一处没查。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "链接.md", "# 链接\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "链接.md"), "action": "link", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    dst = vault / "节点" / "链接.md"
+    assert dst.stat().st_ino == (vault / INBOX / "链接.md").stat().st_ino
+
+    # 造半态: 去掉 done 行（= 卡自己的 test_rerun_after_action_completed_but_uncommitted
+    # 用的那种中断态）, 并把落点原子改写成**逐字节相同**的新 inode（Obsidian 保存即此形态）
+    drop_rows(batch_dir, "done")
+    tmp_same = vault / "节点" / ".改写中"
+    tmp_same.write_bytes(dst.read_bytes())
+    os.replace(tmp_same, dst)
+    assert dst.stat().st_ino != (vault / INBOX / "链接.md").stat().st_ino
+
+    outside = tmp_path / "vault外"
+    outside.mkdir()
+    stale = batch_dir / "stale"
+    if stale.exists():
+        os.replace(stale, batch_dir / "stale-挪开")
+    stale.symlink_to(outside, target_is_directory=True)
+    dst_bytes = dst.read_bytes()
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, f"stale/ 是 symlink 却照样搬了: {r.stdout[:300]}"
+    assert dst.is_file() and dst.read_bytes() == dst_bytes, "用户的文件被搬走了"
+    assert sorted(p.name for p in outside.iterdir()) == [], "文件被搬出 vault 了"
+
+
+def uj_state_receipt() -> str:
+    """`receipt_sha` 的 state 值 —— 从模块读，不手抄字面量。"""
+    return load_journal_module().STATE_RECEIPT_SHA
+
+
+# ═══ 全卡复核 MEDIUM 的门（5 条真行为缺陷 + 8 条零覆盖）═══
+# ⛔ 这一批里有 8 条是「拿掉某处生产判据，103 条门仍然全绿」——门在，但断言不了它
+#    声称断言的事。和 HIGH-E 同一类。
+
+
+def test_truncated_journal_does_not_let_undo_claim_success(tmp_path):
+    """M6: 「最新状态是 planned」只是**账上**的推断，前提是 acting 行还在账上。
+
+    账本一旦在记录边界处被截短（同步回滚 / 外部工具 / 手改 —— `outputs/` 就在 vault 内，
+    会被 Obsidian Sync 一类工具同步），已执行那一件的 acting/done 行就没了，最新状态
+    退回 planned ⇒ 撤销对一件**确实搬走了**的材料说「未执行, 无需还原」，rc=0 报成功
+    而材料仍在落点。实测（整改前）：三件 move 的账截到第 4 条记录 → `✓ 已撤销 2 件`，
+    而乙.md / 丙.md 仍在 `归档/`。
+    """
+    vault, out = base_vault(tmp_path)
+    for n in ("甲", "乙", "丙"):
+        mk(vault / INBOX / f"{n}.md", f"# {n}\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, f"{n}.md"), "action": "move", "target": "归档"} for n in ("甲", "乙", "丙")],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    jp = batch_dir / "journal.jsonl"
+
+    rows = journal_rows(batch_dir)
+    keep = [r for r in rows if r.get("state") != uj_state_receipt()]
+    # 截到「seq1 三条 + seq2 的 planned」为止 —— 记录边界处的截短
+    cut = []
+    seen2 = 0
+    for r in keep:
+        if r.get("seq") == 2:
+            seen2 += 1
+            if seen2 > 1:
+                break
+        cut.append(r)
+    assert sum(1 for r in cut if r.get("seq") == 2) == 1, "前置没成立: seq2 应只剩一条"
+    rewrite_journal(batch_dir, cut)
+    assert (vault / "归档" / "乙.md").is_file(), "前置没成立: 乙应当还在落点上"
+
+    u = run_undo(vault, jp)
+    assert u.returncode != 0, f"截短的账被当成「没执行过」了: {u.stdout[:300]}"
+    assert "没执行过" in u.stderr or "截短" in u.stderr, u.stderr[:300]
+    # ⛔ 敏感性锚: 材料**确实还在落点上** —— 所以「未执行」是句假话。
+    assert (vault / "归档" / "乙.md").is_file()
+
+
+def test_failed_undo_receipt_reports_how_many_were_really_restored(tmp_path):
+    """M7: 撤销逐件推进，第 k 件抛出时前 k-1 件的盘面动作都已做完。
+
+    原先失败回执把 `total`/`completed`/`results` 硬编码成 0 —— 用户据此以为「什么都没撤」，
+    而盘上确实已经还原了 k 件。执行侧那一半是对的（用真实 completed 计数）。
+    """
+    vault, out = base_vault(tmp_path)
+    for n in ("n1", "n2", "n3"):
+        mk(vault / INBOX / f"{n}.md", f"# {n}\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, f"{n}.md"), "action": "copy", "target": "节点"} for n in ("n1", "n2", "n3")],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    # 让 seq1 撤不掉（落点被改动过），seq3/seq2 会先被逆序撤掉
+    with open(vault / "节点" / "n1.md", "a", encoding="utf-8") as f:
+        f.write("用户后来加的一行\n")
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode != 0
+    receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert receipt["ok"] is False
+    assert receipt["completed"] == 2, f"盘上确实还原了 2 件, 回执却写 {receipt['completed']}"
+    assert len(receipt["results"]) == 2, receipt["results"]
+    assert "已还原 2 件" in u.stderr, u.stderr[:300]
+    # ⛔ 敏感性锚: 那 2 件真的还原了。
+    assert (vault / INBOX / "n2.md").is_file() and (vault / INBOX / "n3.md").is_file()
+
+
+def test_second_undo_does_not_blank_the_previous_receipt(tmp_path):
+    """M5: 第二次跑同一条 `--undo` 是文档承诺的幂等空操作，但它写同一个 stem。
+
+    原先回执只由**本次** `restored` 生成 ⇒ 第二次跑把上一次那份**记着产物停放位置**的
+    回执原地换成 `total: 0 / results: []`，而 `undone` 行本身不记停放位置 ——
+    「我的东西去哪了」从此无处可查。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "再撤一次.md", "# 再撤一次\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "再撤一次.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    assert run_undo(vault, batch_dir / "journal.jsonl").returncode == 0
+    first = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert first["total"] == 1 and len(first["results"]) == 1, first
+
+    u2 = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u2.returncode == 0, f"幂等空操作却失败了: {u2.stderr[:300]}"
+    second = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    assert second["total"] == 1, f"第二次跑把回执抹成了「共 {second['total']} 件」"
+    assert len(second["results"]) == 1, second["results"]
+    assert second["results"][0]["state"] == "上一次已撤销", second["results"][0]
+
+
+def test_resumed_undo_still_accounts_for_dirs_of_already_undone_items(tmp_path):
+    """M4: `_dir_retime_plan` 原先用 `latest_by_seq` 建链。
+
+    撤销中途失败后再跑一次时，上一轮已还原那几件的**最新**行全是 `undone` ⇒ 它们碰过的
+    目录既进不了 `dirs_retimed`、也进不了 `dirs_not_retimed` —— 回执对这些目录一个字都
+    不说，而它们的 mtime 确实没被还原。紧挨着的 `created_dirs` 正是为同一原因改成
+    「从**全部**行汇总」的（round-3 L14）。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "d1.md", "# d1\n", age_days=3)
+    mk(vault / INBOX / "d2.md", "# d2\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "d1.md"), "action": "copy", "target": "节点"},
+            {"stable_id": id_of(pv, "d2.md"), "action": "move", "target": "归档"},
+        ],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+
+    # 让 seq1（copy 到 节点/）撤不掉，seq2（move 到 归档/）先被撤
+    blocked = vault / "节点"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o555)
+    try:
+        assert run_undo(vault, batch_dir / "journal.jsonl").returncode != 0
+    finally:
+        os.chmod(blocked, orig)
+    assert (vault / INBOX / "d2.md").is_file(), "前置没成立: seq2 应已被撤"
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stderr[:300]
+    receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    mentioned = set(receipt.get("dirs_retimed") or []) | {d["dir"] for d in (receipt.get("dirs_not_retimed") or [])}
+    assert "归档" in mentioned, f"seq2 碰过的目录在两张表里都不出现, 回执对它一个字都不说: {mentioned}"
+
+
+def test_edited_done_product_gets_the_precise_diagnosis_not_the_ownership_one(tmp_path):
+    """M15: 两道门的触发条件重合时，要让**诊断更准**的那一道先说话。
+
+    `check_destinations_free` 原先对**每一个** plan 无差别跑归属守卫，包括账上已 done 的。
+    于是「用户编辑过自己已经搬过去的那份笔记」这个完全正常的行为，会撞上
+    「不是本批次造的, 先自己处理掉那份同名文件」—— 而它明明就是本批次搬过去的。
+    `verify_done` 对同一输入给的是「账上说第 N 件已完成, 但落点内容已被改动」。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "a.md", "# a\n", age_days=3)
+    mk(vault / INBOX / "b.md", "# b\n", age_days=3)
+    (vault / "只读区").mkdir()
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "a.md"), "action": "move", "target": "节点"},
+            {"stable_id": id_of(pv, "b.md"), "action": "move", "target": "只读区"},
+        ],
+    )
+    blocked = vault / "只读区"
+    orig = stat.S_IMODE(blocked.stat().st_mode)
+    os.chmod(blocked, 0o500)
+    try:
+        assert run_apply(vault, pv, dec).returncode != 0
+    finally:
+        os.chmod(blocked, orig)
+    assert (vault / "节点" / "a.md").is_file(), "前置没成立: 第 1 件应已完成"
+
+    # 用户给已经搬过去的那份追加一段笔记 —— 完全正常的行为
+    with open(vault / "节点" / "a.md", "a", encoding="utf-8") as f:
+        f.write("\n我自己加的一段\n")
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0
+    assert "落点内容已被改动" in r.stderr, f"给的是归属守卫那句错诊断, 而不是 verify_done 的精确诊断: {r.stderr[:300]}"
+    assert "不是本批次造的" not in r.stderr
+
+
+def test_provenance_write_never_touches_a_hardlinked_neighbour(tmp_path):
+    """M2: `atomic_write_bytes` 的原子性（换 inode、不就地截断）原先零门覆盖。
+
+    它的 docstring 明写「原文件在 os.replace 成功之前一个字节都不动」，但把整段换成
+    就地截断写之后 **103 条门仍然全绿**。能分辨的对照输入是「落点有一个硬链接邻居」：
+    换 inode ⇒ 邻居不受影响；就地写 ⇒ 邻居也被写进 provenance 块。
+    """
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "带邻居.md", "# 带邻居\n\n正文\n", age_days=3)
+    neighbour = vault / "节点" / "邻居.md"
+    os.link(str(src), str(neighbour))  # 用户自己建的硬链接，没参与这次清仓
+    before = neighbour.read_bytes()
+    assert neighbour.stat().st_ino == src.stat().st_ino
+
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "带邻居.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    moved = vault / "归档" / "带邻居.md"
+    assert "clear_inbox_provenance" in moved.read_text(encoding="utf-8"), "前置没成立: 应写了溯源"
+    assert neighbour.read_bytes() == before, "硬链接邻居被就地写法改了 —— 它没参与这次清仓"
+    assert "clear_inbox_provenance" not in neighbour.read_text(encoding="utf-8")
+
+
+def test_free_path_never_overwrites_an_existing_parked_item(tmp_path):
+    """M3/M8: `free_path` 是四处停放点共同依赖的防覆盖原语，原先零门覆盖。
+
+    把它改成恒返回原路径（不避让）后 **103 条门全绿**。对照输入是「同一个落点被停放两次」：
+    避让 ⇒ `recycle/undone/` 下两份都在；不避让 ⇒ 第一份被 `os.replace` 无声换掉。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "停两次.md", "# 停两次\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "停两次.md"), "action": "copy", "target": "节点"}],
+    )
+    for _ in range(2):
+        assert run_apply(vault, pv, dec).returncode == 0
+        assert run_undo(vault, only_batch_dir(vault) / "journal.jsonl").returncode == 0
+
+    undone = only_batch_dir(vault) / "recycle" / "undone"
+    parked = sorted(p.name for p in undone.iterdir()) if undone.exists() else []
+    assert len(parked) == 2, f"两次撤销的产物应各留一份, 实得 {parked}"
+    assert len(set(parked)) == 2, f"两份重名了 ⇒ 第一份会被无声换掉: {parked}"
+
+
+def test_copy_destination_keeps_the_source_permission_bits(tmp_path):
+    """M9: copy 落点的权限位原先零覆盖 —— 既有那道门只走 move，而 move 的权限是
+    `os.replace` 自带的（保 inode 连带保 mode）。
+
+    copy 的 tmp 由 `_open_new_exclusive` 以 0o600 建出，源权限**不会**自己跟过来：
+    拿掉 `perform` 里的 chmod 回写后 103 条全绿，而落点会变成 0o600。
+    """
+    vault, out = base_vault(tmp_path)
+    p = mk(vault / INBOX / "权限.md", "# 权限\n", age_days=3)
+    os.chmod(p, 0o644)
+    q = mk(vault / INBOX / "权限.txt", "纯文本\n", age_days=3)
+    os.chmod(q, 0o644)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [
+            {"stable_id": id_of(pv, "权限.md"), "action": "copy", "target": "节点"},
+            {"stable_id": id_of(pv, "权限.txt"), "action": "copy", "target": "节点"},
+        ],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    for name in ("权限.md", "权限.txt"):
+        mode = stat.S_IMODE((vault / "节点" / name).stat().st_mode)
+        assert mode == 0o644, f"{name} 落点权限是 {oct(mode)}, 源是 0o644"
+
+
+def test_move_resumes_when_the_action_landed_but_done_was_not_recorded(tmp_path):
+    """M10: `resumable` 是「主动作的 os.replace 已原子完成、commit 还没落账」时
+    唯一能让重跑走下去的分支（它自己的注释：没有这一层，move/recycle 做成之后重跑会
+    **恒**卡在新鲜度守卫上）。把它写死成 False 后 103 条全绿 —— 正面路径没人走。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "续跑.md", "# 续跑\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "续跑.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    drop_rows(batch_dir, "done")  # 主动作已完成、commit 没落账
+    assert not (vault / INBOX / "续跑.md").exists() and (vault / "归档" / "续跑.md").is_file()
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode == 0, f"resumable 分支没走到, 卡在新鲜度守卫上: {r.stderr[:300]}"
+    assert (vault / "归档" / "续跑.md").is_file()
+    done = [x for x in journal_rows(batch_dir) if x.get("state") == "done"]
+    assert len(done) == 1, f"续跑应当补上恰一条 done 行, 实得 {len(done)}"
+
+
+def test_target_symlink_pointing_back_into_the_vault_is_rejected(tmp_path):
+    """M11: 既有 `bad_targets` 里标「祖先含 symlink」的那一条，夹具的 symlink 指向
+    **vault 外**，于是它先被更早的 realpath 边界判据拒掉 —— `validate_target` 的
+    `assert_symlink_free` 零覆盖（拿掉它 103 条全绿）。
+
+    能把两道判据分开的对照输入是一条**指回 vault 内**的目录 symlink。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "别名.md", "# 别名\n", age_days=3)
+    (vault / "别名").symlink_to(vault / "归档", target_is_directory=True)
+    assert Path(os.path.realpath(vault / "别名")).parent == vault.resolve(), "前置: realpath 仍在 vault 内"
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "别名.md"), "action": "copy", "target": "别名"}],
+    )
+    before = snapshot(vault, skip=("outputs",))
+
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "指回 vault 内的目录 symlink 被接受了"
+    assert snapshot(vault, skip=("outputs",)) == before
+    assert no_outputs(vault), "拒绝被推迟到 perform 之后了（outputs/ 已经建出来）"
+
+
+def test_tampered_rel_path_shape_is_rejected_on_its_own(tmp_path):
+    """M12: 既有那道门的输入 `"../vault外.md"` 同时命中三道判据，实际绿在最后一道上 ——
+    前两道（`..`/绝对路径、两段形状）**同时拿掉**仍 103 全绿。
+
+    这里给形状检查一个**独占**输入：三段、无 `..`、首段仍是收件箱名。
+    再加一条单段输入 —— 形状检查缺席时它会让 `parts[1]` 抛 IndexError，
+    从「干净拒绝」退化成裸 traceback。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "形状.md", "# 形状\n", age_days=3)
+    pv = make_preview(vault, out)
+    sid = id_of(pv, "形状.md")
+    raw = json.loads(pv.read_text(encoding="utf-8"))
+
+    for bad_rel in (f"{INBOX}/子目录/深.md", "形状.md"):
+        data = json.loads(json.dumps(raw))
+        for it in data["items"]:
+            if it.get("stable_id") == sid:
+                it["rel_path"] = bad_rel
+        tampered = tmp_path / "tampered.json"
+        tampered.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
+        dec = write_decisions(tmp_path / "d.json", [{"stable_id": sid, "action": "copy", "target": "节点"}])
+        before = snapshot(vault, skip=("outputs",))
+        r = run_apply(vault, tampered, dec)
+        assert r.returncode != 0, f"rel_path={bad_rel!r} 被接受了"
+        assert "Traceback" not in r.stderr, f"rel_path={bad_rel!r} 退化成裸 traceback: {r.stderr[:300]}"
+        assert "形状不对" in r.stderr or "对不上" in r.stderr or "指纹" in r.stderr, r.stderr[:300]
+        assert snapshot(vault, skip=("outputs",)) == before
+
+
+def test_equal_length_edit_after_preview_is_rejected_on_first_run(tmp_path):
+    """M13: 既有「preview 过期」那道门的输入 size 和 mtime **同时**变，于是绿在 size
+    判据上 —— 把 mtime 比对短路掉后 103 条全绿。
+
+    这里给 mtime 判据一个**独占**输入：等长改写（size 恒定），且**首跑**
+    （账上没有任何 prior 行，sha 复核那条路走不到）。
+    """
+    vault, out = base_vault(tmp_path)
+    src = mk(vault / INBOX / "等长.md", "# AAAA\n", age_days=3)
+    pv = make_preview(vault, out)
+    size_before = src.stat().st_size
+
+    src.write_text("# BBBB\n", encoding="utf-8")  # size 恒定，只有 mtime 变
+    assert src.stat().st_size == size_before, "前置没成立: 这一步必须等长"
+    before = snapshot(vault, skip=("outputs",))
+
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "等长.md"), "action": "copy", "target": "节点"}],
+    )
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "等长改写在首跑上没被拦下"
+    assert "修改时间" in r.stderr, f"拒绝的理由不是 mtime: {r.stderr[:300]}"
+    assert snapshot(vault, skip=("outputs",)) == before
+    assert no_outputs(vault)
+
+
+def test_record_receipt_shas_seals_before_appending(tmp_path):
+    """L9: D-2 那道端到端门的夹具同时造了**中间损坏**和**末行缺换行**两种病，于是
+    `record_receipt_shas` 的第一句 `read_rows()` 直接抛 —— 「先封口再追加」那一半
+    从来没被跑到（删掉 `seal_tail_if_needed()` 那一行，那道门照样绿）。
+
+    ⛔ 如实说明：把 BLOCKER-B 修好之后，所有 CLI 路径上 `load()` 都已经先封过口，
+    这一句在生产链路上是**纵深防御**、没有「第一个封口者」的可达路径。所以这道门
+    直接在模块级调它 —— 只有一种病（末行缺换行、内容完好），`read_rows()` 读得回来，
+    于是 seal 与 append 两句都真的执行。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    tail = json.dumps(
+        {"seq": 1, "state": uj.STATE_DONE, "op": "copy", "batch_id": j.batch_id},
+        ensure_ascii=False,
+    )
+    first = json.dumps(
+        {"seq": 1, "state": uj.STATE_PLANNED, "op": "copy", "batch_id": j.batch_id},
+        ensure_ascii=False,
+    )
+    j.journal_path.write_text(first + "\n" + tail, encoding="utf-8")  # ⛔ 末尾**不**补换行
+    assert not j.journal_path.read_text(encoding="utf-8").endswith("\n"), "前置: 必须缺结尾换行"
+
+    j.record_receipt_shas("receipt", {"/x": "a" * 64})
+
+    raw = j.journal_path.read_text(encoding="utf-8")
+    lines = [ln for ln in raw.split("\n") if ln.strip()]
+    assert tail in lines, "末行那条完整记录被新追加的内容粘掉了（= 没有先封口）"
+    assert any('"receipt_sha"' in ln for ln in lines), "receipt_sha 行没写进去"
+    for ln in lines:
+        json.loads(ln)  # 每一行都必须仍是合法 JSON
+
+
+def test_backup_refuses_when_the_stale_dir_is_a_symlink(tmp_path):
+    """L2: `backup()` 里那条 `assert_symlink_free(self.stale_root)` 无门 —— 删掉它
+    103 条门全绿。
+
+    可达路径：备份落点上已经有一份**内容不同**的文件（用户放的 / 上一批的残留），
+    于是 `backup()` 必须先把它挪进 `stale/` 留痕；此时 `stale/` 若是一条指向 vault 外的
+    symlink，那份文件就会被搬出 vault。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    vault = root / "vault"
+    (vault / "_待处理").mkdir(parents=True, exist_ok=True)
+    src = vault / "_待处理" / "备份源.md"
+    src.write_text("# 源\n", encoding="utf-8")
+
+    occupied = j.backup_root / "_待处理" / "备份源.md"
+    occupied.parent.mkdir(parents=True, exist_ok=True)
+    occupied.write_text("用户放在备份落点上的东西\n", encoding="utf-8")  # 内容不同 ⇒ 必须挪走留痕
+    mine = occupied.read_bytes()
+
+    outside = root.parent / "备份外面"
+    outside.mkdir()
+    if j.stale_root.exists():
+        os.replace(j.stale_root, root / "stale-挪开-bk")
+    j.stale_root.symlink_to(outside, target_is_directory=True)
+
+    try:
+        j.backup(src, "_待处理/备份源.md")
+        raise AssertionError("stale/ 是 symlink 却照样挪了")
+    except (OSError, uj.JournalError, SystemExit):
+        pass
+    assert occupied.read_bytes() == mine, "备份落点上那份用户文件被动了"
+    assert sorted(p.name for p in outside.iterdir()) == [], "它被搬到 vault 外面去了"
+
+
+def test_target_dot_gets_a_clean_refusal_not_a_bare_traceback(tmp_path):
+    """L3/L6: `Path(".").parts` 与 `Path("./").parts` 都是**空元组**（pathlib 把纯 `.`
+    规范化掉了），而 `raw.strip("/")` 判非空放行了它 ⇒ 取 `parts[0]` 抛裸 IndexError，
+    逃出本文件承诺的 `die()` 统一出口。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "点.md", "# 点\n", age_days=3)
+    pv = make_preview(vault, out)
+    sid = id_of(pv, "点.md")
+    before = snapshot(vault, skip=("outputs",))
+    for bad in (".", "./", "//"):
+        dec = write_decisions(tmp_path / "d.json", [{"stable_id": sid, "action": "copy", "target": bad}])
+        r = run_apply(vault, pv, dec)
+        assert r.returncode != 0, f"target={bad!r} 被接受了"
+        assert "Traceback" not in r.stderr, f"target={bad!r} 给的是裸栈: {r.stderr[:300]}"
+        assert r.stderr.lstrip().startswith("✗"), f"target={bad!r} 不是干净拒绝: {r.stderr[:200]}"
+        assert snapshot(vault, skip=("outputs",)) == before
+        assert no_outputs(vault)
+
+
+def test_corrupt_journal_on_the_second_read_is_still_a_clean_refusal(tmp_path):
+    """L5: 第一次 `read_rows()` 已经按「账本损坏要给干净的拒绝, 不是裸 traceback」包过了，
+    而守卫全过之后的 `journal.load()` 没有同等包裹 —— 它比 `read_rows()` 还多一步
+    **会写盘的** `seal_tail_if_needed()`。
+
+    ⛔ 第一版这道门用的输入是「账本中间有坏行」—— 那在**第一次** `read_rows()` 就被拦下了，
+    门绿在更早的判据上（整改前的归档树上照样绿，实测）。真正到得了第二次读账的输入是：
+    账本**读得回来**但**需要封口**（末行缺结尾换行），而封口那一步**写不进去**
+    （账本只读）—— 于是失败恰好发生在 `load()` 里、且只发生在那里。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "二次读账.md", "# 二次读账\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "二次读账.md"), "action": "copy", "target": "节点"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    jp = batch_dir / "journal.jsonl"
+    raw = jp.read_text(encoding="utf-8")
+    assert raw.endswith("\n")
+    jp.write_text(raw[:-1], encoding="utf-8")  # 末行缺结尾换行 ⇒ load() 必须先封口
+    orig = stat.S_IMODE(jp.stat().st_mode)
+    os.chmod(jp, 0o444)  # 封口那一步写不进去 ⇒ 失败只发生在 load() 里
+    try:
+        r = run_apply(vault, pv, dec)
+    finally:
+        os.chmod(jp, orig)
+
+    assert r.returncode != 0
+    assert "Traceback" not in r.stderr, f"第二次读账的失败以裸栈收场: {r.stderr[:400]}"
+    assert r.stderr.lstrip().startswith("✗"), r.stderr[:200]
+    # ⛔ 敏感性锚: 失败确实来自**封口那一步**（不可追加），不是别的更早的守卫。
+    assert "不可追加" in r.stderr, f"拒绝的理由不是封口写不进去: {r.stderr[:300]}"
+
+
+def test_name_too_long_says_the_real_reason(tmp_path):
+    """L7: 唯一名比原名多约 33 字节，于是原名接近 NAME_MAX 的材料在写原语上必失败 ——
+    而 `_open_new_exclusive` 把**所有** OSError 一律包成「已被占用或不可创建」，
+    用户按「已被占用」去查会一无所获。
+    """
+    uj = load_journal_module()
+    vault, out = base_vault(tmp_path)
+    # ⛔ 必须用 ASCII: 本机 APFS 的上限实测是按**字符数**算的（中文 273 字节可建、
+    # ASCII 258 字符不可），拿中文名根本够不到那条线 —— 门会静默空转。
+    long_name = "a" * 248 + ".md"
+    # ⛔ 前提自证: 原名本身可建、而加上 tmp 开销之后必然越界。换个文件系统时这两条
+    # 断言会先说话，不会让门悄悄变成恒绿。
+    probe = tmp_path / long_name
+    probe.write_text("x", encoding="utf-8")
+    assert len(long_name) + uj.TMP_NAME_OVERHEAD > os.pathconf(str(tmp_path), "PC_NAME_MAX"), (
+        "本文件系统上限太宽, 这条门够不到 ENAMETOOLONG —— 需要换更长的名字"
+    )
+    mk(vault / INBOX / long_name, "# 长名\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, long_name), "action": "copy", "target": "节点"}],
+    )
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "长名材料居然写成功了（那这条门的前提不成立）"
+    assert "文件名太长" in r.stderr, f"给的还是「已被占用」那句误导: {r.stderr[:300]}"
+    assert "已被占用" not in r.stderr
+    assert uj.TMP_NAME_OVERHEAD > 30, "开销常量看起来不对"
+
+
+def test_receipt_accounts_for_the_parent_of_a_newly_created_destination(tmp_path):
+    """L13: 落点目录若是本次**新建**的（`归档/2026`），被改动条目集合的其实是它的
+    **父目录** `归档` —— 而 `归档` 从来没进过任何一条账目行，于是撤销既不还原它的 mtime、
+    也不把它登进 `dirs_not_retimed`。回执的「目录时间」一节自称完整，却漏了它。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "深层.md", "# 深层\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "深层.md"), "action": "move", "target": "归档/2026"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    assert (vault / "归档" / "2026" / "深层.md").is_file()
+
+    u = run_undo(vault, batch_dir / "journal.jsonl")
+    assert u.returncode == 0, u.stderr[:300]
+    receipt = json.loads((batch_dir / "undo-receipt.json").read_text(encoding="utf-8"))
+    mentioned = (
+        set(receipt.get("dirs_retimed") or [])
+        | {d["dir"] for d in (receipt.get("dirs_not_retimed") or [])}
+        | set(receipt.get("created_dirs") or [])
+    )
+    assert "归档" in mentioned, f"新建落点的父目录 `归档` 被改动了却既不还原也不登记: {sorted(mentioned)}"
+
+
+def test_every_malformed_input_gets_a_clean_refusal_not_a_crash(tmp_path):
+    """⛔ 分组守卫普查（§6.12b）引出：11 组守卫「整组中和后整套仍全绿」——
+    验伪查明不是「没有门」，是**那些路径上的门只断言了 `rc != 0`**，
+    分不出「干净拒绝」与「崩溃退出」。
+
+    实测（镜像树）：中和 `load_json_file` 的 5 道守卫后喂一份非 JSON 的 preview，
+    **rc 仍是 1，但给的是裸 Traceback**。本卡对这件事是有明文要求的
+    （L3/L6「不是裸 traceback」、L5 同款），却没有一条门把它钉住。
+
+    这条门横切覆盖「坏输入」的各个类：每一类都必须
+    ① rc ≠ 0 ② stderr **不含** Traceback ③ 首个非空行以 `✗` 开头 ④ 零写。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "正常.md", "# 正常\n", age_days=3)
+    good_pv = make_preview(vault, out)
+    good_dec = write_decisions(
+        tmp_path / "ok.json",
+        [{"stable_id": id_of(good_pv, "正常.md"), "action": "copy", "target": "节点"}],
+    )
+
+    junk = tmp_path / "非json.json"
+    junk.write_text("这根本不是 JSON\n", encoding="utf-8")
+    top_list = tmp_path / "顶层是数组.json"
+    top_list.write_text("[1, 2, 3]\n", encoding="utf-8")
+    wrong_ver = tmp_path / "版本不对.json"
+    wrong_ver.write_text(json.dumps({"schema_version": 99, "items": []}), encoding="utf-8")
+    link_pv = tmp_path / "是条软链.json"
+    link_pv.symlink_to(good_pv)
+    missing = tmp_path / "不存在.json"
+
+    cases = [
+        ("preview 非 JSON", ["--preview", str(junk), "--decisions", str(good_dec)]),
+        ("preview 顶层是数组", ["--preview", str(top_list), "--decisions", str(good_dec)]),
+        ("preview 版本不对", ["--preview", str(wrong_ver), "--decisions", str(good_dec)]),
+        ("preview 是 symlink", ["--preview", str(link_pv), "--decisions", str(good_dec)]),
+        ("preview 不存在", ["--preview", str(missing), "--decisions", str(good_dec)]),
+        ("decisions 非 JSON", ["--preview", str(good_pv), "--decisions", str(junk)]),
+        ("decisions 顶层是数组", ["--preview", str(good_pv), "--decisions", str(top_list)]),
+        ("decisions 不存在", ["--preview", str(good_pv), "--decisions", str(missing)]),
+        (
+            "两个模式一起给",
+            ["--preview", str(good_pv), "--decisions", str(good_dec), "--undo", str(tmp_path / "j.jsonl")],
+        ),
+        ("执行模式缺 decisions", ["--preview", str(good_pv)]),
+        ("执行模式缺 preview", ["--decisions", str(good_dec)]),
+        (
+            "work-dir 越界 vault",
+            ["--preview", str(good_pv), "--decisions", str(good_dec), "--work-dir", str(tmp_path / "vault外工作目录")],
+        ),
+    ]
+    before = snapshot(vault, skip=("outputs",))
+    for name, extra in cases:
+        r = subprocess.run(
+            [sys.executable, str(APPLY_SCRIPT), "--vault", str(vault), "--now", NOW_ISO, *extra],
+            capture_output=True,
+            text=True,
+        )
+        err = (r.stderr or "").strip()
+        assert r.returncode != 0, f"[{name}] 居然被接受了"
+        assert "Traceback" not in err, f"[{name}] 给的是裸 traceback: {err[:260]}"
+        first = next((ln for ln in err.split("\n") if ln.strip()), "")
+        assert first.lstrip().startswith("✗"), f"[{name}] 首行不是干净拒绝: {first[:160]}"
+        assert snapshot(vault, skip=("outputs",)) == before, f"[{name}] 动了盘"
+        assert no_outputs(vault), f"[{name}] 把 outputs/ 建出来了"
+
+    # ⛔ 对照锚: 正常输入照常跑通 —— 证明上面的拒绝不是「什么都拒」。
+    assert run_apply(vault, good_pv, good_dec).returncode == 0
+    assert (vault / "节点" / "正常.md").is_file()
+
+
+def test_bad_vault_arguments_get_a_clean_refusal(tmp_path):
+    """同上，覆盖 `resolve_vault` 那一组（vault 本身是 symlink / 不存在）。"""
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "v.md", "# v\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "v.md"), "action": "copy", "target": "节点"}],
+    )
+    linked_vault = tmp_path / "软链vault"
+    linked_vault.symlink_to(vault, target_is_directory=True)
+    for name, v in (("vault 是 symlink", linked_vault), ("vault 不存在", tmp_path / "没有这个vault")):
+        r = subprocess.run(
+            [
+                sys.executable,
+                str(APPLY_SCRIPT),
+                "--vault",
+                str(v),
+                "--now",
+                NOW_ISO,
+                "--preview",
+                str(pv),
+                "--decisions",
+                str(dec),
+            ],
+            capture_output=True,
+            text=True,
+        )
+        err = (r.stderr or "").strip()
+        assert r.returncode != 0, f"[{name}] 居然被接受了"
+        assert "Traceback" not in err, f"[{name}] 裸 traceback: {err[:200]}"
+        assert err.lstrip().startswith("✗"), f"[{name}] 不是干净拒绝: {err[:160]}"
+
+
+# ─── 分组守卫普查（§6.12b）引出：6 组「整组中和仍全绿」里可测的那 4 组 ───
+
+
+def test_plan_refuses_an_unknown_op(tmp_path):
+    """`BatchJournal.plan()` 的「未知动作」是纵深防御（CLI 侧 `validate_action` 先拦），
+    但它自己一条门都没有 —— 整组中和后整套仍全绿。G5-10 要直接复用这个模块，
+    到时候 CLI 那层守卫就不在了。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    base_plan = dict(
+        seq=1,
+        stable_id="x",
+        src="_待处理/a.md",
+        dst="节点/a.md",
+        dst_base=uj.BASE_VAULT,
+        backup=None,
+        sha256_before="0" * 64,
+        mtime_ns_before=0,
+        mode_before=0o644,
+    )
+    try:
+        j.plan(**{**base_plan, "op": "蒸发"})
+        raise AssertionError("未知动作被写进账了")
+    except uj.JournalError as e:
+        assert "未知动作" in str(e), str(e)
+    # ⛔ 对照锚: 合法动作照常写得进去 —— 证明上面的拒绝不是「什么都拒」。
+    j.plan(**{**base_plan, "op": uj.OP_COPY})
+    assert any(r.get("op") == uj.OP_COPY for r in j.read_rows())
+
+
+def test_mkdir_chain_refuses_outside_its_creation_bound(tmp_path):
+    """`mkdir_chain` 的三道边界（上界不是普通目录 / 目标落在上界之外 / 路径上有非目录）
+    整组无门。它是**唯一**被授权造目录的地方，G5-10 复用时这三道就是全部防线。"""
+    uj, j, root = journal_module_fixture(tmp_path)
+    # ① 目标落在允许创建的上界之外
+    try:
+        j.mkdir_chain(root.parent / "上界之外" / "深")
+        raise AssertionError("越界造目录被放行了")
+    except uj.JournalError as e:
+        assert "上界之外" in str(e), str(e)
+    assert not (root.parent / "上界之外").exists(), "拒绝之前已经把目录造出来了"
+
+    # ② 路径上有一段不是普通目录
+    occupied = Path(j.root) / "占位"
+    occupied.write_text("我是文件不是目录\n", encoding="utf-8")
+    try:
+        j.mkdir_chain(occupied / "下面")
+        raise AssertionError("路径上压着一个文件却照样造了")
+    except uj.JournalError as e:
+        assert "不是普通目录" in str(e), str(e)
+    assert occupied.is_file() and occupied.read_text(encoding="utf-8").startswith("我是文件")
+
+    # ⛔ 对照锚: 界内的正常路径照常造得出来。
+    ok = Path(j.root) / "界内" / "一层" / "两层"
+    j.mkdir_chain(ok)
+    assert ok.is_dir()
+
+
+def test_finish_restore_refuses_to_touch_a_foreign_source(tmp_path):
+    """`_finish_restore` 的两道守卫：原路径不是普通文件 / 原路径上不是当初那一份。
+
+    它们的意义是「拒绝必须发生在动手之前」（Codex round-3 H1）—— 否则「拒绝了」的同时
+    已经对用户放在那里的东西 chmod/utime 过了。整组无门。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    vault = Path(j.root)
+    (vault / "_待处理").mkdir(parents=True, exist_ok=True)
+    src = vault / "_待处理" / "收尾.md"
+    src.write_text("用户后来放的另一份\n", encoding="utf-8")
+    os.chmod(src, 0o644)
+    row = {
+        "seq": 1,
+        "op": uj.OP_MOVE,
+        "src": "_待处理/收尾.md",
+        "sha256_before": "0" * 64,
+        "mtime_ns_before": 123456789,
+        "mode_before": 0o600,
+    }
+    before = (src.read_bytes(), src.stat().st_mtime_ns, stat.S_IMODE(src.stat().st_mode))
+
+    try:
+        j._finish_restore(row, src)
+        raise AssertionError("原路径上不是当初那一份, 却照样动手了")
+    except uj.JournalError as e:
+        assert "不是当初那一份" in str(e), str(e)
+    after = (src.read_bytes(), src.stat().st_mtime_ns, stat.S_IMODE(src.stat().st_mode))
+    assert after == before, "拒绝之前已经对用户的文件 chmod/utime 过了"
+
+    # ② 原路径是一条 symlink ⇒ 同样拒绝且不动它
+    link = vault / "_待处理" / "软链.md"
+    link.symlink_to(src)
+    try:
+        j._finish_restore({**row, "src": "_待处理/软链.md"}, link)
+        raise AssertionError("原路径是 symlink 却照样动手了")
+    except uj.JournalError as e:
+        assert "不是普通文件" in str(e), str(e)
+
+
+def test_verify_restored_catches_every_one_of_its_three_dimensions(tmp_path):
+    """`_verify_restored` 的 sha / mtime_ns / mode 三项自检整组无门 ——
+    全树 undo 那道门是靠**测试自己**的快照比对发现差异的，生产侧这道自检拿掉也不会红。
+
+    这里逐维给一个**独占输入**：另外两维都对，只有这一维不对。
+    """
+    uj, j, root = journal_module_fixture(tmp_path)
+    vault = Path(j.root)
+    (vault / "_待处理").mkdir(parents=True, exist_ok=True)
+    src = vault / "_待处理" / "自检.md"
+    src.write_text("原样\n", encoding="utf-8")
+    os.chmod(src, 0o644)
+    st = src.stat()
+    good = {
+        "seq": 1,
+        "sha256_before": uj.sha256_file(src),
+        "mtime_ns_before": st.st_mtime_ns,
+        "mode_before": st.st_mode,
+    }
+
+    j._verify_restored(good, src)  # 对照锚: 三维都对时必须放行
+
+    for tag, bad, word in (
+        ("内容", {**good, "sha256_before": "f" * 64}, "内容对不上"),
+        ("时间", {**good, "mtime_ns_before": st.st_mtime_ns + 10**9}, "修改时间对不上"),
+        ("权限", {**good, "mode_before": (st.st_mode & ~0o777) | 0o600}, "权限位对不上"),
+    ):
+        try:
+            j._verify_restored(bad, src)
+            raise AssertionError(f"{tag}维对不上却放行了")
+        except uj.JournalError as e:
+            assert word in str(e), f"{tag}: {e}"
+
+    # ④ 还原后原路径不是普通文件
+    link = vault / "_待处理" / "自检软链.md"
+    link.symlink_to(src)
+    try:
+        j._verify_restored(good, link)
+        raise AssertionError("还原成 symlink 却放行了")
+    except uj.JournalError as e:
+        assert "不是普通文件" in str(e), str(e)
+
+
+def test_acting_move_with_both_sides_gone_refuses_and_does_not_guess(tmp_path):
+    """分组普查剩下的第 3 组：`perform` 的「源与落点都不存在, 不猜它去哪了」。
+
+    可达状态：一条 move 的 `acting` 行已落账（= 已经动过盘），然后源和落点**双双不在**
+    （用户手工挪走 / 同步工具搬走）。工具必须**拒绝并说清**，而不是猜它去哪了 ——
+    猜错的代价是拿备份往一个错的地方写。
+
+    ⛔ 本门钉的是**这条性质**，不预设是哪一层拦下的：`build_plans` 的新鲜度守卫与
+    `perform` 的这一条都可能先开火。断言只要求「干净拒绝 + 零写 + 备份仍在」。
+    """
+    vault, out = base_vault(tmp_path)
+    mk(vault / INBOX / "双失.md", "# 双失\n", age_days=3)
+    pv = make_preview(vault, out)
+    dec = write_decisions(
+        tmp_path / "d.json",
+        [{"stable_id": id_of(pv, "双失.md"), "action": "move", "target": "归档"}],
+    )
+    assert run_apply(vault, pv, dec).returncode == 0
+    batch_dir = only_batch_dir(vault)
+    drop_rows(batch_dir, "done")  # 剩 planned + acting = 「动过盘但没记 done」
+
+    # 源已经被搬走了（move 做成了）；再把落点也挪走 ⇒ 两边都不在
+    moved = vault / "归档" / "双失.md"
+    assert moved.is_file() and not (vault / INBOX / "双失.md").exists()
+    os.replace(moved, tmp_path / "被用户挪到别处.md")
+
+    before = snapshot(vault, skip=("outputs",))
+    r = run_apply(vault, pv, dec)
+    assert r.returncode != 0, "两边都不在, 却还是往下做了"
+    err = (r.stderr or "").strip()
+    assert "Traceback" not in err, f"给的是裸 traceback: {err[:260]}"
+    assert err.lstrip().startswith("✗"), f"不是干净拒绝: {err[:200]}"
+    assert snapshot(vault, skip=("outputs",)) == before, "拒绝路径动了盘"
+    # ⛔ 敏感性锚: 备份**仍在** —— 这条性质的意义就是「不猜, 但退路还在」。
+    backups = sorted(p.name for p in (batch_dir / "backup").rglob("*") if p.is_file())
+    assert "双失.md" in backups, f"备份不在了, 退路断了: {backups}"
diff --git a/canvas-vault/.claude/scripts/undo_journal.py b/canvas-vault/.claude/scripts/undo_journal.py
new file mode 100644
index 00000000..c093c6a8
--- /dev/null
+++ b/canvas-vault/.claude/scripts/undo_journal.py
@@ -0,0 +1,1570 @@
+#!/usr/bin/env python3
+"""批次备份快照 + undo journal —— 共用模块 (CARD-G5-7, G5-10 复用)。
+
+本模块只提供「把一批文件搬动记成可逆的账」这一件事, 不认识收件箱、不认识白板:
+  · BatchJournal(work_dir, batch_id, root=, fingerprint=)  一个批次 = 一个目录 = 一本账
+  · backup(src)                       —— op 之前的逐字节快照 (undo 的真相源)
+  · plan(...) / commit(...)           —— 先落 planned 行再动手, 动完落 done 行
+  · undo()                            —— 逆序还原; copy/link 产物**移入**回收目录
+  · write_provenance(path, meta)      —— frontmatter 溯源块, 原子写 + 回写 mtime/mode
+  · write_pair_atomically(items)      —— 成对发布 (两份都写好 tmp 才双双就位)
+
+⛔ 三条贯穿全模块的规矩:
+
+1. **零物理删除原语** (os.remove / os.unlink / Path.unlink / shutil.rmtree /
+   os.rmdir / send2trash)。「撤销一次 copy」= 把副本挪进 recycle/undone/, 不是删掉它;
+   写失败的 tmp 挪进 stale/, 不是删掉它。裁判见
+   backend/tests/skills/test_g5_7_inbox_apply.py 的 F2 AST 门 (数 Call 节点, 不数文本)。
+
+2. **「零删除原语」不等于「不会覆盖」。** `os.replace` / `copyfile` / `O_TRUNC` 都能
+   在不调用任何删除原语的情况下把既有内容换掉。所以每一处落笔前都要先证明落点
+   **归自己所有**。
+
+3. **「内容相同」不等于「归我所有」。** 判归属只用可计算的等式: done 行比
+   `sha256_after`; planned 行比「与备份逐字节相同」或「等于把备份按账上那份
+   `prov_meta` 渲染一遍的结果」—— 后者是纯函数, 期望值算得出来, 不是「看起来像」。
+   凡是「全文里出现了某个子串」这类启发式都不作数 (Codex round-2 H1)。
+
+祖先链无 symlink 的判定复用 board-split/scripts/split_preview.py 的
+`assert_symlink_free`（与 clear-inbox/scripts/inbox_preview.py:266-290 同一条理由:
+自己简单写一下, 等于在安全面上开一个没人审过的旁路）。**回执的成对发布不复用**它的
+`write_pair_atomically_checked` —— 那个函数用 `O_CREAT` 先把两个目标建出来, 失败时
+按路径回滚 unlink, 并发下会删到别人刚放上去的同名目录项。
+"""
+
+from __future__ import annotations
+
+import errno
+import hashlib
+import importlib.util
+import json
+import os
+import shutil
+import stat as stat_mod
+import sys
+import uuid
+from datetime import datetime, timezone
+from pathlib import Path
+
+SCHEMA_VERSION = 1
+GENERATOR = "undo_journal.py v1.2 (CARD-G5-7 batch backup + undo journal)"
+
+#: 复用来源 —— <vault>/.claude/scripts/ → <vault>/.claude/skills/board-split/scripts/
+_SP_PATH = Path(__file__).resolve().parents[1] / "skills" / "board-split" / "scripts" / "split_preview.py"
+
+
+def _load_split_preview():
+    """加载写侧防御的单一真相源。⛔ 缺失即拒绝运行, 不做本地降级实现。"""
+    if not _SP_PATH.is_file():
+        raise SystemExit(
+            f"✗ 复用来源缺失, 拒绝以未加固的写侧运行。需要文件: {_SP_PATH}\n  （祖先链 symlink 守卫复用该模块。）"
+        )
+    spec = importlib.util.spec_from_file_location("_g57_split_preview", _SP_PATH)
+    mod = importlib.util.module_from_spec(spec)
+    # ⛔ exec_module 默认会在被导入模块**旁边**写 __pycache__/*.pyc —— 那是往 vault
+    # 里、而且是另一条车道的目录里落文件。零写侧不是「不改用户的 md」。
+    prev = sys.dont_write_bytecode
+    sys.dont_write_bytecode = True
+    try:
+        spec.loader.exec_module(mod)
+    finally:
+        sys.dont_write_bytecode = prev
+    return mod
+
+
+_SP = _load_split_preview()
+
+# ───────────────────────────────── 常量 ─────────────────────────────────
+
+JOURNAL_NAME = "journal.jsonl"
+BACKUP_DIR = "backup"
+RECYCLE_DIR = "recycle"
+UNDONE_DIR = "undone"
+STALE_DIR = "stale"
+
+PROVENANCE_KEY = "clear_inbox_provenance"
+TMP_SUFFIX = ".undo-journal-tmp"
+
+#: journal 行的状态机。tail_sealed 是给「掉电留下的半行」封口用的哨兵行。
+STATE_PLANNED = "planned"
+#: ⛔ 「排期了」与「已经动过盘」之间必须有一条**可观测**的界。没有它, 落点上那份
+#: 同字节的文件既可能是我们刚复制的, 也可能是用户放的, 代码分不出来 —— 于是会给
+#: 用户的文件写溯源、撤销时又把它挪走。多这一行账换来状态机是全的。
+STATE_ACTING = "acting"
+STATE_DONE = "done"
+STATE_UNDONE = "undone"
+STATE_TAIL_SEALED = "tail_sealed"
+#: 记「上一次往回执落点写下去的内容的 sha256」。不是业务状态, 只是归属证据 ——
+#: 有了它, 「这份回执是不是我自己上一版」就是一条可计算的等式, 不必猜。
+STATE_RECEIPT_SHA = "receipt_sha"
+#: 有业务含义的状态 —— 「同一 seq 的最新一条」按它们判, 不按「出现过没有」。
+BUSINESS_STATES = (STATE_PLANNED, STATE_ACTING, STATE_DONE, STATE_UNDONE)
+#: 账本里允许出现的全部 state —— 认不出来的一律按损坏处理, 不静默忽略。
+KNOWN_STATES = BUSINESS_STATES + (STATE_TAIL_SEALED, STATE_RECEIPT_SHA)
+
+#: 可逆的搬运动作。skip 只记账、不动盘。
+OP_COPY = "copy"
+OP_LINK = "link"
+OP_MOVE = "move"
+OP_RECYCLE = "recycle"
+OP_SKIP = "skip"
+OPS = (OP_COPY, OP_LINK, OP_MOVE, OP_RECYCLE, OP_SKIP)
+OPS_LEAVE_SOURCE = (OP_COPY, OP_LINK)
+OPS_TAKE_SOURCE = (OP_MOVE, OP_RECYCLE)
+
+#: dst 的基准: vault 相对 (copy/link/move) 或批次目录相对 (recycle)
+BASE_VAULT = "vault"
+BASE_BATCH = "batch"
+
+PROVENANCE_WRITTEN = "written"
+PROVENANCE_NOT_MARKDOWN = "skipped:not-markdown"
+PROVENANCE_NOT_UTF8 = "skipped:not-utf8"
+PROVENANCE_UNTERMINATED = "skipped:unterminated-frontmatter"
+
+#: ⛔ 这三个字符会被 str.splitlines() 当成换行 —— 落进 journal 就会让「一行一条
+#: 记录」的口径在不同读法下给出不同答案 (含它的那条记录永远重放不掉)。落盘前统一
+#: 转成 \u 转义 (JSON 字符串里合法), 于是整份 journal 里除了行分隔的 \n 再无
+#: 任何「像换行的字节」。读侧一律 split("\n"), 绝不用 splitlines()。
+_LINE_LIKE = {chr(0x2028): "\\u2028", chr(0x2029): "\\u2029", chr(0x0085): "\\u0085"}
+
+
+class JournalError(RuntimeError):
+    """账目层的拒绝 —— 消息即回执正文, 必须精确到「哪一件 / 为什么 / 现在在哪」。"""
+
+
+# ───────────────────────────── 原语 ─────────────────────────────
+
+
+def sha256_file(path) -> str:
+    h = hashlib.sha256()
+    with open(path, "rb") as f:
+        for chunk in iter(lambda: f.read(1 << 20), b""):
+            h.update(chunk)
+    return h.hexdigest()
+
+
+def utc_now_iso(now: datetime | None = None) -> str:
+    dt = now or datetime.now(timezone.utc)
+    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
+
+
+def is_symlink(path) -> bool:
+    return os.path.islink(str(path))
+
+
+def assert_path_safe(path, *, what: str) -> None:
+    """落笔面的通用准入: 祖先链无 symlink, 且末段本身不是 symlink。
+
+    ⛔ 两件事都要查。`O_NOFOLLOW` 只管末段, 而祖先里的一条 symlink 能把「词法上在
+    vault 内」的写整个重定向到别处。
+    """
+    p = Path(path)
+    _SP.assert_symlink_free(p.parent)
+    if is_symlink(p):
+        raise JournalError(f"✗ {what} 是一条 symlink, 拒绝跟随: {p}")
+
+
+def json_line(obj: dict) -> bytes:
+    """一条记录 = 一行 = 一次 os.write。sort_keys 让同输入逐字节可复现。"""
+    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
+    for ch, esc in _LINE_LIKE.items():
+        s = s.replace(ch, esc)
+    if "\n" in s:
+        raise JournalError("journal 记录里出现裸换行, 拒绝写入 (会把一条记录切成两条)")
+    return (s + "\n").encode("utf-8")
+
+
+def append_bytes(path: Path, payload: bytes) -> None:
+    """单次 O_APPEND write + fsync —— 一行即一个原子追加。"""
+    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
+    try:
+        fd = os.open(str(path), flags, 0o644)
+    except OSError as e:
+        raise JournalError(f"✗ journal 不可追加 (可能被 symlink 布防): {path} ({e})") from e
+    try:
+        n = os.write(fd, payload)
+        if n != len(payload):
+            raise JournalError(f"✗ journal 追加不完整 ({n}/{len(payload)} 字节): {path}")
+        os.fsync(fd)
+    finally:
+        os.close(fd)
+
+
+def _tmp_path_for(path: Path) -> Path:
+    """同目录、**唯一名**、点开头的临时文件名。
+
+    ⛔ 固定名 + `O_TRUNC` 是一条覆盖既有内容的路: 名字撞上用户的文件就把它截断;
+    若那个名字恰是指向原件的硬链接, 连原件一起改写。唯一名 + `O_EXCL` 让「撞上了」
+    变成一个响亮的失败, 而不是一次静默覆盖。点开头是给 Obsidian 看的 (它不索引点文件)。
+    """
+    return path.with_name(f".{path.name}.{os.getpid()}-{uuid.uuid4().hex[:8]}{TMP_SUFFIX}")
+
+
+#: 唯一名比原名多出的字节数上界: `.` + `.` + pid(≤7) + `-` + uuid8 + TMP_SUFFIX。
+#: 用来在 ENAMETOOLONG 时给出**准确**的原因, 而不是笼统的「已被占用」。
+TMP_NAME_OVERHEAD = 2 + 7 + 1 + 8 + len(TMP_SUFFIX)
+
+
+def _open_new_exclusive(tmp: Path) -> int:
+    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
+    try:
+        return os.open(str(tmp), flags, 0o600)
+    except OSError as e:
+        # ⛔ 「已被占用」对 ENAMETOOLONG 是**误导**: 唯一名比原名多 TMP_NAME_OVERHEAD
+        # 字节, 于是原名接近 NAME_MAX 的材料在这里必失败, 而用户按「已被占用」去查
+        # 会一无所获（全卡复核 L7）。把真正的原因说出来。
+        if getattr(e, "errno", None) == errno.ENAMETOOLONG:
+            raise JournalError(
+                f"✗ 文件名太长, 放不下临时文件名（临时名比原名多约 {TMP_NAME_OVERHEAD} 字节, "
+                f"多数文件系统上限 255）: {tmp.name} —— 请把材料改个短一点的名字再清仓"
+            ) from e
+        raise JournalError(f"✗ 临时文件已被占用或不可创建, 拒绝写入: {tmp} ({e})") from e
+
+
+def _write_fd(fd: int, data: bytes) -> None:
+    with os.fdopen(fd, "wb") as f:
+        f.write(data)
+        f.flush()
+        os.fsync(f.fileno())
+
+
+def _park_stale(tmp: Path, stale_dir: Path | None):
+    """写失败的 tmp 残片挪进 stale/ 留痕, 不做物理删除。
+
+    ⛔ 这个落点同样要过 symlink 守卫 —— 把 stale/ 指到 vault 外, 残片就被搬出去了。
+    守卫不过时**就地留着不动**: 这是异常处理路径, 再抛一个新异常会把真正的失败原因
+    盖掉, 而把残片留在原目录比搬到不知道哪里更安全。
+
+    返回残片最终所在的路径（停不成功就是它原来的位置）—— 调用方要能说出「哪一份
+    东西需要你去看一眼」, 否则「就地留着」等于无声地留下垃圾 (Codex round-4 L1)。
+    """
+    if stale_dir is None or not os.path.lexists(str(tmp)):
+        return None
+    try:
+        if is_symlink(stale_dir):
+            return tmp
+        _SP.assert_symlink_free(stale_dir.parent)
+        os.makedirs(str(stale_dir), exist_ok=True)
+        _SP.assert_symlink_free(stale_dir)
+        target = free_path(stale_dir / tmp.name)
+        if is_symlink(target):
+            return tmp
+        os.replace(str(tmp), str(target))
+        return target
+    except (OSError, SystemExit, JournalError):
+        return tmp  # 留在原地; 原始失败原因不被掩盖
+
+
+def preserve_foreign_file(path: Path, stale_dir: Path | None, owned_sha: str | None) -> bool:
+    """落点上若是一份**不属于我们**的普通文件, 先挪进 stale/ 留痕。停放成功返回 True。
+
+    ⛔ 「产物可以重新生成」不构成覆盖它的理由: 那个路径上放的可能根本不是我们的
+    产物, 而是用户自己的文件 (Codex round-4 H6)。本工具默认路径 0 物理删除, 覆盖
+    同样算「弄丢」。
+
+    ⛔ 作用域**只到回执落点**, 不进通用的 `_replace_or_park`。round-5 曾把它接进
+    通用路径, 于是业务文件每写一次溯源就被挪进 stale/ 一次, 而且「先挪走旧的、再
+    放新的」中间留出一个正式路径两头都不在的窗口 —— 中断在那里就谁也恢复不了
+    (Codex round-5 HIGH-2, 是 H6 整改自己引入的回归)。作用域和意图要分开看。
+
+    `owned_sha` = 上一次我们往这个路径写下去的内容的 sha256（记在账里）。落点字节与它
+    相等 ⇒ 那就是自家上一版产物, 直接让位不留痕（否则每次重跑都堆两份）。
+
+    ⛔ 判据是**可计算的等式**, 不是「全文里出现了 batch_id」那类子串启发式 —— 后者
+    与本模块第 3 条铁律正面冲突, 而且落点上任何恰好抄了批次号的用户笔记都会被零留痕
+    覆盖（独立复核 H-1 实证; 撤销模式的 batch_id 来自目录名, 长度还不受约束）。
+    """
+    if not os.path.lexists(str(path)) or is_symlink(path) or not Path(path).is_file():
+        return True
+    if owned_sha:
+        try:
+            if sha256_file(path) == owned_sha:
+                return True
+        except OSError:
+            pass
+    if stale_dir is None:
+        # ⛔ 没有留痕的地方 ⇒ 没有「留不住」这回事, 只有「不许盖」。`_park_stale` 在
+        # stale_dir 为 None 时返回 None, 若拿它跟原路径比就会判成「停放成功」——
+        # HIGH-1 那个洞会从默认参数上重新开一次（自查发现, 当前无调用方传 None,
+        # 但这是公开函数, G5-10 要复用）。
+        return False
+    return _park_stale(Path(path), stale_dir) != Path(path)
+
+
+def _replace_or_park(tmp: Path, path: Path, stale_dir: Path | None) -> None:
+    """就位。⛔ 最后这一步也要包在残片处理里 —— 它失败时 tmp 同样留在原地。
+
+    ⛔ 把**停放之后**的真实位置挂到异常上 (`_uj_residue`)。`_park_stale` 的 docstring
+    明写「返回残片最终所在的路径 …… 调用方要能说出哪一份东西需要你去看一眼」, 而这
+    一跳原先把返回值丢了 —— 调用方只能报 tmp 的旧路径, 用户照着去找是空的, 残片其实
+    躺在 stale/ 里 (Codex round-5 LOW-1)。它本来「登记不阻断」, 但 M-3 把 notes 打给
+    了用户, 这条错值从**没人看得到**变成**端到用户眼前**, 所以跟着 M-3 一起修。
+    """
+    try:
+        os.replace(str(tmp), str(path))
+    except BaseException as e:
+        parked = _park_stale(tmp, stale_dir)
+        if parked is not None:
+            try:
+                e._uj_residue = Path(parked)  # type: ignore[attr-defined]
+            except Exception:
+                pass  # 少数内建异常不许挂属性; 报旧路径也好过把原始失败原因弄丢
+        raise
+
+
+class JournalNotOursError(JournalError):
+    """这本账不是当前 vault / 不是一本批次账。
+
+    ⛔ 单独一个类型是为了让调用方能**区别对待**: 被判为「不是我们的」之后, 就
+    一个字节都不许再往那个目录写 —— 包括失败回执。原先所有撤销失败共用一个
+    except, 于是拒绝路径反手把对方批次真实的 undo-receipt 零留痕覆盖成一句假话
+    （全卡复核 BLOCKER-B）。
+    """
+
+
+def safe_join(base, rel, *, what: str) -> Path:
+    """把账本里记的相对路径拼到 base 上, 并**卡死形状**。
+
+    ⛔ 账本是躺在 vault 里 `outputs/clear-inbox/<batch>/journal.jsonl` 的普通文本:
+    用户手改、同步工具改、部分写坏都够得着 —— 它和 preview JSON 是**同一类**输入。
+    执行侧对 preview 的 `rel_path` 卡死了形状（`inbox_apply.source_path`, 注释原话
+    「一条 `../outside.md` 就能让执行侧去搬 vault 外的文件」）, 撤销侧却对
+    `src` / `dst` / `backup` 直接拼 —— 一条 `..` 就能把 vault 内的材料搬出 vault 并
+    报「✓ 已撤销」, 绝对路径变体还会在 vault 外造出目录链然后以裸 traceback 收场
+    （全卡复核 BLOCKER-C 实测）。
+
+    ⛔ 撤销是后悔药, 它比执行更该 fail-closed。`assert_symlink_free` 挡不住这条:
+    它比的是 normpath 与 realpath, 对**无 symlink 的** `../` 路径两者相等, 一律放行。
+    """
+    if not isinstance(rel, str) or not rel:
+        raise JournalError(f"✗ 账上的{what}不是一个路径: {rel!r}")
+    cand = Path(rel)
+    if cand.is_absolute():
+        raise JournalError(f"✗ 账上的{what}是绝对路径, 拒绝采信: {rel!r}")
+    if any(p == ".." for p in cand.parts):
+        raise JournalError(f"✗ 账上的{what}含 `..`, 拒绝越界: {rel!r}")
+    out = Path(base) / cand
+    # ⛔ 这里只做**词法**判定。物理层（祖先/末段是不是 symlink）由调用方既有的
+    # `assert_symlink_free` / `is_symlink` 守卫负责 —— 在这里改用 realpath 会把
+    # 「落点现在是一条指向 vault 外的 symlink」这种情况也吞进同一条错误里, 盖掉那些
+    # 更准确、用户更用得上的诊断（实测: 既有的 symlink 门会从「symlink」变成「越界」）。
+    base_norm = os.path.normpath(str(Path(base)))
+    out_norm = os.path.normpath(str(out))
+    if out_norm != base_norm and not out_norm.startswith(base_norm + os.sep):
+        raise JournalError(f"✗ 账上的{what}归一化后落在 {base} 之外, 拒绝越界: {rel!r}")
+    return out
+
+
+def park_into_stale(path, stale_dir: Path | None, *, what: str) -> Path:
+    """把落点上那份**不是我们造的**东西挪进 stale/ 留痕, 返回它的新位置。
+
+    ⛔ 和 `_park_stale`（给我们自己的 tmp 残片用、挪不成就就地留着）不同: 这里搬的是
+    **用户的文件**, 所以要求更严 —— 留痕目录先证明可用, 挪不成就抛。A_LINK 的半态
+    分支原先是裸 `os.makedirs` + `os.replace`, 是全卡唯一一处既不查 stale/ 是不是
+    symlink、也不记账的搬动: stale/ 被换成指向 vault 外的 symlink 时, 用户的笔记会被
+    无声搬出 vault 而工具报「✓ 全部完成」（全卡复核 HIGH-G 实测）。
+    """
+    assert_stale_dir_usable(stale_dir, what=what)
+    stale = Path(stale_dir)
+    os.makedirs(str(stale), exist_ok=True)
+    _SP.assert_symlink_free(stale)
+    target = free_path(stale / Path(path).name)
+    assert_path_safe(target, what=what)
+    os.replace(str(path), str(target))
+    return target
+
+
+def assert_stale_dir_usable(stale_dir: Path | None, *, what: str) -> None:
+    """落点上有外来文件时, 「有地方留痕」必须在**动盘之前**就证明得了。
+
+    ⛔ 只查 `stale_dir is None` 不够: 它有值但**不可用**（被占成普通文件 / 是一条
+    symlink / 祖先链里有 symlink）时校验段照样放行, 真正的拒绝被推迟到逐条 replace
+    的循环里 —— 第一份已经就位之后第二份才说「留不住」, 于是发布出去的一对回执互相
+    矛盾（机器读 .json 是新的, 人读 .md 还是旧的）, 而两段式**之前**这条输入是零写的。
+    这是两段式整改自己引入的回退 (独立复核 round-2 D-1 实证)。
+
+    这一段只能证明**静态可判**的那几种不可用; 竞态与 IO 错误（ENOSPC/EACCES/被别的
+    进程换掉）仍然只会在动盘段才显形 —— 如实声明, 不假装 replace 之前能证明一切。
+    """
+    if stale_dir is None:
+        raise JournalError(f"✗ {what}上有别的文件且无处留痕, 拒绝覆盖")
+    p = Path(stale_dir)
+    if is_symlink(p):
+        raise JournalError(f"✗ 留痕目录是一条 symlink, 拒绝跟随: {p}")
+    if os.path.lexists(str(p)) and not p.is_dir():
+        raise JournalError(f"✗ 留痕目录被占成了别的东西, 无处留痕: {p}")
+    try:
+        _SP.assert_symlink_free(p.parent)
+    except SystemExit as e:
+        # 统一成 JournalError: 调用方接的是 (OSError, JournalError), 让守卫的失败
+        # 走同一个出口, 免得「拒绝」从一种异常类型漏成另一种。
+        raise JournalError(f"✗ 留痕目录的祖先链上有 symlink, 无处安全留痕: {p}") from e
+
+
+def atomic_write_bytes(path: Path, data: bytes, stale_dir: Path | None = None, mode: int | None = None) -> None:
+    """同目录唯一名 tmp + os.replace (quiz-answer SKILL.md:156-158 口径)。
+
+    ⛔ 原文件在 os.replace 成功之前一个字节都不动 —— 不用 write_text: 它会先按
+    只写模式截断文件, 编码失败时留下一个已经被清空的原件。
+    `mode` 给定时在就位前把权限写到 tmp 上（os.replace 换的是 inode, 不带过去
+    原文件的权限位）。
+    """
+    tmp = _tmp_path_for(path)
+    fd = _open_new_exclusive(tmp)
+    try:
+        _write_fd(fd, data)
+        if mode is not None:
+            os.chmod(str(tmp), stat_mod.S_IMODE(mode))
+    except BaseException:
+        _park_stale(tmp, stale_dir)
+        raise
+    _replace_or_park(tmp, path, stale_dir)
+
+
+def copy_file_atomically(src: Path, dst: Path, stale_dir: Path | None = None) -> None:
+    """把 src 逐字节复制到 dst —— 经唯一名 tmp 再 os.replace 就位。
+
+    ⛔ 不直接 `copyfile(src, dst)`: 那会**截断** dst 那个 inode, 于是
+      · dst 若是用户自己放的同名文件 —— 内容没了;
+      · dst 若与别处硬链接同一个 inode —— 连那一处一起改写。
+    换成「先写新 inode, 再换目录项」, 旧 inode 的其它硬链接原样不动。
+    """
+    tmp = _tmp_path_for(dst)
+    fd = _open_new_exclusive(tmp)
+    try:
+        with os.fdopen(fd, "wb") as out, open(str(src), "rb") as fin:
+            shutil.copyfileobj(fin, out)
+            out.flush()
+            os.fsync(out.fileno())
+    except BaseException:
+        _park_stale(tmp, stale_dir)
+        raise
+    _replace_or_park(tmp, dst, stale_dir)
+
+
+def free_path(path: Path) -> Path:
+    """返回一个尚未被占用的同族路径 (…-2 / …-3 …)。
+
+    ⛔ 撤销时绝不覆盖已存在的条目 —— 覆盖 = 悄悄把某份东西换掉。
+    """
+    if not os.path.lexists(str(path)):
+        return path
+    stem, suffix = path.stem, path.suffix
+    for n in range(2, 10_000):
+        cand = path.with_name(f"{stem}-{n}{suffix}")
+        if not os.path.lexists(str(cand)):
+            return cand
+    raise JournalError(f"✗ 回收目录同名条目过多, 无法安放: {path}")
+
+
+# ─────────────────────────── provenance ───────────────────────────
+
+
+def detect_newline(raw: bytes) -> bytes:
+    """按**字节**探测换行风格。⛔ 绝不用文本读 —— read_text 的 newline=None 会把
+    CRLF 归一成 LF, 于是「保持原样」写回去的是一份被改过行尾的文件。"""
+    i = raw.find(b"\n")
+    if i > 0 and raw[i - 1 : i] == b"\r":
+        return b"\r\n"
+    return b"\n"
+
+
+def frontmatter_span(raw: bytes, nl: bytes) -> tuple[int, int] | None:
+    """返回 (正文起点, 收尾 '---' 行的起点); 没有**完整**的 frontmatter 返回 None。"""
+    opener = b"---" + nl
+    if not raw.startswith(opener):
+        return None
+    start = len(opener)
+    pos = start
+    while pos <= len(raw):
+        eol = raw.find(nl, pos)
+        line = raw[pos:eol] if eol != -1 else raw[pos:]
+        if line == b"---":
+            return start, pos
+        if eol == -1:
+            return None
+        pos = eol + len(nl)
+    return None
+
+
+def _is_provenance_key_line(line: bytes) -> bool:
+    """键行的三种写法都要认 —— 只认裸键会在引号形式下留下重复键。"""
+    key = PROVENANCE_KEY.encode("utf-8")
+    return line.startswith(key + b":") or line.startswith(b'"' + key + b'":') or line.startswith(b"'" + key + b"':")
+
+
+def _is_block_neutral(line: bytes) -> bool:
+    """空行与顶格注释都**不足以**宣布块结束 —— 得看它们后面还缩不缩进。"""
+    s = line.strip()
+    return s == b"" or s.startswith(b"#")
+
+
+def strip_provenance_block(body: bytes, nl: bytes) -> bytes:
+    """摘掉既有的溯源块 (键行 + 其下所有缩进子行) —— 重写即幂等的前提。
+
+    ⛔ 块里夹一个空行或一行顶格注释都不算块结束: 它们只有在**下一个有内容的行不再
+    缩进**时才算出块。只看「连续缩进」会在这些地方提前收手, 把剩下的子行留在原地,
+    于是它们被下一个 mapping 收编 —— 那是静默改掉别人的 metadata。
+    """
+    lines = body.split(nl)
+    out: list[bytes] = []
+    inside = False
+    i = 0
+    while i < len(lines):
+        line = lines[i]
+        if _is_provenance_key_line(line):
+            inside = True
+            i += 1
+            continue
+        if inside:
+            if line.startswith(b" ") or line.startswith(b"\t"):
+                i += 1
+                continue
+            if _is_block_neutral(line):
+                j = i + 1
+                while j < len(lines) and _is_block_neutral(lines[j]):
+                    j += 1
+                if j < len(lines) and (lines[j].startswith(b" ") or lines[j].startswith(b"\t")):
+                    i += 1
+                    continue
+            inside = False
+        out.append(line)
+        i += 1
+    return nl.join(out)
+
+
+def _yaml_scalar(value) -> bytes:
+    """JSON 标量是 YAML 1.2 的合法子集 —— 路径里的冒号/引号/中文一律交给它转义,
+    不手写 YAML 转义规则。"""
+    s = json.dumps("" if value is None else str(value), ensure_ascii=False)
+    for ch, esc in _LINE_LIKE.items():
+        s = s.replace(ch, esc)
+    return s.encode("utf-8")
+
+
+PROVENANCE_FIELDS = ("source_rel_path", "source_mtime_utc", "batch_id", "applied_at_utc", "op")
+
+
+def provenance_block(meta: dict, nl: bytes) -> bytes:
+    lines = [PROVENANCE_KEY.encode("utf-8") + b":"]
+    for key in PROVENANCE_FIELDS:
+        lines.append(b"  " + key.encode("utf-8") + b": " + _yaml_scalar(meta.get(key)))
+    return nl.join(lines) + nl
+
+
+def render_provenance(raw: bytes, meta: dict) -> bytes:
+    """把溯源块合进 frontmatter, 返回**新的全文字节**。原有键一律保留。
+
+    纯函数 —— 同一份输入 + 同一份 meta 恒得同一串字节。落点归属判定靠的就是这一点:
+    「我这一步写出来应该长什么样」算得出来, 于是可以逐字节比, 不必猜。
+    """
+    nl = detect_newline(raw)
+    block = provenance_block(meta, nl)
+    span = frontmatter_span(raw, nl)
+    if span is None:
+        return b"---" + nl + block + b"---" + nl + nl + raw
+    start, end = span
+    body = strip_provenance_block(raw[start:end], nl)
+    if body and not body.endswith(nl):
+        body += nl
+    return raw[:start] + body + block + raw[end:]
+
+
+def provenance_outcome(raw: bytes, suffix: str) -> str:
+    """不落盘地判一份内容会走到哪个分支 —— 与 write_provenance 同一套条件。"""
+    if suffix.lower() != ".md":
+        return PROVENANCE_NOT_MARKDOWN  # 调用方须在**读文件之前**先判这一条
+    try:
+        raw.decode("utf-8")
+    except UnicodeDecodeError:
+        return PROVENANCE_NOT_UTF8
+    nl = detect_newline(raw)
+    if raw.startswith(b"---" + nl) and frontmatter_span(raw, nl) is None:
+        return PROVENANCE_UNTERMINATED
+    return PROVENANCE_WRITTEN
+
+
+def expected_after_provenance(raw: bytes, suffix: str, meta: dict) -> bytes:
+    """这一份内容写完溯源之后应该是什么字节。跳过的三种情形返回原样。"""
+    if provenance_outcome(raw, suffix) != PROVENANCE_WRITTEN:
+        return raw
+    return render_provenance(raw, meta)
+
+
+def write_provenance(path: Path, meta: dict, stale_dir: Path | None = None) -> str:
+    """给本批次产出的 .md 写溯源 frontmatter, 并回写原 mtime 与权限位。
+
+    看不懂结构的文件**一个字节都不动**:
+      · 非 UTF-8 —— 按某个编码猜着写回去等于悄悄损坏用户的材料;
+      · `---` 开了头却没有收尾 `---` —— 在它上面再插一份 frontmatter 会把原来那段
+        挤进正文（渲染成一条分隔线 + 一段裸文本）。看不懂就别动, 在账上说清楚。
+    """
+    p = Path(path)
+    # ⛔ 后缀先判、再读文件: 否则 PDF / 视频这类本可以直接略过的大文件也会被整份
+    # 读进内存（重构时把 read_bytes 提前一行造成的回归, Codex round-3 M12）。
+    if p.suffix.lower() != ".md":
+        return PROVENANCE_NOT_MARKDOWN
+    raw = p.read_bytes()
+    outcome = provenance_outcome(raw, p.suffix)
+    if outcome != PROVENANCE_WRITTEN:
+        return outcome
+    new_raw = render_provenance(raw, meta)
+    if new_raw == raw:
+        return PROVENANCE_WRITTEN  # 已是目标形态 —— 重跑幂等
+    st = p.stat()
+    atomic_write_bytes(p, new_raw, stale_dir, mode=st.st_mode)
+    os.utime(str(p), ns=(st.st_mtime_ns, st.st_mtime_ns))
+    return PROVENANCE_WRITTEN
+
+
+def write_pair_atomically(
+    items: list[tuple[Path, bytes]], stale_dir: Path | None = None, owned_shas: dict | None = None
+) -> None:
+    """成对发布: 两份都写好各自的 tmp, 再双双就位。
+
+    与 split_preview.write_pair_atomically_checked 的差别（有意为之）: 不预建 0 字节
+    目标, 因而失败时**没有**「按路径 unlink 回滚」这一步 —— 那一步在并发下会删到
+    别人刚放上去的同名目录项。代价如实写明: 两次 `os.replace` 之间若进程被杀,
+    仍可能只就位一份。恢复依据是 journal, 回执本来就可以重新生成。
+    """
+    owned_shas = owned_shas or {}
+
+    # ── 第一段: **只读**校验。⛔ 这一段一个字节都不许动盘 —— 上一版把会动盘的
+    # 「停放」放进了校验段, 于是第一份被挪进 stale/ 之后第二份才拒绝, 官方路径两头
+    # 都不在、还一个字都不说（独立复核 M-1 实证）。
+    needs_park: dict = {}
+    for path, _ in items:
+        path = Path(path)
+        assert_path_safe(path, what="回执落点")
+        foreign = (
+            os.path.lexists(str(path))
+            and not is_symlink(path)
+            and path.is_file()
+            and sha256_file(path) != owned_shas.get(str(path))
+        )
+        needs_park[str(path)] = foreign
+    if any(needs_park.values()):
+        # ⛔ 「有地方留痕」是**动盘的前提**, 不是动盘途中才发现的事。
+        assert_stale_dir_usable(stale_dir, what="回执落点")
+
+    tmps: list[tuple[Path, Path]] = []
+    try:
+        for path, data in items:
+            tmp = _tmp_path_for(path)
+            fd = _open_new_exclusive(tmp)
+            try:
+                _write_fd(fd, data)
+            except BaseException:
+                _park_stale(tmp, stale_dir)
+                raise
+            tmps.append((tmp, path))
+    except BaseException:
+        for tmp, _ in tmps:
+            _park_stale(tmp, stale_dir)
+        raise
+    # ── 第二段: 先把**所有**外来文件留痕, 再做**任何一次** replace。
+    # ⛔ 顺序本身就是性质的一部分: 边留痕边 replace 的话, 第 k 份留不住时前 k-1 份
+    # 已经发布出去了 —— 一对回执互相矛盾, 而这条输入在两段式之前是零写的
+    # (独立复核 round-2 D-1)。作用域仍然**只到回执落点**, 不碰业务文件 (round-5 HIGH-2)。
+    for path, _ in items:
+        if not needs_park.get(str(Path(path))):
+            continue
+        # ⛔ 留存失败就**不许覆盖**: 明知留不住还是盖了 = 无声弄丢。
+        if not preserve_foreign_file(Path(path), stale_dir, None):
+            err = JournalError(f"✗ 回执落点上有别的文件且无法留痕, 拒绝覆盖: {path}")
+            residues = [_park_stale(t, stale_dir) or t for t, _ in tmps]
+            err.add_note("残片位置: " + " / ".join(str(r) for r in residues if r))
+            raise err
+
+    # ── 第三段: 全部就位。
+    for idx, (tmp, path) in enumerate(tmps):
+        try:
+            _replace_or_park(tmp, path, stale_dir)
+        except BaseException as e:
+            # ⛔ 还没就位的那几份也要停放 —— 否则第一份失败就会把后面的 tmp 留在
+            # 正式目录里。残片位置挂到异常上, 让调用方说得出「去看哪一份」。
+            # ⛔ 当前这一份报的是**停放之后**的位置 (`_uj_residue`), 不是 tmp 的旧
+            # 路径 —— 后者在 `_replace_or_park` 里已经被挪走, 照着找是空的 (D-3)。
+            residues = [Path(getattr(e, "_uj_residue", None) or tmp)]
+            for rest_tmp, _ in tmps[idx + 1 :]:
+                residues.append(_park_stale(rest_tmp, stale_dir) or rest_tmp)
+            e.add_note("残片位置: " + " / ".join(str(r) for r in residues if r))
+            raise
+
+
+# ─────────────────────────── 账目读法 ───────────────────────────
+
+
+def latest_by_seq(rows: list[dict]) -> dict:
+    """每个 seq 取**最后一条**有业务含义的记录。
+
+    ⛔ 不能按「出现过没有」判。`planned → undone → done`（撤销之后又重新执行过）
+    是合法历史; 把「出现过 undone」当成永久终态, 会让重新执行出来的那一份永远
+    撤不掉, 而且撤销会安静地返回「零件」。
+    """
+    out: dict = {}
+    for r in rows:
+        if r.get("state") in BUSINESS_STATES and "seq" in r:
+            out[r["seq"]] = r
+    return out
+
+
+# ─────────────────────────── 批次账本 ───────────────────────────
+
+
+class BatchJournal:
+    """一个批次的账本。目录布局:
+
+    <work_dir>/<batch_id>/journal.jsonl     一行一条记录
+    <work_dir>/<batch_id>/backup/<rel>      op 之前的逐字节快照
+    <work_dir>/<batch_id>/recycle/<rel>     「删」的留痕落点
+    <work_dir>/<batch_id>/recycle/undone/   撤销 copy/link 时产物的去处
+    <work_dir>/<batch_id>/stale/            写失败的 tmp 残片
+    """
+
+    def __init__(self, work_dir, batch_id: str, root=None, fingerprint: str | None = None):
+        self.work_dir = Path(work_dir)
+        self.batch_id = batch_id
+        #: 创建目录的**上界**。缺省 = work_dir 的父目录必须已存在 (不造祖先链);
+        #: 给了 root 则允许在 root 之内逐级创建 —— 调用方对 root 负责。没有这个
+        #: 上界, 一个打错的 --work-dir 就会在 home 底下造出一串目录来。
+        self.root = Path(root) if root is not None else None
+        #: 这本账属于哪个 vault。撤销时拿当前 vault 的指纹核对。
+        self.fingerprint = fingerprint
+        self.batch_dir = self.work_dir / batch_id
+        self.journal_path = self.batch_dir / JOURNAL_NAME
+        self.backup_root = self.batch_dir / BACKUP_DIR
+        self.recycle_root = self.batch_dir / RECYCLE_DIR
+        self.undone_root = self.recycle_root / UNDONE_DIR
+        self.stale_root = self.batch_dir / STALE_DIR
+        self._tail_malformed = False
+        self._tail_unterminated = False
+        self._tail_bad_count = 0
+
+    # ── 目录 ──────────────────────────────────────────────
+
+    def mkdir_chain(self, target: Path) -> None:
+        """从上界起**逐级**创建, 每级先验祖先无 symlink 再建。
+
+        ⛔ 先验再建的次序不能倒 (split_preview.prepare_out_dir v3 的同一条教训):
+        先 mkdir 会穿过 symlink 在物理目标处把目录创建出来, 形成「拒绝但已写」。
+        """
+        target = Path(target)
+        if self.root is None:
+            parent = target.parent
+            if not parent.is_dir():
+                raise JournalError(f"✗ 目标目录的父目录不存在, 拒绝创建祖先链: {parent}")
+            chain = [target]
+        else:
+            if not self.root.is_dir() or self.root.is_symlink():
+                raise JournalError(f"✗ 创建上界不是普通目录: {self.root}")
+            try:
+                rel = target.resolve().relative_to(self.root.resolve())
+            except ValueError as e:
+                raise JournalError(f"✗ 目标落在允许创建的上界之外, 拒绝: {target}") from e
+            chain, cur = [], self.root
+            for part in rel.parts:
+                cur = cur / part
+                chain.append(cur)
+        for d in chain:
+            if os.path.lexists(str(d)):
+                if d.is_symlink() or not d.is_dir():
+                    raise JournalError(f"✗ 工作目录路径上的 {d} 不是普通目录, 拒绝写入")
+            else:
+                _SP.assert_symlink_free(d.parent)
+                os.makedirs(str(d), exist_ok=True)
+            _SP.assert_symlink_free(d)
+
+    def ensure_dirs(self) -> None:
+        """⛔ 只有准入守卫全部跑完才准调用 —— 拒绝路径必须连 work-dir 都不建。"""
+        self.mkdir_chain(self.batch_dir)
+        self.mkdir_chain(self.backup_root)
+        self.mkdir_chain(self.recycle_root)
+
+    # ── 读账 ──────────────────────────────────────────────
+
+    def read_rows(self) -> list[dict]:
+        """解析 journal。尾部的坏行 (掉电截断) 容忍并封口; 中间损坏一律拒绝。
+
+        ⛔ 只按 "\\n" 切: splitlines() 会在 U+2028/U+2029/U+0085 处多切一刀, 把一条
+        合法记录切成两条非法 JSON —— 那条记录就永远重放不掉了。
+        """
+        self._tail_malformed = False
+        self._tail_unterminated = False
+        self._tail_bad_count = 0
+        if not self.journal_path.is_file():
+            return []
+        raw = self.journal_path.read_bytes().decode("utf-8", errors="replace")
+        # ⛔ 「最后一条 JSON 完整、只差结尾换行」也要封口: 直接 O_APPEND 会让下一条
+        # 记录接在它屁股后面, 两条一起变成读不懂的一行。
+        self._tail_unterminated = bool(raw) and not raw.endswith("\n")
+        parsed: list[dict | None] = []
+        for line in raw.split("\n"):
+            if not line.strip():
+                continue
+            try:
+                obj = json.loads(line)
+            except ValueError:
+                parsed.append(None)
+                continue
+            # ⛔ 认不出来的 state 算损坏, 不能静默忽略: 把 acting 写错一个字母,
+            # 「最新状态」就悄悄退回 planned, 撤销会报「未执行, 无需还原」而产物还在
+            # (Codex round-4 M1)。
+            # ⛔ 而且它**不能**和「半行」共用同一个表示: 共用的话它就顺带继承了半行
+            # 的尾部容忍 —— 一条完整但状态拼错的记录落在账尾就又被忽略了
+            # (Codex round-5 HIGH-3)。两件性质不同的事, 表示也要分开。
+            if not isinstance(obj, dict) or obj.get("state") not in KNOWN_STATES:
+                got = obj.get("state") if isinstance(obj, dict) else "<不是对象>"
+                raise JournalError(
+                    f"✗ journal 第 {len(parsed) + 1} 条记录认不出来 (state={got!r}), "
+                    f"这不是掉电截断, 拒绝在看不懂的账上继续动盘: {self.journal_path}"
+                )
+            parsed.append(obj)
+
+        # 坏行什么时候算「没写完的尾巴」而不是「中间损坏」:
+        #   · 它落在**最后一段**全是坏行的尾巴里 —— 掉电截断, 容忍;
+        #   · 它被某条封口哨兵**明确覆盖** —— 当初封的就是它, 永远容忍。
+        # ⛔ 覆盖面必须是哨兵当初记下的**条数**, 不能是「往前跨过任意多条坏行」:
+        # 否则一条本来完整的业务行后来损坏了, 只要它紧挨着那段旧的封口区, 就会被
+        # 一起放过 —— 最新状态悄悄退回上一步, 撤销报「未执行」而产物还在
+        # (Codex round-4 H3)。
+        covered: set[int] = set()
+        for idx, obj in enumerate(parsed):
+            if not (isinstance(obj, dict) and obj.get("state") == STATE_TAIL_SEALED):
+                continue
+            n = obj.get("sealed_bad_count")
+            # ⛔ 没有计数的哨兵**只覆盖它紧邻的那一条**坏行。曾经为「旧账本兼容」放宽成
+            # 「往前跨过整段连续坏行」—— 那正是 round-4 H3 判为缺陷的语义, 等于把一条已判
+            # HIGH 的安全性质换掉, 换来的兼容面还是空集（本工具尚未发布, 无旧账本）。
+            # 独立复核 M-2 实证: 放宽后「后来才损坏的完整 acting 行」会被静默吞掉,
+            # 撤销报「未执行」而产物还在, 之后整批彻底卡死。
+            n = int(n) if isinstance(n, int) and n > 0 else 1
+            j = idx - 1
+            while n > 0 and j >= 0 and parsed[j] is None:
+                covered.add(j)
+                n -= 1
+                j -= 1
+        trailing_from = len(parsed)
+        while trailing_from > 0 and parsed[trailing_from - 1] is None:
+            trailing_from -= 1
+        for idx, obj in enumerate(parsed):
+            if obj is not None:
+                continue
+            if idx in covered or idx >= trailing_from:
+                continue
+            raise JournalError(
+                f"✗ journal 中间存在损坏记录 (第 {idx + 1} 条可解析行), 这不是掉电截断, "
+                f"拒绝在看不懂的账上继续动盘: {self.journal_path}"
+            )
+        self._tail_bad_count = len(parsed) - trailing_from
+        self._tail_malformed = self._tail_bad_count > 0
+        return [o for o in parsed if o is not None]
+
+    def seal_tail_if_needed(self) -> bool:
+        """给上一次没写完的尾巴封口, 然后才允许继续追加。
+
+        两种没写完:
+          · 尾行**解析不了**（写到一半掉电）—— 补换行终结它, 再落一条哨兵行;
+          · 尾行**解析得了但缺结尾换行** —— 只补一个换行即可。
+        不封口而直接 O_APPEND, 新记录会接在旧尾巴后面连成一条烂行。
+        """
+        if not (self._tail_malformed or self._tail_unterminated):
+            return False
+        payload = b"\n"
+        if self._tail_malformed:
+            payload += json_line(
+                {
+                    "schema_version": SCHEMA_VERSION,
+                    "state": STATE_TAIL_SEALED,
+                    #: 这条哨兵**明确覆盖**它前面这么多条坏行 —— 覆盖面写死, 免得
+                    #: 后来新坏的行蹭着旧封口区被一起放过。
+                    "sealed_bad_count": int(getattr(self, "_tail_bad_count", 1) or 1),
+                    "note": "上一条记录写到一半 (掉电/中断), 已封口忽略",
+                    "sealed_at_utc": utc_now_iso(),
+                }
+            )
+        append_bytes(self.journal_path, payload)
+        self._tail_malformed = False
+        self._tail_unterminated = False
+        self._tail_bad_count = 0
+        return True
+
+    def load(self) -> list[dict]:
+        """读账 + 封口 —— 任何要往账上追加的流程都必须先走这一步。"""
+        rows = self.read_rows()
+        if self.seal_tail_if_needed():
+            rows = self.read_rows()
+        return rows
+
+    # ── 写账 ──────────────────────────────────────────────
+
+    def _append(self, row: dict) -> dict:
+        row = dict(row)
+        row.setdefault("schema_version", SCHEMA_VERSION)
+        row.setdefault("batch_id", self.batch_id)
+        if self.fingerprint is not None:
+            row.setdefault("vault_fingerprint", self.fingerprint)
+        row.setdefault("ts_utc", utc_now_iso())
+        append_bytes(self.journal_path, json_line(row))
+        return row
+
+    def plan(
+        self,
+        *,
+        seq: int,
+        op: str,
+        stable_id: str,
+        src: str,
+        dst: str,
+        dst_base: str,
+        sha256_before: str,
+        mtime_ns_before: int,
+        mode_before: int | None,
+        backup: str | None,
+        prov_meta: dict | None = None,
+        dir_mtimes: dict | None = None,
+        created_dirs: list | None = None,
+        meta: dict | None = None,
+    ) -> dict:
+        if op not in OPS:
+            raise JournalError(f"✗ 未知动作: {op!r}")
+        return self._append(
+            {
+                "seq": seq,
+                "state": STATE_PLANNED,
+                "op": op,
+                "stable_id": stable_id,
+                "src": src,
+                "dst": dst,
+                "dst_base": dst_base,
+                "sha256_before": sha256_before,
+                "mtime_ns_before": mtime_ns_before,
+                "mode_before": mode_before,
+                "backup": backup,
+                #: 本条会写进产物的那份溯源 meta。记下来是为了让「我这一步写出来
+                #: 应该长什么样」可以**重算**（落点归属判定要用）。
+                "prov_meta": dict(prov_meta) if prov_meta else None,
+                # 本条会改动条目集合的那几个目录 —— 撤销时一并还原它们的 mtime。
+                "dir_mtimes": dict(dir_mtimes or {}),
+                # 本条**新建**出来的目录。撤销不会删掉它们 (默认路径 0 物理删除),
+                # 但必须在回执里说出来, 而不是让「全树回到原样」这句话悄悄失真。
+                "created_dirs": list(created_dirs or []),
+                "meta": meta or {},
+            }
+        )
+
+    def commit(
+        self,
+        entry: dict,
+        *,
+        sha256_after: str | None,
+        mtime_ns_after: int | None,
+        provenance: str | None = None,
+        inode: int | None = None,
+        dir_mtimes_at_act: dict | None = None,
+        dir_mtimes_after: dict | None = None,
+    ) -> dict:
+        row = dict(entry)
+        row["state"] = STATE_DONE
+        row["sha256_after"] = sha256_after
+        row["mtime_ns_after"] = mtime_ns_after
+        row["provenance"] = provenance
+        row["inode"] = inode
+        #: op **之后**各目录的 mtime。撤销时要拿它和上一条的「之前」串成一条链,
+        #: 链没断且现值等于最后一环, 才敢把时间改回批前值。
+        #: **动手那一刻**各目录的 mtime。plan 行里的「之前」可能是上一次跑留下的
+        #: 陈旧读数（续跑场景）, 两者不等即说明这一步开工前目录已被人动过 ——
+        #: 那段时间不在任何一步的账里, 目录时间就不能改回批前值。
+        row["dir_mtimes_at_act"] = dict(dir_mtimes_at_act or {})
+        row["dir_mtimes_after"] = dict(dir_mtimes_after or {})
+        row.pop("ts_utc", None)
+        return self._append(row)
+
+    # ── 备份 ──────────────────────────────────────────────
+
+    def backup(self, src_abs: Path, src_rel: str) -> tuple[str, str, int, int]:
+        """op 之前的逐字节快照 —— undo 的真相源。
+        返回 (备份相对路径, sha, mtime_ns, mode)。"""
+        src_abs = Path(src_abs)
+        st = os.lstat(str(src_abs))
+        dst = self.backup_root / src_rel
+        if self.root is not None:
+            self.mkdir_chain(dst.parent)
+        else:
+            os.makedirs(str(dst.parent), exist_ok=True)
+        _SP.assert_symlink_free(dst.parent)
+        if is_symlink(dst):
+            raise JournalError(f"✗ 备份落点是一条 symlink, 拒绝跟随: {dst}")
+        before = sha256_file(src_abs)
+        # ⛔ 经 tmp 再 os.replace 只保住了「别处的硬链接」; 备份路径上若是一份**独立的
+        # 用户文件**, os.replace 照样把它的目录项换掉。所以先判归属: 与源逐字节相同
+        # 就是我们自己上一次写的备份(直接沿用), 否则挪进 stale/ 留痕再写。
+        if os.path.lexists(str(dst)):
+            # ⛔ 沿用既有备份还要求 nlink == 1: 内容一样但与别处共享 inode 的话,
+            # ① 我们的 utime 会改到用户那份文件的时间, ② 用户以后编辑那份文件会
+            # 连唯一的备份一起改掉 —— 备份就不再是独立快照 (Codex round-4 H2)。
+            if dst.is_file() and os.lstat(str(dst)).st_nlink == 1 and sha256_file(dst) == before:
+                os.utime(str(dst), ns=(st.st_mtime_ns, st.st_mtime_ns))
+                return f"{BACKUP_DIR}/{src_rel}", before, st.st_mtime_ns, st.st_mode
+            os.makedirs(str(self.stale_root), exist_ok=True)
+            _SP.assert_symlink_free(self.stale_root)
+            os.replace(str(dst), str(free_path(self.stale_root / dst.name)))
+        copy_file_atomically(src_abs, dst, self.stale_root)
+        os.utime(str(dst), ns=(st.st_mtime_ns, st.st_mtime_ns))
+        if sha256_file(dst) != before:
+            raise JournalError(f"✗ 备份与原件不一致, 拒绝继续 (备份不可信就等于没有退路): {src_rel}")
+        return f"{BACKUP_DIR}/{src_rel}", before, st.st_mtime_ns, st.st_mode
+
+    # ── 归属判定 ──────────────────────────────────────────
+
+    def dst_abs(self, row: dict, vault: Path) -> Path:
+        base = self.batch_dir if row.get("dst_base") == BASE_BATCH else Path(vault)
+        return safe_join(base, row["dst"], what="落点")
+
+    def backup_abs(self, row: dict):
+        return safe_join(self.batch_dir, row["backup"], what="备份路径") if row.get("backup") else None
+
+    def owned_product(self, dst, row: dict) -> bool:
+        """落点上的这份东西是不是本批次造的 —— 只用可计算的等式, 不用启发式。
+
+        · `done` 行：比 `sha256_after`（那就是我们写完之后的实测值）。
+        · `acting` 行：还没记 after, 但期望值算得出来 ——
+            ① 与备份逐字节相同（主动作做了、溯源还没写）, 或
+            ② 等于「把备份按账上那份 prov_meta 渲染一遍」的结果（溯源也写完了）。
+        · `planned` 行：**一律不认领**。那时候主动作还没开始, 落点上按定义不该有我们
+          的东西; 认了就等于把用户恰好同字节的独立文件当成自家产物 (Codex round-3 H2)。
+        ⛔ 绝不用「全文里出现了 batch_id」这类判据: 用户在保留印记的前提下改了正文,
+        它照样为真, 而那份改动会被我们覆盖掉。
+        """
+        dst = Path(dst)
+        state = row.get("state")
+        if state == STATE_DONE:
+            if is_symlink(dst) or not Path(dst).is_file():
+                return False
+            return bool(row.get("sha256_after")) and sha256_file(dst) == row["sha256_after"]
+        if state != STATE_ACTING:
+            return False
+        return self.looks_like_our_product(dst, row)
+
+    def looks_like_our_product(self, path, row: dict) -> bool:
+        """这份内容是不是「本批这一步写出来的样子」—— 两条可计算的等式。"""
+        path = Path(path)
+        if is_symlink(path) or not path.is_file():
+            return False
+        if row.get("sha256_after") and sha256_file(path) == row["sha256_after"]:
+            return True
+        if not row.get("sha256_before"):
+            return False
+        if sha256_file(path) == row["sha256_before"]:
+            return True
+        bak = self.backup_abs(row)
+        meta = row.get("prov_meta")
+        if not (meta and bak and bak.is_file() and not is_symlink(bak)):
+            return False
+        if sha256_file(bak) != row["sha256_before"]:
+            return False  # 备份本身已不可信, 不拿它推期望值
+        return path.read_bytes() == expected_after_provenance(bak.read_bytes(), path.suffix, meta)
+
+    def recorded_receipt_shas(self, rows: list[dict], stem: str) -> dict:
+        """账上记的「上一次这个 stem 的两份回执各是什么内容」。"""
+        out: dict = {}
+        for r in rows:
+            if r.get("state") == STATE_RECEIPT_SHA and r.get("stem") == stem:
+                out = dict(r.get("shas") or {})
+        return out
+
+    def record_receipt_shas(self, stem: str, shas: dict) -> None:
+        """写完回执把它们的 sha 落账 —— 下一次据此认自家产物（尽力而为, 失败不致命）。
+
+        ⛔ 必须**先封口再追加**。这是全模块唯一一个可能在 `load()` 自己抛过之后仍被
+        调用到的 `_append` 点: 撤销失败时 `undo()` 里的 `load()` 抛在封口**之前**,
+        异常被调用方接住后照样会来写回执。不封口直接 O_APPEND, 「完整但缺结尾换行」
+        的末行会被新记录接在屁股后面粘成一条烂行 —— 工具在刚宣布「拒绝在看不懂的账
+        上继续动盘」的那条路径上, 反手把这本账写坏了 (独立复核 round-2 D-2 实证)。
+
+        ⛔ `read_rows()` 抛 ⇒ 这本账根本读不回来 ⇒ **一个字节都不写**。落不了账的
+        代价只是下一次重跑把自家上一版回执多留一次痕 (保守侧), 远轻于弄坏账本。
+        """
+        try:
+            self.read_rows()  # 设 _tail_*; 中间损坏会抛 ⇒ 下面两步都不做
+            self.seal_tail_if_needed()
+            self._append({"state": STATE_RECEIPT_SHA, "stem": stem, "shas": dict(shas)})
+        except (OSError, JournalError):
+            pass
+
+    def mark_acting(self, entry: dict) -> dict:
+        """在主动作**之前**落一条 acting 行 —— 「排期了」与「动过盘了」的分界。"""
+        row = dict(entry)
+        row["state"] = STATE_ACTING
+        row.pop("ts_utc", None)
+        return self._append(row)
+
+    # ── 撤销 ──────────────────────────────────────────────
+
+    def assert_is_ours(self, fingerprint: str | None = None) -> list[dict]:
+        """纯读判定「这本账是不是我们自己这一批的」。**不写一个字节。**
+
+        ⛔ 这是**往账本所在目录写任何东西的准入**: 调用方在这一步通过之前, 不得写
+        回执、不得建 `stale/`、不得追加账目。
+
+        原先撤销侧的零写契约挂在 `JournalNotOursError` 这个**异常类型**上 —— 那是
+        钩子, 不是不变量。`read_rows()` 对「读得出行、但读不懂」的账抛的是普通
+        `JournalError`, 于是它落进**会写回执**的那个 except: 往一个陌生目录写下
+        undo-receipt.json/.md, 并把那里同名的用户文件无声挪进新建的 `stale/`
+        (最终 HEAD 独立复核 H-B, boundary / no-delete / undo-order 三个维度各自撞到)。
+
+        保护性改动要写成不变量: **先证明这是我们的批次目录, 才获得写它的资格**,
+        而不是「捕获到某几个异常类时才不写」—— 后者只覆盖当时想到的那几条路径。
+        """
+        rows = self.read_rows()
+        self._assert_is_a_batch_journal(rows)
+        self._assert_bound_to(rows, fingerprint)
+        return rows
+
+    def _assert_bound_to(self, rows: list[dict], fingerprint: str | None) -> None:
+        """这本账是不是这个 vault 的。
+
+        ⛔ 判据是「**每一条**业务记录都绑着当前 vault」, 不是「当前指纹出现在集合里」——
+        后者对「全部缺失」和「A/B 混合」两种账本都放行。
+        """
+        if fingerprint is None:
+            return
+        for r in rows:
+            if r.get("state") not in BUSINESS_STATES:
+                continue
+            got = r.get("vault_fingerprint")
+            if got != fingerprint:
+                raise JournalNotOursError(
+                    f"✗ 这本账不是当前 vault 的 (第 {r.get('seq')} 条记的是 {got!r}, "
+                    f"现算 {fingerprint!r}), 拒绝拿别处的记录来动这里的文件: {self.journal_path}"
+                )
+            # ⛔ 同一个 vault 里还有「另一批」这回事: 把 A 批的账原样放进 B 批目录,
+            # 只核 vault 的话 B 会拿 A 的落点去复核并报完成 (Codex round-4 H5)。
+            if r.get("batch_id") != self.batch_id:
+                raise JournalNotOursError(
+                    f"✗ 这本账不是本批次的 (第 {r.get('seq')} 条记的是 {r.get('batch_id')!r}, "
+                    f"本批 {self.batch_id!r}), 拒绝采信: {self.journal_path}"
+                )
+
+    def _assert_is_a_batch_journal(self, rows: list[dict]) -> None:
+        """这个文件在**结构上**是不是一本批次账。
+
+        ⛔ `_assert_bound_to` 的判据是「**每一条**业务记录都绑着当前 vault」——
+        对 `rows == []` 是**空真**。而 `read_rows()` 又把「整份文件一条都解析不出
+        JSON」归成「最后一段全是坏行的尾巴」(掉电截断), 于是**任意文本文件**都会被
+        当成一本空账一路通过, 最后打印「✓ 已撤销 0 件」并 rc=0
+        （全卡复核 HIGH-D 实测: 两行普通中文的 journal.jsonl 即可）。
+
+        后果不是「没做事」, 是「指错了文件」与「这一批确实已经撤完了」在输出上
+        **逐字相同** —— 用户据此认为已回滚, 而原批次的 move/recycle 仍然生效。
+        """
+        if not any(r.get("state") in BUSINESS_STATES for r in rows):
+            raise JournalNotOursError(
+                f"✗ 这个文件里没有任何一条批次记录, 它不是一本清仓账本, 拒绝采信: {self.journal_path}"
+            )
+
+    def _entries_to_undo(self, rows: list[dict]) -> list[dict]:
+        """要还原的条目 = 每个 seq 的**最新**状态是 planned / acting / done 的那些。
+
+        ⛔ `acting` 是后来为「排期了 / 动过盘了」的分界新引入的状态, 实现跟着改了、
+        这句说明当初没改（全卡复核 L12, DD-13 名实一致）。少了它, 读这段的人会以为
+        「已动盘未 done」那一件不在撤销面里 —— 而它恰恰是最需要被撤的那一类。
+        """
+        latest = latest_by_seq(rows)
+        out = [r for r in latest.values() if r.get("state") in (STATE_PLANNED, STATE_ACTING, STATE_DONE)]
+        return sorted(out, key=lambda r: r.get("seq", 0), reverse=True)
+
+    def undo(self, vault, fingerprint: str | None = None) -> dict:
+        """逆序还原。任一步对不上即停下, 不继续。"""
+        vault = Path(vault)
+        # ⛔ 绑定与结构校验必须发生在**任何一次写盘之前**。原先第一句就是
+        # `rows = self.load()`, 而 `load()` 内含 `seal_tail_if_needed()` —— 它会往这个
+        # 文件追加一条封口哨兵。于是「这本账不是这个 vault 的」这句拒绝, 是在**已经
+        # 改写过对方账本之后**才说出口的（全卡复核 BLOCKER-B 实测: 453 → 454 字节）。
+        # 先纯读判一遍, 通过了再走 load() 去封口。
+        self.assert_is_ours(fingerprint)
+        # ⛔ `load()` 之后**再判一遍**, 不是冗余: load() 会封口追加, 且两次读取之间
+        # 文件可能被换掉。把两次读合并成一次快照会删掉这条重查契约。
+        rows = self.load()
+        self._assert_is_a_batch_journal(rows)
+        self._assert_bound_to(rows, fingerprint)
+        targets = self._entries_to_undo(rows)
+
+        to_retime, skipped_dirs = self._dir_retime_plan(rows, vault)
+        # ⛔ 从**全部**行汇总, 不是只看最新行: undone 行不带 created_dirs, 第二次
+        # 撤销时「最新行」全成了 undone, 这条如实声明就被抹成空了 (round-3 L14)。
+        created_dirs: list[str] = []
+        for r in rows:
+            for d in r.get("created_dirs") or []:
+                if d not in created_dirs:
+                    created_dirs.append(d)
+
+        # ⛔ 逐件推进, 不用列表推导: 第 k 件抛出时, 前 k-1 件的盘面动作（产物挪进
+        # recycle/undone/、原路径收尾、UNDONE 行落账）都已经做完了。异常里必须把
+        # 「已经还原了几件」带出去, 否则回执会把 total/completed 写成 0, 用户据此
+        # 以为「什么都没撤」（全卡复核 M7 实测: 盘上已还原 2 件, 回执写 0）。
+        restored: list = []
+        try:
+            for row in targets:
+                restored.append(self._undo_one(row, vault))
+        except BaseException as e:
+            try:
+                e._uj_restored = list(restored)  # type: ignore[attr-defined]
+            except Exception:
+                pass
+            raise
+
+        retimed = []
+        vault_real_now = Path(os.path.realpath(vault))
+        for rel, ns in to_retime.items():
+            # ⛔ **物理包含**在这里必须重查, 不能复用 plan 阶段的结论: 两次读取之间夹着
+            # `_undo_one` 的整轮写盘, 祖先目录可能已被换成指向 vault 外的 symlink。
+            # 负控实测: 只中和 plan 那一道, 这一道会独自拦住 ⇒ 它是真承重的。
+            #
+            # 形状(safe_join)则不同: 键已在 `_clean` 里过过同一个函数、同一个字符串,
+            # 这里再调不会有第二种结果。所以它是**构造路径**, 不是设门 —— 不把它写成
+            # 「重查契约」(DD-13 名实一致; 负控点名它时不红, 已如实降级)。
+            d = safe_join(vault, rel, what="目录时间的目录")
+            real_d = Path(os.path.realpath(d))
+            if real_d != vault_real_now and vault_real_now not in real_d.parents:
+                skipped_dirs.append({"dir": rel, "why": "撤销过程中它被解析到了 vault 之外"})
+                continue
+            if d.is_dir() and not is_symlink(d):
+                # ⛔ 目录时间还原是**装饰性**的, 它失败不得否决整批撤销。此刻材料已经
+                # 还原完毕, 若让 OSError(权限/只读卷/ENOENT 竞态) 逃出去, 它会落进
+                # run_undo_mode 那个会写失败回执的 except —— 而 `_uj_restored` 只挂在
+                # `_undo_one` 那圈循环上, 这里抛出时它不存在 ⇒ partial 为空 ⇒ 回执把
+                # 「已还原 N 件」写成「已还原 0 件」, 且 done 行已全部变 undone,
+                # 再跑多少次都收敛不回来 (delta 复核 MEDIUM-4)。
+                # 与 HIGH-1 同一条原则: 装饰性字段的失败只登记, 不升级成整批失败。
+                try:
+                    os.utime(str(d), ns=(int(ns), int(ns)))
+                # ⛔ 不能只接 OSError: `_clean` 的 int() 对 10**30 是**成功**的, 到
+                # os.utime 才抛 **OverflowError**（"timestamp out of range for
+                # platform time_t", 本机实测）—— 它不是 OSError, 会原样逃出去,
+                # 于是这条修复在最容易触发的那个输入上根本不生效。
+                except (OSError, OverflowError, ValueError) as e:
+                    skipped_dirs.append({"dir": rel, "why": f"改不动它的时间, 材料本身已还原: {e}"})
+                else:
+                    retimed.append(rel)
+            else:
+                skipped_dirs.append({"dir": rel, "why": "撤销过程中它不再是普通目录"})
+
+        # ⛔ 「上一次已经撤掉的那几件」也要带回去。第二次跑同一条 `--undo` 是文档承诺的
+        # 幂等空操作, 但回执不能因此变成「共 0 件」—— 它写的是同一个 stem, 会把上一次
+        # 那份**记着产物停放位置**的回执原地换掉, 而 undone 行本身不记停放位置, 于是
+        # 「我的东西去哪了」从此无处可查（全卡复核 M5 实测）。执行侧对同一个坑做了回填
+        # (run_apply 从账上重建 results), 撤销侧原先没有。
+        already: list = []
+        for r in latest_by_seq(rows).values():
+            if r.get("state") == STATE_UNDONE:
+                already.append({"seq": r.get("seq"), "op": r.get("op"), "action": "上一次已撤销"})
+        return {
+            "ok": True,
+            "batch_id": self.batch_id,
+            "restored": restored,
+            "already_undone": sorted(already, key=lambda x: x.get("seq") or 0),
+            "dirs_retimed": sorted(retimed),
+            "dirs_not_retimed": skipped_dirs,
+            "dirs_left_behind": sorted(created_dirs),
+        }
+
+    def _dir_retime_plan(self, rows: list[dict], vault: Path):
+        """哪些目录的时间可以改回批前值。
+
+        ⛔ 「现值 == 最后一次操作后的值」只证明**最后一次操作之后**没人动过, 不证明
+        整个批次期间没人动过。所以要把每一步的「之前 / 之后」串成一条链: 后一步的
+        「之前」必须等于前一步的「之后」, 链不断、且现值等于最后一环, 才敢改。
+        """
+        # ⛔ 不能用 `latest_by_seq`: 撤销中途失败之后再跑一次时, 上一轮已还原那几件的
+        # **最新**行全是 undone, 它们碰过的目录于是既进不了 `to_retime`、也进不了
+        # `skipped` —— 回执的「目录时间」段对这些目录一个字都不说, 而它们的 mtime 确实
+        # 没被还原（全卡复核 M4 实测: `归档` 在两张表里都不出现）。紧挨着的 `undo()`
+        # 对 `created_dirs` 正是为了同一个原因改成「从**全部**行汇总」(round-3 L14)。
+        latest: dict = {}
+        for r in rows:
+            if r.get("state") in (STATE_PLANNED, STATE_ACTING, STATE_DONE) and "seq" in r:
+                latest[r["seq"]] = r
+        chain: dict[str, list] = {}
+        # ⛔ 必须在下面 chain 循环里的 `_clean` **调用之前**绑定: 它是这个函数的局部,
+        # 放到循环之后赋值会让 `_clean` 撞上 UnboundLocalError。
+        bad_dir_keys: dict[str, str] = {}
+        for seq in sorted(latest):
+            r = latest[seq]
+            pre = r.get("dir_mtimes") or {}
+            at_act = r.get("dir_mtimes_at_act") or {}
+            post = r.get("dir_mtimes_after") or {}
+
+            def _slot(rel: str, seq=seq):
+                """⛔ 按 seq 取环, 不能盲取 [-1]: 某一步的 post 里若出现了它自己
+                `pre` 中没有的目录（执行期间目录被改名重建）, 盲取会把那个读数写进
+                **上一步**的环里, 于是撤销拿新目录的时间回填旧目录的批前值。"""
+                bucket = chain.setdefault(rel, [])
+                for item in bucket:
+                    if item["seq"] == seq:
+                        return item
+                item = {"seq": seq, "pre": None, "at_act": None, "post": None}
+                bucket.append(item)
+                return item
+
+            # ⛔ 账本里的目录**键**与**值**都是不可信输入, 但它们只驱动收尾那句
+            # os.utime —— 一个装饰性字段。不过就**登记跳过**, 绝不抛。
+            #
+            # 上一版这里是 fail-closed 抛出, 照搬了 src/dst/backup 的口径。那是把
+            # 两件后果完全不同的事混成一条: src/dst/backup 驱动**用户材料的搬动**,
+            # 放行就等于把材料搬出 vault, 必须拒整批; 而目录时间放行最坏也只是
+            # 「某个目录的 mtime 没回去」。抛出换来的是: 整批撤销被否决、用户材料
+            # 卡在落点、CLI 没有任何跳过开关 ⇒ 这一批再也撤不回来, 而 stderr 还打
+            # 「修好原因后再跑一次只会补做剩下的」这句不实的恢复建议。
+            # 更糟的是抛出点落在**会写回执**那一支, 把上一次成功撤销留下的
+            # undo-receipt 原地换成「共 0 件」——那正是 M5 专门修好的不变量。
+            # （delta 复核 cf951eb4 判 HIGH-1 + MEDIUM ×3, 同一根因。）
+            #
+            # 安全性不依赖抛出: 跳过就**不会有任何 os.utime**, 越界写照样发生不了。
+            def _clean(dct: dict | None, what: str) -> dict:
+                out: dict[str, int] = {}
+                for rel, ns in (dct or {}).items():
+                    try:
+                        safe_join(vault, rel, what="目录时间的目录")
+                    except JournalError as e:
+                        bad_dir_keys.setdefault(str(rel), f"账上的目录键形状不可信, 不动它的时间: {e}")
+                        continue
+                    try:
+                        out[rel] = int(ns)
+                    except (TypeError, ValueError, OverflowError):
+                        # int() 对坏值抛的是 ValueError/TypeError, **两个 except 都不接**
+                        # ⇒ 裸 traceback（delta 复核 MEDIUM-5）。
+                        bad_dir_keys.setdefault(str(rel), f"账上这个目录的{what}不是一个时间数, 不动它的时间: {ns!r}")
+                return out
+
+            for rel, ns in _clean(pre, "操作前时间").items():
+                _slot(rel)["pre"] = ns
+            for rel, ns in _clean(at_act, "动手时时间").items():
+                _slot(rel)["at_act"] = ns
+            for rel, ns in _clean(post, "操作后时间").items():
+                _slot(rel)["post"] = ns
+
+        to_retime: dict[str, int] = {}
+        skipped: list[dict] = []
+        vault_real = Path(os.path.realpath(vault))
+        for rel, why in bad_dir_keys.items():
+            skipped.append({"dir": rel, "why": why})
+        for rel, steps in chain.items():
+            # ⛔ 账本里的目录键与 src/dst/backup 同属不可信输入, 且**同样驱动写盘**
+            # (收尾那句 os.utime)。原先这里直接 `vault / rel`: pathlib 遇绝对路径会把
+            # base 整个丢掉, `..` 交给内核解析, 而现存两道判据 (is_dir / 末段 is_symlink)
+            # 对 `<vault>/../../../..` 全部放行 ⇒ os.utime 打到 vault 之外, 还 rc=0 把
+            # 那条路径当成功项列进回执 (最终 HEAD 独立复核 H-A, 四个维度各自撞到)。
+            #
+            # 两类问题分开处置, 不要混成一句「已不是普通目录」(DD-13 名实一致):
+            #   · **键的形状**来自账本 = 被人改过 ⇒ 与 src 同口径 fail-closed 拒整批。
+            #     这一步在 `_undo_one` 动用户材料**之前**, 拒绝时用户材料一件没动。
+            #   · **目录的当下状态**(不再是目录 / 成了 symlink / 祖先链被换) 是运行期
+            #     变化, 不是篡改 ⇒ 登记跳过, 不拒整批。
+            # 键已在 `_clean` 里过过同一个 safe_join, 这里是**构造路径**不是设门 ——
+            # 同函数同字符串, 不会有第二种结果 (DD-13: 别把不可能触发的分支写成门)。
+            d = safe_join(vault, rel, what="目录时间的目录")
+            if not d.is_dir() or is_symlink(d):
+                skipped.append({"dir": rel, "why": "已不是普通目录"})
+                continue
+            # ⛔ 词法在 vault 内不等于物理在 vault 内: os.utime 会跟随**祖先链**上的
+            # symlink, 而末段 is_symlink 看不到祖先。用正向包含判定一次性覆盖所有位置,
+            # 不去枚举「symlink 可能出现在第几段」(reference: O_NOFOLLOW 只管末段)。
+            real_d = Path(os.path.realpath(d))
+            if real_d != vault_real and vault_real not in real_d.parents:
+                skipped.append({"dir": rel, "why": "物理解析后已不在 vault 内 (路径上有 symlink)"})
+                continue
+            steps = sorted(steps, key=lambda x: x["seq"])
+            why = None
+            for k, st in enumerate(steps):
+                if st["pre"] is None:
+                    why = f"第 {st['seq']} 件没留下操作前的目录时间, 无从证明这期间没人动过"
+                    break
+                if st["post"] is None:
+                    why = f"第 {st['seq']} 件没留下操作后的目录时间 (那一步没记完账), 无从证明这期间没人动过"
+                    break
+                if st["at_act"] is not None and st["at_act"] != st["pre"]:
+                    why = f"第 {st['seq']} 件排期之后、动手之前这个目录被动过"
+                    break
+                if k and steps[k - 1]["post"] != st["pre"]:
+                    why = f"第 {steps[k - 1]['seq']} 件与第 {st['seq']} 件之间这个目录被动过"
+                    break
+            if why is None and d.stat().st_mtime_ns != steps[-1]["post"]:
+                why = "执行之后这个目录被动过, 不改它的时间"
+            if why:
+                skipped.append({"dir": rel, "why": why})
+                continue
+            to_retime[rel] = steps[0]["pre"]
+        return to_retime, skipped
+
+    # ── 撤销一件 ──────────────────────────────────────────
+
+    def _assert_backup_trustworthy(self, row: dict) -> Path:
+        """⛔ 在**动手之前**验备份。事后再验太晚: 正确的产物已经被坏备份盖掉了。"""
+        bak = self.backup_abs(row)
+        if bak is None:
+            raise JournalError(f"✗ 第 {row.get('seq')} 件账上没有备份路径, 无从还原")
+        if is_symlink(bak) or not bak.is_file():
+            raise JournalError(f"✗ 第 {row.get('seq')} 件的备份不在或不是普通文件: {bak}")
+        _SP.assert_symlink_free(bak.parent)
+        if sha256_file(bak) != row.get("sha256_before"):
+            raise JournalError(f"✗ 第 {row.get('seq')} 件的备份已经和原件对不上了, 拒绝拿它去覆盖任何东西: {bak}")
+        return bak
+
+    def _finish_restore(self, row: dict, src: Path) -> None:
+        """把原路径收尾到「与批前逐项相同」: 先验 → 权限 → 时间 → 复核。可重入。
+
+        ⛔ 先验再动。chmod / utime 会**跟随 symlink**, 也会改到用户放在那个路径上的
+        别的文件 —— 拒绝必须发生在动手之前, 否则「拒绝了」的同时已经改了别人的东西
+        (Codex round-3 H1)。
+        """
+        if is_symlink(src) or not src.is_file():
+            raise JournalError(f"✗ 第 {row.get('seq')} 件的原路径不是普通文件, 拒绝在它上面动手: {src}")
+        actual = sha256_file(src)
+        if actual != row.get("sha256_before"):
+            raise JournalError(
+                f"✗ 第 {row.get('seq')} 件的原路径上不是当初那一份 (当前 {actual[:12]}… ≠ 原 "
+                f"{str(row.get('sha256_before'))[:12]}…), 拒绝在它上面动手: {src}"
+            )
+        if row.get("mode_before") is not None:
+            os.chmod(str(src), stat_mod.S_IMODE(int(row["mode_before"])))
+        ns = int(row["mtime_ns_before"])
+        os.utime(str(src), ns=(ns, ns))
+        self._verify_restored(row, src)
+
+    def _rewrite_from_backup(self, row: dict, src: Path) -> None:
+        """用备份逐字节覆写原路径。
+
+        ⛔ 不直接 `copyfile(bak, src)`: 它先截断再写, 中途失败会留下一份半截文件,
+        而那份半截既不等于 before 也不等于 after, 重试时两边都不认 = 再也恢复不了
+        (Codex round-3 H8)。换成原子替换还顺带解决了 0444 写不进去的问题 ——
+        `os.replace` 要的是目录写权限, 不是文件写权限。写完由 _finish_restore
+        按账上的 mode 盖回去。
+        """
+        bak = self._assert_backup_trustworthy(row)
+        copy_file_atomically(bak, src, self.stale_root)
+
+    def _park_product(self, row: dict, dst: Path) -> str:
+        """copy/link 的产物移进 recycle/undone/ 留痕（不是删掉）。"""
+        if self.root is not None:
+            self.mkdir_chain(self.undone_root)
+        else:
+            os.makedirs(str(self.undone_root), exist_ok=True)
+        # ⛔ 这个新落点也要过 symlink 守卫 —— 否则把 undone/ 指到 vault 外,
+        # 撤销会把用户的材料搬出去并报成功。
+        _SP.assert_symlink_free(self.undone_root)
+        target = free_path(self.undone_root / f"{int(row['seq']):03d}-{dst.name}")
+        assert_path_safe(target, what="撤销落点")
+        os.replace(str(dst), str(target))
+        return str(target.relative_to(self.batch_dir))
+
+    def _undo_one(self, row: dict, vault: Path) -> dict:
+        op = row.get("op")
+        seq = row.get("seq")
+        src = safe_join(vault, row["src"], what="原路径")
+        if op == OP_SKIP:
+            self._append({"seq": seq, "state": STATE_UNDONE, "op": op})
+            return {"seq": seq, "op": op, "action": "无需还原"}
+        if op not in OPS:
+            raise JournalError(f"✗ 账上出现未知动作, 拒绝还原: {op!r}")
+
+        _SP.assert_symlink_free(src.parent)
+        if row.get("state") == STATE_PLANNED:
+            # 排期了但主动作还没开始 —— 盘上没有本批留下的任何东西, 只需记账。
+            # ⛔ 不能顺手去「收尾」原路径: 那会对用户放在那里的东西 chmod/utime。
+            #
+            # ⛔ 但「最新状态是 planned」只是**账上**的推断, 它的前提是「acting 行一定
+            # 还在账上」。账本一旦在某条记录边界处被截短（同步回滚 / 外部工具 / 手改 ——
+            # `outputs/` 就在 vault 内, 会被 Obsidian Sync 一类工具同步）, 已执行那一件的
+            # acting/done 行就没了, 最新状态退回 planned —— 于是撤销对一件**确实搬走了**
+            # 的材料说「未执行, 无需还原」, 报 rc=0 成功而材料仍躺在落点上
+            # （全卡复核 M6 实测: 三件 move 的账截到第 4 条记录, `✓ 已撤销 2 件`,
+            # 而乙.md / 丙.md 仍在 归档/）。撤销是后悔药, 这里必须看一眼盘再下结论。
+            probe = self.dst_abs(row, vault) if row.get("dst") else None
+            if probe is not None and os.path.lexists(str(probe)):
+                raise JournalError(
+                    f"✗ 账上说第 {seq} 件没执行过, 但它的落点上确实有东西: {probe}\n"
+                    f"  账本很可能被截短或改过（少了 acting/done 行）, 拒绝按「未执行」处理 ——"
+                    f"按它处理会报成功而材料还在原地。请核对后再撤销。"
+                )
+            self._append({"seq": seq, "state": STATE_UNDONE, "op": op, "note": "未执行, 无需还原"})
+            return {"seq": seq, "op": op, "action": "未执行, 无需还原"}
+
+        dst = self.dst_abs(row, vault)
+
+        # ── 落点已经不在了。三种可能, 都靠「原路径现在是什么」来分辨 ──
+        #    ① 这一条根本没执行到（planned 写了、还没动盘）
+        #    ② 上一次撤销已经还原、只是没来得及记账
+        #    ③ 上一次撤销还原到一半（字节回来了, 时间/权限还没盖回去）
+        #    ①②③ 的正确动作是同一个: 把原路径收尾到批前态, 然后记账。
+        if not os.path.lexists(str(dst)):
+            if is_symlink(src) or not src.is_file():
+                raise JournalError(
+                    f"✗ 第 {seq} 件的去处已不存在, 原路径也没有可用的原件, 无从还原: {dst}"
+                    f"（备份仍在 {row.get('backup')}）"
+                )
+            actual = sha256_file(src)
+            if actual != row.get("sha256_before"):
+                # ⛔ planned/acting 行没有 sha256_after, 不能只认它: 统一走「像不像
+                # 本批这一步写出来的样子」那两条等式 (Codex round-3 H7)。
+                if op in OPS_TAKE_SOURCE and self.looks_like_our_product(src, row):
+                    self._rewrite_from_backup(row, src)  # 溯源还留在上面, 用备份抹掉
+                else:
+                    raise JournalError(
+                        f"✗ 第 {seq} 件的去处已不存在, 而原路径上的内容既不是原件也不是本批次的产物, 拒绝继续: {src}"
+                    )
+            self._finish_restore(row, src)
+            self._append({"seq": seq, "state": STATE_UNDONE, "op": op})
+            return {"seq": seq, "op": op, "action": str(src.relative_to(vault))}
+
+        # ── 落点还在 ──
+        if is_symlink(dst):
+            raise JournalError(f"✗ 第 {seq} 件的落点现在是一条 symlink, 拒绝跟随: {dst}")
+        _SP.assert_symlink_free(dst.parent)
+        if not self.owned_product(dst, row):
+            raise JournalError(
+                f"✗ 第 {seq} 件的落点在执行之后被改动过, 还原会把改动一起搬走 / 让修改时间说谎, 拒绝继续: {dst}"
+            )
+
+        if op in OPS_LEAVE_SOURCE:
+            # ⛔ 搬产物**之前**先确认原路径仍是当初那一份: 拒绝得越早, 被动过的东西
+            # 越少 (Codex round-3 H1 的同族 —— 别在还没验之前先动手)。
+            if is_symlink(src) or not src.is_file() or sha256_file(src) != row.get("sha256_before"):
+                raise JournalError(f"✗ 第 {seq} 件的原路径已不是当初那一份, 撤销的前提不成立, 拒绝继续: {src}")
+            where = self._park_product(row, dst)
+        else:
+            self._assert_backup_trustworthy(row)  # ⛔ 搬之前先验, 不是搬完再验
+            if os.path.lexists(str(src)):
+                raise JournalError(f"✗ 第 {seq} 件的原路径已被新的材料占用, 还原会覆盖它, 拒绝继续: {src}")
+            os.makedirs(str(src.parent), exist_ok=True)
+            os.replace(str(dst), str(src))
+            if sha256_file(src) != row.get("sha256_before"):
+                self._rewrite_from_backup(row, src)
+            where = str(src.relative_to(vault))
+
+        self._finish_restore(row, src)
+        self._append({"seq": seq, "state": STATE_UNDONE, "op": op})
+        return {"seq": seq, "op": op, "action": where}
+
+    def _verify_restored(self, row: dict, src: Path) -> None:
+        if is_symlink(src) or not src.is_file():
+            raise JournalError(f"✗ 还原后原路径不是普通文件: {src}")
+        actual = sha256_file(src)
+        if actual != row.get("sha256_before"):
+            raise JournalError(
+                f"✗ 第 {row.get('seq')} 件还原后内容对不上 (当前 {actual[:12]}… ≠ 原 "
+                f"{str(row.get('sha256_before'))[:12]}…), 拒绝继续: {src}"
+            )
+        st = src.stat()
+        if st.st_mtime_ns != int(row["mtime_ns_before"]):
+            raise JournalError(
+                f"✗ 第 {row.get('seq')} 件还原后修改时间对不上 "
+                f"(mtime_ns 当前 {st.st_mtime_ns} ≠ 记录 {row['mtime_ns_before']}), 拒绝继续: {src}"
+            )
+        want = row.get("mode_before")
+        if want is not None and stat_mod.S_IMODE(st.st_mode) != stat_mod.S_IMODE(int(want)):
+            raise JournalError(
+                f"✗ 第 {row.get('seq')} 件还原后权限位对不上 "
+                f"(当前 {stat_mod.S_IMODE(st.st_mode):o} ≠ 记录 {stat_mod.S_IMODE(int(want)):o}), "
+                f"拒绝继续: {src}"
+            )
diff --git a/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py b/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py
new file mode 100644
index 00000000..010b1db3
--- /dev/null
+++ b/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py
@@ -0,0 +1,1083 @@
+#!/usr/bin/env python3
+"""待处理清仓 —— 执行侧 (CARD-G5-7, scripts-only, 无 SKILL.md)。
+
+输入 = G5-6 只读 preview 的 JSON 产物 + 用户逐条拍板的 decisions；
+输出 = 按拍板把材料 copy / link / move / 移入回收目录 / 留原地, 并落一本可撤销的账。
+
+    inbox_apply.py --vault <V> --preview <inbox-preview-*.json> --decisions <d.json>
+    inbox_apply.py --vault <V> --undo <…/journal.jsonl>
+
+decisions 形态 (schema_version = 1):
+    {"schema_version": 1, "decisions": [
+      {"stable_id": "inb1-…", "action": "copy|link|move|recycle|skip",
+       "target": "<vault 内相对目录>", "confirm": true}
+    ]}
+
+⛔ 四条不肯让步的事:
+
+1. **默认路径 0 物理删除。**「删」在本脚本里只有一个含义 —— 移进
+   `<work-dir>/<batch_id>/recycle/` 留痕, 且必须 `--confirm-recycle`(整批) **且**
+   该条 `confirm: true`(逐件) 双重显式确认, 缺一即**整批拒绝、零写**。本文件与
+   undo_journal.py 内零 os.remove / os.unlink / Path.unlink / shutil.rmtree /
+   os.rmdir / send2trash (AST 门 F2 常驻 backend/tests/skills/test_g5_7_inbox_apply.py)。
+
+2. **不覆盖不属于自己的东西。**「零删除原语」不等于「不会覆盖」——`os.replace` 与
+   `copyfile` 都能在不调用任何删除原语的情况下把既有内容换掉。所以每个落点在落笔前
+   都要先证明**归本批次所有**: 不存在, 或者是自己上一次跑留下的 (按 sha 或自带的
+   批次溯源印记认)。只看「路径在账上」是不够的 —— 中断之后用户完全可能在那个路径上
+   放了自己的新文件。
+
+3. **准入次序铁律**: 全部守卫跑完**再**碰 work-dir —— 拒绝路径连 `outputs/` 这一级
+   都不许被建出来 (口径抄 inbox_preview.py:2425-2455)。
+
+4. **不报含糊的完成。** 任一件失败即 rc≠0, 回执写明「第几件 / 哪一件 / 为什么 /
+   账在哪 / 已完成几件」; 同输入重跑落同一本账, 只补未完成的那几件。
+
+数据面只消费 preview 的 `stable_id` / `rel_path` / `size_bytes` / `mtime_utc` /
+`label` 这些**机械字段**; 提名理由一类经过裸 .strip() 的自由文本一概不进写侧
+(AST 门 F4)。
+"""
+
+from __future__ import annotations
+
+import argparse
+import hashlib
+import importlib.util
+import json
+import os
+import stat as stat_mod
+import sys
+from pathlib import Path
+
+SCHEMA_VERSION = 1
+GENERATOR = "clear-inbox/inbox_apply.py v1.1 (CARD-G5-7 执行侧)"
+
+_HERE = Path(__file__).resolve()
+_PREVIEW_PATH = _HERE.parent / "inbox_preview.py"
+_JOURNAL_PATH = _HERE.parents[3] / "scripts" / "undo_journal.py"
+
+
+def _load_sibling(path: Path, mod_name: str, why: str):
+    """加载兄弟模块。⛔ 缺失即拒绝运行, 不做本地降级实现。"""
+    if not path.is_file():
+        raise SystemExit(f"✗ 复用来源缺失, 拒绝以未加固的写侧运行: {path}\n  （{why}）")
+    spec = importlib.util.spec_from_file_location(mod_name, path)
+    mod = importlib.util.module_from_spec(spec)
+    # ⛔ exec_module 默认会往被导入模块旁边写 __pycache__ —— 那是往 vault 里落文件。
+    prev = sys.dont_write_bytecode
+    sys.dont_write_bytecode = True
+    try:
+        spec.loader.exec_module(mod)
+    finally:
+        sys.dont_write_bytecode = prev
+    return mod
+
+
+_IP = _load_sibling(
+    _PREVIEW_PATH,
+    "_g57_inbox_preview",
+    "时刻格式 / 身份键编码必须与产出 preview 的那个引擎同源, 手抄一份必然漂移",
+)
+_UJ = _load_sibling(
+    _JOURNAL_PATH,
+    "_g57_undo_journal",
+    "备份 / 账本 / 撤销是共用模块, 本脚本不自带第二份实现",
+)
+_SP = _IP._SP  # 祖先链 symlink 守卫的单一真相源 (split_preview)
+
+# ───────────────────────────────── 常量 ─────────────────────────────────
+
+#: 缺省工作目录。`outputs` 在 preview 的语料排除集 (inbox_preview.py:327), 且不在
+#: 收件箱内 —— 于是本脚本的产物不会在下一次 preview 里被当成待处理材料盘点回来。
+DEFAULT_WORK_PARENT = "outputs"
+DEFAULT_WORK_NAME = "clear-inbox"
+
+A_COPY = "copy"
+A_LINK = "link"
+A_MOVE = "move"
+A_RECYCLE = "recycle"
+A_SKIP = "skip"
+ACTIONS = (A_COPY, A_LINK, A_MOVE, A_RECYCLE, A_SKIP)
+
+#: 需要落点目录的动作。recycle 的落点由本脚本定 (回收目录), skip 没有落点。
+ACTIONS_NEEDING_TARGET = (A_COPY, A_LINK, A_MOVE)
+#: 会把源从原路径拿走的动作 —— 重跑对账时「源不在了」对它们是正常的。
+ACTIONS_TAKE_SOURCE = (A_MOVE, A_RECYCLE)
+#: 会产出一份「本批次新造的 md」的动作 —— 只有它们写溯源 frontmatter。
+#: link 与原件同 inode, 写溯源等于改原件, 所以不在此列。
+ACTIONS_WITH_PROVENANCE = (A_COPY, A_MOVE)
+
+#: 落点首段黑名单: 配置目录 / 产物目录不是放学习材料的地方。
+FORBIDDEN_FIRST_SEGMENTS = frozenset({".claude", ".obsidian", DEFAULT_WORK_PARENT})
+
+RECEIPT_STEM = "receipt"
+UNDO_RECEIPT_STEM = "undo-receipt"
+
+
+def sha256_file(path) -> str:
+    return _UJ.sha256_file(path)
+
+
+def die(msg: str):
+    raise SystemExit(msg if msg.startswith("✗") else f"✗ {msg}")
+
+
+# ───────────────────────── 输入读取 ─────────────────────────
+
+
+def load_json_file(path: Path, what: str) -> tuple[dict, str]:
+    """返回 (解析结果, 文件 sha256)。sha 进 batch_id —— 同输入同批次。"""
+    if path.is_symlink():
+        die(f"{what} 本身是 symlink, 拒绝读取: {path}")
+    if not path.is_file():
+        die(f"{what} 不存在或不是普通文件: {path}")
+    raw = path.read_bytes()
+    try:
+        data = json.loads(raw.decode("utf-8"))
+    except (UnicodeDecodeError, ValueError) as e:
+        die(f"{what} 不是合法 UTF-8 JSON: {path} ({e})")
+    if not isinstance(data, dict):
+        die(f"{what} 顶层必须是对象: {path}")
+    if data.get("schema_version") != SCHEMA_VERSION:
+        die(
+            f"{what} 的 schema_version 不是 {SCHEMA_VERSION} "
+            f"(实得 {data.get('schema_version')!r}), 拒绝按未知契约执行: {path}"
+        )
+    return data, hashlib.sha256(raw).hexdigest()
+
+
+def compute_vault_fingerprint(vault: Path) -> str:
+    """与 inbox_preview.py:2157-2158 同式。两边一致性由行为门证明:
+    真跑 preview 产出的指纹必须被接受, 换一个 vault 的必须被拒。"""
+    return "vf1-" + hashlib.sha256(os.path.realpath(vault).encode("utf-8")).hexdigest()[:16]
+
+
+def resolve_vault(raw: str) -> Path:
+    vault = Path(raw)
+    if vault.is_symlink():
+        die(f"vault 路径本身是 symlink, 拒绝越界写入: {vault}")
+    if not vault.is_dir():
+        die(f"vault 不存在或不是目录: {vault}")
+    return vault.resolve()
+
+
+def resolve_work_dir(vault: Path, raw: str | None) -> Path:
+    """只做词法与边界判定, **不创建任何目录**。"""
+    if raw is None:
+        return vault / DEFAULT_WORK_PARENT / DEFAULT_WORK_NAME
+    work = Path(raw)
+    if not work.is_absolute():
+        work = vault / work
+    real = Path(os.path.realpath(work))
+    vault_real = Path(os.path.realpath(vault))
+    if real != vault_real and vault_real not in real.parents:
+        die(f"--work-dir 必须落在 vault 内, 拒绝越界: {work}")
+    return work
+
+
+def assert_work_dir_outside_inbox(vault: Path, work_dir: Path, inbox_name: str) -> None:
+    """工作目录不能落在收件箱里 —— 备份与回收件落进**正在清理的那个目录**,
+    下一次盘点会把它们当噪音扫进来, 而「删掉的东西」就躺在你要清空的地方。"""
+    real = Path(os.path.realpath(work_dir))
+    inbox_real = Path(os.path.realpath(vault / inbox_name))
+    if real == inbox_real or inbox_real in real.parents:
+        die(f"--work-dir 落在收件箱内 ({real}), 拒绝: 备份与回收件不能放进要清理的那个目录")
+
+
+# ───────────────────────── 准入守卫 ─────────────────────────
+
+
+def _path_is_within(real, anchor) -> bool:
+    """`real` 是不是就是 `anchor`、或落在它下面 —— **大小写不敏感**地判。
+
+    ⛔ macOS 默认卷 (APFS/HFS+) 大小写不敏感, 而 `os.path.realpath` **不做**大小写
+    规范化: `realpath('<v>/.Claude')` 原样返回 `.Claude`, 但它和 `.claude` 是同一个
+    目录（`lexists` / `is_dir` 对它都为真）。于是纯字符串比较整条失效 —— 把 target
+    首段换一个字母的大小写, 三道边界判据一起落空, 学习材料被写进 `.claude/`（本工具
+    自己的脚本就在这棵树下）/ `.obsidian/` / `outputs/`（全卡复核 HIGH-F 实测）。
+
+    先用 `samefile` 问文件系统（两端都存在时这是权威答案）, 问不出来再退回逐段
+    casefold 比较 —— 后者对「落点还不存在」的常态也成立。
+    """
+    try:
+        if os.path.exists(real) and os.path.exists(anchor) and os.path.samefile(str(real), str(anchor)):
+            return True
+    except OSError:
+        pass
+    r = [p.casefold() for p in Path(real).parts]
+    a = [p.casefold() for p in Path(anchor).parts]
+    return len(r) >= len(a) and r[: len(a)] == a
+
+
+def validate_target(vault: Path, inbox_name: str, work_dir: Path, raw) -> Path:
+    """落点目录白名单。⛔ 先词法后物理: `..` 与绝对路径在词法层就拒掉, 再用 realpath
+    判边界 —— 只做词法判定会被祖先 symlink 绕过 (O_NOFOLLOW 只管末段)。"""
+    if not isinstance(raw, str) or not raw.strip("/"):
+        die(f"target 必须是非空的 vault 内相对目录, 实得 {raw!r}")
+    cand = Path(raw)
+    if cand.is_absolute():
+        die(f"target 必须是相对目录, 不接受绝对路径: {raw!r}")
+    parts = cand.parts
+    # ⛔ `Path(".").parts` 与 `Path("./").parts` 都是**空元组**（pathlib 把纯 `.` 规范化
+    # 掉了）, 而上面的 `raw.strip("/")` 判非空放行了它 —— 于是下面取 `parts[0]` 抛裸
+    # IndexError, 逃出本文件承诺的 `die()` 统一出口（全卡复核 L3/L6）。
+    if not parts:
+        die(f"target 指的是 vault 根本身, 那不是放学习材料的地方: {raw!r}")
+    if any(part == ".." for part in parts):
+        die(f"target 含 `..`, 拒绝越界: {raw!r}")
+    # ⛔ casefold 比较: 大小写不敏感卷上 `.Claude` 和 `.claude` 是同一个目录。
+    head = parts[0].casefold()
+    if head in {s.casefold() for s in FORBIDDEN_FIRST_SEGMENTS}:
+        die(f"target 首段 {parts[0]!r} 是配置/产物目录, 不是放学习材料的地方: {raw!r}")
+    if head == inbox_name.casefold():
+        die(f"target 指回收件箱本身, 那不叫清仓: {raw!r}")
+
+    dst_dir = vault / cand
+    real = Path(os.path.realpath(dst_dir))
+    vault_real = Path(os.path.realpath(vault))
+    if not _path_is_within(real, vault_real):
+        die(f"target 解析后落在 vault 之外 ({real}), 拒绝越界: {raw!r}")
+    inbox_real = Path(os.path.realpath(vault / inbox_name))
+    if _path_is_within(real, inbox_real):
+        die(f"target 解析后落在收件箱内 ({real}), 拒绝: {raw!r}")
+    work_real = Path(os.path.realpath(work_dir))
+    if _path_is_within(real, work_real):
+        die(f"target 解析后落在工作目录内 ({real}), 拒绝: {raw!r}")
+    # 祖先链无 symlink —— 词法上在 vault 内的写会被祖先 symlink 重定向到别处
+    _SP.assert_symlink_free(dst_dir)
+    return dst_dir
+
+
+def source_path(vault: Path, item: dict, inbox_name: str) -> Path:
+    """源路径 + 形状校验 + 祖先链守卫。
+
+    ⛔ `rel_path` 是从 preview 的 JSON 里读出来的, 而那份 JSON 用户改得动。不校验
+    形状就直接拼路径, 一条 `../outside.md` 就能让执行侧去搬 vault 外的文件（备份
+    落点仍在批次目录内, 看上去一切正常）。preview 自己产出的形状恒是
+    `<收件箱名>/<文件名>` 两段 (inbox_preview.py:1963-1978), 这里照这个形状卡死。
+
+    ⛔ 只查末段也是不够的: 把整个收件箱挪到 vault 外再用一条 symlink 接回来, 末段
+    (那个 .md) 仍是普通文件, 而读写全都发生在 vault 之外 —— 所以还要查祖先链。
+    """
+    rel = item.get("rel_path")
+    if not isinstance(rel, str) or not rel:
+        die(f"preview 条目缺少 rel_path 或格式不对: {rel!r}")
+    cand = Path(rel)
+    if cand.is_absolute() or any(part == ".." for part in cand.parts):
+        die(f"preview 条目的 rel_path 不是 vault 内的相对路径, 拒绝: {rel!r}")
+    parts = cand.parts
+    if len(parts) != 2 or parts[0] != inbox_name:
+        die(f"preview 条目的 rel_path 形状不对 (应为 <{inbox_name}>/<文件名>): {rel!r}")
+    if parts[1] != item.get("name"):
+        die(f"preview 条目的 rel_path 与 name 对不上 ({parts[1]!r} ≠ {item.get('name')!r})")
+
+    src = vault / cand
+    inbox_real = Path(os.path.realpath(vault / inbox_name))
+    if Path(os.path.realpath(src)).parent != inbox_real:
+        die(f"preview 条目解析后不在收件箱内, 拒绝: {rel!r}")
+    _SP.assert_symlink_free(src.parent)
+    return src
+
+
+def check_source_fresh(src: Path, item: dict):
+    """源材料必须仍与 preview 记录的那一份**逐项**对得上。"""
+    rel = item["rel_path"]
+    try:
+        st = os.lstat(str(src))
+    except OSError as e:
+        die(f"源材料已不在原处, preview 已过期, 请重跑 preview: {rel} ({e.strerror})")
+    if stat_mod.S_ISLNK(st.st_mode):
+        die(f"源材料现在是一条 symlink, 拒绝跟随 (可能指向 vault 外): {rel}")
+    if not stat_mod.S_ISREG(st.st_mode):
+        die(f"源材料不是普通文件, 拒绝搬动: {rel}")
+    if st.st_size != item["size_bytes"]:
+        die(f"源材料大小与 preview 不符 ({st.st_size} ≠ {item['size_bytes']}), preview 已过期, 请重跑 preview: {rel}")
+    actual_mtime = _IP.fmt_utc(st.st_mtime)
+    if actual_mtime != item["mtime_utc"]:
+        die(
+            f"源材料修改时间与 preview 不符 ({actual_mtime} ≠ {item['mtime_utc']}), "
+            f"preview 已过期, 请重跑 preview: {rel}"
+        )
+    return st
+
+
+def compute_batch_id(fingerprint: str, preview_sha: str, decisions_sha: str) -> str:
+    """同 vault + 同 preview + 同拍板 ⇒ 同一本账 ⇒ 中断重跑幂等。
+
+    换了 --now 重跑 preview ⇒ JSON 字节变 ⇒ 这是**另一个批次**, 会在落点归属守卫
+    (copy/link/move) 或源材料新鲜度守卫 (move/recycle 的源已被上一批拿走) 上被拦下,
+    而不是默默再做一遍。
+    """
+    raw = "\n".join([fingerprint, preview_sha, decisions_sha]).encode("utf-8")
+    return hashlib.sha256(raw).hexdigest()[:12]
+
+
+def build_plans(vault, work_dir, preview, decisions, confirm_recycle, journal, rows):
+    """把拍板翻译成逐条执行计划。任何一条不过关 ⇒ 整批拒绝、零写。
+
+    `rows` 是本批次账本的既有记录 (只读地读来的)。有它才分得清两种「源不在了」:
+    上一次已经把它合法搬走了 (该跳过 / 该续跑), 还是 preview 过期了 (该拒绝)。
+    没有这一层, move/recycle 做成之后重跑会**恒**卡在新鲜度守卫上, 幂等根本走不到。
+    """
+    label = preview.get("label")
+    if not isinstance(label, str) or not label:
+        die("preview 缺少 label (收件箱目录名), 拒绝执行")
+    items = {}
+    for it in preview.get("items", []):
+        items[it["stable_id"]] = it
+    if not items:
+        die("preview 里没有任何条目, 没有可执行的事")
+
+    raw_list = decisions.get("decisions")
+    if not isinstance(raw_list, list) or not raw_list:
+        die("decisions 必须是非空列表")
+
+    # ⛔ 取每个 seq 的**最新**状态。按「出现过 done」判的话, 撤销之后重新执行的
+    # 那一轮会被当成「上次已完成」直接跳过, 于是什么都没做却报完成。
+    latest = _UJ.latest_by_seq(rows)
+    done_by_seq = {k: r for k, r in latest.items() if r.get("state") == _UJ.STATE_DONE}
+    #: 已排期但还没记完的 —— planned（没动过盘）与 acting（动过盘了）两种。
+    open_by_seq = {k: r for k, r in latest.items() if r.get("state") in (_UJ.STATE_PLANNED, _UJ.STATE_ACTING)}
+
+    plans = []
+    seen = set()
+    for idx, d in enumerate(raw_list, start=1):
+        if not isinstance(d, dict):
+            die(f"第 {idx} 条拍板不是对象: {d!r}")
+        sid = d.get("stable_id")
+        if sid not in items:
+            die(f"第 {idx} 条拍板的 stable_id 不在这份 preview 里 (可能拿错了盘点单): {sid!r}")
+        if sid in seen:
+            die(f"第 {idx} 条拍板的 stable_id 重复出现, 一件材料只能有一个去向: {sid!r}")
+        seen.add(sid)
+
+        action = d.get("action")
+        if action not in ACTIONS:
+            die(f"第 {idx} 条拍板的 action 未知 (只认 {'/'.join(ACTIONS)}): {action!r}")
+
+        prior = done_by_seq.get(idx) or open_by_seq.get(idx)
+        if prior is not None and prior.get("stable_id") not in (None, sid):
+            die(f"第 {idx} 条拍板与账上第 {idx} 条对不上 (账 {prior.get('stable_id')!r} ≠ 拍板 {sid!r})")
+
+        item = items[sid]
+        src = source_path(vault, item, label)
+
+        target_raw = d.get("target")
+        if action in ACTIONS_NEEDING_TARGET:
+            dst_dir = validate_target(vault, label, work_dir, target_raw)
+            dst = dst_dir / item["name"]
+            dst_base = _UJ.BASE_VAULT
+            dst_rel = str(dst.relative_to(vault))
+        else:
+            if target_raw not in (None, ""):
+                die(f"第 {idx} 条拍板的 action={action} 不该带 target, 实得 {target_raw!r}")
+            if action == A_RECYCLE:
+                dst_rel = f"{_UJ.RECYCLE_DIR}/{item['rel_path']}"
+                dst = journal.batch_dir / dst_rel
+                dst_base = _UJ.BASE_BATCH
+            else:
+                dst, dst_base, dst_rel = None, _UJ.BASE_BATCH, ""
+
+        if action == A_RECYCLE:
+            # ⛔ 双重显式确认: 整批 flag 与逐件 confirm 缺一不可, 且 confirm 必须是
+            # **布尔真** —— 认「真值」的话, "no" / 0.0 之外的任何东西都能蒙混过关。
+            if not confirm_recycle:
+                die(
+                    f"第 {idx} 条要移入回收目录, 但没有给 --confirm-recycle, 整批拒绝、未动任何文件: {item['rel_path']}"
+                )
+            if d.get("confirm") is not True:
+                die(
+                    f"第 {idx} 条要移入回收目录, 但该条的 confirm 不是 true "
+                    f"(实得 {d.get('confirm')!r}), 整批拒绝、未动任何文件: {item['rel_path']}"
+                )
+
+        settled = idx in done_by_seq
+        # 已动盘但还没记 done 的取源动作: 源不在、落点在 ⇒ 这是中断点, 不是 preview 过期
+        # ⛔ 只有 **acting**（确实动过盘）才算「源不在是正常的」。planned 只是排了期,
+        # 那时源必须还在原处, 否则就是 preview 过期。
+        resumable = (
+            not settled
+            and open_by_seq.get(idx, {}).get("state") == _UJ.STATE_ACTING
+            and action in ACTIONS_TAKE_SOURCE
+            and not os.path.lexists(str(src))
+            and dst is not None
+            and os.path.lexists(str(dst))
+        )
+        st = None
+        if not (settled or resumable):
+            st = check_source_fresh(src, item)
+            prior_open = open_by_seq.get(idx)
+            if prior_open is not None and prior_open.get("sha256_before"):
+                # ⛔ 账上已经有这一件的 sha 了, 复用旧记录时就该拿它核, 而不是再信
+                # 一次「大小 + 秒级 mtime」那个粗判据 —— 等长改写并保持 mtime 就能
+                # 穿过去, 然后撤销会拿旧内容把新内容盖掉 (Codex round-4 H1)。
+                actual = sha256_file(src)
+                if actual != prior_open["sha256_before"]:
+                    die(
+                        f"第 {idx} 条的源材料在排期之后被改动过 (当前 {actual[:12]}… ≠ 账上 "
+                        f"{prior_open['sha256_before'][:12]}…), 续跑会让账与实盘对不上, "
+                        f"拒绝: {item['rel_path']}（请重跑 preview 另起一批）"
+                    )
+
+        plans.append(
+            {
+                "seq": idx,
+                "action": action,
+                "stable_id": sid,
+                "name": item["name"],
+                "src_rel": item["rel_path"],
+                "src_abs": src,
+                "dst_abs": dst,
+                "dst_base": dst_base,
+                "dst_rel": dst_rel,
+                "mtime_utc": item["mtime_utc"],
+                "size_bytes": item["size_bytes"],
+                "st": st,
+                "settled": settled,
+                "resumable": resumable,
+            }
+        )
+    return plans
+
+
+def check_destinations_free(plans, journal, rows) -> None:
+    """落点归属守卫 —— 「覆写幂等」的安全前提, 对**每一个**动作都要过。
+
+    执行时 copy 是覆写式的、move/recycle 是 os.replace 式的 (才幂等), 所以必须先证明
+    每个落点要么空着, 要么**确实是本批次自己**先前造出来的。少了这一条, 一次重跑就
+    能悄悄盖掉用户的同名文件 —— 而「路径在账上」证明不了这件事: 中断之后用户完全
+    可能在那个路径上放了自己的东西。回收目录同样要过这道门, 它不是法外之地。
+    """
+    # ⛔ acting 必须收进来。加新状态时只改了「最新状态」与撤销侧, 漏了这里 ——
+    # 于是主动作做完、done 还没落账时重跑, 自家产物会被判成外来文件而拒绝
+    # (Codex round-4 H4)。加一个状态就得把**所有读这个状态机的地方**列一遍。
+    by_seq = {
+        k: r
+        for k, r in _UJ.latest_by_seq(rows).items()
+        if r.get("state") in (_UJ.STATE_PLANNED, _UJ.STATE_ACTING, _UJ.STATE_DONE)
+    }
+    for p in plans:
+        dst = p["dst_abs"]
+        if p["action"] == A_SKIP or dst is None:
+            continue
+        if p.get("settled"):
+            # ⛔ 账上已 done 的那几件交给 `verify_done` —— 它对同一个输入给的是
+            # 「账上说第 N 件已完成, 但落点内容已被改动 (…≠…)」, 而这里无差别跑归属守卫
+            # 会先撞上「不是本批次造的, 先自己处理掉那份同名文件」。后者对「用户编辑过
+            # 自己已经搬过去的那份笔记」这个**完全正常**的行为是错的诊断, 而且会把后面
+            # 没补完的那几件永远堵死（全卡复核 M15 实测）。两道门触发条件重合时，
+            # 要让**诊断更准**的那一道先说话。
+            continue
+        if not os.path.lexists(str(dst)):
+            continue
+        if _UJ.is_symlink(dst):
+            die(f"第 {p['seq']} 件的落点是一条 symlink, 拒绝跟随: {p['dst_rel']}")
+        row = by_seq.get(p["seq"])
+        if row is not None and row.get("dst") == p["dst_rel"] and row.get("dst_base") == p["dst_base"]:
+            if journal.owned_product(dst, row):
+                continue  # 是自家上一次跑留下的产物
+        die(
+            f"第 {p['seq']} 件的落点已经有东西了, 而且它不是本批次造的, 不会覆盖它: "
+            f"{p['dst_rel']}（先改个落点, 或自己处理掉那份同名文件）"
+        )
+
+
+# ───────────────────────── 执行 ─────────────────────────
+
+
+def _provenance_meta(plan, batch_id: str, applied_at: str) -> dict:
+    return {
+        "source_rel_path": plan["src_rel"],
+        "source_mtime_utc": plan["mtime_utc"],
+        "batch_id": batch_id,
+        "applied_at_utc": applied_at,
+        "op": plan["action"],
+    }
+
+
+def _dir_chain_for_mtime(vault: Path, d: Path) -> list:
+    """`d` 自己 + 它**尚不存在的那几级的父目录**里最深的那个已存在祖先。
+
+    ⛔ 落点目录是本次新建的（`归档/2026`）时, 被改动条目集合的其实是它的**父目录**
+    `归档` —— 而 `归档` 从来没进过任何一条账目行, 于是撤销既不会还原它的 mtime,
+    也不会把它登进 `dirs_not_retimed`。回执的「目录时间」一节自称完整, 却漏了它
+    （全卡复核 L13）。
+    """
+    out = [d]
+    cur = Path(d)
+    while not cur.exists() and cur != cur.parent:
+        cur = cur.parent
+        out.append(cur)
+    return out
+
+
+def touched_dir_mtimes(vault: Path, plan) -> dict:
+    """本条会改动条目集合的那几个 vault 内目录, 连同它们此刻的 mtime。"""
+    out: dict = {}
+    if plan["action"] == A_SKIP:
+        return out
+    cands = [plan["src_abs"].parent]
+    if plan["dst_base"] == _UJ.BASE_VAULT and plan["dst_abs"] is not None:
+        # ⛔ 落点目录若是本次新建的, 被改动条目集合的是它**最深的那个已存在祖先**;
+        # 不收进来的话那个祖先既不会被还原、也不会被登进 dirs_not_retimed（L13）。
+        cands.extend(_dir_chain_for_mtime(vault, plan["dst_abs"].parent))
+    for d in cands:
+        try:
+            rel = str(d.relative_to(vault))
+        except ValueError:
+            continue  # 不在 vault 内 (回收目录等) —— 不是要还原的面
+        if d.is_dir() and not _UJ.is_symlink(d):
+            out[rel] = d.stat().st_mtime_ns
+    return out
+
+
+def missing_dirs(vault: Path, target: Path) -> list:
+    """target 这一路上还不存在、本次会被建出来的目录 (vault 相对)。
+
+    撤销**不会**删掉它们 (默认路径 0 物理删除), 所以必须记下来在回执里说出口 ——
+    否则「撤销后全树回到原样」这句话会在这一点上悄悄失真。
+    """
+    out = []
+    cur = Path(target)
+    while True:
+        try:
+            rel = str(cur.relative_to(vault))
+        except ValueError:
+            break
+        if os.path.lexists(str(cur)):
+            break
+        out.append(rel)
+        cur = cur.parent
+    return list(reversed(out))
+
+
+def perform(plan, entry, journal, batch_id: str, applied_at: str):
+    """做一件。每一步都写成可重入的: 重跑落到同一结果, 不叠加副作用。"""
+    action = plan["action"]
+    if action == A_SKIP:
+        return None, None, None, None
+
+    src, dst = plan["src_abs"], plan["dst_abs"]
+    if plan["dst_base"] == _UJ.BASE_VAULT:
+        journal.mkdir_chain(dst.parent)
+    else:
+        os.makedirs(str(dst.parent), exist_ok=True)
+    _SP.assert_symlink_free(dst.parent)
+
+    if action == A_COPY:
+        # ⛔ 不直接 copyfile: 它先截断再写, 中途失败留下的半截文件既不等于 before
+        # 也不等于 after, 归属判定两边都不认 = 重试时只能拒绝 (Codex round-3 H8)。
+        _UJ.copy_file_atomically(src, dst, journal.stale_root)
+    elif action == A_LINK:
+        if os.path.lexists(str(dst)):
+            if os.stat(str(dst)).st_ino == os.stat(str(src)).st_ino:
+                pass  # 上一次已经链好, 只是没来得及记账
+            else:
+                # 半态残留: 挪进 stale/ 留痕, 不做物理删除。
+                # ⛔ 走带守卫的 park_into_stale, 不是裸 makedirs+replace —— 后者是全卡
+                # 唯一一处不查 stale/ 是否 symlink 的搬动, 而搬的是**用户的文件**:
+                # stale/ 指向 vault 外时它会被无声搬出去而工具报 ✓ 完成
+                # （全卡复核 HIGH-G）。落点还要记进账, 否则「它去哪了」无处可查。
+                parked = _UJ.park_into_stale(dst, journal.stale_root, what="link 半态残留")
+                entry["link_parked"] = str(parked)
+                print(f"⚠ 落点上原有一份不是本批次造的文件, 已挪到 {parked} 留痕", file=sys.stderr)
+                os.link(str(src), str(dst))
+        else:
+            os.link(str(src), str(dst))
+    elif action in (A_MOVE, A_RECYCLE):
+        if os.path.lexists(str(src)):
+            os.replace(str(src), str(dst))
+        elif not os.path.lexists(str(dst)):
+            raise OSError(f"源与落点都不存在, 不猜它去哪了: {plan['src_rel']}（备份在 {entry.get('backup')}）")
+        # src 不在而 dst 在 = 上一次的 os.replace 已原子完成, 从下面的收尾续跑
+
+    provenance = None
+    if action in ACTIONS_WITH_PROVENANCE:
+        # ⛔ 用**账上那份** prov_meta。续跑时本次的 applied_at 与排期那次不同, 拿新的
+        # 重算会写出与账上期望不符的字节, 于是下一次连自己刚写的产物都不认
+        # (Codex round-3 H6)。账里记的才是这一步的唯一期望。
+        meta = entry.get("prov_meta") or _provenance_meta(plan, batch_id, applied_at)
+        provenance = _UJ.write_provenance(dst, meta, journal.stale_root)
+    mode = entry.get("mode_before")
+    if mode is not None:
+        os.chmod(str(dst), stat_mod.S_IMODE(int(mode)))
+    ns = int(entry["mtime_ns_before"])
+    os.utime(str(dst), ns=(ns, ns))
+    st = os.stat(str(dst))
+    return sha256_file(dst), st.st_mtime_ns, provenance, st.st_ino
+
+
+def verify_done(plan, row, vault: Path, journal) -> None:
+    """复核一条已记 done 的账是否与实盘相符。对不上就停下 —— 世界在两次跑之间被改过,
+    盲目重做可能把用户已经手工整理过的东西再搬一次。"""
+    action = plan["action"]
+    if action == A_SKIP:
+        return
+    dst = journal.dst_abs(row, vault)
+    if not os.path.lexists(str(dst)):
+        die(f"账上说第 {plan['seq']} 件已完成, 但落点已不在: {dst}（请检查后重跑 preview）")
+    if _UJ.is_symlink(dst):
+        die(f"账上说第 {plan['seq']} 件已完成, 但落点现在是一条 symlink: {dst}")
+    actual = sha256_file(dst)
+    if actual != row.get("sha256_after"):
+        die(
+            f"账上说第 {plan['seq']} 件已完成, 但落点内容已被改动 "
+            f"({actual[:12]}… ≠ {str(row.get('sha256_after'))[:12]}…): {dst}"
+        )
+    if action in ACTIONS_TAKE_SOURCE and os.path.lexists(str(plan["src_abs"])):
+        die(f"账上说第 {plan['seq']} 件已搬走, 但原路径又有东西了: {plan['src_rel']}")
+    if action == A_LINK:
+        # ⛔ 硬链接的「完成」是一种**关系**, 不是一份内容: 只验落点内容的话, 原件被
+        # 换成另一个文件之后这条关系早断了, 却还会报完成。
+        src = plan["src_abs"]
+        if _UJ.is_symlink(src) or not src.is_file():
+            die(f"账上说第 {plan['seq']} 件已硬链接, 但原路径已不是普通文件: {plan['src_rel']}")
+        if os.stat(str(src)).st_ino != os.stat(str(dst)).st_ino:
+            die(f"账上说第 {plan['seq']} 件已硬链接, 但它和原件已不是同一份了: {plan['src_rel']}")
+
+
+def render_receipt_md(data: dict) -> str:
+    lines = [
+        f"# 清仓回执 · 批次 {data['batch_id']}",
+        "",
+        f"- 结果: {'全部完成' if data['ok'] else '中途停下'}",
+        f"- 共 {data['total']} 件, 已完成 {data['completed']} 件",
+        f"- 账本: `{data['journal']}`",
+        f"- 时刻(UTC): {data['applied_at_utc']}",
+        "",
+    ]
+    if not data["ok"] and data.get("failed"):
+        f = data["failed"]
+        lines += [
+            "## 停在哪一件",
+            "",
+            f"- 第 {f['index']} 件 · `{f['src']}` · 动作 {f['op']}",
+            f"- 原因: {f['reason']}",
+            "",
+            "前面已完成的那几件都记在账上了; 修好原因后**用同一份 preview 与同一份拍板**重跑, 它只会补做没做完的。",
+            "",
+        ]
+    lines += ["## 逐件", "", "| # | 动作 | 材料 | 去处 | 溯源 |", "|---|---|---|---|---|"]
+    for r in data["results"]:
+        lines.append(f"| {r['index']} | {r['op']} | `{r['src']}` | `{r['dst'] or '—'}` | {r['provenance'] or '—'} |")
+    if data.get("created_dirs"):
+        lines += [
+            "",
+            "## 本次新建的目录",
+            "",
+            "撤销**不会**删掉它们（本工具默认路径上没有物理删除）, 撤销后会留成空目录:",
+            "",
+        ]
+        lines += [f"- `{d}`" for d in data["created_dirs"]]
+    if data.get("dirs_retimed") is not None:
+        lines += ["", "## 目录时间", "", f"- 已还原: {data['dirs_retimed'] or '无'}"]
+        for item in data.get("dirs_not_retimed") or []:
+            lines.append(f"- 未还原 `{item['dir']}`: {item['why']}")
+    lines += ["", f"> {data['note']}", ""]
+    return "\n".join(lines)
+
+
+def write_receipt(journal, data: dict, stem: str) -> None:
+    """写两份回执。落点若已有东西, 只有「与账上记的上一版 sha 相同」才算自家产物,
+    否则先挪进 stale/ 留痕 —— 判据是可计算的等式, 不是子串启发式（独立复核 H-1）。"""
+    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
+    md = render_receipt_md(data).encode("utf-8")
+    items = [
+        (journal.batch_dir / f"{stem}.json", payload),
+        (journal.batch_dir / f"{stem}.md", md),
+    ]
+    try:
+        prior = journal.recorded_receipt_shas(journal.read_rows(), stem)
+    except (OSError, _UJ.JournalError):
+        prior = {}
+    _UJ.write_pair_atomically(items, journal.stale_root, owned_shas=prior)
+    journal.record_receipt_shas(stem, {str(path): hashlib.sha256(blob).hexdigest() for path, blob in items})
+
+
+def _do_one(plan, entry, journal, vault: Path, batch_id: str, applied_at: str, created_dirs: list):
+    """做一件的全部动作: 备份 → plan → acting → perform → commit。
+
+    ⛔ 整段都要能被调用方的失败处理接住。此前只有 perform 在 try 里, 于是 backup /
+    记账 这几步一旦失败就是直接抛出去 —— 前面已完成的那几件没有回执, 「不报含糊的
+    完成」这条承诺在这条路径上落空 (Codex round-4 M3)。
+    """
+    seq = plan["seq"]
+    if entry is None:
+        if plan["action"] == A_SKIP:
+            backup_rel, sha_before, mtime_ns_before, mode_before = (
+                None,
+                sha256_file(plan["src_abs"]),
+                plan["st"].st_mtime_ns,
+                plan["st"].st_mode,
+            )
+        else:
+            backup_rel, sha_before, mtime_ns_before, mode_before = journal.backup(plan["src_abs"], plan["src_rel"])
+        if plan["dst_abs"] is None or plan["dst_base"] != _UJ.BASE_VAULT:
+            new_dirs = []
+        else:
+            new_dirs = missing_dirs(vault, plan["dst_abs"].parent)
+        created_dirs += [d for d in new_dirs if d not in created_dirs]
+        entry = journal.plan(
+            seq=seq,
+            op=plan["action"],
+            stable_id=plan["stable_id"],
+            src=plan["src_rel"],
+            dst=plan["dst_rel"],
+            dst_base=plan["dst_base"],
+            sha256_before=sha_before,
+            mtime_ns_before=mtime_ns_before,
+            mode_before=mode_before,
+            backup=backup_rel,
+            prov_meta=(
+                _provenance_meta(plan, batch_id, applied_at) if plan["action"] in ACTIONS_WITH_PROVENANCE else None
+            ),
+            dir_mtimes=touched_dir_mtimes(vault, plan),
+            created_dirs=new_dirs,
+            meta={"name": plan["name"], "size_bytes": plan["size_bytes"]},
+        )
+    else:
+        created_dirs += [d for d in (entry.get("created_dirs") or []) if d not in created_dirs]
+
+    # ⛔ 动手那一刻再读一次目录时间: entry 里的「之前」可能是上一次跑留下的陈旧
+    # 读数, 那两次之间用户对这个目录做的事不在任何一步的账里。
+    dir_at_act = touched_dir_mtimes(vault, plan)
+    # ⛔ 落一条 acting 行再动手 —— 「排期了」与「动过盘了」的分界线。少了它,
+    # 落点上那份同字节的文件是我们写的还是用户放的, 代码分不出来。
+    if entry.get("state") != _UJ.STATE_ACTING:
+        entry = journal.mark_acting(entry)
+
+    sha_after, mtime_after, provenance, inode = perform(plan, entry, journal, batch_id, applied_at)
+
+    journal.commit(
+        entry,
+        sha256_after=sha_after,
+        mtime_ns_after=mtime_after,
+        provenance=provenance,
+        inode=inode,
+        dir_mtimes_at_act=dir_at_act,
+        dir_mtimes_after=touched_dir_mtimes(vault, plan),
+    )
+    return entry, sha_after, mtime_after, provenance, inode
+
+
+def write_receipt_best_effort(journal, data: dict, stem: str):
+    """写回执, 但**不让它自己的失败盖掉调用方要说的话**。
+
+    ⛔ 原始失败摘要（停在第几件 / 为什么 / 账在哪）才是用户唯一看得懂的东西; 回执
+    写不成只是「少一份可以重新生成的产物」。两条路径（执行 / 撤销）同口径 ——
+    只修 apply 那一半就是「管道只修了一半」（自查发现）。
+    返回写入异常, 没出错则 None。
+    """
+    try:
+        write_receipt(journal, data, stem)
+        return None
+    except (OSError, SystemExit, _UJ.JournalError) as e:
+        # ⛔ `str(e)` 不含 `__notes__` —— 残片位置就挂在那里。只打 str(e) 等于把
+        # round-4 L1 好不容易补上的「哪一份残片要处理」又弄丢了（独立复核 M-3 实证:
+        # 改前走裸 traceback 反而看得到, 改后看不到了）。
+        notes = "".join(f"\n  {n}" for n in getattr(e, "__notes__", []) or [])
+        print(f"⚠ 回执没写成: {e}{notes}（账本仍在 {journal.journal_path}）", file=sys.stderr)
+        return e
+
+
+def run_apply(vault: Path, args, applied_at: str) -> int:
+    preview, preview_sha = load_json_file(Path(args.preview), "preview")
+    expect = preview.get("vault_fingerprint")
+    fingerprint = compute_vault_fingerprint(vault)
+    if expect != fingerprint:
+        die(
+            f"这份 preview 不是为当前 vault 生成的 (指纹 {expect!r} ≠ {fingerprint!r}), "
+            f"拒绝拿着别处的盘点单动这里的文件"
+        )
+    decisions, decisions_sha = load_json_file(Path(args.decisions), "decisions")
+
+    work_dir = resolve_work_dir(vault, args.work_dir)
+    label = preview.get("label")
+    if isinstance(label, str) and label:
+        assert_work_dir_outside_inbox(vault, work_dir, label)
+
+    batch_id = compute_batch_id(fingerprint, preview_sha, decisions_sha)
+    journal = _UJ.BatchJournal(work_dir, batch_id, root=vault, fingerprint=fingerprint)
+
+    # ⛔ 只读地读既有账 —— 读不创建目录, 于是拒绝路径仍然零写
+    try:
+        rows = journal.read_rows()
+    except _UJ.JournalError as e:
+        die(str(e))  # ⛔ 账本损坏要给干净的拒绝, 不是裸 traceback（零写不受影响）
+    # ⛔ 采信历史记录之前先核绑定。只在撤销侧核是不够的: apply 会拿这些行判「哪几件
+    # 已完成」「落点归谁」, 一本不属于本 vault 的账能让它直接报完成 (round-3 H9)。
+    journal._assert_bound_to(rows, fingerprint)
+    plans = build_plans(vault, work_dir, preview, decisions, args.confirm_recycle, journal, rows)
+    check_destinations_free(plans, journal, rows)
+
+    # ── 至此全部守卫通过, 才允许碰 work-dir ──
+    journal.ensure_dirs()
+    # ⛔ 第二次读账同样要包起来。上面第一次 `read_rows()` 已经按「账本损坏要给干净的
+    # 拒绝, 不是裸 traceback」包过了, 而 `load()` 比它**多一步会写盘的**
+    # `seal_tail_if_needed()` —— 漏包的话, 这里的失败会以裸栈收场（全卡复核 L5）。
+    try:
+        rows = journal.load()
+    except _UJ.JournalError as e:
+        die(str(e))
+    latest = _UJ.latest_by_seq(rows)
+    done_rows = {k: r for k, r in latest.items() if r.get("state") == _UJ.STATE_DONE}
+    open_rows = {k: r for k, r in latest.items() if r.get("state") in (_UJ.STATE_PLANNED, _UJ.STATE_ACTING)}
+
+    results, completed, failed, created_dirs = [], 0, None, []
+    for plan in plans:
+        seq = plan["seq"]
+        if seq in done_rows:
+            verify_done(plan, done_rows[seq], vault, journal)
+            row = done_rows[seq]
+            # ⛔ 重跑时也要把旧账上的「本次新建的目录」汇总进来, 否则第二份回执会写成
+            # `created_dirs: []`, 把一条如实声明悄悄抹掉。
+            created_dirs += [d for d in (row.get("created_dirs") or []) if d not in created_dirs]
+            completed += 1
+            results.append(
+                {
+                    "index": seq,
+                    "stable_id": plan["stable_id"],
+                    "op": plan["action"],
+                    "src": plan["src_rel"],
+                    "dst": row.get("dst") or None,
+                    "provenance": row.get("provenance"),
+                    "state": "已完成(上一次)",
+                }
+            )
+            continue
+
+        entry = open_rows.get(seq)
+        try:
+            entry, sha_after, mtime_after, provenance, inode = _do_one(
+                plan, entry, journal, vault, batch_id, applied_at, created_dirs
+            )
+        except (OSError, SystemExit, _UJ.JournalError) as e:
+            failed = {
+                "index": seq,
+                "stable_id": plan["stable_id"],
+                "op": plan["action"],
+                "src": plan["src_rel"],
+                "dst": plan["dst_rel"] or None,
+                "reason": str(e),
+            }
+            break
+
+        completed += 1
+        results.append(
+            {
+                "index": seq,
+                "stable_id": plan["stable_id"],
+                "op": plan["action"],
+                "src": plan["src_rel"],
+                "dst": plan["dst_rel"] or None,
+                "provenance": provenance,
+                "state": "已完成",
+            }
+        )
+    data = {
+        "schema_version": SCHEMA_VERSION,
+        "generator": GENERATOR,
+        "mode": "apply",
+        "batch_id": batch_id,
+        "vault_fingerprint": fingerprint,
+        "applied_at_utc": applied_at,
+        "ok": failed is None,
+        "total": len(plans),
+        "completed": completed,
+        "journal": str(journal.journal_path),
+        "work_dir": str(work_dir),
+        "results": results,
+        "failed": failed,
+        "created_dirs": sorted(created_dirs),
+        "note": (
+            f"撤销这一批: inbox_apply.py --vault <V> --undo {journal.journal_path}"
+            "（撤销会把搬走的放回原路径并还原修改时间与权限; 复制/硬链出来的那几份移进 "
+            "recycle/undone/ 留痕, 不做物理删除; 本次新建的目录会留成空目录）"
+        ),
+    }
+    # ⛔ 回执写入自己再失败, 不能把**原始**失败摘要一起吞掉 (Codex round-5 MEDIUM-2)。
+    receipt_error = write_receipt_best_effort(journal, data, RECEIPT_STEM)
+
+    if failed is not None:
+        print(
+            f"✗ 停在第 {failed['index']} 件（{failed['src']}）: {failed['reason']}\n"
+            f"  已完成 {completed}/{len(plans)} 件; 账本 {journal.journal_path}\n"
+            f"  修好后用同一份 preview 与同一份拍板重跑, 只会补做没做完的。",
+            file=sys.stderr,
+        )
+        return 1
+    if receipt_error is not None:
+        # ⛔ 只说「回执没写成」用户无从判断材料动没动 —— 把实际完成数一起说出来。
+        print(f"  （材料已按拍板处理: {completed}/{len(plans)} 件 · 批次 {batch_id}）", file=sys.stderr)
+        return 1
+    print(f"✓ 清仓完成: {completed}/{len(plans)} 件 · 批次 {batch_id}")
+    print(f"  回执 {journal.batch_dir / (RECEIPT_STEM + '.md')}")
+    print(f"  后悔了就撤销: --undo {journal.journal_path}")
+    return 0
+
+
+def run_undo_mode(vault: Path, journal_arg: str, applied_at: str) -> int:
+    journal_path = Path(journal_arg)
+    if journal_path.is_symlink():
+        die(f"账本是一条 symlink, 拒绝跟随: {journal_path}")
+    if not journal_path.is_file():
+        die(f"账本不存在或不是普通文件: {journal_path}")
+    if journal_path.name != _UJ.JOURNAL_NAME:
+        # ⛔ 只取父目录再固定读 journal.jsonl 的话, 用户指错文件(比如 receipt.json)
+        # 也会照常撤销, 而他以为撤的是别的 (Codex round-4 M2)。
+        die(f"--undo 必须指向 {_UJ.JOURNAL_NAME}, 实得: {journal_path.name}")
+    # ⛔ 撤销侧也要有「写入面在 vault 内」这条边界。apply 侧有 `resolve_work_dir`
+    # (「--work-dir 必须落在 vault 内, 拒绝越界」), 撤销侧原先一条都没有 ——
+    # `--undo` 指到哪里, 回执 / `stale/` / 账目追加就落到哪里, 还会把那个目录里的
+    # 同名用户文件挪进新建的 `stale/`, 而 rc=0 报「✓ 已撤销 0 件」
+    # （全卡复核 BLOCKER-A 实测: 指向一个恰好叫 journal.jsonl 的用户笔记即可）。
+    # `BatchJournal(root=vault)` 只约束 `mkdir_chain`, 回执与账目追加都不走它。
+    journal_real = journal_path.resolve()
+    vault_real = Path(os.path.realpath(vault))
+    if vault_real not in journal_real.parents:
+        die(f"--undo 指向的账本必须落在 vault 内, 拒绝越界: {journal_path}")
+    batch_dir = journal_real.parent
+    fingerprint = compute_vault_fingerprint(vault)
+    journal = _UJ.BatchJournal(batch_dir.parent, batch_dir.name, root=vault, fingerprint=fingerprint)
+    # ⛔ **写这个目录的准入**, 必须在任何一次写盘之前。下面那两个 except 是按
+    # 异常类型分流的, 而「读得出行但读不懂」的账抛的是普通 JournalError, 会落进
+    # 会写回执的那一支 —— 于是 `--undo` 指到 vault 内任何一个恰好叫 journal.jsonl
+    # 的用户文件, 都会在那个目录留下 undo-receipt 并把同名文件挪进新建的 stale/
+    # (最终 HEAD 独立复核 H-B)。这里先纯读判一次, 不过就一个字节都不写。
+    try:
+        journal.assert_is_ours(fingerprint)
+    except (_UJ.JournalError, OSError) as e:
+        print(f"✗ {e}", file=sys.stderr)
+        print("  （没有往这本账所在的目录写任何东西）", file=sys.stderr)
+        return 1
+
+    try:
+        result = journal.undo(vault, fingerprint)
+    except _UJ.JournalNotOursError as e:
+        # ⛔ 这本账刚被判为「不是当前 vault 的 / 不是一本批次账」——那就**一个字节都
+        # 不许往它那儿写**。原先与其它失败共用一个 except, 于是拒绝路径会把对方批次
+        # 真实的 undo-receipt **零留痕**覆盖成「共 0 件 · 中途停下」, 并往对方账本追加
+        # 一条带**本 vault** 指纹的 receipt_sha 行（全卡复核 BLOCKER-B 实测）。
+        # `undo-receipt.md` 是用户唯一读得懂的「我的东西还原了没有」的凭证。
+        print(f"✗ {e}", file=sys.stderr)
+        print("  （没有往这本账所在的目录写任何东西）", file=sys.stderr)
+        return 1
+    except (_UJ.JournalError, SystemExit, OSError) as e:
+        # ⛔ 从异常上取「已经还原了几件」。硬编码 0 的话, 回执会告诉用户「什么都没撤」,
+        # 而盘上确实已经还原了 k 件 —— 执行侧那一半是对的（用真实 completed 计数）,
+        # 只有撤销这一半没有（全卡复核 M7）。
+        partial = list(getattr(e, "_uj_restored", None) or [])
+        data = {
+            "schema_version": SCHEMA_VERSION,
+            "generator": GENERATOR,
+            "mode": "undo",
+            "batch_id": journal.batch_id,
+            "applied_at_utc": applied_at,
+            "ok": False,
+            "total": len(partial),
+            "completed": len(partial),
+            "journal": str(journal.journal_path),
+            "work_dir": str(journal.work_dir),
+            "results": [
+                {
+                    "index": r["seq"],
+                    "stable_id": "",
+                    "op": r["op"],
+                    "src": r["action"],
+                    "dst": None,
+                    "provenance": None,
+                    "state": "已还原",
+                }
+                for r in partial
+            ],
+            "failed": {
+                "index": 0,
+                "stable_id": "",
+                "op": "undo",
+                "src": "",
+                "dst": None,
+                "reason": str(e),
+            },
+            "note": "撤销中途停下: 已还原的那几件记在账上了, 修好原因后再跑一次只会补做剩下的。",
+        }
+        write_receipt_best_effort(journal, data, UNDO_RECEIPT_STEM)
+        print(f"✗ {e}", file=sys.stderr)
+        print(f"  （已还原 {len(partial)} 件; 修好原因后再跑一次只会补做剩下的）", file=sys.stderr)
+        return 1
+
+    # ⛔ 「本次还原的」+「上一次已经撤掉的」一起进回执。只写本次的话, 第二次跑同一条
+    # `--undo`（幂等空操作）会把上一次那份回执原地换成「共 0 件 / results: []」,
+    # 把一条如实声明悄悄抹掉（全卡复核 M5）。执行侧对同一个坑做了回填, 见 run_apply。
+    prior = result.get("already_undone") or []
+    items = [
+        {
+            "index": r["seq"],
+            "stable_id": "",
+            "op": r["op"],
+            "src": r["action"],
+            "dst": None,
+            "provenance": None,
+            "state": "已还原" if r in result["restored"] else "上一次已撤销",
+        }
+        for r in list(result["restored"]) + list(prior)
+    ]
+    data = {
+        "schema_version": SCHEMA_VERSION,
+        "generator": GENERATOR,
+        "mode": "undo",
+        "batch_id": journal.batch_id,
+        "applied_at_utc": applied_at,
+        "ok": True,
+        "total": len(items),
+        "completed": len(result["restored"]),
+        "journal": str(journal.journal_path),
+        "work_dir": str(journal.work_dir),
+        "results": items,
+        "failed": None,
+        "created_dirs": result.get("dirs_left_behind") or [],
+        "dirs_retimed": result.get("dirs_retimed") or [],
+        "dirs_not_retimed": result.get("dirs_not_retimed") or [],
+        "note": "复制/硬链出来的那几份已移进 recycle/undone/ 留痕, 没有做任何物理删除。",
+    }
+    if write_receipt_best_effort(journal, data, UNDO_RECEIPT_STEM) is not None:
+        print(f"  （已撤销 {len(result['restored'])} 件 · 批次 {journal.batch_id}）", file=sys.stderr)
+        return 1
+    print(f"✓ 已撤销 {len(result['restored'])} 件 · 批次 {journal.batch_id}")
+    print(f"  回执 {journal.batch_dir / (UNDO_RECEIPT_STEM + '.md')}")
+    return 0
+
+
+def main() -> int:
+    ap = argparse.ArgumentParser(description="待处理清仓执行侧 (CARD-G5-7)")
+    ap.add_argument("--vault", required=True, help="vault 根目录")
+    ap.add_argument("--preview", default=None, help="G5-6 产出的 inbox-preview-<label>.json")
+    ap.add_argument("--decisions", default=None, help="用户逐条拍板 JSON")
+    ap.add_argument(
+        "--work-dir",
+        default=None,
+        help=f"备份/账本/回收目录 (缺省 <vault>/{DEFAULT_WORK_PARENT}/{DEFAULT_WORK_NAME})",
+    )
+    ap.add_argument(
+        "--confirm-recycle",
+        action="store_true",
+        help="整批允许「移入回收目录」; 仍需每条自带 confirm: true",
+    )
+    ap.add_argument("--undo", default=None, help="撤销模式: 指向某批次的 journal.jsonl")
+    ap.add_argument("--now", default=None, help="回执时刻 ISO-8601 (缺省当前 UTC)")
+    args = ap.parse_args()
+
+    applied_at = _UJ.utc_now_iso(_IP.parse_now(args.now) if args.now else None)
+    vault = resolve_vault(args.vault)
+
+    if args.undo is not None:
+        if args.preview or args.decisions:
+            die("--undo 与执行模式互斥, 请分两次跑")
+        return run_undo_mode(vault, args.undo, applied_at)
+
+    if not args.preview or not args.decisions:
+        die("执行模式必须同时给 --preview 与 --decisions（撤销请用 --undo）")
+    return run_apply(vault, args, applied_at)
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())

=== 附录A 结束 ===

---

## 附录 B：X1 三处生产改动 diff

用途：X1 三条开放面收口的独立复审对象（本轮兼作其独立复审；本卡不改 `inbox_preview.py`，对它的意见标注「移交」）。

以下 = `git --no-pager diff --no-color ac949f6f 69fce02c -- canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py` 的**完整输出**（未经删改）：

=== 附录B 开始 ===
diff --git a/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py b/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
index 6e1e776c..4fe44a1f 100644
--- a/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
+++ b/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
@@ -213,8 +213,9 @@ round-8 §四判定原措辞「全部声明、无未声明项」为 FAIL，理
      ⚠️ 与偏差 15 的 C3 侧裁决**刻意不一致**，这个不一致是被明确选择的，不是遗漏。
  19. **本卡交付时的其余已知缺陷（第五轮终审登记，未修）**：
      · 多行闭合 HTML 注释、frontmatter 里的 YAML 注释 —— 来源写在其中仍会被删；
-     · `splitlines()` 先于不可见归一执行，故 U+001D/001E/2028/2029 这类**行分隔**
-       类字符能绕过护栏（问题在处理顺序，不在码点表）；
+     · ~~`splitlines()` 先于不可见归一执行，故 U+001D/001E/2028/2029 这类**行分隔**
+       类字符能绕过护栏~~ —— **已修（R11-H1）**：分行改走 `md_splitlines()`
+       （`_MD_LINE_SPLIT_RE`，只认 \\n / \\r\\n / \\r），那些码点不再是行界；
      · 空键名编码 DOI/ISBN 的对抗构造。
      ⚠️ 五轮独立审查每一轮都抓出新构造 —— 这份清单是**当轮快照**，不是穷尽。
 ━━━━━━━━━━━━━━━━━━━━━ 与 board-split 的复用关系（卡片 (c)）━━━━━━━━━━━━━━━━━━━━━
@@ -831,6 +832,10 @@ def _classify_lines(text: str) -> list[tuple[str, bool]]:
 def dup_body(text: str) -> str:
     """**逐字保真**的正文形态 —— C4「精确重复」的唯一比对依据。
 
+    ⚠️ 「逐字保真」的口径以 `md_splitlines()` 切出的行为单位：R11-H1 已闭合 ——
+    行分隔符先按 `_MD_LINE_SPLIT_RE`（只认 \\n / \\r\\n / \\r）归一后再比对，
+    U+001D 之类不再被当行界改写。此前 `str.splitlines()` 把它们当行界，
+    `a<U+001D>b` 与 `a\\nb` 判等 —— 那时的「逐字」措辞比实际做到的宽。
     只做无语义的归一：丢标题行（围栏外）、行尾空白 rstrip、丢空行、NFC。
     ⛔ **不** `.strip()` 每行、**不**剥列表符号：那会抹掉代码缩进，让
     `if ok:` + 缩进 `run()` 与 `if ok:` + 顶格 `run()` 判成"逐字相等"，
@@ -876,7 +881,7 @@ def has_substantive_content(text: str) -> bool:
     """
     for ln, kind in _classify_lines_typed(text)[0]:
         if kind == "code":
-            if ln.strip():
+            if ln.strip(" \t"):
                 return True  # 围栏内容 = 真实材料（含长得像围栏的行）
             continue
         if kind == "fence":
@@ -927,7 +932,9 @@ def skeleton_note(text: str, size: int) -> str:
     rows = _classify_lines_typed(text)[0]
     headings = sum(1 for ln, k in rows if k == "text" and _HEADING_RE.match(ln))
     struct = sum(
-        1 for ln, k in rows if k == "text" and not _HEADING_RE.match(ln) and ln.strip()
+        1
+        for ln, k in rows
+        if k == "text" and not _HEADING_RE.match(ln) and ln.strip(" \t")
     )
     fences = sum(1 for _, k in rows if k == "fence")
     return (
@@ -1603,7 +1610,9 @@ def nominate(
     # ⚠️ 与①（未闭合注释）对称：①保护的是「不知道被吞了什么」，⑩保护的是
     # 「知道被吞了什么，但引擎没消费它」。此前只有①有保护，于是把唯一来源
     # 写在闭合注释里的文件 C3/C4 双出口全穿。只收**注释里有非空内容**的行。
-    commented_out = [ln for ln in stripped_comments if ln.strip()] + fm_comment_lines
+    commented_out = [
+        ln for ln in stripped_comments if ln.strip(" \t")
+    ] + fm_comment_lines
     # ⛔ 第九轮 HIGH（R9-H2）：文件名进了 item，但护栏一条都不看它 —— 于是
     # `ISBN_978-7-111-54742-6.md`、`DOI_10.1000_xyz.md` 这类**唯一来源写在文件名
     # 里**的材料，正文一撞上库内某份就被确定删除，文件名里的标识零留痕。

=== 附录B 结束 ===
