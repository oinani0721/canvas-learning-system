> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-9
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r9.md)"`
> 审查绑定: `d102b847`（结论 BLOCKER=0 / **HIGH=0** / MEDIUM=1；整改在 `d86f0bc4`，B3 措辞问题已在 `e8bdd4bd` 自查修掉）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定 **`d102b847f23892650fe2c10996d793a035b14a6a`**，本轮 **BLOCKER=0 HIGH=0 MEDIUM=1**。审查期间出现的工作区修改未计入；以下行号均按该提交。

**MEDIUM-1：源检查通过后仍可被替换，后置 inode 比对会共同外指而通过。**

位置：[scripts/deploy-vault.sh:1164](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1164)、`:1172–1174`、`:1212–1218`。

`lstat` 只证明检查当时源条目是真目录；代码没有保存该合格条目的身份。随后，目标软链解析和“期望源”解析都重新跟随当前路径。如果源已被换成外部软链，两边得到同一个外部 inode，比对仍通过。

**一句复现思路：**在最后一次源 `lstat` 成功后、首次建链前，将 `V/.claude/skills/x` 替换为指向外部目录的软链，后续两次解析同指外部，绑定 helper 仍可成功。

这是**源资格检查之后的第三个窗口**，不同于已登记的清理分支 TOCTOU、打开 vault 前祖先替换。没有据此发现外部写入，故定 MEDIUM。修复需要让后核对照此前确认合格的源条目身份；仅保留源父目录 fd 不够。

对 B1–B4 的回答：

- **B1：静态目录外指已闭合，完整性质尚未闭合。**预置的 `.claude`、`skills`、技能条目软链都会在建叶子链前被拒。真目录内部的 `SKILL.md` 软链或普通文件硬链接不在检查范围；原先对目录做 `pwd -P` 比较也不能证明这些内容没有外部别名，不能将其另算作本次遗漏。
- **B2：两层互补，不能直接删任一层。**删源检查，预置外指源软链会让后核两边相等；删 inode 比对，取得 `sfd` 后将 `.agents` 搬到另一目录，链接字面仍正确，但 `../../` 的实际起点改变，源预检无法发现，现有 inode 比对可以拒绝。
- **B3：正常拷贝得到的真目录满足新增约束。**用户自建的源条目软链，即使指向 vault 内，也一律拒绝；不能宣称支持这种形态。`:1168` 将所有拒绝都解释成“落点会在 vault 之外”，对内部软链不准确。
- **B4：不能给 MEDIUM=0。**除两个已登记窗口外，还剩上述源检查后的替换窗口。

其余问题核对结果：

| 项目 | 结论 |
|---|---|
| OpenCode 发现与去重 | 按题设的多根扫描、frontmatter `name` 去重语义，两条路径可被枚举，但最终保留一个同名技能；不能据此声称文件只被读取一次。静态树本身不能证明扫描器是否跟随软链；即使忽略 `.agents` 一侧，真实 `.claude` 目录仍提供技能。 |
| 相对软链 | `../../.claude/skills/<n>` 从 `.agents/skills` 回到 vault，落点正确，与 `.git` 是文件还是目录无关。 |
| dry 零写 | 未发现本卡新增的 dry 写入路径：`:1459–1465` 提前返回，新增 heredoc 仅在 apply 调用中执行。前后树快照不能证明期间没有建后删；本轮未运行动态零写实验。 |
| `opencode.json` 子串 | 固定提交的非注释行命中 **0**。运行期拼接仅进入 AGENTS.md 正文，没有成为配置写入路径；此处用途合理，但字面门本身不能证明运行期零写。 |
| D-26(i) | `cls_forbidden_paths.py:270` 是唯一专门登记该配置根的锚；删除后普通 `opencode.jsonc`、`.gitignore` 没有专门兜底。但特殊后代仍可能命中其他规则，不能推广为全部放行。`:239–240` 和 `:589–590` 已覆盖所问根路径退化。 |
| AGENTS.md 与写面 | 文案明确要求 vault 根的项目配置，并禁止修改用户级配置。最终已无 `.tmp → mv`：`:1349` 直接以 `O_EXCL` 新建，已有目标一律拒绝。根、正文及动态叶子均有登记或补判。 |
| 三条既有门 | 最终新增的是 **2 个 label**，不是旧描述的 3 个；精确集合仍保留，属于登记实际写面。codex/dsh 的 rc64＋E-1 门及三个禁字面项仍在。 |

独立 AST 枚举确认：本卡 **13 条**调用 `_oc_run`／`_oc_forbid` 的测试均有 rc 断言；新增源链接门同时要求 rc73、原因、零残链、无 AGENTS.md。两个内嵌 Python 块编译检查通过。没有运行 pytest、部署、数据库或模型；作者的负控结果及 PREV/current dry 输出逐字一致，本轮未动态复现。


