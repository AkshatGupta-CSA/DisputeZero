from pydantic import BaseModel
from typing import Any, Dict, Optional

class RazorpayWebhook(BaseModel):
    """
    Defines the exact shape we expect from Razorpay's webhook payload.
    If Razorpay (or a bad actor) sends something else, FastAPI instantly rejects it.
    """
    account_id: str
    event: str
    payload: Dict[str, Any]
    created_at: Optional[int] = None
