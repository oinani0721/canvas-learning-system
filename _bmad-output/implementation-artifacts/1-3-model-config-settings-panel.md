# Story 1.3: 模型配置与系统设置面板

Status: ready-for-dev

## Story

As a 用户,
I want 在 Obsidian 设置面板中配置 LLM 模型供应商和 API Key，并为不同任务（对话、评分、Embedding）指定不同模型，
so that 系统能连接到 AI 服务并按需选择模型。

## Acceptance Criteria

1. **AC-1: Settings Tab 注册与显示**
   - **Given** 用户安装并启用 Canvas Learning System 插件
   - **When** 用户打开 Obsidian 设置（Ctrl+,）→ 社区插件 → Canvas Learning System
   - **Then** 显示 PluginSettingTab 设置面板，包含 6 个配置区域（系统状态、对话模型、评分模型、嵌入模型、后端连接、数据管理）
   - **And** 面板使用 Obsidian 原生 Setting API 构建，视觉风格与 Obsidian 一致

2. **AC-2: 系统健康状态面板（常驻顶部）**
   - **Given** 用户打开 Settings Tab
   - **When** 面板加载
   - **Then** 顶部显示 5 个组件状态灯：Docker / 后端 API / Neo4j / LLM API / LanceDB
   - **And** 每个组件显示绿色（就绪）、黄色（启动中）、或红色（不可达）状态
   - **And** 提供"重新检测"按钮，一键刷新所有状态
   - **And** 状态检测逻辑复用 Story 1.1 的 `GET /api/v1/system/health` 健康检查端点

3. **AC-3: 对话模型配置**
   - **Given** 用户在 Settings Tab "对话模型" 区域操作
   - **When** 配置供应商、模型名称和 API Key
   - **Then** 供应商下拉可选：Google Gemini / Anthropic Claude / OpenAI GPT / 本地模型（Ollama/LM Studio）
   - **And** 模型名称为文本输入框（如 `gemini/gemini-2.0-flash`、`claude-3-5-sonnet-20241022`、`gpt-4o`）
   - **And** API Key 输入框类型为 password（点击可切换显示/隐藏）
   - **And** 提供"测试连接"按钮，调用后端验证接口检查连接有效性
   - **And** 测试成功显示绿色 ✓，失败显示红色 ✗ + 错误信息

4. **AC-4: 评分模型配置**
   - **Given** 用户在 Settings Tab "评分模型" 区域操作
   - **When** 配置评分任务专用的模型和 API Key
   - **Then** 界面结构与对话模型一致（供应商下拉 + 模型名称 + API Key + 测试连接）
   - **And** 评分模型可与对话模型使用不同供应商和 Key（双层 Key 分离）
   - **And** 评分模型 Key 独立存储，互不干扰

5. **AC-5: 嵌入模型状态（只读）**
   - **Given** 用户在 Settings Tab "嵌入模型" 区域
   - **When** 面板加载
   - **Then** 显示 bge-m3 (Ollama) 状态（只读，不可修改）
   - **And** 状态通过后端健康检查获取（Ollama 运行中 + bge-m3 模型已拉取）
   - **And** 显示格式："bge-m3 · Ollama · 🟢 就绪" 或 "bge-m3 · Ollama · 🔴 未就绪"

6. **AC-6: API Key 安全存储**
   - **Given** 用户输入 API Key 并保存
   - **When** 插件存储配置
   - **Then** API Key 存储在 Obsidian 本地插件配置中（`.obsidian/plugins/canvas-learning-system/data.json`）
   - **And** API Key 在 UI 中默认不明文显示（password 类型输入框）
   - **And** API Key 不写入任何日志文件
   - **And** 首次配置 API Key 时显示安全提示："对话内容会发送给所选 LLM API 供应商"

7. **AC-7: 后端连接配置**
   - **Given** 用户在 Settings Tab "后端连接" 区域操作
   - **When** 配置后端地址
   - **Then** 提供后端 API 地址输入框（默认 `http://localhost:8001`）
   - **And** 提供 Neo4j 地址输入框（默认 `bolt://localhost:7689`）
   - **And** 保存后下次启动自动使用新地址

8. **AC-8: 模型配置同步到后端**
   - **Given** 用户在 Settings Tab 保存模型配置
   - **When** 配置变更保存
   - **Then** 前端将模型配置通过 `POST /api/v1/system/config` 同步到后端
   - **And** 后端更新 LiteLLM 配置（`core/litellm_config.py` 运行时刷新）
   - **And** 后端使用新配置进行后续 LLM 调用（评分/提取/索引等内层任务）
   - **And** 同步失败时前端显示错误提示，不阻塞本地保存

## Tasks / Subtasks

- [ ] **Task 1: 前端 — PluginSettingTab 注册与框架** (AC: #1)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/settings.ts`：继承 `PluginSettingTab`，实现 `display()` 方法
  - [ ] 1.2 在 `main.ts` 的 `onload()` 中调用 `this.addSettingTab(new CanvasLearningSettingTab(this.app, this))`
  - [ ] 1.3 定义 `CanvasLearningSettings` 接口（包含所有配置项字段及默认值）
  - [ ] 1.4 实现 `loadSettings()` / `saveSettings()` 方法（基于 Obsidian `loadData()` / `saveData()`）

- [ ] **Task 2: 前端 — 系统健康状态区域** (AC: #2)
  - [ ] 2.1 在 `display()` 顶部创建 "系统状态" 区域标题（`containerEl.createEl('h2', {text: '系统状态'})`）
  - [ ] 2.2 调用 `api-client.checkHealth()` 获取 5 个组件状态
  - [ ] 2.3 为每个组件渲染状态行：组件名称 + 状态图标（🟢/🟡/🔴）+ 状态文字
  - [ ] 2.4 添加"重新检测"按钮，点击后重新调用健康检查并刷新 UI
  - [ ] 2.5 后端不可达时全部显示红色，不阻塞其他设置区域

- [ ] **Task 3: 前端 — 对话模型配置区域** (AC: #3)
  - [ ] 3.1 创建 "对话模型" 区域标题 + 描述文字
  - [ ] 3.2 使用 `new Setting(containerEl)` 添加供应商下拉选择（Google Gemini / Anthropic Claude / OpenAI GPT / 本地模型）
  - [ ] 3.3 添加模型名称文本输入框（`addText`，placeholder 提示格式如 `gemini/gemini-2.0-flash`）
  - [ ] 3.4 添加 API Key 密码输入框（`addText` + `inputEl.type = 'password'`）+ 显示/隐藏切换按钮
  - [ ] 3.5 添加"测试连接"按钮（`addButton`），调用后端 `POST /api/v1/system/test-llm` 验证
  - [ ] 3.6 测试结果在按钮旁显示反馈（成功 ✓ 绿色 / 失败 ✗ 红色 + 错误原因）

- [ ] **Task 4: 前端 — 评分模型配置区域** (AC: #4)
  - [ ] 4.1 创建 "评分模型" 区域标题 + 描述（"用于 AutoSCORE 评分和知识提取的独立模型配置"）
  - [ ] 4.2 复用 Task 3 相同的 UI 模式（供应商 + 模型名称 + API Key + 测试连接）
  - [ ] 4.3 评分模型配置字段独立存储（`scoringProvider`, `scoringModel`, `scoringApiKey`）

- [ ] **Task 5: 前端 — 嵌入模型状态区域（只读）** (AC: #5)
  - [ ] 5.1 创建 "嵌入模型" 区域标题
  - [ ] 5.2 显示只读状态行：`bge-m3 · Ollama · [状态]`
  - [ ] 5.3 状态从健康检查结果中获取 Ollama 组件状态

- [ ] **Task 6: 前端 — API Key 安全处理** (AC: #6)
  - [ ] 6.1 所有 API Key 输入框默认使用 `type='password'`
  - [ ] 6.2 添加"眼睛"图标按钮切换 password/text
  - [ ] 6.3 首次输入 API Key 时显示 Obsidian `Notice` 安全提示（"对话内容会发送给所选 LLM API 供应商"）
  - [ ] 6.4 确保 `saveSettings()` 中不对 API Key 做 console.log 或其他日志输出

- [ ] **Task 7: 前端 — 后端连接配置区域** (AC: #7)
  - [ ] 7.1 创建 "后端连接" 区域标题
  - [ ] 7.2 添加后端 API 地址输入框（默认值 `http://localhost:8001`）
  - [ ] 7.3 添加 Neo4j 地址输入框（默认值 `bolt://localhost:7689`）

- [ ] **Task 8: 前端 — 数据管理区域占位** (AC: #1)
  - [ ] 8.1 创建 "数据管理" 区域标题
  - [ ] 8.2 添加"手动备份"按钮占位（点击显示 Notice "功能将在 Story 1.8 实现"）
  - [ ] 8.3 添加"重建索引"按钮占位（点击显示 Notice "功能将在 Story 2.7 实现"）

- [ ] **Task 9: 后端 — 模型配置接收与 LiteLLM 集成** (AC: #8)
  - [ ] 9.1 创建 `backend/app/core/litellm_config.py`：定义 `ModelTaskConfig(BaseModel)` 模型（provider, model_name, api_key）和 `SystemModelConfig(BaseModel)`（chat, scoring, embedding 三个任务配置）
  - [ ] 9.2 在 `backend/app/api/v1/system.py` 添加 `POST /api/v1/system/config` 端点：接收前端模型配置，写入运行时配置
  - [ ] 9.3 在 `backend/app/api/v1/system.py` 添加 `POST /api/v1/system/test-llm` 端点：使用 LiteLLM `completion()` 发送测试请求验证连接
  - [ ] 9.4 LiteLLM 调用封装：根据 provider 自动映射 model 名称格式（如 `gemini/gemini-2.0-flash`、`anthropic/claude-3-5-sonnet`）
  - [ ] 9.5 API Key 在后端内存中持有（运行时配置），不持久化到后端磁盘文件
  - [ ] 9.6 后端 API Key 不写入日志（logging filter 过滤包含 key/token 的字段）

- [ ] **Task 10: 前端 — Settings 类型定义** (AC: #1-#8)
  - [ ] 10.1 在 `obsidian-canvas-learning/src/types/settings.d.ts` 定义 `CanvasLearningSettings` 接口
  - [ ] 10.2 定义默认配置值常量 `DEFAULT_SETTINGS`
  - [ ] 10.3 在 `api-client.ts` 中添加 `postModelConfig()` 和 `testLlmConnection()` 方法

- [ ] **Task 11: 验证** (AC: #1-#8)
  - [ ] 11.1 Obsidian 中打开设置验证 6 个区域正确显示
  - [ ] 11.2 配置对话模型并测试连接，验证成功/失败反馈
  - [ ] 11.3 配置评分模型使用不同供应商，验证双层 Key 独立
  - [ ] 11.4 验证 API Key 输入框默认隐藏、可切换显示
  - [ ] 11.5 验证系统状态面板正确显示 5 个组件状态
  - [ ] 11.6 验证模型配置成功同步到后端（后端日志确认收到配置，Key 未出现在日志中）
  - [ ] 11.7 运行 `ruff check backend/app/core/litellm_config.py backend/app/api/v1/system.py` 确认 lint 通过
  - [ ] 11.8 运行 TypeScript 编译确认无错误

## Dev Notes

### 依赖关系

- **依赖 Story 1.1**：需要插件骨架（`main.ts`、`manifest.json`、`api-client.ts`）和 FastAPI 健康检查端点已就绪
- **可与 Story 1.2 并行**：Settings Tab 和 SetupWizard 是不同的 Obsidian 组件（PluginSettingTab vs Modal），互不干扰

### Obsidian PluginSettingTab API 关键点

Settings Tab 使用 Obsidian 原生 `PluginSettingTab` 类和 `Setting` API 构建，不使用 Svelte 组件：

```typescript
// obsidian-canvas-learning/src/settings.ts
import { App, PluginSettingTab, Setting } from 'obsidian';

export class CanvasLearningSettingTab extends PluginSettingTab {
    plugin: CanvasLearningPlugin;

    constructor(app: App, plugin: CanvasLearningPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    display(): void {
        const { containerEl } = this;
        containerEl.empty();

        // 系统状态区域
        containerEl.createEl('h2', { text: '系统状态' });
        // ... 状态灯渲染

        // 对话模型区域
        containerEl.createEl('h2', { text: '对话模型' });
        new Setting(containerEl)
            .setName('供应商')
            .setDesc('选择 LLM 供应商')
            .addDropdown(dropdown => dropdown
                .addOption('gemini', 'Google Gemini')
                .addOption('anthropic', 'Anthropic Claude')
                .addOption('openai', 'OpenAI GPT')
                .addOption('ollama', '本地模型 (Ollama/LM Studio)')
                .setValue(this.plugin.settings.chatProvider)
                .onChange(async (value) => {
                    this.plugin.settings.chatProvider = value;
                    await this.plugin.saveSettings();
                }));
        // ... 更多设置项
    }
}
```

### LiteLLM 模型名称格式

LiteLLM SDK 使用 `provider/model-name` 格式路由到不同供应商：

| 供应商 | LiteLLM model 参数格式 | 示例 |
|--------|----------------------|------|
| Google Gemini | `gemini/model-name` | `gemini/gemini-2.0-flash` |
| Anthropic Claude | `anthropic/model-name` | `anthropic/claude-3-5-sonnet-20241022` |
| OpenAI GPT | `openai/model-name` 或直接 `model-name` | `gpt-4o` |
| Ollama 本地 | `ollama/model-name` | `ollama/llama3` |
| LM Studio | `lm_studio/model-name` | `lm_studio/local-model` |

后端 `litellm_config.py` 需根据前端选择的 provider 自动拼接正确格式。

### 双层 Key 分离架构

| 层 | 用途 | Key 来源 | 配置位置 |
|----|------|---------|---------|
| 外层 | Agent 对话（用户 → LLM） | 用户自己的 Key | Settings Tab "对话模型" |
| 内层 | 后端评分/提取/索引 | 后端配置的 Key | Settings Tab "评分模型" |

- 对话模型 Key：Agent SDK 直接使用（前端侧发起 LLM 调用）
- 评分模型 Key：通过 `POST /api/v1/system/config` 同步到后端，后端 LiteLLM 使用

### API Key 安全约束（NFR-SEC-02）

1. **存储**：仅存 Obsidian 本地 `data.json`，不上传外部服务
2. **显示**：UI 中默认 password 类型，可切换显示
3. **日志**：禁止出现在 console.log、文件日志、网络请求日志中
4. **传输**：前端→后端同步走 localhost（NFR-SEC-05），不暴露外部端口
5. **首次提示**：首次输入 Key 时提示用户数据会发送给 LLM 供应商（NFR-SEC-04）

### 后端 LiteLLM 测试连接实现指引

```python
# backend/app/api/v1/system.py（追加）
import litellm

@router.post("/test-llm")
async def test_llm_connection(config: ModelTaskConfig) -> dict:
    """测试 LLM 连接有效性"""
    try:
        model_name = f"{config.provider}/{config.model_name}" if config.provider != "openai" else config.model_name
        response = await litellm.acompletion(
            model=model_name,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
            api_key=config.api_key,
        )
        return {
            "data": {"status": "success", "model": model_name},
            "meta": {"timestamp": datetime.utcnow().isoformat() + "Z"}
        }
    except Exception as e:
        return {
            "data": {"status": "failed", "error": str(e)},
            "meta": {"timestamp": datetime.utcnow().isoformat() + "Z"}
        }
```

### Settings 类型定义指引

```typescript
// obsidian-canvas-learning/src/types/settings.d.ts
export interface CanvasLearningSettings {
    // 对话模型
    chatProvider: string;       // 'gemini' | 'anthropic' | 'openai' | 'ollama'
    chatModel: string;          // e.g. 'gemini-2.0-flash'
    chatApiKey: string;

    // 评分模型
    scoringProvider: string;
    scoringModel: string;
    scoringApiKey: string;

    // 后端连接
    backendUrl: string;         // default: 'http://localhost:8001'
    neo4jUrl: string;           // default: 'bolt://localhost:7689'
}

export const DEFAULT_SETTINGS: CanvasLearningSettings = {
    chatProvider: 'gemini',
    chatModel: '',
    chatApiKey: '',
    scoringProvider: 'gemini',
    scoringModel: '',
    scoringApiKey: '',
    backendUrl: 'http://localhost:8001',
    neo4jUrl: 'bolt://localhost:7689',
};
```

### FR 覆盖

| FR ID | 覆盖方式 |
|-------|---------|
| FR-SYS-02 | AC-3, AC-4: 供应商/模型/API Key 完整配置 |
| FR-SYS-03 | AC-3, AC-4, AC-5: 对话/评分/Embedding 三任务独立配置 |
| FR-SYS-04 | AC-2: 系统健康状态面板 5 组件状态灯 |
| NFR-SEC-02 | AC-6: API Key 安全存储 + 不明文显示 + 不入日志 |
| NFR-SEC-04 | AC-6: 首次配置敏感数据提示 |
| NFR-SEC-05 | AC-8: 前后端通信走 localhost |

### 不做的事项（防蔓延）

- 不实现 SetupWizard 安装引导（Story 1.2 负责）
- 不实现一键启动/重启后端（Story 1.8 负责）
- 不实现数据备份/恢复功能（Story 1.8 负责，本 Story 仅放占位按钮）
- 不实现重建索引功能（Story 2.7 负责，本 Story 仅放占位按钮）
- 不实现多学科配置（Story 1.9 负责）
- 不实现 Agent 对话功能（Story 3.1 负责）
- 不创建 Svelte 组件（Settings Tab 使用原生 Setting API）

### Project Structure Notes

- `obsidian-canvas-learning/src/settings.ts` — 新建文件，PluginSettingTab 实现
- `obsidian-canvas-learning/src/types/settings.d.ts` — 新建文件，Settings 类型定义
- `obsidian-canvas-learning/main.ts` — 追加 `addSettingTab()` 和 `loadSettings()/saveSettings()` 方法
- `obsidian-canvas-learning/src/services/api-client.ts` — 追加 `postModelConfig()` 和 `testLlmConnection()` 方法
- `backend/app/core/litellm_config.py` — 新建文件，LiteLLM 配置管理
- `backend/app/api/v1/system.py` — 追加 `POST /config` 和 `POST /test-llm` 端点
- 所有变更为加法编辑，不修改 Story 1.1 已有功能

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure] — settings.ts 位置和 litellm_config.py 位置
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies] — LiteLLM 统一层和双层 Key 分离
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security] — API Key 安全约束
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns] — REST 端点 `/api/v1/system/`
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Settings Tab 布局] — 6 个配置区域定义
- [Source: _bmad-output/planning-artifacts/prd.md#模型灵活性] — LLM 供应商列表和配置粒度
- [Source: _bmad-output/planning-artifacts/prd.md#安全与隐私] — API Key 安全要求
- [Source: _bmad-output/planning-artifacts/prd.md#能力域 12：系统配置与运维] — FR-SYS-02/03/04

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
