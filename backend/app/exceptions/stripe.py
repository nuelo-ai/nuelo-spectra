"""Custom exceptions for Stripe payment operations."""


class StripeConfigError(Exception):
    """Stripe is not configured (missing API keys)."""
    pass


class StripeWebhookError(Exception):
    """Webhook signature verification or processing failed."""
    pass


class PaymentError(Exception):
    """Payment-related business logic error (declined, invalid state, etc.)."""
    def __init__(self, message: str, code: str = "payment_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class CheckoutValidationError(Exception):
    """Pre-checkout validation failed (wrong tier, already subscribed, trial user top-up, etc.)."""
    def __init__(self, message: str, code: str = "checkout_validation_error"):
        self.message = message
        self.code = code
        super().__init__(message)
