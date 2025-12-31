"""
Stripe Payment Adapter for AI Readiness Compass.

Implements manual capture flow:
- Authorize upfront (hold funds)
- Capture after QA passes
- Cancel if QA fails

This protects customers from being charged for low-quality reports.
"""

import structlog
from dataclasses import dataclass
from typing import Optional

logger = structlog.get_logger()

# Stripe import - will be mocked in tests
try:
    import stripe
except ImportError:
    stripe = None  # Allow module to load without stripe for testing


@dataclass
class PaymentIntent:
    """Result from creating a payment intent."""
    id: str
    client_secret: str
    amount: int
    currency: str
    status: str
    capture_method: str


@dataclass
class PaymentResult:
    """Result from capture/cancel operations."""
    success: bool
    payment_intent_id: str
    status: str
    error: Optional[str] = None


class StripeAdapter:
    """
    Stripe payment adapter with manual capture support.

    Flow:
    1. create_payment_intent() - Authorize card, hold funds
    2. confirm_payment() - Customer confirms (handled by Stripe.js)
    3. capture_payment() - Charge after QA passes
    OR cancel_payment() - Release hold if QA fails
    """

    def __init__(
        self,
        secret_key: str,
        webhook_secret: str = "",
    ):
        """
        Initialize Stripe adapter.

        Args:
            secret_key: Stripe secret key (sk_test_... or sk_live_...)
            webhook_secret: Stripe webhook signing secret
        """
        self._secret_key = secret_key
        self._webhook_secret = webhook_secret

        if stripe:
            stripe.api_key = secret_key

    async def create_payment_intent(
        self,
        amount_cents: int,
        email: str,
        metadata: dict,
        currency: str = "usd",
    ) -> PaymentIntent:
        """
        Create a payment intent with manual capture.

        This authorizes the card but does NOT charge it.
        Funds are held until capture() or cancel() is called.

        Args:
            amount_cents: Amount in cents (e.g., 49700 for $497)
            email: Customer email for receipt
            metadata: Additional data (run_id, company_name, etc.)
            currency: Currency code (default: usd)

        Returns:
            PaymentIntent with client_secret for frontend
        """
        logger.info(
            "creating_payment_intent",
            amount_cents=amount_cents,
            email=email,
            metadata=metadata,
        )

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                capture_method="manual",  # Key: authorize only
                receipt_email=email,
                metadata=metadata,
                automatic_payment_methods={"enabled": True},
            )

            result = PaymentIntent(
                id=intent.id,
                client_secret=intent.client_secret,
                amount=intent.amount,
                currency=intent.currency,
                status=intent.status,
                capture_method=intent.capture_method,
            )

            logger.info(
                "payment_intent_created",
                payment_intent_id=result.id,
                status=result.status,
            )

            return result

        except stripe.error.StripeError as e:
            logger.error(
                "payment_intent_creation_failed",
                error=str(e),
                email=email,
            )
            raise

    async def capture_payment(self, payment_intent_id: str) -> PaymentResult:
        """
        Capture a previously authorized payment.

        Call this AFTER QA validation passes to charge the customer.

        Args:
            payment_intent_id: ID from create_payment_intent()

        Returns:
            PaymentResult with success status
        """
        logger.info(
            "capturing_payment",
            payment_intent_id=payment_intent_id,
        )

        try:
            intent = stripe.PaymentIntent.capture(payment_intent_id)

            result = PaymentResult(
                success=intent.status == "succeeded",
                payment_intent_id=intent.id,
                status=intent.status,
            )

            logger.info(
                "payment_captured",
                payment_intent_id=payment_intent_id,
                status=result.status,
                success=result.success,
            )

            return result

        except stripe.error.StripeError as e:
            logger.error(
                "payment_capture_failed",
                payment_intent_id=payment_intent_id,
                error=str(e),
            )
            return PaymentResult(
                success=False,
                payment_intent_id=payment_intent_id,
                status="failed",
                error=str(e),
            )

    async def cancel_payment(self, payment_intent_id: str) -> PaymentResult:
        """
        Cancel a payment intent and release held funds.

        Call this if QA validation fails - customer is NOT charged.

        Args:
            payment_intent_id: ID from create_payment_intent()

        Returns:
            PaymentResult with success status
        """
        logger.info(
            "canceling_payment",
            payment_intent_id=payment_intent_id,
        )

        try:
            intent = stripe.PaymentIntent.cancel(payment_intent_id)

            result = PaymentResult(
                success=intent.status == "canceled",
                payment_intent_id=intent.id,
                status=intent.status,
            )

            logger.info(
                "payment_canceled",
                payment_intent_id=payment_intent_id,
                status=result.status,
                success=result.success,
            )

            return result

        except stripe.error.StripeError as e:
            logger.error(
                "payment_cancel_failed",
                payment_intent_id=payment_intent_id,
                error=str(e),
            )
            return PaymentResult(
                success=False,
                payment_intent_id=payment_intent_id,
                status="failed",
                error=str(e),
            )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> dict:
        """
        Verify Stripe webhook signature and parse event.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header value

        Returns:
            Parsed webhook event

        Raises:
            stripe.error.SignatureVerificationError: If signature invalid
        """
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            self._webhook_secret,
        )
        return event

    async def get_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """
        Retrieve a payment intent by ID.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            PaymentIntent with current status
        """
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        return PaymentIntent(
            id=intent.id,
            client_secret=intent.client_secret,
            amount=intent.amount,
            currency=intent.currency,
            status=intent.status,
            capture_method=intent.capture_method,
        )
