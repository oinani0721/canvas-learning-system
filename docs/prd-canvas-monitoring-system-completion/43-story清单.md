# 4.3 Story清单

## Story 1.1：连接Canvas内容解析逻辑

**作为**：监控系统开发者
**我想要**：连接现有的`_detect_canvas_changes()`方法到防抖管理器
**以便**：在文件变更后自动触发Canvas内容解析

**技术描述**：
- 修改`DebounceManager._flush_changes()`
- 实现`CanvasMonitorEngine._process_canvas_changes()`
- 调用现有的`_detect_canvas_changes()`
- 触发所有注册的`change_callbacks`

**Acceptance Criteria**：
1. ✅ Canvas修改后500ms触发内容解析
2. ✅ 成功检测节点级别变更
3. ✅ 所有回调被调用
4. ✅ 异常不导致崩溃
5. ✅ 解析耗时记录到性能统计
6. ✅ 单元测试覆盖 > 95%

**Integration Verification**：
- IV1: 现有测试继续通过
- IV2: 防抖机制未受影响
- IV3: CPU < 5%, 内存增长 < 10MB

**工作量估算**：3-5小时

---

## Story 1.2：实现热数据JSON存储

**作为**：监控系统用户
**我想要**：系统实时记录学习活动到JSON文件
**以便**：监控进程崩溃时不丢失今天的数据

**技术描述**：
- 创建`data_stores.py`模块
- 实现`HotDataStore`类
- 实现回调函数`hot_data_callback()`
- 注册到监控引擎

**Acceptance Criteria**：
1. ✅ 每天自动创建新session文件
2. ✅ 事件立即追加到当日文件
3. ✅ JSON写入 < 20ms
4. ✅ 符合预定义Schema
5. ✅ 写入失败自动重试（最多3次）
6. ✅ 支持查询当日统计

**Integration Verification**：
- IV1: 不影响监控实时性（< 600ms）
- IV2: 文件锁不冲突（并发测试）
- IV3: Obsidian编辑无卡顿

**工作量估算**：2-3小时

---

## Story 1.3：实现学习分析回调

**作为**：学习者
**我想要**：系统自动识别学习进步（红→紫→绿）
**以便**：量化地看到理解提升

**技术描述**：
- 创建`learning_analyzer.py`模块
- 实现`LearningAnalyzer`类
- 实现颜色流转分析
- 计算学习指标

**Acceptance Criteria**：
1. ✅ 正确识别4种颜色流转类型
2. ✅ 每种流转类型写入不同事件
3. ✅ 实时更新学习统计
4. ✅ 分析耗时 < 50ms
5. ✅ 支持批量分析
6. ✅ 边缘情况处理

**Integration Verification**：
- IV1: 与现有颜色系统兼容
- IV2: 不干扰Agent操作
- IV3: 多Canvas并发分析准确

**工作量估算**：4-6小时

---

## Story 1.4：实现异步处理架构

**作为**：系统架构师
**我想要**：将Canvas解析放入异步处理管道
**以便**：保证监控主线程不被阻塞

**技术描述**：
- 创建`async_processor.py`模块
- 实现`AsyncCanvasProcessor`类
- 修改`DebounceManager`连接异步队列
- 重构`_process_canvas_changes()`在worker线程执行

**Acceptance Criteria**：
1. ✅ 防抖后立即返回（不等待处理）
2. ✅ 4个worker线程并发处理
3. ✅ 同一Canvas的变更按顺序处理
4. ✅ 回调超时控制（2秒）
5. ✅ 队列容量限制（1000）
6. ✅ 优雅关闭（等待最多30秒）

**Performance**：
- 队列延迟 < 10ms
- Canvas解析 < 150ms
- 总响应 < 800ms

**Integration Verification**：
- IV1: 主线程CPU < 2%
- IV2: 现有测试100%通过
- IV3: 异常不影响监控稳定性

**工作量估算**：6-8小时

---

## Story 1.5：实现冷数据SQLite存储

**作为**：数据分析师
**我想要**：系统将学习历史存储到SQLite
**以便**：查询和分析长期学习趋势

**技术描述**：
- 在`data_stores.py`实现`ColdDataStore`类
- 创建SQLite schema（4个表）
- 实现批量数据导入
- 实现查询接口

**Acceptance Criteria**：
1. ✅ 首次启动自动创建数据库
2. ✅ 支持4种表的插入和查询
3. ✅ 批量插入：1000条 < 500ms
4. ✅ 查询性能：< 100ms
5. ✅ 数据完整性约束
6. ✅ 数据库路径可配置
7. ✅ Schema版本升级机制

**Integration Verification**：
- IV1: 不影响热数据写入（< 20ms）
- IV2: 数据一致性（JSON vs SQLite）
- IV3: 并发访问安全

**工作量估算**：4-5小时

---

## Story 1.6：实现数据同步调度器

**作为**：系统运维人员
**我想要**：系统自动同步热数据到冷数据
**以便**：节省磁盘空间并提供长期查询

**技术描述**：
- 在`data_stores.py`实现`DataSyncScheduler`类
- 实现定时任务（每小时）
- 实现数据迁移逻辑（JSON → SQLite → 删除）
- 实现数据归档（90天后压缩）

**Acceptance Criteria**：
1. ✅ 每小时自动触发同步
2. ✅ 同步流程完整（读取→插入→验证→删除）
3. ✅ 错误处理（损坏/失败/崩溃）
4. ✅ 数据归档（90天后压缩）
5. ✅ 监控和可观测性

**Integration Verification**：
- IV1: 同步期间不影响监控
- IV2: 数据完整性跨存储层
- IV3: 磁盘空间管理

**工作量估算**：3-4小时

---

## Story 1.7：实现学习报告生成

**作为**：学习者
**我想要**：系统生成每日/每周学习报告
**以便**：回顾进度并发现需要复习的知识点

**技术描述**：
- 创建`report_generator.py`模块
- 实现`LearningReportGenerator`类
- 支持3种报告类型（每日/每周/Canvas分析）
- Markdown格式
- 集成到`/learning-report`命令

**Acceptance Criteria**：
1. ✅ 每日报告包含6个部分
2. ✅ 每周报告包含趋势图和热力图
3. ✅ Canvas分析报告包含时间线和效率分析
4. ✅ 生成时间 < 2秒（每日）、< 5秒（每周）
5. ✅ 报告保存到`.learning_reports/`
6. ✅ 支持日期范围参数

**Integration Verification**：
- IV1: 与斜杠命令兼容
- IV2: 报告数据准确性
- IV3: 大数据量性能（30天 < 5秒）

**工作量估算**：4-6小时

---

## Story 1.8：系统集成与性能优化

**作为**：产品负责人
**我想要**：监控系统完全集成并达到性能目标
**以便**：交付生产就绪的完整产品

**技术描述**：
- 集成测试套件（端到端）
- 性能基准测试和优化
- 与12个AI Agent集成验证
- 与艾宾浩斯复习系统集成
- 生产环境配置和文档

**Acceptance Criteria**：
1. ✅ 端到端集成测试通过
2. ✅ 性能目标达成（P50 < 800ms, P95 < 1200ms）
3. ✅ 12个AI Agent集成验证
4. ✅ 艾宾浩斯复习集成
5. ✅ 生产就绪检查（启动脚本、健康检查、日志）
6. ✅ 文档完成（用户手册、故障排除、API文档）

**Integration Verification**：
- IV1: 现有系统零破坏（420测试通过）
- IV2: 真实用户场景测试（UAT）
- IV3: 长期稳定性（72小时soak测试）

**工作量估算**：6-8小时

---

## Story 1.9：监控仪表板与运维工具

**作为**：系统管理员
**我想要**：实时查看监控系统状态
**以便**：快速诊断问题和优化配置

**技术描述**：
- 实现HTTP服务器（端口5678）
- 提供REST API端点（/health, /status, /stats, /sync, /stop）
- 增强`/monitoring-status`斜杠命令

**Acceptance Criteria**：
1. ✅ 健康检查端点（< 50ms）
2. ✅ 状态端点（< 100ms）
3. ✅ 统计端点（< 200ms）
4. ✅ 管理端点（手动同步、优雅停止）
5. ✅ 斜杠命令增强
6. ✅ 安全性（localhost only）

**Integration Verification**：
- IV1: 不影响监控性能
- IV2: 与Claude Code集成
- IV3: 优雅停止机制

**工作量估算**：3-4小时

---
