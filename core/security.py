import re
import json
from typing import Any, Dict

def mask_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively scrubs Personally Identifiable Information (PII) from a dictionary.
    """
    data_str = json.dumps(data)
    
    # Mask Emails
    data_str = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', data_str)
    
    # Mask Indian Phone Numbers (basic 10 digit check)
    data_str = re.sub(r'(?<!\d)\d{10}(?!\d)', '[REDACTED_PHONE]', data_str)
    
    # Mask Credit Card Numbers (16 digits)
    data_str = re.sub(r'(?<!\d)\d{16}(?!\d)', '[REDACTED_CARD]', data_str)
    
    return json.loads(data_str)
