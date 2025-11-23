# Epic 10 Test Suite

## 测试文件结构

```
tests/epic10/
├── README.md                              # 本文件
├── test_10.1_agent_selector.py           # Story 10.1: ReviewBoardAgentSelector多推荐测试
├── test_10.2_scheduler.py                # Story 10.2: IntelligentParallelScheduler测试
├── test_10.3_command.py                  # Story 10.3: IntelligentParallel命令接口测试
├── test_10.4_node_generation.py          # Story 10.4: AutoNodeGenerator测试
├── test_epic10_integration.py            # Epic 10 组件集成测试
├── test_epic10_performance.py            # Epic 10 性能测试
├── test_epic10_e2e.py                    # Epic 10 端到端测试
└── conftest.py                          # 测试配置和fixtures
```

## 测试覆盖率要求

- **单元测试**: 每个组件 > 90%
- **集成测试**: 组件间接口 > 95%
- **端到端测试**: 完整流程 > 90%
- **性能测试**: 所有关键路径 100%

## 运行测试

```bash
# 运行所有Epic 10测试
pytest tests/epic10/

# 运行特定Story测试
pytest tests/epic10/test_10.1_agent_selector.py

# 运行性能测试
pytest tests/epic10/test_epic10_performance.py -v

# 生成覆盖率报告
pytest tests/epic10/ --cov=canvas_utils --cov-report=html
```

## 测试数据

测试数据位于 `tests/epic10/fixtures/` 目录：
- `sample_canvas.json` - 标准Canvas文件样本
- `multiple_yellow_nodes.json` - 多个黄色节点的Canvas
- `agent_recommendations.json` - Agent推荐结果样本
- `scheduling_plan.json` - 调度计划样本