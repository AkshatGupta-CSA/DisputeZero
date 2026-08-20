from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
from core.security import mask_pii
from services.razorpay_client import (
    get_mock_shopify_data, 
    get_mock_delhivery_data, 
    get_mock_subscription_context
)
from services.llm_router import process_event_with_gemini
from services.action_executor import execute_dispute_defense, execute_subscription_recovery
from dotenv import load_dotenv
import os
import webbrowser
import threading
import time
import json
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI(title="Unified Revenue Retention Agent")

# Initialize disputes metadata database if not present
DISPUTES_FILE = "disputes_meta.json"

def load_disputes() -> dict:
    import glob
    disputes = {}
    if os.path.exists(DISPUTES_FILE):
        try:
            with open(DISPUTES_FILE, "r", encoding="utf-8") as f:
                disputes = json.load(f)
        except Exception:
            disputes = {}
            
    # Sync with actual files present in the disputes directory
    file_patterns = [os.path.join("disputes", "defense_letter_*.pdf"), os.path.join("disputes", "defense_letter_*.txt")]
    found_payment_ids = set()
    changed = False
    
    for pattern in file_patterns:
        for file_path in glob.glob(pattern):
            filename = os.path.basename(file_path)
            # Extract payment ID (filename pattern is defense_letter_{payment_id}.{ext})
            name_without_prefix = filename[len("defense_letter_"):]
            payment_id, _ = os.path.splitext(name_without_prefix)
            
            found_payment_ids.add(payment_id)
            
            if payment_id not in disputes:
                try:
                    mtime = os.path.getmtime(file_path)
                    created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
                except Exception:
                    created_at = time.strftime("%Y-%m-%d %H:%M:%S")
                
                disputes[payment_id] = {
                    "id": payment_id,
                    "dispute_id": "disp_mock_" + payment_id[-6:],
                    "status": "New",
                    "file": file_path,
                    "amount": 499.00,
                    "created_at": created_at
                }
                changed = True
                
    # Clean up records if their corresponding physical files were deleted
    to_delete = []
    for pid, info in disputes.items():
        file_path = info.get("file", "")
        if not os.path.exists(file_path):
            to_delete.append(pid)
            
    if to_delete:
        for pid in to_delete:
            del disputes[pid]
        changed = True
        
    if changed:
        save_disputes(disputes)
        
    return disputes

def save_disputes(disputes: dict):
    with open(DISPUTES_FILE, "w", encoding="utf-8") as f:
        json.dump(disputes, f, indent=2)

# Create file if missing
if not os.path.exists(DISPUTES_FILE):
    os.makedirs("disputes", exist_ok=True)
    for i in range(1, 7):
        placeholder_path = os.path.join("disputes", f"defense_letter_pay_test_dispute_{i:03d}.pdf")
        if not os.path.exists(placeholder_path):
            with open(placeholder_path, "w") as f:
                f.write("%PDF-1.4 Mock PDF placeholder")
                
    mock_disputes = {
        "pay_test_dispute_001": {
            "id": "pay_test_dispute_001",
            "dispute_id": "disp_test_001",
            "status": "New",
            "file": os.path.join("disputes", "defense_letter_pay_test_dispute_001.pdf"),
            "amount": 499.00,
            "created_at": "2026-08-20 20:30:00"
        },
        "pay_test_dispute_002": {
            "id": "pay_test_dispute_002",
            "dispute_id": "disp_test_002",
            "status": "Completed",
            "file": os.path.join("disputes", "defense_letter_pay_test_dispute_002.pdf"),
            "amount": 1250.00,
            "created_at": "2026-08-20 18:15:00"
        },
        "pay_test_dispute_003": {
            "id": "pay_test_dispute_003",
            "dispute_id": "disp_test_003",
            "status": "New",
            "file": os.path.join("disputes", "defense_letter_pay_test_dispute_003.pdf"),
            "amount": 899.00,
            "created_at": "2026-08-20 15:45:00"
        },
        "pay_test_dispute_004": {
            "id": "pay_test_dispute_004",
            "dispute_id": "disp_test_004",
            "status": "Pending",
            "file": os.path.join("disputes", "defense_letter_pay_test_dispute_004.pdf"),
            "amount": 1499.00,
            "created_at": "2026-08-19 11:20:00"
        },
        "pay_test_dispute_005": {
            "id": "pay_test_dispute_005",
            "dispute_id": "disp_test_005",
            "status": "Completed",
            "file": os.path.join("disputes", "defense_letter_pay_test_dispute_005.pdf"),
            "amount": 299.00,
            "created_at": "2026-08-18 09:10:00"
        },
        "pay_test_dispute_006": {
            "id": "pay_test_dispute_006",
            "dispute_id": "disp_test_006",
            "status": "New",
            "file": os.path.join("disputes", "defense_letter_pay_test_dispute_006.pdf"),
            "amount": 2499.00,
            "created_at": "2026-08-20 22:05:00"
        }
    }
    save_disputes(mock_disputes)

@app.get("/checkout")
async def get_checkout():
    return FileResponse("checkout.html")

@app.get("/checkout-config")
async def get_checkout_config():
    return {
        "key": os.getenv("RAZORPAY_KEY_ID"),
        "amount": 499900,
        "currency": "INR",
        "name": "Acme SaaS",
        "description": "Pro Annual Plan Subscription"
    }

@app.get("/admin_console")
async def get_admin_console():
    return FileResponse("admin_console.html")

@app.get("/dashboard")
async def get_dashboard():
    return FileResponse("admin_console.html")

@app.get("/payment_success")
async def get_payment_success():
    return FileResponse("payment_success.html")

class DisputeStatusUpdate(BaseModel):
    status: str

@app.get("/api/disputes")
async def get_disputes_api():
    return list(load_disputes().values())

@app.post("/api/disputes/{payment_id}/status")
async def update_dispute_status(payment_id: str, payload: DisputeStatusUpdate):
    disputes = load_disputes()
    if payment_id not in disputes:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if payload.status not in ["Pending", "Completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    disputes[payment_id]["status"] = payload.status
    save_disputes(disputes)
    return {"status": "success", "payment_id": payment_id, "new_status": payload.status}

@app.get("/static/{filename}")
async def get_static_file(filename: str):
    if filename.startswith("defense_letter_"):
        file_path = os.path.join("disputes", filename)
        if os.path.exists(file_path):
            return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/webhook")
async def receive_razorpay_webhook(request: Request):
    """
    The Omni-Trigger: End-to-end autonomous loop (Listen -> Secure -> Context -> Brain -> Action).
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
        
        # 4. Gather Context (Phase 2)
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
        ai_output = ai_result["ai_decision_output"]
        
        # 6. Execute Real-World Actions (Phase 4: The Execution Paths)
        print("Executing Autonomous Actions...")
        action_result = {}
        
        if event_type == "payment.dispute.created":
            pdf_path = execute_dispute_defense(payment_id, ai_output)
            action_result = {"action": "dispute_uploaded", "file": pdf_path}
            
            # Record in disputes metadata database
            try:
                disputes = load_disputes()
                disputes[payment_id] = {
                    "id": payment_id,
                    "dispute_id": secured_payload.get("payload", {}).get("payment", {}).get("entity", {}).get("dispute_id", "disp_mock_" + payment_id[-6:]),
                    "status": "New",
                    "file": pdf_path,
                    "amount": float(secured_payload.get("payload", {}).get("payment", {}).get("entity", {}).get("amount", 49900)) / 100.0,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                save_disputes(disputes)
            except Exception as e:
                print(f"Error updating disputes metadata: {e}")
            
        elif event_type in ["payment.failed", "subscription.halted"]:
            recovery_res = execute_subscription_recovery(payment_id, ai_output)
            action_result = {"action": "whatsapp_recovery_sent", "details": recovery_res}
            
        return {
            "status": "success", 
            "message": f"Full agentic loop completed for {event_type}",
            "ai_output": ai_output,
            "execution_result": action_result,
            "context": context
        }

    except Exception as e:
        print(f"Error processing full agentic loop: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload or execution error")

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000/checkout")

if __name__ == "__main__":
    print("Starting Complete Unified Revenue Retention Agent on port 8000...")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
