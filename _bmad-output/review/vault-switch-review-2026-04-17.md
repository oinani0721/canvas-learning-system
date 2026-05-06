# Vault 快速切换方案 — 审计文档（给用户批注）

> 日期：2026-04-17 | EPIC1-BMAD-DEV-ASSESS-2026-04-17
> 
> 目的：让你审查我的理解是否正确，标注我遗漏或误解的地方。
> 请在任何你想评论的段落下面加 `> BMAD-ANNO:` 批注。

---

## 一、你的需求（我的理解）

你有多门课（CS188、CS61B、线性代数……），每门课有自己独立的 Obsidian 笔记库（vault）。
你需要**每天多次**在不同课之间切换，而且你不想去碰配置文件或命令行。

理想体验：就像电视换台 — 按一下就从 CS188 切到 CS61B，不用关机重开。

---

## 二、我之前遗漏了什么（自我检讨）

### 我犯的错误

**Story 1.8（Vault Switch Runtime API）已经完整定义了你需要的方案**，但我完全没有去看它。

我犯的具体错误：
1. 我只搜了 `openspec/` 和 `_bmad-archive/legacy-stories/`，**没有搜 `_bmad-output/implementation-artifacts/epic-1/`**
   User：肯定是我关于 claude  code 的设置出了一些问题，所以请你仔细 deep explore 解决这个注意力的问题，归档处理掉过时的内容
2. 这个目录下有 13 个完整的 Story spec 文件（1.1 到 1.13），每个都是 `ready-for-dev` 状态
3. 我在 Plan 里从零设计了一套方案，实际上是在重复 Story 1.8 已经写好的内容
4. 更糟糕的是，我的方案缺了 Story 1.8 里的一些关键设计（下面会详细说）

### Story 1.8 已经定义好的内容

| 功能 | Story 1.8 的定义 | 我的 Plan 里有没有 |
|------|-----------------|-------------------|
| `POST /api/v1/vault/switch` 切换端点 | ✅ 有完整 AC + Task | ✅ 类似但细节不同 |
| `GET /api/v1/vault/current` 查当前 vault | ✅ AC #3 | ❌ 我漏了这个 |
| VaultSwitchCoordinator（优雅切换） | ✅ Task 3：切换期间新请求返回 503 | ❌ 我完全没考虑并发安全 |
| `cache_clear()` 机制 | ✅ Task 2：清除 `@lru_cache` + 修改 `os.environ` | ❌ 我用了 in-place mutation（不同方案） |
| Claudian 自动检测 vault 切换 | ✅ AC #5（由 Story 1.12 实现） | ❌ 我完全没考虑自动检测 |
| 切换后日志记录 | ✅ AC #7：structlog 记录 | ❌ 我漏了 |
| 路径验证（必须含 `.obsidian/`） | ✅ Task 1.4 | ✅ 有 |

### 还有两个配套 Story 我也漏了

**Story 1.9: LanceDB vault_id 命名空间隔离**
- 每门课的搜索数据物理隔离（表名加 vault_id 前缀，如 `cs188_note_chunks`）
- 切换 vault 后搜索自动只查当前课的数据
- 我的 Plan 里说"MVP 可接受混合数据"— 但 Story 1.9 已经设计了完整的隔离方案

**Story 1.12: MCP 基础设施工具**
- Claudian 获得 `switch_vault` 和 `check_backend_health` 两个工具
- 你在 Obsidian 里打开另一个 vault，Claudian 自动检测并切换后端
- 有独立的权限层（DEPLOYMENT_TOOLS），防止恶意 prompt 注入

---

## 三、完整的依赖链（你需要知道的）

```
Story 1.7 ✅ 已完成
  └── .env 变量化 + Docker Compose 配置
        │
        ▼
Story 1.8 📋 下一步
  └── Vault 切换 API（后端）
  │     • POST /vault/switch — 切换笔记库
  │     • GET /vault/current — 查看当前笔记库
  │     • VaultSwitchCoordinator — 切换时保护正在进行的操作
  │     • 预计工时：6 小时
  │
  ├──▶ Story 1.9 📋 之后
  │     └── LanceDB 数据隔离
  │           • 每门课的搜索索引物理隔离
  │           • 切换后搜索只查当前课的数据
  │           • 预计工时：6 小时
  │
  └──▶ Story 1.12 📋 之后
        └── Claudian 自动检测 + MCP 工具
              • Claudian 自动发现你打开了哪个 vault
              • 自动切换后端到对应的课程数据
              • 预计工时：5 小时
```

---

## 四、Story 1.8 没有回答的一个问题（需要你确认）

### Docker 挂载问题

Story 1.8 设计了后端的"换台"功能，但有一个基础设施层面的问题**它没有提到**：

**现在的 Docker 容器只能看到一个文件夹**。`docker-compose.yml` 里写的是：
```
你的 canvas-vault/ 文件夹 → 映射到容器里的 /app/vault
```

就像你只把一本课的笔记本放进了教室，其他课的笔记本还在家里。后端就算有了"换台"功能，也没法打开家里的笔记本。

**解决方案**：把所有课的笔记本都放进同一个书包（父目录），然后把整个书包带进教室：

```
你的情况（现在）:                  你需要的:
─────────────                    ─────────────
canvas-vault/ → /app/vault       vaults/ → /app/vaults
  ├── raw/                         ├── CS188/
  ├── wiki/                        │   ├── .obsidian/
  └── ...                          │   ├── raw/
                                   │   └── wiki/
只能看到一门课                      ├── CS61B/
                                   │   ├── .obsidian/
                                   │   └── ...
                                   └── canvas-vault/（现有的）
                                       └── ...
                                   能看到所有课
```

**需要做的改动**:
1. 创建一个 `vaults/` 文件夹
2. 把现有的 `canvas-vault/` 移进去
3. 修改 `.env` 里的路径（从指向一个 vault 改为指向父目录）
4. 修改 `docker-compose.yml` 的挂载（从挂一个 vault 改为挂父目录）
5. **重启一次 Docker**（只需要这一次，之后切换就不用重启了）

### 需要你确认

> **问题**：这个"父目录挂载"方案是否应该作为 Story 1.8 的前置步骤？
> 还是说你打算用其他方式组织不同课的 vault 文件夹？
> 
> 批注位置 ▼我觉得可行

---

## 五、技术方案对比（两种"换台"机制）

| 方面 | Story 1.8 的方案 | 我之前 Plan 的方案 |
|------|-----------------|-------------------|
| **换台方式** | 清除缓存 + 修改环境变量 + 重建 Settings 对象 | 直接修改 Settings 对象的字段 |
| **并发保护** | ✅ VaultSwitchCoordinator（切换期间新请求等待） | ❌ 无保护 |
| **日志记录** | ✅ structlog 记录每次切换 | ❌ 无 |
| **前端 UI** | ❌ 未定义（Story 1.8 只做后端） | ✅ 有 vault 下拉选择器 |
| **数据隔离** | ✅ 由 Story 1.9 实现物理隔离 | ❌ "MVP 可接受混合"（偷懒） |
| **自动检测** | ✅ 由 Story 1.12 实现 Claudian 自动切换 | ❌ 无 |

**结论**：Story 1.8 的方案更完整、更安全。我的 Plan 应该直接按 Story 1.8 来实现，而不是另起炉灶。

---

## 六、实施顺序建议

按 BMAD Story 依赖链，建议的实施顺序：

| 步骤 | 做什么 | 效果 |
|------|--------|------|
| ① 基础设施准备 | 创建 `vaults/` 父目录 + 修改 Docker 挂载 + 一次性重启 | Docker 容器能看到所有 vault |
| ② Story 1.8 | 实现 vault 切换 API + VaultSwitchCoordinator | 可以通过 API 切换，不用重启 |
| ③ Story 1.9 | LanceDB 表名加 vault_id 前缀 | 搜索不会串门 |
| ④ Story 1.12 | Claudian MCP 工具 | Claudian 自动帮你切换 |

步骤 ① 不在任何 Story 里，但是 Story 1.8 能工作的**前提条件**。

---

## 七、需要你批注的问题清单

请在下面每个问题后加 `> BMAD-ANNO:` 批注：

### Q1: 父目录方案

你所有课的 vault 打算放在哪个位置？
- A: 项目内 `canvas-learning-system/vaults/`（和代码放一起）
- B: 项目外的某个路径（如 `~/Documents/vaults/`） User：我只聚焦于一个问题，后面如果我新建其他学科的 vault ，那么我的 Canvas learning systeam 如何部署，父目录的位置会影响这一点吗？
- C: 其他位置

> 批注位置 ▼

### Q2: 实施顺序

你想先做哪个？
- A: 先做基础设施 + Story 1.8（能切换但搜索可能串门）
- B: 一步到位做 1.8 + 1.9（切换 + 数据隔离，但要更久）
  

> 批注位置 ▼
> B

### Q3: 前端 UI

Story 1.8 只定义了后端 API，没有前端 UI。你希望：
- A: 先只用 Claudian 语音/文字切换（"帮我切到 CS61B"）
- B: 在前端加一个下拉选择器，手动点选
- C: 两个都要

> 批注位置 ▼
> 一个问题，我开新的 vault 的话，你最好以插件或者相关脚本的方式，然后我给 claude code 阅读来帮我一键部署Canvas learning systeam 到我当前所学习学科的路径

### Q4: 现有 canvas-vault 的处理

现有的 `canvas-vault/`（刚刚初始化好的）应该怎么办？
- A: 移到 `vaults/canvas-vault/`，作为默认 vault
- B: 改名为具体课程（如 `vaults/CS188/`）
- C: 保留在原位，新 vault 放到别的地方

> 批注位置 ▼

---

## 八、我的教训

这次犯的错误给我的教训：

1. **先查 Story 再设计** — `_bmad-output/implementation-artifacts/epic-1/` 里有完整的 Story spec，应该是第一个搜索位置
2. **不要重新发明轮子** — 用户花了时间做的 BMAD 13-Story QA 已经覆盖了 vault 切换的完整方案
3. **依赖链很重要** — Story 1.8 → 1.9 → 1.12 是一条设计好的链路，跳过任何一环都会缺功能
