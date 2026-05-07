# Round-22 Day 2 设计文档：Vault 直接访问完整方案

> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **调研日期**: 2026-05-06
> **调研方法**: 5 Agent 并行 Deep Explore
> **关联 Story**: 10.3 (Day 2 Cleanup + Vault Mount)
> **用户初衷锚定**: D2 (Round-18 L805) "知识库不用上传文件，直接访问指定文件夹"

---

## Executive Summary（核心结论）

**5 个独立 Agent 调研收敛出 4 个关键事实**：

1. **应用层障碍极小** — TutorBot ReadFileTool 沙箱**已默认关闭**（`manager.py:438` 硬编码 `restrict_to_workspace=False`），无需任何代码改造即可读 host vault 路径。
2. **基础设施层有 1 个 bug** — `docker-compose.canvas.yml` bind mount 路径**指向错误 worktree**（feature-obsidian-hybrid-dev 而非当前 feature-deeptutor-canvas-mvp），Day 2 必修。
3. **架构层需新增 1 模块** — DocumentAdder 强制 `shutil.copy2` 到 `raw/`，违反"vault 单一真相源" → 加 `vault_mode: bool = False` 参数（30 分钟改）+ 容器内 polling daemon（120 行）。
4. **macOS 特有限制 1 条** — inotify 不跨容器边界 → polling 5s 是唯一可行方案，闭环时间 5-7s（用户改 md → fork UI 看到新邻居）。

**Story 10.3 工作量重估**：从 spec 现 0.5 day → **真实 1.5-2 day**。建议拆为 Story 10.3a（核心修复 2-3h）+ Story 10.3b（vault 直读升级 6-9h）。

---

## 一、5 Agent 调研发现整合矩阵

| Agent | 关键发现 | 影响 Story 10.3 |
|---|---|---|
| **A** TutorBot filesystem | ReadFileTool L42-122 已实装 + 沙箱默认关闭 + MCP 已支持 | **0 代码改动** 即可读 host vault；MCP server 配置可选优雅升级 |
| **B** Docker bind mount + macOS 同步 | virtiofs 性能 4× + FSEvents 跨界限制 + vault 路径 bug + 写冲突 | 必修路径 + polling 唯一方案 + Day 9 fcntl lock 提前到 Day 2 |
| **C** KB 上传 vs vault 直读 | DocumentAdder L122 `shutil.copy2` 强制复制 → `vault_mode` 30min 改 + LlamaIndex `index.insert()` 已实现 | 新增 vault_mode 参数 + VaultMonitor polling daemon |
| **D** Story 10.3 vs 10.4 关系 | 10.3 = 读取层（实时） + 10.4 = 注入层（快照），互补零冗余 | 10.3 → 10.4 顺序锁定，**Day 2 + Day 3-4 节奏不变** |
| **E** vault hot-reload 增量 | wikilink_graph_service `refresh()` 全量重建（changed_files 占位） + macOS polling 5s + LlamaIndex `index.insert()` 已支持增量 | Day 2 polling daemon (120 行) + DeepTutor auto-load vault (40 行) |

---

## 二、完整数据流架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           用户层（Host macOS）                                │
│  ┌─────────────────┐                                ┌─────────────────────┐ │
│  │  Obsidian       │    Cmd+S 保存 md              │  Browser :3782      │ │
│  │  vault/节点/*.md│◄──────────────────────────────►│  fork UI            │ │
│  └────────┬────────┘                                └──────────┬──────────┘ │
│           │                                                    │            │
└───────────┼────────────────────────────────────────────────────┼────────────┘
            │ Docker bind mount                                  │ HTTP
            │ (Apple Silicon virtiofs, 4× faster than osxfs)     │
            │                                                    │
┌───────────▼────────────────────────────────────────────────────▼────────────┐
│                           容器层                                              │
│  ┌──────────────────────┐                ┌────────────────────────────────┐│
│  │ /vault (容器内挂载)   │                │ DeepTutor fork (:8001 + :3782) ││
│  │  节点/recursion.md    │                │  ┌──────────────────────────┐  ││
│  │  原白板/whiteboard.md │                │  │ TutorBot AgentLoop      │  ││
│  └──────┬───────────────┘                │  │  - ReadFileTool         │  ││
│         │                                 │  │    (沙箱默认关闭)       │  ││
│  ┌──────▼─────────────────────┐          │  │  - WriteFileTool        │  ││
│  │ VaultMonitor polling       │          │  │    (Day 9 加 fcntl lock)│  ││
│  │  (容器内启动脚本，120 行)   │          │  │  - MCP filesystem       │  ││
│  │  - 每 5s 扫 mtime          │          │  │    (可选 0 代码改进)    │  ││
│  │  - changed_files → POST    │          │  └──────────────────────────┘  ││
│  └──────┬─────────────────────┘          └─────────────┬──────────────────┘│
│         │                                              │ HTTP                │
│         ▼                                              ▼                     │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │ Canvas backend (:8011)                                        │          │
│  │  ┌────────────────────────────────────────────────────────┐  │          │
│  │  │ wikilink_graph_service.py                              │  │          │
│  │  │  - build(vault_path)  ← 全量扫 vault → NetworkX 图     │  │          │
│  │  │  - refresh(changed_files=...)  ← Day 2 调用入口        │  │          │
│  │  │  - get_neighbors(note_path, hop)  ← 实时查询          │  │          │
│  │  └────────────────────────────────────────────────────────┘  │          │
│  └──────────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
        ▲
        │
        │ 双路径访问 vault
        │
┌───────┴─────────────────────────────────────────────────────────────────────┐
│  路径 A (实时单文件, 0s 延迟):                                                │
│    用户点 callout → fork TutorBot → ReadFileTool("/vault/节点/X.md")         │
│    立即返回（无索引、无缓存、无 polling）                                     │
│                                                                              │
│  路径 B (RAG 检索, 5-7s 延迟):                                                │
│    VaultMonitor polling 5s → 检测 mtime 变化 → POST /api/v1/wikilink/refresh │
│    Canvas backend 扫变更 → DeepTutor LlamaIndex index.insert() 增量索引      │
│    用户问 AI → Chat Agent RAG 检索 → 返回新内容                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、Day 2 真实工作量重估（5 agent 整合）

| # | 任务 | 文件 | 工作量 | Agent 来源 |
|---|---|---|---|---|
| 1 | docker-compose.canvas.yml vault 路径修（feature-obsidian-hybrid-dev → feature-deeptutor-canvas-mvp） | `integration/deeptutor-patches/docker/docker-compose.canvas.yml` | 30 min | B |
| 2 | CalloutBlock 1 行修（`<div>{body}</div>` → `<MarkdownRenderer>`），含 TimelineBlock/FlashCardsBlock/DeepDiveBlock 同模式 | fork `web/.../blocks/CalloutBlock.tsx` 等 4 个 | 30 min | A 已知 |
| 3 | `client.py` neighbors path param 修（query → path） | fork `deeptutor/services/canvas/client.py:65` | 30 min | 之前已知 |
| 4 | **VaultMonitor polling daemon**（每 5s 扫 mtime + POST refresh） | 新建 fork `scripts/vault_monitor.py` | **4-5h** | C+E |
| 5 | **DocumentAdder `vault_mode` 参数** + `kb_config.json` `vault_mode/vault_path` 字段 | fork `deeptutor/knowledge/add_documents.py` + `routers/knowledge.py` | **1h** | C |
| 6 | **DeepTutor 自动加载 vault**（`pipeline.initialize` 特殊处理 `kb_name="canvas_vault"`） | fork `deeptutor/services/rag/pipelines/llamaindex/pipeline.py` | **1h** | E |
| 7 | **`vault_file_lock()` + atomic rename**（fcntl + temp/replace 防双写冲突） | 新建 Canvas `backend/app/services/vault_write_service.py` | **2-3h** | B |
| 8 | Docker Compose 容器启动脚本加 polling daemon | fork `Dockerfile` 或 `docker-compose.yml` `command:` | 30 min | E |
| 9 | E2E 测试：Obsidian 改 md → 5-7s 内 fork UI 看到新邻居 | 新建 `tests/e2e/test_vault_hot_update.py` | 1-2h | E |
| 10 | 性能验证：首次 `wikilink/build` < 500ms（28+ md 文件） | 验收命令 | 30 min | B |

**总计**: **9-13h ≈ 1.5-2 day**（vs 原 Story 10.3 spec 0.5 day）

---

## 四、Story 10.3 spec 修订建议

### 选项 A：扩展 Story 10.3（保持单 Story，1.5-2 day）

更新 `10-3-day2-cleanup-vault-mount.md`：
- estimate_hours: 4 → **12**
- 加 4 个新 AC（vault_mode + polling + auto-load + file lock）
- 加 6 个新 Tasks（任务 #4-10）

### 选项 B：拆为 10.3a + 10.3b（**推荐**）

**Story 10.3a: 核心修复（2-3h）— Day 2 上午**
- 路径修 + CalloutBlock + path param
- 验收：vault mount 通 + `wikilink/build` 看到 total_nodes > 0
- AC #1-4（现 spec）

**Story 10.3b: Vault 直读升级（6-9h）— Day 2 下午 + Day 3 部分**
- vault_mode 参数 + VaultMonitor polling + DeepTutor auto-load + file lock
- 验收：Obsidian 改 md → 5-7s 内 fork UI 反映
- AC #5-8（新增）

**为何推荐 B**：
- 10.3a 完成 = 早期价值反馈（callout 渲染 + vault 通）
- 10.3b 渐进升级 = 风险隔离（polling 失败不阻塞 callout 修复）

---

## 五、双路径架构（TutorBot 直读 + RAG polling 增量）

### 路径 A：TutorBot 直读（实时单文件，0s 延迟）

**适用场景**: 用户点 fork callout → AI 当场读 vault md

```python
# 0 代码改动！TutorBot ReadFileTool 已能读 host vault
# 默认沙箱关闭 → ReadFileTool("~/Desktop/canvas/canvas-vault/节点/recursion.md") 直接通

# 可选优雅升级（30 min）：MCP filesystem server
# fork .env 加：
# MCP_VAULT_FS_COMMAND=npx
# MCP_VAULT_FS_ARGS=["@modelcontextprotocol/server-filesystem", "/vault"]
# 自动注册 mcp_vault_fs_read_file/write_file/list_directory 工具
```

**优势**：
- 0 索引延迟（用户改 md 后下次工具调用立即读到新内容）
- 0 缓存陈旧（绕过 LlamaIndex 索引）
- 沙箱已开放（无权限障碍）

**限制**：
- 需要 LLM 主动调用工具（不是被动召回）
- 单文件查询（不适合"全 vault 检索"场景）

### 路径 B：LlamaIndex RAG + polling 增量（5-7s 延迟）

**适用场景**: 用户问"递归基本情况是什么" → Chat Agent RAG 全 vault 召回

**实施清单**:

```python
# 1. DocumentAdder.add_documents 加 vault_mode 参数（30 min, Agent C）
def add_documents(self, source_files, allow_duplicates=False, vault_mode=False):
    if vault_mode:
        files_to_process.append(source_path)  # 不复制，直接索引原路径
    else:
        shutil.copy2(source_path, dest_path)   # 旧路径保持兼容

# 2. DeepTutor pipeline.initialize 特殊处理（40 行，Agent E）
async def initialize(self, kb_name, file_paths, **kwargs):
    if kb_name == "canvas_vault":
        vault_path = Path(os.getenv("CANVAS_VAULT_PATH", "/vault"))
        file_paths = list(vault_path.rglob("*.md"))

# 3. VaultMonitor polling daemon（120 行，Agent E）
# 见 Section 六的具体代码

# 4. 容器内启动脚本（10 行，Agent E）
# Dockerfile CMD 改：
# python scripts/vault_monitor.py & python -m uvicorn deeptutor.api.main:app
```

**优势**：
- 全 vault 语义检索（RAG 召回 top-K）
- 用户感知时间（5-7s）远低于"卡顿阈值"

**限制**：
- 5s polling 周期内有"陈旧窗口"
- LlamaIndex 索引体积增加（每文件 chunks + embeddings）

### 双路径互补

```
用户场景                       推荐路径
──────────────────────────────────────────────────────
点 callout → 看节点详情     →  路径 A（TutorBot 直读）
点 callout → 写笔记 + 看 AI → 路径 A 写 + 路径 B 索引
全文搜索"递归"              →  路径 B（RAG）
看 wikilink 邻居            →  路径 B（Canvas wikilink_graph_service）
```

---

## 六、关键代码片段（直接可用）

### VaultMonitor polling daemon（120 行，Agent E）

```python
# fork scripts/vault_monitor.py
import asyncio
from pathlib import Path
import httpx

async def monitor_vault(vault_path: Path, check_interval_sec: int = 5):
    """每 N 秒扫 vault md 的 mtime，检测变更触发 refresh."""
    mtime_cache: dict[str, float] = {}
    client = httpx.AsyncClient(base_url="http://canvas-backend:8011")

    while True:
        try:
            changed_files = []
            for md_file in vault_path.rglob("*.md"):
                rel_path = str(md_file.relative_to(vault_path))
                current_mtime = md_file.stat().st_mtime
                cached = mtime_cache.get(rel_path)
                if cached is None or current_mtime > cached:
                    changed_files.append(rel_path)
                    mtime_cache[rel_path] = current_mtime

            if changed_files:
                await client.post(
                    "/api/v1/wikilink/refresh",
                    json={"changed_files": changed_files}
                )
                print(f"[VaultMonitor] Refreshed {len(changed_files)} files")

            await asyncio.sleep(check_interval_sec)
        except Exception as e:
            print(f"[VaultMonitor] Error: {e}")
            await asyncio.sleep(check_interval_sec)

if __name__ == "__main__":
    vault = Path(os.getenv("CANVAS_VAULT_PATH", "/vault"))
    asyncio.run(monitor_vault(vault, check_interval_sec=5))
```

### vault_file_lock + atomic rename（Agent B 推荐）

```python
# Canvas backend/app/services/vault_write_service.py
import fcntl
from pathlib import Path
from contextlib import asynccontextmanager

@asynccontextmanager
async def vault_file_lock(md_path: Path, timeout: float = 5.0):
    """Unix/macOS fcntl 文件级锁（Day 9 必备 + Day 2 提前部署）."""
    lock_file = md_path.with_suffix(md_path.suffix + ".lock")
    try:
        with open(lock_file, "w") as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
    except (IOError, OSError):
        raise FileExistsError(f"vault md 被另一进程锁住: {md_path}")
    finally:
        lock_file.unlink(missing_ok=True)

async def write_user_note_atomic(node_id: str, content: str):
    """原子写（temp → final rename）防 partial overwrite."""
    md_path = settings.canvas_base_path / "节点" / f"{node_id}.md"
    async with vault_file_lock(md_path):
        temp = md_path.with_suffix(".tmp")
        temp.write_text(content, encoding="utf-8")
        temp.replace(md_path)  # 原子 rename
        return md_path.stat().st_mtime
```

---

## 七、macOS 特有问题缓解清单

| 问题 | 缓解策略 | 影响 Day |
|---|---|---|
| FSEvents 不跨 bind mount 边界 | polling 5s 周期（VaultMonitor） | Day 2 |
| fsync 阻塞（write_text 比 Linux 慢 2-3×） | 接受性能（用户写笔记不频繁） | 性能预期 |
| 中文目录编码（"原白板/节点/" Alpine Linux 失配） | 容器 ENV 设 LANG=zh_CN.UTF-8 + LC_ALL=zh_CN.UTF-8 | Day 2 验证 |
| 双写冲突（用户 + TutorBot 并发） | fcntl lock + atomic rename | Day 2 提前部署（原 Day 9） |
| bind mount 性能（Apple Silicon virtiofs） | 已是最优，无需调整 | — |

---

## 八、闭环时间预期（用户视角）

| 场景 | 操作链 | 闭环时间 |
|---|---|---|
| **TutorBot 直读单文件**（路径 A） | 点 callout → AI 调 ReadFileTool → 返回内容 | **0-2s** |
| **Obsidian 改 md → wikilink 邻居更新**（路径 B） | Cmd+S → polling 5s → graph refresh 1s → GET neighbors | **5-7s** |
| **fork UI 写笔记 → 触发 RAG 重索引**（路径 B） | WriteFileTool → polling 5s → graph + LlamaIndex.insert 1-2s | **6-9s** |
| **AI 回答含最新 vault 内容**（端到端） | 写 → polling → index → 问 AI → LLM 思考 5s | **10-15s** |

**用户体验判定**：5-15s 落在"后台异步"区间（用户期望 100-500ms 实时响应，10-15s 视为"系统正在处理"），可接受。

---

## 九、风险与降级方案

| 风险 | 概率 | 严重度 | 缓解 |
|---|---|---|---|
| 用户输入丢失（Obsidian + DeepTutor 并写） | ~10% | 🔴 HIGH | fcntl lock + atomic rename（Day 2 提前部署） |
| File corruption（partial overwrite） | <1% | 🔴 HIGH | temp + rename，不能中断 |
| Obsidian 缓存陈旧（改了看不到） | ~5% | 🟠 MED | 2s polling + 强制刷新提示 |
| polling 5s 周期内查询陈旧 | 100% | 🟡 LOW | 接受 5s 延迟（MVP 阶段） |
| LlamaIndex 全量索引慢（vault > 1000 md） | <5%（MVP 阶段） | 🟡 LOW | Day 3+ 增量更新优化 |
| 中文目录在 Alpine Linux 容器编码失配 | ~30% | 🟠 MED | 容器 ENV LANG/LC_ALL 设 UTF-8 |

---

## 十、Day 2 推荐实施清单（按优先级）

### Phase 1: 必修（2-3h，Story 10.3a）
- [ ] docker-compose.canvas.yml vault 路径修（指向当前 worktree）
- [ ] CalloutBlock + TimelineBlock + FlashCardsBlock + DeepDiveBlock 渲染 wikilink（4 文件 1 行修）
- [ ] client.py neighbors path param 修
- [ ] 验证 `wikilink/build` 返回 `total_nodes > 0`

### Phase 2: vault 直读升级（6-9h，Story 10.3b）
- [ ] DocumentAdder vault_mode 参数（30min）
- [ ] DeepTutor pipeline.initialize 特殊处理 canvas_vault（1h）
- [ ] VaultMonitor polling daemon（120 行，4-5h）
- [ ] Docker Compose 启动脚本加 polling
- [ ] vault_file_lock + atomic rename（2-3h，Day 9 提前）
- [ ] E2E 测试 Obsidian 改 md → 5-7s 内 fork UI 反映

### Phase 3 (可选): MCP filesystem 优雅升级（30 min）
- [ ] fork .env 加 MCP_VAULT_FS_* 配置
- [ ] 验证 mcp_vault_fs_read_file 工具被 TutorBot 注册

### 验收标准（合并 Phase 1 + 2）
- [ ] `wikilink/build` 返回 `total_nodes >= 28`（或 vault 实际 md 数）
- [ ] callout 内 `[[xxx]]` 渲染为蓝链
- [ ] Obsidian 编辑 vault md → 5-7s 内 fork wikilink 邻居返回新数据
- [ ] DeepTutor TutorBot 能 ReadFile vault 任意路径（应用层无障碍）
- [ ] DeepTutor LlamaIndex 索引指向 `/vault`（不是 `data/knowledge_bases/`）
- [ ] 双写冲突测试：用户 + TutorBot 并发写同一 md，无数据丢失

---

## 十一、关联文档

- **Round-22 主报告**: `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
- **Round-22 Deep Explore**: `_bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md`
- **Story 10.3 现 spec**: `_bmad-output/implementation-artifacts/epic-10/10-3-day2-cleanup-vault-mount.md`
- **Story 10.3 UAT**: `_bmad-output/验收单/Story-10.3-day2-cleanup-vault-mount.md`
- **Story 10.4 (依赖 10.3)**: `_bmad-output/implementation-artifacts/epic-10/10-4-day3-4-canvas-vault-adapter.md`
- **决策批注 D17**: `_bmad-output/决策批注/D17-round22-fork-mvp-2026-05-06.md`

---

## 十二、5 Agent 调研产物索引

| Agent | 主题 | 输出文件 |
|---|---|---|
| **A** | TutorBot filesystem 工具能力 | `tasks/ae5727084e325f24f.output` |
| **B** | Docker bind mount + macOS 同步 | `tasks/a857945dc0babc1a2.output` |
| **C** | KB 上传 vs vault 直读 | `tasks/acff37e0df2635992.output` |
| **D** | Story 10.3 vs 10.4 关系 | `tasks/a549c63619bf2b30f.output` |
| **E** | vault hot-reload 增量索引 | `tasks/a943b5e6c7166d708.output` |

---

*Day 2 设计文档完成。等用户决策：(A) 扩展 Story 10.3 到 1.5-2 day / (B) 拆为 10.3a + 10.3b 渐进交付 / (C) 直接按本文档跑 Day 2 实施。*


**User：我这里的关键在于 deeptutor 他原本的使用设计是否像 claude code 一样可以阅读本地文件，还是说像 googleLM 一样，我要把相关文件上传到知识库，我需要知道原本的设计使用流程**