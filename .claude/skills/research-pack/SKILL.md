---
name: research-pack
description: |
  Smart codebase packing — dynamically select relevant files based on a research topic,
  pack into under 1M token XML for Deep Research / LLM analysis.
  智能打包 — 根据议题用并行 Agent 深度探索代码库，精准打包供 Deep Research 分析。
  
  Use this skill when the user wants to: pack code for analysis, bundle files for
  deep research, create a context pack, prepare codebase for review, export code
  for external LLM, or says "打包", "pack", "research-pack", "代码审查准备",
  "给 Deep Research 打包", "bundle for analysis".
  
  用法：
    /research-pack scoring 服务设计是否合理
    /research-pack 前端状态管理是否合理
    /research-pack 任意议题...
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
  - ToolSearch
  - mcp__codebase-memory__recall
  - mcp__codebase-memory__brief
  - mcp__codebase-memory__gotchas
---

# Research Pack — 智能打包 Skill

## 核心原则

1. **议题驱动，不用死模板** — 每次根据用户议题动态选文件
2. **按发现方法分工** — 精确匹配 + 模式发现 + 上下文补全，三路互补覆盖
3. **用户确认后再打包** — Agent 找 ~90%，用户审核补齐最后 ~10%
4. **内容感知 Token 估算** — 代码/文档/中文分别计算，避免超限或浪费
5. **精准 > 全量** — 宁可多花时间选对文件，不要无脑灌入

## 参考文件（按需加载，不要一次全读）

| 文件 | 何时读取 |
|------|---------|
| `references/keyword-guide.md` | Phase 1 生成关键词时，参考 7 组扩展示例 |
| `references/agent-prompts.md` | Phase 2 构建 Agent prompt 时，复制对应 Agent 的模板 |

## 执行流程

### Phase 0：项目结构预分析（自动检测，可跳过）

提取项目结构元数据供后续 Agent 使用。**检测失败则跳过，Phase 0 是增强项不是必要项。**

1. **技术栈自动检测**：Glob 检测标志文件（package.json/tsconfig.json/pyproject.toml/Cargo.toml/tauri.conf.json/docker-compose*.yml），决定 Phase 2 Agent B 启用哪些技术栈专用策略
2. **TypeScript 路径别名**（仅 tsconfig.json 存在时）：Read tsconfig.json 提取 `compilerOptions.paths`，传给 Agent A
3. **项目入口文件**：按检测到的技术栈定位入口（package.json main / FastAPI app / tauri.conf.json）
4. **项目上下文摘要**：tech stack + `ls -d */` + 入口列表（供 Phase 5 注入）

### Phase 1：智能议题理解 + 关键词扩展

从用户议题生成 **7 组搜索输入**。详细示例见 → `Read references/keyword-guide.md`

概要：直接关键词 → 扩展关键词 → 路径模式 → 排除模式 → 技术栈专属词 → 代码模式 → 上下文信号。**总预算 40-55 个关键词**。

同时判断涉及的模块（后端/前端/全栈）和分析类型（架构审查/PRD对照/安全/测试迁移/其它）。

### Phase 1.5：Codebase-Memory 预探索（如果 MCP 可用）

在启动 Phase 2 Agent 之前，尝试用 codebase-memory MCP 获取模块关系概要。

**执行步骤**（顺序执行，任何一步失败则跳过整个 Phase 1.5）：

1. 用 `ToolSearch(query: "select:mcp__codebase-memory__recall")` 加载 recall 工具
2. 调用 `mcp__codebase-memory__recall(context: "{Phase 1 的核心关键词，用自然语言描述}", lobe: "canvas-learning-system")`
3. 用 `ToolSearch(query: "select:mcp__codebase-memory__gotchas")` 加载 gotchas 工具
4. 调用 `mcp__codebase-memory__gotchas(lobe: "canvas-learning-system")`

**输出**: 将 recall 和 gotchas 的返回内容拼接为 `[Codebase-Memory Context]` 文本块，格式：
```
[Codebase-Memory Context]
=== Recall Results ===
{recall 返回的条目，每条一行}

=== Known Gotchas ===
{gotchas 返回的条目，每条一行}
```

这个文本块注入 Phase 2 每个 Agent 的 prompt 开头，帮助 Agent 更精准地定位文件。

**降级**: 如果 ToolSearch 找不到 codebase-memory 工具，或调用返回错误/空结果，直接跳过进入 Phase 2，不阻塞流程。

### Phase 2：按发现方法启动 Agent（两波）

详细 Agent prompt 模板见 → `Read references/agent-prompts.md`

**第一波（3 个 Agent 并行）**：
- **Agent A** — 精确匹配 + 调用链追踪（Grep 关键词 → import 链上下游各 2 层）
- **Agent B** — 模式发现（配置引用/事件注册/Docker-CI/环境变量/schema + 技术栈专用追踪）
- **Agent C1** — git 历史 + 项目级文件（不依赖 A+B，自适应时间窗口）

每个 Agent 的 prompt 中包含 Phase 1.5 的 codebase-memory 输出（如有），用于缩小搜索范围和补全 Grep 可能遗漏的隐式关联。

**第二波（A+B+C1 完成后）**：
- **Agent C2** — 补全测试+文档（基于 A+B 结果找对应测试/conftest/PRD/决策记录）

### Phase 3：汇总 + Token 预算管理

1. **去重 + 空结果处理**：合并所有 Agent 结果。< 5 个文件时提示用户扩展关键词或手动指定
2. **排除噪音**：`node_modules/`, `__pycache__/`, `.git/`, `dist/`, `build/`, `*.pyc`, `*.lock`, `*.min.js` + 项目特有归档目录
3. **Token 估算**（优先 Repomix 精确计数，fallback 分类估算）：目标 < 900K tokens
4. **超了** → 按优先级裁剪（核心源码 > API > 模型 > 测试 > 文档），大文件 `--compress`
5. **有余量** → 扩展调用链 + git 最近修改 + 项目级文档

### Phase 3.5：文件清单确认（用户确认后再打包）

**先展示文件清单给用户确认，不直接打包。**

```
📋 议题：{用户议题}
📊 预估：{N} 个文件，约 {M}K tokens（上下文利用率 {M/900*100}%）

=== 核心源码（{n1} 个文件，~{t1}K tok）===
 1. ✅ path/to/core.py  — 核心逻辑 [精确匹配: "keyword"]
 2. ✅ path/to/dep.py   — 依赖模块 [调用链: imported by core]
...

=== 配置/基础设施（{n2} 个文件，~{t2}K tok）===
 3. ✅ docker-compose.yml — Docker [模式发现: 含端口配置]
...

=== 测试（{n3} 个文件，~{t3}K tok）===
 4. ✅ tests/conftest.py  — fixture [上下文补全: 对应测试]
...

=== 文档/PRD（{n4} 个文件，~{t4}K tok）===
 5. ✅ docs/design.md     — 设计文档 [上下文补全: 关联文档]
...

=== Token 余量 ===
已用: {M}K / 900K 上限
剩余: {900-M}K

请确认：
1. 输入编号删除不需要的（如 "删 3 5"）
2. 说文件名或关键词追加遗漏的
3. 确认无误说"打包"
```

发现来源标签：`[精确匹配]` `[调用链]` `[模式发现]` `[上下文补全]`

**等待用户确认后才继续。不要自动跳到 Phase 4。**

### Phase 4：打包

按优先级尝试：
- **方法 A** — Repomix MCP（`mcp__repomix__pack_codebase`，推荐）
- **方法 B** — Repomix CLI（`cat files.txt | npx -y repomix --stdin --style xml -o ".gdr/research-pack-<topic>.xml"`）
- **方法 C** — fallback 手动拼接

确保 `.gdr/` 目录存在。默认不压缩，超限时对非核心文件 `--compress`。输出 XML。

### Phase 5：增量确认 instruction（用户确认后再生成）

**禁止直接生成 instruction。必须先向用户提问确认。**

**Step 5.1 — 向用户展示 instruction 草案并逐项确认：**

```
📝 Instruction 草案（将注入打包文件末尾，指导 Deep Research 如何分析）

1️⃣ 项目背景（自动填充，请确认是否准确）：
   - 技术栈：{Phase 0 tech stack}
   - 架构：{检测到的架构概要}
   - 关键入口：{Phase 0 入口列表}

2️⃣ 分析议题："{用户议题原文}"
   → 这个表述准确吗？还是要调整措辞/补充背景？

3️⃣ 分析方向（默认以下 4 项，你可以增删改）：
   a. 设计/实现是否合理？
   b. 问题列表（CRITICAL / HIGH / MEDIUM / LOW）
   c. 与社区最佳实践差距
   d. 改善建议（附代码示例）
   → 有没有你特别想深挖的方向？或者不需要的方向？

4️⃣ 输出格式偏好：
   a. 表格（| 编号 | 严重度 | 文件:行号 | 问题 | 建议 |）
   b. 分章节叙述
   c. 其他偏好？

5️⃣ 额外上下文（可选）：
   有没有 Deep Research 需要知道的背景信息？
   例如：已知的问题、之前做过的决策、特别关注的风险...
```

**等待用户确认/修改后才继续。不要自动生成。**

**Step 5.2 — 根据用户反馈生成最终 instruction：**

将用户确认的内容组装为 instruction 文件，用 `--instruction-file-path` 注入打包文件末尾。

instruction 结构：
```markdown
# Deep Research 分析请求

## 项目背景
{Step 5.1 确认的项目背景}

## 分析议题
{Step 5.1 确认/调整后的议题}

## 打包内容
{N} 个文件，{M}K tokens

## 分析方法
1. 通读 <directory_structure> 建立心智模型
2. 从入口文件追踪代码路径
3. 引用 <file path="..."> + 行号作为证据
4. 验证发现与代码实际行为一致

## 请分析
{Step 5.1 确认的分析方向}

## 额外上下文
{Step 5.1 用户提供的额外信息，无则省略此节}

## 输出格式
{Step 5.1 确认的格式偏好}
```

### Phase 6：报告结果

```
打包完成！

📦 {N} 个文件，{M}K tokens（利用率 {M/900*100}%）
📄 .gdr/research-pack-<topic>.xml

下一步：拖进 Claude Desktop / Gemini → Deep Research → 分析
```
