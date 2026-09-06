# 独立复核请求 — CARD-G2-6 round-3（第二轮整改后的收口复核）

## 一 背景与最小读取面

同一张卡的第三轮，也是最后一轮。前两轮 + 一轮多视角对抗审查合计挑出 14 个独立缺陷，
每条都在本机复现成立后才改。本轮请复核**第二轮整改本身是否闭环、有没有引入新问题**。

只读下列文件（绝对路径）：

1. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py`
2. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json`
3. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/unit/test_vault_install_manifest.py`
4. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/install-vault.sh`
   （`:61-69`、`:74-109` 是排除与部署语义的真相源）

## 二 第二轮改了什么（请独立核对，不要采信）

**报告落点（两条阻断级）**
- 承重的那道换成了**写法**：`_write_report()` 在同目录用 `O_CREAT|O_EXCL` 独占创建临时文件，
  写完 `os.replace` 换目录项，**绝不原地覆盖已有 inode**。失败一律转 `ReportWriteError` → rc=2。
- 落点判据升级为**禁写根集合**：`_forbidden_roots(tree)` = 树本身 + 树内所有软链的解析目标。
  原来的路径前缀比较与 `st_nlink` 检查保留，但只当可读的早退，不再承重。

**遍历与摘要**
- 自写 `_walk()`（`os.scandir` + 显式捕获 OSError）替代 `Path.rglob`，读不进去的条目产出
  `unreadable`，计入摘要**也计入退出码**。

**清单语义**
- `kind` 增加 `nondir`（对应脚本 `:86` 那条强制删除的实际可删集合）；去掉先前误加在
  `learning_events.jsonl` / `workspace.json` 上的 `kind`；补 `raw/**`、`templates/**`
  两条 exclude（`:74` 的 mkdir 循环覆盖六个骨架目录，而 `:68` 的注释只点名了四个）。
- `_check_relative_segment()` 给 `items[].path` 与 `extra_scan.dir` **共用**，并做路径规范化；
  规范化之后才查重复。清单读取阶段把 OSError / UnicodeDecodeError / ValueError 转 ManifestError。
- 正则去掉 `$` 锚点，所有匹配调用点改 `fullmatch()`；`GLOB_CHARS` 收窄为 `*?`，
  `[` 统一按字面量（代价：不支持字符类模式）。

测试 30 → 68 条；另有 16 条变异逐条验证「拆掉某段逻辑，恰好只有对应的那几条测试变红」。

## 三 请回答的问题（按重要性排序）

① **落点与写法是否真的闭环**：除了硬链接、`/dev/fd/N` 别名、树内软链指向树外这三种，
   还有没有别的方式能让「写报告」这一步影响到 `--vault` / `--source` 里看得见的内容？
   `_write_report` 的临时文件路径（`.<name>.tmp-<pid>`）本身有没有问题——同名残留、
   父目录恰好是被审树的一部分、`os.replace` 跨文件系统、以及并发跑两个实例？
   `_forbidden_roots` 用 `resolve()` 收集软链目标，对悬空软链、软链成环、
   以及指向被审树**内部**的软链分别是什么行为？

② **`unreadable` 的语义是否自洽**：`_walk` 在哪些情形下会产出它、哪些情形会漏掉？
   摘要里写同一个标记意味着「两侧都读不进去」会判等——退出码靠 `unreadable` 非空兜住，
   这个兜法在哪些情形下会失效？`_leaf_digest` 里那个 `except OSError` 返回的
   `U:unreadable` 与 `_walk` 的 unreadable 是不是同一件事，会不会互相掩盖？

③ **清单语义与脚本是否仍然等价**：补上的 `raw/**`、`templates/**` 是否恰当（`:74` 的循环
   对六个骨架目录一视同仁，但 `:68` 的注释只列了四个——按代码补而不按注释补，这个取舍对吗）？
   `nondir` 与脚本 `:86` 的实际可删集合是否逐项一致？去掉 `learning_events.jsonl` /
   `workspace.json` 的 `kind` 之后，有没有新的误判面？

④ **清单校验是否还有能逃出 `ManifestError` 的输入**：`extra_scan` 现在走与 path 同一套校验，
   但 `match` 只校验了「非空字符串」——一个语法古怪的 `match` 值会怎样？
   路径规范化（`PurePosixPath`）对 `.`、多重 `//`、以及 Windows 风格分隔符分别怎么处理，
   规范化之后的重复检查会不会误判两个本来不同的条目为重复？

⑤ **68 条测试与 16 条变异是否名副其实**：有没有哪条断言是恒真的、或者被别的分支兜住？
   特别看这几条新加的：`test_unreadable_alone_still_blocks`（它刻意让两侧都不可读，
   使 unreadable 成为唯一差异来源）、`test_report_behind_vault_symlink_is_refused`、
   `test_bracket_is_literal_in_both_places`、以及那条按函数边界圈定写调用的 AST 门
   （它豁免了 `sys.stdout.write` / `sys.stderr.write`，这个豁免开得够窄吗）。

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条写：**结论一句** + **依据（文件:行）** +
**若要修的话改哪里**。没有问题的分级请显式写「无」。最后给一段总评，说明你实际核对了
哪些断言、哪些因读取面限制未能核对。若认为第二轮的某条整改**方向错了**，请直接说。

## 五 边界

- 不评价下一张卡的范围：五个部署动作做成 CLI（G2-7）、激活的事务与回滚（G2-8）。
- 不评价 `install-vault.sh` 现行会复制那两个本机私有文件这一行为本身（本卡只登记）。
- `extra` 覆盖面是卡文钦定的三条（`.claude/*`、`.obsidian/*.json`、`.obsidian/plugins/*`），
  本卡未改；它看不见 `.obsidian/` 下的非 json 件，这一点已登记转下一张卡，不必替我们裁。
- 不需要运行 `install-vault.sh`。
