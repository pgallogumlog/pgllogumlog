"""
Payment Infrastructure for AI Readiness Compass.

Stripe integration with manual capture flow:
1. Create PaymentIntent with capture_method='manual' (authorize only)
2. Process report and run QA
3. If QA passes: capture_payment() to charge
4. If QA fails: cancel_payment() to release hold
"""

from infrastructure.payments.stripe_adapter import StripeAdapter

__all__ = ["StripeAdapter"]
