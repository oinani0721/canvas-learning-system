> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-8
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r8.md)"`
> 审查绑定: `9df308be`（结论 BLOCKER=0 / **HIGH=0** / MEDIUM=2；其一已在 `8bfe8f24` 自查修掉，另一条「我真删掉了一条规则」整改在 `d102b847`）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定 **`9df308be6501065886cde450dd1339ac9f6f6924`**：**BLOCKER=0 HIGH=0 MEDIUM=2 LOW=0**。本轮两处整改的直接问题已修正，但不能判定“只剩两个已登记窗口”。

以下行号均按该提交的 Git blob；工作区已有一处额外补丁，未计入闭合证据。

1. **MEDIUM — A1：inode 相等没有完整替代原来的物理落点约束。**  
   [scripts/deploy-vault.sh:1179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1179)：这里的 `stat(..., follow_symlinks=True)` 与 `:1174` 的打开操作会共同跟随技能源软链；两边 `(dev, ino)` 相同，不能证明目标物理位于 vault 内。`:982/:991` 的 `-d` 接受源软链，`:1011` 检查的是输出路径；首次生成时输出叶子尚不存在，无法暴露未来目标。原 shell 精确物理路径比较会拒绝这种输入。  
   **复现思路：**在安装结束时预置 `V/.claude/skills/x -> /ordinary-outside/x`，首次生成绑定，当前 Python 检查通过，而被删检查会失败。  
   应在 Python 侧补回技能源目录的约束；无需恢复会剥尾换行的 shell 实现。

2. **MEDIUM — A3：仍有一条行为门只验产物、不验成功。**  
   [backend/tests/unit/test_deploy_vault_sh.py:4552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4552)：`test_hosts_opencode_skill_name_survives_the_shell_python_handoff` 没有断言 `r.returncode`，后面的名字与 `readlink` 断言仍可能接受失败部署。只读 AST 枚举本卡 12 条调用 `_oc_run`／`_oc_forbid` 的测试，仅这一条缺失。  
   **复现思路：**针对 ` .git` 输入，在正确建链后返回失败，使部署 rc=73，该测试现有产物断言仍成立。  
   工作区新增的三行已补这个断言，但它们**不属于 `9df308be`**。

其余问题的判定如下：

| 问题 | 独立复核结果 |
|---|---|
| **A1：本轮直接整改** | 两条换行行为门已断言 rc=0（测试 `:4614/:4648`）；夹具补 `/` 及目录、`SKILL.md` 控制组正确（`:4607/:4619/:4620`）。父目录非软链与叶子目标字符串检查仍在，但物理包含关系存在上面的 MEDIUM。 |
| **A2：AGENTS.md 在位判** | **互补，不能单独替代内部检查。** shell `:1064` 只检查返回后路径是非软链普通文件；Python `:1311` 用 `O_EXCL\|O_NOFOLLOW` 拒绝覆盖，`:1337–1344` 核对 fd／路径身份及各自链接数。现有文件即使带生成标记也拒绝覆盖。 |
| **0：OpenCode 发现与去重** | 官方 `v1.18.31` 源码启用跟随软链；两个不同路径可能各解析一次，随后按 frontmatter `name` 存入同一字典键，最终一个技能，可能有重复名称警告。不能宣称“只读取一次”，也不宜保证最终保留哪个路径。[官方源码](https://github.com/anomalyco/opencode/blob/v1.18.31/packages/opencode/src/skill/index.ts#L97-L227) |
| **1：dry 零写** | 限定代码面内未发现新增写入路径：非注释行无 `<<<`，`:213` 禁止 Python 字节码写入，新增 heredoc 仅在 apply 调用链执行，dry 在 `:1427` 返回。**本轮未实跑零写验收**；前后树快照也不能证明没有发生“创建后删除”的瞬时写入。 |
| **2：禁串与拼接** | 非注释行字面 `opencode.json` 命中数为 **0**。运行期完整文件名只进入说明正文，没有进入配置写入操作；本次用途合理。但这证明了禁串门只是文本门，不能独立证明不存在动态拼接后的写入。 |
| **3：D-26(i)** | `cls_forbidden_paths.py:270` 是唯一专门登记该目录的规则；删掉后普通、不重叠其他禁面的该目录路径没有专门兜底。其他保护目标重叠或 fail-closed 错误仍可能拒绝，因此不能说“删行后一切环境都放行”。`under():239` 明确处理根，`main():589` 补空段列表，未见所问根退化旁路。 |
| **4：AGENTS.md 文案** | `deploy-vault.sh:1407–1413` 输出完整项目文件名、明确 vault 根目录、`remote` 和 `/mcp`，并明确禁止改用户级目录；没有因源码拼接而使最终正文含糊。[项目配置文档](https://opencode.ai/docs/config/#per-project)、[remote MCP 文档](https://opencode.ai/docs/mcp-servers/#remote) |
| **5：live／worktree** | 在所述正常目录树下，两级 `..` 均回到 `$VAULT`；`.git` 是目录还是文件不参与软链解析。此结论不消除上面的源目录软链反例。 |
| **6：写入面** | 条件清单覆盖根与 AGENTS.md，逐段判据覆盖 `.agents` 中间目录，叶子另过同一判据。最终版本已没有 `AGENTS.md.tmp → mv` 发布路径；manifest 两项登记一致。 |
| **7：三条门** | E-1 仍检查指定三组输入的 rc64；禁件门保留三个禁串；写面门仍为精确集合相等。最终新增的是 **两个 label**，不是三个，tmp 已随实现移除。这属于按实际写面登记。 |

`--hosts claude` 下新增操作均受 `HOST_OPENCODE` 条件保护；未发现该路径的新增行为，但没有将作者声称的“两版 dry 输出逐字相同”当成本轮实测。

两个已登记窗口——`deploy-vault.sh:1359→1361` 的清理竞态，以及 `:1129/:1291` 打开目录前的祖先替换——本轮没有新增证据要求将其升级为本卡阻断项，可继续作为明确的移交限制。**本卡仍需处理上述两个 MEDIUM，才能声称本轮整改全部闭合。**

本次仅做只读源码、Git blob、AST 和语法检查；未修改文件、运行部署或 pytest、连接数据库或运行模型。


