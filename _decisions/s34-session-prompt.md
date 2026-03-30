# S35 Session 提示词 — Phase 3 全量推进

## 上下文

S34 完成了 Phase 2 全部 + Phase 3 Step 1 审计确认。现在进入 Phase 3 剩余步骤。

### S34 已完成

1. **Phase 2 全部完成（4 commits）**：
   - `5d2b95b` G-FAKE-001 假命名批量重命名（17标识符+3文件+re-export stub）
   - `1cb8315` 3处 LearningMemoryClient DI 强制注入
   - `ee3daa8` G-PIPE-001 审计纠正（WeightCalculator 已接线）
   - `1f19e00` G-PIPE-006 Verification 评分回写 memory 闭合反馈环

2. **Phase 3 审计**：
   - Step 1（USE_MOCK_VERIFICATION）：✅ 确认已完成，Gemini API 真实评分已是默认路径

3. **known-gotchas**：25条中14已修复，11待修

4. **32 real Neo4j 集成测试**：全 session 保持 PASSED

### S35 需要做的

**Phase 3 Step 2：except Exception → 精确异常处理（全量 558 处）**

S34 审计发现 558 处 `except Exception` 跨 107 个文件。大部分已有 logger.warning 日志但异常类型宽泛。

全量修复策略（用并行 Agent 批量处理）：
1. 按文件分组，每个 Agent 负责 10-20 个文件
2. 对每处 `except Exception`：分析该位置能抛什么异常，替换为精确类型
3. 常见替换模式：
   - Neo4j 操作 → `except (ServiceUnavailable, SessionExpired, TransientError)`
   - JSON 解析 → `except (json.JSONDecodeError, KeyError, TypeError)`
   - 文件 IO → `except (FileNotFoundError, PermissionError, OSError)`
   - API 调用 → `except (httpx.HTTPError, asyncio.TimeoutError, ConnectionError)`
   - 类型转换 → `except (ValueError, TypeError, AttributeError)`
4. 保留 `except Exception` 的合理场景：顶层 API 端点兜底、事件循环保护
5. 每批完成后跑 32 real tests 验证

文件优先级：
- P0: services/ 目录（312处，核心业务逻辑）
- P1: api/v1/endpoints/（~80处，API 层）
- P2: clients/ + middleware/（~80处）
- P3: mcp/ + core/（~80处）

**Phase 3 Step 3：Regex Agent 路由 → 语义路由**

当前 Agent 路由使用正则匹配，无法理解语义。

推荐策略：
1. 审计当前路由实现：`grep -r "regex\|re\.match\|re\.search\|route.*agent\|AgentType" backend/app/services/agent_service.py`
2. 评估当前路由的准确率
3. 如果确实需要语义路由，考虑 Gemini Flash 做 intent classification

**Phase 3 Step 4：FSRS 手动覆盖 → 算法原生适应**

推荐策略：
1. 审计 `mastery_engine.py` 和 `weight_calculator.py` 的 FSRS 使用情况
2. 检查 `fsrs` 库是否已安装并被正确调用
3. 评估手动覆盖 vs 算法原生适应的优先级

## 前置条件

- Docker Desktop 运行中
- `docker compose --profile test up -d neo4j-test`

## 关键文件

- 异常处理热点: `backend/app/services/`（312处 except Exception）
- Agent 路由: `backend/app/services/agent_service.py`
- FSRS 引擎: `backend/app/services/mastery_engine.py`
- 权重计算: `backend/app/services/weight_calculator.py`
- known-gotchas: `docs/known-gotchas.md`（25条，14已修复）
- 决策索引: `_decisions/decision-log.md`
- Real tests: `backend/tests/integration/test_*_real.py`（32个安全网）
