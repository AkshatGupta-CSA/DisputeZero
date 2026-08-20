# Unified Revenue Retention Agent

A modern backend service designed to automate revenue retention by listening to payment gateway webhooks (e.g., Razorpay) for transaction failures or disputes, scrubbing sensitive customer data (PII), gathering commerce and logistics context, and running autonomous execution actions (e.g. generating PDFs or sending recovery messages).

![Webhook Dashboard](assets/dashboard_screenshot.png)

## Project Structure

The project has the following directory structure:

- **`core/`**: Core system guardrails and configuration (e.g., PII masking in `security.py`).
- **`models/`**: Data models and validation schemas (e.g., `DisputeStatusUpdate` in `schemas.py`/`main.py`).
- **`services/`**: Downstream business services and external client integrations:
  * `razorpay_client.py`: Mock context retrieval engine.
  * `llm_router.py`: LLM routing and prompt generation using Gemini.
  * `action_executor.py`: Action dispatcher for PDF compiling and WhatsApp notifications.
- **`utils/`**: General helper functions and utilities (e.g., JSON event logger in `storage.py`).
- **`disputes/`**: Dedicated storage folder keeping generated dispute documents organized and out of the project root.
- **`checkout.html`**: Standing mock D2C billing checkout portal featuring a custom Razorpay modal replica.
- **`admin_console.html`**: Standalone merchant dashboard with Webhook Simulator and Chargeback Disputes Panel.
- **`payment_success.html`**: A subscription purchase success splash page with a 10-second progress-bar redirect.
- **`main.py`**: FastAPI application containing webhook routing, metadata APIs, and startup browser launch scripts.

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

3. **Install wkhtmltopdf (Required for PDF generation):**
   * Download and install the binary package from **[wkhtmltopdf Downloads](https://wkhtmltopdf.org/downloads.html)**. On Windows, it should default to `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe` (pre-configured in the code).

4. **Run the FastAPI server & Interactive Dashboard:**
   * Run the server:
     ```powershell
     python main.py
     ```
   * The server starts on `http://localhost:8000`.
   * The browser will automatically open straight to the D2C checkout portal: `http://localhost:8000/checkout`.

5. **Expose Local Server with NGROK (for Razorpay Webhook testing):**
   ```powershell
   ngrok http 8000
   ```
   Configure the public forwarding HTTPS URL (e.g., `https://xxxx.ngrok-free.app/webhook`) in your Razorpay Dashboard webhooks.

## Architecture and Key Features

### 1. Fully Simulated Custom Sandbox Checkout
To allow fully offline and reliable testing without requiring real credit cards or standard SDK network constraints, we replaced the Razorpay CDN script with a **Custom Mock Payment Modal built from scratch** inside [`checkout.html`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/checkout.html).
* **Accurate Styling:** Replicates standard Razorpay colors, tabs (Card, UPI QR, Netbanking), and details.
* **Test Simulation Outcomes:**
  * **Success:** Redirects to a dynamic [`payment_success.html`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/payment_success.html) page displaying order metadata and a 10-second progress-bar counting down to an auto-close redirect.
  * **Failed (Money Deducted):** Prompts the user with an inline UI warning banner offering to report the failed payment (which fires a simulated webhook to `/webhook` for revenue recovery).
  * **Failed (Insufficient Funds):** Simulates failed checkout branch.

### 2. Tabbed Chargeback Disputes Panel (Admin Console)
The Merchant Dashboard inside [`admin_console.html`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/admin_console.html) has been upgraded with a professional disputes management workspace.
* **Top Webpage Active Disputes Badge:** Displays the real-time count of unresolved disputes at the top of the screen.
* **New disputes (Inbox):** Holds newly received disputes scanned from your folders or sent via webhooks.
* **Status Action Buttons:** Quickly toggle status between `Pending` and `Completed` right beside the document description. The file immediately moves to its relevant tab without reloading the page.
* **Auto-Sync Metadata Database:** The backend scanning engine (`glob` parser in `main.py`) continuously synchronizes the JSON metadata file `disputes_meta.json` with the actual files inside the physical `disputes/` folder. Creating, moving, or deleting files in that folder updates the dashboard metadata dynamically.

### 3. PII Masking Guardrails
Incoming payloads are sanitized inside [`core/security.py`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/core/security.py) by recursively replacing:
* **Emails** -> `[REDACTED_EMAIL]`
* **Indian Phone Numbers** -> `[REDACTED_PHONE]`
* **Credit Cards** -> `[REDACTED_CARD]`

### 4. LLM Routing & Fallbacks
Orchestrates prompt generation inside [`services/llm_router.py`](file:///C:/Users/aksha/.gemini/antigravity/scratch/Unified%20Revenue%20Retention%20Agent/services/llm_router.py), attempting sequential routing across Gemini model classes (`gemini-3.6-flash`, `gemini-2.0-flash`, `gemini-pro`) to prevent buildathon fallback errors.

### 5. Automated PDF Compilation
Converts markdown LLM output to standard HTML templates, utilizing `pdfkit` to compile formal dispute defense documents directly into the `disputes/` directory.

## Handled Webhook Events

The `/webhook` endpoint dynamically processes:
1. `payment.dispute.created` ➔ Automatically compiles shipping/logistics context and uploads a formal PDF defense to `disputes/`.
2. `payment.failed` ➔ Triggers autonomous LLM WhatsApp templates and constructs dynamic UPI checkout links.
3. `subscription.halted` ➔ Dispatches payment reminders to customers to prevent involuntary churn.
