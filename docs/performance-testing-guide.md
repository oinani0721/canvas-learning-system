# Canvas学习系统 - 性能测试指南

## 概述

本文档详细介绍Canvas学习系统的性能测试框架，包括测试组件、使用方法、最佳实践和CI/CD集成。

## 📊 性能测试框架架构

### 核心组件

```
性能测试框架
├── CanvasPerformanceTester     # 核心性能测试器
├── TestCanvasGenerator          # 测试数据生成器
├── PerformanceBaselineManager   # 基准管理器
├── MemoryMonitor               # 内存监控器
├── PerformanceReportGenerator  # 报告生成器
└── PerformanceTestRunner       # 命令行运行器
```

### 数据流程

```
测试Canvas生成 → 性能测试执行 → 结果收集 → 基准比较 → 报告生成
     ↓              ↓              ↓           ↓           ↓
复杂度控制    时间/内存监控    统计分析   回归检测    HTML/JSON输出
```

## 🚀 快速开始

### 1. 基本性能测试

```bash
# 运行基准测试（建立性能基准）
python scripts/performance_test_runner.py baseline --description "初始基准"

# 运行性能比较
python scripts/performance_test_runner.py compare

# 运行压力测试
python scripts/performance_test_runner.py stress --nodes 50,100,200,500 --iterations 3
```

### 2. 内存监控

```bash
# 监控特定Canvas文件的内存使用
python scripts/performance_test_runner.py memory path/to/your/canvas.canvas
```

### 3. 查看可用基准

```bash
# 列出所有已建立的性能基准
python scripts/performance_test_runner.py list
```

## 📋 测试场景详解

### 1. 基准建立模式 (Baseline Mode)

**用途**: 建立系统的性能基准，作为后续比较的基础。

**执行流程**:
1. 生成多种规模的测试Canvas (50-1000节点)
2. 运行多次性能测试 (每种规模3次迭代)
3. 计算平均值和统计指标
4. 保存基准数据

**示例**:
```bash
python scripts/performance_test_runner.py baseline \
  --description "Canvas v2.0发布基准 - 优化后的布局算法"
```

**输出**:
- 基准ID (例如: `baseline_20250122_120000_a1b2c3d4`)
- 性能报告HTML文件
- 详细JSON数据文件

### 2. 性能比较模式 (Compare Mode)

**用途**: 检测代码变更是否导致性能回归或改进。

**执行流程**:
1. 运行当前版本的性能测试
2. 与指定基准（或最新基准）进行比较
3. 分析各项性能指标的变化
4. 生成回归检测结果和建议

**关键指标**:
- **处理时间**: 布局优化算法的执行时间
- **内存使用**: Canvas处理的内存消耗
- **布局质量**: 优化后的布局质量评分
- **重叠数量**: 节点重叠问题的数量
- **成功率**: 测试执行的成功率

**回归检测阈值**:
- 处理时间增加 > 20% → 回归
- 内存使用增加 > 30% → 回归
- 布局质量下降 > 15% → 回归
- 成功率下降 > 5% → 回归

**示例**:
```bash
# 与最新基准比较
python scripts/performance_test_runner.py compare

# 与指定基准比较
python scripts/performance_test_runner.py compare --baseline-id baseline_20250122_120000_a1b2c3d4
```

### 3. 压力测试模式 (Stress Test Mode)

**用途**: 测试系统在大规模数据处理时的性能表现。

**测试规模**:
- **小规模**: 50-100节点 (基础功能验证)
- **中规模**: 200-500节点 (性能基准建立)
- **大规模**: 1000+节点 (极限性能测试)

**示例**:
```bash
# 自定义规模测试
python scripts/performance_test_runner.py stress \
  --nodes 100,300,500,1000,2000 \
  --iterations 5

# 快速压力测试
python scripts/performance_test_runner.py stress --nodes 50,100,200
```

## 🎨 测试数据生成

### Canvas复杂度级别

#### 1. Simple (简单)
- **分布**: 网格状均匀分布
- **连接**: 线性连接
- **特点**: 无重叠，布局规整
- **用途**: 基础功能测试

#### 2. Medium (中等)
- **分布**: 3-5个聚类
- **连接**: 聚类内连接 + 少量跨聚类连接
- **特点**: 模拟真实学习场景
- **用途**: 性能基准测试

#### 3. Complex (复杂)
- **分布**: 多层级结构
- **连接**: 复杂网络连接
- **特点**: 多种布局问题
- **用途**: 算法压力测试

#### 4. Chaotic (混乱)
- **分布**: 随机集中分布
- **连接**: 大量随机连接
- **特点**: 故意造成重叠和混乱
- **用途**: 极限场景测试

### 节点颜色分布

性能测试使用真实使用场景的颜色分布：
- **红色 (不理解)**: 15%
- **绿色 (已掌握)**: 35%
- **紫色 (部分理解)**: 25%
- **蓝色 (AI解释)**: 15%
- **黄色 (个人理解)**: 10%

## 📈 性能报告解读

### HTML报告结构

1. **概览区域**
   - 总测试数和成功率
   - 平均处理时间和评分
   - 内存使用统计
   - 最大节点数

2. **回归分析**
   - 回归检测结果
   - 性能变化趋势
   - 优化建议

3. **详细结果**
   - 每个测试的具体数据
   - 处理时间、内存使用、质量评分
   - 成功/失败状态

4. **性能统计**
   - 处理时间的最小值/最大值/平均值/P95
   - 内存使用统计
   - 测试覆盖率

5. **测试环境**
   - Python版本、操作系统、硬件配置

### 性能评分系统

**总体评分 (0-100分)**:
- 80-100分: 🟢 优秀 (无回归，可能有改进)
- 60-79分: 🟡 良好 (轻微回归，需要关注)
- 40-59分: 🟠 一般 (明显回归，需要优化)
- 0-39分: 🔴 差 (严重回归，需要立即处理)

**评分维度**:
- **处理时间** (40%权重): 响应速度变化
- **内存使用** (30%权重): 内存效率变化
- **布局质量** (30%权重): 算法质量变化

## 🔧 集成到开发流程

### 1. 本地开发

```bash
# 功能开发完成后，运行性能测试
python scripts/performance_test_runner.py compare

# 如果有重大性能变更，更新基准
python scripts/performance_test_runner.py baseline \
  --description "优化布局算法，减少重叠检测时间"
```

### 2. 代码审查

在PR中包含性能测试结果：
- 性能改进的说明
- 回归检测结果
- 如果有回归，解释原因和缓解措施

### 3. CI/CD集成

GitHub Actions自动运行：
- **PR触发**: 运行压力测试，检测回归
- **Main分支推送**: 运行完整比较测试
- **每日定时**: 运行性能回归监控

### 4. 发布流程

发布前建立新的基准：
```bash
python scripts/performance_test_runner.py baseline \
  --description "Canvas v2.1.0发布基准"
```

## 📊 性能目标和基准

### 响应时间目标

| Canvas规模 | 目标时间 | 可接受范围 | 基准值 |
|------------|----------|------------|--------|
| 50节点     | < 500ms  | < 1s       | 180ms  |
| 100节点    | < 1s     | < 2s       | 370ms  |
| 200节点    | < 3s     | < 5s       | 1.2s   |
| 500节点    | < 8s     | < 15s      | 4.5s   |
| 1000节点   | < 15s    | < 30s      | 12s    |

### 内存使用目标

| Canvas规模 | 目标内存 | 可接受范围 | 基准值 |
|------------|----------|------------|--------|
| 50节点     | < 30MB   | < 50MB     | 25MB   |
| 100节点    | < 50MB   | < 100MB    | 45MB   |
| 200节点    | < 100MB  | < 200MB    | 85MB   |
| 500节点    | < 300MB  | < 500MB    | 280MB  |
| 1000节点   | < 600MB  | < 1GB      | 550MB  |

### 布局质量目标

- **质量评分**: ≥ 8.0/10
- **重叠数量**: ≤ 2 (小规模), ≤ 5 (大规模)
- **优化成功率**: ≥ 99%

## 🛠 故障排除

### 常见问题

#### 1. 测试失败
```bash
# 检查Canvas文件是否存在
ls tests/fixtures/performance/

# 检查依赖是否安装
pip install -r requirements.txt
pip install pytest pytest-benchmark psutil jinja2
```

#### 2. 内存不足
```bash
# 减少测试规模
python scripts/performance_test_runner.py stress --nodes 50,100,200

# 减少迭代次数
python scripts/performance_test_runner.py stress --iterations 1
```

#### 3. 基准数据损坏
```bash
# 重新建立基准
rm tests/performance_baseline.json
python scripts/performance_test_runner.py baseline --description "重新建立基准"
```

#### 4. 报告生成失败
```bash
# 检查Jinja2是否安装
pip install jinja2

# 检查输出目录权限
mkdir -p tests/reports
chmod 755 tests/reports
```

### 性能调试

#### 1. 详细日志
```bash
# 启用详细日志
export PYTHONPATH=$PYTHONPATH:.
python -v scripts/performance_test_runner.py stress --nodes 100
```

#### 2. 内存分析
```bash
# 运行内存监控
python scripts/performance_test_runner.py memory tests/fixtures/performance/test_canvas_100_medium.canvas
```

#### 3. 单独测试
```python
# 在Python中单独测试
from tests.test_canvas_performance import CanvasPerformanceTester

tester = CanvasPerformanceTester()
canvas_path = tester.generate_test_canvas(100, "medium")
result = tester.run_performance_test(canvas_path)
print(f"处理时间: {result.processing_time_ms}ms")
print(f"内存使用: {result.memory_usage_mb}MB")
```

## 📚 API参考

### CanvasPerformanceTester

```python
class CanvasPerformanceTester:
    def __init__(self, test_config: Dict = None):
        """初始化性能测试器"""

    def generate_test_canvas(self, node_count: int, complexity: str = "medium") -> str:
        """生成测试Canvas"""

    def run_performance_test(self, canvas_path: str, test_config: Dict = None) -> PerformanceTestResult:
        """运行单个性能测试"""

    def run_stress_test(self, node_counts: List[int], iterations: int = 3) -> StressTestResult:
        """运行压力测试"""

    def monitor_memory_usage(self, canvas_path: str) -> Dict:
        """监控内存使用"""
```

### PerformanceBaselineManager

```python
class PerformanceBaselineManager:
    def __init__(self, baseline_file: str = "tests/performance_baseline.json"):
        """初始化基准管理器"""

    def establish_baseline(self, test_results: List[PerformanceTestResult],
                          test_environment: TestEnvironment, description: str = "") -> str:
        """建立性能基准"""

    def compare_with_baseline(self, current_results: List[PerformanceTestResult],
                             baseline_id: Optional[str] = None) -> RegressionTestResult:
        """与基准比较"""
```

### PerformanceReportGenerator

```python
class PerformanceReportGenerator:
    def generate_performance_report(self, test_results: List[PerformanceTestResult],
                                  test_environment: TestEnvironment,
                                  regression_result: Optional[RegressionTestResult] = None,
                                  output_path: Optional[str] = None) -> str:
        """生成性能报告"""
```

## 🔄 最佳实践

### 1. 测试策略
- **定期基准**: 每次发布前建立新基准
- **持续监控**: CI/CD中自动检测回归
- **分类测试**: 根据功能选择合适的测试规模

### 2. 结果分析
- **关注趋势**: 不仅看单次结果，更要关注变化趋势
- **环境一致**: 确保测试环境的一致性
- **数据备份**: 定期备份重要的基准数据

### 3. 性能优化
- **先测后改**: 在优化前后都进行性能测试
- **逐步优化**: 一次只优化一个方面
- **验证效果**: 优化后要验证是否达到预期效果

## 📞 支持

如果在使用性能测试框架时遇到问题：

1. 查看本文档的故障排除部分
2. 检查GitHub Issues中的相关问题
3. 在项目仓库中创建新的Issue
4. 联系开发团队获取技术支持

---

**文档版本**: 1.0
**最后更新**: 2025-10-22
**维护者**: Canvas学习系统开发团队