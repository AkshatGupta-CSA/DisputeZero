from fastapi import FastAPI, Request, HTTPException
import uvicorn
from core.security import mask_pii
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="Unified Revenue Retention Agent")

@app.post("/webhook")
async def receive_razorpay_webhook(request: Request):
    """
    The Omni-Trigger: Listens for incoming Razorpay webhooks.
    """
    try:
        # 1. Capture the raw JSON payload
        raw_payload = await request.json()
        
        # 2. Extract the event type
        event_type = raw_payload.get("event")
        
        # 3. Filter for the specific events we care about
        target_events = ["dispute.created", "subscription.charged.failed"]
        if event_type not in target_events:
            return {"status": "ignored", "message": f"Event {event_type} not tracked."}
        
        # 4. Scrub sensitive data (PII) before further processing
        secured_payload = mask_pii(raw_payload)
        
        # 5. Log the secure payload (Mocking the handover to Phase 2/3)
        print(f"\n--- INCOMING SECURE EVENT: {event_type} ---")
        print(secured_payload)
        print("-------------------------------------------\n")
        
        return {"status": "success", "message": f"Event {event_type} received and secured."}

    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

if __name__ == "__main__":
    print("Starting Omni-Trigger Webhook Listener on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
