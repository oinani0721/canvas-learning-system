# CARD-G1-1 补审复核请求（BATCH-2026-09-18-第十五批 · 车道 card/p8-backend · round-2 · ZCode/GLM-5.3）

> 本文件由车道 `card-p8-backend` 生成并送 ZCode CLI `--mode build`（天然只读：Bash 与 Write 被阻断）。
> 你在 build 模式下**没有 Bash**，跑不了 git —— 因此本卡代码 diff 已**逐字内嵌**（见 ① 附录 A）。
> 前两轮 Codex 送审均因服务端配额返回 0 字节存档（`codex-review-CARD-G1-1.stderr` / `…-r1b.stderr`），本轮按协议 §2.4.2 走 ZCode 补审通道，绑同一审查 SHA。你的输出将原文存档为 `_bmad-output/审查/zcode-review-CARD-G1-1-r2.md`。

## ① 背景与最小读取面（写死：只读这些，不要漫游仓库）

- 树根（你的 cwd）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend`
- 分支 `card/p8-backend`；**审查绑定 SHA = `4a6524aa12f4c247245afda099bfa19d60dc510c`**（车道实测 `4a6524aa..HEAD` 对本卡两文件零 diff ⇒ 当前树内容 == 送审 SHA 内容）
- 本卡代码面 = 恰两个新文件、零修改既有文件：`scripts/annotation_search.py`（858 行）+ `backend/tests/unit/test_annotation_search.py`（999 行）；全文已内嵌于 **附录 A**（= `git --no-pager diff --no-color 86dc726c 4a6524aa -- backend/tests/unit/test_annotation_search.py scripts/annotation_search.py` 的逐字输出，1857 插入行，diff 文本 sha256 `2ff6ec4c…`）。
- 请读取（除附录外，其余用文件读取工具，路径相对树根；车道已逐一核对存在）：
  1. `_bmad-output/审查/evidence-g11/protocol-s5-annotation-search.patch` —— 协议条款 patch 全文（24 行）。
  2. `_bmad-output/审查/phase0a-annotation-truth/A01-source-boundary-draft.json` 第 42–108 行 —— 八条 source_roots 声明（私人 root 面的唯一输入）。
  3. `_bmad-output/审查/phase0a-annotation-truth/2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md` 第 126–144 行（§4 parser 契约：三层召回 / 至少覆盖清单 / 解析不变量）与第 82 行（repo-wide 容器面）。
  4. `_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md` 第 232–236 行 —— G1-1 原判据方向。
  5. `_bmad-output/审查/evidence-g11/` 下绑最终 HEAD 的裁判存档（**只看下列 final/close 版本**；同名更早时间戳是中间态快照）：
     - `close-judges-20260919T005044.txt`（零写 AST 门 / 只读 hash 门 / ruff / 地盘门 一次跑齐）
     - `negctl-1-20260919T004839.txt` / `negctl-2-20260919T004906.txt` / `negctl-3-20260919T004933.txt` / `negctl-4-20260919T004959.txt`（四段负控，每段带跑前跑后 sha 与变异 diff）
     - `gate-mutation-survey-20260919T004258.txt`（门的变异存活面：七个变异体原本存活）、`gate-mutation-kill-20260919T004432.txt`（补门后逐个复放，七杀七）
     - `annotation-search-final-20260919T003231.txt`（真数据小抄）、`clause-dogfood-20260919T003506.txt`（协议新条款按字面自跑两条路径）
     - `private-root-adversarial-20260918T231429.txt`（私人面对抗输入六段，含正控）
     - `patch-apply-check-final-20260919T003403.txt`、`unit-close-20260919T005033.txt`（tests/unit 目录级，绑最终代码 HEAD）
     - `internal-review-20260919T003425.txt`（车道自跑的内部对抗复核落盘 —— ⚠️ 它在被审文件改动期间进行、按协议 §1 **不作验收依据**，只供你复查当时的判断）
     - 补充：`behavior-20260919T001443.txt` 是中间态快照（33 passed）；点名套件在最终代码上的实测 = **78 passed / 0 skipped**（补审前重跑，随补审落档）。
  6. 主干树协议 §5 —— **内嵌于附录 B**（该文件在你的 cwd 之外、无法保证可达；patch 的基是它的早期 97 行版）。

**背景（本卡解决什么问题）**：294 条 `**User：` 与 348 条 `[!question]+` 形态的用户批注散在两千多个 Markdown 文件里，此前没有任何检索工具，开卡时靠人翻文件。本卡新增只读脚本，按关键词 / Story ID 把批注连同 `file:line`、来源类别、日期（带 `date_source`）一起列出来；私人 root（A01 声明）默认排除、fail-closed。它将支撑批次纪律「开卡必跑批注检索」（替代 A01/A02 全量考古）；本卡的协议条款 patch 就是不落工作树交付该纪律的那份。

**事后事实注记（本卡定稿后发生，供你校准；不作为本卡缺陷）**：主干树协议在本卡定稿后由主 session 追加 §2.4/§2.4.1/§2.4.2（feature 树 commit `90ff4570`，2026-09-19 15:18；现 140 行 / sha256 `20aad922…`）。patch 的基 = 追加前 97 行版（`accbe747…`）。补审前车道只读复测：patch 对当前 140 行版 `git apply --check` 仍 rc=0、协议文件 sha 前后逐字同。请仍按 patch 自身评估。

## ①附录 A：本卡代码 diff（86dc726c → 4a6524aa · 两新文件全文 · 逐字内嵌，含被审源码原文；文中个别用词出自被审代码自身，非本请求措辞）

````diff
diff --git a/backend/tests/unit/test_annotation_search.py b/backend/tests/unit/test_annotation_search.py
new file mode 100644
index 00000000..e125fba5
--- /dev/null
+++ b/backend/tests/unit/test_annotation_search.py
@@ -0,0 +1,999 @@
+"""CARD-G1-1 — `scripts/annotation_search.py` 真数据行为门。
+
+DD-03：不 mock 文件系统、不 monkeypatch 目标目录。tmp fixture 用 `tmp_path` 搭**真**
+目录真文件；真数据用例直接读仓内真 `_bmad-output/` 与真 A01。
+
+只读是本脚本的核心性质，所以 `test_readonly_*` 两条在跑前跑后各算一次树摘要并逐字比，
+摘要排除本卡自己的落档目录 `审查/evidence-g11/` 与 `__pycache__`（否则裁判落档会让
+「前后逐字同」假红——这是判据自伤，不是脚本写了文件）。
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+import subprocess
+import sys
+from pathlib import Path
+
+import pytest
+
+REPO_ROOT = Path(__file__).resolve().parents[3]
+sys.path.insert(0, str(REPO_ROOT / "scripts"))
+
+import annotation_search as mod  # noqa: E402
+
+REAL_BMAD = REPO_ROOT / "_bmad-output"
+REAL_A01 = REAL_BMAD / "审查" / "phase0a-annotation-truth" / "A01-source-boundary-draft.json"
+
+ANCHOR_PLAN = "_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md"
+ANCHOR_PLAN_LINE = 494
+ANCHOR_CARD = "_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md"
+ANCHOR_CARD_LINE = 163
+
+# 与真 A01 同 root_id / privacy_ceiling 的最小副本（8 root）。fixture 自带，
+# 这样「私人 root 从 A01 算出来」这件事在 fixture 上也是真的被算出来的。
+MINIMAL_A01 = {
+    "schema_version": "2.0-draft-test-copy",
+    "source_roots": [
+        {
+            "root_id": "ROOT-REPO-CURRENT",
+            "privacy_ceiling": "P2-personal",
+            "proposed_action": "include-current-repo-after-ownership-classification",
+        },
+        {
+            "root_id": "ROOT-GIT-REFS",
+            "privacy_ceiling": "P2-personal",
+            "proposed_action": "include-history-deduplicated-against-live-planes",
+        },
+        {
+            "root_id": "ROOT-ANCHORED-PRD",
+            "privacy_ceiling": "P1-project-internal",
+            "proposed_action": "include-private-locator-public-commitment",
+        },
+        {
+            "root_id": "ROOT-ACTIVE-VAULT",
+            "privacy_ceiling": "P3-high-sensitive",
+            "proposed_action": "private-layer-only-after-authorization",
+        },
+        {
+            "root_id": "ROOT-EXTERNAL-PRIVATE-01",
+            "privacy_ceiling": "P4-secret",
+            "proposed_action": "private-layer-only-per-item-redaction-or-waiver",
+        },
+        {
+            "root_id": "ROOT-TRANSCRIPTS",
+            "privacy_ceiling": "P3-high-sensitive",
+            "proposed_action": "pending-user-export-and-authorization",
+        },
+        {
+            "root_id": "ROOT-GRAPHITI-MEMORY",
+            "privacy_ceiling": "P3-high-sensitive",
+            "proposed_action": "discovery-hint-only",
+        },
+        {
+            "root_id": "ROOT-OTHER-BACKUPS",
+            "privacy_ceiling": "P4-secret",
+            "proposed_action": "pending-root-enumeration-and-authorization",
+        },
+    ],
+}
+
+
+def write_a01(base: Path, payload=None) -> Path:
+    path = base / "a01.json"
+    path.write_text(json.dumps(payload if payload is not None else MINIMAL_A01, ensure_ascii=False), encoding="utf-8")
+    return path
+
+
+def tree_digest(root: Path, skip_parts=()) -> str:
+    """逐文件 sha256(相对路径 + 内容) 再总 sha —— 对内容与文件集合都敏感。"""
+    digest = hashlib.sha256()
+    rows = []
+    for dirpath, dirnames, filenames in os.walk(root):
+        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
+        for name in sorted(filenames):
+            full = os.path.join(dirpath, name)
+            rel = os.path.relpath(full, root)
+            parts = rel.split(os.sep)
+            if any(part in parts for part in skip_parts):
+                continue
+            rows.append((rel, full))
+    for rel, full in sorted(rows):
+        digest.update(rel.encode("utf-8", "surrogateescape"))
+        with open(full, "rb") as handle:
+            digest.update(hashlib.sha256(handle.read()).digest())
+    return digest.hexdigest()
+
+
+@pytest.fixture()
+def six_forms(tmp_path: Path):
+    """六形态各一份：单行粗体 / User2 换行续写 / ASCII 冒号 / blockquote callout /
+    行内 callout / 空槽。每份单独一个文件，行号可精确断言。"""
+    base = tmp_path / "tree"
+    base.mkdir()
+    (base / "f1-single.md").write_text("# 标题\n\n**User：单行粗体批注 kw-alpha**\n", encoding="utf-8")
+    (base / "f2-user2.md").write_text(
+        "前言\n\n**User2：**\n续写正文第一行 kw-alpha\n续写正文第二行\n\n尾巴\n", encoding="utf-8"
+    )
+    (base / "f3-ascii.md").write_text("抬头\n**User: ASCII 冒号批注 kw-alpha**\n", encoding="utf-8")
+    (base / "f4-blockquote.md").write_text(
+        "引子\n\n> [!question]+ 这是 blockquote 提问 kw-alpha\n> 第二行正文\n\n完\n", encoding="utf-8"
+    )
+    (base / "f5-inline.md").write_text("段落开头 [!error]+ 行内告警 kw-alpha 收尾\n", encoding="utf-8")
+    (base / "f6-empty.md").write_text("模板\n\n**User：**\n\n下一段\n", encoding="utf-8")
+    return base, write_a01(tmp_path)
+
+
+def run_cli(argv, capsys):
+    code = mod.main(argv)
+    captured = capsys.readouterr()
+    return code, captured.out, captured.err
+
+
+# --------------------------------------------------------------------------
+# (g)① 六形态 + 空槽
+# --------------------------------------------------------------------------
+def test_six_forms_hit_first_five_with_exact_lines(six_forms, capsys):
+    base, a01 = six_forms
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-alpha", "--json"], capsys)
+    assert code == 0, err
+    records = json.loads(out)
+    got = {(os.path.basename(r["path"]), r["line"]): r["marker"] for r in records}
+    assert got == {
+        ("f1-single.md", 3): "**User：",
+        ("f2-user2.md", 3): "**User2：",
+        ("f3-ascii.md", 2): "**User:",
+        ("f4-blockquote.md", 3): "[!question]+",
+        ("f5-inline.md", 1): "[!error]+",
+    }
+    assert len(set(got.values())) == 5, "五个形态的 marker 名必须各异"
+    assert "f6-empty.md" not in out, "空槽默认不列"
+    assert "empty=1" in err
+
+
+def test_empty_slot_listed_only_with_include_empty(six_forms, capsys):
+    base, a01 = six_forms
+    code, out, err = run_cli(
+        ["--root", str(base), "--a01", str(a01), "--keyword", "User", "--include-empty", "--json"], capsys
+    )
+    assert code == 0, err
+    records = json.loads(out)
+    empties = [r for r in records if r["empty"]]
+    assert [os.path.basename(r["path"]) for r in empties] == ["f6-empty.md"]
+    assert empties[0]["line"] == 3
+    assert "empty=1" in err
+
+
+def test_user2_continuation_is_captured_in_excerpt(six_forms, capsys):
+    base, a01 = six_forms
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "续写正文第二行", "--json"], capsys)
+    assert code == 0
+    records = json.loads(out)
+    assert len(records) == 1
+    assert records[0]["excerpt"].split("\n") == ["**User2：**", "续写正文第一行 kw-alpha", "续写正文第二行"]
+
+
+# --------------------------------------------------------------------------
+# (g)② --story
+# --------------------------------------------------------------------------
+@pytest.fixture()
+def story_tree(tmp_path: Path):
+    base = tmp_path / "stories"
+    base.mkdir()
+    (base / "CARD-G1-1-in-path.md").write_text("**User：路径里带卡号的批注**\n", encoding="utf-8")
+    (base / "in-body.md").write_text("**User：正文里写了 CARD-G1-1 的批注**\n", encoding="utf-8")
+    (base / "neither.md").write_text("**User：既不在路径也不在正文**\n", encoding="utf-8")
+    return base, write_a01(tmp_path)
+
+
+def test_story_matches_path_or_body_only(story_tree, capsys):
+    base, a01 = story_tree
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--story", "CARD-G1-1", "--json"], capsys)
+    assert code == 0
+    names = sorted(os.path.basename(r["path"]) for r in json.loads(out))
+    assert names == ["CARD-G1-1-in-path.md", "in-body.md"]
+
+
+def test_story_ids_backfilled(story_tree, capsys):
+    """`story_ids` 是**词元抽取**，与 `--story` 的**子串包含**不是同一口径。
+
+    路径 `CARD-G1-1-in-path.md` 抽出的词元就是 `CARD-G1-1-in-path`（卡号后缀本来就
+    可以任意长，`CARD-PYRIGHT-TAIL-BEHAVIOR` 即是），不是 `CARD-G1-1`；两者共有的
+    短形态 `G1-1` 才是两边都抽得到的。断言写实测值，不写「应该抽成什么」。
+    """
+    base, a01 = story_tree
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--story", "CARD-G1-1", "--json"], capsys)
+    assert code == 0
+    by_name = {os.path.basename(r["path"]): r["story_ids"] for r in json.loads(out)}
+    assert by_name["CARD-G1-1-in-path.md"] == ["CARD-G1-1-in-path", "G1-1"]
+    assert by_name["in-body.md"] == ["CARD-G1-1", "G1-1"]
+
+
+def test_story_substring_match_can_overreach_longer_ids(story_tree, capsys):
+    """如实 pin 子串包含的代价：`--story CARD-G1-1` 会连 `CARD-G1-1-in-path` 一起命中。
+
+    这是为了让 `--story G1-1` 能找回 `CARD-G1-1` 而**选**的口径（卡文 §二.8 就同时传
+    `--story CARD-G1-1 --story G1-1`），不是漏判。
+    """
+    base, a01 = story_tree
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--story", "G1-1", "--json"], capsys)
+    assert code == 0
+    names = sorted(os.path.basename(r["path"]) for r in json.loads(out))
+    assert names == ["CARD-G1-1-in-path.md", "in-body.md"]
+
+
+def test_story_matching_is_case_sensitive(story_tree, capsys):
+    base, a01 = story_tree
+    code, _, _ = run_cli(["--root", str(base), "--a01", str(a01), "--story", "card-g1-1", "--json"], capsys)
+    assert code == 1
+
+
+# --------------------------------------------------------------------------
+# (g)③ 私人 root
+# --------------------------------------------------------------------------
+@pytest.fixture()
+def vault_tree(tmp_path: Path):
+    base = tmp_path / "repo"
+    (base / "canvas-vault").mkdir(parents=True)
+    (base / "canvas-vault" / "x.md").write_text("**User：私人 vault 里的批注 kw-private**\n", encoding="utf-8")
+    (base / "public.md").write_text("**User：公开面的批注 kw-public**\n", encoding="utf-8")
+    return base, write_a01(tmp_path)
+
+
+def test_private_root_excluded_by_default(vault_tree, capsys):
+    base, a01 = vault_tree
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-private", "--json"], capsys)
+    # 命中数断言放在最前：负控①（私人 root 判定恒 False）要红在「返回了本不该返回的
+    # 批注」上，而不是先被一条 rc 断言拦下——rc 只是后果，泄漏才是缺陷本身。
+    assert json.loads(out) == [], "私人 root 的批注默认必须一条都不返回"
+    assert "excluded_private_roots=['ROOT-ACTIVE-VAULT'" in err
+    assert "canvas-vault" in err  # pruned_private_paths 显式汇总，不静默
+    assert code == 1
+
+
+def test_public_sibling_still_found(vault_tree, capsys):
+    base, a01 = vault_tree
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-public", "--json"], capsys)
+    assert code == 0
+    assert len(json.loads(out)) == 1
+
+
+def test_include_private_opens_the_vault(vault_tree, capsys):
+    base, a01 = vault_tree
+    code, out, err = run_cli(
+        ["--root", str(base), "--a01", str(a01), "--keyword", "kw-private", "--include-private", "--json"], capsys
+    )
+    assert code == 0
+    records = json.loads(out)
+    assert len(records) == 1
+    assert os.path.basename(records[0]["path"]) == "x.md"
+    assert "excluded_private_roots=[]" in err
+
+
+def test_root_pointing_into_private_root_is_refused(vault_tree, capsys):
+    base, a01 = vault_tree
+    code, _, err = run_cli(["--root", str(base / "canvas-vault"), "--a01", str(a01), "--keyword", "kw-private"], capsys)
+    assert code == 2
+    assert "ROOT-ACTIVE-VAULT" in err
+
+
+def test_symlink_into_private_root_is_refused(vault_tree, capsys):
+    base, a01 = vault_tree
+    link = base.parent / "sneaky-link"
+    os.symlink(base / "canvas-vault", link)
+    code, _, err = run_cli(["--root", str(link), "--a01", str(a01), "--keyword", "kw-private"], capsys)
+    assert code == 2, "realpath 口径：软链指进私人 root 同样拒扫"
+    assert "ROOT-ACTIVE-VAULT" in err
+
+
+@pytest.mark.parametrize("dirname", ["Canvas-Vault", "CANVAS-VAULT", "canvas-Vault"])
+def test_case_variant_private_dir_is_pruned(dirname, tmp_path: Path, capsys):
+    """大小写变体的 canvas-vault 同样不得泄漏。
+
+    2026-09-19 实测：`os.path.realpath` 不归一大小写，而本机 macOS APFS 大小写不敏感
+    ⇒ 未 casefold 前 `Canvas-Vault/` 下的批注被原样返回。这条是那次泄漏的回归门。
+    """
+    base = tmp_path / "repo"
+    (base / dirname).mkdir(parents=True)
+    (base / dirname / "x.md").write_text("**User：大小写变体私人内容 kw-ci**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-ci", "--json"], capsys)
+    assert json.loads(out) == [], f"{dirname} 下的私人批注不得返回"
+    assert "ROOT-ACTIVE-VAULT" in err
+    assert code == 1
+
+
+def test_case_variant_root_is_refused(tmp_path: Path, capsys):
+    base = tmp_path / "repo"
+    (base / "Canvas-Vault").mkdir(parents=True)
+    (base / "Canvas-Vault" / "x.md").write_text("**User：kw-ci**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, _, err = run_cli(["--root", str(base / "Canvas-Vault"), "--a01", str(a01), "--keyword", "kw-ci"], capsys)
+    assert code == 2
+    assert "ROOT-ACTIVE-VAULT" in err
+
+
+def test_blockquote_annotation_does_not_swallow_next_speaker(tmp_path: Path, capsys):
+    """引用块批注区里，User 块不得吃到下一位发言人。
+
+    真数据形态（研究/ 下 2 处实测）：`> **User：**` / `>` / `> **Claude（日期）：** …`。
+    引用块里的「空行」是一个光秃秃的 `>`，str.strip() 判不出来。
+    """
+    base = tmp_path / "bq"
+    base.mkdir()
+    (base / "a.md").write_text(
+        "> **User：**\n> 我的原话 kw-mine\n>\n> **Claude（2026-09-19）：** 回复 kw-claude\n",
+        encoding="utf-8",
+    )
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-mine", "--json"], capsys)
+    assert code == 0
+    records = json.loads(out)
+    assert len(records) == 1
+    assert "kw-claude" not in records[0]["excerpt"], "Claude 的回复不是「用户说过的话」"
+    assert records[0]["excerpt"].split("\n") == ["> **User：**", "> 我的原话 kw-mine"]
+
+
+def test_html_comment_hits_are_labelled_not_dropped(tmp_path: Path, capsys):
+    """HTML 注释里的 marker 照常召回但带 in_html_comment 标注（契约 :134/:139）。
+
+    真数据 26 行 / 6 文件落在注释区内，样例是被注释掉的填写模板。
+    """
+    base = tmp_path / "html"
+    base.mkdir()
+    (base / "a.md").write_text(
+        "正文\n\n<!--\n> [!error]+ 注释掉的模板 kw-html\n-->\n\n**User：注释外的 kw-html**\n",
+        encoding="utf-8",
+    )
+    a01 = write_a01(tmp_path)
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-html", "--json"], capsys)
+    assert code == 0
+    by_line = {r["line"]: r["in_html_comment"] for r in json.loads(out)}
+    assert by_line == {4: True, 7: False}
+    assert "html_comment=1" in err
+
+
+def test_unknown_privacy_ceiling_is_treated_as_private(tmp_path: Path, capsys):
+    """认不出的 privacy_ceiling 按私人处理（fail-closed），并在 stderr 说出来。"""
+    payload = {"source_roots": [dict(r) for r in MINIMAL_A01["source_roots"]]}
+    for entry in payload["source_roots"]:
+        if entry["root_id"] == "ROOT-REPO-CURRENT":
+            entry["privacy_ceiling"] = "P5-brand-new-level"
+    a01 = write_a01(tmp_path, payload)
+    private, _ = mod.load_private_root_ids(str(a01))
+    assert "ROOT-REPO-CURRENT" in private
+
+
+def test_privacy_ceiling_case_and_whitespace_are_normalized(tmp_path: Path):
+    """`  p3-HIGH-sensitive ` 这种写法仍须判成私人，不能因大小写/空白漏判。"""
+    payload = {"source_roots": [dict(r) for r in MINIMAL_A01["source_roots"]]}
+    for entry in payload["source_roots"]:
+        if entry["root_id"] == "ROOT-ACTIVE-VAULT":
+            entry["privacy_ceiling"] = "  P3-HIGH-Sensitive "
+    a01 = write_a01(tmp_path, payload)
+    private, _ = mod.load_private_root_ids(str(a01))
+    assert "ROOT-ACTIVE-VAULT" in private
+
+
+def test_summary_separates_enforced_roots_from_unmapped_ones(capsys):
+    """汇总行只把**真有路径可拦**的 root 报成已排除；其余另起一行如实说明。
+
+    A01 算出 6 个私人 root，仓内只有 ROOT-ACTIVE-VAULT / ROOT-ANCHORED-PRD 有落地路径。
+    把另外 4 个（含两个 P4-secret）一并写进 excluded_ 会读成「它们也被拦住了」。
+    """
+    code, _, err = run_cli(["--keyword", "codex", "--a01", str(REAL_A01)], capsys)
+    assert code == 0
+    assert "excluded_private_roots=['ROOT-ACTIVE-VAULT', 'ROOT-ANCHORED-PRD']" in err
+    assert "private_roots_without_path=" in err
+    for unmapped in ("ROOT-TRANSCRIPTS", "ROOT-GRAPHITI-MEMORY", "ROOT-OTHER-BACKUPS", "ROOT-EXTERNAL-PRIVATE-01"):
+        assert unmapped in err
+
+
+def test_unwalkable_directory_is_reported_not_silently_dropped(tmp_path: Path, capsys):
+    """列不出来的目录进 unwalkable 桶并报数，不静默缩小分母（契约 :142 口径）。"""
+    base = tmp_path / "walk"
+    (base / "ok").mkdir(parents=True)
+    (base / "ok" / "a.md").write_text("**User：可读的 kw-walk**\n", encoding="utf-8")
+    locked = base / "locked"
+    locked.mkdir()
+    (locked / "b.md").write_text("**User：读不到的 kw-walk**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    os.chmod(locked, 0o000)
+    try:
+        code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-walk", "--json"], capsys)
+    finally:
+        os.chmod(locked, 0o755)
+    assert code == 0
+    assert len(json.loads(out)) == 1
+    assert "unwalkable=1" in err
+    assert "unwalkable_dirs=" in err
+
+
+def test_git_env_is_scrubbed_of_git_variables():
+    """给 git 子进程的环境必须剃掉全部 GIT_*。
+
+    GIT_DIR 会让它回答另一个仓库；GIT_TRACE* 会让它自己往文件里写——后者正好绕过
+    零写 AST 门（门看得见 Python 源码的写调用，看不见子进程）。
+    """
+    env = mod.git_env()
+    leaked = [k for k in env if k.startswith("GIT_") and k not in {"GIT_TERMINAL_PROMPT", "GIT_OPTIONAL_LOCKS"}]
+    assert leaked == [], f"未剃掉的 GIT_* 变量：{leaked}"
+    assert env["GIT_OPTIONAL_LOCKS"] == "0"
+    assert env["GIT_TERMINAL_PROMPT"] == "0"
+
+
+def test_private_lookup_keys_are_prefolded():
+    """两张查找表的键必须已经是 fold_path 形态，否则大小写变体会静默漏判。"""
+    for key in list(mod.PRIVATE_COMPONENT_ROOTS) + list(mod.PRIVATE_BASENAME_ROOTS):
+        assert key == mod.fold_path(key), f"查找表键 {key!r} 未按 fold_path 归一"
+
+
+def test_nested_private_dir_is_pruned(tmp_path: Path, capsys):
+    """前缀比较够不到的位置（<root>/sub/canvas-vault/）由组件形态安全网兜住。"""
+    base = tmp_path / "repo"
+    (base / "sub" / "canvas-vault").mkdir(parents=True)
+    (base / "sub" / "canvas-vault" / "deep.md").write_text("**User：深层私人批注 kw-deep**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-deep", "--json"], capsys)
+    assert code == 1
+    assert json.loads(out) == []
+    assert "ROOT-ACTIVE-VAULT" in err
+
+
+# --------------------------------------------------------------------------
+# (g)④ A01 fail-closed
+# --------------------------------------------------------------------------
+def test_a01_missing_is_fail_closed(tmp_path: Path, capsys):
+    base = tmp_path / "t"
+    base.mkdir()
+    (base / "a.md").write_text("**User：随便 kw**\n", encoding="utf-8")
+    code, _, err = run_cli(["--root", str(base), "--a01", str(tmp_path / "nope.json"), "--keyword", "kw"], capsys)
+    assert code == 2
+    assert "A01" in err
+
+
+def test_a01_without_source_roots_is_fail_closed(tmp_path: Path, capsys):
+    base = tmp_path / "t"
+    base.mkdir()
+    (base / "a.md").write_text("**User：随便 kw**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path, {"schema_version": "x"})
+    code, _, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw"], capsys)
+    assert code == 2
+    assert "source_roots" in err
+
+
+def test_a01_entry_missing_privacy_ceiling_is_fail_closed(tmp_path: Path, capsys):
+    base = tmp_path / "t"
+    base.mkdir()
+    (base / "a.md").write_text("**User：随便 kw**\n", encoding="utf-8")
+    broken = {"source_roots": [{"root_id": "ROOT-ACTIVE-VAULT"}]}
+    a01 = write_a01(tmp_path, broken)
+    code, _, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw"], capsys)
+    assert code == 2
+    assert "privacy_ceiling" in err
+
+
+# --------------------------------------------------------------------------
+# (g)⑤ 真数据锚
+# --------------------------------------------------------------------------
+def test_real_anchor_plan_line_494(capsys):
+    code, out, _ = run_cli(["--keyword", "codex", "--a01", str(REAL_A01), "--json"], capsys)
+    assert code == 0
+    hits = [r for r in json.loads(out) if r["path"] == ANCHOR_PLAN and r["line"] == ANCHOR_PLAN_LINE]
+    assert len(hits) == 1, f"计划书:{ANCHOR_PLAN_LINE} 必命中"
+    record = hits[0]
+    assert record["category"] == "审查"
+    assert record["date"] == "2026-08-20"
+    assert record["date_source"] == "filename"
+    assert record["marker"].startswith("**User")
+
+
+def test_real_anchor_card_line_163(capsys):
+    code, out, _ = run_cli(["--keyword", "anki", "--a01", str(REAL_A01), "--json"], capsys)
+    assert code == 0
+    hits = [r for r in json.loads(out) if r["path"] == ANCHOR_CARD and r["line"] == ANCHOR_CARD_LINE]
+    assert len(hits) == 1, f"08-25 卡文:{ANCHOR_CARD_LINE} 必命中"
+    assert hits[0]["category"] == "goal-cards"
+    assert hits[0]["date"] == "2026-08-25"
+
+
+@pytest.mark.parametrize("keyword", ["FSRS", "跨vault", "README"])
+def test_real_themes_are_non_empty(keyword, capsys):
+    code, out, _ = run_cli(["--keyword", keyword, "--a01", str(REAL_A01), "--json"], capsys)
+    assert code == 0
+    assert len(json.loads(out)) >= 1, f"主题 {keyword} 在真 _bmad-output 上应至少 1 块"
+
+
+def test_real_run_excludes_private_roots_and_reports_unreadable(capsys):
+    code, _, err = run_cli(["--keyword", "codex", "--a01", str(REAL_A01), "--json"], capsys)
+    assert code == 0
+    assert "excluded_private_roots=['ROOT-ACTIVE-VAULT'" in err
+    assert "unreadable=" in err
+
+
+# --------------------------------------------------------------------------
+# (g)⑥ 只读
+# --------------------------------------------------------------------------
+def test_readonly_on_fixture_tree(six_forms, capsys):
+    base, a01 = six_forms
+    before = tree_digest(base)
+    run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-alpha"], capsys)
+    assert tree_digest(base) == before
+
+
+def test_readonly_on_real_bmad_output(capsys):
+    skip = ("evidence-g11",)
+    before = tree_digest(REAL_BMAD, skip_parts=skip)
+    run_cli(["--keyword", "codex", "--story", "CARD-G1-1", "--a01", str(REAL_A01)], capsys)
+    assert tree_digest(REAL_BMAD, skip_parts=skip) == before
+
+
+# --------------------------------------------------------------------------
+# (g)⑦ 确定性
+# --------------------------------------------------------------------------
+def test_json_output_is_byte_identical_across_runs(six_forms, capsys):
+    base, a01 = six_forms
+    argv = ["--root", str(base), "--a01", str(a01), "--keyword", "kw-alpha", "--json"]
+    _, first, _ = run_cli(argv, capsys)
+    _, second, _ = run_cli(argv, capsys)
+    assert first == second
+
+
+# --------------------------------------------------------------------------
+# (g)⑧ 不可读桶
+# --------------------------------------------------------------------------
+def test_unreadable_files_counted_not_silently_zero(tmp_path: Path, capsys):
+    base = tmp_path / "bad"
+    base.mkdir()
+    (base / "ok.md").write_text("**User：正常批注 kw-ok**\n", encoding="utf-8")
+    (base / "nul.md").write_bytes(b"**User: has NUL kw-ok**\n\x00tail\n")
+    (base / "latin.md").write_bytes(b"**User: bad utf8 kw-ok \xff\xfe**\n")
+    a01 = write_a01(tmp_path)
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-ok", "--json"], capsys)
+    assert code == 0
+    assert "unreadable=2" in err
+    names = [os.path.basename(r["path"]) for r in json.loads(out)]
+    assert names == ["ok.md"]
+
+
+# --------------------------------------------------------------------------
+# (g)⑨ 日期优先级
+# --------------------------------------------------------------------------
+def test_date_source_priority(tmp_path: Path, capsys):
+    base = tmp_path / "dates"
+    base.mkdir()
+    (base / "2026-01-02-both.md").write_text(
+        "---\ndate: 2025-12-31\n---\n\n**User：两者都有 kw-date**\n", encoding="utf-8"
+    )
+    (base / "2026-03-04-only-name.md").write_text("**User：只有文件名 kw-date**\n", encoding="utf-8")
+    (base / "plain.md").write_text("**User：都没有 kw-date**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-date", "--json"], capsys)
+    assert code == 0
+    by_name = {os.path.basename(r["path"]): (r["date"], r["date_source"]) for r in json.loads(out)}
+    assert by_name["2026-01-02-both.md"] == ("2025-12-31", "frontmatter")
+    assert by_name["2026-03-04-only-name.md"] == ("2026-03-04", "filename")
+    assert by_name["plain.md"] == ("unknown", "unknown")
+
+
+# --------------------------------------------------------------------------
+# (g)⑩ 退出码 + 其余 CLI
+# --------------------------------------------------------------------------
+def test_date_source_git_on_a_real_git_repo(tmp_path: Path, capsys):
+    """git 档必须有自己的门——它是真数据上占比最大的一档（实测 92/251 ≈ 37%）。
+
+    DD-03：不 mock `git_commit_date`，而是在 tmp_path 里 `git init` 建一个**真**仓库并
+    真提交一次。文件名不带日期、正文无 frontmatter ⇒ 日期只能落到 git 这一档。
+    """
+    repo = tmp_path / "repo"
+    repo.mkdir()
+    md = repo / "plain-name.md"
+    md.write_text("**User：只有 git 能给出日期 kw-git**\n", encoding="utf-8")
+    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"]
+    subprocess.run([*git, "init", "-q"], cwd=repo, check=True, capture_output=True)
+    subprocess.run([*git, "add", "plain-name.md"], cwd=repo, check=True, capture_output=True)
+    subprocess.run(
+        [*git, "commit", "-q", "-m", "seed", "--date=2021-03-04T00:00:00"],
+        cwd=repo,
+        check=True,
+        capture_output=True,
+        env={**os.environ, "GIT_COMMITTER_DATE": "2021-03-04T00:00:00"},
+    )
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(repo), "--a01", str(a01), "--keyword", "kw-git", "--json"], capsys)
+    assert code == 0
+    records = json.loads(out)
+    assert len(records) == 1
+    assert records[0]["date_source"] == "git", "该文件只有 git 一档能给出日期"
+    assert records[0]["date"] == "2021-03-04"
+
+
+def test_unclosed_frontmatter_is_not_frontmatter(tmp_path: Path, capsys):
+    """首行 `---` 若没有收尾，就是正文分隔线——不得把正文里的 date: 当成 frontmatter。
+
+    2026-09-19 实测的回归：无下界扫描会把**围栏代码块里**的 `date: 1999-01-01`
+    报成 `date_source=frontmatter`，即一个看起来权威的错日期。
+    """
+    base = tmp_path / "fm"
+    base.mkdir()
+    (base / "2026-05-06-thematic-break.md").write_text(
+        "---\n# 标题\n\n```yaml\ndate: 1999-01-01\n```\n\n**User：这条是 2026 年写的 kw-fm**\n",
+        encoding="utf-8",
+    )
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-fm", "--json"], capsys)
+    assert code == 0
+    record = json.loads(out)[0]
+    assert record["date_source"] == "filename"
+    assert record["date"] == "2026-05-06"
+
+
+@pytest.mark.parametrize(
+    "filename,expected_date,expected_source",
+    [
+        ("ticket-1234-56-7890.md", None, None),  # 月 56 日 78 —— 不是日期，不得抠出来
+        ("2026-02-30-impossible.md", None, None),  # 形状合法但日历上不存在
+        ("2026-02-28-real.md", "2026-02-28", "filename"),  # 控制组：真日期必须认出来
+    ],
+)
+def test_filename_date_must_be_a_real_calendar_date(filename, expected_date, expected_source, tmp_path, capsys):
+    """报一个假日期比报 unknown 更坏：假值会被当事实引用，还会挡掉 git 那一档。"""
+    base = tmp_path / "dates2"
+    base.mkdir()
+    (base / filename).write_text("**User：正文 kw-cal**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-cal", "--json"], capsys)
+    assert code == 0
+    record = json.loads(out)[0]
+    if expected_date is None:
+        assert record["date_source"] != "filename", f"{filename} 不该被当成带日期的文件名"
+    else:
+        assert (record["date"], record["date_source"]) == (expected_date, expected_source)
+
+
+def test_zero_hits_exits_1(six_forms, capsys):
+    base, a01 = six_forms
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "绝不存在的词-zzz", "--json"], capsys)
+    assert code == 1
+    assert json.loads(out) == []
+
+
+def test_no_keyword_and_no_story_exits_2(capsys):
+    code, _, err = run_cli(["--root", str(REAL_BMAD)], capsys)
+    assert code == 2
+    assert "--keyword" in err
+
+
+def test_category_filter(capsys):
+    code, out, _ = run_cli(["--keyword", "anki", "--a01", str(REAL_A01), "--category", "goal-cards", "--json"], capsys)
+    assert code == 0
+    assert {r["category"] for r in json.loads(out)} == {"goal-cards"}
+
+
+def test_context_limit_caps_continuation_lines(six_forms, capsys):
+    base, a01 = six_forms
+    code, out, _ = run_cli(
+        ["--root", str(base), "--a01", str(a01), "--keyword", "kw-alpha", "--context", "1", "--json"], capsys
+    )
+    assert code == 0
+    for record in json.loads(out):
+        assert len(record["excerpt"].split("\n")) <= 2
+
+
+def test_context_zero_does_not_turn_continuation_into_empty_slot(tmp_path: Path, capsys):
+    """--context 改的是显示行数，不该改「这条批注是不是空槽」这个事实。
+
+    2026-09-19 实测的回归：早先把「扫描续行的上限」和「显示上限」写成同一个数，
+    --context 0 会让所有换行续写的批注 empty=1、默认不列——参数悄悄改了语义。
+    """
+    base = tmp_path / "ctx"
+    base.mkdir()
+    (base / "a.md").write_text("**User2：**\n续写正文 kw-ctx\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    for context in ("0", "1", "5"):
+        code, out, err = run_cli(
+            ["--root", str(base), "--a01", str(a01), "--keyword", "User2", "--context", context, "--json"],
+            capsys,
+        )
+        assert "empty=0" in err, f"--context {context} 不得把有续行的批注判成空槽"
+        assert code == 0
+        assert len(json.loads(out)) == 1
+
+
+def test_fenced_code_hits_are_labelled_not_dropped(tmp_path: Path, capsys):
+    """围栏代码块里的 marker 照常召回，但必须带 in_fenced_code 标注并计入汇总。
+
+    契约 §4.2 要求「用状态机识别 fenced code」——识别不等于排除。本仓实测 12.7%
+    的 marker 行在围栏内，其中有真批注被引用进代码块，排除会丢真阳性。
+    """
+    base = tmp_path / "fence"
+    base.mkdir()
+    (base / "a.md").write_text(
+        "正文\n\n```\n**User：围栏里的 kw-fence**\n```\n\n**User：围栏外的 kw-fence**\n",
+        encoding="utf-8",
+    )
+    a01 = write_a01(tmp_path)
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-fence", "--json"], capsys)
+    assert code == 0
+    by_line = {r["line"]: r["in_fenced_code"] for r in json.loads(out)}
+    assert by_line == {4: True, 7: False}
+    assert "fenced=1" in err
+
+
+def test_fence_marker_line_itself_is_not_a_hit(tmp_path: Path, capsys):
+    """围栏起止行本身不参与 marker 匹配（对照输入：把 marker 写在围栏行上）。"""
+    base = tmp_path / "fenceline"
+    base.mkdir()
+    (base / "a.md").write_text("```**User：不该命中 kw-fl**\n```\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-fl", "--json"], capsys)
+    assert json.loads(out) == []
+    assert code == 1
+
+
+# --------------------------------------------------------------------------
+# 门的变异存活面补洞（内部对抗复核 gates 维度实测：下列变异体原本全部「存活」，
+# 即改坏它们之后本文件仍全绿。存活清单见 evidence-g11/gate-mutation-survey-*.txt）
+# --------------------------------------------------------------------------
+def test_git_env_is_actually_wired_into_the_subprocess(tmp_path: Path, monkeypatch, capsys):
+    """证明 git_env() **接上了**，不只是存在。
+
+    变异体 K_git_env_unwired（把 git_env 从 subprocess.run 上摘掉）原本存活——
+    因为旧门只单测了这个函数的返回值，没有任何一条测试走过「它有没有被用上」。
+    这里在调用方环境里塞一个坏掉的 GIT_DIR：若它漏进子进程，git 会去那个不存在的
+    仓库找、返回非 0 ⇒ date_source 退成 unknown；接上了才仍是 git。
+    """
+    repo = tmp_path / "repo"
+    repo.mkdir()
+    (repo / "plain.md").write_text("**User：只有 git 能定日期 kw-wire**\n", encoding="utf-8")
+    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"]
+    subprocess.run([*git, "init", "-q"], cwd=repo, check=True, capture_output=True)
+    subprocess.run([*git, "add", "plain.md"], cwd=repo, check=True, capture_output=True)
+    subprocess.run(
+        [*git, "commit", "-q", "-m", "seed", "--date=2019-07-08T00:00:00"],
+        cwd=repo,
+        check=True,
+        capture_output=True,
+        env={**os.environ, "GIT_COMMITTER_DATE": "2019-07-08T00:00:00"},
+    )
+    a01 = write_a01(tmp_path)
+
+    # 对照组：环境干净时必须是 git 档（证明这条路径本来走得通）
+    code, out, _ = run_cli(["--root", str(repo), "--a01", str(a01), "--keyword", "kw-wire", "--json"], capsys)
+    assert code == 0
+    assert json.loads(out)[0]["date_source"] == "git"
+
+    # 负控输入：塞一个坏 GIT_DIR。接线成立 ⇒ 结果不变。
+    monkeypatch.setenv("GIT_DIR", str(tmp_path / "definitely-not-a-repo.git"))
+    code, out, _ = run_cli(["--root", str(repo), "--a01", str(a01), "--keyword", "kw-wire", "--json"], capsys)
+    assert code == 0
+    record = json.loads(out)[0]
+    assert record["date_source"] == "git", "调用方的 GIT_DIR 漏进了子进程 ⇒ git_env 没接上"
+    assert record["date"] == "2019-07-08"
+
+
+def test_tool_writes_nothing_anywhere_in_the_repo(capsys):
+    """只读的量面必须覆盖**整个仓库**，不只是 `_bmad-output`。
+
+    变异体 F_writes_outside（让脚本往目标目录之外写）原本存活：旧的只读门只对
+    `_bmad-output` 与 fixture 树算摘要，仓里别处新增的文件一个都看不见。
+    这里用 `git status --porcelain -uall` 覆盖全仓（排除本卡自己的落档目录）。
+    """
+    scope = ["--porcelain", "-uall", "--", ".", ":(exclude)_bmad-output/审查/evidence-g11"]
+
+    def repo_status():
+        proc = subprocess.run(
+            ["git", "-c", "core.quotepath=false", "status", *scope],
+            cwd=REPO_ROOT,
+            capture_output=True,
+            encoding="utf-8",
+            errors="replace",
+            check=True,
+        )
+        return proc.stdout
+
+    before = repo_status()
+    run_cli(["--keyword", "codex", "--story", "CARD-G1-1", "--a01", str(REAL_A01)], capsys)
+    assert repo_status() == before, "运行前后全仓 git status 必须逐字同"
+
+
+def test_prefix_rule_alone_catches_a_private_root_without_component_name(tmp_path: Path, capsys):
+    """给前缀比较层一个**只有它能抓**的输入。
+
+    变异体 A_no_prefix（摘掉前缀比较层）原本存活——因为所有私人面用例走的都是
+    `canvas-vault` 这个目录名，组件名安全网把前缀层的覆盖面整个吃掉了
+    （「加一道更强的门会吃掉旧门的测试面」）。ROOT-ANCHORED-PRD 的 `.gdr/_external`
+    既不含 canvas-vault 组件、basename 也不是 PRD 文件名，只有前缀规则拦得住。
+    """
+    base = tmp_path / "repo"
+    (base / ".gdr" / "_external").mkdir(parents=True)
+    (base / ".gdr" / "_external" / "notes.md").write_text("**User：外部私人 kw-gdr**\n", encoding="utf-8")
+    (base / "pub.md").write_text("**User：公开 kw-gdr**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-gdr", "--json"], capsys)
+    assert code == 0
+    names = [os.path.basename(r["path"]) for r in json.loads(out)]
+    assert names == ["pub.md"], ".gdr/_external 下的内容只能由前缀规则拦住"
+    assert "ROOT-ANCHORED-PRD" in err
+
+
+@pytest.mark.parametrize(
+    "rel,expected",
+    [
+        ("验收单/批注回复/x.md", "批注回复"),
+        ("研究/2026-08-27-批注回复-C2.md", "批注回复"),
+        ("验收单/UAT-x.md", "验收单批注区"),
+        ("审查/x.md", "审查"),
+        ("研究/x.md", "研究"),
+        ("implementation-artifacts/goal-cards/x.md", "goal-cards"),
+        ("planning-artifacts/x.md", "planning-artifacts"),
+        ("决策批注/x.md", "决策批注"),
+        ("research/x.md", "其他"),
+        ("review/x.md", "其他"),
+        ("Session 3/x.md", "其他"),
+    ],
+)
+def test_classify_covers_all_eight_buckets(rel, expected):
+    """八类映射逐桶钉住（含 research/ 与 review/ 落「其他」这两条卡文 §〇 的规范口径）。
+
+    变异体 D_thin_classify / D2_thin_classify_all（把 classify 削成只返回一类）原本
+    全部存活——这张表此前一条断言都没有。
+    """
+    assert mod.classify(rel) == expected
+
+
+def test_multiple_markers_on_one_line_all_reported(tmp_path: Path, capsys):
+    """同一行上的多个 marker 必须逐个成条。
+
+    变异体 E_first_marker_only（每行只取第一个 marker）原本存活。
+    """
+    base = tmp_path / "multi"
+    base.mkdir()
+    (base / "a.md").write_text("**User：正文 [!error]+ 同一行第二个 marker kw-multi**\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-multi", "--json"], capsys)
+    assert code == 0
+    records = json.loads(out)
+    assert [r["marker"] for r in records] == ["**User：", "[!error]+"]
+    assert {r["line"] for r in records} == {1}
+
+
+def test_context_zero_shows_only_the_marker_line(tmp_path: Path, capsys):
+    """`--context 0` 的摘录必须恰好 1 行。
+
+    变异体 H_no_display_slice（去掉 `collected[:context]`）原本存活：旧用例用
+    `--context 1`，而扫描下限也是 1，两者恰好等价 ⇒ 那一刀切不切都一样。
+    """
+    base = tmp_path / "ctx0"
+    base.mkdir()
+    (base / "a.md").write_text("**User2：**\n续写一 kw-c0\n续写二\n", encoding="utf-8")
+    a01 = write_a01(tmp_path)
+    code, out, err = run_cli(
+        ["--root", str(base), "--a01", str(a01), "--keyword", "User2", "--context", "0", "--json"], capsys
+    )
+    assert code == 0
+    assert json.loads(out)[0]["excerpt"].split("\n") == ["**User2：**"]
+    assert "empty=0" in err, "--context 0 只改显示，不该把有续行的批注判成空槽"
+
+
+def test_output_is_deterministic_across_separate_processes(six_forms):
+    """确定性必须跨**进程**证，而且 stdout / stderr 都要比。
+
+    两处教训都写在这里：
+    * 变异体 G_nondet_stderr（汇总行掺进程号）原本存活，因为旧用例只比 stdout；
+    * 补完 stderr 之后它**仍然**存活——旧用例在同一个进程里调两次 main()，
+      `os.getpid()` 当然相同。同进程比两次证明不了跨进程确定性，
+      PYTHONHASHSEED 决定的 set 迭代序、pid、启动时刻都从这个缝里漏过去。
+    所以这里起两个真子进程，并刻意给它们**不同的 PYTHONHASHSEED**。
+    """
+    base, a01 = six_forms
+    argv = [
+        sys.executable,
+        str(REPO_ROOT / "scripts" / "annotation_search.py"),
+        "--root",
+        str(base),
+        "--a01",
+        str(a01),
+        "--keyword",
+        "kw-alpha",
+        "--json",
+    ]
+
+    def run(seed):
+        return subprocess.run(
+            argv,
+            capture_output=True,
+            encoding="utf-8",
+            errors="replace",
+            check=False,
+            env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"},
+        )
+
+    first, second = run("0"), run("12345")
+    assert first.returncode == second.returncode == 0
+    assert first.stdout == second.stdout
+    assert first.stderr == second.stderr, "汇总行在两个进程之间必须逐字同"
+
+
+def test_marker_table_shape():
+    assert len(mod.MARKERS) == 10
+    callouts = sorted(k[len(mod.CALLOUT_PREFIX) :] for k in mod.MARKERS if k.startswith(mod.CALLOUT_PREFIX))
+    assert callouts == ["BMAD-ANNO", "error", "hint", "info", "note", "question", "tip", "todo", "warning"]
+
+
+@pytest.mark.parametrize(
+    "line,expected",
+    [
+        ("**User**：契约 :131 的拆开粗体形态", "**User**："),
+        ("> [!todo]+ 📝 批注区（直接写 **User：**）", "[!todo]+"),
+        ("> [!NOTE] Obsidian 的 callout 类型大小写不敏感", "[!NOTE]"),
+        ("> [!WARNING] 同上", "[!WARNING]"),
+        ("**User 修正：改口", "**User 修正："),
+        ("**User Comment: english variant", "**User Comment:"),
+    ],
+)
+def test_contract_t1_t2_variants_are_matched(line, expected):
+    """契约 :131/:134 点名、且真数据里确实出现过的形态，逐条钉住。
+
+    实测支撑：`**User**：` 1 处、`[!todo]+` 10 处、大写 callout 3 处（2026-09-19 于本树）。
+    """
+    hits = mod.find_markers(line)
+    assert hits, f"{line!r} 应当命中"
+    assert hits[0][1] == expected
+
+
+def test_inline_bold_in_continuation_does_not_truncate_block(tmp_path: Path, capsys):
+    """续行里的行内加粗是成对的，不该把批注块提前截断。
+
+    旧规则「见到 ** 就停」会在第一条含行内加粗的续行处收尾，使同一条批注的剩余
+    正文变成检索不到的面。
+    """
+    base = tmp_path / "pairs"
+    base.mkdir()
+    (base / "a.md").write_text(
+        "**User：开头正文\n中间有**行内加粗**的一行\n结尾关键词 kw-tail**\n\n后面段落\n",
+        encoding="utf-8",
+    )
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-tail", "--json"], capsys)
+    assert code == 0, "结尾在第三行的关键词必须仍在检索面内"
+    records = json.loads(out)
+    assert len(records) == 1
+    assert records[0]["excerpt"].split("\n")[-1] == "结尾关键词 kw-tail**"
+
+
+def test_closed_bold_annotation_does_not_swallow_following_reply(tmp_path: Path, capsys):
+    """`**User：…**` 自闭合后紧跟的 Claude 回复不得被算进这条批注的摘录。"""
+    base = tmp_path / "reply"
+    base.mkdir()
+    (base / "a.md").write_text(
+        "**User：我的原话 kw-mine**\n> [!note]+ Claude 回复：这不是用户说的 kw-claude\n",
+        encoding="utf-8",
+    )
+    a01 = write_a01(tmp_path)
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-mine", "--json"], capsys)
+    assert code == 0
+    records = json.loads(out)
+    assert len(records) == 1
+    assert records[0]["excerpt"] == "**User：我的原话 kw-mine**"
+    assert "kw-claude" not in records[0]["excerpt"]
+
+
+def test_private_root_ids_are_derived_from_a01_not_hardcoded(tmp_path: Path):
+    """把 A01 里 ROOT-ACTIVE-VAULT 降成 P2 ⇒ 它就不再是私人 root。"""
+    payload = {"source_roots": [dict(r) for r in MINIMAL_A01["source_roots"]]}
+    for entry in payload["source_roots"]:
+        if entry["root_id"] == "ROOT-ACTIVE-VAULT":
+            entry["privacy_ceiling"] = "P2-personal"
+            entry["proposed_action"] = "include-current-repo"
+    a01 = write_a01(tmp_path, payload)
+    private, declared = mod.load_private_root_ids(str(a01))
+    assert "ROOT-ACTIVE-VAULT" not in private
+    assert len(declared) == 8
+    real_private, real_declared = mod.load_private_root_ids(str(REAL_A01))
+    assert "ROOT-ACTIVE-VAULT" in real_private
+    assert "ROOT-ANCHORED-PRD" in real_private  # private-locator 口径
+    assert len(real_private) == 6
+    assert len(real_declared) == 8
diff --git a/scripts/annotation_search.py b/scripts/annotation_search.py
new file mode 100644
index 00000000..53e501f0
--- /dev/null
+++ b/scripts/annotation_search.py
@@ -0,0 +1,858 @@
+#!/usr/bin/env python3
+"""批注只读检索（CARD-G1-1）。
+
+按关键词 / Story ID 在 Markdown 里找回「用户说过的话」，输出 ``file:line`` + 摘录 +
+日期（带 ``date_source``）+ 来源类别。
+
+覆盖面（契约 ``2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md`` §4.1 的 T1 全部
+与 T2 的粗体 / blockquote / 行内三形态）：
+
+* 粗体 User 族：``**User：`` / ``**User:`` / ``**User ：`` / ``**User2：`` /
+  ``**User 修正：`` / ``**User Comment:`` 等（契约 ``:134``）。
+* callout 族：``[!question]+`` / ``[!error]+`` / ``[!tip]+`` / ``[!note]+`` /
+  ``[!warning]+`` / ``[!hint]+`` / ``[!info]+`` / ``[!BMAD-ANNO]``，blockquote
+  （``> [!x]+``）与行内两种形态都算。
+
+**不做**（如实声明，非遗漏）：契约 ``:132`` 的 T3 broad discovery（``user``/``USer``
+异常大小写、role 字段、转述、无冒号编号）须人工分类，不进本脚本；契约 ``:82`` 的非
+Markdown 容器（Canvas JSON / JSONL / YAML / 对话导出）不解析；修正链去重 /
+atomization（契约 §4.2 末条）不做。
+
+**只读**：本脚本自身除 stdout / stderr 外零写——不建目录、不改被扫文件。唯一子进程
+是 ``git log -1 --format=%cs``（只读查询），且仅在 frontmatter 与文件名都给不出日期
+时才调用；该子进程拿到的是**剃掉全部 ``GIT_*`` 的环境**（见 ``git_env``），否则
+``GIT_DIR`` 会让它回答另一个仓库、``GIT_TRACE*`` 会让它自己往文件里写。
+
+⚠️ 一处如实声明：以 ``python3 scripts/annotation_search.py`` 方式跑时不产生任何缓存
+（``__main__`` 不写字节码）；但被 ``import`` 进别的进程时，**Python 解释器**可能在
+``scripts/__pycache__`` 写 ``.pyc``。那是解释器行为不是本脚本的写调用，所以全部裁判
+一律带 ``PYTHONDONTWRITEBYTECODE=1``。
+
+**私人 root**：默认排除的私人根**不写死在本文件里**，而是从 A01
+(``A01-source-boundary-draft.json``) 的 ``source_roots`` 算出——``privacy_ceiling``
+∈ {P3-high-sensitive, P4-secret} 的 root，加上 ``proposed_action`` 含
+``private-locator`` 的 root。A01 读不到 / 结构不对 ⇒ 退出码 2（fail-closed），
+**不**降级成「当作没有私人 root 继续扫」。
+"""
+
+from __future__ import annotations
+
+import argparse
+import datetime
+import json
+import os
+import re
+import subprocess
+import sys
+import unicodedata
+from pathlib import Path
+
+REPO_ROOT = str(Path(__file__).resolve().parents[1])
+
+DEFAULT_ROOT = os.path.join(REPO_ROOT, "_bmad-output")
+DEFAULT_A01 = os.path.join(
+    REPO_ROOT,
+    "_bmad-output",
+    "审查",
+    "phase0a-annotation-truth",
+    "A01-source-boundary-draft.json",
+)
+
+PRUNE_DIRS = frozenset({".obsidian", "__pycache__", "node_modules", ".git"})
+
+# --- marker 表 -------------------------------------------------------------
+# name -> 正则。一族粗体 User + 八个 callout 类型，逐条可数（len(MARKERS) == 9）。
+# `\*{0,2}` 覆盖契约 :131 T2 的「marker 被粗体符号拆开」形态（`**User**：`，
+# 真数据 1 处：`验收单/Story-2.1-Phase1-成熟度升级-2026-05-03.md:279`）。
+# callout 一律 IGNORECASE —— Obsidian 的 callout 类型本就大小写不敏感，
+# 真数据里 `[!WARNING]` / `[!NOTE]` 共 3 处，逐字小写匹配会漏掉。
+MARKERS = {
+    "user_bold": re.compile(r"\*\*User(?:\s?\d)?\s?(?:修正|Comment)?\*{0,2}\s?[：:]"),
+    "callout_question": re.compile(r"\[!question\][+-]?", re.I),
+    "callout_error": re.compile(r"\[!error\][+-]?", re.I),
+    "callout_tip": re.compile(r"\[!tip\][+-]?", re.I),
+    "callout_note": re.compile(r"\[!note\][+-]?", re.I),
+    "callout_warning": re.compile(r"\[!warning\][+-]?", re.I),
+    "callout_hint": re.compile(r"\[!hint\][+-]?", re.I),
+    "callout_info": re.compile(r"\[!info\][+-]?", re.I),
+    # `[!todo]+ 📝 批注区（直接写 **User：**）` 是本仓批注区的标准容器形态，
+    # 真数据 10 处 —— 漏掉它等于漏掉「批注区」这个入口本身。
+    "callout_todo": re.compile(r"\[!todo\][+-]?", re.I),
+    "callout_BMAD-ANNO": re.compile(r"\[!BMAD-ANNO\][+-]?", re.I),
+}
+
+CALLOUT_PREFIX = "callout_"
+
+# --- Story ID 形态 ---------------------------------------------------------
+# 只用于回填 `story_ids` 字段；`--story` 的匹配本身是大小写敏感的子串包含。
+STORY_ID_PATTERNS = (
+    re.compile(r"CARD-[A-Za-z0-9][A-Za-z0-9\-]*"),
+    re.compile(r"Story[\- ]\d+\.\d+[A-Za-z0-9.]*"),
+    re.compile(r"DEBT-\d+"),
+    re.compile(r"T-new-\d+"),
+    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{1,2}\d{1,2}-[A-Za-z0-9]{1,3}(?![A-Za-z0-9])"),
+)
+
+# --- 来源类别（路径前缀口径）------------------------------------------------
+CATEGORIES = (
+    "验收单批注区",
+    "批注回复",
+    "审查",
+    "研究",
+    "goal-cards",
+    "planning-artifacts",
+    "决策批注",
+    "其他",
+)
+
+# --- 私人 root 的路径映射 ---------------------------------------------------
+# A01 只声明 root_id / privacy_ceiling，**没有 path 字段**，所以 root_id -> 路径
+# 的映射只能由本脚本自带。A01 若将来补上 path 字段，这里要同步。
+#
+# 相对形态锚在「每个扫描根及其各级祖先」与仓根上做 realpath 前缀比较；
+# 组件形态（路径里出现名为 canvas-vault 的目录段）与 basename 形态是安全网，
+# 挡住前缀比较覆盖不到的位置（例如 <root>/sub/canvas-vault/）。
+PRIVATE_RELATIVE_PATHS = {
+    "ROOT-ACTIVE-VAULT": ("canvas-vault",),
+    "ROOT-ANCHORED-PRD": (
+        os.path.join(".gdr", "_external"),
+        os.path.join("docs", "scheme-a-planning", "14-scheme-a-implementation-prd.md"),
+    ),
+}
+PRIVATE_ABSOLUTE_PATHS = {
+    "ROOT-ACTIVE-VAULT": ("/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault",),
+    "ROOT-ANCHORED-PRD": ("/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md",),
+}
+# ⚠️ 下面两张表的**键**是拿来和 fold_path() 的输出比对的，所以必须写成
+# NFC + casefold 后的形态（全小写）。单测 test_private_lookup_keys_are_prefolded
+# 把这条不变量钉成门——写错大小写会静默漏判，不是报错。
+PRIVATE_COMPONENT_ROOTS = {"canvas-vault": "ROOT-ACTIVE-VAULT"}
+PRIVATE_BASENAME_ROOTS = {"14-scheme-a-implementation-prd.md": "ROOT-ANCHORED-PRD"}
+
+PRIVATE_CEILINGS = frozenset({"p3-high-sensitive", "p4-secret"})
+# 明确判定为**非**私人的 ceiling。凡不在这张表也不在 PRIVATE_CEILINGS 的取值
+# （拼写变体、前后空白、将来新增的 P5…）一律按私人处理 —— 这是 fail-closed：
+# 认不出的敏感级别当敏感，而不是当公开。
+PUBLIC_CEILINGS = frozenset({"p0-public", "p1-project-internal", "p2-personal"})
+PRIVATE_ACTION_TOKEN = "private-locator"
+
+# 围栏代码块识别（契约 §4.2 :139 要求「用状态机识别 fenced code」）。
+# ⚠️ 识别 ≠ 排除：本仓 12.7%（148/1167 实测 2026-09-19）的 marker 行落在围栏内，
+# 其中既有真批注被引用进代码块（如 obsidian-qa-round11:618 的 `**User：以下是 ChatGpt 调研结果**`），
+# 也有纯格式示例（如 obsidian-qa-round3:554 的 `> [!error]+ ❌ 错误`）。排除会丢真阳性，
+# 所以照常召回，但每条记录带 in_fenced_code 标注、汇总行报计数，让人一眼能筛。
+FENCE_RE = re.compile(r"^\s{0,3}(?:```|~~~)")
+
+# HTML 注释同理（契约 :134 的「至少覆盖」清单含「HTML 注释、模板/示例/引用」，
+# :139 要求状态机识别 HTML comment）。真数据 26 行 / 6 文件落在注释区内，
+# 样例是被注释掉的填写模板（验收单/Story-2.5.X-progressive-confirmation.md:781-787）。
+# 同样是**标注不排除**：注释掉的也可能是真批注，删了就找不回来。
+HTML_COMMENT_OPEN = "<!--"
+HTML_COMMENT_CLOSE = "-->"
+
+# 续行遇到「另一个人开口」就停。真数据里批注区的标准写法是
+# `> **User：** …` / `>` / `> **Claude（2026-07-20）：** …`（研究/ 下 2 处实测），
+# 引用块里的「空行」是一个光秃秃的 `>`，用 str.strip() 判不出来，于是 Claude 的
+# 回复会被 append 进 User 那条记录，工具就把别人的话当成「用户说过的话」返回。
+SPEAKER_LABEL_RE = re.compile(r"^\s*>*\s*\*\*[^*]{1,24}?[：:]")
+QUOTE_BLANK_RE = re.compile(r"^[>\s]*$")
+
+FRONTMATTER_KEYS = ("date", "created", "updated")
+# frontmatter 的扫描上界。没有这个界，首行那个 `---` 其实是正文分隔线时，
+# 解析会一路扫到 EOF，把正文里（甚至围栏代码块里）的 `date:` 当成 frontmatter，
+# 于是报出一个**看起来权威**的错日期（2026-09-19 实测：围栏内的 `date: 1999-01-01`
+# 被报成 `date_source=frontmatter`）。
+FRONTMATTER_MAX_LINES = 200
+
+# ⚠️ 两侧的 `(?<!\d)` / `(?!\d)` 不可省：没有边界时 `ticket-1234-56-7890.md` 会被
+# 抠出 `1234-56-78`（月 56 日 78），而且因为 filename 档排在 git 档之前，这个假值会
+# **挡掉**本来能给出真实提交日期的那一档——报出来的不是「定不了日期」而是一个假日期。
+DATE_RE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
+EXCERPT_LINE_LIMIT = 200
+
+
+class A01Error(Exception):
+    """A01 缺失 / 结构不合约 —— fail-closed，调用方须以退出码 2 结束。"""
+
+
+class PrivateRootRefused(Exception):
+    """`--root` 指向 A01 声明的私人 root —— 退出码 2。"""
+
+
+# --------------------------------------------------------------------------
+# A01
+# --------------------------------------------------------------------------
+def load_private_root_ids(a01_path):
+    """从 A01 算出私人 root_id 集合。任何读不到 / 结构不对都抛 A01Error。"""
+    try:
+        with open(a01_path, "r", encoding="utf-8") as handle:
+            data = json.load(handle)
+    except FileNotFoundError as exc:
+        raise A01Error(f"A01 边界声明读不到：{a01_path}") from exc
+    except OSError as exc:
+        raise A01Error(f"A01 边界声明打不开：{a01_path}（{exc}）") from exc
+    except (ValueError, UnicodeDecodeError) as exc:
+        raise A01Error(f"A01 边界声明不是合法 JSON：{a01_path}（{exc}）") from exc
+
+    if not isinstance(data, dict):
+        raise A01Error(f"A01 顶层不是 JSON object：{a01_path}")
+    roots = data.get("source_roots")
+    if not isinstance(roots, list) or not roots:
+        raise A01Error(f"A01 顶层缺 source_roots 列表：{a01_path}")
+
+    private = set()
+    declared = []
+    for idx, entry in enumerate(roots):
+        if not isinstance(entry, dict):
+            raise A01Error(f"A01 source_roots[{idx}] 不是 object：{a01_path}")
+        root_id = entry.get("root_id")
+        ceiling = entry.get("privacy_ceiling")
+        if not isinstance(root_id, str) or not root_id:
+            raise A01Error(f"A01 source_roots[{idx}] 缺 root_id：{a01_path}")
+        if not isinstance(ceiling, str) or not ceiling:
+            raise A01Error(f"A01 source_roots[{idx}]（{root_id}）缺 privacy_ceiling：{a01_path}")
+        declared.append(root_id)
+        action = entry.get("proposed_action")
+        normalized = ceiling.strip().casefold()
+        if normalized in PRIVATE_CEILINGS:
+            private.add(root_id)
+        elif normalized not in PUBLIC_CEILINGS:
+            # 认不出的敏感级别按私人处理，并把这件事说出来（不静默）。
+            print(
+                f"annotation_search.py: A01 的 {root_id} privacy_ceiling={ceiling!r} 不在已知取值里，"
+                "按私人 root 处理（fail-closed）。",
+                file=sys.stderr,
+            )
+            private.add(root_id)
+        elif isinstance(action, str) and PRIVATE_ACTION_TOKEN in action.casefold():
+            private.add(root_id)
+    return private, declared
+
+
+def build_private_paths(private_root_ids, scan_roots):
+    """root_id -> realpath 前缀列表。
+
+    基点 = 仓根 ∪ 每个扫描根本身及其各级祖先。这样 tmp fixture 里的
+    ``<fixture>/canvas-vault`` 与 ``--root <fixture>/canvas-vault`` 都能被同一套
+    前缀规则判出，不必把 fixture 路径写进脚本。
+    """
+    bases = {os.path.realpath(REPO_ROOT)}
+    for root in scan_roots:
+        current = os.path.realpath(root)
+        while True:
+            bases.add(current)
+            parent = os.path.dirname(current)
+            if parent == current:
+                break
+            current = parent
+
+    mapping = {}
+    for root_id in sorted(private_root_ids):
+        found = []
+        for rel in PRIVATE_RELATIVE_PATHS.get(root_id, ()):
+            for base in bases:
+                found.append(os.path.realpath(os.path.join(base, rel)))
+        for absolute in PRIVATE_ABSOLUTE_PATHS.get(root_id, ()):
+            found.append(os.path.realpath(absolute))
+        mapping[root_id] = sorted(set(found))
+    return mapping
+
+
+def fold_path(value):
+    """路径比较的归一口径：NFC + casefold。
+
+    ⚠️ 单靠 ``os.path.realpath`` 不够：它解软链、解 ``..``，但**不归一大小写**，
+    而本机 macOS APFS（以及 Windows）默认大小写不敏感——``<base>/Canvas-Vault`` 与
+    ``<base>/canvas-vault`` 是同一个目录，逐字节比较却判成两个。2026-09-19 实测：
+    未做 casefold 前，``Canvas-Vault/`` 下的批注会被原样返回，即私人面泄漏。
+    NFC 同理挡住 macOS 上分解形态（NFD）与预组合形态写法不同的同一个目录名。
+
+    代价（如实声明）：在大小写敏感的文件系统上，一个**确实另有其物**、只是恰好叫
+    ``Canvas-Vault`` 的目录也会被一并排除。这是刻意选的 fail-safe 方向——本工具的
+    默认立场是宁可少看也不碰私人面，需要时用 ``--include-private`` 显式解除。
+    """
+    return unicodedata.normalize("NFC", value).casefold()
+
+
+def private_root_of(path, private_paths):
+    """path（任意形态）落在哪个私人 root 下；不落则返回 None。
+
+    realpath 口径 + ``fold_path`` 归一（见该函数 docstring 里的实测理由）。
+    """
+    real = fold_path(os.path.realpath(path))
+    for root_id, prefixes in private_paths.items():
+        for prefix in prefixes:
+            folded = fold_path(prefix)
+            if real == folded or real.startswith(folded + os.sep):
+                return root_id
+    for part in real.split(os.sep):
+        hit = PRIVATE_COMPONENT_ROOTS.get(part)
+        if hit is not None and hit in private_paths:
+            return hit
+    hit = PRIVATE_BASENAME_ROOTS.get(os.path.basename(real))
+    if hit is not None and hit in private_paths:
+        return hit
+    return None
+
+
+# --------------------------------------------------------------------------
+# 扫描
+# --------------------------------------------------------------------------
+def iter_markdown_files(scan_roots, private_paths, include_private, pruned, unwalkable):
+    """产出待扫的 .md realpath，去重、确定序。私人子树跳过并登记进 pruned。
+
+    ``os.walk`` 默认把 ``scandir`` 的 OSError **直接吞掉**，于是一棵列不出来的子树
+    （权限不足 / 挂载点掉线 / 路径过长）连同它下面所有 .md 一起从输入面消失，
+    ``files_scanned`` 只是变小，没有任何人会知道。契约 :142 的口径是「不能静默当 0」，
+    所以这里传 ``onerror`` 把它们收进 ``unwalkable`` 桶并在汇总行报数。
+    """
+    seen = set()
+    out = []
+
+    def on_walk_error(err):
+        unwalkable.append(getattr(err, "filename", None) or str(err))
+
+    for root in scan_roots:
+        real_root = os.path.realpath(root)
+        if os.path.isfile(real_root):
+            if real_root.endswith(".md") and real_root not in seen:
+                seen.add(real_root)
+                out.append(real_root)
+            continue
+        for dirpath, dirnames, filenames in os.walk(real_root, onerror=on_walk_error):
+            keep = []
+            for name in sorted(dirnames):
+                if name in PRUNE_DIRS:
+                    continue
+                child = os.path.join(dirpath, name)
+                if not include_private:
+                    owner = private_root_of(child, private_paths)
+                    if owner is not None:
+                        pruned.add((owner, child))
+                        continue
+                keep.append(name)
+            dirnames[:] = keep
+            for name in sorted(filenames):
+                if not name.endswith(".md"):
+                    continue
+                full = os.path.join(dirpath, name)
+                if not include_private and private_root_of(full, private_paths) is not None:
+                    pruned.add((private_root_of(full, private_paths), full))
+                    continue
+                real = os.path.realpath(full)
+                if real in seen:
+                    continue
+                seen.add(real)
+                out.append(real)
+    return sorted(out, key=sort_key_path)
+
+
+def sort_key_path(path):
+    """NFC 归一后再比，避免同名文件在 NFD / NFC 文件系统上排序不同。"""
+    return (unicodedata.normalize("NFC", path), path)
+
+
+def read_text(path):
+    """严格 UTF-8 读取。含 NUL 或解码失败 → 返回 None（进 unreadable 桶）。"""
+    try:
+        with open(path, "rb") as handle:
+            raw = handle.read()
+    except OSError:
+        return None
+    if b"\x00" in raw:
+        return None
+    try:
+        return raw.decode("utf-8")
+    except UnicodeDecodeError:
+        return None
+
+
+# --------------------------------------------------------------------------
+# 日期
+# --------------------------------------------------------------------------
+def find_date(text):
+    """从文本里取第一个**日历上真实存在**的 `YYYY-MM-DD`，取不到返回 None。
+
+    只用正则不够：`1234-56-78` 形状合法但不是日期，`2026-02-30` 亦然。报一个假日期
+    比报 `unknown` 更坏——前者会被当成事实引用，后者只是承认不知道。
+    """
+    for match in DATE_RE.finditer(text):
+        year, month, day = (int(g) for g in match.groups())
+        try:
+            datetime.date(year, month, day)
+        except ValueError:
+            continue
+        return match.group(0)
+    return None
+
+
+def frontmatter_date(lines):
+    """只认文件开头**闭合的** `---` 块里的 `key: value`，不引 PyYAML。
+
+    「闭合」是硬条件：首行 `---` 若在 FRONTMATTER_MAX_LINES 内没有对应的收尾行，
+    它就是一条正文分隔线而不是 frontmatter 开头，此时一个字段都不认。
+    """
+    if not lines or lines[0].strip() != "---":
+        return None
+    end = None
+    for offset in range(1, min(len(lines), FRONTMATTER_MAX_LINES + 1)):
+        if lines[offset].strip() in ("---", "..."):
+            end = offset
+            break
+    if end is None:
+        return None
+    for line in lines[1:end]:
+        if ":" not in line:
+            continue
+        key = line[: line.index(":")].strip().lower()
+        if key not in FRONTMATTER_KEYS:
+            continue
+        value = line[line.index(":") + 1 :].strip().strip("'\"")
+        found = find_date(value)
+        if found is not None:
+            return found
+    return None
+
+
+def git_env():
+    """给 git 子进程一份剃掉全部 ``GIT_*`` 的环境。
+
+    不传 ``env=`` 就是把调用方环境整份继承给 git，两个后果都不是假想：
+
+    * ``GIT_DIR`` 一旦存在，git 的仓库发现不再看 ``cwd`` ⇒ ``date`` 会变成
+      **另一个仓库**对这条路径的答案，而 ``date_source`` 仍写 ``git``。
+    * ``GIT_TRACE`` / ``GIT_TRACE2`` / ``GIT_TRACE2_EVENT`` 之类会让 git
+      **往文件里写**——零写 AST 门只看得见 Python 源码里的写调用，看不见子进程。
+
+    ``GIT_OPTIONAL_LOCKS=0`` 再挡一层：只读查询不去碰 index.lock。
+    """
+    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
+    env["GIT_TERMINAL_PROMPT"] = "0"
+    env["GIT_OPTIONAL_LOCKS"] = "0"
+    return env
+
+
+def git_commit_date(path):
+    """`git log -1 --format=%cs` —— 只读查询；任何失败都降级返回 None。"""
+    workdir = os.path.dirname(path)
+    if not workdir:
+        workdir = "."
+    try:
+        proc = subprocess.run(
+            ["git", "log", "-1", "--format=%cs", "--", path],
+            cwd=workdir,
+            capture_output=True,
+            encoding="utf-8",
+            errors="replace",
+            env=git_env(),
+            check=False,
+            timeout=15,
+        )
+    except (OSError, subprocess.SubprocessError, UnicodeDecodeError, ValueError):
+        return None
+    if proc.returncode != 0:
+        return None
+    return find_date(proc.stdout.strip())
+
+
+def resolve_date(path, lines, cache):
+    """frontmatter → 文件名 → git → unknown。返回 (date, date_source)。
+
+    ⚠️ 三种来源都是**文件级**的，不是「批注写下的时刻」——所以 date_source 必须
+    随日期一起输出，不把 git 提交日期冒充成用户落笔时间。
+    """
+    if path in cache:
+        return cache[path]
+    value = frontmatter_date(lines)
+    if value is not None:
+        result = (value, "frontmatter")
+    else:
+        found = find_date(os.path.basename(path))
+        if found is not None:
+            result = (found, "filename")
+        else:
+            value = git_commit_date(path)
+            if value is not None:
+                result = (value, "git")
+            else:
+                result = ("unknown", "unknown")
+    cache[path] = result
+    return result
+
+
+# --------------------------------------------------------------------------
+# 类别
+# --------------------------------------------------------------------------
+def relative_label(path, scan_roots):
+    """展示用相对路径：`_bmad-output` 段之后；没有该段则相对仓根 / 扫描根。"""
+    real = os.path.realpath(path)
+    parts = real.split(os.sep)
+    if "_bmad-output" in parts:
+        idx = len(parts) - 1 - parts[::-1].index("_bmad-output")
+        return "/".join(parts[idx + 1 :])
+    for root in scan_roots:
+        real_root = os.path.realpath(root)
+        if real == real_root or real.startswith(real_root + os.sep):
+            return os.path.relpath(real, real_root)
+    return os.path.basename(real)
+
+
+def classify(rel):
+    if rel.startswith("验收单/批注回复/"):
+        return "批注回复"
+    if rel.startswith("研究/") and "批注回复" in os.path.basename(rel):
+        return "批注回复"
+    if rel.startswith("验收单/"):
+        return "验收单批注区"
+    if rel.startswith("审查/"):
+        return "审查"
+    if rel.startswith("研究/"):
+        return "研究"
+    if rel.startswith("implementation-artifacts/goal-cards/"):
+        return "goal-cards"
+    if rel.startswith("planning-artifacts/"):
+        return "planning-artifacts"
+    if rel.startswith("决策批注/"):
+        return "决策批注"
+    return "其他"
+
+
+def display_path(path):
+    real = os.path.realpath(path)
+    repo = os.path.realpath(REPO_ROOT)
+    if real == repo or real.startswith(repo + os.sep):
+        return os.path.relpath(real, repo)
+    return real
+
+
+# --------------------------------------------------------------------------
+# 块
+# --------------------------------------------------------------------------
+def stops_block(line):
+    """这一行是否该终止上一条批注的续行收集。
+
+    三类都算「批注到此为止」：
+
+    * 真空行；
+    * **引用块里的空行**——那是一个光秃秃的 ``>``，``str.strip()`` 判不出来。
+      漏掉这条，``> **User：**`` 的块会一路吃到下面 ``> **Claude（日期）：**``，
+      工具就把别人的话当成「用户说过的话」返回（真数据 2 处）；
+    * **另一个人开口**——任何以粗体标签开头的行（``**X：``），以及任何本身就命中
+      marker 的行（下一条批注的起点）。
+    """
+    if QUOTE_BLANK_RE.match(line):
+        return True
+    if SPEAKER_LABEL_RE.match(line):
+        return True
+    return bool(find_markers(line))
+
+
+def extract_block(lines, index, marker_name, marker_end, context):
+    """marker 行 + 续行。callout 取后续 ``>`` 开头的行；粗体 User 取到收尾 ``**``
+    或空行为止。
+
+    返回 ``(block, rest, has_continuation)``。
+
+    ⚠️ ``has_continuation`` 是**独立于** ``--context`` 的事实：续行到底存不存在，
+    不该由「显示几行」这个参数决定。所以扫描的下限恒为 1 行，``--context`` 只截
+    ``block`` 的长度。2026-09-19 实测：早先版本把两者混成一个上限，``--context 0``
+    会让所有换行续写的批注被判成空槽从而默认不列——参数改的是显示，结果却改了语义。
+    """
+    line = lines[index]
+    rest = line[marker_end:]
+    limit = max(context, 1)
+    collected = []
+
+    if marker_name.startswith(CALLOUT_PREFIX):
+        cursor = index + 1
+        while cursor < len(lines) and len(collected) < limit:
+            nxt = lines[cursor]
+            if not nxt.lstrip().startswith(">") or stops_block(nxt):
+                break
+            collected.append(nxt)
+            cursor += 1
+    elif re.sub(r"[*\s]", "", rest) != "":
+        # 形态 A —— `**User：正文……**`：粗体包住正文本身，收尾靠 `**` **配对**判定。
+        # marker 自带一个开启 `**`，所以从奇数起算，累计个数变回偶数 = 该粗体段闭合。
+        # ⚠️ 不能写成「见到 `**` 就停」：续行里的**行内加粗**是成对的，奇偶不变却会
+        # 骗停，把同一条批注的剩余正文变成检索不到的面。反过来，闭合即停也正好挡住
+        # 紧跟其后的 Claude 回复被算进「用户说过的话」。
+        pairs = 1 + rest.count("**")
+        if pairs % 2 != 0:
+            cursor = index + 1
+            while cursor < len(lines) and len(collected) < limit:
+                nxt = lines[cursor]
+                if stops_block(nxt):
+                    break
+                collected.append(nxt)
+                pairs += nxt.count("**")
+                if pairs % 2 == 0:
+                    break
+                cursor += 1
+    else:
+        # 形态 B —— `**User2：**` 这类**只有标签**的行：粗体包的是标签不是正文，
+        # 标签行自身已经配平，正文在后续行，到空行为止。用形态 A 的配对规则会在
+        # 第一条续行就收尾（2026-09-19 实测：三行的批注只取到两行）。
+        cursor = index + 1
+        while cursor < len(lines) and len(collected) < limit:
+            nxt = lines[cursor]
+            if stops_block(nxt):
+                break
+            collected.append(nxt)
+            cursor += 1
+
+    return [line] + collected[:context], rest, len(collected) > 0
+
+
+def is_empty_slot(rest, has_continuation):
+    """marker 后正文（去 ``**`` 与空白）为空且无续行 ⇒ 空槽。"""
+    return re.sub(r"[*\s]", "", rest) == "" and not has_continuation
+
+
+def extract_story_ids(text):
+    found = set()
+    for pattern in STORY_ID_PATTERNS:
+        for match in pattern.finditer(text):
+            found.add(match.group(0))
+    return sorted(found)
+
+
+def find_markers(line):
+    """一行上所有 marker 命中，按起点排序：[(name, matched_text, end), ...]"""
+    hits = []
+    for name, pattern in MARKERS.items():
+        for match in pattern.finditer(line):
+            hits.append((match.start(), name, match.group(0), match.end()))
+    hits.sort(key=lambda item: (item[0], item[1]))
+    return [(name, text, end) for _, name, text, end in hits]
+
+
+def search(
+    scan_roots,
+    keywords=(),
+    stories=(),
+    categories=(),
+    context=5,
+    include_empty=False,
+    include_private=False,
+    a01_path=DEFAULT_A01,
+):
+    """返回 (records, stats)。records 已按 (path, line) 确定序排好。
+
+    抛 A01Error（A01 不合约）/ PrivateRootRefused（--root 落进私人 root）。
+    """
+    private_root_ids, declared_roots = load_private_root_ids(a01_path)
+    scan_roots = list(scan_roots)
+    private_paths = build_private_paths(private_root_ids, scan_roots)
+    # 有路径可拦的 root（其余只是 A01 声明过、仓内无落地路径，不能算「已排除」）。
+    enforced_root_ids = {rid for rid, paths in private_paths.items() if paths}
+
+    if not include_private:
+        for root in scan_roots:
+            owner = private_root_of(root, private_paths)
+            if owner is not None:
+                raise PrivateRootRefused(f"按 A01 {owner} 私人 root 拒扫：{root}；需要请 --include-private 并自负授权")
+
+    pruned = set()
+    unwalkable = []
+    files = iter_markdown_files(scan_roots, private_paths, include_private, pruned, unwalkable)
+
+    lowered_keywords = [kw.lower() for kw in keywords]
+    wanted_categories = set(categories)
+
+    records = []
+    date_cache = {}
+    marker_hits = 0
+    fenced_hits = 0
+    html_comment_hits = 0
+    empty_count = 0
+    unreadable = []
+
+    for path in files:
+        text = read_text(path)
+        if text is None:
+            unreadable.append(path)
+            continue
+        lines = text.split("\n")
+        rel = relative_label(path, scan_roots)
+        category = classify(rel)
+        shown_path = display_path(path)
+        fenced = False
+        commented = False
+        for index, line in enumerate(lines):
+            if FENCE_RE.match(line):
+                fenced = not fenced
+                continue
+            # HTML 注释状态：开合可能在同一行，所以先看开、行末再看合。
+            opens = HTML_COMMENT_OPEN in line
+            closes = HTML_COMMENT_CLOSE in line
+            in_comment = commented or opens
+            if opens and not closes:
+                commented = True
+            elif closes:
+                commented = False
+            for marker_name, marker_text, marker_end in find_markers(line):
+                marker_hits += 1
+                if fenced:
+                    fenced_hits += 1
+                if in_comment:
+                    html_comment_hits += 1
+                block, rest, has_continuation = extract_block(lines, index, marker_name, marker_end, context)
+                empty = is_empty_slot(rest, has_continuation)
+                if empty:
+                    empty_count += 1
+                    if not include_empty:
+                        continue
+                if wanted_categories and category not in wanted_categories:
+                    continue
+                block_text = "\n".join(block)
+                matched = False
+                if lowered_keywords:
+                    low = block_text.lower()
+                    for kw in lowered_keywords:
+                        if kw in low:
+                            matched = True
+                            break
+                if not matched and stories:
+                    for story in stories:
+                        if story in block_text or story in shown_path:
+                            matched = True
+                            break
+                if not matched:
+                    continue
+                date, date_source = resolve_date(path, lines, date_cache)
+                records.append(
+                    {
+                        "path": shown_path,
+                        "line": index + 1,
+                        "category": category,
+                        "date": date,
+                        "date_source": date_source,
+                        "marker": marker_text,
+                        "in_fenced_code": fenced,
+                        "in_html_comment": in_comment,
+                        "story_ids": extract_story_ids(block_text + "\n" + shown_path),
+                        "excerpt": block_text,
+                        "empty": empty,
+                    }
+                )
+
+    records.sort(key=lambda rec: (sort_key_path(rec["path"]), rec["line"], rec["marker"]))
+    stats = {
+        "files_scanned": len(files),
+        "marker_hits": marker_hits,
+        "fenced_hits": fenced_hits,
+        "html_comment_hits": html_comment_hits,
+        "shown": len(records),
+        "empty": empty_count,
+        "unreadable": len(unreadable),
+        "unreadable_paths": sorted(unreadable, key=sort_key_path),
+        # ⚠️ 只报**真的有路径映射、真的在拦**的 root。A01 算出 6 个私人 root，
+        # 但仓内只有 2 个有落地路径（见 PRIVATE_RELATIVE_PATHS / PRIVATE_ABSOLUTE_PATHS）；
+        # 把另外 4 个（含两个 P4-secret）一并写进 excluded_ 会读成「它们也被拦住了」，
+        # 而实际上它们是**没有可拦的路径**，不是「已排除」。两者分开报。
+        "excluded_private_roots": [] if include_private else sorted(enforced_root_ids),
+        "private_roots_without_path": sorted(private_root_ids - enforced_root_ids),
+        "declared_roots": declared_roots,
+        "unwalkable": sorted(set(unwalkable)),
+        "pruned_private_paths": sorted({item[1] for item in pruned}, key=sort_key_path),
+    }
+    return records, stats
+
+
+# --------------------------------------------------------------------------
+# CLI
+# --------------------------------------------------------------------------
+def build_parser():
+    parser = argparse.ArgumentParser(
+        prog="annotation_search.py",
+        description="批注只读检索：关键词 / Story ID → file:line + 摘录 + 日期 + 来源类别。",
+    )
+    parser.add_argument(
+        "--keyword", action="append", default=[], help="关键词，可重复，大小写不敏感，块内任一行命中即算"
+    )
+    parser.add_argument(
+        "--story", action="append", default=[], help="Story / 卡号，可重复，大小写敏感，路径或块文本含即命中"
+    )
+    parser.add_argument("--root", action="append", default=[], help=f"扫描根，可重复，默认 {DEFAULT_ROOT}")
+    parser.add_argument("--a01", default=DEFAULT_A01, help="A01 边界声明 JSON 路径")
+    parser.add_argument(
+        "--category", action="append", default=[], choices=list(CATEGORIES), help="只看某些来源类别，可重复"
+    )
+    parser.add_argument("--context", type=int, default=5, help="摘录续行上限，默认 5")
+    parser.add_argument("--include-empty", action="store_true", help="把空槽也列出来（默认只计数）")
+    parser.add_argument("--include-private", action="store_true", help="解除 A01 私人 root 排除（自负授权）")
+    parser.add_argument("--json", action="store_true", dest="as_json", help="stdout 输出 JSON 数组")
+    return parser
+
+
+def format_summary(stats):
+    return (
+        "# files_scanned={files_scanned} marker_hits={marker_hits} shown={shown} "
+        "empty={empty} fenced={fenced_hits} html_comment={html_comment_hits} "
+        "unreadable={unreadable} unwalkable={unwalkable_count} "
+        "excluded_private_roots={excluded_private_roots}".format(unwalkable_count=len(stats["unwalkable"]), **stats)
+    )
+
+
+def main(argv=None):
+    parser = build_parser()
+    args = parser.parse_args(argv)
+
+    if not args.keyword and not args.story:
+        parser.print_usage(sys.stderr)
+        print("annotation_search.py: 至少需要一个 --keyword 或 --story", file=sys.stderr)
+        return 2
+    if args.context < 0:
+        parser.print_usage(sys.stderr)
+        print("annotation_search.py: --context 不能为负", file=sys.stderr)
+        return 2
+
+    scan_roots = args.root if args.root else [DEFAULT_ROOT]
+
+    try:
+        records, stats = search(
+            scan_roots,
+            keywords=args.keyword,
+            stories=args.story,
+            categories=args.category,
+            context=args.context,
+            include_empty=args.include_empty,
+            include_private=args.include_private,
+            a01_path=args.a01,
+        )
+    except A01Error as exc:
+        print(f"annotation_search.py: {exc}", file=sys.stderr)
+        print("annotation_search.py: A01 不可用即拒扫（fail-closed），不降级为「没有私人 root」。", file=sys.stderr)
+        return 2
+    except PrivateRootRefused as exc:
+        print(f"annotation_search.py: {exc}", file=sys.stderr)
+        return 2
+
+    if args.as_json:
+        print(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True))
+    else:
+        for rec in records:
+            head = rec["excerpt"].split("\n")[0].strip()
+            if len(head) > EXCERPT_LINE_LIMIT:
+                head = head[:EXCERPT_LINE_LIMIT] + "…"
+            print("{path}:{line} | {category} | {date}({date_source}) | {marker} | {head}".format(head=head, **rec))
+
+    print(format_summary(stats), file=sys.stderr)
+    if stats["pruned_private_paths"]:
+        print(f"# pruned_private_paths={stats['pruned_private_paths']}", file=sys.stderr)
+    if stats["unreadable_paths"]:
+        print(f"# unreadable_paths={stats['unreadable_paths']}", file=sys.stderr)
+    if stats["unwalkable"]:
+        print(f"# unwalkable_dirs={stats['unwalkable']}", file=sys.stderr)
+    if stats["private_roots_without_path"]:
+        print(
+            f"# private_roots_without_path={stats['private_roots_without_path']}"
+            "（A01 声明为私人，但仓内无落地路径可拦——不等于那里没有批注）",
+            file=sys.stderr,
+        )
+    return 0 if records else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
````

## ①附录 B：主干树协议 §5 当前版（:134-140，内嵌引文）

```
## 5. 排批（主 session）

- `/goal` 正文硬限 4000 字符 → 短 goal（≤3800，长度门脚本必跑）+ 卡文（无限制，车道必读）分层。
- 卡文事实必须在**当前主干**实测；主干前进后复用旧卡文前重验（第十批 X8：7 条事实在新主干上失效）。
- 台账是全部卡的共同写入面 → **只有主 session 改**；卡在验收单写「台账待登记条目」。
- **tests/unit 既有红基线**：主 session 每批开跑前落一份 nodeid 口径的基线（`_bmad-output/审查/evidence-b<N>/unit-red-baseline-<主干SHA>.txt`），车道开工/收工各跑一次目录级并 `diff`，差集才算本卡引入或修复；「298/289」这类含日志噪音的行数不得作分母。
- 每张卡的完成条件含「本卡未证明什么」必填；数字与命令输出一致（`wc -m` 计字符非字节）。
```

## ② 作者自述 —— 请独立核对，不要采信

1. **零写**：除 stdout / stderr 外零写调用。唯一子进程是 `git log -1 --format=%cs -- <file>`（环境经 `git_env()` 剃掉全部 `GIT_*`）。自证 = 一道 AST 门（数 `open(mode 含 w/a/x/+)`、`os.remove/unlink/rename/replace/makedirs/mkdir/rmdir`、`shutil.*`、`Path.write_*` 等写调用，以及 argv[0:2] 不是 `["git","log"]` 的 subprocess 调用）：被测文件计数 **0**、验伪锚探针计数 **2**。
2. **不 import 目标目录内任何模块**；stdlib-only（argparse / json / os / re / subprocess / sys / unicodedata / pathlib）。
3. **私人 root 名单不写死**：从 A01 的 `privacy_ceiling ∈ {P3-high-sensitive, P4-secret}`（5 条）∪ `proposed_action` 含 `private-locator`（`ROOT-ANCHORED-PRD`）算出；root_id → 路径映射由脚本自带（A01 无 path 字段）；判定用 `os.path.realpath` 再 `fold_path()`（NFC + casefold）前缀比较，另有 `canvas-vault` 组件名与 PRD basename 两条安全网。
4. **A01 缺失 / 顶层无 `source_roots` / 某条缺 `privacy_ceiling` ⇒ rc=2**（fail-closed），不降级。
5. **真数据锚必命中**：`--keyword codex` 命中 `_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:494`；`--keyword anki` 命中 `_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md:163`；三主题 FSRS / 跨vault / README 各 ≥1。
6. **目标目录前后逐字同**：对 `_bmad-output` 逐文件 sha256 再总 sha（排除本卡落档目录 `审查/evidence-g11/` 与 `__pycache__`），跑前跑后相同；同口径对两文件小目录改一字节会变（证明摘要对内容敏感）。
7. **协议本体零改动**：条款只以 patch 交付（`git apply --check` rc=0；生成时基 = 97 行版），本卡不曾直改任何工作树的协议文件。

## ③ 请优先回答的问题（按重要性排序）

0. **只读是不是真只读**：AST 门只看语法形态，请找**门未覆盖的路径** —— 有没有执行路径会落盘、改 mtime、留缓存？`git log` 子进程会不会在带自定义 filter / hook 的仓库里产生副作用，或因 cwd 取自被扫文件所在目录而在某些输入下出问题？`--root` 指向软链、`..` 路径、hardlink、大小写不敏感文件系统上的 `Canvas-Vault`、NFD 形态目录名 —— realpath 之外还有没有**未被拦下的输入**能落进私人 root？反方向也要看：把「每个扫描根的各级祖先」当基点来推导私人路径，会不会把**不该私有**的目录误判为私有？
1. **空槽与不可读文件是否被静默当 0**（契约 `:142` 明确要求 NUL / 非法编码不能静默当 0）。
2. **关键词只匹配 marker 行还是整块**：多行续写的批注，正文含关键词而首行不含时会不会漏？反过来，块提取会不会越界把不属于该批注的后续内容也算进命中面？
3. **`date_source` 会不会把 git 提交日期冒充成批注写下的时刻而不标明**；frontmatter 解析（不引 PyYAML）在 `---` 出现在正文、key 重复、值带引号时的行为。
4. **输出排序在中文路径 / NFC-NFD 差异下是否仍确定**；同参数两次运行是否逐字同。
5. **测试是否真读真 `_bmad-output`（DD-03 禁 mock）**，以及真数据用例断言行号（:494 / :163）在主干文件变动后的脆弱性 —— 这是设计选择还是隐患，若行号漂移应如何登记？另请点名：有没有哪条测试在被测代码删掉整段逻辑后仍然全绿（即那道门其实锁不住它声称锁住的东西）。
6. **patch 是否只加一条、只加在 §5、§1-§4 一字未改**；新条款措辞是否与协议既有条款冲突或无法执行。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- `file:line`
- 一句能让人自己验证的思路：具体的**负控输入**或**对照输入** → 观察到的错误输出。
- 若属于「**门未覆盖的路径**」或「**未被拦下的输入**」，请明确说是哪道门、哪类输入。

宁可少报也不要报推测：不确定的降级为 LOW 或不报，并说明不确定在哪里。
措辞请用：负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径。

## ⑤ 边界

- 只读复核，不修改任何文件（build 模式本身已禁 Bash / Write），不连任何数据库（本卡不连库）。
- 不评契约 `:132` 的 T3 broad discovery（`user`/`USer` 异常大小写、role 字段、转述、无冒号编号）—— 该层须人工分类，明确不在本卡范围。
- 不评契约 `:82` 的非 Markdown 容器（Canvas JSON / JSONL / YAML / 对话导出）—— 明确不在本卡范围。
- 不评修正链去重 / atomization、A02 ledger、G1-2 开卡小抄工作流、G1-3 能力证据台账 —— 都是另卡。
- 不要求对 live vault 或锚定 PRD 实跑 `--include-private`；那两处本卡默认连读都排除。
