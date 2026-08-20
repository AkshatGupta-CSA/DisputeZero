from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from core.security import mask_pii
from dotenv import load_dotenv
import os
import webbrowser
import threading
import time

# Load environment variables
load_dotenv()

app = FastAPI(title="Unified Revenue Retention Agent")

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Revenue Retention Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e2e;
            color: #cdd6f4;
            margin: 0;
            padding: 40px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 600px;
        }
        h1 {
            color: #f5c2e7;
            text-align: center;
            margin-bottom: 5px;
        }
        p.subtitle {
            color: #a6adc8;
            text-align: center;
            margin-bottom: 30px;
        }
        .card {
            background-color: #313244;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            border: 1px solid #45475a;
        }
        button {
            display: block;
            width: 100%;
            padding: 12px;
            margin: 12px 0;
            border: none;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
        }
        button:active {
            transform: scale(0.98);
        }
        .btn-failed { background-color: #f38ba8; color: #11111b; }
        .btn-failed:hover { opacity: 0.9; }
        .btn-dispute { background-color: #fab387; color: #11111b; }
        .btn-dispute:hover { opacity: 0.9; }
        .btn-halted { background-color: #a6e3a1; color: #11111b; }
        .btn-halted:hover { opacity: 0.9; }
        
        .logs-container {
            background-color: #11111b;
            border-radius: 8px;
            padding: 15px;
            height: 200px;
            overflow-y: auto;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            color: #89b4fa;
            border: 1px solid #45475a;
        }
        .log-entry {
            margin-bottom: 8px;
            white-space: pre-wrap;
        }
        .log-time { color: #a6adc8; }
        .log-error { color: #f38ba8; }
        .log-success { color: #a6e3a1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Unified Revenue Retention Agent</h1>
        <p class="subtitle">Mock Webhook Testing Dashboard</p>
        
        <div class="card">
            <button class="btn-failed" onclick="triggerWebhook('payment.failed')">Trigger payment.failed</button>
            <button class="btn-dispute" onclick="triggerWebhook('payment.dispute.created')">Trigger payment.dispute.created</button>
            <button class="btn-halted" onclick="triggerWebhook('subscription.halted')">Trigger subscription.halted</button>
        </div>
        
        <div class="card">
            <h3>Response Logs</h3>
            <div id="logs" class="logs-container">
                <div class="log-entry"><span class="log-time">[System]</span> Dashboard loaded. Ready to send webhooks.</div>
            </div>
        </div>
    </div>

    <script>
        const payloads = {
            'payment.failed': {
                "account_id": "acc_test_123",
                "event": "payment.failed",
                "payload": {
                    "payment": {
                        "entity": {
                            "id": "pay_test_xyz123",
                            "email": "angry.customer@example.com",
                            "contact": "9876543210",
                            "card_number": "4111111111111111",
                            "error_description": "insufficient_funds"
                        }
                    }
                }
            },
            'payment.dispute.created': {
                "account_id": "acc_test_123",
                "event": "payment.dispute.created",
                "payload": {
                    "payment": {
                        "entity": {
                            "id": "pay_test_dispute_001",
                            "email": "customer@example.com",
                            "contact": "9876543210",
                            "amount": 49900,
                            "currency": "INR",
                            "dispute_id": "disp_test_001",
                            "dispute_reason": "fraud"
                        }
                    }
                }
            },
            'subscription.halted': {
                "account_id": "acc_test_123",
                "event": "subscription.halted",
                "payload": {
                    "subscription": {
                        "entity": {
                            "id": "sub_test_halted_001",
                            "customer_id": "cust_test_001",
                            "email": "customer@example.com",
                            "plan_id": "plan_test_monthly",
                            "status": "halted",
                            "reason": "payment_failure",
                            "halted_at": 1724169600
                        }
                    }
                }
            }
        };

        function log(message, type = 'info') {
            const logsDiv = document.getElementById('logs');
            const time = new Date().toLocaleTimeString();
            let typeClass = '';
            if (type === 'success') typeClass = 'log-success';
            if (type === 'error') typeClass = 'log-error';
            
            logsDiv.innerHTML += `<div class="log-entry"><span class="log-time">[${time}]</span> <span class="${typeClass}">${message}</span></div>`;
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }

        async function triggerWebhook(eventName) {
            log(`Sending payload for ${eventName}...`);
            try {
                const response = await fetch('/webhook', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payloads[eventName])
                });
                
                const data = await response.json();
                if (response.ok) {
                    log(`[${eventName}] Success: ${JSON.stringify(data)}`, 'success');
                } else {
                    log(`[${eventName}] Error ${response.status}: ${JSON.stringify(data)}`, 'error');
                }
            } catch (err) {
                log(`[${eventName}] Network Error: ${err.message}`, 'error');
            }
        }
    </script>
</body>
</html>
"""

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    return DASHBOARD_HTML

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
        target_events = ["payment.dispute.created", "payment.failed", "subscription.halted"]
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

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000/dashboard")

if __name__ == "__main__":
    print("Starting Omni-Trigger Webhook Listener on port 8000...")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
