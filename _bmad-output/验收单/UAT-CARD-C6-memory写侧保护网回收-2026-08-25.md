# 验收单 · CARD-C6 找回丢失的保护网（memory 写侧隔离测试回收）

> **批次**: BATCH-2026-08-25-跨vault与收束 · 车道 3 第一卡
> **分支**: `card/l3-recap-skill`（不 push，等你验收）
> **日期**: 2026-08-25

---

## 一、你需要做什么（用户产品体验）

**没有任何要你操作的**。这张卡是纯防护网：上一批为解锁测试收集临时绕过的坏测试，已按新架构语义重写并恢复。你的日常使用零变化。

唯一一件需要你**过目**的事在「三、待确认节」——为了让新防护网真的生效，CI 测试清单加了一行（不 push 不会触发，等你验收合并后才会跑到）。

## 二、技术判据（Claude 已代跑，全部通过）

| 裁判 | 命令 | 结果 |
|---|---|---|
| conftest 无 collect_ignore | `grep -c collect_ignore backend/tests/conftest.py` | **0** ✅ |
| 全量收集恢复 | `cd backend && .venv/bin/pytest --collect-only -q` | **6636 collected**（≥6634），无 Interrupted ✅ |
| 新测试全绿 | `pytest tests/unit/test_memory_service_contextvar_leak.py -v` | **7 passed** ✅ |
| memory lane 无新增失败 | `pytest tests/unit -q -k memory` 与 HEAD 基线逐条 diff | **失败清单完全一致**（39 failed + 9 errors 全为存量债，2026-04-07 审计已知）✅ |

### 语义重写的核心（为什么不是机械翻译）

旧测试断言 `_resolve_memory_group_id` 尊重 per-request ContextVar；新实现 `_vault_scoped_group_id` 契约**相反**——读进程级 active vault（`app.config.get_current_vault_id`），**忽略** ContextVar。新测试 7 条：

1. canvas 写恒 `vault:` 前缀（完整值断言）
2. 无参写恒 `vault:` 前缀
3. **冲突 ContextVar 被忽略**（防"混合回归"——Codex 一轮 HIGH-1 补上）
4. canvas_name > subject 二级优先（memory_service 层反转 builder 层排序，测试钉死）
5. 双 vault（canonical id 层）不碰撞
6. **sanitize 有损边界钉死**（"CS 61B"/"CS-61B" 同 canonical——Codex 一轮 HIGH-2 如实入档）
7. deprecated 裸 subject 仍落 vault: 桶

docstring 显式记录：**memory 写侧 = 进程级单 active vault** 契约、`record_knowledge_entity` 直通 caller group_id 的已知例外（存量缺口，非本卡引入、非本卡修复）、与未来单进程多 vault 后端（D1-B 形态）的耦合。

### Codex 对抗审查

- 一轮（ultra）：`_bmad-output/审查/codex-review-CARD-C6.md` — 0 BLOCKER + 4 HIGH + 1 MEDIUM
- 处置：H1 补冲突 ContextVar 测试 · H2 docstring 收窄至 canonical id 层 + 边界钉死测试 · H3 docstring 收窄至"经本 resolver 路由的写"并列明例外 · H4 测试入 CI 显式清单 + test.yml/CURRENT_TASK.md 两处 stale 注释修正 · M5 D3-B 归因改 D1-B
- 二轮复核（high）：H1-H4 + M5 全部 RESOLVED，**「BLOCKER/HIGH 清零: 是」**（原文见同文件末尾附录）
- 二轮残留 3 条 LOW 已顺手处置（token reset / 计数注释去钉死 / score-history 措辞），复跑 7 passed

## 三、待确认节（等你点头，不点头不动）

1. **CI 清单 +1 行**：`.github/workflows/test.yml` 显式测试清单加入 `tests/unit/test_memory_service_contextvar_leak.py`（5→7 条快测，~0.5s）。这是 Codex HIGH-4 的处置——P0 防护网不进 CI 门等于没挂。**本分支未 push，CI 不会跑到；你早间验收合并后生效**。若你不同意加，把这行删掉即可，其余判据不受影响。
   - 备注：CURRENT_TASK.md「开工前必读③」说过"扩 CI 覆盖面前先解决全量跑不完，别直接加文件"——本次是**单文件 0.5s 快测**，与上一轮"+5 契约文件"同 pattern，非全量扩面；如你认为仍违反该纪律，撤这一行即可。

## 四、改动清单

- `backend/tests/unit/test_memory_service_contextvar_leak.py` — 语义重写（7 测试 + 契约 docstring）
- `backend/tests/conftest.py` — 删 CARD-E0 collect_ignore 块（12 行）
- `.github/workflows/test.yml` — 清单 +1 行 + stale 注释修正（待确认节 #1）
- `CURRENT_TASK.md` — 遗留行更新（该测试不再是"被 CI 隔离"状态）
