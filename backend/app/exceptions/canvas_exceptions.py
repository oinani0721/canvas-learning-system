# Canvas Learning System - Custom Exceptions
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
"""
Custom exception classes for Canvas Learning System.

All exceptions follow the error response schema defined in:
[Source: specs/data/error-response.schema.json]

Exception Hierarchy:
    CanvasException (base)
    ├── CanvasNotFoundError (404)
    ├── NodeNotFoundError (404)
    ├── ValidationError (400)
    └── AgentExecutionError (500)
"""

from typing import Any, Dict, Optional


class CanvasException(Exception):
    """
    Base exception class for all Canvas Learning System errors.

    This is the root of the exception hierarchy. All custom exceptions
    should inherit from this class.

    Attributes:
        message: Human-readable error message
        code: HTTP status code
        details: Additional error details (optional)

    Example:
        >>> raise CanvasException("Something went wrong", code=500)

    [Source: specs/data/error-response.schema.json - defines response format]
    """

    def __init__(
        self,
        message: str,
        code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize CanvasException.

        Args:
            message: Human-readable error message
            code: HTTP status code (default: 500)
            details: Additional error details (optional)

        # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
        """
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary format matching error-response.schema.json.

        Returns:
            Dictionary with code, message, and optional details

        [Source: specs/data/error-response.schema.json]
        """
        result: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class CanvasNotFoundError(CanvasException):
    """
    Exception raised when a Canvas file is not found.

    HTTP Status Code: 404

    Example:
        >>> raise CanvasNotFoundError("discrete_math")

    [Source: specs/api/fastapi-backend-api.openapi.yml - 404 response for canvas endpoints]
    """

    def __init__(
        self,
        canvas_name: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize CanvasNotFoundError.

        Args:
            canvas_name: Name of the canvas that was not found
            details: Additional error details (optional)

        # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
        """
        message = f"Canvas '{canvas_name}' not found"
        super().__init__(
            message=message,
            code=404,
            details=details or {"canvas_name": canvas_name},
        )
        self.canvas_name = canvas_name


class NodeNotFoundError(CanvasException):
    """
    Exception raised when a node is not found within a Canvas.

    HTTP Status Code: 404

    Example:
        >>> raise NodeNotFoundError("node-123", "discrete_math")

    [Source: specs/api/fastapi-backend-api.openapi.yml - 404 response for node endpoints]
    """

    def __init__(
        self,
        node_id: str,
        canvas_name: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize NodeNotFoundError.

        Args:
            node_id: ID of the node that was not found
            canvas_name: Name of the canvas containing the node
            details: Additional error details (optional)

        # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
        """
        message = f"Node '{node_id}' not found in canvas '{canvas_name}'"
        super().__init__(
            message=message,
            code=404,
            details=details or {"node_id": node_id, "canvas_name": canvas_name},
        )
        self.node_id = node_id
        self.canvas_name = canvas_name


class ValidationError(CanvasException):
    """
    Exception raised when request validation fails.

    HTTP Status Code: 400

    Example:
        >>> raise ValidationError("Invalid node color", field="color", value="invalid")

    [Source: specs/api/fastapi-backend-api.openapi.yml - 400 response for validation errors]
    [Source: specs/data/error-detail.schema.json - error detail format]
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize ValidationError.

        Args:
            message: Description of the validation error
            field: Name of the field that failed validation (optional)
            value: The invalid value (optional)
            details: Additional error details (optional)

        # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = value

        super().__init__(
            message=message,
            code=400,
            details=error_details if error_details else None,
        )
        self.field = field
        self.value = value


class AgentExecutionError(CanvasException):
    """
    Exception raised when an AI agent execution fails.

    HTTP Status Code: 500

    Example:
        >>> raise AgentExecutionError(
        ...     "Agent timed out",
        ...     agent_type="decomposition",
        ...     node_id="node-123"
        ... )

    [Source: specs/api/fastapi-backend-api.openapi.yml - 500 response for agent errors]
    """

    def __init__(
        self,
        message: str,
        agent_type: Optional[str] = None,
        node_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize AgentExecutionError.

        Args:
            message: Description of the agent error
            agent_type: Type of agent that failed (optional)
            node_id: ID of the node being processed (optional)
            details: Additional error details (optional)

        # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
        """
        error_details = details or {}
        if agent_type:
            error_details["agent_type"] = agent_type
        if node_id:
            error_details["node_id"] = node_id

        super().__init__(
            message=message,
            code=500,
            details=error_details if error_details else None,
        )
        self.agent_type = agent_type
        self.node_id = node_id
