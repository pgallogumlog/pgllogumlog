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
from web.api.compass import router as compass_router

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
        title="AI Readiness Compass",
        description="AI Readiness Assessment and Strategic Planning",
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
    app.include_router(tests_router, prefix="/api/tests", tags=["Tests"])
    app.include_router(compass_router, prefix="/api/compass", tags=["Compass"])

    # Static files and templates
    app.mount("/static", StaticFiles(directory="web/ui/static"), name="static")
    templates = Jinja2Templates(directory="web/ui/templates")

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """Home page with test runner UI."""
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "title": "AI Readiness Compass"},
        )

    @app.get("/test-runner", response_class=HTMLResponse)
    async def test_runner_ui(request: Request):
        """Test runner UI page."""
        return templates.TemplateResponse(
            "test_runner.html",
            {"request": request, "title": "Test Runner"},
        )

    @app.get("/submit", response_class=HTMLResponse)
    async def submit_form(request: Request):
        """AI Readiness Compass submission form (legacy route)."""
        return templates.TemplateResponse(
            "submit.html",
            {"request": request, "title": "AI Readiness Compass"},
        )

    @app.get("/compass", response_class=HTMLResponse)
    async def compass_form(request: Request):
        """AI Readiness Compass premium assessment form."""
        settings = get_settings()
        return templates.TemplateResponse(
            "compass.html",
            {
                "request": request,
                "title": "AI Readiness Compass",
                "stripe_publishable_key": settings.stripe_publishable_key,
                "price_dollars": settings.compass_price_cents / 100,
            },
        )

    return app


# Create the app instance
app = create_app()
