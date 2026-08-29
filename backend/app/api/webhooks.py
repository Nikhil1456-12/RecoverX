"""Webhook endpoints for Razorpay integration."""
from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import json
import logging

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhook events."""
    if settings.is_demo_mode:
        body = await request.json()
        logger.info(f"Webhook received (DEMO MODE): {body.get('event', 'unknown')}")
        return {"status": "ok", "mode": "demo"}
    
    # Production webhook verification
    body = await request.body()
    signature = request.headers.get('x-razorpay-signature', '')
    
    if settings.RAZORPAY_WEBHOOK_SECRET:
        expected = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    payload = json.loads(body)
    event = payload.get('event', '')
    
    logger.info(f"Razorpay webhook: {event}")
    
    # Handle events
    if event == 'payment.failed':
        # Process failed payment
        pass
    elif event == 'payment.captured':
        # Process successful payment
        pass
    
    return {"status": "ok"}
