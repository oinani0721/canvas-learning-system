# EPIC-31 对抗性审查 — 同步问题事后分析

> 日期: 2026-02-10
> 触发: 对抗性审查后用户追问 "阻塞项是否已实现但未同步"

---

## 1. 发现的三层同步断裂

### 层1: Context Compaction 摘要幻觉
| 问题 | 详情 |
|------|------|
| **现象** | 上一轮会话的 compaction 摘要声称 "Story 31.A.7 TTLCache startup warning - earlier check found it at line 503-505: `logger.warning('VerificationService using IN-MEMORY TTLCache...')`" |
| **事实** | `verification_service.py:480-490` 只有 `logger.info(...)` 初始化状态日志。L503-505 是 `start_session` 方法签名。**不存在** "IN-MEMORY TTLCache" 警告文字 |
| **根因** | Context compaction 在压缩长对话时，将 **测试文件中的期望断言** 与 **实际代码内容** 混淆，生成了虚假的"已找到"结论 |
| **影响** | 导致对抗性审查一度认为 31.A.7 "部分实现"，降低了问题严重程度判定 |

### 层2: Story 文件标记 "Done" 但实现代码缺失
| 问题 | 详情 |
|------|------|
| **现象** | `31.A.7.story.md`, `31.A.8.story.md`, `31.A.9.story.md` 全部标记 `状态: Done` |
| **事实** | 运行测试: 31.A.7 = 0/11 FAIL, 31.A.8 = 0/16 FAIL, 31.A.9 = 5/5 PASS |
| **根因** | 某次开发过程完成了 "写 Story 文件 + 写测试文件" 两个步骤，但遗漏了 "写实现代码" 的步骤。Story 被标记 Done 可能是因为 Story 文件本身已完成（内容编写完毕），而非代码实现完毕 |
| **影响** | 对抗性审查初期信任 Story 状态，未立即运行测试验证 |

### 层3: esbuild outfile 部署断裂
| 问题 | 详情 |
|------|------|
| **现象** | CLAUDE.md 声称 "esbuild.config.mjs 的 outfile 已配置为直接输出到 vault 插件目录，禁止修改回源码目录" |
| **事实** | `esbuild.config.mjs:43` 实际为 `outfile: 'main.js'`（源码目录），从未修改过 |
| **证据** | 源码 main.js: 911,523 bytes @ 12:05 vs vault main.js: 932,168 bytes @ 04:39 — 大小不同、时间不同 |
| **根因** | CLAUDE.md 中的 "已修复" 架构描述是规划/愿景，不是实际状态。`npm run build` 从未输出到 vault |
| **影响** | Obsidian 运行的始终是手动复制的旧版本 main.js |

---

## 2. 教训与防御措施

### 教训 A: 永远不信 Story 状态，只信测试结果
```
Story 标记 "Done" ≠ 代码已实现
测试文件存在 ≠ 测试通过
唯一可信: pytest/jest 实际运行结果
```

### 教训 B: Context Compaction 摘要可能包含幻觉
```
compaction 摘要中的 "earlier check found X at line Y" 必须重新验证。
上一轮 agent 的结论不能直接信任。
恢复会话后，关键事实必须重新 grep 验证。
```

### 教训 C: CLAUDE.md 声称的修复必须用代码验证
```
CLAUDE.md 说 "已修复" ≠ 代码已修改
必须 Read 实际文件确认。
本次发现 esbuild outfile 从未修改为 vault 路径。
```

### 教训 D: 对抗性审查必须包含 "运行测试" 步骤
```
之前的审查流程: grep 代码 → 分析 → 出结论
正确的审查流程: grep 代码 → 运行相关测试 → 对比结果 → 出结论
测试结果是最权威的证据，grep 只是辅助。
```

---

## 3. 修正后的 EPIC-31 阻塞项状态

| 原编号 | 发现 | 原判定 | 修正判定 | 依据 |
|--------|------|--------|---------|------|
| #1 | `getAllRelations()` 死代码 | 🔴 阻塞 | 🔴 阻塞 | vault main.js 确认存在 |
| #4 | TTLCache "跨进程持久化" 幻觉 | 🔴 阻塞 | 🔴 阻塞 | 31.A.7 测试 0/11 FAIL |
| #5 | Mock 评分缺乏降级标识 | 🟡 重要 | 🔴 升级为阻塞 | 31.A.8 测试 0/16 FAIL |
| #2 | EPIC 完成度百分比无支撑 | 🔴 阻塞 | 🟡 降级为重要 | 文档问题 |
| #3 | NFR 评估缺失 | 🔴 阻塞 | 🟡 降级为重要 | 流程问题 |
| 新 | 31.A.9 已实现但标记 Pending | — | ✅ 已解决 | 5/5 PASS |
| 新 | esbuild outfile 未指向 vault | — | 🔴 阻塞 | CLAUDE.md 幻觉，源码≠部署 |
| 新 | 31.A.7/31.A.8 Done≠实现 | — | 🔴 阻塞 | 测试 FAIL 确认 |
