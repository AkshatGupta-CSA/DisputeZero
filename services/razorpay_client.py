def get_mock_shopify_data(payment_id: str) -> dict:
    """
    Simulates fetching the original order invoice from Shopify.
    """
    return {
        "platform": "Shopify",
        "order_id": f"ORD_{payment_id[-6:]}",
        "customer_name": "Rahul Sharma",
        "items": [
            {"name": "Wireless Noise-Cancelling Headphones", "price": 4999, "qty": 1}
        ],
        "shipping_address": "Koramangala, Bangalore, Karnataka",
        "order_status": "fulfilled"
    }

def get_mock_delhivery_data(payment_id: str) -> dict:
    """
    Simulates fetching the proof of delivery from a logistics partner.
    """
    return {
        "logistics_partner": "Delhivery",
        "tracking_id": f"AWB_{payment_id[-8:]}",
        "status": "Delivered",
        "delivery_date": "2026-08-18T14:30:00Z",
        "signed_by": "Rahul S.",
        "delivery_ip": "115.97.104.22" # Crucial evidence for dispute defense
    }

def get_mock_subscription_context() -> dict:
    """
    Simulates fetching the user's subscription failure context.
    """
    return {
        "plan_name": "Pro Annual Plan",
        "failure_reason": "insufficient_funds",
        "customer_lifetime_value": 15000,
        "negotiation_leverage": "High" # Tells the LLM it's worth offering a discount/pause
    }
