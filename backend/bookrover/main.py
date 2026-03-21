"""FastAPI application factory for BookRover.

Creates and configures the FastAPI instance, registers all routers,
and applies middleware. The Mangum handler wraps the app for AWS Lambda.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from bookrover.config import Settings


def create_app() -> FastAPI:
    """Create and configure the BookRover FastAPI application.

    Returns:
        Configured FastAPI instance with middleware and routers applied.
    """
    settings = Settings()

    app = FastAPI(
        title="BookRover API",
        version="0.1.0",
        description="Backend API for the BookRover door-to-door book selling management app.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers are registered here as features are built:
    from bookrover.routers import admin
    app.include_router(admin.router)

    return app


app = create_app()

# AWS Lambda entry point — Mangum translates API Gateway proxy events to ASGI.
handler = Mangum(app)
