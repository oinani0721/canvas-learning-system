"""
并行Agent处理API - Canvas学习系统

提供用户友好的API接口，包括：
- 批量任务提交和管理
- 执行状态实时查询
- 结果获取和导出
- 配置管理和系统控制

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
Story: 8.14 (Task 7)
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
import threading
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn

# 导入内部模块
from parallel_agent_executor import ParallelAgentExecutor, AgentTask, Priority
from task_queue_manager import TaskQueueManager, TaskDefinition, TaskPriority
from result_aggregator import ResultAggregator, AgentResult, ResultMetadata, ValidationResult
from performance_monitor import PerformanceMonitor
from error_handling_manager import ErrorHandlingManager, ErrorRecord


# Pydantic模型定义
class TaskSubmissionRequest(BaseModel):
    """任务提交请求模型"""
    agent_name: str = Field(..., description="Agent名称")
    canvas_path: str = Field(..., description="Canvas文件路径")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    priority: str = Field(default="normal", description="任务优先级")
    timeout_seconds: int = Field(default=120, description="超时时间（秒）")
    retry_attempts: int = Field(default=3, description="重试次数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class BatchTaskSubmissionRequest(BaseModel):
    """批量任务提交请求模型"""
    tasks: List[TaskSubmissionRequest] = Field(..., description="任务列表")
    max_concurrent: Optional[int] = Field(None, description="最大并发数")
    execution_name: Optional[str] = Field(None, description="执行名称")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    parallel_processing: Optional[Dict[str, Any]] = None
    context_isolation: Optional[Dict[str, Any]] = None
    task_queue: Optional[Dict[str, Any]] = None
    error_handling: Optional[Dict[str, Any]] = None
    performance_monitoring: Optional[Dict[str, Any]] = None


class ExecutionStatusResponse(BaseModel):
    """执行状态响应模型"""
    execution_id: str
    status: str
    submission_timestamp: str
    task_queue: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    error_management: Dict[str, Any]


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str
    agent_name: str
    worker_id: Optional[str]
    submission_time: str
    start_time: Optional[str]
    completion_time: Optional[str]
    execution_duration_ms: Optional[float]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]


class SystemStatusResponse(BaseModel):
    """系统状态响应模型"""
    system_healthy: bool
    uptime_seconds: float
    active_executions: int
    total_executions: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    worker_status: Dict[str, Any]
    performance_snapshot: Dict[str, Any]
    error_summary: Dict[str, Any]


@dataclass
class APIConfig:
    """API配置"""
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    auto_start: bool = True
    enable_docs: bool = True
    enable_metrics_endpoint: bool = True
    rate_limit: bool = True
    max_concurrent_requests: int = 100


class ParallelAgentAPI:
    """并行Agent处理API主类

    提供RESTful API接口，支持所有并行Agent处理功能。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化API

        Args:
            config: API配置
        """
        self.config = config or {}
        self.api_config = APIConfig(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 8000),
            debug=self.config.get("debug", False)
        )

        # 初始化核心组件
        self.executor = ParallelAgentExecutor()
        self.result_aggregator = ResultAggregator(self.config.get("result_aggregation", {}))
        self.performance_monitor = PerformanceMonitor(self.config.get("performance_monitoring", {}))
        self.error_handler = ErrorHandlingManager(self.config.get("error_handling", {}))

        # FastAPI应用
        self.app = FastAPI(
            title="Canvas Learning System - Parallel Agent API",
            description="并行Agent处理系统API接口",
            version="1.0.0",
            docs_url="/docs" if self.api_config.enable_docs else None,
            redoc_url="/redoc" if self.api_config.enable_docs else None
        )

        # 系统状态
        self.start_time = time.time()
        self.system_healthy = True
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time_ms": 0.0
        }

        # 设置路由
        self._setup_routes()

        # 启动后台任务
        self.background_tasks = []

    def _setup_routes(self) -> None:
        """设置API路由"""

        # 任务提交路由
        @self.app.post("/api/v1/tasks/submit", response_model=Dict[str, str])
        async def submit_single_task(request: TaskSubmissionRequest):
            """提交单个任务"""
            return await self._handle_single_task_submission(request)

        @self.app.post("/api/v1/tasks/batch", response_model=Dict[str, str])
        async def submit_batch_tasks(request: BatchTaskSubmissionRequest, background_tasks: BackgroundTasks):
            """提交批量任务"""
            return await self._handle_batch_task_submission(request, background_tasks)

        # 状态查询路由
        @self.app.get("/api/v1/executions/{execution_id}/status", response_model=ExecutionStatusResponse)
        async def get_execution_status(execution_id: str):
            """获取执行状态"""
            return await self._handle_execution_status_query(execution_id)

        @self.app.get("/api/v1/tasks/{task_id}/status", response_model=TaskStatusResponse)
        async def get_task_status(task_id: str):
            """获取任务状态"""
            return await self._handle_task_status_query(task_id)

        @self.app.get("/api/v1/executions/{execution_id}/results")
        async def get_execution_results(execution_id: str):
            """获取执行结果"""
            return await self._handle_execution_results_query(execution_id)

        # 系统状态路由
        @self.app.get("/api/v1/system/status", response_model=SystemStatusResponse)
        async def get_system_status():
            """获取系统状态"""
            return await self._handle_system_status_query()

        @self.app.get("/api/v1/system/metrics")
        async def get_system_metrics():
            """获取系统指标"""
            return await self._handle_system_metrics_query()

        # 配置管理路由
        @self.app.get("/api/v1/config")
        async def get_config():
            """获取当前配置"""
            return await self._handle_config_query()

        @self.app.put("/api/v1/config")
        async def update_config(request: ConfigUpdateRequest):
            """更新配置"""
            return await self._handle_config_update(request)

        # 结果导出路由
        @self.app.get("/api/v1/results/export")
        async def export_results(
            execution_id: Optional[str] = Query(None),
            format: str = Query("json", regex="^(json|yaml|csv)$")
        ):
            """导出结果"""
            return await self._handle_results_export(execution_id, format)

        # 文件下载路由
        @self.app.get("/api/v1/results/download/{filename}")
        async def download_result_file(filename: str):
            """下载结果文件"""
            return await self._handle_result_file_download(filename)

        # 健康检查路由
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

        # 根路径
        @self.app.get("/")
        async def root():
            """根路径信息"""
            return {
                "name": "Canvas Learning System - Parallel Agent API",
                "version": "1.0.0",
                "status": "running",
                "docs_url": "/docs" if self.api_config.enable_docs else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _handle_single_task_submission(self, request: TaskSubmissionRequest) -> Dict[str, str]:
        """处理单个任务提交

        Args:
            request: 任务提交请求

        Returns:
            Dict[str, str]: 提交结果
        """
        start_time = time.time()

        try:
            # 创建任务
            task_data = {
                "agent_name": request.agent_name,
                "canvas_path": request.canvas_path,
                "input_data": request.input_data,
                "priority": request.priority,
                "timeout_seconds": request.timeout_seconds,
                "retry_attempts": request.retry_attempts,
                "metadata": request.metadata
            }

            # 提交到执行器
            execution_id = await self.executor.submit_batch_tasks([task_data])

            self.api_stats["successful_requests"] += 1

            return {
                "execution_id": execution_id,
                "status": "submitted",
                "message": "任务提交成功"
            }

        except Exception as e:
            self.api_stats["failed_requests"] += 1
            raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")

        finally:
            self._update_api_stats(time.time() - start_time)

    async def _handle_batch_task_submission(self, request: BatchTaskSubmissionRequest,
                                         background_tasks: BackgroundTasks) -> Dict[str, str]:
        """处理批量任务提交

        Args:
            request: 批量任务提交请求
            background_tasks: 后台任务

        Returns:
            Dict[str, str]: 提交结果
        """
        start_time = time.time()

        try:
            # 转换任务数据
            tasks_data = []
            for task_request in request.tasks:
                task_data = {
                    "agent_name": task_request.agent_name,
                    "canvas_path": task_request.canvas_path,
                    "input_data": task_request.input_data,
                    "priority": task_request.priority,
                    "timeout_seconds": task_request.timeout_seconds,
                    "retry_attempts": task_request.retry_attempts,
                    "metadata": task_request.metadata
                }
                tasks_data.append(task_data)

            # 提交到执行器
            execution_id = await self.executor.submit_batch_tasks(
                tasks_data,
                max_concurrent=request.max_concurrent
            )

            # 添加后台任务用于监控
            if request.execution_name:
                background_tasks.add_task(
                    self._monitor_execution_background,
                    execution_id,
                    request.execution_name
                )

            self.api_stats["successful_requests"] += 1

            return {
                "execution_id": execution_id,
                "status": "submitted",
                "task_count": len(tasks_data),
                "message": f"批量任务提交成功，共{len(tasks_data)}个任务"
            }

        except Exception as e:
            self.api_stats["failed_requests"] += 1
            raise HTTPException(status_code=500, detail=f"批量任务提交失败: {str(e)}")

        finally:
            self._update_api_stats(time.time() - start_time)

    async def _handle_execution_status_query(self, execution_id: str) -> ExecutionStatusResponse:
        """处理执行状态查询

        Args:
            execution_id: 执行ID

        Returns:
            ExecutionStatusResponse: 执行状态
        """
        try:
            status = await self.executor.get_execution_status(execution_id)

            if "error" in status:
                raise HTTPException(status_code=404, detail=status["error"])

            return ExecutionStatusResponse(**status)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"查询执行状态失败: {str(e)}")

    async def _handle_task_status_query(self, task_id: str) -> TaskStatusResponse:
        """处理任务状态查询

        Args:
            task_id: 任务ID

        Returns:
            TaskStatusResponse: 任务状态
        """
        try:
            # 从队列管理器获取任务状态
            task_execution = await self.executor.queue_manager.get_task_execution_info(task_id)

            if not task_execution:
                raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

            return TaskStatusResponse(**task_execution)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")

    async def _handle_execution_results_query(self, execution_id: str):
        """处理执行结果查询

        Args:
            execution_id: 执行ID

        Returns:
            Dict: 执行结果
        """
        try:
            results = await self.executor.get_execution_results(execution_id)

            if "error" in results:
                raise HTTPException(status_code=404, detail=results["error"])

            return results

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"查询执行结果失败: {str(e)}")

    async def _handle_system_status_query(self) -> SystemStatusResponse:
        """处理系统状态查询

        Returns:
            SystemStatusResponse: 系统状态
        """
        try:
            # 获取各组件状态
            queue_status = await self.executor.queue_manager.get_queue_status()
            performance_snapshot = self.performance_monitor.get_current_performance_snapshot()
            error_summary = self.error_handler.get_error_statistics()
            worker_status = await self.executor.queue_manager.get_worker_status()

            return SystemStatusResponse(
                system_healthy=self.system_healthy,
                uptime_seconds=time.time() - self.start_time,
                active_executions=len(self.executor.executions),
                total_executions=self.executor.metrics["total_executions"],
                active_tasks=queue_status.get("running_tasks", 0),
                completed_tasks=queue_status.get("completed_tasks", 0),
                failed_tasks=queue_status.get("failed_tasks", 0),
                worker_status=worker_status,
                performance_snapshot=performance_snapshot,
                error_summary=error_summary
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

    async def _handle_system_metrics_query(self):
        """处理系统指标查询

        Returns:
            Dict: 系统指标
        """
        try:
            # 生成性能报告
            performance_report = self.performance_monitor.generate_performance_report()

            # 获取错误趋势
            error_trends = self.error_handler.get_error_trends()

            return {
                "performance_report": performance_report,
                "error_trends": error_trends,
                "api_statistics": self.api_stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")

    async def _handle_config_query(self):
        """处理配置查询

        Returns:
            Dict: 当前配置
        """
        try:
            return {
                "parallel_processing": self.executor.config.get("parallel_processing", {}),
                "context_isolation": self.executor.config.get("context_isolation", {}),
                "task_queue": self.executor.config.get("task_queue", {}),
                "error_handling": self.executor.config.get("error_handling", {}),
                "performance_monitoring": self.executor.config.get("performance_monitoring", {})
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

    async def _handle_config_update(self, request: ConfigUpdateRequest):
        """处理配置更新

        Args:
            request: 配置更新请求

        Returns:
            Dict: 更新结果
        """
        try:
            update_data = request.dict(exclude_unset=True)

            # 更新执行器配置
            success = self.executor.configure_parallel_settings(update_data)

            if success:
                return {
                    "status": "success",
                    "message": "配置更新成功",
                    "updated_sections": list(update_data.keys())
                }
            else:
                raise HTTPException(status_code=500, detail="配置更新失败")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")

    async def _handle_results_export(self, execution_id: Optional[str], format: str):
        """处理结果导出

        Args:
            execution_id: 执行ID
            format: 导出格式

        Returns:
            FileResponse: 导出文件
        """
        try:
            from result_aggregator import ResultFormat

            # 导出结果
            filepath = await self.result_aggregator.export_results(
                execution_id=execution_id,
                format=ResultFormat(format)
            )

            return FileResponse(
                path=filepath,
                filename=Path(filepath).name,
                media_type="application/octet-stream"
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"导出结果失败: {str(e)}")

    async def _handle_result_file_download(self, filename: str):
        """处理结果文件下载

        Args:
            filename: 文件名

        Returns:
            FileResponse: 结果文件
        """
        try:
            results_dir = Path(self.result_aggregator.results_directory)
            filepath = results_dir / filename

            if not filepath.exists():
                raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")

            return FileResponse(
                path=filepath,
                filename=filename,
                media_type="application/octet-stream"
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

    async def _monitor_execution_background(self, execution_id: str, execution_name: str):
        """后台监控执行

        Args:
            execution_id: 执行ID
            execution_name: 执行名称
        """
        try:
            # 定期检查执行状态
            while True:
                status = await self.executor.get_execution_status(execution_id)

                if status.get("overall_status") in ["completed", "failed", "cancelled"]:
                    # 执行完成，记录日志
                    print(f"执行 [{execution_name}] ({execution_id}) 已完成: {status.get('overall_status')}")
                    break

                await asyncio.sleep(30)  # 每30秒检查一次

        except Exception as e:
            print(f"后台监控任务失败 [{execution_name}]: {e}")

    def _update_api_stats(self, response_time_ms: float) -> None:
        """更新API统计信息

        Args:
            response_time_ms: 响应时间（毫秒）
        """
        self.api_stats["total_requests"] += 1

        # 更新平均响应时间
        total_requests = self.api_stats["total_requests"]
        current_avg = self.api_stats["average_response_time_ms"]
        new_avg = (current_avg * (total_requests - 1) + response_time_ms) / total_requests
        self.api_stats["average_response_time_ms"] = new_avg

    async def initialize(self) -> None:
        """初始化API服务"""
        try:
            # 初始化执行器
            await self.executor.initialize()

            # 启动性能监控
            await self.performance_monitor.start_monitoring()

            print(f"Parallel Agent API 已初始化")
            print(f"服务地址: http://{self.api_config.host}:{self.api_config.port}")
            print(f"API文档: http://{self.api_config.host}:{self.api_config.port}/docs")

        except Exception as e:
            print(f"API初始化失败: {e}")
            self.system_healthy = False

    async def shutdown(self) -> None:
        """关闭API服务"""
        try:
            # 关闭执行器
            await self.executor.shutdown()

            # 停止性能监控
            await self.performance_monitor.stop_monitoring()

            print("Parallel Agent API 已关闭")

        except Exception as e:
            print(f"API关闭时出错: {e}")

    def run(self) -> None:
        """启动API服务"""
        if __name__ == "__main__":
            uvicorn.run(
                self.app,
                host=self.api_config.host,
                port=self.api_config.port,
                log_level="debug" if self.api_config.debug else "info"
            )


# 创建API实例
api_instance = ParallelAgentAPI()

# 全局函数用于命令行启动
async def start_api_server(config: Optional[Dict[str, Any]] = None) -> None:
    """启动API服务器

    Args:
        config: API配置
    """
    if config:
        api_instance.config.update(config)

    await api_instance.initialize()

    # 启动服务器（在主线程中）
    uvicorn.run(
        api_instance.app,
        host=api_instance.api_config.host,
        port=api_instance.api_config.port,
        log_level="debug" if api_instance.api_config.debug else "info"
    )


# 简化的同步接口函数（用于程序化调用）
def submit_single_task(agent_name: str, canvas_path: str, input_data: Dict[str, Any],
                      priority: str = "normal", timeout_seconds: int = 120) -> str:
    """提交单个任务（同步接口）

    Args:
        agent_name: Agent名称
        canvas_path: Canvas文件路径
        input_data: 输入数据
        priority: 任务优先级
        timeout_seconds: 超时时间

    Returns:
        str: 执行ID
    """
    async def _submit():
        task_data = {
            "agent_name": agent_name,
            "canvas_path": canvas_path,
            "input_data": input_data,
            "priority": priority,
            "timeout_seconds": timeout_seconds
        }
        return await api_instance.executor.submit_batch_tasks([task_data])

    return asyncio.run(_submit())


def submit_batch_tasks(tasks: List[Dict[str, Any]], max_concurrent: Optional[int] = None) -> str:
    """提交批量任务（同步接口）

    Args:
        tasks: 任务列表
        max_concurrent: 最大并发数

    Returns:
        str: 执行ID
    """
    async def _submit():
        return await api_instance.executor.submit_batch_tasks(tasks, max_concurrent)

    return asyncio.run(_submit())


def get_execution_status(execution_id: str) -> Dict[str, Any]:
    """获取执行状态（同步接口）

    Args:
        execution_id: 执行ID

    Returns:
        Dict: 执行状态
    """
    return asyncio.run(api_instance.executor.get_execution_status(execution_id))


def get_execution_results(execution_id: str) -> Dict[str, Any]:
    """获取执行结果（同步接口）

    Args:
        execution_id: 执行ID

    Returns:
        Dict: 执行结果
    """
    return asyncio.run(api_instance.executor.get_execution_results(execution_id))


def get_system_status() -> Dict[str, Any]:
    """获取系统状态（同步接口）

    Returns:
        Dict: 系统状态
    """
    return asyncio.run(api_instance._handle_system_status_query())


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Canvas Learning System - Parallel Agent API")
    parser.add_argument("--host", default="localhost", help="服务器地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--config", help="配置文件路径")

    args = parser.parse_args()

    # 准备配置
    config = {
        "host": args.host,
        "port": args.port,
        "debug": args.debug
    }

    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
            config.update(file_config)

    # 启动服务器
    asyncio.run(start_api_server(config))