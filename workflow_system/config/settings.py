"""
Application Settings - Loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===================
    # AI Provider (Claude)
    # ===================
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # ===================
    # Google OAuth
    # ===================
    google_credentials_file: str = Field(
        default="config/google_credentials.json",
        description="Path to Google OAuth credentials JSON for Gmail",
    )
    google_sheets_credentials_file: str = Field(
        default="config/google_service_account.json",
        description="Path to Google Service Account credentials JSON for Sheets",
    )
    gmail_user_email: str = Field(default="", description="Gmail account to monitor")
    gmail_poll_interval_seconds: int = Field(default=60, description="Email poll interval")

    # ===================
    # SMTP Email Settings
    # ===================
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port (587 for TLS, 465 for SSL)")
    smtp_user: str = Field(default="", description="SMTP username (usually your email)")
    smtp_password: str = Field(default="", description="SMTP password (Gmail App Password)")
    smtp_from_email: str = Field(default="", description="From email address (defaults to smtp_user)")
    smtp_use_tls: bool = Field(default=True, description="Use TLS (True for port 587)")

    # ===================
    # Workflow Result Delivery
    # ===================
    auto_send_workflow_emails: bool = Field(
        default=True,
        description="Automatically send workflow results via email"
    )
    workflow_result_email: str = Field(
        default="pgallogumlog@gmail.com",
        description="Email address for workflow results"
    )

    # ===================
    # Google Sheets
    # ===================
    google_sheets_qa_log_id: str = Field(default="", description="QA Logs spreadsheet ID")
    google_sheets_config_id: str = Field(default="", description="Config spreadsheet ID")

    # ===================
    # Application
    # ===================
    app_env: str = Field(default="development", description="Environment name")
    app_debug: bool = Field(default=True, description="Debug mode")
    app_host: str = Field(default="127.0.0.1", description="Server host")
    app_port: int = Field(default=8000, description="Server port")

    # ===================
    # Database
    # ===================
    database_url: str = Field(
        default="sqlite+aiosqlite:///data/workflow_system.db",
        description="Database connection URL",
    )

    # ===================
    # Self-Consistency Engine
    # ===================
    sc_temperatures: str = Field(
        default="0.3,0.5,0.7,0.85,1.0",
        description="Comma-separated temperature values (0-1 range)",
    )
    sc_min_consensus_votes: int = Field(
        default=3, description="Minimum votes for consensus (60% of 5 responses)"
    )
    sc_model: str = Field(
        default="claude-sonnet-4-20250514", description="Claude model for SC engine"
    )

    # ===================
    # QA Auditor
    # ===================
    qa_model: str = Field(
        default="claude-sonnet-4-20250514", description="Claude model for QA"
    )
    qa_min_pass_score: int = Field(default=7, description="Minimum score to pass QA")

    # ===================
    # QA Call Capture
    # ===================
    qa_run_probabilistic: bool = Field(
        default=True, description="Run probabilistic validators (relevance, hallucination)"
    )
    qa_probabilistic_sample_rate: float = Field(
        default=1.0, description="Fraction of calls to run probabilistic checks on (0.0-1.0)"
    )
    qa_call_log_sheet: str = Field(
        default="AI Call Log", description="Sheet name for per-call QA logs"
    )
    qa_summary_sheet: str = Field(
        default="Workflow QA Summary", description="Sheet name for workflow QA summaries"
    )
    qa_enable_capture: bool = Field(
        default=True, description="Enable AI call capture for QA"
    )

    # ===================
    # Test Runner
    # ===================
    test_runner_default_tier: str = Field(default="Standard", description="Default tier")
    test_runner_max_parallel: int = Field(
        default=5, description="Max parallel test executions"
    )

    @property
    def temperatures(self) -> List[float]:
        """Parse temperature string into list of floats."""
        return [float(t.strip()) for t in self.sc_temperatures.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()
