"""
技术验证和监控系统测试 - Story 8.18

测试技术验证和监控系统的所有核心功能，确保系统的稳定性和准确性。

测试覆盖范围：
1. Context7技术验证测试 - 验证技术验证逻辑的准确性
2. 监控系统性能测试 - 验证监控系统的性能表现
3. 告警系统测试 - 验证告警触发和抑制机制
4. 仪表板功能测试 - 验证监控仪表板的数据展示
5. 配置系统测试 - 验证配置加载和处理逻辑
6. 集成测试 - 验证各组件间的协作

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
Story: 8.18 - 建立完整技术验证和监控系统
"""

# 导入被测试的模块
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

sys.path.append('..')

from context7_technology_validator import (
    Context7TechnologyValidator,
    Context7ValidationResult,
    PerformanceBenchmark,
    create_context7_validator,
    run_context7_validation,
)
from monitoring_dashboard import DashboardConfig, MonitoringDashboard, create_monitoring_dashboard
from technical_validation_monitoring_system import (
    SystemHealthMetrics,
    TechnicalValidationMonitoringSystem,
    TechnologyValidationResult,
    create_technical_monitoring_system,
    run_quick_health_check,
)


class TestTechnicalValidationMonitoringSystem:
    """技术验证和监控系统测试"""

    @pytest.fixture
    def temp_config_dir(self):
        """临时配置目录fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            test_config = {
                "monitoring": {
                    "enabled": True,
                    "monitoring_interval_seconds": 5,
                    "data_retention_days": 7
                },
                "context7_validations": {
                    "confidence_threshold": 7.0,
                    "validated_technologies": {
                        "test_tech": {"expected_confidence": 8.0}
                    }
                }
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(test_config, f)

            yield str(config_path)

    @pytest.fixture
    def monitoring_system(self, temp_config_dir):
        """监控系统实例fixture"""
        return TechnicalValidationMonitoringSystem(temp_config_dir)

    def test_system_initialization(self, monitoring_system):
        """测试系统初始化"""
        assert monitoring_system is not None
        assert monitoring_system.config_path is not None
        assert monitoring_system.monitoring_session_id is not None
        assert len(monitoring_system.monitoring_session_id) == 36  # UUID长度
        assert monitoring_system.monitoring_active is False
        assert isinstance(monitoring_system.technology_validations, dict)
        assert isinstance(monitoring_system.active_alerts, list)
        assert isinstance(monitoring_system.health_metrics, dict)

    def test_config_loading(self, temp_config_dir):
        """测试配置加载"""
        system = TechnicalValidationMonitoringSystem(temp_config_dir)

        assert system.config["monitoring"]["enabled"] is True
        assert system.config["monitoring"]["monitoring_interval_seconds"] == 5
        assert system.config["context7_validations"]["confidence_threshold"] == 7.0

    def test_default_config_loading(self):
        """测试默认配置加载"""
        system = TechnicalValidationMonitoringSystem("non_existent_config.yaml")

        assert "monitoring" in system.config
        assert "context7_validations" in system.config
        assert "alert_system" in system.config

    @pytest.mark.asyncio
    async def test_start_monitoring_session(self, monitoring_system):
        """测试启动监控会话"""
        session_id = monitoring_system.start_monitoring_session()

        assert session_id is not None
        assert len(session_id) == 36
        assert monitoring_system.monitoring_active is True
        assert monitoring_system.monitoring_session_id == session_id

    @pytest.mark.asyncio
    async def test_context7_technology_validation(self, monitoring_system):
        """测试Context7技术验证"""
        result = await monitoring_system.validate_context7_technologies()

        assert "validation_status" in result
        assert "last_verification_timestamp" in result
        assert "verified_technologies" in result
        assert len(result["verified_technologies"]) > 0

        for tech in result["verified_technologies"]:
            assert "technology_name" in tech
            assert "context7_confidence_score" in tech
            assert "validation_status" in tech
            assert "performance_benchmarks" in tech
            assert "integration_health" in tech

    @pytest.mark.asyncio
    async def test_graphiti_performance_monitoring(self, monitoring_system):
        """测试Graphiti性能监控"""
        result = await monitoring_system.monitor_graphiti_performance()

        assert "neo4j_cluster_status" in result
        assert "query_performance_metrics" in result
        assert "data_consistency_checks" in result
        assert "knowledge_graph_health" in result

        # 验证Neo4j集群状态
        neo4j_status = result["neo4j_cluster_status"]
        assert "cluster_health" in neo4j_status
        assert "active_nodes" in neo4j_status
        assert "data_replication_status" in neo4j_status

    @pytest.mark.asyncio
    async def test_mcp_memory_service_monitoring(self, monitoring_system):
        """测试MCP记忆服务监控"""
        result = await monitoring_system.monitor_mcp_memory_service()

        assert "service_status" in result
        assert "vector_database_metrics" in result
        assert "embedding_model_performance" in result
        assert "memory_operations_metrics" in result

        # 验证服务状态
        service_status = result["service_status"]
        assert "service_health" in service_status
        assert "uptime_hours" in service_status
        assert "version" in service_status

    @pytest.mark.asyncio
    async def test_parallel_processing_monitoring(self, monitoring_system):
        """测试并行处理监控"""
        result = await monitoring_system.monitor_parallel_processing()

        assert "process_pool_status" in result
        assert "task_queue_metrics" in result
        assert "concurrency_performance" in result
        assert "error_handling_metrics" in result

        # 验证进程池状态
        pool_status = result["process_pool_status"]
        assert "active_workers" in pool_status
        assert "worker_utilization" in pool_status
        assert "process_health_score" in pool_status

    @pytest.mark.asyncio
    async def test_slash_command_system_monitoring(self, monitoring_system):
        """测试斜杠命令系统监控"""
        result = await monitoring_system.monitor_slash_command_system()

        assert "command_registry_status" in result
        assert "command_performance_metrics" in result
        assert "user_interaction_metrics" in result

        # 验证命令注册状态
        registry_status = result["command_registry_status"]
        assert "total_registered_commands" in registry_status
        assert "command_health_score" in registry_status

    @pytest.mark.asyncio
    async def test_technical_debt_analysis(self, monitoring_system):
        """测试技术债务分析"""
        result = await monitoring_system.analyze_technical_debt()

        assert "code_quality_metrics" in result
        assert "dependency_health" in result
        assert "performance_risks" in result
        assert "scalability_concerns" in result

        # 验证代码质量指标
        code_quality = result["code_quality_metrics"]
        assert "technical_debt_score" in code_quality
        assert "test_coverage_percentage" in code_quality
        assert "maintainability_index" in code_quality

    @pytest.mark.asyncio
    async def test_health_assessment_generation(self, monitoring_system):
        """测试健康评估生成"""
        # 先添加一些健康指标
        monitoring_system.health_metrics["test_component"] = SystemHealthMetrics(
            component_name="Test Component",
            health_score=85.0,
            status="good",
            key_metrics={"metric1": 100.0}
        )

        result = await monitoring_system.generate_health_assessment()

        assert "overall_system_health" in result
        assert "overall_health_score" in result
        assert "component_health_scores" in result
        assert "components_requiring_attention" in result
        assert "total_components_monitored" in result
        assert "assessment_timestamp" in result

    @pytest.mark.asyncio
    async def test_comprehensive_validation(self, monitoring_system):
        """测试综合验证"""
        result = await monitoring_system.run_comprehensive_validation()

        assert "validation_session_id" in result
        assert "validation_timestamp" in result
        assert "validation_duration_seconds" in result
        assert "context7_validations" in result
        assert "graphiti_monitoring" in result
        assert "mcp_memory_monitoring" in result
        assert "parallel_processing_monitoring" in result
        assert "slash_command_system_monitoring" in result
        assert "technical_debt_monitoring" in result
        assert "health_assessment" in result
        assert "overall_system_health" in result

    def test_alert_system_setup(self, monitoring_system):
        """测试告警系统设置"""
        alert_config = {
            "enabled": True,
            "alert_levels": ["critical", "warning"],
            "performance_degradation": {"threshold_percentage": 25}
        }

        success = monitoring_system.setup_alert_system(alert_config)

        assert success is True
        assert monitoring_system.config["alert_system"]["enabled"] is True
        assert "critical" in monitoring_system.config["alert_system"]["alert_levels"]

    def test_monitoring_dashboard_creation(self, monitoring_system):
        """测试监控仪表板创建"""
        dashboard_config = monitoring_system.create_monitoring_dashboard()

        assert "dashboard_id" in dashboard_config
        assert "title" in dashboard_config
        assert "panels" in dashboard_config
        assert "refresh_interval_seconds" in dashboard_config
        assert len(dashboard_config["panels"]) > 0

    def test_predictive_maintenance_enablement(self, monitoring_system):
        """测试预测性维护启用"""
        success = monitoring_system.enable_predictive_maintenance()

        assert success is True
        assert monitoring_system.config["predictive_maintenance"]["enabled"] is True
        assert monitoring_system.config["predictive_maintenance"]["failure_prediction"] is True

    def test_monitoring_summary(self, monitoring_system):
        """测试监控摘要"""
        # 添加一些测试数据
        monitoring_system.technology_validations["test"] = Mock()
        monitoring_system.health_metrics["test"] = Mock()
        monitoring_system.active_alerts.append(Mock())

        summary = monitoring_system.get_monitoring_summary()

        assert "session_id" in summary
        assert "start_time" in summary
        assert "monitoring_active" in summary
        assert "technologies_validated" in summary
        assert "health_components_monitored" in summary
        assert "active_alerts_count" in summary

    def test_stop_monitoring_session(self, monitoring_system):
        """测试停止监控会话"""
        # 先启动监控
        monitoring_system.start_monitoring_session()
        assert monitoring_system.monitoring_active is True

        # 停止监控
        monitoring_system.stop_monitoring_session()
        assert monitoring_system.monitoring_active is False

    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试create_technical_monitoring_system
        system = await create_technical_monitoring_system()
        assert isinstance(system, TechnicalValidationMonitoringSystem)

        # 测试run_quick_health_check
        with patch('technical_validation_monitoring_system.create_technical_monitoring_system') as mock_create:
            mock_system = AsyncMock()
            mock_system.run_comprehensive_validation.return_value = {"test": "result"}
            mock_create.return_value = mock_system

            result = await run_quick_health_check()
            assert result == {"test": "result"}


class TestContext7TechnologyValidator:
    """Context7技术验证器测试"""

    @pytest.fixture
    def validator(self):
        """验证器实例fixture"""
        return Context7TechnologyValidator(confidence_threshold=7.5)

    def test_validator_initialization(self, validator):
        """测试验证器初始化"""
        assert validator.confidence_threshold == 7.5
        assert isinstance(validator.validation_history, dict)
        assert isinstance(validator.baseline_metrics, dict)
        assert isinstance(validator.risk_thresholds, dict)

        # 验证基准指标包含预期技术
        assert "graphiti" in validator.baseline_metrics
        assert "mcp_memory" in validator.baseline_metrics
        assert "aiomultiprocess" in validator.baseline_metrics

    @pytest.mark.asyncio
    async def test_graphiti_integration_validation(self, validator):
        """测试Graphiti集成验证"""
        result = await validator.validate_graphiti_integration()

        assert isinstance(result, Context7ValidationResult)
        assert result.technology_name == "Graphiti"
        assert isinstance(result.context7_confidence_score, float)
        assert result.validation_status in ["verified", "warning", "failed"]
        assert isinstance(result.performance_benchmarks, dict)
        assert isinstance(result.integration_health, dict)
        assert isinstance(result.risk_assessment, dict)
        assert result.context7_verification_id is not None

    @pytest.mark.asyncio
    async def test_mcp_integration_validation(self, validator):
        """测试MCP集成验证"""
        result = await validator.validate_mcp_integration()

        assert isinstance(result, Context7ValidationResult)
        assert result.technology_name == "MCP Memory Service"
        assert isinstance(result.context7_confidence_score, float)
        assert result.validation_status in ["verified", "warning", "failed"]

    @pytest.mark.asyncio
    async def test_aiomultiprocess_integration_validation(self, validator):
        """测试aiomultiprocess集成验证"""
        result = await validator.validate_aiomultiprocess_integration()

        assert isinstance(result, Context7ValidationResult)
        assert result.technology_name == "aiomultiprocess"
        assert isinstance(result.context7_confidence_score, float)
        assert result.validation_status in ["verified", "warning", "failed"]

    @pytest.mark.asyncio
    async def test_context7_confidence_query(self, validator):
        """测试Context7置信度查询"""
        confidence = await validator._query_context7_confidence("测试技术")

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 10.0

    @pytest.mark.asyncio
    async def test_performance_benchmarks_comparison(self, validator):
        """测试性能基准对比"""
        # 先添加一些验证历史
        await validator.validate_graphiti_integration()

        result = await validator.compare_performance_benchmarks()

        assert isinstance(result, dict)
        if "graphiti" in result:
            benchmarks = result["graphiti"]
            for metric_name, benchmark in benchmarks.items():
                assert isinstance(benchmark, PerformanceBenchmark)
                assert benchmark.current_value >= 0
                assert benchmark.baseline_value >= 0
                assert benchmark.status in ["improved", "stable", "degraded"]

    @pytest.mark.asyncio
    async def test_integration_risk_assessment(self, validator):
        """测试集成风险评估"""
        # 先添加一些验证历史
        await validator.validate_graphiti_integration()

        result = await validator.assess_integration_risk()

        assert isinstance(result, dict)
        if "graphiti" in result:
            risk_data = result["graphiti"]
            assert "overall_risk_level" in risk_data
            assert "overall_risk_score" in risk_data
            assert "total_risks" in risk_data
            assert "critical_risks_count" in risk_data
            assert "risk_trend" in risk_data

    def test_validation_summary(self, validator):
        """测试验证摘要"""
        # 添加一些模拟验证历史
        mock_result = Mock()
        mock_result.context7_confidence_score = 8.0
        mock_result.validation_status = "verified"
        mock_result.validation_timestamp = datetime.now()
        mock_result.risk_assessment = {"overall_risk_level": "low"}

        validator.validation_history["test_tech"] = [mock_result]

        summary = validator.get_validation_summary()

        assert "total_technologies_validated" in summary
        assert "validation_summary" in summary
        assert "overall_context7_confidence" in summary
        assert "high_risk_technologies" in summary
        assert summary["total_technologies_validated"] == 1
        assert summary["overall_context7_confidence"] == 8.0

    @pytest.mark.asyncio
    async def test_comprehensive_validation(self, validator):
        """测试综合验证"""
        result = await validator.run_comprehensive_validation()

        assert isinstance(result, dict)
        assert "graphiti" in result
        assert "mcp_memory" in result
        assert "aiomultiprocess" in result

        for tech, validation_result in result.items():
            assert isinstance(validation_result, Context7ValidationResult)
            assert validation_result.technology_name in ["Graphiti", "MCP Memory Service", "aiomultiprocess"]

    def test_risk_trend_analysis(self, validator):
        """测试风险趋势分析"""
        # 创建模拟验证结果
        mock_results = []
        risk_levels = ["low", "medium", "high"]

        for i, level in enumerate(risk_levels):
            mock_result = Mock()
            mock_result.risk_assessment = {"overall_risk_level": level}
            mock_result.validation_timestamp = datetime.now() + timedelta(hours=i)
            mock_results.append(mock_result)

        validator.validation_history["test_tech"] = mock_results

        trend = validator._analyze_risk_trend("test_tech", mock_results)
        assert trend == "increasing"

    def test_overall_risk_score_calculation(self, validator):
        """测试综合风险分数计算"""
        risk_assessment = {
            "risk_details": [
                {"probability": 0.5, "impact_score": 0.8},
                {"probability": 0.3, "impact_score": 0.6}
            ]
        }

        score = validator._calculate_overall_risk_score(risk_assessment)

        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0

    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试create_context7_validator
        validator = await create_context7_validator(8.0)
        assert isinstance(validator, Context7TechnologyValidator)
        assert validator.confidence_threshold == 8.0

        # 测试run_context7_validation
        with patch('context7_technology_validator.create_context7_validator') as mock_create:
            mock_validator = AsyncMock()
            mock_validator.run_comprehensive_validation.return_value = {"test": "result"}
            mock_create.return_value = mock_validator

            result = await run_context7_validation()
            assert result == {"test": "result"}


class TestMonitoringDashboard:
    """监控仪表板测试"""

    @pytest.fixture
    def dashboard(self):
        """仪表板实例fixture"""
        return MonitoringDashboard()

    def test_dashboard_initialization(self, dashboard):
        """测试仪表板初始化"""
        assert dashboard is not None
        assert isinstance(dashboard.dashboard_configs, dict)
        assert isinstance(dashboard.dashboard_data, dict)
        assert isinstance(dashboard.active_sessions, dict)

    def test_technical_monitoring_dashboard_creation(self, dashboard):
        """测试技术监控仪表板创建"""
        config = dashboard.create_technical_monitoring_dashboard()

        assert isinstance(config, DashboardConfig)
        assert config.dashboard_id is not None
        assert len(config.dashboard_id) == 36
        assert "Canvas学习系统" in config.title
        assert config.layout == "grid"
        assert len(config.panels) > 0

        # 验证面板配置
        panel_ids = [panel.panel_id for panel in config.panels]
        expected_panels = [
            "system_overview",
            "context7_validations",
            "performance_charts",
            "alerts_timeline",
            "technical_debt",
            "component_health"
        ]

        for expected_panel in expected_panels:
            assert expected_panel in panel_ids

    def test_context7_validation_dashboard_creation(self, dashboard):
        """测试Context7验证仪表板创建"""
        config = dashboard.create_context7_validation_dashboard()

        assert isinstance(config, DashboardConfig)
        assert "Context7技术验证" in config.title
        assert len(config.panels) > 0

        # 验证特定面板存在
        panel_ids = [panel.panel_id for panel in config.panels]
        assert "context7_overview" in panel_ids
        assert "validation_matrix" in panel_ids
        assert "confidence_trends" in panel_ids

    @pytest.mark.asyncio
    async def test_dashboard_data_retrieval(self, dashboard):
        """测试仪表板数据获取"""
        # 创建测试仪表板
        config = dashboard.create_technical_monitoring_dashboard()

        # 获取仪表板数据
        data = await dashboard.get_dashboard_data(config.dashboard_id)

        assert "dashboard_id" in data
        assert "title" in data
        assert "last_updated" in data
        assert "panels" in data
        assert len(data["panels"]) == len(config.panels)

        # 验证面板数据
        for panel_id, panel_data in data["panels"].items():
            if "error" not in panel_data:
                assert panel_data is not None

    @pytest.mark.asyncio
    async def test_panel_data_retrieval(self, dashboard):
        """测试面板数据获取"""
        config = dashboard.create_technical_monitoring_dashboard()

        # 获取特定面板数据
        panel_data = await dashboard.get_dashboard_data(
            config.dashboard_id,
            "system_overview"
        )

        assert "system_overview" in panel_data
        assert isinstance(panel_data["system_overview"], dict)

    @pytest.mark.asyncio
    async def test_system_health_panel_data(self, dashboard):
        """测试系统健康面板数据"""
        data = await dashboard._get_system_health_data({})

        assert "overall_health" in data
        assert "health_score" in data
        assert "active_alerts" in data
        assert "monitored_components" in data
        assert "last_updated" in data

    @pytest.mark.asyncio
    async def test_context7_validations_panel_data(self, dashboard):
        """测试Context7验证面板数据"""
        data = await dashboard._get_context7_validations_data({})

        assert "validations" in data
        assert "total_count" in data
        assert "verified_count" in data
        assert "average_confidence" in data
        assert "last_updated" in data

        # 验证验证数据结构
        if data["validations"]:
            validation = data["validations"][0]
            assert "technology" in validation
            assert "confidence_score" in validation
            assert "status" in validation

    @pytest.mark.asyncio
    async def test_performance_metrics_panel_data(self, dashboard):
        """测试性能指标面板数据"""
        data = await dashboard._get_performance_metrics_data({})

        assert "metrics" in data
        assert "time_series" in data
        assert "baseline" in data
        assert "last_updated" in data

        # 验证时间序列数据
        if data["time_series"]:
            data_point = data["time_series"][0]
            assert "timestamp" in data_point
            assert "response_time" in data_point

    @pytest.mark.asyncio
    async def test_alerts_panel_data(self, dashboard):
        """测试告警面板数据"""
        data = await dashboard._get_alerts_data({})

        assert "alerts" in data
        assert "total_count" in data
        assert "severity_breakdown" in data
        assert "last_updated" in data

        # 验证告警数据结构
        if data["alerts"]:
            alert = data["alerts"][0]
            assert "alert_id" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "timestamp" in alert

    def test_dashboard_session_creation(self, dashboard):
        """测试仪表板会话创建"""
        config = dashboard.create_technical_monitoring_dashboard()

        session_id = dashboard.create_dashboard_session(config.dashboard_id)

        assert session_id is not None
        assert len(session_id) == 36
        assert session_id in dashboard.active_sessions

        session = dashboard.active_sessions[session_id]
        assert session["dashboard_id"] == config.dashboard_id
        assert "created_at" in session
        assert "last_activity" in session
        assert session["auto_refresh"] is True

    def test_dashboard_session_update(self, dashboard):
        """测试仪表板会话更新"""
        config = dashboard.create_technical_monitoring_dashboard()
        session_id = dashboard.create_dashboard_session(config.dashboard_id)

        # 更新会话
        success = dashboard.update_dashboard_session(session_id, auto_refresh=False)

        assert success is True
        assert dashboard.active_sessions[session_id]["auto_refresh"] is False

    def test_expired_session_cleanup(self, dashboard):
        """测试过期会话清理"""
        config = dashboard.create_technical_monitoring_dashboard()
        session_id = dashboard.create_dashboard_session(config.dashboard_id)

        # 模拟过期会话
        dashboard.active_sessions[session_id]["last_activity"] = datetime.now() - timedelta(hours=25)

        # 清理过期会话
        dashboard.cleanup_expired_sessions(max_inactive_hours=24)

        assert session_id not in dashboard.active_sessions

    def test_dashboard_html_generation(self, dashboard):
        """测试仪表板HTML生成"""
        config = dashboard.create_technical_monitoring_dashboard()

        html = dashboard.get_dashboard_html(config.dashboard_id)

        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
        assert config.title in html
        assert "dashboard-grid" in html

    def test_dashboard_data_export(self, dashboard):
        """测试仪表板数据导出"""
        config = dashboard.create_technical_monitoring_dashboard()

        export_path = dashboard.export_dashboard_data(config.dashboard_id, "json")

        assert isinstance(export_path, str)
        assert export_path.endswith(".json")
        assert config.dashboard_id in export_path

    def test_error_handling(self, dashboard):
        """测试错误处理"""
        # 测试不存在的仪表板
        with pytest.raises(ValueError):
            dashboard.get_dashboard_html("non_existent_id")

        with pytest.raises(ValueError):
            dashboard.create_dashboard_session("non_existent_id")

        # 测试不存在的面板 - 注意：这个测试需要在异步上下文中运行
        config = dashboard.create_technical_monitoring_dashboard()
        # 由于get_dashboard_data是异步的，这里我们只测试同步的部分
        assert config.dashboard_id is not None

    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """测试异步错误处理"""
        dashboard = MonitoringDashboard()
        config = dashboard.create_technical_monitoring_dashboard()

        # 测试不存在的面板
        with pytest.raises(ValueError):
            await dashboard.get_dashboard_data(config.dashboard_id, "non_existent_panel")

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """测试便捷函数"""
        dashboard = create_monitoring_dashboard()
        assert isinstance(dashboard, MonitoringDashboard)


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_monitoring_system_with_validator(self):
        """测试监控系统与验证器集成"""
        # 创建监控系统
        monitoring_system = TechnicalValidationMonitoringSystem()

        # 创建Context7验证器
        validator = Context7TechnologyValidator()

        # 运行验证
        validation_results = await validator.run_comprehensive_validation()

        # 将验证结果添加到监控系统
        for tech_name, result in validation_results.items():
            monitoring_system.technology_validations[tech_name] = TechnologyValidationResult(
                technology_name=result.technology_name,
                context7_confidence_score=result.context7_confidence_score,
                validation_status=result.validation_status,
                performance_benchmarks=result.performance_benchmarks,
                integration_health={},
                risk_assessment=result.risk_assessment
            )

        # 生成健康评估
        health_assessment = await monitoring_system.generate_health_assessment()

        assert "overall_health" in health_assessment
        assert "health_score" in health_assessment

    @pytest.mark.asyncio
    async def test_dashboard_with_monitoring_system(self):
        """测试仪表板与监控系统集成"""
        # 创建监控系统
        monitoring_system = TechnicalValidationMonitoringSystem()

        # 运行监控获取数据
        await monitoring_system.validate_context7_technologies()
        await monitoring_system.monitor_graphiti_performance()

        # 创建仪表板
        dashboard = MonitoringDashboard(monitoring_system)
        config = dashboard.create_technical_monitoring_dashboard()

        # 获取仪表板数据
        dashboard_data = await dashboard.get_dashboard_data(config.dashboard_id)

        assert "panels" in dashboard_data
        assert len(dashboard_data["panels"]) > 0

    def test_configuration_integration(self):
        """测试配置集成"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            test_config = {
                "monitoring": {
                    "enabled": True,
                    "monitoring_interval_seconds": 10
                },
                "context7_validations": {
                    "confidence_threshold": 8.0
                }
            }
            yaml.dump(test_config, f)
            config_path = f.name

        try:
            # 使用配置创建系统
            monitoring_system = TechnicalValidationMonitoringSystem(config_path)
            validator = Context7TechnologyValidator(
                confidence_threshold=monitoring_system.config["context7_validations"]["confidence_threshold"]
            )

            assert monitoring_system.config["monitoring"]["monitoring_interval_seconds"] == 10
            assert validator.confidence_threshold == 8.0

        finally:
            # 清理临时文件
            Path(config_path).unlink()


class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_validation_performance(self):
        """测试验证性能"""
        validator = Context7TechnologyValidator()

        start_time = time.time()
        await validator.run_comprehensive_validation()
        end_time = time.time()

        validation_time = end_time - start_time

        # 验证应该在合理时间内完成（小于5秒）
        assert validation_time < 5.0

    @pytest.mark.asyncio
    async def test_monitoring_performance(self):
        """测试监控性能"""
        monitoring_system = TechnicalValidationMonitoringSystem()

        start_time = time.time()
        await monitoring_system.run_comprehensive_validation()
        end_time = time.time()

        monitoring_time = end_time - start_time

        # 监控应该在合理时间内完成（小于10秒）
        assert monitoring_time < 10.0

    @pytest.mark.asyncio
    async def test_dashboard_data_loading_performance(self):
        """测试仪表板数据加载性能"""
        dashboard = MonitoringDashboard()
        config = dashboard.create_technical_monitoring_dashboard()

        start_time = time.time()
        await dashboard.get_dashboard_data(config.dashboard_id)
        end_time = time.time()

        load_time = end_time - start_time

        # 数据加载应该在1秒内完成
        assert load_time < 1.0

    def test_memory_usage(self):
        """测试内存使用"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 创建多个系统实例
        systems = []
        for _ in range(10):
            systems.append(TechnicalValidationMonitoringSystem())

        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # 内存增长应该在合理范围内（小于100MB）
        assert memory_increase < 100 * 1024 * 1024  # 100MB


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
