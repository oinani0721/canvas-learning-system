# 独立复核请求 — CARD-G2-6 round-2（针对 round-1 四条意见的整改）

## 一 背景与最小读取面

这是同一张卡的第二轮。round-1 提了 1 BLOCKER + 1 HIGH + 2 MEDIUM，四条我们都在本机
独立复现成立，然后逐条改了代码并补了回归测试。本轮请复核**整改本身**。

被改的三个文件（绝对路径，只读这些即可）：

1. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py`
2. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json`
3. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/unit/test_vault_install_manifest.py`

参考（按需）：
4. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/install-vault.sh`
   （`:61-69`、`:74-109` 两段是排除语义的真相源）
5. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/_bmad-output/审查/codex-review-CARD-G2-6.md`
   （round-1 原文）

## 二 四条整改的做法（请独立核对，不要采信）

- **BLOCKER（树外报告若与树内文件同 inode 会写穿）**：对**已存在**的 `--report` 文件检查
  `st_nlink > 1`，不是独占就退出 2 拒写。理由是 `resolve()` 解得开符号链接、解不开硬链接。
- **HIGH（目录摘要没应用排除规则，正常部署被判 content-drift）**：抽出 `ExcludeMatcher`，
  让**分类、extra 豁免、目录摘要过滤三处共用同一套判定**；摘要按各自 vault 根整棵剔除
  被排除的子树（`is_under_exclusion` 会检查该条目及其所有祖先前缀）。
- **MEDIUM（排除模式没表达脚本的文件类型条件）**：清单加 `kind` 字段（`dir` / `file` / 空=不限），
  `.claude/**/__pycache__` 标 `dir`（对应 `find -type d`）、`.claude/hooks/pending_archives*.jsonl`
  标 `file`（对应 `rm -f`），`_kind_ok()` 在三个匹配点统一生效。
- **MEDIUM（非字符串 action 抛 TypeError 逃出捕获面）**：`load_manifest` 先验 `isinstance(str)`
  再查枚举，`kind` 同样先验类型。

回归测试由 30 条增至 42 条，四条各有反例。另对四处新逻辑各做了一轮「临时置为不生效、
看是否恰好对应的测试变红」的验证。

## 三 请回答的问题（按重要性排序）

① **BLOCKER 是否真的堵住了，堵法有没有遗漏的同类形态**：除了「报告路径与树内文件共享
   inode」，还有没有别的方式能让写报告这一步影响到 `--vault` / `--source` 里的内容？
   `st_nlink` 这个判据在报告文件**不存在**、是符号链接、或位于不同文件系统时分别如何表现？

② **HIGH 的修复是否完整**：`ExcludeMatcher` 的三个使用点（分类、extra 豁免、摘要过滤）
   语义是否一致？`is_under_exclusion` 逐级检查祖先前缀的做法，在「祖先被排除但自身不该被
   排除」或反过来的情形下是否正确？摘要从「递归调用」改成「rglob + 叶子摘要」后，
   有没有哪种目录结构的差异现在会被判等（即摘要变弱了）？

③ **`kind` 语义与脚本是否真的对齐**：`find -type d` 对符号链接指向目录的情形如何处理，
   校验器用 `is_dir() and not is_symlink()` 是否对得上？`rm -f` 对符号链接指向文件的情形呢？
   清单里其它没标 `kind` 的排除项（`原白板/**`、`outputs/**` 等）留空是否恰当？

④ **schema 校验是否还有能逃出 `ManifestError` 的输入**：请设想各种畸形清单（嵌套类型、
   超长值、`extra_scan` 里的非法项、path 里的特殊字符），判断哪些会以 `ManifestError`
   以外的异常终止，从而拿不到承诺的退出码 2。

⑤ **回归测试是否真的能在修复前打红**：`:xxx` 这四条新测试（硬链接拒绝、正确部署不报 drift、
   类型条件、非字符串 action），如果把对应修复逐个撤掉，是否恰好只有它自己变红？
   有没有哪条其实是被别的断言兜住的？另外测试里的合成 vault 与真实 vault 形态差异，
   会不会让某条测试在真实场景下失效？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条写：**结论一句** + **依据（文件:行）** +
**若要修的话改哪里**。没有问题的分级请显式写「无」。最后给一段总评，说明你实际核对了
哪些断言、哪些因读取面限制未能核对。若认为 round-1 的某条整改**方向错了**，请直接说。

## 五 边界

- 不评价下一张卡的范围：把五个部署动作做成 CLI（G2-7）、激活的事务与回滚（G2-8）。
- 不评价 `install-vault.sh` 现行会复制那两个本机私有文件这一行为本身（本卡只登记）。
- 不需要运行 `install-vault.sh`。
- 现网 vault 报告里的 5 个 `extra` 项应否补进清单，本卡未作裁定，不必替我们裁。
