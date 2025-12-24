"""
FastAPI Application.

Main web application setup with routes and middleware.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import get_container, get_settings
from web.api.health import router as health_router
from web.api.tests import router as tests_router
from web.api.workflows import router as workflows_router
from web.api.qa_dashboard import router as qa_dashboard_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    settings = get_settings()
    logger.info(
        "application_starting",
        env=settings.app_env,
        host=settings.app_host,
        port=settings.app_port,
    )
    yield
    logger.info("application_shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Workflow Automation System",
        description="AI Workflow Proposal System with Self-Consistency Voting",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.app_debug,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(health_router, prefix="/api", tags=["Health"])
    app.include_router(workflows_router, prefix="/api/workflows", tags=["Workflows"])
    app.include_router(tests_router, prefix="/api/tests", tags=["Tests"])
    app.include_router(qa_dashboard_router)

    # Static files and templates
    app.mount("/static", StaticFiles(directory="web/ui/static"), name="static")
    templates = Jinja2Templates(directory="web/ui/templates")

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """Home page with test runner UI."""
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "title": "Workflow Automation System"},
        )

    @app.get("/test-runner", response_class=HTMLResponse)
    async def test_runner_ui(request: Request):
        """Test runner UI page."""
        return templates.TemplateResponse(
            "test_runner.html",
            {"request": request, "title": "Test Runner"},
        )

    @app.get("/qa-dashboard", response_class=HTMLResponse)
    async def qa_dashboard_ui(request: Request):
        """QA Dashboard UI page."""
        return templates.TemplateResponse(
            "qa_dashboard.html",
            {"request": request, "title": "QA Dashboard"},
        )

    return app


# Create the app instance
app = create_app()
