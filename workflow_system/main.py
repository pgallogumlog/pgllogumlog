"""
Workflow Automation System - Main Entry Point.

Run with: python main.py
Or: uvicorn main:app --reload

The application will be available at http://localhost:8000
"""

import sys
from pathlib import Path



# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
import structlog

from config import get_settings
from web.app import app


def configure_logging():
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def main():
    """Main entry point."""
    configure_logging()
    settings = get_settings()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          Workflow Automation System v1.0.0                  ║
╠══════════════════════════════════════════════════════════════╣
║  Environment: {settings.app_env:<44} ║
║  Server:      http://{settings.app_host}:{settings.app_port:<33} ║
║  API Docs:    http://{settings.app_host}:{settings.app_port}/docs{' ' * 27} ║
╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "web.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level="info" if settings.is_development else "warning",
    )


if __name__ == "__main__":
    main()
