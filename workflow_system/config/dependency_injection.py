"""
Dependency Injection Container.
Provides factory functions for creating service instances with proper dependencies.
This enables easy mocking in tests.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol, runtime_checkable

from config.settings import Settings, get_settings


# ===================
# Abstract Interfaces (Protocols)
# ===================


@runtime_checkable
class AIProvider(Protocol):
    """Interface for AI providers (Claude, etc.)."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a response from the AI model."""
        ...

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> dict:
        """Generate a JSON response from the AI model."""
        ...

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> tuple[str, dict]:
        """Generate a response with full metadata for QA capture."""
        ...

    async def generate_json_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> tuple[dict, dict]:
        """Generate a JSON response with full metadata for QA capture."""
        ...

    async def generate_parallel(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperatures: list[float] | None = None,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> list[str]:
        """Generate multiple responses in parallel with different temperatures."""
        ...

    async def generate_parallel_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperatures: list[float] | None = None,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> list[tuple[str, dict]]:
        """Generate multiple responses in parallel with metadata."""
        ...


@runtime_checkable
class EmailClient(Protocol):
    """Interface for email operations."""

    async def fetch_unread(self) -> list[dict]:
        """Fetch unread emails."""
        ...

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
    ) -> bool:
        """Send an email."""
        ...

    async def mark_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        ...


@runtime_checkable
class SheetsClient(Protocol):
    """Interface for Google Sheets operations."""

    async def append_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        values: list,
    ) -> bool:
        """Append a row to a sheet."""
        ...

    async def read_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> list[dict]:
        """Read all rows from a sheet."""
        ...


@runtime_checkable
class PaymentClient(Protocol):
    """Interface for payment operations (Stripe)."""

    async def create_payment_intent(
        self,
        amount_cents: int,
        email: str,
        metadata: dict,
    ) -> object:
        """Create a payment intent with manual capture."""
        ...

    async def capture_payment(self, payment_intent_id: str) -> object:
        """Capture an authorized payment."""
        ...

    async def cancel_payment(self, payment_intent_id: str) -> object:
        """Cancel a payment intent and release hold."""
        ...

    async def get_payment_intent(self, payment_intent_id: str) -> object:
        """Retrieve a payment intent by ID."""
        ...

    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """Verify Stripe webhook signature and return event."""
        ...


# ===================
# Dependency Container
# ===================


class Container:
    """
    Dependency Injection Container.

    Usage:
        container = Container(settings)
        ai = container.ai_provider()
        email = container.email_client()

    For testing:
        container = Container(settings)
        container.override_ai_provider(MockAIProvider())
    """

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._overrides: dict = {}

    def override(self, name: str, instance: object) -> None:
        """Override a dependency with a custom instance (for testing)."""
        self._overrides[name] = instance

    def clear_overrides(self) -> None:
        """Clear all dependency overrides."""
        self._overrides.clear()

    @property
    def settings(self) -> Settings:
        """Get application settings."""
        return self._settings

    def ai_provider(self) -> AIProvider:
        """Get AI provider instance."""
        if "ai_provider" in self._overrides:
            return self._overrides["ai_provider"]

        from infrastructure.ai.claude_adapter import ClaudeAdapter

        return ClaudeAdapter(
            api_key=self._settings.anthropic_api_key,
            default_model=self._settings.sc_model,
        )

    def capturing_ai_provider(
        self,
        run_id: str,
        run_probabilistic: bool = True,
        probabilistic_sample_rate: float = 1.0,
    ) -> AIProvider:
        """
        Get AI provider instance wrapped with QA capture.

        Creates a CapturingAIAdapter that intercepts all AI calls,
        captures inputs/outputs, and runs validation pipeline.

        Args:
            run_id: Unique identifier for this workflow run
            run_probabilistic: Whether to run probabilistic validators
            probabilistic_sample_rate: Fraction of calls to run probabilistic checks on

        Returns:
            CapturingAIAdapter wrapping the base AI provider
        """
        if "ai_provider" in self._overrides:
            base_provider = self._overrides["ai_provider"]
        else:
            from infrastructure.ai.claude_adapter import ClaudeAdapter

            base_provider = ClaudeAdapter(
                api_key=self._settings.anthropic_api_key,
                default_model=self._settings.sc_model,
            )

        from contexts.qa.scoring import ValidationPipeline
        from infrastructure.ai.capturing_adapter import CapturingAIAdapter

        # Create validation pipeline
        pipeline = ValidationPipeline(
            ai_provider=base_provider,
            run_probabilistic=run_probabilistic,
            probabilistic_sample_rate=probabilistic_sample_rate,
        )

        return CapturingAIAdapter(
            wrapped=base_provider,
            run_id=run_id,
            validation_pipeline=pipeline,
            enable_capture=True,
            min_pass_score=self._settings.qa_min_pass_score,
        )

    def email_client(self) -> EmailClient:
        """Get email client instance."""
        if "email_client" in self._overrides:
            return self._overrides["email_client"]

        from infrastructure.email.smtp_adapter import SMTPAdapter

        return SMTPAdapter(
            smtp_host=self._settings.smtp_host,
            smtp_port=self._settings.smtp_port,
            smtp_user=self._settings.smtp_user,
            smtp_password=self._settings.smtp_password,
            from_email=self._settings.smtp_from_email or self._settings.smtp_user,
            use_tls=self._settings.smtp_use_tls,
        )

    def sheets_client(self) -> SheetsClient:
        """Get Google Sheets client instance."""
        if "sheets_client" in self._overrides:
            return self._overrides["sheets_client"]

        from infrastructure.storage.sheets_adapter import SheetsAdapter

        return SheetsAdapter(
            credentials_file=self._settings.google_sheets_credentials_file,
        )

    def payment_client(self) -> PaymentClient:
        """Get payment client instance (Stripe)."""
        if "payment_client" in self._overrides:
            return self._overrides["payment_client"]

        from infrastructure.payments.stripe_adapter import StripeAdapter

        return StripeAdapter(
            secret_key=self._settings.stripe_secret_key,
            webhook_secret=self._settings.stripe_webhook_secret,
        )

    def compass_sheets_logger(self):
        """
        Get Compass QA sheets logger instance.

        Returns a logger that writes QA validation results to Google Sheets.
        Logs to two sheets:
        - "Compass AI Call Log": Per-call validation details
        - "Compass QA Summary": Per-run summaries
        """
        if "compass_sheets_logger" in self._overrides:
            return self._overrides["compass_sheets_logger"]

        # Return None if no spreadsheet ID configured
        spreadsheet_id = self._settings.google_sheets_qa_log_id
        if not spreadsheet_id:
            return None

        from contexts.compass.sheets_logger import CompassQASheetsLogger

        return CompassQASheetsLogger(
            sheets_client=self.sheets_client(),
            spreadsheet_id=spreadsheet_id,
        )


# Global container instance
@lru_cache
def get_container() -> Container:
    """Get cached container instance."""
    return Container()
