# Unified Revenue Retention Agent

A modern backend service designed to automate revenue retention by listening to payment gateway webhooks (e.g., Razorpay) for transaction failures or disputes, scrub sensitive customer data (PII), and prepare payloads for downstream processing.

## Project Structure

The project has the following directory structure:

- **`core/`**: Core system guardrails and configuration (e.g., PII masking in `security.py`).
- **`models/`**: Data models and validation schemas.
- **`services/`**: Downstream business services.
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

3. **Run the FastAPI server:**
   ```powershell
   python main.py
   ```
   The webhook listener will spin up on `http://localhost:8000`.

## Security Guardrails

All incoming webhook payloads are immediately scanned and cleaned by the PII masking logic in [`core/security.py`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/core/security.py). It redacts:
* **Emails** -> `[REDACTED_EMAIL]`
* **Indian Phone Numbers** -> `[REDACTED_PHONE]`
* **Credit Card Numbers** -> `[REDACTED_CARD]`

## Handled Events

The `/webhook` endpoint currently listens for and processes:
1. `dispute.created`
2. `subscription.charged.failed`
