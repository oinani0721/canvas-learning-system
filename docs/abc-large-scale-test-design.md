# A/B/C 大基数对比测试方案

> 基于 workflow-research-full-report.md §9 + A的升级.md + 实测对比经验设计
> 目标：在 Mac Agent Teams 上运行 20 任务 × 3 工作流 × 3 重复 = 180 次执行

---

## 一、三个参赛选手（精确定义）

### 选手 A：GSD → TDAD → Workflow A → pytest-gremlins（四层防护）

```
Layer 1: GSD plan-phase → PLAN.md（≤3 任务/计划）
Layer 2: tdad analyze → test_map.txt 注入 test-writer 上下文
Layer 3: Agent Teams 物理隔离
  - test-writer Teammate（只看 contracts/ + test_map.txt，不看 src/）
  - implementer Teammate（只看测试文件 + src/）
  - SendMessage 传递测试文件路径
Layer 4: Stop hook → pytest-gremlins 变异测试
  + TaskCompleted hook → facade 静态检测（AST）
```

### 选手 B：BMAD V6 Dev Agent

```
/bmad-bmm-dev-story → Dev Agent（Amelia）单 context 实现
→ 实现完成后 Quinn QA 生成测试
→ git commit
```

### 选手 C：Superpowers TDD

```
superpowers:writing-plans → 任务分解
→ superpowers:test-driven-development（严格 Red/Green）
→ superpowers:requesting-code-review（两阶段审查）
→ git commit
```

---

## 二、任务矩阵（20 个任务，6 层复杂度）

### L1: 纯函数（3 个）— 基线，所有工作流都应该成功

| ID | 任务 | target_files | 验收 |
|----|------|-------------|------|
| T01 | scoring_utils 新增 `score_to_grade()`（A/B/C/D/F 映射） | scoring_utils.py | `pytest -k grade` |
| T02 | sanitize_subject_name 支持日文片假名 | subject_config.py | `pytest -k sanitize` |
| T03 | 新增 `truncate_to_token_limit()` 函数 | 新文件 text_utils.py | `pytest -k truncate` |

### L2: 单层 IO + Facade 诱导（3 个）

| ID | 任务 | target_files | 陷阱 |
|----|------|-------------|------|
| T04 | 修复 FSRS 参数序列化（float 精度丢失） | mastery_store.py | 必须断言精确浮点值，不能 `isinstance` |
| T05 | episode_worker 死信重试逻辑修复 | episode_worker.py | 必须测试真实 asyncio 行为 |
| T06 | prompt 模板加载回退机制 | question_generator.py | 文件不存在时的降级 |

### L3: 单数据库（3 个）— Neo4j 测试退化点

| ID | 任务 | target_files | 陷阱 |
|----|------|-------------|------|
| T07 | 修复 group_id 查询的 Cypher 注入风险 | memory_service.py | 必须用真实 Neo4j 或参数化查询 |
| T08 | 实现 episode 批量写入（batch_add） | episode_worker.py | 并发写入竞态条件 |
| T09 | Neo4j fulltext 索引中文分词优化 | memory_service.py | 中文搜索返回结果验证 |

### L4: 跨层（4 个）— Context contamination 检测

| ID | 任务 | target_files | 陷阱 |
|----|------|-------------|------|
| T10 | Profile Tip 点击跳转接线 | App.tsx + LearningProfile.tsx | 前后端联动 |
| T11 | search_memories 三层 fallthrough 修复 | memory_service.py + rag_service.py | 跨服务调用链 |
| T12 | 考察中 /explain 命令注入 Layer4 规则 | layer4_rules.md + question_generator.py + SkillSelector.tsx | 跨前后端+prompt |
| T13 | Dashboard Exam History 接入真实数据 | ExamCard.tsx + exam_service.py | 前端组件+后端 API |

### L5: 前端（3 个）— IPC mock 质量检测

| ID | 任务 | target_files | 陷阱 |
|----|------|-------------|------|
| T14 | 全局主题从硬编码改为 CSS 变量 | tailwind.config.ts + index.css + 各组件 | 169 处硬编码替换 |
| T15 | NodeContextMenu 添加"创建疑问节点"选项 | NodeContextMenu.tsx + canvas-store.ts | 状态管理 |
| T16 | Chat 消息 Markdown 渲染支持代码高亮 | markdown-renderers.tsx | 第三方库集成 |

### L6: 全栈（4 个）— 综合失效检测

| ID | 任务 | target_files | 陷阱 |
|----|------|-------------|------|
| T17 | 实现 record_learning_memory 全链路（MCP → Neo4j → Graphiti） | memory_tools.py + memory_service.py + episode_worker.py | 三层管道打通 |
| T18 | 实现 Edge 对话触发双重策略（EI+SE） | 新文件 edge_service.py + 新组件 | 全新功能 |
| T19 | 实现 Area9 2x2 置信度矩阵采集 | calibration_tracker.py + ExamCanvas.tsx | 数据采集+前端展示 |
| T20 | 评分 Bug 端到端修复（后端归一化+前端展示+FSRS 接入） | agent_service.py + mastery_engine.py + LearningProfile.tsx | 全栈回归 |

---

## 三、3 类必须包含的陷阱任务

已嵌入上方矩阵：

| 陷阱类型 | 对应任务 | 检测目标 |
|---------|---------|---------|
| **Facade 诱导** | T04, T05, T06 | spec 只描述输入输出，不指明函数 → 看工作流是否写 facade |
| **Unsatisfiable spec** | 额外：T21 "返回同时按相关度和时间排序的结果" | test-writer 是否幻觉出不可能的 API |
| **Context contamination** | T11, T12 | 仓库中旧 API 约定是否污染新代码 |

---

## 四、评测指标（自动化优先）

| 指标 | 类型 | 工具 | 权重 | 自动化？ |
|------|------|------|------|---------|
| **Mutation kill rate** | 连续 0-100% | pytest-gremlins | **40%**（主指标） | ✅ |
| **功能正确性** | 二值 pass/fail | pytest | **25%** | ✅ |
| **Facade 检测** | 二值 有/无 | detect_facade.py（AST） | **20%** | ✅ |
| **Implementer 重试次数** | 计数 | Agent 日志解析 | **10%** | ✅ |
| **Token 消耗** | 连续 | API 日志 | **5%** | ✅ |

### 综合评分公式

```
score = mutation_kill_rate × 0.4
      + (pass ? 25 : 0) × 0.01
      + (no_facade ? 20 : 0) × 0.01
      + max(0, (1 - retries/5)) × 10 × 0.01
      + max(0, (1 - tokens/200000)) × 5 × 0.01
```

---

## 五、实验控制（公平性保障）

### 5.1 相同起点
```bash
# 每个任务从相同 git commit 开始
BASE_SHA=$(git rev-parse HEAD)

for task in T01 T02 ... T20; do
  for wf in A B C; do
    for rep in 1 2 3; do
      git worktree add "/tmp/exp/${task}_${wf}_${rep}" "$BASE_SHA"
    done
  done
done
```

### 5.2 执行顺序随机化
```
# Latin square 设计：避免顺序效应
# 第 1 轮：A-B-C
# 第 2 轮：B-C-A
# 第 3 轮：C-A-B
```

### 5.3 环境一致性
- 所有工作流使用 **同一 Mac 机器、同一 Claude Opus 4.6 模型**
- temperature=0（减少随机性，但不完全消除）
- Docker services（Neo4j 7691、Ollama）在实验前启动，不在实验中重启
- 每个 worktree 独立，互不影响

### 5.4 超时控制
- 每个任务最大 **15 分钟**
- 超时 = 自动判定失败 + retry=∞

---

## 六、统计分析方法

### 6.1 主检验
- **Mutation kill rate**（连续变量）：Friedman 检验（非参数，3 组配对）
- **Facade 检出率**（二值变量）：Cochran's Q 检验

### 6.2 事后检验
- Friedman 显著 → Nemenyi 事后检验（A vs B, A vs C, B vs C）
- Cochran's Q 显著 → McNemar 配对 + Bonferroni 校正（α/3 = 0.0167）

### 6.3 样本量功效分析
| 任务数 | 重复次数 | 总对比数 | 大效应量功效 |
|--------|---------|---------|------------|
| 10 | 3 | 30 | ~60%（不够） |
| **20** | **3** | **60** | **>95%（推荐）** |
| 20 | 5 | 100 | >99%（过度） |

**推荐：20 任务 × 3 重复 = 60 对配对，大效应量 >95% 功效**

---

## 七、自动化执行脚本骨架

```bash
#!/bin/bash
# experiment-runner.sh — Mac 上运行大基数对比测试

BASE_SHA=$(git rev-parse HEAD)
RESULTS_DIR="./experiment-results"
mkdir -p "$RESULTS_DIR"

TASKS=(T01 T02 T03 T04 T05 T06 T07 T08 T09 T10 T11 T12 T13 T14 T15 T16 T17 T18 T19 T20)
WORKFLOWS=(A B C)
REPS=(1 2 3)

for task in "${TASKS[@]}"; do
  # 读取任务描述
  TASK_DESC=$(jq -r ".tasks[] | select(.id == \"$task\") | .description" experiment-tasks.json)
  
  for rep in "${REPS[@]}"; do
    # Latin square 随机化
    case $rep in
      1) ORDER=(A B C) ;;
      2) ORDER=(B C A) ;;
      3) ORDER=(C A B) ;;
    esac
    
    for wf in "${ORDER[@]}"; do
      WORK_DIR="/tmp/exp/${task}_${wf}_${rep}"
      LOG_FILE="$RESULTS_DIR/${task}_${wf}_${rep}.json"
      
      echo "=== $task / Workflow $wf / Rep $rep ==="
      
      # 创建独立 worktree
      git worktree add "$WORK_DIR" "$BASE_SHA" 2>/dev/null
      
      START_TIME=$(date +%s)
      
      # 执行对应工作流（超时 15 分钟）
      timeout 900 bash -c "
        cd $WORK_DIR
        case $wf in
          A) claude -p 'Execute task with Workflow A TDD isolation: $TASK_DESC' ;;
          B) claude -p 'Execute task with BMAD dev-story approach: $TASK_DESC' ;;
          C) claude -p 'Execute task with Superpowers TDD: $TASK_DESC' ;;
        esac
      "
      EXIT_CODE=$?
      
      END_TIME=$(date +%s)
      DURATION=$((END_TIME - START_TIME))
      
      # 收集指标
      cd "$WORK_DIR/backend"
      
      # 1. pytest 通过？
      python -m pytest tests/ -q --tb=no 2>/dev/null
      PYTEST_PASS=$?
      
      # 2. mutation kill rate
      CHANGED=$(git diff --name-only HEAD -- '*.py' | grep -v test_ | tr '\n' ',')
      if [ -n "$CHANGED" ]; then
        python -m pytest --gremlins --gremlin-paths="$CHANGED" --gremlin-json 2>/dev/null
        MUTATION_SCORE=$(cat .gremlins-report.json | jq '.kill_rate // 0')
      else
        MUTATION_SCORE="N/A"
      fi
      
      # 3. facade 检测
      python scripts/detect_facade.py 2>/dev/null
      FACADE_COUNT=$?
      
      # 4. 写入结果
      cat > "$LOG_FILE" <<EOF
{
  "task": "$task",
  "workflow": "$wf",
  "rep": $rep,
  "duration_sec": $DURATION,
  "pytest_pass": $( [ $PYTEST_PASS -eq 0 ] && echo "true" || echo "false" ),
  "mutation_score": $MUTATION_SCORE,
  "facade_detected": $( [ $FACADE_COUNT -eq 0 ] && echo "false" || echo "true" ),
  "timeout": $( [ $EXIT_CODE -eq 124 ] && echo "true" || echo "false" )
}
EOF
      
      cd -
      
      # 清理 worktree
      git worktree remove "$WORK_DIR" --force 2>/dev/null
    done
  done
done

echo "=== 实验完成 ==="
echo "结果在 $RESULTS_DIR/"
```

---

## 八、结果分析脚本骨架

```python
#!/usr/bin/env python3
# analyze-experiment.py

import json, glob, numpy as np
from scipy.stats import friedmanchisquare, cochrans_q

results = []
for f in glob.glob("experiment-results/*.json"):
    results.append(json.load(open(f)))

# 按工作流分组
A = [r for r in results if r["workflow"] == "A"]
B = [r for r in results if r["workflow"] == "B"]
C = [r for r in results if r["workflow"] == "C"]

# Friedman 检验（mutation kill rate）
scores_A = [r["mutation_score"] for r in A if r["mutation_score"] != "N/A"]
scores_B = [r["mutation_score"] for r in B if r["mutation_score"] != "N/A"]
scores_C = [r["mutation_score"] for r in C if r["mutation_score"] != "N/A"]

stat, p = friedmanchisquare(scores_A, scores_B, scores_C)
print(f"Friedman: χ²={stat:.2f}, p={p:.4f}")
if p < 0.05:
    print("→ 三组有显著差异，执行 Nemenyi 事后检验")

# Facade 率
facade_A = sum(1 for r in A if r["facade_detected"]) / len(A) * 100
facade_B = sum(1 for r in B if r["facade_detected"]) / len(B) * 100
facade_C = sum(1 for r in C if r["facade_detected"]) / len(C) * 100
print(f"Facade 率: A={facade_A:.0f}% B={facade_B:.0f}% C={facade_C:.0f}%")
```

---

## 九、预估资源消耗

| 项目 | 数值 |
|------|------|
| 总执行次数 | 20 × 3 × 3 = **180 次** |
| 每次最大 15 分钟 | 理论最大 **45 小时** |
| 实际（含快速任务） | 预计 **15-25 小时** |
| API token（按 200K/次） | 约 **36M tokens** |
| 估算 API 成本 | Opus $15/M input → **约 $270-540** |
| Mac 运行时间 | **2-3 天连续运行**（或 5-7 天分段） |

---

## 十、阶段性执行建议

不要一次跑 180 次。分三期：

### 第一期：5 任务 × 3 工作流 × 1 重复 = 15 次（3-5 小时）
选 T01, T04, T07, T10, T17（每层 1 个）
**目的**：验证实验基础设施能跑通，初步观察差异方向

### 第二期：10 任务 × 3 工作流 × 2 重复 = 60 次（8-12 小时）
加入剩余任务 + 陷阱任务
**目的**：初步统计分析，如果已经显著差异可以停止

### 第三期：20 任务 × 3 工作流 × 3 重复 = 180 次（15-25 小时）
完整实验
**目的**：统计显著结论 + 发表级证据
