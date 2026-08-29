import hmac
import hashlib
import uuid

class RazorpayPaymentAdapter:
    def __init__(self, key_id: str = None, key_secret: str = None, is_demo_mode: bool = True):
        self.key_id = key_id
        self.key_secret = key_secret
        self.is_demo_mode = is_demo_mode

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str, secret: str) -> bool:
        if self.is_demo_mode:
            return True
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

    def fetch_payment(self, payment_id: str) -> dict:
        if self.is_demo_mode:
            return {
                "id": payment_id,
                "status": "failed",
                "amount": 10000,
                "currency": "INR",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Payment failed due to customer reason",
                "method": "card"
            }
        return {} # Mock implementation for non-demo

    def create_payment_link(self, amount: int, customer_name: str, customer_email: str, customer_phone: str, notes: dict = None) -> dict:
        if self.is_demo_mode:
            link_id = f"plink_{uuid.uuid4().hex[:14]}"
            return {
                "id": link_id,
                "short_url": f"https://rzp.io/i/{link_id}",
                "amount": amount,
                "currency": "INR",
                "customer": {
                    "name": customer_name,
                    "email": customer_email,
                    "contact": customer_phone
                }
            }
        return {}

    def retry_payment(self, payment_id: str, order_id: str) -> dict:
        if self.is_demo_mode:
            return {
                "id": payment_id,
                "status": "created",
                "order_id": order_id
            }
        return {}
