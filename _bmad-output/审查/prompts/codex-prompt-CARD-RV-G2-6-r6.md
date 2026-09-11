# CARD-RV-G2-6（U3-A）独立复核请求（round-6）

## 一 背景与最小读取面

worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，最终 HEAD **`8fb59bd2`**。

本卡前五轮：r1 绑 `6bdb0fab`、r2 `736eb490`、r3 `977d1e6d`、r4 `ee18eb44`、
**r5 绑 `ee18eb44`，结果 0 BLOCKER / 2 HIGH / 6 MEDIUM / 2 LOW**。
我当时按协议「轮次上限 5」停手交人审；但卡文的完成条件是硬性的「绑最终 HEAD 的一轮
BLOCKER/HIGH = 0」，复核指出未满足，故本轮**只针对你 r5 的那两条 HIGH** 做整改后再送审。

⚠️ 期间同车道跑完了 CARD-G2-7a（U3-B，5 轮、r3/r4/r5 连续 0B/0H），它改过**同一份**
`verify_vault_install.py`。所以我先在当前 HEAD 复现了那两条 HIGH，确认没被顺带修掉。

**请只读以下五处（不要读别的、不要读 live vault、不要执行安装脚本）：**

1. 本轮整改：`git diff 7cb2d93e 8fb59bd2 -- . ':(exclude)_bmad-output'`
2. 本卡（U3-A）原始改动面：`git diff da690bf8 086771d3 -- . ':(exclude)_bmad-output'`
3. 校验器全文：`scripts/verify_vault_install.py`
4. 门文件：`backend/tests/unit/test_vault_install_manifest.py`
5. 定性表：`_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md`

## 二 你 r5 两条 HIGH 的处置

| 你给的 | 复现（当前 HEAD） | 修法 |
|---|---|---|
| **HIGH-1** `kind=file` 把软链目标查询失败当成「不匹配」，可假绿 | 成立。`_entry_state` 是 lstat 语义，只覆盖「目录项本身查不到」；`kind == "file"` 分支的 `path.is_file()` 跟随软链且吞 `OSError` ⇒ 链目标查不到时返回 `False` | 改走三态 `_resolved_kind()`（`os.stat` 跟随链、区分 `unreadable`）：查不到 → `None`。`dir`/`nondir` 维持 lstat 语义（对应 `find -type d` 不跟随链），因带 `not is_symlink()` 不受影响 |
| **HIGH-2** 同类型设备节点丢失设备号，不同对象判 match | 成立（`:711` 只记 `S_IFMT`） | 字符/块设备摘要带 `st_rdev` |

门：新增两条，变异 **2/2 KILLED**，各绑自己声称的断言。H2 的门读系统已有的
`/dev/null` 与 `/dev/zero`（只 `lstat` + 摘要，不创建节点），并带正控先断言两者同为字符设备。

## 三 请按重要性排序回答的问题

1. **H1 的修法是否完整**：`kind == "file"` 现在走 `_resolved_kind`，但 `dir` / `nondir`
   仍用 `is_dir() and not is_symlink()`。我的论证是「带 `not is_symlink()` 后链一律判 False、
   不依赖跟随后的查询结果」。这个论证成立吗？`is_dir()` 自身吞 `OSError` 的路径还有没有残留？
2. **H1 的三态是否传播到位**：`_kind_ok` 返回 `None` 之后，`matches_exact` / `is_under_exclusion` /
   `hits_for` 到 `verify()` 的整条链上，有没有哪一段把 `None` 又压回二值？
3. **H2 的收窄是否够**：现在摘要是 `(S_IFMT, st_rdev)`。FIFO / socket 仍只有类型位——
   它们没有设备号，这个处理对吗？还有别的「同类型不同对象」会碰撞吗？
4. r5 你给的 6 MEDIUM / 2 LOW 我**未处置**（轮次与范围原因，已登记转卡）。其中有哪几条
   现在看应当优先？
5. 现在还有哪些声明比证据宽？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条：一句问题 + `file:line` + 一句复现思路。
无问题的项明说「核对结果：无问题」并说明核对程度。

## 五 边界

只读审查；不执行安装脚本；不连数据库；不评 U3-B/U3-C 的消费方。
不需要攻击性内容；关心**误伤与漏报**。
