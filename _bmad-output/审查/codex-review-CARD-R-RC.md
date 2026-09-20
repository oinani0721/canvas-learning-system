> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p10-docs · 卡 CARD-R-RC round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-R-RC.md)"`
> 审查绑定: `ef8ace4a73b346790672a61e5308458fbfbcec4f..5cd1cae1e749411197148bfc4319fa9e24685f3f`
> ⛔ 该绑定**不是**最终 HEAD: prompt 是 amend 之前写的, 作者未同步更新, Codex 如实按 `5cd1cae1` 审并自行指出。按 D-15「最后一轮必须绑最终 HEAD」**本轮不计入配额**, 结论仅作整改输入。
> 会话头自证（抄 `.stderr`, 括注行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

复核结论：**未确认 BLOCKER；发现 1 项 HIGH、4 项 MEDIUM，另有 LOW 级边界。作者自述不能全部成立。**

本轮绑定 `ef8ace4a…5cd1cae1`。实测工作树 HEAD 已到 `c4fea853…`，以下源码和行号均以 **`5cd1cae1` 提交对象**为准，未混入后续修订。未修改文件、未联网或连接数据库；未重新运行会创建文件的 pytest。

1. **HIGH｜⓪ 子模块忽略配置属于未声明的「门未覆盖的路径」。**  
   [freeze_release_candidate.py:138](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:138) 未指定 `--ignore-submodules=none`，仍受子模块忽略配置影响：`untracked` 可隐藏子模块未跟踪文件，`dirty` 可隐藏内部工作树改动，`all` 还可隐藏子模块检出 HEAD 相对 gitlink 的差异。它们属于仓内状态，未被 `:77–81` 的 caveat 涵盖。全局 `core.excludesFile` 忽略来源也未明确列出。  
   **复现思路／对照输入：**在干净的含子模块仓中配置 `submodule.<name>.ignore=all`，再修改子模块；比较脚本所用 status 与加 `--ignore-submodules=none` 的结果。前者可能为空，成为未被拦下的输入。此处未声称本仓当前采用该配置。

2. **MEDIUM｜⓪ SHA、dirty 与锁文件不是同一时刻的快照。**  
   [freeze_release_candidate.py:289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:289) 先采 SHA，`:292` 仅检查一次状态，随后读取锁、等待校验器，直到写回执前都不复核。现有 caveat 没声明这个时间窗口。  
   **复现思路：**在状态检查返回干净后并发修改文件，或在 SHA 采样后切到另一干净提交；这些未被拦下的输入可使旧 SHA、后读的锁内容和 `dirty=false` 出现在同一回执。此项由控制流确定，未进行并发实跑。

3. **MEDIUM｜① README 没交代持续追加证据时如何保持执行树干净。**  
   [README.md:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/README.md:43) 要求先冻结再填证据；脚本 `:343–344` 本身便生成未跟踪骨架。README `:67–69` 又规定文档变更也换 SHA、重开窗口，而既有 `:123` 要求执行时 `dirty=false`。  
   **复现思路／对照输入：**在默认、未忽略的证据目录冻结 S；不提交骨架则执行树脏，提交清脏则 HEAD 变 S′。持续追加证据重复这个问题。  
   **不是不能向旧 rc 写文件**——追加无需再次冻结。缺的是明确的操作规则：执行树固定干净 S，证据在哪里采集、在哪里归档，以及归档提交为何不改变候选身份。README 写清了改代码的代价，尚未解决证据追加自身的流程冲突。

4. **MEDIUM｜① 实现的是同目录防覆盖，不是同 SHA 防重冻。**  
   [freeze_release_candidate.py:320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:320) 只检查 `rc_dir.exists()`；默认名称还包含日期。  
   **复现思路／未被拦下的输入：**同一干净 SHA、同一树外 `--out-root`，依次指定 `--rc-name rc-a`、`rc-b`，两次均能通过；跨日默认命名也能重复。测试 `:289–298` 只验证同名拒绝。因此 README `:66` 的“一个 SHA 一个 rc”没有被机械执行。

5. **MEDIUM｜索引参数空串可通过“二选一”门。**  
   [freeze_release_candidate.py:280](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:280) 比较 `bool()`，没有判断参数是否提供；`:376–377` 又原样写入。  
   **负控输入：**`--index-sha '' --index-sha-null-reason reason`。两个参数都给却通过，且写出 `index_sha=""`，不满足 schema `:206` 的 `minLength: 1`。反向“有效值＋空理由”同样通过。本轮已用绑定源码在内存中确认参数门行为。

6. **LOW｜③ `check` 成功只证明 SHA 一致，结构非法的 journey 也能通过。**  
   [freeze_release_candidate.py:504](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:504) 仅比较 SHA。现有测试 `:483` 恰好提供了**对照输入**：`candidate` 只有 `sha`，缺少 schema 要求的 `branch`、`dirty`，但测试 `:501` 要求 `check=0`。  
   **复现思路：**保持 SHA 与回执相同，删除 journey 的必需字段；一致性检查仍绿，schema 应红。  
   按当前“SHA 一致性检查”的职责，这不是完整发布门被绕过。可以保留窄职责，但应明确输出“未验 schema”；若要让一次 `check` 同时证明格式合法，应向校验器传入这些具体 manifest 路径，单跑 `--all` 看不到树外文件。

其余问题的核对结果：

- **⓪ 已声明边界基本属实。** `--untracked-files=all` 不包含被忽略文件；`assume-unchanged`、`skip-worktree` 可以隐藏未暂存改动。`-z` 的 rename 两段会多计一条，但非空判定仍拒绝，不构成放行。dirty 拒绝分支确实早于创建输出目录；这不应扩写成 Git 内部元数据也绝无写入。
- **② 缺 J01–J10 的事实没有丢失。** [实回执:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-rrc/rc-manifest-real-rc-20260918-5cd1cae1.json:65) 的 `null` 表示“未执行”，不是“实跑失败”。下一行明确写了缺 J01–J10，且 `journeys_expected` 列出十项。它缺少结构化的校验观测结果，但没有伪装成 PASS，也没有丢失缺项陈述。
- **④ 两份“锁”只证明文件指纹。** [脚本:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:193) 证明两文件存在、当刻字节的 SHA-256 和长度，不证明 venv、node_modules、传递依赖或容器实装一致。**对照输入：**相同两文件、不同 jsonschema 实装版本，锁指纹仍相同。“jsonschema 当前为传递依赖”在本读取面内仍只是源码自述。
- **⑤ 双树说明已是填写规则，不只是叙述。** [README.md:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/README.md:96) 明确了三个字段的来源和写法。余下歧义是第 2 条把“无宿主 bind 路径”当作统一理由，却未区分确实不涉索引的旅程，也未要求记录实际取证尝试。无 bind 路径本身不能证明所有读取方式都不可用。本轮按边界未核验 compose、`.env` 或运行容器，因此不替拓扑自述背书。

**⑥ 真 Git 与三段负控：核心结论 PASS。** 测试确实调用真实 `git init/add/commit`、冻结脚本和校验器 subprocess；未发现 mock、monkeypatch、autouse 或 subprocess 打桩。绑定版本共有 21 条测试。

我从绑定源码独立计算了三种单行变异的 SHA-256，均与原日志完整匹配：

| 负控输入 | 日志中的失败位置 | 判断 |
|---|---|---|
| dirty 恒干净 | [dirty 日志:33](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-rrc/negctl-dirty-20260918T195712.txt:33)，测试 `:214`，实际 `0 != 1` | 单层变异成立 |
| SHA 比对失效 | [checksha 日志:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-rrc/negctl-checksha-20260918T195745.txt:25)，测试 `:496` | 单层变异成立 |
| 锁 SHA 变常量 | [locksha 日志:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-rrc/negctl-locksha-20260918T195819.txt:14)，测试 `:265` | 单层变异成立 |

**LOW 证据限制：**dirty 日志只保留已跟踪用例的完整 traceback；未跟踪用例虽列在失败摘要中，其精确断言落点没有直接日志证明。末尾 `rc=0` 也不能当作 pytest 的退出码。

指定差异确为三个文件；README 删除内容行数为 **0**；没有新增真实 `<rc>/`。SHA 正则与授权 schema 片段一致，锁缺失拒绝、真实 subprocess 调用及 `--all` 返回 2 的透传逻辑均成立。


