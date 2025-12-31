"""
Unit tests for Compass API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from web.app import create_app


class MockPaymentIntent:
    """Mock Stripe PaymentIntent."""

    def __init__(
        self,
        id: str = "pi_test123",
        client_secret: str = "pi_test123_secret",
        amount: int = 49700,
        currency: str = "usd",
    ):
        self.id = id
        self.client_secret = client_secret
        self.amount = amount
        self.currency = currency
        self.capture_method = "manual"


class MockPaymentClient:
    """Mock payment client for testing."""

    def __init__(self):
        self.create_payment_intent = AsyncMock(
            return_value=MockPaymentIntent()
        )
        self.capture_payment = AsyncMock()
        self.cancel_payment = AsyncMock()
        self.get_payment_intent = AsyncMock()
        self.verify_webhook_signature = MagicMock(return_value={"type": "test"})


class MockSettings:
    """Mock settings for testing."""

    compass_price_cents = 49700
    compass_test_mode = False  # Test production mode behavior
    stripe_secret_key = "sk_test_fake"
    stripe_webhook_secret = "whsec_fake"
    stripe_publishable_key = "pk_test_fake"
    app_env = "test"
    app_debug = True
    app_host = "127.0.0.1"
    app_port = 8000


@pytest.fixture
def mock_payment_client():
    """Create mock payment client."""
    return MockPaymentClient()


@pytest.fixture
def mock_container(mock_payment_client):
    """Create mock container with payment client."""
    container = MagicMock()
    container.settings = MockSettings()
    container.payment_client.return_value = mock_payment_client
    return container


@pytest.fixture
def test_client(mock_container):
    """Create test client with mocked dependencies."""
    with patch("web.api.compass.get_container", return_value=mock_container):
        app = create_app()
        yield TestClient(app)


class TestCompassPriceEndpoint:
    """Tests for /api/compass/price endpoint."""

    def test_returns_price_info(self, test_client, mock_container):
        """Should return compass price information."""
        with patch("web.api.compass.get_container", return_value=mock_container):
            response = test_client.get("/api/compass/price")

        assert response.status_code == 200
        data = response.json()
        assert data["amount_cents"] == 49700
        assert data["amount_dollars"] == 497.0
        assert data["currency"] == "usd"
        assert data["product"] == "AI Readiness Compass"


class TestCreatePaymentIntentEndpoint:
    """Tests for /api/compass/create-payment-intent endpoint."""

    def test_creates_payment_intent(self, test_client, mock_container, mock_payment_client):
        """Should create a payment intent with manual capture."""
        with patch("web.api.compass.get_container", return_value=mock_container):
            response = test_client.post(
                "/api/compass/create-payment-intent",
                json={"email": "test@example.com"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "client_secret" in data
        assert "payment_intent_id" in data
        assert data["amount"] == 49700
        assert data["currency"] == "usd"

    def test_calls_payment_client(self, test_client, mock_container, mock_payment_client):
        """Should call payment client with correct parameters."""
        with patch("web.api.compass.get_container", return_value=mock_container):
            test_client.post(
                "/api/compass/create-payment-intent",
                json={"email": "test@example.com"},
            )

        mock_payment_client.create_payment_intent.assert_called_once()
        call_kwargs = mock_payment_client.create_payment_intent.call_args[1]
        assert call_kwargs["amount_cents"] == 49700
        assert call_kwargs["email"] == "test@example.com"


class TestCompassSubmitEndpoint:
    """Tests for /api/compass/submit endpoint."""

    def test_accepts_valid_submission(self, test_client, mock_container, mock_payment_client):
        """Should accept valid compass submission."""
        with patch("web.api.compass.get_container", return_value=mock_container):
            response = test_client.post(
                "/api/compass/submit",
                json={
                    "company_name": "Acme Corp",
                    "website": "https://acme.com",
                    "industry": "Technology",
                    "company_size": "50-200",
                    "data_maturity": 3,
                    "automation_experience": 4,
                    "change_readiness": 3,
                    "pain_point": "Customer support overload",
                    "description": "We're drowning in support tickets",
                    "email": "ceo@acme.com",
                    "contact_name": "John Smith",
                    "payment_method_id": "pm_test123",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["run_id"].startswith("compass-")
        assert data["status"] == "payment_authorized"

    def test_validates_self_assessment_range(self, test_client, mock_container):
        """Should reject invalid self-assessment scores."""
        with patch("web.api.compass.get_container", return_value=mock_container):
            response = test_client.post(
                "/api/compass/submit",
                json={
                    "company_name": "Acme Corp",
                    "industry": "Technology",
                    "company_size": "50-200",
                    "data_maturity": 6,  # Invalid: > 5
                    "automation_experience": 4,
                    "change_readiness": 3,
                    "pain_point": "Test",
                    "description": "Test",
                    "email": "test@example.com",
                    "contact_name": "Test",
                    "payment_method_id": "pm_test",
                },
            )

        assert response.status_code == 422  # Validation error

    def test_validates_required_fields(self, test_client, mock_container):
        """Should reject submission missing required fields."""
        with patch("web.api.compass.get_container", return_value=mock_container):
            response = test_client.post(
                "/api/compass/submit",
                json={
                    "company_name": "Acme Corp",
                    # Missing other required fields
                },
            )

        assert response.status_code == 422


class TestCompassStatusEndpoint:
    """Tests for /api/compass/status endpoint."""

    def test_returns_status(self, test_client, mock_container):
        """Should return status for a run_id."""
        with patch("web.api.compass.get_container", return_value=mock_container):
            response = test_client.get("/api/compass/status/compass-test123")

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "compass-test123"
        assert "status" in data


class TestWebhookEndpoint:
    """Tests for /api/compass/webhook endpoint."""

    def test_handles_webhook(self, test_client, mock_container, mock_payment_client):
        """Should handle Stripe webhook events."""
        mock_payment_client.verify_webhook_signature.return_value = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "metadata": {"run_id": "compass-test123"},
                }
            },
        }

        with patch("web.api.compass.get_container", return_value=mock_container):
            response = test_client.post(
                "/api/compass/webhook",
                content=b'{"test": "data"}',
                headers={"stripe-signature": "sig_test"},
            )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
