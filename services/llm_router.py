import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables to fetch the Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def process_event_with_gemini(event_type: str, secured_payload: dict, context: dict) -> dict:
    """
    Sends the secured event and context to Gemini Flash to generate 
    a defense letter or a recovery negotiation strategy.
    """
    # Using Gemini 1.5 Flash or modern equivalents for webhook routing and decision making
    # Note: If gemini-3.5-flash is not available, we can fallback to gemini-1.5-flash
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception:
        model = genai.GenerativeModel("gemini-pro")
    
    if event_type == "payment.dispute.created":
        prompt = f"""
        You are an expert fintech AI legal assistant for a Razorpay merchant. 
        A customer has filed a chargeback dispute. Your job is to draft a formal, compelling defense letter to the bank.
        
        Here is the secure payment/dispute data:
        {secured_payload}
        
        Here is the gathered merchant context (Shopify Order & Delhivery Logistics Proof):
        {context}
        
        Instructions:
        1. Summarize the evidence clearly (mention the order details, delivery status, and matching delivery timestamp/IP).
        2. Draft a professional, firm dispute defense letter addressed to the issuing bank.
        3. Keep it concise, formal, and structured for submission.
        """
        
    elif event_type in ["payment.failed", "subscription.halted"]:
        prompt = f"""
        You are an AI retention specialist for a Razorpay merchant. 
        A customer's recurring payment has failed or their subscription has halted.
        
        Here is the secure event data:
        {secured_payload}
        
        Here is the subscription context:
        {context}
        
        Instructions:
        1. Analyze the failure reason and customer value (CLV).
        2. Draft a personalized, friendly, and persuasive WhatsApp message to the customer. 
        3. Offer a clear resolution (e.g., asking to switch their payment method to UPI or offering to pause the subscription).
        """
    else:
        return {"error": "Unknown event type for LLM routing."}

    # Generate the response from Gemini
    response = model.generate_content(prompt)
    
    return {
        "event_type": event_type,
        "ai_decision_output": response.text
    }
