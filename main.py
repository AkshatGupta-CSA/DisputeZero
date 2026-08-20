from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from core.security import mask_pii
from services.razorpay_client import (
    get_mock_shopify_data, 
    get_mock_delhivery_data, 
    get_mock_subscription_context
)
from services.llm_router import process_event_with_gemini
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
    <title>Razorpay Webhook Retainer Dashboard</title>
    <style>
        :root {
            --rp-navy: #0b192c;
            --rp-blue: #0c6cff;
            --rp-blue-hover: #0056cc;
            --rp-bg: #f8fafe;
            --rp-card-bg: #ffffff;
            --rp-text-main: #2d3748;
            --rp-text-muted: #718096;
            --rp-border: #e2e8f0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--rp-bg);
            color: var(--rp-text-main);
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        .sidebar {
            width: 240px;
            background-color: var(--rp-navy);
            color: #ffffff;
            display: flex;
            flex-direction: column;
            padding: 20px 0;
            flex-shrink: 0;
        }
        .sidebar-logo {
            font-size: 20px;
            font-weight: 800;
            padding: 0 24px;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            color: #ffffff;
            letter-spacing: -0.5px;
        }
        .sidebar-logo span {
            color: var(--rp-blue);
            margin-left: 2px;
            font-weight: 400;
        }
        .sidebar-menu {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .sidebar-item {
            padding: 14px 24px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            color: #a0aec0;
            transition: all 0.2s;
            display: flex;
            align-items: center;
        }
        .sidebar-item:hover, .sidebar-item.active {
            color: #ffffff;
            background-color: rgba(255, 255, 255, 0.05);
            border-left: 4px solid var(--rp-blue);
            padding-left: 20px;
        }
        .main-content {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .topbar {
            height: 60px;
            background-color: #ffffff;
            border-bottom: 1px solid var(--rp-border);
            display: flex;
            align-items: center;
            padding: 0 30px;
            justify-content: space-between;
        }
        .topbar-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--rp-text-main);
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1.2fr;
            gap: 30px;
            padding: 30px;
            flex-grow: 1;
            overflow-y: auto;
            align-items: start;
        }
        .card {
            background-color: var(--rp-card-bg);
            border-radius: 6px;
            border: 1px solid var(--rp-border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            padding: 24px;
            display: flex;
            flex-direction: column;
        }
        .card-title {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--rp-text-muted);
            margin-bottom: 20px;
        }
        .btn-webhook {
            background-color: #ffffff;
            border: 1px solid var(--rp-border);
            color: var(--rp-text-main);
            padding: 14px 20px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
            text-align: left;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .btn-webhook:hover {
            border-color: var(--rp-blue);
            box-shadow: 0 0 0 1px var(--rp-blue);
            background-color: #fcfdff;
        }
        .btn-webhook:active {
            transform: scale(0.99);
        }
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-failed { background-color: #fff5f5; color: #e53e3e; border: 1px solid #fed7d7; }
        .badge-dispute { background-color: #fffaf0; color: #dd6b20; border: 1px solid #feebc8; }
        .badge-halted { background-color: #f0fff4; color: #38a169; border: 1px solid #c6f6d5; }

        .logs-container {
            background-color: #0f172a;
            border-radius: 4px;
            padding: 16px;
            overflow-y: auto;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 12px;
            color: #e2e8f0;
            height: 380px;
            border: 1px solid #1e293b;
        }
        .log-entry {
            margin-bottom: 10px;
            line-height: 1.6;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 8px;
        }
        .log-entry:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }
        .log-time { color: #64748b; margin-right: 8px; }
        .log-success { color: #4ade80; font-weight: bold; }
        .log-error { color: #f87171; font-weight: bold; }
        .log-payload {
            background-color: #1e293b;
            padding: 8px;
            border-radius: 4px;
            margin-top: 5px;
            color: #38bdf8;
            overflow-x: auto;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-logo">razorpay<span>retention</span></div>
        <ul class="sidebar-menu">
            <li class="sidebar-item active">Webhook Simulator</li>
            <li class="sidebar-item">Analytics Dashboard</li>
            <li class="sidebar-item">Dispute Files</li>
            <li class="sidebar-item">Security Settings</li>
        </ul>
    </div>
    <div class="main-content">
        <div class="topbar">
            <div class="topbar-title">Retainer Webhook Dashboard</div>
            <div style="font-size: 12px; color: var(--rp-text-muted);">Environment: <strong style="color: var(--rp-blue)">Razorpay Test Mode</strong></div>
        </div>
        <div class="dashboard-grid">
            <div class="card">
                <div class="card-title">Simulate Webhook Trigger</div>
                <button class="btn-webhook" onclick="triggerWebhook('payment.failed')">
                    <span>payment.failed</span>
                    <span class="badge badge-failed">Failed</span>
                </button>
                <button class="btn-webhook" onclick="triggerWebhook('payment.dispute.created')">
                    <span>payment.dispute.created</span>
                    <span class="badge badge-dispute">Dispute</span>
                </button>
                <button class="btn-webhook" onclick="triggerWebhook('subscription.halted')">
                    <span>subscription.halted</span>
                    <span class="badge badge-halted">Halted</span>
                </button>
            </div>
            <div class="card">
                <div class="card-title">Live Event Streams</div>
                <div id="logs" class="logs-container">
                    <div class="log-entry"><span class="log-time">[00:00:00]</span> Initialized Razorpay Dashboard listener...</div>
                </div>
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

        function log(message, type = 'info', extra = '') {
            const logsDiv = document.getElementById('logs');
            const time = new Date().toLocaleTimeString();
            let typeClass = '';
            if (type === 'success') typeClass = 'log-success';
            if (type === 'error') typeClass = 'log-error';
            
            let extraHTML = '';
            if (extra) {
                extraHTML = `<div class="log-payload">${extra}</div>`;
            }
            
            logsDiv.innerHTML += `
                <div class="log-entry">
                    <span class="log-time">[${time}]</span>
                    <span class="${typeClass}">${message}</span>
                    ${extraHTML}
                </div>
            `;
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }

        async function triggerWebhook(eventName) {
            log(`Triggering webhook endpoint with ${eventName}...`, 'info');
            try {
                const response = await fetch('/webhook', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payloads[eventName])
                });
                
                const data = await response.json();
                const prettyJSON = JSON.stringify(data, null, 2);
                if (response.ok) {
                    log(`[${eventName}] Response 200 OK`, 'success', prettyJSON);
                } else {
                    log(`[${eventName}] Error ${response.status}`, 'error', prettyJSON);
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
    The Omni-Trigger: Listens for incoming Razorpay webhooks, gathers context, and activates the Gemini Brain.
    """
    try:
        raw_payload = await request.json()
        event_type = raw_payload.get("event")
        
        target_events = ["payment.dispute.created", "payment.failed", "subscription.halted"]
        if event_type not in target_events:
            return {"status": "ignored", "message": f"Event {event_type} not tracked."}
        
        # 1. Scrub sensitive data (PII)
        secured_payload = mask_pii(raw_payload)
        
        # 2. Store the secured event locally
        from utils.storage import store_webhook_event
        store_webhook_event(event_type, secured_payload)
        
        # 3. Extract Payment ID safely
        payment_id = "pay_unknown"
        if "payment" in secured_payload.get("payload", {}):
            payment_id = secured_payload["payload"]["payment"]["entity"].get("id", "pay_unknown")
        elif "subscription" in secured_payload.get("payload", {}):
            payment_id = secured_payload["payload"]["subscription"]["entity"].get("id", "sub_unknown")
            
        print(f"\n--- INCOMING SECURE EVENT: {event_type} ---")
        
        # 4. Gather Context
        context = {}
        if event_type == "payment.dispute.created":
            print(f"Gathering Shopify & Delhivery proof for {payment_id}...")
            context["commerce_data"] = get_mock_shopify_data(payment_id)
            context["logistics_data"] = get_mock_delhivery_data(payment_id)
            
        elif event_type in ["payment.failed", "subscription.halted"]:
            print(f"Gathering subscription profile for {payment_id}...")
            context["subscription_data"] = get_mock_subscription_context()
            
        # 5. Activate the Brain (Phase 3: Gemini LLM Orchestration)
        print("Engaging Gemini Flash Brain...")
        ai_result = process_event_with_gemini(event_type, secured_payload, context)
        
        print("\n=== GEMINI EXECUTION RESULT ===")
        print(ai_result["ai_decision_output"])
        print("=================================\n")
        
        return {
            "status": "success", 
            "message": f"Gemini successfully processed {event_type}",
            "ai_output": ai_result["ai_decision_output"],
            "context": context
        }

    except Exception as e:
        print(f"Error processing webhook through LLM: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload or LLM error")

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000/dashboard")

if __name__ == "__main__":
    print("Starting Unified Revenue Retention Agent (With Gemini Brain) on port 8000...")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
