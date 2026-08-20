import os
import pdfkit
import requests
import markdown

def execute_dispute_defense(payment_id: str, ai_letter_text: str) -> str:
    """
    Converts the LLM's defense letter into a formal PDF and simulates 
    uploading it to the Razorpay Disputes API.
    """
    # Create disputes directory if it does not exist
    disputes_dir = "disputes"
    os.makedirs(disputes_dir, exist_ok=True)
    
    pdf_filename = os.path.join(disputes_dir, f"defense_letter_{payment_id}.pdf")
    
    # Convert raw markdown formatting into clean HTML elements
    html_body = markdown.markdown(ai_letter_text)
    
    # Wrap the parsed HTML body in page styles for PDF conversion
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Helvetica, Arial, sans-serif; margin: 40px; color: #333; }}
                h2 {{ color: #111; border-bottom: 2px solid #000; padding-bottom: 10px; }}
                p {{ line-height: 1.6; }}
                ul, ol {{ line-height: 1.6; margin-bottom: 15px; padding-left: 20px; }}
                li {{ margin-bottom: 5px; }}
                code {{ background-color: #f4f6f8; padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }}
                blockquote {{ border-left: 4px solid #ccd; padding-left: 15px; color: #555; margin-left: 0; }}
            </style>
        </head>
        <body>
            <h2>Formal Chargeback Defense Submission</h2>
            <p><strong>Payment ID:</strong> {payment_id}</p>
            <hr/>
            <div>{html_body}</div>
        </body>
    </html>
    """
    
    # Generate the physical PDF file
    try:
        default_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        if os.path.exists(default_path):
            config = pdfkit.configuration(wkhtmltopdf=default_path)
            pdfkit.from_string(html_content, pdf_filename, configuration=config)
        else:
            pdfkit.from_string(html_content, pdf_filename)
        print(f"[ACTION] Successfully generated defense PDF: {pdf_filename}")
    except Exception as e:
        pdf_filename = os.path.join(disputes_dir, f"defense_letter_{payment_id}.txt")
        print(f"[WARNING] wkhtmltopdf not found or error generating PDF: {e}. Saving as text backup to {pdf_filename}")
        with open(pdf_filename, "w", encoding="utf-8") as f:
            f.write(ai_letter_text)

    # Simulate submission to Razorpay Test Disputes API
    # In production, you would make an authenticated POST/PUT request to Razorpay's dispute evidence upload endpoint.
    print(f"[ACTION] Uploading {pdf_filename} to Razorpay Disputes API (Test Mode)... Done!")
    
    return pdf_filename

def execute_subscription_recovery(payment_id: str, ai_whatsapp_message: str) -> dict:
    """
    Simulates sending the recovery message via Twilio/WhatsApp sandbox 
    and generating a dynamic Razorpay UPI payment link.
    """
    # Simulate generating a dynamic UPI payment link via Razorpay API
    mock_upi_link = f"https://rzp.io/i/mock_{payment_id[-6:]}"
    
    full_message = f"{ai_whatsapp_message}\n\nPay securely via UPI: {mock_upi_link}"
    
    print(f"\n--- TWILIO WHATSAPP SANDBOX DISPATCH ---")
    print(f"Sending to customer for payment {payment_id}:")
    print(full_message)
    print("-----------------------------------------\n")
    
    # In production, you would call Twilio's API here:
    # client.messages.create(body=full_message, from_='whatsapp:+14155238886', to='whatsapp:+91XXXXXXXXXX')
    
    return {
        "status": "sent",
        "payment_link": mock_upi_link,
        "channel": "WhatsApp"
    }
