# Unified Revenue Retention Agent

A modern backend service designed to automate revenue retention by listening to payment gateway webhooks (e.g., Razorpay) for transaction failures or disputes, scrub sensitive customer data (PII), gather commerce and logistics context, and prepare payloads for downstream processing.

## Project Structure

The project has the following directory structure:

- **`core/`**: Core system guardrails and configuration (e.g., PII masking in `security.py`).
- **`models/`**: Data models and validation schemas (e.g., `RazorpayWebhook` schema in `schemas.py`).
- **`services/`**: Downstream business services and external client integrations (e.g., Mock context engine in `razorpay_client.py`).
- **`utils/`**: General helper functions and utilities.
- **`main.py`**: The FastAPI application entry point, containing the `/webhook` listener.
- **`.env`**: Local secret environment variables (excluded from Git).
- **`requirements.txt`**: Project dependencies.
- **`.gitignore`**: Pattern rules for files/folders to exclude from version control.

## Setup Instructions

1. **Activate the Virtual Environment:**
   * **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
   * **macOS/Linux:** `source .venv/bin/activate`

2. **Configure Environment Variables:**
   * Populate your credentials in the [`.env`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/.env) file:
     * `RAZORPAY_KEY_ID`
     * `RAZORPAY_KEY_SECRET`
     * `RAZORPAY_WEBHOOK_SECRET`
     * `GEMINI_API_KEY`

3. **Run the FastAPI server & Interactive Dashboard:**
   ```powershell
   python main.py
   ```
   * The webhook listener will spin up on `http://localhost:8000`.
   * An **Interactive Testing Dashboard** will automatically open in a new browser tab at `http://localhost:8000/dashboard` to let you test webhooks with one click.

4. **Expose Local Server with NGROK (for Razorpay Webhook testing):**
   Since Razorpay needs a public URL to send webhook events, use NGROK to expose your local port `8000`:
   ```powershell
   ngrok http 8000
   ```
   Copy the generated forwarding HTTPS URL (e.g., `https://xxxx.ngrok-free.app`) and configure it in your Razorpay Dashboard webhooks settings as the Webhook URL (pointing to `https://xxxx.ngrok-free.app/webhook`).

## Features and Guardrails

### 1. Security & PII Masking
All incoming webhook payloads are immediately scanned and cleaned by the PII masking logic in [`core/security.py`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/core/security.py). It redacts:
* **Emails** -> `[REDACTED_EMAIL]`
* **Indian Phone Numbers** -> `[REDACTED_PHONE]`
* **Credit Card Numbers** -> `[REDACTED_CARD]`

### 2. Payload Validation
FastAPI automatically validates incoming webhooks using the Pydantic schema defined in [`models/schemas.py`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/models/schemas.py). The schema ensures the payload matches the expected structure:
* `account_id` (string)
* `event` (string)
* `payload` (dictionary)
* `created_at` (optional integer)

### 3. Context Retrieval Engine
Mock context retrieval methods are implemented in [`services/razorpay_client.py`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/services/razorpay_client.py) to simulate pulling essential data for decision making:
* **Shopify Data**: Simulates fetching the original invoice details (customer name, items, shipping address).
* **Delhivery Data**: Simulates fetching logistics status, tracking number, and delivery IP (crucial for defending disputes).
* **Subscription Context**: Simulates fetching subscription history, renewal status, CLV, and negotiation leverage.

## Handled Events

The `/webhook` endpoint currently listens for and processes:
1. `payment.dispute.created`
2. `payment.failed`
3. `subscription.halted`
