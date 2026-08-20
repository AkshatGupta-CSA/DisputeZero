import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables to fetch the Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def process_event_with_gemini(event_type: str, secured_payload: dict, context: dict) -> dict:
    """
    Sends the secured event and context to Gemini to generate 
    a defense letter or a recovery negotiation strategy.
    """
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

    # Try different models sequentially to handle API key / version model access permissions
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]
    response = None
    last_error = None

    for model_name in models_to_try:
        try:
            print(f"Attempting generation with model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            # If successful, exit fallback loop
            break
        except Exception as e:
            last_error = e
            print(f"Model {model_name} failed: {e}")
            continue

    if response is None:
        raise Exception(f"All Gemini models failed. Last error: {last_error}")
    
    return {
        "event_type": event_type,
        "ai_decision_output": response.text
    }
