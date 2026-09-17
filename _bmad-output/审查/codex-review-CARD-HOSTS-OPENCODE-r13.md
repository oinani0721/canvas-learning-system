> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-13
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r13.md)"`
> 审查绑定: `ff9e0156`（结论 **BLOCKER=0 / HIGH=0 / MEDIUM=0** ✅ 并**同意**「到此为止」的边界判断；同时更正了车道一处事实断言（macOS 有 `F_GETPATH`）。整改在 `d6f96fa8`，仅措辞）
> ⚠️ attempt-1 挂起（进程在但 stderr 64 分钟无写入、末行 `ERROR: Reconnecting... 2/5`、存档 0 字节），
> 按协议 §2 停掉并原样重发；本存档来自 **attempt-2**，`.stderr` 亦为 attempt-2 那份
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定最终 HEAD **`ff9e0156eb04d3baa4be93ebe07b1e4ea598ac1d`**，限定文件与该提交一致。

**本轮 BLOCKER=0 HIGH=0 MEDIUM=0；未发现新增 LOW。** 同意把剩余并发窗口作为明确的移交限制，不继续叠加检查。

**F1：同意“到此为止”，但需限定理由。**

在“其他进程仍可修改相关目录、没有排他控制”的模型下，增加路径复查不能保证检查后的路径持续不变。真正排除这种交错，需要停止相关修改者，或通过权限隔离排除其修改能力；普通协作锁无法约束不合作进程。

“按 fd 反查路径无”应限定为 Python `os` 没有可移植直接接口：macOS 有 `F_GETPATH`，但它仍只是一次查询，不能闭合检查与使用之间的窗口。这不改变上述裁定。[Apple 官方说明](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fcntl.2.html)

**F2：收工核与失败留链的组合合理，未见新增独立缺陷。**

- [deploy-vault.sh:1286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1286) 从 `vault` 路径重新打开，再逐级打开 `.agents/skills`；缺项时在 `ok=True` 和成功输出之前失败，随后报告已创建条目。
- 它只核对本次目录采样中的**名称存在性**，不重新证明每个条目的类型、目标和身份，不能称为完整或原子的最终验收。
- “之后不再写”只适用于建链函数；调用方在 `:1048` 随后发布 `AGENTS.md`，Phase B 后续还写 key。
- [deploy-vault.sh:1327](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1327) 不自动删除残链，避免按名字清理误删替代对象，取舍合理。但报告列出的是**原目标路径**，不保证搬移后的残链仍在那里。

已知边界的一句复现思路：在 `deploy-vault.sh:1294` 列目录完成后搬移该目录，即可说明最后一次检查不能保证返回时路径仍不变；本轮未执行写盘复现。

**F3：按本卡威胁模型，记为信息项／已接受限制。**

“移交限制 + 非并发环境不可达”方向正确，建议改成：**“相关路径未发生并发变更时，此类竞态不可达。”** 并发来源也包括同步软件、另一部署进程和人工操作；范围包含 vault 的祖先、源目录及叶子条目，不仅是 `.agents/skills` 被搬移。若以后用于共享目录、不可信协作者或跨权限部署，须重新定级。

前述问题的核对结果：

| 问题 | 最终 HEAD 的结论 |
|---|---|
| 技能发现与相对落点 | 当前 OpenCode 官方实现跟随软链，可能经两个路径读取并产生重复名称警告，但最终按 frontmatter `name` 保留一个条目；不能声称只物理读取一次。相对软链从自身父目录解析，与 `.git` 是文件还是目录无关。[官方源码](https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/opencode/src/skill/index.ts) |
| dry 零写 | 新 heredoc 均在函数内，dry 在调用它们之前返回；静态未见本卡新增的提前写入路径。未独立重跑“整个 tmp 根零写”实验。 |
| 子串门与文案 | 非注释行没有字面 `opencode.json`；拼接结果只进入说明文案，不成为配置写入目标。作为文案例外可以接受，但词法门不是运行期安全证明。文案明确要求 vault 根的项目配置，并禁止用户级配置。 |
| D-26(i) | `cls_forbidden_paths.py:270` 是唯一专用登记点；删除后，普通且不与其他保护面重叠的路径没有专门兜底。其他保护规则仍可能因路径重叠而拒绝。`:239–240` 已处理保护目标为 `/` 的情况。 |
| 写面与既有门 | 根目录、`AGENTS.md`、动态叶子及中间目录均有对应判据。最终版已无 `AGENTS.md.tmp → mv`，新增的是 **2 个标签，不是 3 个**；精确集合门仍为相等比较，属于登记，没有改松。已有宿主拒绝门和禁件门仍保留。 |

OpenCode 发现结论核对的是当前公开源码，未验证本机安装版本。

**F4：建议验收单采用以下措辞：**

> 本绑定器要求部署期间 vault、其祖先路径及相关源目录、目标目录和条目不被其他进程并发搬移、替换或删除。目录 fd 固定对象身份，不固定其在路径树中的位置。收工核从 vault 路径重新解析，检查本次采样中所需条目名称是否存在；它不是原子快照，也不保证检查后路径持续不变。相关路径无上述并发变更时，此类竞态不可达。检测失败时返回非零，不自动回滚此前创建的软链；报告列出原目标路径，需在停止并发修改后人工确认残留的实际位置与状态。

验证范围：Bash 语法检查、两个内嵌 Python 程序编译检查、内存抽取执行的 7 个静态测试函数及 `under()` 边界检查均通过。未写文件、未连接数据库、未运行宿主模型；作者 Q-1/Q-2 的行为负控未独立重跑。


