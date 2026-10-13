import stripe
from app.core.config import settings
from app.core.exceptions import AppException, ResponseCode, Message

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    def construct_webhook_event(self, payload: bytes, signature: str):
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise AppException(ResponseCode.SERVICE_UNAVAILABLE, "Stripe webhook is not configured")
        try:
            return stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except Exception as e:
            raise AppException(ResponseCode.BAD_REQUEST, "Invalid Stripe webhook", details={"error": str(e)})

    def create_checkout_session(
            self,
            service_name: str,
            amount_cents: int,
            success_url: str,
            cancel_url: str,
    ):
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                customer_creation="always",
                payment_intent_data={
                    "setup_future_usage": "off_session"
                },

                line_items=[{
                    "price_data": {
                        "currency": settings.PAYMENT_CURRENCY.lower(),
                        "product_data": {
                            "name": service_name,
                            "description": f"Payment for {service_name}",
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],

                success_url=success_url,
                cancel_url=cancel_url,

                expand=["payment_intent"],
            )

            return session

        except Exception as e:
            raise AppException(ResponseCode.SERVICE_UNAVAILABLE, Message.PAYMENT_GATEWAY_ERROR, details={"error": str(e)})

    def retrieve_session(self, session_id: str):
        try:
            return stripe.checkout.Session.retrieve(session_id)
        except Exception as e:
            raise AppException(ResponseCode.SERVICE_UNAVAILABLE, Message.PAYMENT_GATEWAY_ERROR, details={"error": str(e)})

stripe_service = StripeService()
