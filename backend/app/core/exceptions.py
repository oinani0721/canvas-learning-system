# ✅ Verified from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#错误处理策略
"""
Custom exceptions for Canvas Learning System.
[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#异常层次结构]
"""


class CanvasException(Exception):
    """Canvas操作基础异常"""
    pass


class CanvasNotFoundException(CanvasException):
    """Canvas文件未找到"""
    def __init__(self, canvas_name: str):
        self.canvas_name = canvas_name
        super().__init__(f"Canvas '{canvas_name}' not found")


class NodeNotFoundException(CanvasException):
    """节点未找到"""
    def __init__(self, node_id: str, canvas_name: str = None):
        self.node_id = node_id
        self.canvas_name = canvas_name
        msg = f"Node '{node_id}' not found"
        if canvas_name:
            msg += f" in canvas '{canvas_name}'"
        super().__init__(msg)


class ValidationError(CanvasException):
    """数据验证错误"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        self.message = message
        super().__init__(message)


class AgentCallError(Exception):
    """Agent调用错误"""
    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        super().__init__(f"Agent '{agent_name}' call failed: {message}")


class TaskNotFoundError(Exception):
    """后台任务未找到"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task '{task_id}' not found")


class PromptLoadError(Exception):
    """Prompt 模板加载错误（文件缺失/格式错误/元数据不完整）

    Story 7.3: Prompt 版本管理与回归测试
    [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
    """
    def __init__(self, message: str, prompt_name: str = "", file_path: str = ""):
        self.prompt_name = prompt_name
        self.file_path = file_path
        detail = f"Prompt '{prompt_name}'" if prompt_name else "Prompt"
        if file_path:
            detail += f" (file: {file_path})"
        super().__init__(f"{detail}: {message}")
