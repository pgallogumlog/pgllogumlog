"""
Unit tests for Stripe Payment Adapter.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from infrastructure.payments.stripe_adapter import (
    StripeAdapter,
    PaymentIntent,
    PaymentResult,
)


class MockStripePaymentIntent:
    """Mock Stripe PaymentIntent object."""

    def __init__(
        self,
        id: str = "pi_test123",
        client_secret: str = "pi_test123_secret",
        amount: int = 49700,
        currency: str = "usd",
        status: str = "requires_capture",
        capture_method: str = "manual",
    ):
        self.id = id
        self.client_secret = client_secret
        self.amount = amount
        self.currency = currency
        self.status = status
        self.capture_method = capture_method


class MockStripeError(Exception):
    """Mock Stripe error."""
    pass


@pytest.fixture
def mock_stripe():
    """Create mock stripe module."""
    with patch("infrastructure.payments.stripe_adapter.stripe") as mock:
        mock.error = MagicMock()
        mock.error.StripeError = MockStripeError
        yield mock


@pytest.fixture
def adapter(mock_stripe):
    """Create adapter with mocked stripe."""
    return StripeAdapter(
        secret_key="sk_test_fake",
        webhook_secret="whsec_fake",
    )


class TestStripeAdapter:
    """Tests for StripeAdapter."""

    @pytest.mark.asyncio
    async def test_create_payment_intent_uses_manual_capture(self, adapter, mock_stripe):
        """Should create intent with capture_method='manual'."""
        mock_stripe.PaymentIntent.create.return_value = MockStripePaymentIntent()

        result = await adapter.create_payment_intent(
            amount_cents=49700,
            email="test@example.com",
            metadata={"run_id": "compass-123"},
        )

        # Verify manual capture was used
        mock_stripe.PaymentIntent.create.assert_called_once()
        call_kwargs = mock_stripe.PaymentIntent.create.call_args[1]
        assert call_kwargs["capture_method"] == "manual"
        assert call_kwargs["amount"] == 49700
        assert call_kwargs["receipt_email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_create_payment_intent_returns_payment_intent(self, adapter, mock_stripe):
        """Should return PaymentIntent dataclass."""
        mock_stripe.PaymentIntent.create.return_value = MockStripePaymentIntent(
            id="pi_abc123",
            client_secret="pi_abc123_secret",
            amount=49700,
        )

        result = await adapter.create_payment_intent(
            amount_cents=49700,
            email="test@example.com",
            metadata={},
        )

        assert isinstance(result, PaymentIntent)
        assert result.id == "pi_abc123"
        assert result.client_secret == "pi_abc123_secret"
        assert result.amount == 49700
        assert result.capture_method == "manual"

    @pytest.mark.asyncio
    async def test_capture_payment_success(self, adapter, mock_stripe):
        """Should capture payment and return success."""
        mock_stripe.PaymentIntent.capture.return_value = MockStripePaymentIntent(
            id="pi_test",
            status="succeeded",
        )

        result = await adapter.capture_payment("pi_test")

        assert isinstance(result, PaymentResult)
        assert result.success is True
        assert result.status == "succeeded"
        assert result.payment_intent_id == "pi_test"
        mock_stripe.PaymentIntent.capture.assert_called_once_with("pi_test")

    @pytest.mark.asyncio
    async def test_capture_payment_failure(self, adapter, mock_stripe):
        """Should handle capture failure gracefully."""
        mock_stripe.PaymentIntent.capture.side_effect = MockStripeError("Card declined")

        result = await adapter.capture_payment("pi_test")

        assert result.success is False
        assert result.status == "failed"
        assert "Card declined" in result.error

    @pytest.mark.asyncio
    async def test_cancel_payment_success(self, adapter, mock_stripe):
        """Should cancel payment and release hold."""
        mock_stripe.PaymentIntent.cancel.return_value = MockStripePaymentIntent(
            id="pi_test",
            status="canceled",
        )

        result = await adapter.cancel_payment("pi_test")

        assert result.success is True
        assert result.status == "canceled"
        mock_stripe.PaymentIntent.cancel.assert_called_once_with("pi_test")

    @pytest.mark.asyncio
    async def test_cancel_payment_failure(self, adapter, mock_stripe):
        """Should handle cancel failure gracefully."""
        mock_stripe.PaymentIntent.cancel.side_effect = MockStripeError("Already captured")

        result = await adapter.cancel_payment("pi_test")

        assert result.success is False
        assert result.status == "failed"
        assert "Already captured" in result.error

    @pytest.mark.asyncio
    async def test_get_payment_intent(self, adapter, mock_stripe):
        """Should retrieve payment intent by ID."""
        mock_stripe.PaymentIntent.retrieve.return_value = MockStripePaymentIntent(
            id="pi_retrieve_test",
            status="requires_capture",
        )

        result = await adapter.get_payment_intent("pi_retrieve_test")

        assert isinstance(result, PaymentIntent)
        assert result.id == "pi_retrieve_test"
        mock_stripe.PaymentIntent.retrieve.assert_called_once_with("pi_retrieve_test")

    def test_verify_webhook_signature(self, adapter, mock_stripe):
        """Should verify webhook signature."""
        mock_event = {"type": "payment_intent.succeeded", "data": {}}
        mock_stripe.Webhook.construct_event.return_value = mock_event

        result = adapter.verify_webhook_signature(
            payload=b'{"test": "data"}',
            signature="sig_test",
        )

        assert result == mock_event
        mock_stripe.Webhook.construct_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_amount_passed_correctly(self, adapter, mock_stripe):
        """Should pass correct amount for $497 product."""
        mock_stripe.PaymentIntent.create.return_value = MockStripePaymentIntent()

        await adapter.create_payment_intent(
            amount_cents=49700,  # $497.00
            email="test@example.com",
            metadata={},
        )

        call_kwargs = mock_stripe.PaymentIntent.create.call_args[1]
        assert call_kwargs["amount"] == 49700

    @pytest.mark.asyncio
    async def test_metadata_passed_to_stripe(self, adapter, mock_stripe):
        """Should pass metadata to Stripe."""
        mock_stripe.PaymentIntent.create.return_value = MockStripePaymentIntent()

        metadata = {
            "run_id": "compass-abc123",
            "company_name": "Acme Corp",
            "tier": "premium",
        }

        await adapter.create_payment_intent(
            amount_cents=49700,
            email="ceo@acme.com",
            metadata=metadata,
        )

        call_kwargs = mock_stripe.PaymentIntent.create.call_args[1]
        assert call_kwargs["metadata"] == metadata
