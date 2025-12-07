"""
FastAPI Application Entry Point for Canvas Learning System

Provides the main FastAPI application with:
- OpenAPI documentation at /docs (Swagger UI) and /redoc (ReDoc)
- CORS middleware configuration
- All API routers registered

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: FastAPI application initialization)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import (
    agents_router,
    canvas_router,
    health_router,
    review_router,
)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: application initialization)

    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()

    # Create FastAPI application with OpenAPI configuration
    # Source: specs/api/fastapi-backend-api.openapi.yml
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        # OpenAPI docs configuration
        docs_url="/docs" if settings.DEBUG else "/docs",  # Always enable for testing
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
        # OpenAPI metadata
        openapi_tags=[
            {
                "name": "System",
                "description": "系统健康检查"
            },
            {
                "name": "Canvas",
                "description": "Canvas文件和节点操作"
            },
            {
                "name": "Agents",
                "description": "AI Agent调用接口"
            },
            {
                "name": "Review",
                "description": "艾宾浩斯复习系统"
            }
        ],
        contact={
            "name": "Canvas Learning System",
            "url": "https://github.com/canvas-learning-system"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    )

    # Configure CORS middleware
    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: CORS middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers with API version prefix
    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: include_router)
    app.include_router(health_router, prefix=settings.API_V1_PREFIX)
    app.include_router(canvas_router, prefix=settings.API_V1_PREFIX)
    app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
    app.include_router(review_router, prefix=settings.API_V1_PREFIX)

    # Root endpoint - defined inside create_app to be included in test app
    @app.get("/", tags=["System"])
    async def root():
        """
        Root endpoint returning API information.

        Returns basic API info for discovery purposes.
        """
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/api/v1/openapi.json"
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
