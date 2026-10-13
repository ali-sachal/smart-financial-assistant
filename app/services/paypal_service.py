import requests
from requests.auth import HTTPBasicAuth
from app.core.config import settings
from app.core.exceptions import AppException, ResponseCode, Message
import logging

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self):
        self.mode = settings.PAYPAL_MODE
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_SECRET
        self.base_url = "https://api-m.sandbox.paypal.com" if self.mode == "sandbox" else "https://api-m.paypal.com"

    def get_access_token(self):
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {
            "grant_type": "client_credentials"
        }
        try:
            response = requests.post(
                url, 
                headers=headers, 
                data=data, 
                auth=HTTPBasicAuth(self.client_id, self.client_secret)
            )
            response.raise_for_status()
            return response.json()["access_token"]
        except Exception as e:
            logger.error(f"Failed to get PayPal access token: {e}")
            raise AppException(ResponseCode.SERVICE_UNAVAILABLE, Message.PAYMENT_GATEWAY_ERROR, details={"error": str(e)})

    def create_order(self, uuid: str, amount_cents: int, currency: str | None = None, return_url: str = "", cancel_url: str = ""):
        access_token = self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        # PayPal expects amount in standard units (e.g. 10.00), not cents
        amount_val = "{:.2f}".format(amount_cents / 100)
        currency = (currency or settings.PAYMENT_CURRENCY).upper()
        
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": str(uuid),
                    "amount": {
                        "currency_code": currency,
                        "value": amount_val
                    }
                }
            ],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "user_action": "PAY_NOW"
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create PayPal order: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"PayPal Response: {e.response.text}")
            raise AppException(ResponseCode.SERVICE_UNAVAILABLE, Message.PAYMENT_GATEWAY_ERROR, details={"error": str(e)})

    def capture_order(self, order_id: str):
        access_token = self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to capture PayPal order: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"PayPal Response: {e.response.text}")
            raise AppException(ResponseCode.SERVICE_UNAVAILABLE, Message.PAYMENT_GATEWAY_ERROR, details={"error": str(e)})

paypal_service = PayPalService()
