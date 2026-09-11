# CARD-RV-G2-6（U3-A）独立复核请求（round-7）

## 一 背景与最小读取面

worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，最终 HEAD **`fd7e91f3`**。

本卡前五轮：r1 绑 `6bdb0fab`、r2 `736eb490`、r3 `977d1e6d`、r4 `ee18eb44`、
**r5 绑 `ee18eb44`，结果 0 BLOCKER / 2 HIGH / 6 MEDIUM / 2 LOW**。
我当时按协议「轮次上限 5」停手交人审；但卡文的完成条件是硬性的「绑最终 HEAD 的一轮
BLOCKER/HIGH = 0」，复核指出未满足，故本轮**只针对你 r5 的那两条 HIGH** 做整改后再送审。

⚠️ 期间同车道跑完了 CARD-G2-7a（U3-B，5 轮、r3/r4/r5 连续 0B/0H），它改过**同一份**
`verify_vault_install.py`。所以我先在当前 HEAD 复现了那两条 HIGH，确认没被顺带修掉。

**请只读以下五处（不要读别的、不要读 live vault、不要执行安装脚本）：**

1. 本轮整改：`git diff 7cb2d93e fd7e91f3 -- . ':(exclude)_bmad-output'`
2. 本卡（U3-A）原始改动面：`git diff da690bf8 086771d3 -- . ':(exclude)_bmad-output'`
3. 校验器全文：`scripts/verify_vault_install.py`
4. 门文件：`backend/tests/unit/test_vault_install_manifest.py`
5. 定性表：`_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md`

## 二 你 round-6 的 HIGH 与那条 MEDIUM 的处置

| 你给的 | 修法 |
|---|---|
| **HIGH（旧 M2 升级）** extra 消费端丢失类型查询失败，可最终假绿 | `_collect_extra` 建 `kind_unreadable` 列表透传给 `is_under_exclusion`，命中时**登记 `report.unreadable`** 并跳过（不进 extra 也不进 allowed-extra） |
| **M1**（我 r6 修法引入的误报）不存在的精确 `exclude + kind=file` 被误阻断 | `kind == "file"` 分支对 `state == "absent"` 短路返回 `False` —— 不存在是**确定的否定答案**，不是「问不出来」 |

变异 **3/3 KILLED**，三个变异体照出三种形态：撤掉透传 ⇒ `allowed-extra=['alias/f.json']`（你描述的原缺陷）；
保留透传但**只 `continue` 不登记** ⇒ 两个桶都空、rc 照样 0（这是我第一版的写法，门抓住了这个中间态）；
撤掉 `absent` 短路 ⇒ 误报 unreadable。

**同一错误第三次出现**已如实记录：`_resolved_kind` 只有四态、缺 `absent` 这一档 ——
round-4 修 `_entry_state` 的 ENOTDIR、round-5 新写 `_resolved_kind` 时原样重犯、round-6 消费它时再犯。

你 r6 的 M3/M4/M5/M6 与 L1/L2 **本轮未处置**（已登记转卡）。

## 三 请按重要性排序回答的问题

1. **本轮两处修法是否完整**：`kind == "file"` 现在走 `_resolved_kind`，但 `dir` / `nondir`
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
