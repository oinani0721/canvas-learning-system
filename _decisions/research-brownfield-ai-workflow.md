# 高效开发者 Brownfield AI 开发日常

> 综合 7 组 WebSearch + 15 篇深度来源，提取真实开发者在大型既有项目上使用 Claude Code / AI 的具体做法。
> 日期：2026-03-24

---

## 一、Session 管理：一个 session 多长？做什么？

### 1.1 Session 时长和边界

| 来源 | 做法 |
|------|------|
| Anthropic 官方 Best Practices | 上下文窗口是最重要的资源。性能从 20-40% 占用开始下降。`/clear` 在不相关任务之间清除。 |
| Druce.ai (speedrunning 文章) | 每个 session 30-45 分钟，超过后 context 累积噪音导致质量下降。2 小时 session 通常触发 2-3 次压缩，摘要质量逐步稀释。 |
| Shrivu Shankar (sshh.io) | 用 `/context` 实时监控 token 用量。Monorepo 基线约 20k tokens (10%)，剩下 180k 才是实际工作空间。 |
| Boris Cherny (Claude Code 创造者) | 不追求长 session。跑 10-15 个并行 Claude 实例，每个做一件事。10-20% 的 session 被直接丢弃。 |

**实操规则**：
- 一个 session = 一个明确任务（一个 bug fix、一个 feature、一次重构）
- `/clear` 在任务切换时强制执行，不要在同一 session 里混杂不相关任务
- 超过 50% context 占用时，要么 `/clear` 要么 `/compact` 带上明确指令
- 连续纠正 2 次仍不对 → `/clear` + 写一个更好的初始 prompt，比继续纠正更快

### 1.2 Session 类型

| Session 类型 | 时长 | 做什么 | 模式 |
|-------------|------|--------|------|
| **探索/调研** | 15-30 min | Plan Mode，读代码，理解架构，不改任何东西 | Plan Mode |
| **规划** | 15-30 min | 写 spec、分解任务、生成实施计划 | Plan Mode → 手动编辑计划 |
| **实施** | 30-45 min | 执行计划中的一个步骤，跑测试，commit | Normal Mode + Auto Accept |
| **审查** | 15-20 min | 独立 session 审查另一个 session 的产出 | 新鲜 context，无偏见 |
| **Debug** | 20-40 min | 贴报错 → 定位 → 修复 → 验证 | Normal Mode |

### 1.3 Session 之间的上下文传递

**"Document & Clear" 方法**（sshh.io）：
1. 让 Claude 把当前进度 dump 到一个 .md 文件
2. `/clear` 清空 context
3. 新 session 读取该 .md 文件继续

**Session 恢复**：
- `claude --continue`：恢复最近一次对话
- `claude --resume`：从历史 session 列表中选择
- `/rename` 给 session 起有意义的名字（如 `oauth-migration`、`fix-memory-leak`）

---

## 二、任务分解：怎么决定先做什么？

### 2.1 Spec-First 方法（Addy Osmani）

```
1. 和 LLM 对话写出详细 spec.md（需求、架构、数据模型、测试策略）
2. 把 spec 喂给推理模型，生成分步实施计划
3. 每步实施后测试，再进入下一步
```

**关键原则**：15 分钟的规划 > 2 小时的盲目编码

### 2.2 粒度控制

| 做法 | 来源 |
|------|------|
| 每次 prompt 只做一件事：一个函数、一个 bug、一个 feature | Addy Osmani |
| 大请求产出 "jumbled mess"，小请求产出可控结果 | 多位 HN 评论者 |
| "如果能一句话描述 diff，跳过计划直接做" | Anthropic 官方 |
| 估算超过 2 天的工作 → 自动拆成 2-3 个小 ticket | subagent 并行开发模式 |

### 2.3 Brownfield 项目的特殊分解策略

**Spec-Driven Development (SDD) 四阶段**：
1. **Codebase Discovery** — AI 自动分析结构、依赖、测试覆盖率、文档
2. **Synthesis & As-Is Report** — 生成"现状快照"文档
3. **Socratic Clarification** — 通过结构化提问理解业务逻辑、架构假设、技术债
4. **Hybrid Specification** — 基于现有代码 + 新需求生成 spec

**D3 Framework (论文 arXiv:2512.01155)**：
- Discover → Define → Deliver
- 用角色分离的 prompting：Builder 生成，Reviewer 审查
- Brownfield 中"spec 跟随理解，而不是理解跟随 spec"

### 2.4 每日任务安排（Boris Cherny 模式）

```
早上：Review agents 产出的 PR 和 diff。Approve / reject / 留评论。
白天：Queue 任务（带 spec + 测试），agents 在隔离 worktree 中领取执行。
晚上：Review PR，merge 好的，queue 夜间任务。Agents 在你睡觉时继续工作。
```

每天 offload 2-3 小时的 review 和 spec 工作，agents 持续产出。

---

## 三、质量保证：怎么防止修了又坏？

### 3.1 第一原则：给 Claude 验证自己的方式

> "This is the single highest-leverage thing you can do." — Anthropic 官方

| 验证方式 | 做法 |
|---------|------|
| 测试套件 | 实施后让 Claude 跑测试，失败了自己 debug |
| 截图对比 | 贴 UI 截图让 Claude 视觉验证 |
| Linter/Formatter | 每次编辑后自动运行 |
| 编译循环 | 告诉 Claude 编译命令，让它自己 debug 编译错误 |

### 3.2 多模型交叉验证

- **Addy Osmani**：用第二个 AI session（不同模型）审查第一个的输出
- **"cranky senior developer" prompt** (Druce.ai)：让 Claude 假装是"讨厌你代码的资深开发者"来 review
- **Writer/Reviewer 模式** (Anthropic 官方)：Session A 写代码，Session B（新鲜 context）review

### 3.3 提交级验证

- **超细粒度 commit**（Addy Osmani）："像游戏存档一样 commit"，每个小任务完成后立即 commit
- **PreCommit Hook 强制测试**（sshh.io）：包装 `git commit` 命令，只有测试通过才允许提交
- **PostToolUse Hook 格式化**（Boris Cherny）：每次 Write/Edit 后自动跑 `bun run format || true`

### 3.4 TDD-Guard 模式

```
1. 一次只写一个测试
2. 测试必须因正确的原因失败
3. 写最小实现让测试通过
4. 禁止 Claude 同时写所有测试再一起实现
```

### 3.5 Brownfield 特有的质量问题

| 问题 | 对策 |
|------|------|
| Claude 会和你的代码风格"打架" | 在 CLAUDE.md 中明确建立项目约定 |
| 大型重构容易引入破坏 | 用 subagent 做只读 review，不污染主 context |
| 改了一处，别处坏了 | 跑全量测试而非单文件测试 |
| AI 产出看起来对但逻辑有隐患 | 像审查初级工程师的代码一样审查每一行 |

---

## 四、上下文管理：怎么保持 Claude 记住项目？

### 4.1 CLAUDE.md 分层体系

| 层级 | 路径 | 作用 | 是否提交 git |
|------|------|------|-------------|
| 全局 | `~/.claude/CLAUDE.md` | 个人风格偏好，跨所有项目 | 否 |
| 项目根 | `./CLAUDE.md` | 团队共享约定、构建命令、架构决策 | 是 |
| 子目录 | `./src/CLAUDE.md` | 特定模块的约定 | 是 |
| 本地 | `./CLAUDE.local.md` | 个人项目偏好 | 否 (.gitignore) |

### 4.2 CLAUDE.md 写作原则

**关键数据**（Boris Cherny 的团队用 2.5k tokens）：

| 应该写 | 不应该写 |
|--------|---------|
| Claude 猜不到的 Bash 命令 | Claude 读代码就能推断的东西 |
| 与默认不同的代码风格规则 | 标准语言约定 |
| 测试指令和首选测试框架 | 详细 API 文档（改为链接） |
| 仓库礼仪（分支命名、PR 约定） | 频繁变动的信息 |
| 项目特有的架构决策 | 长篇教程 |
| 常见坑和非显而易见的行为 | "写干净代码"之类的废话 |

**反模式**：
- 不要在 CLAUDE.md 中 `@` 引用大文件（每次 session 都会全量加载）
- 不要超过 200 行 / 2000 tokens（太长 Claude 会忽略部分规则）
- 不要只写"不要做 X"，必须同时给出替代方案
- 如果 Claude 反复违反规则 → 文件太长，规则被淹没了

**维护方式**：
- Boris Cherny 用 `@.claude` tag 在同事 PR 上收集错误 → 更新 CLAUDE.md
- 像对待代码一样对待 CLAUDE.md：出问题时 review，定期剪枝，观察 Claude 行为是否真的改变

### 4.3 上下文保鲜技术

| 技术 | 做法 |
|------|------|
| **Skills (按需加载)** | 把领域知识放 `.claude/skills/` 而非 CLAUDE.md，Claude 按需加载不膨胀每个 session |
| **Subagent 隔离** | 让 subagent 去读大量文件做调研，只把摘要带回主 session |
| **`/btw` 侧问** | 快速问题用 `/btw`，答案显示在浮层中不进入对话历史 |
| **CONTEXT.md** | 复杂任务时手动创建 CONTEXT.md 在目标目录，提供任务特定上下文 |
| **`/catchup`** | 清空后用 `/catchup` 读取当前分支的变更文件，快速恢复上下文 |

### 4.4 "Lazy-Loading Context" 高级技巧

定义一个"AI 接待员"角色，根据任务类型条件性地加载角色和任务文件：
- 只有相关的 guidelines 才会到达模型
- 避免不相关上下文稀释任务特定信息

---

## 五、并行开发：一个人当一个团队用

### 5.1 Boris Cherny 的并行模式

```
- 终端 5 个 Claude（编号 tab 1-5），每个独立 git checkout
- 浏览器 5-10 个 Claude（claude.ai）
- 用 --teleport 在本地和 web 之间迁移任务
- 10-20% 的 session 直接丢弃（实验失败是正常的）
- 全部用 Opus 4.5 + thinking（"算上迭代周期，比小模型更快"）
```

### 5.2 Git Worktree 并行

```bash
# 预热 5 个 worktree，各自有独立依赖
git worktree add ../worktree-1 -b feature-1
git worktree add ../worktree-2 -b feature-2
# 每个 worktree 一个 Claude session
# 用 worktrunk 或 conductor.build 管理
```

**注意**：预装依赖避免端口冲突。

### 5.3 Fan-Out 批量处理

```bash
# 1. 让 Claude 列出需要迁移的文件
# 2. 循环处理
for file in $(cat files.txt); do
  claude -p "Migrate $file from X to Y. Return OK or FAIL." \
    --allowedTools "Edit,Bash(git commit *)"
done
```

先在 2-3 个文件上测试 prompt，然后全量执行。

### 5.4 Agent Teams 模式

| 角色 | 职责 |
|------|------|
| Product Manager agent | 分解需求、用户故事 |
| UX Designer agent | 界面设计、组件规范 |
| Implementation agent | 编码、测试 |
| Code Reviewer agent | 独立 context 审查 |

Brownfield 关键：所有 agent 必须读取同一份 CLAUDE.md 中的项目约定，确保代码风格一致。

---

## 六、与用户/PM 的协作方式

### 6.1 Interview 模式

```
我想构建 [简要描述]。用 AskUserQuestion 工具深度访谈我。
问技术实现、UI/UX、边界情况、顾虑和权衡。
不要问显而易见的问题，挖掘我可能没考虑到的难点。
持续访谈直到覆盖所有方面，然后写完整 spec 到 SPEC.md。
```

spec 完成后，开新 session 执行（新鲜 context 专注于实施）。

### 6.2 规划-实施分离

```
Phase 1: Plan Mode — Claude 读文件、回答问题、不做修改
Phase 2: 创建实施计划 → Ctrl+G 在编辑器中手动修改计划
Phase 3: Normal Mode — 按计划实施 + 跑测试
Phase 4: Commit + PR
```

### 6.3 日常节奏（综合多位开发者）

```
08:00-09:00  Review 夜间 agent 产出的 PR/diff
09:00-09:30  规划当天任务（spec + 测试定义）
09:30-12:00  实施 session x 2-3（每个 30-45 min）
             并行跑 2-3 个独立 Claude session
12:00-13:00  午休
13:00-13:30  Review 上午产出，merge/reject
13:30-16:00  实施 session x 2-3
16:00-16:30  Code review（用独立 session）
16:30-17:00  Queue 夜间任务 + 更新 CLAUDE.md
```

---

## 七、关键反模式（来自真实项目的血泪教训）

| 反模式 | 后果 | 正确做法 |
|--------|------|---------|
| "Kitchen Sink Session" | 一个 session 混杂多个不相关任务 → context 充满噪音 | 一个 session 一个任务，`/clear` 切换 |
| 反复纠正 | 纠正超过 2 次 → context 充满失败尝试 | `/clear` + 重写更好的初始 prompt |
| 过度膨胀 CLAUDE.md | 太长导致规则被忽略 | < 200 行。能用 hook 强制执行的就不写规则 |
| "Trust-then-verify gap" | 看起来对但不处理边界情况 | 必须提供验证手段（测试、截图、脚本） |
| 无限探索 | "investigate X" 不限范围 → 读几百个文件耗尽 context | 限定范围 or 用 subagent |
| 全量加载代码库 | 大文件塞进 context → Claude 忘记细节 | 用工具按需查找，不全量加载 |
| 跳过测试定义 | 没有测试 → 开发者自己变成反馈循环 → 产出减半 | 每个计划必须包含可执行的验证步骤 |
| 对 production 数据库开发 | 风险不可控 | 严格沙箱，feature branch |

---

## 八、Brownfield 项目的黄金法则

1. **理解先于 spec** — Brownfield 中 spec 跟随理解，不是理解跟随 spec。先让 AI 做 codebase discovery。
2. **增量改造** — 不要试图一次性重写。小块改、勤 commit、保持随时可回滚。
3. **参考现有模式** — "看 X 文件怎么做的，按同样模式做 Y"比抽象指令有效 10 倍。
4. **Claude 会和你的代码风格打架** — 必须在 CLAUDE.md 中明确约定，否则它会按自己偏好改你代码。
5. **成熟项目要 measured approach** — Greenfield 可以"let it rip"，10+ 年老项目必须频繁介入和审查。
6. **Hook 强制执行 > CLAUDE.md 规则建议** — 规则会被忘记，hook 永远不会。
7. **独立 context review** — 写代码的 session 不能 review 自己的代码（有偏见）。

---

## Sources

- [My Claude Code Setup](https://psantanna.com/claude-code-my-workflow/workflow-guide.html)
- [Addy Osmani - My LLM Coding Workflow Going Into 2026](https://addyosmani.com/blog/ai-coding-workflow/)
- [Speedrunning the Claude Code Learning Curve](https://druce.ai/2026/02/claude-code)
- [How I 10x My Engineering With AI](https://every.to/source-code/the-three-ways-i-work-with-llms)
- [How I Use Every Claude Code Feature (sshh.io)](https://blog.sshh.io/p/how-i-use-every-claude-code-feature)
- [Creator of Claude Code Reveals His Workflow (VentureBeat)](https://venturebeat.com/technology/the-creator-of-claude-code-just-revealed-his-workflow-and-developers-are)
- [Inside the Development Workflow of Claude Code's Creator (InfoQ)](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/)
- [Best Practices for Claude Code (Official Docs)](https://code.claude.com/docs/en/best-practices)
- [How to Use Claude Code Subagents to Parallelize Development](https://zachwills.net/how-to-use-claude-code-subagents-to-parallelize-development/)
- [Spec-Driven Development for Brownfield Code](https://github.com/kpiteira/spec-driven-development/blob/main/04_SYSTEM_Brownfield_Workflow.md)
- [Beyond Greenfield: The D3 Framework (arXiv:2512.01155)](https://arxiv.org/abs/2512.01155)
- [BMAD Method Brownfield Development](https://deepwiki.com/bmadcode/BMAD-METHOD/4.9-brownfield-development-workflow)
- [HN: How I Use Claude Code in Existing Complex Codebase](https://news.ycombinator.com/item?id=44774121)
- [HN: Claude is Amazing at Brownfield](https://news.ycombinator.com/item?id=46016504)
- [HN: Getting Good Results from Claude Code](https://news.ycombinator.com/item?id=44836879)
- [HN: How Are You Productively Using Claude Code?](https://news.ycombinator.com/item?id=44548554)
- [Coding with Claude: Reduce Technical Debt with AI](https://vendiadvertising.com/insight/coding-claude-how-reduce-your-technical-debt-ai)
- [Claude Code Sub-Agents: Parallel vs Sequential Patterns](https://claudefa.st/blog/guide/agents/sub-agent-best-practices)
- [Writing a Good CLAUDE.md (HumanLayer)](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Claude Code Context Management Guide (SitePoint)](https://www.sitepoint.com/claude-code-context-management/)
