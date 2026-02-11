# EPIC-32 对抗性审核报告 (Adversarial Audit)

**日期**: 2026-02-10
**审核范围**: EPIC-32 Ebbinghaus Review System Enhancement (Stories 32.1-32.8)
**审核方法**: 代码现实检查 + DI完整性 + 死代码检测 + 测试实际运行

---

## 1. 代码现实检查 (Code Reality Check)

| EPIC声称 | 代码位置 | 状态 |
|----------|----------|------|
| FSRS-4.5 算法集成 | `review_service.py:666-763` | ✅ 真实 — py-fsrs 库 |
| Score→Rating 映射 | `review_service.py:805-933` | ✅ 存在 — 0-100→1-4 |
| FSRS Card 持久化 | `review_service.py` JSON atomic write | ✅ 存在 — async lock + tempfile |
| GET /fsrs-state/{concept_id} | `review.py:1318-1391` | ✅ 存在 |
| FSRSManager 类 | `fsrs_manager.py` (397行) | ✅ 真实 — 非mock |
| USE_FSRS 配置开关 | `config.py:452` | ✅ 存在 — rollback switch |
| Ebbinghaus 回退 | `review_service.py:699,745-762` | ✅ WARNING 级日志 |

**结论**: 0 个幻觉, 所有 EPIC 声称的功能在代码中均存在。

## 2. DI完整性检查

| Service | 构造参数 | dependencies.py 传参 | 状态 |
|---------|---------|---------------------|------|
| ReviewService | fsrs_manager | `create_fsrs_manager(settings)` | ✅ 传入 |
| ReviewService | canvas_service | `get_canvas_service()` | ✅ 传入 |
| ReviewService | task_manager | `BackgroundTaskManager()` | ✅ 传入 |
| create_fsrs_manager | settings | `get_settings()` | ✅ 传入 |

**结论**: 0 个 DI 断裂。

## 3. 死代码/静态模板检测

- `grep -rn "TODO\|FIXME\|HACK\|STUB" review_service.py` → **0 匹配**
- 降级路径均有 WARNING 级日志（非静默降级）
- `_provide_hint()` 类静态模板问题在 EPIC-32 中不存在

**结论**: 0 个死代码/静态模板。

## 4. 测试实际运行结果

### 修复前 (P0!)
```
149 passed, 3 FAILED
FAILED test_fsrs_state_query.py::TestFSRSStateQueryEndpoint::test_endpoint_returns_fsrs_state_when_card_exists
FAILED test_fsrs_state_query.py::TestFSRSStateQueryEndpoint::test_endpoint_handles_special_characters_in_concept_id
FAILED test_fsrs_state_query.py::TestFSRSStateQueryEndpoint::test_endpoint_handles_null_retrievability_and_due
```

**根因**: 测试 patch 目标错误 — `app.dependencies.get_review_service` vs 实际使用的 `app.api.v1.endpoints.review._get_review_service_singleton`

### 修复后
```
152 passed, 0 FAILED (含 test_fsrs_state_query.py 12 + test_fsrs_state_api.py 12 + test_review_service_fsrs.py 35 + test_story_38_3 29)
```

**修复内容** (`test_fsrs_state_query.py`):
1. Patch 目标: `app.dependencies.get_review_service` → `app.api.v1.endpoints.review._get_review_service_singleton`
2. Mock 类型: `return_value=mock_service` → `new_callable=AsyncMock, return_value=mock_service`
3. 添加 `override_settings` autouse fixture + `TestClient` 使用 context manager
4. 添加 `_test_settings_override()` 函数提供测试配置

## 5. BMad 报告交叉验证

| BMad 声称 | 实际情况 | 差异 |
|----------|---------|------|
| ~347 测试, 100% 通过 | 149 通过, 3 失败 (修复前) | 🔴 BMad 报告不准确 |
| 测试质量评分 41/100 (F) | 测试确实有质量问题 | ✅ BMad 评分方向正确 |
| 覆盖率 P0:100%, P1:89% | 逻辑覆盖基本完整 | ✅ 基本一致 |

## 6. 残留质量风险 (P1/P2)

| 风险 | 位置 | 严重度 | 建议 |
|------|------|--------|------|
| `datetime.now()` 未 mock | `test_fsrs_manager.py:124,234` | P1 — 跨日边界 flaky | 使用 freezegun |
| yield 无 try/finally | `test_fsrs_state_api.py:40,47,64` | P1 — 单例泄漏 | 添加 cleanup |
| 无 E2E 测试 | 整个 EPIC-32 | P2 — 回归保护不足 | 后续补充 |
| TTL cache 无过期测试 | ReviewService.get_fsrs_state | P2 — cache 行为未验证 | 后续补充 |

## 7. 最终判定

**🟢 通过** — 代码实现完整、DI 正确、无幻觉、无死代码。测试失败已修复。
