> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-7
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r7.md)"`
> 审查绑定: `5af9c7ff`（结论 BLOCKER=0 / **HIGH=0** / MEDIUM=1；Z1–Z4 四项判全部闭合。整改在 `6f198150` + `9df308be`）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定 **`5af9c7ffe78dd1ec0c2725998434a784bca9d261`**，分支正确。**本轮 BLOCKER=0 HIGH=0；仍有 MEDIUM=1，无新增 LOW。**

审查期间工作区出现了未提交修改；以下结论和行号均对应指定提交，不包含这些后续修改。

**MEDIUM-1：尾随 LF 的名字已保真，但后置落点检查仍误拒。**

`scripts/deploy-vault.sh:997-998` 的参数展开正确；然而 `:1071` 的 `tphys="$(… pwd -P)"` 仍会删除路径末尾全部 LF，随后 `:1073` 与保留 LF 的 `$name` 比较必然不等。此时软链和 AGENTS.md 已经生成，控制流却返回步 3 失败、rc 73。

配套测试 `backend/tests/unit/test_deploy_vault_sh.py:4602-4606` 只检查建出的名字，没有断言返回码，因此漏掉这个失败；`:4599` 的夹具还缺少名字与 `SKILL.md` 之间的 `/`。

**复现思路：**预置 `.claude/skills/trailnl<LF>/SKILL.md`，在现有行为用例中补上成功返回码断言，会因上述后置比较失败而变红。

本轮纯内存 Bash 对照已确认：预期路径保留 LF，命令替换后的路径丢失 LF；未执行部署。

四项整改的闭合判断如下：

| 项目 | 判断 |
|---|---|
| **Z1：序号 label** | **闭合。** `deploy-vault.sh:999-1005` 在同一循环追加名字和对应路径；序号仅用于标签，没有对应关系断裂。 |
| **Z1：参数展开保真** | **局部闭合，整体 PARTIAL。** `${_p##*/}` 本身保真，258 组内存字节样本零差异；NUL、`/` 本来不能属于合法 basename。剩余问题是上述后置命令替换。 |
| **Z2/Z3：去注释与必要条件** | **闭合。** 测试 `:4425` 的 `split("\n")` 与当前 `StringIO(...).readline` 行界一致；`tokenize` 列坐标是 Unicode 码点索引，制表符算一个位置，与 Python 字符串切片对齐。`:4477-4486` 只让 Python 代码满足必要条件、两侧检查禁串，拆分合理。 |
| **Z4：清理 guard 门** | **闭合。** 去注释后的 PYPUB 中两个锚各出现 **1 次**；测试 `:4493-4496` 确实限定清理分支并检查先后顺序。删除 guard、移到截断之后，负控均失败。 |

其余问题的核对结果：

- **0／5：发现与落点。** 按题给的多根扫描、frontmatter `name` 去重语义，跟随条目软链时可能扫描同一 SKILL.md 两次，最终同名条目只有一份；若扫描器忽略别名侧软链，原 `.claude/skills` 根仍提供该技能。不能把“最终一份”说成“只读取一次”。相对目标从 `.agents/skills` 回退两级到 vault，祖先 `.git` 是目录还是文件不改变落点（`deploy-vault.sh:1150-1158`）。

- **1：dry 零写。** 所审控制流未发现本卡新增的提前写入：宿主解析只用参数展开；新增 heredoc 均在 apply 才调用的函数内；步 3 在 `:1435-1441` 提前返回，TMPDIR 已纳入步 1 判据。快照门无法证明“建后又删”的瞬时零写，本轮也没有重跑文件系统行为验收或扩大检查外部依赖。

- **2／4：禁串与文案。** 指定提交非注释行中，`opencode.json` 和 `.config/opencode` 均为 **零命中**。`:1406` 拼接的文件名只进入正文，`:1423-1427` 明确指向 vault 根目录的项目配置、remote MCP 和完整 `/mcp`，并明确不要修改用户级配置。该拼接可以解释文案需求，但**词法门不能据此证明运行期零写**；当前调用链未发现把它用于配置文件写入。

- **3：D-26(i)。** `cls_forbidden_paths.py:270` 是正常、保护目标不重叠时专门登记该目录的唯一承重点；删除后，没有另一条文件名规则专门兜住这两个普通文件。其他保护根重叠或枚举失败仍可能拒绝，不能推广成“任何环境必放行”。`:239-241` 正确处理保护根 `/`，`:589-590` 补查空分段根路径，未见所问旁路。此项依据静态核对，未重跑作者的删行负控。

- **6／7：登记与旧门。** `.agents/skills` 的逐段检查同时覆盖中间目录 `.agents`；动态叶子在 `deploy-vault.sh:1005-1013` 走同一判据。最终提交实际新增 **两个 label，不是三个**；AGENTS.md 已直接以 `O_CREAT|O_EXCL|O_NOFOLLOW` 创建，任何既存目标均拒绝，没有 `AGENTS.md.tmp → mv` 发布路径。Manifest 两项及四处测试集合更新一致；g2_8 仍是精确集合门，属于登记。旧门仍保留指定三组 rc 64 输入和三项禁串。

两个已登记窗口仍在：清理分支 `deploy-vault.sh:1373-1375` 的链接数检查到截断之间，以及 `:1143`／`:1304` 打开 vault 前的祖先替换。**除此之外，指定提交还剩上述 MEDIUM-1，因此不能确认 Z5 的“仅剩两个窗口”。**

验证范围：只读语法检查、六条静态门、五个内存负控及 Bash 字节对照；未改文件、未连接数据库、未运行模型或完整 pytest。


