# Agent Prompt 详细模板

执行 Phase 2 时，将以下 prompt 传给对应的 Explore Agent。
用 Phase 1 生成的关键词和 Phase 0 的项目元数据替换占位符。
如果 Phase 1.5 codebase-memory 有输出，将其作为 `[Codebase-Memory Context]` 段注入每个 Agent prompt 的开头。

---

## Agent A — 精确匹配 + 调用链追踪

```
任务：用关键词搜索种子文件，然后追踪 import 调用链。
输入：Phase 1 的直接关键词、扩展关键词、路径模式、排除模式。
      Phase 0 的 tsconfig paths 映射（如有）。
      [Codebase-Memory Context]（如有）：模块摘要、已知关联、代码陷阱。
      利用 codebase-memory 上下文中提到的模块名和关联关系作为额外搜索种子。

步骤：
1. 用 Grep 搜索所有关键词组（直接 + 扩展 + codebase-memory 提到的模块名），排除 Phase 1 的排除模式
2. 对每个种子文件，读取内容找到它 import 的模块（下游 2 层）
   - TypeScript：如果 import 路径以 @ 开头，用 tsconfig paths 映射替换为实际路径
   - Python：追踪 from X import Y 和 import X
3. 反向追踪：rg -l "import.*模块名|from.*模块名" 找到谁调用了种子文件（上游 2 层）
4. 收集 API endpoint（如果议题涉及 API）
5. 输出：文件路径列表 + 发现来源标签
   格式：文件路径 — 简述 [精确匹配: "关键词"] 或 [调用链: imports X / imported by Y]

注意：排除 node_modules/, __pycache__/, .git/, dist/, build/
```

---

## Agent B — 模式发现（配置/事件/框架约定）

```
任务：找到通过非 import 方式关联的文件——配置引用、事件注册、框架约定。
输入：Phase 1 的关键词。Phase 0 检测到的技术栈列表。
      [Codebase-Memory Context]（如有）：模块摘要、已知关联、代码陷阱。
      利用 codebase-memory 提到的隐式依赖（事件、配置引用）作为搜索线索。

步骤：
1. 搜索配置文件中的代码引用：YAML/TOML/JSON 中以字符串形式引用的类路径
   rg -l "关键词" --type yaml --type toml --type json
2. 搜索事件/消息注册模式：addEventListener, .on(, subscribe(, emit(, dispatch(
3. 搜索 Docker/CI 配置中的模块引用：docker-compose*.yml, Dockerfile*, .github/workflows/
4. 搜索环境变量定义和引用：.env*, rg "os.environ|process.env"
5. 搜索 schema/model 定义：rg "class.*Model|BaseModel|Schema"

6. 技术栈专用追踪（仅执行 Phase 0 检测到的技术栈对应策略）：

   Tauri（检测到 tauri.conf.json 时启用）：
   前端：rg "invoke\s*[<(]\s*['\"](\w+)['\"]" -g '*.{ts,tsx}' → 提取命令名
   后端：对每个命令名，rg -l "fn\s+{cmd}" -t rust → command 实现
   注册：rg -l "generate_handler!" -t rust
   标签：[模式发现: Tauri IPC invoke("{cmd}") ↔ #[tauri::command]]

   Neo4j（检测到 neo4j 相关依赖或 Cypher 查询时启用）：
   节点标签：rg -oP '\(\w*:(\w+)' -t py → 找对应模型定义
   关系类型：rg -oP '\[\w*:(\w+)\]' -t py
   标签：[模式发现: Cypher (:Label) 对应模型]

   FastAPI（检测到 fastapi 依赖时启用）：
   路由注册：rg "include_router" -t py → 注册文件
   端点定义：rg "APIRouter" -t py → router 文件
   标签：[模式发现: FastAPI include_router 注册链]

   Django（检测到 django 依赖时启用）：
   URL 配置：rg "urlpatterns" -t py → URL 映射
   View 定义：rg "class.*View|def.*request" -t py
   标签：[模式发现: Django URL→View 映射]

   未检测到以上技术栈时跳过步骤 6。

7. 注意：排除 node_modules/, __pycache__/, .git/, dist/, build/, *.pyc, *.lock
8. 输出：文件路径列表 + 发现来源标签
   格式：文件路径 — 简述 [模式发现: 含XX配置/事件注册/IPC/Cypher/路由]
```

---

## Agent C1 — git 历史 + 项目级文件（与 A+B 并行）

```
任务：收集最近修改的相关文件和项目级文件（不依赖 A+B 结果）。
输入：Phase 1 的关键词。
      [Codebase-Memory Context]（如有）：模块摘要、已知关联、代码陷阱。

步骤：
1. 找 git 最近修改的相关文件：
   git log --since="2 weeks ago" --name-only --pretty=format:"" | sort -u | grep "关键词"
   （自适应：提交少于 20 个则扩展到 4 周，超过 100 个则缩短到 1 周）
2. 收集项目级文件：CLAUDE.md, pyproject.toml, README.md, tauri.conf.json, package.json
3. 收集类型定义文件：*.d.ts, 共享类型文件
4. 注意：排除 *.backup*, *.OLD*, .worktrees/, _archive/
5. 输出：文件路径列表 + 发现来源标签
   格式：文件路径 — 简述 [上下文补全: 最近修改/项目级]
```

---

## Agent C2 — 补全测试+文档（A+B+C1 完成后启动）

```
任务：基于 Agent A 和 B 的结果，补全测试文件和关联文档。
输入：Agent A 和 B 找到的文件路径列表（作为 prompt 的一部分传入）。

步骤：
1. 对 A 找到的核心源码模块，找对应测试：
   rg -l "test.*模块名|模块名.*test" 在测试目录下搜索
   找 conftest.py 中的相关 fixture
2. 找关联文档/PRD/决策记录：
   rg -l "关键词" docs/ _decisions/ → 相关文档
   docs/architecture/ 中与议题相关的设计文档
   docs/deep-research-* 中与议题相关的调研报告
3. 注意：排除 *.backup*, *.OLD*, .worktrees/, _archive/
4. 输出：文件路径列表 + 发现来源标签
   格式：文件路径 — 简述 [上下文补全: 对应测试/关联文档]
```
