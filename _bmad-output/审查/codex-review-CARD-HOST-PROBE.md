> 批次: BATCH-2026-09-07-第十三批 · 车道 U4（card-u4-hosts） · 卡 CARD-HOST-PROBE round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOST-PROBE.md)"`
> 审查绑定: `434c77dc`（= 送审时 HEAD；零代码卡，`git diff --stat --no-color 434c77dc HEAD -- . ':(exclude)_bmad-output'` 为空 ⇒ 代码树仍绑定，r1 后改动全在 `_bmad-output/`）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: <车道树>` / `model: gpt-6-astra`
> 结果计数: BLOCKER 0 · HIGH 6 · MEDIUM 4 · LOW 2。逐条处置见实测表 §七（撤销 1 / 收窄 8 / 更正 1 / 新增发现 2）。
> ⚠️ 整改未复审（零代码卡 1 轮），登记交主 session 裁定。

---

复核发现：**P6 的拒写结论、若干宿主能力推断及副作用清单需要更正**。P0、P4 和 P2 断连确实到达 MCP 连接层的证据成立。本次仅按限定范围只读，未修改文件、启动宿主或连接端口。

**BLOCKER**

无新增。§六.11 已登记的 `~/.codex/config.toml` 禁写面失败仍待裁定；保留阻断、不自行放宽的处理正确。

**HIGH**

1. **P6：三个“拒绝格”没有实际写入工具返回，唯一成功格不足以证明两层限制。**  
   [P6c:12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/P6c-codex-write-target-layer-20260908T070744.txt:12)记录了普通目录写入成功，但 `.agents` 的错误仅在模型消息中；[P6d:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/P6d-codex-readonly-plaindir-20260908T070851.txt:11)连写入调用都未展示，`ABSENT` 同时符合“没有尝试”。  
   **复核思路：**每格须对应实际写命令、工具拒绝结果与文件状态；即使补齐，也只能先确认该 `.agents` 路径，不能推广为所有隐藏目录规则。

2. **P6／表 A／§四 Codex：“无 skills 发现机制”把未验证写成了机制不存在。**  
   [P6a:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/P6a-codex-readonly-20260908T070528.txt:10)只证明模型通过 `rg`、`cat` 获取名称，提示词还透露了 `probe-skill` 路径。  
   **复核思路：**当前收窄为“本次通过 shell 列出，自动发现未验证”；后续阳性须使用不透露名字的提示和宿主加载证据。

3. **P7：“项目级文件根本未被读取”超出了有效清单能证明的范围。**  
   [P7:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/P7-codex-mcp-list-20260908T070457.txt:20)只支持“本次列表没有项目条目”，仍不能排除读取后忽略或不合并。  
   **复核思路：**收窄为该次列表结果；“是否读取”须有加载诊断，受信项目行为继续保留未验。

4. **P8／§三.5／§四：“三处都读且按 name 去重”缺少独立目录阳性。**  
   [P8:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/P8-opencode-20260908T071157.txt:27)没有展示 `.opencode` 来源；`probe-skill` 仅出现一次，也符合“.opencode 未扫描”，所引位置亦无二进制常量证据。  
   **复核思路：**以后先用各目录独有名字分别证明扫描，再测试同名冲突；目前只能确认“本次枚举没有重复”。

5. **§六.6／表 A：副作用确有遗漏，“OpenCode 未见新建物”被快照直接反驳。**  
   [开工快照:3086](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/runtime-state-open-20260908T064311.txt:3086)显示空目录；[收工快照:3117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/runtime-state-close-20260908T071818.txt:3117)显示新增 `~/.config/opencode/.gitignore`、`opencode.jsonc`，另有 `~/.claude.json` 大小从 95756 变为 95945。  
   **复核思路：**对已有快照做局部差异核对并补登记；这些证明窗口内变化，尚不能唯一归因到某条探针。

6. **§三.7／§六.11：“MCP 段数恒 8”不能推出“配置语义面未变”。**  
   [因果 r2:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/causal-codex-writes-config-r2-20260908T071710.txt:19)支持新目录记录增加，但没有比较 MCP 段内值；trust 记录本身也有配置语义。  
   **复核思路：**当前仅保留“projects 增一、MCP 段数不变”；语义不变需要脱敏的分段内容摘要对照。

**MEDIUM**

1. **P2／§四／§五.6：8011 正控未直接绑定 dsh 内的具体工具名。**  
   [P2a:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/P2a-dsh-mcp-8011-20260908T065433.txt:6)直接展示的是 web 启动与超时终止；P2e/P2f 的列举、调用来自 curl。P2b 的错误链确实进入 MCP 客户端并出现 `ECONNREFUSED`，足以排除更早的 profile 失败，因此**整组证据强于仅看进程启动**，但仍未证明 dsh 注册或调用指定工具；错误文本也未展示 `listTools()` 调用。  
   **复核思路：**保留连接层对照，拆开“后端工具可调用”和“dsh 工具可用”，后者须绑定宿主内公开工具名字面量。

2. **P9／§三.6：无响应超时不能确认“流已保持打开、非拒绝”。**  
   [P9b:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/审查/evidence-host-probe/P9b-sse-rejection-layer-20260908T065803.txt:10)实际是 `http_code=000`、无响应头、零字节超时；没有已接受 SSE 流的响应证据。  
   **复核思路：**保留 `mount_http()`、initialize 成功和旧端点 404 的结论，把带会话 GET 收窄为“等待六秒未收到响应”。

3. **P10／§六.5：“发现祖先目录”仍不足以证明“.git 是遍历边界”。**  
   §五.8 不外推 live vault 的处理正确；但[§六.5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/_bmad-output/研究/2026-09-08-HOST-PROBE-宿主实测表.md:118)又断言两家以 `.git` 文件为边界，与 §五.13 的保留冲突。  
   **复核思路：**限定为“该 worktree 场景发现 cwd 与车道树根的技能”；边界需另设中间层、根外哨兵对照。

4. **§三.7：“workspace-write 必然写、任何卡都会触发、属于假阻断”泛化过宽。**  
   r1/r2 支持本机该版本在全新目录条件下的因果解释，未覆盖已有记录、重复执行等条件；是否“假阻断”也仍属规则裁定。  
   **复核思路：**保留本次条件下的因果结论，删除普遍量词并维持待裁定状态。

**LOW**

1. **§二／§六.1：CONFIRMED 汇总漏计 P8 的 MCP 子项。**  
   按原表对子结论的计数口径，原始标签应为 **12**，不是 11；这是内部计数核对，不代表本次认可全部结论。  
   **复核思路：**逐项列出状态后计数；P0～P10 没有空状态，所列 NOT-RUN 均有具体原因。

2. **§三.8／§六.6：“dsh 每次启动都原样重写”超过检查点证据。**  
   当前证据仅支持窗口内 mtime 变化、检查点 sha 相同。  
   **复核思路：**收窄为已观测事实，或补逐次启动前后的绑定记录。

P0 的 `128/0` 正负控成立；P4 的宿主 `project: 3/1` 加上 `probe-skill` 字面量成立，确实证明发现，超过进程启动。§四已明确受信项目、dsh headless、OpenCode 模型侧未验，没有冒称这三面已测；推荐依据仍须同步收窄上述能力推断。

两次方法修正方向正确：P1 改用配置字面量，消除了行数／sha 的歧义；补 workspace-write 正控，也纠正了用 read-only 阴性排除因果的错误。现有 P1 首轮摘要未保留那一行报错正文，因此“差异恰是报错本身”无法在本读取面内独立确认。
