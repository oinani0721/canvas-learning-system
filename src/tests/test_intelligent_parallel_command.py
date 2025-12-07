"""
测试智能并行命令处理器 - Story 10.3

测试IntelligentParallelCommandHandler的各项功能，包括：
- 参数验证
- Canvas节点检测
- 预览模式
- 用户确认
- 错误处理

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-27
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from canvas_utils import (
    IntelligentParallelCommandHandler,
)


class TestIntelligentParallelCommandHandler:
    """测试IntelligentParallelCommandHandler类"""

    @pytest.fixture
    def handler(self):
        """创建命令处理器实例"""
        return IntelligentParallelCommandHandler()

    @pytest.fixture
    def mock_canvas_data(self):
        """创建模拟Canvas数据"""
        return {
            "nodes": [
                {
                    "id": "yellow-1",
                    "type": "text",
                    "text": "这是第一个黄色节点的理解内容",
                    "x": 100,
                    "y": 200,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色
                },
                {
                    "id": "yellow-2",
                    "type": "text",
                    "text": "这是第二个黄色节点的理解内容",
                    "x": 500,
                    "y": 200,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色
                },
                {
                    "id": "yellow-empty",
                    "type": "text",
                    "text": "",
                    "x": 900,
                    "y": 200,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色但为空
                },
                {
                    "id": "red-1",
                    "type": "text",
                    "text": "红色节点内容",
                    "x": 100,
                    "y": 400,
                    "width": 400,
                    "height": 300,
                    "color": "1"  # 红色
                }
            ],
            "edges": []
        }

    @pytest.fixture
    def temp_canvas_file(self, mock_canvas_data):
        """创建临时Canvas文件"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(mock_canvas_data, f, ensure_ascii=False, indent=2)
            temp_path = f.name

        yield temp_path

        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    class TestParameterValidation:
        """测试参数验证功能"""

        @pytest.mark.asyncio
        async def test_validate_default_parameters(self, handler):
            """测试默认参数验证"""
            params = {}
            validated = handler._validate_parameters(params)

            assert validated['max'] == 12
            assert validated['auto'] is False
            assert validated['dry_run'] is False
            assert validated['verbose'] is False

        @pytest.mark.asyncio
        async def test_validate_custom_parameters(self, handler):
            """测试自定义参数验证"""
            params = {
                'max': 8,
                'auto': True,
                'dry_run': True,
                'verbose': True
            }
            validated = handler._validate_parameters(params)

            assert validated['max'] == 8
            assert validated['auto'] is True
            assert validated['dry_run'] is True
            assert validated['verbose'] is True

        @pytest.mark.asyncio
        async def test_validate_invalid_max_parameter(self, handler):
            """测试无效的max参数"""
            # 测试超出范围
            with pytest.raises(ValueError, match="--max参数必须是1-20之间的整数"):
                handler._validate_parameters({'max': 25})

            with pytest.raises(ValueError, match="--max参数必须是1-20之间的整数"):
                handler._validate_parameters({'max': 0})

            # 测试非整数
            with pytest.raises(ValueError, match="--max参数必须是1-20之间的整数"):
                handler._validate_parameters({'max': 'abc'})

        @pytest.mark.asyncio
        async def test_validate_nodes_parameter(self, handler):
            """测试nodes参数验证"""
            params = {'nodes': 'node1,node2, node3'}
            validated = handler._validate_parameters(params)

            assert validated['nodes'] == ['node1', 'node2', 'node3']

        @pytest.mark.asyncio
        async def test_validate_boolean_parameters_conversion(self, handler):
            """测试布尔参数类型转换"""
            # 测试各种真值
            for true_val in [1, '1', True, 'true', 'yes']:
                validated = handler._validate_parameters({'auto': true_val})
                assert validated['auto'] is True

            # 测试各种假值
            for false_val in [0, '0', False, 'false', 'no', '']:
                validated = handler._validate_parameters({'auto': false_val})
                assert validated['auto'] is False

    class TestCanvasPathResolution:
        """测试Canvas路径解析功能"""

        @pytest.mark.asyncio
        async def test_resolve_explicit_canvas_path(self, handler, temp_canvas_file):
            """测试解析显式指定的Canvas路径"""
            resolved_path = handler._resolve_canvas_path(temp_canvas_file)
            assert os.path.isabs(resolved_path)
            assert resolved_path == os.path.abspath(temp_canvas_file)

        @pytest.mark.asyncio
        async def test_resolve_nonexistent_canvas_file(self, handler):
            """测试解析不存在的Canvas文件"""
            with pytest.raises(FileNotFoundError, match="Canvas文件不存在"):
                handler._resolve_canvas_path("nonexistent.canvas")

        @pytest.mark.asyncio
        async def test_resolve_relative_canvas_path(self, handler, temp_canvas_file):
            """测试解析相对路径Canvas文件"""
            # 获取相对路径
            abs_path = os.path.abspath(temp_canvas_file)
            rel_path = os.path.relpath(abs_path, os.getcwd())

            resolved_path = handler._resolve_canvas_path(rel_path)
            assert os.path.isabs(resolved_path)
            assert resolved_path == abs_path

        @pytest.mark.asyncio
        @patch('os.listdir')
        @patch('os.path.exists')
        async def test_auto_find_canvas_file(self, mock_exists, mock_listdir, handler):
            """测试自动查找Canvas文件"""
            # 模拟当前目录有Canvas文件
            mock_listdir.return_value = ['test.canvas', 'other.txt']
            mock_exists.side_effect = lambda path: path.endswith('.canvas')

            resolved_path = handler._resolve_canvas_path(None)
            assert resolved_path.endswith('test.canvas')

        @pytest.mark.asyncio
        @patch('os.listdir')
        @patch('os.walk')
        @patch('os.path.exists')
        async def test_auto_find_canvas_in_subdirectory(
            self,
            mock_exists,
            mock_walk,
            mock_listdir,
            handler
        ):
            """测试在子目录中查找Canvas文件"""
            # 当前目录没有Canvas文件
            mock_listdir.return_value = ['subdir', 'other.txt']
            mock_exists.return_value = False

            # 子目录有Canvas文件
            mock_walk.return_value = [
                (os.getcwd(), ['subdir'], []),
                (os.path.join(os.getcwd(), 'subdir'), [], ['test.canvas'])
            ]
            mock_exists.side_effect = lambda path: 'test.canvas' in path

            resolved_path = handler._resolve_canvas_path(None)
            assert 'subdir' in resolved_path
            assert resolved_path.endswith('test.canvas')

        @pytest.mark.asyncio
        @patch('os.listdir')
        @patch('os.walk')
        @patch('os.path.exists')
        async def test_no_canvas_file_found(
            self,
            mock_exists,
            mock_walk,
            mock_listdir,
            handler
        ):
            """测试找不到Canvas文件的情况"""
            mock_listdir.return_value = ['subdir', 'other.txt']
            mock_walk.return_value = []
            mock_exists.return_value = False

            with pytest.raises(FileNotFoundError, match="未找到Canvas文件"):
                handler._resolve_canvas_path(None)

    class TestTargetNodesDetection:
        """测试目标节点检测功能"""

        @pytest.mark.asyncio
        async def test_get_all_yellow_nodes(self, handler, mock_canvas_data, temp_canvas_file):
            """测试获取所有黄色节点"""
            with patch.object(handler.canvas_orchestrator, 'read_canvas', return_value=mock_canvas_data):
                nodes = await handler._get_target_nodes(temp_canvas_file)

                # 应该返回两个有内容的黄色节点
                assert len(nodes) == 2
                assert 'yellow-1' in nodes
                assert 'yellow-2' in nodes
                assert 'yellow-empty' not in nodes  # 空节点应被跳过

        @pytest.mark.asyncio
        async def test_get_specific_yellow_nodes(self, handler, mock_canvas_data, temp_canvas_file):
            """测试获取指定的黄色节点"""
            with patch.object(handler.canvas_orchestrator, 'read_canvas', return_value=mock_canvas_data):
                nodes = await handler._get_target_nodes(
                    temp_canvas_file,
                    ['yellow-1', 'yellow-2', 'red-1']
                )

                # 只返回有效的黄色节点
                assert len(nodes) == 2
                assert 'yellow-1' in nodes
                assert 'yellow-2' in nodes
                assert 'red-1' not in nodes  # 不是黄色节点

        @pytest.mark.asyncio
        async def test_get_empty_nodes_list(self, handler, mock_canvas_data, temp_canvas_file):
            """测试空Canvas或没有黄色节点"""
            empty_canvas = {"nodes": [], "edges": []}
            with patch.object(handler.canvas_orchestrator, 'read_canvas', return_value=empty_canvas):
                nodes = await handler._get_target_nodes(temp_canvas_file)
                assert len(nodes) == 0

        @pytest.mark.asyncio
        async def test_get_nonexistent_nodes(self, handler, mock_canvas_data, temp_canvas_file):
            """测试获取不存在的节点"""
            with patch.object(handler.canvas_orchestrator, 'read_canvas', return_value=mock_canvas_data):
                nodes = await handler._get_target_nodes(
                    temp_canvas_file,
                    ['nonexistent-1', 'nonexistent-2']
                )
                assert len(nodes) == 0

    class TestPreviewMode:
        """测试预览模式功能"""

        @pytest.fixture
        def mock_scheduling_plan(self):
            """创建模拟调度计划"""
            return {
                "plan_id": "plan-1234567890abcdef",
                "canvas_path": "/path/to/test.canvas",
                "node_analysis": {
                    "total_nodes": 2,
                    "yellow_nodes": 2,
                    "grouped_nodes": 2,
                    "skipped_nodes": 0
                },
                "task_groups": [
                    {
                        "group_id": "group-1",
                        "agent_type": "clarification-path",
                        "nodes": ["yellow-1"],
                        "estimated_duration": "45-60秒",
                        "priority_score": 0.85,
                        "dependencies": [],
                        "resource_requirements": {"concurrent_slots": 1}
                    },
                    {
                        "group_id": "group-2",
                        "agent_type": "memory-anchor",
                        "nodes": ["yellow-2"],
                        "estimated_duration": "30-40秒",
                        "priority_score": 0.65,
                        "dependencies": [],
                        "resource_requirements": {"concurrent_slots": 1}
                    }
                ],
                "execution_strategy": {
                    "max_concurrent_groups": 2,
                    "total_estimated_duration": "60-90秒",
                    "optimization_strategy": "dependency_aware",
                    "fallback_strategy": "sequential_processing"
                },
                "user_confirmation_required": True
            }

        @pytest.mark.asyncio
        async def test_format_preview_result(self, handler, mock_scheduling_plan):
            """测试格式化预览结果"""
            result = handler._format_preview_result(mock_scheduling_plan)

            assert result["status"] == "preview"
            assert "智能并行处理计划预览" in result["message"]
            assert "发现 2 个黄色节点" in result["message"]
            assert "生成 2 个任务组" in result["message"]
            assert "clarification-path" in result["message"]
            assert "memory-anchor" in result["message"]

            # 检查执行计划信息
            plan = result["execution_plan"]
            assert plan["total_nodes"] == 2
            assert plan["task_groups"] == 2
            assert plan["estimated_duration"] == "60-90秒"
            assert plan["max_concurrent"] == 2

            # 检查建议
            assert len(result["suggestions"]) > 0
            assert any("跳过确认" in s for s in result["suggestions"])

        @pytest.mark.asyncio
        async def test_dry_run_mode(self, handler, temp_canvas_file):
            """测试dry-run模式"""
            params = {"dry_run": True}
            target_nodes = ["yellow-1", "yellow-2"]

            # Mock调度器和分析结果
            mock_analysis = MagicMock()
            mock_plan = {
                "plan_id": "test-plan",
                "canvas_path": temp_canvas_file,
                "task_groups": [],
                "execution_strategy": {},
                "node_analysis": {"yellow_nodes": 2}
            }

            with patch.object(handler, '_get_target_nodes', return_value=target_nodes):
                with patch.object(handler.scheduler, 'analyze_canvas_nodes', return_value=mock_analysis):
                    with patch.object(handler.scheduler, 'create_scheduling_plan', return_value=mock_plan):
                        result = await handler.handle_intelligent_parallel(params)

                        assert result["status"] == "preview"
                        assert "预览" in result["message"]

    class TestUserConfirmation:
        """测试用户确认功能"""

        @pytest.fixture
        def mock_scheduling_plan(self):
            """简化的调度计划用于确认测试"""
            return {
                "canvas_path": "test.canvas",
                "node_analysis": {"yellow_nodes": 2},
                "task_groups": [
                    {
                        "group_id": "group-1",
                        "agent_type": "clarification-path",
                        "nodes": ["node1"],
                        "estimated_duration": "45-60秒",
                        "priority_score": 0.85,
                        "dependencies": []
                    }
                ],
                "execution_strategy": {
                    "max_concurrent_groups": 1,
                    "total_estimated_duration": "45-60秒"
                }
            }

        @pytest.mark.asyncio
        @patch('builtins.input')
        async def test_user_confirm_yes(self, mock_input, handler, mock_scheduling_plan):
            """测试用户确认执行（输入Y）"""
            mock_input.return_value = 'y'
            result = await handler._request_user_confirmation(mock_scheduling_plan)

            assert result["confirmed"] is True
            assert result["user_response"] == 'y'

        @pytest.mark.asyncio
        @patch('builtins.input')
        async def test_user_confirm_no(self, mock_input, handler, mock_scheduling_plan):
            """测试用户取消执行（输入n）"""
            mock_input.return_value = 'n'
            result = await handler._request_user_confirmation(mock_scheduling_plan)

            assert result["confirmed"] is False
            assert result["user_response"] == 'n'

        @pytest.mark.asyncio
        @patch('builtins.input')
        async def test_user_confirm_empty(self, mock_input, handler, mock_scheduling_plan):
            """测试用户默认确认（直接回车）"""
            mock_input.return_value = ''
            result = await handler._request_user_confirmation(mock_scheduling_plan)

            assert result["confirmed"] is True
            assert result["user_response"] == ''

        @pytest.mark.asyncio
        @patch('builtins.input')
        async def test_user_confirm_invalid_then_yes(self, mock_input, handler, mock_scheduling_plan):
            """测试用户先输入无效值再确认"""
            mock_input.side_effect = ['invalid', 'y']
            result = await handler._request_user_confirmation(mock_scheduling_plan)

            assert result["confirmed"] is True
            assert mock_input.call_count == 2

        @pytest.mark.asyncio
        @patch('builtins.input')
        async def test_user_confirm_keyboard_interrupt(self, mock_input, handler, mock_scheduling_plan):
            """测试用户中断执行（Ctrl+C）"""
            mock_input.side_effect = KeyboardInterrupt()
            result = await handler._request_user_confirmation(mock_scheduling_plan)

            assert result["confirmed"] is False
            assert result["user_response"] == "interrupted"

    class TestProgressCallback:
        """测试进度回调功能"""

        @pytest.mark.asyncio
        async def test_progress_callback_verbose(self, handler):
            """测试详细进度回调"""
            callback = handler._create_progress_callback(verbose=True)

            progress_info = {
                "progress_percentage": 50,
                "completed_tasks": 3,
                "total_tasks": 6,
                "current_task": "clarification-path",
                "elapsed_time": 60
            }

            # 测试回调不会抛出异常
            with patch('builtins.print') as mock_print:
                await callback(progress_info)
                assert mock_print.call_count == 5  # 应该打印5行信息

        @pytest.mark.asyncio
        async def test_progress_callback_simple(self, handler):
            """测试简洁进度回调"""
            callback = handler._create_progress_callback(verbose=False)

            progress_info = {
                "progress_percentage": 75,
                "completed_tasks": 9,
                "total_tasks": 12,
                "current_task": "memory-anchor",
                "elapsed_time": 90
            }

            # 测试回调不会抛出异常
            with patch('builtins.print') as mock_print:
                await callback(progress_info)
                assert mock_print.call_count == 2  # 应该打印2行信息

    class TestErrorHandling:
        """测试错误处理功能"""

        @pytest.mark.asyncio
        async def test_handle_no_yellow_nodes(self, handler, temp_canvas_file):
            """测试没有黄色节点的情况"""
            params = {"canvas_file": temp_canvas_file}

            with patch.object(handler, '_get_target_nodes', return_value=[]):
                result = await handler.handle_intelligent_parallel(params)

                assert result["status"] == "warning"
                assert "未找到可处理的黄色节点" in result["message"]
                assert "请先填写黄色节点" in result["suggestion"]

        @pytest.mark.asyncio
        async def test_handle_file_not_found_error(self, handler):
            """测试文件不存在错误"""
            params = {"canvas_file": "nonexistent.canvas"}

            result = await handler.handle_intelligent_parallel(params)

            assert result["status"] == "error"
            assert "Canvas文件不存在" in result["message"]
            assert any("路径是否正确" in s for s in result["suggestions"])

        @pytest.mark.asyncio
        async def test_handle_value_error(self, handler):
            """测试参数值错误"""
            params = {"max": 100}  # 超出范围

            result = await handler.handle_intelligent_parallel(params)

            assert result["status"] == "error"
            assert "ValueError" in result["error_code"]
            assert any("参数是否有效" in s for s in result["suggestions"])

        @pytest.mark.asyncio
        async def test_handle_general_exception(self, handler):
            """测试通用异常处理"""
            params = {}

            # Mock一个抛出异常的方法
            with patch.object(handler, '_validate_parameters', side_effect=RuntimeError("测试异常")):
                result = await handler.handle_intelligent_parallel(params)

                assert result["status"] == "error"
                assert "测试异常" in result["message"]
                assert "RuntimeError" in result["error_code"]

    class TestSuccessFormatting:
        """测试成功结果格式化"""

        @pytest.fixture
        def mock_execution_result(self):
            """模拟执行结果"""
            return {
                "execution_statistics": {
                    "total_execution_time": 120,
                    "success_rate": 100,
                    "average_task_duration": 40,
                    "failed_tasks": 0
                },
                "task_results": [
                    {"agent_type": "clarification-path"},
                    {"agent_type": "memory-anchor"}
                ]
            }

        @pytest.fixture
        def mock_scheduling_plan(self):
            """模拟调度计划"""
            return {
                "canvas_path": "test.canvas",
                "node_analysis": {"yellow_nodes": 2},
                "task_groups": [
                    {"group_id": "group-1"},
                    {"group_id": "group-2"}
                ]
            }

        @pytest.mark.asyncio
        async def test_format_success_result(
            self,
            handler,
            mock_execution_result,
            mock_scheduling_plan
        ):
            """测试格式化成功结果"""
            result = handler._format_success_result(
                mock_execution_result,
                mock_scheduling_plan
            )

            assert result["status"] == "success"
            assert "智能并行处理完成" in result["message"]
            assert "处理节点: 2个" in result["message"]
            assert "执行时间: 120秒" in result["message"]
            assert "成功率: 100%" in result["message"]

            # 检查结果摘要
            summary = result["results_summary"]
            assert summary["processed_nodes"] == 2
            assert summary["task_groups"] == 2
            assert summary["execution_time"] == 120
            assert summary["success_rate"] == 100

            # 检查学习建议
            assert len(result["learning_suggestions"]) > 0
            assert any("澄清解释" in s for s in result["learning_suggestions"])
            assert any("记忆锚点" in s for s in result["learning_suggestions"])

        @pytest.mark.asyncio
        async def test_generate_learning_suggestions(self, handler):
            """测试生成学习建议"""
            # 测试长时间执行
            result = {"execution_statistics": {"average_task_duration": 150}}
            suggestions = handler._generate_learning_suggestions(result)
            assert any("降低并发数" in s for s in suggestions)

            # 测试有失败任务
            result = {"execution_statistics": {"success_rate": 80, "failed_tasks": 2}}
            suggestions = handler._generate_learning_suggestions(result)
            assert any("任务失败" in s for s in suggestions)

            # 测试不同Agent类型
            result = {
                "execution_statistics": {"success_rate": 100},
                "task_results": [
                    {"agent_type": "clarification-path"},
                    {"agent_type": "comparison-table"}
                ]
            }
            suggestions = handler._generate_learning_suggestions(result)
            assert any("例题练习" in s for s in suggestions)
            assert any("应用场景" in s for s in suggestions)

    class TestIntegration:
        """集成测试"""

        @pytest.mark.asyncio
        async def test_full_execution_flow(self, handler, temp_canvas_file, mock_canvas_data):
            """测试完整执行流程（自动模式）"""
            params = {
                "canvas_file": temp_canvas_file,
                "auto": True,  # 跳过用户确认
                "dry_run": False
            }

            # Mock所有依赖
            target_nodes = ["yellow-1", "yellow-2"]
            mock_analysis = MagicMock()
            mock_plan = {
                "plan_id": "test-plan",
                "canvas_path": temp_canvas_file,
                "node_analysis": {"yellow_nodes": 2},
                "task_groups": [
                    {
                        "group_id": "group-1",
                        "agent_type": "clarification-path",
                        "nodes": ["yellow-1"],
                        "estimated_duration": "45-60秒",
                        "priority_score": 0.85,
                        "dependencies": [],
                        "resource_requirements": {"concurrent_slots": 1}
                    }
                ],
                "execution_strategy": {
                    "max_concurrent_groups": 1,
                    "total_estimated_duration": "45-60秒"
                }
            }
            mock_execution_result = {
                "execution_statistics": {
                    "total_execution_time": 50,
                    "success_rate": 100
                },
                "task_results": []
            }

            with patch.object(handler, '_get_target_nodes', return_value=target_nodes):
                with patch.object(handler.scheduler, 'analyze_canvas_nodes', return_value=mock_analysis):
                    with patch.object(handler.scheduler, 'create_scheduling_plan', return_value=mock_plan):
                        with patch.object(
                            handler.scheduler,
                            'execute_plan_with_progress',
                            return_value=mock_execution_result
                        ):
                            with patch.object(handler, '_apply_results_to_canvas'):
                                result = await handler.handle_intelligent_parallel(params)

                                assert result["status"] == "success"
                                assert "智能并行处理完成" in result["message"]
                                assert result["canvas_path"] == temp_canvas_file

        @pytest.mark.asyncio
        async def test_full_preview_flow(self, handler, temp_canvas_file):
            """测试完整预览流程"""
            params = {
                "canvas_file": temp_canvas_file,
                "dry_run": True
            }

            target_nodes = ["yellow-1"]
            mock_analysis = MagicMock()
            mock_plan = {
                "plan_id": "test-plan",
                "canvas_path": temp_canvas_file,
                "node_analysis": {"yellow_nodes": 1},
                "task_groups": [],
                "execution_strategy": {}
            }

            with patch.object(handler, '_get_target_nodes', return_value=target_nodes):
                with patch.object(handler.scheduler, 'analyze_canvas_nodes', return_value=mock_analysis):
                    with patch.object(handler.scheduler, 'create_scheduling_plan', return_value=mock_plan):
                        result = await handler.handle_intelligent_parallel(params)

                        assert result["status"] == "preview"
                        assert "预览" in result["message"]

        @pytest.mark.asyncio
        async def test_cancelled_execution_flow(self, handler, temp_canvas_file):
            """测试用户取消执行流程"""
            params = {
                "canvas_file": temp_canvas_file,
                "auto": False  # 需要用户确认
            }

            target_nodes = ["yellow-1"]
            mock_analysis = MagicMock()
            mock_plan = {
                "plan_id": "test-plan",
                "canvas_path": temp_canvas_file,
                "node_analysis": {"yellow_nodes": 1},
                "task_groups": [],
                "execution_strategy": {}
            }

            with patch.object(handler, '_get_target_nodes', return_value=target_nodes):
                with patch.object(handler.scheduler, 'analyze_canvas_nodes', return_value=mock_analysis):
                    with patch.object(handler.scheduler, 'create_scheduling_plan', return_value=mock_plan):
                        with patch.object(
                            handler,
                            '_request_user_confirmation',
                            return_value={"confirmed": False, "user_response": "n"}
                        ):
                            result = await handler.handle_intelligent_parallel(params)

                            assert result["status"] == "cancelled"
                            assert "用户取消了执行" in result["message"]
